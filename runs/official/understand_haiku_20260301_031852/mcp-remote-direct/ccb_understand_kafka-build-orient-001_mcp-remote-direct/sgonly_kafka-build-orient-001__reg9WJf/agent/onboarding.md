# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Apache Kafka uses **Gradle** as its build system. The main build configuration is in `/build.gradle` at the repository root, with additional build properties in `gradle.properties` and shared configurations in `gradle/` directory.

Key build features:
- **Plugins**: Java-library, Jacoco (code coverage), Spotbugs, Scala plugin, Shadow plugin for fat JARs
- **Supported Java versions**: Minimum Java 8, with special handling for Java 16+ using `--add-opens` flags
- **Test execution**: Configurable with `maxParallelForks` property (defaults to number of available processors)
- **Modular structure**: Gradle subprojects for different modules (core, clients, streams, etc.)

### Broker Startup - Main Entry Point

**Primary Entry Point**: `core/src/main/scala/kafka/Kafka.scala`
- `main()` function: Parses command-line arguments, loads `server.properties` file
- Supports override properties via `--override key=value` pattern
- Handles ZooKeeper mode vs KRaft mode based on configuration

### Key Classes in Broker Initialization

1. **KafkaConfig** (`core/src/main/scala/kafka/server/KafkaConfig.scala`, line 181)
   - Extends `AbstractKafkaConfig`
   - Contains all broker configuration parameters
   - Configuration is populated from `server.properties` and command-line overrides
   - Manages dynamic configuration through `DynamicBrokerConfig`

2. **KafkaServer** (`core/src/main/scala/kafka/server/KafkaServer.scala`, line 112)
   - Main broker class representing lifecycle of a single Kafka broker
   - Handles all startup and shutdown operations
   - Key method: `startup()` (line 216)

3. **KafkaRaftServer** (for KRaft mode)
   - Alternative to KafkaServer when running in KRaft mode (without ZooKeeper)

### Broker Startup Sequence

The `KafkaServer.startup()` method (line 216-400+ in KafkaServer.scala) performs these critical steps:

1. **Initialize ZooKeeper Client** (line 231)
   - Connects to ZooKeeper cluster
   - Sets up configuration repository for dynamic config management

2. **Get/Generate Cluster ID** (line 235)
   - Retrieves existing cluster ID or generates new one from ZooKeeper

3. **Load Metadata** (line 239-313)
   - Loads meta.properties from log directories
   - Initializes MetaPropertiesEnsemble for consistency verification

4. **Initialize Core Components** (line 270-400+):
   - **KafkaScheduler**: Thread pool for background tasks (line 271)
   - **Metrics**: Initialize JMX and other metrics reporters (line 275-277)
   - **LogManager**: Manages topic logs and partitions (line 317)
   - **SocketServer**: Network communication layer (line 383)
   - **ReplicaManager**: Manages replica leadership and ISR
   - **KafkaController**: Cluster coordinator (for controller broker)
   - **GroupCoordinator**: Consumer group coordination
   - **TransactionCoordinator**: Transaction management
   - **AdminManager**: Administrative operations handler

5. **Start Request Handlers** (line 401+)
   - Data plane request handler pool
   - Control plane request handler pool
   - These process incoming client and inter-broker requests

### Startup Initialization Pattern

```scala
// From Kafka.scala main()
val server = buildServer(serverProps)  // Creates KafkaServer or KafkaRaftServer
server.startup()                        // Starts all components
server.awaitShutdown()                 // Blocks until shutdown signal
```

---

## 2. Module Structure

Apache Kafka is organized into multiple independent modules, each with a specific responsibility. The codebase follows a modular design to separate concerns and allow independent development and testing.

### Core Modules

#### **core/** - Core Broker and Server Logic
- **Responsibilities**: Broker startup, request handling, coordination, replication, log management, ZooKeeper interaction
- **Key directories**:
  - `core/src/main/scala/kafka/server/` - Broker server classes (KafkaServer, KafkaApis, LogManager, etc.)
  - `core/src/main/scala/kafka/controller/` - Controller logic
  - `core/src/main/scala/kafka/log/` - Log segment management, log recovery
  - `core/src/main/scala/kafka/network/` - Network layer (SocketServer, RequestChannel)
  - `core/src/main/scala/kafka/zk/` - ZooKeeper client and operations
  - `core/src/test/` - Comprehensive unit and integration tests

#### **server/** - Server Configuration and Utilities
- **Responsibilities**: Broker-specific configuration, security, metrics, fault handling
- **Key directories**:
  - `server/src/main/java/org/apache/kafka/server/config/` - Configuration classes
  - `server/src/main/java/org/apache/kafka/server/authorizer/` - Authorization framework
  - `server/src/main/java/org/apache/kafka/server/metrics/` - Metrics infrastructure

#### **clients/** - Client Libraries
- **Responsibilities**: Producer and Consumer APIs, Protocol handling
- **Key components**:
  - `clients/src/main/java/org/apache/kafka/clients/producer/` - Producer implementation
  - `clients/src/main/java/org/apache/kafka/clients/consumer/` - Consumer implementation
  - `clients/src/main/java/org/apache/kafka/common/` - Common classes (TopicPartition, Node, errors)

#### **metadata/** - Metadata Management
- **Responsibilities**: Metadata image/snapshot, metadata serialization, replication control
- **Key directories**:
  - `metadata/src/main/java/org/apache/kafka/metadata/` - Metadata classes
  - `metadata/src/main/java/org/apache/kafka/controller/` - KRaft controller implementation
  - `metadata/src/main/java/org/apache/kafka/image/` - Metadata image representation

#### **group-coordinator/** - Consumer Group Coordination
- **Responsibilities**: Consumer group management, rebalancing, offset tracking
- **Key files**: Group coordinator state machine, member assignment logic

#### **transaction-coordinator/** - Transaction Management
- **Responsibilities**: Transaction coordination, transaction log management
- **Key files**: Transaction state manager, transaction marker handling

#### **storage/** - Storage Abstraction
- **Responsibilities**: Log segment storage interface, storage layer abstraction
- **Key files**: Remote storage support, directory storage interface

#### **raft/** - RAFT Consensus
- **Responsibilities**: RAFT consensus implementation for KRaft controller
- **Key files**: RAFT log, quorum configuration, snapshot handling

#### **streams/** - Kafka Streams
- **Responsibilities**: Stream processing library, DSL, state stores, topology
- **Key directories**: `streams/src/main/java/org/apache/kafka/streams/`

#### **connect/** - Kafka Connect
- **Responsibilities**: Distributed data integration framework
- **Key directories**: `connect/api/`, `connect/runtime/`, `connect/sink-source-utils/`

#### **bin/** - Scripts and Tools
- **Responsibilities**: Executable shell scripts for broker startup and admin tools
- **Key scripts**:
  - `bin/kafka-server-start.sh` - Broker startup script
  - `bin/kafka-topics.sh` - Topic management tool
  - `bin/kafka-console-producer.sh` - Producer tool
  - `bin/kafka-console-consumer.sh` - Consumer tool

#### **config/** - Default Configuration Files
- **Responsibilities**: Default property files for broker, client, and tools
- **Key files**:
  - `config/server.properties` - Default broker configuration
  - `config/producer.properties` - Default producer configuration
  - `config/consumer.properties` - Default consumer configuration

#### **tests/** - System and Performance Tests
- **Responsibilities**: End-to-end tests, system tests, performance tests
- **Key directories**: Integration tests, failure scenario tests

### Architectural Layers

1. **Network Layer** (`core/src/main/scala/kafka/network/`)
   - SocketServer: Manages socket connections (data plane and control plane)
   - RequestChannel: Routes requests to appropriate handlers
   - Supports multiple network protocols (PLAINTEXT, SSL/TLS, SASL)

2. **Request Processing Layer** (`core/src/main/scala/kafka/server/`)
   - KafkaApis: Processes client requests (fetch, produce, etc.)
   - ControllerApis: Processes controller-specific requests
   - KafkaRequestHandlerPool: Thread pool for request processing

3. **Storage Layer** (`core/src/main/scala/kafka/log/`)
   - LogManager: Manages topic log partitions
   - Log: Single topic partition log
   - LogSegment: Individual log files
   - RecoveryPoint: Last cleanly written offset

4. **Replication Layer** (`core/src/main/scala/kafka/server/`)
   - ReplicaManager: Manages replica leadership
   - ISR (In-Sync Replicas) management
   - Replica fetcher threads

5. **Coordination Layer** (group-coordinator/, transaction-coordinator/)
   - Group coordination for consumer groups
   - Transaction state management
   - Offset management

### Dependency Flow
```
clients/ <---> network layer <---> core/ <---> storage/
                                    ^
                                    |
metadata/ <---> KRaft controller
                    ^
                    |
                    +---- raft/
```

---

## 3. Topic Creation Flow

Topic creation in Kafka is an asynchronous, multi-stage process that involves client requests, request handling, controller coordination, and replica assignment. Here's the complete end-to-end flow:

### Stage 1: Client Request

**Client Code** (via AdminClient or kafka-topics.sh tool)
```java
// From clients/src/main/java/org/apache/kafka/clients/admin/KafkaAdminClient.java
CreateTopicsRequest.Builder requestBuilder = new CreateTopicsRequest.Builder(
    new CreateTopicsRequestData()
        .setTopics(creatableTopics)
        .setTimeoutMs(timeoutMs)
);
```

### Stage 2: Broker Request Reception

**File**: `core/src/main/scala/kafka/server/KafkaApis.scala`, line 2002
- **Method**: `handleCreateTopicsRequest(request: RequestChannel.Request)`
- **Key Steps**:
  1. Validates that the receiving broker is the controller (line 2017)
  2. Performs authorization checks via `authHelper` (line 2027-2051)
  3. Filters topics based on permissions (authorized vs unauthorized)
  4. Prevents creation of internal topics like `__cluster_metadata` (line 2055-2057)
  5. Detects duplicate topic entries (line 2058-2061)

### Stage 3: Admin Manager Processing

**File**: `core/src/main/scala/kafka/server/ZkAdminManager.scala`, line 159
- **Method**: `createTopics(timeout, validateOnly, toCreate, includeConfigsAndMetadata, controllerMutationQuota, responseCallback)`
- **Key Steps**:

#### Step 3.1: Topic Validation (line 169-219)
For each topic in the request:
1. **Check if topic exists** (line 170-171)
   - Consults `metadataCache` to prevent duplicate topic names
   - Throws `TopicExistsException` if found

2. **Validate configs** (line 173-175)
   - Checks that no config values are null
   - Validates config syntax and allowed values

3. **Resolve partition assignment** (line 177-199)
   - If both `numPartitions`/`replicationFactor` AND explicit assignments provided: error (line 177-180)
   - If `numPartitions` and `replicationFactor` provided:
     - Uses `AdminUtils.assignReplicasToBrokers()` to calculate replica assignments
   - If explicit assignments provided:
     - Validates broker IDs exist
     - Parses assignment data structure

4. **Validate with policies** (line 204-205)
   - Calls `adminZkClient.validateTopicCreate()` to verify assignments are valid
   - Calls `validateTopicCreatePolicy()` to check custom validation policies

#### Step 3.2: Topic Creation (line 214-219)
- **validateOnly=true**: Returns without creating (for validation-only requests)
- **validateOnly=false**:
  - Calls `adminZkClient.createTopicWithAssignment()`
  - Writes ZooKeeper znodes:
    - `/config/topics/{topic}` - Topic configuration
    - `/brokers/topics/{topic}` - Topic partition assignment
  - Populates topic IDs for topic-level UUID tracking

#### Step 3.3: Purgatory Management (line 239-256)
- **Immediate response** if:
  - Timeout <= 0 (no waiting)
  - `validateOnly=true`
  - Any topic had errors
- **Delayed response** otherwise:
  - Creates `DelayedCreatePartitions` waiting entry
  - Puts request into topic purgatory (waiting queue)
  - Watches for partition leader election completion

### Stage 4: Controller Metadata Updates

**ZooKeeper Watch Triggers**:
1. Controller watches `/brokers/topics/{topic}` changes (line 1621 KafkaZkClient)
2. When assignment is written, watch triggers
3. Controller processes topic creation:
   - Adds topic to `metadataCache`
   - Initiates ISR initialization on replicas
   - Publishes topic metadata to brokers

### Stage 5: Broker Replica Initialization

**Replica Manager** (`core/src/main/scala/kafka/server/ReplicaManager.scala`):
1. Receives metadata update about new topic
2. Creates new replicas based on assignment:
   - If current broker is leader: creates leader replica
   - If current broker is in ISR: creates follower replica
3. Initializes replica log segments
4. Starts ISR tracking

### Stage 6: Response to Client

**Response Path** (line 2006-2012 in KafkaApis.scala):
```scala
def sendResponseCallback(results: CreatableTopicResultCollection): Unit = {
  val responseData = new CreateTopicsResponseData()
    .setTopics(results)
  val response = new CreateTopicsResponse(responseData)
  requestHelper.sendResponseMaybeThrottleWithControllerQuota(...)
}
```

Response includes for each topic:
- Error code (NONE if success)
- Topic configuration (if client has describe permission)
- Number of partitions
- Replication factor
- Partition assignments (if requested)

### Key Classes Involved

| Class | File | Purpose |
|-------|------|---------|
| `CreateTopicsRequest` | clients/ | Client request data structure |
| `CreatableTopic` | common/message/ | Individual topic to create |
| `KafkaApis` | core/server/ | Main request handler |
| `ZkAdminManager` | core/server/ | Admin operations coordinator |
| `AdminZkClient` | core/zk/ | ZooKeeper operations |
| `KafkaZkClient` | core/zk/ | ZooKeeper client wrapper |
| `ReplicaManager` | core/server/ | Replica management |
| `MetadataCache` | core/server/ | In-memory metadata |
| `AdminUtils` | core/admin/ | Replica assignment algorithm |
| `DelayedCreatePartitions` | core/server/ | Delayed operation for partition creation completion |

### Topic Creation Example

```scala
// From ZkAdminManager.scala
val assignments = CoreUtils.replicaToBrokerAssignmentAsScala(
  AdminUtils.assignReplicasToBrokers(
    brokers.asJavaCollection,    // List of broker objects
    resolvedNumPartitions = 3,   // Number of partitions
    resolvedReplicationFactor = 2 // Replication factor
  )
)
// Result: Map[Int, Seq[Int]] = {
//   0 -> Seq(0, 1),  // Partition 0: leader on broker 0, replica on broker 1
//   1 -> Seq(1, 2),  // Partition 1: leader on broker 1, replica on broker 2
//   2 -> Seq(2, 0)   // Partition 2: leader on broker 2, replica on broker 0
// }

adminZkClient.createTopicWithAssignment(
  "my-topic",     // Topic name
  configs,        // Topic configuration properties
  assignments,    // Replica assignments
  validate = false,
  config.usesTopicId
)
```

---

## 4. Testing Framework

Apache Kafka uses a comprehensive testing strategy combining unit tests, integration tests, and system tests using multiple frameworks. Here's the complete testing architecture:

### Test Frameworks and Libraries

1. **JUnit 5 (Jupiter)** - Primary test framework
   - Location: `core/src/test/java/kafka/test/annotation/`, `core/src/test/java/kafka/test/junit/`
   - Used for: Unit tests, integration tests
   - Key annotations: `@Test`, `@BeforeEach`, `@AfterEach`, `@TestTemplate`, `@ClusterTemplate`

2. **ScalaTest** (for Scala code)
   - Used for: Scala unit tests
   - Location: `core/src/test/scala/`
   - Key features: `describe`/`it` DSL, property-based testing

3. **Mockito** - Mocking framework
   - For: Unit test mocking
   - Location: Integrated with test dependencies

4. **AssertJ** - Fluent assertions
   - For: More readable assertions
   - Alternative to JUnit assertions

### Kafka-Specific Testing Infrastructure

#### **Test Harnesses**

1. **QuorumTestHarness** (`core/src/test/scala/integration/kafka/server/QuorumTestHarness.scala`)
   - **Purpose**: Base class for tests that need a running Kafka cluster
   - **Supports**: Both ZooKeeper and KRaft modes
   - **Key methods**:
     - `createBroker()`: Instantiate broker with custom config
     - `brokers`: Access list of running brokers
     - Lifecycle: `@BeforeAll`, `@AfterAll` for cluster setup/teardown
   - **Implementations**:
     - `ZooKeeperQuorumImplementation`: Creates embedded ZooKeeper + brokers
     - `KRaftQuorumImplementation`: Creates KRaft controller + brokers

2. **KafkaServerTestHarness** (`core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala`)
   - **Purpose**: Extends QuorumTestHarness with additional helpers
   - **Key features**:
     - Default broker configuration
     - Helper methods for common test scenarios
     - Methods: `servers`, `getController()`, `createTopic()`, etc.

3. **IntegrationTestHarness** (`core/src/test/scala/integration/kafka/api/IntegrationTestHarness.scala`)
   - **Purpose**: Full cluster setup with producer/consumer clients
   - **Provides**: Producer and consumer test utilities
   - **Extends**: KafkaServerTestHarness

#### **Embedded Cluster Utilities**

1. **EmbeddedKafkaCluster** (`streams/src/test/java/org/apache/kafka/streams/integration/utils/EmbeddedKafkaCluster.java`)
   - Purpose: Embedded single-process Kafka cluster for Streams testing
   - Features: Easy broker access, automatic cleanup

2. **KafkaEmbedded** (`streams/src/test/java/org/apache/kafka/streams/integration/utils/KafkaEmbedded.java`)
   - Purpose: Wraps single Kafka broker for testing
   - Methods: `kafkaServer()` to access underlying KafkaServer

### Unit Test Patterns

```scala
// Example: Unit test for KafkaConfig
class KafkaConfigTest {
  @Test
  def testDefaultValues(): Unit = {
    val props = new Properties()
    props.put("broker.id", "0")
    val config = KafkaConfig.fromProps(props)
    assertEquals(0, config.brokerId)
  }
}
```

### Integration Test Patterns

```scala
// Example: Integration test with broker cluster
class TopicCreationTest extends IntegrationTestHarness {
  override val brokerCount = 3  // 3 broker cluster

  @Test
  def testCreateTopic(): Unit = {
    val topic = "test-topic"
    createTopic(topic, numPartitions = 3, replicationFactor = 2)

    // Use producer/consumer to verify topic exists
    val records = produceAndConsume(topic)
    assertEquals(expectedRecords.size, records.size)
  }
}
```

### JUnit 5 Test Template Annotation

Kafka provides a custom `@ClusterTemplate` annotation for parameterized cluster testing:

```java
// core/src/test/java/kafka/test/annotation/ClusterTemplate.java
@Retention(RUNTIME)
@TestTemplate
@Tag("integration")
public @interface ClusterTemplate {
  String value() default "";
}
```

**Usage**: Mark a test method with `@ClusterTemplate` to run it across different cluster configurations (ZooKeeper mode, KRaft mode, etc.)

### Test Configuration

**KafkaConfig Helpers** in `core/src/test/scala/unit/kafka/utils/TestUtils.scala`:
```scala
object TestUtils {
  def createBrokerConfig(nodeId: Int, zkConnect: String): Properties = {
    val props = new Properties()
    props.put("broker.id", nodeId.toString)
    props.put("zookeeper.connect", zkConnect)
    props.put("log.dirs", TestUtils.tempDir().getAbsolutePath)
    props
  }
}
```

### Common Test Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| **Unit Test** | Single component in isolation with mocks | KafkaConfigTest |
| **Integration Test** | Multiple components with real cluster | TopicCreationTest extends QuorumTestHarness |
| **System Test** | Full end-to-end testing via scripts | tests/kafkatest/tests/ (Python scripts) |
| **Performance Test** | Benchmark and performance analysis | jmh-benchmarks/ |

### Running Tests

```bash
# Run all tests
./gradlew test

# Run specific test class
./gradlew test --tests KafkaConfigTest

# Run integration tests
./gradlew integrationTest

# Run with custom JVM options
./gradlew test -Dtest.args="-Dlog4j.configuration=file:config/log4j-test.properties"
```

---

## 5. Configuration System

The Kafka configuration system is hierarchical and dynamically manages broker parameters across static, dynamic, and per-listener configurations. It supports validation, defaults, and dynamic updates without restarting the broker.

### Configuration Architecture

#### **1. Configuration Definition Registry**

**Primary File**: `server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java` (line 43-68)

```java
public static final ConfigDef CONFIG_DEF = Utils.mergeConfigs(Arrays.asList(
    RemoteLogManagerConfig.configDef(),
    ZkConfigs.CONFIG_DEF,
    ServerConfigs.CONFIG_DEF,          // Core broker configs
    KRaftConfigs.CONFIG_DEF,           // KRaft-specific configs
    SocketServerConfigs.CONFIG_DEF,    // Network configs
    ReplicationConfigs.CONFIG_DEF,     // Replication configs
    GroupCoordinatorConfig.GROUP_COORDINATOR_CONFIG_DEF,
    GroupCoordinatorConfig.NEW_GROUP_CONFIG_DEF,
    GroupCoordinatorConfig.OFFSET_MANAGEMENT_CONFIG_DEF,
    GroupCoordinatorConfig.CONSUMER_GROUP_CONFIG_DEF,
    CleanerConfig.CONFIG_DEF,
    LogConfig.SERVER_CONFIG_DEF,
    TransactionLogConfigs.CONFIG_DEF,
    // ... more configs
));
```

**Key Config Modules**:
- `ServerConfigs`: `broker.id`, `port`, `log.dirs`, etc.
- `ZkConfigs`: `zookeeper.connect`, `zookeeper.session.timeout.ms`, etc.
- `KRaftConfigs`: `node.id`, `controller.quorum.voters`, etc.
- `SocketServerConfigs`: `listeners`, `advertised.listeners`, etc.
- `ReplicationConfigs`: `default.replication.factor`, `min.insync.replicas`, etc.
- `LogConfig`: Log segment size, retention policies, compression, etc.
- `GroupCoordinatorConfig`: Consumer group settings
- `TransactionLogConfigs`: Transaction manager configurations

#### **2. Configuration Loading and Storage**

**KafkaConfig Class** (`core/src/main/scala/kafka/server/KafkaConfig.scala`, line 181-220)

```scala
class KafkaConfig(doLog: Boolean, val props: util.Map[_, _])
  extends AbstractKafkaConfig(KafkaConfig.configDef, props, ...) {

  // Static broker configs - read at startup
  val brokerId: Int = getInt(ServerConfigs.BROKER_ID_CONFIG)
  val zkConnect: String = getString(ZkConfigs.ZK_CONNECT_CONFIG)

  // Managed via DynamicBrokerConfig
  private[server] val dynamicConfig = new DynamicBrokerConfig(this)

  // Per-listener network configs
  val listeners: Seq[EndPoint] = parseListeners()
}
```

**Loading Flow**:
1. Broker startup reads `server.properties` file
2. `KafkaConfig.fromProps(properties)` instantiates config
3. `AbstractKafkaConfig` extends Kafka's `AbstractConfig` for validation
4. ConfigDef validates each property matches defined type and constraints

#### **3. Configuration Categories**

| Category | Update Method | Storage | Example |
|----------|---------------|---------|---------|
| **Static** | Requires restart | server.properties file | `broker.id`, `log.dirs` |
| **Dynamic Broker-level** | ALTER_CONFIGS via API | ZooKeeper `/config/brokers/{id}` | `num.io.threads`, `log.flush.ms` |
| **Dynamic Cluster-level** | ALTER_CONFIGS via API | ZooKeeper `/config/brokers/<default>` | `log.retention.hours` (default) |
| **Per-listener** | ALTER_CONFIGS with listener prefix | ZooKeeper | `listener.ssl.keystore.location` |

#### **4. Dynamic Configuration Management**

**DynamicBrokerConfig** (`core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`, line 204)

Purpose: Manages runtime configuration updates without restart

**Key Methods**:
- `validateReconfiguration()`: Validates configs before applying
- `updateCurrentConfig()`: Updates current config instance
- `reloadUpdatedFilesWithoutConfigChange()`: Reloads password files, etc.

**Validation Flow**:
```scala
// From DynamicBrokerConfig.scala line 868-875
override def validateReconfiguration(configs: util.Map[String, _]): Unit = {
  val updatedMetricsReporters = metricsReporterClasses(configs)
  updatedMetricsReporters.foreach { className =>
    val clazz = Utils.loadClass(className, classOf[MetricsReporter])
    clazz.getConstructor()  // Verify constructor exists
  }
}
```

#### **5. Configuration Sources**

**Priority Order**:
1. Command-line overrides (`--override key=value`)
2. server.properties file values
3. ConfigDef defaults
4. ZooKeeper dynamic configs (applied after startup)

**Loading Code** (`kafka/Kafka.scala`, line 30-61):
```scala
def getPropsFromArgs(args: Array[String]): Properties = {
  val props = Utils.loadProps(args(0))  // Load server.properties
  if (args.length > 1) {
    // Parse --override arguments
    props ++= CommandLineUtils.parseKeyValueArgs(...)
  }
  props
}
```

#### **6. Configuration Validation**

**Two-phase Validation**:

1. **Static Validation** (at config instantiation)
   - ConfigDef type checking (STRING, INT, BOOLEAN, etc.)
   - Range validation (min, max values)
   - Enumeration validation (valid values list)

2. **Semantic Validation** (in broker startup)
   - Cross-config dependencies (e.g., `advertised.listeners` must be in `listeners`)
   - Mode-specific validation (KRaft vs ZooKeeper)
   - Resource availability checks

**Example** (`KafkaConfig.scala`, line 929-942):
```scala
def validateAdvertisedBrokerListenersNonEmptyForBroker(): Unit = {
  require(advertisedBrokerListenerNames.nonEmpty,
    "There must be at least one broker advertised listener.")
}
```

#### **7. Dynamic Config Update Flow**

**Request Path**: Client → `AlterConfigsRequest` → Broker → `ConfigAdminManager`

**ConfigAdminManager** (`core/src/main/scala/kafka/server/ConfigAdminManager.scala`, line 268-277):
```scala
private def validateBrokerConfigChange(props: Properties, configResource: ConfigResource): Unit = {
  DynamicConfig.Broker.validate(props)
}
```

**Applying Updates**:
1. Client sends `AlterConfigs` request with new config values
2. Request validated by `DynamicBrokerConfig.validateReconfiguration()`
3. ZooKeeper configs updated if valid
4. ZooKeeper watch triggers on all brokers
5. Each broker:
   - Reads updated configs from ZooKeeper
   - Calls `DynamicConfig.reconfigure()` to apply changes
   - Updates internal state (e.g., new thread pools, metrics reporters)

#### **8. Configuration Getter Pattern**

**In KafkaConfig**:
```scala
val brokerIdGenerationEnable: Boolean = getBoolean(ServerConfigs.BROKER_ID_GENERATION_ENABLE_CONFIG)
val maxReservedBrokerId: Int = getInt(ServerConfigs.RESERVED_BROKER_MAX_ID_CONFIG)
val zkConnect: String = getString(ZkConfigs.ZK_CONNECT_CONFIG)
```

**Config Access Methods**:
- `getString(configName)`: Get string value
- `getInt(configName)`: Get integer value
- `getBoolean(configName)`: Get boolean value
- `getList(configName)`: Get list value
- `originals()`: Access all original config properties

### Configuration Files

**Default Locations**:
- `config/server.properties` - Broker configuration template
- `config/producer.properties` - Producer defaults
- `config/consumer.properties` - Consumer defaults
- `config/log4j.properties` - Logging configuration

**Common Server Properties**:
```properties
broker.id=0
listeners=PLAINTEXT://localhost:9092
advertised.listeners=PLAINTEXT://localhost:9092
log.dirs=/tmp/kafka-logs
zookeeper.connect=localhost:2181
num.io.threads=8
num.network.threads=5
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
```

---

## 6. Adding a New Broker Configuration Parameter

This section provides a step-by-step guide for adding a new broker configuration parameter with validation, dynamic update support, and proper testing.

### Example: Adding `message.max.bytes` (hypothetical enhancement)

### Step 1: Define the Configuration Parameter

**File**: Identify the appropriate config class module in `server/src/main/java/org/apache/kafka/server/config/`

For a **server/replication config**, edit: `ServerConfigs.java` or `ReplicationConfigs.java`

```java
// Example in ServerConfigs.java
public static final String CUSTOM_MESSAGE_MAX_BYTES = "custom.message.max.bytes";
public static final int CUSTOM_MESSAGE_MAX_BYTES_DEFAULT = 1048576;  // 1MB

public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(
        CUSTOM_MESSAGE_MAX_BYTES,              // Config name
        ConfigDef.Type.INT,                    // Type
        CUSTOM_MESSAGE_MAX_BYTES_DEFAULT,      // Default value
        ConfigDef.Range.atLeast(0),            // Validator (>= 0)
        ConfigDef.Importance.MEDIUM,           // Importance for documentation
        "Maximum size of custom messages in bytes",  // Documentation
        "Replication",                         // Group name
        0,                                     // Order in group
        ConfigDef.Width.MEDIUM,
        CUSTOM_MESSAGE_MAX_BYTES,              // Config name (display)
        Collections.singletonList(              // Synonyms if any
            new ConfigKeyInfo()
        )
    );
```

**Config Definition Parameters**:
- **Type**: INT, STRING, BOOLEAN, LIST, DOUBLE, LONG, SHORT, PASSWORD, CLASS
- **Default**: Default value if not specified
- **Validator**: Custom validation logic (e.g., `ConfigDef.Range.atLeast(0)`)
- **Importance**: HIGH, MEDIUM, LOW
- **Description**: User-facing documentation
- **Group**: For UI/documentation organization

### Step 2: Add Configuration Getter to KafkaConfig

**File**: `core/src/main/scala/kafka/server/KafkaConfig.scala`

Add property accessor:

```scala
// Around line 430 in KafkaConfig.scala
val customMessageMaxBytes: Int = getInt(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES)
```

**Naming Convention**: Use camelCase for Scala properties, UPPER_SNAKE_CASE for config constant names

### Step 3: Mark as Dynamic or Static

**For Dynamic Configs** (can be updated without restart):

Edit: `core/src/main/scala/kafka/server/DynamicConfig.scala`

```scala
object Broker {
  private val brokerConfigs = new ConfigDef()
    .define(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES, ...)  // Add here
}
```

**For Static Configs** (requires restart):

Don't add to DynamicConfig. Attempting to update will throw error.

### Step 4: Add Validation Logic (If Needed)

**File**: `core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`

For complex validation:

```scala
override def validateReconfiguration(configs: util.Map[String, _]): Unit = {
  super.validateReconfiguration(configs)

  // Custom validation for the new config
  if (configs.containsKey(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES)) {
    val value = configs.get(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES).asInstanceOf[Integer]
    if (value < 1024) {
      throw new ConfigException(
        ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES,
        value,
        "Must be at least 1024 bytes"
      )
    }
  }
}
```

### Step 5: Apply Configuration in Runtime Code

**Usage Pattern** in relevant component:

If config affects replica manager:

```scala
// In ReplicaManager.scala
class ReplicaManager(..., config: KafkaConfig) {
  private val customMessageMaxBytes = config.customMessageMaxBytes

  def handleProduceRequest(...): Unit = {
    // Validate message size against customMessageMaxBytes
    if (messageSize > customMessageMaxBytes) {
      throw new ApiException(Errors.MESSAGE_TOO_LARGE)
    }
  }
}
```

For dynamic updates, listen to config changes:

```scala
// In DynamicBrokerConfig.scala
dynamicConfig.addReconfigurable(new Reconfigurable {
  override def configure(configs: util.Map[String, _]): Unit = {
    val newValue = configs.get(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES).asInstanceOf[Integer]
    replicaManager.updateCustomMessageMaxBytes(newValue)
  }
})
```

### Step 6: Handle Per-Listener Configurations (If Applicable)

Some configs support per-listener overrides (e.g., SSL settings):

**For per-listener config**:

Use config name pattern: `{listener}.{config_name}`

```scala
// In KafkaConfig.scala, listener-specific configs
val listenerSecurityProtocolMap: Map[ListenerName, SecurityProtocol] =
  parseListenerSecurityProtocolMap()

def perListenerConfig(listenerName: ListenerName, baseName: String): Option[String] = {
  val listenerConfigName = s"${listenerName.value()}.$baseName"
  Option(getString(listenerConfigName)).orElse(Option(getString(baseName)))
}
```

### Step 7: Write Unit Tests

**File**: `core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala`

```scala
class KafkaConfigTest {
  @Test
  def testCustomMessageMaxBytesConfig(): Unit = {
    val props = new Properties()
    props.put("broker.id", "0")
    props.put(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES, "2048")

    val config = KafkaConfig.fromProps(props)
    assertEquals(2048, config.customMessageMaxBytes)
  }

  @Test
  def testCustomMessageMaxBytesDefault(): Unit = {
    val props = new Properties()
    props.put("broker.id", "0")

    val config = KafkaConfig.fromProps(props)
    assertEquals(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES_DEFAULT, config.customMessageMaxBytes)
  }

  @Test
  def testCustomMessageMaxBytesValidation(): Unit = {
    val props = new Properties()
    props.put("broker.id", "0")
    props.put(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES, "-1")  // Invalid

    assertThrows(classOf[ConfigException], () => KafkaConfig.fromProps(props))
  }
}
```

### Step 8: Write Dynamic Update Tests

**File**: `core/src/test/scala/unit/kafka/server/DynamicBrokerConfigTest.scala`

```scala
class DynamicBrokerConfigTest {
  @Test
  def testDynamicCustomMessageMaxBytesUpdate(): Unit = {
    val config = KafkaConfig.fromProps(createBrokerConfig())
    val dynamicConfig = new DynamicBrokerConfig(config)

    val props = new Properties()
    props.put(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES, "4096")

    // Should not throw
    dynamicConfig.validate(props, perBrokerConfig = true)

    // Apply update
    dynamicConfig.updateCurrentConfig(
      new KafkaConfig(props)
    )

    // Verify new value
    assertEquals(4096, config.customMessageMaxBytes)
  }
}
```

### Step 9: Update Broker Configuration Schema (KRaft Controllers)

**File**: `metadata/src/main/java/org/apache/kafka/metadata/KafkaConfigSchema.java`

If the config should be replicated to KRaft controllers:

```java
public static final Map<ConfigResource.Type, ConfigDef> CONFIG_DEFS =
    Collections.singletonMap(
        ConfigResource.Type.BROKER,
        Utils.mergeConfigs(Arrays.asList(
            ServerConfigs.CONFIG_DEF,  // Includes new config
            // ...
        ))
    );
```

### Step 10: Add to Configuration Documentation

**Files to update**:
1. `config/server.properties` - Add property with documentation comment
2. Official Kafka documentation files (if maintaining docs)

```properties
# Custom message maximum bytes
# Default: 1048576 (1MB)
# custom.message.max.bytes=1048576
```

### Step 11: Add Integration Test

**File**: `core/src/test/scala/integration/kafka/server/BrokerConfigTest.scala`

```scala
class BrokerConfigTest extends QuorumTestHarness {
  @Test
  def testCustomMessageMaxBytesConfigurable(): Unit = {
    val config = createBrokerConfig()
    config.put(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES, "2048")

    // Start broker with config
    val broker = createServer(KafkaConfig.fromProps(config))

    try {
      // Verify config is applied
      assertEquals(2048, broker.config.customMessageMaxBytes)

      // If dynamic, test update
      val alterConfigRequest = new AlterConfigsRequest.Builder(
        new AlterConfigsRequestData()
          .setResources(new ConfigResourceCollection(Arrays.asList(
            new ConfigResource()
              .setType(ConfigResource.Type.BROKER.id.toByte)
              .setName("0")
              .setConfigs(new ConfigEntryCollection(Arrays.asList(
                new ConfigEntry()
                  .setConfigName(ServerConfigs.CUSTOM_MESSAGE_MAX_BYTES)
                  .setConfigValue("4096")
              )))
          )))
      ).build()

      // Send alter request and verify
    } finally {
      broker.shutdown()
    }
  }
}
```

### Step 12: Test with kafka-configs.sh Tool

After building:

```bash
# List current config
./bin/kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 0 --describe

# Update config dynamically (if marked as dynamic)
./bin/kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 0 --alter \
  --add-config custom.message.max.bytes=4096

# Verify update
./bin/kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 0 --describe
```

### Key Considerations When Adding Config

| Aspect | Decision |
|--------|----------|
| **Static vs Dynamic** | Static if requires restart; Dynamic if runtime update needed |
| **Validation** | Use ConfigDef validators, add complex logic in DynamicBrokerConfig |
| **Per-listener** | Use listener prefix pattern for per-listener settings |
| **Documentation** | Add comment, type, default, range, and impact description |
| **Backward compat** | Ensure old config names work via synonyms if deprecating |
| **Testing** | Unit tests (defaults, validation), Integration tests (runtime behavior) |
| **Default value** | Should work for majority of use cases; allow override |

### Checklist for Adding Config

- [ ] Define in appropriate ConfigDef (ServerConfigs, ReplicationConfigs, etc.)
- [ ] Add getter to KafkaConfig class
- [ ] Decide: Static or Dynamic (add to DynamicConfig if dynamic)
- [ ] Add validation logic in DynamicBrokerConfig if needed
- [ ] Use config in relevant broker components
- [ ] Write unit tests (default, validation, dynamic update)
- [ ] Write integration tests
- [ ] Update server.properties documentation
- [ ] Test with kafka-configs.sh
- [ ] Update KrafKafkaConfigSchema if needed for KRaft
- [ ] Add to official documentation/release notes

---

## Summary

This orientation covers:
1. **Build & Startup**: Gradle-based build, KafkaServer/KafkaRaftServer as entry points
2. **Architecture**: Modular design with core/, server/, clients/, metadata/, streams/ etc.
3. **Topic Creation**: Multi-stage flow through KafkaApis → ZkAdminManager → ZooKeeper → ReplicaManager
4. **Testing**: JUnit 5, QuorumTestHarness, both ZK and KRaft test modes
5. **Configuration**: AbstractKafkaConfig registry, DynamicBrokerConfig for updates
6. **Adding Config**: 12-step process for static/dynamic configs with validation and testing

These patterns and structures are the foundation for understanding and contributing to Apache Kafka.
