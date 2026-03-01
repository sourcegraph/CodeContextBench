# Kafka Message Lifecycle

## Q1: Producer-Side Batching and Transmission

When a producer calls `KafkaProducer.send(record)`, the message travels through the following stages:

### 1. Entry Point and Serialization
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java`
- **Method**: `send(ProducerRecord<K, V> record, Callback callback)` (line 941)
  - Calls `doSend(interceptedRecord, callback)` (line 944)

### 2. Serialization and Partition Assignment
- **Method**: `doSend(ProducerRecord<K, V> record, Callback callback)` (line 974)
  - Line 999: Serializes key using `keySerializerPlugin.get().serialize(record.topic(), record.headers(), record.key())`
  - Line 1007: Serializes value using `valueSerializerPlugin.get().serialize(record.topic(), record.headers(), record.value())`
  - Line 1017: Assigns partition via `partition(record, serializedKey, serializedValue, cluster)`
  - Line 1029: **Appends to RecordAccumulator**: `accumulator.append(record.topic(), partition, timestamp, serializedKey, serializedValue, headers, appendCallbacks, remainingWaitMs, nowMs, cluster)`
  - Line 1043: Wakes up the Sender thread if batch is full or new batch created

### 3. RecordAccumulator - Batching Logic
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java`
- **Method**: `append(String topic, int partition, long timestamp, byte[] key, byte[] value, Header[] headers, AppendCallbacks callbacks, long maxTimeToBlock, long nowMs, Cluster cluster)` (line 275)
  - Maintains per-partition deques (line 313): `Deque<ProducerBatch> dq = topicInfo.batches.computeIfAbsent(effectivePartition, k -> new ArrayDeque<>())`
  - **Tries to append to existing batch** (line 319): `tryAppend(timestamp, key, value, headers, callbacks, dq, nowMs)`
  - If no batch exists or batch is full, **allocates new buffer** (line 333): `buffer = free.allocate(size, maxTimeToBlock)`
  - **Creates new ProducerBatch** (line 345): `appendNewBatch(topic, effectivePartition, dq, timestamp, key, value, headers, callbacks, buffer, nowMs)`
  - Returns `RecordAppendResult` containing the future and flags for batch fullness

### 4. Sender Thread - Network Transmission
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java`
- **Main Loop**: `run()` (line 236) → `runOnce()` (line 305)

- **Send Logic**: `sendProducerData(long now)` (line 357)
  - Line 360: Gets ready batches: `this.accumulator.ready(metadataSnapshot, now)`
  - Line 395: **Drains batches from accumulator**: `accumulator.drain(metadataSnapshot, result.readyNodes, this.maxRequestSize, now)`
  - Line 396: Adds to in-flight batches: `addToInflightBatches(batches)`
  - Line 442: **Sends produce requests**: `sendProduceRequests(batches, now)`

- **Produce Request Construction**: `sendProduceRequest(long now, int destination, short acks, int timeout, List<ProducerBatch> batches)` (line 864)
  - Line 874: Gets `MemoryRecords records = batch.records()` (ProducerBatch contains serialized records already in RecordBatch format)
  - Line 897-904: Creates `ProduceRequest` with the MemoryRecords

### Key Batching Triggers
- **Batch is full** (reached `batch.size`)
- **Linger timeout expires** (configured by `linger.ms`)
- **Manual flush** or **producer.flush()**
- **Producer closed** (sends remaining records)

---

## Q2: Broker-Side Append and Replication

When a produce request arrives at the broker, it's processed through multiple layers:

### 1. Request Routing - KafkaApis
- **File**: `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala`
- **Method**: `handleProduceRequest(request: RequestChannel.Request, requestLocal: RequestLocal)` (line 388)
  - Line 389: Extracts `ProduceRequest` from request body
  - Line 406-442: Validates authorization and request content
  - Line 429: Casts records as `MemoryRecords` (serialized RecordBatch format from network)
  - Line 435-437: Validates records: `ProduceRequest.validateRecords(request.header.apiVersion, memoryRecords)`
  - Line 535-544: **Delegates to ReplicaManager**: `replicaManager.handleProduceAppend(...)`

### 2. ReplicaManager - Produce Append
- **File**: `/workspace/core/src/main/scala/kafka/server/ReplicaManager.scala`
- **Method**: `handleProduceAppend(timeout: Long, requiredAcks: Short, internalTopicsAllowed: Boolean, ...)` (line 731)
  - Performs transactional verification (if transactional)
  - Line 637: **Appends to local log**: `appendToLocalLog(internalTopicsAllowed, origin, entriesPerPartition, requiredAcks, requestLocal, verificationGuards)`
  - Line 704-711: **Waits for replication if acks=-1**: `maybeAddDelayedProduce(requiredAcks, timeout, entriesPerPartition, localProduceResults, produceStatus, responseCallback)`

- **Local Log Append**: `appendToLocalLog(...)` (line 1370)
  - Line 1407: Gets partition: `partition = getPartitionOrException(topicIdPartition)`
  - Line 1408: **Calls partition's append method**: `partition.appendRecordsToLeader(records, origin, requiredAcks, requestLocal, verificationGuard)`

### 3. Partition - Leader Append
- **File**: `/workspace/core/src/main/scala/kafka/cluster/Partition.scala`
- **Method**: `appendRecordsToLeader(records: MemoryRecords, origin: AppendOrigin, requiredAcks: Int, ...)` (line 1361)
  - Line 1363-1375: Acquires read lock on leaderIsrUpdateLock
  - Line 1376: **Appends to leader log**: `leaderLog.appendAsLeader(records, this.leaderEpoch, origin, requestLocal, verificationGuard)`

### 4. UnifiedLog (Log) - Message Persistence
- **File**: `/workspace/storage/src/main/java/org/apache/kafka/storage/internals/log/UnifiedLog.java`
- **Method**: `appendAsLeader(MemoryRecords records, int leaderEpoch, AppendOrigin origin, RequestLocal requestLocal, VerificationGuard verificationGuard)` (line 1024)
  - Line 1030: Calls internal `append(...)` method

- **Core Append Logic**: `append(MemoryRecords records, AppendOrigin origin, boolean validateAndAssignOffsets, ...)` (line 1081)

  **Phase 1: Analyze and Validate** (line 1093)
  - `analyzeAndValidateRecords(records, origin, ignoreRecordSize, ...)` - Validates message format, size, offsets

  **Phase 2: Synchronization and Offset Assignment** (line 1102-1152)
  - If `validateAndAssignOffsets=true`:
    - Line 1110: Gets next offset: `localLog.logEndOffset()`
    - Line 1113-1125: Creates `LogValidator` with compression settings and target magic value
    - Line 1126: **Assigns offsets and timestamps**: `validator.validateMessagesAndAssignOffsets(...)`

  **Phase 3: Epoch Cache Update** (line 1178-1190)
  - Updates leader epoch cache for each batch

  **Phase 4: Segment Management** (line 1199)
  - `maybeRoll(validRecords.sizeInBytes(), appendInfo)` - Rolls to new segment if current is full

  **Phase 5: Producer State Management** (line 1208-1209)
  - `analyzeAndValidateProducerState(logOffsetMetadata, validRecords, origin, verificationGuard)` - Validates idempotent/transactional state

  **Phase 6: Write to Disk** (line 1224)
  - **`localLog.append(appendInfo.lastOffset(), validRecords)`** - **Writes to segment file**
  - Line 1225: Updates high watermark
  - Line 1228: Updates producer state
  - Line 1232-1235: Updates transaction index for completed transactions
  - Line 1248: Flushes if unflushed messages >= flush interval

### Replication Process
- **ReplicaFetcherThread** fetches committed batches from leader via replica fetch requests
- Each follower replica receives batches and calls `appendAsFollower()` on its log
- **High Water Mark (HWM)** advances only when acks=-1 and required replicas acknowledge

---

## Q3: Consumer-Side Fetch and Delivery

When a consumer calls `poll()`, messages flow through the following stages:

### 1. Consumer Poll Entry Point
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java`
- **Method**: `poll(final Duration timeout)` (line 894)
  - Delegates to consumer implementation

### 2. Classic Consumer Poll
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/ClassicKafkaConsumer.java`
- **Method**: `poll(final Duration timeout)` (line 624)
  - Line 625: Converts to timer and calls internal `poll(Timer)`
- **Method**: `poll(final Timer timer)` (line 631)
  - Line 646: **Collects available fetches**: `pollForFetches(timer)`
  - Line 663: Applies interceptors and creates `ConsumerRecords`
  - Returns `ConsumerRecords<K, V>` to application

### 3. Fetch Request Management
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java`
- **Extends**: `AbstractFetch` which manages fetch request building
- **Method**: `sendFetches()` - Builds and sends FetchRequests to brokers
  - Creates `FetchRequest.Builder` with partition offsets and max bytes
  - Line 193: Sends via `client.send(fetchTarget, request)` (network send)

### 4. Fetch Response Processing
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/FetchCollector.java`
- **Method**: `collectFetch(final FetchBuffer fetchBuffer)` (line 92)
  - Line 99-109: Gets `CompletedFetch` from buffer
  - Line 108-109: Initializes fetch if needed: `initialize(completedFetch)` - Parses FetchResponse
  - Line 133: **Extracts records**: `fetchRecords(nextInLineFetch, recordsRemaining)`

- **Method**: `fetchRecords(final CompletedFetch nextInLineFetch, int maxRecords)` (line 150)
  - Line 170: **Calls fetchRecords on CompletedFetch**: `nextInLineFetch.fetchRecords(fetchConfig, deserializers, ...)`

### 5. Record Deserialization
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/CompletedFetch.java`
- **Method**: `fetchRecords(...)` - Deserializes records
  - Iterates through `MemoryRecords` batches
  - For each `Record`:
    - Extracts key bytes and value bytes
    - **Calls key deserializer** on key bytes → `K` object
    - **Calls value deserializer** on value bytes → `V` object
    - Creates `ConsumerRecord<K, V>` with:
      - Topic, partition, offset, timestamp, key, value, headers, leaderEpoch

### 6. Offset Management
- **Before returning records**: Consumer can configure offset commit strategy
  - **Auto-commit**: Periodically commits offsets via `CommitRequestManager`
  - **Manual commit**: User calls `commitSync()` or `commitAsync()`
  - **No-commit**: Consumer reads from beginning/end on restart

- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/CommitRequestManager.scala`
- Sends `OffsetCommitRequest` to group coordinator

---

## Q4: End-to-End Transformation Points

Messages undergo the following transformations as they flow through Kafka:

### **T1: Serialization (Producer-Side)**
- **Location**: `KafkaProducer.doSend()` (lines 999, 1007)
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java`
- **What changes**: Application objects (K, V) → byte arrays
- **Process**:
  ```
  K (application object) → keySerializer → byte[] (serialized key)
  V (application object) → valueSerializer → byte[] (serialized value)
  ```
- **Configured by**: `key.serializer`, `value.serializer` properties

### **T2: RecordBatch Framing (Producer-Side)**
- **Location**: `RecordAccumulator.tryAppend()` and batch construction
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/ProducerBatch.java`
- **What changes**: Individual serialized records → RecordBatch protocol frame
- **Process**:
  - Serialized bytes wrapped in `RecordBatch` structure with:
    - `baseOffset` (offset in partition)
    - `baseTimestamp` (timestamp)
    - `magic` (record format version: typically 2)
    - `compression` (compression codec: none, gzip, snappy, lz4, zstd)
    - `producerId` (for idempotent/transactional producers)
    - `producerEpoch`
    - `isTransactional` flag
- **Protocol ref**: Kafka wire protocol RecordBatch format (RecordBatch.CURRENT_MAGIC_VALUE)

### **T3: Network Transmission (Producer → Broker)**
- **Location**: `Sender.sendProduceRequest()`
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java`
- **What changes**: RecordBatch objects → ProduceRequest protocol message → network bytes
- **Process**:
  ```
  RecordBatch → ProduceRequest (with compression, acks, timeout)
              → ProduceRequest serialized to bytes
              → network transmission to broker
  ```
- **Data includes**:
  - Topic name/ID
  - Partition number
  - Serialized/compressed record batches
  - Required acks (-1, 0, 1)
  - Request timeout

### **T4: Broker-Side Deserialization and Validation**
- **Location**: `KafkaApis.handleProduceRequest()` → `ReplicaManager.appendToLocalLog()`
- **File**: `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala`
- **What changes**: ProduceRequest bytes → MemoryRecords (uncompressed for processing)
- **Process**:
  - Network bytes deserialized into ProduceRequest
  - `MemoryRecords` extracted as serialized batch format
  - `LogValidator.validateMessagesAndAssignOffsets()` decompresses if needed
  - If producer used compression, decompression occurs here

### **T5: Offset Assignment and Recompression (Broker-Side)**
- **Location**: `UnifiedLog.append()` with offset validation phase
- **File**: `/workspace/storage/src/main/java/org/apache/kafka/storage/internals/log/UnifiedLog.java`
- **What changes**: Messages with producer offsets → messages with broker-assigned offsets; compression may change
- **Process**:
  - LogValidator re-validates each message:
    - Checks CRC (if present)
    - Validates key/value sizes
    - Assigns partition leader epoch
    - Compresses to configured broker compression (if different from source)
  - Result: `validRecords` ready for disk persistence
  - Line 1224: `localLog.append()` writes to segment

### **T6: Disk Persistence (LogSegment)**
- **Location**: `LocalLog.append()` (in LogSegment)
- **File**: `/workspace/storage/src/main/java/org/apache/kafka/storage/internals/log/LogSegment.java`
- **What changes**: In-memory RecordBatch → file-backed mmap'd buffer → disk
- **Process**:
  - RecordBatch written to active LogSegment file (e.g., `000000000000000000.log`)
  - Index files updated: `.index` (offset → file position), `.timeindex` (timestamp → offset)
  - Data persisted based on `log.flush.interval.messages` or `log.flush.interval.ms`
  - OS eventually flushes to disk (fsync)

### **T7: Replication (Broker → Replica Brokers)**
- **Location**: `ReplicaFetcherThread` → follower `appendAsFollower()`
- **File**: `/workspace/core/src/main/scala/kafka/server/ReplicaFetcherThread.scala`
- **What changes**: Messages remain in RecordBatch format; transmitted via replica fetch protocol
- **Process**:
  - ReplicaFetcherThread reads from leader's log
  - Sends replica fetch request to leader
  - Leader responds with batches (same format as on disk)
  - Follower appends via `appendAsFollower()` (no offset reassignment)
  - Follower's log synchronized with leader

### **T8: Network Transmission (Broker → Consumer)**
- **Location**: `KafkaApis.handleFetchRequest()` → FetchResponse
- **File**: `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala`
- **What changes**: RecordBatch on disk → FetchResponse → network bytes
- **Process**:
  - Broker reads from LogSegment (may decompress from disk format)
  - Creates FetchResponse with:
    - Topic, partition, high watermark, last stable offset
    - Records in compact binary format (RecordBatch)
  - Response serialized and sent over network

### **T9: Consumer-Side Deserialization**
- **Location**: `CompletedFetch.fetchRecords()` in FetchCollector
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/CompletedFetch.java`
- **What changes**: RecordBatch bytes → ConsumerRecord<K, V> objects
- **Process**:
  - FetchResponse bytes deserialized into MemoryRecords
  - Each RecordBatch decompressed (if compressed)
  - Each Record extracted:
    - Key bytes → keyDeserializer → K object
    - Value bytes → valueDeserializer → V object
  - ConsumerRecord<K, V> created with all metadata:
    - topic, partition, offset, timestamp, key, value, headers, leaderEpoch

### **T10: Consumer Application Delivery**
- **Location**: `ClassicKafkaConsumer.poll()` → `onConsume()` interceptors
- **File**: `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/ClassicKafkaConsumer.java`
- **What changes**: ConsumerRecords → InterceptedConsumerRecords → application objects
- **Process**:
  - ConsumerRecords passed through `ConsumerInterceptor.onConsume()` hooks
  - Records returned to application code
  - Application code accesses K and V objects directly

---

## Summary of Transformation Points (Ordered)

| Order | Transformation | Producer/Broker/Consumer | File Location | Key Method |
|-------|---|---|---|---|
| T1 | Serialization (Objects → bytes) | Producer | KafkaProducer.java | doSend() line 999, 1007 |
| T2 | RecordBatch Framing | Producer | ProducerBatch.java | (batch construction) |
| T3 | Network TX (Batch → ProduceRequest) | Producer | Sender.java | sendProduceRequest() line 864 |
| T4 | Broker Request Deserialization | Broker | KafkaApis.scala | handleProduceRequest() line 388 |
| T5 | Offset Assignment & Recompression | Broker | UnifiedLog.java | append() line 1081 |
| T6 | Disk Persistence (mmap) | Broker | LogSegment.java | append() |
| T7 | Replica Fetch & Append | Broker | ReplicaFetcherThread.scala | appendAsFollower() |
| T8 | Network TX (Batch → FetchResponse) | Broker | KafkaApis.scala | handleFetchRequest() line 555 |
| T9 | Consumer Deserialization (bytes → Objects) | Consumer | CompletedFetch.java | fetchRecords() |
| T10 | Application Delivery | Consumer | ClassicKafkaConsumer.java | poll() line 631 |

---

## Evidence

### Producer Files
- `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java` - Entry point, serialization (lines 941-1046)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java` - Batching (lines 275-358)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java` - Network transmission (lines 236-444)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/producer/internals/ProducerBatch.java` - Batch structure

### Broker Files
- `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala` - Request handling (lines 388-550, 555)
- `/workspace/core/src/main/scala/kafka/server/ReplicaManager.scala` - Replication coordination (lines 627-650, 731-791, 1370-1410)
- `/workspace/core/src/main/scala/kafka/cluster/Partition.scala` - Partition-level append (lines 1361-1388)
- `/workspace/storage/src/main/java/org/apache/kafka/storage/internals/log/UnifiedLog.java` - Log persistence (lines 1024-1254)
- `/workspace/storage/src/main/java/org/apache/kafka/storage/internals/log/LogSegment.java` - Segment-level storage

### Consumer Files
- `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java` - Consumer entry (line 894)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/ClassicKafkaConsumer.java` - Poll logic (lines 624-672)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java` - Fetch management (lines 145-147)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/FetchCollector.java` - Collection (lines 92-148)
- `/workspace/clients/src/main/java/org/apache/kafka/clients/consumer/internals/CompletedFetch.java` - Deserialization

### Key Protocol/Format Files
- `/workspace/common/src/main/java/org/apache/kafka/common/record/RecordBatch.java` - RecordBatch protocol format
- `/workspace/common/src/main/java/org/apache/kafka/common/record/MemoryRecords.java` - In-memory batch container
