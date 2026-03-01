# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler Components
- **pkg/scheduler/scheduler.go** — Main scheduler entry point; initializes framework profiles, scheduling queue, cache, and event handlers; manages the scheduler's lifecycle
- **pkg/scheduler/schedule_one.go** — Implements the main scheduling loop (ScheduleOne) with two-phase design: schedulingCycle and bindingCycle
- **pkg/scheduler/eventhandlers.go** — Event handlers for resource changes (Pods, Nodes, PVCs) that trigger requeuing of affected pods

### Framework (Plugin System)
- **pkg/scheduler/framework/interface.go** — Defines all plugin interfaces (PreEnqueue, QueueSort, PreFilter, Filter, PostFilter, PreScore, Score, Reserve, Permit, PreBind, Bind, PostBind) and the Framework interface contract
- **pkg/scheduler/framework/types.go** — Core types: QueuedPodInfo, PodInfo, Status (with codes: Success, Error, Unschedulable, UnschedulableAndUnresolvable, Wait, Skip, Pending), and cluster event definitions
- **pkg/scheduler/framework/cycle_state.go** — CycleState: a thread-safe state container (using sync.Map) for plugins to store and retrieve scheduling cycle data; allows plugins to share state across extension points
- **pkg/scheduler/framework/runtime/framework.go** — frameworkImpl: the concrete Framework implementation that orchestrates plugin execution, manages plugin instances, and implements all Run* methods for extension points

### Scheduling Queue
- **pkg/scheduler/internal/queue/scheduling_queue.go** — PriorityQueue implementation with three sub-queues: activeQ (ready for scheduling), backoffQ (temporarily blocked), unschedulablePods (rejected and waiting for events); manages pod requeuing based on cluster events
- **pkg/scheduler/internal/queue/events.go** — Cluster event definitions and enqueue extension point support for efficient pod requeuing based on resource changes

### Cache (Node Information)
- **pkg/scheduler/internal/cache/cache.go** — Scheduler cache that maintains assumed pod state and NodeInfo snapshots; tracks pod-to-node assignments for the duration of a scheduling cycle before actual binding
- **pkg/scheduler/internal/cache/interface.go** — Cache interface contract
- **pkg/scheduler/internal/cache/snapshot.go** — Snapshot of cache state at the beginning of scheduling cycle; contains list of nodes and their allocatable resources
- **pkg/scheduler/internal/cache/node_tree.go** — Efficient node tree structure for quick lookups

### Plugin Framework Runtime
- **pkg/scheduler/framework/runtime/registry.go** — Plugin registry that maps plugin names to factory functions
- **pkg/scheduler/framework/runtime/instrumented_plugins.go** — Wrapper for metrics recording around plugin execution
- **pkg/scheduler/framework/runtime/waiting_pods_map.go** — Manages pods waiting in Permit extension point
- **pkg/scheduler/profile/profile.go** — Profiles: allow multiple schedulers with different plugins/configuration to coexist in a single scheduler deployment

### Built-in Plugins (Examples)
- **pkg/scheduler/framework/plugins/noderesources/fit.go** — Filter plugin that checks if pod fits on node (CPU, memory)
- **pkg/scheduler/framework/plugins/noderesources/least_allocated.go** — Score plugin for node spreading
- **pkg/scheduler/framework/plugins/nodeaffinity/node_affinity.go** — Filter and score based on nodeAffinity
- **pkg/scheduler/framework/plugins/interpodaffinity/plugin.go** — Filter and score based on pod affinity/anti-affinity
- **pkg/scheduler/framework/plugins/defaultbinder/default_binder.go** — Default Bind plugin that patches pod.spec.nodeName

---

## Dependency Chain

### Entry Point & Main Loop
1. **Entry:** `pkg/scheduler/scheduler.go:New()` → Creates Scheduler instance with cache, queue, and framework profiles
2. **Initialization Flow:**
   - `New()` creates internalcache.New() → scheduler cache
   - `New()` creates internalqueue.NewSchedulingQueue() → PriorityQueue
   - `New()` creates profile.NewMap() → Framework instances via frameworkruntime.NewFramework()
   - `New()` calls addAllEventHandlers() → registers k8s informer event handlers

3. **Main Loop:** `pkg/scheduler/scheduler.go:Run()` → Starts goroutine loop calling ScheduleOne repeatedly

### ScheduleOne: The Two-Phase Scheduling Pipeline
**File:** `pkg/scheduler/schedule_one.go:ScheduleOne()`

```
ScheduleOne()
├── NextPod() → Pop from SchedulingQueue (PriorityQueue.Pop)
├── frameworkForPod() → Get Framework for pod's schedulerName
├── Create CycleState → New cycle-local state container
│
├─── SCHEDULING CYCLE ───────────────────────────────────────
├── schedulingCycle(ctx, state, fwk, podInfo, start, podsToActivate)
│   ├── SchedulePod(ctx, fwk, state, pod) → schedulePod()
│   │   ├── Cache.UpdateSnapshot() → Take snapshot of cache state
│   │   ├── RunPreFilterPlugins(ctx, state, pod)
│   │   │   └── Execute all PreFilterPlugin.PreFilter() methods
│   │   │       └── Can return PreFilterResult to narrow node list
│   │   ├── findNodesThatFitPod() → Filter phase
│   │   │   ├── Get nominated node (from preemption) if exists
│   │   │   ├── RunFilterPlugins() on candidate nodes (parallel)
│   │   │   │   └── Filter plugins evaluate each node
│   │   │   └── Return feasibleNodes list
│   │   ├── RunPreScorePlugins(ctx, state, pod, feasibleNodes)
│   │   │   └── Prepare for scoring (informational extension point)
│   │   ├── prioritizeNodes() → Scoring phase
│   │   │   ├── RunScorePlugins() on feasible nodes (parallel)
│   │   │   │   └── Each Score plugin scores nodes 0-100
│   │   │   ├── Aggregate scores from all plugins (weighted)
│   │   │   └── Run Extenders' Score method if configured
│   │   └── selectHost() → Pick highest-scored node
│   │
│   ├── assume() → Cache.AssumePod(pod, nodeName)
│   │   └── Add pod to cache with nodeName set
│   │       (allows parallel scheduling without waiting for binding)
│   │
│   ├── RunReservePluginsReserve(ctx, state, pod, nodeName)
│   │   └── Reserve plugins update internal state (e.g., volume limits)
│   │       If fails: RunReservePluginsUnreserve() + Cache.ForgetPod()
│   │
│   └── RunPermitPlugins(ctx, state, pod, nodeName)
│       └── Permit plugins can return Success or Wait
│           If Wait: pod added to WaitingPods map (blocking until Allow/Reject)
│
└─── BINDING CYCLE (asynchronous) ───────────────────────────
    └── bindingCycle(ctx, state, fwk, scheduleResult, podInfo, start, podsToActivate)
        ├── WaitOnPermit(ctx, pod) → Block until Permit plugins allow or reject
        │
        ├── RunPreBindPlugins(ctx, state, pod, nodeName)
        │   └── Final checks (e.g., mount volumes, setup networking)
        │
        ├── bind(ctx, fwk, pod, nodeName, state) → Run bind plugins
        │   ├── RunBindPlugins(ctx, state, pod, nodeName)
        │   │   └── Bind plugins patch pod.spec.nodeName
        │   │       (first plugin that handles wins, others skipped)
        │   └── Call Kubernetes API to create binding
        │
        └── RunPostBindPlugins(ctx, state, pod, nodeName)
            └── Cleanup/informational work (e.g., event recording)
```

### Scheduling Queue Flow
**File:** `pkg/scheduler/internal/queue/scheduling_queue.go`

```
Pod Lifecycle in Queue:
1. Pod Created/Updated → EventHandler
   ├── Run PreEnqueuePlugins (if configured)
   └── Add to queue (activeQ, backoffQ, or unschedulablePods)

2. Pop() → Scheduler picks next pod
   └── Increment SchedulingCycle counter

3. After Scheduling Cycle:
   ├── Success: pod moves to binding (asynchronous)
   ├── Unschedulable: pod added to unschedulablePods
   │   └── Waits for cluster events to move back
   └── Error: pod added to backoffQ with exponential backoff

4. Event Handler (e.g., NodeAdded, VolumeProvisioned)
   ├── Query queueingHintMap for affected pods
   ├── Move matching pods from unschedulablePods to backoffQ/activeQ
   └── QueueingHintFn can filter pods (return QueueSkip to skip requeue)

5. Done(podUID) → Called when pod binding completes
   └── Removes pod from inFlightPods tracking
```

### Cache Integration
**File:** `pkg/scheduler/internal/cache/cache.go`

```
Cache maintains:
- assumedPods: set of pod keys that have been assumed (scheduled but not yet bound)
- podStates: map of pod key → {pod, deadline, bindingFinished}
- nodes: map of node name → NodeInfo (doubly-linked list, head = most recently updated)
- nodeTree: efficient tree for node lookups

UpdateSnapshot() lifecycle:
1. Called at start of each scheduling cycle
2. Traverses doubly-linked list from head (most recent) backwards
3. Copies only NodeInfo entries changed since last snapshot
4. Returns when reaches node with old generation number
5. Used by plugins as read-only reference during scheduling

Key insight: Assumed pods allow parallel scheduling while binding happens asynchronously
```

### Plugin Framework Execution
**File:** `pkg/scheduler/framework/runtime/framework.go`

```
frameworkImpl manages 12 extension points:

1. PreEnqueue (Queue initialization)
   └── PreEnqueuePlugin.PreEnqueue() - Gate pods before they enter queue

2. QueueSort (Queue ordering)
   └── QueueSortPlugin.Less() - Determine pod priority in queue

3. PreFilter (Preparation & filtering)
   └── PreFilterPlugin.PreFilter() - Early rejection, narrow node list

4. Filter (Node feasibility)
   └── FilterPlugin.Filter() - Parallel filtering of nodes

5. PostFilter (Handle unschedulable)
   └── PostFilterPlugin.PostFilter() - Preemption & pod manipulation

6. PreScore (Score preparation)
   └── PreScorePlugin.PreScore() - Prepare for scoring

7. Score (Node ranking)
   └── ScorePlugin.Score() - Rank feasible nodes (0-100)
   └── ScorePlugin.NormalizeScore() - Normalize scores per plugin

8. Reserve (Resource reservation)
   └── ReservePlugin.Reserve/Unreserve() - Update internal state

9. Permit (Admission & gating)
   └── PermitPlugin.Permit() - Allow, Wait, or Reject pod

10. PreBind (Final checks)
    └── PreBindPlugin.PreBind() - Volume mounting, networking setup

11. Bind (Node binding)
    └── BindPlugin.Bind() - Patch pod.spec.nodeName

12. PostBind (Cleanup)
    └── PostBindPlugin.PostBind() - Recording events, cleanup

RunX methods execute plugins with error handling:
- Short-circuit on first non-Success status for PreFilter, Filter, PreScore, Reserve, PreBind, Bind
- Aggregate scores for Score
- Allow multiple PostFilter and PostBind plugins (informational)
```

---

## Analysis

### Design Patterns Identified

#### 1. **Plugin Framework / Extension Point Pattern**
The scheduler uses a well-defined plugin architecture with 12 extension points. Each extension point represents a specific phase in the scheduling lifecycle. Plugins implement interfaces to participate at one or more extension points. This provides:
- **Extensibility**: Users can add custom plugins without modifying core scheduler
- **Modularity**: Each plugin concerns is isolated
- **Composability**: Multiple plugins can run at each extension point

#### 2. **Two-Phase Scheduling Design**
The scheduler separates **scheduling** (finding a node) from **binding** (assigning to node):
- **Synchronous Scheduling Cycle**: PreFilter → Filter → PostFilter → PreScore → Score → Reserve → Permit
- **Asynchronous Binding Cycle**: WaitOnPermit → PreBind → Bind → PostBind

Benefits:
- Parallelism: Multiple pods can be scheduled while previous pods are binding
- "Assume" optimization: Pod assumed in cache immediately after scheduling, reserves resources before actual binding
- Reduced latency: Binding delays don't block scheduling of other pods

#### 3. **Cache Snapshot Pattern**
At the start of each scheduling cycle, the scheduler takes a read-only snapshot of the cache (node information). This snapshot:
- Provides consistent view during scheduling cycle
- Allows plugins to see assumed pods affecting node capacity
- Uses generation counters to copy only changed NodeInfo entries (efficient incremental updates)
- Enables parallel Filter/Score plugins without synchronization concerns

#### 4. **State Container (CycleState)**
CycleState uses `sync.Map` to allow plugins to store cycle-local data:
- PreFilter plugins compute and store reusable state
- PreScore plugins prepare state for Score plugins
- Thread-safe access without locks for typical read-heavy patterns
- Allows plugins to share computed information

#### 5. **Backoff & Event-Driven Requeuing**
When a pod fails scheduling:
- Pod moves to backoffQ with exponential backoff (1s → 10s)
- Pod only returns to activeQ when a "relevant" cluster event occurs (node added, taint removed, etc.)
- Plugins implement `EnqueueExtensions.EventsToRegister()` to indicate which events can make them schedulable
- Efficient: Uses `QueueingHintFn` to filter irrelevant events per plugin

#### 6. **Nominated Node Pattern (Preemption)**
When preemption is needed:
- PostFilter plugins (e.g., DefaultPreemption) identify candidate victims
- If preemption succeeds, assign pod.Status.NominatedNodeName
- In next scheduling attempt, scheduler tries nominated node first
- Improves chance of successful scheduling after pod evictions

### Component Responsibilities

#### **Scheduler (scheduler.go)**
- Entry point and lifecycle management
- Initializes cache, queue, frameworks, and event handlers
- Implements ScheduleOne loop as main scheduling goroutine
- Routes pods to appropriate framework profile
- Handles scheduling failures via FailureHandler

#### **SchedulingQueue (PriorityQueue)**
- Manages three pod queues: activeQ, backoffQ, unschedulablePods
- Tracks in-flight pods (currently being scheduled/bound)
- Implements event-driven requeuing with queueing hints
- Enforces backoff policy
- Integrates with PreEnqueue plugins for pod gating

#### **Cache**
- Maintains assumed pod tracking (pods in scheduling but not yet bound)
- Stores node information with generation tracking
- Provides snapshot for scheduling cycle (immutable view of node state)
- Tracks PVC usage, image state, and other node attributes
- Cleanup goroutine expires assumed pods that don't complete binding within TTL

#### **Framework (frameworkImpl)**
- Plugin registry and instantiation
- Orchestrates plugin execution across 12 extension points
- Manages waiting pods (from Permit plugins)
- Aggregates scoring results from multiple Score plugins
- Handles plugin initialization with config and handles

#### **CycleState**
- Per-scheduling-cycle container for plugin state
- Allows plugins to share computed information (e.g., affinity selectors)
- Thread-safe via sync.Map
- Can be cloned for preemption scenarios (evaluating pod placement with different node states)

### Data Flow Description

#### **From Pod Creation to Node Binding**

1. **Pod Enters System**
   - Informer watches new Pod, triggers ADD event handler
   - PreEnqueue plugins gate pod (may reject)
   - Pod added to SchedulingQueue (activeQ or unschedulablePods if gated)

2. **Scheduler Selects Pod (Pop)**
   - ScheduleOne() blocks on SchedulingQueue.Pop()
   - QueueSort plugin determines priority among active pods
   - Pod wrapper (QueuedPodInfo) returned with metadata (attempts, timestamp)

3. **Scheduling Cycle Begins**
   - Create fresh CycleState for this pod
   - Call cache.UpdateSnapshot() → get node information snapshot
   - PreFilter plugins run (can narrow node list via PreFilterResult)
   - Filter plugins run in parallel → narrow to feasible nodes
   - If no feasible nodes:
     - PostFilter plugins attempt to remedy (preemption)
     - If still fails, pod marked Unschedulable, moved to unschedulablePods or backoffQ
     - Scheduling cycle ends, wait for cluster event to retry

4. **Assume in Cache**
   - After node selected, call cache.AssumePod()
   - Pod added to cache.assumedPods and cache.podStates
   - This allows other pods' Filter/Score plugins to see this pod's resource consumption
   - Multiple pods can be scheduled sequentially before any binding completes

5. **Reserve Phase**
   - Reserve plugins update their internal state (e.g., volume count limits)
   - If fails, Unreserve called on all Reserve plugins, pod forgotten from cache
   - If succeeds, return to scheduling cycle caller

6. **Permit Phase**
   - Permit plugins make final admission decision
   - Can return Success (proceed to binding), Wait (hold in queue), or Reject
   - If Wait, pod added to framework's waitingPods map, binding delayed
   - If Reject/Error, Unreserve called, pod forgotten, moved back to queue

7. **Binding Cycle Starts (Async)**
   - Go routine launched for binding to avoid blocking scheduler loop
   - If Permit returned Wait, binding waits on WaitOnPermit() signal
   - Signal comes from permit plugin calling Allow() on WaitingPod
   - If pod is rejected during wait, binding cycle error handler invoked

8. **PreBind Phase**
   - PreBind plugins run (e.g., volume mounting, network setup)
   - If fails, binding cycle error handler invokes

9. **Bind Phase**
   - Bind plugins run (first to succeed wins, others skipped)
   - DefaultBinder patches pod.spec.nodeName
   - API call sends binding to apiserver
   - If fails, binding cycle error handler invokes

10. **PostBind Phase**
    - PostBind plugins run (informational/cleanup)
    - Event recorded in kubernetes events

11. **Queue Done**
    - SchedulingQueue.Done(podUID) called
    - Pod removed from inFlightPods tracking
    - Any cluster events that occurred during pod's scheduling/binding are processed

12. **Pod Scheduled**
    - Pod with bound nodeName eventually becomes Running

### Interface Contracts

#### **Plugin Interface (Base)**
```go
type Plugin interface {
    Name() string
}
```

#### **PreEnqueuePlugin**
```go
// Called before pod added to activeQ
// Can gate pod from entering queue
PreEnqueue(ctx context.Context, p *v1.Pod) *Status
```

#### **FilterPlugin**
```go
// Return Success if pod fits on node, else Unschedulable/Error
Filter(ctx context.Context, state *CycleState, pod *v1.Pod, nodeInfo *NodeInfo) *Status
```

#### **ScorePlugin**
```go
// Score node (0-100). Higher score = more preferred
// NormalizeScore normalizes scores across all nodes (optional)
Score(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) (int64, *Status)
NormalizeScore(ctx context.Context, state *CycleState, p *v1.Pod, scores NodeScoreList) *Status
```

#### **ReservePlugin**
```go
// Reserve: update state when pod assumed. Idempotent.
// Unreserve: cleanup if scheduling fails later
Reserve(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) *Status
Unreserve(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string)
```

#### **PermitPlugin**
```go
// Return (Status, Timeout)
// Success: proceed to binding
// Wait: hold in WaitingPods until Allow() called by another plugin
// Reject/Error: fail scheduling
Permit(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) (*Status, time.Duration)
```

#### **BindPlugin**
```go
// Bind pod to node. Patch pod.spec.nodeName, etc.
// Return Skip if not handling, Success/Error if handled
Bind(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) *Status
```

#### **EnqueueExtensions (Optional)**
```go
// Plugins that reject pods (PreFilter, Filter, Reserve, Permit) should implement
// to declare which cluster events can make them schedulable again
EventsToRegister() []ClusterEventWithHint
// Each ClusterEventWithHint contains event and optional QueueingHintFn
// QueueingHintFn filters out irrelevant events for efficiency
```

---

## Summary

The Kubernetes scheduler implements a sophisticated plugin-based architecture with **12 extension points** organized into a **two-phase design** (synchronous scheduling cycle + asynchronous binding cycle). The architecture separates concerns across multiple components: a **scheduling queue** manages pod priority and backoff, a **cache** maintains node information and assumed pod state using snapshot+generation approach, and a **framework** orchestrates plugin execution while providing state sharing via CycleState. Pods flow from queue → scheduling cycle (PreFilter → Filter → PostFilter → PreScore → Score → Reserve → Permit) → assume in cache → async binding cycle (WaitOnPermit → PreBind → Bind → PostBind). When scheduling fails, pods are efficiently requeued based on cluster events and plugin-specific queueing hints, implementing a backoff strategy. This design enables high throughput scheduling (multiple pods parallelized), extensibility (custom plugins), and correctness (two-phase avoids binding inconsistencies).
