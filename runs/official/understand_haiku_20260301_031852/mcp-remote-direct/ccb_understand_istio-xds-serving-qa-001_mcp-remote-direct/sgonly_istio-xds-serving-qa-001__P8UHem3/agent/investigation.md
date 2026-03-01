# Istio Pilot xDS Serving Architecture

## Q1: Config Ingestion Pipeline

### How Pilot Watches Kubernetes Custom Resources

Pilot watches Kubernetes custom resources (VirtualService, DestinationRule, ServiceEntry) through a hierarchical configuration system:

**ConfigStoreController Interface** (`pilot/pkg/model/config.go:188-201`)
- Extends `ConfigStore` interface with three additional methods:
  - `RegisterEventHandler(kind config.GroupVersionKind, handler EventHandler)` - Register handlers for specific resource types
  - `Run(stop <-chan struct{})` - Start the controller watching for changes
  - `HasSynced() bool` - Indicates whether initial sync is complete
- Handlers are executed sequentially on a single worker queue in registration order
- Provides AT LEAST consistency: cached view is as fresh as or fresher than the notification moment

**Kubernetes Implementation** (`pilot/pkg/config/kube/crdclient/client.go`)
- Implements `ConfigStoreController` interface
- Uses Kubernetes dynamic client to watch CRD resources
- Maintains a local fully-replicated cache of the config store
- Dispatches change events to registered handlers

**Config Change Event Flow**:
1. Kubernetes API watches trigger updates in the CRD client
2. Changes are queued through `RegisterEventHandler` callbacks
3. Event handlers are called with old/new config versions and the event type (ADD/UPDATE/DELETE)
4. Handlers execute on a single worker queue, preserving ordering

**Aggregate Config Store** (`pilot/pkg/config/aggregate/config.go:34-82`)
- `MakeCache()` creates an aggregate config store cache from multiple config store caches
- Merges multiple config sources (Kubernetes, file-based, memory)
- Provides unified schema view across all sources
- Read-only aggregator for Istio configuration

**Service Registry Controller** (`pilot/pkg/serviceregistry/aggregate/controller.go:41-130`)
- `Controller` aggregates data across different registries (Kubernetes, ServiceEntry)
- `AddRegistry()` method (line 187) adds registries and ensures event handlers propagate
- Merges services from multiple clusters and sources
- `mergeService()` (line 312) merges two clusters' k8s services with conflict detection

### Config Change Delivery to xDS

**Event Handler Registration Chain**:
1. Pilot's `DiscoveryServer` registers handlers on the `ConfigStoreController`
2. Each handler receives updates through the `EventHandler` callback signature
3. Updates flow through the event aggregation layer to the DiscoveryServer

**ConfigUpdate Path** (`pilot/pkg/xds/discovery.go:297-318`):
- `DiscoveryServer.ConfigUpdate(req *model.PushRequest)` is called by handlers
- Increments `InboundUpdates` counter
- Places the `PushRequest` onto the `pushChannel` for debouncing
- `handleUpdates()` (line 325) reads from pushChannel and applies debounce logic

**Debouncing Mechanism** (`pilot/pkg/xds/discovery.go:330-327`):
- `debounce()` function ensures minimum quiet time between events
- Batches rapid config changes together
- Maximum delay cap (default 10s) ensures timely delivery
- Prevents "thundering herd" of individual pushes on rapid config changes
- When quiet time elapsed, calls `s.Push()` to trigger xDS generation

---

## Q2: Internal Service Model

### Platform-Specific to Internal Model Conversion

**Core Service Type** (`pilot/pkg/model/service.go:59-123`)
```
Service struct:
  - Hostname: FQDN for the service (e.g., "catalog.mystore.com")
  - Ports: PortList with protocol and port numbers
  - ClusterVIPs: Service address per cluster (for load balancer IPs)
  - DefaultAddress: Default load balancer IP
  - Resolution: STATIC, PASSTHROUGH, or DNS
  - MeshExternal: Boolean indicating if external to mesh
  - ServiceAccounts: List of accounts running the service
  - Attributes: ServiceAttributes for RBAC and other metadata
```

**Kubernetes to Internal Conversion**:
- Kubernetes Services → `Service` with ClusterVIPs from service.spec.clusterIP
- ServiceEntry → `Service` with Resolution and MeshExternal settings
- Service hostname resolution is handled by `host.Name` types with FQDN format

**ServiceEntry vs Kubernetes Service**:
- **Kubernetes Service**: Maps to internal `Service` with STATIC resolution, ClusterVIP from clusterIP
- **ServiceEntry**: Creates `Service` with user-specified resolution mode (DNS, PASSTHROUGH), allows external services, custom endpoints via WorkloadEntry

### PushContext: The Internal Configuration Index

**PushContext Structure** (`pilot/pkg/model/push_context.go:206-279`)
```
Key indexes maintained:
  - ServiceIndex: Index services by hostname, port, and other fields
  - virtualServiceIndex: Index VirtualServices by hostname with wildcard support
  - destinationRuleIndex: Index DestinationRules by hostname with wildcard support
  - gatewayIndex: Index gateways by namespace and name
  - sidecarIndex: Index Sidecars by namespace and workload selector
  - serviceAccounts: Map of (hostname, port) → service accounts
  - envoyFiltersByNamespace: Map namespace → EnvoyFilter configs
  - AuthnPolicies: Authn policies indexed by namespace
  - AuthzPolicies: Authz policies indexed by namespace
  - ProxyConfigs: ProxyConfig resources indexed
  - Telemetry: Telemetry policies indexed
  - Mesh: MeshConfig for mesh-wide settings
  - Networks: MeshNetworks for multi-cluster topology
```

**PushContext Initialization** (`pilot/pkg/model/push_context.go:1285-1343`)
- `InitContext()` method called when new push is needed
- For full push or initial sync:
  - `createNewContext()` (line 1320):
    - `initServiceRegistry()`: Load all services from service discovery
    - `initVirtualServices()`: Load and index all VirtualServices
    - `initDestinationRules()`: Load and merge DestinationRules
    - `initKubernetesGateways()`: Load Kubernetes Gateway API resources
    - `initAuthorizationPolicies()`: Load AuthzPolicies
    - `initTelemetry()`: Load Telemetry resources
    - `initSidecarScopes()`: Compute Sidecar scopes for each proxy type
- For incremental updates:
  - `updateContext()` (line 1345): Re-index only changed config types

**Service Discovery Integration** (`pilot/pkg/model/context.go:120-126`)
```
Environment.ServiceDiscovery points to aggregate controller
This provides:
  - AllServices(): Get all services across all clusters/registries
  - GetService(hostname): Lookup specific service
  - InstancesByPort(service, port): Get all endpoints for service:port
  - WorkloadHealthCheckInfo(hostname): Health status
```

---

## Q3: xDS Generation and Dispatch

### Config Update Reception and Debouncing

**DiscoveryServer Structure** (`pilot/pkg/xds/discovery.go:63-121`)
```
Key fields:
  - Env: *model.Environment with full runtime state
  - Generators: map[string]model.XdsResourceGenerator keyed by type
  - pushChannel: Buffered channel for config updates (before debounce)
  - pushQueue: Queue after debounce, before xDS push
  - Cache: XdsCache for response caching
  - adsClients: Active gRPC connections from proxies
  - InboundUpdates: Counter of received config updates
  - CommittedUpdates: Counter of processed updates in PushContext
```

**Update Flow**:
1. `ConfigUpdate()` receives push request from handler
2. Increments `InboundUpdates` counter
3. Places request on `pushChannel` (non-blocking)
4. `handleUpdates()` goroutine reads from channel
5. Debounce logic waits for `DebounceAfter` duration (default 100ms) with `debounceMax` cap (10s)
6. When stable, calls `s.Push()` with debounced request
7. Increments `CommittedUpdates` counter

**Debounce Implementation** (`pilot/pkg/xds/discovery.go:330-327`):
- Separate goroutine reads from `pushChannel`
- Accumulates requests during quiet period
- Periodically checks if `maxDelay` exceeded
- Calls `pushFn` (which is `s.Push`) when ready
- Ensures both rapid and slow updates are handled efficiently

### Generator Architecture and Dispatch

**Generator Registration** (See `pilot/pkg/bootstrap/configcontroller.go` and xDS setup)
- Each xDS resource type (CDS, EDS, LDS, RDS, SDS, etc.) has a corresponding `XdsResourceGenerator`
- Generators map in DiscoveryServer:
  - Key: `typeURL` (e.g., "type.googleapis.com/envoy.config.cluster.v3.Cluster")
  - Value: `XdsResourceGenerator` implementation

**Generator Selection** (`pilot/pkg/xds/xdsgen.go:67-91`)
```go
func (s *DiscoveryServer) findGenerator(typeURL string, con *Connection) model.XdsResourceGenerator {
    // Priority:
    // 1. Custom generator by proxy metadata + typeURL
    // 2. Custom generator by proxy type + typeURL
    // 3. Default generator by typeURL
    // 4. Proxy's default XdsResourceGenerator
    // 5. Fallback to "api" (MCP) or "event" (debug)
}
```

**Generator Dispatch** (`pilot/pkg/xds/xdsgen.go:96-141`)
```go
func (s *DiscoveryServer) pushXds(con *Connection, w *model.WatchedResource, req *model.PushRequest) error {
    gen := s.findGenerator(w.TypeUrl, con)  // Select generator
    res, logdata, err := gen.Generate(con.proxy, w, req)  // Call generator
    // Send response back to proxy
}
```

**XdsResourceGenerator Interface** (`pilot/pkg/model/context.go:276-285`)
```go
type XdsResourceGenerator interface {
    // Generate produces Sotw (state-of-the-world) resources for xDS
    Generate(proxy *model.Proxy, w *model.WatchedResource, req *model.PushRequest)
             (model.Resources, model.XdsLogDetails, error)
}

type XdsDeltaResourceGenerator interface {
    XdsResourceGenerator
    // GenerateDeltas produces incremental delta resources
    GenerateDeltas(proxy *model.Proxy, req *model.PushRequest, w *model.WatchedResource)
                   (model.Resources, model.DeletedResources, model.XdsLogDetails, bool, error)
}
```

### Push Execution Flow

**Push Method** (`pilot/pkg/xds/discovery.go:254-280`)
1. If incremental push: Use existing push context and skip cache clear, call `AdsPushAll()`
2. If full push:
   - Save old push context metrics
   - Create new `PushContext` via `initPushContext()`
   - Drop relevant cache entries
   - Call `AdsPushAll()` with new context
3. `AdsPushAll()` iterates connected proxies and calls `pushXds()` for each watched resource

**PushContext Creation** (`pilot/pkg/xds/discovery.go:507-522`)
```go
func (s *DiscoveryServer) initPushContext(req *model.PushRequest, oldPushContext *model.PushContext, version string) (*model.PushContext, error) {
    push := model.NewPushContext()
    push.PushVersion = version  // Monotonic version for tracking
    if err := push.InitContext(s.Env, oldPushContext, req); err != nil {
        return nil, err
    }
    s.Env.SetPushContext(push)  // Make available globally
    return push, nil
}
```

---

## Q4: Resource Translation

### DestinationRule → CDS (Cluster Configuration)

**Translation Pipeline**:
1. `CdsGenerator` (`pilot/pkg/xds/cds.go:26-28`) wraps `ConfigGenerator`
2. On push request, calls `ConfigGenerator.BuildClusters()`
3. **Input**: Proxy (to determine relevant services) + PushRequest
4. **Output**: List of `cluster.Cluster` protobuf messages

**BuildClusters Implementation** (`pilot/pkg/networking/core/cluster.go:52-65`)
- Gathers relevant services for proxy from `SidecarScope` or gateway config
- Calls `buildClusters()` for each service
- Creates one cluster per service or per DestinationRule subset

**DestinationRule Application** (`pilot/pkg/networking/core/cluster.go`):
- DestinationRule parsed from `PushContext.destinationRuleIndex`
- For each DestinationRule subset:
  - Traffic policy settings applied to Cluster:
    - Connection pooling → `cluster.CircuitBreakers`
    - Outlier detection → `cluster.OutlierDetection`
    - Load balancer settings → `cluster.LbPolicy` and `cluster.CommonLbConfig`
    - TLS settings → `cluster.TransportSocket` with mTLS configuration
- Cluster name format: `outbound|{port}|{subset}|{hostname}`

**Delta Handling** (`pilot/pkg/networking/core/cluster.go:67-142`)
- Detects DestinationRule updates and recomputes only affected subset clusters
- `deltaFromDestinationRules()` identifies services affected by DR change
- Returns both new clusters and list of deleted clusters

### VirtualService → RDS (HTTP Route Configuration)

**Translation Pipeline**:
1. `RdsGenerator` (`pilot/pkg/xds/rds.go:24-26`) wraps `ConfigGenerator`
2. On push request, calls `ConfigGenerator.BuildHTTPRoutes()`
3. **Input**: Proxy + requested route names
4. **Output**: List of `route.RouteConfiguration` protobuf messages

**BuildHTTPRoutes** (`pilot/pkg/networking/core/httproute.go:57-60`):
- Iterates through services visible to proxy
- For each service with listeners:
  - Finds matching VirtualServices by host name
  - Builds HTTP routes for each VirtualService

**VirtualService to Routes Conversion** (`pilot/pkg/networking/core/route/route.go:377-381`)
```go
func BuildHTTPRoutesForVirtualService(
    node *model.Proxy,
    virtualService config.Config,
    serviceRegistry map[host.Name]*model.Service,
    hashByDestination *LoadBalancerPolicy,
    listenPort int,
    meshGateway sets.Set[string],
    opts RouteOptions,
) ([]*route.Route, error)
```

- VirtualService HTTP routes (`spec.http[]`):
  - Match conditions → Envoy RouteMatch
  - Destinations → Weighted route clusters
  - Timeouts/retries → RouteAction settings
  - Header manipulation → HeaderMutationOptions
- Destination weights translated to cluster weights
- Subsets referenced in Destination → exact cluster name (with subset)

### ServiceEntry/Endpoints → EDS (Endpoint Discovery)

**Translation Pipeline**:
1. `EdsGenerator` (`pilot/pkg/xds/eds.go:82-87`) maintains reference to `EndpointIndex`
2. On push request, calls `buildEndpoints()` to populate `ClusterLoadAssignment`
3. **Input**: Proxy + resource names to return + PushRequest
4. **Output**: List of `endpoint.ClusterLoadAssignment` protobuf messages

**Endpoint Discovery Integration**:
- Service discovery controllers (Kubernetes, ServiceEntry) call `DiscoveryServer.EDSUpdate()`
- `EDSUpdate()` updates `EndpointIndex` and triggers push for affected services
- EndpointIndex structure:
  - Keyed by ShardKey (cluster, namespace identity)
  - Contains service name → []*IstioEndpoint mapping
  - Includes health status, load balancer weights

**IstioEndpoint to Envoy Conversion** (`pilot/pkg/xds/eds.go`):
- Each `IstioEndpoint` represents one pod/VM instance:
  - Address (IPv4/IPv6)
  - Port (target port)
  - Labels (for subset matching)
  - Health status
  - Load balancer weight
  - Locality info (for split horizon)
- Converted to `endpoint.LbEndpoint` with metadata for:
  - Connection pooling
  - Health checks
  - Priority and locality
  - Load balancer metadata

**ClusterLoadAssignment Assembly** (`pilot/pkg/xds/endpoints/endpoint_builder.go`):
- Creates one `ClusterLoadAssignment` per cluster name
- Endpoints grouped by locality (for split-horizon + load balancing)
- Each `LocalityLbEndpoints` weighted by locality weight
- Endpoints within locality weighted by user-specified weights

---

## Evidence

### Q1: Config Ingestion Pipeline
- `pilot/pkg/model/config.go:188-201` — ConfigStoreController interface definition
- `pilot/pkg/config/memory/controller.go` — Memory-based ConfigStoreController implementation
- `pilot/pkg/config/kube/crdclient/client.go:180-256` — Kubernetes CRD client implementation
- `pilot/pkg/config/aggregate/config.go:34-82` — Aggregate config store maker
- `pilot/pkg/serviceregistry/aggregate/controller.go:34-187` — Aggregate service registry controller
- `pilot/pkg/xds/discovery.go:297-327` — ConfigUpdate and debounce flow

### Q2: Internal Service Model
- `pilot/pkg/model/service.go:59-123` — Service struct definition
- `pilot/pkg/model/push_context.go:206-279` — PushContext structure with indexes
- `pilot/pkg/model/push_context.go:1285-1343` — InitContext and createNewContext methods
- `pilot/pkg/model/context.go:120-126` — Environment.ServiceDiscovery integration
- `pilot/pkg/model/destination_rule.go:31-100` — DestinationRule merge logic

### Q3: xDS Generation and Dispatch
- `pilot/pkg/xds/discovery.go:63-121` — DiscoveryServer structure
- `pilot/pkg/xds/discovery.go:325-327` — handleUpdates and debounce mechanism
- `pilot/pkg/xds/discovery.go:507-522` — initPushContext and PushContext creation
- `pilot/pkg/xds/xdsgen.go:67-91` — findGenerator method for selector dispatch
- `pilot/pkg/xds/xdsgen.go:96-141` — pushXds execution and generator calling
- `pilot/pkg/model/context.go:276-285` — XdsResourceGenerator interface

### Q4: Resource Translation
- `pilot/pkg/xds/cds.go:26-28` — CdsGenerator structure
- `pilot/pkg/networking/core/cluster.go:52-142` — BuildClusters and delta generation
- `pilot/pkg/xds/rds.go:24-70` — RdsGenerator calling BuildHTTPRoutes
- `pilot/pkg/networking/core/httproute.go:57-60` — BuildHTTPRoutes implementation
- `pilot/pkg/networking/core/route/route.go:377-381` — BuildHTTPRoutesForVirtualService
- `pilot/pkg/xds/eds.go:42-145` — EDSUpdate flow and EdsGenerator
- `pilot/pkg/xds/eds.go:82-87` — EdsGenerator with EndpointIndex
- `pilot/pkg/model/service.go` — Service struct for hostname/port mapping
- `pilot/pkg/model/controller.go` — ServiceDiscovery interface and handlers

