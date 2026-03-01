# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

The root cause is a **metric state loss bug during queue resharding transitions**. When resharding occurs, the `start()` method unconditionally resets pending sample counters (`pendingSamples.Set(0)`) BEFORE all samples from the previous shard generation have been properly accounted for. Combined with a timing race condition where samples can be enqueued during the soft-shutdown window, metrics become desynchronized from actual queue state, causing "stuck" pending sample counts.

## Root Cause

**File:** `storage/remote/queue_manager.go`
**Function:** `shards.start()` (lines 1237-1266)
**Specific Issue:** Line 1241 unconditionally resets the pending samples metric

```go
func (s *shards) start(n int) {
	s.mtx.Lock()
	defer s.mtx.Unlock()

	s.qm.metrics.pendingSamples.Set(0)  // ← BUG: Unconditional reset
	s.qm.metrics.numShards.Set(float64(n))
	...
	s.queues = newQueues
	...
	s.enqueuedSamples.Store(0)
	...
}
```

The corresponding `stop()` method (lines 1269-1305) has a critical synchronization window:

1. **Line 1274-1276:** Takes RLock, closes `softShutdown` channel, releases lock
2. **Line 1281-1290:** Takes write Lock, flushes queues, waits for completion with `flushDeadline`
3. **Line 1293:** If deadline expires, calls `hardShutdown()` to cancel context

## Evidence

### The Race Condition Mechanism

**In `stop()` method (lines 1269-1290):**
- After closing `softShutdown` (line 1275) and releasing RLock
- Before taking the write Lock (line 1281)
- **There exists a window where new samples can still be enqueued**
- The enqueue check happens AFTER reading `len(s.queues)` but samples can increment counters

**In `enqueue()` method (lines 1312-1333):**
```go
func (s *shards) enqueue(ref chunks.HeadSeriesRef, data timeSeries) bool {
	s.mtx.RLock()
	defer s.mtx.RUnlock()
	shard := uint64(ref) % uint64(len(s.queues))
	select {
	case <-s.softShutdown:
		return false  // ← Should block new samples
	default:
		appended := s.queues[shard].Append(data)
		if !appended {
			return false
		}
		switch data.sType {
		case tSample:
			s.qm.metrics.pendingSamples.Inc()  // ← Counter increased
```

### Metric Tracking Desynchronization

**In `runShard()` hard shutdown path (lines 1561-1578):**
```go
case <-ctx.Done():
	// Hard shutdown drops remaining samples
	droppedSamples := int(s.enqueuedSamples.Load())
	...
	s.qm.metrics.pendingSamples.Sub(float64(droppedSamples))  // ← Decremented here
	...
	return
```

**Problem:** When `start()` is called immediately after `stop()` completes:
- Line 1241: `s.qm.metrics.pendingSamples.Set(0)` unconditionally resets the gauge
- If any runShard is still in the process of calling `updateMetrics()` from a concurrent send
- The in-flight decrement is lost when the gauge is forcefully set to 0
- New samples arriving during resharding bypass the old queue state tracking

### The Intermittent Nature

The issue is intermittent because it only manifests when:
1. **Target discovery changes** occur simultaneously with active writes
2. **Resharding is triggered** by load changes
3. **Flush deadline is tight** (default may vary), causing hard shutdown invocation
4. **Timing aligns** such that:
   - Some shards complete flushing within deadline
   - Others timeout and are hard-shutdown
   - `updateMetrics()` calls are in-flight when `start()` resets counters
   - New samples are enqueued to replace old samples in the routing calculation

## Affected Components

1. **`storage/remote/queue_manager.go:shards struct`** (lines 1209-1234)
   - Holds mutable queue references and atomic counters
   - Single `enqueuedSamples` counter per shard generation

2. **`storage/remote/queue_manager.go:reshardLoop()`** (lines 1184-1199)
   - Orchestrates the stop/start cycle
   - No synchronization between stop() completion and start() metrics reset

3. **`storage/remote/queue_manager.go:updateMetrics()`** (lines 1661-1695)
   - Called asynchronously from runShard goroutines
   - Decrements `pendingSamples` without holding locks
   - Can race with `start()` calling `Set(0)`

4. **Metrics affected:**
   - `prometheus_remote_storage_samples_pending` (pendingSamples gauge)
   - `prometheus_remote_storage_exemplars_pending` (pendingExemplars gauge)
   - `prometheus_remote_storage_histograms_pending` (pendingHistograms gauge)

## Why It Happens During Target Discovery Changes

When targets are added/removed:
1. The number of series changes
2. Series IDs/refs are reassigned
3. New refs hash to different shards: `shard = uint64(ref) % uint64(len(s.queues))`
4. Before resharding: ref 5 → shard 1 (in 4-shard setup)
5. After resharding: ref 5 → shard 5 (in 6-shard setup)
6. Samples "move" between shards logically, but queues are replaced
7. If resharding occurs during this transition, tracking can be lost

## Recommendation

### Fix Strategy

The root cause should be fixed by:
1. **Option A (Atomic):** Replace `Set(0)` with `Sub(pendingSamples.Load())` to preserve any in-flight metrics updates
2. **Option B (Synchronized):** Hold the write lock during the entire flush period to prevent enqueue races
3. **Option C (Tracked):** Accumulate dropped samples during hard shutdown and verify the count before resetting

### Diagnostic Steps to Confirm

1. **Enable debug logging** for resharding:
   ```
   level=debug msg="Resharding queues"
   level=debug msg="QueueManager.calculateDesiredShards"
   ```

2. **Watch for this pattern:**
   - `level=info msg="Remote storage resharding" from=X to=Y`
   - Followed by `level=info msg="Currently resharding, skipping."` (indicates back-to-back reshards)
   - Followed by metrics showing `samples_pending > 0` with `samples_dropped_total` not incrementing

3. **Check for timeouts:**
   - Look for absence of `level=debug msg="runShard timer ticked, sending buffered data"` on specific shards
   - This indicates shards not processing queues after resharding

4. **Metric anomaly detection:**
   - Query: `delta(prometheus_remote_storage_samples_pending[5m]) != delta(prometheus_remote_storage_samples_dropped_total[5m])`
   - If true, samples are "disappearing" without being counted as dropped

5. **Log correlation:**
   - Match timestamps of `"Remote storage resharding"` messages
   - Look for concurrent `"Failed to flush all samples on shutdown"` errors
   - Cross-reference with target discovery changes in Prometheus logs

### Verification

The bug is confirmed if:
- `prometheus_remote_storage_samples_pending` remains > 0 after a reshard
- No corresponding increase in `prometheus_remote_storage_samples_dropped_total`
- The metric value eventually decreases only when new targets/samples arrive (forcing the queue forward)
- Hard shutdown timeout logs are present in the same time window
