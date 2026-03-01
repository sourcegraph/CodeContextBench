# Istio Pilot xDS Serving Architecture

## Q1: Config Ingestion Pipeline

### How Pilot watches and ingests Kubernetes custom resources

**CRD Watching and Event Handling:**

Pilot uses **`pilot/pkg/config/kube/crdclient/client.go:Client`** as the primary Kubernetes controller for watching CRDs. The `Client` type implements the `ConfigStoreController` interface and uses Kubernetes informers to watch custom resources like VirtualService, DestinationRule, ServiceEntry, and Gateway.

- **File**: `pilot/pkg/config/kube/crdclient/client.go:99-120`
- **Implementation**: The `Client` maintains a map of handlers per resource type (`handlers map[config.GroupVersionKind][]model.EventHandler`) and uses the Kubernetes dynamic informer framework with typed clients for performance
- **Key Method**: The `Client` registers event handlers for each supported schema and queues config change events through `queue.Instance`

**Event Delivery to xDS Layer:**

Config change events flow through:
1. **Resource Update Callbacks**: Services are notified of config changes through the `model.EventHandler` interface
2. **ConfigStoreController**: The `Client` implements `pilot/pkg/model/controller.go:ConfigStoreController` interface which includes:
   - `AppendServiceHandler()` - registers handlers for service changes
   - The handlers are triggered when resources are added/updated/deleted

**Aggregate Service Registry (Multi-Source Merging):**

- **File**: `pilot/pkg/config/aggregate/config.go`
- **MakeCache() function**: Creates an aggregate config store from multiple sources (file-based, Kubernetes, etc.)
- **Store aggregation**: `pilot/pkg/config/aggregate/config.go:84-92` defines the aggregate `store` type which:
  - Maintains `stores map[config.GroupVersionKind][]model.ConfigStore` mapping config types to multiple stores
  - Returns configs from the first store that has them via `Get()` method
  - Merges schemas from all sources into a unified collection

**Flow to DiscoveryServer:**

1. Config changes trigger handlers registered via `AppendServiceHandler()`
2. The `DiscoveryServer` (in `pilot/pkg/xds/discovery.go`) is notified through its `ConfigUpdate()` method
3. Kubernetes events are also fed through `pilot/pkg/xds/discovery.go:SvcUpdate()` and `EDSUpdate()` for service and endpoint updates

---

## Q2: Internal Service Model

### Translation of platform-specific resources to internal model

**Key Internal Model Types:**

1. **Service Type** (`pilot/pkg/model/service.go:69-100`):
   - Represents an Istio service with FQDN (hostname), ports, and optional virtual IP
   - Fields: `Hostname`, `Ports`, `ClusterVIPs`, `ServiceAccounts`, `Attributes`
   - Hostname examples: `catalog.mystore.com`, `service-name.default.svc.cluster.local`

2. **IstioEndpoint Type** (defined in model package):
   - Represents individual service instances (pods/VMs)
   - Contains address, port, labels, and metadata for traffic policies

3. **ServiceEntry Integration**:
   - ServiceEntry is converted to the same `Service` model
   - Difference from Kubernetes Service: ServiceEntry allows defining external services with arbitrary IPs and hostnames
   - Both are indexed uniformly in `PushContext` for route/cluster generation

### PushContext - Central Configuration Index

**File**: `pilot/pkg/model/push_context.go`

The `PushContext` is the core in-memory model representing the complete configuration state at a point in time:

1. **serviceIndex** (push_context.go:64-89):
   - `public []*Service` - services visible to all namespaces (exportTo: "*")
   - `privateByNamespace map[string][]*Service` - namespace-local services (exportTo: ".")
   - `exportedToNamespace map[string][]*Service` - selectively exported services
   - `HostnameAndNamespace map[host.Name]map[string]*Service` - fast lookup by hostname

2. **VirtualService and DestinationRule Indexes**:
   - `virtualServiceIndex` maintains VirtualServices by hostname/namespace
   - `destinationRuleIndex` maintains DestinationRules by service hostname
   - These are keyed for O(1) lookup during cluster and route generation

3. **Endpoint Storage**:
   - `EndpointIndex` (in `model/context.go:140`) - global per-server endpoint storage
   - Sharded by service and namespace: `UpdateServiceEndpoints()` called from `pilot/pkg/xds/discovery.go:EDSUpdate()`

4. **Initialization**:
   - **File**: `pilot/pkg/xds/discovery.go:507-523`
   - `initPushContext()` builds a new `PushContext` from current config store state
   - Indexes all services, resolves DestinationRules and VirtualServices
   - Computes SidecarScope for each proxy (which services are visible to a proxy)

---

## Q3: xDS Generation and Dispatch

### Configuration Update Reception and Debouncing

**Config Update Entry Point:**
- **File**: `pilot/pkg/xds/discovery.go:298-318`
- **Method**: `DiscoveryServer.ConfigUpdate(req *model.PushRequest)`
- Pushes to `pushChannel` - a buffered channel (size 10) for debouncing

**Debouncing Mechanism:**
- **File**: `pilot/pkg/xds/discovery.go:325-412`
- **debounce() function**: Implements "quiet time" based debouncing:
  - `DebounceAfter`: minimum time to wait for stability (default 100ms)
  - `debounceMax`: maximum wait even if changes continue (default 10s)
  - Merges rapid config changes via `PushRequest.Merge()`
- After debounce, sends to `pushQueue` via `s.Push()`

### Generator Architecture

**Generator Registration:**
- **File**: `pilot/pkg/xds/discovery.go:73`
- `Generators map[string]model.XdsResourceGenerator` - maps generator ID to implementation
- Default generators registered for each xDS type (CDS, EDS, LDS, RDS, SDS, etc.)

**Generator Selection - findGenerator():**
- **File**: `pilot/pkg/xds/xdsgen.go:67-91`
- **Lookup priority**:
  1. `Generators[proxy.Metadata.Generator+"/"+typeURL]` - proxy-specific generator
  2. `Generators[string(proxy.Type)+"/"+typeURL]` - type-specific (Router, SidecarProxy, etc.)
  3. `Generators[typeURL]` - default generator for resource type
  4. Falls back to `proxy.XdsResourceGenerator` or "api" generator

**Generator Interface:**
- **File**: `pilot/pkg/model/config.go` (defines `XdsResourceGenerator`)
- Implemented by:
  - `CdsGenerator` - clusters (pilot/pkg/xds/cds.go:26)
  - `EdsGenerator` - endpoints (pilot/pkg/xds/eds.go)
  - `LdsGenerator` - listeners (pilot/pkg/xds/lds.go:27)
  - `RdsGenerator` - routes (pilot/pkg/xds/rds.go:24)
  - `SecretGen` - secrets/certs (pilot/pkg/xds/sds.go:110)

### XDS Generation and Dispatch Flow

**pushXds() - Resource Generation:**
- **File**: `pilot/pkg/xds/xdsgen.go:96-179`
- Called from `pushConnection()` for each watched resource type
- Steps:
  1. Find generator via `findGenerator(typeURL, con)`
  2. Call `generator.Generate(proxy, watchedResource, pushRequest)`
  3. Generate may return empty if no changes required (optimization)
  4. Build `DiscoveryResponse` with generated resources
  5. Send via `xds.Send(con, resp)`

**Push Order (Ordered Delivery):**
- **File**: `pilot/pkg/xds/ads.go:502-514`
- `PushOrder = [ClusterType, EndpointType, ListenerType, RouteType, SecretType, ...]`
- Ensures CDS arrives before RDS (routes need cluster references)
- Ensures EDS before LDS (listeners may reference endpoints)

**Push to Connected Proxies:**
- **File**: `pilot/pkg/xds/ads.go:562-594`
- `AdsPushAll(req)` queues push to all connected proxies via `pushQueue.Enqueue()`
- Each proxy processes through `sendPushes()` goroutine
- Calls `pushConnection()` for each proxy, which iterates watched resources in order

---

## Q4: Resource Translation

### DestinationRule → Envoy Cluster (CDS)

**Translation Path:**

1. **Discovery**: `PushContext` indexes all DestinationRules by service hostname
   - **File**: `pilot/pkg/model/push_context.go` - maintains `destinationRuleIndex`

2. **Cluster Building**: When generating CDS for a proxy:
   - **File**: `pilot/pkg/networking/core/configgen.go:34-35`
   - Interface: `BuildClusters(node *model.Proxy, req *model.PushRequest)`
   - Implementation: `pilot/pkg/networking/core/cluster.go:56-65`

3. **Traffic Policy → Cluster Settings**:
   - **File**: `pilot/pkg/networking/core/cluster_traffic_policy.go`
   - DestinationRule's `TrafficPolicy` fields map to Envoy `Cluster` protobuf:
     - `connectionPool` → `ClusterConfig.ConnectTimeout`, `http_protocol_options`
     - `loadBalancer` (Round Robin, LeastConn, etc.) → `Cluster.LbPolicy`
     - `tls` settings → `Cluster.TransportSocket` with mTLS configuration
     - `outlierDetection` → `Cluster.OutlierDetection`

4. **Subset Creation**:
   - For each subset in DestinationRule, creates a separate Envoy cluster
   - Subset name: `<service-hostname>|<subset-name>`
   - Subset's labels become cluster metadata used for load balancing

### VirtualService → Envoy Route Configuration (RDS)

**Translation Path:**

1. **Discovery**: `PushContext` indexes VirtualServices by hostname
   - Routes are built per service

2. **Route Building**:
   - **File**: `pilot/pkg/networking/core/configgen.go:42-43`
   - Interface: `BuildHTTPRoutes(node *model.Proxy, req *model.PushRequest, routeNames []string)`
   - Implementation: `pilot/pkg/networking/core/httproute.go:58-100`

3. **VirtualService Rules → Envoy Routes**:
   - **File**: `pilot/pkg/networking/core/route/route.go`
   - For each `VirtualService.http[i]` rule:
     - `match` (path, headers, query params) → Envoy `RouteMatch`
     - `route.destination` → Envoy `RouteAction.Cluster` with proper subset
     - `timeout`, `retries` → Envoy route action configuration
     - `corsPolicy`, `fault`, `mirror` → corresponding Envoy filter configs

4. **Virtual Host Creation**:
   - **File**: `pilot/pkg/networking/core/httproute.go:69-77`
   - Groups routes by domain/hostname into virtual hosts
   - VirtualService's `hosts` field determines which virtual host receives the route

### Endpoint Discovery (EDS) - ClusterLoadAssignment Building

**Translation Path:**

1. **Endpoint Index Storage**:
   - **File**: `pilot/pkg/model/endpointshards.go`
   - `EndpointIndex` maintains shards keyed by `ShardKey` (service hostname + namespace)
   - Populated via `EDSUpdate()` from service registry (Kubernetes or ServiceEntry)

2. **EDS Generator**:
   - **File**: `pilot/pkg/xds/eds.go:124-140`
   - `EdsGenerator.Generate()` delegates to `ConfigGenerator.BuildEndpoints()`

3. **ClusterLoadAssignment Building**:
   - **File**: `pilot/pkg/xds/endpoints/endpoint_builder.go:85-100`
   - `EndpointBuilder` translates service endpoints:
     - Fetches `IstioEndpoint` list for a service from `EndpointIndex`
     - Groups endpoints by locality/zone for locality-aware load balancing
     - Applies filters (health status, network reachability)
   - For each endpoint:
     - Creates Envoy `LbEndpoint` with address, port, health status
     - Applies DestinationRule subset labels as metadata
     - **File**: `pilot/pkg/xds/endpoints/ep_filters.go` - applies filters like network, health status

4. **Result**:
   - **File**: `github.com/envoyproxy/go-control-plane/envoy/config/endpoint/v3`
   - Produces `ClusterLoadAssignment` protobuf with:
     - `ClusterName` (same as cluster name from CDS)
     - `Endpoints[LocalityLbEndpoints]` grouped by locality
     - Each endpoint marked with health status and labels

---

## Evidence

### Key Files and Line References

**Config Ingestion:**
- `pilot/pkg/config/kube/crdclient/client.go:99-120` - Client type and schema initialization
- `pilot/pkg/config/aggregate/config.go:84-92` - Aggregate store merging
- `pilot/pkg/xds/discovery.go:298-318` - ConfigUpdate entry point

**Internal Model:**
- `pilot/pkg/model/service.go:69-100` - Service type definition
- `pilot/pkg/model/push_context.go:64-89` - serviceIndex structure
- `pilot/pkg/model/context.go:96-144` - Environment and PushContext

**xDS Generation:**
- `pilot/pkg/xds/discovery.go:73` - Generators map
- `pilot/pkg/xds/discovery.go:325-412` - Debouncing logic
- `pilot/pkg/xds/xdsgen.go:67-91` - findGenerator() lookup
- `pilot/pkg/xds/xdsgen.go:96-179` - pushXds() function
- `pilot/pkg/xds/ads.go:502-514` - Push order constants
- `pilot/pkg/xds/ads.go:562-594` - AdsPushAll and push distribution

**Resource Translation:**
- `pilot/pkg/networking/core/cluster.go:52-65` - BuildClusters interface and implementation
- `pilot/pkg/networking/core/cluster_traffic_policy.go` - DestinationRule traffic policy translation
- `pilot/pkg/networking/core/httproute.go:58-100` - BuildHTTPRoutes implementation
- `pilot/pkg/networking/core/route/route.go` - VirtualService rule translation
- `pilot/pkg/xds/endpoints/endpoint_builder.go:85-100` - Endpoint building
- `pilot/pkg/xds/eds.go:124-140` - EDS generator

**Generator Implementations:**
- `pilot/pkg/xds/cds.go:26` - CdsGenerator
- `pilot/pkg/xds/eds.go` - EdsGenerator
- `pilot/pkg/xds/lds.go:27` - LdsGenerator
- `pilot/pkg/xds/rds.go:24` - RdsGenerator
