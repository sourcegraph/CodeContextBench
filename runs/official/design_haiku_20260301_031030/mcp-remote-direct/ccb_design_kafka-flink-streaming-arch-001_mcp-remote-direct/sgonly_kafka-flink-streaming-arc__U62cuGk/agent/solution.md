# Kafka-Flink Streaming Data Flow Architecture Analysis

## Files Examined

### Apache Kafka Client API (github.com/sg-evals/kafka--0753c489)

**Producer Interface & Classes:**
- `clients/src/main/java/org/apache/kafka/clients/producer/Producer.java` — Generic producer interface with send(), flush(), and transaction support
- `clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java` — Concrete implementation of the Producer interface
- `clients/src/main/java/org/apache/kafka/clients/producer/ProducerRecord.java` — Data structure containing topic, partition, key, value, timestamp, and headers for records sent to Kafka
- `clients/src/main/java/org/apache/kafka/clients/producer/Callback.java` — Callback interface for async send() operations

**Serialization Layer (Producer-side):**
- `clients/src/main/java/org/apache/kafka/common/serialization/Serializer.java` — Interface for converting objects to byte arrays; accepts configure() and serialize(topic, data) methods

**Consumer Interface & Classes:**
- `clients/src/main/java/org/apache/kafka/clients/consumer/Consumer.java` — Generic consumer interface with poll(), commitSync(), subscribe(), and assign()
- `clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java` — Concrete implementation with poll(timeout), commitSync(offsets), and group coordination
- `clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerRecord.java` — Data structure containing topic, partition, offset, timestamp, key, value, headers for records received from Kafka

**Deserialization Layer (Consumer-side):**
- `clients/src/main/java/org/apache/kafka/common/serialization/Deserializer.java` — Interface for converting byte arrays to objects; accepts deserialize(topic, data) and deserialize(topic, headers, data) methods

**Offset Management:**
- `clients/src/main/java/org/apache/kafka/clients/consumer/OffsetAndMetadata.java` — Serializable data structure tracking consumer group offset, metadata string, and optional leader epoch for a specific partition

### Apache Flink Connector Framework (github.com/sg-evals/flink--0cc95fcc)

**Source API (flink-core):**
- `flink-core/src/main/java/org/apache/flink/api/connector/source/Source.java` — Factory interface that creates SourceReader and SplitEnumerator; defines split/checkpoint serializers
- `flink-core/src/main/java/org/apache/flink/api/connector/source/SourceReader.java` — Interface with pollNext(), snapshotState(), and start(); extends CheckpointListener
- `flink-core/src/main/java/org/apache/flink/api/connector/source/SplitEnumerator.java` — Coordinator interface managing split discovery and assignment; snapshotState() for checkpointing
- `flink-core/src/main/java/org/apache/flink/api/connector/source/SourceSplit.java` — Marker interface for immutable split objects (e.g., Kafka partition assignments)

**Deserialization Schema (Flink serde boundary):**
- `flink-core/src/main/java/org/apache/flink/api/common/serialization/DeserializationSchema.java` — Interface bridge between raw bytes (from any source) and Flink objects; methods: deserialize(byte[]), deserialize(byte[], Collector<T>), isEndOfStream(T)
- `flink-core/src/main/java/org/apache/flink/api/common/serialization/AbstractDeserializationSchema.java` — Base implementation providing type information extraction

**Connector-Base Framework (flink-connector-base):**
- `flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/SourceReaderBase.java` — Abstract base implementation of SourceReader; manages split fetcher threads and record queues
- `flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/splitreader/SplitReader.java` — Interface for reading records from one or more splits; methods: fetch() (blocking), handleSplitsChanges(), wakeUp()
- `flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/RecordEmitter.java` — Interface for transforming fetched records and emitting to downstream; emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)

**Runtime Integration (flink-runtime):**
- `flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceOperator.java` — Concrete operator class implementing PushingAsyncDataInput and OperatorEventHandler; runs SourceReader and coordinates with SourceCoordinator
- `flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceOperatorFactory.java` — Factory creating SourceOperator instances with watermark strategy
- `flink-runtime/src/main/java/org/apache/flink/streaming/runtime/tasks/SourceOperatorStreamTask.java` — Task wrapper for executing SourceOperator

---

## Dependency Chain

### 1. Kafka Producer API (Sender Path)

```
Application Code
    ↓
Producer<K, V>          [Interface: send(ProducerRecord), flush(), close()]
    ↓
ProducerRecord<K, V>    [Contains: topic, partition, key, value, headers, timestamp]
    ↓
Serializer<K> + Serializer<V>  [Interface: serialize(topic, data) → byte[]]
    ↓
KafkaProducer (internals)  [Manages batching, partitioning, and sending]
    ↓
Kafka Broker Network    [Writes serialized records to log]
```

**Key Interfaces:**
- `Serializer<T>` — `byte[] serialize(String topic, T data)`
- Producers can be configured with `key.serializer` and `value.serializer` class names

---

### 2. Kafka Consumer API (Receiver Path)

```
Kafka Broker Network    [Stores serialized records in partitions]
    ↓
KafkaConsumer (internals)  [NetworkClient → FetchSessionHandler → Fetcher]
    ↓
Deserializer<K> + Deserializer<V>  [Interface: deserialize(topic, data) → T]
    ↓
ConsumerRecord<K, V>   [Contains: topic, partition, offset, key, value, headers, timestamp]
    ↓
ConsumerRecords<K, V>  [Batch from poll(duration)]
    ↓
Application Code
    ↓
commitSync(Map<TopicPartition, OffsetAndMetadata>)  [Updates broker with consumer group offset]
```

**Key Interfaces:**
- `Consumer<K, V>` — `ConsumerRecords<K, V> poll(Duration timeout)`, `void commitSync(Map<TopicPartition, OffsetAndMetadata> offsets)`
- `Deserializer<T>` — `T deserialize(String topic, byte[] data)`
- `OffsetAndMetadata` — `new OffsetAndMetadata(long offset, String metadata)`

---

### 3. Flink Source API (High-Level Framework)

```
StreamExecutionEnvironment.addSource(Source<T, SplitT, EnumChkT>)
    ↓
Source Factory Pattern:
  • createEnumerator() → SplitEnumerator<SplitT, EnumChkT>
  • createReader() → SourceReader<T, SplitT>
  • getSplitSerializer() → SimpleVersionedSerializer<SplitT>
  • getEnumeratorCheckpointSerializer() → SimpleVersionedSerializer<EnumChkT>
    ↓
SplitEnumerator<SplitT, EnumChkT>
  • Runs on JobManager (coordinator)
  • Discovers splits (e.g., Kafka partitions)
  • handleSplitRequest(int subtaskId) → assigns splits to readers
  • snapshotState(long checkpointId) → CheckpointT
    ↓
SplitEnumeratorContext
  • assignSplit(SourceSplit split, int subtaskId)
  • assignSplits(SplitsAssignment assignment)
    ↓
SourceReader<T, SplitT>
  • Runs on TaskManager (parallel instances)
  • start()
  • pollNext(ReaderOutput<T> output) → InputStatus
  • snapshotState(long checkpointId) → List<SplitT>
  • Implements CheckpointListener
    ↓
(Deserialized) Element T
```

**Key Interfaces:**
- `Source<T, SplitT, EnumChkT>` — Factory for enumerator/reader creation
- `SplitEnumerator<SplitT, CheckpointT>` — Coordinator logic for split assignment
- `SourceReader<T, SplitT>` — Parallel reader; extends CheckpointListener

---

### 4. Flink Connector-Base Framework (Abstract Implementation Layer)

```
Custom Connector (e.g., Flink Kafka Connector)
    ↓
Extends Source<T, KafkaPartition, KafkaSourceEnumCheckpoint>
    ↓
SourceReaderBase<E, T, SplitT, SplitStateT>  [Abstract base for common patterns]
    ├─ E: Intermediate element type (rich metadata from fetcher)
    ├─ T: Final element type emitted downstream
    ├─ SplitT: Source split type (implements SourceSplit)
    └─ SplitStateT: Mutable split state for checkpointing
        ↓
        Uses:
        ├─ SplitFetcherManager     [Manages fetcher threads running SplitReader]
        ├─ FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>  [Thread-safe queue]
        └─ RecordEmitter<E, T, SplitStateT>  [Transforms E → T]
    ↓
SplitReader<E, SplitT>  [Interface for reading from splits]
    • RecordsWithSplitIds<E> fetch()  [Blocking read, may be interrupted]
    • void handleSplitsChanges(SplitsChange<SplitT>)  [Non-blocking]
    • void wakeUp()  [Interrupt fetch()]
    ↓
Implementation Examples:
    • KafkaPartitionSplitReader (wraps KafkaConsumer)
    • FileSourceSplitReader (reads file paths)
    ↓
RecordEmitter<E, T, SplitStateT>  [Interface for post-fetch transformation]
    • void emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)
    ↓
Downstream Operators
```

**Key Abstractions:**
- `SourceReaderBase` handles: thread management, record queuing, checkpoint coordination
- Connector developers only need to implement: `SplitReader` + `RecordEmitter`

---

### 5. Flink Runtime Integration (SourceOperator)

```
SourceOperatorFactory<OUT, SplitT>
    ↓
SourceOperator<OUT, SplitT>  [Extends AbstractStreamOperator]
    implements PushingAsyncDataInput<OUT>
    implements OperatorEventHandler
    implements CheckpointListener
    ↓
Core Methods:
    • void initializeState(StateInitializationContext)
      → Loads ListState<byte[]> for split state restoration
    • void emitNext(DataOutput<OUT> output)
      → Calls sourceReader.pollNext(currentMainOutput)
      → Returns InputStatus (MORE_AVAILABLE, NOTHING_AVAILABLE, END_OF_DATA, END_OF_INPUT)
    • void snapshotState(StateSnapshotContext)
      → Calls sourceReader.snapshotState(checkpointId)
      → Persists List<SplitT> to operator state
    • void notifyCheckpointComplete(long checkpointId)
      → Forwards to sourceReader.notifyCheckpointComplete(checkpointId)
    • void notifyCheckpointAborted(long checkpointId)
      → Forwards to sourceReader.notifyCheckpointAborted(checkpointId)
    • void handleOperatorEvent(OperatorEvent event)
      → Processes AddSplitEvent, NoMoreSplitsEvent, SourceEventWrapper
    ↓
Task Coordinator:
    • SourceOperatorStreamTask wraps SourceOperator
    • Receives events from SourceCoordinator (JobManager)
    • Sends split requests back to coordinator
    ↓
Output:
    • Emits StreamRecord<OUT> instances
    • Emits Watermarks, RecordAttributes
```

---

## Serialization/Deserialization Boundary

Kafka-Flink integration involves **TWO serialization layers**:

### Layer 1: Kafka Serialization (Within Kafka)
```
Kafka Producer:
  T (Java object) → Serializer<T>.serialize(topic, data) → byte[] → Kafka Broker

Kafka Consumer:
  Kafka Broker → byte[] → Deserializer<T>.deserialize(topic, data) → T (Java object)
```

**Characteristics:**
- Configured via `key.serializer`, `value.serializer`, `key.deserializer`, `value.deserializer`
- Each Serializer/Deserializer is stateless (configure/close methods for optional lifecycle)
- Header-aware overloads: `serialize(topic, headers, data)`, `deserialize(topic, headers, data)`

### Layer 2: Flink Deserialization (Between Kafka Consumer and Flink Stream)
```
KafkaConsumer → ConsumerRecord<byte[], byte[]>
    ↓
DeserializationSchema<T>.deserialize(byte[] message) → T

OR (if replicating multiple records):

DeserializationSchema<T>.deserialize(byte[] message, Collector<T> out)
    ↓
Emits zero or more T objects
```

**Characteristics:**
- Flink-specific interface bridging raw bytes to application types
- Supports "end-of-stream" markers via `isEndOfStream(T element)`
- Can initialize with context (metrics, user code class loader) via `open(InitializationContext)`

### Adaptation Pattern (Flink Kafka Connector)

```
KafkaConsumer.poll(timeout)
    ↓
Iterator<ConsumerRecord<byte[], byte[]>>
    ↓
SplitReader.fetch()  [Iterates and collects ConsumerRecords]
    ↓
RecordsWithSplitIds<ConsumerRecord<byte[], byte[]>>
    ↓
RecordEmitter.emitRecord(ConsumerRecord elem, SourceOutput<T> out, SplitState state)
    ├─ Calls DeserializationSchema.deserialize(elem.value())
    ├─ Optionally extracts timestamp from ConsumerRecord.timestamp()
    ├─ Optionally uses watermark strategy
    └─ Emits record to downstream via out.collect(T)
```

---

## Checkpoint-Offset Integration

### Checkpoint Flow in Flink

```
JobManager (Checkpoint Coordinator)
    ↓
1. Triggers checkpoint at barrier
    ↓ (sends RequestCheckpointBarrier event)
    ↓
SourceOperator on TaskManager
    ↓
2. Calls sourceReader.snapshotState(checkpointId)
    ↓
3. SourceReader returns List<SplitT> containing:
   • Partition assignments
   • Current offsets within each partition
   • Any in-flight state
    ↓
4. SourceOperator persists List<SplitT> to ListState
    ↓
5. Checkpoint completes (barrier reaches sink)
    ↓ (sends CheckpointCompletedAck back to JobManager)
    ↓
6. JobManager marks checkpoint as committed
    ↓
7. JobManager notifies SourceOperator
    ↓ (sends checkpoint completion event)
    ↓
8. SourceOperator.notifyCheckpointComplete(checkpointId)
    ↓
9. Forwards to sourceReader.notifyCheckpointComplete(checkpointId)
```

### Kafka Offset Commit Integration

**The Flink Kafka Connector bridges Flink checkpoints to Kafka consumer group offsets:**

```
Step 6-9: Checkpoint completion notification received
    ↓
KafkaSourceReader extends SourceReaderBase
    ↓
10. Implements notifyCheckpointComplete(long checkpointId)
    ↓
11. Extracts per-partition offsets from internal split state
    ↓
12. Builds Map<TopicPartition, OffsetAndMetadata>
    • Key: TopicPartition(topic, partition)
    • Value: OffsetAndMetadata(offset, metadata="Flink-checkpointId-...")
    ↓
13. Calls consumer.commitSync(offsetsMap)
    ↓
KafkaConsumer.commitSync()
    ↓
14. Sends OffsetCommitRequest to broker
    ↓
15. Broker updates consumer group __consumer_offsets internal topic
    ↓
16. Returns successfully (or throws CommitFailedException on failure)
    ↓
17. If commit fails: Flink treats checkpoint as failed, rolls back
    ↓
18. If commit succeeds: Consumer group offset now matches Flink checkpoint
```

**Key Properties:**
- **Exactly-once semantics:** Flink only commits Kafka offsets after checkpoint completes
- **Failure recovery:** If task crashes before checkpoint completion, Kafka offset is not updated; restart replays records from last committed offset
- **Idempotence:** If committed offset = current consumed offset, subsequent polls start from same position (safe for replay)

### CheckpointListener Interface

```
public interface CheckpointListener {
    void notifyCheckpointComplete(long checkpointId) throws Exception;
    void notifyCheckpointAborted(long checkpointId) throws Exception;
}
```

**Implemented by:**
- `SourceReader<T, SplitT>` — For sources (e.g., commit Kafka offsets)
- `SplitEnumerator<SplitT, CheckpointT>` — For split discovery (e.g., notify external system)
- Custom functions implementing CheckpointListener

---

## Thread Architecture

### Kafka Consumer/Producer Threads

**KafkaConsumer (Single-threaded API):**
- Must be called from a single thread (the "poll thread")
- Internally uses Fetcher + Sender threads for async network I/O
- `poll()` method is blocking; returns available records or times out
- Thread safety: Only the poll thread should call poll/commit/subscribe

**KafkaProducer (Thread-safe):**
- Can be called from multiple threads concurrently
- Internally batches records and sends asynchronously via Sender threads
- `send()` returns Future; callback is invoked from Sender thread

### Flink SplitReader/SplitFetcherManager Threads

```
SourceOperator (runs on Task's main thread)
    ↓
SourceReaderBase (manages thread pool)
    │
    ├─ Main thread (mailbox processor)
    │  • Calls pollNext() from this thread (non-blocking)
    │  • Returns records from internal queue
    │  • Handles split assignment events
    │
    └─ Fetcher Thread Pool (SplitFetcherManager)
       • 1+ fetcher threads for reading
       • Each fetcher calls SplitReader.fetch() (blocking)
       • Fetcher threads push records into FutureCompletingBlockingQueue
       • Main thread polls from queue (non-blocking via queue.poll())
```

**Design Pattern: Async Handoff**
- Fetcher threads do blocking I/O (Kafka's poll)
- Main thread remains responsive to checkpoints, watermarks, events
- Queue coordination: Main thread waits for availability (CompletableFuture)

---

## Consumer Group Coordination

### Kafka Group Rebalancing

```
Broker (Group Coordinator for consumer group)
    ↓
Consumer 1 (SourceOperator instance 0)
Consumer 2 (SourceOperator instance 1)
...
Consumer N (SourceOperator instance parallelism)
    ↓
All consumers poll() simultaneously
    ↓
Broker detects missing heartbeat or new consumer
    ↓
Initiates rebalance:
  1. Sends IllegalGenerationException in poll() response
  2. Consumers rejoin group (RebalanceListener callbacks)
  3. GroupCoordinator runs assigned strategy (RangeAssignor, RoundRobinAssignor, etc.)
  4. Partitions redistributed to consumers
    ↓
Each consumer receives new assignment in poll()
    ↓
New partitions added via addSplits(List<SplitT>)
    ↓
Continues polling from new set of partitions
```

**Flink Integration:**
- Flink's parallelism determines number of KafkaConsumers (one per SourceReader instance)
- Each SourceReader is a separate consumer in the consumer group
- Flink uses sticky/cooperative rebalancing to minimize stop-the-world

### Heartbeat & Rebalancing

```
Each KafkaConsumer sends heartbeat every session.timeout.ms / 3
    ↓
If SourceTask is blocked (doing checkpoint), heartbeat thread still active
    ↓
If heartbeat fails for session.timeout.ms, consumer is considered dead
    ↓
Broker removes from group, initiates rebalance
    ↓
For Kafka connectors: Configure heartbeat.interval.ms << checkpoint interval
```

---

## Data Flow Example: Kafka to Flink to Sink

```
Topic "orders" (3 partitions, 100k messages)
    ↓ Kafka Broker stores
    ├─ orders-0: msgs [0-33k]
    ├─ orders-1: msgs [33k-66k]
    └─ orders-2: msgs [66k-100k]
    ↓
Step 1: Create Kafka Source
    flinkEnv.fromSource(
        kafkaSource(topics=["orders"]),
        watermarkStrategy=ingestionTime(),
        uid="kafka-source"
    )
    ↓
Step 2: SourceCoordinator (JobManager) creates KafkaSourceEnumerator
    ├─ Discovers 3 partitions
    ├─ Creates KafkaPartition splits
    ├─ Assigns to 2 SourceReader instances (parallelism=2):
    │  • Reader-0: [orders-0, orders-1]
    │  • Reader-1: [orders-2]
    ↓
Step 3: SourceOperator instances on TaskManagers (parallelism=2)
    ├─ Task-0 (SourceOperator-0):
    │  ├─ Creates KafkaSourceReader
    │  ├─ Creates KafkaConsumer(groupId="flink-orders")
    │  └─ Subscribes to [orders-0, orders-1]
    │
    └─ Task-1 (SourceOperator-1):
       ├─ Creates KafkaSourceReader
       ├─ Creates KafkaConsumer(groupId="flink-orders")
       └─ Subscribes to [orders-2]
    ↓
Step 4: Main loop (per SourceOperator)
    SourceOperator.emitNext()
    ├─ Calls sourceReader.pollNext(output)
    │  ├─ SourceReaderBase checks queue: nothing available
    │  ├─ Returns CompletableFuture (no data yet)
    │  └─ Main thread waits (non-blocking)
    │
    └─ [Meanwhile, Fetcher Thread 0 is running]
       ├─ Calls SplitReader.fetch()
       ├─ KafkaPartitionSplitReader calls:
       │  consumer.poll(Duration.ofMillis(1000))
       ├─ Broker returns ConsumerRecords:
       │  ├─ [orders-0, offset=100]: {key="order1", value={"item":"foo"}}
       │  ├─ [orders-0, offset=101]: {key="order2", value={"item":"bar"}}
       │  └─ [orders-1, offset=50]: {key="order3", value={"item":"baz"}}
       ├─ Packs into RecordsWithSplitIds<ConsumerRecord>
       └─ Pushes to queue
    ↓
Step 5: Queue becomes non-empty, future completes
    Main thread resumes:
    ├─ Calls RecordEmitter.emitRecord(ConsumerRecord, output, splitState)
    ├─ Deserializer.deserialize(consumerRecord.value())
    │  → Order(itemId="foo", ...)
    ├─ output.collect(Order(...))
    │  → Emits StreamRecord<Order> downstream
    ├─ splitState.offset = 100  (tracks progress)
    └─ Returns InputStatus.MORE_AVAILABLE
    ↓
Step 6: Checkpoint triggered (e.g., every 60 seconds)
    Barrier received at SourceOperator
    ├─ Task.snapshotState(StateSnapshotContext context)
    ├─ SourceOperator calls:
    │  sourceReader.snapshotState(checkpointId=42)
    ├─ SourceReaderBase calls:
    │  KafkaPartitionSplitReader.snapshotState()
    ├─ Returns List<KafkaPartitionSplit> with:
    │  • Partition assignment [orders-0, orders-1]
    │  • Last committed offset: 101 (for orders-0), 50 (for orders-1)
    ├─ SourceOperator persists to state backend:
    │  ListState["SourceReaderState"].add(serialized KafkaPartitionSplit)
    └─ Checkpoint barrier flows downstream to sink
    ↓
Step 7: Checkpoint completes across all operators
    JobManager marks checkpoint as successful
    ↓
Step 8: Notification propagates back
    JobManager → SourceCoordinator → SourceOperator
    ├─ SourceOperator.notifyCheckpointComplete(42)
    ├─ Calls sourceReader.notifyCheckpointComplete(42)
    ├─ KafkaSourceReader.notifyCheckpointComplete(42):
    │  ├─ For each KafkaPartitionSplit:
    │  │  • Build OffsetAndMetadata(offset=101, metadata="ckpt-42")
    │  │  • Add to commitMap[TopicPartition(orders-0)] = OffsetAndMetadata(101)
    │  │  • Add to commitMap[TopicPartition(orders-1)] = OffsetAndMetadata(50)
    │  ├─ Call consumer.commitSync(commitMap)
    │  └─ Kafka broker updates __consumer_offsets topic
    │     ✓ Consumer group "flink-orders" now has offsets 101, 50
    ↓
Step 9: Consumer group offsets are now durable
    If task crashes now:
    ├─ Task restarted
    ├─ initializeState() loads checkpoint splits from state backend
    ├─ SourceReader restores KafkaPartitionSplit with offset=101, 50
    ├─ consumer.seek(TopicPartition(orders-0), 101)
    ├─ consumer.seek(TopicPartition(orders-1), 50)
    └─ Next poll() returns records starting from offset 102, 51
       ✓ No duplicate records! (orders-0/100-101 were already processed)
    ↓
Step 10: Continue polling, eventually finish consuming all 100k messages
    All offsets reach end-of-partition
    ├─ SplitReader.fetch() returns empty RecordsWithSplitIds
    ├─ pollNext() returns InputStatus.END_OF_DATA
    ├─ SourceOperator transitions to finished state
    ├─ Downstream operators finish processing
    └─ Flink job completes successfully
```

---

## Summary

The Kafka-Flink streaming data flow pipeline integrates two independent systems through careful boundary management:

1. **Kafka's Role:** Provides durable, append-only logs with consumer group offset tracking via `KafkaConsumer.poll()` and `commitSync(Map<TopicPartition, OffsetAndMetadata>)`. Serialization occurs at produce/consume boundaries using `Serializer`/`Deserializer` interfaces.

2. **Flink's Role:** Provides fault-tolerant stream processing with distributed sources. The `Source` API abstracts split discovery (SplitEnumerator) and parallel reading (SourceReader). The `SourceOperator` runtime integrates readers with Flink's checkpoint mechanism, ensuring exactly-once delivery semantics.

3. **Bridge Design:** The Flink Kafka Connector implements `SourceReader` to wrap `KafkaConsumer`, uses `SplitReader` to handle per-partition polling, and implements `RecordEmitter` to deserialize records via `DeserializationSchema`. Upon checkpoint completion, the connector calls `commitSync()` to durably commit offsets, tying Flink's checkpoint snapshots to Kafka's consumer group offset commits.

4. **Thread Model:** Kafka's single-threaded consumer API is wrapped in Flink's async fetcher threads (non-blocking hand-off via `FutureCompletingBlockingQueue`). Main task thread remains responsive to checkpoint events and watermark emissions while fetcher threads perform blocking Kafka polls. This ensures Flink's responsive, event-driven model coexists with Kafka's polling-based consumption.

5. **Exactly-Once Guarantee:** Flink persists splits (including Kafka partition offsets) in state backend, and **only after checkpoint completion** does the Kafka connector call `commitSync()`. If failure occurs between checkpoint snapshot and offset commit, Flink restores from checkpoint and re-consumes the same offsets, while Kafka's broker still has the old committed offset, enabling safe replay without duplicates or loss.
