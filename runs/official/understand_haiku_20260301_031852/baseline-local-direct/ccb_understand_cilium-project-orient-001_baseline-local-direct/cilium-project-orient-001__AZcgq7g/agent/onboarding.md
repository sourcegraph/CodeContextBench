# Cilium Codebase Orientation

## 1. Main Entry Point

### Location: `/workspace/daemon/main.go`

The cilium-agent binary starts with the `main()` function in `/workspace/daemon/main.go` (lines 11-15):

```go
func main() {
	agentHive := hive.New(cmd.Agent)
	cmd.Execute(cmd.NewAgentCmd(agentHive))
}
```

### Dependency Injection Framework: **Cilium Hive**

Cilium uses the **Hive** dependency injection framework (from `github.com/cilium/hive`) to wire components together. The key files are:

- **`/workspace/pkg/hive/hive.go`**: Wraps the upstream hive.New to create a Hive with Cilium defaults
- **`/workspace/daemon/cmd/root.go`**: `NewAgentCmd()` creates the Cobra CLI command and initializes the Hive
- **`/workspace/daemon/cmd/cells.go`**: Defines the hierarchical module structure using Hive cells

### CLI Framework: **Cobra**

CLI is initialized using `github.com/spf13/cobra` in `NewAgentCmd()`. The main root command is defined in `/workspace/daemon/cmd/root.go` (line 20).

### Configuration: **Viper**

Configuration is bound using `github.com/spf13/viper` via `h.RegisterFlags()` and `h.Viper()` calls in the root command initialization.

### Component Initialization Flow

1. **main()** creates a Hive with `cmd.Agent` module
2. **Hive.Run()** is called from the root Cobra command (line 40 in root.go)
3. The Hive wires together all cells and starts them in dependency order
4. Components are injected via constructor functions defined in cells

---

## 2. Core Packages

### Five Key Core Packages:

#### 1. **`pkg/policy`** - Network Policy Repository and State
- **Purpose**: Core policy engine that maintains the policy repository, parses policy rules, and generates the policy decision logic for endpoints
- **Key Files**:
  - `repository.go`: Policy repository implementation
  - `l4.go`: L4 filter and port range logic
  - `mapstate.go`: Maps policy rules to eBPF map state
  - `distillery.go`: Policy derivation and optimization
- **Responsibilities**:
  - Manages policy rules from CRDs
  - Generates datapath decisions (allow/deny)
  - Handles policy revisions and dependencies

#### 2. **`pkg/endpoint`** - Endpoint Lifecycle and Synchronization
- **Purpose**: Manages individual endpoints (pods/containers), their state, and policy enforcement
- **Key Files**:
  - `endpoint.go`: Core endpoint state machine
  - `policy.go`: Policy application to endpoints
  - `bpf.go`: eBPF program compilation and loading for endpoints
  - `regeneration/`: Endpoint regeneration orchestration
- **Responsibilities**:
  - Maintains endpoint identities, labels, and security information
  - Coordinates endpoint policy regeneration
  - Synchronizes policy rules to eBPF maps via policymap

#### 3. **`pkg/datapath`** - eBPF Datapath and System Integration
- **Purpose**: Abstracts the network datapath implementation (primarily eBPF on Linux)
- **Key Subdirectories**:
  - `loader/`: eBPF program compilation, loading, and management
  - `linux/`: Linux-specific datapath implementation
  - `maps/`: eBPF maps definitions and operations
  - `types/`: Datapath interfaces and contracts
- **Responsibilities**:
  - Compiles eBPF programs from C source
  - Loads/unloads eBPF programs into kernel
  - Manages eBPF map creation and synchronization
  - Handles BPF tail calls and program chains

#### 4. **`pkg/k8s`** - Kubernetes Integration and CRD Watching
- **Purpose**: Integrates Cilium with Kubernetes, watches CRDs, and synchronizes state
- **Key Subdirectories**:
  - `apis/cilium.io/v2/`: CRD type definitions (CiliumNetworkPolicy, ClusterwideCiliumNetworkPolicy, etc.)
  - `watchers/`: Kubernetes resource watchers for policies, services, endpoints, etc.
  - `client/`: Kubernetes client setup and management
- **Key Packages**:
  - `policy/k8s/`: CiliumNetworkPolicy watcher and processor
- **Responsibilities**:
  - Watches CiliumNetworkPolicy CRDs
  - Translates K8s NetworkPolicies to Cilium rules
  - Syncs endpoint information from Kubernetes
  - Manages security identities

#### 5. **`pkg/endpointmanager`** - Endpoint Collection Management
- **Purpose**: Maintains a collection of all locally running endpoints and provides lookup/query facilities
- **Key Files**:
  - `endpointmanager.go`: Endpoint manager implementation
  - `cell.go`: Hive cell for dependency injection
- **Responsibilities**:
  - Maintains endpoint registry indexed by various keys (ID, IP, container name, etc.)
  - Provides thread-safe access to endpoints
  - Coordinates endpoint creation, deletion, and updates
  - Triggers endpoint regeneration on policy changes

### Honorable Mentions - Also Core:

- **`pkg/maps/policymap/`**: eBPF policy map management (maps policy rules to kernel BPF maps)
- **`pkg/identity`**: Security identity allocation and management
- **`pkg/ipcache`**: IP-to-identity mapping cache for policy lookups

---

## 3. Configuration Loading

### Configuration Pipeline

Cilium supports multiple configuration sources in a priority-based pipeline:

1. **Default Values** (hardcoded in `pkg/defaults/`)
2. **Configuration File** (YAML, default: `/etc/cilium/cilium.yaml`)
3. **Configuration Directory** (`--config-dir` flag, `/etc/cilium/config.d/`)
4. **Environment Variables** (prefixed with `CILIUM_`)
5. **Command-Line Flags**

### Configuration Flow (from `daemon/cmd/root.go`):

```
1. cobra.OnInitialize() callbacks execute:
   - option.InitConfig() loads config file and env vars (line 67)
   - initDaemonConfig() initializes daemon-specific config (line 72)
   - initLogging() sets up logging (line 74)

2. option.InitConfig() (pkg/option/config.go:4215):
   - Reads config file specified by --config or default
   - Reads config directory if specified
   - Binds viper with CILIUM_ env prefix
   - Validates and merges all sources

3. Configuration is stored in option.Config (DaemonConfig struct)
```

### Configuration Libraries and Structures

- **Configuration Binding Library**: `github.com/spf13/viper`
- **Main Config Struct**: `pkg/option/DaemonConfig` (pkg/option/config.go:1401)
  - Contains 200+ configuration fields covering:
    - Network modes (datapath, tunneling, routing)
    - Policy enforcement options
    - IPAM configuration
    - K8s integration options
    - Monitoring and debugging settings
    - eBPF and kernel version requirements

- **Config File Formats Supported**:
  - YAML (primary format)
  - Environment variables
  - Key-value files in a directory (one key-value pair per file)

### Key Configuration Init Functions

- `option.InitConfig()` - Main initialization (returns a cobra.OnInitialize callback)
- `option.Config.Validate()` - Validates configuration before daemon starts
- `initDaemonConfig()` - Daemon-specific initialization in daemon_main.go

---

## 4. Test Structure

Cilium uses multiple complementary testing approaches:

### 1. **Unit Tests** (Standard Go Tests)
- **Location**: `*_test.go` files alongside source code throughout `pkg/`
- **Pattern**: Uses `testing.T` and assertion libraries (testify/assert)
- **Examples**:
  - `pkg/policy/policy_test.go`
  - `pkg/option/config_test.go`
  - `pkg/maps/policymap/policymap_test.go`
- **Run with**: `go test ./pkg/...`

### 2. **Privileged Tests** (Require Root)
- **Identified by**: `testutils.PrivilegedTest(t)` call in test function
- **Examples**:
  - `daemon/cmd/daemon_privileged_test.go` - Tests system networking (netlink operations)
  - `pkg/maps/policymap/policymap_privileged_test.go` - Tests eBPF map operations
- **Purpose**: Test functionality requiring elevated privileges (eBPF, netlink, cgroups)
- **Run with**: `go test -run TestName` with `sudo` privileges

### 3. **Integration Tests** (End-to-End)
- **Location**: `/workspace/test/` directory
- **Subdirectories**:
  - `test/k8s/` - Kubernetes integration tests with Ginkgo framework
  - `test/controlplane/` - Control plane unit tests
  - `test/bpf/` - eBPF program behavior tests
  - `test/l4lb/` - Load balancer tests
  - `test/eks/`, `test/gke/` - Cloud-specific integration tests
- **Framework**: Uses Ginkgo and Gomega for test organization
- **Pattern**: Full Cilium deployment in test environment with policy application
- **Run via**: Vagrant/VM-based test framework (see `/workspace/test/Vagrantfile`)

### 4. **BPF/Datapath Tests**
- **Location**: `bpf/tests/` and embedded in endpoint tests
- **Purpose**: Tests eBPF program correctness
- **Tools**: Custom BPF test helpers and assertion framework
- **Examples**: Verifying packet processing, policy enforcement at the eBPF level

### 5. **Fuzzing Tests**
- **Location**: `*_fuzz_test.go` files
- **Example**: `pkg/policy/fuzz_test.go`
- **Purpose**: Fuzzing policy parsing and rule generation
- **Framework**: Go's native fuzzing (Go 1.18+)

### Test Build Tags

- `// +build privileged` or `//go:build` with privileged constraints
- Tests requiring specific conditions are tagged and can be skipped in standard CI runs

### Test Organization Best Practices Observed

1. Tests are co-located with source code
2. Privileged and unprivileged tests are separate
3. Integration tests are in a dedicated `/test` directory
4. Unit tests use testify/assert for readable assertions
5. Controller group and goroutine cleanup is carefully managed

---

## 5. Network Policy Pipeline

### Complete Path from CRD to eBPF Enforcement

#### **Stage 1: CRD Definition and Watching**
**Files**:
- `pkg/k8s/apis/cilium.io/v2/cnp_types.go` - CiliumNetworkPolicy CRD definition
- `pkg/policy/k8s/watcher.go` - K8s resource watcher
- `pkg/policy/k8s/cilium_network_policy.go` - Policy change handlers

**Components**:
- Kubernetes informs watch for `CiliumNetworkPolicy` and `ClusterwideCiliumNetworkPolicy` CRDs
- When CRD is created/updated/deleted, the watcher detects changes
- `policyWatcher.onUpsert()` is called for additions/updates
- `policyWatcher.onDelete()` is called for deletions

**Data**:
- CRD spec contains `api.Rule` with ingress/egress rules and selectors
- Each rule can contain L3 (CIDR), L4 (protocol/port), and L7 (HTTP, DNS) matchers

#### **Stage 2: Policy Parsing and Repository Update**
**Files**:
- `pkg/policy/repository.go` - Policy repository
- `pkg/policy/api/rule.go` - Rule parsing and validation
- `pkg/policy/l4.go` - L4 filter processing

**Components**:
- `policyWatcher.upsertCiliumNetworkPolicyV2()` calls `cnp.Parse()` to convert YAML to Rule objects
- Rules are passed to `policyManager.PolicyAdd(rules, options)`
- Policy repository stores rules indexed by source and resource ID
- Policy distillery (`policy/distillery.go`) derives per-endpoint policy from stored rules

**Key Logic**:
- Reference resolution (CiliumCIDRGroup references are expanded)
- ToServices references are resolved to actual services
- Duplicate detection and validation
- Policy revision is incremented

#### **Stage 3: Endpoint Selection and Filtering**
**Files**:
- `pkg/policy/repository.go` - `SelectPolicies()` method
- `pkg/endpoint/policy.go` - Endpoint policy application
- `pkg/labels/` - Label selection logic

**Components**:
- Policy rules have selectors (e.g., `k8s:app=web`)
- Repository evaluates which endpoints match which policies
- For each endpoint with a security identity, compute applicable rules
- Endpoint labels are matched against policy selectors

**Key Logic**:
- Label-based matching using label selectors
- Identity-based lookups for performance
- Deny policies are evaluated separately from allow policies

#### **Stage 4: Endpoint Regeneration and Datapath Sync**
**Files**:
- `pkg/endpoint/regeneration/` - Regeneration orchestration
- `pkg/endpoint/bpf.go` - eBPF compilation and loading
- `pkg/endpoint/policy.go` - Policy-to-eBPF translation
- `pkg/maps/policymap/policymap.go` - Policy map structure

**Components**:
- `endpoint.Regenerate()` is triggered when policy changes
- Generates new eBPF programs from template with endpoint-specific constants
- Compiles eBPF source to object files using LLVM/clang
- For each endpoint:
  - Generate header file with policy rules in a decision tree format
  - Compile `cilium/bpf/Makefile` to build endpoint-specific BPF programs
  - Load programs into kernel
  - Create/update `cilium_policy_<epid>` BPF map
  - Populate map with policy decision entries (Identity, Port, Protocol → Allow/Deny)

**Key Data Structures**:
- `PolicyKey`: Identity + Protocol + Port tuple for map lookups
- `PolicyEntry`: Action (allow/deny) + statistics
- Decision tree compiled into eBPF bytecode

---

### Summary of the Four Main Stages:

1. **CRD Creation** → K8s watcher detects `CiliumNetworkPolicy`
2. **Policy Parsing** → Rules extracted, stored in policy repository, revision bumped
3. **Endpoint Matching** → Policy repository determines which rules apply to which endpoints
4. **eBPF Enforcement** → Endpoint regenerates BPF programs and syncs policy maps to kernel

---

## 6. Adding a New Network Policy Type

### Scenario: Adding Support for a New L7 Protocol Filter (e.g., gRPC)

### Required Changes (In Order):

#### **Step 1: Define the New Rule Type in Policy API**
**Files to Modify**:
- `pkg/policy/api/` - Add new protocol support

**Changes**:
1. Create `pkg/policy/api/grpc.go` (new file) to define:
   ```go
   type PortRuleGRPC struct {
       // Service name to match
       Services []string
       // Method name patterns
       Methods []string
       // Metadata header matching
       Metadata []HeaderMatch
   }
   ```

2. Update `pkg/policy/api/l7.go` if it exists, or create:
   - Add gRPC variant to allow definition in rules

3. Update `pkg/policy/api/rule.go`:
   - Add `GRPC *PortRuleGRPC` field to `PortRule` struct
   - Update rule validation logic

#### **Step 2: Update CRD Type Definitions**
**Files to Modify**:
- `pkg/k8s/apis/cilium.io/v2/cnp_types.go` and related rule types

**Changes**:
1. Ensure `api.Rule` (from Step 1) is embedded
2. Update validation kubebuilder tags if needed
3. Update CRD examples in `api/` directory

#### **Step 3: Update Policy Parsing Logic**
**Files to Modify**:
- `pkg/policy/api/rule.go` - Add validation
- `pkg/policy/repository.go` - Update policy derivation if needed

**Changes**:
1. In rule validation, validate gRPC-specific fields
2. Update `GetL7Rules()` if it exists to handle gRPC
3. Update policy distillery if special handling needed

#### **Step 4: Update Envoy Integration (L7 Proxy)**
**Files to Modify**:
- `pkg/envoy/` or `pkg/proxy/`
- Likely need to integrate with Envoy configuration generation

**Changes**:
1. Extend Envoy config generation to translate gRPC rules to Envoy RBACs
2. Add gRPC-specific routing rules to Envoy configuration

#### **Step 5: Update Endpoint Policy Compilation**
**Files to Modify**:
- `pkg/endpoint/policy.go` - Endpoint policy application
- `pkg/endpoint/bpf.go` - eBPF template updates if needed

**Changes**:
1. Update `Endpoint.updateNetworkPolicy()` to handle gRPC rules
2. Pass gRPC rules to proxy configuration
3. If BPF-level enforcement is needed, update policy map structure

#### **Step 6: Update Tests**
**Files to Add/Modify**:
- `pkg/policy/api/rule_validation_test.go` - Add gRPC validation tests
- `pkg/policy/repository_test.go` - Test gRPC rule selection
- `pkg/k8s/apis/cilium.io/v2/*_test.go` - Test CRD parsing
- `daemon/cmd/policy_test.go` - Integration tests

**New Test Files**:
- `pkg/policy/api/grpc_test.go` - Unit tests for gRPC rule parsing

#### **Step 7: Update Documentation and Examples**
**Files to Create/Modify**:
- `examples/policies/` - Add example CNP with gRPC rules
- `Documentation/policy/` - Document new rule type

#### **Step 8: Update Maps/Constants (if needed)**
**Files to Modify** (if BPF-level enforcement required):
- `pkg/maps/policymap/` - May need to extend map key/value structures
- `bpf/lib/` - Update BPF helper functions to understand gRPC protocol

---

### Implementation Order Summary:

1. **Policy API definition** (pkg/policy/api/)
2. **CRD types** (pkg/k8s/apis/)
3. **Policy parsing** (pkg/policy/)
4. **Proxy/Envoy integration** (pkg/envoy/, pkg/proxy/)
5. **Endpoint policy application** (pkg/endpoint/)
6. **Tests throughout** (alongside each change)
7. **Documentation**

### Key Design Principles to Follow:

- **Separation of Concerns**: Policy rules are defined in API, parsed in repository, enforced by proxies/datapath
- **No Datapath Changes if Possible**: If gRPC is purely L7, only proxy integration is needed (no eBPF changes)
- **Backward Compatibility**: New rule types should be optional fields
- **Test Coverage**: Every new field should have corresponding unit and integration tests
- **Consistent Naming**: Follow existing patterns (e.g., `PortRuleGRPC` like `PortRuleHTTP`)

---
