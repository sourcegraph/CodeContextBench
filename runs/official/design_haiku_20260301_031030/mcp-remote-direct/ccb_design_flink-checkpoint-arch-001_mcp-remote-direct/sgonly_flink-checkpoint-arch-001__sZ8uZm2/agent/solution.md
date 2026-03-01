# Flink Checkpoint Coordination Architecture Analysis

## Files Examined

### Core Coordinator Components
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CheckpointCoordinator.java** — JobManager-side coordinator that orchestrates distributed checkpoints, manages PendingCheckpoint lifecycle, triggers barriers, and collects acknowledgments
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/PendingCheckpoint.java** — Intermediate checkpoint state tracking all task acknowledgments and state snapshots; transitions to CompletedCheckpoint upon full acknowledgment
- **flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CompletedCheckpoint.java** — Final checkpoint state stored with metadata and state handles after all acknowledgments received

### Barrier Event and Transport
- **flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/CheckpointBarrier.java** — Barrier event containing checkpoint ID, timestamp, and CheckpointOptions; propagated through network as markers between data records
- **flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/serialization/EventSerializer.java** — Serialization layer for checkpoint barriers on network channels

### Barrier Handlers (Alignment Strategies)
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierHandler.java** — Abstract base for all barrier handlers; defines processBarrier() interface and tracks alignment metrics (duration, bytes processed)
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/SingleCheckpointBarrierHandler.java** — Implements aligned/unaligned checkpoint barriers; blocks or buffers data based on BarrierHandlerState; used for exactly-once semantics with single-checkpoint-at-a-time tracking
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierTracker.java** — Tracks multiple barriers without blocking; does not hold post-checkpoint data; used for at-least-once semantics; monitors barrier arrival from all channels

### Task-Side Execution
- **flink-runtime/src/main/java/org/apache/flink/runtime/taskmanager/Task.java** — TaskManager-side task wrapper; receives triggerCheckpointBarrier() RPC and delegates to invokable; coordinates checkpoint decline/completion notifications
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/StreamTask.java** — Streaming task implementation; implements triggerCheckpointAsync() and triggerCheckpointOnBarrier(); orchestrates operator checkpoint through SubtaskCheckpointCoordinator
- **flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/Execution.java** — Execution vertex in job graph; holds RPC handle to TaskManager and calls triggerCheckpoint() RPC on Task

### Input/Output Management
- **flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/BarrierHandlerState.java** — State machine defining barrier handler behavior (WaitingForFirstBarrier, AlignedBarrier, UnalignedBarrier states)
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/runtime/tasks/MultipleInputStreamTask.java** — Multi-input streaming task variant; emits barriers to source inputs and triggers checkpoint propagation

### RPC Interfaces and Messaging
- **flink-runtime/src/main/java/org/apache/flink/runtime/jobmaster/RpcTaskManagerGateway.java** — RPC gateway from JobMaster to TaskManager; provides triggerCheckpoint(), notifyCheckpointOnComplete(), notifyCheckpointAborted() methods
- **flink-runtime/src/main/java/org/apache/flink/runtime/messages/checkpoint/AcknowledgeCheckpoint.java** — RPC message from TaskManager to JobMaster containing task state, metrics, and completion status

## Dependency Chain

### Phase 1: Checkpoint Trigger (JobManager → Sources)

1. **Entry Point**: `CheckpointCoordinator.triggerCheckpoint(CheckpointType)`
   - User or periodic scheduler invokes checkpoint trigger
   - Calls: `CheckpointCoordinator.triggerCheckpointFromCheckpointThread()`

2. **Create Pending Checkpoint**: `CheckpointCoordinator.createPendingCheckpoint()`
   - Allocates new checkpoint ID via `CheckpointIDCounter.getAndIncrement()`
   - Creates `PendingCheckpoint` with list of tasks requiring acknowledgment
   - Collects `CheckpointPlan` (which tasks to trigger, which to commit)

3. **Initialize Storage Location**: `CheckpointCoordinator.initializeCheckpointLocation()`
   - Prepares checkpoint storage directory
   - Sets `CheckpointStorageLocation` on PendingCheckpoint

4. **Snapshot Coordinator State**: `OperatorCoordinatorCheckpoints.triggerAndAcknowledgeAllCoordinatorCheckpoints()`
   - Checkpoints any OperatorCoordinators (source coordinators, etc.)
   - Ensures external source state is synchronized

5. **Create CheckpointOptions**: `CheckpointCoordinator.triggerTasks()`
   - Builds `CheckpointOptions` (unaligned, aligned timeout, savepoint format)
   - Iterates through all tasks in `CheckpointPlan.getTasksToTrigger()`

6. **RPC Dispatch to Tasks**: `Execution.triggerCheckpoint()` or `Execution.triggerSynchronousSavepoint()`
   - Calls `TaskManagerGateway.triggerCheckpoint(checkpointID, timestamp, CheckpointOptions)`
   - RPC to remote Task on TaskManager

### Phase 2: Source Barrier Emission (TaskManager)

7. **Task Receives RPC**: `Task.triggerCheckpointBarrier()`
   - Validates task is RUNNING
   - Creates `CheckpointMetaData` with checkpoint ID and timestamp
   - Calls: `((CheckpointableTask) invokable).triggerCheckpointAsync()`

8. **Stream Task Handles Async Trigger**: `StreamTask.triggerCheckpointAsync()`
   - Injects trigger into mailbox for task thread
   - Returns CompletableFuture indicating acceptance

9. **Source Emits Barriers**: `MultipleInputStreamTask.emitBarrierForSources()`
   - Iterates through all source inputs
   - Injects `CheckpointBarrier` into source buffers
   - Barriers appear as events in the stream between data records
   - Sources also emit `CancelCheckpointMarker` if checkpoint cancelled

### Phase 3: Barrier Propagation Through DAG (Network Layer)

10. **Barrier Transport**: `EventSerializer.serializeCheckpointBarrier()` → Network → `EventSerializer.deserializeCheckpointBarrier()`
    - Barriers serialized as events in pipelined subpartitions
    - Delivered to downstream tasks via NetworkEnvironment

11. **Downstream Tasks Receive Barriers**:
    - Each input channel receives `CheckpointBarrier` event
    - Non-source tasks do not trigger immediately; barriers are processed by barrier handler

### Phase 4: Barrier Alignment (Downstream Tasks)

12. **Barrier Handler Processing**: `CheckpointBarrierHandler.processBarrier(CheckpointBarrier, InputChannelInfo)`
    - **Aligned Checkpoint** (`SingleCheckpointBarrierHandler`):
      - On first barrier arrival: blocks/buffers further data on that channel
      - Tracks barriers from each input channel
      - Once all N input channels have sent the barrier:
        - Alignment complete → calls `notifyCheckpoint(barrier)`
    - **At-Least-Once** (`CheckpointBarrierTracker`):
      - Does not block channels
      - Simply tracks barrier arrival count
      - Once all barriers received: calls `notifyCheckpoint(barrier)`

13. **Notify Checkpoint Handler**: `CheckpointBarrierHandler.notifyCheckpoint()`
    - Creates `CheckpointMetaData` from barrier
    - Calls: `CheckpointableTask.triggerCheckpointOnBarrier()`

### Phase 5: Operator State Snapshot (Task-Side)

14. **Trigger Operator Checkpoint**: `StreamTask.triggerCheckpointOnBarrier()`
    - Checks task is still RUNNING
    - Calls: `SubtaskCheckpointCoordinator.startCheckpointAsync()`

15. **Snapshot Operator Chain**: `SubtaskCheckpointCoordinator.startCheckpointAsync()`
    - Iterates through all operators in task chain
    - Calls `SnapshotFuture` for each operator's state (keyed state, operator state)
    - Collects `TaskStateSnapshot` containing operator-to-state mappings

16. **Async State Persistence**: State backend (`RocksDBStateBackend`, `HashMapStateBackend`)
    - Takes synchronized snapshot (consistent point-in-time)
    - Persists to configured backend (RocksDB, HDFS, S3, etc.)
    - Returns `StreamStateHandle` for each state component

17. **Broadcast Barrier to Outputs**: `TaskToOperatorInput.emitBarrier()`
    - After checkpoint complete, downstream operator also emits barrier
    - Barriers propagate downstream as inter-operator signals

### Phase 6: Acknowledgment & Completion (TaskManager → JobManager)

18. **Send Acknowledgment**: `CheckpointResponder.acknowledgeCheckpoint()`
    - Creates `AcknowledgeCheckpoint` message with:
      - Checkpoint ID
      - Task execution ID
      - `TaskStateSnapshot` (operator states)
      - `CheckpointMetrics` (alignment duration, bytes processed)
    - Sends RPC to JobMaster's `CheckpointCoordinator.receiveAcknowledgeMessage()`

19. **Receive & Record Acknowledgment**: `CheckpointCoordinator.receiveAcknowledgeMessage()`
    - Validates checkpoint still pending
    - Calls: `PendingCheckpoint.acknowledgeTask(executionAttemptId, taskStateSnapshot, metrics)`
    - `PendingCheckpoint.acknowledgeTask()` returns `TaskAcknowledgeResult` (SUCCESS, DUPLICATE, UNKNOWN, DISCARDED)
    - Registers shared states to `SharedStateRegistry`
    - Increments acknowledgment counter

20. **Check Completion**: `PendingCheckpoint.isFullyAcknowledged()`
    - Checks: all tasks acknowledged AND all operator coordinators acknowledged AND all master states acknowledged
    - If true, initiates checkpoint finalization

### Phase 7: Checkpoint Finalization & Metadata Storage

21. **Finalize Checkpoint**: `CheckpointCoordinator.completePendingCheckpoint()`
    - Calls: `PendingCheckpoint.finalizeCheckpoint()`
    - `PendingCheckpoint.finalizeCheckpoint()` creates `CheckpointMetadata` containing:
      - All `OperatorState` objects (keyed states, operator states per subtask)
      - Master hook states
      - Checkpoint properties
    - Serializes metadata and writes to storage via `CheckpointMetadataOutputStream`
    - Calls: `out.closeAndFinalizeCheckpoint()` → returns `CompletedCheckpointStorageLocation`
    - Creates `CompletedCheckpoint` object with all metadata and state handles

22. **Store Completed Checkpoint**: `CheckpointCoordinator.addCompletedCheckpointToStoreAndSubsumeOldest()`
    - Adds checkpoint to `CompletedCheckpointStore` (typically `DefaultCompletedCheckpointStore`)
    - Subsumes older checkpoints (garbage collection)
    - Returns new checkpoint to caller

23. **Report Completion Stats**: `CheckpointCoordinator.reportCompletedCheckpoint()`
    - Updates failure manager
    - Reports statistics to `CheckpointStatsTracker`
    - Logs checkpoint completion

### Phase 8: Notification to Tasks (Commit)

24. **Notify Checkpoint Complete**: `CheckpointCoordinator.sendAcknowledgeMessages()`
    - For each task in `CheckpointPlan.getTasksToCommitTo()`:
      - Calls: `Execution.notifyCheckpointOnComplete(checkpointId, timestamp)`
      - RPC: `TaskManagerGateway.notifyCheckpointOnComplete()` → `Task.notifyCheckpointComplete()`

25. **Task Receives Completion Notification**: `Task.notifyCheckpointComplete()`
    - Injects notification into mailbox
    - Calls: `StreamTask.notifyCheckpointComplete(checkpointId)`
    - `SubtaskCheckpointCoordinator.notifyCheckpointComplete(checkpointId)`
    - Operators notified via `notifyCheckpointComplete()` callback
    - Operators can commit external transactional writes (Kafka exactly-once, S3 multi-part upload, etc.)

## Analysis

### Design Patterns Identified

#### 1. **Distributed Two-Phase Commit Protocol**
- **Phase 1 (Prepare)**: Checkpoint trigger → barrier propagation → state snapshot
  - CheckpointCoordinator initiates and waits for all tasks to snapshot
  - Guarantees consistent global checkpoint across all tasks
- **Phase 2 (Commit)**: All acknowledgments collected → finalization → notification
  - JobManager makes commitment decision (when all acks received)
  - Notifies tasks to commit external state

#### 2. **State Machine Pattern (Barrier Handler)**
```
WaitingForFirstBarrier
  ↓ (on first barrier)
AlignedBarrier (blocks channels, waits for all)
  ↓ (on all barriers aligned)
AlignedCheckpoint (or UnalignedCheckpoint state)
  ↓ (after snapshot)
WaitingForNextCheckpoint
```
This ensures exactly-once semantics by aligning all inputs before triggering snapshot.

#### 3. **Async/Future-based Orchestration**
- `CheckpointCoordinator` uses `CompletableFuture` chains to orchestrate:
  - ID generation → pending creation → coordinator snapshots → master states → task triggers → all acks → finalization
- Non-blocking design prevents JobManager thread starvation
- Executor threads handle I/O-bound operations

#### 4. **RPC Callback Pattern**
- Checkpoint trigger sent via RPC (async fire-and-forget)
- Acknowledgments collected via separate RPC messages
- Completion notifications pushed back via RPC
- Decouples task execution timeline from coordinator

### Component Responsibilities

#### **CheckpointCoordinator (JobManager)**
- **Orchestration**: Decides when to trigger checkpoints (periodic or manual)
- **Coordination**: Manages checkpoint IDs, tracks which tasks must acknowledge
- **Decision Making**: Determines when checkpoint is complete (all acks received)
- **Finalization**: Writes checkpoint metadata, manages storage
- **Cleanup**: Subsumes old checkpoints, garbage collects state

#### **PendingCheckpoint**
- **State Collection**: Accumulates task acknowledgments and operator states
- **Aggregation**: Merges `TaskStateSnapshot` objects from multiple tasks
- **Validation**: Checks all required acknowledgments received
- **Finalization**: Creates final `CheckpointMetadata` and `CompletedCheckpoint`

#### **CheckpointBarrierHandler (TaskManager)**
- **Alignment Enforcement**: Ensures barriers from all inputs arrive (for aligned checkpoints)
- **Data Buffering**: Buffers post-barrier data until alignment complete (for exactly-once)
- **Metrics Collection**: Tracks alignment duration, bytes processed during alignment
- **Notification Dispatch**: Invokes actual checkpoint when alignment ready

#### **StreamTask**
- **Barrier Processing**: Receives barriers from network, dispatches to operator chain
- **State Snapshots**: Orchestrates operator state capture
- **Acknowledgment**: Collects task state and sends back to coordinator
- **Completion Notification**: Receives commit signal and notifies operators

#### **Network Layer**
- **Barrier Transport**: Delivers barriers as special events between data records
- **FIFO Ordering**: Ensures barriers maintain temporal causality
- **Serialization**: Converts barriers to/from network format

### Data Flow Description

#### **Checkpoint Trigger Flow**
```
External Trigger (REST API / periodic timer)
    ↓
CheckpointCoordinator.triggerCheckpoint(CheckpointType)
    ↓ [ID generation + PendingCheckpoint creation]
CreatePendingCheckpoint()
    ↓ [Storage initialization]
InitializeCheckpointLocation()
    ↓ [Operator coordinator snapshots]
TriggerOperatorCoordinatorCheckpoints()
    ↓ [Master hook snapshots]
SnapshotMasterState()
    ↓ [Build checkpoint options]
CreateCheckpointOptions()
    ↓ [RPC to source tasks]
Execution.triggerCheckpoint() [for each source]
    ↓ [Network RPC]
Task.triggerCheckpointBarrier()
    ↓ [Inject barrier into source]
StreamTask.triggerCheckpointAsync()
    ↓ [Emit barrier]
SourceOperator.emitBarrier()
    ↓ [Barrier in network stream]
CheckpointBarrier flows downstream
```

#### **Barrier Alignment Flow**
```
CheckpointBarrier arrives on InputChannelInfo
    ↓ [Barrier handler processes]
CheckpointBarrierHandler.processBarrier(barrier, channel)
    ↓ [For aligned checkpoints]
SingleCheckpointBarrierHandler.processBarrier()
    ↓ [Track barrier, block channel]
MarkChannelAligned(channel)
    ↓ [Check if all N channels received]
AllBarriersAligned? → NO → Wait for more barriers
    ↓ → YES
TriggerCheckpointOnAligned()
    ↓ [Notify task to snapshot]
notifyCheckpoint(barrier)
    ↓
CheckpointableTask.triggerCheckpointOnBarrier()
    ↓
SnapshotOperatorChain()
    ↓ [Parallel state snapshots]
Operator.snapshotState()
    ↓ [Write to backend]
StateBackend.persist()
    ↓ [Create TaskStateSnapshot]
TaskStateSnapshot.merge()
    ↓ [Send ACK]
CheckpointResponder.acknowledgeCheckpoint()
```

#### **Acknowledgment & Completion Flow**
```
TaskStateSnapshot + CheckpointMetrics
    ↓ [RPC message]
AcknowledgeCheckpoint message
    ↓ [Network RPC to JobMaster]
JobMaster receives on CheckpointCoordinator
    ↓
CheckpointCoordinator.receiveAcknowledgeMessage()
    ↓ [Find pending checkpoint]
PendingCheckpoint.acknowledgeTask()
    ↓ [Record operator states]
UpdateOperatorState()
    ↓ [Increment counter]
numAcknowledgedTasks++
    ↓ [Check if fully acknowledged]
isFullyAcknowledged()? → NO → Wait for more acks
    ↓ → YES
CompletePendingCheckpoint()
    ↓ [Finalize metadata]
PendingCheckpoint.finalizeCheckpoint()
    ↓ [Write to storage]
CheckpointMetadataOutputStream.write()
    ↓ [Create completed checkpoint]
CompletedCheckpoint created
    ↓ [Store completed]
CompletedCheckpointStore.addCheckpoint()
    ↓ [Send completion notifications]
SendAcknowledgeMessages()
    ↓ [RPC to tasks]
Task.notifyCheckpointComplete()
    ↓ [Operator commit callbacks]
OperatorChain.notifyCheckpointComplete()
```

### Interface Contracts Between Components

#### **CheckpointCoordinator ↔ Execution (RPC)**
```java
Execution.triggerCheckpoint(checkpointId, timestamp, CheckpointOptions)
  → sends RPC to TaskManagerGateway
  → Task.triggerCheckpointBarrier()
```

#### **Execution ↔ Task ↔ StreamTask**
```java
Task.triggerCheckpointBarrier()
  → StreamTask.triggerCheckpointAsync(CheckpointMetaData, CheckpointOptions)
  → CheckpointBarrierHandler.processBarrier() [if not source]
  → StreamTask.triggerCheckpointOnBarrier() [when aligned]
```

#### **StreamTask ↔ CheckpointBarrierHandler**
```java
CheckpointBarrierHandler.processBarrier(barrier, channel)
  ← (eventually)
CheckpointBarrierHandler.notifyCheckpoint(barrier)
  → StreamTask.triggerCheckpointOnBarrier()
```

#### **StreamTask ↔ SubtaskCheckpointCoordinator**
```java
SubtaskCheckpointCoordinator.startCheckpointAsync()
  → Operator.snapshotState() [for each operator]
  → StateBackend.persist()
  ← TaskStateSnapshot [collected results]
```

#### **Task ↔ CheckpointCoordinator (RPC)**
```java
CheckpointResponder.acknowledgeCheckpoint(AcknowledgeCheckpoint)
  → RPC to JobMaster
  → CheckpointCoordinator.receiveAcknowledgeMessage()
```

#### **CheckpointCoordinator ↔ Execution ↔ Task (RPC)**
```java
Execution.notifyCheckpointOnComplete(checkpointId, timestamp)
  → RPC to TaskManagerGateway
  → Task.notifyCheckpointComplete()
  → StreamTask.notifyCheckpointComplete()
```

### Aligned vs Unaligned Checkpoint Handling

#### **Aligned Checkpoints** (`SingleCheckpointBarrierHandler`, default for exactly-once)
- **Barrier Processing**: Blocks input channels after receiving first barrier for a checkpoint
- **Data Buffering**: In-memory buffering of post-barrier data until all barriers received
- **Guarantees**: Exact alignment point across all inputs; no duplicate or missing data
- **Trade-off**: Higher latency during alignment, higher memory usage for buffering
- **State**: `AlignedBarrier` state in `BarrierHandlerState`
- **Configuration**: No special config needed (default behavior for `CheckpointMode.EXACTLY_ONCE`)

#### **Unaligned Checkpoints** (`SingleCheckpointBarrierHandler` in unaligned mode, for low latency)
- **Barrier Processing**: No blocking; processes post-barrier data immediately
- **Data Buffering**: Persists in-flight data to checkpoint storage alongside state
- **Guarantees**: Captures global snapshot including in-flight data; exactly-once without alignment overhead
- **Trade-off**: Larger checkpoint size (includes in-flight data), more state to store/restore
- **State**: `UnalignedBarrier` state in `BarrierHandlerState`
- **Configuration**: Enabled via `CheckpointOptions.unaligned()` when supported

#### **At-Least-Once Mode** (`CheckpointBarrierTracker`)
- **Barrier Processing**: No blocking; doesn't enforce alignment
- **Data Buffering**: No buffering; all post-barrier data flows immediately
- **Guarantees**: Best-effort checkpoint; may see duplicate records after failure
- **Trade-off**: Lowest latency, smallest memory footprint, weakest semantics
- **State**: `AtLeastOnceState` (no blocking)

### PendingCheckpoint Lifecycle

```
CREATE (initial state)
  ├─ initialized with task list to acknowledge
  ├─ associated with CheckpointPlan (which tasks to trigger, which to commit)
  └─ CompletableFuture created for completion signal

ACTIVE (waiting for acknowledgments)
  ├─ tasks trigger and send back AcknowledgeCheckpoint messages
  ├─ PendingCheckpoint.acknowledgeTask() called for each ack
  ├─ operator states accumulated in operatorStates map
  └─ numAcknowledgedTasks incremented

FULLY_ACKNOWLEDGED (all acks received)
  ├─ isFullyAcknowledged() returns true
  ├─ completePendingCheckpoint() triggered
  └─ initiates finalization phase

FINALIZING (metadata being written)
  ├─ CheckpointMetadata created containing all operator states
  ├─ metadata serialized and written to storage
  └─ CompletedCheckpointStorageLocation obtained

COMPLETED (successfully finalized)
  ├─ CompletedCheckpoint object created
  ├─ added to CompletedCheckpointStore
  ├─ older checkpoints subsumed
  └─ CompletableFuture fulfilled with CompletedCheckpoint

DISCARDED/FAILED (no recovery)
  ├─ triggered by explicit abort (timeout, error)
  ├─ all accumulated state discarded
  ├─ tasks notified to abort
  └─ CompletableFuture fulfilled with exception

From DISCARDED, can never return to ACTIVE (checkpoint lost)
```

## Summary

The Flink checkpoint coordination architecture implements a distributed two-phase commit protocol spanning JobManager and all TaskManagers. The JobManager's CheckpointCoordinator triggers checkpoints and manages the PendingCheckpoint lifecycle; barriers flow through the network graph to enforce alignment semantics; TaskManager's barrier handlers decide when to snapshot state; operators capture state snapshots; tasks send acknowledgments back; finally, when all acknowledgments arrive, the coordinator finalizes the checkpoint and notifies tasks for external commit. The design supports both exactly-once (aligned barriers with data buffering) and at-least-once (unaligned barriers, no blocking) modes, using state machines to track barrier arrivals and async/future-based orchestration to avoid blocking the coordinator thread.
