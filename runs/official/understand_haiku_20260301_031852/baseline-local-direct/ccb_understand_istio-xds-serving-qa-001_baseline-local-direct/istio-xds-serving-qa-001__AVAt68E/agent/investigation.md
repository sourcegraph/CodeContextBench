# Istio Pilot xDS Serving Architecture

## Q1: Config Ingestion Pipeline

### How Pilot Watches and Ingests Kubernetes Custom Resources

Istio's config ingestion pipeline consists of multiple layers that work together to ingest and propagate configuration changes:

#### ConfigStoreController Interface
**File:** `pilot/pkg/model/config.go:188`
The core interface that manages config watching and change notification:
```go
type ConfigStoreController interface {
    ConfigStore
    RegisterEventHandler(kind config.GroupVersionKind, handler EventHandler)
    Run(stop <-chan struct{})
    HasSynced() bool
}
```

#### Kubernetes CRD Client Implementation
**File:** `pilot/pkg/config/kube/crdclient/client.go:61-90`
The `Client` type implements `ConfigStoreController` for Kubernetes CRDs:
- Uses Kubernetes informer framework to watch for changes
- Maintains a handler registry (`handlers map[config.GroupVersionKind][]model.EventHandler`) that fires on config updates
- Uses a work queue (`queue.Instance`) to process events sequentially
- Supports filtering by GVK (GroupVersionKind) to optimize watching only relevant resources

#### Event Handler Registration
**File:** `pilot/pkg/bootstrap/server.go:919`
Config change handlers are registered during bootstrap:
```go
s.configController.RegisterEventHandler(schema.GroupVersionKind(), configHandler)
```

Each resource type (VirtualService, DestinationRule, ServiceEntry, Gateway, etc.) gets registered with a handler that triggers `ConfigUpdate` calls.

#### Config Aggregation
**File:** `pilot/pkg/config/aggregate/config.go:63-82`
The aggregate config store (`storeCache`) merges multiple config stores:
- Maintains `caches []model.ConfigStoreController` for different config sources
- Distributes `RegisterEventHandler` calls to all underlying caches
- Provides a unified view across multiple config stores

### How Config Changes Are Queued and Delivered

#### Event Propagation Path
1. **Watch Discovery:** Kubernetes informer detects resource change
2. **Handler Invocation:** Registered handlers in `crdclient/client.go` are invoked
3. **Event Queuing:** Work queue processes the event asynchronously
4. **Handler Dispatch:** All registered handlers for that GVK are called sequentially

#### Change Notification to xDS Layer
**File:** `pilot/pkg/xds/discovery.go:298`
```go
func (s *DiscoveryServer) ConfigUpdate(req *model.PushRequest) {
    s.pushChannel <- req
}
```

The `ConfigUpdate` method is the entry point for config changes:
- Receives a `PushRequest` with the updated config details
- Pushes to `pushChannel` for debouncing

#### Debouncing Pipeline
**File:** `pilot/pkg/xds/discovery.go:325-330`
- `pushChannel` feeds into debouncing logic in `handleUpdates()`
- Debouncing combines rapid config changes to avoid thrashing
- After debouncing, request goes to `pushQueue` (PushQueue)
- Finally triggers `Push()` method when stable

### Aggregate Service Registry's Role

**File:** `pilot/pkg/serviceregistry/aggregate/controller.go:42-55`
The `Controller` type aggregates data from multiple service registries:
- Maintains `registries []*registryEntry` for different providers and clusters
- Implements `model.AggregateController` and `model.ServiceDiscovery`
- Merges service data from Kubernetes, ServiceEntry, and other sources
- Forwards service discovery events to DiscoveryServer via `SvcUpdate()` and `EDSUpdate()` callbacks

**Files:**
- `pilot/pkg/xds/eds.go:31` - `SvcUpdate()` callback for service changes
- `pilot/pkg/xds/eds.go:47` - `EDSUpdate()` callback for endpoint changes

---

## Q2: Internal Service Model

### Key Internal Model Types

#### Service Type
**File:** `pilot/pkg/model/service.go:59-80`
Represents an Istio service abstraction:
- `Attributes ServiceAttributes` - metadata for RBAC
- `Ports PortList` - network ports where service listens
- `ServiceAccounts []string` - service account SPIFFE identities
- `Hostname host.Name` - FQDN like `catalog.default.svc.cluster.local`
- `ClusterName cluster.Name` - which cluster this service belongs to

#### PushContext Type
**File:** `pilot/pkg/model/push_context.go:206-225`
Central context built for each push cycle, maintains comprehensive indexes:

**Key Indexes in PushContext:**
- `ServiceIndex serviceIndex` - Services indexed by visibility (private/public/exported)
- `virtualServiceIndex virtualServiceIndex` - VirtualServices by gateway and namespace
- `destinationRuleIndex destinationRuleIndex` - DestinationRules by namespace/host
- `sidecarIndex sidecarIndex` - Sidecar scopes for each namespace
- `gatewayIndex gatewayIndex` - Gateway configurations
- `authzPolicies` - Authorization policy indexes
- `ProxyStatus map[string]map[string]ProxyPushStatus` - Per-proxy push status for debugging

#### Service Index Structure
**File:** `pilot/pkg/model/push_context.go:63-90`
```go
type serviceIndex struct {
    privateByNamespace map[string][]*Service      // "." visibility
    public []*Service                             // "*" visibility
    exportedToNamespace map[string][]*Service     // Explicitly exported
    HostnameAndNamespace map[host.Name]map[string]*Service
    instancesByPort map[string]map[int][]*IstioEndpoint
}
```

#### IstioEndpoint Type
**File:** `pilot/pkg/model/service.go` (referenced in endpoint indexes)
Represents an actual instance/pod running a service - contains:
- IP address and port
- Labels for subset matching
- Service account identity
- Network topology (region, zone)

### Kubernetes Service to Internal Model Conversion

**File:** `pilot/pkg/serviceregistry/kube/controller/controller.go`
The Kubernetes controller converts native K8s Services:
1. **Service Discovery:** Watches K8s Service objects
2. **Endpoint Watching:** Watches EndpointSlice objects for pod instances
3. **Conversion:** Builds `Service` and `IstioEndpoint` objects from K8s resources
4. **Index Building:** Populates PushContext's serviceIndex

**Process:**
- K8s Service with hostname `svc.namespace.svc.cluster.local` → Istio `Service` with FQDN
- K8s EndpointSlice entries → Istio `IstioEndpoint` objects
- Includes port protocol detection (HTTP, TCP, gRPC, etc.)

### ServiceEntry vs. Kubernetes Service

**Key Differences:**

**ServiceEntry (Custom Resource):**
- **File:** `pilot/pkg/config/kube/crdclient/client.go` handles these via config store
- Explicitly defined via Istio CRD
- Can define external services, hosts outside the cluster, or services without pods
- Translated by config handlers into Service objects
- Endpoints defined in ServiceEntry spec instead of from pod discovery

**Kubernetes Service:**
- Discovered via service registry
- Requires pod selector and actual pods running
- Endpoints automatically discovered from pod endpoints
- Limited to cluster.local domain by default

Both are merged into the unified service index in PushContext.

---

## Q3: xDS Generation and Dispatch

### How DiscoveryServer Receives Config Updates and Debounces Changes

#### ConfigUpdate Entry Point
**File:** `pilot/pkg/xds/discovery.go:298-318`
```go
func (s *DiscoveryServer) ConfigUpdate(req *model.PushRequest) {
    s.InboundUpdates.Inc()
    s.pushChannel <- req
}
```
- Increments `InboundUpdates` counter
- Non-blocking push to `pushChannel` (buffer size 10)

#### Debouncing Logic
**File:** `pilot/pkg/xds/discovery.go:330-400`
The `debounce()` function implements the debouncing strategy:
- **DebounceAfter:** Minimum wait time after last change (default 100ms)
- **debounceMax:** Maximum wait time regardless of activity (default 10s)
- **enableEDSDebounce:** Flag to control whether EDS changes are debounced

**Behavior:**
1. Rapid config changes within DebounceAfter window are merged into single push
2. If changes keep arriving, waits up to debounceMax before forcing push
3. Events are merged into a single `PushRequest` before being sent to `pushQueue`

#### Configuration Update Counter
- `InboundUpdates`: Total config events received
- `CommittedUpdates`: Events that made it into PushContext (incremented after successful push)

### Generator Architecture

#### Generator Registration
**File:** `pilot/pkg/bootstrap/discovery.go:29-69`
The `InitGenerators()` function registers all xDS generators:

```go
generators[v3.ClusterType] = &xds.CdsGenerator{ConfigGenerator: cg}
generators[v3.ListenerType] = &xds.LdsGenerator{ConfigGenerator: cg}
generators[v3.RouteType] = &xds.RdsGenerator{ConfigGenerator: cg}
generators[v3.EndpointType] = edsGen
generators[v3.SecretType] = secretGen
generators[v3.ExtensionConfigurationType] = ecdsGen
generators[v3.NameTableType] = ndsGen
```

**File:** `pilot/pkg/model/context.go:276-279`
The `XdsResourceGenerator` interface:
```go
type XdsResourceGenerator interface {
    Generate(proxy *Proxy, w *WatchedResource, req *PushRequest) (Resources, XdsLogDetails, error)
}
```

#### Generator Selection Logic
**File:** `pilot/pkg/xds/xdsgen.go:67-91`
The `findGenerator()` method selects the appropriate generator:

```go
func (s *DiscoveryServer) findGenerator(typeURL string, con *Connection) model.XdsResourceGenerator {
    // Try client-specific + type-specific generator
    if g, f := s.Generators[con.proxy.Metadata.Generator+"/"+typeURL]; f {
        return g
    }
    // Try proxy-type specific generator
    if g, f := s.Generators[string(con.proxy.Type)+"/"+typeURL]; f {
        return g
    }
    // Try type-specific generator
    if g, f := s.Generators[typeURL]; f {
        return g
    }
    // Fall back to default generators
    return s.Generators["api"] // or "event" for debug types
}
```

Selection order:
1. `GeneratorMetadata/TypeUrl` (e.g., "grpc/type.googleapis.com/envoy.config.endpoint.v3.ClusterLoadAssignment")
2. `ProxyType/TypeUrl` (e.g., "sidecar/...")
3. `TypeUrl` (default generators like CdsGenerator, LdsGenerator)

#### Pre-registered Generators
**File:** `pilot/pkg/bootstrap/discovery.go:57-68`
Multiple generator sets:
- **Default ("api"):** Uses `ConfigGenerator` for standard Istio config translation
- **gRPC generators:** Custom handling for gRPC clients (via `grpcgen.GrpcConfigGenerator`)
- **Waypoint/Ambient:** Specialized generators for ambient mesh

### How pushXds Selects and Dispatches Generators

#### pushXds Method
**File:** `pilot/pkg/xds/xdsgen.go:96-179`
```go
func (s *DiscoveryServer) pushXds(con *Connection, w *model.WatchedResource, req *model.PushRequest) error {
    gen := s.findGenerator(w.TypeUrl, con)
    res, logdata, err := gen.Generate(con.proxy, w, req)
    // Send DiscoveryResponse with resources
}
```

**Dispatch Flow:**
1. For each proxy connection (`con`) and watched resource type (`w.TypeUrl`)
2. Call `findGenerator()` to get the right generator
3. Invoke `Generate()` which returns xDS resources
4. Build `DiscoveryResponse` with resources and version info
5. Send via xDS stream

#### Resource Types and Their Generators
**File:** `pilot/pkg/xds/v3/` (TypeUrl constants):
- **CDS (Cluster Discovery Service):** `CdsGenerator` - invokes `ConfigGenerator.BuildClusters()`
- **RDS (Route Discovery Service):** `RdsGenerator` - invokes `ConfigGenerator.BuildHTTPRoutes()`
- **LDS (Listener Discovery Service):** `LdsGenerator` - invokes `ConfigGenerator.BuildListeners()`
- **EDS (Endpoint Discovery Service):** `EdsGenerator` - custom endpoint index lookup
- **SDS (Secret Discovery Service):** `SecretGen` - credentials controller integration
- **ECDS (Extension Configuration):** `EcdsGenerator` - extension configs
- **NDS (Name Table/DNS):** `NdsGenerator` - DNS name table for proxy
- **PCDS (Proxy Configuration):** `PcdsGenerator` - trust bundle configuration

---

## Q4: Resource Translation

### DestinationRule → Envoy Cluster Configuration (CDS)

#### DestinationRule Processing
**File:** `pilot/pkg/model/destination_rule.go:31-80`
`PushContext.mergeDestinationRule()` merges multiple DestinationRules for the same host:
- Merges subsets from multiple rules
- Applies traffic policy settings
- Handles visibility/exportTo rules
- Stores in `consolidatedDestRules` index

#### Translation to Cluster Settings
**File:** `pilot/pkg/networking/core/cluster.go:52-65`
`ConfigGeneratorImpl.BuildClusters()` generates Envoy Clusters:

**Process:**
1. Iterates through services visible to the proxy
2. For each service, gets DestinationRule via `PushContext.destinationRuleIndex`
3. Extracts traffic policy settings:
   - Connection pool settings (max connections, requests per connection)
   - TLS settings (mTLS mode, SNI)
   - Load balancer configuration (round-robin, least request, etc.)
   - Outlier detection settings
   - Retry policies (via `ConnectionPoolSettings`)
4. Creates Envoy `Cluster` resource with these settings

**Cluster Types Generated:**
- **Outbound clusters:** One per service hostname + subset
- **Inbound clusters:** For sidecar inbound traffic
- **EDS-based clusters:** With `type: EDS` pointing to EndpointIndex

**DestinationRule Fields Mapped:**
- `TrafficPolicy.ConnectionPool` → Envoy cluster's `max_connections`, `max_requests`
- `TrafficPolicy.TLS` → Envoy cluster's `transport_socket` (TLS config)
- `TrafficPolicy.LoadBalancer` → Envoy cluster's `lb_policy`
- `TrafficPolicy.OutlierDetection` → Envoy cluster's `outlier_detection`
- `Subsets` → Multiple clusters per subset (e.g., `reviews-v1`, `reviews-v2`)

### VirtualService → Envoy Route Configuration (RDS)

#### VirtualService Processing
**File:** `pilot/pkg/model/push_context.go:99-115`
`virtualServiceIndex` maintains VS by:
- Gateway visibility
- Namespace and exportTo settings
- Delegate VS relationships

#### Translation to HTTP Routes
**File:** `pilot/pkg/networking/core/httproute.go:57-80`
`ConfigGeneratorImpl.BuildHTTPRoutes()` generates Envoy RouteConfigurations:

**Process:**
1. Iterates through route names requested by proxy
2. For each route, looks up associated VirtualServices via gateway
3. For each VirtualService:
   - **Host matching:** Match on `virtualService.hosts`
   - **HTTP routes:** Translate `http[]` field to Envoy HTTP routes
   - **Route rules:** For each HTTP route rule:
     - Match conditions (path prefix, headers, methods)
     - Route actions (cluster, weight, timeout)
     - Retries, timeouts, fault injection
     - Mirror/shadow traffic settings
4. Builds Envoy RouteConfiguration with VirtualHosts and Routes

**VirtualService Fields Mapped:**
- `Hosts` → Envoy VirtualHost domain matching
- `Http[].Match` → Envoy RouteMatch (path, headers, methods)
- `Http[].Route` → Envoy Route(weighted routing to clusters)
- `Http[].Timeout` → Envoy timeout settings
- `Http[].Retries` → Envoy retry policy
- `Http[].Fault` → Envoy fault injection
- `Http[].Mirror` → Envoy mirroring to shadow cluster
- `Http[].Headers` → Envoy request/response header manipulation
- `Delegates` → Delegated routing to nested VirtualServices

### ClusterLoadAssignment for Endpoint Discovery (EDS)

#### EDS Generator
**File:** `pilot/pkg/xds/eds.go:84-100`
`EdsGenerator` maintains optimized endpoint lookup:
```go
type EdsGenerator struct {
    Cache model.XdsCache
    EndpointIndex *model.EndpointIndex
}
```

#### Endpoint Update Pipeline
**File:** `pilot/pkg/xds/eds.go:47-61`
`EDSUpdate()` is called by service registry when endpoints change:
1. Updates `Env.EndpointIndex` with new IstioEndpoint list
2. Triggers ConfigUpdate with `EndpointUpdate` reason
3. EDS push is debounced (if `enableEDSDebounce`) or pushed immediately

#### ClusterLoadAssignment Generation
**File:** `pilot/pkg/xds/endpoints/` (endpoint generation)
For each service and port, generates Envoy `ClusterLoadAssignment`:

**Structure:**
- **ClusterName:** `hostname` or `hostname|port|subset`
- **Endpoints:** List of LocalityLbEndpoints (endpoints grouped by zone/region)
- **LocalityLbEndpoints:**
  - **Locality:** Region/zone information for traffic policies
  - **LbEndpoints:** Individual endpoint with address:port and health status
  - **Priority:** For locality-aware load balancing
  - **LoadBalancingWeight:** For weighted locality balancing
- **Policy:** Load balancing policies for outlier detection

**Endpoint Population:**
1. Gets all IstioEndpoints for service from EndpointIndex
2. Groups by locality (zone/region/cluster)
3. Filters by destination rule subset selectors
4. Adds health status
5. Applies network policies (local vs. remote endpoint filtering)

#### Config Sources Feeding EDS
**File:** `pilot/pkg/xds/eds.go:92-99`
Skipped config types for EDS (won't trigger EDS push):
```
VirtualService, Gateway, WorkloadGroup, AuthorizationPolicy,
RequestAuthentication, Secret, Telemetry, WasmPlugin, etc.
```

Only ServiceEntry and DestinationRule updates trigger EDS delta recalculation.

---

## Evidence

### Key File References

**Config Ingestion:**
- `pilot/pkg/model/config.go:173-201` - ConfigStoreController interface
- `pilot/pkg/config/kube/crdclient/client.go:61-100` - Kubernetes CRD client
- `pilot/pkg/config/aggregate/config.go:63-82` - Aggregate config store
- `pilot/pkg/bootstrap/server.go:919` - Handler registration in bootstrap
- `pilot/pkg/xds/discovery.go:298-318` - ConfigUpdate entry point
- `pilot/pkg/xds/discovery.go:325-400` - Debouncing logic
- `pilot/pkg/serviceregistry/aggregate/controller.go:42-55` - Aggregate registry

**Internal Service Model:**
- `pilot/pkg/model/push_context.go:206-225` - PushContext definition
- `pilot/pkg/model/push_context.go:63-90` - serviceIndex structure
- `pilot/pkg/model/service.go:59-80` - Service type definition
- `pilot/pkg/model/destination_rule.go:31-80` - DestinationRule merging
- `pilot/pkg/serviceregistry/kube/controller/controller.go:1-100` - K8s service conversion

**xDS Generation and Dispatch:**
- `pilot/pkg/xds/discovery.go:137-168` - NewDiscoveryServer
- `pilot/pkg/bootstrap/discovery.go:29-69` - InitGenerators
- `pilot/pkg/model/context.go:276-279` - XdsResourceGenerator interface
- `pilot/pkg/xds/xdsgen.go:67-91` - findGenerator logic
- `pilot/pkg/xds/xdsgen.go:96-179` - pushXds method
- `pilot/pkg/xds/discovery.go:254-282` - Push method

**Resource Translation:**
- `pilot/pkg/networking/core/cluster.go:52-65` - BuildClusters (CDS)
- `pilot/pkg/networking/core/httproute.go:57-80` - BuildHTTPRoutes (RDS)
- `pilot/pkg/xds/eds.go:84-100` - EdsGenerator
- `pilot/pkg/xds/eds.go:47-61` - EDSUpdate flow
- `pilot/pkg/xds/endpoints/` - Endpoint generation logic

### Type/Interface References
- `model.PushContext` - Central context for push cycles
- `model.ConfigStoreController` - Config watching interface
- `model.XdsResourceGenerator` - Generator interface
- `model.Service` - Internal service representation
- `model.IstioEndpoint` - Endpoint/instance representation
- `xds.DiscoveryServer` - Main xDS server implementation
- `xds.EdsGenerator` - Endpoint discovery generator
- `core.ConfigGenerator` - Envoy config builder interface
- `aggregate.Controller` - Service registry aggregator
