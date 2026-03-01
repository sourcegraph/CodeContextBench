# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

The Prometheus remote-write queue system experiences intermittent sample loss and stalled shards during dynamic resharding operations. When target discovery changes trigger shard count adjustments, a race condition between metric resetting and incomplete queue flushing causes samples to be silently dropped while metrics incorrectly report zero pending samples.

## Root Cause

### Primary Issue: Metric Reset During Incomplete Flush

**File**: `storage/remote/queue_manager.go`, **Function**: `shards.start()` (line 1237-1266)

The bug occurs at line 1241:
```go
func (s *shards) start(n int) {
    s.mtx.Lock()
    defer s.mtx.Unlock()

    s.qm.metrics.pendingSamples.Set(0)  // Line 1241 - RESETS METRIC
    s.qm.metrics.numShards.Set(float64(n))
```

When resharding is triggered in `reshardLoop()` (line 1184-1199):
```go
case numShards := <-t.reshardChan:
    t.shards.stop()      // Line 1193 - Stops old shards
    t.shards.start(numShards)  // Line 1194 - Starts new shards
```

The sequence creates a race condition:

1. **stop() is called** (line 1269-1305):
   - Closes `softShutdown` channel (line 1275)
   - All queues attempt FlushAndShutdown (line 1284)
   - Waits up to `flushDeadline` for completion (line 1289)

2. **If flush times out** (line 1289):
   - Hard shutdown is triggered (line 1293)
   - Old shard goroutines begin dropping samples (line 1566-1577 in `runShard`)
   - Samples in queues are lost

3. **start() is called while old shards still dropping**:
   - **Immediately resets metric: `pendingSamples.Set(0)`** (line 1241)
   - Creates new queue array (line 1244-1246)
   - Starts new shard goroutines (line 1263-1265)
   - Dropped samples from old shards are never reflected in metrics

### Secondary Issue: Shard Assignment Changes During Transition

**File**: `storage/remote/queue_manager.go`, **Function**: `enqueue()` (line 1312-1341)

The shard assignment is computed by: `shard := uint64(ref) % uint64(len(s.queues))` (line 1315)

During resharding:
- Old queues have count `N`
- New queues have count `M` (where N ≠ M due to scaling)
- Samples that fail to enqueue during shutdown retry later
- They now hash to potentially different shard indices
- This can create unbalanced load or ordering issues

## Evidence

### Key Code Paths

**Resharding Trigger** (`queue_manager.go:1057-1082`):
```go
func (t *QueueManager) updateShardsLoop() {
    ...
    case t.reshardChan <- desiredShards:
        t.logger.Info("Remote storage resharding", "from", t.numShards, "to", desiredShards)
        t.numShards = desiredShards
```

**Sample Enqueueing** (`queue_manager.go:1312-1341`):
- Line 1326: `s.qm.metrics.pendingSamples.Inc()` - increments when added
- Line 1241: `s.qm.metrics.pendingSamples.Set(0)` - **unconditionally reset!**
- No corresponding decrement when old samples are dropped

**Sample Drop Path** (`queue_manager.go:1561-1578`):
```go
case <-ctx.Done():
    droppedSamples := int(s.enqueuedSamples.Load())
    s.qm.metrics.pendingSamples.Sub(float64(droppedSamples))  // Only if hard shutdown
    s.qm.metrics.failedSamplesTotal.Add(float64(droppedSamples))
```

The problem: When `Set(0)` is called in `start()`, this overrides any attempted decrements from old shards.

### Timing Window

The issue manifests as **intermittent** because it depends on:
1. **Resharding trigger**: Target discovery changes (add/remove targets)
2. **Load at trigger time**: Number of samples in flight when resharding begins
3. **Flush deadline**: Whether old queues can send all samples within timeout
4. **Remote backend latency**: If remote storage is slow, flush times out

Scenarios that increase probability:
- High sample volume during discovery change
- Slow remote-write backend (causing sends to take > flushDeadline)
- Frequent target discovery updates

## Affected Components

### Primary Package
- **`storage/remote/`**: Queue management, resharding logic

### Specific Files
- `queue_manager.go`: Core resharding mechanism (lines 1057-1305)
- Lines 1237-1266: `shards.start()` - the bug trigger
- Lines 1184-1199: `reshardLoop()` - orchestrates resharding
- Lines 1269-1305: `shards.stop()` - initiates flush/shutdown
- Lines 1312-1341: `enqueue()` - shard assignment

### Metrics Affected
- `prometheus_remote_storage_samples_pending` - reports 0 despite queued samples
- `prometheus_remote_storage_shards` - transitions occur during vulnerable window
- `prometheus_remote_storage_samples_dropped_total` - incomplete on timeout

## Mechanism: Why Shards Stall

1. **During resharding transition window**:
   - `softShutdown` is closed in old shards (line 1275)
   - `enqueue()` fails for new samples (line 1317-1318)
   - No new shards exist yet (sequential: stop → start)

2. **Failed samples in WAL retry loop** (line 815-866 example):
   ```go
   for {
       if t.shards.enqueue(...) {
           continue outer
       }
       t.metrics.enqueueRetriesTotal.Inc()
       time.Sleep(time.Duration(backoff))
       // Retry with exponential backoff
   }
   ```

3. **When start() completes**:
   - Retrying samples go to new queues
   - But if new shard count differs, hash assignments change
   - Some historical samples may hash to different (potentially saturated) shards

4. **Result**:
   - Specific shards appear stuck with `samples_pending > 0`
   - Other shards drain normally
   - Uneven load distribution persists

## Diagnostic Evidence

### Logs to Watch For
- `"Remote storage resharding"` - indicates resharding started
- `"Currently resharding, skipping"` - resharding in progress (from line 1076)
- `"Failed to flush all samples on shutdown"` - samples dropped (from line 1299)
- `"enqueue_retries_total"` increasing - samples failing to enqueue (metric)

### Metrics to Correlate
1. `prometheus_remote_storage_shards` - changes during resharding
2. `prometheus_remote_storage_samples_pending` - should **not** drop to 0 during transition
3. `prometheus_remote_storage_samples_dropped_total` - increase during timeout
4. `prometheus_remote_storage_enqueue_retries_total` - spikes during resharding window
5. Query: Which shards have high pending values?
   - `prometheus_remote_storage_samples_pending{shard="X"}` if exposed per-shard

### Reproduction Conditions
- Trigger target discovery changes while sending high sample volume
- Configure remote backend with high latency
- Set low `flushDeadline` in config
- Monitor metrics during target add/remove operations

## Recommendation

### Fix Strategy

**Option 1: Atomic Metric Update (Recommended)**
- Track pending samples from old shards before reset
- Only reset new shards' metrics
- Don't call `Set(0)` unconditionally

**Option 2: Prevent Resharding During Flush**
- Don't trigger new resharding until old shards fully shutdown
- Wait for `s.done` channel before calling `start()`
- Currently already done sequentially, so issue is timing

**Option 3: Increase Flush Timeout**
- Current default `flushDeadline` may be too aggressive
- Extend to allow slow backends to drain queues
- Less ideal: masks the real issue

### Diagnostic Steps for Root Cause Confirmation

1. **Query metrics during target discovery change**:
   ```
   # Watch when resharding starts
   prometheus_remote_storage_shards

   # Should NOT drop to 0 mid-resharding
   prometheus_remote_storage_samples_pending

   # Count dropped samples
   prometheus_remote_storage_samples_dropped_total
   ```

2. **Enable debug logging** in remote storage:
   - Check logs for "Resharding done" log message
   - Verify samples_pending > 0 at that point
   - If pending drops to 0 immediately after, bug confirmed

3. **Trace queue depth**:
   - Check old shard queue lengths before stop()
   - Check if samples appear in queued-but-dropped metrics
   - Correlate timestamp of resharding with metric spikes

4. **Check remote backend latency**:
   - If backend slowness triggered timeout, check remote latency metrics
   - Confirm `flushDeadline` is insufficient for current backend

## Related Issues

- CHANGELOG #13562: "Disable resharding during active retry backoffs"
- CHANGELOG #7122: "Fixed blocked resharding edge case"
- These suggest this is a known challenging area with prior bugs

## Conclusion

The intermittent sample loss during resharding is caused by unconditionally resetting the `pendingSamples` metric while old queue shards are still in the process of flushing (and potentially timing out and hard-shutting down). The metric reset hides dropped samples, and the shard reassignment during the vulnerable window creates asymmetric load on new shards, causing some to appear stalled. The issue is intermittent because it depends on the timing of target discovery changes relative to ongoing sample processing and remote backend latency.
