# Kafka Message Lifecycle

## Q1: Producer-Side Batching and Transmission

### Overview
When a producer calls `KafkaProducer.send(record)`, the message travels through several components before reaching the network. The key components are the serializer, partitioner, RecordAccumulator for batching, and the Sender thread for network transmission.

### Detailed Flow

**1. Serialization and Partitioning**
- `KafkaProducer.send(ProducerRecord<K, V> record)` at line 941 in `clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java` calls `doSend()`
- `doSend()` (line 974):
  - Runs ProducerInterceptors.onSend() to allow interceptors to modify records
  - Gets cluster metadata via `waitOnMetadata()` (line 988)
  - Serializes the key using `keySerializerPlugin.get().serialize()` (line 999)
  - Serializes the value using `valueSerializerPlugin.get().serialize()` (line 1007)
  - Determines partition via `partition()` method (line 1017) which applies the configured Partitioner
  - Estimates record size with `AbstractRecords.estimateSizeInBytesUpperBound()` (line 1022)

**2. Batching in RecordAccumulator**
- `RecordAccumulator.append()` is called at line 1029 with serialized key, value, and partition info
- The RecordAccumulator maintains per-partition queues of `ProducerBatch` objects
- Key batching logic in `append()` (line 275 in `clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java`):
  - Gets or creates a TopicInfo for the topic
  - Determines effective partition using BuiltInPartitioner if partition was unknown
  - Checks for in-progress batches in partition queue via `tryAppend()` (line 319)
  - If no suitable batch exists, allocates a buffer via `BufferPool.allocate()` (line 333)
  - Creates new batch via `appendNewBatch()` (line 345):
    - Allocates a `MemoryRecordsBuilder` (line 393)
    - Creates `ProducerBatch` wrapping the builder (line 394)
    - Adds batch to incomplete batches queue via `incomplete.add()` (line 399)
  - Returns `RecordAppendResult` containing future for this record's metadata

**3. Batching Triggers**
- Back in `doSend()` (line 1041), if `result.batchIsFull || result.newBatchCreated`, the Sender thread is awakened via `sender.wakeup()` (line 1043)
- Batches become ready to send when:
  - Batch is full (reaches configured `batch.size`)
  - `linger.ms` timeout expires
  - `flush()` is called

**4. Sender Thread Transmission**
- The Sender thread runs in `Sender.run()` (line 236 in `clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java`)
- Main loop calls `runOnce()` repeatedly (line 242)
- `runOnce()` calls `sendProducerData()` (line 339)
- `sendProducerData()` (line 357):
  - Fetches metadata snapshot via `metadata.fetchMetadataSnapshot()` (line 358)
  - Calls `accumulator.ready()` to get list of ready partitions with data (line 360)
  - Requests metadata update for partitions with unknown leaders (lines 363-372)
  - Removes nodes that aren't ready to send (lines 376-392)
  - Drains batches via `accumulator.drain()` (line 395) - groups batches by destination broker node
  - Calls `sendProduceRequests()` (line 442)

**5. Network Request Building and Sending**
- `sendProduceRequests()` (line 856):
  - Iterates through each node (destination broker) and calls `sendProduceRequest()` for each
- `sendProduceRequest()` (line 864):
  - Groups batches by topic-partition (line 868)
  - Extracts MemoryRecords from each batch (line 874)
  - Builds ProduceRequestData.TopicProduceDataCollection (line 871-886)
  - Creates `ProduceRequest.Builder` with acks, timeout, and optional transactional ID (lines 897-904)
  - Creates `ClientRequest` via `client.newClientRequest()` (line 912)
  - Sends request via `client.send()` (line 914)
  - Registers response callback `handleProduceResponse()` (line 909)

### Key Configuration Parameters
- **batch.size**: Threshold at which batches are sent (default 16KB)
- **linger.ms**: Time to wait for batching before sending (default 0ms)
- **buffer.memory**: Total memory for buffering (default 32MB)
- **acks**: Producer acks requirement (-1/all for full replication, 1 for leader only, 0 for none)
- **compression.type**: Compression applied to batch (none, gzip, snappy, lz4, zstd)

## Q2: Broker-Side Append and Replication

### Overview
When a Produce request arrives at the broker, it follows a precise sequence: routing to the partition leader, validating transaction state, appending to the local log, and coordinating replication to follower replicas.

### Detailed Flow

**1. Request Routing to Partition**
- The broker's network processor receives the ProduceRequest
- `ReplicaManager.handleProduceAppend()` is called (line 731 in `core/src/main/scala/kafka/server/ReplicaManager.scala`) if transactional verification is needed, or `appendRecords()` is called directly (line 674)
- `handleProduceAppend()` (line 731):
  - Wraps responseCallback to run on request handler thread
  - Calls `appendRecords()` with wrapped callback (line 674)

**2. Local Log Append**
- `appendRecords()` (line 674):
  - Validates required acks value (line 683)
  - Calls `appendRecordsToLeader()` to append to local log (line 688)
  - Builds produce partition status (line 698)
  - Calls `maybeAddDelayedProduce()` to handle replication waits (line 704)

- `appendRecordsToLeader()` (line 627):
  - Calls `appendToLocalLog()` to perform the actual append (line 637)
  - Returns map of `TopicIdPartition` to `LogAppendResult`
  - Calls `addCompletePurgatoryAction()` to trigger delayed produce completions (line 647)

- `appendToLocalLog()` (line 1370):
  - For each topic-partition, retrieves the Partition object via `getPartitionOrException()` (line 1407)
  - Calls `partition.appendRecordsToLeader()` (line 1408)
  - Records statistics (bytes/messages in rate, latency)
  - Wraps in `LogAppendResult` containing the `LogAppendInfo`

**3. Partition-Level Append with Replication Coordination**
- `Partition.appendRecordsToLeader()` (line 1361 in `core/src/main/scala/kafka/cluster/Partition.scala`):
  - Acquires read lock on leaderIsrUpdateLock (line 1363)
  - Gets leader log via `leaderLogIfLocal` (line 1364)
  - Validates ISR size against min.insync.replicas (line 1370)
  - Calls `leaderLog.appendAsLeader()` to append to UnifiedLog (line 1376)
  - Checks if high water mark should be incremented via `maybeIncrementLeaderHW()` (line 1379)
  - Returns LogAppendInfo with high water mark change information (line 1387)

**4. UnifiedLog Append**
- `UnifiedLog.appendAsLeader()` (in `storage/src/main/java/org/apache/kafka/storage/log/UnifiedLog.java`):
  - Validates record batch magic version
  - Assigns offsets to messages
  - Writes records to disk via memory-mapped files
  - Returns `LogAppendInfo` containing:
    - First offset: lowest offset in batch
    - Last offset: highest offset in batch
    - Log append time: broker timestamp when appended
    - Number of messages
    - Validation stats

**5. Replication to Followers**
- Replication is handled asynchronously after local append
- `ReplicaFetcherThread` on each follower pulls from leader (in `core/src/main/scala/kafka/server/ReplicaFetcherThread.scala`)
- Follower sends FetchRequest to leader specifying offset to fetch from
- Leader returns messages after local log append
- Follower receives response and calls `Partition.appendRecordsToFollowerOrFutureReplica()` (line 1331 in `core/src/main/scala/kafka/cluster/Partition.scala`)
- Follower appends received messages and updates its high water mark
- As followers acknowledge the append, ISR is maintained

**6. Producer Response**
- `maybeAddDelayedProduce()` (line 704):
  - Creates `DelayedProduce` operation waiting for replication acks
  - If `requiredAcks == -1` (all replicas), waits for all in-sync replicas to acknowledge
  - If `requiredAcks == 1` (leader), responds immediately after local append
  - If `requiredAcks == 0` (none), responds after network send
- `handleProduceResponse()` in Sender (line 568 in `clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java`):
  - Parses ProduceResponse containing base offset and log append time for each partition
  - For each batch, calls `completeBatch()` to resolve the Future with metadata
  - ProducerCallback is invoked with RecordMetadata or error

## Q3: Consumer-Side Fetch and Delivery

### Overview
When a consumer calls `poll()`, it retrieves messages previously appended to the broker via a coordinated fetch process, deserializes them, and manages offset commits.

### Detailed Flow

**1. Poll Entry Point**
- `KafkaConsumer.poll(Duration timeout)` (line 894 in `clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java`):
  - Delegates to internal delegate (ClassicKafkaConsumer or AsyncKafkaConsumer)
  - Ultimately calls `Fetcher.sendFetches()` (line 105 in `clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java`)

**2. Fetch Request Building**
- `Fetcher.sendFetches()` (line 105):
  - Calls `prepareFetchRequests()` which groups subscribed partitions by broker leader
  - Returns Map<Node, FetchSessionHandler.FetchRequestData> with each broker's partitions
  - Calls `sendFetchesInternal()` (line 107) for each fetch request

- `sendFetchesInternal()` (line 184):
  - For each broker/FetchRequestData pair:
    - Creates `FetchRequest.Builder` via `createFetchRequest()` (line 192)
    - Sends request via `client.send()` (line 193)
    - Registers listener callbacks:
      - `handleFetchSuccess()` on success (line 111)
      - `handleFetchFailure()` on failure (line 116)

**3. Fetch Request Details**
- FetchRequest includes:
  - Replica ID (consumer uses replica ID -1)
  - For each partition:
    - Fetch offset (where consumer left off)
    - Max bytes to return
    - Current leader epoch (for fencing detection)
  - Isolation level (read_committed or read_uncommitted)
  - Min bytes and max wait time (for batching at broker)

**4. Broker-Side Fetch Processing**
- `Partition.fetchRecords()` (line 1414 in `core/src/main/scala/kafka/cluster/Partition.scala`):
  - Verifies consumer is authorized to read from partition
  - Calls `readFromLocalLog()` which calls `readRecords()` (line 1423-1431)
  - Returns `LogReadInfo` containing:
    - MemoryRecords: serialized messages from log
    - High water mark or last stable offset (depending on isolation level)

**5. Response and Deserialization**
- `handleFetchSuccess()` in Fetcher:
  - Parses FetchResponse for each partition
  - Extracts MemoryRecords containing RecordBatches
  - Calls `FetchCollector.collectFetch()` (line 145)

- `FetchCollector.collectFetch()`:
  - For each RecordBatch in MemoryRecords:
    - Deserializes each Record:
      - Key deserialization via `keyDeserializerPlugin.get().deserialize()`
      - Value deserialization via `valueDeserializerPlugin.get().deserialize()`
    - Creates `ConsumerRecord` with:
      - Topic, partition, offset
      - Timestamp (from batch or message)
      - Deserialized key and value
      - Headers
      - Leader epoch
  - Buffers records in consumer's fetch buffer
  - Maintains high water mark for each partition

**6. Record Delivery to Application**
- `KafkaConsumer.poll()` returns `ConsumerRecords<K, V>` containing:
  - Map of TopicPartition to ConsumerRecord lists
  - Application iterates over records
  - Application can call `commitSync()` or `commitAsync()` to commit offsets

**7. Offset Commits**
- Offset commits can occur:
  - Explicitly via `commitSync(offsets)` / `commitAsync(offsets, callback)`
  - Implicitly via `enable.auto.commit=true` based on `auto.commit.interval.ms`
  - As part of consumer group rebalancing
- Offset is sent to group coordinator broker and stored in `__consumer_offsets` topic
- Next `poll()` call fetches from committed offset, achieving exactly-once message delivery with retries

## Q4: End-to-End Transformation Points

### Transformation Point Sequence

**1. User Object → Serialized Bytes (Producer)**
- **Location**: `KafkaProducer.doSend()`, lines 999 and 1007
- **File**: `clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java`
- **Operation**:
  - Key: `keySerializerPlugin.get().serialize(record.topic(), record.headers(), record.key())`
  - Value: `valueSerializerPlugin.get().serialize(record.topic(), record.headers(), record.value())`
- **Change**: Object instances (String, byte[], Avro, JSON, etc.) converted to byte arrays
- **Purpose**: Network-safe binary representation

**2. Serialized Bytes → RecordBatch Framing (Producer Batching)**
- **Location**: `RecordAccumulator.appendNewBatch()`, line 393
- **File**: `clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java`
- **Operation**:
  - Creates `MemoryRecordsBuilder` wrapping a ByteBuffer
  - Appends serialized records via `ProducerBatch.tryAppend()`
  - Applies compression (gzip, snappy, lz4, zstd) if configured
- **Change**: Individual serialized messages wrapped in RecordBatch format:
  - Batch header (magic version, attributes, CRC, timestamps)
  - Compressed payload (if configured)
  - Per-record offsets (relative offsets within batch)
- **Purpose**: Efficient transmission, compression, deduplication detection

**3. Batch Framing → Network Serialization (Sender)**
- **Location**: `Sender.sendProduceRequest()`, lines 897-904
- **File**: `clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java`
- **Operation**:
  - MemoryRecords (from batch) included directly in ProduceRequestData
  - ProduceRequest wire format encodes RequestHeader + ProduceRequestData
- **Change**: RecordBatches embedded in ProduceRequest protocol format with:
  - RequestHeader (API key, version, correlation ID, client ID)
  - Timeout, acks, transactional ID
  - Topic-partition-records list
- **Purpose**: Protocol-compliant transmission to broker

**4. Network Deserialization → Log Append (Broker)**
- **Location**: `ReplicaManager.appendToLocalLog()`, line 1408
- **File**: `core/src/main/scala/kafka/server/ReplicaManager.scala`
- **Operation**:
  - ProduceRequest deserialized into Map[TopicIdPartition, MemoryRecords]
  - Calls `Partition.appendRecordsToLeader()`
  - Calls `UnifiedLog.appendAsLeader()` to write to persistent log
- **Change**: Protocol format → ByteBuffer → Disk file (memory-mapped)
- **Purpose**: Persistent storage with sequential writes

**5. Log Bytes → RecordBatch Format (Fetcher)**
- **Location**: `Partition.fetchRecords()` / `readRecords()`, lines 1414-1431
- **File**: `core/src/main/scala/kafka/cluster/Partition.scala`
- **Operation**:
  - Reads MemoryRecords from disk by offset range
  - Decompresses if batch is compressed
  - Returns MemoryRecords in FetchResponse
- **Change**: Disk bytes → Decompressed RecordBatches (if needed)
- **Purpose**: Decompression for consumer access

**6. RecordBatch → Deserialized Objects (Consumer)**
- **Location**: `FetchCollector.collectFetch()` / message deserialization
- **File**: `clients/src/main/java/org/apache/kafka/clients/consumer/internals/FetchCollector.java`
- **Operation**:
  - Iterates RecordBatch → Record
  - Deserializes key via `keyDeserializer.deserialize()`
  - Deserializes value via `valueDeserializer.deserialize()`
  - Wraps in `ConsumerRecord`
- **Change**: Byte arrays → Objects (String, byte[], Avro, JSON, etc.)
- **Purpose**: Application-usable format

### Summary Table

| Step | Component | Input | Output | Transformation |
|------|-----------|-------|--------|-----------------|
| 1 | KafkaProducer | ProducerRecord<K,V> | byte[], byte[] | Serialization |
| 2 | RecordAccumulator | byte[], byte[] | MemoryRecords (RecordBatch) | Batching + Compression |
| 3 | Sender | MemoryRecords | ProduceRequest wire format | Request Encoding |
| 4 | Broker Network | Request bytes | Map[TP, MemoryRecords] | Request Decoding |
| 5 | UnifiedLog | MemoryRecords | Disk bytes (log segment) | Persistence |
| 6 | Partition | Disk bytes (range) | MemoryRecords | Read from Storage |
| 7 | FetchCollector | MemoryRecords (RecordBatch) | List<ConsumerRecord> | Deserialization |

## Evidence

### Producer-Side Files
- `clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java` (lines 941-1075)
  - `send()` method: entry point
  - `doSend()` method: orchestrates serialization, partitioning, accumulation
- `clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java` (lines 275-400)
  - `append()` method: batching logic
  - `appendNewBatch()` method: batch creation
- `clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java` (lines 236-916)
  - `run()` method: sender thread loop
  - `sendProducerData()` method: batch readiness and draining
  - `sendProduceRequest()` method: request building and sending

### Broker-Side Files
- `core/src/main/scala/kafka/server/ReplicaManager.scala` (lines 627-1447)
  - `appendRecords()` method: entry point for produce requests
  - `appendRecordsToLeader()` method: local append orchestration
  - `appendToLocalLog()` method: per-partition append
- `core/src/main/scala/kafka/cluster/Partition.scala` (lines 1361-1450)
  - `appendRecordsToLeader()` method: partition-level append logic
  - `fetchRecords()` method: log read for consumers
- `storage/src/main/java/org/apache/kafka/storage/log/UnifiedLog.java`
  - `appendAsLeader()` method: actual log write to disk

### Consumer-Side Files
- `clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java` (lines 893-896)
  - `poll()` method: entry point
- `clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java` (lines 105-212)
  - `sendFetches()` method: fetch request preparation and sending
  - `sendFetchesInternal()` method: request building and callback registration
  - `handleFetchSuccess()` method: response processing
- `clients/src/main/java/org/apache/kafka/clients/consumer/internals/FetchCollector.java`
  - `collectFetch()` method: deserialization and record delivery

### Replication Files
- `core/src/main/scala/kafka/server/ReplicaFetcherThread.scala` (lines 86-125)
  - `processPartitionData()` method: follower fetch response handling
  - `Partition.appendRecordsToFollowerOrFutureReplica()` method: follower log append

### Key Classes and Methods
- **RecordBatch**: `org.apache.kafka.common.record.RecordBatch` - wire format for batched records
- **MemoryRecords**: `org.apache.kafka.common.record.MemoryRecords` - in-memory representation
- **ProduceRequest**: `org.apache.kafka.common.requests.ProduceRequest` - producer request protocol
- **FetchRequest**: `org.apache.kafka.common.requests.FetchRequest` - consumer fetch protocol
- **LogAppendInfo**: `org.apache.kafka.server.log.LogAppendInfo` - metadata about appended records
