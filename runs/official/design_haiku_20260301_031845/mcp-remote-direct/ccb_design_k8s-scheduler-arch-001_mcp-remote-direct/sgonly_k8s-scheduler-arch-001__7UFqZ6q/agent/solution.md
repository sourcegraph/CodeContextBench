# Kubernetes Scheduler Architecture Analysis

## Overview

The Kubernetes scheduler is responsible for assigning unscheduled Pods to Nodes. It follows a two-phase design: a **scheduling cycle** that evaluates and selects a node, and a **binding cycle** that commits the pod assignment. The scheduler uses an extensible **plugin framework** that allows both in-tree and out-of-tree plugins to participate in scheduling decisions at well-defined extension points.

---

## Files Examined

### Core Scheduler Files
- **pkg/scheduler/scheduler.go** — Main `Scheduler` struct containing queue, cache, framework profiles, and initialization logic; implements `New()` and `Run()` entry points
- **pkg/scheduler/schedule_one.go** — Main scheduling loop (`ScheduleOne()`) and orchestration of scheduling/binding cycles (`schedulingCycle()`, `bindingCycle()`)

### Framework & Plugin Infrastructure
- **pkg/scheduler/framework/interface.go** — Defines all plugin interfaces (PreEnqueue, QueueSort, PreFilter, Filter, PostFilter, PreScore, Score, Reserve, Permit, PreBind, Bind, PostBind), `Framework`, `Handle`, and `Status` types
- **pkg/scheduler/framework/cycle_state.go** — `CycleState` struct for plugin state management across a scheduling cycle using thread-safe storage
- **pkg/scheduler/framework/runtime/framework.go** — `frameworkImpl` implementing the `Framework` interface; manages plugin registration and execution

### Scheduling Queue & Cache
- **pkg/scheduler/internal/queue/scheduling_queue.go** — `PriorityQueue` implementation with three sub-queues: activeQ, backoffQ, unschedulablePods
- **pkg/scheduler/internal/cache/cache.go** — `cacheImpl` maintaining node information, tracking assumed pods, and managing cache assumptions
- **pkg/scheduler/internal/cache/node_tree.go** — Tree structure for efficient node lookup
- **pkg/scheduler/internal/cache/snapshot.go** — Immutable snapshot of cache taken at scheduling cycle start

### Event Handling & Extenders
- **pkg/scheduler/eventhandlers.go** — Event handlers for pod/node/storage class updates triggering queue requeuing
- **pkg/scheduler/extender.go** — HTTP-based external scheduler extender interface

---

## Dependency Chain

### 1. **Entry Point: Scheduler Initialization & Run**
   - **`scheduler.New(ctx, client, informerFactory, ...)`** (pkg/scheduler/scheduler.go:253)
     - Creates in-tree plugin registry
     - Builds scheduler profiles and framework instances
     - Initializes scheduling queue (PriorityQueue)
     - Initializes scheduler cache
     - Registers event handlers for pods/nodes
     - Returns `*Scheduler` instance

   - **`sched.Run(ctx)`** (pkg/scheduler/scheduler.go:435)
     - Starts scheduling queue goroutines
     - Launches main scheduling loop via `wait.UntilWithContext(ctx, sched.ScheduleOne, 0)`

### 2. **Main Scheduling Loop**
   - **`sched.ScheduleOne(ctx)`** (pkg/scheduler/schedule_one.go:66)
     - Calls `sched.NextPod(logger)` → pops from `SchedulingQueue`
     - Retrieves framework for pod's scheduler name
     - Calls **`sched.schedulingCycle(ctx, state, fwk, podInfo, start, podsToActivate)`** (line 111)
     - On success, launches binding cycle in goroutine

### 3. **Scheduling Cycle (Pod Selection)**
   - **`schedulingCycle()`** (pkg/scheduler/schedule_one.go:139)
     1. Calls **`sched.SchedulePod(ctx, fwk, state, pod)`** → **`sched.schedulePod()`** (line 390)
        - Updates cache snapshot via `sched.Cache.UpdateSnapshot()`
        - **Phase A: Filtering**
          - Calls `sched.findNodesThatFitPod(ctx, fwk, state, pod)`
          - Runs **PreFilter plugins** via `fwk.RunPreFilterPlugins()` (line 453)
          - Calls **`findNodesThatPassFilters()`** (line 573)
            - Runs **Filter plugins** in parallel via `fwk.Parallelizer().Until()` (line 640)
            - Calls `fwk.RunFilterPluginsWithNominatedPods(ctx, state, pod, nodeInfo)` per node
          - Processes extender filters via `findNodesThatPassExtenders()`
        - **Phase B: Scoring**
          - Calls **`prioritizeNodes()`** (line 425)
          - Runs **PreScore plugins** via `fwk.RunPreScorePlugins()`
          - Runs **Score plugins** on each feasible node via `fwk.RunScorePlugins()`
          - Scores with extenders (if present)
        - **Phase C: Selection**
          - Calls `selectHost()` to pick best-scored node

     2. On success, **assumes pod** via `sched.assume(logger, assumedPod, nodeName)` (line 198)
        - Adds pod to cache with assumed state

     3. Runs **Reserve plugins** via `fwk.RunReservePluginsReserve()` (line 209)
        - If fails, calls `fwk.RunReservePluginsUnreserve()` and `sched.Cache.ForgetPod()`

     4. Runs **Permit plugins** via `fwk.RunPermitPlugins()` (line 231)
        - Creates waiting pods if any plugin returns "Wait"

### 4. **Binding Cycle (Pod Commitment)**
   - **`bindingCycle()`** (pkg/scheduler/schedule_one.go:265)
     1. Waits on **Permit plugins** via `fwk.WaitOnPermit()` (line 278)

     2. Runs **PreBind plugins** via `fwk.RunPreBindPlugins()` (line 294)
        - Performs pre-binding validation (e.g., PVC checks)

     3. Runs **Bind plugins** via `sched.bind()` (line 299)
        - Default: calls API server to create Pod binding
        - Can be overridden by custom bind plugins

     4. Runs **PostBind plugins** via `fwk.RunPostBindPlugins()` (line 312)
        - Informational, performs cleanup/logging

---

## Architecture Analysis

### Design Patterns

#### 1. **Plugin Framework Architecture**
The scheduler uses an **extension point** pattern where plugins implement specific interfaces and hook into well-defined points in the scheduling pipeline:

```
Extension Points (in execution order):
├─ PreEnqueue (before pod enters activeQ)
├─ QueueSort (sorts pods in queue)
├─ PreFilter (pod-level filtering setup, can filter out nodes)
├─ Filter (per-node filtering, parallel execution)
├─ PostFilter (preemption/recovery if no nodes fit)
├─ PreScore (informational, after filtering)
├─ Score (per-node scoring, parallel execution)
├─ Reserve (mark node as having resources reserved)
├─ Permit (final gate before binding, can wait)
├─ PreBind (validation before binding)
├─ Bind (performs actual binding)
└─ PostBind (post-binding cleanup)
```

#### 2. **Two-Phase Scheduling Design**
- **Scheduling Cycle** (synchronous): Evaluates pods/nodes, makes scheduling decision
- **Binding Cycle** (asynchronous): Commits binding to API server without blocking other scheduling

This enables the scheduler to continue scheduling other pods while binding happens asynchronously.

#### 3. **State Isolation via CycleState**
Each scheduling cycle creates a fresh `CycleState` that plugins use to store temporary data:
- Thread-safe storage using `sync.Map`
- Plugins write computed state in PreFilter/PreScore
- Other plugins read this state in Filter/Score
- Allows plugins to share information without direct coupling

#### 4. **Assume-Release Pattern**
Before binding completes, the pod is "assumed" in the cache:
- Updates cache immediately after successful Reserve phase
- Allows next scheduling cycle to see "reserved" resources
- If binding fails later, cache is updated via `ForgetPod()`
- Prevents scheduling multiple pods to same space

#### 5. **Queue-based Requeuing**
Pods move through queue states based on scheduling outcome:
```
Pod States in Queue:
├─ activeQ: Ready to be scheduled
├─ backoffQ: Unschedulable but will retry after backoff
└─ unschedulablePods: Unschedulable, stays until cluster event triggers requeue
```

#### 6. **Snapshot Isolation**
Cache snapshot taken at cycle start ensures consistent view throughout filtering/scoring:
- Prevents race conditions between cycle phases
- Snapshot remains unchanged during Permit phase
- Binding cycle may see different cluster state (acceptable)

### Component Responsibilities

#### **Scheduler (pkg/scheduler/scheduler.go)**
- Orchestrates overall scheduling workflow
- Maintains cache and queue
- Manages framework profiles (supports multiple scheduler instances)
- Registers event handlers to respond to cluster changes

#### **Framework (pkg/scheduler/framework/runtime/framework.go)**
- Loads and initializes plugins
- Routes scheduling requests through plugin extension points
- Manages plugin execution (sequential or parallel)
- Provides Handle interface for plugins to access cluster state

#### **SchedulingQueue (pkg/scheduler/internal/queue/scheduling_queue.go)**
- Maintains pod queues with priority
- Moves pods between queues based on scheduling outcomes
- Integrates with plugins for event-driven requeuing
- Supports backoff for failed pods

#### **Cache (pkg/scheduler/internal/cache/cache.go)**
- Maintains node information (CPU, memory, pods)
- Tracks assumed pods with configurable TTL
- Provides snapshots for consistent scheduling cycles
- Expires long-lived assumptions automatically

#### **Plugins (via plugin interfaces in framework/interface.go)**
- **PreFilter/Filter**: Determine node feasibility
- **Score**: Rank feasible nodes
- **Reserve/Permit**: Gate decisions before binding
- **Bind/PreBind/PostBind**: Manage binding lifecycle
- **PostFilter**: Implement preemption or recovery logic

### Data Flow

#### **Scheduling Cycle Data Flow**
```
Pod from Queue
    ↓
[CycleState created]
    ↓
[Cache Snapshot taken]
    ↓
RunPreFilterPlugins() ← Plugins can exclude entire node sets
    ↓
RunFilterPlugins() on each node (parallel) ← Per-node feasibility
    ↓
[Feasible nodes list]
    ↓
RunPreScorePlugins() ← Informational, prepare scoring state
    ↓
RunScorePlugins() on feasible nodes (parallel) ← Rank nodes
    ↓
selectHost() ← Pick highest-scored node
    ↓
Cache.AssumedPodAdded() ← Reserve resources in cache
    ↓
RunReservePlugins() ← Plugins update internal state
    ↓
RunPermitPlugins() ← Final gate (can wait)
    ↓
Return: Success → Launch Binding Cycle
```

#### **Binding Cycle Data Flow**
```
[From Scheduling Cycle: Assumed Pod Info]
    ↓
WaitOnPermit() ← Block if Permit returned "Wait"
    ↓
RunPreBindPlugins() ← Validation (e.g., PVC checks)
    ↓
RunBindPlugins() ← Commit to API server
    ↓
RunPostBindPlugins() ← Cleanup/logging
    ↓
Queue.Done() ← Mark pod processing complete
    ↓
Success: Pod bound to node
```

### Interface Contracts

#### **Plugin Interface (framework/interface.go:329)**
All plugins must implement:
```go
type Plugin interface {
    Name() string
}
```

#### **Extension Point Interfaces**
- **PreFilterPlugin** → `PreFilter(ctx, state, pod) (*PreFilterResult, *Status)`
- **FilterPlugin** → `Filter(ctx, state, pod, nodeInfo) *Status`
- **ScorePlugin** → `Score(ctx, state, pod, nodeName) (int64, *Status)`
- **ReservePlugin** → `Reserve(ctx, state, pod, nodeName) *Status`
- **PermitPlugin** → `Permit(ctx, state, pod, nodeName) (*Status, time.Duration)`
- **BindPlugin** → `Bind(ctx, state, pod, nodeName) *Status`

#### **Status Codes**
- `Success` (nil): Operation succeeded
- `Unschedulable`: Pod doesn't fit (might succeed after preemption)
- `UnschedulableAndUnresolvable`: Pod doesn't fit (preemption won't help)
- `Wait`: Permit plugin wants to wait before binding
- `Error`: Unexpected failure
- `Pending`: Scheduling succeeded but waiting for external action

#### **Framework Handle Interface (framework/interface.go:663)**
Plugins receive `Handle` providing:
- `SnapshotSharedLister()` → Access to node/pod cache snapshots
- `ClientSet()` → Kubernetes client
- `EventRecorder()` → Record events
- Waiting pod management
- Pod nominator for preemption hints

### Queue Integration

#### **Scheduling Queue States**
- **activeQ**: Heap of pods ready to schedule, sorted by priority
- **backoffQ**: Pods that failed and are backing off
- **unschedulablePods**: Pods that can't be scheduled now

#### **Pod Movement Triggers**
- Pod creation/update → added to activeQ
- Pod rejected unschedulable → moved to backoffQ
- Long unschedulable pod → expires from unschedulablePods to activeQ
- Cluster event (node added, resource freed) → pods requeued via `MoveAllToActiveOrBackoffQueue()`

#### **Queueing Hints (plugin EnqueueExtensions)**
Plugins can register `EventsToRegister()` to specify which cluster events should requeue pods they rejected:
- Avoids unnecessary requeuing
- Improves scheduling efficiency
- Plugins return QueueingHint for events they care about

### Error Handling & Recovery

#### **Scheduling Cycle Failures**
1. **PreFilter failure** → Mark all nodes unschedulable, trigger PostFilter
2. **Filter/Score failure** → Continue with other nodes or fall through
3. **PostFilter (preemption)** → Attempts to preempt pods to make room
4. **Reserve failure** → Calls `Unreserve()` on all plugins, forgets pod

#### **Binding Cycle Failures**
1. **PreBind/Bind failure** → Trigger `Unreserve()`, forget pod from cache
2. **Assumed pod expires** → Cache automatically forgets after TTL
3. **Pod update during cycle** → Binding cycle detects and handles gracefully

---

## Summary

The Kubernetes scheduler v1.30.0 implements a sophisticated two-phase scheduling architecture that separates pod selection (scheduling cycle) from commitment (binding cycle). It uses an extensible plugin framework with 12 extension points, enabling both in-tree and out-of-tree plugins to influence decisions without tight coupling. The scheduler maintains a priority-based queue and an intelligent cache that tracks node resources and assumed pod reservations. By using CycleState for isolation, snapshots for consistency, and the assume-release pattern for optimistic concurrency, the scheduler efficiently handles large clusters while allowing asynchronous binding without blocking other scheduling decisions. This design enables high throughput and low latency pod scheduling while maintaining correctness and extensibility.

