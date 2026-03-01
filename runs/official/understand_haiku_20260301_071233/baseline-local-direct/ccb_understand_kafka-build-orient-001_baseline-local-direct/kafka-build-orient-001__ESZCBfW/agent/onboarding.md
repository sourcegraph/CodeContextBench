# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
**Gradle** is the primary build system for Kafka. The build configuration is defined in:
- `/workspace/build.gradle` - Root build file with plugins and global configuration
- `/workspace/settings.gradle` - Multi-module configuration with all project modules
- `/workspace/gradle/dependencies.gradle` - Dependency version management

Key build plugins used:
- Java-library plugin for standard Java/Scala compilation
- Shadow plugin for creating fat JARs
- Spotless for code formatting
- Spotbugs for static analysis
- Jacoco for code coverage

Build command: `./gradlew build` or scoped to specific modules like `./gradlew core:build`

### Broker Startup - Main Entry Point
**File**: `/workspace/core/src/main/scala/kafka/Kafka.scala`

**Main startup flow**:
1. `Kafka.main()` - Parses command-line arguments (server.properties file path and optional overrides)
2. `getPropsFromArgs()` - Loads properties from server.properties file and applies CLI overrides
3. `buildServer()` - Creates either a `KafkaServer` (ZooKeeper mode) or `KafkaRaftServer` (KRaft mode)
4. `server.startup()` - Calls the server's startup method
5. `server.awaitShutdown()` - Waits for shutdown signal

### Key Classes in Broker Initialization
**File**: `/workspace/core/src/main/scala/kafka/server/KafkaServer.scala`

Major initialization steps in `KafkaServer.startup()` (line 216):

1. **ZooKeeper Connection** - Initialize and connect to ZooKeeper cluster
   - `initZkClient(time)` - Creates KafkaZkClient
   - `configRepository = new ZkConfigRepository()` - For dynamic config management

2. **Cluster and Broker Identity**
   - `getOrGenerateClusterId()` - Gets or creates unique cluster ID
   - `getOrGenerateBrokerId()` - Gets or generates unique broker ID
   - Sets `config._brokerId` and `config._nodeId`

3. **Metadata and Storage**
   - Load `MetaPropertiesEnsemble` from log directories
   - Create `LogManager` (line 317) - Manages all log files and segments
   - Create `RemoteLogManager` (line 329) - Optional remote storage management

4. **Network and Coordination**
   - Create `SocketServer` (line 383) - Handles client connections
   - Initialize `MetadataCache` (line 331) - In-memory cluster metadata cache
   - Create `ReplicaManager` (line 403) - Manages replica state and log synchronization

5. **Controllers and Coordinators**
   - Create `KafkaController` (line 414) - Cluster leader election and partition management
   - Create `GroupCoordinator` (line 506) - Manages consumer groups
   - Create `TransactionCoordinator` (line 527) - Manages transactions
   - Create `DelegationTokenManager` (line 410) - Token-based authentication

6. **Request Processing**
   - Create `KafkaApis` (line 585) - Main request handler
   - Create `RequestHandlerPool` (line 609) - Thread pool for async request processing
   - Start socket server to accept client connections

**Key initialization classes**:
- `KafkaConfig` - Centralized configuration object
- `LogManager` - Log file management
- `ReplicaManager` - Replication logic
- `KafkaController` - Cluster coordination
- `SocketServer` - Network communication
- `KafkaApis` - Request handling

---

## 2. Module Structure

Kafka is organized into the following core modules (defined in `settings.gradle`):

### Core Modules

1. **core** (`/workspace/core`)
   - **Responsibility**: Main Kafka broker implementation
   - **Key packages**:
     - `kafka.server.*` - Broker startup, request handling (KafkaServer, KafkaApis, ReplicaManager)
     - `kafka.controller.*` - Cluster controller logic
     - `kafka.coordinator.*` - Group and transaction coordination
     - `kafka.log.*` - Log storage and management
     - `kafka.admin.*` - Admin command-line tools
   - Contains both Scala and Java code
   - Largest module with most broker logic

2. **clients** (`/workspace/clients`)
   - **Responsibility**: Producer and Consumer client libraries
   - **Key features**:
     - Protocol definitions and request/response types
     - `org.apache.kafka.clients.producer.KafkaProducer` - Producer API
     - `org.apache.kafka.clients.consumer.KafkaConsumer` - Consumer API
     - Network client and metadata management
   - Used by both broker and external applications

3. **server** (`/workspace/server`)
   - **Responsibility**: Broker configuration and utilities
   - **Key content**:
     - `org.apache.kafka.server.config.*` - Configuration definitions (ServerConfigs, KRaftConfigs, ZkConfigs, etc.)
     - `org.apache.kafka.server.authorizer.*` - Authorization interfaces
     - `org.apache.kafka.server.metrics.*` - Metrics definitions
   - Shared between ZooKeeper and KRaft modes

4. **server-common** (`/workspace/server-common`)
   - **Responsibility**: Common server utilities
   - **Key content**:
     - Common request/response processing
     - Shared server components

5. **metadata** (`/workspace/metadata`)
   - **Responsibility**: Metadata management and synchronization
   - **Key content**:
     - Metadata log format and serialization
     - Metadata image and loader
     - Used in KRaft mode for distributed metadata

6. **raft** (`/workspace/raft`)
   - **Responsibility**: Raft consensus implementation
   - **Key content**:
     - Raft state machine
     - Leader election
     - Log replication
   - Used in KRaft (KafkaRaft) mode instead of ZooKeeper

7. **storage** (`/workspace/storage`)
   - **Responsibility**: Log storage implementation
   - **Key packages**:
     - `org.apache.kafka.storage.internals.log.*` - LogConfig, LogCleaner, log format
   - Abstraction for log file handling

8. **group-coordinator** (`/workspace/group-coordinator`)
   - **Responsibility**: Consumer group coordination
   - **Key features**:
     - Consumer group management
     - Group state machine
     - Rebalancing logic

9. **transaction-coordinator** (`/workspace/transaction-coordinator`)
   - **Responsibility**: Transaction coordination
   - **Key features**:
     - Transaction log management
     - Producer ID allocation
     - Transactional guarantees

10. **streams** (`/workspace/streams`)
    - **Responsibility**: Kafka Streams topology and processing
    - **Key features**:
      - Stream processing DSL
      - Stateful operations (windows, joins, aggregations)
      - Interactive queries

11. **connect** (`/workspace/connect`)
    - **Responsibility**: Kafka Connect framework
    - **Key features**:
      - Source and Sink connector APIs
      - Worker and task management
      - Connectors: File, JDBC, Mirror Maker

12. **tools** (`/workspace/tools`)
    - **Responsibility**: Command-line tools
    - **Key tools**:
      - `kafka-topics.sh` - Topic management
      - `kafka-configs.sh` - Configuration management
      - `kafka-acls.sh` - ACL management

### Module Dependencies
```
clients (lowest level - no kafka dependencies)
    ↑
server-common
    ↑
server
    ↑
raft, metadata, storage, group-coordinator, transaction-coordinator
    ↑
core (broker)
    ↑
streams, connect, tools (depend on core)
```

---

## 3. Topic Creation Flow

### End-to-End Request Flow

**Request Path**: Client CreateTopicsRequest → Broker → AdminManager → ZooKeeper → Topic Created

### Detailed Flow

#### 1. **Request Reception**
**File**: `/workspace/core/src/main/scala/kafka/server/KafkaApis.scala` line 208

```scala
case ApiKeys.CREATE_TOPICS => maybeForwardToController(request, handleCreateTopicsRequest)
```

The broker determines if the request should be forwarded to the controller or handled locally.

#### 2. **Request Handling**
**Method**: `KafkaApis.handleCreateTopicsRequest()` (line 2002)

**Steps**:
- Validates that the requesting broker is the controller
- If not controller: returns `NOT_CONTROLLER` error
- If controller:
  - Performs authorization checks (CREATE permission on TOPIC or CLUSTER)
  - Filters topics the client is authorized to create
  - Validates topic configurations
  - Delegates to `ZkAdminManager.createTopics()`

#### 3. **Admin Manager Processing**
**Class**: `/workspace/core/src/main/scala/kafka/server/ZkAdminManager.scala`
**Method**: `createTopics()` (line 159)

**This method performs the following**:

**Step 3a: Validate and Calculate Assignments** (lines 166-213)
```scala
val brokers = metadataCache.getAliveBrokers()
val metadata = toCreate.values.map(topic => {
  // 1. Check topic doesn't already exist
  if (metadataCache.contains(topic.name))
    throw new TopicExistsException(...)

  // 2. Validate topic configs (no null values)
  val nullConfigs = topic.configs.asScala.filter(_.value == null).map(_.name)
  if (nullConfigs.nonEmpty)
    throw new InvalidConfigurationException(...)

  // 3. Calculate partition assignments
  val resolvedNumPartitions = if (topic.numPartitions == NO_NUM_PARTITIONS)
    defaultNumPartitions else topic.numPartitions
  val resolvedReplicationFactor = if (topic.replicationFactor == NO_REPLICATION_FACTOR)
    defaultReplicationFactor else topic.replicationFactor

  val assignments = if (topic.assignments.isEmpty) {
    // Use default replica assignment algorithm (rack-aware)
    AdminUtils.assignReplicasToBrokers(brokers, resolvedNumPartitions, resolvedReplicationFactor)
  } else {
    // Use user-provided assignments
    topic.assignments
  }

  // 4. Validate with ZK and policies
  adminZkClient.validateTopicCreate(topic.name, assignments, configs)
  validateTopicCreatePolicy(topic, numPartitions, replicationFactor, assignments)

  // 5. Populate metadata for response
  maybePopulateMetadataAndConfigs(includeConfigsAndMetadata, topic.name, configs, assignments)

  // For validateOnly requests, return metadata without creating
  if (validateOnly) {
    CreatePartitionsMetadata(topic.name, assignments.keySet)
  } else {
    // Create topic in ZooKeeper
    adminZkClient.createTopicWithAssignment(topic.name, configs, assignments, validate = false, config.usesTopicId)
    populateIds(includeConfigsAndMetadata, topic.name)
    CreatePartitionsMetadata(topic.name, assignments.keySet)
  }
})
```

**Step 3b: Wait for Topic Creation Completion** (lines 239-257)
```scala
if (timeout <= 0 || validateOnly || !metadata.exists(_.error.is(Errors.NONE))) {
  // Return immediately if no timeout, validate-only mode, or errors
  responseCallback(results)
} else {
  // Create delayed operation and wait for topic leader election
  val delayedCreate = new DelayedCreatePartitions(timeout, metadata, this, responseCallback)
  val delayedCreateKeys = toCreate.values.map(topic => TopicKey(topic.name)).toBuffer
  // Put in purgatory (delayed operation queue) until completion
  topicPurgatory.tryCompleteElseWatch(delayedCreate, delayedCreateKeys)
}
```

#### 4. **ZooKeeper Operations**
**File**: `/workspace/core/src/main/scala/kafka/zk/AdminZkClient.scala`

**Method**: `createTopicWithAssignment()` creates ZK nodes:
```
/config/topics/{topic_name}          - Topic configuration
/brokers/topics/{topic_name}         - Topic partition assignments
/brokers/topics/{topic_name}/partitions/{partition} - Per-partition metadata
```

#### 5. **Controller Watcher Notification**
When ZK nodes are created, the controller watches for changes and:
- Triggers leader election for new partitions
- Waits for in-sync replicas (ISR) to be established
- Signals completion of topic creation

#### 6. **Response Sent to Client**
**Response includes**:
- Success/error for each requested topic
- Topic configuration (if authorized)
- Number of partitions and replication factor

### Key Classes and Methods

| Component | File | Key Method | Purpose |
|-----------|------|-----------|---------|
| Request Handler | KafkaApis.scala | handleCreateTopicsRequest() | Entry point for CreateTopics request |
| Admin Manager | ZkAdminManager.scala | createTopics() | Coordinates topic creation |
| ZK Client | AdminZkClient.scala | createTopicWithAssignment() | Creates ZK nodes |
| Controller | KafkaController.scala | onNewTopicCreation() | Performs leader election |
| Delayed Op | DelayedCreatePartitions.scala | tryComplete() | Waits for ISR to be established |
| Metadata Cache | MetadataCache.scala | updateMetadata() | Updates in-memory metadata |

### Configuration Points
- Default partitions: `num.partitions` config
- Default replication factor: `default.replication.factor` config
- Rack awareness: Uses broker rack information from config
- Min ISR: Configurable per-topic via `min.insync.replicas`

---

## 4. Testing Framework

### Test Frameworks and Tools

**JUnit 5 (Jupiter)**: Primary testing framework
- File: Test files in `/workspace/*/src/test/`
- Annotation: `@Test` for test methods
- Class naming convention: `*Test.scala` or `*Test.java`

**Mockito**: Mocking framework
- Library: `mockitoCore` in dependencies
- Usage: Mock server components, Kafka clients, etc.

**ScalaTest** (legacy): Some tests still use ScalaTest assertions
- Scala-specific testing utilities

### Unit Test Patterns

#### 1. **Server Component Tests**
Location: `/workspace/core/src/test/scala/unit/kafka/server/`

Example: `DynamicBrokerConfigTest.scala` (line 56)
```scala
class DynamicBrokerConfigTest {
  @Test
  def testConfigUpdate(): Unit = {
    // 1. Setup: Create broker config
    val props = TestUtils.createBrokerConfig(0, null, port = 8181)
    val config = KafkaConfig(props)
    val dynamicConfig = config.dynamicConfig
    dynamicConfig.initialize(None, None)

    // 2. Execute: Update configuration
    val props1 = new Properties
    props1.put("listener.name.external.${SSL_KEYSTORE_LOCATION_CONFIG}", newKeystore)
    dynamicConfig.updateBrokerConfig(0, props1)

    // 3. Verify: Assert expected state
    assertEquals(newKeystore, config.valuesWithPrefixOverride("listener.name.external.").get(SslConfigs.SSL_KEYSTORE_LOCATION_CONFIG))
  }
}
```

**Common Utilities**:
- `TestUtils.createBrokerConfig()` - Creates minimal broker config for testing
- `Mockito.mock()` - Create mocks of server components
- `assertEquals()`, `assertTrue()`, `assertThrows()` - JUnit assertions

#### 2. **API Request/Response Tests**
Location: `/workspace/core/src/test/scala/unit/kafka/server/`

Example: `CreateTopicsRequestTest.scala`

Pattern:
```scala
// Create test broker with config
val config = createBrokerConfig(...)
val server = EmbeddedKafkaCluster(config)

// Create request
val request = new CreateTopicsRequest.Builder(...)
  .topics(topic, 1, 3) // name, partitions, replication-factor
  .build()

// Send request and verify response
val response = server.adminClient.createTopics(topics)
assertEquals(Errors.NONE, response.values().iterator().next().error())
```

#### 3. **Integration Tests**
Location: `/workspace/core/src/test/scala/integration/kafka/`

Pattern: Tests with real ZooKeeper and Kafka cluster
```scala
class TopicCommandIntegrationTest extends ZooKeeperTestHarness {
  val serverConfigs = (0 until numServers).map(createBrokerConfig(_))
  val cluster = new KafkaCluster(serverConfigs) // Real broker instances

  cluster.createTopic("test-topic", partitions = 3, replicationFactor = 2)
  cluster.verifyTopic("test-topic")
  cluster.shutdown()
}
```

**Base classes for integration tests**:
- `ZooKeeperTestHarness` - Sets up ZooKeeper for testing
- `KafkaCluster` - Sets up real Kafka broker instances
- `EmbeddedKafkaCluster` - Lightweight embedded cluster

### Test Configuration

**File**: `/workspace/core/src/test/scala/unit/kafka/server/AbstractCreateTopicsRequestTest.scala`

Base test class provides:
- Mock broker setup
- Config creation utilities
- Request/response helpers
- Authentication/authorization test utilities

### Testing Best Practices

1. **Unit Tests**: Test individual components (config validation, request parsing)
   - Mock external dependencies
   - Focus on business logic
   - Location: `unit/` subdirectories

2. **Integration Tests**: Test multiple components together
   - Use real ZooKeeper/Kafka clusters
   - Test end-to-end flows
   - Location: `integration/` subdirectories

3. **System Tests**: Test entire system (located in `/workspace/tests/`)
   - Run against real cluster
   - Verify durability, replication, failover

### Running Tests
```bash
# Run all tests in a module
./gradlew core:test

# Run specific test class
./gradlew core:test --tests DynamicBrokerConfigTest

# Run integration tests only
./gradlew core:integrationTest

# Run with specific options
./gradlew core:test -Dlog4j.configuration=file:log4j-test.xml
```

---

## 5. Configuration System

### Configuration Architecture

Kafka broker configuration has three layers:

1. **Static Configuration** (defined at startup)
   - Read from `server.properties` file
   - CLI overrides via `--override` flag
   - Immutable after broker startup

2. **Dynamic Configuration** (can be updated at runtime)
   - Updated via `AlterConfigs` admin API
   - Stored in ZooKeeper path `/config/brokers/{broker_id}`
   - Applied to running broker without restart

3. **Per-Topic Configuration**
   - Set during topic creation or via `AlterConfigs` API
   - Stored in ZooKeeper `/config/topics/{topic_name}`

### Configuration Registry Location

**Main Registry**: `/workspace/server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`

Configuration is built from multiple ConfigDef sources merged together (line 45):
```java
public static final ConfigDef CONFIG_DEF = Utils.mergeConfigs(Arrays.asList(
    RemoteLogManagerConfig.configDef(),
    ZkConfigs.CONFIG_DEF,
    ServerConfigs.CONFIG_DEF,           // Main broker configs
    KRaftConfigs.CONFIG_DEF,            // KRaft-specific configs
    SocketServerConfigs.CONFIG_DEF,     // Network configs
    ReplicationConfigs.CONFIG_DEF,      // Replication configs
    GroupCoordinatorConfig.GROUP_COORDINATOR_CONFIG_DEF,  // Group coordination
    CleanerConfig.CONFIG_DEF,           // Log cleaner configs
    LogConfig.SERVER_CONFIG_DEF,        // Log/segment configs
    TransactionLogConfigs.CONFIG_DEF,   // Transaction log configs
    QuotaConfigs.CONFIG_DEF,            // Quota/throttle configs
    // ... and more
));
```

### Core Config Modules

| Module | File | Responsibility |
|--------|------|-----------------|
| ServerConfigs | `/workspace/server/src/main/java/.../config/ServerConfigs.java` | General broker configs (message.max.bytes, num.io.threads, etc.) |
| ZkConfigs | `/workspace/server/src/main/java/.../config/ZkConfigs.java` | ZooKeeper connection configs |
| KRaftConfigs | `/workspace/server/src/main/java/.../config/KRaftConfigs.java` | KRaft cluster configs |
| SocketServerConfigs | `/workspace/server/src/main/java/.../network/SocketServerConfigs.java` | Network and listener configs |
| ReplicationConfigs | `/workspace/server/src/main/java/.../config/ReplicationConfigs.java` | Replication behavior configs |
| LogConfig | `/workspace/storage/src/main/java/.../log/LogConfig.java` | Log file and segment configs |

### How Configs are Accessed

**File**: `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`

1. **Loading Configuration**
```scala
val props = Utils.loadProps("server.properties")
val config = KafkaConfig.fromProps(props, doLog = true)
```

2. **Accessing Config Values**
```scala
config.brokerId                    // Typed accessor for int configs
config.getString("config.name")    // Generic string accessor
config.getInt("config.name")       // Generic int accessor
config.getLong("config.name")      // Generic long accessor
config.getBoolean("config.name")   // Generic boolean accessor
```

3. **Config Types Defined**
Each config has:
- **Name**: Configuration key (e.g., `broker.id`)
- **Default Value**: Applied if not specified
- **Type**: STRING, INT, LONG, BOOLEAN, LIST, DOUBLE, PASSWORD
- **Validator**: Range validator, valid values list, custom validators
- **Importance**: LOW, MEDIUM, HIGH
- **Documentation**: Help text for users

Example from ServerConfigs (line 47):
```java
public static final String BROKER_ID_CONFIG = "broker.id";
public static final int BROKER_ID_DEFAULT = -1;
public static final String BROKER_ID_DOC = "The broker id for this server...";

.define(BROKER_ID_CONFIG, INT, BROKER_ID_DEFAULT, HIGH, BROKER_ID_DOC)
```

### Configuration Validation

**Validators Available**:
- `ConfigDef.Range.atLeast(n)` - Minimum value validation
- `ConfigDef.Range.between(min, max)` - Range validation
- `ConfigDef.ValidString.in(values)` - Allowed values list
- `ConfigDef.NonNullValidator()` - Non-null check
- Custom validators implementing `ConfigDef.Validator`

Example (ServerConfigs line 146):
```java
.define(NUM_IO_THREADS_CONFIG, INT, NUM_IO_THREADS_DEFAULT, atLeast(1), HIGH, NUM_IO_THREADS_DOC)
```

### Dynamic Configuration Updates

**File**: `/workspace/core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`

Configs can be updated dynamically in two ways:

1. **Reconfigurable Components**: Components implementing `org.apache.kafka.common.Reconfigurable`
   - Called with `onNewBrokerConfig()` when config changes
   - Must handle dynamic updates without restart
   - Examples: SocketServer, ReplicaManager, LogManager

2. **Configuration Update Process**:
   - Admin client sends `AlterConfigs` request
   - Controller updates ZooKeeper `/config/brokers/{broker_id}` node
   - All brokers watch this ZK node for changes
   - Brokers load updated config and call `onNewBrokerConfig()` on affected components
   - No broker restart required

---

## 6. Adding a New Broker Configuration

### Complete Step-by-Step Process

#### Step 1: Define the Configuration Parameter

**File**: Choose the appropriate config module based on the parameter's purpose

Example use cases:
- General broker config → `/workspace/server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`
- Replication-related → `/workspace/server/src/main/java/org/apache/kafka/server/config/ReplicationConfigs.java`
- ZooKeeper-related → `/workspace/server/src/main/java/org/apache/kafka/server/config/ZkConfigs.java`

**Implementation** (adding to ServerConfigs.java):

```java
// 1. Define constants for the new config
public static final String MY_NEW_CONFIG = "my.new.config";
public static final String MY_NEW_CONFIG_DEFAULT = "default_value";
public static final String MY_NEW_CONFIG_DOC =
    "Description of what this config does, what values are accepted, and examples.";

// 2. Define range/validator constraints (if needed)
public static final Range MY_NEW_CONFIG_RANGE = atLeast(0);
public static final ValidString MY_NEW_CONFIG_VALIDATOR =
    ValidString.in("value1", "value2", "value3");

// 3. Register in CONFIG_DEF
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    // ... existing configs ...
    .define(MY_NEW_CONFIG, INT, MY_NEW_CONFIG_DEFAULT,
            MY_NEW_CONFIG_RANGE, MEDIUM, MY_NEW_CONFIG_DOC)
    // ... remaining configs ...
```

#### Step 2: Add Accessor to KafkaConfig (if needed)

**File**: `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`

If you need typed accessor (recommended for frequently accessed configs):

```scala
class KafkaConfig(props: java.util.Map[_, _], doLog: Boolean = true)
    extends AbstractKafkaConfig(KafkaConfig.CONFIG_DEF, props, null, doLog) {

  // ... existing accessors ...

  val myNewConfig = getInt(ServerConfigs.MY_NEW_CONFIG)
}
```

Alternatively, access via generic methods:
```scala
val value: Int = config.getInt(ServerConfigs.MY_NEW_CONFIG)
val value: String = config.getString(ServerConfigs.MY_NEW_CONFIG)
```

#### Step 3: Handle Dynamic Updates (if applicable)

**Question**: Can this config be updated without restarting the broker?

**If YES** (e.g., thread counts, timeouts):

**File**: Implement `org.apache.kafka.common.Reconfigurable` in the component that uses this config

```java
public class MyComponent implements Reconfigurable {
    private volatile int myNewConfigValue;

    // Initial configuration
    public void configure(Map<String, ?> configs) {
        this.myNewConfigValue = (Integer) configs.get(ServerConfigs.MY_NEW_CONFIG);
    }

    // Called when config is dynamically updated
    @Override
    public void onNewBrokerConfig(Map<String, ?> newConfigs, Set<String> changedKeys) {
        if (changedKeys.contains(ServerConfigs.MY_NEW_CONFIG)) {
            this.myNewConfigValue = (Integer) newConfigs.get(ServerConfigs.MY_NEW_CONFIG);
            // Apply changes without restart
            adjustComponentBehavior(this.myNewConfigValue);
        }
    }

    @Override
    public Set<String> reconfigurableConfigs() {
        return Collections.singleton(ServerConfigs.MY_NEW_CONFIG);
    }
}
```

Register the component in KafkaServer:
```scala
// In KafkaServer.startup()
if (config.isDynamicConfigUpdateEnabled) {
    myComponent.onNewBrokerConfig(config.dynamicConfig.currentKafkaConfig.originals,
                                   changedConfigs)
}
```

**If NO** (static configuration only):
- No additional code needed
- Config will be read once at startup
- Document that broker restart required for this config

#### Step 4: Add Configuration Validation (if custom logic needed)

**File**: `/workspace/core/src/main/scala/kafka/server/KafkaConfig.scala`

In the constructor, add custom validation:

```scala
class KafkaConfig(props: java.util.Map[_, _], doLog: Boolean = true)
    extends AbstractKafkaConfig(KafkaConfig.CONFIG_DEF, props, null, doLog) {

    // ... existing code ...

    // Custom validation logic
    if (myNewConfig < 0) {
        throw new ConfigException(ServerConfigs.MY_NEW_CONFIG, myNewConfig,
            "my.new.config must not be negative")
    }

    // Cross-config validation
    if (myNewConfig > someOtherConfig) {
        throw new ConfigException(ServerConfigs.MY_NEW_CONFIG, myNewConfig,
            "my.new.config must not exceed some.other.config")
    }
}
```

#### Step 5: Update Configuration Usage in Code

**File**: Wherever the config should be used (e.g., `/workspace/core/src/main/scala/kafka/server/KafkaServer.scala`)

```scala
// In broker startup or component initialization
val myComponentConfig = new MyComponentConfig(
    config.myNewConfig,           // Use typed accessor if available
    config.getString("other.config")
)

val myComponent = new MyComponent(myComponentConfig)
```

#### Step 6: Add Unit Tests for Configuration

**File**: `/workspace/core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala` or new test file

```scala
class MyNewConfigTest {

    @Test
    def testMyNewConfigDefaultValue(): Unit = {
        val props = TestUtils.createBrokerConfig(0, null)
        // Don't set my.new.config, should use default
        val config = KafkaConfig(props)
        assertEquals(ServerConfigs.MY_NEW_CONFIG_DEFAULT, config.myNewConfig)
    }

    @Test
    def testMyNewConfigCustomValue(): Unit = {
        val props = TestUtils.createBrokerConfig(0, null)
        props.put(ServerConfigs.MY_NEW_CONFIG, "custom_value")
        val config = KafkaConfig(props)
        assertEquals("custom_value", config.myNewConfig)
    }

    @Test
    def testMyNewConfigValidation(): Unit = {
        val props = TestUtils.createBrokerConfig(0, null)
        props.put(ServerConfigs.MY_NEW_CONFIG, "-1")  // Invalid: negative
        assertThrows(classOf[ConfigException], () => KafkaConfig(props))
    }

    @Test
    def testMyNewConfigDynamicUpdate(): Unit = {
        val props = TestUtils.createBrokerConfig(0, null)
        val config = KafkaConfig(props)
        val dynamicConfig = config.dynamicConfig
        dynamicConfig.initialize(None, None)

        // Update dynamic config
        val updateProps = new Properties()
        updateProps.put(ServerConfigs.MY_NEW_CONFIG, "new_value")
        dynamicConfig.updateBrokerConfig(config.brokerId, updateProps)

        // Verify component handles update
        val component = getMyComponentFromServer()  // Get component from running server
        assertEquals("new_value", component.getCurrentConfigValue())
    }
}
```

#### Step 7: Add Integration Tests (if needed)

**File**: `/workspace/core/src/test/scala/integration/kafka/MyNewConfigIntegrationTest.scala`

```scala
class MyNewConfigIntegrationTest extends ZooKeeperTestHarness {

    @Test
    def testMyNewConfigInCluster(): Unit = {
        val brokerConfigs = (0 until 2).map { i =>
            val config = createBrokerConfig(i)
            config.put(ServerConfigs.MY_NEW_CONFIG, "value_for_broker_" + i)
            config
        }

        val cluster = new KafkaCluster(brokerConfigs)

        // Test that config affects cluster behavior
        verifyClusterBehaviorWithConfig()

        cluster.shutdown()
    }
}
```

#### Step 8: Update Documentation

**Files to update**:
- Add to documentation comments in the config file
- Update Kafka configuration documentation (if this is a public config)
- Add migration guide if replacing/deprecating an old config

**Documentation template**:
```
CONFIG NAME: my.new.config
TYPE: Integer / String / Boolean / List
DEFAULT: <default_value>
DYNAMIC UPDATES: true / false
IMPORTANCE: LOW / MEDIUM / HIGH

DESCRIPTION:
Brief description of what this config does.

VALUE CONSTRAINTS:
- Minimum: X
- Maximum: Y
- Valid values: [list]

EXAMPLES:
my.new.config=10

RELATED CONFIGS:
- other.config.name
```

#### Step 9: Handle Configuration in Different Modes

**ZooKeeper Mode**: Config stored in static file or ZK
**KRaft Mode**: Config stored in metadata log

If your config applies to only one mode:
```scala
if (config.requiresZookeeper) {
    // ZK-specific initialization
} else {
    // KRaft-specific initialization
}
```

#### Step 10: Update Gradle Build Configuration (if needed)

Usually not needed unless adding new config module. The CONFIG_DEF is automatically included via module dependencies.

### Configuration Change Validation Checklist

- [ ] Config added to appropriate module (ServerConfigs, etc.)
- [ ] Constants defined (name, default, doc)
- [ ] Type validation added (Range, ValidString, etc.)
- [ ] Accessor added to KafkaConfig (if frequently used)
- [ ] Custom validation logic added (if complex rules)
- [ ] Component updated to use new config
- [ ] Reconfigurable interface implemented (if dynamic update supported)
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Documentation updated
- [ ] Backwards compatibility considered
- [ ] Both ZK and KRaft modes tested (if applicable)

### Example: Adding a New Thread Pool Configuration

**Real example**: Adding `num.replication.threads`

```java
// 1. ServerConfigs.java
public static final String NUM_REPLICATION_THREADS_CONFIG = "num.replication.threads";
public static final int NUM_REPLICATION_THREADS_DEFAULT = 4;
public static final String NUM_REPLICATION_THREADS_DOC =
    "The number of threads used for replication. Increasing this value may " +
    "improve replication throughput at the cost of increased CPU and memory usage.";

.define(NUM_REPLICATION_THREADS_CONFIG, INT, NUM_REPLICATION_THREADS_DEFAULT,
        atLeast(1), HIGH, NUM_REPLICATION_THREADS_DOC)

// 2. KafkaConfig.scala
val numReplicationThreads = getInt(ServerConfigs.NUM_REPLICATION_THREADS_CONFIG)

// 3. ReplicaManager.scala - Uses config to size thread pool
class ReplicaManager(...) extends Reconfigurable {
    private var threadPool = createThreadPool(config.numReplicationThreads)

    override def onNewBrokerConfig(newConfigs: Map[String, ?], changedKeys: Set[String]) {
        if (changedKeys.contains(ServerConfigs.NUM_REPLICATION_THREADS_CONFIG)) {
            val newThreadCount = newConfigs.get(ServerConfigs.NUM_REPLICATION_THREADS_CONFIG).asInstanceOf[Int]
            resizeThreadPool(newThreadCount)
        }
    }
}

// 4. Tests verify thread pool is sized correctly
```

---

## Summary

This onboarding document provides the architectural foundation for understanding Apache Kafka:

- **Build System**: Gradle multi-module build
- **Startup Flow**: Kafka.scala → KafkaServer.scala with 6 major initialization phases
- **Module Structure**: 12 major modules with clear responsibilities
- **Topic Creation**: Multi-stage flow through KafkaApis → ZkAdminManager → ZooKeeper
- **Testing**: JUnit 5 + Mockito for unit tests, real clusters for integration tests
- **Configuration**: Three-layer system (static, dynamic, per-topic) with CONFIG_DEF registry
- **Adding Config**: 10-step process with validation, dynamic updates, and testing

Use this knowledge to navigate the codebase, understand request flows, and implement changes safely.
