# Investigation Report: Remote-Write Queue Resharding Failure

## Summary

The remote-write queue resharding failure is caused by a race condition in shard assignment during the resharding window. When the number of shards changes, samples from the same series can be routed to different shards on retry, violating ordering guarantees and causing some shards to stall with stuck pending samples.

## Root Cause

**Location:** `storage/remote/queue_manager.go` - Shard assignment calculation at line 1315 combined with resharding logic at lines 1184-1199.

**Mechanism:**

The shard assignment uses modulo arithmetic on the series reference:
```go
shard := uint64(ref) % uint64(len(s.queues))  // Line 1315 in enqueue()
```

When resharding occurs, the number of shards changes from N to M. This causes the same series reference to map to different shards:
- Before resharding with 4 shards: series ref=10 → 10 % 4 = shard 2
- After resharding to 6 shards: series ref=10 → 10 % 6 = shard 4

**The Race Window:**

1. `updateShardsLoop()` (lines 1064-1082) detects resharding need
2. Sends desired shard count to `reshardChan` (line 1072)
3. `reshardLoop()` receives this and executes (lines 1184-1199):
   ```go
   case numShards := <-t.reshardChan:
       t.shards.stop()      // Close old shards
       t.shards.start(numShards)  // Create new shards
   ```

4. **Critical race:** Between `stop()` (line 1193) and `start()` (line 1194)
   - Old shards are flushed and closed via `softShutdown` channel (line 1275)
   - Samples in the retry backoff loop (from `Append()` functions) get `enqueue()` returning false (line 1318)
   - These samples sleep with exponential backoff (lines 748-754)
   - While they sleep, new shards are created with different modulo values
   - When they retry, `enqueue()` calculates a different shard number

## Evidence

### Code References

**1. Shard Assignment Bug:**
- File: `storage/remote/queue_manager.go`
- Line 1315: `shard := uint64(ref) % uint64(len(s.queues))`
- When `len(s.queues)` changes (from N to M), same series gets different assignment

**2. Resharding Sequence:**
- File: `storage/remote/queue_manager.go`
- Lines 1184-1199: `reshardLoop()` - sequentially calls stop() then start()
- Line 1193: `t.shards.stop()` - closes softShutdown channel
- Line 1194: `t.shards.start(numShards)` - creates new shards with new modulo base
- **No synchronization between these calls to protect in-flight samples**

**3. softShutdown Channel:**
- File: `storage/remote/queue_manager.go`
- Line 1275: `close(s.softShutdown)` closes in stop()
- Line 1317-1318: enqueue() returns false when softShutdown closed
- Samples in retry loops retry after new shards created with different assignment

**4. Metrics Reset Issue:**
- File: `storage/remote/queue_manager.go`
- Line 1241: `s.qm.metrics.pendingSamples.Set(0)` - reset when start() called
- This occurs while samples may be in flight during retry backoff
- Can cause metric inconsistency and mask the stalled shards

**5. Comments Confirming Ordering Intent:**
- File: `storage/remote/queue_manager.go`
- Lines 1190-1192: Comment states goal is to "guarantee we only ever deliver samples in order"
- Lines 1307-1311: enqueue() documentation says resharding causes retries
- This ordering guarantee is violated by the race condition

### Test Evidence

Test `TestReshard()` (queue_manager_test.go:514-551) explicitly tests resharding but only in controlled conditions without concurrent Append() calls during the stop/start transition.

Test `TestReshardRaceWithStop()` (queue_manager_test.go:553-590) tests race between resharding and Stop(), but not the critical race between stop/start during in-flight sample retry loops.

## Affected Components

1. **`storage/remote/QueueManager`** - Main orchestrator
   - `reshardLoop()` - executes resharding (line 1184)
   - `updateShardsLoop()` - detects when resharding needed (line 1064)
   - `Append()`, `AppendExemplars()`, `AppendHistograms()`, `AppendFloatHistograms()` - entry points that retry on false returns

2. **`storage/remote/shards`** - Queue management
   - `enqueue()` - performs modulo-based shard assignment (line 1315)
   - `start()` - creates new shards, resets metrics (line 1237)
   - `stop()` - gracefully shuts down old shards (line 1269)

3. **`storage/remote/queue`** - Individual shard queues
   - Receives samples assigned via modulo calculation

4. **Metrics** - Monitoring indicators
   - `prometheus_remote_storage_samples_pending` - reset to 0 during start()
   - May show stuck shards with >0 samples that can't progress

## Why The Issue Is Intermittent

The race condition only manifests when **all** of these conditions align:

1. **Resharding is triggered** while the queue has pending work
   - `updateShardsLoop()` periodic check finds desiredShards ≠ numShards (line 1065)
   - `shouldReshard()` returns true (line 1066)

2. **Samples are in-flight during the resharding window** (between stop() and start())
   - Samples in `Append()` retry backoff loop (lines 748-754)
   - Not yet enqueued or enqueued but not yet sent

3. **Timing causes retry to occur after new shards created**
   - Sample sleeps for backoff duration (line 748)
   - During sleep, stop() completes and start() creates new shards
   - On wake, retry calculation with new modulo value

4. **New shard count differs by enough to change modulo results**
   - Resharding from 4→6 shards: 10 % 4 ≠ 10 % 6 (2 ≠ 4)
   - Resharding from 4→8 shards: 10 % 4 ≠ 10 % 8 (2 ≠ 2) - would not trigger in this case

This timing-dependent behavior causes intermittent sample stalling.

## Metrics Showing The Stall

Stalled shards manifest as:
- **`prometheus_remote_storage_samples_pending`** remains stuck at >0
  - Reset to 0 at start() (line 1241) but never decrements for stuck samples
  - Some shards accumulate out-of-order samples that block the shard from progressing

- **`prometheus_remote_storage_enqueued_samples_total`** may show unexpected patterns
  - Samples counted in one shard but not flowing out

- **Logs show incomplete resharding**
  - "Resharding queues" message followed by "Resharding done"
  - But metrics show no progress in affected shards

## Recommendation

### Fix Strategy

Implement one of these approaches:

**Option 1: Prevent In-Flight Sample Rerouting (Recommended)**
- Add a write lock to the resharding sequence that prevents enqueue() during transition
- Modify stop()/start() to coordinate through the QueueManager
- Ensure all in-flight samples either complete with old shards or are drained before new modulo applies

**Option 2: Use Consistent Hashing or Explicit Shard Mapping**
- Instead of modulo assignment, maintain an explicit series→shard mapping
- Mapping persists across resharding until series is explicitly removed
- Requires additional memory but guarantees no rerouting

**Option 3: Drain In-Flight Samples Before Resharding**
- Before calling reshardChan send, wait for all in-flight retries to complete
- Add a mechanism to pause new Append() calls during resharding window
- Ensures no samples are in retry backoff when stop() is called

### Diagnostic Steps

1. **Monitor resharding events:**
   ```
   - Watch for: level=info msg="Remote storage resharding"
   - Timestamp this event
   ```

2. **Correlate with metrics:**
   ```
   - Check prometheus_remote_storage_samples_pending at resharding time
   - Verify it returns to expected levels within batch deadline
   - Look for spikes in specific shards
   ```

3. **Check application logs:**
   ```
   - Search for: "Resharding queues" + "Resharding done"
   - Look for time delta between messages
   - Search for enqueue retry backoff patterns around resharding
   ```

4. **Reproduce the issue:**
   ```
   - Trigger target discovery changes (add/remove targets)
   - Monitor for samples_pending metric
   - If metric stalls >0 after resharding, root cause confirmed
   ```

5. **Validate ordering:**
   ```
   - Monitor remote backend for samples from same series arriving out-of-order
   - Check if samples from same series appear in different time windows
   - Correlate with resharding event timing
   ```

## Impact Assessment

- **Severity:** High - violates ordering guarantees for samples
- **Scope:** Any setup that triggers resharding during active sampling
- **Customer Impact:** Missing or out-of-order metrics after target discovery changes
- **Frequency:** Intermittent, depends on timing alignment
- **Detection:** Metrics show stuck pending samples after resharding

