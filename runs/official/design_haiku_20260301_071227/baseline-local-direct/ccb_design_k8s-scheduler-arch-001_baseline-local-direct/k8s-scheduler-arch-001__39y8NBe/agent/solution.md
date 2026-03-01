# Kubernetes Scheduler Architecture Analysis

## Files Examined

### Core Scheduler Files
- `pkg/scheduler/scheduler.go` — Main scheduler structure initialization, configuration, and setup of the scheduler instance with queue, cache, profiles, and event handlers
- `pkg/scheduler/schedule_one.go` — Main scheduling loop entry point (ScheduleOne, schedulingCycle, bindingCycle) and the core algorithm for filtering, scoring, and binding pods

### Framework Core
- `pkg/scheduler/framework/interface.go` — Framework interfaces defining all plugin types (PreFilter, Filter, PostFilter, PreScore, Score, Reserve, Permit, PreBind, Bind, PostBind) and status codes
- `pkg/scheduler/framework/cycle_state.go` — CycleState data structure for per-scheduling-cycle plugin state storage using sync.Map for thread-safe read-write operations
- `pkg/scheduler/framework/types.go` — Core types like NodeInfo, PreFilterResult, PostFilterResult, Status codes, and framework abstractions

### Framework Runtime Implementation
- `pkg/scheduler/framework/runtime/framework.go` — frameworkImpl structure implementing the Framework interface, with methods to run all plugin extension points (RunPreFilterPlugins, RunFilterPlugins, RunScorePlugins, etc.)
- `pkg/scheduler/framework/runtime/registry.go` — Plugin registry for registering and looking up plugins by name
- `pkg/scheduler/framework/runtime/waiting_pods_map.go` — Management of pods waiting in Permit phase

### Scheduling Queue
- `pkg/scheduler/internal/queue/scheduling_queue.go` — SchedulingQueue interface and PriorityQueue implementation managing three pod queues: activeQ, backoffQ, and unschedulablePods with pod state transitions

### Scheduler Cache
- `pkg/scheduler/internal/cache/interface.go` — Cache interface defining operations like AssumePod, FinishBinding, ForgetPod, AddPod, UpdatePod with pod state machine (Initial → Assumed → Added → Expired/Deleted)
- `pkg/scheduler/internal/cache/cache.go` — cacheImpl implementing pod and node management with assumed pod expiration, node info tracking, and snapshot generation
- `pkg/scheduler/internal/cache/snapshot.go` — Snapshot structure for a consistent view of all node information at the start of a scheduling cycle

### Plugin Framework Support
- `pkg/scheduler/framework/parallelize/` — Parallelization utilities for running plugins concurrently
- `pkg/scheduler/profile/profile.go` — Scheduling profile management for supporting multiple scheduler configurations

## Dependency Chain

### 1. Entry Point: Main Scheduling Loop

**Entry:** `pkg/scheduler/scheduler.go:Scheduler.Run()`
- Starts the SchedulingQueue worker goroutine
- Launches `ScheduleOne()` in a separate goroutine via `wait.UntilWithContext()`

**Calls:** `pkg/scheduler/schedule_one.go:Scheduler.ScheduleOne()`
- Retrieves next unscheduled pod from the SchedulingQueue via `sched.NextPod()`
- Gets the appropriate Framework for the pod's scheduler name via `sched.frameworkForPod()`

### 2. Scheduling Cycle Phase

**Delegates to:** `pkg/scheduler/schedule_one.go:Scheduler.schedulingCycle()`

**Flow:**
1. Calls `sched.SchedulePod()` → delegates to `sched.schedulePod()`

   **In schedulePod():**
   - Updates cache snapshot: `sched.Cache.UpdateSnapshot()` → gets current cluster state
   - Calls `sched.findNodesThatFitPod()` which:

     a. **PreFilter Phase:** `fwk.RunPreFilterPlugins()`
        - Plugins: PreEnqueue, PreFilter
        - May return PreFilterResult to filter node set
        - Returns status (Success/Unschedulable/Error)

     b. **Filter Phase:** `sched.findNodesThatPassFilters()` with parallelization
        - Calls `fwk.RunFilterPluginsWithNominatedPods()` for each node
        - Plugins: Filter
        - Evaluates nominated node first (from previous preemption)
        - Parallelizes node evaluation using `fwk.Parallelizer().Until()`
        - Returns feasible nodes

     c. **Extender Filter:** `findNodesThatPassExtenders()`
        - External extenders can filter nodes

     d. **Scoring Phase:** `prioritizeNodes()`
        - Calls `fwk.RunPreScorePlugins()` — informational, prepares state
        - Calls `fwk.RunScorePlugins()` — runs Score plugins for each node
        - Extenders can also prioritize nodes in parallel
        - Combines all scores (framework + extenders)
        - Calls `selectHost()` to pick best node via reservoir sampling

2. If SchedulePod succeeds, pod gets a suggested host
3. Calls `sched.assume()` to optimistically assume pod on the node
   - Updates Cache.AssumePod() to record assumption
   - Sets pod.Spec.NodeName
   - Deletes nominated node name if present

4. **Reserve Phase:** `fwk.RunReservePluginsReserve()`
   - Plugins: Reserve
   - If fails, calls `fwk.RunReservePluginsUnreserve()` and forgets the pod

5. **Permit Phase (first part):** `fwk.RunPermitPlugins()`
   - Plugins: Permit
   - Can return Success, Wait, or rejection
   - If Wait, pod is added to waiting pods map

6. **Pod Activation:** Activates pods in `podsToActivate` map via `sched.SchedulingQueue.Activate()`

**Returns:** `ScheduleResult` with suggested node, evaluated node count, and feasible node count

### 3. Binding Cycle Phase (Asynchronous)

**If schedulingCycle succeeds, launches async goroutine:**

**Delegates to:** `pkg/scheduler/schedule_one.go:Scheduler.bindingCycle()`

**Flow:**
1. **Permit Wait Resolution:** `fwk.WaitOnPermit()`
   - Waits for all Permit plugins to allow the pod
   - Can reject after timeout

2. **PreBind Phase:** `fwk.RunPreBindPlugins()`
   - Plugins: PreBind
   - Last chance for plugins to reject before binding

3. **Bind Phase:** `sched.bind()`
   - Tries extenders first via `sched.extendersBinding()`
   - Falls back to `fwk.RunBindPlugins()`
   - Plugins: Bind
   - Actually creates the binding object in the API server

4. **Cache Finalization:** `sched.Cache.FinishBinding()`
   - Signals that binding is complete and assumed pod can expire

5. **PostBind Phase:** `fwk.RunPostBindPlugins()`
   - Plugins: PostBind
   - Informational, for cleanup or record-keeping

6. **Pod Activation:** Activates remaining pods in `podsToActivate`

7. **Queue Cleanup:** `sched.SchedulingQueue.Done()` marks pod as no longer processing

### 4. Failure Handling

**If schedulingCycle fails:**

**Calls:** `sched.FailureHandler()` → `sched.handleSchedulingFailure()`

**Flow:**
- PostFilter plugins run to attempt preemption or other remediation
- Pod is rejected and added back to the scheduling queue
- Pod may go to backoffQ or unschedulablePods based on failure type

**If bindingCycle fails:**

**Calls:** `sched.handleBindingCycleError()`

**Flow:**
- Calls `fwk.RunReservePluginsUnreserve()` to clean up state
- Calls `sched.Cache.ForgetPod()` to remove assumption
- Generates AssignedPodDelete event to requeue affected pods
- Calls FailureHandler to handle the binding failure

## Analysis

### Design Patterns Identified

#### 1. **Two-Phase Commit Pattern**
The scheduler uses an optimistic locking pattern with assume-then-bind:
- **Scheduling Cycle**: Assumes pod on a node in the cache (in-memory assumption)
- **Binding Cycle**: Actually commits the assumption by calling the API server
- **Benefit**: Allows asynchronous binding without blocking other scheduling operations
- **Rollback**: If binding fails, assume is rolled back via Cache.ForgetPod()

#### 2. **Plugin Framework with Extension Points**
The framework implements a well-defined extension point pattern:
- **Scheduling Cycle Extension Points** (synchronous):
  1. **PreEnqueue**: Gate pods before entering the queue
  2. **QueueSort**: Order pods in the queue
  3. **PreFilter**: Early rejection or node filtering
  4. **Filter**: Node feasibility checks (replaces old predicates)
  5. **PostFilter**: Preemption and remediation (runs on failure)
  6. **PreScore**: Preparation before scoring
  7. **Score**: Node ranking (replaces old priorities)
  8. **Reserve**: Resource booking before binding
  9. **Permit**: Final gate before binding (can wait)

- **Binding Cycle Extension Points** (asynchronous):
  1. **WaitOnPermit**: Waits for Permit plugins
  2. **PreBind**: Pre-binding validation
  3. **Bind**: Actually bind the pod
  4. **PostBind**: Post-binding actions

#### 3. **Parallelization Strategy**
- Filter plugins run in parallel across nodes for efficiency
- Score plugins run per-node but can be parallelized
- Extenders run in parallel for filtering and scoring
- Early exit when sufficient feasible nodes are found (percentage-based)

#### 4. **Pod Queue State Machine**
Three-queue system with sophisticated state transitions:
```
activeQ        → Currently being considered for scheduling
  ↓
backoffQ       → Temporarily unschedulable, backing off before retry
  ↓
unschedulablePods → Permanently unschedulable, waiting for cluster changes
  ↓
(Event-driven requeue back to activeQ or backoffQ)
```

#### 5. **Cache Pod State Machine**
```
Initial → Assumed → Added → Deleted
            ↓
          Expired (if not confirmed)
```

#### 6. **CycleState for Per-Cycle Plugin Data**
- Each scheduling cycle gets a fresh CycleState
- Plugins write pre-calculated data in PreFilter/PreScore
- Other plugins read this data in Filter/Score phases
- Uses sync.Map for thread-safe concurrent reads
- Cloned for PreScore evaluation (with pod additions/removals)

### Component Responsibilities

#### **Scheduler (scheduler.go)**
- Orchestrates the two scheduling phases (scheduling + binding)
- Manages pod queue and cache lifecycle
- Configures profiles and plugins
- Handles scheduling failures and retries

#### **Framework Runtime (framework/runtime/framework.go)**
- Loads and instantiates plugins
- Calls plugins at appropriate extension points in order
- Aggregates plugin results (e.g., combining scores)
- Manages the waiting pods map for Permit phase

#### **SchedulingQueue (internal/queue/scheduling_queue.go)**
- Maintains pod queues (active, backoff, unschedulable)
- Handles pod state transitions based on scheduling outcomes
- Implements backoff strategy for retries
- Executes EnqueueExtensions for efficient pod requeuing based on cluster events

#### **Cache (internal/cache/cache.go)**
- Maintains current cluster state snapshot
- Tracks assumed pods and their expiration
- Manages pod and node information
- Provides consistent view via Snapshot for scheduling cycle

#### **CycleState (framework/cycle_state.go)**
- Thread-safe storage for per-cycle plugin state
- Allows plugins to share data without locks
- Cloned when evaluating pods with added/removed pods (preemption)

### Data Flow Description

#### **Scheduling Cycle Data Flow**

```
Pod enters SchedulingQueue
    ↓
ScheduleOne() pops pod from queue
    ↓
Cache.UpdateSnapshot() → Snapshot of current node states
    ↓
CycleState created → PreEnqueue plugins run
    ↓
PreFilter plugins → May filter node set, populate CycleState
    ↓
For each node (parallelized):
  Filter plugins → Evaluate feasibility, populate diagnosis
    ↓
Filter Extenders → Additional filtering
    ↓
PreScore plugins → Preparation for scoring
    ↓
For each feasible node:
  Score plugins → Calculate node scores
    ↓
Score Extenders → Additional scoring (parallelized)
    ↓
Combine all scores → Select best node via reservoir sampling
    ↓
Cache.AssumePod() → Optimistically record pod assignment
    ↓
Reserve plugins → Book resources
    ↓
Permit plugins → Final gate (may wait)
    ↓
Return ScheduleResult (node name + metrics)
```

#### **Binding Cycle Data Flow**

```
Async goroutine spawned from ScheduleOne
    ↓
WaitOnPermit() → Wait for Permit plugins
    ↓
PreBind plugins → Final validation before binding
    ↓
Bind plugins / Extenders → Actually send binding to API server
    ↓
Cache.FinishBinding() → Allow assumed pod expiration
    ↓
PostBind plugins → Cleanup and notifications
    ↓
SchedulingQueue.Done() → Mark pod as processed
    ↓
Pod is bound or error handled
```

### Interface Contracts

#### **Plugin Interface Contract**
```
All plugins implement:
- Name() string → returns plugin name

PreFilter plugins:
- PreFilter(ctx, state, pod) (*PreFilterResult, *Status)
- PreFilterExtensions() → for incremental updates

Filter plugins:
- Filter(ctx, state, pod, nodeInfo) *Status

Score plugins:
- Score(ctx, state, pod, nodeName) (int64, *Status)
- ScoreExtensions().NormalizeScore() (optional)

Reserve plugins:
- Reserve(ctx, state, pod, nodeName) *Status
- Unreserve(ctx, state, pod, nodeName)

Permit plugins:
- Permit(ctx, state, pod, nodeName) (*Status, time.Duration)
- Can return Wait to delay binding

Bind plugins:
- Bind(ctx, state, pod, nodeName) *Status
```

#### **Framework Handle Contract**
Plugins receive a Handle providing:
- `SnapshotSharedLister()` → Read cluster state
- `ClientSet()` → Kubernetes API client
- `EventRecorder()` → Record events
- `SharedInformerFactory()` → Watch resources

#### **Status Code Contract**
Plugins return Status with codes:
- `Success` → Proceed
- `Unschedulable` → Pod can't fit here, but might fit elsewhere
- `UnschedulableAndUnresolvable` → Pod can't fit anywhere, skip preemption
- `Wait` → Permit plugins can delay binding
- `Pending` → Scheduling succeeded but plugin waits for external action
- `Error` → Internal error, retry later
- `Skip` → Skip this plugin and related ones

### Efficiency Optimizations

1. **Adaptive Node Sampling**: Evaluates percentage of nodes based on cluster size
2. **Nominated Node Fast-Track**: Tries previously nominated node first after preemption
3. **Early Exit**: Stops searching for feasible nodes once threshold reached
4. **Parallelization**: Filters and scores nodes in parallel
5. **Backoff Strategy**: Unschedulable pods wait before retrying
6. **Snapshot Consistency**: Single snapshot for entire scheduling cycle
7. **CycleState Cloning**: Minimal overhead for preemption evaluation
8. **EnqueueExtensions**: Efficient event-driven requeuing instead of global scanning

## Summary

The Kubernetes scheduler implements a sophisticated two-phase scheduling architecture with an extensible plugin framework. Pods flow through a **scheduling cycle** (finding the best node) followed by an **asynchronous binding cycle** (confirming the binding in the API server). The framework provides 14 extension points across both phases, allowing plugins to influence decisions at each stage. Key architectural decisions include the optimistic assumption model (assume then bind asynchronously), a three-queue prioritization system for managing pod states, and parallelized filtering and scoring across nodes. This design enables the scheduler to make fast, optimal scheduling decisions while supporting preemption, pod priorities, and complex constraint enforcement through a pluggable architecture.
