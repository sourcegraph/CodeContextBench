# Cilium eBPF Fault Isolation

## Q1: Per-Node eBPF Lifecycle

Cilium compiles, loads, and attaches eBPF programs independently on each node with per-node kernel-specific configuration. This isolation is fundamental to Cilium's fault tolerance.

### Compilation (Node-Specific)
**Component:** `pkg/datapath/loader/compile.go` - The `compile()` function (lines 170-256) and `getBPFCPU()` function (lines 135-157)

- Each node's Cilium agent compiles eBPF programs locally using **clang** targeting BPF bytecode
- Compilation probes the kernel's capabilities at runtime to determine the appropriate BPF instruction set (v1, v2, or v3) via `getBPFCPU()` which calls `probes.HaveV3ISA()`, `probes.HaveProgramHelper()`, and `probes.HaveV2ISA()` in `pkg/datapath/linux/probes`
- Configuration headers (`netdev_config.h`, `filter_config.h`) are written per-node with kernel version and feature flags specific to that node
- **Each endpoint gets a per-node compiled template** via `pkg/datapath/loader/template.go` which creates endpoint-specific maps with names like `cilium_policy_v2_<endpoint_id>` (see `pkg/maps/policymap/policymap.go` line 34: `MapName = "cilium_policy_v2_"`)

### Loading and Attachment (Node-Local)
**Component:** `pkg/datapath/loader/loader.go` - Functions `ReloadDatapath()` (lines 700-731), `reloadEndpoint()` (lines 511-583), and `reloadHostEndpoint()` (lines 319-334)

- The `loader.ReloadDatapath()` method calls `l.templateCache.fetchOrCompile()` to compile the program if needed
- eBPF programs are loaded into the kernel using `bpf.LoadAndAssign()` which loads the ELF binary into that node's kernel
- **Kernel verifier validation is per-node**: If the verifier rejects a program, it fails only on that node (lines 217-243 in `compile.go` show error handling for compilation failures)
- Programs are attached to network interfaces via netlink calls to that node's interface (e.g., `attachSKBProgram()` in `loader.go` lines 547-550 for ingress, 553-555 for egress)
- **Maps are pinned to the node's bpffs**: `ebpf.MapOptions{PinPath: bpf.TCGlobalsPath()}` (line 347, 395, 447 in `loader.go`) ensures maps persist only on that node's filesystem

### Lifecycle Summary
- **Compilation Lock**: `pkg/datapath/loader/base.go` line 392 uses `l.compilationLock.Lock()` to serialize compilation and prevent concurrent compilation attempts on a single node
- **Per-Node State Directory**: `pkg/endpoint/endpoint.go` shows each endpoint has a local `StateDir()` (used at line 704 in `loader.go`)
- **Node-Local Configuration**: `pkg/datapath/loader/base.go` line 63-74 writes node-specific configuration via `l.writeNodeConfigHeader(cfg)` before any compilation

## Q2: Deployment Architecture

Cilium's deployment model isolates each node through **per-node DaemonSet deployment with independent agent lifecycle management**.

### Deployment Model
**Component:** `Documentation/network/kubernetes/concepts.rst` (lines 18-25), `install/kubernetes/cilium/values.yaml` (lines 219-226)

- Cilium is deployed as a **DaemonSet** resource, which Kubernetes automatically schedules one pod per node
- Each Cilium agent pod runs independently with its own process, configuration, and state
- The DaemonSet manifest includes node selectors and tolerations to ensure agents run on specific node types

### Per-Node Agent Initialization
**Component:** `daemon/cmd/daemon.go` (lines 424-430), `pkg/datapath/loader/base.go` (lines 378-546 - `Reinitialize()` method)

- Each agent initializes the datapath independently via `loader.Reinitialize()` which:
  - Creates BPF filesystem (bpffs) directory at `bpf.TCGlobalsPath()` (line 413)
  - Sets up node-specific tunnel devices (line 436)
  - Applies node-specific sysctl settings (line 449)
  - Compiles base datapath programs (XDP, socket LB, overlay, wireguard)
- **Isolation Guarantee**: The call to `l.compilationLock.Lock()` (line 392) ensures only one node's compilation happens at a time, but each node has its own independent initialization sequence

### Failure Isolation Mechanism
**Component:** `pkg/datapath/loader/loader.go` - `ReloadDatapath()` returns error on line 710; if error occurs, only that endpoint on that node fails

- When an endpoint's eBPF program fails to load (e.g., kernel verifier rejects it), the error is scoped to that single endpoint on that single node
- **Control flow**: `ReloadDatapath()` line 708 calls `fetchOrCompile()` which returns an error if compilation/loading fails
- The Cilium agent continues running and other endpoints/nodes are unaffected
- Failed endpoints are logged but don't stop the agent from processing other endpoints

### Control Plane vs. Data Plane Split
- **Control Plane** (cluster-wide): Policy distribution, identity management via kvstore (etcd/consul)
- **Data Plane** (node-local): eBPF program compilation, loading, and execution entirely local to each node
- If one node's agent can't load policies into eBPF, the control plane continues distributing policies to other nodes

## Q3: Policy Distribution vs. Enforcement

Cilium separates **cluster-wide policy distribution** from **per-node enforcement**, enabling node-local fault tolerance.

### Policy Distribution (Cluster-Wide)
**Component:** `pkg/policy/distillery.go` - `policyCache` type (lines 15-50) and `pkg/policy/repository.go`

- Network policies are CiliumNetworkPolicy CRDs stored in Kubernetes API server (cluster-wide state)
- Policies are synchronized to all agents via Kubernetes watchers
- The policy repository maintains the "source of truth" for what rules should exist

### Per-Node Policy Resolution
**Component:** `pkg/policy/distillery.go` - `updateSelectorPolicy()` method (lines 73-100)

- Each node independently resolves policies for its local endpoints
- The `policyCache.updateSelectorPolicy()` method:
  - Calls `cache.repo.resolvePolicyLocked(identity)` (line 94) to resolve policies specific to that node's endpoints
  - Returns a `selectorPolicy` object that's node-local
  - Caches the result per-identity (line 24 shows `policies map[identityPkg.NumericIdentity]*cachedSelectorPolicy`)

### Policy to eBPF Translation (Per-Node Endpoint)
**Component:** `pkg/endpoint/bpf.go` (lines 86-100), `pkg/endpoint/policy.go` (lines 40-53)

- Each endpoint maintains its own policy map at path `bpf.LocalMapPath(policymap.MapName, e.ID)` (line 88 in `bpf.go`)
- The endpoint ID is local to the node (16-bit number, `uint16` from `endpoint/endpoint.go` line 685-686)
- **Policy Map Naming**: `cilium_policy_v2_<endpoint_id>` ensures each endpoint has a unique, node-local policy map
- **Regeneration**: When policies change, only affected endpoints on that node regenerate their programs via `endpoint.Regenerate()` (see `endpoint/regenerator.go` for regeneration logic)

### Compilation Failure Isolation
**Component:** `pkg/datapath/loader/loader.go` line 708-731 - `ReloadDatapath()` method

- If a specific endpoint's eBPF program fails to compile/load:
  - That endpoint's status is updated to indicate regeneration failure
  - **Other endpoints continue operating normally** (they use cached compiled templates from `objectCache`)
  - Policy updates are still applied to other endpoints
  - The node's agent remains healthy and continues serving other endpoints

### Why Distribution Isn't Blocked
- **Decoupling**: Policy distribution (kvstore → agent) is separate from enforcement (agent → eBPF)
- **Asynchronous**: Policy changes trigger endpoint regeneration but don't block distribution to other nodes
- **Error Handling**: If one endpoint's regeneration fails, the controller logs the error but continues with other endpoints
- **Endpoint-Specific Compilation**: Each endpoint uses its own cached compiled template (`objectCache` in `cache.go` lines 26-38), so compilation failure in one endpoint doesn't affect others

## Q4: eBPF Map Scoping and State Isolation

eBPF maps are **entirely node-local** with filesystem-based pinning ensuring complete isolation across nodes.

### Map Creation and Pinning (Node-Local)
**Component:** `pkg/maps/policymap/policymap.go` (lines 23-44), `pkg/datapath/loader/loader.go` (lines 346-350)

- **Endpoint-specific policy maps** are named `cilium_policy_v2_<endpoint_id>` where `endpoint_id` is the 16-bit Cilium internal endpoint ID (local to the node)
- Maps are created and loaded via:
  ```go
  bpf.LoadAndAssign(&obj, spec, &bpf.CollectionOptions{
      CollectionOptions: ebpf.CollectionOptions{
          Maps: ebpf.MapOptions{PinPath: bpf.TCGlobalsPath()},
      },
      ...
  })
  ```
  (lines 345-351 in `loader.go`)
- **PinPath**: Maps are pinned at `bpf.TCGlobalsPath()` which is `/sys/fs/bpf/cilium/` per node (kernel's bpffs mounted locally on each node)

### Map Isolation Mechanisms
**Component:** `pkg/bpf/map_linux.go` - Map struct (lines 65-73), `pkg/datapath/loader/template.go` (lines 159-173)

1. **Filesystem Namespace**: bpffs `/sys/fs/bpf/` is kernel-managed per-node; maps pinned here are only accessible on that node's kernel
2. **Map Naming with Endpoint ID**:
   - Template maps use `templateLxcID` (line 164 in `template.go`)
   - Endpoint maps are renamed using `ELFMapSubstitutions()` which maps `cilium_policy_v2_<template_id>` to `cilium_policy_v2_<actual_endpoint_id>`
   - Each endpoint's policy map is unique per-node

3. **Per-Device Maps**: Device-specific maps like `cilium_calls_netdev_<ifindex>` (line 221 in `loader.go`) are indexed by the node's local interface index

### Global vs. Endpoint Maps
**Component:** `pkg/maps/api.go`, `pkg/datapath/loader/loader.go` (lines 100-102)

- **Global Maps** (shared across endpoints on a node):
  - `cilium_lxc` - endpoint metadata indexed by endpoint ID
  - `cilium_ipcache` - IP-to-identity mapping
  - `cilium_call_policy` - tail call map for policy enforcement
  - These are created once per node and reused by all endpoints

- **Per-Endpoint Maps**:
  - `cilium_policy_v2_<id>` - policy entries specific to that endpoint
  - Each endpoint has its own isolated map instance

### State Isolation Guarantees
**Component:** `pkg/endpoint/regenerator.go` (lines 63-87), `pkg/endpoint/bpf.go` (lines 86-100)

1. **Map Failure Isolation**: If endpoint A's policy map fails to update:
   - The error is caught at `reloadEndpoint()` (line 534 in `loader.go`) which returns the error
   - Endpoint A's regeneration fails and is logged
   - Endpoint B's policy map continues operating (it has its own `cilium_policy_v2_<B_id>` map)

2. **Kernel Verifier per Map**: When a program is loaded that uses endpoint-specific maps, kernel verifier checks map compatibility per-program; failure doesn't affect other programs on other maps

3. **No Cross-Node Map Sharing**: Unlike centralized systems, Cilium maps are:
   - Not shared via network (they're kernel structures in bpffs)
   - Not replicated to other nodes
   - Not backed by a distributed storage system
   - Purely node-local kernel memory

### BPF Links and Pinning
**Component:** `pkg/datapath/loader/loader.go` (lines 760-771, 546)

- TC BPF programs are attached via `bpf_link` structures pinned to `bpffsEndpointLinksDir()` (line 546)
- Each endpoint has its own directory for links: `bpf.CiliumPath()/<endpoint_id>/`
- When an endpoint is deleted, its link directory is removed (lines 766-771): `bpf.Remove(bpffsEndpointLinksDir(...))`
- This ensures no dangling references or cross-endpoint interference

## Evidence

### File Path References
- **Compilation**: `pkg/datapath/loader/compile.go` - `compile()`, `getBPFCPU()`, `compileDatapath()`
- **Loading**: `pkg/datapath/loader/loader.go` - `ReloadDatapath()`, `reloadEndpoint()`, `reloadHostEndpoint()`, `attachSKBProgram()`
- **Caching**: `pkg/datapath/loader/cache.go` - `objectCache`, `UpdateDatapathHash()`
- **Policy Resolution**: `pkg/policy/distillery.go` - `policyCache`, `updateSelectorPolicy()`
- **Endpoint Policy**: `pkg/endpoint/bpf.go` - `policyMapPath()`, `writeInformationalComments()`
- **Policy Maps**: `pkg/maps/policymap/policymap.go` - `MapName`, `PolicyKey`, `PolicyMap`
- **Per-Node Initialization**: `pkg/datapath/loader/base.go` - `Reinitialize()`, `writeNetdevHeader()`, `writeNodeConfigHeader()`
- **Template Generation**: `pkg/datapath/loader/template.go` - `ELFMapSubstitutions()`, `ELFVariableSubstitutions()`

### Key Class and Function References
1. **loader struct** (`pkg/datapath/loader/loader.go:74-89`): Wraps per-node compilation and loading state
2. **ReloadDatapath()** (`pkg/datapath/loader/loader.go:700-731`): Per-node endpoint eBPF loading with per-endpoint error handling
3. **objectCache** (`pkg/datapath/loader/cache.go:26-53`): Per-node template caching with independent compilation
4. **policyCache** (`pkg/policy/distillery.go:15-64`): Per-node policy resolution with per-identity caching
5. **PolicyMap** (`pkg/maps/policymap/policymap.go:97-110`): Per-endpoint map with endpoint-ID-based naming
6. **Endpoint.policyMapPath()** (`pkg/endpoint/bpf.go:86-89`): Returns `bpf.LocalMapPath(policymap.MapName, e.ID)` for endpoint-specific path
7. **bpf.LoadAndAssign()** (`pkg/bpf/`): Pins maps to `bpf.TCGlobalsPath()` for node-local filesystem storage

### Architectural Guarantees

1. **Per-Node Compilation**: Each node independently probes kernel capabilities and compiles accordingly
2. **Per-Node Loading**: eBPF programs are loaded into that node's kernel; verifier failures are node-local
3. **Per-Node Caching**: Compiled templates are cached in memory per-node, compiled once, reused per-endpoint
4. **Per-Node State**: All state (maps, programs, links) stored in `/sys/fs/bpf/` per-node (kernel-managed)
5. **Per-Endpoint Maps**: Each endpoint has unique policy map named with endpoint ID, ensuring isolation
6. **No Global Coordination**: Endpoint regeneration failures don't block policy distribution or other endpoints
7. **Error Isolation**: Compilation/loading failures for endpoint A don't affect endpoints B, C, etc. on the same node or any endpoints on other nodes

This architecture ensures that eBPF datapath failures remain scoped to the affected node, enabling the cluster to continue enforcing policies on other nodes while the failed node either recovers or is replaced.
