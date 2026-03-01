# Kafka-Flink Streaming Data Flow Architecture

## Files Examined

### Apache Kafka (Client API)
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/Producer.java** — Interface defining producer send, transaction, and configuration methods
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/ProducerRecord.java** — Data model for records sent to Kafka (topic, partition, timestamp, key, value, headers)
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java** — Concrete implementation of producer with batching, compression, and async callbacks
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/Consumer.java** — Interface defining consumer subscription, polling, and offset commit methods
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerRecord.java** — Data model for records received from Kafka (includes offset, partition, timestamp, leaderEpoch)
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java** — Concrete implementation with consumer group coordination and fetch management
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/OffsetAndMetadata.java** — Metadata wrapper for committed offsets with optional leaderEpoch and custom metadata
- **kafka/clients/src/main/java/org/apache/kafka/common/serialization/Serializer.java** — Interface for converting objects to bytes (topic and header aware)
- **kafka/clients/src/main/java/org/apache/kafka/common/serialization/Deserializer.java** — Interface for converting bytes to objects (topic and header aware)

### Apache Flink (Source API)
- **flink-core/src/main/java/org/apache/flink/api/connector/source/Source.java** — Factory interface that creates SplitEnumerator and SourceReader instances
- **flink-core/src/main/java/org/apache/flink/api/connector/source/SourceReader.java** — Interface for readers running in TaskManagers; provides non-blocking pollNext, snapshotState, and split addition
- **flink-core/src/main/java/org/apache/flink/api/connector/source/SplitEnumerator.java** — Interface for discovering splits and assigning them to readers; handles snapshotState and CheckpointListener
- **flink-core/src/main/java/org/apache/flink/api/connector/source/SourceReaderContext.java** — Runtime context for readers (metrics, configuration)
- **flink-core/src/main/java/org/apache/flink/api/connector/source/SplitEnumeratorContext.java** — Runtime context for enumerators (split assignment, event dispatch to readers)

### Apache Flink (Connector Base Framework)
- **flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/SourceReaderBase.java** — Abstract base for readers; handles SplitReader thread management, RecordEmitter invocation, and queue handoff
- **flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/splitreader/SplitReader.java** — Interface for synchronous record fetching (blocking fetch, split changes, wakeup)
- **flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/RecordEmitter.java** — Interface for converting SplitReader elements (E) to output records (T) with split state updates
- **flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/fetcher/SplitFetcherManager.java** — Manages fetcher threads that run SplitReaders and handle element queuing

### Apache Flink (Serialization)
- **flink-core/src/main/java/org/apache/flink/api/common/serialization/DeserializationSchema.java** — Interface for converting bytes to Flink objects; complements Kafka deserializer
- **flink-core/src/main/java/org/apache/flink/api/common/serialization/SerializationSchema.java** — Interface for converting Flink objects to bytes; complements Kafka serializer

### Apache Flink (Runtime)
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceOperator.java** — Runtime operator that holds SourceReader, orchestrates polling, and triggers checkpoints

---

## Dependency Chain

### 1. Kafka Producer Data Path
```
Application Code
    ↓
ProducerRecord<K, V> (contains topic, partition, key, value, headers, timestamp)
    ↓
Serializer<K>.serialize(topic, headers, key)  → byte[]
Serializer<V>.serialize(topic, headers, value) → byte[]
    ↓
KafkaProducer.send(ProducerRecord)
    ↓
Batching & Compression (managed by Sender thread)
    ↓
NetworkClient (sends to broker)
    ↓
Broker Storage (append to log)
    ↓
RecordMetadata (returned to callback or Future)
```

**Key Interfaces:**
- `Producer<K, V>` — Define contract for send(), flush(), metrics(), transaction methods
- `Serializer<T>` — configure(), serialize(topic, headers, data) → byte[]

---

### 2. Kafka Consumer Data Path
```
Broker (partition log at offset N)
    ↓
KafkaConsumer.poll(timeout)
    ↓
Fetcher (background thread manages fetch position)
    ↓
NetworkClient.fetch(topics, offsets, max_bytes)
    ↓
Deserializer<K>.deserialize(topic, headers, bytes) → K
Deserializer<V>.deserialize(topic, headers, bytes) → V
    ↓
ConsumerRecord<K, V> (wraps key, value, offset, partition, timestamp, leaderEpoch)
    ↓
ConsumerRecords (batch grouped by partition)
    ↓
Consumer.commitSync() or Consumer.commitAsync()
    ↓
OffsetAndMetadata (offset + metadata + leaderEpoch)
    ↓
Broker stores offset in __consumer_offsets topic
```

**Key Interfaces:**
- `Consumer<K, V>` — subscribe(), poll(), assign(), commitSync(), seek(), metrics()
- `Deserializer<T>` — configure(), deserialize(topic, headers, data) → T
- `ConsumerRecord<K, V>` — immutable, contains offset, partition, timestamp, leaderEpoch
- `OffsetAndMetadata` — (long offset, Optional<Integer> leaderEpoch, String metadata)

---

### 3. Flink Source API (High-Level)
```
StreamExecutionEnvironment.addSource(Source<T, SplitT, EnumChkT>)
    ↓
Source.createEnumerator(SplitEnumeratorContext) → SplitEnumerator
Source.createReader(SourceReaderContext) → SourceReader
    ↓
[COORDINATOR THREAD]
SplitEnumerator.start()
SplitEnumerator.handleSplitRequest(subtaskId)
SplitEnumeratorContext.assignSplit(split, subtaskId)
    ↓
[TASK MANAGER THREADS]
SourceReader.addSplits(splits)
SourceReader.pollNext(output)
    ↓
ReaderOutput<T>.collect(record)
    ↓
[BACK TO COORDINATOR]
SourceReader.snapshotState(checkpointId) → List<SplitT>
SplitEnumerator.snapshotState(checkpointId) → EnumChkT
    ↓
StateBackend stores serialized state
```

**Key Interfaces:**
- `Source<T, SplitT, EnumChkT>` — createEnumerator(), restoreEnumerator(), getSplitSerializer(), getEnumeratorCheckpointSerializer()
- `SplitEnumerator<SplitT, CheckpointT>` — start(), handleSplitRequest(), addSplitsBack(), addReader(), snapshotState(), notifyCheckpointComplete()
- `SourceReader<T, SplitT>` — start(), pollNext(output), snapshotState(), isAvailable(), addSplits(), notifyNoMoreSplits(), notifyCheckpointComplete()

---

### 4. Flink Connector-Base Framework (Low-Level)
```
SourceReaderBase<E, T, SplitT, SplitStateT> extends SourceReader<T, SplitT>
    ↓
    ├─ SplitFetcherManager<E, SplitT>
    │   ├─ Multiple SplitFetcher threads
    │   └─ Each runs: SplitReader<E, SplitT>.fetch() → RecordsWithSplitIds<E>
    │
    ├─ RecordEmitter<E, T, SplitStateT>
    │   └─ Converts E → T via emitRecord(element, output, splitState)
    │
    └─ FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>
        └─ Handoff between fetcher threads and main task thread
```

**Key Interfaces:**
- `SourceReaderBase` — orchestrates split management, element queuing, record emission
- `SplitFetcherManager` — manages thread pool running SplitReaders
- `SplitReader<E, SplitT>` — fetch() → RecordsWithSplitIds<E>, handleSplitsChanges(), wakeUp()
- `RecordEmitter<E, T, SplitStateT>` — emitRecord(E, SourceOutput<T>, SplitStateT)

**Thread Model:**
- **Main Task Thread:** Calls pollNext(), manages watermarks, emits records to downstream
- **Fetcher Threads:** Call SplitReader.fetch() (blocking), put results in queue, woken up by main thread

---

### 5. Flink Serde Boundary (Dual Serialization)
```
[Kafka Domain]
ConsumerRecord<byte[], byte[]>
    ↓
[Deserialization Layer 1: Kafka]
ConsumerRecord → Deserializer<K> → K (application object)
ConsumerRecord → Deserializer<V> → V (application object)
    ↓
[Flink Domain]
Intermediate Record (E from SplitReader.fetch())
    ↓
[Deserialization Layer 2: Flink]
RecordEmitter.emitRecord(E, output, splitState)
    → DeserializationSchema<T>.deserialize(byte[]) → T (Flink type)
    ↓
SourceOutput<T>.collect(T)
    → StreamRecord<T> (emitted to downstream)
```

**Dual Layers:**
1. **Kafka Serialization** (Serializer/Deserializer) — Converts between JVM objects and Kafka wire protocol bytes
2. **Flink Serialization** (SerializationSchema/DeserializationSchema) — Converts between Flink runtime types and application types (or vice versa for sinks)

**Key Interfaces:**
- `DeserializationSchema<T>` — open(context), deserialize(byte[]) → T, isEndOfStream(T)
- `SerializationSchema<T>` — open(context), serialize(T) → byte[]

---

### 6. Flink Checkpoint Integration (Critical Path)
```
[TASK MANAGER: Polling Loop]
while (running) {
    InputStatus status = sourceReader.pollNext(output);
    // Emit records to downstream
}
    ↓
[CHECKPOINT TRIGGERED by JobManager]
StateSnapshotContext context = checkpointBarrier
    ↓
SourceOperator.snapshotState(context)
    │
    └─ long checkpointId = context.getCheckpointId()
       SourceReader.snapshotState(checkpointId) → List<SplitT>
       SourceReaderState.update(splits)  // Stores to StateBackend
    ↓
[BACKGROUND: State Serialization]
SimpleVersionedListState serializes splits
    ↓
[ACKNOWLEDGEMENT PHASE]
Checkpoint completes when all operators acknowledge
    ↓
SourceOperator.notifyCheckpointComplete(checkpointId)
    │
    └─ SourceReader.notifyCheckpointComplete(checkpointId)
    ↓
[For Kafka Integration: flink-connector-kafka]
SourceReader (Kafka-specific impl)
    └─ KafkaConsumer.commitSync() or commitAsync()
       → Sends OffsetCommitRequest to __consumer_offsets
       → Broker acknowledges offset stored safely
```

**Key Components:**
- `SourceOperator.snapshotState()` — Calls SourceReader.snapshotState() and stores results
- `SourceOperator.notifyCheckpointComplete()` — Calls SourceReader.notifyCheckpointComplete(), which for Kafka invokes consumer offset commit
- `StateSnapshotContext` — Provides checkpointId and access to StateBackend
- Offset Commit Latency: Happens after checkpoint is marked complete (not blocking the checkpoint)

---

### 7. Kafka-Specific Consumer Offset Coordination
```
[Checkpoint Completion]
SourceReader (flink-connector-kafka)
    │
    └─ KafkaSourceReader extends SourceReaderBase
       │
       ├─ SplitReader impl: KafkaPartitionSplitReader
       │   └─ wraps: KafkaConsumer<K, V>
       │
       └─ notifyCheckpointComplete(checkpointId)
           │
           └─ For each assigned TopicPartition tp:
               OffsetAndMetadata offsetAndMetadata = new OffsetAndMetadata(
                   nextRecord.offset() + 1,  // Commit position after last consumed
                   leaderEpoch,
                   "checkpoint-" + checkpointId
               )
               KafkaConsumer.commitSync(Map<TopicPartition, OffsetAndMetadata>)
                   ↓
               Sends OffsetCommitRequest(group, topicPartition, offset) to __consumer_offsets
                   ↓
               Broker writes offset atomically
                   ↓
               KafkaConsumer receives OffsetCommitResponse
                   ↓
               Future Kafka sessions start from committed offset + 1
```

---

## Architecture Analysis

### Data Flow Semantics

#### 1. **Record Lifecycle**
- **Creation (Kafka):** ProducerRecord encapsulates key, value, headers, partition hint
- **Serialization (Kafka):** Serializer converts objects to wire bytes
- **Transmission:** NetworkClient sends to broker
- **Storage:** Broker appends to partition log with offset
- **Fetching (Kafka):** KafkaConsumer.poll() retrieves ConsumerRecord (offset-aware)
- **Deserialization (Kafka):** Deserializer converts wire bytes back to objects
- **Flink Ingestion:** SourceReader receives KafkaConsumer.poll() results
- **Flink SplitReader:** Wraps KafkaConsumer, extracts ConsumerRecord, tracks offset
- **Flink Serde (Layer 2):** DeserializationSchema converts to Flink output type
- **Emission:** SourceOutput.collect() sends record downstream

#### 2. **Offset Management (Dual Responsibility)**
- **Kafka Consumer:** Maintains fetch position (next expected offset)
- **Flink Checkpoint:** Snapshots split state (last consumed offset per partition)
- **Synchronization Point:** SourceReader.notifyCheckpointComplete() commits offsets
  - Ensures exactly-once semantics: record is emitted → checkpoint completes → offset is committed
  - On failure: SourceReader restores from checkpoint → resumes from last committed offset + 1

#### 3. **Checkpoint-Offset Interaction**
```
Timeline:
T0: KafkaConsumer.poll() → ConsumerRecord offset=100
T1: SourceReader.pollNext() emits record downstream
T2: Checkpoint triggered (checkpoint ID = 5)
T3: SourceOperator.snapshotState(5) → SourceReader.snapshotState(5)
    → stores "offset=101" in StateBackend
T4: All operators snapshot completes
T5: CheckpointCoordinator marks checkpoint 5 complete
T6: SourceOperator.notifyCheckpointComplete(5)
    → SourceReader.notifyCheckpointComplete(5)
    → KafkaConsumer.commitSync(tp → OffsetAndMetadata(101))
    → Broker stores offset 101 in __consumer_offsets
T7: If task fails after T6 and recovers:
    → TaskManager restores checkpoint 5
    → SourceReader reads "offset=101" from state
    → KafkaConsumer.seek(tp, 101)
    → Next poll() returns ConsumerRecord offset=101, 102, ...
```

### Consumer Group Coordination

**Kafka Side:**
- Multiple KafkaConsumer instances join a consumer group (via group.id)
- ConsumerCoordinator negotiates rebalancing when members join/leave
- Leader performs partition assignment (round-robin, range, sticky, custom)
- Each member receives assigned TopicPartitions via ConsumerRebalanceListener
- Offset commits go to __consumer_offsets with (group, topic, partition, offset)

**Flink Side:**
- SourceOperator runs in single TaskManager subtask
- Multiple SourceOperators exist (one per parallel subtask)
- SplitEnumerator (running in JobManager) receives partition assignments
- Distributes TopicPartition splits to SourceReaders via SplitEnumeratorContext.assignSplit()
- Each SourceReader manages KafkaConsumer with same group.id

**Interaction:**
- Flink's parallelism (number of subtasks) must ≤ number of partitions (else some consumers are idle)
- Flink coordinates via SplitEnumerator; Kafka coordinates via ConsumerCoordinator
- Both systems independently manage offsets (though Flink's checkpoint takes precedence for recovery)

### Thread Architecture

**Kafka:**
```
[User Thread]
consumer.poll(timeout) → ConsumerRecords

    ↓

[Fetcher Thread (background)]
Manages fetch position per partition
Sends FetchRequests to brokers
Buffers responses in per-partition queues

    ↓

[User Thread]
Receives ConsumerRecords from per-partition queues
```

**Flink + Kafka:**
```
[Task Thread (SourceOperator)]
while (running) {
    sourceReader.pollNext(output)
        ↓ (delegates to SourceReaderBase)
}

    ↓

[Fetcher Thread (SplitFetcher in SplitFetcherManager)]
while (running) {
    records = splitReader.fetch()  // SplitReader wraps KafkaConsumer
        ↓
        (calls KafkaConsumer.poll() internally)
        ↓ (KafkaConsumer has own Fetcher thread)
    elementsQueue.put(records)  // Handoff to task thread
}

    ↓

[Task Thread (SourceOperator)]
recordEmitter.emitRecord(record, output, splitState)
output.collect(record)
downstream.receive(record)
```

### Serialization Boundary Details

**Kafka Serializer/Deserializer:**
- Operates on **JVM application objects** (user's domain model)
- Example: `Serializer<Order>` where Order is a POJO
- Serializer produces **wire format bytes** (JSON, Avro, Protobuf, custom binary)
- Deserializer consumes wire format bytes and reconstructs JVM object
- Configured per topic via `key.serializer`, `value.serializer` producer properties
- Configured per topic via `key.deserializer`, `value.deserializer` consumer properties

**Flink DeserializationSchema/SerializationSchema:**
- Operates on Flink's **StreamRecord<T>** type system
- Example: `DeserializationSchema<Row>` where Row is Flink's row type
- DeserializationSchema converts **wire bytes** (from Kafka or source) → **Flink-typed record**
- SerializationSchema converts **Flink-typed record** → **wire bytes** (to Kafka sink)
- Can be different from Kafka serializers (e.g., Kafka uses JSON, Flink uses Avro)

**Typical Flow (Kafka Source):**
```
Kafka (JSON bytes)
    ↓
Kafka Deserializer (JSON) → POJO (Order)
    ↓
Flink SplitReader receives POJO
    ↓
Flink DeserializationSchema (POJO) → Row (Flink typed)
    ↓
Flink operator receives Row
```

**Typical Flow (Kafka Sink):**
```
Flink operator emits Row
    ↓
Flink SerializationSchema (Row) → bytes
    ↓
Flink Kafka Sink
    ↓
Kafka Serializer (bytes) → already serialized, passes through
    → OR Kafka Serializer (object from SerializationSchema) → bytes
```

---

## Summary

The Kafka-Flink integration spans two independent systems with clear separation of concerns:

1. **Kafka handles:** Producer API (record creation, serialization, broker delivery), consumer API (fetching, deserialization, offset management), and consumer group coordination. The `KafkaConsumer` and `Deserializer` are the primary integration points.

2. **Flink handles:** Data source abstraction (Source/SourceEnumerator/SourceReader), connector framework (SourceReaderBase/SplitReader/RecordEmitter), runtime execution (SourceOperator), checkpointing, and watermarks. The `SourceReader` and `DeserializationSchema` are the primary integration points.

3. **Kafka-Flink Connector (separate module) bridges them:** A KafkaSource implements Source<T, KafkaSourceSplit, KafkaSourceEnumCheckpoint>, a KafkaSourceReader wraps KafkaConsumer, and a KafkaPartitionSplitReader implements SplitReader<ConsumerRecord, KafkaSourceSplit>. The connector translates between Kafka's poll-based API and Flink's split/reader model, and crucially, coordinates offset commits with checkpoint completion to guarantee exactly-once processing.

The dual serialization boundary (Kafka Serializer + Flink DeserializationSchema) allows independent format choices at each layer, while the checkpoint-offset integration ensures that offset commits are atomic with Flink's snapshot durability, providing the foundation for failure recovery and exactly-once semantics in capital markets streaming applications.
