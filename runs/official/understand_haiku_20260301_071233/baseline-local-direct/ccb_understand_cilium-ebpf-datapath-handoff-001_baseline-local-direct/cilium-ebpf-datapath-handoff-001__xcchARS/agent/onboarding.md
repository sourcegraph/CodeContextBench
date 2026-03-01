# Cilium eBPF Datapath Subsystem Handoff Guide

## Overview

This document provides a comprehensive guide to the Cilium eBPF datapath subsystem—the core of Cilium's networking and security enforcement capabilities. The datapath is responsible for loading eBPF programs into the kernel, enforcing network policies, performing NAT/load balancing, and implementing service mesh functionality.

---

## 1. Purpose

### Problem Statement

The eBPF datapath solves a fundamental networking problem: **how to enforce complex network policies and perform sophisticated packet manipulation at kernel level with minimal overhead**.

Traditional approaches (iptables, userspace proxies) have significant limitations:
- **iptables**: Hard-coded rule format, poor scalability, limited context awareness
- **Userspace networking**: High CPU overhead from kernel-userspace context switches, packet copies, and increased latency
- **Traditional kernel modules**: Complex maintenance, versioning issues, reduced stability

### Why eBPF?

Cilium uses eBPF because it provides:

1. **Kernel-Native Execution**: Programs run directly in the kernel with minimal overhead
2. **Dynamic Programmability**: Policies can be changed without recompiling the kernel or restarting services
3. **Efficient Packet Processing**: Direct memory access allows fine-grained packet inspection and modification
4. **Atomic Policy Updates**: Maps and tail calls allow coordinated policy changes across hooks
5. **Rich Context**: Access to connection state, routing tables, socket information, and custom maps
6. **Security Isolation**: Kernel verifier ensures programs cannot crash the kernel or access arbitrary memory

### Key Responsibilities

The datapath subsystem is responsible for:

1. **eBPF Program Compilation**: Converting C source code into eBPF bytecode optimized for the target kernel
2. **Program Loading**: Injecting compiled eBPF programs into the kernel at various hook points
3. **Policy Enforcement**: Implementing ingress/egress policies via eBPF maps and tail calls
4. **Connection Tracking**: Maintaining stateful connections through eBPF maps
5. **Load Balancing**: Distributing traffic across service backends using consistent hashing (Maglev) or random selection
6. **NAT (Network Address Translation)**: Translating source/destination addresses and ports
7. **Encryption/Decryption**: Supporting IPsec and WireGuard encryption
8. **Network Tunneling**: Supporting Vxlan, Geneve, and other tunnel encapsulations
9. **Service Mesh Integration**: Enabling transparent proxy redirection for service mesh features

### Integration with Kubernetes Networking

The datapath integrates with Kubernetes at multiple levels:

- **Pod Networking**: Intercepts all traffic entering/leaving pod network namespaces via `cil_from_container` and `cil_to_container` hooks
- **Host Networking**: Processes traffic on the host network interface via `cil_from_netdev` and `cil_to_netdev` hooks
- **Service Handling**: Load balances traffic to ClusterIP services, NodePort services, and external load balancers
- **Network Policy Enforcement**: Applies Kubernetes NetworkPolicy rules to deny/allow traffic based on labels and selectors
- **DNS Policy**: Integrates with Cilium DNS policy for DNS-based policy enforcement
- **Multi-Cluster**: Supports ClusterMesh for cross-cluster service discovery and communication

---

## 2. Dependencies

### Upstream Dependencies (Who Calls the Datapath)

The following subsystems call into the datapath to load/manage eBPF programs:

1. **Endpoint Manager** (`pkg/endpoint/`): Loads eBPF programs when pods are created/destroyed
2. **Policy Engine** (`pkg/policy/`): Updates policy maps when NetworkPolicy rules change
3. **Service Manager** (`pkg/service/`): Updates service maps when Kubernetes services change
4. **Node Controller** (`pkg/controller/`): Reinitializes datapath when node configuration changes
5. **Agent** (`daemon/`): Bootstrap and initialization of the datapath subsystem

### Downstream Dependencies (What the Datapath Calls)

The datapath subsystem internally uses:

1. **eBPF Library** (`pkg/ebpf/`): Map registration and management
2. **Maps Subsystem** (`pkg/maps/`):
   - `policymap/`: Per-endpoint policy decision maps
   - `ctmap/`: Connection tracking maps (TCP4, TCP6, ANY4, ANY6)
   - `callsmap/`: Tail call maps for dynamic program dispatch
   - `configmap/`: Runtime configuration maps
   - `lbmap/`: Load balancer maps
   - Others: CIDR maps, bandwidth maps, etc.

3. **BPF Library** (`pkg/bpf/`): ELF file loading, pinning, unpinning
4. **Linux Datapath** (`pkg/datapath/linux/`):
   - `probes/`: Kernel feature detection
   - `iptables/`: IPtables rule management
   - `route/`: Routing table management
   - `sysctl/`: Sysctl parameter management
5. **Hive Cell System** (`pkg/hive/`): Dependency injection and lifecycle management

### Go-to-C Boundary

The Go code interacts with eBPF C programs through several mechanisms:

```
┌─────────────────────────────────────────────────────────────┐
│                   Go Control Plane                           │
│                  (pkg/datapath/loader)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  ┌──────────────┐          ┌──────────────┐
  │  Compilation │          │   Loading    │
  │   (compile.go)          │  (netlink.go)│
  └──────────────┘          └──────────────┘
        │                         │
        ▼                         ▼
  ┌─────────────────────────────────────────┐
  │      eBPF ELF Object File (.o)           │
  │   - Compiled C programs (bpf_*.c)        │
  │   - Map definitions                      │
  │   - Relocation info                      │
  └─────────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────────┐
  │  Kernel eBPF Maps (BPF Filesystem)       │
  │  - cilium_policy_* (per-endpoint)        │
  │  - cilium_call_policy (tail calls)       │
  │  - cilium_ct_{tcp,any}_{4,6}             │
  │  - And 50+ other maps                    │
  └─────────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────────┐
  │  Kernel eBPF Programs (Attached Hooks)   │
  │  - cil_from_container (tc ingress)       │
  │  - cil_to_container (tc egress)          │
  │  - cil_from_netdev (tc ingress)          │
  │  - cil_to_netdev (tc egress)             │
  │  - cil_xdp_entry (XDP)                   │
  │  - cil_from_host (tc ingress)            │
  │  - cil_to_host (tc egress)               │
  └─────────────────────────────────────────┘
```

### Kernel APIs Used

The datapath relies on several kernel mechanisms:

1. **eBPF System Calls** (BPF_PROG_LOAD, BPF_MAP_CREATE, etc.): Via `cilium/ebpf` library
2. **Netlink API** (`pkg/datapath/loader/netlink.go`):
   - Manages TC (Traffic Control) qdiscs and filters
   - Attaches/detaches eBPF programs to interfaces
3. **BPF Filesystem** (`/sys/fs/bpf`):
   - Persists maps across program reloads
   - Allows multiple programs to share maps
4. **XDP (eXpress Data Path)**: For early packet processing before network stack
5. **TC (Traffic Control)**: Ingress and egress packet processing
6. **Socket Options**: eBPF programs attached to socket operations
7. **Kernel Helper Functions**: `bpf_map_lookup_elem`, `bpf_tail_call`, `bpf_get_current_pid_tgid`, etc.

---

## 3. Relevant Components

### Core Directory Structure

```
/workspace/
├── bpf/                              # C eBPF source code
│   ├── bpf_lxc.c                     # Container endpoint (cil_from_container, cil_to_container)
│   ├── bpf_host.c                    # Host endpoint (cil_from_host, cil_to_host)
│   ├── bpf_xdp.c                     # XDP pre-filter program
│   ├── bpf_overlay.c                 # Overlay network handling
│   ├── bpf_sock.c                    # Socket-level load balancing
│   ├── bpf_wireguard.c               # WireGuard support
│   ├── bpf_network.c                 # Network policy program
│   ├── lib/                          # Shared eBPF headers (~60 .h files)
│   │   ├── common.h                  # Common definitions (tail call IDs, drop codes)
│   │   ├── policy.h                  # Policy enforcement logic
│   │   ├── lb.h                      # Load balancing implementation
│   │   ├── nat.h                     # NAT/DNAT logic
│   │   ├── conntrack.h               # Connection tracking
│   │   ├── maps.h                    # Map definitions and helpers
│   │   └── ...                       # IPv4, IPv6, encryption, tunneling, etc.
│   ├── include/                      # Header files for eBPF
│   └── Makefile, Makefile.bpf        # Build configuration

└── pkg/datapath/                     # Go datapath implementation
    ├── loader/                       # eBPF loader (core subsystem)
    │   ├── loader.go                 # Main Loader interface & ReloadDatapath()
    │   ├── base.go                   # Reinitialize(), writes config headers
    │   ├── compile.go                # Compilation logic, clang invocation
    │   ├── netlink.go                # Program loading, TC attachment
    │   ├── cache.go                  # ObjectCache for compiled templates
    │   ├── template.go               # Template configuration generation
    │   ├── hash.go                   # Cache invalidation via hashing
    │   ├── xdp.go                    # XDP program management
    │   ├── tc.go                     # TC qdisc/filter management
    │   ├── netkit.go                 # Netkit device support
    │   ├── tcx.go                    # TCX (newer TC mechanism) support
    │   ├── paths.go                  # Directory paths configuration
    │   └── metrics/                  # Metrics collection
    │
    ├── linux/                        # Linux-specific datapath implementation
    │   ├── datapath.go               # linuxDatapath struct implementing Datapath interface
    │   ├── node.go                   # Node configuration and routing
    │   ├── devices.go                # Network device management
    │   ├── ipsec.go                  # IPsec configuration
    │   ├── probes/                   # Kernel feature detection
    │   │   ├── probes.go             # Feature probe manager
    │   │   ├── attach_type.go        # eBPF program attach type detection
    │   │   └── kernel_hz.go          # Kernel timer frequency detection
    │   ├── iptables/                 # IPtables rule management
    │   ├── route/                    # Linux routing tables
    │   ├── sysctl/                   # Sysctl parameter management
    │   └── ...
    │
    ├── types/                        # Interface definitions
    │   ├── datapath.go               # Datapath interface
    │   ├── loader.go                 # Loader interface, PreFilter interface
    │   ├── endpoint.go               # Endpoint interface
    │   ├── config.go                 # Configuration types
    │   └── ...
    │
    ├── maps/                         # Map-related utilities
    │   ├── iptables/
    │   ├── policymap/                # Policy map management
    │   └── ...
    │
    └── ipcache/                      # IP identity cache

└── pkg/maps/                         # eBPF map implementations
    ├── policymap/                    # Per-endpoint policy maps (cilium_policy_*)
    │   └── policymap.go              # PolicyMap type, access methods
    ├── ctmap/                        # Connection tracking maps
    ├── callsmap/                     # Tail call program arrays
    ├── configmap/                    # Configuration maps
    ├── lbmap/                        # Load balancer maps
    └── ...                           # 30+ other map types

└── pkg/bpf/                          # Low-level eBPF utilities
    └── *.go                          # ELF loading, pinning, map operations
```

### Key Files and Their Purposes

#### Compilation Pipeline

| File | Purpose |
|------|---------|
| `pkg/datapath/loader/compile.go` | Invokes clang to compile C source to eBPF bytecode, handles preprocessor output and verification |
| `bpf/Makefile`, `bpf/Makefile.bpf` | Compilation rules: clang flags, kernel version detection, sparse checking |
| `pkg/datapath/loader/template.go` | Generates template endpoint configs, wraps EndpointConfiguration with dummy values |
| `pkg/datapath/loader/hash.go` | Hashes configuration to detect when recompilation is needed |

#### Loading Pipeline

| File | Purpose |
|------|---------|
| `pkg/datapath/loader/loader.go:ReloadDatapath()` | Main entry point: compiles/loads eBPF for an endpoint, manages caching |
| `pkg/datapath/loader/netlink.go:loadDatapath()` | Kernel-facing: loads ELF into kernel, pins maps to bpffs, handles verifier errors |
| `pkg/datapath/loader/netlink.go:attachProgram()` | Attaches programs to TC ingress/egress or XDP |
| `pkg/bpf/collection.go` | Wraps cilium/ebpf library, handles map pinning and unpinning |

#### Configuration Generation

| File | Purpose |
|------|---------|
| `pkg/datapath/loader/base.go:writeNetdevHeader()` | Generates `netdev_config.h` with interface-specific config (MACs, MTU, etc.) |
| `pkg/datapath/loader/base.go:writeNodeConfigHeader()` | Generates `node_config.h` with node-wide config (IPs, routing, policy settings) |
| `pkg/datapath/loader/base.go:writePreFilterHeader()` | Generates `filter_config.h` for XDP prefilter CIDR ranges |

#### Caching

| File | Purpose |
|------|---------|
| `pkg/datapath/loader/cache.go:objectCache` | In-memory cache of compiled ELF specs, indexed by configuration hash |
| `pkg/datapath/loader/cache.go:UpdateDatapathHash()` | Invalidates cache when node configuration changes |

### Entry Points into eBPF Programs

All entry points are defined symbolically in `pkg/datapath/loader/loader.go` and correspond to function names in C:

```c
// Container endpoint (bpf_lxc.c)
int cil_from_container(struct __ctx_buff *ctx)  // Ingress (from pod)
int cil_to_container(struct __ctx_buff *ctx)    // Egress (to pod)

// Host endpoint (bpf_host.c, various attachment points)
int cil_from_host(struct __ctx_buff *ctx)       // From host network stack
int cil_to_host(struct __ctx_buff *ctx)         // To host network stack
int cil_from_netdev(struct __ctx_buff *ctx)     // From external interface (ingress)
int cil_to_netdev(struct __ctx_buff *ctx)       // To external interface (egress)

// XDP pre-filter (bpf_xdp.c)
int cil_xdp_entry(struct xdp_md *ctx)           // Early packet filtering

// Overlay network (bpf_overlay.c)
int cil_from_overlay(struct __ctx_buff *ctx)    // Tunnel ingress
int cil_to_overlay(struct __ctx_buff *ctx)      // Tunnel egress

// WireGuard (bpf_wireguard.c)
int cil_to_wireguard(struct __ctx_buff *ctx)    // WireGuard egress
```

### eBPF Map Landscape

The datapath uses 50+ different maps. Key categories:

#### Policy Maps (Per-Endpoint)
- **`cilium_policy_<EPID>`** (BPF_MAP_TYPE_HASH): Policy decisions for endpoint with ID EPID
- **`cilium_call_policy`** (BPF_MAP_TYPE_PROG_ARRAY): Tail call targets for policy enforcement
- **`cilium_egresscall_policy`** (BPF_MAP_TYPE_PROG_ARRAY): Egress-specific policy tail calls

#### Connection Tracking
- **`cilium_ct_tcp4`, `cilium_ct_tcp6`**: TCP connections
- **`cilium_ct_any4`, `cilium_ct_any6`**: Other protocols (UDP, ICMP)
- Shared across all endpoints for efficient lookup

#### Configuration
- **`cilium_config`**: Runtime configuration (feature flags, MTU, IP settings)
- **`cilium_lb4_services`, `cilium_lb4_backends`**: Service definitions and backend pools
- **`cilium_nodeport_neigh`**: Neighbor information for NodePort NAT

#### Other Important Maps
- **`cilium_ipcache`**: IP-to-security-identity mapping
- **`cilium_egressmap`**: Egress gateway rules
- **`cilium_tunnel_map`**: Tunnel endpoint information
- **`cilium_encrypt_state`**: IPsec/WireGuard state

See `pkg/maps/` for complete list.

### Program Execution Flow

When a packet arrives at an endpoint:

```
┌─────────────────────────────────────────┐
│ Packet arrives on pod interface (veth)  │
└──────────────────────┬──────────────────┘
                       │
          ┌────────────▼────────────┐
          │   TC Ingress Filter     │
          │  (cil_from_container)   │
          └────────────┬────────────┘
                       │
         ┌─────────────▼──────────────┐
         │ 1. Extract packet info     │
         │ 2. Look up source identity │
         │ 3. Tail call to policy     │
         │ 4. Apply policy decision   │
         └─────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ Packets either:             │
        │ - Dropped (policy deny)     │
        │ - Load balanced (tail call) │
        │ - NAT'd (DNAT, masquerade)  │
        │ - Forwarded                 │
        └──────────────┬──────────────┘
                       │
          ┌────────────▼────────────┐
          │   TC Egress Filter      │
          │  (cil_to_container)     │
          │ (or cil_to_netdev for   │
          │  inter-node traffic)    │
          └────────────┬────────────┘
                       │
         ┌─────────────▼──────────────┐
         │ 1. Final policy check      │
         │ 2. Conntrack update        │
         │ 3. Return to network stack │
         └────────────────────────────┘
```

---

## 4. Failure Modes

### eBPF Program Compilation Failures

**Causes:**
- Unsupported kernel features (e.g., calling a helper function not available in the kernel)
- eBPF verifier rejects the program (memory safety violations)
- Clang compilation errors
- Invalid C syntax in generated headers

**Handling:**
- **File**: `pkg/datapath/loader/compile.go:compileDatapath()`
- **Mechanism**: Captures clang stderr/stdout, returns error with diagnostic info
- **User Impact**: Endpoint fails to become ready; error logged with compilation output
- **Recovery**: Fix kernel version, disable incompatible features via config, or update code

**Diagnostics:**
```bash
# Check compilation output
kubectl logs -n kube-system cilium-xxxx --tail=100 | grep "BPF"
# Check verifier logs
# Check kernel version compatibility
uname -r
```

### eBPF Verifier Failures

**Causes:**
- **Uninitialized variables**: Using variables without setting all bytes
- **Unbounded loops**: eBPF doesn't allow loops that verifier can't prove bounded
- **Out-of-bounds memory access**: Accessing packet/map data beyond bounds
- **Invalid pointer arithmetic**: Pointer math that could point outside valid ranges
- **Stack overflow**: Local variables exceed 512-byte stack limit
- **Tail call limits**: Exceeded max tail call depth (typically 32-33 levels)

**Handling:**
- **File**: `pkg/datapath/loader/netlink.go:loadDatapath()`
- **Mechanism**: cilium/ebpf library captures verifier output
- **Detection**: `ebpf.VerifierError` type
- **User Impact**: Program fails to load; verbose verifier error logged
- **Workaround**: Refactor code to avoid verifier issues

**Example Error:**
```
verifier error:
  ... invalid memory access for read from stack R1 offset=-8 size=8
```

### eBPF Map Failures

**Causes:**
- **Map full**: Map max_entries exceeded (pre-allocated max size)
- **Map incompatibility**: Pinned map has different structure than current code
- **Permission denied**: Lack of CAP_SYS_ADMIN or MAP_CREATE capability
- **Type mismatch**: Trying to update map with wrong key/value size

**Handling:**
- **Files**:
  - `pkg/datapath/loader/netlink.go:loadDatapath()` - detects incompatibilities
  - `pkg/maps/` - individual map implementations
- **Mechanism**: Maps are pinned to `/sys/fs/bpf/tc/` and reloaded across restarts
- **Type checking**: Signature mismatch detected and maps recreated
- **Policy maps**: Automatically enlarged in `pkg/maps/policymap/`

**Recovery:**
```bash
# Check map status
bpftool map list
# Check policy map size
bpftool map show id <MAP_ID>
# Remove stale maps (careful!)
rm /sys/fs/bpf/tc/globals/cilium_policy_*
```

### Kernel Compatibility Issues

**Categories:**

1. **Missing Kernel Features**: Helper function not available
2. **Behavioral Changes**: Different kernel version changes semantics
3. **API Changes**: Deprecated system calls or structures

**Detection:**
- **Files**: `pkg/datapath/linux/probes/`
- **Mechanism**: Loads test programs to probe kernel capabilities
- **Key Function**: `probes.ProbeManager.GetProbes()` compiles features.h header with detected capabilities

**Example Probes:**
```go
// In pkg/datapath/linux/probes/probes.go
HaveFibIfindex bool         // FIB lookup support
HaveSessionCookie bool      // Session cookie available
HaveIfindex bool            // Interface index in context
```

**Handling:**
- Conditional compilation via `#ifdef` in eBPF C code
- Config headers (`node_config.h`, `ep_config.h`) control features
- Features disabled if not supported

### Configuration Errors

**Common Issues:**

1. **Invalid IPv4/IPv6 CIDR blocks**: IPcache configuration
2. **Invalid MAC addresses**: Used in ARP/neighbor lookup
3. **Invalid endpoint IDs**: Out of range (0-65535 for standard endpoints)
4. **Inconsistent policy configuration**: Policy verdict mismatches

**Detection:**
- **File**: `pkg/datapath/loader/` - config generation and validation
- **Mechanisms**:
  - Template endpoint (ID 65535) used for validation
  - Config validation before header generation
  - Endpoint hash changes trigger recompilation

**Recovery:**
```bash
# Inspect configuration
cilium config
# Check template compilation
ls -la /var/run/cilium/state/templates/
```

### eBPF Program Crashes (Kernel Panics)

**Causes:**
- Invalid memory access (prevented by verifier in theory)
- Null pointer dereference
- Integer overflow in loops
- Corrupted map structures

**Prevention:**
- Verifier prevents most memory access violations
- Type-safe map access via cilium/ebpf library
- Bounds checking in C code

**Debugging:**
```bash
# Kernel logs
dmesg | tail -50
# Check for BPF-related panics
journalctl -xe | grep -i bpf
```

### Header File Generation Failures

**Causes:**
- Invalid endpoint configuration passed from Go
- IOError writing config files
- Filesystem issues (permission denied, disk full)

**Handling:**
- **File**: `pkg/datapath/loader/base.go`
- **Functions**:
  - `writeNetdevHeader()` - writes `netdev_config.h`
  - `writeNodeConfigHeader()` - writes `node_config.h`
  - `writePreFilterHeader()` - writes `filter_config.h`

**Recovery:**
```bash
# Check state directory permissions
ls -la /var/run/cilium/state/
# Check disk space
df -h
```

---

## 5. Testing

### Test Organization

```
/workspace/bpf/tests/          # eBPF C program tests
├── bpf_ct_tests.c             # Connection tracking tests
├── bpf_nat_tests.c            # NAT logic tests
├── fib_tests.c                # FIB lookup tests
├── drop_notify_test.c         # Drop notification tests
└── ... (40+ more test files)

/workspace/pkg/datapath/loader/  # Go loader tests
├── loader_test.go             # Tests for Reinitialize, ReloadDatapath
├── compile_test.go            # Compilation unit tests
├── cache_test.go              # Object cache tests
├── netlink_test.go            # TC attachment tests
├── xdp_test.go                # XDP loading tests
└── ...

/workspace/pkg/datapath/linux/
├── node_linux_test.go         # Node config tests
├── devices_controller_test.go  # Device detection tests
└── ...
```

### eBPF Test Framework

eBPF programs are tested using a userspace test framework that:

1. **Compiles eBPF programs** to bytecode
2. **Loads test programs** into kernel
3. **Creates synthetic test contexts** (simulated packets)
4. **Executes programs** with test data
5. **Verifies results** (dropped, modified, passed)

**Example Test Pattern** (from `/workspace/bpf/tests/`):

```c
// Test program: verify policy enforcement
#include "lib/policy.h"

// ... setup endpoint config ...

int test_policy_allow(void *ctx) {
    // Set up packet and context
    struct __ctx_buff pkt = {...};
    __u32 src_identity = 1001;

    // Call policy enforcement
    int ret = allow_to_endpoint(...);

    // Assert result
    if (ret != CTX_ACT_OK) {
        return TEST_ERROR;
    }
    return TEST_OK;
}
```

### Go Unit Tests

**Key Test Areas:**

1. **Compilation Tests** (`loader_test.go`):
   - Test eBPF programs compile without errors
   - Verify generated headers are syntactically correct
   - Test template compilation with various configurations

2. **Caching Tests** (`cache_test.go`):
   - Verify object cache deduplication works
   - Test hash invalidation when config changes

3. **Loading Tests** (`netlink_test.go`):
   - Verify TC filters are attached correctly
   - Test cleanup/unload operations
   - Verify program symbols are found

### Integration Tests

**In-Cluster Policy Tests:**
- Deploy pods with Kubernetes NetworkPolicy
- Verify traffic is allowed/denied as expected
- Use tools like `cilium connectivity test`

**Command:**
```bash
cilium connectivity test --target-namespace default
```

**What It Tests:**
- Pod-to-pod connectivity
- Pod-to-external connectivity
- Policy enforcement
- Service load balancing
- DNS policy

### Test Pattern: Policy Enforcement

To test a new policy feature:

1. **Write eBPF test** in `bpf/tests/` exercising the feature
2. **Create Go unit test** for compilation in `pkg/datapath/loader/`
3. **Create integration test** or use `cilium connectivity test`
4. **Manual verification** using `cilium monitor` and packet capture

### Debugging Test Failures

**Check eBPF Program Correctness:**
```bash
# Disassemble compiled program
llvm-objdump -d bpf_lxc.o | less

# Check for uninitialized variables
clang -emit-llvm -c bpf_lxc.c -o bpf_lxc.ll
llvm-dis bpf_lxc.ll
```

**Inspect Runtime State:**
```bash
# List loaded programs
bpftool prog list

# Inspect specific program
bpftool prog show id <PROG_ID> opcodes

# Dump map contents
bpftool map dump id <MAP_ID>
```

**Use Cilium Monitoring:**
```bash
# Monitor policy enforcement decisions
cilium monitor --type trace

# Show dropped packets
cilium monitor --type drop

# Monitor events
cilium monitor
```

---

## 6. Debugging

### Troubleshooting eBPF Loading Failures

**Step 1: Check Agent Logs**
```bash
# Get cilium agent logs
kubectl logs -n kube-system cilium-xxxxx --tail=200

# Filter for eBPF errors
kubectl logs -n kube-system cilium-xxxxx | grep -i "ebpf\|verifier\|error"
```

**Step 2: Verify Kernel Support**
```bash
# Check kernel version (minimum 4.9, recommend 5.4+)
uname -r

# Check for eBPF feature support
cat /proc/config.gz | gunzip | grep CONFIG_BPF

# Verify bpffs is mounted
mount | grep bpf

# Check if mounted correctly
ls -la /sys/fs/bpf/
```

**Step 3: Check Compilation Output**
```bash
# Find state directory
ls -la /var/run/cilium/state/

# Check for template compilation failures
ls /var/run/cilium/state/templates/

# Inspect generated config headers
cat /var/run/cilium/state/templates/bpf_lxc.c  # If available
```

**Step 4: Manual Compilation Test**
```bash
cd /workspace/bpf

# Try manual compilation
clang -O2 -target bpf \
  -I. -Iinclude \
  -D__NR_CPUS__=$(nproc --all) \
  -c bpf_lxc.c -o bpf_lxc.o 2>&1

# Check for verifier errors in dmesg
dmesg | tail -100 | grep -i verifier
```

### Inspecting eBPF Maps at Runtime

**List All Maps:**
```bash
bpftool map list
```

**Inspect Policy Map:**
```bash
# Find policy map ID
bpftool map list | grep cilium_policy

# Dump contents
bpftool map dump id <MAP_ID> | head -50

# Get map statistics
bpftool map show id <MAP_ID>
```

**Inspect Connection Tracking Map:**
```bash
bpftool map dump id <CT_MAP_ID> | head -20
```

**Check Map Pinning:**
```bash
# Verify maps are pinned to bpffs
ls -la /sys/fs/bpf/tc/globals/

# Check if map is pinned correctly
bpftool map show id <MAP_ID> | grep "path"
```

### Tools for Debugging eBPF Programs

**1. bpftool** - Comprehensive eBPF inspection
```bash
# Show loaded programs
bpftool prog list

# Dump program bytecode
bpftool prog dump id <PROG_ID> xlated

# Show program attach points
bpftool prog show id <PROG_ID>

# Get program stats
bpftool prog stat
```

**2. cilium monitor** - Monitor datapath activity
```bash
# Basic monitoring
cilium monitor

# Monitor specific event types
cilium monitor --type drop      # Dropped packets
cilium monitor --type trace     # Policy trace
cilium monitor --type debug     # Debug events

# Filter by pod
cilium monitor --from-namespace default --to-namespace default
```

**3. tc (Traffic Control)** - Inspect TC filters/qdiscs
```bash
# List tc qdiscs on interface
tc qdisc show dev eth0

# List tc filters on interface
tc filter show dev eth0 ingress
tc filter show dev eth0 egress

# Dump filter details (includes BPF program info)
tc filter show dev eth0 ingress details
```

**4. tcpdump / packet capture** - Capture traffic
```bash
# Capture on pod interface
tcpdump -i eth0 -n host 10.0.0.5

# Capture with detail
tcpdump -i eth0 -n -v
```

**5. strace** - Trace syscalls (for loader issues)
```bash
# Trace cilium-agent (get logs with BPF syscalls)
strace -e trace=bpf cilium-agent -config-file=... 2>&1 | head -100
```

### Verifying Policy Enforcement

**1. Check Policy Map Configuration:**
```bash
# Get endpoint ID
cilium endpoint list

# Check policy map exists
bpftool map list | grep cilium_policy_<EPID>

# Dump policy entries (key=identity+port+direction, value=allow/deny)
bpftool map dump id <MAP_ID>
```

**2. Monitor Policy Decisions:**
```bash
# Monitor all policy events
cilium monitor --type trace

# Generate test traffic and observe
kubectl exec -it <pod> -- curl <target-pod>
```

**3. Inspect Policy Verdict:**
```bash
# Use cilium monitor to see if packet is allowed/denied
cilium monitor --type drop | grep "packet dropped"
```

### Performance Debugging

**1. Check eBPF Program Performance:**
```bash
# Get program stats
bpftool prog stat

# Profile program execution (requires BPF_ENABLE_STATS kernel config)
bpftool prog show id <PROG_ID> # Look at "run_time_ns", "run_cnt"
```

**2. Monitor Tail Call Depth:**
```bash
# Tail calls are used for policy dispatch
# If tail call limit is hit, packet is dropped
cilium monitor --type drop | grep "tail_call"
```

**3. Profile Datapath Latency:**
```bash
# Use cilium monitor with timestamps
cilium monitor --timestamp

# Measure round-trip latency
kubectl exec <pod> -- ping -c 10 <target>
```

### Analyzing eBPF Disassembly

**Get Program Disassembly:**
```bash
# Dump as LLVM IR
bpftool prog dump id <PROG_ID> xlated

# Dump as assembly
bpftool prog dump id <PROG_ID> jited

# Get human-readable disassembly (requires llvm-objdump)
llvm-objdump -d /sys/fs/bpf/tc/globals/<PROG_NAME>
```

**Interpret Disassembly:**
- `BPF_LD_ABS`: Load absolute offset from packet
- `BPF_LDX_MEM`: Load from memory (map/stack)
- `BPF_STX_MEM`: Store to memory
- `BPF_CALL`: Call kernel helper function
- `BPF_JMP`: Conditional/unconditional jump

### Checking Kernel Compatibility

**Verify Kernel Features:**
```bash
# Check supported eBPF types
cat /sys/kernel/debug/tracing/available_filter_functions | grep bpf

# Check loaded kernel modules
lsmod | grep bpf

# Check kernel config
cat /boot/config-$(uname -r) | grep BPF
```

**Run Kernel Feature Probes:**
```bash
# Cilium runs these probes automatically
# Manually check via:
cilium config | grep Features
```

### Map Issues Debugging

**Check for Map Leaks:**
```bash
# List all maps by name pattern
bpftool map list | grep cilium_

# Check if old maps still exist (should be cleaned up)
bpftool map list | grep -v "cilium_" | head

# If leaks, manually pin to bpffs (Cilium should handle)
```

**Map Size Issues:**
```bash
# Check map size and max entries
bpftool map show id <MAP_ID>

# For policy maps, max_entries = 16384 by default
# If full, check:
cilium bpf policy list | wc -l

# If approaching limit, increase via config:
# --bpf-map-policy-size
```

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Verifier error: invalid memory access" | Out-of-bounds access | Check pointer arithmetic, bounds checking in code |
| "Program type doesn't support attach type" | Kernel too old | Upgrade kernel or disable feature |
| "Map pinning failed" | Permission denied | Check file permissions on /sys/fs/bpf |
| "Tail call limit exceeded" | Policy too complex | Simplify policy, refactor code |
| "BPF verifier loop detected" | Unbounded loop | Add verifier pragma or refactor |
| "Program not found at symbol X" | ELF parsing error | Check symbol names match in C and Go |
| Policy not applied | Map not updated | Check Cilium event logs, verify policy sync |

---

## 7. Adding a New Hook

### Overview

Adding a new eBPF hook involves creating a new attachment point where eBPF programs process packets. Common scenarios:

1. **New protocol support** (e.g., SCTP hooks)
2. **New attachment point** (e.g., new network interface type)
3. **New service mesh feature** (e.g., transparent proxy hook)

### Step-by-Step Process

#### Step 1: Determine Hook Type

Choose the eBPF program type based on attachment point:

| Hook Type | Program Type | Where Used | Best For |
|-----------|--------------|-----------|----------|
| **TC (Traffic Control)** | `BPF_PROG_TYPE_SCHED_CLS` | Network interfaces (ingress/egress) | Most common; post network stack |
| **XDP** | `BPF_PROG_TYPE_XDP` | Physical device driver level | Early filtering; DoS mitigation |
| **socket operations** | `BPF_PROG_TYPE_SOCK_OPS` | Socket events | Connection establishment |
| **socket filter** | `BPF_PROG_TYPE_SOCKET_FILTER` | Raw sockets | Per-socket filtering |
| **tc l4** | `BPF_PROG_TYPE_SCHED_ACT` | TC actions | Advanced traffic manipulation |

Most Cilium hooks use **TC** because they operate at a good balance of early processing vs. context availability.

#### Step 2: Create eBPF C Program

**File**: Create new file in `/workspace/bpf/` (e.g., `bpf_myproto.c`)

**Structure:**
```c
// SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
/* Copyright Authors of Cilium */

#include <bpf/ctx/skb.h>
#include <bpf/api.h>

#include <node_config.h>
#include <ep_config.h>

#define IS_BPF_MYPROTO 1
#define EVENT_SOURCE MY_PROTO_EP_ID

// Include shared libraries
#include "lib/common.h"
#include "lib/maps.h"
#include "lib/identity.h"
#include "lib/policy.h"
#include "lib/myproto.h"  // New protocol-specific header

// Main entry point
int cil_myproto_process(struct __ctx_buff *ctx)
{
    // 1. Extract packet headers
    // 2. Lookup endpoint/identity
    // 3. Check policy
    // 4. Perform necessary transformations
    // 5. Return action (CTX_ACT_OK, DROP, REDIRECT, etc.)

    return CTX_ACT_OK;
}
```

**Key Components:**

```c
// Define entry point name (will be referenced in Go loader)
#define symbolMyProtoProcess "cil_myproto_process"

// Include required headers for:
// - Packet context access: lib/eth.h, lib/ipv4.h, lib/ipv6.h
// - Identity lookup: lib/identity.h
// - Policy enforcement: lib/policy.h
// - Helpers: lib/common.h

// Use tail calls for complex logic:
tail_call_internal(ctx, CILIUM_CALL_MYPROTO_HANDLER, ext_err)
```

#### Step 3: Define Tail Call ID

**File**: `/workspace/bpf/lib/common.h`

Add new tail call ID:
```c
#define CILIUM_CALL_MYPROTO_HANDLER    99  // Choose unused ID
```

#### Step 4: Create Go Loader Integration

**File**: `pkg/datapath/loader/loader.go` (or new file `pkg/datapath/loader/myproto.go`)

**Add to Loader Type Definition:**
```go
const (
    symbolMyProtoProcess = "cil_myproto_process"
)

var (
    myprotoProg = progInfo{
        Source:     "bpf_myproto.c",
        Output:     "bpf_myproto.o",
        OutputType: outputObject,
    }
)
```

**Add Compilation Info** (in `pkg/datapath/loader/compile.go`):
```go
var programs = []progInfo{
    // ... existing programs ...
    myprotoProg,
}
```

#### Step 5: Create Attachment Logic

**File**: Create new file `pkg/datapath/loader/myproto.go`

**Implement Program Attachment:**
```go
func (l *loader) attachMyProto(ifName string, spec *ebpf.CollectionSpec) error {
    // 1. Extract program from spec
    prog := spec.Programs[symbolMyProtoProcess]
    if prog == nil {
        return fmt.Errorf("program %s not found", symbolMyProtoProcess)
    }

    // 2. Attach to TC qdisc
    // For ingress:
    iface, err := net.InterfaceByName(ifName)
    if err != nil {
        return err
    }

    l, err := netlink.LinkByIndex(iface.Index)
    if err != nil {
        return err
    }

    // 3. Create or reuse qdisc
    qdiscExists := // check if qdisc exists
    if !qdiscExists {
        qdisc := &netlink.GenericQdisc{
            QdiscAttrs: netlink.QdiscAttrs{
                LinkIndex: l.Attrs().Index,
                Parent:    netlink.HANDLE_INGRESS,
                Handle:    netlink.MakeHandle(0xffff, 0),
            },
            QdiscType: "clsact",
        }
        if err := netlink.QdiscAdd(qdisc); err != nil {
            return err
        }
    }

    // 4. Attach program via TC filter
    filter := &netlink.BpfFilter{
        FilterAttrs: netlink.FilterAttrs{
            LinkIndex: l.Attrs().Index,
            Parent:    netlink.HANDLE_MIN_INGRESS,
            Priority:  1,
            Protocol:  unix.ETH_P_ALL,
        },
        Fd:    prog.FD(),
        Name:  symbolMyProtoProcess,
    }

    return netlink.FilterAdd(filter)
}
```

#### Step 6: Integrate with Reinitialize Flow

**File**: `pkg/datapath/loader/base.go` (or appropriate location)

Add to `Reinitialize()` or create specialized reinitialization:
```go
func (l *loader) reinitializeMyProto(ctx context.Context, spec *ebpf.CollectionSpec) error {
    devices := // get list of devices to attach to

    for _, ifName := range devices {
        if err := l.attachMyProto(ifName, spec); err != nil {
            return fmt.Errorf("attach myproto to %s: %w", ifName, err)
        }
    }

    return nil
}
```

Call from `Reinitialize()`:
```go
func (l *loader) Reinitialize(...) error {
    // ... existing code ...

    if err := l.reinitializeMyProto(ctx, spec); err != nil {
        return fmt.Errorf("reinitialize myproto: %w", err)
    }

    return nil
}
```

#### Step 7: Handle Endpoint-Specific Code

If the hook needs per-endpoint configuration:

**File**: `pkg/datapath/loader/loader.go`

Modify `ReloadDatapath()` to include myproto:
```go
func (l *loader) ReloadDatapath(ctx context.Context, ep datapath.Endpoint, ...) error {
    // ... existing logic ...

    // For container endpoints, attach myproto hooks
    if !ep.IsHost() {
        if err := l.attachMyProtoEndpoint(ep, spec); err != nil {
            return err
        }
    }

    return nil
}
```

#### Step 8: Define Maps (If Needed)

Create eBPF maps for the new hook (in `pkg/maps/`):

**File**: `pkg/maps/mymaps/mymaps.go`

```go
package mymaps

import "github.com/cilium/cilium/pkg/bpf"

const (
    MapName = "cilium_myproto"
)

// Register map in cell initialization
```

**File**: `pkg/maps/cells.go` - Register new map

#### Step 9: Add Configuration Headers

If the hook needs compile-time configuration:

**File**: `pkg/datapath/loader/base.go`

Add header generation:
```go
func (l *loader) writeMyProtoHeader(dir string) error {
    headerPath := filepath.Join(dir, "myproto_config.h")
    f, err := os.Create(headerPath)
    if err != nil {
        return err
    }
    defer f.Close()

    // Write configuration based on EndpointConfiguration
    fmt.Fprintf(f, "#define MYPROTO_ENABLED 1\n")
    // ... more config ...

    return nil
}
```

Call from config generation pipeline:
```go
func (l *loader) writeNetdevHeader(dir string) error {
    // ... existing code ...
    if err := l.writeMyProtoHeader(dir); err != nil {
        return err
    }
    return nil
}
```

#### Step 10: Write Tests

**File**: `pkg/datapath/loader/myproto_test.go`

```go
func TestCompileMyProto(t *testing.T) {
    // Test compilation
    l := newTestLoader(t)
    ctx, cancel := context.WithTimeout(context.Background(), contextTimeout)
    defer cancel()

    // Should not error
    assert.NoError(t, l.Reinitialize(ctx, ...))
}

func TestAttachMyProto(t *testing.T) {
    // Test attachment to interface
    l := newTestLoader(t)

    // Create test interface
    // Verify attachment
}
```

**File**: `/workspace/bpf/tests/myproto_tests.c`

```c
#include "lib/myproto.h"

int test_myproto_basic(void *ctx) {
    // Test basic myproto functionality
    return TEST_OK;
}
```

#### Step 11: Update Documentation

**File**: `Documentation/network/ebpf/` - Add or update docs

Document:
- Purpose of new hook
- When it's triggered
- Configuration options
- Performance implications

#### Step 12: Testing Checklist

- [ ] eBPF program compiles without verifier errors
- [ ] Go code compiles without errors
- [ ] Unit tests pass
- [ ] Programs attach to interfaces correctly
- [ ] Integration tests pass
- [ ] Policies work with new hook
- [ ] Performance is acceptable
- [ ] Documentation is complete

### Example: Adding TCP Option Hook

Here's a concrete example of adding a hook to process TCP options:

**1. Create C program** (`bpf_tcp_opts.c`):
```c
int cil_tcp_options(struct __ctx_buff *ctx)
{
    // Parse TCP options from packet
    // Validate/modify as needed
    // Return packet or drop
    return CTX_ACT_OK;
}
```

**2. Register in Go** (`pkg/datapath/loader/loader.go`):
```go
const symbolTcpOptions = "cil_tcp_options"

var tcpOptsProg = progInfo{
    Source: "bpf_tcp_opts.c",
    Output: "bpf_tcp_opts.o",
    OutputType: outputObject,
}
```

**3. Attach to TC** (`pkg/datapath/loader/tcp_opts.go`):
```go
func (l *loader) attachTcpOptions(spec *ebpf.CollectionSpec) error {
    // Attach after existing ingress programs
    // Use priority to control ordering
}
```

**4. Test** (`pkg/datapath/loader/tcp_opts_test.go`):
```go
func TestTcpOptionsAttach(t *testing.T) {
    // Verify program loads and attaches
}
```

### Common Pitfalls

1. **Forgetting to handle both IPv4 and IPv6**: Most hooks need separate code paths
2. **Not checking kernel capability**: Use probes to detect support
3. **Tail call limits**: Deep call chains can exceed kernel limits (32-33 levels)
4. **Map pinning conflicts**: Different programs expecting different map layouts
5. **Missing symbol in ELF**: Ensure function names match between C and Go
6. **Memory limits**: Stack is limited to 512 bytes; avoid large local structures
7. **Verifier complexity**: Overly complex code can confuse verifier; simplify or split

### Advanced: Custom Tail Calls

For complex hooks, use tail calls to jump between programs:

**In eBPF C:**
```c
int cil_myproto_entry(struct __ctx_buff *ctx) {
    // Initial processing
    // ... some logic ...

    // Jump to custom handler
    return tail_call_internal(ctx, CILIUM_CALL_MYPROTO_HANDLER, &ext_err);
}

// In cilium_call_myproto map, populate entry for this endpoint:
// map[endpoint_id] = &cil_myproto_handler
```

**In Go:**
```go
// Update tail call map when endpoint config changes
func (l *loader) updateMyProtoTailCalls(ep datapath.Endpoint) error {
    callMap := callsmap.GetMap(ep.GetID())

    progFd := ... // get FD of custom handler program
    callMap.Update(CILIUM_CALL_MYPROTO_HANDLER, progFd)

    return nil
}
```

### Debugging New Hooks

**Verify Compilation:**
```bash
# Manually compile new program
cd /workspace/bpf
clang -O2 -target bpf -c bpf_myproto.c -o bpf_myproto.o
```

**Check Program Loading:**
```bash
# List loaded programs
bpftool prog list | grep myproto

# Verify attachment point
bpftool prog show id <PROG_ID>
```

**Monitor Execution:**
```bash
# Generate traffic that should trigger hook
# Monitor in cilium monitor
cilium monitor --type trace

# Check if program is called
bpftool prog stat | grep myproto
```

---

## Summary

The Cilium eBPF datapath is a sophisticated system requiring coordination between:

1. **C eBPF programs** (`/workspace/bpf/`) - kernel-space packet processing
2. **Go loader** (`/workspace/pkg/datapath/loader/`) - compilation, loading, management
3. **eBPF maps** (`/workspace/pkg/maps/`) - data structures shared with kernel
4. **Linux integration** (`/workspace/pkg/datapath/linux/`) - kernel feature detection, system configuration

Key areas for future work:

- **Performance optimization**: Profile and optimize hot paths in eBPF C code
- **Feature additions**: New hooks, protocols, or policy types
- **Kernel compatibility**: Support newer kernel versions and deprecate old ones
- **Testing**: Expand test coverage for edge cases and failure modes
- **Documentation**: Keep docs synchronized with code changes

When in doubt, follow the existing patterns in the codebase and refer to the test suite for examples.

---

**Document Version**: 1.0
**Last Updated**: 2026-03-01
**Cilium Version**: 1.16.5
