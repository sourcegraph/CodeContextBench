# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler Files
- **pkg/scheduler/scheduler.go** — Scheduler struct, main orchestrator managing Cache, SchedulingQueue, Profiles, and NextPod function. Initializes the plugin registry, creates scheduling queue and cache.
- **pkg/scheduler/schedule_one.go** — ScheduleOne() entry point for the main scheduling loop. Contains schedulingCycle() and bindingCycle() implementations. Core scheduling algorithm with filtering, scoring, and binding phases.
- **pkg/scheduler/eventhandlers.go** — Event handlers for Pod/Node watchers. Routes events to SchedulingQueue and triggers pod requeuing.

### Framework and Plugin Architecture
- **pkg/scheduler/framework/interface.go** — Defines all plugin interfaces (PreEnqueuePlugin, PreFilterPlugin, FilterPlugin, PostFilterPlugin, PreScorePlugin, ScorePlugin, ReservePlugin, PermitPlugin, PreBindPlugin, BindPlugin, PostBindPlugin). Defines Framework interface with plugin execution methods.
- **pkg/scheduler/framework/cycle_state.go** — CycleState struct using sync.Map for thread-safe plugin state storage during a scheduling cycle. Allows plugins to read/write arbitrary data.
- **pkg/scheduler/framework/runtime/framework.go** — frameworkImpl implementing the Framework interface. Manages plugin initialization, registration at extension points, and orchestration of plugin execution.
- **pkg/scheduler/framework/runtime/registry.go** — Plugin registry mapping plugin names to factory functions.

### Scheduling Queue
- **pkg/scheduler/internal/queue/scheduling_queue.go** — SchedulingQueue interface and PriorityQueue implementation. Contains three sub-queues: activeQ (pods being scheduled), podBackoffQ (failed pods with backoff), unschedulablePods (pods rejected by plugins).
- **pkg/scheduler/internal/queue/events.go** — ClusterEvent and queueing hint definitions for efficient pod requeuing based on cluster events.

### Scheduler Cache
- **pkg/scheduler/internal/cache/cache.go** — Cache implementation tracking NodeInfo in a doubly-linked list, assumed pods, and image states. UpdateSnapshot() called at start of each scheduling cycle.
- **pkg/scheduler/internal/cache/snapshot.go** — Snapshot of NodeInfo objects taken at scheduling cycle start. Contains nodeInfoList, nodeInfoMap, and specialized lists for affinity constraints.
- **pkg/scheduler/internal/cache/interface.go** — Cache interface defining contract for scheduler cache operations.
- **pkg/scheduler/internal/cache/node_tree.go** — nodeTree data structure for efficiently finding nodes in the snapshot.

### Plugin Implementations
- **pkg/scheduler/framework/plugins/registry.go** — In-tree plugin registry with default plugins (NodeName, NodeUnschedulable, DefaultBinder, etc.).
- **pkg/scheduler/framework/plugins/queuesort/** — PrioritySort plugin implementing QueueSortPlugin.
- **pkg/scheduler/framework/plugins/noderesources/** — NodeResourcesFit implementing PreFilterPlugin and FilterPlugin.
- **pkg/scheduler/framework/plugins/tainttoleration/** — TaintToleration plugin (Filter and PreScore).
- **pkg/scheduler/framework/plugins/interpodaffinity/** — InterPodAffinity plugin (PreFilter, Filter, PreScore, Score).
- **pkg/scheduler/framework/plugins/defaultbinder/** — DefaultBinder implementing BindPlugin.
- **pkg/scheduler/framework/plugins/defaultpreemption/** — DefaultPreemption implementing PostFilterPlugin for preemption logic.

### Supporting Utilities
- **pkg/scheduler/extender.go** — Out-of-tree scheduler extender support (legacy HTTP-based extensibility).
- **pkg/scheduler/profile/profile.go** — Profile management creating separate Framework instances per scheduler profile.
- **pkg/scheduler/metrics/** — Metrics collection for scheduler events and performance.

## Dependency Chain

### 1. Scheduler Initialization
```
New() in scheduler.go
  ├─ Creates plugin registry from in-tree and out-of-tree plugins
  ├─ Builds profiles via profile.NewMap()
  │  └─ NewFramework() in runtime/framework.go for each profile
  │     └─ Initializes plugins from registry at extension points
  ├─ Creates SchedulingQueue via internalqueue.NewSchedulingQueue()
  ├─ Creates Cache via internalcache.New()
  ├─ Sets up event handlers via addAllEventHandlers()
  │  └─ Watches Pod, Node, PVC, Service events
  └─ Returns fully initialized Scheduler
```

### 2. Main Scheduling Loop
```
Scheduler.Run()
  ├─ Starts SchedulingQueue.Run()
  ├─ Spawns goroutine calling ScheduleOne() loop
  │  └─ wait.UntilWithContext(ctx, sched.ScheduleOne, 0)
  └─ Waits for context cancellation

Scheduler.ScheduleOne()
  ├─ Calls NextPod() → SchedulingQueue.Pop()
  ├─ Calls frameworkForPod() to get Framework for pod's scheduler name
  ├─ Creates CycleState
  ├─ Calls schedulingCycle()
  │  └─ Returns ScheduleResult or error
  └─ On success, spawns goroutine for bindingCycle()
```

### 3. Scheduling Cycle (Synchronous, Main Thread)
```
schedulingCycle()
  ├─ Calls SchedulePod()
  │  ├─ Cache.UpdateSnapshot() — takes fresh snapshot of node state
  │  ├─ Calls findNodesThatFitPod()
  │  │  ├─ Runs PreFilter plugins
  │  │  ├─ Filters nodes by PreFilterResult
  │  │  ├─ Evaluates nominated node if present
  │  │  ├─ Calls findNodesThatPassFilters()
  │  │  │  └─ Runs Filter plugins on all nodes in parallel
  │  │  └─ Runs extender filters
  │  ├─ Runs PreScore plugins
  │  ├─ Runs Score plugins on feasible nodes
  │  ├─ Selects best-scored node
  │  └─ Returns ScheduleResult with suggested host
  ├─ On failure, runs PostFilter plugins (preemption)
  ├─ Calls assume() — adds pod to Cache with node binding
  ├─ Runs Reserve plugins
  ├─ Runs Permit plugins (may return Wait status)
  └─ Returns ScheduleResult and assumed pod
```

### 4. Binding Cycle (Asynchronous, Separate Goroutine)
```
bindingCycle()
  ├─ Calls WaitOnPermit() — waits if Permit plugins returned Wait
  ├─ Runs PreBind plugins
  ├─ Calls bind() — executes Bind plugins
  │  └─ Default: DefaultBinder creates PodBinding
  ├─ On Bind success:
  │  ├─ Runs PostBind plugins
  │  └─ Returns success
  └─ On error:
     ├─ Calls handleBindingCycleError()
     ├─ Runs Unreserve plugins
     ├─ Cache.ForgetPod() — removes pod assumption
     └─ Requeues pod via MoveAllToActiveOrBackoffQueue()
```

### 5. Event-Driven Requeuing
```
Event Handlers (Pod/Node watchers)
  ├─ Pod events → triggers pod requeue
  ├─ Node events → triggers queueing hints
  │  └─ Plugins implement EnqueueExtensions
  │     └─ Advises which pods to requeue based on event type
  └─ Events queued in SchedulingQueue.inFlightEvents
     └─ Processed after in-flight pod's scheduling completes
```

## Architecture Analysis

### Design Patterns

1. **Two-Phase Scheduling Design**
   - **Scheduling Cycle**: Synchronous, deterministic, locks Cache
   - **Binding Cycle**: Asynchronous, non-blocking, allows next scheduling cycle to start
   - **Assumption Step**: Pod assumed in Cache before binding, enabling pipeline parallelism

2. **Plugin Framework Pattern**
   - **Extension Points**: 12 well-defined points where plugins inject behavior
   - **Registry Pattern**: Plugins registered at startup, loaded from configuration
   - **Chain of Responsibility**: Plugins executed in order at each extension point
   - **Fail-Fast**: First plugin failure aborts cycle (except informational plugins)

3. **State Management**
   - **CycleState**: Thread-safe map (sync.Map) for per-cycle plugin state
   - **Cache**: In-memory representation of cluster state (nodes, pods, volumes)
   - **Snapshot**: Immutable view of Cache taken at cycle start, used throughout cycle

4. **Priority Queue Strategy**
   - **Active Queue**: Pods ready for scheduling
   - **Backoff Queue**: Pods waiting for backoff period to expire
   - **Unschedulable Queue**: Pods with unresolvable issues (5-min timeout)
   - **Queueing Hints**: Smart requeuing based on cluster events (feature gated)

### Component Responsibilities

**Scheduler**
- Orchestrates the scheduling pipeline
- Manages NextPod function and retry loops
- Handles failure scenarios and error callbacks
- Maintains percentage-of-nodes optimization

**Framework (frameworkImpl)**
- Initializes and manages plugins
- Calls plugins at each extension point in correct order
- Manages waiting pods and permit plugin logic
- Provides Handle interface for plugin access to cluster state

**SchedulingQueue (PriorityQueue)**
- Manages pod lifecycle (pending → active → scheduled → done)
- Implements priority ordering via QueueSort plugins
- Tracks in-flight pods and received events
- Requeues pods based on cluster events and queueing hints

**Cache (cacheImpl)**
- Maintains in-memory cluster state (nodes, pods, volumes, images)
- Manages assumed pods with TTL-based expiration
- Maintains doubly-linked list for generation tracking
- Provides efficient snapshot for read operations

**CycleState**
- Provides thread-safe plugin state storage (sync.Map)
- Allows plugins to read/write arbitrary data per cycle
- Tracks skip sets for Filter and Score plugins
- Records plugin metrics sampling decisions

### Data Flow Through Scheduling

```
┌──────────────────────────────────────────────────────────────────┐
│                        SCHEDULING CYCLE                          │
└──────────────────────────────────────────────────────────────────┘

1. SchedulingQueue.Pop() → QueuedPodInfo
2. Create CycleState (per-cycle plugin state)
3. Cache.UpdateSnapshot() → NodeSnapshot
4. RunPreFilterPlugins(state, pod) → PreFilterResult
   - May filter out nodes
5. RunFilterPlugins(state, pod, nodeInfo) × N nodes (parallel)
   - Returns feasible nodes
6. RunPreScorePlugins(state, pod, feasibleNodes)
7. RunScorePlugins(state, pod, nodeName) × feasibleNodes (parallel)
   - Normalizes scores per plugin
8. SelectHost(scores) → Selected node
9. Cache.AssumedPod(pod, node) → Updates cache
10. RunReservePlugins(state, pod, node)
11. RunPermitPlugins(state, pod, node) → may return Wait

┌──────────────────────────────────────────────────────────────────┐
│                        BINDING CYCLE                             │
│              (Runs asynchronously in separate goroutine)         │
└──────────────────────────────────────────────────────────────────┘

1. WaitOnPermit(pod) — blocks if Permit returned Wait
2. RunPreBindPlugins(state, pod, node)
3. RunBindPlugins(state, pod, node) → creates Binding object
4. API Server accepts binding → pod scheduled
5. RunPostBindPlugins(state, pod, node)
6. SchedulingQueue.Done(pod.UID)
```

### Plugin Framework Extension Points

**Pre-Scheduling**
- **PreEnqueue**: Lightweight filter before adding pod to activeQ
- **QueueSort**: Determines pod ordering in activeQ (exactly one required)

**Scheduling Cycle**
- **PreFilter**: Early validation, may return filtered node set
- **Filter**: Predicate evaluation (node compatibility)
- **PostFilter**: Preemption logic when pod doesn't fit
- **PreScore**: Informational extension point before scoring
- **Score**: Rank nodes (normalized to 0-100)
- **Reserve**: Reserve resources in plugin state (must support Unreserve)
- **Permit**: Final approval before binding (may return Wait for external approval)

**Binding Cycle**
- **PreBind**: Final pre-binding checks
- **Bind**: Persist binding (default creates PodBinding)
- **PostBind**: Informational extension point after binding

### Interface Contracts

**Framework.Handle Interface** (passed to plugins)
```go
// Plugins can access:
- SnapshotSharedLister() — read-only cluster state snapshot
- ClientSet() — Kubernetes API client
- SharedInformerFactory() — event-driven cluster state
- Extenders() — out-of-tree extender plugins
- EventRecorder() — emit events to API server
- IterateOverWaitingPods() — waiting permits
```

**Plugin State via CycleState**
```go
// Pre-Filter plugins write state, Filter plugins read and may modify
state.Write(key, pluginSpecificData)  // write once
state.Read(key)                        // read many times
state.Delete(key)                      // cleanup
```

### Interaction Between Key Components

**SchedulingQueue ↔ Cache**
- Queue pops pods for scheduling
- Scheduling cycle assumes pod in cache
- On failure, ForgetPod removes assumption
- Events from cache handlers trigger queue requeuing

**Cache ↔ Framework (via Snapshot)**
- Cache creates Snapshot at cycle start
- Framework provides Snapshot to Handle interface
- Plugins read nodes, pods, volumes from Snapshot
- Plugins cannot modify Snapshot (immutable view)

**Framework ↔ CycleState**
- Framework creates CycleState per scheduling cycle
- Passes CycleState to all plugins at all extension points
- PreFilter plugins initialize cycle state
- Filter/Score plugins read and build on PreFilter state

**Scheduler ↔ FailureHandler**
- Scheduler invokes FailureHandler on scheduling failure
- Handler examines failure reason and metrics
- May implement backoff, requeuing, or preemption logic

## Summary

The Kubernetes scheduler uses a **plugin-based two-phase architecture** where scheduling (synchronous) and binding (asynchronous) phases are decoupled through the assumption step. The **SchedulingQueue** manages pod flow through three states (active/backoff/unschedulable), while the **Cache** maintains cluster state and enables **snapshot-based consistency** during scheduling cycles. The **Framework** orchestrates **12 extension points** where plugins can inject filtering, scoring, resource reservation, and binding logic. **CycleState** enables plugins to share per-cycle state, and **EnqueueExtensions** provide efficient event-driven requeuing based on cluster changes. This architecture achieves throughput via asynchronous binding and parallelism in filtering/scoring while maintaining scheduling determinism through snapshot isolation.
