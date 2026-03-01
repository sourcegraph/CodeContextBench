# Cilium eBPF Fault Isolation

## Q1: Per-Node eBPF Lifecycle

### How are eBPF programs compiled, loaded, and attached on each node independently?

Each Cilium node independently compiles, loads, and attaches eBPF programs through a dedicated loader component. The lifecycle is entirely node-local and triggered per-endpoint.

**Compilation Component:**
The `pkg/datapath/loader/loader.go:74-89` defines the `loader` struct which manages all compilation and loading operations. Each node instantiates a single `loader` instance that compiles eBPF programs using a cache system (`templateCache`) to amortize compilation costs.

**Compilation Process:**
- `pkg/datapath/loader/loader.go:700-731` contains `ReloadDatapath()`, the entry point for endpoint-specific eBPF program compilation. This function takes an endpoint and local node configuration and compiles the program for that specific node.
- The function calls `l.templateCache.fetchOrCompile(ctx, cfg, ep, &dirs, stats)` which either retrieves a cached pre-compiled template or triggers compilation via `pkg/datapath/loader/compile.go`.
- `pkg/datapath/loader/compile.go:134-170` contains `getBPFCPU()` which probes kernel capabilities to determine which BPF instruction set to use (v1, v2, or v3). This is **node-specific** because kernel features vary across nodes.
- `pkg/datapath/loader/compile.go:32-65` defines program compilation metadata, showing programs are compiled to object files (`.o`) in the endpoint's state directory: `endpointPrefix = "bpf_lxc"`, `endpointObj = "bpf_lxc.o"`, etc.

**Node-Specific Configuration:**
The `directoryInfo` struct (`pkg/datapath/loader/compile.go:90-100`) specifies compilation directories:
- `Library`: BPF source code directory
- `Runtime`: Runtime headers directory
- `State`: Node-specific headers for templating (kernel version, enabled features)
- `Output`: Endpoint state directory on **this node only**

This means compilation output is stored on the local node's filesystem, not shared across the cluster.

**Loading and Attachment:**
After compilation, the loader attaches the compiled eBPF objects to kernel interfaces:
- `pkg/datapath/loader/objects.go:14-36` defines `lxcObjects` which represent loaded eBPF programs and maps for an endpoint
- `pkg/datapath/loader/loader.go:727-731` calls `reloadEndpoint(ep, spec)` which loads the compiled object files and attaches them to the endpoint's veth interface
- `pkg/datapath/loader/base.go`, `tc.go`, `tcx.go`, and `xdp.go` contain specific attachment logic for different kernel hook types

**Per-Node Isolation Point:**
The compilation output directory is **per-endpoint, per-node**: each endpoint's `.o` file is stored in `ep.StateDir()` (line 705 in loader.go). If Node A fails to compile for Endpoint X due to kernel verifier rejection, Node B's compilation for Endpoint X proceeds independently because each node writes to its own filesystem.

### What component is responsible for compiling eBPF programs on each node?

The `pkg/datapath/loader/` package, specifically:
- **Compilation orchestration:** `loader.ReloadDatapath()` (loader.go:700)
- **Template caching:** `objectCache` (cache.go:26-54) handles compilation amortization
- **Actual compilation:** `pkg/datapath/loader/compile.go` contains `compile()` function and clang invocation
- **Kernel probing:** `pkg/datapath/loader/compile.go:135-170` detects BPF CPU version via `probes.HaveV3ISA()`, `probes.HaveProgramHelper()`

### How does node-specific configuration (kernel version, enabled features, etc.) affect compilation?

Node-specific kernel features directly affect the compiled output:
- **BPF CPU Version Selection:** `compile.go:135-170` probes kernel capabilities and selects v1, v2, or v3 BPF instruction set
- **Feature Headers:** The `State` directory in `directoryInfo` (compile.go:97) contains node-specific headers generated before compilation that define enabled features
- **Datapath Hash:** `pkg/datapath/loader/cache.go:56-94` shows `UpdateDatapathHash()` invalidates the object cache when node configuration changes. The hash is computed from the node's specific configuration, ensuring nodes with different kernel versions get different compiled programs.
- **Example:** `pkg/datapath/loader/loader.go:176-224` shows `hostRewrites()` modifies eBPF variables like `SECCTX_FROM_IPCACHE`, `THIS_INTERFACE_MAC`, and `interface_ifindex` based on the specific host's configuration

### At what point in the lifecycle does the eBPF program become node-local vs. cluster-wide?

**Node-local:** The eBPF bytecode itself is compiled and stored per-node. The source C code (`pkg/datapath/loader/compile.go:42-43` shows `endpointProg = "bpf_lxc.c"`) is cluster-wide, but the compiled object files (`.o`) are per-node and never shared.

**Cluster-wide:** The *policy rules* that are encoded into eBPF programs are defined cluster-wide via `CiliumNetworkPolicy` CRDs.

**Transition point:** `pkg/datapath/loader/loader.go:708` calls `fetchOrCompile()`. Before this point, policies are cluster-wide; after compilation starts, the output is node-local.

---

## Q2: Deployment Architecture

### How is the Cilium agent deployed across the cluster (DaemonSet, static pods, etc.)?

Cilium agent runs as a **Kubernetes DaemonSet** on each node. While explicit DaemonSet definitions are in Helm charts (outside `/pkg`), the agent implementation shows the per-node architecture:

**Agent Initialization:**
- `daemon/cmd/daemon.go:85-149` defines the `Daemon` struct, which is instantiated once per node
- Each Daemon instance has a single `loader` field (`daemon.go:128`), proving each node runs its own loader
- `daemon/cmd/daemon_main.go` is the entry point executed by the DaemonSet pod

**Per-Node Execution:**
The agent runs independently on each node and never shares state with other nodes:
- `daemon/cmd/daemon.go:90-149` shows Daemon manages node-local state: `endpointManager`, `ipam`, `ipcache`, `policy` repository, `loader`
- Policy repository (`daemon.go:100`) is a local instance, though it's updated from cluster-wide policy CRDs

### What happens when one node's Cilium agent fails to initialize its eBPF programs?

**Isolation of failure:** When one node's agent encounters a compilation error (e.g., kernel verifier rejects a program), the failure is handled at the per-endpoint level and does not propagate to other nodes.

**Error handling in endpoint regeneration:**
- `pkg/endpoint/bpf.go:379-520` contains `regenerateBPF()` which handles compilation for a single endpoint
- Lines 565-572 show the error handling: if `e.owner.Orchestrator().ReloadDatapath()` fails, the error is logged (`e.getLogger().WithError(err).Error()`) but only affects this endpoint
- The error is returned to the endpoint's regeneration context, not propagated cluster-wide

**Per-endpoint failure isolation:**
- `pkg/endpoint/bpf.go:548-586` contains `realizeBPFState()`, called per-endpoint, which invokes `ReloadDatapath()` (line 566)
- If compilation fails for Endpoint A on Node 1, Endpoint B on Node 1 can still be compiled independently (different regeneration call)
- Endpoints on Node 2 are completely unaffected (different Daemon instance, different loader, different compilation)

**Control plane vs. data plane split:**
- The policy repository is updated cluster-wide in the control plane (agents on all nodes receive policy updates)
- However, the data plane (eBPF compilation and loading) happens independently per-node via `pkg/endpoint/regenerationcontext.go:55-74`
- If Node 1's compilation fails, its endpoint remains in a degraded state, but Node 2 continues enforcing policies normally

### How does the control plane vs. data plane split contribute to isolation?

**Control Plane (Cluster-wide):**
- `pkg/policy/repository.go` manages cluster-wide policy state
- `pkg/policy/distillery.go` computes policy for security identities
- All nodes receive the same policy updates via Kubernetes watchers (`daemon/k8s`)

**Data Plane (Per-node):**
- Each node independently translates policies into eBPF bytecode via the loader
- `pkg/datapath/loader/` compiles policies specific to the node's kernel and configuration
- `pkg/endpoint/bpf.go:379-520` regenerates eBPF programs per-endpoint, not cluster-wide

**Isolation Example:**
If a policy rule triggers a compilation failure on Node 1 due to kernel verifier issues, but Node 2 has a newer kernel:
1. The policy repository updates both nodes with the same rule
2. Node 1's compilation fails, endpoint degraded
3. Node 2's compilation succeeds, endpoint enforces the policy normally

This is only possible because eBPF programs are compiled **per-node**, not shared.

---

## Q3: Policy Distribution vs. Enforcement

### How are CiliumNetworkPolicy resources distributed to each node?

**Distribution mechanism:**
- `pkg/policy/k8s/cilium_network_policy.go` watches Kubernetes for CiliumNetworkPolicy CRD events
- `pkg/policy/k8s/watcher.go` implements the Kubernetes watcher that receives policy changes across all nodes simultaneously
- `daemon/cmd/daemon.go:96` shows each node's policy repository subscribes to these watchers

**Cluster-wide delivery:**
The Kubernetes API server distributes CiliumNetworkPolicy resources to all nodes' agents. Every agent receives the same policy CRD.

### What component on each node translates policies into eBPF bytecode?

**Policy resolution:**
- `pkg/policy/repository.go` maintains a cache of resolved policies indexed by security identity
- `pkg/policy/distillery.go:15-50` defines the distillery that resolves policies (distills them from abstract rules into enforcement rules)

**Per-endpoint policy compilation:**
- `pkg/endpoint/policy.go:177-378` contains `regeneratePolicy()` which resolves the cluster-wide policy to a specific endpoint's identity
- Line 194 in policy.go calls `e.policyGetter.GetPolicyRepository().GetRevision()` to get the latest policy revision
- `pkg/policy/distillery.go` performs `resolvePolicyLocked()` (mentioned in pkg/policy/distillery_test.go) to compute the endpoint's specific policy

**eBPF bytecode generation:**
- `pkg/endpoint/bpf.go:548-586` contains `realizeBPFState()` which invokes `ReloadDatapath()` (line 566)
- `ReloadDatapath()` calls the loader's `fetchOrCompile()` (loader.go:708) which generates eBPF bytecode from the pre-computed policy

### Why doesn't a compilation failure on one node block policy distribution to other nodes?

**Decoupled compilation:**
The key is that each node compiles independently. The sequence is:

1. **Policy CRD arrives** → All nodes receive the update to their policy repository simultaneously
2. **Endpoint regeneration triggered** → Each node's endpoints start regeneration independently
   - `pkg/endpoint/bpf.go:379` regenerateBPF() is called per-endpoint, per-node
3. **Compilation happens per-node** → `ReloadDatapath()` (loader.go:700) is called for each endpoint
4. **If one node fails** → Only that endpoint on that node is affected
   - `pkg/endpoint/bpf.go:565-572` shows error handling: failure is logged but doesn't propagate
5. **Other nodes continue** → They compile the same policy for their endpoints independently

**No global synchronization point:**
Unlike systems with centralized compilation, Cilium has no step where "wait for all nodes to compile before proceeding." Each node's compilation is independent, so:
- Node 1 fails to compile Endpoint X → Endpoint X degraded
- Node 2 compiles Endpoint Y with the same policy → Success
- Node 3 compiles Endpoint Z with the same policy → Success

---

## Q4: eBPF Map Scoping and State Isolation

### Are eBPF maps node-local or cluster-wide?

**eBPF maps are entirely node-local.** Each map is scoped to a specific endpoint on a specific node.

**Per-endpoint policy maps:**
- `pkg/maps/policymap/policymap.go:31-34` shows `MapName = "cilium_policy_v2_"` with a comment: "MapName is the prefix for **endpoint-specific** policy maps"
- `pkg/endpoint/bpf.go:87-88` contains `policyMapPath()` which returns `bpf.LocalMapPath(policymap.MapName, e.ID)`
- `pkg/bpf/bpffs_linux.go:112-114` shows `LocalMapPath(name, id)` formats the path as a **per-endpoint map**: it calls `LocalMapName(name, id)` which (line 107-109) returns `fmt.Sprintf("%s%05d", name, id)` - a name + endpoint ID suffix

**Example:** Endpoint ID 100 has map name `cilium_policy_v2_00100` unique to that endpoint.

**Node-local storage:**
- `pkg/bpf/bpffs_linux.go:112-114` uses `MapPath()` which stores maps in the node's local BPF filesystem, not a shared cluster resource

### What mechanisms (BPF filesystem pinning, namespaces) ensure map isolation?

**BPF Filesystem Pinning:**
- `pkg/bpf/pinning.go:75-140` defines the pinning mechanism
- Lines 93-121 show `mapsToReplace()` and `commitMapPins()` which pin maps to the local BPF filesystem
- `pkg/bpf/pinning.go:126-139` commits pins with `pin.m.Pin(pin.path)`, storing maps in the node's `/sys/fs/bpf/` filesystem

**Node-local paths:**
- Maps are pinned to paths like `/sys/fs/bpf/cilium/globals/cilium_policy_v2_00100` (per-endpoint)
- These paths exist only on the individual node

**Namespace isolation:**
While not explicitly shown in `/pkg` code, the Linux kernel isolates:
- Network namespaces: Each pod/container has its own network namespace
- eBPF programs: Attached to specific network interfaces (veth pairs) on a specific node
- Maps: Accessible only within the node's BPF subsystem

**Per-endpoint map creation:**
- `pkg/endpoint/bpf.go:738-743` shows `e.policyMap = policymap.OpenOrCreate(e.policyMapPath())`
- Each endpoint's map is created/opened on its specific node, never synchronized to other nodes

### If a node fails to create or update a map, how does that affect other nodes' packet processing?

**Complete isolation:**
A node's map failure affects **only that node**.

**Failure handling:**
- `pkg/endpoint/bpf.go:506-512` contains `regenerateBPF()` which calls `e.policyMapSync()` (line 507)
- If `policyMapSync()` fails, the error is returned (line 509): `return 0, fmt.Errorf("unable to regenerate policy because PolicyMap synchronization failed: %w", err)`
- This error affects only the endpoint on this node

**Other nodes unaffected:**
- Each node maintains its own policy map instances
- `pkg/maps/policymap/policymap.go:97-99` shows `PolicyMap` wraps a `bpf.Map` instance that is completely node-local
- Node 1's map failure does not affect Node 2's map (they are separate kernel eBPF map objects)

**Example failure scenario:**
1. Node 1's policymap becomes full (`MaxEntries = 16384` at line 94)
2. Endpoint regeneration on Node 1 fails with `ErrPolicyEntryMaxExceeded` (endpoint/bpf.go:61)
3. Endpoint on Node 1 is degraded
4. Node 2's policymap is unaffected and continues processing packets normally
5. Endpoints on Node 2 remain operational

**No map replication:**
Maps are never replicated or shared between nodes, so:
- No cluster-wide map consistency protocol
- No blocking of other nodes due to one node's map issues
- Each node's packet processing is independent

---

## Evidence

### Q1: Per-Node eBPF Lifecycle
- `pkg/datapath/loader/loader.go:700-731` - ReloadDatapath() per-endpoint compilation entry point
- `pkg/datapath/loader/loader.go:74-89` - loader struct, single instance per node
- `pkg/datapath/loader/compile.go:32-65` - program compilation definitions
- `pkg/datapath/loader/compile.go:90-100` - directoryInfo with node-specific paths
- `pkg/datapath/loader/compile.go:134-170` - getBPFCPU() probes kernel capabilities
- `pkg/datapath/loader/cache.go:56-94` - UpdateDatapathHash() validates node configuration
- `pkg/bpf/pinning.go:126-139` - commitMapPins() pins maps to node-local filesystem
- `pkg/datapath/loader/objects.go:14-36` - lxcObjects represents loaded eBPF objects

### Q2: Deployment Architecture
- `daemon/cmd/daemon.go:85-149` - Daemon struct with single loader instance per node
- `daemon/cmd/daemon.go:90-149` - Per-node state management
- `daemon/cmd/daemon_main.go` - Entry point for DaemonSet pod
- `pkg/endpoint/bpf.go:379-520` - regenerateBPF() handles per-endpoint failures
- `pkg/endpoint/bpf.go:565-572` - Error handling for compilation failures
- `pkg/datapath/loader/loader.go:176-224` - hostRewrites() modifies eBPF variables per-host

### Q3: Policy Distribution vs. Enforcement
- `pkg/policy/k8s/cilium_network_policy.go` - Kubernetes policy watcher
- `pkg/policy/k8s/watcher.go` - Cluster-wide policy distribution
- `pkg/policy/repository.go` - Policy cache per node instance
- `pkg/policy/distillery.go:15-50` - Policy resolution per-endpoint
- `pkg/endpoint/policy.go:177-378` - regeneratePolicy() per-endpoint
- `pkg/endpoint/bpf.go:548-586` - realizeBPFState() per-endpoint compilation
- `pkg/datapath/loader/loader.go:700-731` - ReloadDatapath() per-endpoint, per-node

### Q4: eBPF Map Scoping and State Isolation
- `pkg/maps/policymap/policymap.go:31-34` - Per-endpoint policy maps
- `pkg/bpf/bpffs_linux.go:106-114` - LocalMapPath() and LocalMapName() create endpoint-specific paths
- `pkg/endpoint/bpf.go:87-88` - policyMapPath() returns per-endpoint map path
- `pkg/bpf/pinning.go:75-140` - Pinning mechanism for node-local storage
- `pkg/endpoint/bpf.go:738-743` - policymap.OpenOrCreate() per-endpoint
- `pkg/endpoint/bpf.go:506-512` - policyMapSync() failures affect only the endpoint
- `pkg/maps/policymap/policymap.go:88-95` - MaxEntries per map, independent per node
- `pkg/policy/mapstate.go:82-100` - mapState indexed per-endpoint
