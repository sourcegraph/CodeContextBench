# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

The issue is a **race condition and metric tracking loss during queue resharding**. When resharding transitions from N to M shards, buffered samples in old shard queues can be silently dropped without proper metric updates. Additionally, the `pendingSamples` gauge is unconditionally reset to 0 during shard startup, causing loss of tracking for any pending data that was queued but not yet sent to remote storage.

## Root Cause

The root cause involves a **three-part failure** in the resharding mechanism:

### 1. **Unbuffered Samples Lost During Flush Timeout**
**File:** `storage/remote/queue_manager.go`, lines 1447-1454

When `FlushAndShutdown()` is called during resharding:
```go
func (q *queue) FlushAndShutdown(done <-chan struct{}) {
    for q.tryEnqueueingBatch(done) {
        time.Sleep(time.Second)
    }
    q.batchMtx.Lock()
    defer q.batchMtx.Unlock()
    q.batch = nil          // <-- Clears buffered samples WITHOUT sending
    close(q.batchQueue)
}
```

If a timeout occurs in `stop()` and `hardShutdown()` is triggered (line 1293), the `<-done` case in `tryEnqueueingBatch()` at line 1469-1472 receives the signal. This exits the flush loop, and then line 1453 **silently drops** any remaining buffered samples in `q.batch` that weren't sent to the `batchQueue` channel.

These samples are **not decremented from the `pendingSamples` gauge**, causing tracking loss.

### 2. **Metrics Reset Before Old Goroutines Complete**
**File:** `storage/remote/queue_manager.go`, lines 1184-1199 and 1237-1266

In `reshardLoop()`:
```go
func (t *QueueManager) reshardLoop() {
    for {
        select {
        case numShards := <-t.reshardChan:
            t.shards.stop()        // Line 1193
            t.shards.start(numShards)  // Line 1194
        case <-t.quit:
            return
        }
    }
}
```

And in `start()`:
```go
func (s *shards) start(n int) {
    s.mtx.Lock()
    defer s.mtx.Unlock()

    s.qm.metrics.pendingSamples.Set(0)  // <-- Line 1241: UNCONDITIONALLY RESETS
    s.qm.metrics.numShards.Set(float64(n))

    newQueues := make([]*queue, n)
    // ... create new queues ...

    s.done = make(chan struct{})   // <-- Line 1255: RECREATES done CHANNEL
    s.enqueuedSamples.Store(0)      // <-- Line 1256: RESETS COUNTERS

    for i := range n {
        go s.runShard(hardShutdownCtx, i, newQueues[i])  // Line 1264
    }
}
```

**The Race Condition:**
1. `stop()` closes `softShutdown`, waits for flushes, then calls `hardShutdown()` if timeout occurs
2. Old `runShard()` goroutines receive `<-ctx.Done()` signal and begin cleanup at lines 1563-1577:
   ```go
   case <-ctx.Done():
       droppedSamples := int(s.enqueuedSamples.Load())
       s.qm.metrics.pendingSamples.Sub(float64(droppedSamples))
       s.samplesDroppedOnHardShutdown.Add(uint32(droppedSamples))
       return
   ```
3. **MEANWHILE**, `start()` is called and executes line 1241:
   ```go
   s.qm.metrics.pendingSamples.Set(0)  // Overwrites any tracking!
   ```
4. The `done` channel is also recreated at line 1255, so the old `runShard()` goroutines' signal to close `s.done` (line 1494) goes to the old channel instead of the new one

### 3. **No Safeguard Against Early Metric Reset**
**File:** `storage/remote/queue_manager.go`, line 1241

The `start()` function unconditionally resets `pendingSamples` to 0 without verifying that:
- All old shard goroutines have completed
- All buffered data has been accounted for in metrics
- No samples are in flight during the transition

This causes **silent loss of pending sample tracking** during the transition window.

## Evidence

### Code References

1. **Metric Reset Without Synchronization**
   - Location: `storage/remote/queue_manager.go:1241`
   - Issue: `s.qm.metrics.pendingSamples.Set(0)` is called unconditionally when starting new shards
   - Impact: Any pending samples from old shards that couldn't be flushed are lost from tracking

2. **Buffered Samples Dropped Without Metric Update**
   - Location: `storage/remote/queue_manager.go:1447-1454`
   - Issue: `q.batch = nil` clears samples without decrementing metrics
   - Impact: Samples in partial batches are silently dropped during hard shutdown

3. **Unsynchronized Channel Replacement**
   - Location: `storage/remote/queue_manager.go:1255` and `1493-1495`
   - Issue: `s.done` is recreated in `start()` while old `runShard()` goroutines still reference it
   - Impact: Cleanup signals from old shards are sent to the wrong channel

4. **Race Condition Window**
   - Location: `storage/remote/queue_manager.go:1184-1199`
   - Issue: `stop()` followed immediately by `start()` with no synchronization barrier
   - Impact: Old goroutines may still be running metrics updates while new shards initialize

### Timing Diagram

```
Time →

updateShardsLoop (every 10s):
  Calculates desired shards
  Sends to reshardChan
  Updates t.numShards (metadata only)
                    │
                    ▼
reshardLoop:
  Receives from reshardChan
  Calls t.shards.stop()
    ├─ Closes softShutdown
    ├─ Spawns FlushAndShutdown goroutines
    ├─ Waits up to flushDeadline
    └─ If timeout: calls hardShutdown() → cancels context
          │
          ├─ Old runShard() goroutines see <-ctx.Done()
          │   and call metrics.pendingSamples.Sub()
          │   [Race condition here]
          │
  Calls t.shards.start()
    ├─ Takes write lock
    ├─ Calls pendingSamples.Set(0)  ◄─── OVERWRITES old runShard()'s updates!
    ├─ Recreates s.done channel      ◄─── Old runShard()'s signal lost!
    ├─ Spawns new runShard() goroutines
    └─ Releases lock
          │
          ▼ [Optional: old runShard() finally decrements pendingSamples, goes negative or 0]
```

## Affected Components

1. **Queue Manager** (`storage/remote/queue_manager.go`)
   - `reshardLoop()` - initiates resharding without synchronization
   - `start()` - resets metrics unconditionally
   - `stop()` - doesn't guarantee complete metric accounting before returning

2. **Queue and Shard Management** (`storage/remote/queue_manager.go`)
   - `shards.enqueue()` - unable to route samples if channels are mid-transition
   - `queue.FlushAndShutdown()` - loses buffered samples without tracking
   - `runShard()` - may have metrics decremented after parent metrics are reset

3. **Metrics** (`storage/remote/queue_manager.go`)
   - `pendingSamples` gauge - unconditionally reset
   - `enqueuedSamples` counter - reset without coordination
   - `done` channel - recreated while old goroutines reference it

## Why This Is Intermittent

The issue is intermittent because it **only occurs when**:

1. **Resharding Coincides with Data Backlog**: If there are buffered samples in old queue partials when resharding happens
2. **Flush Timeout Occurs**: The `flushDeadline` (default behavior) is exceeded during `stop()`, triggering `hardShutdown()`
3. **Timing Alignment**: Old `runShard()` goroutines are still running when `start()` resets metrics (tight timing race)
4. **Target Discovery Changes**: The combination of target changes + incoming samples creates a scenario where the old shard partial batches can't flush quickly enough

When resharding happens without backlog or with quick flushes, samples are sent successfully and the race doesn't manifest.

## Recommendation

### Fix Strategy

**Option 1: Synchronize Metric Updates** (Recommended)
- Ensure all old `runShard()` goroutines have completed and their metrics updates are finalized before `start()` resets metrics
- Add a sync barrier or atomic coordination between `stop()` completion and `start()` initialization
- Track the number of pending samples that will be lost and decrement them explicitly before resetting

**Option 2: Properly Flush Buffered Samples**
- In `FlushAndShutdown()`, when hard shutdown occurs, ensure buffered samples in `q.batch` are accounted for in failed metrics before clearing
- Decrement `pendingSamples` by the number of buffered samples being dropped

**Option 3: Avoid Unconditional Reset**
- Instead of `pendingSamples.Set(0)`, track the actual pending count from old shards and properly transition it to new shards
- Add a temporary counter during resharding to account for samples in flight

### Diagnostic Steps

**To Confirm Root Cause:**

1. **Enable Debug Logging** in `updateShardsLoop()` and `reshardLoop()` to capture:
   - Timestamp of resharding start/end
   - `pendingSamples` value before and after `start()`
   - Number of samples dropped during hard shutdown

2. **Monitor These Metrics:**
   - `prometheus_remote_storage_samples_pending` - should return to 0 or decrease monotonically
   - `prometheus_remote_storage_samples_dropped_total` - should increase if samples are lost
   - Compare with `prometheus_remote_storage_samples_total` to detect gaps

3. **Check Logs for:**
   - "Remote storage resharding" messages
   - "Currently resharding, skipping" messages (indicates back-to-back reshards)
   - Error messages about flushing samples
   - Warnings about skipping resharding due to recent errors

4. **Add Validation:**
   - Before `start()`, verify all old `runShard()` goroutines have exited (check `s.running` atomic)
   - Assert that `s.enqueuedSamples` matches the samples accounted for in metrics
   - Verify no writes to metrics occur after `start()` resets them

### Code Location Reference

- **Resharding Logic:** `storage/remote/queue_manager.go:1184-1199`
- **Metric Reset:** `storage/remote/queue_manager.go:1237-1266` (specifically line 1241)
- **Flush Logic:** `storage/remote/queue_manager.go:1268-1305` and `1447-1477`
- **Shard Goroutine Cleanup:** `storage/remote/queue_manager.go:1491-1602` (specifically lines 1563-1577)
