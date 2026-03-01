# Cilium eBPF Datapath Subsystem - Team Handoff Document

## 1. Purpose

### What Problem Does the eBPF Datapath Solve?

The eBPF datapath is Cilium's **networking and security engine running in the Linux kernel**. It implements:

- **High-performance packet processing**: Filters, routes, and transforms network traffic without context switches to userspace
- **Network policy enforcement**: Enforces Kubernetes NetworkPolicy and Cilium's CiliumNetworkPolicy at the kernel level
- **Service mesh functionality**: Load balances traffic, implements service discovery, and routes based on identities
- **Connection tracking and NAT**: Maintains connection state and performs network address translation
- **Kernel-native security**: Leverages kernel eBPF hooks for minimal overhead compared to iptables or userspace networking

### Why eBPF Instead of Alternatives?

| Approach | Limitations | Cilium's Choice |
|---|---|---|
| **iptables** | Rule count limits, O(n) lookup, no way to pass identity context between packets | ❌ |
| **Userspace networking** | High overhead from context switches, CPU utilization issues, scalability problems | ❌ |
| **eBPF (Cilium's choice)** | Can access kernel structures directly, O(1) map lookups, sub-microsecond latency, can scale to thousands of endpoints | ✅ |

### Key Responsibilities

1. **Identity-based packet classification**: Determines which workload a packet comes from using security identities
2. **Policy lookup and enforcement**: Uses in-kernel LPM TRIE maps to enforce ingress/egress policies
3. **Service load balancing**: Distributes traffic across backends using various algorithms (random, Maglev hash)
4. **Connection state tracking**: Maintains TCP/UDP connection state with LRU hash maps
5. **Encryption/decryption**: Handles WireGuard and IPsec encryption
6. **IPv6 Segment Routing (SRv6)**: Implements advanced routing for container orchestration

### Kubernetes Networking Integration

Cilium replaces kube-proxy's iptables rules with eBPF equivalents that:
- Intercept service traffic and redirect to appropriate backends
- Support socket-level load balancing (reducing latency)
- Allow transparent proxy integration with Envoy for L7 policy enforcement

---

## 2. Dependencies

### Upstream Dependencies (What Calls the Datapath)

```
daemon/cmd/daemon.go (Cilium Agent)
    ↓
pkg/datapath/linux/datapath.go (Linux Datapath Implementation)
    ↓
pkg/datapath/loader/ (eBPF Loader - Main Entry Point)
    ↓
pkg/endpoint/bpf.go (Endpoint Manager calls ReloadDatapath)
```

**Call Flow for Policy Updates:**
```
endpoint manager: endpoint needs regeneration
    ↓
endpoint.bpf.go:Regenerate()
    ↓
loader.ReloadDatapath(ctx, endpoint, stats)
    ↓
loader.reloadDatapath() → compiles and loads eBPF programs
```

### Downstream Dependencies (What the Datapath Calls)

**Linux Kernel Hooks:**
- **XDP (eXpress Data Path)**: Earliest hook, before main kernel networking stack
- **TC (Traffic Control) Ingress/Egress**: Layer 3 hook via `tc qdisc`
- **TCX (Traffic Control eXtension)**: Newer, more efficient TC replacement
- **Netkit**: Interface type for advanced networking scenarios
- **Socket-level hooks**: `cgroup_sock_ops`, socket send/recv for transparent proxies

**eBPF Maps:**
```
Kernel eBPF Maps
├── Policy Maps (cilium_policy_*): Per-endpoint policy decisions
├── Connection Tracking (cilium_ct_*): Connection state
├── Identity Cache (cilium_ipcache): IP → Security Identity mapping
├── NAT Maps (cilium_nat_*): Port translation state
├── Load Balancer Maps (cilium_lb_*): Service backends
├── Calls Maps (cilium_calls_*): Tail call program arrays
└── ... (20+ other specialized maps)
```

### Go ↔ C Boundary

**How eBPF Programs Are Loaded:**

1. **Compilation Phase**: `pkg/datapath/loader/compile.go`
   - Clang compiles eBPF C code to ELF object files
   - Compiler flags define feature detection results (e.g., `HAVE_XDP_LOAD_BYTES`)
   - Outputs: `bpf_lxc.o`, `bpf_host.o`, `bpf_xdp.o`, etc.

2. **Loading Phase**: `pkg/datapath/loader/netlink.go`
   - Uses libbpf (via `github.com/cilium/ebpf`) to parse ELF files
   - Loads compiled programs into the kernel
   - Creates and initializes eBPF maps
   - Pinned maps to `/sys/fs/bpf/cilium/` for persistence

3. **Attachment Phase**: `pkg/datapath/loader/tc.go`, `tcx.go`, `xdp.go`
   - Attaches programs to network interfaces using netlink
   - Uses tail calls to chain multiple programs together

**Key Constants for Entry Points** (in `pkg/datapath/loader/loader.go:47-62`):
```go
symbolFromEndpoint = "cil_from_container"    // Pod → host direction
symbolToEndpoint   = "cil_to_container"      // Host → pod direction
symbolFromNetwork  = "cil_from_network"      // Network → pod
symbolFromHostNetdevEp = "cil_from_netdev"   // Device → host
symbolToHostNetdevEp   = "cil_to_netdev"     // Host → device
symbolFromHostEp = "cil_from_host"          // Host interface egress
symbolToHostEp   = "cil_to_host"            // Host interface ingress
symbolFromHostNetdevXDP = "cil_xdp_entry"   // XDP entry point
```

### Kernel API Dependencies

**Minimum Kernel Versions:**
- Base eBPF: Linux 4.8+
- eBPF maps: 4.8+
- TC hooks: 4.8+
- XDP: 4.10+
- BPF tail calls: 4.2+ (for chaining programs)
- BPF-to-BPF calls: 5.5+ (for code organization)
- TCX (newer): 6.3+

**Key Kernel Features Probed** (in `pkg/datapath/linux/probes/probes.go`):
- `CONFIG_BPF` and `CONFIG_BPF_SYSCALL`
- `CONFIG_HAVE_EBPF_JIT` and `CONFIG_BPF_JIT_ALWAYS_ON`
- `CONFIG_BPF_EVENTS` for tracing
- `CONFIG_CGROUP_BPF` for cgroup-level policies
- `CONFIG_XDP_SOCKETS` for XDP support
- Helper function availability (via feature probes)

---

## 3. Relevant Components

### Main Source Directories

```
Cilium eBPF Datapath Structure:
├── bpf/                              ← eBPF C programs (kernel code)
│   ├── bpf_lxc.c                    ← Container endpoint datapath (300+ lines)
│   ├── bpf_host.c                   ← Host-side datapath (1000+ lines)
│   ├── bpf_xdp.c                    ← XDP entry point
│   ├── bpf_network.c                ← Network-wide datapath
│   ├── bpf_overlay.c                ← Overlay networking
│   ├── bpf_wireguard.c              ← WireGuard integration
│   ├── lib/                         ← Shared eBPF C libraries
│   │   ├── maps.h                   ← Map definitions and helpers
│   │   ├── tailcall.h               ← Tail call macros
│   │   ├── policy.h                 ← Policy enforcement logic
│   │   ├── nat.h                    ← NAT implementation
│   │   ├── lb.h                     ← Load balancing
│   │   ├── ipv4.h, ipv6.h          ← IP processing
│   │   ├── config.h                 ← Configuration helpers
│   │   └── ... (20+ other libraries)
│   ├── include/                     ← C header files
│   │   ├── ep_config.h              ← Per-endpoint config
│   │   ├── node_config.h            ← Node-wide config
│   │   └── netdev_config.h          ← Network device config
│   ├── Makefile                     ← Build system for eBPF
│   └── tests/                       ← eBPF unit tests
│
├── pkg/datapath/                    ← Go datapath abstraction layer
│   ├── loader/                      ← eBPF Program Loading
│   │   ├── loader.go               ← Main loader (ReloadDatapath entry point)
│   │   ├── compile.go              ← Clang compilation logic
│   │   ├── netlink.go              ← Program loading via libbpf
│   │   ├── tc.go                   ← Traffic Control attachment
│   │   ├── tcx.go                  ← TCX (TC eXtension) attachment
│   │   ├── xdp.go                  ← XDP program attachment
│   │   ├── netkit.go               ← Netkit attachment
│   │   ├── base.go                 ← Base program building
│   │   ├── cache.go                ← Template cache (pre-compiled programs)
│   │   └── metrics/                ← Loader-related metrics
│   │
│   ├── linux/                      ← Linux-specific implementations
│   │   ├── datapath.go             ← Linux datapath implementation
│   │   ├── probes/                 ← Kernel feature detection
│   │   │   ├── probes.go           ← Probe manager and system config
│   │   │   ├── attach_type.go      ← Check supported attach types
│   │   │   └── ... (8+ probe files)
│   │   ├── ipsec/                  ← IPsec integration
│   │   ├── config/                 ← Datapath configuration
│   │   └── ... (other Linux-specific)
│   │
│   ├── maps/                       ← eBPF map definitions (NOT here, see below)
│   ├── types/                      ← Interfaces and types
│   │   ├── loader.go               ← Loader interface definition
│   │   ├── config.go               ← Configuration types
│   │   └── ... (other types)
│   └── ... (other datapath components)
│
├── pkg/maps/                        ← eBPF Map Definitions (Go wrappers)
│   ├── policymap/                  ← Policy enforcement maps
│   │   └── policymap.go            ← Per-endpoint policy map structure
│   ├── ctmap/                      ← Connection tracking maps
│   ├── ipcache/                    ← IP to identity cache
│   ├── lbmap/                      ← Load balancer backend maps
│   ├── nat/                        ← NAT maps
│   ├── callsmap/                   ← Tail call maps
│   ├── nodemap/                    ← Node information maps
│   ├── neighbor*/                  ← Neighbor/ARP maps
│   └── ... (25+ other map types)
│
├── pkg/ebpf/                        ← Low-level eBPF Go APIs
│   ├── ebpf.go                      ← eBPF program utilities
│   ├── map.go                       ← Map utilities
│   ├── map_register.go              ← Map registration
│   └── doc.go
│
├── pkg/bpf/                         ← BPF utilities
│   ├── collection.go                ← ELF collection loading/validation
│   ├── helpers.go                   ← BPF helper functions
│   └── ... (other utilities)
│
└── pkg/endpoint/                    ← Endpoint Manager
    ├── bpf.go                       ← Calls ReloadDatapath() for endpoint
    └── ... (endpoint management)
```

### Critical Files for Understanding eBPF Program Loading

**Essential Reading Order:**

1. **Entry Points**
   - `pkg/datapath/types/loader.go` (22 lines) - Define Loader interface
   - `pkg/datapath/linux/datapath.go` (100+ lines) - Linux implementation

2. **Program Compilation**
   - `pkg/datapath/loader/compile.go` (100-200 lines) - Clang compilation
   - `pkg/datapath/loader/loader.go` (200-300 lines) - Main loader logic

3. **Program Loading & Attachment**
   - `pkg/datapath/loader/netlink.go` (500+ lines) - libbpf-based loading
   - `pkg/datapath/loader/tc.go` (300+ lines) - TC attachment
   - `pkg/datapath/loader/tcx.go` (150+ lines) - TCX attachment
   - `pkg/datapath/loader/xdp.go` (200+ lines) - XDP attachment

4. **eBPF Program Logic**
   - `bpf/lib/maps.h` (200+ lines) - Map definitions and tail call helpers
   - `bpf/lib/policy.h` (300+ lines) - Policy enforcement
   - `bpf/bpf_lxc.c` (1000+ lines) - Container datapath
   - `bpf/bpf_host.c` (1500+ lines) - Host datapath

5. **Maps & Policy**
   - `pkg/maps/policymap/policymap.go` - Policy map structure
   - `pkg/maps/callsmap/callsmap.go` - Tail call maps

### eBPF Program Structure

Each eBPF program has multiple sections (entry points):

**In bpf_lxc.c:**
- `cil_from_container`: Ingress (container → host)
- `cil_to_container`: Egress (host → container)

**In bpf_host.c:**
- `cil_to_host`: Ingress to cilium_host interface
- `cil_from_host`: Egress from cilium_host interface
- `cil_from_netdev`: Ingress on physical devices
- `cil_to_netdev`: Egress on physical devices
- `cil_xdp_entry`: XDP hook entry point

### eBPF Maps (Key Data Structures)

**Policy Enforcement:**
- `cilium_call_policy`: Tail call map for ingress policy programs (program array)
- `cilium_egresscall_policy`: Tail call map for egress policy programs
- `cilium_policy_<endpoint_id>`: Per-endpoint LPM TRIE map (identity:port:direction → allow/deny)

**Connection Tracking:**
- `cilium_ct_global_tcp`: Global TCP connection tracking (IPv4/IPv6)
- `cilium_ct_global_udp`: Global UDP connection tracking

**IP-Identity Mapping:**
- `cilium_ipcache`: IP address → Security Identity mapping (hash map)

**Load Balancing:**
- `cilium_lb_*`: Various load balancer maps for services
- `cilium_srv6_*`: SRv6 service maps

**Tail Calls:**
- `cilium_calls_<id>`: Per-endpoint program array for tail calls
- `cilium_custom_calls_<id>`: Custom program hooks

**Other:**
- `cilium_ct_*`: IPv4/IPv6 connection tracking
- `cilium_nodeport_*`: NodePort service maps
- `cilium_nat_*`: NAT state tracking
- `cilium_encrypt_*`: Encryption metadata
- `cilium_metrics`: Metrics collection

---

## 4. Failure Modes

### eBPF Program Loading Failures

#### Verifier Failures

**Problem**: The eBPF verifier rejects program loads if they violate kernel safety rules.

**Common Causes**:
- **Unbounded loops**: eBPF can't have unbounded loops (kernel prevents DoS)
- **Out-of-bounds memory access**: Accessing memory beyond packet or stack bounds
- **Invalid register usage**: Using uninitialized registers
- **Complexity limit**: Program exceeds instruction limit (~100k instructions per kernel version)

**Detection**:
```go
// pkg/datapath/loader/netlink.go:loadDatapath()
// Returns error with verifier log:
// "invalid memory access for read from context addr=offset+size"
```

**Recovery**:
1. Check kernel logs: `dmesg | grep -i "ebpf\|bpf"`
2. Enable verifier logging (rebuilds with debug flags)
3. Simplify program logic or split into tail calls

#### Map Incompatibility Failures

**Problem**: Maps can't be loaded if their structure (key/value size, type, max entries) differs from pinned versions.

**Common Causes**:
- Changing endpoint ID size (uint8 → uint16)
- Changing key/value structures in policy maps
- Max entries mismatch between runs

**Detection** (in `pkg/bpf/collection.go:256-260`):
```go
// MapSpecs that differ (type/key/value/max/flags) from their pinned versions
// will result in an ebpf.ErrMapIncompatible
```

**Recovery**:
```bash
# Unpin incompatible maps
sudo rm /sys/fs/bpf/cilium/tc/globals/cilium_policy_*
# Restart agent
systemctl restart cilium
```

#### Permission Failures

**Problem**: eBPF requires CAP_BPF and CAP_PERFMON (or CAP_SYS_ADMIN on older kernels).

**Common Causes**:
- Running Cilium in unprivileged container
- SELinux policies blocking eBPF syscalls
- AppArmor restrictions

**Detection**:
```
error: "failed loading eBPF collection: permission denied"
```

**Recovery**:
1. Run with `--cap-add=CAP_BPF --cap-add=CAP_PERFMON`
2. Or grant `--cap-add=CAP_SYS_ADMIN` (broader)
3. Disable SELinux or update policies

### eBPF Map Failures

#### Map Full Failures

**Problem**: Connection tracking or policy maps reach max_entries limit.

**Impact**:
- New connections drop silently
- Packets matching new identities are dropped
- Service load balancing fails for new backends

**Detection**:
```bash
# Check map pressure
cilium-dbg bpf map list
# Look for pressure > 0.1 (threshold in policymap.go)
```

**Monitoring** (metrics):
```go
// pkg/metrics/metrics.go:
BpfMapPressure // Map utilization as percentage
BpfMapSize     // Current entries vs max entries
```

**Recovery**:
1. Increase `--bpf-map-dynamic-size-ratio` (for dynamic sizing)
2. Increase max entries in map definitions
3. Restart agent to recreate maps with new size

#### Map Update Failures

**Problem**: Updating policy or NAT entries in kernel maps fails.

**Common Causes**:
- Map locked by multiple processes
- Memory exhaustion in kernel
- Incompatible data format

**Detection**:
```go
// pkg/endpoint/bpf.go:
// "cilium_call_policy: delete: key does not exist"
```

**Impact**:
- Policies don't apply to traffic
- Old policies persist even after update
- Service routing becomes inconsistent

### Kernel Compatibility Issues

#### Feature Detection Failures

Cilium probes for kernel features at startup (`pkg/datapath/linux/probes/probes.go`):

```go
type SystemConfig struct {
    ConfigBpf          KernelParam  // CONFIG_BPF
    ConfigBpfSyscall   KernelParam  // CONFIG_BPF_SYSCALL
    ConfigCgroupBpf    KernelParam  // CONFIG_CGROUP_BPF
    // ... 30+ kernel config checks
}
```

**If critical features missing:**
```
error: "BPF requires CONFIG_BPF_SYSCALL (see docs/)"
```

**Recovery**:
- Check `/boot/config-$(uname -r)` for missing CONFIGs
- Recompile kernel with required options
- Or use system with adequate kernel support

#### Helper Function Unavailable

**Problem**: eBPF program calls a kernel helper not available in this kernel version.

**Example**:
```
error: "XDP program requires bpf_xdp_load_bytes (kernel 5.8+)"
```

**Detection** (in `pkg/datapath/linux/probes/probes.go`):
```go
ProgramHelpers map[ProgramHelper]bool  // Each helper is probed
// XDP: { bpf_xdp_load_bytes, bpf_xdp_store_bytes, bpf_xdp_get_buff_len }
// TC: { bpf_skb_load_bytes, bpf_skb_store_bytes, ... }
```

**Recovery**:
1. Disable features requiring newer helpers: `--bpf-skip-feature=xyz`
2. Upgrade kernel

### Configuration Errors

#### Invalid Node Configuration

**Problem**: Node configuration header generation fails.

**Detected in**: `pkg/datapath/loader/template.go`

**Common Causes**:
- Invalid CIDR ranges in node configuration
- Conflicting endpoint ID ranges
- Invalid network device specification

**Detection**:
```
error: "invalid node configuration: invalid CIDR"
```

#### Endpoint-Specific Failures

**Problem**: Specific endpoint policy can't be loaded.

**Examples**:
- Port range overflow
- Policy identity conflict
- Invalid protocol specifications

**Detection** (in `pkg/endpoint/bpf.go:Regenerate()`):
```
error: "failed to generate endpoint: invalid policy entry"
```

**Recovery**:
1. Check endpoint logs: `kubectl logs -c agent <pod> | grep endpoint-id`
2. Verify endpoint configuration: `cilium endpoint get <id>`
3. Look for conflicting policies

### Recovery and Mitigation

#### Automatic Recovery Mechanisms

1. **Template Cache** (`pkg/datapath/loader/cache.go`):
   - Pre-compiles datapath templates
   - Falls back to cached version on compilation failure
   - Prevents complete datapath loss during compilation errors

2. **Map Pinning** (`pkg/bpf/`:
   - Maps persist at `/sys/fs/bpf/cilium/` across restarts
   - Avoids losing connection tracking state
   - Can be cleared with `cilium bpf reset` if needed

3. **Graceful Degradation**:
   - If XDP fails, falls back to TC
   - If TCX fails, falls back to legacy TC
   - If policy loading fails, endpoint isolation applies

#### Manual Recovery

```bash
# Full BPF reset (dangerous - drops all state)
cilium bpf reset

# Reload datapath for specific interface
cilium-dbg reload-datapath

# Check loader status
cilium-dbg endpoint status | grep datapath

# View verifier logs (if debug enabled)
cat /sys/kernel/debug/tracing/trace_pipe | grep BPF
```

---

## 5. Testing

### Testing Architecture

```
Test Pyramid:
├── eBPF Unit Tests (bpf/tests/)
├── Go Integration Tests (pkg/datapath/loader/*_test.go)
├── End-to-End Cluster Tests (test/)
└── CI/CD Pipeline Validation
```

### eBPF Unit Tests

**Location**: `bpf/tests/*.c`

**Framework**: Custom BPF test harness (no external framework)

**Test Structure**:
```c
// Example from Documentation/contributing/testing/bpf.rst
__section(CALLS_MAP_ID)
int __check_entrypoint(struct __ctx_buff *ctx) {
    SETUP  // Pre-populate maps/data (optional)
    // RUN test logic
    CHECK(...) // Assertions
    return 0;
}
```

**Key Test Patterns**:
1. **PKTGEN**: Generate test packets
2. **SETUP**: Pre-populate maps
3. **CHECK**: Actual test program
4. **Assertions**: Validate packet/map state

**Testing Tail Calls**:
```c
// From bpf/tests/drop_notify_test.c
// Can't directly return from tail call, so:
// 1. Use PKTGEN to create packet context
// 2. Use SETUP to configure maps
// 3. Use CHECK to invoke tail call
// 4. Check results in map updates
```

**Running BPF Tests**:
```bash
cd bpf
make tests
# Requires kernel with:
# - CONFIG_BPF_SYSCALL
# - CONFIG_BPF_EVENTS
# - BPF_PROG_RUN support (kernel 5.8+)
```

### Go Integration Tests

**Location**: `pkg/datapath/loader/*_test.go`

**Test Files**:
- `loader_test.go`: Loader functionality
- `compile_test.go`: Compilation process
- `tc_test.go`: TC attachment
- `tcx_test.go`: TCX attachment
- `xdp_test.go`: XDP attachment
- `netlink_test.go`: Program loading

**Key Test Functions**:
```go
// pkg/datapath/loader/loader_test.go
func testReloadDatapath(t *testing.T, ep *testutils.TestEndpoint)
func TestCompileAndLoad(t *testing.T)
func TestEndpointHash(t *testing.T)  // Detects config changes
```

**Test Infrastructure**:
```go
// pkg/datapath/loader/loader_test.go:newTestLoader()
// Creates minimal test environment with:
// - Configuration
// - Sysctl mock
// - Prefilter mock
// - Compilation lock
```

**Requires**:
- Linux kernel with BPF support
- Clang/LLVM for compilation
- CAP_BPF or CAP_SYS_ADMIN
- Usually run as root only

### Testing Policy Enforcement

**No direct unit tests**, but verified via:

1. **Integration tests** (`test/bpf/`):
   ```go
   // test/runtime/policy.go
   // Full Kubernetes cluster with NetworkPolicy
   // Validates that policies actually drop/allow packets
   ```

2. **Policy map inspection**:
   ```bash
   # See what's in policy map for endpoint
   cilium-dbg bpf policy get <endpoint_id>

   # Expected format:
   # POLICY   DIRECTION   TRAFFIC_VALIDATION
   # 12345    ingress     allow on port 8080
   ```

3. **Packet tracing**:
   ```bash
   # Monitor dropped packets
   cilium-dbg monitor --type drop

   # Monitor policy verdicts
   cilium-dbg monitor --type policy-verdict
   ```

### Test Patterns for eBPF Programs

#### Testing Without Full Cluster

```bash
# Create minimal test endpoint
cilium-dbg endpoint create <pod-name> <interface> <ip>

# Add policy
kubectl apply -f - <<EOF
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: test-deny
spec:
  endpointSelector:
    matchLabels:
      role: test
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: allowed
EOF

# Verify it loaded
cilium endpoint get <id> -o json | jq .policy
```

#### Testing Host Firewall

```c
// In bpf_host.c, controlled by ENABLE_HOST_FIREWALL
#ifdef ENABLE_HOST_FIREWALL
  ret = invoke_tailcall_if(is_defined(ENABLE_HOST_FIREWALL),
      CILIUM_CALL_IPV4_HOST_POLICY,
      tail_handle_ipv4_host_policy,
      &ext_err);
#endif
```

**Test via**:
```bash
# Enable in values
--enable-host-firewall=true

# Verify host policies load
cilium endpoint get 1 -o json | jq '.host_firewall_enforced'
```

### Integration Test Entry Points

**Main test suites** (`test/runtime/`):
- `policy.go`: Network policy enforcement
- `lb.go`: Load balancing / Services
- `connectivity.go`: Basic connectivity
- `monitor.go`: Monitoring and debugging

**Running Integration Tests**:
```bash
cd test/
# Requires Docker, Kind cluster, ~30 minutes
make test-integration
```

### Debugging Tests

**Enable debug output**:
```bash
# During compilation (generates verifier logs)
make VERBOSE=1

# During tests
TEST_VERBOSE=1 go test ./pkg/datapath/loader/...

# BPF-level debug output
# In bpf code:
#include "lib/dbg.h"
printk("debug message: %d", value);
# Appears in: /sys/kernel/debug/tracing/trace_pipe
```

---

## 6. Debugging

### Troubleshooting Workflow

```
1. Symptom observation
    ↓
2. Check Cilium agent logs
    ↓
3. Inspect endpoint state
    ↓
4. Monitor live traffic
    ↓
5. Examine eBPF maps
    ↓
6. Check kernel compatibility
    ↓
7. Review datapath code
```

### Tool: cilium-dbg

**Location**: Binary in container at `/usr/bin/cilium-dbg`

**Key Subcommands**:

```bash
# Endpoint inspection
cilium-dbg endpoint list              # List all endpoints
cilium-dbg endpoint get <id>          # Details for endpoint
cilium-dbg endpoint status <id>       # Policy state
cilium-dbg endpoint log <id>          # Enable debug for endpoint

# Map inspection
cilium-dbg bpf map list               # Show all maps + pressure
cilium-dbg bpf map dump <map_name>    # Dump map contents
cilium-dbg bpf policy get <id>        # Show policy for endpoint
cilium-dbg bpf ct list <id>           # Show connections for endpoint

# Monitoring
cilium-dbg monitor                    # Live traffic monitoring
cilium-dbg monitor --type drop        # Only drops
cilium-dbg monitor --type policy-verdict

# Configuration
cilium-dbg config                     # Show current config
cilium-dbg config get <option>        # Get specific option
```

### Tool: cilium monitor

**Live monitoring of datapath events:**

```bash
kubectl exec -it -n kube-system cilium-xxxxx cilium-dbg -- monitor

# Example output:
# XX drop (Policy denied) ingress 12345->0 from identity=999 to 12346
# XX debug capture from identity=999 (TCP 1.2.3.4:52341->5.6.7.8:80)
# XX policy-verdict L3/L4 allow ingress from identity=999 to port=80/tcp
```

**Event Types**:
- `drop`: Packet dropped (reason in parentheses)
- `policy-verdict`: Policy decision
- `trace`: Packet trace events
- `debug`: Debug messages from eBPF code
- `capture`: Captured packet payload

### Tool: bpftool

**Lower-level kernel BPF introspection:**

```bash
# List all loaded eBPF programs
sudo bpftool prog list

# Show program details
sudo bpftool prog show id <id>

# Show program instruction dump
sudo bpftool prog dump xlated id <id>

# List eBPF maps
sudo bpftool map list

# Dump specific map
sudo bpftool map dump name cilium_ipcache

# View map statistics
sudo bpftool map stat

# Pin/unpin programs (usually Cilium does this)
sudo bpftool prog pin id <id> /sys/fs/bpf/my_prog
```

### Inspecting eBPF Maps

**Important maps to monitor:**

```bash
# Policy enforcement
cilium-dbg bpf policy get <endpoint_id>
# Shows: POLICY | DIRECTION | TRAFFIC_VALIDATION

# Connection tracking
cilium-dbg bpf ct list <endpoint_id>
# Shows: source_ip:port | dest_ip:port | state | lifetime

# IP identity mapping (critical for policy!)
cilium-dbg bpf map dump cilium_ipcache | head -20
# Format: ip:prefix_length -> identity | flags

# Load balancer backends
cilium-dbg bpf map dump cilium_lb_services | head -10
# Shows: service_id -> backend pool

# Map pressure (important for capacity planning)
cilium-dbg bpf map list | grep -E "pressure|Name"
# Pressure > 0.1 indicates capacity concerns
```

### Verifying Policy Enforcement

**Step 1: Check policy is loaded**
```bash
# On pod that should have policy:
cilium-dbg endpoint get <pod_id> -o json | jq '.policy'

# Expected output: policy enabled, revision number, enforcement status
```

**Step 2: Inspect policy map**
```bash
# Get policy map for endpoint
cilium-dbg bpf policy get <endpoint_id> | grep -E "allow|deny"

# Should see entries like:
# 12345/80    ingress    allow  (L4/port allow)
# 12345/*     ingress    deny   (identity deny unless explicitly allowed)
```

**Step 3: Monitor actual traffic**
```bash
# In one terminal, start monitor
cilium-dbg monitor --type policy-verdict | grep <endpoint_id>

# In another, send traffic and check verdict:
# XX policy-verdict L3 allow ingress from identity=<src> to <dst>
# XX drop (Policy denied) ingress if not allowed
```

**Step 4: Check identity assignment**
```bash
# Get security identity for pod
cilium-dbg endpoint get <pod_id> -o json | jq '.identity'

# Check what IP maps to that identity
cilium-dbg bpf map dump cilium_ipcache | grep 10.0.0.100
# Expected: 10.0.0.100:32 -> identity=12345 ...
```

### Debugging Program Loading Failures

**If datapath reload fails:**

```bash
# 1. Check agent logs
kubectl logs -c agent <pod> --tail=100 | grep -i "ebpf\|load\|error"

# 2. Get specific error
kubectl logs -c agent <pod> -c=agent --timestamps=true | tail -20

# Common errors:
# - "BPF program verifier rejection"
# - "map incompatible with existing map"
# - "program too large for kernel"
```

**Enable debug mode:**
```bash
# In values.yaml:
--bpf-compiler-flags="-DDEBUG_BTF"

# Or via API:
cilium-dbg config set bpf-compiler-flags="-DDEBUG_BTF"
```

### Kernel-Level Debugging

**View BPF verifier logs:**
```bash
# Connect to container/node
sudo cat /sys/kernel/debug/tracing/trace_pipe | grep BPF

# If verifier log from Cilium compilation (if debug enabled):
# In agent logs, detailed error with instruction number
```

**Check current BPF programs attached:**
```bash
# Query interface for attached programs
sudo ip link show <device>

# XDP program:
sudo ip link show eth0 | grep -i xdp

# TC programs (older format):
sudo tc filter show dev eth0 ingress

# TCX programs (newer format):
sudo ip link show eth0 | grep tcx
```

### Performance Debugging

**Check eBPF CPU usage:**
```bash
# Via metrics
cilium-dbg config get metrics
# Look for: cilium_ebpf_* metrics

# More detailed: enable per-cpu stats
--ebpf-stats=true

# Check map operation latency
# Metrics: cilium_map_operations_duration_seconds
```

**Check map efficiency:**
```bash
# Policy map lookups per second
cilium-dbg bpf map dump cilium_policy_<id> | wc -l
# Rule count should be << max_entries (default 16384)

# Hash bucket distribution (for CT map)
bpftool map show name cilium_ct_global_tcp
# Check average bucket depth, ideally ~1.0
```

### Tools Summary

| Tool | Purpose | Example |
|------|---------|---------|
| `cilium-dbg` | Cilium CLI inspection | `cilium-dbg endpoint get 123` |
| `cilium monitor` | Live traffic events | `cilium monitor --type drop` |
| `bpftool` | Kernel BPF introspection | `bpftool prog list` |
| `tc` | TC filter inspection | `tc filter show dev eth0` |
| `ip link` | Network device state | `ip link show eth0` |
| `dmesg` | Kernel logs | `dmesg \| grep BPF` |
| `strace` | Syscall tracing | `strace -e bpf cilium-agent` |

---

## 7. Adding a New Hook

### Step-by-Step: Adding a New eBPF Attach Point

Let's walk through adding a hypothetical "container exit" hook.

#### Step 1: Define the Hook in eBPF

**File**: `bpf/bpf_lxc.c`

```c
// Add new entry point function
__section("to-container-exit")
int cil_exit_from_container(struct __sk_buff *ctx) {
    __u32 endpoint_id = get_endpoint_id(ctx);

    /* Perform exit-time logic */
    perform_connection_cleanup();
    perform_accounting();

    return CTX_ACT_OK;
}
```

**Or in shared library** (`bpf/lib/exit.h`):
```c
// Shared exit logic
static __always_inline int handle_exit(struct __sk_buff *ctx) {
    // Exit handler logic
    return 0;
}
```

#### Step 2: Create Go Loader Functions

**File**: `pkg/datapath/loader/exit.go` (new file)

```go
package loader

import (
    "fmt"
    "github.com/cilium/ebpf"
    "github.com/vishvananda/netlink"
)

// attachExitProgram attaches the container exit program
func attachExitProgram(device netlink.Link, prog *ebpf.Program,
    progName, bpffsDir string) error {
    if prog == nil {
        return fmt.Errorf("program %s is nil", progName)
    }

    // Exit handlers might attach to qdisc egress at a special priority
    // Implementation depends on kernel hook point
    // For example, attach to device egress via TC at priority 999

    return attachSKBProgram(device, prog, progName,
        bpffsDeviceLinksDir(bpf.CiliumPath(), device),
        netlink.HANDLE_MIN_EGRESS, option.Config.EnableTCX)
}
```

#### Step 3: Update the Main Loader

**File**: `pkg/datapath/loader/loader.go`

```go
// Add symbol constant
const (
    symbolFromContainerExit = "cil_exit_from_container"  // New line
    // ... existing symbols
)

// Add to ReloadDatapath or reloadDatapath method
func (l *loader) reloadDatapath(ep datapath.Endpoint,
    spec *ebpf.CollectionSpec) error {

    device, err := safenetlink.LinkByName(ep.InterfaceName())
    if err != nil {
        return fmt.Errorf("retrieving device: %w", err)
    }

    coll, commit, err := loadDatapath(spec,
        ELFMapSubstitutions(ep),
        ELFVariableSubstitutions(ep))
    if err != nil {
        return err
    }
    defer coll.Close()

    // Existing attachments...

    // NEW: Attach exit program
    if prog := coll.Programs[symbolFromContainerExit]; prog != nil {
        if err := attachExitProgram(device, prog,
            symbolFromContainerExit,
            bpffsDeviceLinksDir(bpf.CiliumPath(), device)); err != nil {
            return fmt.Errorf("attaching exit program: %w", err)
        }
    }

    if err := commit(); err != nil {
        return fmt.Errorf("committing bpf pins: %w", err)
    }

    return nil
}
```

#### Step 4: Register Map If Needed

**File**: `pkg/maps/exitmap/exitmap.go` (if you need a custom map)

```go
package exitmap

import (
    "fmt"
    "github.com/cilium/ebpf"
    "github.com/cilium/cilium/pkg/bpf"
)

const (
    MapName = "cilium_exit_metrics"  // Custom map for exit tracking
)

type ExitMap struct {
    *bpf.Map
}

func (m *ExitMap) Update(key, value []byte) error {
    return m.Map.Update(key, value)
}
```

**Register in**: `pkg/maps/cells.go` (cell-based initialization)

#### Step 5: Define in eBPF Header

**File**: `bpf/include/ep_config.h` or `bpf/lib/maps.h`

```c
// Define exit-related constants if needed
#define CILIUM_MAP_EXIT_METRICS    CILIUM_MAP_EXIT_METRICS // Add unique ID

// Or define the map in eBPF:
#ifdef EXIT_METRICS_MAP
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);           // endpoint ID
    __type(value, exit_metrics);  // metrics struct
    __uint(pinning, LIBBPF_PIN_BY_NAME);
    __uint(max_entries, 100000);
} cilium_exit_metrics __section_maps_btf;
#endif
```

#### Step 6: Handle in Compilation

**File**: `pkg/datapath/loader/compile.go`

If your new hook requires different compilation flags:

```go
// In the programs struct or append to options
progInfo{
    Source: "bpf_lxc.c",
    Output: "bpf_lxc.o",
    OutputType: outputObject,
    Options: []string{
        // ... existing options
        "-DENABLE_EXIT_HANDLER=1",  // New flag for exit handler
    },
}
```

Or handle via endpoint config:
```go
// In pkg/datapath/loader/loader.go:EndpointConfiguration()
opts["EXIT_HANDLER_ENABLED"] = uint64(1)  // Pass to eBPF
```

#### Step 7: Handle Unloading

**File**: `pkg/datapath/loader/loader.go` - Unload method

```go
func (l *loader) Unload(ep datapath.Endpoint) {
    // Remove exit program from device
    device, err := safenetlink.LinkByName(ep.InterfaceName())
    if err != nil {
        return  // Already gone
    }

    // Detach: might use detachSKBProgram or custom logic
    detachSKBProgram(device, symbolFromContainerExit,
        bpffsDeviceLinksDir(bpf.CiliumPath(), device),
        netlink.HANDLE_MIN_EGRESS)
}
```

#### Step 8: Add Tests

**File**: `pkg/datapath/loader/exit_test.go`

```go
package loader

import (
    "testing"
    "github.com/stretchr/testify/require"
)

func TestAttachExitProgram(t *testing.T) {
    // Create test environment
    // Verify program attaches correctly
    // Check program is in filter list
}
```

#### Step 9: Document the Hook

**File**: `bpf/README.md` or `Documentation/network/ebpf/intro.rst`

```rst
Exit Handler Hook
==================

Triggered when a container exits or connection terminates.

Entry Point: ``cil_exit_from_container``

Use Cases:
- Connection cleanup
- Per-connection accounting
- Exit-time logging

Limitations:
- Cannot modify packets (connection already terminating)
- Limited packet buffer context
```

### eBPF Program Types Available

| Type | Trigger Point | Use Cases | Example |
|------|---|---|---|
| `TC_SKB` | TC ingress/egress | Main packet processing | `bpf_lxc`, `bpf_host` |
| `XDP` | NIC driver RX | High-speed filtering, early drop | `bpf_xdp` |
| `CGROUP_SKB` | Per-cgroup packets | Container-wide policies | Host firewall |
| `SOCKET_FILTER` | Socket data | Stream processing | Proxy integration |
| `SK_MSG` | Socket send | L7 load balancing | Encrypted traffic |
| `SOCKET_OPS` | TCP state changes | Connection tracking | Service mesh |
| `NETKIT` | Netkit interface | Advanced datapath | Overlay modes |

### Common Integration Points

```
Data Packet Flow Through Datapath:

1. XDP (cil_xdp_entry)
   ↓ [Early drop, DDoS protection]
2. TC Ingress (cil_from_netdev / cil_from_container)
   ↓ [Identity lookup, Policy check]
3. Policy Enforcement (tail call to cilium_call_policy)
   ↓ [Per-endpoint policy decisions]
4. Service Load Balancing (cilium_lb_* maps)
   ↓ [Service routing, backend selection]
5. Connection Tracking (cilium_ct_* maps)
   ↓ [State tracking, NAT]
6. Encryption (if enabled)
   ↓ [WireGuard or IPsec]
7. TC Egress (cil_to_netdev / cil_to_container)
   ↓ [Final routing, delivery]
8. Network Interface
```

### Registering with Tail Call System

If your new hook needs to integrate with existing datapath:

```c
// In bpf/lib/maps.h - add tail call index
#define CILIUM_CALL_EXIT_HANDLER 100  // Unique index

// In bpf code that should call your handler:
#include "lib/tailcall.h"
invoke_tailcall_if(is_defined(ENABLE_EXIT_HANDLER),
    CILIUM_CALL_EXIT_HANDLER,
    tail_handle_exit,
    &ext_err);
```

Then in Go loader, ensure the calls map is populated:
```go
// pkg/datapath/loader/netlink.go:loadDatapath()
// The resolveAndInsertCalls() function handles populating
// the tail call maps with program FDs
```

---

## Summary: Key Takeaways

### Critical Concepts

1. **Identity-based Policy**: Security decisions are made based on pod identities, not IP addresses
2. **In-kernel Enforcement**: All decisions happen in eBPF, not userspace proxies
3. **Tail Call Chaining**: Complex logic is split into multiple eBPF programs connected via tail calls
4. **Map-based Configuration**: Nearly all runtime data (policies, connections, identities) lives in eBPF maps
5. **Template-based Compilation**: Programs are compiled with per-node configuration to avoid recompilation

### Key Files to Know

- **Entry Point**: `pkg/datapath/loader/loader.go:ReloadDatapath()`
- **Compilation**: `pkg/datapath/loader/compile.go`
- **Loading**: `pkg/datapath/loader/netlink.go`
- **Attachment**: `pkg/datapath/loader/{tc,tcx,xdp,netkit}.go`
- **Main Programs**: `bpf/{bpf_lxc,bpf_host,bpf_xdp,bpf_network}.c`
- **Shared Libraries**: `bpf/lib/{policy,maps,nat,lb,ipv4,ipv6}.h`
- **Maps**: `pkg/maps/{policymap,ctmap,ipcache,lbmap}/`

### When Something Breaks

1. Check Cilium agent logs: `kubectl logs <pod> -c agent`
2. Verify program load: `cilium endpoint get <id> -o json | jq .datapath`
3. Inspect maps: `cilium-dbg bpf map list`
4. Monitor traffic: `cilium-dbg monitor --type drop`
5. Check kernel: `dmesg | grep -i ebpf`
6. Review probes: `cilium-dbg status --verbose | grep bpf`

### Recommended Reading Order

1. Architecture: `Documentation/network/ebpf/intro.rst`
2. Loader code: Start with `loader.go`, then `netlink.go`
3. Compilation: `compile.go`
4. eBPF programs: `bpf/bpf_lxc.c` (easier) then `bpf_host.c` (more complex)
5. Maps: `pkg/maps/policymap/` for core concepts
6. Testing: `Documentation/contributing/testing/bpf.rst`

---

## Additional Resources

- **Upstream Cilium Docs**: https://docs.cilium.io/
- **eBPF Guide**: https://ebpf.io/
- **Kernel BPF Docs**: Documentation/bpf/ in Linux kernel source
- **Design Documents**: https://cilium.io/blog/
- **Community Forum**: https://github.com/cilium/cilium/discussions/

---

**Document Version**: 1.0
**Cilium Version**: v1.16.5
**Last Updated**: 2026-03-01
