# Flink Checkpoint Coordination Architecture Analysis

## Files Examined

### JobManager-Side Checkpoint Coordination (Runtime)
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CheckpointCoordinator.java** — Central coordinator that triggers checkpoints, maintains pending checkpoints map, receives acknowledgments, and completes checkpoints. Manages two-phase commit lifecycle.
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/PendingCheckpoint.java** — Represents a checkpoint in progress; tracks which tasks have acknowledged, accumulates operator states from acknowledgments, transitions to CompletedCheckpoint once fully acknowledged.
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CompletedCheckpoint.java** — Immutable representation of a successfully completed checkpoint; persists operator states and master hook states to external storage.
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CheckpointCoordinatorGateway.java** — RPC gateway interface for receiving acknowledgments from tasks.

### RPC and Execution Graph Integration
- **flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/Execution.java** — Wraps task execution; implements `triggerCheckpoint()` and `triggerSynchronousSavepoint()` that send RPC messages to TaskExecutor.
- **flink-runtime/src/main/java/org/apache/flink/runtime/taskmanager/Task.java** — TaskManager-side task wrapper; receives `triggerCheckpointBarrier()` RPC call and invokes `CheckpointableTask.triggerCheckpointAsync()`.
- **flink-runtime/src/main/java/org/apache/flink/runtime/messages/checkpoint/AcknowledgeCheckpoint.java** — RPC message from TaskExecutor to CheckpointCoordinator carrying task's state snapshot and metrics.

### Network Barrier Events
- **flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/CheckpointBarrier.java** — Immutable event object representing checkpoint barrier; carries checkpoint ID, timestamp, and checkpoint options (aligned/unaligned flags).
- **flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/serialization/EventSerializer.java** — Serializes/deserializes CheckpointBarrier for network transmission through input channels.
- **flink-runtime/src/main/java/org/apache/flink/runtime/io/network/partition/PipelinedSubpartition.java** — Produces output and injects barriers into result partitions for downstream consumption.

### TaskManager-Side Barrier Processing (Streaming)
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierHandler.java** — Abstract base class defining the barrier handler interface; tracks alignment duration and checkpoint start delay.
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/SingleCheckpointBarrierHandler.java** — Concrete handler implementing **aligned checkpoint** semantics; blocks input channels until barriers received from all sources, then triggers state snapshot.
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierTracker.java** — Concrete handler implementing **unaligned checkpoint** semantics; tracks barriers without blocking; allows data to flow past barriers for at-least-once guarantees.
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/BarrierHandlerState.java** — State machine interface defining state transitions (WaitingForFirstBarrier, CollectingBarriers, etc.) for barrier processing.
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointedInputGate.java** — Wraps input channels and delegates barrier events to CheckpointBarrierHandler for processing.

### Operator-Level Checkpoint Handling
- **flink-runtime/src/main/java/org/apache/flink/runtime/jobgraph/tasks/CheckpointableTask.java** — Interface that operators implement; `triggerCheckpointAsync()` initiates state snapshot; `triggerCheckpointOnBarrier()` called by barrier handler.
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/SubtaskCheckpointCoordinator.java** — Orchestrates operator state snapshots during barrier alignment; collects channel states and operator states into TaskStateSnapshot.

## Dependency Chain

### Phase 1: Checkpoint Trigger (JobManager → TaskManagers)

1. **Entry Point**: `CheckpointCoordinator.triggerCheckpoint()`
   - Location: `CheckpointCoordinator.java:573-575`
   - Initiates periodic or manual checkpoint with specified type
   - Asynchronously creates `PendingCheckpoint` with all tasks that need to acknowledge
   - Registers timeout cancellation

2. **Pending Checkpoint Creation**: `CheckpointCoordinator.createPendingCheckpoint()`
   - Location: `CheckpointCoordinator.java:600-750`
   - Creates new `PendingCheckpoint` object tracking all source and operator tasks
   - Initializes checkpoint storage location
   - Triggers operator coordinator checkpoints asynchronously
   - Schedules master hook state snapshots

3. **RPC Dispatch to TaskExecutors**: `CheckpointCoordinator.triggerTasks()`
   - Location: `CheckpointCoordinator.java:836-868`
   - Iterates through `checkpoint.getCheckpointPlan().getTasksToTrigger()`
   - For each task, calls either:
     - `Execution.triggerCheckpoint()` for asynchronous checkpoints
     - `Execution.triggerSynchronousSavepoint()` for savepoints
   - Waits for all RPC acknowledgments via `FutureUtils.waitForAll()`

4. **Execution RPC Call**: `Execution.triggerCheckpoint()` / `triggerSynchronousSavepoint()`
   - Location: `Execution.java:1070-1086`
   - Delegates to `triggerCheckpointHelper()`
   - Sends RPC to `TaskExecutorGateway.triggerCheckpoint()`
   - Returns CompletableFuture for RPC completion

5. **TaskExecutor Reception**: `Task.triggerCheckpointBarrier()`
   - Location: `Task.java:1360-1425`
   - Receives checkpoint ID, timestamp, checkpoint options
   - Invokes `CheckpointableTask.triggerCheckpointAsync()` on the task's invokable
   - Handles execution state checks and rejection scenarios
   - Calls `declineCheckpoint()` on failure

### Phase 2: Barrier Injection (Sources → Operators)

6. **Source Task Barrier Emission**: `SourceTask` / `StreamSource`
   - Implements `CheckpointableTask.triggerCheckpointAsync()`
   - Creates `CheckpointBarrier` object with checkpoint ID
   - Emits barrier event into all output result partitions
   - Allows downstream operators to receive barriers

7. **Barrier Serialization & Network Transport**:
   - Location: `EventSerializer.java:265-340`
   - `CheckpointBarrier` serialized to ByteBuffer via `EventSerializer.serializeCheckpointBarrier()`
   - Transmitted through network layer in pipelined result partitions
   - Deserialized at downstream input channels

### Phase 3: Barrier Reception & Alignment (TaskManager Side)

8. **Checkpoint Input Gate Reception**: `CheckpointedInputGate.pollNext()`
   - Wraps input gate and intercepts `CheckpointBarrier` events
   - Delegates barriers to `CheckpointBarrierHandler.processBarrier()`
   - Maintains channel indices for multi-input operators

9. **Barrier Handler Processing**: Two implementations based on checkpoint mode

   **A. Aligned Checkpoints** (SingleCheckpointBarrierHandler):
   - Location: `SingleCheckpointBarrierHandler.java:213-279`
   - `processBarrier()`: Receives barrier on a channel
   - Blocks that input channel via `CheckpointableInput.blockChannel()`
   - Tracks received barriers in `alignedChannels` set
   - Monitors alignment timeout via `registerAlignmentTimer()`
   - When all input channels have barriers:
     - `markAlignmentEnd()` records alignment duration
     - Transitions state to trigger checkpoint
     - Calls `notifyCheckpoint()` → `CheckpointableTask.triggerCheckpointOnBarrier()`

   **B. Unaligned Checkpoints** (CheckpointBarrierTracker):
   - Location: `CheckpointBarrierTracker.java:93-151`
   - `processBarrier()`: Tracks barrier without blocking
   - Maintains `pendingCheckpoints` queue tracking partial arrivals
   - When all barriers for a checkpoint ID received:
     - `triggerCheckpointOnAligned()` fires checkpoint
     - Allows data to flow past barriers for at-least-once semantics

10. **State Machine Transitions**: `BarrierHandlerState` implementations
    - Location: `BarrierHandlerState.java:42-79`
    - States: `WaitingForFirstBarrier` → `CollectingBarriers` → checkpoint triggered
    - `barrierReceived()`: Process barrier in current state
    - `alignedCheckpointTimeout()`: Switch to unaligned on timeout
    - `abort()`: Handle checkpoint cancellation

### Phase 4: State Snapshot (Operator Execution)

11. **Checkpoint Notification to Operator**: `CheckpointBarrierHandler.notifyCheckpoint()`
    - Location: `CheckpointBarrierHandler.java:125-149`
    - Creates `CheckpointMetaData` with barrier's checkpoint ID, timestamp
    - Calculates alignment metrics (duration, start delay)
    - Invokes `CheckpointableTask.triggerCheckpointOnBarrier()`

12. **Subtask State Snapshot**: `SubtaskCheckpointCoordinator.checkpointState()`
    - Collects state from all operators in the task
    - Performs synchronous and asynchronous state snapshots
    - Accumulates channel state (InputChannelState, OutputChannelState)
    - Returns `TaskStateSnapshot` with OperatorSubtaskState entries
    - Persists to state backend (RocksDB, MemoryStateBackend, etc.)

### Phase 5: Acknowledgment (TaskManagers → JobManager)

13. **Acknowledgment Message Construction**: `RuntimeEnvironment.acknowledgeCheckpoint()`
    - Location: `RuntimeEnvironment.java:336-349`
    - Collects checkpoint metrics and task state snapshot
    - Constructs `AcknowledgeCheckpoint` RPC message
    - Calls `CheckpointResponder.acknowledgeCheckpoint()`

14. **RPC Dispatch to JobManager**: `RpcCheckpointResponder.acknowledgeCheckpoint()`
    - Location: `RpcCheckpointResponder.java:43-56`
    - Sends `AcknowledgeCheckpoint` message to `CheckpointCoordinatorGateway`
    - Includes:
      - JobID, ExecutionAttemptID, checkpoint ID
      - TaskStateSnapshot (operator and channel states)
      - CheckpointMetrics (alignment duration, bytes persisted, etc.)

15. **JobManager Reception**: `CheckpointCoordinator.receiveAcknowledgeMessage()`
    - Location: `CheckpointCoordinator.java:1210-1355`
    - Validates message against current job and pending checkpoints
    - Registers shared states from subtask state
    - Calls `PendingCheckpoint.acknowledgeTask()` to record acknowledgment

### Phase 6: Checkpoint Completion (Two-Phase Commit Finalization)

16. **Task Acknowledgment Recording**: `PendingCheckpoint.acknowledgeTask()`
    - Location: `PendingCheckpoint.java:385-462`
    - Removes task from `notYetAcknowledgedTasks` map
    - Adds ExecutionAttemptID to `acknowledgedTasks` set
    - Accumulates OperatorState from TaskStateSnapshot into pending checkpoint's operator states
    - Returns `TaskAcknowledgeResult` (SUCCESS, DUPLICATE, UNKNOWN, DISCARDED)
    - Increments `numAcknowledgedTasks` counter
    - Records checkpoint metrics and statistics

17. **Completion Check**: `CheckpointCoordinator.maybeCompleteCheckpoint()`
    - Location: `CheckpointCoordinator.java:1100-1117`
    - Checks if `checkpoint.isFullyAcknowledged()`:
      - All tasks acknowledged
      - All operator coordinators acknowledged
      - All master hook states acknowledged
    - If all three conditions met, calls `completePendingCheckpoint()`

18. **Pending Checkpoint Finalization**: `CheckpointCoordinator.completePendingCheckpoint()`
    - Location: `CheckpointCoordinator.java:1365-1402`
    - Calls `PendingCheckpoint.finalizeCheckpoint()`:
      - Calls `checkpointPlan.fulfillFinishedTaskStatus()` for finished operators
      - Writes checkpoint metadata to storage via `CheckpointMetadata` serialization
      - Invokes `CheckpointMetadataOutputStream.closeAndFinalizeCheckpoint()` to persist metadata
    - Receives `CompletedCheckpoint` object from finalization
    - Adds completed checkpoint to `CompletedCheckpointStore` via `addCompletedCheckpointToStoreAndSubsumeOldest()`
    - Removes pending checkpoint from `pendingCheckpoints` map
    - Subsumes older pending checkpoints

19. **Completion Notification & Stats**: `CheckpointCoordinator.reportCompletedCheckpoint()`
    - Location: `CheckpointCoordinator.java:1404-1419`
    - Logs checkpoint statistics (size, duration, end-to-end latency)
    - Calls `failureManager.handleCheckpointSuccess()` for retry mechanism updates
    - Reports stats to `CheckpointStatsTracker`

20. **Task Commit Notification**: `CheckpointCoordinator.sendAcknowledgeMessages()`
    - Location: `CheckpointCoordinator.java:1439-1443`
    - Iterates through `checkpoint.getCheckpointPlan().getTasksToCommitTo()`
    - Sends `notifyCheckpointComplete()` RPC to each task
    - Allows tasks to release resources held during checkpoint
    - Returns cancelled checkpoint ID for subsumption cleanup

21. **CompletedCheckpoint Creation**: `PendingCheckpoint.finalizeCheckpoint()`
    - Location: `PendingCheckpoint.java:317-365`
    - **Two-Phase Commit Completion:**
      - Phase 1: Accumulated all operator states from task acknowledgments
      - Phase 2: Finalized states, persisted metadata, created immutable snapshot
    - Constructs `CompletedCheckpoint` with:
      - Accumulated OperatorState map
      - Master hook states
      - Checkpoint properties and storage location
      - Metadata handle pointing to persisted metadata file
    - Marks `PendingCheckpoint` as disposed (state cleanup)
    - Returns `CompletedCheckpoint` for store and future completion

## Analysis

### Design Patterns Identified

#### 1. **Two-Phase Distributed Commit Protocol**
Flink implements a two-phase commit pattern:
- **Phase 1 (Prepare)**: Trigger checkpoints at all tasks, collect state snapshots
  - JobManager sends trigger messages to all source tasks
  - Barriers propagate downstream through the task graph
  - Each task captures operator state and channel state
  - Tasks acknowledge with their state snapshots
- **Phase 2 (Commit)**: Once all acknowledgments received, finalize and persist
  - Checkpoint coordinator aggregates all received states
  - Persists metadata to external storage
  - Sends commit notification to all tasks
  - Tasks can release temporary buffers and resources

#### 2. **Barrier-Based Alignment (Chandy-Lamport Snapshot)**
The barrier mechanism implements the Chandy-Lamport distributed snapshot algorithm:
- **Barriers as markers**: CheckpointBarrier objects flow through the same network channels as data
- **Alignment**: Operators block input channels until barriers received from all sources
- **In-flight data capture**: Barriers establish consistent cut points in the data stream
- **Exactly-once guarantee**: Synchronized barrier alignment ensures no data is processed twice

#### 3. **Pluggable Handler Architecture (Strategy Pattern)**
`CheckpointBarrierHandler` has multiple implementations for different semantics:
- `SingleCheckpointBarrierHandler`: Aligned checkpoints with exactly-once guarantees
- `CheckpointBarrierTracker`: Unaligned/at-least-once checkpoints with lower latency
- `BarrierHandlerState`: State machine for barrier processing logic transitions

#### 4. **Asynchronous RPC-Based Coordination**
All coordination between JobManager and TaskExecutors is asynchronous:
- `Execution.triggerCheckpoint()` returns `CompletableFuture<Acknowledge>`
- `CheckpointCoordinator` uses `FutureUtils.waitForAll()` to aggregate RPC futures
- `receiveAcknowledgeMessage()` processes acknowledgments out-of-order
- Enables non-blocking, scalable coordination

#### 5. **Future-Based Lifecycle Management**
`PendingCheckpoint` uses `CompletableFuture<CompletedCheckpoint>` for async completion:
- Callers register callbacks via `.thenAccept()`
- Non-blocking wait for checkpoint completion
- Exception propagation for failure handling

### Component Responsibilities

**CheckpointCoordinator (JobManager)**:
- Triggers checkpoints at configured intervals or on-demand
- Manages lifecycle of pending and completed checkpoints
- Receives and processes acknowledgments from tasks
- Decides when checkpoint is complete and can be committed
- Persists completed checkpoint metadata
- Handles checkpoint timeouts and failures

**PendingCheckpoint**:
- Tracks which tasks need to acknowledge
- Accumulates operator states from task acknowledgments
- Finalizes checkpoint by writing metadata
- Transitions to CompletedCheckpoint once all tasks acknowledged

**CompletedCheckpoint**:
- Immutable snapshot of checkpoint state
- Contains all operator states keyed by OperatorID
- Persisted to external storage system
- Used for recovery on job restart

**Execution (ExecutionGraph)**:
- Represents single execution attempt of a task vertex
- Sends RPC trigger message to TaskExecutor
- Implements TaskActions interface for task control

**Task (TaskManager)**:
- Receives checkpoint trigger RPC
- Invokes CheckpointableTask.triggerCheckpointAsync()
- Collects state snapshots from operators
- Sends acknowledgment RPC back to JobManager

**SingleCheckpointBarrierHandler**:
- Processes barrier events on input channels
- Blocks input channels until all barriers received (alignment)
- Maintains state machine for barrier processing
- Tracks alignment duration and checkpoint start delay
- Triggers state snapshot when all barriers aligned

**CheckpointBarrierTracker**:
- Tracks barriers without blocking input channels
- Enables unaligned checkpoints for lower latency
- Triggers checkpoint when all barriers received
- Discards data after checkpoint to implement at-least-once

**SubtaskCheckpointCoordinator**:
- Orchestrates operator state snapshots
- Collects channel states (InputChannelState, OutputChannelState)
- Manages state backend interactions
- Accumulates metrics (bytes persisted, sync/async duration)

### Data Flow Description

**Upstream (Trigger to Execution)**:
```
CheckpointCoordinator.triggerCheckpoint()
  → createPendingCheckpoint() [creates PendingCheckpoint tracking tasks]
  → triggerTasks() [iterates checkpoint.getTasksToTrigger()]
    → Execution.triggerCheckpoint() [RPC]
      → TaskExecutor.triggerCheckpoint() [RPC to TaskManager]
        → Task.triggerCheckpointBarrier() [invokes CheckpointableTask]
          → StreamTask.triggerCheckpointAsync() [sources emit barriers]
```

**Lateral (Barrier Propagation)**:
```
SourceTask emits CheckpointBarrier
  → ResultPartition.enqueueEvent(barrier)
    → Serialized via EventSerializer.serializeCheckpointBarrier()
    → Transmitted through network layer
  → Downstream InputGate receives barrier
    → CheckpointedInputGate.pollNext() [intercepts barrier]
      → CheckpointBarrierHandler.processBarrier() [routes based on implementation]
```

**Downward (Snapshot to Acknowledgment)**:
```
Barrier collected on all input channels
  → CheckpointBarrierHandler.notifyCheckpoint()
    → CheckpointableTask.triggerCheckpointOnBarrier()
      → SubtaskCheckpointCoordinator.checkpointState()
        → Operator snapshots + channel states → TaskStateSnapshot
        → State backend persistence (async)
  → CheckpointMetrics + TaskStateSnapshot
    → RuntimeEnvironment.acknowledgeCheckpoint()
      → RpcCheckpointResponder.acknowledgeCheckpoint() [RPC]
        → CheckpointCoordinator.receiveAcknowledgeMessage()
```

**Completion (Aggregation to Finalization)**:
```
CheckpointCoordinator.receiveAcknowledgeMessage()
  → PendingCheckpoint.acknowledgeTask() [records ack]
  → checkpoint.isFullyAcknowledged()? [all tasks + coordinators + masters]
    → completePendingCheckpoint()
      → PendingCheckpoint.finalizeCheckpoint()
        → Metadata serialization + storage
        → CompletedCheckpoint creation
      → addCompletedCheckpointToStore()
      → sendAcknowledgeMessages() [notify tasks]
        → Task.notifyCheckpointComplete() [RPC]
```

### Interface Contracts Between Components

**CheckpointCoordinator ↔ Execution**:
- `Execution.triggerCheckpoint(long id, long ts, CheckpointOptions opts)` → `CompletableFuture<Acknowledge>`
- JobManager provides checkpoint metadata; TaskManager confirms RPC delivery

**Execution ↔ Task**:
- RPC: `TaskExecutorGateway.triggerCheckpoint(ExecutionAttemptID, long id, long ts, CheckpointOptions)`
- Task invokes user code checkpoint logic via `CheckpointableTask` interface

**CheckpointCoordinator ↔ CheckpointCoordinatorGateway**:
- `receiveAcknowledgeMessage(AcknowledgeCheckpoint msg)` ← RPC from TaskExecutor
- `receiveDeclineMessage(DeclineCheckpoint msg)` ← RPC on failure

**PendingCheckpoint ↔ TaskStateSnapshot**:
- `acknowledgeTask(ExecutionAttemptID, TaskStateSnapshot states, CheckpointMetrics metrics)`
- Accumulates per-subtask states into map keyed by OperatorID

**CheckpointBarrierHandler ↔ CheckpointableTask**:
- `notifyCheckpoint(CheckpointBarrier barrier)` calls `triggerCheckpointOnBarrier(CheckpointMetaData, CheckpointOptions, CheckpointMetrics)`
- Handler controls when checkpoint is triggered; task controls state snapshot

**BarrierHandlerState ↔ SingleCheckpointBarrierHandler**:
- State machine interface: `barrierReceived()`, `alignedCheckpointTimeout()`, `abort()`, `endOfPartitionReceived()`
- Controller callback: `triggerGlobalCheckpoint()`, `initInputsCheckpoint()`, `isTimedOut()`

### Aligned vs Unaligned Checkpoint Barrier Handling

**SingleCheckpointBarrierHandler (Aligned)**:
- **Blocking**: When first barrier received, blocks that channel via `CheckpointableInput.blockChannel()`
- **Alignment phase**: Waits for barriers from all input channels
- **Exactly-once**: No data processed after barrier until checkpoint complete
- **Latency impact**: Alignment can stall operators if input streams have different rates
- **State machine**: WaitingForFirstBarrier → AllBarriersReceived → trigger checkpoint

**CheckpointBarrierTracker (Unaligned)**:
- **Non-blocking**: Processes barriers without blocking input channels
- **At-least-once**: Data continues flowing; processed after barriers can be reprocessed on recovery
- **Lower latency**: Not affected by stream rate imbalance
- **Tracking**: Maintains queue of partial checkpoints; tracks which channels sent barriers
- **Subsumption**: Older incomplete checkpoints discarded when newer checkpoint completes

### PendingCheckpoint Lifecycle

1. **Creation**: `new PendingCheckpoint()` with initial state:
   - `notYetAcknowledgedTasks` = all tasks from CheckpointPlan
   - `acknowledgedTasks` = empty
   - `operatorStates` = empty
   - `pendingCheckpointStats` = tracking structure

2. **Accumulation**: Each acknowledgment calls `acknowledgeTask()`:
   - Moves ExecutionAttemptID from `notYetAcknowledgedTasks` to `acknowledgedTasks`
   - Merges operator states into `operatorStates` map
   - Updates metrics (alignment duration, bytes persisted, etc.)
   - Increments `numAcknowledgedTasks`

3. **Completion Check**: After each acknowledgment:
   - `checkpoint.isFullyAcknowledged()` checks three conditions:
     - `areTasksFullyAcknowledged()`: `notYetAcknowledgedTasks.isEmpty()`
     - `areCoordinatorsFullyAcknowledged()`: `notYetAcknowledgedOperatorCoordinators.isEmpty()`
     - `areMasterStatesFullyAcknowledged()`: `notYetAcknowledgedMasterStates.isEmpty()`

4. **Finalization**: When fully acknowledged:
   - `finalizeCheckpoint()` writes metadata
   - Disposes pending checkpoint (releases temporary resources)
   - Creates immutable `CompletedCheckpoint`

5. **Failure Path**:
   - `abortPendingCheckpoint()` on decline/timeout
   - Discards pending checkpoint without persisting
   - Calls `discardSubtaskState()` to clean up state handles

### Acknowledgment-Based Completion Protocol

**RPC-based acknowledgment flow**:
1. Task completes checkpoint: state snapshot ready
2. Sends `AcknowledgeCheckpoint` RPC message with:
   - Job ID, Execution Attempt ID, Checkpoint ID
   - TaskStateSnapshot (per-operator states + channel states)
   - CheckpointMetrics (alignment duration, bytes, durations)
3. JobManager receives acknowledgment
4. Validates against known pending checkpoint
5. Records acknowledgment in PendingCheckpoint
6. Checks if all tasks acknowledged
7. If yes, initiates completion phase: finalize + persist + notify

**Idempotency & ordering**:
- Acknowledgments can arrive out-of-order (async RPC)
- Duplicate detection: `TaskAcknowledgeResult.DUPLICATE` if already acknowledged
- Unknown task detection: `TaskAcknowledgeResult.UNKNOWN` for task failures/retries
- Discarded checkpoint detection: `TaskAcknowledgeResult.DISCARDED` if checkpoint already failed

## Summary

Flink's checkpoint coordination architecture implements a **two-phase distributed commit protocol** where the JobManager (CheckpointCoordinator) triggers checkpoints by injecting CheckpointBarrier events into the data stream. These barriers flow through all tasks, establishing consistent snapshot points via the Chandy-Lamport algorithm. **Aligned barriers** (SingleCheckpointBarrierHandler) block channels until all input barriers received, ensuring exactly-once semantics. **Unaligned barriers** (CheckpointBarrierTracker) allow data to flow past barriers for lower latency with at-least-once guarantees. Tasks collect operator and channel state snapshots triggered by barrier arrival, then acknowledge to the JobManager with accumulated state. Once the CheckpointCoordinator receives acknowledgments from all tasks, it finalizes the PendingCheckpoint by writing metadata to persistent storage and creating a CompletedCheckpoint, implementing a complete two-phase commit that ensures consistent distributed snapshots of all state.
