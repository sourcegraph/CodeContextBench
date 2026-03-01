# Kubernetes Scheduler Architecture: Pod to Node Assignment Pipeline

## Files Examined

### Core Scheduler Components
- `pkg/scheduler/scheduler.go` — Main Scheduler struct; orchestrates the entire scheduling system; manages Cache, SchedulingQueue, Profiles, and event handlers
- `pkg/scheduler/schedule_one.go` — Core scheduling logic; implements the two-phase pipeline (ScheduleOne, schedulingCycle, bindingCycle, schedulePod)
- `pkg/scheduler/eventhandlers.go` — Event handlers for Pod/Node updates; populates SchedulingQueue with pending pods

### Plugin Framework
- `pkg/scheduler/framework/interface.go` — Plugin interfaces (PreFilter, Filter, Score, Reserve, Permit, Bind, PostBind, PostFilter); Framework and Handle interfaces; Status codes
- `pkg/scheduler/framework/cycle_state.go` — CycleState; thread-safe state container for sharing data between plugins during a scheduling cycle
- `pkg/scheduler/framework/runtime/framework.go` — frameworkImpl; orchestrates plugin execution; implements all Run*Plugins methods

### Cache and Queue
- `pkg/scheduler/internal/cache/cache.go` — Scheduler cache; maintains node information and pod assumptions; tracks assumed pods with TTL expiration
- `pkg/scheduler/internal/queue/scheduling_queue.go` — PriorityQueue implementation; manages three sub-queues: activeQ, backoffQ, unschedulablePods

---

## Dependency Chain

### Entry Point: Main Scheduling Loop

1. **Entry**: `pkg/scheduler/scheduler.go:Run()` (line 435)
   - Starts the scheduling queue
   - Spawns goroutine calling `ScheduleOne()` in a loop

2. **Main Loop**: `pkg/scheduler/schedule_one.go:ScheduleOne()` (line 66)
   - Blocks on `sched.NextPod()` which calls `SchedulingQueue.Pop()`
   - Retrieves next pod from queue
   - Calls `sched.frameworkForPod()` to get the appropriate Framework for the pod's scheduler name

### Phase 1: Scheduling Cycle

3. **Scheduling Cycle**: `pkg/scheduler/schedule_one.go:schedulingCycle()` (line 139)
   - Calls `sched.SchedulePod()` (function pointer, default is `sched.schedulePod`)
   - Handles pod filtering and scheduling
   - If successful: calls `sched.assume()` to reserve the pod in cache
   - Runs Reserve plugins via `fwk.RunReservePluginsReserve()`
   - Runs Permit plugins via `fwk.RunPermitPlugins()`
   - Returns `ScheduleResult` with suggested node name
   - If failed: calls `fwk.RunPostFilterPlugins()` for preemption

4. **Pod Scheduling**: `pkg/scheduler/schedule_one.go:schedulePod()` (line 390)
   - Calls `sched.Cache.UpdateSnapshot()` to create snapshot of current node state
   - Calls `sched.findNodesThatFitPod()` to filter nodes via Filter plugins
   - Calls `prioritizeNodes()` to score remaining nodes via Score plugins
   - Calls `selectHost()` to pick best node based on scores
   - Returns `ScheduleResult` with node name

5. **Node Filtering**: `pkg/scheduler/schedule_one.go:findNodesThatFitPod()` (line 442)
   - Runs PreFilter plugins via `fwk.RunPreFilterPlugins()` to optionally reduce node set
   - Filters nodes in parallel via `fwk.RunFilterPlugins()` for each node
   - Collects feasible nodes

6. **Plugin Execution**: `pkg/scheduler/framework/runtime/framework.go`
   - `RunPreFilterPlugins()` (line ~700): executes all registered PreFilter plugins sequentially; returns PreFilterResult to optionally limit node candidates
   - `RunFilterPlugins()` (line ~800): executes Filter plugins in parallel for each node
   - `RunScorePlugins()` (line 1078): executes Score plugins in parallel across all nodes; normalizes scores; applies plugin weights
   - `RunPostFilterPlugins()` (line ~890): executes PostFilter plugins (preemption logic) when no nodes pass filters
   - `RunReservePluginsReserve()`: executes Reserve plugin reserve methods
   - `RunPermitPlugins()`: executes Permit plugins; may return Wait to block binding

### Phase 2: Binding Cycle

7. **Binding Cycle** (async): `pkg/scheduler/schedule_one.go:bindingCycle()` (line 265)
   - Spawned in goroutine from ScheduleOne after schedulingCycle succeeds
   - Calls `fwk.WaitOnPermit()` to unblock if Permit returned Wait
   - Runs PreBind plugins via `fwk.RunPreBindPlugins()`
   - Calls `sched.bind()` to bind the pod to node via Bind plugins
   - Runs PostBind plugins via `fwk.RunPostBindPlugins()` (informational)
   - Calls `sched.SchedulingQueue.Done()` to mark pod as processed
   - If binding fails, calls `handleBindingCycleError()` which calls Unreserve plugins

### Support: Cache and Queue Interactions

8. **Scheduler Cache** (pkg/scheduler/internal/cache/cache.go)
   - `UpdateSnapshot()` (line 185): Creates snapshot of current node information at beginning of scheduling cycle
   - `AssumePod()` (called via sched.assume()): Marks pod as assumed to enable immediate scheduling of subsequent pods
   - `ForgetPod()`: Removes assumed pod if scheduling fails
   - Maintains assumed pod TTL and expires pods after binding
   - Maintains node tree for efficient lookups

9. **Scheduling Queue** (pkg/scheduler/internal/queue/scheduling_queue.go)
   - Three internal queues:
     - `activeQ`: Pods ready to be scheduled (highest priority at head)
     - `backoffQ`: Pods in exponential backoff (completed their backoff go to activeQ)
     - `unschedulablePods`: Pods marked unschedulable; moved to backoffQ on cluster events
   - `Pop()` returns next pod to schedule; blocks if queue empty
   - `AddUnschedulableIfNotPresent()`: Moves failed pods to unschedulablePods
   - `Activate()`: Moves pods from unschedulable/backoff to activeQ
   - Tracks in-flight pods to suppress duplicate event-based requeuing

---

## Detailed Architectural Analysis

### 1. Two-Phase Scheduling Design

The scheduler uses a **two-phase pipeline** to decouple scheduling decisions from actual binding:

**Scheduling Cycle** (synchronous, fast):
- Determines which node is best for the pod
- Creates a "snapshot" of current cluster state
- Runs all filter and scoring logic
- Upon success, "assumes" the pod in cache (optimistic locking)
- Runs Reserve and Permit plugins for additional approval
- Takes ~milliseconds per pod

**Binding Cycle** (asynchronous, can be slower):
- Only runs if scheduling cycle succeeded
- Executes in separate goroutine
- Runs PreBind and Bind plugins
- Persists the pod-to-node binding to API server
- Runs PostBind plugins for cleanup/logging
- Can take seconds due to API calls

This design enables the scheduler to schedule multiple pods in parallel without waiting for API writes.

### 2. Plugin Framework Architecture

The framework implements an **extension point pattern** with 10+ extension points:

```
PreEnqueue → [enter scheduling queue] → QueueSort
            ↓
        [pop from queue]
            ↓
        PreFilter ← PreFilterExtensions (AddPod/RemovePod for affinity calculations)
            ↓
        Filter (in parallel per node)
            ├→ PostFilter (preemption) [if all nodes filtered out]
            └→ PreScore
            ├→ Score (in parallel per node) ← ScoreExtensions (NormalizeScore)
            └→ Reserve
            ├→ Permit (may block)
            ├→ [binding cycle]
            ├→ PreBind
            ├→ Bind
            └→ PostBind
```

**Key Design Patterns**:

1. **Status-driven control flow**: All plugins return Status codes (Success, Unschedulable, Error, Wait, Skip) that determine what runs next
2. **Early termination**: If any plugin rejects, subsequent plugins in that extension point are skipped
3. **Parallelization**: Filter and Score plugins run in parallel across nodes (using Parallelizer with configurable parallelism)
4. **Plugin chaining**: Plugins can read/modify CycleState to share data (e.g., PreFilter computes affinity matrix, Filter plugins use it)
5. **Optional extensions**: Plugins like PreFilter can implement PreFilterExtensions to handle AddPod/RemovePod efficiently
6. **Metric recording**: Each plugin execution is measured; metrics recorder samples 10% of cycles for performance

### 3. CycleState: Plugin Data Sharing

`CycleState` (pkg/scheduler/framework/cycle_state.go) is a thread-safe key-value store that exists for one scheduling cycle:

- Plugins write computed state in early extension points (PreFilter, PreScore)
- Plugins read state in later extension points (Filter, Score)
- Uses `sync.Map` for efficient concurrent read-many/write-once pattern
- Implements `.Clone()` for creating node-specific copies during preemption scenarios
- Stores pod-to-activate list via reserved key `PodsToActivateKey`

### 4. Scheduler Cache: State Management

The cache (pkg/scheduler/internal/cache/cache.go) maintains a consistent view of cluster state:

**Dual Representation**:
- **Active cache** (nodes map + doubly-linked list): All known nodes, sorted by recency
- **Assumed pods** (assumedPods set): Pod keys marked as "assumed" during scheduling

**Snapshot Pattern**:
- At start of each scheduling cycle, `UpdateSnapshot()` creates a snapshot of cache state
- Snapshot is a read-only view of node info used during filtering/scoring
- Snapshot generation number tracks which nodes changed since last snapshot
- Only changed nodes are updated in snapshot (optimization for large clusters)

**Pod Assumption**:
- After scheduler chooses a node but before binding to API server, `assume()` adds pod to cache
- Marked in `assumedPods` set with deadline (TTL configurable, default 0 = no expiration)
- Enables scheduling subsequent pods without waiting for binding
- Prevents re-scheduling same pod multiple times

**Expiration**:
- Assumed pods expire if binding takes too long (handled by background goroutine)
- When pod is actually bound (BindPhase), pod moved from assumed to normal state

### 5. Scheduling Queue: Pod Lifecycle Management

The queue (pkg/scheduler/internal/queue/scheduling_queue.go) implements a priority queue with three sub-queues:

```
Pod Lifecycle:
1. Add() → activeQ [if PreEnqueue passes]
2. Pop() → dequeued from activeQ, marked in-flight
3. AddUnschedulableIfNotPresent() → unschedulablePods [if scheduling failed]
4. [cluster event] → MoveAllToActiveOrBackoffQueue() [e.g., node added]
   ├→ To activeQ [if event might make pod schedulable]
   └→ To backoffQ [if needs backoff (exponential, 1s-10s)]
5. [backoff expires] → activeQ [automatic, managed by background goroutine]
```

**Backoff Strategy**:
- Initial: 1 second (configurable)
- Max: 10 seconds (configurable)
- Exponential increase: doubles on each requeue
- Pods stuck in unschedulable move to backoff after 5 minutes (configurable)

**Event Handling**:
- Tracks which events are "in flight" (occurred while pod was being scheduled)
- After pod Done(), replays in-flight events to determine if pod should be requeued
- Uses plugin EnqueueExtensions for efficient event-to-plugin filtering
- Default: re-enqueue all pods for any cluster event (conservative)
- Optimized: plugins can implement EnqueueExtensions to only requeue on relevant events

### 6. Core Workflows

**Successful Pod Scheduling**:
```
1. ScheduleOne() pops pod from queue
2. schedulingCycle():
   a. UpdateSnapshot() gets current node state
   b. RunPreFilterPlugins() → optionally reduces node set
   c. findNodesThatFitPod() → RunFilterPlugins() in parallel → feasible nodes
   d. prioritizeNodes() → RunScorePlugins() in parallel → scored nodes
   e. selectHost() picks best node
   f. assume() adds pod to cache with node name
   g. RunReservePluginsReserve() → additional approval
   h. RunPermitPlugins() → may block (Wait)
3. bindingCycle() (async in goroutine):
   a. WaitOnPermit() if blocked
   b. RunPreBindPlugins() final checks before binding
   c. bind() creates Pod.Binding to API server via RunBindPlugins()
   d. RunPostBindPlugins() cleanup
   e. Done() marks complete
```

**Failed Pod Scheduling (no feasible nodes)**:
```
1. schedulingCycle() returns FitError
2. RunPostFilterPlugins() e.g., preemption plugin
   - May evict lower-priority pods
   - Returns nominatedNodeName for retry
3. If no PostFilter success:
   - handleSchedulingFailure() called
   - Pod moved to unschedulablePods
   - Pod stays there until cluster event triggers MoveAllToActiveOrBackoffQueue()
```

**Failed Binding**:
```
1. bindingCycle() encounters PreBind or Bind failure
2. handleBindingCycleError():
   a. RunReservePluginsUnreserve() cleanup
   b. Cache.ForgetPod() remove assumption
   c. MoveAllToActiveOrBackoffQueue() requeue pod
   d. FailureHandler() for event recording
```

### 7. Key Design Decisions

| Aspect | Design | Rationale |
|--------|--------|-----------|
| **Snapshot-based filtering** | Immutable snapshot taken once per cycle | Avoids race conditions; deterministic behavior; efficient for large clusters |
| **Parallel filtering/scoring** | Multiple nodes evaluated in parallel | Reduces latency; uses worker pool (parallelism config) |
| **Assume pattern** | Optimistic pod placement; reverted on binding failure | Enables scheduling multiple pods per cycle without serialization |
| **Three-queue design** | activeQ, backoffQ, unschedulablePods | Prevents thundering herd; provides exponential backoff; efficient event handling |
| **Plugin-driven architecture** | Extension points; status-based control flow | Enables customization; decouples core from policies |
| **Async binding** | Binding runs independently after scheduling | Prevents binding latency from blocking subsequent scheduling |
| **CycleState sharing** | Plugins store shared computation in state | Enables efficient incremental updates (PreFilterExtensions) |

---

## Summary

The Kubernetes scheduler is a sophisticated **distributed scheduling system** that implements a **two-phase pipeline** (fast scheduling cycle + asynchronous binding cycle) to efficiently assign Pods to Nodes at scale.

The **plugin framework** provides a flexible extension-point architecture with 10+ decision points (PreFilter, Filter, Score, Reserve, Permit, Bind, PostBind, PostFilter) enabling both core functionality and custom policies.

**Core data structures**—SchedulingQueue (activeQ/backoffQ/unschedulablePods), Cache (assumed pods + node snapshot), and CycleState (per-pod plugin state)—work together to:
- Maintain cluster state efficiently (snapshots, assumed pods)
- Handle pod retries intelligently (exponential backoff, event-driven requeuing)
- Enable parallel scheduling without coordination (optimistic locking via assumptions)
- Support complex placement policies (affinity, preemption, custom plugins)

The architecture prioritizes **scalability** (parallel filtering/scoring, snapshot-based mutations, async binding), **correctness** (status-driven control flow, deterministic snapshots), and **extensibility** (pluggable policies, event-driven requeuing hints).
