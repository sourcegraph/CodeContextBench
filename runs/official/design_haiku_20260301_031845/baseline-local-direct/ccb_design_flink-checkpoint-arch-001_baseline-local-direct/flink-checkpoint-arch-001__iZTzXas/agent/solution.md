# Flink Checkpoint Coordination Architecture Analysis

## Files Examined

### JobManager-Side Checkpoint Coordination
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CheckpointCoordinator.java** — Central orchestrator for distributed checkpoint coordination; manages checkpoint lifecycle from trigger through completion, handles barrier distribution to sources, and collects task acknowledgments
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/PendingCheckpoint.java** — Represents an in-flight checkpoint awaiting acknowledgment from all tasks; tracks task states and metadata, implements acknowledgment protocol
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CompletedCheckpoint.java** — Represents a successfully completed checkpoint with finalized state; persisted as metadata and stored in CompletedCheckpointStore
- **flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/Execution.java** — Execution attempt wrapper; exposes triggerCheckpoint() and triggerSynchronousSavepoint() methods that RPC to TaskManager

### Barrier Events and Network Layer
- **flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/CheckpointBarrier.java** — Immutable barrier event carrying checkpoint ID, timestamp, and checkpoint options; serialized and propagated through network streams as monotonically increasing markers

### TaskManager-Side Barrier Processing
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierHandler.java** — Abstract base class for barrier processing; defines processBarrier() contract and notifyCheckpoint() to trigger task-level snapshotting; tracks alignment metrics
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/SingleCheckpointBarrierHandler.java** — Handles both aligned and unaligned checkpoint barriers using a state machine; waits for barriers from all input channels before triggering checkpoint snapshot
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierTracker.java** — Unaligned checkpoint variant that does not block input channels; tracks which channels have sent barriers for each checkpoint and notifies when all barriers received

### Barrier State Machine
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/BarrierHandlerState.java** — State machine interface with states: WaitingForFirstBarrier, CollectingBarriers (aligned), and unaligned variants; defines barrierReceived(), announcementReceived(), and alignment timeout transitions
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/WaitingForFirstBarrier.java** — Initial state waiting for first barrier from any input channel; blocks further data on that channel
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CollectingBarriers.java** — Aligned checkpoint state collecting barriers from remaining channels; blocks them until all barriers arrive
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/AlternatingWaitingForFirstBarrierUnaligned.java** — Unaligned checkpoint state allowing data flow to continue while tracking barriers

### Task-Level Snapshot Coordination
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/SubtaskCheckpointCoordinator.java** — Interface coordinating state snapshots at task level; methods: initInputsCheckpoint() (setup), checkpointState() (snapshot), notifyCheckpointComplete() (finalization)
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/StreamTask.java** — Implements CheckpointableTask; receives triggerCheckpointOnBarrier() from barrier handler and delegates to SubtaskCheckpointCoordinator for state snapshot

## Dependency Chain

### 1. Checkpoint Trigger Path

**Entry Point:** `CheckpointCoordinator.triggerCheckpoint()`
- Called periodically or on-demand; initiates a new checkpoint
- Calls `triggerCheckpointFromCheckpointThread()` with checkpoint properties

**Step 2:** `startTriggeringCheckpoint()`
- Orchestrates asynchronous checkpoint initialization
- Calls `checkpointPlanCalculator.calculateCheckpointPlan()` to determine which tasks must be checkpointed
- Gets next checkpoint ID via `checkpointIdCounter.getAndIncrement()`
- Creates `PendingCheckpoint` with initial task/coordinator/master state tracking

**Step 3:** `triggerCheckpointRequest()`
- Called after pending checkpoint creation succeeds
- Delegates to `triggerTasks()`

**Step 4:** `triggerTasks()`
- Location: `CheckpointCoordinator:836-868`
- Creates `CheckpointOptions` with alignment mode (aligned vs unaligned)
- **For each source task in checkpoint plan:**
  - Calls `execution.triggerCheckpoint(checkpointId, timestamp, checkpointOptions)` (RPC)
  - Collects future for acknowledgment

### 2. Source Task Barrier Injection

**TaskManager receives:** `Task.triggerCheckpointBarrier()`
- Creates `CheckpointBarrier` with barrier ID, timestamp, options
- Injects barrier into source's output gates (network buffers)
- Barrier is serialized and sent to all downstream tasks

### 3. Barrier Propagation through Task Graph

**Barrier travels through network:** Checkpoint barriers are emitted as special events in data streams
- Each input channel receives barriers from upstream operators
- CheckpointBarrier events are deserialized by EventSerializer
- Barriers maintain strict ordering (monotonically increasing IDs)

### 4. Barrier Reception and Alignment (Aligned Checkpoints)

**Downstream Task receives barrier:** `CheckpointBarrierHandler.processBarrier()`
- Path: `SingleCheckpointBarrierHandler:214-235` (for aligned)
- Checks if this is a new checkpoint or duplicate

**State Machine Transitions:**
1. **Initial state:** `WaitingForFirstBarrier`
   - First barrier from any channel triggers `markAlignmentStart()`
   - Channel is marked as blocked (data buffered until checkpoint completes)
   - State transitions to `CollectingBarriers`

2. **Collecting state:** `CollectingBarriers`
   - Subsequent barriers collected from remaining channels
   - Data on those channels is blocked
   - When all channels have sent barriers: `markAlignmentEnd()` and `allBarriersReceivedFuture.complete()`

**Location reference:** `SingleCheckpointBarrierHandler:269-278`
- When `alignedChannels.size() == targetChannelCount`, all barriers received
- Calls `resetAlignmentTimer()` and completes `allBarriersReceivedFuture`

### 5. Checkpoint Snapshot Trigger at Task

**Barrier handler triggers snapshot:** `notifyCheckpoint()`
- Location: `CheckpointBarrierHandler:125-149`
- Constructs `CheckpointMetaData` with barrier ID and timestamps
- Constructs `CheckpointMetricsBuilder` with alignment duration metrics
- **Calls:** `toNotifyOnCheckpoint.triggerCheckpointOnBarrier(checkpointMetaData, checkpointOptions, checkpointMetrics)`
  - `toNotifyOnCheckpoint` is a `CheckpointableTask` (typically `StreamTask`)

### 6. Task State Snapshot

**StreamTask receives trigger:** `triggerCheckpointOnBarrier()`
- Delegates to `SubtaskCheckpointCoordinator.initInputsCheckpoint()` (setup)
- Then calls `SubtaskCheckpointCoordinator.checkpointState()` (execution)
- Operator chain snapshots state asynchronously:
  - Each operator in the chain calls `snapshotState()`
  - State is serialized to configured backend (RocksDB, in-memory, etc.)

### 7. Task Acknowledgment Path

**Task completes snapshot:** After state snapshot finishes, task constructs `AcknowledgeCheckpoint` message containing:
- Checkpoint ID
- Task execution ID
- Subtask state (serialized state handle)
- Checkpoint metrics (alignment duration, bytes processed)

**Message is sent back to JobManager:** RPC call to `CheckpointCoordinator.receiveAcknowledgeMessage()`

### 8. PendingCheckpoint Acknowledgment Collection

**Entry point:** `CheckpointCoordinator.receiveAcknowledgeMessage()`
- Location: `CheckpointCoordinator:1210-1355`
- Validates message (job ID, checkpoint exists)
- Retrieves `PendingCheckpoint` from `pendingCheckpoints` map by ID
- Calls `checkpoint.acknowledgeTask(executionAttemptId, subtaskState, metrics)`

**PendingCheckpoint.acknowledgeTask()** (`PendingCheckpoint:385-462`)
- Removes task from `notYetAcknowledgedTasks`
- Adds to `acknowledgedTasks`
- Stores operator state in `operatorStates` map
- Updates stats with checkpoint metrics
- Returns `TaskAcknowledgeResult.SUCCESS`

**Completion check:** `checkpoint.isFullyAcknowledged()`
- Checks if all three conditions met:
  - All tasks acknowledged: `areTasksFullyAcknowledged()`
  - All operator coordinators acknowledged: `areCoordinatorsFullyAcknowledged()`
  - All master states acknowledged: `areMasterStatesFullyAcknowledged()`

### 9. PendingCheckpoint to CompletedCheckpoint Transition

**When fully acknowledged:** `CheckpointCoordinator.completePendingCheckpoint()`
- Location: `CheckpointCoordinator:1365-1402`

**Step 1:** `completedCheckpointStore.getSharedStateRegistry().checkpointCompleted()`
- Marks shared state as complete in registry

**Step 2:** `finalizeCheckpoint()` → `PendingCheckpoint.finalizeCheckpoint()`
- Location: `PendingCheckpoint:317-365`
- Fills in finished task status: `checkpointPlan.fulfillFinishedTaskStatus()`
- Creates `CheckpointMetadata` with operator states and master states
- Writes metadata via `CheckpointMetadataOutputStream`:
  - Calls `Checkpoints.storeCheckpointMetadata(savepoint, out)`
  - Finalizes location: `out.closeAndFinalizeCheckpoint()`
- Constructs `CompletedCheckpoint` instance
- Marks pending checkpoint as disposed but preserves state

**Step 3:** `addCompletedCheckpointToStoreAndSubsumeOldest()`
- Stores `CompletedCheckpoint` in `CompletedCheckpointStore` (e.g., FileSystemCheckpointStore)
- Subsumes older checkpoints per retention policy
- Cleans up discarded checkpoints

**Step 4:** `reportCompletedCheckpoint()` and notifications
- Reports success to `CheckpointFailureManager`
- Updates statistics in `CheckpointStatsTracker`

**Step 5:** `cleanupAfterCompletedCheckpoint()`
- Sends "checkpoint complete" notifications to all tasks
- Calls `sendAcknowledgeMessages()` to notify tasks they can commit state
- Tasks call `SubtaskCheckpointCoordinator.notifyCheckpointComplete()`

## Analysis

### Design Patterns Identified

1. **Two-Phase Commit Protocol**
   - Phase 1 (Barrier Injection): CheckpointCoordinator sends barrier events to all sources; sources inject barriers into data streams
   - Phase 2 (Acknowledgment): Tasks snapshot state and send acknowledgments back; coordinator finalizes when all acknowledge
   - Provides distributed consistency guarantees: all tasks snapshot same logical point in stream

2. **State Machine Pattern (Barrier Processing)**
   - BarrierHandlerState interface defines states and transitions
   - WaitingForFirstBarrier → CollectingBarriers → (checkpoint triggered) transitions
   - Unaligned variants bypass blocking by using state machine to track barrier receipt without blocking

3. **Future/Promise Pattern**
   - CheckpointCoordinator uses CompletableFutures for asynchronous coordination
   - PendingCheckpoint.onCompletionPromise completes when checkpoint fully acknowledged
   - Enables non-blocking checkpoint orchestration

4. **Visitor Pattern (State Transitions)**
   - Each BarrierHandlerState implements barrierReceived(), announcementReceived()
   - Returns next state, enabling state machine transitions through different aligners

### Component Responsibilities

**JobManager Coordinator Layer:**
- **CheckpointCoordinator:** Orchestrates timing, tracks pending/completed, manages lifecycle
- **PendingCheckpoint:** Aggregates acknowledgments, tracks per-task state, triggers completion
- **CompletedCheckpoint:** Immutable snapshot of successful checkpoint; persisted for recovery

**TaskManager Barrier Processing Layer:**
- **CheckpointBarrierHandler:** Abstract handler unifying aligned/unaligned processing
- **SingleCheckpointBarrierHandler:** Implements barrier alignment waiting; blocks channels
- **CheckpointBarrierTracker:** Alternative handler for unaligned; doesn't block, just tracks
- **BarrierHandlerState:** State machine controlling when to trigger vs. wait for barriers

**Task Execution Layer:**
- **SubtaskCheckpointCoordinator:** Manages state snapshot lifecycle at task level
- **StreamTask:** Entry point for barrier reception; delegates to barrier handler and coordinator
- **OperatorChain:** Each operator snapshots its state (called by SubtaskCheckpointCoordinator)

### Data Flow Description

**Upstream (Coordinator → Source Tasks):**
```
CheckpointCoordinator.triggerCheckpoint()
  ↓
CheckpointCoordinator.triggerTasks() [sends RPC]
  ↓
Execution.triggerCheckpoint() [RPC call]
  ↓
Task.triggerCheckpointBarrier() [receives on TaskManager]
  ↓
CheckpointBarrier created and injected into source output
  ↓
Barrier serialized and sent through network buffers
```

**Barrier Propagation (Source → Downstream Tasks):**
```
Barrier emitted at source
  ↓
Travels through network (network.api.CheckpointBarrier)
  ↓
Deserialized at each downstream task input
  ↓
CheckpointBarrierHandler.processBarrier() receives barrier
  ↓
State machine processes (WaitingForFirstBarrier → CollectingBarriers)
  ↓
When all barriers received: notifyCheckpoint()
```

**Downstream (Task Snapshot → Acknowledgment):**
```
CheckpointBarrierHandler.notifyCheckpoint()
  ↓
StreamTask.triggerCheckpointOnBarrier() [calls barrier handler]
  ↓
SubtaskCheckpointCoordinator.checkpointState()
  ↓
Each operator in OperatorChain snapshots state
  ↓
State persisted to StateBackend (async)
  ↓
AcknowledgeCheckpoint message constructed
  ↓
RPC sent to JobManager
```

**Completion (Acknowledgment → CompletedCheckpoint):**
```
CheckpointCoordinator.receiveAcknowledgeMessage() [RPC endpoint]
  ↓
PendingCheckpoint.acknowledgeTask() [removes from notYetAcknowledged]
  ↓
If isFullyAcknowledged():
  ↓
    CheckpointCoordinator.completePendingCheckpoint()
    ↓
    PendingCheckpoint.finalizeCheckpoint()
    ↓
    Create CompletedCheckpoint (metadata written)
    ↓
    Store in CompletedCheckpointStore
    ↓
    sendAcknowledgeMessages() to all tasks
    ↓
    SubtaskCheckpointCoordinator.notifyCheckpointComplete()
```

### Aligned vs. Unaligned Checkpoint Handling

**Aligned Checkpoints (Exactly-Once Semantics)**
- **Handler:** SingleCheckpointBarrierHandler with state machine
- **Behavior:** Blocks input channels when first barrier received
- **States:**
  1. WaitingForFirstBarrier: First barrier blocks its channel, markAlignmentStart()
  2. CollectingBarriers: Remaining barriers collected, their channels blocked
  3. All barriers received: Snapshot triggered, data processing continues
- **Guarantees:** All in-flight data before checkpoint is processed; exact exactly-once
- **Cost:** Alignment time (latency); may pause processing while waiting for slow channels
- **Location:** `WaitingForFirstBarrier`, `CollectingBarriers` classes

**Unaligned Checkpoints (At-Least-Once Semantics)**
- **Handler:** SingleCheckpointBarrierHandler with unaligned states OR CheckpointBarrierTracker
- **Behavior:** Does NOT block input channels; barriers don't wait
- **States:**
  1. WaitingForFirstBarrier (unaligned variant): Accepts first barrier, doesn't block
  2. CollectingBarriers (unaligned variant): Continues processing, tracks barrier receipt
  3. Snapshot triggered immediately when first barrier received (in-flight data included)
- **Guarantees:** In-flight data included in checkpoint (recovery may replay some data); at-least-once
- **Cost:** Lower latency alignment; no pausing, but state backup larger
- **Location:** `AlternatingWaitingForFirstBarrierUnaligned`, `AlternatingCollectingBarriersUnaligned`

**Aligned Checkpoint with Timeout (Practical Hybrid)**
- **Configuration:** `alignedCheckpointTimeout` setting
- **Behavior:** Start aligned, but if alignment takes too long, switch to unaligned mid-checkpoint
- **Transition:** Method `alignedCheckpointTimeout()` on state machine triggers timeout transition
- **Benefit:** Gets exactly-once when fast, but doesn't stall when channels are slow
- **Location:** `AbstractAlternatingAlignedBarrierHandlerState`

### PendingCheckpoint Lifecycle and Acknowledgment Protocol

**Creation:** `CheckpointCoordinator.createPendingCheckpoint()`
- Initializes with tasks to wait for (`notYetAcknowledgedTasks` map)
- Initializes with operator coordinators to acknowledge
- Initializes with master state identifiers
- Sets up completion future (`onCompletionPromise`)

**Progression (Acknowledgment Phase):**
1. **Initial state:** All tasks in `notYetAcknowledgedTasks`, `acknowledgedTasks` empty
2. **Per acknowledgment:** `acknowledgeTask()` moves task from not-yet to acknowledged, stores state
3. **Fully acknowledged check:** `isFullyAcknowledged()` returns true when:
   ```
   notYetAcknowledgedTasks.isEmpty()
   && notYetAcknowledgedOperatorCoordinators.isEmpty()
   && notYetAcknowledgedMasterStates.isEmpty()
   && !disposed
   ```
4. **Completion trigger:** Once fully acknowledged, coordinator calls `completePendingCheckpoint()`

**Finalization:** `PendingCheckpoint.finalizeCheckpoint()`
- Writes checkpoint metadata to external storage (file system, etc.)
- Creates immutable `CompletedCheckpoint` with all operator states
- Marks self as disposed (but does not delete state)
- Returns new CompletedCheckpoint instance

**State Persistence:**
- PendingCheckpoint keeps state as serialized values (never actual object references)
- State is deserialized only during recovery
- CompletedCheckpoint metadata is persisted; state is referenced by handles (paths/pointers)

**Timeout & Cleanup:**
- PendingCheckpoint has `cancellerHandle` (scheduled timeout)
- If not fully acknowledged within `checkpointTimeout`, aborts via `abortPendingCheckpoint()`
- Disposed checkpoints are removed from `pendingCheckpoints` map after completion/abort

## Summary

Flink's checkpoint coordination implements a **distributed two-phase commit protocol** where the CheckpointCoordinator on the JobManager orchestrates barrier injection through the task graph, with barriers synchronizing all tasks to a consistent state. Barriers propagate through the network as special events while the state machine-based CheckpointBarrierHandler on each task manages alignment (blocking channels or tracking receipt depending on aligned vs. unaligned mode). Once barriers are aligned and received, tasks snapshot state via SubtaskCheckpointCoordinator and send acknowledgments back to the coordinator. The PendingCheckpoint collects task acknowledgments and, once fully acknowledged, finalizes to a CompletedCheckpoint, persisting metadata while notifying tasks that the checkpoint succeeded. This architecture supports both exactly-once (aligned) and at-least-once (unaligned) processing semantics with configurable timeout-based hybrid modes.

