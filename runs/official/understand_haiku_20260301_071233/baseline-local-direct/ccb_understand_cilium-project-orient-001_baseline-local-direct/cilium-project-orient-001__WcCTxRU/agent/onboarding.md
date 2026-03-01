# Cilium Codebase Orientation

## 1. Main Entry Point

The cilium-agent binary starts execution in `/workspace/daemon/main.go`:

```go
func main() {
	agentHive := hive.New(cmd.Agent)
	cmd.Execute(cmd.NewAgentCmd(agentHive))
}
```

**Key Components:**

- **Main Function**: `/workspace/daemon/main.go:11-15`
- **Root Command**: `/workspace/daemon/cmd/root.go` - Defines `NewAgentCmd()` which creates a Cobra CLI command with configuration loading and validation
- **Dependency Injection Framework**: **Hive** (`github.com/cilium/hive`) - A lightweight dependency injection framework used to wire all components
  - Defined in: `/workspace/daemon/cmd/cells.go` - Contains the `Agent` cell definition that registers all infrastructure, control plane, and datapath cells
  - Uses a modular cell-based architecture where each component is a "cell" that can declare its dependencies

**Configuration Pipeline:**
1. `option.InitConfig()` - Called via Cobra's `OnInitialize` hooks in `/workspace/daemon/cmd/root.go:67`
2. Loads configuration from multiple sources:
   - Config file (specified via `--config` flag or default `$HOME/ciliumd.yaml`)
   - Config directory (via `--config-dir` flag) - reads individual files for each option
   - Command-line flags
   - Environment variables (prefixed with `CILIUM_`)

**Configuration Library**: **Viper** (`github.com/spf13/viper`) and **Cobra** (`github.com/spf13/cobra`)

---

## 2. Core Packages

### Core Packages Under `pkg/`

1. **`pkg/policy`** - Network policy management and enforcement
   - Responsible for parsing, storing, and computing network policies
   - `Repository` struct manages policy rules
   - `PolicyCache` and `SelectorPolicy` cache resolved policies
   - Distillery (`distillery.go`) computes endpoint-specific policies
   - Key interfaces: `Repository.PolicyAdd()`, `Repository.PolicyDelete()`, `PolicyCache`

2. **`pkg/datapath`** - eBPF and datapath programming layer
   - **`pkg/datapath/linux`** - Linux-specific datapath implementation
   - **`pkg/datapath/maps`** - Interface definitions for BPF maps
   - **`pkg/datapath/types`** - Core datapath interfaces (Datapath, Orchestrator, Compiler)
   - Responsible for compiling BPF programs, managing datapath state, and coordinating with the kernel
   - `Orchestrator` interface for reinitializing base programs when configuration changes

3. **`pkg/endpoint`** - Endpoint (pod/container) management
   - Core struct: `Endpoint` in `endpoint.go` - represents a single container/pod
   - Handles endpoint lifecycle: creation, update, deletion
   - Implements policy resolution for individual endpoints via `updateNetworkPolicy()`
   - `RegeneratorCell` provides utilities for endpoint regeneration
   - Tracks endpoint state, identities, and security policies

4. **`pkg/endpointmanager`** - Manages all local endpoints
   - Maintains collection of locally running endpoints
   - Provides `EndpointManager` interface for accessing, creating, and deleting endpoints
   - Handles endpoint synchronization with Kubernetes

5. **`pkg/k8s`** - Kubernetes integration layer
   - **`pkg/k8s/watchers`** - Kubernetes resource watchers (pods, services, network policies)
   - **`pkg/k8s/client`** - Kubernetes API client wrappers
   - **`pkg/k8s/apis/cilium.io`** - CRD type definitions (CiliumNetworkPolicy, CiliumClusterwideNetworkPolicy, etc.)
   - Handles pod discovery, endpoint provisioning, and service tracking

6. **`pkg/identity`** - Security identity management
   - Allocates and manages numeric identities for pods/nodes
   - `IdentityAllocator` manages the mapping of labels to identities
   - Provides `Identity` struct with label information
   - Critical for policy enforcement - policies are defined in terms of identities

7. **`pkg/ipcache`** - IP-to-Identity mapping cache
   - Maintains bidirectional mapping between IP addresses and security identities
   - Synchronized with datapath via BPF maps
   - Used for policy enforcement and traffic steering

---

## 3. Configuration Loading

**Configuration Struct**: `option.DaemonConfig` in `/workspace/pkg/option/daemon.go`

**Main Config File**: `/workspace/pkg/option/config.go` - Contains ~4300 lines with configuration options, validation, and loading logic

**Configuration Loading Pipeline:**

1. **Entry Point**: `option.InitConfig()` at `/workspace/pkg/option/config.go:4215`
   - Creates a callback function that is invoked via Cobra's `OnInitialize()` hook

2. **Configuration Sources** (in priority order):
   - **Config Directory** (`--config-dir` flag): Reads individual files from directory where filename = option name, file content = option value
     - Validated via `validateConfigMap()` and merged via `MergeConfig()`
   - **Config File** (`--config` flag or default): YAML format
     - Uses `viper.ReadInConfig()` to load
   - **Command-line Flags**: Registered via `h.RegisterFlags()` in `root.go:48`
   - **Environment Variables**: Prefixed with `CILIUM_` (set via `viper.SetEnvPrefix()`)

3. **Configuration Library Stack**:
   - **Viper** (`github.com/spf13/viper`) - Configuration management with multiple source support
   - **Cobra** (`github.com/spf13/cobra`) - CLI framework and flag parsing
   - **Pflag** (`github.com/spf13/pflag`) - POSIX-style flag parsing

4. **Configuration Validation**:
   - `option.Config.Validate()` validates after initial loading
   - Custom validators for specific options via `option.Config.Opts.Library.ValidateConfigurationMap()`
   - Deprecated field replacement via `ReplaceDeprecatedFields()`

5. **Key Configuration Modules**:
   - `pkg/option/option.go` - Option library with validation logic
   - `pkg/option/daemon.go` - Daemon-specific config struct
   - `pkg/ipam/option/ipam.go` - IPAM-specific config options

---

## 4. Test Structure

Cilium uses multiple testing approaches organized by type and privilege level:

### Unit Tests
- **Standard Go tests** (`*_test.go` files)
- Run with `go test` without special privileges
- Located alongside source files
- Examples: `/workspace/daemon/cmd/daemon_test.go`, `/workspace/pkg/policy/l4_test.go`
- Use **Hive test framework** (`github.com/cilium/hive/hivetest`) for testing dependency-injected code
  - Example: `DaemonSuite` in `/workspace/daemon/cmd/daemon_test.go` uses `hive.Hive` for testing

### Privileged Tests
- **File naming**: `*_privileged_test.go`
- **Trigger**: Call `testutils.PrivilegedTest(t)` at start of test - skips test if not running as root
- Used for tests that need kernel access, network namespaces, or system-level operations
- Examples: `/workspace/daemon/cmd/daemon_privileged_test.go`, `/workspace/pkg/maps/policymap/policymap_privileged_test.go`
- Can create network namespaces, netlink operations, eBPF map operations

### BPF Tests
- **BPF program unit tests**: C code tests in `/workspace/bpf/tests/` directory
- **BPF test harness**: `/workspace/bpf/tests/bpftest/bpf_test.go` - Go test that compiles and runs BPF tests
- Examples: `bpf_ct_tests.c`, `bpf_nat_tests.c`, `conntrack_test.c`
- Use custom test framework in C headers (`builtin_test.h`)

### Integration Tests
- **Control Plane Tests**: `/workspace/test/controlplane/`
  - Kubernetes integration tests using Ginkgo framework
  - Test CNP handling, service integration, node management
  - Located in subdirectories: `node/`, `pod/`, `services/`
- **Run requirements**: Full Kubernetes cluster (via Vagrant or other K8s setup)

### End-to-End Tests
- Test directory structure: `/workspace/test/` contains various E2E test suites
- Subdirectories: `consul/`, `bpf/`, `bigtcp/`, `eks/`, `gke/` for different test scenarios
- Use Vagrant or cloud provider setups

### Fuzz Tests
- **Fuzzing tests**: `fuzz_test.go` files (e.g., `/workspace/pkg/policy/fuzz_test.go`)
- Use Go's native fuzzing framework
- Test robustness of parsing and validation logic

### Test Utilities
- **Shared test utilities**: `/workspace/pkg/testutils/`
  - `IntegrationTests()` - Check if running integration tests
  - `PrivilegedTest()` - Check for root privileges
  - Mock implementations for testing without real resources

---

## 5. Network Policy Pipeline

A CiliumNetworkPolicy (CNP) from Kubernetes API to eBPF enforcement flows through these stages:

### Stage 1: CRD Definition & Kubernetes Storage
- **CRD Type**: `github.com/cilium/cilium/pkg/k8s/apis/cilium.io/v2.CiliumNetworkPolicy`
- **Files**:
  - Type definition: `/workspace/pkg/k8s/apis/cilium.io/v2/cnp_types.go`
  - Status struct: `CiliumNetworkPolicyStatus`, `CiliumNetworkPolicyNodeStatus`
- **Structure**:
  - `Spec` field: Single `api.Rule`
  - `Specs` field: List of `api.Rules`
  - Policy rules defined in: `/workspace/pkg/policy/api/` (rule.go, selector.go, l4.go, etc.)

### Stage 2: Kubernetes Watcher & Event Reception
- **Watcher**: `/workspace/pkg/policy/k8s/watcher.go:watchResources()`
  - Uses Kubernetes `resource.Resource` API for watching CiliumNetworkPolicy, CiliumClusterwideNetworkPolicy, and CiliumCIDRGroup resources
  - Handles three event types: `Upsert`, `Delete`, `Sync`
- **Cache**: `policyWatcher.cnpCache` (map of `resource.Key` → `types.SlimCNP`)
- **Event Flow**:
  ```
  K8s Event → watchResources() → onUpsert()/onDelete() → resolveCiliumNetworkPolicyRefs()
  ```

### Stage 3: Policy Reference Resolution & Translation
- **References**: Resolves external resource references in policies:
  - `CiliumCIDRGroup` references (via `resolveCIDRGroupRef()`)
  - `ToServices` references (via `resolveToServices()`)
- **Translation**: Inlines external references into "translated" CNP
- **Output**: Creates intermediate `types.SlimCNP` representation with resolved references

### Stage 4: Policy Repository Import & Identity Binding
- **Parser**: `types.SlimCNP.Parse()` converts raw policy to internal representation
- **Repository**: `policy.Repository` at `/workspace/pkg/policy/repository.go`
  - Stores all imported policies
  - Method: `PolicyAdd()` imports parsed rules
  - Method: `PolicyDelete()` removes policies
- **Identity Binding**: Policies are cached against security identities via `PolicyCache`
  - Cache key: `identity.NumericIdentity`
  - Enables per-endpoint policy resolution
- **Source Tracking**: Policies tracked by `source.CustomResource` to enable bulk updates/deletes by resource

### Stage 5: Endpoint Regeneration & Policy Computation
- **Trigger**: Policy changes trigger endpoint regeneration
- **Endpoint Selection**: Policy repository identifies affected endpoints via label selectors
- **Policy Computation**: For each endpoint:
  - `policy.PolicyCache.updateSelectorPolicy(identity)` resolves policy for endpoint's identity
  - `distillery.go:Consume()` computes endpoint-specific `EndpointPolicy`
  - Result: Ingress/egress allow rules, L4 filters, L7 policies, proxy redirects
- **Update**: `endpoint.updateNetworkPolicy()` publishes policy to L7 proxies

### Stage 6: BPF Map Programming & Kernel Enforcement
- **Map Types**:
  - `policy_map` (per-endpoint): Stores allow/deny rules indexed by remote identity
  - `cilium_call_map`: Program call stack for module composition
  - `ipcache`: IP-to-identity mapping for datapath lookups
- **Policy Map Update**: `/workspace/pkg/maps/policymap/policymap.go`
  - Method: `PolicyMap.UpdatePolicy()` writes endpoint policy into BPF map
  - Format: `policy_entry_v2` struct (allow/deny flags, port ranges, protocol masks)
- **eBPF Program Enforcement**:
  - BPF programs in `/workspace/bpf/` load policy from maps
  - On packet arrival: lookup sender identity → lookup rules in policy_map → apply allow/deny decisions
  - Redirect matching traffic to L7 proxies as needed

### Key Components at Each Stage
1. **CRD Types**: `/workspace/pkg/k8s/apis/cilium.io/v2/`
2. **K8s Watcher**: `/workspace/pkg/policy/k8s/cilium_network_policy.go`, `watcher.go`
3. **Policy Repository**: `/workspace/pkg/policy/repository.go`
4. **Policy Cache/Distillery**: `/workspace/pkg/policy/distillery.go`
5. **Endpoint Policy**: `/workspace/pkg/endpoint/policy.go`
6. **BPF Maps**: `/workspace/pkg/maps/policymap/`
7. **BPF Programs**: `/workspace/bpf/`

---

## 6. Adding a New Network Policy Type

To add a new network policy type (e.g., a new L7 protocol filter), follow this sequence:

### 1. Define the API Type
**Location**: `/workspace/pkg/policy/api/`
- Create or modify a file (e.g., `newprotocol.go`)
- Define struct:
  ```go
  type NewProtocolRule struct {
    // Fields for the rule
  }
  ```
- Add validation methods:
  ```go
  func (r *NewProtocolRule) Validate() error { ... }
  ```
- Update `/workspace/pkg/policy/api/rule.go` to include the new type in `Rule` struct
- Update `/workspace/pkg/policy/api/rule_validation.go` to add validation logic

### 2. Implement Policy Distillation
**Location**: `/workspace/pkg/policy/`
- Update `distillery.go`:
  - Modify `EndpointPolicy` struct (or related structs) to include new rule type
  - Update `Consume()` logic to compute endpoint-specific rules for new type
- Update `repository.go`:
  - Update rule merging and conflict resolution logic if needed
  - Ensure `PolicyAdd()` and `PolicyDelete()` handle new type

### 3. Update L4 Filter Logic
**Location**: `/workspace/pkg/policy/l4.go`
- Update L4 filter matching to account for new protocol
- Modify `L4Filter` struct if new type has L4 components
- Update filter compilation logic in `l4.go`

### 4. Update BPF Map Format
**Location**: `/workspace/pkg/maps/policymap/`
- Modify `policymap.go`:
  - Update policy entry struct if new protocol requires new fields
  - Update `PolicyMap.UpdatePolicy()` to encode new rule type into BPF map
  - Add helper functions for new protocol if needed

### 5. Implement BPF Program Logic
**Location**: `/workspace/bpf/`
- Update BPF programs that enforce policies:
  - `bpf/lib/l4.h` - L4 filter lookup logic
  - `bpf/lib/policy.h` - Policy decision logic
  - Add new protocol handling in packet processing path
- Add BPF tests in `/workspace/bpf/tests/` to verify new protocol is enforced correctly

### 6. Update Endpoint Policy Application
**Location**: `/workspace/pkg/endpoint/`
- Update `endpoint.go`:
  - Modify endpoint state tracking if new protocol requires tracking
  - Update `desiredPolicy` computation if needed
- Update `policy.go`:
  - Modify proxy redirect logic if new protocol requires L7 proxy
  - Update `proxyID()` and redirect port lookup if applicable

### 7. Update K8s CRD Parser
**Location**: `/workspace/pkg/policy/k8s/`
- Update parser in `watcher.go` if new type needs special handling
- Ensure `cnp.Parse()` in `cilium_network_policy.go` correctly converts K8s API to policy API

### 8. Add Tests
**Location**: Various `*_test.go` files
- Unit tests: `/workspace/pkg/policy/api/*_test.go` - Test parsing and validation
- Integration tests: `/workspace/daemon/cmd/policy_test.go` - Test policy application to endpoints
- BPF tests: `/workspace/bpf/tests/` - Test BPF enforcement

### 9. Update CiliumNetworkPolicy CRD Type
**Location**: `/workspace/pkg/k8s/apis/cilium.io/v2/cnp_types.go`
- May need to update status fields if new type has special status requirements
- Ensure Kubernetes API validation rules are documented

### File Change Summary
```
/workspace/pkg/policy/api/newprotocol.go           (NEW or modified)
/workspace/pkg/policy/api/rule.go                  (modify Rule struct)
/workspace/pkg/policy/api/rule_validation.go       (modify validation)
/workspace/pkg/policy/distillery.go                (modify EndpointPolicy computation)
/workspace/pkg/policy/repository.go                (update policy merging if needed)
/workspace/pkg/policy/l4.go                        (add filter matching logic)
/workspace/pkg/maps/policymap/policymap.go         (update map entry format)
/workspace/bpf/lib/l4.h                            (add BPF logic)
/workspace/bpf/lib/policy.h                        (update policy decision logic)
/workspace/pkg/endpoint/policy.go                  (update proxy redirect logic if needed)
/workspace/pkg/policy/k8s/watcher.go               (add special handling if needed)
/workspace/pkg/k8s/apis/cilium.io/v2/cnp_types.go (update CRD if needed)
/workspace/pkg/policy/api/*_test.go                (add tests)
/workspace/daemon/cmd/policy_test.go               (add integration tests)
/workspace/bpf/tests/newprotocol_test.c            (add BPF tests)
```

### Key Insights
- **Policy as Identity-Based Rules**: Policies are compiled into rules indexed by source identity, not individual IP addresses
- **BPF Map is Authority**: The BPF map is the source of truth for kernel enforcement; all policy changes must flow through BPF map updates
- **Endpoint Regeneration**: Policy changes trigger full endpoint regeneration to ensure consistency
- **Layered Enforcement**: L3/L4 filtering happens in eBPF; L7 filtering happens in user-space proxies coordinated via BPF redirect rules
