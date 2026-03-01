# Cilium eBPF Datapath Subsystem Handoff Documentation

## Executive Summary

The Cilium eBPF datapath is the core networking and security engine that enforces policies at the kernel level. It replaces traditional iptables with in-kernel eBPF programs that provide superior performance, granularity, and real-time policy enforcement. This document covers the architecture, components, operations, and procedures for maintaining and extending this critical subsystem.

---

## 1. Purpose

### What Problem Does the eBPF Datapath Solve?

The eBPF datapath is Cilium's answer to efficient, fine-grained network policy enforcement in containerized environments:

**Before eBPF (Traditional Approach):**
- iptables-based solutions required userspace processing and syscalls for each connection
- Performance degradation with increasing policy complexity
- No visibility into L7 (application layer) traffic
- Limited granularity—policies based on IP/port only

**With eBPF Datapath:**
- Kernel-resident programs intercept packets at multiple hook points before they reach userspace
- Sub-microsecond decision making with no context switches
- Identity-aware policies (Cilium security identities replace IP-based matching)
- L3/L4 policy enforcement in the kernel; L7 proxying via Envoy
- Native integration with Kubernetes NetworkPolicy semantics

### Why Cilium Uses eBPF Instead of Traditional Approaches

1. **Performance**: Kernel execution eliminates userspace context switches and reduces latency
2. **Efficiency**: Maps (BPF hash tables) enable fast O(1) lookups for policy decisions
3. **Observability**: eBPF programs emit structured events to userspace for monitoring
4. **Programmability**: Same C code compiled to eBPF allows sophisticated logic while maintaining safety
5. **Kernel Verifier**: Guarantees programs cannot crash the kernel, unlike kernel modules
6. **Security**: Fine-grained identity-based policies (not just IP-based)

### Key Responsibilities of the Datapath Subsystem

The eBPF datapath is responsible for:

1. **Policy Enforcement**: Allow/deny decisions for L3/L4 traffic based on security identities
2. **Service Mesh Functionality**: Load balancing, service discovery, and traffic redirection
3. **Connectivity**: Routing packets between pods/containers, including overlay networks (VXLAN, Geneve)
4. **Encryption**: Optional transparent encryption of inter-node traffic
5. **Monitoring & Observability**: Policy verdict logging, packet tracing, drop monitoring
6. **NAT & Connection Tracking**: Stateful connection handling and translation
7. **Endpoint Management**: Managing per-endpoint policy maps and program updates

### Integration with Kubernetes Networking

- **Pod Identity**: Each pod is assigned a unique security identity (numeric label)
- **NetworkPolicy Enforcement**: Kubernetes NetworkPolicy is compiled into eBPF policy maps
- **Service Mesh**: Service IPs are intercepted and redirected to appropriate backends
- **Host Networking**: Host endpoint policies control traffic on the host itself
- **Cluster Mesh**: Multi-cluster networking via overlay tunnels with per-cluster policy enforcement

---

## 2. Dependencies

### Upstream Dependencies (What Calls Into the Datapath)

```
User Applications (in containers/pods)
    ↓
Kernel Network Stack (TCP/IP)
    ↓
eBPF Datapath Programs
```

- **Kernel Hook Points**: XDP (driver entry), TC (traffic control), socket operations
- **Kernel APIs Used**:
  - BPF Maps (hash tables, tail call maps, per-CPU maps)
  - Kernel helpers (route lookups, checksum calculations, etc.)
  - Connection tracking infrastructure
  - Tunnel interfaces (VXLAN, Geneve, WireGuard)

### Downstream Dependencies (What the Datapath Calls)

**Go Code Calling the Datapath:**

1. **pkg/datapath/loader** → Compiles and loads eBPF programs into the kernel
2. **pkg/endpoint** → Manages endpoint-specific policy maps; triggers datapath regeneration
3. **pkg/policy** → Provides policy decisions (allow/deny rules)
4. **pkg/maps/policymap** → Manages per-endpoint policy lookup tables
5. **daemon/cmd** → Daemon initialization and endpoint management

**eBPF Programs Calling Each Other:**

- **Tail Calls**: Programs jump to other programs via cilium_call_policy map
- **Map Sharing**: Multiple programs access the same BPF maps for shared state

### Go ↔ C eBPF Boundary

**Go → eBPF:**
```
1. Go code detects policy change or endpoint creation
2. Go generates endpoint configuration (header files with #defines)
3. Go invokes clang to compile eBPF C programs with injected config
4. Go loads compiled eBPF objects into the kernel via bpf() syscall
5. Go attaches programs to kernel hook points (XDP, TC, etc.)
6. Go populates BPF maps with policy decisions, connection tracking, etc.
```

**eBPF → Go (Data Flow):**
```
1. eBPF programs read maps for policy/routing decisions
2. eBPF programs emit events to perf buffers (monitoring data)
3. Go userspace reads events from perf buffers via epoll
4. Events are decoded and forwarded to monitors/metrics
```

### Kernel APIs the Datapath Relies On

- **BPF Syscall**: `bpf(2)` for program loading, map operations
- **Netlink**: Device enumeration, XDP attachment, TC filter attachment
- **Sysctl**: Kernel parameter checks (e.g., BPF JIT, unprivileged BPF settings)
- **Kernel Helpers**:
  - `bpf_map_lookup_elem()` - Policy lookups
  - `bpf_redirect()` - Packet forwarding
  - `bpf_fib_lookup()` - Routing decisions
  - `bpf_get_current_pid_tgid()` - Process identity
  - And many others defined in `bpf/include/linux/bpf.h`

### External Dependencies

- **cilium/ebpf** (vendor/github.com/cilium/ebpf): Go library for loading eBPF programs
- **LLVM/Clang**: Compiles C → eBPF bytecode
- **Linux Kernel**: 4.14+ for basic BPF support; 5.10+ for optimal features

---

## 3. Relevant Components

### Directory Structure

```
cilium/
├── bpf/                          # eBPF C programs
│   ├── bpf_lxc.c                # Endpoint program (main policy enforcement)
│   ├── bpf_host.c               # Host endpoint program
│   ├── bpf_xdp.c                # XDP entry point
│   ├── bpf_network.c            # Network/underlay datapath
│   ├── bpf_overlay.c            # Overlay network programs
│   ├── bpf_wireguard.c          # WireGuard integration
│   ├── bpf_sock.c               # Socket operations (proto)
│   ├── lib/                      # Shared eBPF libraries
│   │   ├── policy.h             # Policy lookup functions
│   │   ├── lxc.h                # Container-specific logic
│   │   ├── lb.h                 # Load balancing
│   │   ├── nat.h                # NAT/SNAT
│   │   ├── common.h             # Common structures (PolicyKey, etc.)
│   │   ├── maps.h               # Map definitions
│   │   └── ...                  # 50+ other library files
│   ├── include/
│   │   ├── bpf/api.h           # Cilium-specific eBPF APIs
│   │   ├── linux/bpf.h         # Kernel BPF definitions
│   └── ...
│
├── pkg/
│   ├── datapath/                # Datapath abstraction layer
│   │   ├── types/
│   │   │   ├── loader.go        # Loader interface definition
│   │   │   ├── datapath.go      # Datapath interface definition
│   │   │   ├── config.go        # Configuration interfaces
│   │   │   └── ...
│   │   ├── loader/              # eBPF loader & compiler
│   │   │   ├── loader.go        # Main loader implementation
│   │   │   ├── compile.go       # C → eBPF compilation logic
│   │   │   ├── base.go          # Base program compilation
│   │   │   ├── xdp.go           # XDP loading/attachment
│   │   │   ├── tc.go            # TC/SKB program loading
│   │   │   ├── tcx.go           # TCX (newer TC) support
│   │   │   ├── netlink.go       # Netlink API for attachment
│   │   │   ├── template.go      # Template ELF substitutions
│   │   │   ├── hash.go          # Program hashing (caching)
│   │   │   ├── cache.go         # Compiled program caching
│   │   │   └── metrics/         # Loader metrics
│   │   ├── linux/
│   │   │   ├── datapath.go      # Linux datapath implementation
│   │   │   ├── config/          # Config writer for templates
│   │   │   │   └── config.go    # Header file generation
│   │   │   ├── probes/          # Kernel feature detection
│   │   │   │   ├── probes.go    # Kernel capability probing
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── maps/
│   │   │   └── map.go           # Map management (basic)
│   │   ├── ipcache/             # IP → Identity mapping in maps
│   │   └── ...
│   │
│   ├── maps/
│   │   ├── policymap/
│   │   │   ├── policymap.go     # Policy map implementation
│   │   │   └── ...              # Policy map entry types
│   │   ├── ctmap/               # Connection tracking maps
│   │   ├── lxcmap/              # Endpoint metadata maps
│   │   ├── callsmap/            # Tail call maps
│   │   └── ...
│   │
│   ├── endpoint/
│   │   ├── endpoint.go          # Endpoint data structure
│   │   ├── bpf.go               # Endpoint datapath regeneration
│   │   ├── policy.go            # Policy application to endpoint
│   │   └── ...
│   │
│   ├── bpf/                     # Low-level BPF utilities
│   │   ├── map.go               # BPF map operations
│   │   ├── collection.go        # BPF collection loading
│   │   ├── ops_linux.go         # Map update/delete operations
│   │   └── ...
│   │
│   └── ...
│
└── daemon/cmd/
    ├── daemon.go                # Daemon main loop
    ├── config.go                # Configuration handling
    └── ...
```

### Key Files for Datapath Understanding

| File | Purpose |
|------|---------|
| `pkg/datapath/types/loader.go` | `Loader` interface - contract for loading eBPF programs |
| `pkg/datapath/types/datapath.go` | `Datapath` interface - abstraction layer |
| `pkg/datapath/loader/loader.go` | Main loader implementation; `ReloadDatapath()` entry point |
| `pkg/datapath/loader/compile.go` | Compilation: C → object files via clang |
| `pkg/datapath/loader/base.go` | Base program (xdp, host, container) compilation |
| `pkg/datapath/loader/template.go` | ELF substitutions; map renaming for endpoints |
| `bpf/bpf_lxc.c` | Container endpoint program (policy enforcement happens here) |
| `bpf/bpf_host.c` | Host endpoint program |
| `bpf/lib/policy.h` | Policy lookup macro and decision logic |
| `bpf/lib/common.h` | `PolicyKey`, `PolicyEntry` struct definitions |
| `pkg/maps/policymap/policymap.go` | Policy map key/value types and management |
| `pkg/endpoint/bpf.go` | Endpoint datapath regeneration orchestration |
| `pkg/datapath/linux/config/config.go` | Header file generation (lxc_config.h, node_config.h, etc.) |

### The eBPF Loader Pipeline

```
1. ReloadDatapath(endpoint)
   ↓
2. Generate Endpoint Config (header files)
   ├── WriteEndpointConfig() → lxc_config.h
   ├── WriteNodeConfig() → node_config.h
   └── WriteNetdevConfig() → netdev_config.h
   ↓
3. Compile C → Object File
   ├── clang bpf_lxc.c -DLXC_ID=<epid> → bpf_lxc.o
   ├── Map rename substitutions
   └── Variable substitutions (#define replacements)
   ↓
4. Load Object File into Kernel
   ├── Load programs via BPF syscall
   ├── Load maps via BPF syscall
   └── Handle map incompatibilities
   ↓
5. Attach Programs to Kernel Hook Points
   ├── XDP: Device ingress (if enabled)
   ├── TC Ingress: Incoming traffic to endpoint
   └── TC Egress: Outgoing traffic from endpoint
   ↓
6. Populate Maps
   ├── Policy map: identity → allow/deny rules
   ├── CTmap: connection tracking state
   └── Neighbor map: IP → MAC resolution
```

### eBPF Programs Compiled

| Program | Source | Hook Point | Purpose |
|---------|--------|-----------|---------|
| `bpf_lxc` | `bpf/bpf_lxc.c` | TC (ingress/egress) | Container endpoint; policy enforcement, load balancing |
| `bpf_host` | `bpf/bpf_host.c` | TC (ingress/egress) | Host endpoint; host-to-pod policy |
| `bpf_xdp` | `bpf/bpf_xdp.c` | XDP (driver entry) | Early packet processing; DDoS protection, pre-filtering |
| `bpf_network` | `bpf/bpf_network.c` | TC (ingress/egress) | Host networking; underlay/node-to-node traffic |
| `bpf_overlay` | `bpf/bpf_overlay.c` | TC | Overlay network (VXLAN, Geneve) handling |
| `bpf_wireguard` | `bpf/bpf_wireguard.c` | TC | WireGuard encryption integration |
| `bpf_sock` | `bpf/bpf_sock.c` | Socket ops / cgroup | Socket-level policy enforcement (proto) |

### BPF Maps Used by the Datapath

Key maps (defined in `bpf/lib/maps.h`, managed in Go):

| Map | Purpose | Scope |
|-----|---------|-------|
| `cilium_policy_<epid>` | Per-endpoint policy lookup | Per-endpoint |
| `cilium_call_policy` | Tail call jump table for policies | Global |
| `cilium_ct_tcp4_global` | IPv4 TCP connection tracking | Global |
| `cilium_ct_tcp6_global` | IPv6 TCP connection tracking | Global |
| `cilium_ct_any4_global` | IPv4 other protocols CT | Global |
| `cilium_ct_any6_global` | IPv6 other protocols CT | Global |
| `cilium_nat_<direction>4` | IPv4 NAT state | Global |
| `cilium_nat_<direction>6` | IPv6 NAT state | Global |
| `cilium_lxc` | Endpoint metadata (IP, identity) | Global |
| `cilium_ipcache` | IP → identity mappings | Global |
| `cilium_lb_*` | Load balancer state | Global |
| `cilium_nodeport_neigh` | Neighbor discovery cache | Global |

---

## 4. Failure Modes

### eBPF Verifier Failures

**When it happens**: Program loading fails, kernel rejects the compiled eBPF bytecode

**Common causes**:
- **Unsafe memory access**: Accessing memory outside of BPF-allowed regions
- **Unbounded loops**: Verifier detects potential infinite loops
- **Out-of-range jumps**: Branch targets don't exist
- **Missing null checks**: Map lookups not checked before dereference
- **Invalid helper calls**: Calling BPF helper with wrong argument types

**How Cilium handles it**:
```go
// pkg/datapath/loader/netlink.go
var ve *ebpf.VerifierError
if errors.As(err, &ve) {
    // Write full verifier log to disk for debugging
    fmt.Fprintf(os.Stderr, "Verifier error: %s\nVerifier log: %+v\n", err, ve)
}
```

**Recovery**:
- Verifier log is written to `<endpoint-dir>/verifier.log`
- Endpoint regeneration fails; endpoint status set to "Failure"
- Operator must fix the C code causing the issue

### Map Incompatibility Errors

**When it happens**: Existing pinned map doesn't match program expectations (different key/value types, sizes, etc.)

**Common causes**:
- **Program update changes map layout**: e.g., adding fields to `PolicyKey`
- **Size mismatch**: Old map max_entries < new program's needs
- **Type change**: Hash map → array map, etc.

**Error indication**:
```
ebpf.ErrMapIncompatible: map specs differ
```

**How Cilium handles it**:
```go
// pkg/bpf/bpf_linux.go
if errors.Is(err, ebpf.ErrMapIncompatible) {
    // Found incompatible map. Must be removed before re-loading.
    // Cilium pins maps and must clean them up manually.
}
```

**Recovery**:
- Remove the incompatible map: `rm /sys/fs/bpf/cilium/cilium_policy_<epid>`
- Retry endpoint regeneration
- Automatic cleanup happens in template cache revalidation

### Kernel Compatibility Issues

**How Cilium detects them**:
```go
// pkg/datapath/linux/probes/probes.go
probes.HaveProgramHelper(ebpf.SchedCLS, asm.FnFibLookup)  // Returns error if not supported
probes.HaveAttachType(ebpf.SchedCLS, ebpf.AttachTCEgress) // Check attach type support
```

**Common incompatibilities**:
- **BPF JIT not available**: Kernel compiled without CONFIG_BPF_JIT
- **Missing kernel helpers**: Feature added in later kernel (e.g., `bpf_fib_lookup()` added 4.17)
- **Attach type not supported**: Newer attach types (e.g., TCX) need kernel 6.6+
- **BPF type format (BTF) issues**: Kernel doesn't have BTF support

**Examples**:
```go
// daemon/cmd/kube_proxy_replacement.go
if probes.HaveProgramHelper(ebpf.SchedCLS, asm.FnFibLookup) != nil {
    return fmt.Errorf("BPF NodePort services needs kernel 4.17.0 or newer")
}
```

**Recovery**:
- Upgrade kernel or disable features requiring newer kernel versions
- Cilium logs which features are disabled due to kernel limitations

### Map Full / Full Conditions

**When it happens**: BPF map reaches max_entries; new entries cannot be inserted

**Maps that can fill**:
- `cilium_ct_*` (connection tracking): Each connection = 1 entry
- `cilium_nat_*` (NAT): Each NAT translation = 1 entry
- `cilium_policy_<epid>`: Each peer identity × protocol × port = 1 entry

**How Cilium handles it**:
- **CT/NAT maps**: Garbage collection runs periodically to evict idle connections
- **Policy maps**: Pressure metrics reported; operator warned via logs
- **Recovery**: Resize maps via agent configuration (`--bpf-ct-tcp-max`, `--bpf-nat-max`, etc.)

**Metrics**:
```
cilium_policy_endpoint_enforcement_status{enforcement="denied"} # Policy map pressure
```

### Program Loading Failures (Permission, Resource Limits)

**When it happens**: `BPF_PROG_LOAD` syscall fails

**Common causes**:
- **Insufficient privileges**: Not running as root
- **BPF disabled in kernel**: CONFIG_BPF not set
- **Memory limit**: Not enough memory to allocate program/maps
- **Locked memory limit**: RLIMIT_MEMLOCK too small
- **BPF syscall disabled**: Disabled via seccomp or AppArmor

**How Cilium handles it**:
```go
// pkg/datapath/loader/netlink.go
if err := bpf.LoadCollection(spec, opts); err != nil {
    return nil, nil, fmt.Errorf("loading eBPF collection into kernel: %w", err)
}
```

**Recovery**:
- Run Cilium with proper privileges
- Increase locked memory limit: `ulimit -l unlimited`
- Enable BPF in kernel config and recompile kernel

### eBPF Program Crashes (Kernel Panic)

**How it's prevented**: The BPF verifier guarantees programs cannot crash the kernel.

**What CAN happen instead**:
- Program returns `DROP` → Packet silently dropped
- Program returns invalid action → Packet dropped with log
- Program accesses invalid memory → Verifier rejects program

**Monitoring**:
- Monitor `cilium-dbg monitor` for `DROP` events
- Check kernel logs for BPF-related warnings (dmesg)
- Policy enforcement failures logged via monitor subsystem

---

## 5. Testing

### Test Organization

```
cilium/
├── pkg/datapath/loader/      # Loader unit tests
│   ├── loader_test.go         # TestCompileAndLoadDefaultEndpoint, TestCompileFailure*
│   ├── compile_test.go        # Compilation logic tests
│   ├── cache_test.go          # Template caching tests
│   ├── hash_test.go           # Program hashing tests
│   └── ...
├── pkg/endpoint/
│   ├── bpf_test.go            # Endpoint datapath tests
│   └── policy_test.go         # Policy enforcement tests
├── pkg/datapath/linux/config/
│   ├── config_test.go         # Config writer tests
│   └── ...
├── test/
│   ├── k8s/                   # End-to-end K8s integration tests
│   ├── controlplane/          # Control-plane tests
│   └── runtime/               # Legacy runtime tests
└── bpf/tests/                 # eBPF unit tests (C code testing)
    ├── bpf_ct_tests.c         # Connection tracking tests
    └── ...
```

### Unit Testing Patterns

**Loader tests** (`pkg/datapath/loader/loader_test.go`):
```go
func TestCompileOrLoadDefaultEndpoint(t *testing.T) {
    ep := testutils.NewTestEndpoint()  // Create test endpoint
    initEndpoint(t, &ep)
    testReloadDatapath(t, &ep)         // Compile & load
    // Assertions: object exists, maps are present, etc.
}
```

Tests verify:
- Program compilation succeeds
- Object files are generated correctly
- Maps are created and accessible
- Program attachment works

**Configuration tests** (`pkg/datapath/linux/config/config_test.go`):
```go
func TestWriteEndpointConfig(t *testing.T) {
    cfg := configWriterForTest(t)
    // Write config header
    err := cfg.WriteEndpointConfig(w, &dummyEPCfg)
    require.NoError(t, err)
    // Verify header content
}
```

### Integration Testing

**E2E Kubernetes tests** (`test/k8s/`):
- Full cluster setup with real endpoints
- Policy enforcement validation via traffic tests
- Load balancer tests via service access
- Multi-node testing for tunnel/encapsulation

**Control-plane tests** (`test/controlplane/`):
- Policy compilation to eBPF maps
- Service state synchronization
- Endpoint lifecycle management

### eBPF Program Validation

**Before deployment**:
1. Syntax check: clang parsing succeeds
2. Verifier check: kernel verifier accepts program
3. Type checking: C struct layouts match BPF layout assumptions
4. Alignment check: `pkg/datapath/alignchecker` validates C ↔ Go struct alignment

**Alignment validation**:
```go
// bpf/bpf_alignchecker.c - generates alignment errors at compile time
// if C struct layouts don't match Go expectations
```

### Testing Policy Enforcement Without Full Cluster

**Mock endpoint tests**:
```go
ep := testutils.NewTestEndpoint()
datapathCfg := configWriterForTest(t)
// Compile and load program
loader.ReloadDatapath(ctx, ep, stats)
// Verify policy maps are populated
```

**Map inspection**:
- Use `cilium-dbg map` to read policy map entries
- Verify identity → allow/deny mappings

**bpftool inspection**:
```bash
bpftool map show              # List loaded maps
bpftool map dump id <id>      # Dump map contents
bpftool prog show             # List loaded programs
```

### Test Utilities

Key test helpers in `pkg/testutils/`:
- `TestEndpoint` - Mock endpoint with configurable options
- `TestEndpointWithOptions` - Customize behavior
- BPF configuration helpers
- Policy utilities

---

## 6. Debugging

### Troubleshooting eBPF Program Loading Failures

**Step 1: Check kernel version and features**
```bash
# Check kernel version
uname -r

# Check BPF JIT enabled
cat /proc/sys/net/core/bpf_jit_enable

# Probe available kernel features
cilium-dbg probe list
```

**Step 2: Check verifier log**
```bash
# In endpoint directory
cat /var/run/cilium/state/<endpoint-id>/verifier.log

# Look for specific error line and instruction
```

**Step 3: Inspect intermediate artifacts**
```bash
# Check generated header files
cat /var/run/cilium/state/<endpoint-id>/lxc_config.h

# Check object file (requires LLVM tools)
llvm-objdump -S <object-file> > disasm.txt

# Compare with verifier log line numbers
```

### Inspecting eBPF Maps at Runtime

**Using cilium-dbg**:
```bash
# List all maps
cilium-dbg map list

# Dump policy map for endpoint
cilium-dbg map dump cilium_policy_<epid>

# Format: identity:protocol:port → action
```

**Using bpftool**:
```bash
# List maps by ID
bpftool map show

# Dump specific map
bpftool map dump id <map-id>

# Get map statistics
bpftool map stat
```

**Via libbpf tools**:
```bash
# Pin and inspect maps manually
ls -la /sys/fs/bpf/cilium/

# Inspect connection tracking map
bpftool map dump id <ct-map-id> | head -50
```

### Tools for Debugging eBPF Programs

| Tool | Purpose | Usage |
|------|---------|-------|
| `bpftool` | Low-level BPF introspection | `bpftool prog list`, `bpftool map dump` |
| `cilium-dbg monitor` | Observe policy verdicts, drops, traces | `cilium-dbg monitor -vv --namespace myns` |
| `cilium-dbg map` | High-level map inspection | `cilium-dbg map dump cilium_policy_123` |
| `llvm-objdump` | Disassemble eBPF object files | `llvm-objdump -S prog.o` |
| `llvm-readelf` | Inspect ELF sections | `llvm-readelf -S prog.o` |
| `perf` | Profile eBPF execution | `perf record -e bpf -p <pid>` |

### Verifying Policy Enforcement

**Check endpoint policy map population**:
```bash
# List policy decisions for endpoint
cilium-dbg endpoint inspect <epid>

# Check policy map entries
cilium-dbg map dump cilium_policy_<epid>
```

**Key map entry format** (`PolicyKey` → `PolicyEntry`):
```
Key:   [prefix_len][identity][egress/ingress][protocol][port]
Value: [action (allow/deny)][proxy_port][counters]
```

**Monitor policy enforcement**:
```bash
# Watch policy verdicts in real-time
cilium-dbg monitor -t policy

# Output shows: ALLOWED/DENIED identities, L4 rules matched
```

### Logs and Metrics for Datapath Issues

**Key logs to check**:
```bash
# Daemon logs
journalctl -u cilium --no-pager | grep -i datapath

# Look for keywords:
# - "Verifier error" → Program rejected by kernel
# - "loading eBPF collection into kernel" → Loading failure
# - "regeneration.*failed" → Endpoint datapath failed
```

**Metrics** (Prometheus):
```
cilium_datapath_operations_total{operation="compile",status="success/failure"}
cilium_endpoint_regenerations_total{outcome="success/failure"}
cilium_policy_map_pressure # Pressure on policy maps
cilium_bpf_maps_virtual_memory_max_bytes # Memory usage
```

**Debug verbose mode**:
```bash
# Enable verbose datapath debugging
cilium-agent --debug-verbose=datapath
```

### Investigating Performance Problems

**Map lookup performance**:
- Check policy map size: `bpftool map show`
- Hash collision rate: `bpftool map stat`
- For high pressure, increase map size: `--bpf-policy-map-max`

**Program execution latency**:
```bash
# Use perf to profile eBPF execution
perf record -e bpf -p <cilium-agent-pid>
perf report
```

**Connection tracking bottlenecks**:
- Check CT map size and garbage collection frequency
- Monitor `bpf_ct_cleanup_*` metrics
- Increase CT map sizes if frequently full

---

## 7. Adding a New Hook Point

This section describes how to add new eBPF hook points for protocol handling or new policy types.

### Step-by-Step Implementation

#### Step 1: Choose Program Type

Decide which BPF program type to use:

| Type | Attach Point | Use Case |
|------|-------------|----------|
| **XDP** | Device driver (earliest) | Early filtering, DDoS protection |
| **TC (SchedCLS)** | Traffic control layer | Primary policy enforcement |
| **Socket** | Socket operations | Socket-level filtering (connect, bind) |
| **Cgroup** | cgroup2 | Cgroup-based policy |
| **Tracepoint** | Kernel trace events | Observability, monitoring |

For most new policies: **Use TC (SchedCLS)** which attaches to container endpoint programs.

#### Step 2: Create eBPF C Source

**Location**: `bpf/` directory

**Example: Adding a new protocol handler**

Create `bpf/bpf_lxc.c` (or extend existing):
```c
// bpf/lib/myprotocol.h - New protocol logic
static __always_inline int handle_myprotocol(struct __ctx_buff *ctx,
                                              __u16 sport, __u16 dport) {
    // 1. Lookup policy in policy map
    struct policy_key key = {
        .identity = source_identity,
        .nexthdr = IPPROTO_MYPROTO,
        .dport = dport,
    };

    struct policy_entry *entry = map_lookup_elem(&POLICY_MAP, &key);
    if (!entry) {
        return CTX_ACT_DROP;  // Default deny
    }

    // 2. Check if allowed
    if (entry->flags & POLICY_ALLOW) {
        return CTX_ACT_OK;
    }

    return CTX_ACT_DROP;
}

// In bpf_lxc.c main path:
int handle_lxc_in() {
    // ... existing code ...

    // Call new protocol handler
    ret = handle_myprotocol(ctx, sport, dport);
    if (ret != CTX_ACT_OK) {
        return ret;
    }
}
```

**Key design patterns**:
- Use `map_lookup_elem()` to read policy decisions
- Check for NULL returns (policy not found)
- Return standard actions: `CTX_ACT_OK` (allow), `CTX_ACT_DROP` (deny)
- Use tail calls for large programs: `tail_call(ctx, &POLICY_MAP, tail_call_id)`

#### Step 3: Add Loader Logic (Go Code)

**Location**: `pkg/datapath/loader/`

Create or extend loader functions:

```go
// pkg/datapath/loader/custom_hook.go

// compileMycustomProgram compiles the new program
func (l *loader) compileMyCustomProgram(ctx context.Context, ep datapath.Endpoint) (string, error) {
    dirs := l.getCompilationDirectories(ep)

    prog := &progInfo{
        Source: "bpf_myproto.c",
        Output: "bpf_myproto.o",
        OutputType: outputObject,
        Options: []string{
            fmt.Sprintf("-DLXC_ID=%d", ep.GetID()),
            fmt.Sprintf("-DTHIS_MTU=%d", l.nodeConfig.MTU),
        },
    }

    return l.compile(ctx, prog, dirs)
}

// attachMyCustomProgram attaches the compiled program to the kernel
func (l *loader) attachMyCustomProgram(ctx context.Context, ep datapath.Endpoint, progPath string) error {
    spec, err := ebpf.LoadCollectionSpec(progPath)
    if err != nil {
        return err
    }

    coll, _, err := bpf.LoadCollection(spec, &bpf.CollectionOptions{})
    if err != nil {
        return err
    }
    defer coll.Close()

    // Get program from collection
    prog := coll.Programs["cil_myproto"]
    if prog == nil {
        return fmt.Errorf("program cil_myproto not found")
    }

    // Attach to kernel hook (example: TC)
    device, err := safenetlink.LinkByName(ep.InterfaceName())
    if err != nil {
        return err
    }

    return attachSKBProgram(device, prog, "cil_myproto", bpffsDir, parent, tcxEnabled)
}
```

#### Step 4: Integrate into ReloadDatapath

Update the main loader function:

```go
// In pkg/datapath/loader/loader.go

func (l *loader) ReloadDatapath(ctx context.Context, ep datapath.Endpoint, stats *metrics.SpanStat) (string, error) {
    // ... existing compilation ...

    // Add new program compilation
    if option.Config.EnableMyProtocol {
        customProgPath, err := l.compileMyCustomProgram(ctx, ep)
        if err != nil {
            return "", fmt.Errorf("compiling custom protocol: %w", err)
        }

        // Load and attach
        if err := l.attachMyCustomProgram(ctx, ep, customProgPath); err != nil {
            return "", fmt.Errorf("attaching custom protocol: %w", err)
        }
    }

    // ... rest of function ...
}
```

#### Step 5: Register Tail Call Entry (If Using Tail Calls)

If the new hook uses tail calls to jump to policy enforcement:

```c
// bpf/lib/myprotocol.h

#ifndef POLICY_CALL_MAP
#error "POLICY_CALL_MAP must be defined"
#endif

// Register this program as entry point 50 in tail call map
__section("tail_calls/policy")
int entry_myprotocol(struct __ctx_buff *ctx) {
    // Entry point for this protocol's policy
    tail_call(ctx, &POLICY_CALL_MAP, CUSTOM_POLICY_ID);
    return CTX_ACT_DROP;
}
```

Go-side registration:
```go
// pkg/datapath/loader/loader.go - when building tail call map
tailCallKey := uint32(CUSTOM_POLICY_ID)  // 50
tailCallValue := prog.FD()               // Program FD
callsMap.Put(tailCallKey, tailCallValue)
```

#### Step 6: Add Configuration Support

Add configuration options:

```go
// pkg/option/config.go

var (
    // EnableMyProtocol enables the custom protocol handler
    EnableMyProtocol = "enable-myprotocol"
)

// In initConfig():
flags.BoolVar((*bool)(&c.EnableMyProtocol), EnableMyProtocol, false,
    "Enable custom protocol support in the datapath")
```

#### Step 7: Add Policy Decision Entry to Maps

Update policy map structures if needed:

```go
// pkg/maps/policymap/policymap.go

// Extend PolicyKey if new lookup dimensions needed
type PolicyKey struct {
    Prefixlen        uint32 `align:"lpm_key"`
    Identity         uint32 `align:"sec_label"`
    TrafficDirection uint8  `align:"egress"`
    NextHdr          uint8  `align:"protocol"`      // Your protocol number
    DestPortNetwork  uint16 `align:"dport"`
    CustomField      uint16 `align:"custom_field"`  // New field (if needed)
}
```

#### Step 8: Test the Hook

**Unit test**:
```go
// pkg/datapath/loader/loader_test.go

func TestMyCustomProtocolProgram(t *testing.T) {
    ep := testutils.NewTestEndpoint()
    initEndpoint(t, &ep)

    // Enable feature
    option.Config.EnableMyProtocol = true

    // Reload datapath
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    stats := &metrics.SpanStat{}
    _, err := testLoader.ReloadDatapath(ctx, ep, stats)
    require.NoError(t, err)

    // Verify program loaded
    // Verify maps populated
}
```

**Integration test**:
```go
// test/k8s/myproto_test.go

func TestMyProtocolPolicy(t *testing.T) {
    // Create pod with policy
    // Send traffic using custom protocol
    // Verify policy enforcement via cilium-dbg monitor
}
```

#### Step 9: Document the Feature

- Update `bpf/Makefile` if needed to include new sources
- Add feature flag documentation
- Document kernel version requirements (via probes)
- Add to feature matrix in docs

### Example: XDP Hook for Early Filtering

**C Code** (`bpf/bpf_xdp.c`):
```c
SEC("xdp")
int cil_xdp_entry(struct xdp_md *ctx) {
    // Early packet filtering
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    // Check source MAC is known (anti-spoofing)
    struct endpoint_info *ep = map_lookup_elem(&ENDPOINT_MAP, &eth->h_source);
    if (!ep)
        return XDP_DROP;  // Unknown source

    return XDP_PASS;  // Proceed to TC layer
}
```

**Loader** (`pkg/datapath/loader/xdp.go` - extend existing):
```go
// Attaches XDP to physical device for early filtering
func attachXDPProgram(iface netlink.Link, prog *ebpf.Program, progName, bpffsDir string, flags link.XDPAttachFlags) error {
    // Use ebpf-go link API
    l, err := link.AttachXDP(link.XDPOptions{
        Program:   prog,
        Interface: iface.Attrs().Index,
        Flags:     flags,
    })
    if err != nil {
        return err
    }
    // Pin for persistence
    return bpf.PinLink(filepath.Join(bpffsDir, progName), l)
}
```

### Key Considerations

1. **Program Size**: Large programs fail verifier. Use tail calls to split logic.
2. **Memory Layout**: Ensure C struct definitions match Go representations (alignment checker).
3. **Map Persistence**: Pin maps to `/sys/fs/bpf/cilium` for cleanup and reuse.
4. **Kernel Features**: Always probe for required features before attaching.
5. **Performance**: Use percpu maps for high-frequency operations.
6. **Testing**: Test without full cluster using unit tests with mock endpoints.
7. **Backward Compatibility**: Don't break existing policy map formats.

---

## 8. Debugging Deep Dives

### Case Study 1: Policy Not Being Enforced

**Symptoms**: Pods can communicate when policy says they shouldn't.

**Diagnosis**:

1. Check policy map is populated:
```bash
cilium-dbg map dump cilium_policy_<victim-epid> | grep <attacker-identity>
# If empty: policy not compiled to map
```

2. Check endpoint status:
```bash
cilium-dbg endpoint list
# Look for "Denied" / "Allowed" status
```

3. Inspect policy in userspace:
```bash
cilium-dbg policy get | grep -A5 <pod-name>
# Compare with what's in BPF map
```

4. Enable monitor to see traffic:
```bash
cilium-dbg monitor -t policy --namespace <ns> --pod-selector 'app=<label>'
# Watch for DENIED/ALLOWED verdicts
```

5. Check if program is actually attached:
```bash
bpftool net list | grep <device>
# Verify BPF_PROG_TYPE_SCHED_CLS programs are attached
```

**Common root causes**:
- Policy hasn't reached datapath (compilation/map update race)
- Program not attached due to incompatible kernel
- Policy map full (pressure metric check)
- BPF verifier rejected program with `Verifier error` in logs

### Case Study 2: Connection Tracking Issues

**Symptoms**: Connections hang, timeouts, or wrong backend selected for load balancing.

**Diagnosis**:

1. Check CT map occupancy:
```bash
bpftool map show | grep -i "ct_tcp"
bpftool map stat | grep -i "ct_tcp"
# Check if near max_entries
```

2. Inspect CT entry for connection:
```bash
# First, identify connection tuple (src_ip, src_port, dst_ip, dst_port)
bpftool map dump id <ct-map-id> | grep <src_ip>
```

3. Check GC is working:
```bash
# Monitor GC in logs
journalctl -u cilium | grep -i "CT.*cleanup"
```

4. Verify NAT map consistency:
```bash
# For SNAT, check reverse mapping
bpftool map dump id <nat-map-id> | grep <external-ip>
```

**Root causes**:
- CT map full (need garbage collection or larger map)
- Stale CT entries not cleaned (GC disabled)
- NAT map inconsistent with CT (race condition)
- Connection not found in map (kernel packet filtering issue)

---

## 9. Quick Reference

### Common Debugging Commands

```bash
# Monitor policy enforcement
cilium-dbg monitor -t policy -v

# Inspect endpoint datapath
cilium-dbg endpoint inspect <endpoint-id>

# Dump policy map
cilium-dbg map dump cilium_policy_<ep-id>

# List loaded programs
bpftool prog list

# Inspect program code
bpftool prog dump xlated id <prog-id>

# Check kernel BPF support
cilium-dbg probe list

# Monitor event stream
cilium-dbg monitor

# Enable verbose debug mode
cilium-agent --debug-verbose=datapath
```

### Key File Locations

- **BPF programs**: `/bpf/bpf_*.c`
- **eBPF libraries**: `/bpf/lib/`
- **Go loader**: `/pkg/datapath/loader/loader.go`
- **Linux-specific**: `/pkg/datapath/linux/`
- **Endpoint management**: `/pkg/endpoint/bpf.go`
- **Maps**: `/sys/fs/bpf/cilium/` (runtime)
- **State**: `/var/run/cilium/state/` (endpoint configs)
- **Tests**: `/pkg/datapath/loader/*_test.go`

### Environment Variables

```bash
# Enable eBPF verifier log
BPF_VERIFIER_LOG=1

# Custom BPF directory
BPF_DIR=/custom/bpf

# Dry mode (don't load into kernel)
DRY_MODE=1
```

### Configuration Flags (cilium-agent)

```
--bpf-root              BPF filesystem root (default: /sys/fs/bpf)
--bpf-policy-map-max    Max policy map entries (default: 16384)
--bpf-ct-tcp-max        CT TCP map max entries (default: auto-sized)
--bpf-nat-max           NAT map max entries (default: auto-sized)
--enable-policy         Policy enforcement mode (default, never, always)
--datapath              Datapath implementation (linux, fake)
--xdp-mode              XDP attachment mode (driver, generic, best-effort)
--debug-verbose         Verbose debug groups (datapath, policy, flow, etc.)
```

---

## Appendix: eBPF Datapath Architecture Diagram

```
External Network
    ↓
[NIC] → XDP (bpf_xdp.c)
    ↓ [early filtering, DDoS protection]
[Network Stack]
    ↓
[Host Device] → TC Ingress (bpf_network.c or bpf_host.c)
    ↓ [decapsulation, overlay handling]
[Routing/Forwarding]
    ↓
[Virtual Interface (veth)] → TC Ingress (bpf_lxc.c)
    ↓ [← Policy lookup in cilium_policy_<epid>]
[Container]
    ↓ (packets to external)
[Virtual Interface (veth)] → TC Egress (bpf_lxc.c)
    ↓ [← Policy lookup in cilium_policy_<epid>]
[Routing/Forwarding]
    ↓
[Host Device] → TC Egress (bpf_network.c or bpf_host.c)
    ↓ [encapsulation, SNAT, NAT]
[Network Stack]
    ↓
[NIC] → XDP (bpf_xdp.c if attached)
    ↓
External Network
```

**BPF Maps in the Path**:
- `cilium_policy_<epid>`: Identity → allow/deny decisions
- `cilium_ct_tcp4_global`: Connection tracking state
- `cilium_nat_*`: Network address translation
- `cilium_lxc`: Endpoint metadata
- `cilium_ipcache`: IP → Identity mappings
- `cilium_lb_*`: Load balancer state

---

## Summary

The Cilium eBPF datapath is a sophisticated system that marries kernel-resident eBPF programs with userspace Go controllers to provide high-performance, identity-aware network policy enforcement. Understanding its architecture, operation, and debugging techniques is essential for maintaining and extending Cilium in production environments.

Key takeaways:
- **Compilation pipeline**: Config generation → C compilation → eBPF loading → Kernel attachment
- **Policy enforcement**: Identity-based, map-driven lookups in hot paths
- **Failure handling**: Graceful degradation with detailed logging and monitoring
- **Extensibility**: New hooks added via eBPF C code + Go loader logic
- **Debugging**: Rich tooling (cilium-dbg, bpftool) for inspection and troubleshooting

For more detailed information, consult:
- `Documentation/network/ebpf/` - eBPF architecture docs
- `pkg/datapath/types/loader.go` - Loader interface contract
- `bpf/lib/policy.h` - Policy enforcement macros
- Test files for concrete usage examples

Good luck maintaining the Cilium datapath!
