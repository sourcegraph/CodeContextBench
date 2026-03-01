# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

The remote-write queue resharding mechanism has a race condition where partial batches can be silently dropped during the flush-and-shutdown phase, while their sample counts remain recorded in the `enqueuedSamples` counter. When new shards are started, this counter is reset to zero instead of being properly reconciled, leaving `prometheus_remote_storage_samples_pending` metric in a stalled state showing samples that were actually lost.

## Root Cause

**Location:** `storage/remote/queue_manager.go`

**Mechanism:** Three interacting functions create a window where samples are lost but metrics are not properly updated:

### 1. Resharding Orchestration (`reshardLoop`, line 1184-1199)
```go
func (t *QueueManager) reshardLoop() {
    defer t.wg.Done()
    for {
        select {
        case numShards := <-t.reshardChan:
            t.shards.stop()      // Line 1193: Wait for flush
            t.shards.start(numShards)  // Line 1194: Start new shards
```

The reshardLoop calls `stop()` to cleanly flush all queues before starting new shards.

### 2. Incomplete Flush on Shutdown (`queue.FlushAndShutdown`, lines 1447-1455)
```go
func (q *queue) FlushAndShutdown(done <-chan struct{}) {
    for q.tryEnqueueingBatch(done) {
        time.Sleep(time.Second)  // Line 1449
    }
    q.batchMtx.Lock()
    defer q.batchMtx.Unlock()
    q.batch = nil              // Line 1453: DISCARDS PARTIAL BATCH
    close(q.batchQueue)        // Line 1454
}
```

The `FlushAndShutdown()` method tries to enqueue the partial batch but will silently discard it if:
- The `batchQueue` channel remains full (no receiver draining it)
- Hard shutdown is triggered via `<-done` before the batch is sent

### 3. Metric Counter Reset (`shards.start`, lines 1256-1258)
```go
func (s *shards) start(n int) {
    s.mtx.Lock()
    defer s.mtx.Unlock()
    // ... create new queues ...
    s.enqueuedSamples.Store(0)      // Line 1256: RESET, NOT DECREMENT
    s.enqueuedExemplars.Store(0)    // Line 1257
    s.enqueuedHistograms.Store(0)   // Line 1258
```

The new shards reset the enqueued sample counters to zero without accounting for samples lost from old shards.

## Evidence

### Code References

1. **Sample Enqueuing** (`queue_manager.go:1312-1340` - `enqueue()` function):
   - Line 1326: `s.qm.metrics.pendingSamples.Inc()` - increments when sample queued
   - Line 1315: `shard := uint64(ref) % uint64(len(s.queues))` - calculates destination shard

2. **Metric Decrement on Send** (`queue_manager.go:1689` - `updateMetrics()` function):
   ```go
   s.qm.metrics.pendingSamples.Sub(float64(sampleCount))  // Only called on successful send
   ```

3. **Flush Attempt** (`queue_manager.go:1459-1476` - `tryEnqueueingBatch()`):
   - Line 1462-1463: Returns false if batch is empty
   - Line 1467-1468: Returns false if batch successfully enqueued
   - Line 1469-1472: Returns false if hard shutdown signal received
   - Line 1475: Returns true (needs retry) only if `batchQueue` is full

4. **Hard Shutdown Timing** (`queue_manager.go:1286-1294` - `stop()` function):
   ```go
   select {
   case <-s.done:
       return
   case <-time.After(s.qm.flushDeadline):  // Default: 1 minute
   }
   // Force an unclean shutdown.
   s.hardShutdown()  // Cancels context, triggering runShard to exit
   <-s.done
   ```

## Race Condition Scenario

```
Timeline:
1. [updateShardsLoop] Detects need to reshard from 4→6 shards
2. [updateShardsLoop] Sends desiredShards to reshardChan
3. [reshardLoop] Receives from reshardChan, calls shards.stop()
4. [stop] Closes softShutdown, causing all active enqueue() calls to fail and retry
5. [stop] Takes Lock (waiting for all enqueue RLocks to release)
6. [stop] Launches FlushAndShutdown goroutines for each queue
7. [queue.FlushAndShutdown] Tries to send partial batch:
   - If batchQueue is full: tryEnqueueingBatch returns true, sleeps 1 second
   - Meanwhile, runShard might be stuck in sendBatch() (network latency, slow endpoint)
   - batchQueue channel remains full
8. [stop] Timeout of flushDeadline (default 1 minute) expires
9. [stop] Calls s.hardShutdown() canceling context
10. [runShard] Receives ctx.Done():
    - Calculates droppedSamples = enqueuedSamples.Load()
    - Subtracts from pendingSamples
    - But enqueuedSamples already reflects OLD samples plus NEW samples enqueued during transition
11. [stop] Returns
12. [reshardLoop] Calls shards.start()
13. [start] Resets enqueuedSamples.Store(0) - LOSES ACCOUNTING OF LOST SAMPLES
14. [start] Creates new empty shards
15. New samples arrive and get queued
    - But pendingSamples metric is now inconsistent with actual queued data
```

## Intermittency Analysis

The issue is **intermittent** because it depends on timing:

1. **Condition A - Flush Timeout**: The hard shutdown must trigger (flushDeadline expires) rather than completing gracefully. This happens when:
   - Remote endpoint is slow/unresponsive
   - Network congestion during send attempts
   - batchQueue remains full because runShard can't drain it fast enough

2. **Condition B - Concurrent Traffic**: New samples must arrive during the transition window. If target discovery changes (adds/removes targets) and generates many new samples during resharding, enqueuers are blocked by softShutdown being closed, increasing the chance of partial batches being discarded.

3. **Condition C - Partial Batch Exists**: A partial batch must exist (not yet full) at the moment resharding is initiated.

All three conditions must align for the metric to stall.

## Affected Components

- **`storage/remote/queue_manager.go`**:
  - `QueueManager.reshardLoop()` - orchestrates reshard cycle
  - `shards.stop()` - manages graceful shutdown with timeout
  - `shards.start()` - initializes new shards, RESETS counters
  - `queue.FlushAndShutdown()` - incomplete batch handling
  - `shards.enqueue()` - adds to pendingSamples counter

- **Metrics**:
  - `prometheus_remote_storage_samples_pending` - stalled reporting
  - `prometheus_remote_storage_pendingSamples` - internal counter (may show overflow)

## Recommendation

### Root Fix Strategy

The core issue is that `shards.start()` uses `.Store(0)` to reset the enqueued sample counters instead of decrementing them:

```go
// CURRENT (WRONG):
s.enqueuedSamples.Store(0)

// SHOULD BE:
oldSamples := s.enqueuedSamples.Load()
if oldSamples > 0 {
    s.qm.metrics.pendingSamples.Sub(float64(oldSamples))
}
s.enqueuedSamples.Store(0)
```

Additionally, `queue.FlushAndShutdown()` should guarantee sending the partial batch or explicitly dropping it while updating metrics:

```go
// After the flush retry loop, if batch still exists:
if len(q.batch) > 0 {
    // Log dropped samples
    s.qm.metrics.pendingSamples.Sub(float64(len(q.batch)))
    s.enqueuedSamples.Sub(int64(len(q.batch)))
}
q.batch = nil
```

### Diagnostic Steps

1. **Enable debug logging** for reshard operations:
   ```
   Storage/remote: set log level to DEBUG
   Watch for: "Resharding queues" and "Resharding done" messages
   Check timing between resharding start and completion
   ```

2. **Monitor these metrics during target discovery changes**:
   ```
   prometheus_remote_storage_samples_pending  # Should return to 0 after reshard
   prometheus_remote_storage_shards           # Verify shard count changed
   prometheus_remote_storage_sent_bytes_total # Should increase continuously
   prometheus_remote_storage_failed_samples_total  # Watch for drops
   ```

3. **Confirm the diagnosis**:
   - Track `pendingSamples` before resharding
   - Observe if it stops decreasing after "Resharding done"
   - Check if `failed_samples_total` increases (should be logged if >0 samples dropped)
   - Compare `sent_bytes_total` rate before/after reshard (should remain steady)

4. **Network/Endpoint health**:
   - During resharding, monitor remote endpoint response times
   - Check if endpoint becomes unavailable briefly
   - Review `prometheus_remote_storage_slow_requests` (if available)
   - Slow endpoint triggers timeout → hard shutdown → metric loss

## Additional Notes

- The default `flushDeadline` is typically 1 minute (configurable)
- If resharding happens frequently with high throughput, probability of partial batch loss increases
- The issue correlates with target discovery changes because they trigger resharding AND may generate sample spikes
- Samples aren't actually lost from remote storage if they were already sent before the reshard; only in-flight/queued samples are affected
