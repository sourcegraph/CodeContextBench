# Cilium eBPF Datapath Subsystem - Handoff Documentation

## Table of Contents
1. [Purpose](#1-purpose)
2. [Dependencies](#2-dependencies)
3. [Relevant Components](#3-relevant-components)
4. [Failure Modes](#4-failure-modes)
5. [Testing](#5-testing)
6. [Debugging](#6-debugging)
7. [Adding a New Hook](#7-adding-a-new-hook)

---

## 1. Purpose

### Problem Statement
The eBPF datapath is the core execution engine of Cilium's networking and security capabilities. It solves the fundamental problem of enforcing network policies and implementing sophisticated packet processing at kernel level without requiring userspace context switches, making it extremely performant and efficient.

### Why eBPF Instead of iptables or Userspace Networking?

**Performance Benefits:**
- **Zero-copy processing**: eBPF programs run in kernel space, eliminating userspace/kernel boundary crossings
- **Atomic operations**: All packet processing decisions are made atomically without lock contention
- **Early packet filtering**: XDP allows dropping packets at the NIC driver level before allocation to kernel networking stack
- **In-kernel maps**: Shared state (policies, connections, load balancing) is maintained in kernel memory with O(1) access

**Capability Benefits:**
- **Stateful enforcement**: Connection tracking and stateful firewalling without iptables conntrack overhead
- **L7 policy integration**: Can mark packets for user-space proxy without full kernel L7 support
- **Service mesh**: Integrated load balancing, traffic management, and service discovery
- **Observability**: Deep packet introspection and monitoring without mirror ports or packet copying

**Compared to iptables:**
- iptables chains linear rule evaluation; eBPF uses O(1) map lookups
- iptables cannot maintain sophisticated state; eBPF maintains connection tracking, identity mappings, etc.
- iptables has high memory overhead; eBPF maps are memory-efficient
- iptables is static; eBPF can dynamically update configuration via maps

### Key Responsibilities of the Datapath Subsystem

1. **Program Compilation & Loading** (`pkg/datapath/loader/`):
   - Compile C eBPF programs to ELF object files using Clang
   - Manage template caching for performance
   - Load compiled programs into kernel with all BPF maps
   - Handle kernel compatibility and verifier failures

2. **Network Interface Management** (`pkg/datapath/linux/`):
   - Auto-detect or manage network devices (physical NICs, veth pairs)
   - Attach/detach eBPF programs to devices using TC, TCX, XDP, or netkit hooks
   - Track device state and respond to network topology changes

3. **Policy Enforcement** (`bpf/lib/policy.h`, `pkg/maps/policymap/`):
   - Maintain policy maps in kernel memory
   - Implement identity-based allow/deny rules
   - Support CIDR-based policies via IP address to identity mapping
   - Enforce both ingress and egress policies

4. **Connection Tracking** (`pkg/maps/ctmap/`, `bpf/lib/conntrack.h`):
   - Track established connections for stateful firewalling
   - Implement NAT state tracking for masquerading
   - Support connection cleanup on policy changes

5. **Load Balancing** (`bpf/lib/lb.h`, `pkg/maps/lbmap/`):
   - Implement Kubernetes service load balancing in kernel
   - Support both ClusterIP and NodePort services
   - Perform in-kernel service endpoint selection (Maglev or random)
   - Handle connection affinity and session persistence

6. **Tunneling & Encryption** (`bpf/lib/encap.h`, `bpf/lib/encrypt.h`):
   - Encapsulate inter-cluster traffic
   - Implement VXLAN/Geneve tunneling
   - Support transparent encryption for pod-to-pod communication

### Kubernetes Integration

The eBPF datapath integrates with Kubernetes at multiple levels:

```
Kubernetes API
        ↓
Cilium Agent (userspace) ← reads → CiliumNetworkPolicy, Service, Node, Endpoint CRDs
        ↓ (compiles and loads)
eBPF Programs (kernel space)
        ↓ (queries and updates)
Kernel eBPF Maps (connection state, policy, identity mappings, service endpoints)
        ↓ (packet processing)
Linux Kernel (network stack, interfaces)
        ↓
Network Devices (veth, physical NICs, tunnels)
```

**Key Integration Points:**
- **Endpoint Management**: Each pod gets a unique identity; its network interface has eBPF programs attached
- **Policy Synchronization**: CiliumNetworkPolicy objects trigger recompilation of eBPF programs with policy rules
- **Service Mapping**: Kubernetes services are converted into eBPF map entries for load balancing
- **Identity Resolution**: Pod/namespace identity assigned by Cilium agent is stored in eBPF maps

---

## 2. Dependencies

### Upstream Dependencies (What Calls Into the Datapath)

```
┌─────────────────────────────────────────────────────────────┐
│ Cilium Agent (pkg/daemon/)                                  │
├─────────────────────────────────────────────────────────────┤
│ ├─ Endpoint Manager (pkg/endpoint/)                         │
│ │  └─> Calls loader.ReloadDatapath() when endpoint added   │
│ ├─ Policy Engine (pkg/policy/)                             │
│ │  └─> Triggers recompilation on policy changes            │
│ ├─ Service Manager (pkg/service/)                          │
│ │  └─> Updates ServiceMap → lb.h map updates               │
│ └─ Node Manager (pkg/node/)                                │
│    └─> Triggers reinitialization on topology changes       │
└─────────────────────────────────────────────────────────────┘
```

**Key Interfaces Called:**
- `loader.ReloadDatapath(ctx, endpoint, stats)` - Compile and load program for endpoint
- `loader.Reinitialize(ctx, nodeConfig, tunnelConfig, iptMgr, proxy)` - Global reinitialization
- `loader.ReinitializeXDP(ctx, extraCArgs)` - Recompile XDP program
- `loader.EndpointHash(cfg)` - Get hash of endpoint configuration to detect changes
- `loader.HostDatapathInitialized()` - Wait for host datapath ready

**Key Integration Packages:**
- `pkg/datapath/types/` - Interfaces that must be implemented
- `pkg/datapath/loader/` - Actual loader implementation
- `pkg/datapath/loader/metrics/` - Loader metrics and span tracking
- `pkg/identity/` - Identity allocation used by datapath

### Downstream Dependencies (What Datapath Calls)

```
┌──────────────────────────────────────────────────────────────────┐
│ eBPF Datapath (pkg/datapath/loader/)                            │
├──────────────────────────────────────────────────────────────────┤
│ ├─ Kernel (via syscalls)                                         │
│ │  ├─ bpf() syscall - Load/manage eBPF programs                 │
│ │  ├─ netlink - Attach programs to interfaces (TC, XDP, netkit) │
│ │  └─ sysctl - Configure kernel parameters                      │
│ ├─ Maps (in-kernel)                                              │
│ │  ├─ Policy Maps (policymap.MapName)                           │
│ │  ├─ Call Map (callsmap.MapName) - Tail call table             │
│ │  ├─ CT Maps (ctmap.Map{TCP4,Any4,TCP6,Any6})                 │
│ │  ├─ NAT Maps (natmap)                                         │
│ │  ├─ LB Maps (lbmap)                                           │
│ │  └─ Identity Cache (ipcache)                                  │
│ ├─ Tools                                                         │
│ │  ├─ Clang/LLVM - Compile eBPF programs                        │
│ │  └─ tc/ip netlink commands - Manage interface attachments     │
│ └─ Configuration                                                 │
│    ├─ node_config.h - Dynamically generated                     │
│    ├─ ep_config.h - Per-endpoint configuration                  │
│    ├─ netdev_config.h - Device configuration                    │
│    └─ filter_config.h - XDP filter rules                        │
└──────────────────────────────────────────────────────────────────┘
```

### The Go-to-C Boundary

**How Go code loads C programs:**

1. **Compilation (`pkg/datapath/loader/compile.go`)**:
   - Go calls Clang to compile `.c` files to `.o` (object files)
   - Template compilation with dummy values generates "shape" of all programs
   - Real endpoint compilation replaces dummy values with actual configuration

2. **Map Interaction (`pkg/ebpf/`)**:
   - Uses `github.com/cilium/ebpf` Go library (vendored)
   - `ebpf.CollectionSpec` parses compiled ELF files
   - Maps are created and shared between kernel and userspace
   - Go code populates kernel maps (policies, services, identities)

3. **Program Loading (`pkg/datapath/loader/loader.go`)**:
   ```go
   // Load eBPF collection from compiled object file
   spec, err := ebpf.LoadCollectionSpec(objPath)
   coll, err := spec.Load(&ebpf.CollectionOptions{})

   // Access programs by their section names
   progIngress := coll.Programs["cil_from_container"]
   progEgress := coll.Programs["cil_to_container"]
   ```

4. **Attachment (`pkg/datapath/loader/tc.go`, `.../xdp.go`, `.../netkit.go`)**:
   - Programs attached to network interfaces using kernel APIs
   - TC/TCX/netkit: ebpf.Link for kernel hook management
   - XDP: ebpf.Program pinned to bpffs + netlink attachment

5. **Runtime Updates (`pkg/maps/`)**:
   - Go code opens existing maps via bpffs pins
   - Updates map entries: `map.Put(key, value)`
   - eBPF programs read updated values on next packet

### Kernel APIs Used

| Kernel API | Purpose | Used By |
|-----------|---------|---------|
| `bpf()` syscall | Load/unload programs, create/manage maps | ebpf library |
| TC (Traffic Control) | Attach programs to ingress/egress of interface | tc.go |
| TCX (TC eXtensions) | Modern alternative to TC with better semantics | tc.go, tcx.go |
| netkit | New kernel hook for veth-like namespace transitions | netkit.go |
| XDP (eXpress Data Path) | Driver-level packet processing | xdp.go |
| netlink (NETLINK_ROUTE) | Query/modify kernel routing, interface attributes | safenetlink/ |
| BPF Maps | Persistent storage for program state | All eBPF programs |
| BPF Helpers | Functions called by eBPF programs (bpf_map_lookup_elem, etc.) | bpf/lib/*.h |

**Example: Program Loading Flow:**

```
Go Code (ReloadDatapath)
    ↓ calls Clang
Linux: clang -O2 -target bpf bpf_lxc.c -c -o bpf_lxc.o
    ↓ produces ELF file
bpf_lxc.o (compiled)
    ↓ parsed by ebpf.CollectionSpec
In-memory: ebpf.CollectionSpec {
  Programs: {
    "cil_from_container": &ebpf.Program{},
    "cil_to_container": &ebpf.Program{},
    ...
  }
  Maps: {
    "cilium_policy_XYZ": &ebpf.Map{},
    "cilium_ct_tcp4": &ebpf.Map{},
    ...
  }
}
    ↓ coll.Load() calls bpf() syscall
Kernel: eBPF programs + maps loaded in kernel memory
    ↓ programs pinned to bpffs
/sys/fs/bpf/cilium/bpf_lxc_XYZ
    ↓ attached to interface
Interface veth123 has eBPF programs active
```

---

## 3. Relevant Components

### Directory Structure Overview

```
/workspace/
├── bpf/                          # eBPF C source code
│   ├── bpf_lxc.c                 # Per-endpoint container traffic processing
│   ├── bpf_host.c                # Host endpoint processing
│   ├── bpf_xdp.c                 # XDP pre-filter for early packet drop
│   ├── bpf_network.c             # Generic network processing
│   ├── bpf_overlay.c             # Overlay network (tunnel) processing
│   ├── bpf_sock.c                # Socket-level operations (eBPF sockops)
│   ├── bpf_wireguard.c           # WireGuard integration
│   ├── lib/                       # Shared eBPF libraries
│   │   ├── common.h              # Core packet processing utilities
│   │   ├── policy.h              # Policy enforcement logic
│   │   ├── lb.h                  # Load balancing (60KB, most complex)
│   │   ├── nat.h                 # NAT and masquerading
│   │   ├── conntrack.h           # Connection tracking state machine
│   │   ├── identity.h            # Security identity lookup
│   │   ├── encap.h               # Packet encapsulation (tunneling)
│   │   ├── nodeport.h            # NodePort service implementation
│   │   ├── maps.h                # Map definitions and access
│   │   └── [many more].h
│   ├── include/                  # BPF compiler includes
│   │   └── bpf/                  # BPF helper definitions
│   ├── node_config.h             # Generated: global configuration
│   ├── ep_config.h               # Generated: per-endpoint config
│   ├── netdev_config.h           # Generated: network device config
│   ├── filter_config.h           # Generated: XDP filter rules
│   ├── Makefile                  # Builds all eBPF programs
│   └── Makefile.bpf              # Compilation rules (clang invocation)
│
├── pkg/
│   ├── datapath/                 # Platform-agnostic datapath interface
│   │   ├── types/                # Interface definitions
│   │   │   ├── loader.go         # Loader interface
│   │   │   ├── config.go         # Configuration interfaces
│   │   │   ├── endpoint.go       # Endpoint interface
│   │   │   └── node.go           # Node configuration interface
│   │   ├── loader/               # *** MAIN LOADER IMPLEMENTATION ***
│   │   │   ├── loader.go         # Primary loader - ReloadDatapath, Reinitialize
│   │   │   ├── compile.go        # Clang compilation orchestration
│   │   │   ├── base.go           # Base program attachment setup
│   │   │   ├── template.go       # Template caching for performance
│   │   │   ├── tc.go             # TC/TCX program attachment
│   │   │   ├── xdp.go            # XDP program management
│   │   │   ├── netlink.go        # Low-level netlink attachment
│   │   │   ├── netkit.go         # netkit (new veth hook) support
│   │   │   ├── tcx.go            # TCX (modern TC) support
│   │   │   ├── hash.go           # Configuration hashing
│   │   │   ├── cache.go          # Caching compiled programs
│   │   │   ├── cell.go           # Hive dependency injection
│   │   │   └── metrics/          # Loader metrics
│   │   ├── linux/                # Linux-specific implementations
│   │   │   ├── datapath.go       # Linux datapath instance
│   │   │   ├── devices_controller.go  # Network device synchronization
│   │   │   ├── devices.go        # Device management and detection
│   │   │   ├── node.go           # Linux node datapath implementation
│   │   │   ├── node_ids.go       # Node identity mapping
│   │   │   ├── probes/          # Kernel capability probing
│   │   │   ├── config/          # Linux-specific config generation
│   │   │   ├── ipsec/           # IPSec implementation
│   │   │   ├── modules/         # Kernel module management
│   │   │   ├── route/           # Route management
│   │   │   ├── sysctl/          # Sysctl tuning
│   │   │   └── safenetlink/     # Safe netlink operations
│   │   ├── fake/                 # Fake datapath for testing
│   │   ├── maps/                 # Map management
│   │   ├── iptables/            # Legacy iptables management
│   │   ├── alignchecker/        # Struct alignment verification
│   │   └── tables/              # StateDB tables for devices/routes
│   │
│   ├── ebpf/                     # eBPF map wrappers
│   │   ├── ebpf.go              # Core eBPF utilities
│   │   ├── map.go               # Map management interface
│   │   └── map_register.go      # Map registration
│   │
│   ├── maps/                     # Kernel map implementations
│   │   ├── policymap/           # Policy decision maps
│   │   ├── ctmap/               # Connection tracking maps
│   │   ├── callsmap/            # Tail call map
│   │   ├── lbmap/               # Load balancing maps
│   │   ├── ipcache/             # IP → Identity cache
│   │   ├── nat/                 # NAT state maps
│   │   ├── authmap/             # Authentication state
│   │   └── [many more]/
│   │
│   └── bpf/                      # BPF-related utilities (Go side)
│       ├── map.go
│       ├── prog.go
│       └── [utilities for managing eBPF from Go]
```

### Critical Files for eBPF Datapath Understanding

#### 1. **Loader (Core Implementation)**

| File | Purpose | Key Functions |
|------|---------|---|
| `loader/loader.go` | Main loader orchestration | `ReloadDatapath()`, `Reinitialize()`, `New()` |
| `loader/compile.go` | Clang compilation | `compileProgramSubcommand()`, `GetBPFCPU()` |
| `loader/template.go` | Template caching | `objectCache`, `WriteNodeConfig()` |
| `loader/base.go` | Program attachment to interfaces | `compileDatapathProgramBase()` |
| `loader/tc.go` | TC/TCX program attachment | `attachSKBProgram()`, `attachTCProgram()` |
| `loader/xdp.go` | XDP program management | `ReloadXDP()`, `maybeUnloadObsoleteXDPPrograms()` |
| `loader/netlink.go` | Low-level netlink operations | Network interface manipulation |
| `loader/cache.go` | Object file caching | `objectCache.Put()`, `objectCache.Get()` |

#### 2. **eBPF Programs (C Code)**

| File | Purpose | Symbol (Entry Point) |
|------|---------|---|
| `bpf_lxc.c` | Per-pod container traffic processing | `cil_from_container`, `cil_to_container` |
| `bpf_host.c` | Host endpoint network processing | `cil_from_host`, `cil_to_host` |
| `bpf_xdp.c` | Early packet filtering at driver level | `cil_xdp_entry` |
| `bpf_network.c` | Generic network traffic (rarely used) | - |
| `bpf_overlay.c` | Overlay network processing | `cil_from_overlay`, `cil_to_overlay` |
| `bpf_sock.c` | Socket-level operations | Socket filter programs |
| `bpf_wireguard.c` | WireGuard encapsulation | - |

**Key eBPF Libraries (in bpf/lib/):**

| Library | Purpose | Size | Key Macros/Functions |
|---------|---------|------|---|
| `lib/common.h` | Core utilities | 36KB | Packet parsing, context access, tail calls |
| `lib/policy.h` | Policy lookups | 12KB | `policy_lookup_*()`, verdict enforcement |
| `lib/lb.h` | Load balancing | 60KB | Service lookup, endpoint selection, connection affinity |
| `lib/nat.h` | Network address translation | 47KB | NAT state, masquerade address selection |
| `lib/conntrack.h` | Connection tracking | 33KB | CT state machine, established tracking |
| `lib/maps.h` | Map definitions | 8KB | Map declarations and access helpers |
| `lib/encap.h` | Tunneling | 7KB | VXLAN/Geneve encapsulation |
| `lib/identity.h` | Identity resolution | 7KB | Reverse IP lookup to identity |
| `lib/nodeport.h` | NodePort services | 94KB | NodePort-specific logic, external traffic handling |

#### 3. **Network Device & Interface Management**

| File | Purpose |
|------|---------|
| `linux/devices_controller.go` | Subscribes to netlink for device changes, populates StateDB tables |
| `linux/devices.go` | Device detection logic (wildcard matching, filtering) |
| `linux/datapath.go` | Linux datapath instance, orchestrates components |
| `linux/node.go` | Node-wide datapath configuration (57KB, complex) |
| `linux/probes/` | Kernel capability detection (BPF maps types, verifier quirks) |

#### 4. **Configuration Generation**

| File | Purpose | Generated Files |
|------|---------|---|
| `loader/base.go:writeNetdevHeader()` | Network device config | `netdev_config.h` (via templateCache) |
| `loader/base.go:writeNodeConfigHeader()` | Global node config | `node_config.h` (from option.Config) |
| `loader/base.go:writePreFilterHeader()` | XDP filter rules | `filter_config.h` |
| `loader/template.go:WriteNodeConfig()` | Node config writer | Generates #define directives |

These files are included by eBPF programs at compile-time and define:
- IP addresses, MAC addresses, interface indices
- Feature flags (ENABLE_IPV6, ENABLE_NODEPORT, etc.)
- Policy maps to use
- Identity mappings

#### 5. **Key Maps (In-Kernel Storage)**

Maps are defined in eBPF code and accessed by both eBPF programs and Go code:

| Map Name | Definition | Type | Purpose |
|----------|-----------|------|---------|
| `cilium_policy_XYZ` | `lib/maps.h` | Map[u32 identity → policy verdict] | Store policy decisions by security identity |
| `cilium_call_*` | `lib/maps.h` | Array[u32 index → prog fd] | Tail call table for modular programs |
| `cilium_ct_tcp4/tcp6` | `lib/conntrack.h` | Map[tuple → CT state] | TCP connection tracking |
| `cilium_ct_any4/any6` | `lib/conntrack.h` | Map[tuple → CT state] | Non-TCP protocol tracking |
| `cilium_lb4_services` | `lib/lb.h` | Map[SVC key → SVC object] | Service endpoints and load balancing |
| `cilium_lb4_backends` | `lib/lb.h` | Map[backend id → backend] | Backend endpoint addresses |
| `cilium_ipv4_ipcache` | `lib/identity.h` | Map[IPv4 → identity + EncryptKey] | IP to security identity mapping |
| `cilium_ipv6_ipcache` | `lib/identity.h` | Map[IPv6 → identity + EncryptKey] | IPv6 security identity mapping |

### Code Flow: Loading a Pod Endpoint

```
Endpoint Created Event (in Cilium Agent)
    ↓
daemon/cmd/daemon.go: endpointManager.UpdateEndpoint()
    ↓
endpoint/endpoint.go: Endpoint.SetupDatapath()
    ↓
loader/loader.go: loader.ReloadDatapath(ctx, endpoint, stats)
    ├─ Acquire compilationLock
    │
    ├─ Get endpoint configuration (ID, IP, MAC, identity, etc.)
    │
    ├─ Check if already compiled via hash (loader/hash.go)
    │
    ├─ If not cached, compile:
    │   ├─ loader/compile.go: compileDatapathProgramSubcommand()
    │   │  ├─ Write ep_config.h (endpoint configuration)
    │   │  ├─ Write node_config.h (global configuration)
    │   │  ├─ Call clang to compile bpf_lxc.c → bpf_lxc_EPID.o
    │   │  └─ Output: /var/run/cilium/bpf_lxc_12345.o
    │   │
    │   ├─ ebpf.LoadCollectionSpec(bpf_lxc_EPID.o)
    │   └─ coll.Load() - Create maps in kernel
    │
    ├─ Get eBPF program references
    │   ├─ progIngress: cil_from_container (TC ingress)
    │   └─ progEgress: cil_to_container (TC egress)
    │
    ├─ Get endpoint interface (e.g., "veth0")
    │
    ├─ Attach programs to interface:
    │   ├─ loader/tc.go: attachSKBProgram(device, progIngress, parent=BPF_TC_INGRESS)
    │   │  ├─ Check if TCX supported
    │   │  ├─ Try upsertTCXProgram() (preferred)
    │   │  │  ├─ ebpf.Link: TCX ingress attachment
    │   │  │  └─ Pin to /sys/fs/bpf/cilium/cil_from_container
    │   │  └─ Fallback: attachTCProgram() with legacy TC
    │   │
    │   └─ Same for egress with BPF_TC_EGRESS
    │
    └─ Return success
```

---

## 4. Failure Modes

### A. eBPF Program Compilation Failures

#### 1.1 Clang Compilation Error
**Symptom**: `failed to compile eBPF programs: clang command failed`

**Root Causes**:
- C syntax errors in eBPF program source
- Undefined macros (missing node_config.h or ep_config.h)
- Incompatible helper function usage
- Non-portable C constructs

**Detection**:
```go
// loader/compile.go: compileDatapathProgramSubcommand()
cmd := exec.CommandContext(ctx, compiler, ...)
if err := cmd.Run(); err != nil {
    // Clang returned error; stderr contains compiler messages
}
```

**Recovery**:
- Fix C code syntax
- Check configuration header generation (`base.go:writeNetdevHeader()`)
- Verify Clang version supports required BPF instruction set
- Check `node_config.h` is properly generated before compilation

#### 1.2 eBPF Verifier Rejection
**Symptom**: `error verifying eBPF program: invalid instruction sequence`

**Root Causes**:
- Program uses unverifiable memory access patterns
- Loop unrolling insufficient (verifier cannot prove termination)
- Dead code with unreachable paths
- Stack overflow (BPF stack is 512 bytes)
- Unbounded loops

**Common Patterns**:
```c
// BAD: Infinite loop (verifier rejects)
#pragma unroll
for (int i = 0; i < 1000; i++) { ... }

// GOOD: Bounded unrolling
#pragma unroll
for (int i = 0; i < 10; i++) { ... }  // Known constant

// BAD: Variable loop bound
for (int i = 0; i < n; i++) { ... }  // Verifier can't prove termination

// GOOD: Pragma unroll without loop
#pragma unroll
for (int i = 0; i < max_iterations; i++) {
    if (i >= actual_count) break;  // Explicit bound check
}
```

**Detection**:
```go
// pkg/datapath/linux/probes/probes.go
// Verifier failures caught when loading collection:
coll, err := spec.Load(&ebpf.CollectionOptions{})
// err contains verifier error message with instruction number
```

**Recovery**:
- Reduce loop iterations
- Unroll loops manually with explicit iteration bounds
- Simplify stack usage (split into multiple functions)
- Use local helper functions instead of inlining everything
- Profile with `llvm-objdump` to see code size and complexity

#### 1.3 Map Size Too Small
**Symptom**: `BPF_MAP_TYPE_HASH: max_entries too small for hash`

**Root Causes**:
- Policy maps need entries for all policy decisions
- CT maps need entries for all concurrent connections
- LB maps insufficient for all services/endpoints

**Configuration**:
Map sizes are defined in:
- `lib/maps.h` (eBPF program side)
- `pkg/maps/*/map.go` (Go side)

**Recovery**:
- Increase `MaxEntries` in map definition
- For policy maps: `POLICY_MAP_SIZE` in `lib/maps.h`
- For CT maps: `CONNTRACK_TABLE_SIZE` in node config
- Monitor map utilization with `bpftool`

### B. eBPF Program Loading Failures

#### 2.1 BPF Map Already Exists Error
**Symptom**: `map already exists` or `pin already exists`

**Root Causes**:
- Previous program instance not cleaned up
- Reloading with mismatched map definitions
- Multiple loader instances running

**Detection**:
```go
// loader/loader.go: ReloadDatapath()
// When map already pinned in bpffs
spec.Maps[mapName].Pinning = ebpf.PinByName
coll, err := spec.Load(...)  // Fails if pinned map has different type/size
```

**Recovery**:
- Unload previous programs: `loader.Unload(endpoint)`
- Remove stale pinned maps: `/sys/fs/bpf/cilium/`
- Restart Cilium agent (cleans up on startup)
- Check for concurrent Cilium instances (should only be one)

#### 2.2 Insufficient Kernel Memory
**Symptom**: `Cannot allocate memory` when loading maps

**Root Causes**:
- Not enough kernel memory for eBPF maps
- System out of memory
- ulimit restrictions on locked memory

**Detection**:
```go
// First time eBPF programs loaded
// bpf() syscall fails with ENOMEM
```

**Recovery**:
```bash
# Remove memory locks for eBPF programs
ulimit -l unlimited

# Or increase system memory limits
sysctl -w vm.max_map_count=262144
```

#### 2.3 Program Type Mismatch
**Symptom**: `program type mismatch: expected BPF_PROG_TYPE_SCHED_CLS, got BPF_PROG_TYPE_XDP`

**Root Causes**:
- Attaching program with wrong section to hook
- Program compiled with wrong entrypoint symbol
- Kernel doesn't support program type

**Detection**:
```go
// loader/tc.go or loader/xdp.go
// When attaching program
prog := coll.Programs["cil_from_container"]
// Must be BPF_PROG_TYPE_SCHED_CLS for TC
```

**Recovery**:
- Verify program section in ELF: `llvm-objdump -d bpf_lxc.o`
- Check kernel supports required program types: `bpftool feature probe`
- Recompile with correct libbpf sections

### C. Program Attachment Failures

#### 3.1 TC/TCX Not Supported
**Symptom**: `attaching tcx program: operation not supported`

**Root Causes**:
- Kernel too old (TCX added in Linux 6.6)
- Interface doesn't support TC_EGRESS_BLOCK/TC_INGRESS_BLOCK
- Netkit interfaces on kernel without netkit support

**Graceful Fallback**:
```go
// loader/tc.go: attachSKBProgram()
// Tries TCX first
if errors.Is(err, link.ErrNotSupported) {
    // Falls back to legacy TC
    return attachTCProgram(device, prog, ...)
}
```

#### 3.2 XDP Load Failure
**Symptom**: `XDP attach failed: device does not support XDP`

**Root Causes**:
- Device driver doesn't support XDP (e.g., veth when not in driver mode)
- XDP mode conflict (already attached in different mode)
- Virtual devices (veth) only support generic XDP without netkit

**Detection**:
```go
// loader/xdp.go: ReloadXDP()
// Tries to attach; falls back gracefully for unsupported devices
```

**Recovery**:
- Use `option.XDPModeGeneric` instead of driver mode for virtual devices
- Disable XDP if not needed
- Update device drivers to support XDP

#### 3.3 Interface Not Found
**Symptom**: `link with name eth0 not found`

**Root Causes**:
- Device deleted before attachment
- Interface name changed
- Network namespace not accessible

**Recovery**:
- Wait for endpoint setup before attachment
- Use device index instead of name if possible
- Verify network namespace

### D. Runtime eBPF Program Failures

#### 4.1 Program Returns DROP/TC_DROP
**Symptom**: Packets silently dropped, no errors in kernel logs

**Root Causes**:
- Policy decision returned DROP
- Packet malformed (fails parsing)
- CT lookup failed with malformed packet
- LB service not found
- Permission denied by policy

**Debugging**:
```bash
# Enable eBPF debug logging
cilium config set policy-verdict=true

# Check which rules are matching
cilium policy trace -s <source-identity> -d <dest-identity>

# Monitor packet drops
cilium monitor --drop
```

#### 4.2 Kernel Panic from eBPF Program
**Symptom**: Kernel panic with eBPF stack trace in dmesg

**Root Causes**:
- Out-of-bounds map access
- Null pointer dereference
- Invalid memory access
- Bug in eBPF program logic

**Prevention**:
- Test with `clang -fsanitize=address` (address sanitizer)
- Use bounded loops with explicit checks
- Always check map lookup results before use
- Use kernel verifier output: `bpftool prog show`

**Recovery**:
- Disable offending eBPF hook temporarily
- Update to patched Cilium version
- Add explicit bounds checking in eBPF code

#### 4.3 Map Corruption
**Symptom**: Incorrect policy/CT/LB decisions, stale map data

**Root Causes**:
- Data race in map access (eBPF and Go updating simultaneously)
- Incorrect key/value serialization
- Wrong map type (per-cpu vs shared)
- Bug in Go code updating maps

**Prevention**:
- Ensure proper locking when updating maps from Go
- Use atomic operations for map updates
- Verify key/value sizes at runtime
- Use `bpftool map dump` to inspect map contents

**Recovery**:
- Restart Cilium agent to reinitialize maps
- Delete corrupted map entries manually
- Rebuild eBPF programs with fresh compilation

### E. Configuration Errors

#### 5.1 Incompatible Configuration
**Symptom**: `policy not enabled but ENABLE_POLICY_DENY set`

**Root Causes**:
- Conflicting configuration options
- Generated headers with invalid combinations
- Old configuration not cleaned up

**Detection**:
```go
// loader/base.go: compileDatapathProgramBase()
// Validates endpoint configuration
if !cfg.RequireEgressProg() && hasEgressPolicy {
    log.Warn("Egress prog not required but policy requires it")
}
```

**Recovery**:
- Review `option.Config` settings
- Clean `/var/run/cilium/` directory
- Verify node configuration with `cilium status`

#### 5.2 Missing Required Header
**Symptom**: `ep_config.h: no such file or directory`

**Root Causes**:
- Compilation directory not writable
- Header generation failed silently
- Incorrect working directory

**Prevention**:
- Verify `/var/run/cilium/` directory exists and is writable
- Check compilation logs for header write errors
- Ensure endpoint state directory is accessible

---

## 5. Testing

### A. Unit Testing the Loader

**Location**: `pkg/datapath/loader/`

**Test Files**:
- `loader_test.go` - Main loader tests
- `compile_test.go` - Compilation tests
- `cache_test.go` - Object cache tests
- `hash_test.go` - Hash generation tests
- `netlink_test.go` - Netlink operation tests
- `tc_test.go` - TC attachment tests
- `xdp_test.go` - XDP attachment tests

**Key Test Patterns**:

```go
// loader_test.go: TestReloadDatapath
func TestReloadDatapath(t *testing.T) {
    testutils.PrivilegedTest(t)  // Requires CAP_SYS_ADMIN

    // Setup
    ep := &testutils.TestEndpoint{
        InterfaceName: "veth0",
        Identity:     256,
        IPv4: netip.MustParseAddr("10.0.0.1"),
    }
    initEndpoint(t, ep)

    // Get loader
    ldr := NewLoader(ctx, &Config{
        Library: bpfDir,
        Output:  tmpDir,
    })

    // Reload
    symPath, err := ldr.ReloadDatapath(ctx, ep, &metrics.SpanStat{})
    require.NoError(t, err)

    // Verify
    require.FileExists(t, symPath)  // Program loaded successfully
}
```

**Test Requirements**:
- Run as root (eBPF loading requires CAP_SYS_ADMIN)
- Real network interfaces (dummy device) or use netlink mocking
- Temporary BPF filesystem for testing
- Clean up BPF objects after each test

**Run Tests**:
```bash
# Run loader tests
cd /workspace
go test -v ./pkg/datapath/loader/...

# With coverage
go test -v -cover ./pkg/datapath/loader/...

# Specific test
go test -v -run TestReloadDatapath ./pkg/datapath/loader/
```

### B. eBPF Program Testing

**Location**: `bpf/tests/`

**Test Framework**: Custom eBPF test harness (libbpf)

**Test Files**:
- `bpf/tests/` - Directory with test programs
- Uses `TEST_SECTION()` macro to define test cases
- Compiles test programs alongside main programs

**Test Approach**:
```c
// Example: Test policy lookup
#define TEST_SECTION "test_policy_lookup"

__u32 test_policy_lookup(void)
{
    struct policy_entry *entry;
    __u32 key = 100;

    entry = policy_lookup(&key);
    return (entry != NULL) ? 0 : -1;  // Return 0 on success
}
```

**Running eBPF Tests**:
```bash
# Compile tests
cd /workspace/bpf
make test

# Run specific test
./test_runner test_policy_lookup
```

### C. Integration Testing

**Location**: `pkg/datapath/linux/` tests, `pkg/endpoint/` tests

**Integration Test Patterns**:

```go
// Example: Test endpoint with policy
func TestEndpointWithPolicy(t *testing.T) {
    testutils.PrivilegedTest(t)

    // Setup cluster
    cluster := cilium.NewTestCluster()
    defer cluster.Cleanup()

    // Create pod
    pod := cluster.CreatePod("default", "test-pod")

    // Create network policy
    policy := &cilium.NetworkPolicy{
        PodSelector: labels.Everything(),
        PolicyTypes: []PolicyType{PolicyTypeIngress},
        Ingress: []IngressRule{
            {
                From: []PodSelector{...},
            },
        },
    }
    cluster.ApplyPolicy(policy)

    // Wait for policy to be loaded
    require.EventuallyWithT(t, func(c *assert.CollectT) {
        policies := pod.GetAppliedPolicies()
        assert.Len(c, policies, 1)
    }, 10*time.Second, 100*time.Millisecond)

    // Test: Send traffic through policy
    result := pod.SendPacket(destPod)
    assert.Equal(t, "ALLOWED", result.Decision)
}
```

### D. Policy Enforcement Testing

**Without a Full Cluster**:

1. **Standalone eBPF Test**:
   ```bash
   # Load bpf_lxc.o with test maps
   bpftool prog load bpf_lxc.o type sched_cls

   # Populate policy map
   bpftool map update pinned /sys/fs/bpf/cilium/cilium_policy_1234 \
       key 0x01 0x00 0x00 0x00 value 0x01 0x00 0x00 0x00

   # Send test packets via tc
   tc qdisc add dev veth0 ingress
   tc filter add dev veth0 ingress bpf da bytecode $(cat bpf_lxc.bc)
   ```

2. **Mock Kernel Interface** (Unit Test):
   ```go
   // Mock eBPF map lookups
   policyMap := NewMockMap(policymap.MapName)
   policyMap.Put(identity.NumericIdentity(100), PolicyAllow)

   // Simulate packet processing
   result := processMockPacket(policyMap, sourceIdentity, destIdentity)
   ```

### E. Datapath Testing Checklist

**After Making Changes to Datapath**:

- [ ] Compilation tests pass: `go test ./pkg/datapath/loader/compile*`
- [ ] Loader tests pass: `go test ./pkg/datapath/loader/`
- [ ] eBPF program compiles: `cd bpf && make`
- [ ] eBPF verifier accepts: `bpftool prog show` (no verification errors)
- [ ] Policy tests pass: `go test ./pkg/policy/`
- [ ] Endpoint tests pass: `go test ./pkg/endpoint/`
- [ ] Integration tests (if available): `go test ./test/integration/...`
- [ ] Manual cluster test: Deploy test workload and verify policies work

### F. Debugging Tests

**Enable Debug Logging**:
```go
log.SetLevel(logrus.DebugLevel)
```

**Inspect Generated Files**:
```bash
# Check generated node_config.h
cat /var/run/cilium/node_config.h

# Check generated ep_config.h
cat /var/run/cilium/ep_config_12345.h

# Verify compiled object file
llvm-objdump -d /var/run/cilium/bpf_lxc_12345.o | head -50
```

**Use eBPF Tools**:
```bash
# List loaded programs
bpftool prog list

# Show program details
bpftool prog show id 123

# Dump program bytecode
bpftool prog dump id 123 xlated
```

---

## 6. Debugging

### A. Troubleshooting Program Loading Failures

#### Step 1: Verify Compilation

```bash
# Check if clang is available
which clang
clang --version

# Try manual compilation
cd /workspace/bpf
clang -O2 -target bpf -I./include -c bpf_lxc.c -o bpf_lxc.o

# Check output
llvm-objdump -d bpf_lxc.o | head -30
```

#### Step 2: Inspect Object File

```bash
# List sections
llvm-objdump -h bpf_lxc.o

# List programs
bpftool gen object - bpf_lxc.o | grep "cil_"

# Show map definitions
bpftool gen object - bpf_lxc.o | grep "map"
```

#### Step 3: Verify Generated Configuration Headers

```bash
# Check node configuration
cat /var/run/cilium/node_config.h | head -50

# Verify include guards and defines
grep "ENABLE_" /var/run/cilium/node_config.h

# Check policy map names
grep "policy_map" /var/run/cilium/node_config.h
```

### B. Debugging eBPF Verifier Failures

**Error Message Example**:
```
Error at instruction 42: Illegal instruction
Type mismatch
```

**Investigation Steps**:

```bash
# Get detailed verifier logs
bpftool prog load bpf_lxc.o type sched_cls verbose 2>&1 | grep -A5 "Error"

# Compile with verbose flags
clang -Xclang -target bpf -std=gnu89 -O2 \
  -Wall -Wextra -Werror bpf_lxc.c -c -o bpf_lxc.o

# Examine intermediate representation
clang -emit-llvm -c bpf_lxc.c -o bpf_lxc.ll
cat bpf_lxc.ll | grep "error"
```

**Common Verifier Issues**:

| Issue | Cause | Fix |
|-------|-------|-----|
| Invalid loop bounds | Unbounded iteration | Add explicit bounds checks |
| Invalid memory access | Out-of-bounds array access | Verify array indices before use |
| Invalid call | Calling non-existent helper | Use only approved BPF helpers |
| Unreachable instructions | Dead code paths | Remove unreachable code |
| Stack overflow | Using >512 bytes on stack | Reduce local variables |

### C. Inspecting eBPF Maps at Runtime

```bash
# List all maps
bpftool map list

# Show policy map
bpftool map show id <ID>
bpftool map dump id <ID>

# Look up specific key
bpftool map lookup id <ID> key 0x01 0x00 0x00 0x00

# Dump entire map
bpftool map dump id <ID> > /tmp/map_dump.txt

# Monitor map updates
bpftool map perf_buffer show  # For ringbuffer/perf_buffer maps
```

**Interpreting Policy Map**:
```bash
# Format: key=<identity>, value=<verdict>
# key: source identity (u32)
# value: bitmask of allowed actions
#   - 0x01 = ALLOW
#   - 0x00 = DENY (default)

$ bpftool map dump id 42
key: 00 01 00 00  value: 01 00 00 00   # Identity 256 → ALLOW
key: 00 02 00 00  value: 00 00 00 00   # Identity 512 → DENY
```

### D. Available Debugging Tools

#### 1. Cilium Monitor
```bash
# Monitor packet decisions
cilium monitor --drop        # Show dropped packets
cilium monitor --capture=all # Show all decisions
cilium monitor -j            # JSON output

# Filter by endpoint
cilium monitor --related-to pod/test-namespace/test-pod
```

#### 2. Policy Tracing
```bash
# Trace policy decision
cilium policy trace \
  --source-identity 256 \
  --destination-identity 512

# Verbose output
cilium policy trace --verbose ...

# Show matching rules
cilium policy get
```

#### 3. BPFTool
```bash
# Program inspection
bpftool prog show
bpftool prog dump id <id> xlated    # Show bytecode
bpftool prog dump id <id> jited     # Show JIT-compiled code
bpftool prog disasm id <id>         # Disassemble

# Map inspection
bpftool map show
bpftool map dump id <id>
bpftool map lookup id <id> key <key_bytes>

# Link inspection
bpftool link show
bpftool link pin id <id> /sys/fs/bpf/my_prog
```

#### 4. TC Command
```bash
# Show attached TC programs
tc qdisc show
tc filter show dev eth0

# Show verbose details
tc -s filter show dev eth0

# Check BPF program bytecode
tc filter show dev eth0 ingress filter bpf bytecode
```

#### 5. Kernel Logs
```bash
# Watch eBPF-related logs
dmesg | grep -i ebpf
dmesg | grep -i bpf
dmesg | tail -50

# Enable kernel tracing
echo 1 > /proc/sys/kernel/trace_enabled
trace-cmd record -e syscalls:sys_enter_bpf
```

### E. Performance Debugging

**Identify Performance Issues**:

```bash
# Check map lookup latency
bpftool map show  # List maps
bpftool stat get stats

# Inspect program statistics
bpftool prog stat show

# Use perf to profile
perf record -e bpf:* -g -a sleep 10
perf report
```

**Common Performance Issues**:

| Symptom | Cause | Fix |
|---------|-------|-----|
| High CPU usage | Complex policy evaluation, full CT/LB map scans | Optimize policy rules, increase map size |
| Packet drops | Map full or tail call limit | Increase map size or reduce tail call depth |
| Latency spikes | Lock contention on maps | Use per-CPU maps, reduce lock hold time |

### F. Packet Tracing Through Datapath

```c
// In eBPF program, use:
#include "lib/trace.h"

// Emit trace event
trace_printk("Processing packet, policy=%d", policy_decision);
cilium_monitor_event(ctx, TRACE_TO_CONTAINER);

// In bpf_dbg.h:
trace_ctx()  // Macro for conditional tracing
```

**View Trace Output**:
```bash
# Monitor trace events
cilium monitor --monitor-verbosity=info

# Check kernel trace buffer
cat /sys/kernel/debug/tracing/trace_pipe | grep cilium
```

### G. Root Cause Analysis Template

**When debugging a failure, follow:**

1. **Identify Layer**:
   - Compilation? → Check clang, C syntax, verifier logs
   - Loading? → Check kernel memory, permission, map conflicts
   - Attachment? → Check kernel support, interface state
   - Runtime? → Check packet format, map content, program logic

2. **Inspect Logs**:
   ```bash
   journalctl -u cilium -n 100 -f     # Cilium agent logs
   dmesg -T | tail -50                # Kernel logs
   tail -100 /var/log/cilium/cilium.log  # Agent log file
   ```

3. **Check Configuration**:
   ```bash
   cilium status  # Overall status
   cilium config  # All configuration
   cilium endpoints list  # All endpoints and their status
   ```

4. **Verify State**:
   ```bash
   # BPF map content
   bpftool map dump id <id>

   # Loaded programs
   bpftool prog show

   # Kernel capabilities
   bpftool feature probe
   ```

5. **Isolate Variables**:
   - Disable XDP, test TC only
   - Disable policies, test connectivity
   - Disable encryption, test unencrypted
   - Use minimal policy rules

---

## 7. Adding a New Hook

### Understanding Hook Types

Cilium supports attaching eBPF programs at multiple hook points:

| Hook Type | Location | Program Type | Entry Point | Use Case |
|-----------|----------|--------------|-------------|----------|
| **TC Ingress** | Pod → Host | `BPF_PROG_TYPE_SCHED_CLS` | `cil_from_container` | Ingress policy, identity resolution |
| **TC Egress** | Host → Pod | `BPF_PROG_TYPE_SCHED_CLS` | `cil_to_container` | Egress policy, NAT, encryption |
| **XDP** | Device driver | `BPF_PROG_TYPE_XDP` | `cil_xdp_entry` | Early filtering, DDoS mitigation |
| **netkit** | veth equivalent | `BPF_PROG_TYPE_SCHED_CLS` | `cil_from_netkit` | Modern pod interface processing |
| **TCX** | Modern TC replacement | `BPF_PROG_TYPE_SCHED_CLS` | `cil_from_tcx` | Future-proof TC replacement |
| **Socket filter** | Socket syscalls | `BPF_PROG_TYPE_SOCKET_FILTER` | Custom | Socket-level operations |
| **sockops** | Socket events | `BPF_PROG_TYPE_SOCK_OPS` | Custom | Connection lifecycle tracking |

### Example: Adding an Egress L7 Hook

**Scenario**: You want to add a new hook for L7 protocol processing before encryption.

#### Step 1: Add eBPF Program

**File**: `bpf/bpf_l7_hook.c` (new)

```c
#include <bpf/ctx/skb.h>
#include <bpf/api.h>
#include <node_config.h>
#include <ep_config.h>

#define IS_BPF_L7_HOOK 1
#define EVENT_SOURCE LXC_ID

// Include necessary libraries
#include "lib/common.h"
#include "lib/l3.h"
#include "lib/l4.h"
#include "lib/drop.h"
#include "lib/trace.h"
#include "lib/policy.h"

// Define entry point section for TC egress hook
__section("classifier/l7_egress")
int cil_l7_egress_hook(struct __ctx_buff *ctx)
{
    struct iphdr *ip4 = NULL;
    __u32 protocol = 0;

    // Parse packet
    if (ctx->protocol == htons(ETH_P_IP)) {
        ip4 = (__typeof(ip4))(unsigned long)ctx->data + ETH_HLEN;
        if ((unsigned long)ip4 + sizeof(*ip4) > (unsigned long)ctx->data_end)
            return CTX_ACT_OK;

        protocol = ip4->protocol;
    }

    // Example: Special L7 processing for HTTP
    if (protocol == IPPROTO_TCP) {
        __u16 dport = (__typeof(dport))(unsigned long)(ip4 + 1) + sizeof(struct tcphdr) - 2;
        // dport extraction logic...

        // Check if this is an L7-policy-required flow
        // Call your L7 processing logic
        return cil_l7_process(ctx, ip4);
    }

    // Default: pass through
    return CTX_ACT_OK;
}

// Helper function for L7 processing
static __always_inline int cil_l7_process(struct __ctx_buff *ctx, struct iphdr *ip4)
{
    // Your L7 logic here
    return CTX_ACT_OK;
}

char _license[] __section("license") = "Dual BSD/GPL";
int _version __section("version") = 1;
```

#### Step 2: Update Compilation

**File**: `pkg/datapath/loader/compile.go`

```go
// Add to progInfo definitions (around line 75)
const (
    l7HookPrefix = "bpf_l7_hook"
    l7HookProg   = l7HookPrefix + "." + string(outputSource)
    l7HookObj    = l7HookPrefix + ".o"
)

// In progInfos() function, add:
progInfos := []progInfo{
    // ... existing programs ...
    {
        Source: filepath.Join(l7HookProg),
        Output: l7HookObj,
        OutputType: outputObject,
        Section: "classifier/l7_egress",
    },
}
```

#### Step 3: Update Loader to Attach Hook

**File**: `pkg/datapath/loader/loader.go`

```go
// In loader.ReloadDatapath():
func (l *loader) ReloadDatapath(ctx context.Context, ep Endpoint, stats *SpanStat) (string, error) {
    // ... existing code ...

    // Load the l7_hook program
    l7HookProg := coll.Programs["cil_l7_egress_hook"]
    if l7HookProg == nil {
        log.Warnf("L7 hook program not found")
    } else {
        // Attach l7_hook between existing hooks
        // For example, attach after ingress but before standard egress
        if err := l.attachL7Hook(ctx, ep, l7HookProg); err != nil {
            log.WithError(err).Warnf("Failed to attach L7 hook")
            // Continue with fallback
        }
    }

    // ... rest of function ...
}

// New function: attachL7Hook
func (l *loader) attachL7Hook(ctx context.Context, ep Endpoint, prog *ebpf.Program) error {
    device, err := safenetlink.LinkByName(ep.InterfaceName())
    if err != nil {
        return fmt.Errorf("device not found: %w", err)
    }

    // Attach using TC at priority between standard hooks
    // Priority 50 is between ingress (100) and standard egress (200)
    return attachSKBProgram(
        device,
        prog,
        "cil_l7_egress",
        l.cfg.BpffsBase,
        50,  // Parent/priority
        l.tcxEnabled,
    )
}
```

#### Step 4: Add Type Registration

**File**: `pkg/datapath/loader/template.go`

Update template cache to handle new program:

```go
// Add to WriteNodeConfig() if new program needs configuration:
func (t *templateCache) WriteNodeConfig(w io.Writer, cfg *LocalNodeConfiguration) error {
    // ... existing config writes ...

    // Add L7 hook specific configuration
    fmt.Fprintf(w, "#define L7_HOOK_ENABLED %d\n", cfg.L7HookEnabled)

    return nil
}
```

#### Step 5: Update Tests

**File**: `pkg/datapath/loader/loader_test.go` (add test)

```go
func TestReloadDatapathWithL7Hook(t *testing.T) {
    testutils.PrivilegedTest(t)

    // Setup
    ep := &testutils.TestEndpoint{
        InterfaceName: "veth0",
        Identity: 256,
        IPv4: netip.MustParseAddr("10.0.0.1"),
        Options: map[string]string{
            // Enable L7 hook in config
            "enable-l7-hook": "true",
        },
    }
    initEndpoint(t, ep)

    // Compile and load
    ldr := NewLoader(ctx, &Config{Library: bpfDir, Output: tmpDir})
    symPath, err := ldr.ReloadDatapath(ctx, ep, &metrics.SpanStat{})
    require.NoError(t, err)

    // Verify l7 hook is loaded
    require.FileExists(t, symPath)

    // Optionally: check that the program is attached
    links, err := netlink.LinkList()
    require.NoError(t, err)
    foundL7Hook := false
    for _, link := range links {
        if link.Attrs().Name == "veth0" {
            // Check for L7 hook in filters
            foundL7Hook = true  // Would need more complex checking
        }
    }
}
```

#### Step 6: Documentation

Update documentation:

**File**: `/workspace/Documentation/network/ebpf/l7_hook.md`

```markdown
# L7 Hook

The L7 hook provides application-layer protocol processing before standard
egress policy enforcement.

## Configuration

Enable via: `cilium config set enable-l7-hook=true`

## Performance

The L7 hook adds ~500 CPU cycles to the egress path per packet.
```

#### Step 7: Integration Points

Make hook discoverable:

**File**: `pkg/datapath/linux/config/types.go` (if config struct needed)

```go
type L7HookConfig struct {
    Enabled bool
    Mode    string  // "permissive" or "enforcing"
    MaxRate uint64  // Rate limit for L7 processing
}

func (cfg L7HookConfig) GetOptions() *option.IntOptions {
    return &option.IntOptions{
        // ...
    }
}
```

### Complete Integration Checklist

When adding a new hook, ensure:

- [ ] **eBPF Program**:
  - [ ] Correct program type (TC/XDP/socket/etc.)
  - [ ] Proper section name (`classifier/...`, `xdp/...`)
  - [ ] Compiles without verifier errors
  - [ ] Includes required headers (common.h, drop.h, etc.)
  - [ ] Returns proper action (CTX_ACT_OK, TC_DROP, etc.)

- [ ] **Loader Integration**:
  - [ ] Added to `compile.go` progInfo
  - [ ] Program extracted from loaded collection
  - [ ] Attachment implemented in loader.go
  - [ ] Error handling and fallback logic
  - [ ] Program pinned to bpffs if needed

- [ ] **Configuration**:
  - [ ] Generated headers updated if config needed
  - [ ] Feature flag in node config
  - [ ] Enabled/disabled by runtime option
  - [ ] Performance considerations documented

- [ ] **Maps**:
  - [ ] Any new maps defined in lib/maps.h
  - [ ] Go map wrappers in pkg/maps/
  - [ ] Initial population logic

- [ ] **Testing**:
  - [ ] Unit test for loader
  - [ ] eBPF program test in bpf/tests/
  - [ ] Integration test with real endpoint
  - [ ] Error condition testing

- [ ] **Documentation**:
  - [ ] Code comments explaining logic
  - [ ] README or doc.go
  - [ ] Arch decision record
  - [ ] Performance implications

- [ ] **Observability**:
  - [ ] Metrics for attachment success/failure
  - [ ] Trace/debug output
  - [ ] Monitor hooks available
  - [ ] Error logging

---

## Appendix: Key Code Locations Reference

### Most-Touched Files During Development

```
High Priority (Touch Often):
├── pkg/datapath/loader/loader.go          # Main loader logic
├── bpf/lib/policy.h                       # Policy enforcement
├── bpf/lib/lb.h                           # Load balancing
├── pkg/datapath/loader/base.go            # Program attachment
└── pkg/maps/policymap/policymap.go        # Policy map management

Medium Priority (Touch Occasionally):
├── pkg/datapath/loader/compile.go         # Compilation orchestration
├── pkg/datapath/loader/template.go        # Template caching
├── bpf/lib/conntrack.h                    # Connection tracking
├── pkg/datapath/linux/devices_controller.go # Device management
└── pkg/datapath/types/config.go           # Interface definitions

Low Priority (Reference Only):
├── bpf/lib/nat.h                          # NAT (rarely changed)
├── pkg/datapath/linux/node.go             # Node configuration
├── bpf/lib/encap.h                        # Tunneling (stable)
└── pkg/datapath/linux/probes/             # Kernel probes
```

### Key Data Flow Paths

```
Input: New Pod Created
→ endpoint/endpoint.go: SetupDatapath()
→ loader/loader.go: ReloadDatapath()
→ loader/compile.go: compileDatapathProgramSubcommand()
→ Clang: compile bpf_lxc.c
→ ebpf.CollectionSpec: parse object file
→ bpf() syscall: load programs and maps
→ loader/base.go: attachSKBProgram()
→ netlink: attach to TC hook
→ Output: Pod traffic processed by eBPF

Input: Policy Applied
→ policy/policy.go: policy resolution
→ policymap/policymap.go: Put(identity, decision)
→ bpftool: update kernel map
→ eBPF programs: read updated policy
→ Output: New policy decisions applied to packets
```

### Configuration Flow

```
User Configuration (option.Config)
    ↓
loader/base.go: writeNetdevHeader()
    ↓ generates
netdev_config.h #defines
    ↓ included by
bpf/*.c → Clang
    ↓ compiled to
bpf/*.o with embedded configuration
    ↓ loaded to
Kernel as immutable constants
```

---

## Summary

The Cilium eBPF datapath is a sophisticated system that bridges the gap between kernel-level packet processing and userspace policy management. Understanding this handoff document should give you enough context to:

1. **Understand** how packets flow through the system
2. **Debug** failures at each layer (compilation, loading, attachment, runtime)
3. **Extend** with new capabilities by adding hooks
4. **Maintain** the system through testing and monitoring
5. **Troubleshoot** production issues with systematic debugging approaches

The most important principle: **the datapath processes millions of packets per second, so performance, correctness, and debuggability are paramount**. Every change should be tested thoroughly, and every failure mode should have a clear recovery path.

Good luck maintaining and extending Cilium's eBPF datapath!
