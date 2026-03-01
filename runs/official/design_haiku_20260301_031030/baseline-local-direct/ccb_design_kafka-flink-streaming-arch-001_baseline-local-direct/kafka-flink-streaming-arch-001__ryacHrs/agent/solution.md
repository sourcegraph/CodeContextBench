# Kafka-Flink Streaming Data Flow: Cross-Repo Architectural Analysis

## Files Examined

### Apache Kafka (Producer/Consumer API)
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/Producer.java** — Core interface defining send(), flush(), commit/abort transaction contracts
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java** — Implementation managing RecordAccumulator, Sender thread, BufferPool, TransactionManager, ProducerMetadata
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/ProducerRecord.java** — Data container with topic, partition, key, value, timestamp, headers
- **kafka/clients/src/main/java/org/apache/kafka/common/serialization/Serializer.java** — Interface for T → byte[] conversion with topic/header context
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/Consumer.java** — Core interface defining subscribe(), poll(), commitSync/Async(), seek()
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java** — Implementation managing ConsumerMetadata, group coordination, fetch batching, offset tracking
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerRecord.java** — Data container with topic, partition, offset, key, value, timestamp, headers
- **kafka/clients/src/main/java/org/apache/kafka/common/serialization/Deserializer.java** — Interface for byte[] → T conversion with topic/header context
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/OffsetAndMetadata.java** — Data container for offset + metadata + leaderEpoch used in commit operations
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/internals/ConsumerCoordinator.java** — Manages consumer group membership, rebalancing, offset commits/fetches, auto-commit scheduling

### Apache Flink (Source API & Connector Framework)

#### flink-core (Source Abstractions)
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/Source.java** — Factory interface creating SplitEnumerator (JobManager) and SourceReader (Task). Methods: getBoundedness(), createEnumerator(), restoreEnumerator(), getSplitSerializer()
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SourceReader.java** — Interface for reading from assigned splits. Methods: start(), pollNext(), snapshotState(checkpointId), addSplits(), handleSourceEvents()
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SplitEnumerator.java** — Discovers splits and assigns to readers. Methods: start(), handleSplitRequest(), snapshotState(), notifyCheckpointComplete()
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SourceEvent.java** — Marker interface for bidirectional reader↔enumerator events
- **flink/flink-core/src/main/java/org/apache/flink/api/common/serialization/DeserializationSchema.java** — Interface for byte[] → T conversion. Methods: deserialize(byte[]), deserialize(byte[], Collector<T>), isEndOfStream()
- **flink/flink-core/src/main/java/org/apache/flink/api/common/serialization/SerializationSchema.java** — Interface for T → byte[] conversion. Methods: serialize(T)
- **flink/flink-core/src/main/java/org/apache/flink/api/common/typeinfo/TypeInformation.java** — Type abstraction enabling runtime serializer generation, semantic validation, schema mapping

#### flink-connector-base (Connector Framework)
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/SourceReaderBase.java** — Abstract base implementing SourceReader with SplitFetcherManager delegation, non-blocking poll(), split management, rate limiting
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/splitreader/SplitReader.java** — Interface for low-level split reading. Methods: fetch(), handleSplitsChanges(), wakeUp()
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/RecordEmitter.java** — Interface transforming intermediate elements E to final output T. Method: emitRecord(E, SourceOutput<T>, SplitStateT)
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/fetcher/SplitFetcherManager.java** — Abstract manager coordinating SplitFetcher threads, maintaining elements queue, supporting single-thread or per-split threading models

#### flink-runtime (Runtime Integration & Checkpointing)
- **flink/flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceOperator.java** — Runtime bridge for Source API. Manages reader lifecycle, processes OperatorEvents from coordinator, coordinates checkpoints via snapshotState() → sourceReader.snapshotState() → ListState storage
- **flink/flink-runtime/src/main/java/org/apache/flink/runtime/operators/coordination/OperatorEvent.java** — Base interface for events between OperatorCoordinator and OperatorEventHandler
- **flink/flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceCoordinator.java** — JobManager-side coordinator managing split assignments, enumerator lifecycle. Critical: notifyCheckpointComplete() calls enumerator.notifyCheckpointComplete() enabling external offset commits
- **flink/flink-runtime/src/main/java/org/apache/flink/runtime/state/StateSnapshotContext.java** — Context providing checkpointId and state backends during snapshot operations
- **flink/flink-runtime/src/main/java/org/apache/flink/streaming/api/checkpoint/CheckpointedFunction.java** — Interface with snapshotState(FunctionSnapshotContext) and initializeState(FunctionInitializationContext) for checkpoint coordination
- **flink/flink-runtime/src/main/java/org/apache/flink/api/common/state/CheckpointListener.java** — Interface defining notifyCheckpointComplete(checkpointId) contract for external system commits (e.g., Kafka offsets)
- **flink/flink-runtime/src/main/java/org/apache/flink/runtime/state/StateBackend.java** — Abstraction for state storage (HashMapStateBackend, RocksDBStateBackend)
- **flink/flink-runtime/src/main/java/org/apache/flink/runtime/state/TaskStateManager.java** — Manages state reporting/retrieval for task checkpoints
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/ReaderOutput.java** — Output interface for SourceReader to emit records. Methods: collect(), emitWatermark(), createOutputForSplit()

---

## Dependency Chain

### 1. Kafka Producer Side: Object → Network
```
Application Code
    ↓
ProducerRecord<K, V>
    • topic: String
    • partition: Integer (optional)
    • key: K (optional)
    • value: V
    • timestamp: Long (optional)
    • headers: Headers
    ↓
Producer.send(ProducerRecord<K, V>)
    ↓
KafkaProducer.send()
    ↓ (serialization happens here)
Serializer<K>.serialize(topic, key) → byte[]
Serializer<V>.serialize(topic, value) → byte[]
    ↓
RecordAccumulator (buffers records)
    ↓
Sender Thread (background)
    ↓
KafkaProducer.NetworkClient
    ↓
Kafka Broker
```

### 2. Kafka Consumer Side: Network → Object + Offset Management
```
Kafka Broker
    ↓
KafkaConsumer.NetworkClient
    ↓
Deserializer<K>.deserialize(topic, keyBytes) → K
Deserializer<V>.deserialize(topic, valueBytes) → V
    ↓
ConsumerRecord<K, V>
    • topic: String
    • partition: int
    • offset: long ← CRITICAL: position in topic-partition
    • key: K
    • value: V
    • timestamp: long
    • headers: Headers
    ↓
Consumer.poll(Duration) → ConsumerRecords<K, V>
    ↓
Application receives ConsumerRecords
    ↓
Consumer.commitSync(Map<TopicPartition, OffsetAndMetadata>)
    or Consumer.commitAsync(...)
    ↓
ConsumerCoordinator
    ↓
Kafka Broker (__consumer_offsets topic)
    ↓
Last committed offset = TopicPartition → OffsetAndMetadata(offset=1050, metadata="", leaderEpoch=10)
```

### 3. Flink Source API: Factory Pattern
```
Source<T, SplitT, EnumChkT> Interface
    ↓
(JobManager Side)
SplitEnumerator<SplitT, EnumChkT>
    • Creates initial or restored SplitT instances
    • Calls SourceReader.addSplits(List<SplitT>) via SourceOperator
    • Implements snapshotState(checkpointId) → EnumChkT
    • Receives notifyCheckpointComplete(checkpointId) ← KEY HOOK
    ↓
(Task Side)
SourceReader<T, SplitT>
    • Assigned splits via addSplits(List<SplitT>)
    • Non-blocking pollNext(ReaderOutput<T>)
    • Implements snapshotState(checkpointId) → List<SplitT>
    • Receives notifyCheckpointComplete(checkpointId)
    ↓
ReaderOutput<T>
    • collect(T record) — emit to downstream
    • emitWatermark(Watermark) — watermark emission
```

### 4. Flink Connector-Base: Concrete Reader Implementation
```
SourceReaderBase<T, SplitT, SplitStateT, SplitReaderT extends SplitReader<E, SplitT>>
    ↓ (delegates to)
SplitFetcherManager<E, SplitT>
    ↓ (creates)
SplitFetcher<E, SplitT> (background thread)
    ↓
SplitReader<E, SplitT>
    • fetch() → FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>
    • Wraps external system (e.g., KafkaConsumer)
    ↓
E (intermediate element type from external system)
    ↓ (transforms via)
RecordEmitter<E, T, SplitStateT>
    • emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)
    • Handles deserialization, watermark generation
    ↓
T (final record type emitted downstream)
```

### 5. Dual Serialization Boundary: Kafka ↔ Flink
```
Kafka Client Layer:                 Flink Streaming Layer:
────────────────────────────────────────────────────────

Serializer<T> ←→ ProducerRecord<K,V>    (no Flink type system)
                                ↓
                      KafkaFlink Connector
                      (separate repo)
                                ↓
                   SerializationSchema<T>
                   + TypeInformation<T>
                        ↓
                   Flink's downstream typing/serialization

Deserializer<T> ←→ ConsumerRecord<K,V>  (Kafka deserialized bytes)
                                ↓
                      KafkaFlink Connector
                      (separate repo)
                                ↓
                   DeserializationSchema<T>
                   + RecordEmitter
                        ↓
                   Flink's downstream typing/watermarking
```

### 6. Checkpoint-Offset Integration (THE CRITICAL CHAIN)

#### Snapshot Phase (During Checkpoint):
```
CheckpointCoordinator.initializeCheckpoint(checkpointId)
    ↓
SourceOperator.snapshotState(StateSnapshotContext context)
    {
        long checkpointId = context.getCheckpointId();
        readerState.update(sourceReader.snapshotState(checkpointId));
    }
    ↓
SourceReader.snapshotState(long checkpointId) → List<SplitT>
    {
        // For Kafka connector, returns List<KafkaPartitionSplit>
        // Each split contains: topicPartition, startingOffset, stoppingOffset
    }
    ↓
SimpleVersionedListState<SplitT> serialization
    ↓
StateBackend (RocksDB, HashMapStateBackend, etc.)
    ↓
Persistent Storage (HDFS, S3, Local FS)
    ↓
SourceCoordinator.checkpointCoordinator(checkpointId)
    {
        context.onCheckpoint(checkpointId);
        // Enumerator can also snapshot: List<KafkaPartition> assignments
    }
```

#### Checkpoint Completion Phase (OFFSET COMMIT TRIGGER):
```
CheckpointCoordinator.notifyCheckpointComplete(checkpointId)
    ↓
SourceOperator.notifyCheckpointComplete(checkpointId)
    ↓
sourceReader.notifyCheckpointComplete(checkpointId)
    {
        // SourceReaderBase delegates to SplitFetcher threads
        // Optionally flush rate limiters
    }
    ↓
SourceCoordinator.notifyCheckpointComplete(checkpointId)
    {
        enumerator.notifyCheckpointComplete(checkpointId);
    }
    ↓
SplitEnumerator.notifyCheckpointComplete(checkpointId)  [Default: no-op]
    {
        // For Kafka connector: OVERRIDE TO COMMIT OFFSETS
        // Kafka Connector Implementation:
        // for (KafkaPartition partition : assignedPartitions) {
        //     TopicPartition tp = new TopicPartition(partition.topic, partition.partition);
        //     OffsetAndMetadata offsetMeta = new OffsetAndMetadata(
        //         lastEmittedOffset + 1,
        //         "Flink checkpoint " + checkpointId
        //     );
        //     KafkaConsumer.commitSync(
        //         Map.of(tp, offsetMeta)
        //     );
        // }
    }
    ↓
KafkaConsumer.commitSync(Map<TopicPartition, OffsetAndMetadata>)
    ↓
ConsumerCoordinator
    ↓
Kafka Broker (__consumer_offsets topic)
    ↓
Last Committed Offset Updated
```

#### Recovery Phase (Restore from Checkpoint):
```
TaskManager receives state from CheckpointStore
    ↓
SourceOperator.initializeState(StateInitializationContext context)
    {
        ListState<SplitT> splitState = context.getOperatorStateStore()
            .getListState(SPLITS_STATE_DESC);
        List<SplitT> restoredSplits = splitState.get();
    }
    ↓
SourceReader.addSplits(List<SplitT> splits)
    {
        // For Kafka: List<KafkaPartitionSplit> from checkpoint
        // Each split knows its current offset
        // SplitFetcherManager resumes fetching from that offset
    }
    ↓
SplitReader.fetch()
    {
        // For Kafka: KafkaConsumer.seek(TopicPartition, offset)
        // Resume from checkpoint position, no re-processing
    }
```

---

## Analysis

### Kafka Producer/Consumer Architecture

**Producer Model (Asynchronous Batching):**
- `ProducerRecord` encapsulates: topic, partition (optional), key, value, timestamp, headers
- `Serializer<K>` and `Serializer<V>` convert application objects to bytes at serialization boundary
- `KafkaProducer` maintains `RecordAccumulator` buffering records by partition, with background `Sender` thread batching and sending
- Thread-safe for concurrent sends from multiple application threads
- Supports transactional semantics (`beginTransaction()`, `commitTransaction()`, `abortTransaction()`)
- Producer metrics track throughput, latency, compression

**Consumer Model (Single-Threaded Pull with Group Coordination):**
- `KafkaConsumer` is NOT thread-safe; single application thread polls
- `Consumer.poll(Duration)` blocks until records available or timeout, returning `ConsumerRecords<K, V>`
- `Deserializer<K>` and `Deserializer<V>` convert bytes to objects at deserialization boundary
- `ConsumerRecord` includes critical metadata: topic, partition, **offset**, timestamp, headers
- `Consumer.subscribe(Collection<String> topics)` triggers rebalancing via `ConsumerCoordinator` managing group membership
- **Offset Management:**
  - Auto-commit: `enable.auto.commit=true` + `auto.commit.interval.ms` configures periodic `ConsumerCoordinator` → `commitAsync()`
  - Manual commit: Application calls `Consumer.commitSync(offsets)` or `Consumer.commitAsync(offsets, callback)` with `OffsetAndMetadata` map
  - `OffsetAndMetadata` ties offset number to consumer-provided metadata (e.g., timestamp or external state reference)
  - Committed offsets stored in Kafka's `__consumer_offsets` internal topic, per consumer group

**Critical Kafka Offset Semantics:**
- Offset = position within partition; `ConsumerRecord.offset()` indicates the record's position
- `commitSync(Map<TopicPartition, OffsetAndMetadata>)` commits the NEXT offset to process (offset+1)
- `seek()` rewinds consumer to specific offset for replay
- Consumer group coordination ensures load balancing; rebalancing migrates partitions between consumers
- Consumer failure → failed partitions reassigned to healthy consumers via rebalancing

### Flink Source API Architecture

**Three-Layer Factory Pattern:**
1. **Source Factory** — Returns `SplitEnumerator` (coordinator-side) and `SourceReader` (task-side) instances
2. **Split Enumerator** (JobManager process) — Discovers source partitions/splits; assigns to readers; checkpoint-aware
3. **Source Reader** (Task process) — Fetches from assigned splits; non-blocking poll model; manages split-level state

**Source Reader Non-Blocking Model:**
- `SourceReader.pollNext(ReaderOutput<T>)` is NON-BLOCKING: returns immediately with available record or null
- Unlike Kafka's blocking `poll()`, Flink polls continuously in task mailbox
- `isAvailable()` returns CompletableFuture signaling when data ready (avoids busy-wait)
- Enables Flink to interleave multiple sources and other task operations

**Split Abstraction:**
- Generic `SplitT` type represents a partition/shard of data
- Example (Kafka): `KafkaPartitionSplit` contains `TopicPartition`, `startingOffset`, `stoppingOffset`
- `SplitEnumerator` creates/assigns splits dynamically; supports rebalancing via `addSplitsBack()`
- Checkpoint includes current split list; recovery restores reader to checkpointed splits

**SourceReaderBase Implementation (from connector-base):**
- Wraps `SplitFetcherManager` managing background fetcher threads
- Main task thread calls non-blocking `pollNext()` against `FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>`
- Fetcher threads call blocking `SplitReader.fetch()` → intermediate elements E
- `RecordEmitter` transforms E → final output T (handles deserialization, watermarks)
- Supports configurable threading: single-thread or one-thread-per-split

### Serialization/Deserialization Boundary (Kafka ↔ Flink)

**Kafka's Native Serializers (Clients):**
- `Serializer<T>` — Application type T → `byte[]` for ProducerRecord
- `Deserializer<T>` — `byte[]` from ConsumerRecord → Application type T
- Topic and headers accessible during serialization/deserialization for context

**Flink's Schema Boundary:**
- `DeserializationSchema<T>` — `byte[]` → T, with Collector for multi-record output
- `SerializationSchema<T>` — T → `byte[]`, for sinks writing to external systems
- Sits between Flink's core types and external system formats

**Dual Serialization in Kafka Connectors (Conceptual):**
```
Kafka's Serializer/Deserializer    Flink's Schema
─────────────────────────────────  ──────────────
Serializer<Message> ──────────────→ SerializationSchema<Message>
                                    (may be identical or wrapped)

Deserializer<Message> ←──────────── DeserializationSchema<Message>
                                    (may be identical or wrapped)
```

In practice, Flink Kafka connector bridges:
1. Kafka's `Deserializer<V>` (deserialized message value)
2. Optional additional `DeserializationSchema<T>` for further transformations
3. Final `TypeInformation<T>` for Flink's type system and serialization

**Type Information Layer:**
- `TypeInformation<T>` — Flink's runtime type abstraction
- Enables dynamic serializer generation for Java types (POJO, Tuple, Array, etc.)
- Handles semantic validation (e.g., key field existence for keyed states)
- Bridges schema (field names, types) to binary serialization

### Checkpoint-Offset Integration (The Critical Path)

**Why Flink Checkpoints Need External Commits:**

Flink maintains two independent state:
1. **Flink State** — Operator state in state backend (RocksDB, HashMap, etc.), recoverable on task restart
2. **External System State** — Kafka broker's `__consumer_offsets` topic, stores committed consumer group offsets

Without committing offsets to Kafka, recovery would re-process records already consumed:
- Task fails at offset 1050
- Flink restores reader splits to offset 1050 (from Flink checkpoint)
- But Kafka broker still remembers committed offset as 1040
- Reader resumes from offset 1040 → duplicate processing of 1040-1049

**Checkpoint Completion Callback Chain (The Bridge):**

Flink provides `CheckpointListener.notifyCheckpointComplete(long checkpointId)` interface:
- Called AFTER checkpoint is persisted and before resuming task
- Enables Kafka connector to commit offsets corresponding to that checkpoint
- `SourceCoordinator.notifyCheckpointComplete()` is called by checkpoint coordinator
- Coordinator calls `enumerator.notifyCheckpointComplete(checkpointId)`
- Kafka Connector's `SplitEnumerator` override calls:
  ```java
  KafkaConsumer.commitSync(Map<TopicPartition, OffsetAndMetadata>)
  ```

**Checkpoint Subsuming Contract (Monotonic Progress):**
```
Checkpoint IDs: strictly increasing (100 < 101 < 102 < ...)
Offsets in splits: monotonically advancing (more records processed per checkpoint)

Scenario:
- Checkpoint 100 completes → commit offsets @ 1050 ✓
- Checkpoint 101 completes → commit offsets @ 1100 ✓ (subsumes 100)
- Checkpoint 102 fails to complete → offsets stay @ 1100 ✓

Result: No duplicate reprocessing; monotonic offset advancement
```

**Recovery Guarantees:**
1. Task fails after checkpoint 100 is complete but before 101
2. Flink restores to checkpoint 100 (split states with offsets embedded)
3. Reader resumes from offset = checkpoint offsets (which were committed)
4. No records reprocessed between 100 and failure point

**SourceReaderBase.snapshotState() Implementation:**
```java
public List<SplitT> snapshotState(long checkpointId) {
    List<SplitT> splits = new ArrayList<>();
    splitStates.forEach((splitId, context) -> {
        SplitT split = toSplitType(splitId, context.state);
        splits.add(split);
    });
    return splits;
}
```
- Returns current list of assigned splits, each with its current offset embedded
- For Kafka: `KafkaPartitionSplit` with `TopicPartition`, `startingOffset`, `stoppingOffset`
- Offsets capture position in each partition at snapshot time

**SourceOperator.snapshotState() Integration:**
```java
public void snapshotState(StateSnapshotContext context) throws Exception {
    long checkpointId = context.getCheckpointId();
    readerState.update(sourceReader.snapshotState(checkpointId));
}
```
- Gets `checkpointId` from context
- Calls reader's snapshot, receives split list with embedded offsets
- Updates `SimpleVersionedListState<SplitT>` with new split list
- State backend serializes and persists

### Thread Architecture Implications

**Kafka Consumer (Single-threaded):**
- Application thread calls `poll()` → blocking until data available or timeout
- Internal: fetcher threads fetch from brokers, parse responses, buffer locally
- Consumer thread coordinates fetchers, returns parsed ConsumerRecords
- Not thread-safe; designed for single application thread per consumer instance

**Flink Reader with Fetcher Threads:**
- **Task Thread (main):** Calls non-blocking `pollNext()` on `SourceReaderBase`
  - Returns immediately if records in queue; null if empty
  - Updates state, emits watermarks
  - Interleaves with other task operations (other sources, stateful operators)
- **Fetcher Thread(s):** Call blocking `SplitReader.fetch()` → `SplitReader` wraps Kafka consumer
  - Thread pool managed by `SplitFetcherManager`
  - Configurable: single shared thread or one thread per split
  - Results placed in `FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>`
- **Mailbox Coordination:** Task thread uses mailbox pattern to safely coordinate with fetcher threads

**Kafka Connector Architecture (Filling the Gap):**
```
Kafka's Single Thread        Flink's Multi-Thread
───────────────────────────────────────────────
KafkaConsumer (single thread)
    ↑
SplitReader<E, SplitT> (wraps KafkaConsumer)
    ↑
SplitFetcher (runs in ExecutorService thread pool)
    ↓
[Non-blocking queue handoff]
    ↓
SourceReaderBase (task main thread)
    ↓
Flink downstream
```

The Kafka connector creates wrapper `SplitReader` per split, running in fetcher threads, allowing Flink to parallelize reads across multiple Kafka partitions while Kafka's consumer stays single-threaded internally.

---

## Summary

The Kafka-Flink integration spans two independent systems bridged by a three-layer architecture:

1. **Kafka APIs** provide producer/consumer clients with serialization, offset management, and consumer group coordination, while Flink provides a factory-pattern Source abstraction (SplitEnumerator + SourceReader) with non-blocking polling and built-in checkpoint support.

2. **Serialization Boundary**: Kafka's `Serializer/Deserializer` interfaces operate at the client level; Flink's `DeserializationSchema/SerializationSchema` and `TypeInformation` provide additional type abstraction and runtime code generation, bridged in connectors (flink-connector-kafka) that wrap Kafka consumers.

3. **Checkpoint-Offset Integration** is the critical path ensuring exactly-once semantics: `SourceOperator.snapshotState()` captures splits with embedded offsets into Flink's state backend; on completion, `notifyCheckpointComplete()` signals the `SplitEnumerator` to commit those offsets via `KafkaConsumer.commitSync()`, ensuring monotonic progress and zero duplicate processing on recovery through the checkpoint subsuming contract.

---

## Key Architectural Insights

### Why This Design?

- **Separation of Concerns**: Kafka focuses on durability/ordering; Flink adds scalable processing with fault tolerance
- **Non-Blocking I/O**: Flink's `pollNext()` enables interleaving multiple sources and operators on a single thread; Kafka's `poll()` is blocking but internal fetchers enable threading
- **Exactly-Once**: Coupling Flink state persistence with external offset commits (via `notifyCheckpointComplete()`) ensures no duplicate processing and data consistency
- **Flexible Connectors**: Source API abstractions allow diverse connectors (Kafka, Pulsar, S3, databases) with pluggable split discovery, reading, and serialization

### Data Flow Example (Kafka → Flink)

```
User publishes ProducerRecord(topic="trades", key="AAPL", value=Trade)
    ↓
Serializer<Trade> → bytes
    ↓
KafkaProducer → Kafka broker
    ↓ (time passes)
Flink Kafka Connector SplitEnumerator discovers TopicPartition("trades", 0)
    ↓
Assigns KafkaPartitionSplit(topic="trades", partition=0, offset=1000) to SourceReader
    ↓
SourceReader.addSplits([KafkaPartitionSplit(...)])
    ↓
SplitFetcher thread calls SplitReader.fetch()
    ↓
SplitReader wraps KafkaConsumer.poll() → ConsumerRecord<?, Trade>
    ↓
RecordEmitter deserializes via DeserializationSchema<Trade>
    ↓
SourceReaderBase.pollNext() returns Trade record to task
    ↓
Flink processes trade (e.g., calculates risk)
    ↓
Checkpoint triggered → snapshotState() saves offset=1001
    ↓
Checkpoint completes → SplitEnumerator.notifyCheckpointComplete()
    ↓
KafkaConsumer.commitSync({TopicPartition("trades",0): OffsetAndMetadata(1001)})
    ↓
Kafka broker updates __consumer_offsets with (trades,0) → offset 1001
```

On recovery, reader resumes from offset 1001 → no duplicates.
