# Apache Kafka Codebase Orientation

## 1. Build System and Broker Startup

### Build System
Apache Kafka uses **Gradle** as its build system. The main build configuration is defined in:
- **`build.gradle`**: Root build file
- **`settings.gradle`**: Defines module structure and configuration
- **`wrapper.gradle`**: Gradle wrapper configuration for reproducible builds

### Broker Startup Entry Point

The main entry point for starting a Kafka broker is:
- **File**: `core/src/main/scala/kafka/Kafka.scala`
- **Main Class**: `kafka.Kafka` (object with `main` method)

#### Key Startup Flow:

1. **`Kafka.main(args: Array[String])`** (lines 87-128):
   - Parses command-line arguments using `getPropsFromArgs()`
   - Builds either a `KafkaServer` (ZooKeeper mode) or `KafkaRaftServer` (KRaft mode)
   - Registers shutdown hooks for graceful termination
   - Calls `server.startup()` to start the broker
   - Calls `server.awaitShutdown()` to keep broker running

2. **`buildServer(props: Properties): Server`** (lines 70-85):
   - Creates `KafkaConfig` from properties
   - Checks `config.requiresZookeeper` to determine mode
   - Returns either `KafkaServer` (ZK) or `KafkaRaftServer` (KRaft)

### Key Classes Involved in Broker Initialization

1. **`kafka.server.KafkaServer`** (`core/src/main/scala/kafka/server/KafkaServer.scala`, line 112)
   - Main ZooKeeper-based broker implementation
   - Extends `KafkaBroker` and `Server` traits
   - Constructor takes: `config: KafkaConfig`, `time: Time`, `threadNamePrefix: Option[String]`, `enableForwarding: Boolean`
   - Key initialization components:
     - `kafkaMetricsReporters`: KafkaMetricsReporter instances
     - `socketServer`: SocketServer for handling network communication
     - `logManager`: LogManager for managing log segments
     - `replicaManager`: ReplicaManager for replica management
     - `kafkaController`: KafkaController for cluster coordination
     - `groupCoordinator`: GroupCoordinator for consumer groups
     - `transactionCoordinator`: TransactionCoordinator for transactions
     - `metadataCache`: ZkMetadataCache for caching metadata
     - `zkClient`: KafkaZkClient for ZooKeeper communication

2. **`kafka.server.KafkaConfig`** (`core/src/main/scala/kafka/server/KafkaConfig.scala`, line 181)
   - Extends `AbstractKafkaConfig` from `server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`
   - Holds all broker configuration parameters
   - Merges ConfigDef from multiple sources (ZK, Server, Replication, Security, etc.)
   - Contains both static and dynamic broker configurations

3. **`kafka.server.KafkaRaftServer`** (KRaft mode alternative)
   - For KRaft-only mode (without ZooKeeper)
   - Uses raft-based metadata replication

## 2. Module Structure

Kafka is organized into multiple modules, each with specific responsibilities:

### Core Modules

1. **`clients/`** - Kafka Java client libraries
   - **`clients/src/main/java/org/apache/kafka/clients/`**: Core client implementation
     - Producer API
     - Consumer API
     - Admin API
     - Network communication layer
   - Responsibility: Provides client-side APIs for producers, consumers, and administrators

2. **`core/`** - Core broker implementation
   - **`core/src/main/scala/kafka/server/`**: Broker server logic
     - `KafkaServer.scala`: Main broker class
     - `KafkaApis.scala`: Request handling for all API requests
     - `ReplicaManager.scala`: Manages log replicas
     - `LogManager.scala`: Manages log segments and retention
     - `KafkaController.scala`: Cluster coordination
     - `ConfigHandler.scala`: Dynamic configuration handling
   - **`core/src/main/scala/kafka/network/`**: Network layer
   - **`core/src/main/scala/kafka/log/`**: Log management and segments
   - **`core/src/test/`**: Unit and integration tests for core functionality
   - Responsibility: Main broker functionality

3. **`server/`** - Server-side configurations and utilities
   - **`server/src/main/java/org/apache/kafka/server/config/`**: Configuration definitions
     - `ServerConfigs.java`: Broker-level configuration definitions
     - `AbstractKafkaConfig.java`: Base config class merging all ConfigDefs
   - Responsibility: Server configuration infrastructure

4. **`server-common/`** - Common server-side utilities
   - **`server-common/src/main/java/org/apache/kafka/server/config/`**: Shared config definitions
     - `QuotaConfigs.java`: Quota configuration definitions
     - `ReplicationConfigs.java`: Replication configuration
     - `ZkConfigs.java`: ZooKeeper configuration
   - Responsibility: Shared configuration and utilities

5. **`group-coordinator/`** - Consumer group coordination
   - Consumer group metadata and rebalancing logic
   - Responsibility: Manages consumer group state and rebalancing

6. **`transaction-coordinator/`** - Transaction coordination
   - Transactional write support
   - Responsibility: Manages transactional operations and cleanup

7. **`storage/`** - Storage layer abstractions
   - **`storage/src/main/java/org/apache/kafka/storage/internals/log/`**: Log configuration and management
   - Responsibility: Storage engine abstractions

8. **`raft/`** - Raft consensus for KRaft mode
   - Raft-based leader election and log replication
   - Responsibility: KRaft metadata replication

9. **`metadata/`** - Metadata layer
   - **`metadata/src/main/java/org/apache/kafka/metadata/`**: Metadata structures
   - Responsibility: Metadata schema and definitions

10. **`streams/`** - Kafka Streams framework
    - Stream processing topology
    - Responsibility: Stream processing library

11. **`connect/`** - Kafka Connect framework
    - Distributed data pipelines
    - Responsibility: Data integration framework

12. **`tools/`** - Administrative tools
    - Topic management tools, performance testing tools
    - Responsibility: Operational utilities

13. **`tests/`** - System tests and integration tests
    - Python-based integration test framework
    - Responsibility: End-to-end testing

## 3. Topic Creation Flow

Topic creation in Kafka goes through several layers from client request to actual topic creation:

### Complete Request Flow

```
Client Request
    ↓
KafkaApis.handleCreateTopicsRequest() (core/src/main/scala/kafka/server/KafkaApis.scala, line 2002)
    ↓
Authorization checks (authHelper.authorize())
    ↓
Validation (topic name, partition count, replication factor, configs)
    ↓
ZkAdminManager.createTopics() (core/src/main/scala/kafka/server/ZkAdminManager.scala, line 159)
    ↓
AdminZkClient.createTopicWithAssignment() (writes to ZooKeeper)
    ↓
Partition Assignment & Log Creation
    ↓
Response sent to client
```

### Key Classes and Methods

1. **`KafkaApis.handleCreateTopicsRequest(request: RequestChannel.Request)`** (line 2002)
   - Entry point for CreateTopics API request
   - **Steps:**
     - Check if controller is active (if not, return NOT_CONTROLLER error)
     - Create CreatableTopicResultCollection to collect results
     - Check cluster-level CREATE authorization using `authHelper.authorize()`
     - Filter topics by CREATE permission (per-topic authorization)
     - Validate topics don't already exist
     - Check for duplicate topic names in request
     - Populate metadata and configs for authorized topics
     - Call `zkSupport.adminManager.createTopics()` to perform actual creation
     - Send response with results

2. **`ZkAdminManager.createTopics()`** (line 159)
   - **Parameters:**
     - `timeout: Int`: Request timeout in ms
     - `validateOnly: Boolean`: If true, only validate without creating
     - `toCreate: Map[String, CreatableTopic]`: Topics to create
     - `includeConfigsAndMetadata: Map[String, CreatableTopicResult]`: Results to populate
     - `controllerMutationQuota: ControllerMutationQuota`: For quota enforcement
     - `responseCallback: Map[String, ApiError] => Unit`: Callback with results

   - **Core Logic (lines 166-237):**
     - Get list of alive brokers from metadata cache
     - For each topic:
       - Validate topic doesn't already exist
       - Validate no null config values
       - Validate numPartitions/replicationFactor not mixed with explicit assignments
       - Resolve partition count (use default if not specified)
       - Resolve replication factor (use default if not specified)
       - Calculate replica assignments using `AdminUtils.assignReplicasToBrokers()`
       - Validate topic configs against ConfigDef
       - Call `adminZkClient.createTopicWithAssignment()` to write to ZooKeeper
     - If timeout <= 0, validateOnly=true, or errors exist: return immediately with results
     - Otherwise: wait for partition creation with timeout

3. **`AdminZkClient.createTopicWithAssignment()`** (in `kafka.zk.AdminZkClient`)
   - Writes topic metadata to ZooKeeper:
     - `/config/topics/{topicName}`: Topic configuration
     - `/brokers/topics/{topicName}`: Partition assignment

### Key Components Involved

1. **`kafka.server.KafkaApis`** (line 1)
   - Handles all API requests
   - Has access to:
     - `metadataSupport`: For metadata operations
     - `authHelper`: For authorization checks
     - `zkSupport.adminManager`: For topic operations

2. **`kafka.zk.AdminZkClient`**
   - Wrapper around ZooKeeper operations
   - Methods:
     - `createTopicWithAssignment()`: Creates topic with explicit partition assignment
     - `validateTopicCreate()`: Validates topic creation parameters

3. **Metadata Cache** (`kafka.server.MetadataCache`)
   - In-memory cache of cluster metadata
   - Used to:
     - Check if topic already exists
     - Get list of alive brokers for assignment

4. **Configuration Validation**
   - Topic configs validated against `LogConfig.SERVER_CONFIG_DEF`
   - Uses ConfigDef validators to check value types and ranges

### Response Generation

After successful creation or error, response contains:
- Topic name
- Error code (Errors.NONE for success)
- Error message (if applicable)
- Topic metadata (partitions, replicas, ISR)
- Topic configuration (if authorized)

## 4. Testing Framework

Kafka uses multiple testing frameworks and patterns for unit and integration testing:

### Testing Frameworks

1. **JUnit 5** (Jupiter)
   - Modern Java testing framework
   - Used with annotations: `@Test`, `@BeforeEach`, `@AfterEach`, `@Timeout`, `@ExtendWith`
   - Imports: `org.junit.jupiter.api.*`

2. **ScalaTest** (for Scala tests)
   - Scala testing framework with multiple styles
   - Used with traits for test organization
   - Example: `core/src/test/scala/unit/kafka/server/KafkaServerTest.scala`

3. **Mockito**
   - Mocking framework for Java/Scala
   - Used to mock dependencies in unit tests
   - Annotations: `@Mock`, `@ExtendWith(MockitoExtension.class)`

### Test Harnesses and Base Classes

1. **`QuorumTestHarness`** (`core/src/test/scala/integration/kafka/server/QuorumTestHarness.scala`)
   - Base class for tests that need broker infrastructure
   - **Responsibilities:**
     - Manages ZooKeeper instance (EmbeddedZookeeper) for ZK mode
     - Manages KRaft controller for KRaft mode
     - Creates and starts broker instances
     - Handles cleanup
   - **Traits:**
     - `ZooKeeperQuorumImplementation`: For ZK-based tests
     - `KRaftQuorumImplementation`: For KRaft-based tests
   - **Key Methods:**
     - `createBroker()`: Creates a broker instance
     - `setUp()`: Initializes test environment (with `@BeforeAll`, `@BeforeEach`)
     - `tearDown()`: Cleans up resources (with `@AfterAll`, `@AfterEach`)

2. **`KafkaServerTestHarness`** (`core/src/test/scala/unit/kafka/integration/KafkaServerTestHarness.scala`)
   - Extends `QuorumTestHarness`
   - Adds convenience methods for ZK-based testing
   - **Key properties:**
     - `servers: mutable.Buffer[KafkaServer]`: All broker instances
     - `getController(): KafkaServer`: Returns controller broker
   - Simplifies test setup for broker-focused tests

3. **`IntegrationTestHarness`** (`core/src/test/scala/integration/kafka/api/IntegrationTestHarness.scala`)
   - Extends `KafkaServerTestHarness`
   - Adds producer and consumer setup
   - **Key properties:**
     - `producer`: KafkaProducer instance
     - `consumer`: KafkaConsumer instance
   - Used for end-to-end integration tests

### Testing Patterns

#### Unit Tests
- Location: `core/src/test/scala/unit/kafka/server/`
- Example: `KafkaApisTest.scala` (line 107)
- Pattern:
  ```scala
  class KafkaApisTest extends Logging {
    private val requestChannel: RequestChannel = mock(classOf[RequestChannel])
    private val replicaManager: ReplicaManager = mock(classOf[ReplicaManager])
    // ... setup mock dependencies ...

    @Test
    def testCreateTopicsWithAuthorizer(): Unit = {
      val authorizer: Authorizer = mock(classOf[Authorizer])
      // ... test logic ...
    }
  }
  ```

#### Integration Tests
- Location: `core/src/test/scala/integration/kafka/api/` or `core/src/test/scala/integration/kafka/server/`
- Example: `PlaintextAdminIntegrationTest.scala`
- Pattern:
  ```scala
  class PlaintextAdminIntegrationTest extends IntegrationTestHarness {
    override def brokerCount: Int = 3

    @Test
    @Timeout(120)
    def testCreateTopic(): Unit = {
      createTopic("test-topic")
      // ... assertions ...
    }
  }
  ```

#### Mocking Dependencies
- Use Mockito for complex dependencies:
  ```java
  @ExtendWith(MockitoExtension.class)
  public class MyTest {
    @Mock
    private SomeDependency dependency;

    @Test
    void testSomething() {
      when(dependency.method()).thenReturn(value);
      // ... test logic ...
      verify(dependency, times(1)).method();
    }
  }
  ```

#### Configuration in Tests
- Use `TestUtils.createBrokerConfig()` to create test configurations:
  ```scala
  val props = TestUtils.createBrokerConfig(brokerId, zkConnect)
  val config = KafkaConfig.fromProps(props)
  ```

## 5. Configuration System

Kafka's configuration system is hierarchical and flexible, supporting both static and dynamic configurations:

### Configuration Hierarchy

1. **Dynamic Broker Config (Highest Priority)**
   - Stored in ZooKeeper: `/configs/brokers/{brokerId}`
   - Per-broker specific settings
   - Can be updated without restart

2. **Dynamic Default Broker Config**
   - Stored in ZooKeeper: `/configs/brokers/<default>`
   - Cluster-wide defaults for dynamic configs
   - Can be updated without restart

3. **Static Broker Config**
   - From `server.properties` file passed at startup
   - Cannot be changed without restart

4. **Default Configuration (Lowest Priority)**
   - Hardcoded defaults in ConfigDef

### Configuration Definition System

1. **`AbstractKafkaConfig.CONFIG_DEF`** (`server/src/main/java/org/apache/kafka/server/config/AbstractKafkaConfig.java`, line 45)
   - Master ConfigDef that merges all configuration sources:
     ```java
     public static final ConfigDef CONFIG_DEF = Utils.mergeConfigs(Arrays.asList(
         RemoteLogManagerConfig.configDef(),
         ZkConfigs.CONFIG_DEF,
         ServerConfigs.CONFIG_DEF,
         KRaftConfigs.CONFIG_DEF,
         SocketServerConfigs.CONFIG_DEF,
         ReplicationConfigs.CONFIG_DEF,
         // ... more configs ...
         DelegationTokenManagerConfigs.CONFIG_DEF,
         PasswordEncoderConfigs.CONFIG_DEF
     ));
     ```

2. **Individual ConfigDef Modules**
   - Each module defines its own configs:
     - `ServerConfigs.CONFIG_DEF`: General broker configs (broker.id, num.io.threads, etc.)
     - `ZkConfigs.CONFIG_DEF`: ZooKeeper connection configs
     - `SocketServerConfigs.CONFIG_DEF`: Network/listener configs
     - `ReplicationConfigs.CONFIG_DEF`: Replication configs
     - `LogConfig.SERVER_CONFIG_DEF`: Log segment configs
     - `QuotaConfigs.CONFIG_DEF`: Quota configs
     - etc.

3. **ConfigDef Structure**
   - Defines configuration using fluent builder pattern:
   ```java
   new ConfigDef()
       .define(CONFIG_NAME, Type.STRING, DEFAULT_VALUE, Validator,
               Importance.HIGH, "Documentation string")
   ```
   - **Type**: STRING, INT, LONG, BOOLEAN, LIST, DOUBLE, PASSWORD, CLASS
   - **Validator**: Range validators (atLeast, between), custom validators, etc.
   - **Importance**: HIGH, MEDIUM, LOW
   - **Reconfigurable**: Marked with `Reconfigurable` interface

### Key Configuration Classes

1. **`kafka.server.KafkaConfig`** (`core/src/main/scala/kafka/server/KafkaConfig.scala`, line 181)
   - Extends `AbstractKafkaConfig`
   - Constructor: `new KafkaConfig(props: java.util.Map[_, _])`
   - **Key Methods:**
     - `fromProps(props: Properties): KafkaConfig`: Factory method
     - `getString(key: String): String`: Get string config value
     - `getInt(key: String): Int`: Get integer config value
     - `getBoolean(key: String): Boolean`: Get boolean config value
     - etc.
   - **Key Properties:**
     - `brokerId`: Broker identifier
     - `zkConnect`: ZooKeeper connection string
     - `listeners`: Network endpoints to listen on
     - `advertisedListeners`: Endpoints advertised to clients
     - `logDirs`: Directories for log storage
     - `numPartitions`: Default partition count for auto-created topics
     - `defaultReplicationFactor`: Default replication factor
     - etc.

2. **`DynamicBrokerConfig`** (`core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`, line 204)
   - Manages dynamic configuration updates
   - **Key Properties:**
     - `AllDynamicConfigs`: Set of configs that can be updated dynamically
     - `DynamicSecurityConfigs`: SSL/SASL configs that can be updated
     - `DynamicLogConfig.ReconfigurableConfigs`: Log-related configs
     - etc.
   - **Key Methods:**
     - `validateConfigs()`: Validate config changes
     - `updateConfig()`: Apply config updates

### Configuration Validation

1. **ConfigDef Validation**
   - Type checking: Ensures values match declared type
   - Range validation: Checks min/max values
   - Custom validators: Plugin custom validation logic
   - Example from ServerConfigs:
   ```java
   .define(ServerConfigs.NUM_IO_THREADS_CONFIG, INT,
           NUM_IO_THREADS_DEFAULT, atLeast(1),
           HIGH, NUM_IO_THREADS_DOC)
   ```

2. **Dynamic Config Validation** (`DynamicBrokerConfig.validateConfigs()`, line 142)
   - Checks if configs are reconfigurable
   - Validates listener-specific configs
   - Ensures password values are handled correctly

3. **Topic Config Validation**
   - Uses `LogConfig.SERVER_CONFIG_DEF` for topic-level configs
   - Validates during topic creation in `ZkAdminManager.createTopics()`

## 6. Adding a New Broker Configuration

To add a new broker configuration parameter, follow these steps:

### Step 1: Define Configuration in ConfigDef

**File**: Identify the appropriate configuration module based on the config's purpose:
- General broker configs → `server/src/main/java/org/apache/kafka/server/config/ServerConfigs.java`
- ZooKeeper configs → `server/src/main/java/org/apache/kafka/server/config/ZkConfigs.java`
- Network/listener configs → `server/src/main/java/org/apache/kafka/network/SocketServerConfigs.java`
- Replication configs → `server/src/main/java/org/apache/kafka/server/config/ReplicationConfigs.java`
- Log configs → `storage/src/main/java/org/apache/kafka/storage/internals/log/LogConfig.java`
- Custom module for your feature

**Example: Add a new broker config in ServerConfigs.java**

```java
public class ServerConfigs {
    // 1. Define config name constant
    public static final String MY_NEW_CONFIG = "my.new.config";

    // 2. Define default value
    public static final int MY_NEW_CONFIG_DEFAULT = 1000;

    // 3. Define documentation
    public static final String MY_NEW_CONFIG_DOC = "Description of what this config does. " +
            "Include details about valid ranges and usage patterns.";

    // 4. Add to CONFIG_DEF
    public static final ConfigDef CONFIG_DEF = new ConfigDef()
        // ... existing configs ...
        .define(MY_NEW_CONFIG,           // config name
                ConfigDef.Type.INT,       // type (STRING, INT, LONG, BOOLEAN, LIST, etc.)
                MY_NEW_CONFIG_DEFAULT,    // default value
                atLeast(0),              // validator (optional: range, custom validators)
                ConfigDef.Importance.MEDIUM,  // importance level
                MY_NEW_CONFIG_DOC);       // documentation
    // ... other configs ...
}
```

### Step 2: Add Configuration Property to KafkaConfig

**File**: `core/src/main/scala/kafka/server/KafkaConfig.scala`

Add a property to access your config:

```scala
class KafkaConfig private(doLog: Boolean, val props: util.Map[_, _])
  extends AbstractKafkaConfig(KafkaConfig.configDef, props, Utils.castToStringObjectMap(props), doLog) {

  // Add your config property:
  val myNewConfig: Int = getInt(ServerConfigs.MY_NEW_CONFIG)
}
```

### Step 3: Determine if Config is Dynamically Reconfigurable

**Decision**: Can this config be updated without broker restart?

**If YES** (Dynamic config):

1. **Mark as Reconfigurable in ConfigDef**:
   - Implement `Reconfigurable` interface in relevant component
   - Override `reconfigure()` method to handle updates

2. **Add to Dynamic Config Set**:
   - File: `core/src/main/scala/kafka/server/DynamicBrokerConfig.scala`
   - Add to appropriate ReconfigurableConfigs set:
   ```scala
   object DynamicBrokerConfig {
     // For socket-related configs:
     private val DynamicSocketConfigs = Set(MY_NEW_CONFIG)

     // For log-related configs:
     // Add to DynamicLogConfig.ReconfigurableConfigs

     // Then include in AllDynamicConfigs:
     val AllDynamicConfigs = DynamicSecurityConfigs ++
       LogCleaner.ReconfigurableConfigs ++
       DynamicLogConfig.ReconfigurableConfigs ++
       // ... include your set ...
       DynamicSocketConfigs // Add here
   }
   ```

3. **Implement Configuration Handler**:
   - File: `core/src/main/scala/kafka/server/ConfigHandler.scala`
   - Update `BrokerConfigHandler.processConfigChanges()` to apply your config:
   ```scala
   class BrokerConfigHandler(...) extends ConfigHandler {
     def processConfigChanges(brokerId: String, properties: Properties): Unit = {
       // Handle MY_NEW_CONFIG change
       properties.getProperty(ServerConfigs.MY_NEW_CONFIG) match {
         case value if value != null =>
           val newValue = value.toInt
           // Apply the configuration change
           // Example: kafkaConfig.dynamicConfig.updateConfig(...)
         case _ => // Config not changed
       }
     }
   }
   ```

**If NO** (Static config only):
- No changes needed beyond steps 1-2
- Document that it requires broker restart

### Step 4: Add Validation (If Needed)

**File**: Validation logic depends on config type

For custom validation:

```java
// In ServerConfigs.java, provide custom validator:
public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(MY_NEW_CONFIG,
            ConfigDef.Type.INT,
            MY_NEW_CONFIG_DEFAULT,
            new ConfigDef.Validator() {  // Custom validator
                @Override
                public void ensureValid(String name, Object value) {
                    Integer val = (Integer) value;
                    if (val < 0 || val > 10000) {
                        throw new ConfigException(name, value,
                            "Must be between 0 and 10000");
                    }
                }
            },
            ConfigDef.Importance.MEDIUM,
            MY_NEW_CONFIG_DOC);
```

### Step 5: Add Tests

#### Unit Test for Configuration Parsing

**File**: `core/src/test/scala/unit/kafka/server/KafkaConfigTest.scala`

```scala
class KafkaConfigTest {
  @Test
  def testMyNewConfig(): Unit = {
    val props = new Properties()
    props.put(ServerConfigs.MY_NEW_CONFIG, "500")
    val config = KafkaConfig.fromProps(props)
    assertEquals(500, config.myNewConfig)
  }

  @Test
  def testMyNewConfigValidation(): Unit = {
    val props = new Properties()
    props.put(ServerConfigs.MY_NEW_CONFIG, "-1")  // Invalid
    assertThrows(classOf[ConfigException],
      () => KafkaConfig.fromProps(props))
  }
}
```

#### Integration Test for Dynamic Update (If Applicable)

**File**: `core/src/test/scala/integration/kafka/server/DynamicBrokerReconfigurationTest.scala`

```scala
class DynamicBrokerReconfigurationTest extends IntegrationTestHarness {
  @Test
  def testMyNewConfigDynamicUpdate(): Unit = {
    // Get current value
    val adminClient = createAdminClient()
    val initialConfigs = adminClient.describeConfigs(
      Seq(broker0Resource).asJava).all().get()

    // Update config dynamically
    val configMap = Seq((ServerConfigs.MY_NEW_CONFIG, "750"))
    adminClient.alterConfigs(Map(broker0Resource -> new ConfigResource(...)))

    // Verify update
    val updatedConfigs = adminClient.describeConfigs(...)...
    assertEquals("750", updatedConfigs.get(ServerConfigs.MY_NEW_CONFIG))
  }
}
```

### Step 6: Update Documentation

Add documentation for your configuration:

1. **Configuration File Comments**:
   - Update sample `config/server.properties` if applicable
   - Add comment explaining the parameter

2. **Official Documentation**:
   - Update Kafka documentation website
   - Add to broker configuration reference page

3. **Migration Guide** (if replacing existing config):
   - Document deprecation path
   - Provide migration examples

### Step 7: Build and Test

```bash
# Build the project (specific module)
./gradlew core:compileScala

# Run unit tests
./gradlew core:test -k KafkaConfigTest

# Run integration tests
./gradlew core:integrationTest -k DynamicBrokerReconfigurationTest
```

### Example: Complete Implementation

For a new config `broker.processing.timeout.ms`:

**1. ServerConfigs.java**:
```java
public static final String BROKER_PROCESSING_TIMEOUT_MS_CONFIG = "broker.processing.timeout.ms";
public static final int BROKER_PROCESSING_TIMEOUT_MS_DEFAULT = 30000;
public static final String BROKER_PROCESSING_TIMEOUT_MS_DOC =
    "The maximum time in milliseconds for broker to process a request before timing out.";

public static final ConfigDef CONFIG_DEF = new ConfigDef()
    .define(BROKER_PROCESSING_TIMEOUT_MS_CONFIG, INT,
            BROKER_PROCESSING_TIMEOUT_MS_DEFAULT,
            atLeast(1),
            MEDIUM,
            BROKER_PROCESSING_TIMEOUT_MS_DOC);
```

**2. KafkaConfig.scala**:
```scala
val brokerProcessingTimeoutMs: Int =
  getInt(ServerConfigs.BROKER_PROCESSING_TIMEOUT_MS_CONFIG)
```

**3. Usage in BrokerServer**:
```scala
val timeout = config.brokerProcessingTimeoutMs
// Use timeout in request processing
```

**4. Test in KafkaConfigTest.scala**:
```scala
@Test
def testBrokerProcessingTimeoutMs(): Unit = {
  val props = new Properties()
  props.put(ServerConfigs.BROKER_PROCESSING_TIMEOUT_MS_CONFIG, "60000")
  val config = KafkaConfig.fromProps(props)
  assertEquals(60000, config.brokerProcessingTimeoutMs)
}
```
