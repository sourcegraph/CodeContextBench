# Kafka-Flink Streaming Data Flow Architecture Analysis

## Files Examined

### Apache Kafka (clients/src)
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/Producer.java** — Producer interface defining send/flush/close semantics
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java** — Concrete producer implementation with Serializer integration and internal Sender thread
- **kafka/clients/src/main/java/org/apache/kafka/clients/producer/ProducerRecord.java** — Key/value record wrapper with topic, partition, headers, and timestamp metadata
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/Consumer.java** — Consumer interface defining subscribe/poll/commitSync/commitAsync patterns
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java** — Concrete consumer implementation with group coordination and offset management
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerRecord.java** — Deserialized record with topic, partition, offset, timestamp, key, value, and leader epoch
- **kafka/clients/src/main/java/org/apache/kafka/clients/consumer/OffsetAndMetadata.java** — Offset commit container with offset, metadata, and leader epoch for exactly-once semantics
- **kafka/clients/src/main/java/org/apache/kafka/common/serialization/Serializer.java** — Interface converting typed objects to byte arrays (used by producer)
- **kafka/clients/src/main/java/org/apache/kafka/common/serialization/Deserializer.java** — Interface converting byte arrays to typed objects (used by consumer)

### Apache Flink (flink-core)
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/Source.java** — Factory interface creating SourceReader and SplitEnumerator, manages split/checkpoint serialization
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SourceReader.java** — Interface for reading from splits, implements CheckpointListener for offset commits on checkpoint completion
- **flink/flink-core/src/main/java/org/apache/flink/api/connector/source/SplitEnumerator.java** — Interface discovering splits and assigning to readers, implements CheckpointListener for enumerator state
- **flink/flink-core/src/main/java/org/apache/flink/api/common/serialization/DeserializationSchema.java** — Schema for deserializing Kafka byte payloads to Flink objects (dual boundary with Kafka Deserializer)

### Apache Flink (flink-connector-base)
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/SourceReaderBase.java** — Abstract implementation of SourceReader managing SplitFetcherManager and RecordEmitter
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/splitreader/SplitReader.java** — Interface for fetching records from a data source (Kafka consumer wraps this)
- **flink/flink-connectors/flink-connector-base/src/main/java/org/apache/flink/connector/base/source/reader/RecordEmitter.java** — Interface for emitting fetched records with split state updates (timestamp extraction, offset tracking)

### Apache Flink (flink-runtime)
- **flink/flink-runtime/src/main/java/org/apache/flink/streaming/api/operators/SourceOperator.java** — Runtime operator implementing checkpoint protocol: snapshotState() calls SourceReader.snapshotState(), notifyCheckpointComplete() triggers SourceReader.notifyCheckpointComplete() for Kafka offset commits

---

## Dependency Chain

```
                         ┌─────────────────────────────────────────┐
                         │      DATA FLOW: Producer Path            │
                         └─────────────────────────────────────────┘

ProducerRecord<K, V>
   │ (topic, partition, key, value, headers, timestamp)
   │
   ├─→ KafkaProducer.send(ProducerRecord)
   │     │
   │     ├─→ Serializer<K>.serialize(topic, key)   [Kafka serde boundary]
   │     │
   │     ├─→ Serializer<V>.serialize(topic, value) [Kafka serde boundary]
   │     │
   │     └─→ RecordAccumulator → Sender (internal thread)
   │           │
   │           └─→ Broker (network I/O)


                    ┌─────────────────────────────────────────┐
                    │     DATA FLOW: Consumer + Flink Path    │
                    └─────────────────────────────────────────┘

KafkaConsumer.poll(Duration)
   │ (consumer group, partition assignment, offset tracking)
   │
   ├─→ Fetcher (internal) → Broker fetch
   │
   └─→ Deserializer<K>.deserialize(topic, key_bytes)
   └─→ Deserializer<V>.deserialize(topic, value_bytes)
        │
        └─→ ConsumerRecord<K, V>
             │ (offset, partition, timestamp, key, value, headers)
             │
             ├─→ [FLINK CONNECTOR WRAPPING HERE]
             │
             └─→ SplitReader.fetch()  [flink-connector-kafka wrapper]
                  │
                  ├─→ RecordsWithSplitIds<ConsumerRecord>
                  │
                  └─→ SourceReaderBase (polling loop in fetcher thread)
                       │
                       ├─→ RecordEmitter.emitRecord(ConsumerRecord, output, splitState)
                       │    │
                       │    ├─→ [OPTIONAL] DeserializationSchema<T>.deserialize(bytes)
                       │    │    [Dual serde boundary: Kafka Deserializer + Flink Schema]
                       │    │
                       │    └─→ SourceOutput<T> (downstream task)
                       │
                       └─→ SourceOperator.pollNext(ReaderOutput)
                            │
                            └─→ Flink Task Thread


                    ┌──────────────────────────────────────────┐
                    │    CHECKPOINT: State Snapshot Path       │
                    └──────────────────────────────────────────┘

JobManager.triggerCheckpoint(checkpointId)
   │
   └─→ SourceOperator.snapshotState(StateSnapshotContext)
       │
       ├─→ sourceReader.snapshotState(checkpointId)
       │    │ (returns List<SplitT> with current offsets)
       │    │
       │    └─→ SourceReaderBase.snapshotState()
       │         │
       │         └─→ SplitReader's internal offset state
       │              (KafkaConsumer's current position)
       │
       └─→ readerState.update(splits)  [ListState<SplitT>]


                    ┌──────────────────────────────────────────┐
                    │    CHECKPOINT: Offset Commit Path        │
                    └──────────────────────────────────────────┘

JobManager.notifyCheckpointComplete(checkpointId)
   │
   └─→ SourceOperator.notifyCheckpointComplete(checkpointId)
       │
       └─→ sourceReader.notifyCheckpointComplete(checkpointId)
           │
           └─→ SourceReaderBase.notifyCheckpointComplete()
               │
               └─→ SplitFetcherManager → Fetcher Thread
                   │
                   └─→ KafkaConsumer.commitSync(Map<TopicPartition, OffsetAndMetadata>)
                       │
                       └─→ Broker OffsetCommit API
                           (consumer group __consumer_offsets topic)
```

---

## Detailed Analysis

### 1. Kafka Producer API

**Role in Architecture:** Source of data before Kafka cluster.

The Kafka producer API defines the boundary for sending data into Kafka:
- **Producer<K, V> interface** (producer/Producer.java): Generic contract with `send(ProducerRecord)`, `flush()`, `commitTransaction()` methods
- **ProducerRecord<K, V>** (producer/ProducerRecord.java): Immutable data container with:
  - `topic`: target Kafka topic
  - `partition`: optional partition assignment
  - `key`: optional routing key for partition selection
  - `value`: actual message payload
  - `headers`: record metadata (can be used for tracing, schema versions)
  - `timestamp`: event time or ingestion time

- **KafkaProducer** (producer/KafkaProducer.java): Concrete implementation with:
  - Internal `RecordAccumulator` (batches records for efficiency)
  - Internal `Sender` thread (background I/O for non-blocking send)
  - **First serialization boundary:** `Serializer<K>` and `Serializer<V>` convert typed objects to byte arrays before network transmission

**Relevance to Kafka-Flink:** The producer path is typically used in reverse—Flink SINKs write to Kafka. The focus of this analysis is the CONSUMER path (data flowing INTO Flink).

---

### 2. Kafka Consumer API

**Role in Architecture:** Primary ingestion point for streaming data from Kafka into Flink.

The Kafka consumer API provides the fundamental offset management and record delivery semantics:

- **Consumer<K, V> interface** (consumer/Consumer.java): Generic contract defining:
  - `subscribe(Collection<String> topics)` — Join consumer group and listen to topics
  - `assign(Collection<TopicPartition> partitions)` — Manual partition assignment (no group coordination)
  - `poll(Duration timeout)` → `ConsumerRecords<K, V>` — Block and fetch available records
  - `commitSync(Map<TopicPartition, OffsetAndMetadata>)` — Synchronously commit offsets to broker
  - `commitAsync(OffsetCommitCallback)` — Asynchronously commit offsets

- **KafkaConsumer** (consumer/KafkaConsumer.java): Concrete implementation:
  - Maintains consumer group membership via heartbeats and coordination protocol
  - Internal `Fetcher` (fetcher/Fetcher.java): Manages fetch requests, decompression, record parsing
  - Internal `SubscriptionState`: Tracks assigned partitions, current fetch position, and committed offsets per partition
  - **Second serialization boundary:** `Deserializer<K>` and `Deserializer<V>` convert byte arrays to typed objects **after** network transmission

- **ConsumerRecord<K, V>** (consumer/ConsumerRecord.java): Deserialized record containing:
  - `offset`: Kafka partition offset (used for exactly-once semantics)
  - `partition`: partition number
  - `topic`: topic name
  - `key`: deserialized key or null
  - `value`: deserialized payload
  - `timestamp`: broker timestamp or producer timestamp
  - `leaderEpoch`: broker leader epoch (detects log truncation)
  - `serializedKeySize`, `serializedValueSize`: for metrics

- **OffsetAndMetadata** (consumer/OffsetAndMetadata.java): Offset commit container:
  - `offset`: The partition offset to commit (next offset to be consumed)
  - `metadata`: Optional string metadata (can store consumer checkpoint ID or custom data)
  - `leaderEpoch`: Leader epoch at the time of commit (enables truncation detection)
  - Used in `commitSync(Map<TopicPartition, OffsetAndMetadata>)` calls

- **Serializer/Deserializer interfaces**:
  - `Serializer<T>.serialize(topic, headers, data) → byte[]`
  - `Deserializer<T>.deserialize(topic, headers, bytes) → T`
  - These are **Kafka's internal serde boundary**, independent of Flink's schema system

---

### 3. Flink Source API (flink-core)

**Role in Architecture:** Abstraction layer defining how data flows into Flink operators from external systems.

The Source API is Flink's unified abstraction (FLIP-27) for connector development:

- **Source<T, SplitT, EnumChkT> interface** (api/connector/source/Source.java): Factory pattern:
  - `createEnumerator(SplitEnumeratorContext)` → Creates `SplitEnumerator` for discovering work
  - `createReader(SourceReaderContext)` → Creates `SourceReader` for reading one split
  - `getSplitSerializer()` → Returns versioned serializer for splits (used in checkpointing)
  - `getEnumeratorCheckpointSerializer()` → Returns serializer for enumerator state
  - **Generic parameters:**
    - `T`: The type emitted to downstream operators (e.g., `Trade`, `PriceQuote`)
    - `SplitT extends SourceSplit`: Work unit type (e.g., `KafkaPartitionSplit` with partition number)
    - `EnumChkT`: Enumerator checkpoint type (e.g., `TopicPartition[]` list)

- **SourceReader<T, SplitT> interface** (api/connector/source/SourceReader.java): Runtime reader:
  - `start()` — Called once at task initialization
  - `pollNext(ReaderOutput<T> output) → InputStatus` — Non-blocking poll for one record
  - `snapshotState(checkpointId) → List<SplitT>` — Returns current splits with their offset state
  - `notifyCheckpointComplete(checkpointId)` — **Critical for Kafka offset commits** (see section 6)
  - Extends `CheckpointListener` for Flink's exactly-once semantics

- **SplitEnumerator<SplitT, CheckpointT> interface** (api/connector/source/SplitEnumerator.java): Coordinator:
  - `start()` — Begin discovering splits
  - `handleSplitRequest(subtaskId, hostname)` — Reader requests more work
  - `addSplitsBack(List<SplitT>, subtaskId)` — Handle reader failure recovery
  - `snapshotState(checkpointId) → CheckpointT` — Snapshot enumerator state
  - Extends `CheckpointListener`
  - **For Kafka:** Lists topics, discovers partitions, assigns partition-splits to readers

---

### 4. Flink Connector-Base Framework

**Role in Architecture:** Reusable base classes implementing the common patterns for connectors.

The connector-base module provides template implementations to reduce boilerplate:

- **SourceReaderBase<E, T, SplitT, SplitStateT>** (connector/base/source/reader/SourceReaderBase.java):
  - Abstract implementation of `SourceReader<T, SplitT>`
  - Manages a **SplitFetcherManager**: Thread pool running `SplitReader` instances in background fetcher threads
  - Provides a **FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>**: Thread-safe handoff from fetcher threads to task thread
  - Integrates **RecordEmitter<E, T, SplitStateT>**: Processes each fetched record (timestamp extraction, state updates)
  - **Generic parameters:**
    - `E`: Intermediate element type from SplitReader (e.g., raw `ConsumerRecord<byte[], byte[]>`)
    - `T`: Final element type emitted downstream (e.g., deserialized `Trade` object)
    - `SplitStateT`: Mutable split state (e.g., `KafkaPartitionSplit.OffsetState` with current offset)

- **SplitReader<E, SplitT> interface** (connector/base/source/reader/splitreader/SplitReader.java): Blocking fetcher:
  - `fetch() → RecordsWithSplitIds<E>` — Block and fetch records from source (e.g., `KafkaConsumer.poll()`)
  - `handleSplitsChanges(SplitsChange<SplitT>)` — Non-blocking: handle split additions/removals
  - `wakeUp()` — Interrupt blocking fetch (used for graceful shutdown)
  - `pauseOrResumeSplits(pause, resume)` — Watermark alignment support
  - **For Kafka:** Wraps `KafkaConsumer`, transforms `ConsumerRecord` into `RecordsWithSplitIds`

- **RecordEmitter<E, T, SplitStateT> interface** (connector/base/source/reader/RecordEmitter.java): Transform and emit:
  - `emitRecord(E element, SourceOutput<T> output, SplitStateT splitState)` — Process one fetched record
  - Called per-record in task thread (not in fetcher thread)
  - Updates `splitState` with offset/position info (for snapshotting)
  - **For Kafka:**
    - Applies `DeserializationSchema<T>` if needed (optional second deserialization)
    - Updates `KafkaPartitionSplit.OffsetState` with consumed offset
    - Extracts timestamp via `WatermarkStrategy`

- **SplitFetcherManager<E, SplitT>**: Manages thread pool:
  - One `SplitFetcher` thread per logical "split reader" (may manage multiple Kafka partitions)
  - Queues `FetchTask`, `AddSplitsTask`, `RemoveSplitsTask` for thread-safe communication
  - Coordinates between task thread and fetcher threads

---

### 5. Serialization/Deserialization Boundary (Dual Serde Model)

**Role in Architecture:** Two independent serialization layers bridge Kafka and Flink type systems.

This is a critical architectural insight—there are **two separate serde boundaries**:

#### Boundary 1: Kafka's Internal Serializer/Deserializer
- Located at network I/O layer in `KafkaProducer` and `KafkaConsumer`
- **Producer side:** `Serializer<K>.serialize()` and `Serializer<V>.serialize()` convert Java objects to byte arrays
- **Consumer side:** `Deserializer<K>.deserialize()` and `Deserializer<V>.deserialize()` convert byte arrays to Java objects
- Example: `JsonDeserializer` for JSON payloads, `StringDeserializer` for strings, `BytesDeserializer` for raw bytes
- **Flink's role:** Configure KafkaConsumer with Kafka-native serializers (built-in or custom)

#### Boundary 2: Flink's DeserializationSchema
- Located in `RecordEmitter.emitRecord()` within the Flink task thread
- `DeserializationSchema<T>.deserialize(byte[] bytes) → T`
- **Optional:** If Kafka's deserializer output is sufficient, schema can be a pass-through identity
- **Complex cases:** Schema can apply additional transformations (schema registry lookup, field projection, type conversion)
- Example: `AvroDeserializationSchema`, `JsonDeserializationSchema`, custom `DeserializationSchema` implementations
- **Rationale:** Allows Flink connectors to apply Flink-specific transformations while Kafka handles its own serde

#### Data Type Flow Example
```
Kafka Network (bytes)
    ↓
KafkaConsumer.poll()
    ↓ [Kafka Deserializer]
ConsumerRecord<K, V>  (K and V are already deserialized Java objects)
    ↓ [Flink wraps]
RecordsWithSplitIds<ConsumerRecord<K, V>>
    ↓ [SourceReaderBase.pollNext() → RecordEmitter.emitRecord()]
    ↓ [Flink DeserializationSchema (optional, if ConsumerRecord value is bytes)]
T (final type, e.g., Trade, PriceQuote)
    ↓
Flink Task Output (to downstream operators)
```

In capital markets scenarios:
- **Kafka Deserializer:** Converts wire-format (Avro, Protocol Buffers, FIX) to Java objects or byte arrays
- **Flink DeserializationSchema:** Validates, transforms (filter by exchange, adjust timestamps), enriches with reference data

---

### 6. Checkpoint Mechanism Integration with Kafka Offset Commits

**Role in Architecture:** Achieves exactly-once semantics by coordinating Flink checkpoints with Kafka offset commits.

This is the **core integration point** between Kafka and Flink:

#### The Problem Being Solved
Kafka tracks offsets (which records have been consumed). Flink tracks snapshots (operator state at a point in time). Without coordination:
- If Flink crashes after processing a record but before saving its state, Kafka will re-deliver the record (no exactly-once)
- If Kafka commits an offset before Flink has saved state, offset commit is wasted

#### The Solution: Deferred Offset Commits

Flink uses the **semantic that offset commits only happen AFTER checkpoint completion**, ensuring the processed records are saved:

1. **Snapshot Phase (while checkpoint is being taken):**
   ```
   JobManager.triggerCheckpoint(checkpointId) [barrier in stream]
       ↓
   SourceOperator.snapshotState(StateSnapshotContext context)
       ├─→ long checkpointId = context.getCheckpointId()
       ├─→ sourceReader.snapshotState(checkpointId)
       │    [SourceReader returns List<SplitT> with current offsets]
       │
       └─→ readerState.update(splits)
           [Saves to ListState<byte[]> via split serializer]
   ```
   - `snapshotState()` is called during checkpoint coordination (barriers in stream)
   - Returns the **current position/offset** of each Kafka partition split
   - Offset is NOT committed to Kafka yet (only saved in Flink state backend)
   - This happens on every checkpoint (frequency: e.g., every 1 minute)

2. **Completion Phase (after checkpoint is durable):**
   ```
   JobManager.notifyCheckpointComplete(checkpointId)
       ↓
   SourceOperator.notifyCheckpointComplete(checkpointId)
       ├─→ super.notifyCheckpointComplete(checkpointId)  [operator cleanup]
       │
       └─→ sourceReader.notifyCheckpointComplete(checkpointId)
           [Critical: This triggers offset commit to Kafka]
           ↓
           SourceReaderBase.notifyCheckpointComplete()
               ↓
               SplitFetcherManager
                   ↓
                   Fetcher Thread (non-task thread)
                       ↓
                       KafkaConsumer.commitSync(
                           Map<TopicPartition, OffsetAndMetadata> offsets
                       )
                       [Send OffsetCommit request to Broker]
                       ↓
                       Broker OffsetManager
                           [Stores offset in __consumer_offsets topic]
   ```
   - `notifyCheckpointComplete()` is called ONLY after checkpoint succeeds (has been persisted)
   - This is when Kafka offsets are committed via `KafkaConsumer.commitSync()`
   - The `OffsetAndMetadata` object can include `checkpointId` in the metadata string for tracing

#### Ensuring Exactly-Once Semantics

The guarantee works because:
1. **If Flink crashes during processing:** The checkpoint is not marked as complete → offsets are NOT committed to Kafka → on recovery, Kafka re-delivers the records from the last committed offset
2. **If Flink commits Flink state but crashes before Kafka commit:** `notifyCheckpointComplete()` is not called → offsets NOT committed to Kafka → re-delivery on recovery
3. **Only on successful completion:** Both Flink state AND Kafka offset are committed, ensuring no data loss or duplication

#### Integration Points

- **SourceReader implements CheckpointListener:**
  ```java
  public interface SourceReader<T, SplitT> extends CheckpointListener {
      List<SplitT> snapshotState(long checkpointId);
      default void notifyCheckpointComplete(long checkpointId) throws Exception {}
  }
  ```
  - Framework calls both methods in response to Flink checkpoint lifecycle events

- **SourceOperator delegates to SourceReader:**
  ```java
  public void snapshotState(StateSnapshotContext context) {
      readerState.update(sourceReader.snapshotState(checkpointId));
  }

  public void notifyCheckpointComplete(long checkpointId) {
      sourceReader.notifyCheckpointComplete(checkpointId);  // ← offset commit happens here
  }
  ```

#### Thread Safety Model

- `snapshotState()` — Called in task thread (can safely read current offset from split state)
- `notifyCheckpointComplete()` — Called in task thread, but delegates to `SplitFetcherManager`, which queues the offset commit to the background fetcher thread for thread-safe `KafkaConsumer` access
- `KafkaConsumer.commitSync()` — Runs in fetcher thread, blocking until broker ack

---

### 7. Thread Architecture: Kafka Fetcher vs. Flink SplitFetcherManager

**Role in Architecture:** Non-blocking event processing model that doesn't block the task thread on I/O.

#### Kafka's Thread Model (Inside KafkaConsumer)
- **Task thread:** Calls `KafkaConsumer.poll(Duration timeout)` → Blocks until records available or timeout
- **Fetcher thread (internal):** Background thread fetching from brokers asynchronously
- **Sender thread (internal):** Background thread for offset commits and group coordination
- **Synchronization:** Blocking queue between fetcher and task thread

#### Flink's Thread Model (SourceReaderBase)
- **Task thread:** Calls `SourceReader.pollNext(ReaderOutput) → InputStatus`
  - **MUST be non-blocking** (Flink's guarantee for single-threaded task execution)
  - Returns immediately (either MORE_AVAILABLE, NO_MORE_AVAILABLE, or END_OF_INPUT)

- **Fetcher thread (SourceReaderBase-managed):** Background thread running `SplitReader.fetch()`
  - Calls blocking `KafkaConsumer.poll()` (OK because it's a background thread)
  - Puts records into `FutureCompletingBlockingQueue<RecordsWithSplitIds<E>>`

- **Synchronization:** Non-blocking queue check in task thread:
  ```java
  InputStatus pollNext(ReaderOutput<T> output) {
      RecordsWithSplitIds<E> currentFetch = elementsQueue.poll();  // non-blocking
      if (currentFetch == null) {
          return InputStatus.NOTHING_AVAILABLE;  // task thread continues, no blocking
      }
      // ... emit records via RecordEmitter ...
      return InputStatus.MORE_AVAILABLE;
  }
  ```

#### Advantage for Capital Markets
- Low-latency streaming: Task thread can emit watermarks, process other sources, or backpressure downstream without waiting for Kafka I/O
- Partition-level parallelism: Multiple partitions can be fetched in parallel by fetcher threads, improving throughput

---

### 8. Consumer Group Coordination Model

**Role in Architecture:** Balances load across Kafka partitions among multiple Flink tasks.

#### Kafka's Model
- **Consumer group:** Set of consumers sharing `group.id`
- **Rebalancing:** When consumers join/leave, broker re-assigns partitions to balance load
- **Heartbeat protocol:** Consumers send heartbeats every `heartbeat.interval.ms` to maintain group membership
- **Session timeout:** If no heartbeat for `session.timeout.ms`, consumer is considered dead and partitions re-assigned

#### Flink's Model (via KafkaConsumer)
- Flink task = one consumer instance
- **Parallelism:** Multiple Flink tasks (subtasks 0, 1, 2, ...) → multiple consumers in same group
- **Rebalancing:** On task restart or scale-out, Kafka detects consumer change → re-assigns partitions
- **Flink coordination:** SplitEnumerator + SplitFetcherManager coordinate which task gets which partition
  - Enumerator discovers partitions: `listPartitions("topic")` → `[topic-0, topic-1, topic-2, ...]`
  - Assigns to readers: task-0 gets partition-0, task-1 gets partition-1, etc.
  - On rebalancing, new assignments flow through `handleSplitsChanges()`

#### Example for High-Frequency Trading
```
Kafka Cluster: topic "trades" with 4 partitions
Flink Job: parallelism = 4 (4 tasks)

Partition Assignment:
  Task 0 ↔ topic-trades-0 (NYSE data)
  Task 1 ↔ topic-trades-1 (Nasdaq data)
  Task 2 ↔ topic-trades-2 (CME data)
  Task 3 ↔ topic-trades-3 (London Stock Exchange)

Each task runs in parallel, consuming from its partition(s)
If Task 2 fails:
  - Flink detects failure, restarts Task 2
  - Kafka broker detects consumer absence, rebalances
  - Partitions may be re-assigned to remaining tasks
  - After recovery, new assignments sent to all tasks
```

---

### 9. Capital Markets Streaming Scenario

**Concrete example:** Real-time trade latency calculation system

```
Trades → Kafka [multiple partitions by asset/exchange]
           ↓
      [Flink Source]
           ↓
      Deserialize (JSON/Avro trade record)
           ↓
      Partition by asset:
      [Task 0] Handle AAPL trades → Latency calculator
      [Task 1] Handle MSFT trades → Latency calculator
      [Task 2] Handle GOOG trades → Latency calculator
           ↓
      Calculate P&L, risk metrics
           ↓
      [Flink Sink] Write to TimescaleDB (analytics)
      [Flink Sink] Write to Redis (real-time dashboard)

Checkpoint every 60 seconds:
  1. Inject barrier in stream
  2. Each task snapshots its current state + Kafka partition offset
  3. Checkpoint committed to state backend (HDFS, S3, RocksDB)
  4. Checkpoint marked complete
  5. Flink calls KafkaConsumer.commitSync() for each partition offset
  6. Offsets now persisted in Kafka's __consumer_offsets topic

On failure (e.g., network glitch at T+45s):
  - Last checkpoint at T+0s was complete
  - Offsets committed for T+0s position
  - On recovery:
    - Restore Flink state to T+0s snapshot
    - KafkaConsumer seeks to T+0s committed offset
    - Reprocesses trades from T+0s to T+45s
    - Ensures no missed or duplicated trades in analytics
```

---

## Summary

The Kafka-Flink streaming integration achieves exactly-once semantics through a **two-phase offset commit protocol**:
1. **Snapshot phase:** Flink captures current Kafka partition offsets (without committing) during checkpoint coordination
2. **Completion phase:** Only after checkpoint succeeds, Flink calls `KafkaConsumer.commitSync()` to durably commit offsets

Data flows through **two serialization boundaries** (Kafka's Serializer/Deserializer + Flink's optional DeserializationSchema), a **non-blocking SourceReader interface** that delegates to background fetcher threads wrapping `KafkaConsumer.poll()`, and a **consumer group coordination model** leveraging Kafka's native rebalancing for partition distribution across Flink task parallelism. This architecture provides low-latency, scalable streaming for capital markets workloads (trade ingestion, pricing, risk) with guaranteed exactly-once processing semantics.
