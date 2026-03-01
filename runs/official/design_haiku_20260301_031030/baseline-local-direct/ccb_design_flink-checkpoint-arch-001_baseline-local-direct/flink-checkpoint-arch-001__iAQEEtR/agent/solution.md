# Flink Checkpoint Coordination Architecture Analysis

## Files Examined

### JobManager-Side Checkpoint Coordination
- `flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CheckpointCoordinator.java` — Central coordinator orchestrating the entire checkpoint lifecycle, triggering barriers, and collecting acknowledgments
- `flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/PendingCheckpoint.java` — Represents an in-flight checkpoint tracking acknowledged tasks and state metadata
- `flink-runtime/src/main/java/org/apache/flink/runtime/checkpoint/CompletedCheckpoint.java` — Final checkpoint state after all tasks acknowledge, containing operator states and metadata handles

### TaskManager-Side Barrier Propagation
- `flink-runtime/src/main/java/org/apache/flink/runtime/io/network/api/CheckpointBarrier.java` — Event propagated through network channels containing checkpoint ID, timestamp, and options
- `flink-runtime/src/main/java/org/apache/flink/runtime/taskmanager/Task.java` — Task receives and forwards checkpoint trigger via RPC
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/StreamTask.java` — Streaming task implementation that triggers checkpoint async, emits barriers to downstream

### Barrier Handling & Alignment
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierHandler.java` — Abstract base class defining barrier processing interface and checkpoint notification
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/SingleCheckpointBarrierHandler.java` — Implements aligned checkpoint barrier handling with support for alternating aligned/unaligned modes
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointBarrierTracker.java` — At-least-once semantic barrier tracker (no alignment, non-blocking)
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/CheckpointedInputGate.java` — Network input gate wrapper that intercepts barrier events and routes to handler

### Supporting Components
- `flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/Execution.java` — Execution vertex RPC interface for triggering checkpoints on TaskManagers
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/io/checkpointing/BarrierHandlerState.java` — State machine managing barrier reception workflow (aligned vs unaligned)

---

## Dependency Chain

### 1. Checkpoint Trigger Phase

**Entry Point:** `CheckpointCoordinator.triggerCheckpoint(boolean isPeriodic)`
- Constructs `CheckpointTriggerRequest` and calls `startTriggeringCheckpoint()`

**Step 2:** `CheckpointCoordinator.startTriggeringCheckpoint(CheckpointTriggerRequest request)`
- Validates global state via `preCheckGlobalState()`
- Asynchronously calculates checkpoint plan via `checkpointPlanCalculator.calculateCheckpointPlan()`
- Allocates checkpoint ID via `checkpointIdCounter.getAndIncrement()`

**Step 3:** `CheckpointCoordinator.createPendingCheckpoint(...)`
- Creates `PendingCheckpoint` instance with:
  - Set of `notYetAcknowledgedTasks` (all tasks that must acknowledge)
  - Set of `notYetAcknowledgedOperatorCoordinators`
  - Empty `acknowledgedTasks` set
  - `CheckpointPlan` containing the task graph topology

**Step 4:** `CheckpointCoordinator.triggerCheckpointRequest(CheckpointTriggerRequest, PendingCheckpoint)`
- Calls `triggerTasks()` which dispatches to each task execution

**Step 5:** `CheckpointCoordinator.triggerTasks()`
- Creates `CheckpointOptions` with checkpoint type, mode, and alignment settings
- For each `Execution execution` in `checkpoint.getCheckpointPlan().getTasksToTrigger()`:
  - Calls `execution.triggerCheckpoint(checkpointId, timestamp, checkpointOptions)` (RPC)

### 2. Barrier Injection at Sources

**Entry Point:** `Execution.triggerCheckpoint(long, long, CheckpointOptions)`
- Routes through `TaskManagerGateway.triggerCheckpoint(attemptId, jobId, checkpointId, timestamp, checkpointOptions)`

**Step 2:** `Task.triggerCheckpointBarrier(long, long, CheckpointOptions)`
- Verifies task is in RUNNING state
- Casts `invokable` to `CheckpointableTask` interface
- Invokes `invokable.triggerCheckpointAsync(CheckpointMetaData, CheckpointOptions)`

**Step 3:** `StreamTask.triggerCheckpointAsync(CheckpointMetaData, CheckpointOptions)`
- Posts work to task's mailbox executor
- Checks if all input gates are finished
- Calls either:
  - `triggerCheckpointAsyncInMailbox()` for source/finished-input tasks
  - `triggerUnfinishedChannelsCheckpoint()` for intermediate tasks with open input channels

**Step 4a (Sources/Finished Inputs):** `StreamTask.triggerCheckpointAsyncInMailbox()`
- Initializes checkpoint in `subtaskCheckpointCoordinator.initInputsCheckpoint()`
- Calls `performCheckpoint()` to snapshot operator state

**Step 4b (Intermediate Tasks):** `StreamTask.triggerUnfinishedChannelsCheckpoint()`
- Creates `CheckpointBarrier` event with checkpoint ID and options
- For each unfinished input channel:
  - Calls `checkpointBarrierHandler.processBarrier(barrier, channelInfo, true)`

### 3. Barrier Propagation Through Network

**Entry Point:** Barriers emitted at sources flow through network channels as `CheckpointBarrier` events

**Step 2:** `CheckpointedInputGate.pollNext()`
- Pulls buffers/events from underlying `InputGate`
- Intercepts `CheckpointBarrier` events

**Step 3:** `CheckpointedInputGate.handleEvent(BufferOrEvent)`
- Routes `CheckpointBarrier` to `barrierHandler.processBarrier(barrier, channelInfo, false)`

### 4. Aligned Checkpoint Barrier Handling

**Entry Point:** `SingleCheckpointBarrierHandler.processBarrier(CheckpointBarrier, InputChannelInfo, boolean isRpcTriggered)`

**Step 2:** `checkNewCheckpoint(CheckpointBarrier barrier)`
- If this is first barrier for this checkpoint ID:
  - Sets `currentCheckpointId = barrierId`
  - Initializes `pendingCheckpointBarrier`
  - Sets `targetChannelCount` to number of open channels
  - Registers alignment timer if alternating mode and timeout configured

**Step 3:** `markCheckpointAlignedAndTransformState(...)`
- Adds channel to `alignedChannels` set
- Transitions state machine via `currentState.barrierReceived()`
  - For aligned mode: blocks input channels (via `CheckpointableInput.blockChannel()`)
  - For unaligned mode: records buffered in-flight data

**Step 4:** Check alignment completion: `alignedChannels.size() == targetChannelCount`
- When all channels aligned, calls `triggerCheckpoint(CheckpointBarrier trigger)`

**Step 5:** `triggerCheckpoint()` → `notifyCheckpoint(CheckpointBarrier barrier)`
- Creates `CheckpointMetaData` from barrier
- Calls `toNotifyOnCheckpoint.triggerCheckpointOnBarrier(metadata, options, metrics)`

### 4b. At-Least-Once Tracking (CheckpointBarrierTracker)

**Entry Point:** `CheckpointBarrierTracker.processBarrier(CheckpointBarrier, InputChannelInfo, boolean)`

**Step 2:** Track barriers without blocking:
- Maintains `pendingCheckpoints` deque of `CheckpointBarrierCount` entries
- Each entry tracks how many barriers received for that checkpoint ID
- Does NOT block input channels

**Step 3:** When all barriers received for a checkpoint:
- Invokes `notifyCheckpoint()` to trigger operator checkpoint
- Maintains at-most 50 pending checkpoint tracks to bound memory

### 5. State Snapshot & Downstream Barrier Propagation

**Entry Point:** `StreamTask.triggerCheckpointOnBarrier(CheckpointMetaData, CheckpointOptions, CheckpointMetricsBuilder)`

**Step 2:** `performCheckpoint()` chains of operations:
- Calls `subtaskCheckpointCoordinator.checkpointState()` which:
  - Snapshots operator state asynchronously via state backend
  - Collects state metadata (handles, offsets, etc.)

**Step 3:** Upon checkpoint completion:
- Broadcasts `CheckpointBarrier` to all downstream operators
- Operators emit barrier after processing all pre-checkpoint records

### 6. Acknowledgment Collection at JobManager

**Entry Point:** TaskManager sends `AcknowledgeCheckpoint` RPC message after snapshot completes
- Contains checkpoint ID, subtask state (operator states), metrics (alignment duration, bytes persisted)
- Routed to `CheckpointCoordinator.receiveAcknowledgeMessage(AcknowledgeCheckpoint, taskManagerLocationInfo)`

**Step 2:** `CheckpointCoordinator.receiveAcknowledgeMessage()`
- Looks up `PendingCheckpoint` by checkpoint ID
- Registers shared states with `CompletedCheckpointStore.getSharedStateRegistry()`

**Step 3:** `PendingCheckpoint.acknowledgeTask(ExecutionAttemptID, TaskStateSnapshot, CheckpointMetrics)`
- Removes task from `notYetAcknowledgedTasks` map
- Adds task to `acknowledgedTasks` set
- Stores operator states in `operatorStates` map
- Increments `numAcknowledgedTasks` counter
- Records metrics in `pendingCheckpointStats`

**Step 4:** Check completion: `PendingCheckpoint.isFullyAcknowledged()`
- Returns `numAcknowledgedTasks == checkpointPlan.getTasksToCommitTo().size()`

**Step 5:** If fully acknowledged:
- Calls `CheckpointCoordinator.completePendingCheckpoint(PendingCheckpoint)`

### 7. Checkpoint Completion & Persistence

**Entry Point:** `CheckpointCoordinator.completePendingCheckpoint(PendingCheckpoint pendingCheckpoint)`

**Step 2:** Finalize checkpoint:
- Calls `finalizeCheckpoint(pendingCheckpoint)` which:
  - Serializes metadata to `CheckpointMetadataOutputStream`
  - Flushes operator states to storage backend
  - Returns `CompletedCheckpoint` instance

**Step 3:** Persist metadata:
- Calls `addCompletedCheckpointToStoreAndSubsumeOldest()`:
  - Adds to `CompletedCheckpointStore` (FileSystemCheckpointStore, ZooKeeperCheckpointStore, etc.)
  - Subsumes older incomplete checkpoints to save storage

**Step 4:** Signal completion:
- Completes `PendingCheckpoint.onCompletionPromise` future with `CompletedCheckpoint`
- Calls `reportCompletedCheckpoint()` to update stats and failure manager

**Step 5:** Notify downstream:
- Calls `sendAcknowledgeMessages()` to send completion notifications to tasks
- Each task receives `NotifyCheckpointComplete` RPC

---

## Analysis

### Design Patterns Identified

#### 1. **Two-Phase Commit Protocol**
The checkpoint coordination implements a distributed two-phase commit:
- **Phase 1 (Commit):** CheckpointCoordinator broadcasts barrier trigger → tasks snapshot state → tasks acknowledge
- **Phase 2 (Abort/Complete):** Upon all acknowledgments → checkpoint finalized → tasks notified

#### 2. **Event-Sourced Barrier Propagation**
Barriers flow as immutable events through the network:
- Sources inject barriers into streams deterministically
- Barriers are appended to record streams to define checkpoint boundaries
- Each operator receives all pre-checkpoint records before barrier
- Exactly-once guarantees enforced by buffering post-barrier records until barrier alignment completes

#### 3. **State Machine-Based Barrier Handling (BarrierHandlerState)**
`SingleCheckpointBarrierHandler` uses state transitions:
- `WaitingForFirstBarrier` → first barrier arrives
- `CollectingBarriers` (aligned mode) → blocks channels, buffers post-barrier records
- `AlignedCheckpointCheckpoint` → all barriers received, triggers snapshot
- Supports alternating aligned/unaligned modes for different operator configurations

#### 4. **Async/Sync Duality**
- **Async Path:** Source tasks trigger checkpoint immediately upon RPC
- **Sync Path:** Intermediate tasks wait for barrier reception before triggering checkpoint
- Ensures causal ordering: sources → barriers → downstream operators

#### 5. **Pending/Completed Checkpoint Lifecycle**
- **PendingCheckpoint:** Created when trigger starts, tracks outstanding acknowledgments (mutable state)
- **CompletedCheckpoint:** Immutable snapshot of final state after all acks received
- Transition occurs only once via `isFullyAcknowledged()` check

#### 6. **Pluggable Alignment Strategies**
- `CheckpointBarrierHandler` interface allows multiple implementations:
  - `SingleCheckpointBarrierHandler`: Aligned (exactly-once) with timeout → unaligned fallback
  - `CheckpointBarrierTracker`: Tracking-only (at-least-once), no blocking

#### 7. **Channel-Level Granularity**
Alignment occurs at input channel level (`InputChannelInfo`), not task level:
- Each task waits for barriers from all input channels independently
- Enables operators with multiple inputs to correctly align checkpoints per channel
- Facilitates partial alignment in large pipelines

### Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **CheckpointCoordinator** | Orchestrates checkpoint lifecycle: trigger, dispatch, track acks, finalize |
| **PendingCheckpoint** | Tracks in-flight state: outstanding tasks, received states, operator snapshots |
| **CompletedCheckpoint** | Immutable checkpoint metadata: operator states, handles, external pointer |
| **CheckpointBarrier** | Event marking checkpoint boundary in record stream |
| **CheckpointBarrierHandler** | Processes barriers, enforces alignment semantics, notifies task |
| **SingleCheckpointBarrierHandler** | Aligned barrier handling with state machine transitions and timeouts |
| **CheckpointBarrierTracker** | Non-blocking barrier tracking for at-least-once semantics |
| **CheckpointedInputGate** | Network gate wrapper intercepting barrier events |
| **StreamTask** | Converts RPC checkpoint trigger to state snapshot and barrier injection |

### Data Flow Description

#### Trigger Flow (JobManager → TaskManager)
```
CheckpointCoordinator.triggerCheckpoint()
  ├─ Create PendingCheckpoint (tracks notYetAcknowledgedTasks)
  ├─ For each source task Execution:
  │   └─ RPC: taskManagerGateway.triggerCheckpoint(checkpointId, timestamp, options)
  └─ Task.triggerCheckpointBarrier() → StreamTask.triggerCheckpointAsync()
      ├─ If source: Snapshot state immediately
      └─ If intermediate: Inject CheckpointBarrier into output stream
```

#### Barrier Flow (Source → Sink)
```
Source emits CheckpointBarrier into output stream
  ↓
Network serialization (CheckpointBarrierSerializer)
  ↓
Received on intermediate task InputGate
  ↓
CheckpointedInputGate.pollNext() intercepts
  ↓
CheckpointBarrierHandler.processBarrier()
  ├─ Aligned mode: Block input channels, buffer post-barrier records
  └─ At-least-once: Just track barrier count
  ↓
On alignment completion:
  ├─ Trigger task's checkpoint snapshot
  ├─ Broadcast CheckpointBarrier to downstream operators
  └─ Continue processing post-barrier records
```

#### Acknowledgment Flow (TaskManager → JobManager)
```
Task snapshot completes (async state backend write)
  ↓
TaskStateSnapshot captured with operator states
  ↓
RPC: AcknowledgeCheckpoint(checkpointId, executionAttemptId, taskStateSnapshot, metrics)
  ↓
CheckpointCoordinator.receiveAcknowledgeMessage()
  ├─ PendingCheckpoint.acknowledgeTask() stores state
  ├─ Increments numAcknowledgedTasks
  └─ Check if fully acknowledged
  ↓
If fully acknowledged:
  └─ CheckpointCoordinator.completePendingCheckpoint()
      ├─ Finalize → serialize metadata
      ├─ Add to CompletedCheckpointStore
      ├─ Complete PendingCheckpoint.onCompletionPromise
      └─ Notify tasks of completion (NotifyCheckpointComplete RPC)
```

### Interface Contracts Between Components

#### CheckpointCoordinator ↔ Execution (RPC)
```java
// Trigger
Execution.triggerCheckpoint(checkpointId, timestamp, checkpointOptions)
  → TaskManagerGateway.triggerCheckpoint(...)

// Acknowledge
CheckpointCoordinator.receiveAcknowledgeMessage(AcknowledgeCheckpoint)
```

#### Task ↔ StreamTask (Local Interface)
```java
// Interface: CheckpointableTask
public CompletableFuture<Boolean> triggerCheckpointAsync(
    CheckpointMetaData checkpointMetaData,
    CheckpointOptions checkpointOptions)

public void triggerCheckpointOnBarrier(
    CheckpointMetaData checkpointMetaData,
    CheckpointOptions checkpointOptions,
    CheckpointMetricsBuilder checkpointMetrics) throws IOException
```

#### CheckpointedInputGate ↔ CheckpointBarrierHandler
```java
// Barrier reception
barrierHandler.processBarrier(CheckpointBarrier, InputChannelInfo, isRpcTriggered)

// Barrier announcement (for timeout planning)
barrierHandler.processBarrierAnnouncement(barrier, sequenceNumber, channelInfo)

// Cancellation
barrierHandler.processCancellationBarrier(CancelCheckpointMarker, channelInfo)

// Input finish
barrierHandler.processEndOfPartition(InputChannelInfo)
```

#### CheckpointBarrierHandler → CheckpointableTask (Callback)
```java
// Triggered when barrier alignment complete
toNotifyOnCheckpoint.triggerCheckpointOnBarrier(...)

// Called on abort (cancellation, timeout, failure)
notifyAbort(checkpointId, CheckpointException)
```

### Aligned vs Unaligned Checkpoint Handling

#### **Aligned Checkpoints (Exactly-Once)**
- **Mechanism:** Block input channels upon first barrier reception
- **Guarantees:** No duplicate processing, exactly-once semantics
- **Cost:** Latency increase as operators wait for slowest upstream
- **Handler:** `SingleCheckpointBarrierHandler` with `CollectingBarriers` state
- **State Buffering:** In-memory or disk buffering of records arriving after barrier on unaligned channels
- **Timeout:** Optional `alignedCheckpointTimeout` triggers switch to unaligned after timeout

#### **Unaligned Checkpoints (Exactly-Once with Lower Latency)**
- **Mechanism:** Snapshot immediately upon first barrier, buffer in-flight records
- **Guarantees:** Records buffered in-flight are persisted with state; no duplicates
- **Cost:** Larger checkpoint size due to channel state (in-flight buffers)
- **Handler:** `SingleCheckpointBarrierHandler` with `CollectingBarriersUnaligned` state
- **Channel State:** Captures `ChannelState` (InputChannelInfo → buffered data)
- **Recovery:** On restore, recovered buffers re-injected into channels before processing resumes

#### **At-Least-Once (Unguarded)**
- **Mechanism:** No blocking, no buffering; just track barrier reception
- **Guarantees:** Barriers only signal completion observation, no processing semantics
- **Use Case:** Sources with no prior state (Kafka offsets tracked externally)
- **Handler:** `CheckpointBarrierTracker`
- **Note:** Deprecated in favor of exactly-once modes; kept for backward compatibility

---

## Summary

Flink's checkpoint coordination implements a **distributed two-phase commit protocol** where the JobManager (CheckpointCoordinator) orchestrates barrier-based snapshot initiation across the task graph. Barriers flow as immutable events through network channels, with (Single)CheckpointBarrierHandler enforcing exactly-once alignment semantics by selectively blocking input channels and buffering out-of-order records. The PendingCheckpoint tracks in-flight state until all tasks acknowledge via AcknowledgeCheckpoint RPCs, upon which CheckpointCoordinator finalizes the checkpoint into a CompletedCheckpoint with persisted operator states. Support for both aligned and unaligned modes optimizes the trade-off between latency and checkpoint overhead while maintaining correctness guarantees.
