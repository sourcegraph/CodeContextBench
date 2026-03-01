# Cilium eBPF Fault Isolation

## Q1: Per-Node eBPF Lifecycle

### How eBPF programs are compiled, loaded, and attached independently on each node

**Component: Compilation**

Each Cilium agent running on a node independently compiles eBPF programs locally using the `loader` component:

1. **Local Kernel Probing** (`pkg/datapath/loader/compile.go:135-157`):
   - `getBPFCPU()` function probes the kernel at runtime to detect available BPF ISA versions
   - Detects support for BPF v3, v2, or v1 based on kernel helpers: `probes.HaveV3ISA()`, `probes.HaveV2ISA()`
   - This allows per-node CPU-specific optimizations based on kernel capabilities
   - Result is stored in `nameBPFCPU` variable, making compilation node-specific

2. **Template-Based Compilation** (`pkg/datapath/loader/cache.go:26-94`):
   - `objectCache` maintains a per-node cache of compiled eBPF templates
   - `UpdateDatapathHash()` monitors node configuration changes (kernel version, enabled features)
   - When configuration changes, the cache is invalidated and recompilation is triggered
   - Hash is calculated per-node from `LocalNodeConfiguration`

3. **Compilation Process** (`pkg/datapath/loader/compile.go:170-257`):
   - `compile()` function uses clang to compile BPF C code into object files
   - Node configuration (kernel MHz, number of CPUs) is injected via `-D` compiler flags
   - Headers are generated from node-specific state in `pkg/datapath/loader/cache.go:141-142`
   - Each compilation produces a node-local object file stored in the state directory

**Component: Loading and Attachment**

4. **Per-Endpoint Loading** (`pkg/datapath/loader/loader.go:700-732`):
   - `ReloadDatapath()` loads compiled BPF programs for a specific endpoint
   - `templateCache.fetchOrCompile()` retrieves or generates a template for the endpoint configuration
   - Templates are cached locally at `<StateDir>/templates/` (see `pkg/defaults/defaults.go:56-57`)
   - Each endpoint gets its own policy programs loaded independently

5. **Program Attachment via TC/XDP** (`pkg/datapath/loader/loader.go:507-584`, `loader.go:319-334`):
   - Programs attached at Linux Traffic Control (tc) ingress/egress hooks
   - `attachSKBProgram()` attaches to endpoint's veth device interface
   - `attachCiliumHost()` and `attachNetworkDevices()` attach host/device programs
   - Each attachment is per-interface, per-direction, per-node

**Key Insight**: Node-specific configuration affects compilation (kernel features, CPU variant) but failures are isolated because each node compiles independently before any cluster-wide policy is applied.

---

## Q2: Deployment Architecture

### How Cilium's deployment model ensures per-node isolation

**DaemonSet Deployment** (`install/kubernetes/cilium/templates/cilium-agent/daemonset.yaml`):

1. **One Pod Per Node**:
   - Cilium is deployed as a Kubernetes DaemonSet (not Deployment)
   - Each node runs exactly one Cilium agent pod
   - If the DaemonSet is updated, each pod is updated independently, not rolled out cluster-wide
   - Failure of one node's pod does NOT prevent other nodes' pods from running

2. **Per-Node BPF Filesystem Mount** (`daemonset.yaml:809-815`, `daemonset.yaml:602-606`):
   - Each Cilium pod mounts the host's BPF filesystem at `/sys/fs/bpf`
   - This is a per-node filesystem; each node has its own `/sys/fs/bpf` on the host
   - BPF maps and programs are stored per-node in `/sys/fs/bpf/cilium/`
   - If one node's BPF filesystem is corrupted, other nodes' filesystems are unaffected

3. **Independent Agent Initialization** (`daemon/cmd/daemon_main.go`, `daemon/cmd/daemon.go`):
   - Each agent initializes independently in `func newDaemon()`
   - Calls `d.initMaps()` (`daemon/cmd/datapath.go:145-156`) to open/create BPF maps
   - Maps are created in the node-local BPF filesystem
   - If map initialization fails on node A, node B's maps are unaffected

4. **Compilation Lock Per Agent** (`daemon/cmd/daemon.go:119-122`, `pkg/datapath/loader/loader.go:86`):
   - Each agent maintains a `compilationLock` to serialize eBPF compilation
   - Compilation happens locally; no cluster-wide coordination
   - One node's compilation failure doesn't block other nodes' compilation

**Control Plane / Data Plane Split**:

5. **Control Plane**: Kubernetes API Server (central, cluster-wide)
6. **Data Plane**: eBPF programs on each node (distributed, per-node)
   - Policy definitions are distributed via Kubernetes API as CRDs
   - But enforcement happens independently per-node through locally-compiled eBPF
   - Each node enforces policies using its own compiled eBPF bytecode

**Fallback Behavior** (`pkg/datapath/loader/loader.go:280-281`, `pkg/datapath/loader/compile.go:141-157`):
- If a node cannot compile eBPF for its kernel version, it logs an error and continues
- Other nodes continue to operate normally
- The failing node may degrade to fallback mode or log policy enforcement failures
- No cascade to other nodes

---

## Q3: Policy Distribution vs. Enforcement

### How cluster-wide CRDs are translated to per-node eBPF enforcement

**Policy Distribution** (Kubernetes API):

1. **Cluster-Wide Policy Resources**:
   - `CiliumNetworkPolicy` (namespaced) and `CiliumClusterwideNetworkPolicy` (cluster-wide)
   - These are standard Kubernetes Custom Resource Definitions (CRDs)
   - Stored in etcd, accessible to all agents via Kubernetes API watch
   - Distribution is handled by Kubernetes API server, not Cilium

2. **Per-Node Policy Watcher** (`daemon/cmd/daemon.go`, `pkg/k8s/watchers/watcher.go`):
   - Each agent runs a watcher on the Kubernetes API
   - All agents watch the same policy resources
   - When a policy changes, all agents are notified simultaneously via API watch

**Policy Translation (Per-Node Compilation)**:

3. **Policy to eBPF Translation** (`pkg/policy/`, `pkg/endpoint/bpf.go:529-584`):
   - Each agent independently translates policies into eBPF bytecode
   - Translation happens in `Endpoint.SyncPolicy()` and `policyMapSync()`
   - Policy state is stored in `desiredPolicy` and `realizedPolicy` per endpoint
   - Translation is deterministic but node-local (no cross-node dependencies)

4. **Per-Endpoint Policy Maps** (`pkg/maps/policymap/policymap.go:31-39`):
   - Each endpoint gets a policy map: `cilium_policy_v2_<endpoint-id>`
   - Maps are created locally on each node
   - Policy keys: `(identity, traffic_direction, protocol, port, prefix_len)`
   - Policy values: allow/deny decisions with proxy port info
   - Maps are stored per-endpoint in node-local BPF filesystem

5. **Endpoint Regeneration** (`pkg/endpoint/bpf.go`, `pkg/endpoint/regenerator.go`):
   - When a policy changes, affected endpoints are regenerated
   - Regeneration happens per-endpoint, per-node
   - Each agent calculates affected endpoints independently
   - Endpoint compilation via `ReloadDatapath()` with endpoint-specific configuration
   - Template hashing in `pkg/datapath/loader/cache.go:170` ensures consistency within a node

**Why One Node Failure Doesn't Propagate**:

6. **Independent Translation**:
   - Policy resource exists in Kubernetes API (shared)
   - But translation to eBPF happens independently per-node
   - If node A's compiler/verifier rejects a program, node B's compiler still succeeds
   - Node A logs the error but doesn't affect node B's policy enforcement

7. **Endpoint-Specific Configuration** (`pkg/datapath/types/config.go`):
   - Each node has `LocalNodeConfiguration` with kernel-specific settings
   - Endpoints use this node-local config during compilation
   - Same policy + different kernel config = potentially different compiled eBPF
   - This allows graceful degradation per-node

---

## Q4: eBPF Map Scoping and State Isolation

### How eBPF map state is isolated across nodes

**Map Creation and Scoping**:

1. **Per-Node BPF Filesystem Hierarchy** (`pkg/datapath/loader/paths.go:15-75`):
   - Maps are pinned to `/sys/fs/bpf/cilium/` on each node (host-level path)
   - Endpoint maps: `/sys/fs/bpf/cilium/endpoints/<endpoint-id>/`
   - Device maps: `/sys/fs/bpf/cilium/devices/<device-name>/`
   - Links directory: `/sys/fs/bpf/cilium/endpoints/<endpoint-id>/links/`
   - Each path is node-local (on host filesystem, not in container)

2. **Per-Endpoint Maps** (`pkg/maps/policymap/policymap.go:31-39`):
   - Policy map name: `cilium_policy_v2_<endpoint-id>`
   - Endpoint ID is assigned per-container per-node (e.g., 1-65535)
   - Same container on different nodes gets different endpoint IDs
   - Maps with different IDs don't interact

3. **Global vs. Per-Endpoint Maps**:
   - **Global maps** (shared across endpoints on a node):
     - `cilium_call_policy`: Program array for policy tail calls (per-node)
     - `cilium_ct_<dir>_<version>`: Connection tracking (per-node, shared)
     - `cilium_ipcache`: IP to identity mapping (per-node, shared via BPF filesystem)
   - **Per-Endpoint maps**:
     - `cilium_policy_v2_<epid>`: Policy decisions (per-endpoint, per-node)
     - `cilium_calls_<epid>`: Custom calls (per-endpoint, per-node)

4. **BPF Filesystem Pinning** (`pkg/datapath/loader/loader.go:345-376`, `loader.go:516-520`):
   - Maps are pinned to the BPF filesystem during load in `bpf.LoadAndAssign()`
   - Pin path includes node-local state directory: `bpf.TCGlobalsPath()`
   - When a map is pinned, subsequent accesses refer to the pinned path
   - **Isolation mechanism**: Different nodes have different host filesystems

**Network Namespace Isolation**:

5. **Container Network Namespace**:
   - Each container runs in a separate network namespace (on host)
   - Host-facing veth device is in host namespace
   - eBPF programs attach to veth device, enforce policy in host namespace
   - TC hooks on veth enforce ingress/egress policy for the container
   - **Isolation**: eBPF programs access maps via file descriptor, which references the pinned path on the node

6. **Map State Independence**:
   - If node A fails to create a map, node B's maps are unaffected
   - Maps are created independently during agent init (`daemon/cmd/datapath.go:145-156`)
   - Creation happens in parallel (no cross-node synchronization)
   - Map entries are not synchronized across nodes (except through policy updates)

**Failure Scenarios**:

7. **Map Full / Overflow**:
   - If an endpoint's policy map overflows on node A, only that endpoint on node A is affected
   - Other endpoints on node A can still write to their maps
   - All endpoints on node B operate normally (their maps are separate)
   - Agent can lockdown the endpoint if configured (`option.EnableEndpointLockdownOnPolicyOverflow`)

8. **Map Corruption / Loss**:
   - If node A's BPF filesystem is unmounted, maps are lost on node A
   - Node B's BPF filesystem (on different host) is unaffected
   - On node A restart, maps are recreated from scratch (endpoints reinitialized)
   - No cluster-wide impact

9. **Kernel Verifier Rejection**:
   - If a program is rejected by kernel verifier on node A (e.g., due to kernel version mismatch)
   - Node B's kernel may accept the same program (different kernel version, different verifier rules)
   - eBPF source is compiled node-locally with node-specific parameters
   - Compilation can succeed on node B even if it fails on node A

---

## Evidence

### Key Files and References

#### Q1: Per-Node eBPF Lifecycle
- **Compilation Logic**: `pkg/datapath/loader/compile.go:135-257`
  - `getBPFCPU()`: Kernel feature detection
  - `compile()`: Local compilation
  - `compileDatapath()`: Compilation orchestration

- **Caching**: `pkg/datapath/loader/cache.go:26-223`
  - `objectCache`: Per-node template cache
  - `fetchOrCompile()`: Template caching and compilation
  - `UpdateDatapathHash()`: Cache invalidation on config change

- **Loader**: `pkg/datapath/loader/loader.go:74-732`
  - `loader` struct: Per-node loader instance
  - `ReloadDatapath()`: Endpoint program loading
  - `reloadEndpoint()`: Per-endpoint attachment
  - `reloadHostEndpoint()`: Host endpoint attachment

#### Q2: Deployment Architecture
- **DaemonSet Config**: `install/kubernetes/cilium/templates/cilium-agent/daemonset.yaml`
  - BPF filesystem mount: lines 809-815, 602-606
  - Pod-per-node scheduling

- **Agent Initialization**: `daemon/cmd/daemon.go:119-207`, `daemon/cmd/daemon_main.go:1240-1250`
  - `compilationLock`: Per-agent compilation synchronization
  - `initMaps()`: Independent map initialization
  - `CheckOrMountFS()`: Per-node BPF filesystem mounting

#### Q3: Policy Distribution vs. Enforcement
- **Policy Repository**: `pkg/policy/repository.go:34-151`
  - `PolicyContext`: Per-node policy evaluation context
  - Policy resolution per identity

- **Endpoint Policy Sync**: `pkg/endpoint/bpf.go:529-584`
  - `policyMapSync()`: Per-endpoint policy synchronization
  - `applyPolicyMapChangesLocked()`: Per-endpoint policy application

- **Policy Maps**: `pkg/maps/policymap/policymap.go:22-95`
  - `MapName` prefix: `cilium_policy_v2_`
  - `PolicyKey`, `PolicyEntry`: Per-endpoint policy entries

#### Q4: eBPF Map Scoping and State Isolation
- **BPFfs Paths**: `pkg/datapath/loader/paths.go:15-75`
  - `bpffsEndpointDir()`: Per-endpoint BPF directory
  - `bpffsDeviceDir()`: Per-device BPF directory
  - `bpffsEndpointLinksDir()`: Per-endpoint link pins

- **Map Attachment**: `pkg/datapath/loader/loader.go:338-378`, `loader.go:511-584`
  - `attachCiliumHost()`: Host-facing program attachment
  - `reloadEndpoint()`: Endpoint program loading with map pins
  - Map pinning path: `bpf.TCGlobalsPath()` (node-local)

- **Network Isolation**: `Documentation/reference-guides/bpf/progtypes.rst:703-718`
  - Container network namespace isolation via veth
  - Host-facing veth in host namespace where eBPF attaches

### Kernel and Framework References
- **ebpf-go library**: Used for eBPF program loading (`github.com/cilium/ebpf`)
- **Kubernetes API**: Policy distribution via CRD watch
- **Linux kernel**: Per-node eBPF verifier, per-node BPF filesystem
- **TC (Traffic Control)**: Hook point for program attachment
- **veth pairs**: Network namespace isolation mechanism

