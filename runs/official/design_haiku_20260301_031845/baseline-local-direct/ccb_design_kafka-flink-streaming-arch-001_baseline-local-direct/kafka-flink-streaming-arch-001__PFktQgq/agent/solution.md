# Kafka-Flink Streaming Data Flow Architecture Analysis

## Files Examined

### Apache Kafka (Producer API)
- `kafka/clients/src/main/java/org/apache/kafka/clients/producer/Producer.java` — Generic producer interface with send(), flush(), partitionsFor() contract
- `kafka/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java` — Concrete implementation wrapping producer client with internal serializer integration
- `kafka/clients/src/main/java/org/apache/kafka/clients/producer/ProducerRecord.java` — Data envelope: `ProducerRecord<K, V>` containing topic, partition, key, value, timestamp, headers
- `kafka/clients/src/main/java/org/apache/kafka/common/serialization/Serializer.java` — Interface `Serializer<T>`: `serialize(String topic, T data) -> byte[]` with optional headers support

### Apache Kafka (Consumer API)
- `kafka/clients/src/main/java/org/apache/kafka/clients/consumer/Consumer.java` — Generic consumer interface with poll(), commitSync(), commitAsync(), seek(), position()
- `kafka/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java` — Concrete consumer implementation with group coordination and offset management
- `kafka/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerRecord.java` — Data envelope: `ConsumerRecord<K, V>` with topic, partition, offset, timestamp, key, value, headers
- `kafka/clients/src/main/java/org/apache/kafka/clients/consumer/OffsetAndMetadata.java` — Commit metadata: `OffsetAndMetadata(long offset, String metadata)` for offset commits
- `kafka/clients/src/main/java/org/apache/kafka/common/serialization/Deserializer.java` — Interface `Deserializer<T>`: `deserialize(String topic, byte[] data) -> T` with headers support

### Apache Flink (Core Source API)
- `flink/flink-core/src/main/java/org/apache/flink/api/connector/source/Source.java` — Factory interface creating `SplitEnumerator` and `SourceReader`, provides split/checkpoint serializers
- `flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SourceReader.java` — Interface with `pollNext(ReaderOutput<T>)`, `snapshotState(checkpointId)`, `notifyCheckpointComplete()`
- `flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SplitEnumerator.java` — Partition discovery and assignment: `addReader()`, `handleSplitRequest()`, `snapshotState()`, `notifyCheckpointComplete()`
- `flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SourceSplit.java` — Marker interface for split types (partition identifiers)

### Apache Flink (Connector Base Framework)
- `flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/SourceReaderBase.java` — Abstract base class implementing SourceReader, manages `SplitFetcherManager<E, SplitT>` thread pool, `RecordEmitter<E, T, SplitStateT>` for deserialization, and `FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>` for buffering
- `flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/splitreader/SplitReader.java` — Interface: `fetch()` -> `RecordsWithSplitIds<E>`, `handleSplitsChanges()`, `wakeUp()` — wraps connector-specific fetchers (e.g., KafkaConsumer)
- `flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/RecordEmitter.java` — Interface: `emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)` — applies Flink's DeserializationSchema

### Apache Flink (Serialization Boundary)
- `flink/flink-core/src/main/java/org/apache/flink/api/common/serialization/DeserializationSchema.java` — Flink schema interface: `deserialize(byte[] message) -> T` or `deserialize(byte[] message, Collector<T> out)`, separate from Kafka's Deserializer
- `flink/flink-core/src/main/java/org/apache/flink/api/common/serialization/SerializationSchema.java` — Flink schema interface: `serialize(T element) -> byte[]` for sink operators
- `flink/flink-core/src/main/java/org/apache/flink/api/common/state/CheckpointListener.java` — Interface: `notifyCheckpointComplete(checkpointId)`, `notifyCheckpointAborted(checkpointId)` — for transactional commit semantics

### Apache Flink (Runtime Integration)
- `flink/flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceOperator.java` — Runtime operator orchestrating SourceReader, checkpoint coordination:
  - `snapshotState(StateSnapshotContext)` calls `sourceReader.snapshotState(checkpointId)` -> stores split state in ListState
  - `notifyCheckpointComplete(checkpointId)` delegates to `sourceReader.notifyCheckpointComplete()` for consumer offset commits

---

## Dependency Chain: Complete Data Flow

### 1. Kafka Producer Path (Writing to Topic)
```
User Code
    ↓
Producer<K, V> interface
    ↓
KafkaProducer<K, V> {
    keySerializer: Serializer<K>      // serialize key
    valueSerializer: Serializer<V>    // serialize value
}
    ↓
send(ProducerRecord<K, V>) -> Future<RecordMetadata>
    ↓
ProducerRecord<K, V> {
    topic: String
    partition: Integer (optional, partitioner chosen if null)
    key: K (serialized via keySerializer)
    value: V (serialized via valueSerializer)
    timestamp: Long (optional)
    headers: Headers
}
    ↓
KafkaProducer.Sender (internal batch thread)
    ↓
Kafka Broker (persists to partition log)
```

**Key Design:** Kafka's `Serializer<T>` is **topic-aware** (`serialize(String topic, T data)`) and **header-aware** (`serialize(String topic, Headers headers, T data)`), allowing custom metadata injection per topic.

---

### 2. Kafka Consumer Path (Reading from Topic)
```
Kafka Broker (partition log with offsets)
    ↓
KafkaConsumer<K, V> {
    keyDeserializer: Deserializer<K>     // deserialize key
    valueDeserializer: Deserializer<V>   // deserialize value
    groupId: String                       // consumer group for offset coordination
    offsetCommitStrategy: auto or manual
}
    ↓
poll(Duration timeout) -> ConsumerRecords<K, V> {
    List<ConsumerRecord<K, V>> records per partition
}
    ↓
ConsumerRecord<K, V> {
    topic: String
    partition: int
    offset: long (position in partition)
    key: K (deserialized via keyDeserializer)
    value: V (deserialized via valueDeserializer)
    timestamp: Long (broker timestamp or producer timestamp)
    headers: Headers
    leaderEpoch: Optional<Integer>
}
    ↓
commitSync() or commitAsync(Map<TopicPartition, OffsetAndMetadata>)
    ↓
KafkaConsumer.Coordinator {
    consumerGroupCoordinator(brokerAddress)
    commitOffsetRequest(groupId, offsets)
}
    ↓
Kafka Broker (__consumer_offsets internal topic)
```

**Key Design:** Kafka's `Deserializer<T>` mirrors `Serializer<T>`: topic-aware and header-aware. **Consumer offset commits** are **explicit**: the application calls `commitSync()` with `OffsetAndMetadata(offset, metadata)`. The `offset` field points to the **next record to consume** (offset + 1).

---

### 3. Flink Source API Layer (Abstraction)
```
StreamExecutionEnvironment.addSource(Source<T, SplitT, EnumChkT>)
    ↓
Source<T, SplitT, EnumChkT> {
    createEnumerator(SplitEnumeratorContext) -> SplitEnumerator<SplitT, EnumChkT>
    createReader(SourceReaderContext) -> SourceReader<T, SplitT>
    getSplitSerializer() -> SimpleVersionedSerializer<SplitT>
    getEnumeratorCheckpointSerializer() -> SimpleVersionedSerializer<EnumChkT>
}
    ↓
Two Parallel Threads in Coordinator:
┌─ SplitEnumerator<SplitT, EnumChkT> (JobManager / Coordinator)
│  ├─ start()
│  ├─ handleSplitRequest(subtaskId) -> assignSplit(SplitT, subtaskId)
│  ├─ addSplitsBack(splits, subtaskId) (on reader failure/rebalance)
│  ├─ snapshotState(checkpointId) -> EnumChkT
│  ├─ notifyCheckpointComplete(checkpointId)
│  └─ restoreEnumerator(context, EnumChkT checkpoint)
│
└─ SourceReader<T, SplitT> (parallel TaskManager, one per parallelism)
   ├─ start()
   ├─ addSplits(Collection<SplitT>) (receives from enumerator)
   ├─ pollNext(ReaderOutput<T> output) -> InputStatus {MORE_AVAILABLE, NOTHING_AVAILABLE, END_OF_INPUT}
   ├─ snapshotState(checkpointId) -> List<SplitT> (return in-progress splits)
   ├─ notifyCheckpointComplete(checkpointId)
   └─ notifyCheckpointAborted(checkpointId)
```

**Key Abstraction:** Flink's Source API is **split-based**, not partition-based. A SplitT can represent:
- A Kafka partition (TopicPartition)
- A Kafka partition + offset range
- Any data source's logical chunk

---

### 4. Flink Connector-Base Framework (Kafka-Specific)
```
SourceReaderBase<E, T, SplitT, SplitStateT> implements SourceReader<T, SplitT> {

    SplitFetcherManager<E, SplitT> {
        List<SplitFetcher<E, SplitT>> fetchers (thread pool)
        ├─ Each SplitFetcher<E, SplitT> wraps:
        │  └─ SplitReader<E, SplitT> (Kafka-specific)
        │      ├─ fetch() -> RecordsWithSplitIds<E>
        │      │   └─ For Kafka: pulls ConsumerRecords<K, V>, wraps in E (e.g., KafkaSourceRecord)
        │      ├─ handleSplitsChanges(SplitsChange<SplitT>)
        │      │   └─ For Kafka: calls consumer.assign(), consumer.seek()
        │      └─ wakeUp() -> unblocks fetch()
        │
        └─ FutureCompletingBlockingQueue<RecordsWithSplitIds<E>> elementsQueue
           └─ Buffering between fetcher threads (I/O-bound) and main thread
    }

    RecordEmitter<E, T, SplitStateT> {
        emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)
        └─ For Kafka: applies Flink's DeserializationSchema<T>
           Input: E (Kafka ConsumerRecord or custom wrapper)
           Output: T (user POJO)
           State: SplitStateT (tracks offset progress per split)
    }

    Map<String, SplitContext<T, SplitStateT>> splitStates
    └─ Tracks mutable state per split (offset, watermark, etc.)

    Main Thread Loop:
    ├─ pollNext(ReaderOutput<T> output)
    │   ├─ currentFetch = elementsQueue.poll()  // from fetcher threads
    │   ├─ for each record in currentFetch:
    │   │   ├─ recordEmitter.emitRecord(record, output, splitState)
    │   │   ├─ output.collect(T element)
    │   │   └─ splitState.offset += 1
    │   └─ return InputStatus.MORE_AVAILABLE or NOTHING_AVAILABLE
    │
    ├─ snapshotState(checkpointId) -> List<SplitT>
    │   └─ For each split in splitStates:
    │       ├─ Include SplitT + splitState (e.g., current offset, watermark)
    │       └─ Return list of splits to checkpoint
    │
    └─ notifyCheckpointComplete(checkpointId)
        └─ splitFetcherManager.notifyCheckpointComplete(checkpointId)
           └─ For Kafka: triggers KafkaConsumer.commitSync() with new offsets
}
```

**Data Type Bridge:**
- Kafka produces: `ConsumerRecord<K, V>` (bytes already deserialized by Kafka's Deserializer)
- Wrapped as: `E` type (e.g., `KafkaSourceRecord<K, V>` or raw ConsumerRecord)
- RecordEmitter applies Flink's `DeserializationSchema<T>` to convert E → T
- Example: E = ConsumerRecord<byte[], byte[]>, T = Trade (POJO)

---

### 5. Dual Serialization Boundary (Critical Architecture Point)

```
┌─────────────────────────────────────────────────────────────────────┐
│ KAFKA SERIALIZATION (First Boundary)                                │
├─────────────────────────────────────────────────────────────────────┤
│ Producer Side:                                                       │
│   ProducerRecord<String, Trade> object                              │
│       ↓ keySerializer.serialize(topic, "trade-123")                 │
│       ↓ valueSerializer.serialize(topic, tradeObj)                  │
│   byte[] key, byte[] value → Broker                                 │
│                                                                      │
│ Consumer Side:                                                       │
│   byte[] key, byte[] value ← Broker                                 │
│       ↓ keyDeserializer.deserialize(topic, keyBytes)                │
│       ↓ valueDeserializer.deserialize(topic, valueBytes)            │
│   ConsumerRecord<String, Trade> object (already deserialized)       │
└─────────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FLINK DESERIALIZATION (Second Boundary)                             │
├─────────────────────────────────────────────────────────────────────┤
│ Flink's DeserializationSchema<T> (Flink-specific)                   │
│   Input: byte[] (from ConsumerRecord.value() - already deserialized │
│           by Kafka's Deserializer<V>)                               │
│       OR: ConsumerRecord<K, V> (for Flink to deserialize differently)
│       ↓ schema.deserialize(bytes) or                                │
│         schema.deserialize(bytes, Collector<T> out)                 │
│   Output: T (Flink's desired type)                                  │
│                                                                      │
│ Example: ConsumerRecord<String, byte[]> (value is JSON bytes)       │
│    ↓ CustomJsonDeserializationSchema                                │
│    ↓ ObjectMapper.readValue(bytes, Trade.class)                     │
│   T = Trade POJO (deserialized in Flink)                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Implication:** Two deserialization stages exist:
1. **Kafka Stage** (Kafka client library): Enforced on ConsumerRecord fields
2. **Flink Stage** (Flink connector): Optional, user-defined, for POJO conversion

Many Kafka connectors use Kafka's Deserializer for raw bytes/strings, then apply Flink's DeserializationSchema for type conversion.

---

### 6. Checkpoint-Offset Integration (Most Complex)

```
┌─────────────────────────────────────────────────────────────────────┐
│ FLINK CHECKPOINT MECHANISM                                          │
├─────────────────────────────────────────────────────────────────────┤
│
│ 1. Checkpoint Triggered (Coordinator)
│    ├─ checkpointId = 12345
│    ├─ SplitEnumerator.snapshotState(12345) → EnumChkT
│    └─ SourceOperator.snapshotState(checkpointId) is called
│
│ 2. SourceOperator.snapshotState(StateSnapshotContext) [line 608]
│    ├─ checkpointId = context.getCheckpointId()  // e.g., 12345
│    ├─ readerState.update(sourceReader.snapshotState(checkpointId))
│    │   ↓
│    │   SourceReader.snapshotState(12345) -> List<SplitT>
│    │   ├─ For each split:
│    │   │   SplitContext<T, SplitStateT> {
│    │   │       currentOffset = 5000  // offset progress
│    │   │       watermark = 2024-01-15T10:30:00Z
│    │   │   }
│    │   ├─ Return list of splits with embedded state
│    │   └─ Example: [TopicPartition(0, "trades"), offset=5000]
│    │
│    └─ ListState<SplitT> readerState (Flink's state backend)
│        ├─ Persist to RocksDB / StateBackend
│        └─ Serialized via Source.getSplitSerializer()
│
│ 3. Checkpoint Completes (Coordinator confirms all tasks)
│    └─ SourceOperator.notifyCheckpointComplete(12345) [line 640]
│        ├─ super.notifyCheckpointComplete(12345)
│        └─ sourceReader.notifyCheckpointComplete(12345)
│            ├─ SourceReaderBase.notifyCheckpointComplete(12345)
│            │   ├─ splitFetcherManager.notifyCheckpointComplete(12345)
│            │   │   └─ For each SplitFetcher:
│            │   │       └─ SplitReader.notifyCheckpointComplete(12345) [Kafka-specific]
│            │   │           ├─ Retrieve offsets for checkpoint 12345
│            │   │           │   (from snapshots taken at step 2)
│            │   │           ├─ Build Map<TopicPartition, OffsetAndMetadata> {
│            │   │           │      (TopicPartition(topic="trades", partition=0),
│            │   │           │       OffsetAndMetadata(5001, "flink-12345"))
│            │   │           │   }
│            │   │           │   Note: offset = 5001, not 5000!
│            │   │           │   (Kafka offset = last consumed + 1)
│            │   │           ├─ kafkaConsumer.commitSync(offsetMap, timeout)
│            │   │           └─ Kafka broker stores in __consumer_offsets
│            │   │
│            │   └─ Clear in-progress splits not in latest checkpoint
│            │
│            └─ Implements CheckpointListener interface
│
└─────────────────────────────────────────────────────────────────────┘

Recovery Scenario:
┌─────────────────────────────────────────────────────────────────────┐
│ RECOVERY FROM CHECKPOINT                                            │
├─────────────────────────────────────────────────────────────────────┤
│
│ 1. Task fails after processing offset 5000
│ 2. Flink restores ListState<SplitT> from checkpoint 12345
│    ├─ Deserialize splits via Source.getSplitSerializer()
│    └─ SourceReader receives: [TopicPartition(0, "trades"), offset=5000]
│
│ 3. SourceReaderBase.addSplits(splits) [called during initialization]
│    ├─ SplitReader.handleSplitsChanges(SplitsChange {add, remove})
│    │   └─ For Kafka: kafkaConsumer.assign(TopicPartition(0))
│    │               kafkaConsumer.seek(TopicPartition(0), 5001)
│    │               (seek to offset 5001: next unprocessed record)
│    │
│    └─ Guarantees exactly-once semantics (no duplicate processing)
│
│ 4. Resume polling from offset 5001
│    └─ KafkaConsumer.poll() returns records starting at 5001
│
└─────────────────────────────────────────────────────────────────────┘
```

**Critical Integration Points:**
1. **SourceOperator (Runtime)** ← checkpoint coordination hub
   - Receives checkpoint signal from TaskManager
   - Orchestrates split state snapshot
   - Delegates offset commit on completion

2. **SourceReaderBase** ← implements CheckpointListener
   - Tracks split progress (offset) in SplitStateT
   - Returns list of splits for snapshotState()
   - Receives notifyCheckpointComplete() callback

3. **KafkaConsumer** ← Flink delegates to Kafka's commit API
   - commitSync() called with `Map<TopicPartition, OffsetAndMetadata>`
   - Each OffsetAndMetadata = (offset + 1, metadata string)
   - Stores in Kafka's __consumer_offsets topic
   - Used on recovery: consumer.committed() retrieves last committed

---

### 7. Consumer Group Coordination Model

```
KafkaConsumer (single instance per SourceReader subtask) {
    properties {
        groupId: "flink-job-trades"           // Flink job identifies itself
        enableAutoCommit: false               // Manual, checkpoint-driven
        isolationLevel: "read_committed"      // Strong consistency
        sessionTimeoutMs: 30000
    }

    Consumer Coordinator (internal Flink thread) {
        Heartbeat: ↔ Kafka Group Coordinator broker
        RebalanceListener: notifies on partition assignment changes
        Offset Storage: Commits to __consumer_offsets via broker
    }
}

Kafka Broker Side (__consumer_offsets internal topic):
├─ Topic: __consumer_offsets (compacted)
├─ Key: (groupId="flink-job-trades", topic="trades", partition=0)
├─ Value: OffsetAndMetadata {
│      offset: 5001              // Next record to consume
│      metadata: "flink-12345"   // Checkpoint ID as context
│      leaderEpoch: 10           // For log truncation detection
│  }
├─ Used by: All consumers in group "flink-job-trades"
│           for resuming after failure
└─ Retention: Indefinite (compacted topic keeps latest offset per partition)

Flink's Advantage:
├─ Explicit checkpoint-driven commits (not auto)
├─ Can recover to exact checkpoint state
├─ Metadata field stores checkpoint ID for audit trail
└─ No silent auto-commits that could lose progress
```

---

### 8. Thread Architecture: Kafka Fetcher vs Flink SplitFetcherManager

```
Kafka Client Internals (Single KafkaConsumer instance):
┌─────────────────────────────────┐
│ Application Thread (Main)       │ (blocking on poll())
│ KafkaConsumer<K, V>.poll()      │
└─────────────┬───────────────────┘
              │
        ┌─────┴────────┐
        ↓              ↓
┌───────────────────┐ ┌─────────────────────┐
│ Fetcher Thread    │ │ Sender Thread       │
│ (background I/O)  │ │ (batching producer) │
│ ├─ Partition 0    │ │ (not used in Source)│
│ ├─ Partition 1    │ └─────────────────────┘
│ └─ Partition 2    │
└───────────────────┘

Flink SplitFetcherManager (Connector-Base):
┌─────────────────────────────────────────────────┐
│ SourceReaderBase (Main Streaming Thread)        │ (mailbox)
│ pollNext(ReaderOutput<T>) { elementsQueue.poll()}
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
┌─────────────────┐  ┌─────────────────┐
│ SplitFetcher #1 │  │ SplitFetcher #2 │ (thread pool)
│ ├─ SplitReader  │  │ ├─ SplitReader  │
│ │   ├─ KafkaConsumer  │   ├─ KafkaConsumer
│ │   └─ poll()   │  │   └─ poll()   │
│ └─ push to queue│  │ └─ push to queue│
└─────────────────┘  └─────────────────┘

FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>
   ↑ fetchers push blocking (records from fetch())
   │ main thread polls non-blocking
   └─ Decouples I/O from streaming thread

Key Advantage:
├─ Kafka's Fetcher is single-threaded per consumer
├─ Flink wraps in SplitFetcher threads (pool)
│  allowing parallel fetch + deserialization
├─ Non-blocking main thread (mailbox executor model)
└─ Better latency for high-parallelism deployments
```

---

## Analysis: Complete Data Flow Integration

### A. Writing Path (Producer to Kafka)

**Flow:**
1. User creates `ProducerRecord<String, Trade>` with topic "trades", key "T-001", value Trade object
2. KafkaProducer's internal logic:
   - Calls `keySerializer.serialize("trades", null, "T-001")` → `[0x54, 0x2D, 0x30, 0x30, 0x31]` (UTF-8 bytes)
   - Calls `valueSerializer.serialize("trades", null, tradeObj)` → custom bytes (e.g., JSON serialized)
   - Batches record with others (configurable linger.ms, batch.size)
   - Sender thread writes to Kafka broker
3. Kafka broker appends to partition 0's log, assigns offset 5000
4. Returns RecordMetadata(topic="trades", partition=0, offset=5000, timestamp=...)

**Architecture**: Synchronous API (Future-based), asynchronous execution (background sender thread).

---

### B. Reading Path (Kafka to Consumer)

**Flow:**
1. KafkaConsumer initialized with groupId="flink-job-trades", enableAutoCommit=false
2. Consumer assigned `TopicPartition(topic="trades", partition=0)` via group coordination
3. Kafka broker's high water mark (HWM) = 5000 (latest committed offset)
4. Consumer's Fetcher thread reads from HWM (or explicit seek position)
5. Broker returns batch: `[ConsumerRecord(offset=5000, value=[JSON bytes]), ConsumerRecord(offset=5001, ...)]`
6. Fetcher thread deserializes via valueDeserializer: JSON bytes → Trade object
7. KafkaConsumer.poll() returns `ConsumerRecords<String, Trade>` containing already-deserialized records
8. Application (Flink) receives ConsumerRecord with offset, key, value, timestamp metadata

**Key Behavior:**
- Deserialization happens in Kafka's Fetcher thread (background)
- poll() returns objects, not bytes
- Offset tracking is automatic but commit is manual (when enabled)

---

### C. Flink Source Integration (Bridging Kafka to Flink)

**Flow:**
1. FlinkKafkaSource (in separate flink-connector-kafka repo) implements Source<T, KafkaSourceSplit, KafkaSourceEnumeratorState>
2. Splits: Each TopicPartition(topic, partition) becomes one split
3. SplitEnumerator (coordinator):
   - Creates KafkaConsumer(adminProps) to list partitions via KafkaConsumer.partitionsFor("trades")
   - Discovers Topic="trades" has 4 partitions
   - Generates 4 splits: [KafkaSourceSplit(topic="trades", partition=0, startOffset=0, endOffset=MAX)]
   - Assigns splits to readers: splits [0,1] → reader0, splits [2,3] → reader1
4. SourceReader (parallel task):
   - Creates KafkaConsumer with consumerGroupId="flink-job-trades"
   - Receives splits via addSplits()
   - For each split: kafkaConsumer.assign(), kafkaConsumer.seek(offset)

**Serialization Layers:**
- Kafka split state is serialized via Source.getSplitSerializer()
- Example: KafkaSourceSplit(topic, partition, startOffset, endOffset) → SimpleVersionedSerializer stores binary form
- On recovery: deserialize splits, seek KafkaConsumer to startOffset

---

### D. Deserialization in SourceReaderBase (RecordEmitter)

**Flow:**
1. SplitFetcher calls SplitReader.fetch() (Kafka-specific wrapper)
   - Returns RecordsWithSplitIds<ConsumerRecord<K, V>> (type E)
2. SourceReaderBase.pollNext() receives batch:
   ```java
   currentFetch = elementsQueue.poll()  // { splitId="topic-partition-0", records=[CR1, CR2, ...] }
   for (ConsumerRecord<K, V> record : currentFetch.getRecords(splitId)) {
       recordEmitter.emitRecord(record, output, splitState);  // apply Flink schema
   }
   ```
3. RecordEmitter (user implementation for KafkaSource):
   ```java
   emitRecord(ConsumerRecord<byte[], byte[]> cr, SourceOutput<Trade> output, KafkaSplitState state) {
       // Flink's DeserializationSchema<Trade>
       byte[] valueBytes = cr.value();  // already bytes (Kafka's deserializer not used)
       Trade trade = schema.deserialize(valueBytes);  // JSON → POJO
       output.collect(trade);
       state.offset = cr.offset();  // update progress
   }
   ```
4. ReaderOutput sends typed record downstream (to map, filter, sink operators)

**Key Point:** Kafka's Deserializer might be ByteArrayDeserializer (returns bytes), and Flink's DeserializationSchema handles type conversion. OR, Kafka deserializes to String/Trade, and Flink's schema is identity/passthrough.

---

### E. Checkpoint Mechanism (Exactly-Once Guarantees)

**Scenario:** Checkpoint 12345 with 100ms alignment timeout

**Step 1: Snapshot (All Tasks)**
```
JobManager checkpoint coordinator
├─ assignCheckpointID(12345)
├─ Barrier injected into all sources
│
TaskManager (SourceOperator) receives barrier:
├─ snapshotState(StateSnapshotContext) is called synchronously
│   ├─ readerState.update(sourceReader.snapshotState(12345))
│   │   ├─ SourceReaderBase iterates splits
│   │   ├─ For each: KafkaSplitState { offset=5000, watermark=2024-01-15T10:30:00Z }
│   │   └─ Serializes via Source.getSplitSerializer()
│   └─ readerState persisted to state backend (RocksDB)
│
├─ Barrier forwarded downstream (to operators, sinks)
└─ Task acknowledges barrier
```

**Step 2: Completion (Coordinator)**
```
JobManager
├─ Receives acks from all tasks
├─ Checkpoint 12345 is durable (no data loss on failure)
└─ Coordinator calls notifyCheckpointComplete(12345) on all tasks
```

**Step 3: Commit Offsets (All Tasks)**
```
TaskManager (SourceOperator) receives notifyCheckpointComplete(12345):
├─ notifyCheckpointComplete(12345)  [line 640-642 SourceOperator.java]
│   ├─ super.notifyCheckpointComplete(12345)
│   └─ sourceReader.notifyCheckpointComplete(12345)
│       ├─ SourceReaderBase.notifyCheckpointComplete(12345)
│       │   ├─ Retrieve splits from checkpoint 12345
│       │   │   (loaded from state backend)
│       │   │   splits = [KafkaSplit(topic="trades", partition=0, offset=5000)]
│       │   │
│       │   ├─ Build offsetMap:
│       │   │   Map<TopicPartition, OffsetAndMetadata> {
│       │   │     (TopicPartition("trades", 0), OffsetAndMetadata(5001, "flink-12345"))
│       │   │   }
│       │   │   Note: 5001 = next-to-consume offset
│       │   │
│       │   ├─ kafkaConsumer.commitSync(offsetMap, timeout)
│       │   │   ├─ KafkaConsumer sends OffsetCommitRequest to coordinator
│       │   │   ├─ Broker writes to __consumer_offsets topic
│       │   │   └─ Returns success (or throws exception on timeout/error)
│       │   │
│       │   └─ Clear old split states for older checkpoints
│       │
│       └─ Task acknowledges completion
```

**Step 4: Recovery (On Failure)**
```
New TaskManager (restart due to failure at offset 5050)

Initialize SourceOperator:
├─ initializeState(StateInitializationContext)
│   └─ readerState = load from state backend checkpoint 12345
│       splits = [KafkaSplit(offset=5000)]
│
├─ Create SourceReader
├─ Create KafkaConsumer with groupId="flink-job-trades"
├─ addSplits([KafkaSplit(offset=5000)])
│   └─ SplitReader.handleSplitsChanges(add=[KafkaSplit(offset=5000)])
│       ├─ kafkaConsumer.assign(TopicPartition("trades", 0))
│       ├─ kafkaConsumer.seek(TopicPartition("trades", 0), 5001)
│       │   (seek to next unprocessed offset)
│       └─ Ready to fetch from offset 5001
│
└─ Resume polling
   └─ First record from broker: offset 5001 (no duplicates, no data loss)
```

**Guarantees:**
- **Atomicity:** Snapshot and commit are separate phases, preventing partial failures
- **Durability:** State stored in Flink state backend + Kafka offset commit
- **Idempotency:** Offset points to "next record", reprocessing from same offset is safe
- **Consistency:** CheckpointListener.notifyCheckpointComplete() only called after barrier propagates through all tasks

---

### F. Watermark & Event Time Integration

```
SourceOperator contains TimestampsAndWatermarks<OUT> {
    WatermarkStrategy watermarkStrategy
    ├─ WatermarkGenerator (stateful per task)
    │   ├─ onEvent(T element, long eventTimestamp)
    │   └─ onPeriodicEmit(WatermarkOutput)
    │
    └─ Assigns timestamp = element.eventTime (from ConsumerRecord.timestamp())
        └─ Kafka broker timestamp (log append time) or producer-assigned
}

Example flow:
├─ KafkaConsumer.poll() returns ConsumerRecord(timestamp=2024-01-15T10:30:00.123)
├─ SourceReaderBase.pollNext() emits: output.collect(trade)
│   └─ SourceOutput applies watermark strategy
│       ├─ Assign timestamp from trade.eventTime or ConsumerRecord.timestamp()
│       ├─ Watermark generator consumes timestamp
│       ├─ Periodically emits Watermark(currentWatermark)
│       └─ Watermark propagates to downstream operators
│
└─ Downstream operators use watermark for:
    ├─ Window closing (tumbling 1-minute windows)
    ├─ Late event handling (allowed lateness)
    └─ Join timeouts (stream joins)
```

---

## Summary

**Kafka-Flink streaming data flow** is a two-stage architecture:

1. **Kafka Stage** (producers write, consumer reads partition logs):
   - Producer: serialize via `Serializer<T>` → ProducerRecord → Kafka broker
   - Consumer: broker returns ConsumerRecord → deserialize via `Deserializer<T>` → application receives object
   - Offsets: managed by consumer group coordinator, persisted in `__consumer_offsets`

2. **Flink Stage** (source connector bridges to streaming runtime):
   - Source API abstracts splits (TopicPartition) and enumerator (discovery)
   - SourceReaderBase + SplitFetcherManager wrap KafkaConsumer in thread pool for parallelism
   - RecordEmitter applies Flink's `DeserializationSchema` for type conversion
   - **Checkpoint Mechanism:**
     - Snapshot: SourceOperator calls sourceReader.snapshotState() → stores split offsets
     - Commit: SourceOperator calls sourceReader.notifyCheckpointComplete() → triggers kafkaConsumer.commitSync() with `OffsetAndMetadata(offset+1, checkpointId)`
     - Recovery: reloads split state from state backend, seeks KafkaConsumer to next offset, resumes from checkpoint boundary

**Key Insight:** Flink delegates offset management to Kafka's consumer group coordination (via `commitSync()`) but controls **when** commits happen (on checkpoint completion, not auto). This enables exactly-once semantics: the checkpoint ID serves as a commit marker, allowing recovery to a consistent point across all operators.

The dual serialization boundary (Kafka Serializer/Deserializer + Flink DeserializationSchema) allows flexibility: Kafka handles partition-level serialization, while Flink applies domain-specific type conversion in the streaming context.
