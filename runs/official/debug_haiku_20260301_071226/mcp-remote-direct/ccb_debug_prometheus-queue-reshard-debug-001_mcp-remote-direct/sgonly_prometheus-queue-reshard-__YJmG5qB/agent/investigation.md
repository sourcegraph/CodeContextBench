# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

After a Prometheus upgrade or during dynamic target discovery changes, remote-write destinations intermittently stop receiving samples. The root cause is a race condition in the queue resharding mechanism where the pending samples metric (`prometheus_remote_storage_samples_pending`) is reset to zero while samples may still be in flight, causing the metric to become inconsistent with actual pending data and creating stuck shards.

## Root Cause

**Location:** `storage/remote/queue_manager.go`, functions `start()` (line 1241), `enqueue()` (lines 1312-1340), and the interaction between `reshardLoop()` (lines 1184-1199) and `updateMetrics()` (lines 1661-1695)

**Mechanism:** The race condition involves an unsynchronized reset of the pending samples metric during resharding:

1. **Metric Reset During Resharding** (line 1241 in `start()`):
   ```go
   func (s *shards) start(n int) {
       s.mtx.Lock()
       defer s.mtx.Unlock()

       s.qm.metrics.pendingSamples.Set(0)  // <-- METRIC RESET
       s.qm.metrics.numShards.Set(float64(n))

       newQueues := make([]*queue, n)
       for i := range n {
           newQueues[i] = newQueue(...)
       }
       s.queues = newQueues  // <-- Queue array replaced
       ...
   }
   ```

2. **Premature Metric Reset Timing:**
   - When `reshardLoop()` calls `stop()`, old queue goroutines begin flushing samples
   - `stop()` waits up to `flushDeadline` for samples to be sent (default varies, can be seconds)
   - However, `start()` is called **immediately after** `stop()` returns
   - `start()` unconditionally resets `pendingSamples` to 0 **before** verifying all pending samples were actually sent

3. **Sample Flush Race Window:**
   ```go
   func (t *QueueManager) reshardLoop() {
       for {
           select {
           case numShards := <-t.reshardChan:
               t.shards.stop()        // Tries to flush old shards
               t.shards.start(numShards) // <-- IMMEDIATELY resets metrics
           case <-t.quit:
               return
           }
       }
   }
   ```

4. **Incomplete Flush Scenario:**
   - If `stop()` doesn't fully flush all samples within `flushDeadline`, it performs a hard shutdown
   - Hard shutdown causes remaining samples to be dropped from the old shards
   - But `start()` has already reset the metric, losing track of how many samples were dropped
   - New samples enqueued to new shards are now tracked, but the metric started at 0 instead of reflecting the true pending count

## Evidence

### Code References:

1. **Metrics Reset (queue_manager.go:1241):**
   - Unconditional `Set(0)` on pending samples metric when new shards start
   - No accounting for samples that may still be flushing from old shards

2. **Flush Timeout Handling (queue_manager.go:1286-1294):**
   ```go
   select {
   case <-s.done:
       return
   case <-time.After(s.qm.flushDeadline):
   }
   // Force an unclean shutdown
   s.hardShutdown()
   <-s.done
   ```
   - If flush times out, hard shutdown is initiated
   - Pending samples are counted as dropped, but metric was already reset

3. **Sample Enqueue with Metric Tracking (queue_manager.go:1312-1340):**
   ```go
   func (s *shards) enqueue(ref chunks.HeadSeriesRef, data timeSeries) bool {
       s.mtx.RLock()
       defer s.mtx.RUnlock()

       shard := uint64(ref) % uint64(len(s.queues))
       select {
       case <-s.softShutdown:
           return false
       default:
           appended := s.queues[shard].Append(data)
           if !appended {
               return false
           }
           ...
           s.qm.metrics.pendingSamples.Inc()  // Incremented here
           ...
       }
   }
   ```

4. **Metrics Update After Send (queue_manager.go:1661-1695):**
   - `updateMetrics()` decrements pending samples when batches are sent
   - Called from `sendSamples()` which is called from each shard's `runShard()` goroutine
   - This is the only place where pending samples are decremented

5. **Recent Enhancements (CHANGELOG.md:292):**
   - Issue #14450 added check to skip resharding if no successful send in past update period
   - But this doesn't address the metric reset race during actual resharding

### Test Case Evidence (queue_manager_test.go:514-550):
- `TestReshard()` explicitly tests resharding but only verifies data eventually arrives
- Does not stress-test the metric consistency during resharding
- Does not test the flushDeadline timeout scenario

## Affected Components

1. **storage/remote/queue_manager.go**
   - `reshardLoop()` - initiates resharding
   - `start()` - creates new shards and resets metrics (BUG LOCATION)
   - `stop()` - flushes old shards
   - `enqueue()` - adds samples and increments metrics
   - `updateMetrics()` - sends/drops samples and updates metrics

2. **Metrics System:**
   - `prometheus_remote_storage_samples_pending` - becomes inconsistent
   - Other pending metrics (`pending_exemplars`, `pending_histograms`) - same issue

3. **WAL and Target Discovery:**
   - Target discovery changes trigger resharding
   - New samples arrive while resharding is in progress
   - Can cause contention between old/new shard queue assignments

## Why This Is Intermittent

The issue is intermittent because it requires a specific timing window:

1. **Trigger Condition:** Resharding must occur (usually due to load changes from target discovery updates)

2. **Race Window:** The timing window exists between:
   - When `stop()` begins its flushDeadline timeout
   - When `start()` completes and resets the metric

3. **Manifestation Depends On:**
   - How many samples are pending when resharding occurs
   - Whether the flush completes before the deadline
   - Whether new samples arrive during the resharding window
   - Which shard receives the stuck samples (random distribution based on series refs)

4. **Why Not Always Visible:**
   - If resharding happens when queue is empty, no samples to lose track of
   - If resharding completes quickly (good network, small backlog), flush completes before timeout
   - If samples resume flowing, the metric can eventually reconcile (though via error paths)

## Diagnostic Approach

To confirm this root cause, monitor these metrics and logs simultaneously:

1. **Logs to Watch:**
   ```
   "level=info msg="Resharding queues" from=X to=Y"
   "level=info msg="Resharding done" numShards=Y"
   ```

2. **Metrics to Check:**
   - `prometheus_remote_storage_samples_pending` - should increase when samples enqueued, decrease when sent
   - `prometheus_remote_storage_samples_dropped_total{reason="..."}` - count of dropped samples
   - `prometheus_remote_storage_shards` - number of active shards

3. **Correlation Pattern:**
   - Around resharding events, look for:
     - `pending_samples` jumping to non-zero after resharding
     - Some shards remaining idle (not processing any batches)
     - Matching increase in `samples_dropped_total` immediately after the flush timeout

4. **Network/Load Conditions:**
   - Issue is most likely when:
     - Remote endpoint is slow or temporarily unresponsive
     - `flushDeadline` is exceeded during resharding
     - High cardinality of series causes many shards to be involved

## Recommendation

The fix requires ensuring metrics accurately reflect pending samples across resharding operations:

### Fix Strategy (Priority Order):

1. **Immediate:** Count pending samples from old shards BEFORE resetting metric
   - Before `start()` resets the metric, query `enqueuedSamples` from each old shard
   - Add those to a temporary counter
   - Subtract as they're actually sent from old shards after resharding
   - Initialize new shard metric to this value instead of 0

2. **Alternative:** Defer metric reset until old shards confirm complete flush
   - Modify `start()` to only reset metrics after receiving confirmation from old shards
   - Or track metrics per-shard cohort (old vs. new) during resharding window

3. **Robustness:** Increase `flushDeadline` or add exponential backoff
   - Current timeout may be too short under load
   - Consider longer deadline or retry logic before hard shutdown

4. **Observability:** Add metrics for resharding events
   - `prometheus_remote_storage_resharding_duration_seconds` - time spent in resharding
   - `prometheus_remote_storage_samples_flushed_during_reshard_total` - track samples during reshard
   - Log samples lost due to hard shutdown with shard identifiers

### Verification Steps:

After fix is implemented, run:
- Existing `TestReshard()` and `TestReshardRaceWithStop()` test cases
- New stress test: trigger resharding while sending high-volume samples
- New test: simulate `flushDeadline` timeout and verify metrics remain consistent
- Integration test: verify metric consistency across upgrade with target discovery changes
