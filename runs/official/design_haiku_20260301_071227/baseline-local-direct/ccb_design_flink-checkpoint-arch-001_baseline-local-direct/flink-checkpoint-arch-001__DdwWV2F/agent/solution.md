# Flink Checkpoint Coordination Architecture Analysis

## Files Examined

### JobManager-Side Coordinator (flink-runtime/checkpoint/)
- **CheckpointCoordinator.java** — Central orchestrator that triggers checkpoints, manages PendingCheckpoints, processes task acknowledgments, and coordinates the two-phase commit. Maintains the state of all active/pending checkpoints and completes them when all tasks acknowledge.
- **PendingCheckpoint.java** — Represents a checkpoint in flight; tracks task acknowledgments, manages operator state collection, and transitions to CompletedCheckpoint when fully acknowledged. Implements ack-based completion protocol with TaskAcknowledgeResult states.
- **CompletedCheckpoint.java** — Final checkpoint state after all tasks have acknowledged; contains all state handles, metadata, and persisted to the checkpoint store. Used for recovery.
- **CheckpointIDCounter.java** — Ensures monotonically increasing checkpoint IDs across job manager instances for consistency.

### Task-Side Barrier Handling (flink-runtime/streaming/runtime/io/checkpointing/)
- **CheckpointBarrier.java** — Network event (RuntimeEvent) that flows through the task graph; carries checkpoint ID, timestamp, and CheckpointOptions (aligned/unaligned mode).
- **CheckpointedInputGate.java** — Wraps InputGate; intercepts CheckpointBarrier events and delegates to CheckpointBarrierHandler. Acts as the integration point between network I/O and barrier processing.
- **CheckpointBarrierHandler.java** — Abstract handler defining the interface for barrier processing; notifies task when checkpoint should be triggered via triggerCheckpointOnBarrier(). Tracks alignment duration and checkpoint start delay metrics.
- **SingleCheckpointBarrierHandler.java** — Concrete implementation for handling barriers with state machine-driven behavior via BarrierHandlerState. Supports both aligned and unaligned checkpoints using alternating state transitions. Tracks which channels have received barriers.
- **CheckpointBarrierTracker.java** — Alternative handler for "at-most-once" mode; does NOT block input channels. Tracks barrier counts per checkpoint ID in a deque. Simpler than SingleCheckpointBarrierHandler but doesn't guarantee exactly-once.
- **BarrierHandlerState.java** — State machine interface with implementations for waiting/collecting aligned/unaligned barriers. Transitions triggered by barrier arrival, alignment timeout, end-of-partition.

### Task-Side Checkpoint Execution (flink-runtime/streaming/runtime/tasks/)
- **SubtaskCheckpointCoordinator.java** — Interface coordinating checkpoint work on task side; initiates channel state capture, snapshot building, state upload.
- **SubtaskCheckpointCoordinatorImpl.java** — Implementation that orchestrates async snapshot, manages ChannelStateWriter, and reports state to JobManager via AcknowledgeCheckpoint.
- **StreamTask.java** — Implements CheckpointableTask; triggerCheckpointOnBarrier() entry point called by barrier handler. Delegates to performCheckpoint() which invokes SubtaskCheckpointCoordinator.
- **AsyncCheckpointRunnable.java** — Async task that snapshots operator state without blocking the main task thread.

### Execution Graph Integration (flink-runtime/executiongraph/)
- **Execution.java** — Represents a single task execution attempt; triggerCheckpoint() and triggerSynchronousSavepoint() send RPC messages to task manager via TaskManagerGateway. Returns CompletableFuture<Acknowledge>.

### Network Events (flink-runtime/io/network/)
- **CheckpointBarrier.java** (in api/) — CheckpointBarrier is a RuntimeEvent subclass, serialized specially by EventSerializer. Contains barrier ID, timestamp, and CheckpointOptions for mode (aligned/unaligned).

## Dependency Chain

### 1. Entry Point: Checkpoint Triggering
```
CheckpointCoordinator.triggerCheckpoint(boolean)
  → triggerCheckpointFromCheckpointThread(CheckpointProperties, String, boolean)
    → chooseRequestToExecute(CheckpointTriggerRequest)
      → startTriggeringCheckpoint(CheckpointTriggerRequest)
```

### 2. Checkpoint Plan and Creation
```
startTriggeringCheckpoint()
  → checkpointPlanCalculator.calculateCheckpointPlan()
  → checkpointIdCounter.getAndIncrement()
  → createPendingCheckpoint()
    → new PendingCheckpoint(...)
```

### 3. Barrier Injection - RPC to Tasks
```
triggerTasks(CheckpointTriggerRequest, long, PendingCheckpoint)
  → For each Execution in checkpoint.getCheckpointPlan().getTasksToTrigger():
    → execution.triggerCheckpoint(checkpointId, timestamp, CheckpointOptions)
      → triggerCheckpointHelper() [in Execution]
        → sendMessageToTaskManager(RPC) → CheckpointBarrier sent via network
```

**Key Point:** CheckpointOptions encodes alignment mode (aligned/unaligned) and timeout values.

### 4. Barrier Reception and Processing (Data Path)
```
Input Network
  → InputChannel
    → InputGate
      → CheckpointedInputGate.getNextBufferOrEvent()
        → CheckpointBarrierHandler.processBarrier(CheckpointBarrier, InputChannelInfo)
```

**Two Handler Implementations:**

**A. SingleCheckpointBarrierHandler (Exactly-Once, Default)**
```
processBarrier(barrier, channelInfo, isRpcTriggered)
  → checkNewCheckpoint(barrier)
  → markCheckpointAlignedAndTransformState(channelInfo, barrier, ...)
    → alignedChannels.add(channelInfo)
    → BarrierHandlerState.barrierReceived() [State Machine]
      → transitionState(NextState)
      → When all barriers received:
        → allBarriersReceived() → true
          → triggerGlobalCheckpoint(barrier)
            → controller.initInputsCheckpoint(barrier)
            → controller.triggerGlobalCheckpoint(barrier)
```

**B. CheckpointBarrierTracker (At-Most-Once)**
```
processBarrier(barrier, channelInfo, isRpcTriggered)
  → pendingCheckpoints.find(barrierId)
  → barrierCount++
  → If barrierCount == numOpenChannels:
    → notifyCheckpoint(barrier) [Checkpoint triggered immediately]
```

### 5. Task-Side Checkpoint Execution
```
CheckpointBarrierHandler.notifyCheckpoint(barrier)
  → toNotifyOnCheckpoint.triggerCheckpointOnBarrier(
      CheckpointMetaData, CheckpointOptions, CheckpointMetrics)
    → StreamTask.triggerCheckpointOnBarrier()
      → performCheckpoint(metadata, options, metrics)
        → subTaskCheckpointCoordinator.initInputsCheckpoint()
        → subTaskCheckpointCoordinator.checkpointState()
          → AsyncCheckpointRunnable (snapshot state asynchronously)
            → operator.snapshotState(...)
            → subTaskCheckpointCoordinator.reportTaskStateToJobManager()
              → [Async] RPC: AcknowledgeCheckpoint to JobManager
```

### 6. Acknowledgment and Completion (JobManager)
```
CheckpointCoordinator.receiveAcknowledgeMessage(AcknowledgeCheckpoint)
  → pendingCheckpoints.get(checkpointId)
    → checkpoint.acknowledgeTask(executionAttemptId, subtaskState, metrics)
      → [Lock] notYetAcknowledgedTasks.remove(attemptId)
      → [Lock] acknowledgedTasks.add(attemptId)
      → operatorStates.put(operatorId, taskState)
      → return TaskAcknowledgeResult.SUCCESS
  → If checkpoint.isFullyAcknowledged():
    → completePendingCheckpoint(pendingCheckpoint)
      → finalizeCheckpoint(pendingCheckpoint)
        → pendingCheckpoint.finalizeCheckpoint()
          → checkpointStorageView.commitCheckpointMetadata()
          → new CompletedCheckpoint(...)
      → addCompletedCheckpointToStoreAndSubsumeOldest()
        → completedCheckpointStore.addCheckpoint()
      → sendAcknowledgeMessages(tasksToCommitTo, checkpointId)
        → For each task: task.notifyCheckpointComplete()
```

## Analysis

### Design Patterns Identified

**1. Two-Phase Distributed Commit Protocol**
- **Phase 1 (Barrier Injection):** JobManager sends barriers through network to inject consistent snapshot boundary
- **Phase 2 (Acknowledgment):** Tasks respond with AcknowledgeCheckpoint after state snapshot, JobManager collects and transitions to CompletedCheckpoint

**2. State Machine for Barrier Processing**
- BarrierHandlerState defines states: `WaitingForFirstBarrier`, `CollectingBarriers`, `AlternatingWaitingForFirstBarrier`, `AlternatingCollectingBarriers`
- Transitions triggered by:
  - `barrierReceived()` - new barrier from input channel
  - `announcementReceived()` - early barrier announcement (unaligned mode)
  - `endOfPartitionReceived()` - input channel closed
  - `alignedCheckpointTimeout()` - switch to unaligned if alignment takes too long
  - `abort()` - cancellation signal

**3. Aligned vs. Unaligned Barrier Handling**
- **Aligned (SingleCheckpointBarrierHandler with WaitingForFirstBarrier state):**
  - Blocks input channels after first barrier received
  - Collects barriers from all channels before triggering checkpoint
  - Ensures exactly-once semantics
  - Higher latency due to waiting for slowest channel

- **Unaligned (SingleCheckpointBarrierHandler with AlternatingWaitingForFirstBarrier state):**
  - Does NOT block input channels; allows data to flow
  - Captures in-flight data via ChannelStateWriter
  - Switches to "collecting" state, records data until all barriers received
  - Lower latency but more complex state management

- **At-Most-Once (CheckpointBarrierTracker):**
  - Never blocks; checkpoint triggered as soon as first barrier received
  - No state guarantees

**4. Barrier Propagation via Network Events**
- CheckpointBarrier is a RuntimeEvent (not data) that flows through InputGate → InputChannel
- CheckpointedInputGate intercepts and queues for handler processing
- Barriers propagate in-order per channel, broadcast to downstream via operator output

**5. Async Snapshot with Non-Blocking Dispatch**
- State snapshot happens asynchronously via AsyncCheckpointRunnable
- Does not block the main task thread (operator execution continues)
- AcknowledgeCheckpoint sent asynchronously after snapshot completes
- RPC dispatch returns CompletableFuture for JobManager to wait

**6. PendingCheckpoint Lifecycle and Acknowledgment Protocol**
```
PendingCheckpoint states:
  - Initialized: Created in startTriggeringCheckpoint()
  - Waiting: Timer set for checkpoint timeout (default 10 min)
  - Acknowledged: Each task ack → acknowledgeTask() removes from notYetAcknowledgedTasks
  - Complete: When isFullyAcknowledged() → true, triggers completePendingCheckpoint()
  - Disposed: After completion or failure, removed from pendingCheckpoints map

Acknowledgment result states:
  - SUCCESS: New task acknowledged
  - DUPLICATE: Task acknowledged twice (ignore)
  - UNKNOWN: Execution attempt ID not in plan
  - DISCARDED: PendingCheckpoint was already discarded (timeout)
```

### Component Responsibilities

**CheckpointCoordinator (JobManager):**
- Triggers checkpoint on schedule
- Creates PendingCheckpoint with CheckpointPlan (tasks to trigger, acknowledge, commit to)
- Sends RPC trigger messages via Execution.triggerCheckpoint()
- Manages checkpoint timeout with timer.schedule(CheckpointCanceller)
- Receives and aggregates task acknowledgments
- Transitions PendingCheckpoint → CompletedCheckpoint when all tasks ack
- Manages CheckpointStorage for metadata persistence

**Execution (JobManager):**
- Represents a task execution attempt with ExecutionAttemptID
- Sends triggerCheckpoint() RPC via TaskManagerGateway
- Encodes CheckpointOptions (mode: aligned/unaligned, timeout)

**CheckpointedInputGate & BarrierHandler (Task):**
- Intercepts CheckpointBarrier events from input
- State machine decides when to trigger checkpoint (aligned vs unaligned)
- Blocks/unblocks input channels per barrier alignment strategy
- Calls toNotifyOnCheckpoint.triggerCheckpointOnBarrier()
- Computes alignment metrics (duration, start delay, bytes processed)

**StreamTask (Task):**
- Implements CheckpointableTask interface
- Calls triggerCheckpointOnBarrier() when barrier handler signals
- Delegates snapshot to SubtaskCheckpointCoordinator

**SubtaskCheckpointCoordinator (Task):**
- Initializes input channel state capture via ChannelStateWriter
- Invokes operator.snapshotState() asynchronously
- Manages state upload to CheckpointStorage
- Sends AcknowledgeCheckpoint RPC with SubtaskState back to JobManager

### Data Flow Description

**Forward Path (Checkpoint Triggering):**
```
JobManager Thread
  → CheckpointCoordinator.triggerCheckpoint()
    → createPendingCheckpoint()
    → triggerTasks()
      → Execution.triggerCheckpoint() [RPC dispatch]

Task Manager (Source Task)
  ← Receives RPC message
  → Injects CheckpointBarrier into output records
  → Sends barrier downstream via network

Intermediate Task
  ← CheckpointBarrier arrives via InputChannel
  → CheckpointedInputGate intercepts barrier
  → CheckpointBarrierHandler.processBarrier()
    → When all barriers collected:
      → Calls triggerCheckpointOnBarrier()
      → StreamTask snapshots state
      → Sends CheckpointBarrier downstream
```

**Backward Path (Acknowledgment):**
```
Task Manager (Any Task)
  → After state snapshot complete
  → Sends AcknowledgeCheckpoint RPC

JobManager Thread
  ← CheckpointCoordinator.receiveAcknowledgeMessage()
  → PendingCheckpoint.acknowledgeTask()
  → If isFullyAcknowledged():
    → completePendingCheckpoint()
    → PendingCheckpoint.finalizeCheckpoint()
    → Creates CompletedCheckpoint
    → Stores in completedCheckpointStore
    → Returns future to client
```

### Interface Contracts Between Components

**CheckpointCoordinator ↔ Execution:**
- `Execution.triggerCheckpoint(long checkpointId, long timestamp, CheckpointOptions) → CompletableFuture<Acknowledge>`
- CheckpointOptions encodes: checkpoint type (full/incremental), alignment mode, aligned timeout

**CheckpointBarrierHandler ↔ StreamTask:**
- `CheckpointableTask.triggerCheckpointOnBarrier(CheckpointMetaData, CheckpointOptions, CheckpointMetricsBuilder)`
- Task must complete snapshot and call coordinator to report

**SubtaskCheckpointCoordinator ↔ CheckpointCoordinator:**
- RPC: `AcknowledgeCheckpoint(jobId, executionAttemptId, checkpointId, subtaskState, checkpointMetrics)`
- JobManager aggregates states into OperatorState per operator

**BarrierHandlerState ↔ SingleCheckpointBarrierHandler:**
- State transitions return next BarrierHandlerState
- Controller interface (SingleCheckpointBarrierHandler implements) provides:
  - `allBarriersReceived()` - query
  - `triggerGlobalCheckpoint()` - callback when ready
  - `initInputsCheckpoint()` - initialize unaligned state capture

## Summary

Flink implements checkpoint coordination as a **two-phase distributed commit protocol** where the JobManager's CheckpointCoordinator:
1) Injects CheckpointBarrier events into the task graph via RPC, which flow through the network to establish a consistent snapshot boundary (Phase 1)
2) Collects acknowledgments from all tasks after they snapshot their state (Phase 2), transitioning PendingCheckpoint to CompletedCheckpoint

The task-side barrier handling uses a **state machine (BarrierHandlerState)** to switch between aligned (blocking, exactly-once) and unaligned (non-blocking, lower-latency) checkpoint modes based on configuration and alignment timeout. State snapshots happen asynchronously without blocking operator execution, and the AcknowledgeCheckpoint RPC aggregates per-operator state at the JobManager where a final CompletedCheckpoint is persisted once all task acknowledgments arrive, enabling recovery to a consistent global snapshot.
