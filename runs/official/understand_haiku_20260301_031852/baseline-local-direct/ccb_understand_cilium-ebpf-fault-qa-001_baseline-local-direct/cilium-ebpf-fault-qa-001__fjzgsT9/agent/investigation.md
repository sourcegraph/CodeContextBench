# Cilium eBPF Fault Isolation

## Q1: Per-Node eBPF Lifecycle

### How eBPF programs are compiled, loaded, and attached per node independently:

**Component Responsible for Compilation:**
- **`pkg/datapath/loader/loader.go:ReloadDatapath()`** (line 700) is the central function responsible for compiling and loading eBPF programs on each node
- **`pkg/datapath/loader/compile.go`** handles the actual compilation process using `clang` compiler (line 39: `compiler = "clang"`)
- Each Cilium agent instantiates its own `loader` struct (line 74 in `loader.go`) with local configuration

**Node-Specific Configuration Effects on Compilation:**
- **`pkg/datapath/loader/base.go:writeNodeConfigHeader()`** (line 63) writes node-specific configuration to header files that are included during compilation
- **`pkg/datapath/loader/loader.go:hostRewrites()`** (line 176) calculates interface-specific values like MAC addresses (`THIS_INTERFACE_MAC_1`, `THIS_INTERFACE_MAC_2`) that are node-dependent
- **`pkg/datapath/loader/base.go:writeNetdevHeader()`** (line 46) writes interface-specific configuration for each node's network devices
- **Kernel feature detection** in `pkg/datapath/linux/probes` affects which eBPF features are enabled during compilation on each node
- **`pkg/datapath/loader/compile.go`** probes for CPU features (`nameBPFCPU`, line 68-72) which are node-specific and affect instruction selection

**When eBPF Programs Become Node-Local:**
- Programs become node-local immediately upon compilation: each node compiles eBPF source to `.o` files in its local state directory
- **`pkg/datapath/loader/loader.go:ReloadDatapath()`** calls **`l.templateCache.fetchOrCompile()`** (line 708) which compiles and caches compiled eBPF objects in `directoryInfo.State` (line 704-705: `State: ep.StateDir()`)
- Each endpoint has a node-local state directory: `ep.StateDir()` points to `/var/run/cilium/state/<endpoint-id>/` on that node
- **`pkg/datapath/loader/cache.go:objectCache`** (line 27) maintains per-node template cache that is "NOT accessed by another process" (line 31)

**Kernel Version and Feature Dependency:**
- Compilation includes node-specific kernel probes that determine kernel capabilities
- A kernel verifier rejection on one node affects only that node's compilation
- Fallback mechanisms are per-node (e.g., `nameBPFCPU` default to "v1" per node)

---

## Q2: Deployment Architecture

### How Cilium's deployment ensures per-node isolation:

**Deployment Model - DaemonSet:**
- **`install/kubernetes/cilium/templates/cilium-agent/daemonset.yaml`** (line 16: `kind: DaemonSet`) shows Cilium is deployed as a Kubernetes DaemonSet
- This ensures exactly one Cilium agent pod runs per node (line 37-47: pod spec with node affinity)
- Each node's Cilium agent is independent and autonomous

**Daemon Architecture:**
- **`daemon/cmd/daemon.go`** defines the `Daemon` struct (line 92) which is the main Cilium agent process
- Each node instantiates its own Daemon with its own:
  - **Policy Repository** (line 100): `policy policy.PolicyRepository` - local policy management
  - **Loader** (accessed via `owner.Loader()`): each daemon has its own loader instance for eBPF compilation
  - **Endpoint Manager** (referenced via `owner.QueueEndpointBuild()`): each node manages only local endpoints
  - **Compilation Lock** (line 396 in `bpf.go`): **`e.owner.GetCompilationLock().RLock()`** - each node has its own lock to serialize compilation

**Failure Isolation on Single Node Failure:**
- If a Cilium agent on node-A fails to initialize eBPF programs:
  - **`pkg/endpoint/bpf.go:regenerateBPF()`** (line 379) returns an error for that node only
  - **`pkg/endpoint/policy.go:Regenerate()`** (line 725) handles the error locally and marks the endpoint's health as degraded
  - **`pkg/endpoint/bpf.go` line 569**: error is logged locally: `e.getLogger().WithError(err).Error("Error while reloading endpoint BPF program")`
  - Other nodes' Cilium agents continue normal operation because they have independent loader instances and endpoint managers

**Control Plane vs Data Plane Split:**
- **Control plane** (policy distribution): cluster-wide CiliumNetworkPolicy resources distributed via Kubernetes API to all nodes
- **Data plane** (policy enforcement): each node independently:
  - Watches policy resources
  - Compiles policies locally
  - Loads eBPF programs locally
  - Enforces policies locally

---

## Q3: Policy Distribution vs. Enforcement

### How cluster-wide policies become per-node enforcement:

**CiliumNetworkPolicy Distribution:**
- **`pkg/policy/k8s/watcher.go:policyWatcher`** (line 26) runs on each node independently
- **`pkg/policy/k8s/watcher.go:watchResources()`** (line 71) watches cluster-wide CiliumNetworkPolicy resources using Kubernetes client
- Each node watches the same CRDs but maintains its own local cache: **`cnpCache`** (line 56 in `watcher.go`)

**Per-Node Policy Translation to eBPF:**
- **`pkg/policy/repository.go`** defines the local Repository (line 73: `policyContext` struct with `repo *Repository`)
- Each node's policyRepository maintains local selector cache and policy resolution
- **`pkg/policy/distillery.go`** compiles resolved policies into endpoint-specific eBPF bytecode
- **`pkg/policy/cell/policy_importer.go:PolicyImporter`** (line 33) interface defined per-node
  - **`UpdatePolicy()`** (line 34) method is called to apply policy changes locally
  - Each node runs its own `policyImporter` (line 50) that processes policy updates in a local queue (line 62: `q chan *policytypes.PolicyUpdate`)

**Why Compilation Failure on One Node Doesn't Block Others:**
1. **Policy watchers are independent**: each node's watcher receives updates from Kubernetes API independently
2. **Compilation is per-node**: **`loader.go:ReloadDatapath()`** compiles for a specific endpoint on a specific node
3. **Error handling is local**: **`endpoint/bpf.go`** (line 566-572) catches compilation errors and reports them locally only
4. **Policy distribution doesn't wait for compilation**: PolicyImporter queues updates asynchronously (line 62 in `policy_importer.go`) and each endpoint processes them independently

**Policy Translation Flow:**
- Cluster policy resource → (K8s API) → each node's policyWatcher
- policyWatcher → (local queue) → policyImporter
- policyImporter → (local repo) → Repository.GetSelectorPolicy()
- Repository → (per-endpoint) → EndpointPolicy.DistillPolicy() in **`pkg/policy/distillery.go`**
- EndpointPolicy → (loader.ReloadDatapath) → eBPF bytecode

---

## Q4: eBPF Map Scoping and State Isolation

### How eBPF maps are isolated across nodes:

**Map Locality - Endpoint-Specific and Node-Local:**
- **`pkg/bpf/bpffs_linux.go:LocalMapName()`** (line 107) creates endpoint-local map names: `fmt.Sprintf("%s%05d", name, id)`
- **`pkg/bpf/bpffs_linux.go:LocalMapPath()`** (line 112) creates node-local paths: `MapPath(LocalMapName(name, id))`
- Maps are NOT cluster-wide; they are per-endpoint on each node

**BPF Filesystem Pinning and Node Isolation:**
- **`pkg/bpf/bpffs_linux.go:BPFFSRoot()`** (line 44) returns the bpffs mount point (default `/sys/fs/bpf`)
- Each node has its own BPF filesystem mount (line 130: `log.Infof("Mounting BPF filesystem at %s", bpffsRoot)`)
- **`CiliumPath()`** (line 57) returns node-local Cilium BPF path: `filepath.Join(bpffsRoot, "cilium")`
- All pinned maps for that node are under this node-local path

**Map Types and Their Isolation:**
- **Policy Maps**: **`pkg/maps/policymap/policymap.go:Open()`** (line 500) opens maps at node-local paths created by `LocalMapPath()`
- **Connection Tracking Maps**: **`pkg/maps/ctmap/ctmap.go`** (line 62-72) maps like `MapNameTCP6`, `MapNameTCP4` are per-node
- **LXC Endpoint Maps**: **`pkg/maps/lxcmap/lxcmap.go`** stores endpoint information in endpoint-local maps
- Each endpoint ID is unique within a node, so `LocalMapPath(name, endpoint_id)` is unique per node

**State Isolation Example:**
- Policy map for endpoint 1234 on node-A: `/sys/fs/bpf/cilium/cilium_policy01234`
- Policy map for endpoint 1234 on node-B: `/sys/fs/bpf/cilium/cilium_policy01234` (but on node-B's BPF mount)
- Both maps are completely independent because they're on different nodes' filesystem mounts

**Map Creation and Failure Isolation:**
- **`pkg/endpoint/bpf.go:realizeBPFState()`** (line 548) calls **`ReloadDatapath()`** which creates and populates maps
- **`pkg/endpoint/bpf.go:WriteEndpoint()`** (line 473 calls `lxcmap.WriteEndpoint()`) synchronizes map state
- If a map creation fails on node-A (e.g., due to resource limits or kernel version mismatch), it only affects that node's packet processing
- Node-B's maps continue to be created and updated independently

**Namespacing via BPF Filesystem:**
- **`pkg/bpf/bpffs_linux.go:mountFS()`** (line 121) mounts the BPF filesystem at the node-local bpffsRoot
- **`hasMultipleMounts()`** (line 153) checks for multiple BPF filesystem mounts, ensuring isolation
- Each mount is independent and kernel-enforced isolation

**Cross-Node Map Sync is Explicit:**
- Global maps (e.g., Connection Tracking) that need cross-node visibility are explicitly synchronized via:
  - IPCache synchronization
  - kVStore distribution (etcd/Consul)
  - Hubble event distribution
- But at the eBPF level, the maps themselves are pinned only locally

---

## Evidence

### Key File Paths and References:

#### Per-Node eBPF Compilation and Loading:
1. `pkg/datapath/loader/loader.go:700` - `ReloadDatapath()` - Central entry point for per-node eBPF loading
2. `pkg/datapath/loader/compile.go:39` - Clang compiler configuration
3. `pkg/datapath/loader/base.go:63` - `writeNodeConfigHeader()` - Node-specific config generation
4. `pkg/datapath/loader/loader.go:176` - `hostRewrites()` - Interface-specific values (MAC, IP)
5. `pkg/datapath/loader/cache.go:27` - `objectCache` - Per-node template cache
6. `pkg/bpf/bpffs_linux.go:106-114` - `LocalMapName()` and `LocalMapPath()` - Node-local map paths
7. `pkg/endpoint/bpf.go:548` - `realizeBPFState()` - Per-endpoint BPF realization

#### DaemonSet Deployment:
1. `install/kubernetes/cilium/templates/cilium-agent/daemonset.yaml:16` - DaemonSet definition
2. `daemon/cmd/daemon.go:92` - Daemon struct - per-node agent
3. `daemon/cmd/daemon.go:100` - PolicyRepository - per-node policy management

#### Policy Distribution vs Enforcement:
1. `pkg/policy/k8s/watcher.go:26-71` - `policyWatcher` - Per-node watcher watching cluster-wide policies
2. `pkg/policy/k8s/watcher.go:56` - `cnpCache` - Per-node policy cache
3. `pkg/policy/cell/policy_importer.go:33-96` - `PolicyImporter` interface and implementation - per-node policy processing
4. `pkg/endpoint/policy.go:221` - Policy resolution via local Repository
5. `pkg/endpoint/bpf.go:566-572` - Per-node error handling for eBPF compilation failures
6. `pkg/endpoint/events.go:29-77` - `EndpointRegenerationEvent.Handle()` - Per-node event processing

#### Map Scoping and State Isolation:
1. `pkg/bpf/bpffs_linux.go:44` - `BPFFSRoot()` - Node-local BPF filesystem mount point
2. `pkg/bpf/bpffs_linux.go:57` - `CiliumPath()` - Node-local Cilium path
3. `pkg/bpf/bpffs_linux.go:106-114` - `LocalMapName()` and `LocalMapPath()` - Endpoint-specific map paths
4. `pkg/bpf/bpffs_linux.go:121-150` - `mountFS()` - Independent BPF filesystem mounting per node
5. `pkg/maps/policymap/policymap.go:487-506` - `Open()` / `OpenOrCreate()` - Map opening at node-local paths
6. `pkg/maps/ctmap/ctmap.go:62-72` - Connection tracking map names (per-node)
7. `pkg/endpoint/bpf.go:473` - `lxcmap.WriteEndpoint()` - Writing endpoint state to node-local maps

#### Compilation Lock (Per-Node Serialization):
1. `pkg/datapath/types/loader.go:76-83` - `CompilationLock` interface definition
2. `pkg/endpoint/bpf.go:396-398` - Compilation lock usage to serialize per-node eBPF compilation

#### Error Isolation:
1. `pkg/endpoint/policy.go:774-776` - Error handling and status reporting (per-endpoint, per-node)
2. `pkg/endpoint/bpf.go:568-571` - eBPF compilation error handling (per-node, local error logging)

### Summary of Isolation Mechanisms:

1. **Daemon Isolation**: Each node runs one Cilium daemon with its own loader, policy repo, and endpoint manager
2. **Compilation Isolation**: Each node compiles eBPF independently based on local kernel version and features
3. **Map Isolation**: Maps are pinned to node-local BPF filesystem paths using endpoint-specific naming
4. **Policy Distribution**: Cluster-wide policies are watched and applied locally by each node's agent
5. **Error Containment**: Compilation and loading errors are caught and handled locally, not propagated cluster-wide
6. **Independent Failure Modes**: One node's kernel verifier rejection, resource exhaustion, or compilation failure does not affect other nodes
