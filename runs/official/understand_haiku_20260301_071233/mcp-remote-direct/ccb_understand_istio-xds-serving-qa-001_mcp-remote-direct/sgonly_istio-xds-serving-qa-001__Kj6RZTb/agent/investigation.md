# Istio Pilot xDS Serving Architecture

## Q1: Config Ingestion Pipeline

### CRD Watching and Ingestion

Pilot watches Kubernetes custom resources (VirtualService, DestinationRule, ServiceEntry, etc.) through a multi-layered config management system:

1. **ConfigStoreController Interface** (`pilot/pkg/model/config.go:188`)
   - Extends `ConfigStore` interface to add event handling capabilities
   - Defines `RegisterEventHandler(kind config.GroupVersionKind, handler EventHandler)` for registering config change handlers
   - Defines `Run(stop <-chan struct{})` to process events until shutdown signal
   - Defines `HasSynced() bool` to track initial synchronization completion

2. **Memory-based Controller Implementation** (`pilot/pkg/config/memory/controller.go:28-40`)
   - `Controller` struct implements `ConfigStoreController` interface
   - Uses `Monitor` (event dispatcher) to propagate config changes
   - When configs are Create/Update/Delete, it calls `monitor.ScheduleProcessEvent()` to queue config change events
   - Events are dispatched asynchronously to registered handlers with (old, new, event type)

3. **Event Processing Pipeline** (`pilot/pkg/config/memory/monitor.go:45-100`)
   - `configStoreMonitor` manages handlers per config type
   - Buffered event channel (`eventCh`) queues config changes (default buffer: 100)
   - `ScheduleProcessEvent()` either:
     - Handles events synchronously (SyncMonitor) for testing
     - Queues events asynchronously for production use
   - `processConfigEvent()` calls all registered handlers for that config type

### Event Handler Chain and xDS Push Triggering

4. **Event Handler Registration to xDS** (`pilot/pkg/bootstrap/server.go:860-902`)
   - `DiscoveryServer.ConfigUpdate()` is registered as an event handler with the config controller
   - When a config event occurs, it receives: previous config, current config, and event type (Add/Update/Delete)
   - `ConfigUpdate()` creates a `PushRequest` with:
     - `ConfigsUpdated`: set of affected config keys (Kind, Name, Namespace)
     - `Full`: boolean indicating full vs. incremental push
     - `Reason`: reason for the push (ConfigUpdate, etc.)

5. **Debouncing and Push Queuing** (`pilot/pkg/xds/discovery.go:297-327`)
   - `ConfigUpdate()` sends `PushRequest` to `pushChannel` (buffered channel)
   - `handleUpdates()` goroutine runs debounce logic on `pushChannel`
   - Debounce waits for:
     - `DebounceAfter`: minimum quiet time before processing events
     - `debounceMax`: maximum delay before forcing a push
   - Once debounce completes, `Push()` is called with merged `PushRequest`

### Aggregate Service Registry

6. **Aggregate Config Controller** (`pilot/pkg/config/aggregate/config.go:63-82`)
   - `MakeCache()` creates an aggregate `ConfigStoreController` from multiple stores
   - Merges multiple config sources (Kubernetes CRDs, file-based, etc.)
   - `storeCache` type wraps the underlying stores
   - Deduplicates configs across stores by `NamespacedName`
   - Each config type maps to one or more underlying stores via `stores map[config.GroupVersionKind][]model.ConfigStore`
   - `Get()` returns first match from stores in order
   - `List()` aggregates and deduplicates configs from all stores

---

## Q2: Internal Service Model

### Key Internal Model Types

1. **Service Struct** (`pilot/pkg/model/service.go:69-123`)
   - Represents an Istio service (e.g., `catalog.mystore.com:8080`)
   - Fields:
     - `Hostname`: fully qualified service name
     - `Ports`: list of listening ports
     - `ClusterVIPs`: load balancer IPs per cluster
     - `Resolution`: how instances are resolved (Static, DNS, Passthrough)
     - `MeshExternal`: true for ServiceEntry-defined services
     - `Attributes`: namespace, labels, service accounts for RBAC
   - Platform adapters populate these fields from platform resources

2. **PushContext** (`pilot/pkg/model/push_context.go:206-279`)
   - Immutable snapshot of mesh configuration state
   - Regenerated (partially or fully) on each config push
   - Contains multiple configuration indexes:
     - `ServiceIndex`: services indexed by various fields (FQDN, namespace, etc.)
     - `virtualServiceIndex`: VirtualServices by destination host
     - `destinationRuleIndex`: DestinationRules indexed by host
     - `gatewayIndex`: Gateway configurations
     - `sidecarIndex`: Sidecar configurations
     - `envoyFiltersByNamespace`: EnvoyFilters for traffic manipulation
     - `wasmPluginsByNamespace`: WASM plugins
     - `AuthnPolicies`: authentication policy collection
     - `AuthzPolicies`: authorization policy collection
     - `Telemetry`: telemetry configurations
     - `ProxyConfigs`: proxy-specific configurations
   - Lock-free lookups due to being immutable snapshot

### Kubernetes Service to Internal Model Conversion

3. **Service Registry** (`pilot/pkg/serviceregistry/`)
   - Kubernetes service controller watches `v1.Service` objects
   - Converts Kubernetes Service to internal `Service`:
     - Service name → `Hostname` (e.g., "svc-name.default.svc.cluster.local")
     - Service ports → `Ports` list
     - Service ClusterIP → `ClusterVIPs`
     - Service labels → `Attributes.Labels`
   - Registers handlers to notify xDS on service changes
   - Maintains separate registries per provider (Kubernetes, Consul, etc.)

### ServiceEntry vs. Kubernetes Service

4. **ServiceEntry Model** (`pilot/pkg/model/`)
   - ServiceEntry resources define external services explicitly
   - Key differences from Kubernetes Service:
     - `MeshExternal`: true for ServiceEntry
     - `Endpoints`: explicitly defined hosts/ports (not auto-discovered)
     - `Resolution`: can be DNS, Passthrough, or Static
     - No automatic pod discovery
   - Stored in config store as `kind.ServiceEntry`
   - Retrieved via config store queries

### PushContext Initialization

5. **PushContext Init** (`pilot/pkg/xds/discovery.go:507-522`)
   - Called via `initPushContext()` when full push is triggered
   - Calls `push.InitContext(s.Env, oldPushContext, req)` with:
     - `Environment`: contains config store and service registries
     - `oldPushContext`: previous state for delta computation
     - `PushRequest`: identifies what changed
   - `InitContext()` builds all indexes by querying config store and service registries
   - Result stored on `Environment` and accessible via `s.Env.PushContext()`

---

## Q3: xDS Generation and Dispatch

### DiscoveryServer and Event Handling

1. **DiscoveryServer Struct** (`pilot/pkg/xds/discovery.go:63-135`)
   - Pilot's gRPC server implementing Envoy xDS APIs
   - Key components:
     - `Generators`: map[string]XdsResourceGenerator - registered generators for each TypeUrl
     - `pushChannel`: buffered channel receiving config changes
     - `pushQueue`: queue after debouncing, before actual push
     - `adsClients`: map of connected proxy connections
     - `Cache`: XDS resource cache (type→resources)
     - `DebounceOptions`: controls push debouncing
     - `InboundUpdates`/`CommittedUpdates`: metrics for config changes

2. **Push Flow** (`pilot/pkg/xds/discovery.go:254-282`)
   - Full push:
     - `Push(req)` calls `initPushContext()` to rebuild configuration indexes
     - Creates new `PushContext` with all config recomputed
     - Calls `AdsPushAll(req)` to push to all connected proxies
   - Incremental push:
     - Uses current `globalPushContext()`
     - Clears cache entries for changed configs via `dropCacheForRequest()`
     - Calls `AdsPushAll(req)` with same push context

3. **Config Change to Push** (`pilot/pkg/xds/discovery.go:297-327`)
   - `ConfigUpdate(req)` entry point from config store handlers
   - Sends `PushRequest` to `pushChannel`
   - `handleUpdates()` goroutine debounces via `debounce()` helper
   - Debounce merges rapid events and enforces min/max delays
   - After debounce, `Push()` is called with merged request

### Generator Architecture and Dispatch

4. **Generator Registration** (`pilot/pkg/bootstrap/discovery.go:29-57`)
   - Initialize generators in `InitGenerators()`:
     - `CdsGenerator`: generates Cluster resources
     - `EdsGenerator`: generates Endpoint resources
     - `LdsGenerator`: generates Listener resources
     - `RdsGenerator`: generates Route resources
     - Others: StatusGenerator, WorkloadGenerator, WasmPluginGenerator, etc.
   - Stored in `DiscoveryServer.Generators` map by TypeUrl:
     - `s.Generators["cds"] = CdsGenerator{ConfigGenerator: cg}`
     - `s.Generators["eds"] = EdsGenerator{...}`
     - etc.

5. **Generator Selection and Dispatch** (`pilot/pkg/xds/xdsgen.go:67-91`)
   - `findGenerator(typeURL string, con *Connection)` selects appropriate generator:
     - Priority 1: Generator specific to connection's metadata + type (`Metadata.Generator/typeURL`)
     - Priority 2: Generator specific to proxy type (`sidecar/cds`, `router/cds`)
     - Priority 3: Default generator for type (`cds`, `eds`)
     - Fallback: Use proxy's `XdsResourceGenerator` or default "api" generator
   - Allows per-proxy or per-proxy-type custom generators

6. **pushXds Function** (`pilot/pkg/xds/xdsgen.go:96-179`)
   - Generates and sends xDS response for a watched resource
   - Flow:
     1. `findGenerator()` selects generator for TypeUrl
     2. Generator's `Generate(proxy, watched_resource, push_request)` called
     3. Returns `Resources` (array of xDS resources) and `XdsLogDetails`
     4. Wraps in `DiscoveryResponse` with:
        - `TypeUrl`: resource type
        - `VersionInfo`: push version string
        - `Nonce`: unique identifier for this response
        - `ControlPlane`: istiod instance info
     5. Sends via `xds.Send(con, resp)` over gRPC stream

### XdsResourceGenerator Interface

7. **Generator Interface** (`pilot/pkg/model/context.go:276-284`)
   - `XdsResourceGenerator.Generate()`:
     - Input: `Proxy` (client info), `WatchedResource` (what client wants), `PushRequest` (what changed)
     - Output: `Resources` ([]Resource), `XdsLogDetails`, `error`
     - Resource contains Envoy protobuf + metadata
   - `XdsDeltaResourceGenerator` extends with `GenerateDeltas()` for incremental updates

---

## Q4: Resource Translation

### DestinationRule to CDS (Cluster Discovery Service)

1. **DestinationRule Processing** (`pilot/pkg/xds/cds.go:26-46`)
   - `CdsGenerator` struct wraps `ConfigGenerator`
   - Implements `XdsResourceGenerator` interface
   - `Generate()` calls `ConfigGenerator.BuildClusters(proxy, request)`

2. **Cluster Building** (`pilot/pkg/networking/core/cluster.go:56-213`)
   - `BuildClusters()` creates Envoy Cluster resources:
     - One default cluster per service port
     - Additional subset clusters from DestinationRule
   - For each service:
     1. Create base Cluster with service endpoints
     2. Query `PushContext.DestinationRule(hostname)` for traffic policies
     3. Apply DestinationRule to cluster via `applyDestinationRule()`:
        - Connection pool settings (TCP/HTTP)
        - Load balancer algorithm (Round Robin, etc.)
        - Outlier detection
        - TLS settings
     4. Create subset clusters from DestinationRule subsets
   - Stores in `Cluster` resource with Envoy configuration

3. **CDS Cache and Delta** (`pilot/pkg/xds/cds.go:66-140`)
   - `cdsNeedsPush()` determines if push needed:
     - Full push required for CDS
     - Skips on endpoint-only updates
     - Checks `ConfigsUpdated` for DestinationRule, Gateway, VirtualService
   - `GenerateDeltas()` for incremental: only regenerate changed services

### VirtualService to RDS (Route Discovery Service)

4. **VirtualService Processing** (`pilot/pkg/xds/rds.go:24-70`)
   - `RdsGenerator` struct wraps `ConfigGenerator`
   - `Generate()` calls `ConfigGenerator.BuildHTTPRoutes(proxy, request, routeNames)`

5. **Route Building** (`pilot/pkg/networking/core/httproute.go` and `route/route.go:377-381`)
   - `BuildHTTPRoutes()` creates Envoy RouteConfiguration resources:
     - Groups routes by port/listener
     - For each VirtualService:
       - Extract hosts from spec
       - Match against service registry
       - Build http_routes via `BuildHTTPRoutesForVirtualService()`
   - `BuildHTTPRoutesForVirtualService()` processes VirtualService spec:
     - For each match/route rule:
       - Match conditions (URI, headers, etc.)
       - Destination cluster (DestinationRule subset)
       - Retries, timeouts, circuit breakers
       - Load balancer configuration
   - Returns Envoy `RouteConfiguration` with virtual hosts and routes

6. **RDS Cache and Push** (`pilot/pkg/xds/rds.go:44-62`)
   - `rdsNeedsPush()` determines if push needed:
     - Full push required for RDS
     - Checks `ConfigsUpdated` for VirtualService, DestinationRule, Gateway
   - Skips on endpoint-only or authorization-only updates

### Endpoints to EDS (Endpoint Discovery Service)

7. **Endpoint Discovery** (`pilot/pkg/xds/eds.go:82-145`)
   - `EdsGenerator` uses optimized in-memory endpoint storage
   - `EndpointIndex`: maintains endpoint shards per service/namespace
   - `Generate()` calls `buildEndpoints(proxy, request, watched_resource)`
   - Creates `ClusterLoadAssignment` resources:
     - Service endpoints organized by locality
     - Health check endpoints
     - Priority/weight for traffic distribution

8. **Endpoint Updates** (`pilot/pkg/xds/eds.go:51-58`)
   - Service controller registers handler to watch Pod/Endpoint changes
   - On Pod creation/deletion: `EndpointIndex.UpdateServiceEndpoints()`
   - Triggers incremental push if EDS debounce enabled
   - `ConfigUpdate()` with ServiceEntry config updates

### ConfigGenerator Interface

9. **Core ConfigGenerator** (`pilot/pkg/networking/core/configgen.go:27-54`)
   - Defines all xDS generation methods:
     - `BuildListeners(node, push)`: LDS output
     - `BuildClusters(node, request)`: CDS output (clusters)
     - `BuildHTTPRoutes(node, request, names)`: RDS output (routes)
     - `BuildDeltaClusters()`: incremental CDS
     - `BuildExtensionConfiguration()`: ECDS (extension config)
     - `BuildNameTable()`: DNS name table for resolution
   - `ConfigGeneratorImpl` implements interface with caching

### Listener Generation (LDS)

10. **Listener Building** (`pilot/pkg/xds/lds.go:27-100`)
    - `LdsGenerator` wraps `ConfigGenerator.BuildListeners()`
    - Creates Envoy `Listener` resources for:
      - Inbound listeners (sidecar)
      - Outbound listeners (sidecar)
      - Gateway listeners (for Gateways)
    - Filters applied via EnvoyFilters
    - Routes attached to HttpConnectionManager

---

## Evidence

### Key File References

**Config Ingestion:**
- `pilot/pkg/model/config.go:188-201` - ConfigStoreController interface
- `pilot/pkg/config/memory/controller.go:28-65` - Controller implementation
- `pilot/pkg/config/memory/monitor.go:45-100` - Event monitor
- `pilot/pkg/config/aggregate/config.go:63-82` - Aggregate config controller
- `pilot/pkg/bootstrap/configcontroller.go:116-122` - Config controller setup

**Event to Push:**
- `pilot/pkg/xds/discovery.go:297-327` - ConfigUpdate and debouncing
- `pilot/pkg/xds/discovery.go:254-282` - Push method
- `pilot/pkg/bootstrap/server.go:860-902` - Event handler registration

**Internal Model:**
- `pilot/pkg/model/service.go:69-123` - Service struct
- `pilot/pkg/model/push_context.go:206-279` - PushContext struct
- `pilot/pkg/model/controller.go:23-55` - Controller interface
- `pilot/pkg/xds/discovery.go:507-522` - PushContext initialization

**xDS Generation:**
- `pilot/pkg/xds/discovery.go:63-135` - DiscoveryServer struct
- `pilot/pkg/bootstrap/discovery.go:29-57` - Generator registration
- `pilot/pkg/xds/xdsgen.go:67-91` - Generator selection
- `pilot/pkg/xds/xdsgen.go:96-179` - pushXds function
- `pilot/pkg/model/context.go:276-284` - XdsResourceGenerator interface

**Resource Translation:**
- `pilot/pkg/xds/cds.go:26-46` - CdsGenerator
- `pilot/pkg/networking/core/cluster.go:56-213` - BuildClusters
- `pilot/pkg/xds/rds.go:24-70` - RdsGenerator
- `pilot/pkg/networking/core/route/route.go:377-381` - BuildHTTPRoutesForVirtualService
- `pilot/pkg/xds/eds.go:82-145` - EdsGenerator
- `pilot/pkg/xds/lds.go:27-100` - LdsGenerator
- `pilot/pkg/networking/core/configgen.go:27-54` - ConfigGenerator interface
