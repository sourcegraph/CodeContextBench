# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler
- **pkg/scheduler/scheduler.go** — Main Scheduler struct managing lifecycle, initialization of queue/cache/profiles, and the main Run loop
- **pkg/scheduler/schedule_one.go** — Contains ScheduleOne entry point and the two-phase scheduling/binding cycle implementation
- **pkg/scheduler/eventhandlers.go** — Event handlers that watch cluster events and feed pods into the scheduling queue

### Framework & Plugin System
- **pkg/scheduler/framework/interface.go** — Defines all plugin interfaces (PreFilter, Filter, Score, Reserve, Permit, Bind, etc.), Framework interface, and Status codes
- **pkg/scheduler/framework/cycle_state.go** — CycleState struct for sharing data between plugins within a scheduling cycle
- **pkg/scheduler/framework/runtime/framework.go** — frameworkImpl implementing the Framework interface; instantiates plugins and executes them
- **pkg/scheduler/framework/runtime/registry.go** — Plugin registry mapping plugin names to factory functions
- **pkg/scheduler/framework/plugins/** — Built-in plugin implementations (NodeResourcesFit, InterPodAffinity, PodTopologySpread, etc.)

### Scheduling Queue
- **pkg/scheduler/internal/queue/scheduling_queue.go** — SchedulingQueue interface and PriorityQueue implementation with activeQ, backoffQ, unschedulablePods sub-queues
- **pkg/scheduler/internal/queue/events.go** — Cluster events and queueing hints for requeuing pods

### Cache
- **pkg/scheduler/internal/cache/cache.go** — Cache struct managing assumed pods, node info, and image states
- **pkg/scheduler/internal/cache/snapshot.go** — Snapshot of cache taken at start of scheduling cycle
- **pkg/scheduler/internal/cache/node_tree.go** — Efficient node lookup structure

### Profiles
- **pkg/scheduler/profile/profile.go** — Profile struct wrapping a Framework instance for a scheduler profile

## Dependency Chain

### 1. Entry Point: Pod Lifecycle
```
Event Source (API Server)
  ↓
eventhandlers.go: addPodToSchedulingQueue()
  ↓ (via Informer)
internalqueue.SchedulingQueue: Add()
  ↓
Pod enters activeQ/backoffQ
```

### 2. Main Scheduling Loop
```
Scheduler.Run() [pkg/scheduler/scheduler.go:435]
  ↓ (spawns goroutine)
Scheduler.ScheduleOne() [pkg/scheduler/schedule_one.go:66]
  ↓
Scheduler.NextPod() → SchedulingQueue.Pop()
  ↓ (retrieves next pod from priority queue)
framework.QueuedPodInfo
```

### 3. Scheduling Cycle (Lock & Assume Phase)
```
Scheduler.ScheduleOne() [schedule_one.go:66]
  ├─ Scheduler.schedulingCycle() [schedule_one.go:139]
  │   ├─ Scheduler.SchedulePod() [schedule_one.go:390] (delegated to sched.SchedulePod function)
  │   │   ├─ Cache.UpdateSnapshot() — creates point-in-time snapshot of nodes
  │   │   ├─ Scheduler.findNodesThatFitPod() [schedule_one.go:442]
  │   │   │   ├─ Framework.RunPreFilterPlugins()
  │   │   │   │   ├─ frameworkImpl.runPreFilterPlugin() [runtime/framework.go:700+]
  │   │   │   │   └─ PreFilterPlugin.PreFilter()
  │   │   │   ├─ Scheduler.findNodesThatPassFilters()
  │   │   │   │   ├─ Framework.RunFilterPlugins() [runs in parallel via parallelizer]
  │   │   │   │   │   └─ FilterPlugin.Filter()
  │   │   │   │   └─ Returns feasibleNodes list
  │   │   │   └─ Returns diagnosis with node statuses
  │   │   ├─ Framework.RunPreScorePlugins()
  │   │   │   └─ PreScorePlugin.PreScore()
  │   │   ├─ prioritizeNodes() — scores via Framework.RunScorePlugins()
  │   │   │   └─ ScorePlugin.Score() + NormalizeScore()
  │   │   └─ selectHost() — picks best node
  │   │
  │   ├─ Scheduler.assume() — marks pod as assumed in cache
  │   ├─ Framework.RunReservePluginsReserve() — reserve plugins update state
  │   │   └─ ReservePlugin.Reserve()
  │   └─ Framework.RunPermitPlugins() — permit plugins can delay/reject
  │       └─ PermitPlugin.Permit()
  │
  └─ Binding Cycle (async via goroutine) [schedule_one.go:118-133]
      └─ Scheduler.bindingCycle() [schedule_one.go:265]
          ├─ Framework.WaitOnPermit() — wait for any delayed permits
          ├─ Framework.RunPreBindPlugins()
          │   └─ PreBindPlugin.PreBind()
          ├─ Scheduler.bind() → Framework.RunBindPlugins()
          │   └─ BindPlugin.Bind() — typically creates pod binding via API
          ├─ Framework.RunPostBindPlugins()
          │   └─ PostBindPlugin.PostBind()
          └─ Cache.ForgetPod() OR Cache.AssumedPods cleanup
```

### 4. Plugin Framework Initialization
```
Scheduler.New() [pkg/scheduler/scheduler.go:252]
  ├─ profile.NewMap() [pkg/scheduler/profile/profile.go]
  │   └─ frameworkruntime.NewFramework() [framework/runtime/framework.go:242]
  │       ├─ Registry.Factory() — instantiates each plugin
  │       │   └─ pluginFactoryFunc(ctx, args, handle)
  │       ├─ frameworkImpl.getExtensionPoints()
  │       ├─ updatePluginList() — assigns plugins to extension point lists
  │       ├─ frameworkImpl.expandMultiPointPlugins()
  │       └─ frameworkImpl.setInstrumentedPlugins() — wraps with metrics
  │
  └─ SchedulingQueue.NewSchedulingQueue() [pkg/scheduler/internal/queue/scheduling_queue.go:130]
      └─ PriorityQueue with activeQ, backoffQ, unschedulablePods
```

## Design Patterns & Architecture

### Two-Phase Scheduling Design

**Scheduling Cycle (Synchronous Lock Phase)**
- Pod is popped from queue and sent through filtering/scoring plugins
- Framework.RunPreFilterPlugins() → Framework.RunFilterPlugins() → Framework.RunScorePlugins()
- Best node is selected
- **"Assume" step**: Pod is marked as running on node in cache (pessimistic locking)
- Framework.RunReservePluginsReserve() allows plugins to reserve resources
- Framework.RunPermitPlugins() can delay or reject at last moment
- Returns CycleState with scheduling decision

**Binding Cycle (Asynchronous Unbind Phase)**
- Runs in separate goroutine (doesn't block scheduler)
- Framework.WaitOnPermit() blocks if permit plugins requested wait
- Framework.RunPreBindPlugins() final checks before binding
- Framework.RunBindPlugins() creates actual Pod-to-Node binding in API server
- Framework.RunPostBindPlugins() cleanup/notifications
- If binding fails, assumed pod is "forgotten" from cache, triggering requeue

### Plugin Framework Architecture

**Extension Points (Hooks)**
1. **PreEnqueue** — Filter pods before adding to queue (in-place optimization)
2. **QueueSort** — Sort pods in scheduling queue (exactly one plugin required)
3. **PreFilter** — Pre-process pod; may exclude nodes or skip filter phase
4. **Filter** — Run in parallel; determine feasible nodes (replaces old "Predicates")
5. **PostFilter** — Run if no feasible nodes (e.g., preemption logic)
6. **PreScore** — Information-only; ran for feasible nodes
7. **Score** — Run in parallel; score each feasible node (replaces old "Priorities")
8. **Reserve** — Update plugin state after scheduling decision
9. **Permit** — Final gate before binding; can wait or reject
10. **PreBind** — Final checks immediately before binding
11. **Bind** — Perform actual binding (one of plugins in list will bind)
12. **PostBind** — Cleanup after successful binding

**Plugin Lifecycle**
- Plugins are loaded from Registry based on KubeSchedulerProfile configuration
- Each plugin implements framework.Plugin interface (Name() method)
- Plugins can optionally implement EnqueueExtensions for event-based requeuing
- frameworkImpl calls pluginFactoryFunc with context, args, and Handle (which provides access to cache, listers, event recorder)
- Plugins store scheduling-cycle state in CycleState.storage (thread-safe sync.Map)

### Scheduling Queue

**Three-Queue Model**
- **activeQ** (priority heap): Pods being actively considered for scheduling
- **backoffQ** (priority heap by backoff expiry): Pods in backoff after failed attempt
- **unschedulablePods**: Pods determined unschedulable; moved to backoffQ after timeout

**Queueing Hints & Efficient Requeuing**
- Plugins implement EnqueueExtensions.EventsToRegister() to specify cluster events they care about
- When event occurs (e.g., node added, taint removed), only affected pods are requeued
- Avoids requeuing all pods for every cluster event (performance optimization)

### Cache Architecture

**Assumptions & Snapshot Model**
- When pod is assumed, it's added to cache with nodeName set
- Real Pod in API server doesn't have nodeName yet (binding hasn't occurred)
- Cache maintains assumedPods set and podState map tracking assumed pods and their deadlines
- Deadlines allow cache to clean up stale assumed pods (prevents memory leaks if binding fails)

**Node Information Management**
- Cache.NodeInfo tracks pods, resources, and predicates on each node
- Doubly-linked list of NodeInfo sorted by recency (head = most recent)
- UpdateSnapshot() called at start of scheduling cycle creates point-in-time view
- Generation numbers track changes, allowing incremental snapshot updates

**Image States**
- Tracks image pull latency and availability on nodes
- Used by plugins like ImageLocality for scheduling decisions

### CycleState Design

**Thread-Safe Scheduling Context**
- Each pod gets its own CycleState instance for a scheduling cycle
- Backed by sync.Map for "write once, read many" optimization
- Plugins can store intermediate results (e.g., PreFilter stores computed data read by Filter)
- Allows zero-copy plugin communication

**State Propagation**
- PodsToActivateKey reserved key: Plugins can inject pods to be activated post-scheduling
- SkipFilterPlugins, SkipScorePlugins: PreFilter/PreScore plugins can signal to skip coupled plugins
- Plugin metrics flags: Controls per-cycle metrics recording

### Multi-Profile Support

**Scheduler Profiles**
- Scheduler can run multiple scheduler profiles simultaneously
- Each profile has own Framework, QueueSort, and plugin chain
- Pods specify .spec.schedulerName to choose profile
- Allows different scheduling logic for different workload types

## Key Data Structures

### ScheduleResult
```go
type ScheduleResult struct {
    SuggestedHost string           // Selected node name
    EvaluatedNodes int             // Nodes evaluated in filtering + beyond
    FeasibleNodes int              // Nodes that passed filtering
    nominatingInfo *NominatingInfo // For preemption tracking
}
```

### QueuedPodInfo
```go
type QueuedPodInfo struct {
    Pod                      *v1.Pod
    Timestamp                time.Time     // When pod entered queue
    UnschedulablePlugins     sets.Set[string]
    Attempts                 int           // Scheduling attempts count
    InitialAttemptTimestamp  *time.Time
}
```

### FitError (Scheduling Failure)
```go
type FitError struct {
    Pod         *v1.Pod
    NumAllNodes int
    Diagnosis   Diagnosis
}

type Diagnosis struct {
    NodeToStatusMap map[string]*Status  // Per-node rejection reasons
    PreFilterMsg    string
    PostFilterMsg   string
}
```

## Data Flow During Scheduling

1. **Pod Arrival**: Pod added to queue via event handler
2. **Pop Phase**: ScheduleOne pops next pod from queue
3. **Framework Selection**: Find Framework matching pod's schedulerName
4. **Snapshot**: Cache.UpdateSnapshot() creates point-in-time node view
5. **PreFilter**: Plugins may narrow down candidate nodes
6. **Filter**: Determine feasible nodes (parallel execution)
7. **Score**: Rank feasible nodes (parallel execution)
8. **Selection**: Pick best node
9. **Assume**: Mark pod as running on node in cache
10. **Reserve**: Plugins update internal state
11. **Permit**: Final gate; can delay or reject
12. **Bind (async)**: Wait for permits, run PreBind plugins, call Bind plugins, run PostBind
13. **Cleanup**: Mark pod as truly scheduled or requeue if binding failed

## Failure Handling

**Scheduling Cycle Failure** → Handled by FailureHandler
- PostFilterPlugins run (e.g., preemption to free up resources)
- Pod moved to backoffQ with exponential backoff
- Will retry after backoff expires or cluster event occurs

**Binding Cycle Failure** → Handled by handleBindingCycleError
- Called if PreBind, Bind, or PostBind plugins fail
- Reserve plugins' Unreserve methods called to clean up
- assumed pod forgotten from cache
- Pod requeued (triggers event-based requeue or backoff)

## Summary

The Kubernetes scheduler implements a sophisticated two-phase lock-free scheduling architecture using a plugin framework. Pods are sorted via PriorityQueue, processed through a snapshot of cluster state, evaluated by parallel filter/score plugins, and speculatively assumed to run on selected nodes. The binding phase then asynchronously confirms the scheduling decision. The design enables multiple scheduling profiles, efficient event-driven pod requeuing via queueing hints, and extensibility through plugin interfaces at twelve extension points. CycleState provides thread-safe temporary state sharing between plugins, while the cache maintains node information with generation tracking for efficient incremental snapshots. This architecture balances throughput (parallel filtering/scoring), fairness (multiple queue levels with backoff), and extensibility (plugin framework with 12 extension points).
