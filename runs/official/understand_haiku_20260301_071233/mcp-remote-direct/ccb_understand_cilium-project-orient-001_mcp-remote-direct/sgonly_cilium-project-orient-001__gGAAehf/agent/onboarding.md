# Cilium Codebase Orientation

## 1. Main Entry Point

The cilium-agent binary starts execution at **`daemon/main.go`**:

```go
func main() {
    agentHive := hive.New(cmd.Agent)
    cmd.Execute(cmd.NewAgentCmd(agentHive))
}
```

### CLI Framework
- **Framework**: [Cobra](https://github.com/spf13/cobra) (github.com/spf13/cobra)
- **Initialization**: Command is created in `daemon/cmd/root.go::NewAgentCmd()`
- **Key configuration setup**:
  - `option.InitConfig()` loads config from files and command-line flags
  - `initEnv()` initializes working directories
  - `h.Run()` starts the hive and all registered components

### Dependency Injection Framework
- **Framework**: Hive (github.com/cilium/cilium/pkg/hive)
- **Main agent definition**: `daemon/cmd/cells.go::Agent` cell module
- **Structure**:
  - `Agent` module imports `Infrastructure` and `ControlPlane` modules
  - `Infrastructure`: External services (K8s client, metrics, REST API, storage)
  - `ControlPlane`: Business logic cells (endpoint manager, policy repository, node manager, etc.)
  - `datapath.Cell`: BPF datapath implementation
- **Configuration binding**: Uses Viper (github.com/spf13/viper) for configuration management via `h.Viper()`

---

## 2. Core Packages

Five essential packages handling the main responsibilities:

### **pkg/policy** - Network Policy Processing
- **Responsibility**: Policy parsing, compilation, and management
- **Key types**: `Repository` (central policy store), `EndpointPolicy` (computed policy for an endpoint)
- **Key files**:
  - `repository.go`: Policy storage and retrieval
  - `distillery.go`: Compiles rules into per-endpoint policies
  - `l4.go`: Layer 4 rule handling (ports, protocols)
  - `mapstate.go`: Maps policies to BPF map entries
- **Core interfaces**: `PolicyManager`, `PolicyRepository`

### **pkg/endpoint** - Endpoint Lifecycle Management
- **Responsibility**: Managing local endpoints (pods/containers), their state, and regeneration
- **Key types**: `Endpoint` struct with fields for identity, policy, datapath state
- **Key files**:
  - `endpoint.go`: Core endpoint definition and state
  - `policy.go`: Policy computation for endpoints (`regeneratePolicy()`, `syncPolicyMap()`)
  - `bpf.go`: BPF map synchronization for endpoints
  - `events.go`: Endpoint event handling
- **Core responsibility**: Tracks which pods run locally, their security identities, and triggers policy enforcement

### **pkg/datapath** - BPF Program & Map Management
- **Responsibility**: Compiling and loading eBPF programs, managing BPF maps
- **Key types**: `Datapath` interface, `BPFProgram` wrapper, map synchronization logic
- **Key files**:
  - `datapath.go`: Main datapath interface
  - Linux-specific in `pkg/datapath/linux/`
- **Core responsibility**: Translates policy into eBPF programs and updates kernel BPF maps used by the datapath

### **pkg/k8s** - Kubernetes Integration
- **Responsibility**: Watching Kubernetes resources, translating them to Cilium constructs
- **Key types**: `Clientset` (K8s API client), `Service`, `Endpoint` structures
- **Key subpackages**:
  - `pkg/k8s/watchers`: Observes K8s resources (Pods, Services, NetworkPolicies, CiliumNetworkPolicies)
  - `pkg/k8s/apis/cilium.io`: Cilium CRD types (CiliumNetworkPolicy, CiliumEndpoint, etc.)
  - `pkg/k8s/resource`: Generic resource watching framework
- **Core responsibility**: Bridges Kubernetes API server to Cilium's in-memory state

### **pkg/endpointmanager** - Endpoint Collection Management
- **Responsibility**: Stores and manages all local endpoints, coordinates updates
- **Key types**: `EndpointManager` interface with methods like `GetPolicyEndpoints()`, `RegenerateAllEndpoints()`
- **Core responsibility**: Central registry of local endpoints, triggers regeneration when policies change

---

## 3. Configuration Loading

The agent loads configuration through a multi-stage pipeline:

### **Configuration Pipeline**

1. **Default Values**: Defined in `pkg/defaults/` and `pkg/option/constants.go`
2. **File-based Config**: Reads from YAML/JSON file (default: `/etc/cilium/cilium.yaml`)
3. **Directory-based Config**: Reads from directory where each file name is a config key (`--config-dir`)
4. **Command-line Flags**: Override file-based config

### **Configuration Libraries & Modules**

- **Viper** (github.com/spf13/viper): Configuration binding library
  - Loaded via `h.Viper()` in the Hive
  - Supports YAML, JSON, TOML, and environment variables

- **Main Config Struct**: `pkg/option/config.go::DaemonConfig`
  - Fields: BPF directories, device names, IP ranges, routing mode, datapath mode, etc.
  - Validation: `DaemonConfig.Validate()` checks configuration consistency
  - Global instance: `option.Config` (singleton)

### **Configuration Initialization Flow** (in `daemon/cmd/root.go`)
```
cobra.OnInitialize() hook:
  1. option.InitConfig() - loads from file/env
  2. initDaemonConfig() - applies daemon-specific overrides
  3. initLogging() - sets up logging with config
→ Viper bound to Hive
→ All cells access config via DaemonConfig dependency injection
```

### **Runtime Configuration Changes**
- `option.DaemonConfig.Opts`: Mutable options that can be changed at runtime via REST API
- Mutable options defined in `pkg/option/runtime_options.go`
- Changes trigger endpoint regeneration when applicable

---

## 4. Test Structure

Cilium uses multiple testing approaches across the codebase:

### **Unit Tests**
- **Location**: Co-located with source files (e.g., `pkg/policy/policy_test.go`)
- **Framework**: Go's standard `testing` package with custom test data builders
- **Example**: `pkg/policy/repository_test.go` tests policy addition/deletion/lookup with mock endpoints
- **Run**: `go test ./pkg/...`

### **Privileged Tests** (BPF-specific)
- **Location**: Files ending in `_privileged_test.go` (e.g., `daemon/cmd/daemon_privileged_test.go`)
- **Requires**: Root access, BPF kernel capabilities
- **Responsibility**: Tests actual BPF program compilation and map operations
- **Run**: `go test -run TestPrivileged -tags=privileged ./...`
- **Example**: Compiling BPF programs, verifying map sizes, testing hook attachment

### **Integration Tests**
- **Location**: `test/` directory (e.g., `test/runtime/`, `test/k8s/`)
- **Framework**: Ginkgo (BDD testing framework)
- **Scope**: Full agent startup with real K8s cluster or mock environment
- **Example**: `test/k8s/` contains tests for Kubernetes integration scenarios
- **Run**: Via Makefile: `make test-runtime`

### **End-to-End Tests**
- **Location**: `test/controlplane/` (agent-only), `test/k8s/` (with K8s)
- **Setup**: Vagrant or Docker-based test environments
- **Scope**: Full deployment scenarios (single-node, multi-node, multi-cluster)
- **Example**: Network connectivity verification, policy enforcement validation

### **BPF Program Tests**
- **Location**: `bpf/` directory with inline test programs
- **Framework**: Custom BPF test harness
- **Scope**: Verifies BPF program behavior in isolation
- **Example**: Testing load balancing logic, NAT logic in BPF code

---

## 5. Network Policy Pipeline

A CiliumNetworkPolicy flows through multiple stages from CRD definition to eBPF enforcement:

### **Stage 1: CRD Definition & K8s Storage**
- **File**: `pkg/k8s/apis/cilium.io/v2/cnp_types.go`
- **Type**: `CiliumNetworkPolicy` CRD
- **Fields**: `Spec` (policy rules), `Specs` (list of rules), `Status` (per-node enforcement status)
- **Rule format**: `api.Rule` containing L3/L4/L7 matching criteria
- **Storage**: Stored in Kubernetes etcd as a custom resource

### **Stage 2: Resource Watching & Translation**
- **Component**: `pkg/policy/k8s/cell.go::Cell` (K8s policy watcher)
- **Inputs**: Watches `CiliumNetworkPolicy`, `CiliumClusterwideNetworkPolicy`, `NetworkPolicy`, `CiliumCIDRGroup` resources
- **Key function**: `startK8sPolicyWatcher()` registers watchers for all policy resources
- **Translation**: Converts K8s policy objects to Cilium's `api.Rules` format
- **Output**: Calls `PolicyManager.PolicyAdd()` to add rules to the repository

### **Stage 3: Policy Repository & Compilation**
- **Component**: `pkg/policy/repository.go::Repository`
- **Function**: Maintains all active policies and compiles them against endpoints
- **Key method**: `PolicyAdd()` adds rules, triggers distillery to recompile affected endpoint policies
- **Distillery**: `pkg/policy/distillery.go` computes which endpoints are affected by a policy
- **Selector matching**: Policies with label selectors are matched against endpoint identities

### **Stage 4: Endpoint Regeneration & Policy Computation**
- **Trigger**: When a policy is added/updated/deleted, affected endpoints are marked for regeneration
- **Component**: `pkg/endpointmanager/manager.go::RegenerateAllEndpoints()`
- **Per-endpoint computation**: `pkg/endpoint/policy.go::regeneratePolicy()`
  - Queries `PolicyRepository` for all applicable rules based on endpoint's identity
  - Computes desired policy state: ingress/egress rules, L7 rules, security identity
  - Result: `EndpointPolicy` struct containing computed policy
- **Output**: `desiredPolicy` set on endpoint

### **Stage 5: BPF Map Synchronization**
- **Component**: `pkg/endpoint/bpf.go::syncPolicyMap()`
- **Process**:
  - Compares `desiredPolicy` (new) vs `realizedPolicy` (currently enforced)
  - Computes diff: rules to add, remove, or update
  - Applies changes to BPF policy maps (`cilium_policy_*` maps)
- **Maps updated**:
  - `cilium_policy_{ingress,egress}`: Port-level policies per endpoint
  - `cilium_ct_*`: Connection tracking state
  - `cilium_lb_*`: Load balancing state
- **BPF program**: eBPF verifier ensures kernel can safely load updated policy

### **Stage 6: Runtime Enforcement**
- **Location**: eBPF programs in `bpf/` directory
- **Enforcement points**:
  - TC (Traffic Control) hooks on pod devices: ingress/egress policy checks
  - XDP (eXpress Data Path) hooks: early-stage drop/allow decisions
- **Lookup**: When a packet arrives, eBPF looks up endpoint ID, then policy map, enforces decision

### **Summary Flow**
```
CRD (CiliumNetworkPolicy YAML)
  ↓
Kubernetes API Server (etcd)
  ↓
K8s Watcher (pkg/policy/k8s/)
  ↓
Policy Repository (pkg/policy/repository.go)
  ↓
Endpoint Regeneration (pkg/endpointmanager/)
  ↓
Per-Endpoint Policy Computation (pkg/endpoint/policy.go)
  ↓
BPF Map Sync (pkg/endpoint/bpf.go)
  ↓
BPF Maps (cilium_policy_*, etc.)
  ↓
eBPF Programs (bpf/tc*.c, bpf/xdp*.c)
  ↓
Kernel Enforcement (packet allow/drop/redirect decisions)
```

---

## 6. Adding a New Network Policy Type (e.g., L7 Protocol Filter)

To add support for a new L7 protocol filter (e.g., a new gRPC method filter), modify the following:

### **Step 1: Define the API Type**
- **File**: `pkg/policy/api/l4.go`
- **Change**: Add new field to `L7Rules` struct (alongside `HTTP`, `Kafka`, `DNS`)
  ```go
  type L7Rules struct {
      HTTP []PortRuleHTTP `json:"http,omitempty"`
      NewProto []PortRuleNewProto `json:"newproto,omitempty"`  // NEW
  }
  ```
- **Also in**: `pkg/policy/api/rule_validation.go` - add validation logic

### **Step 2: Define CRD Schema**
- **File**: `pkg/k8s/apis/cilium.io/client/crds/v2/ciliumnetworkpolicies.yaml`
- **Change**: Add OpenAPI schema validation for the new L7 rule type in the CRD spec
- **Also**: Update CCNP (ClusterwideCNP) CRD for consistency

### **Step 3: Add K8s Type Helpers**
- **File**: `pkg/k8s/apis/cilium.io/v2/cnp_types.go`
- **Change**: May need custom deep copy/equality methods if the new type has complex fields

### **Step 4: Implement Policy Compilation**
- **File**: `pkg/policy/distillery.go` or new file if complex logic
- **Change**: Add logic to handle the new L7 rule type when compiling endpoint policies
  - Check: how does the new rule affect which endpoints? (selector matching, port matching)
  - Compile to: `EndpointPolicy.L7Rules` on affected endpoints

### **Step 5: Add Validation**
- **File**: `pkg/policy/api/rule_validation.go`
- **Change**: Add validation for the new rule type in `Validate()` method
  - Regex validation for fields (if applicable)
  - Check for conflicting rules
  - Ensure protocol is correctly specified

### **Step 6: Implement BPF Integration**
- **File**: `pkg/envoy/xds_server.go` (for L7 proxy) OR `pkg/datapath/` (for direct BPF)
- **For Envoy-based**: Add rule compilation to Envoy configuration (if using HTTP/gRPC proxies)
  - Function: `GetEnvoyHTTPRules()` or similar
  - Generate Envoy listener/route configurations
- **For BPF-based**: Compile rules directly to BPF program
  - Update BPF code in `bpf/` to perform lookups and enforce

### **Step 7: Update Endpoint Policy Sync**
- **File**: `pkg/endpoint/bpf.go::syncPolicyMap()`
- **Change**: Ensure new L7 rule types are correctly written to BPF maps
  - Map names: `cilium_l7_*` (if added) or existing maps
  - Key/value encoding for new rules

### **Step 8: Add Tests**
- **Unit tests**: `pkg/policy/api/rule_validation_test.go` - test validation logic
- **Policy tests**: `pkg/policy/distillery_test.go` - test compilation
- **Integration tests**: `test/controlplane/` - test full pipeline with endpoints
- **Example**: Test that a pod with label `role=client` can call `/newproto/method` but not `/newproto/other`

### **Step 9: Update Documentation**
- **File**: `Documentation/security/policy/language.rst`
- **Change**: Document the new protocol filter syntax, examples, and limitations

### **Step 10: Handle Marshaling/Unmarshaling**
- **File**: `pkg/policy/api/` - if custom JSON/YAML handling needed
- **Change**: Add `UnmarshalJSON()` / `MarshalJSON()` if automatic marshaling is insufficient

### **Key Interdependencies to Consider**
- **K8s watcher**: Automatically picks up new types from `L7Rules` via reflection
- **Policy repository**: Must correctly identify affected endpoints for the new rule
- **BPF map sizes**: May need to increase if new rules require more storage
- **Proxy redirection**: If using Envoy proxy, integrate with `pkg/proxy/` and `pkg/envoy/`
- **Backward compatibility**: Ensure old policies still work after changes

---

## Summary

Cilium uses **Hive** for dependency injection, **Cobra** for CLI, and **Viper** for configuration. The system has a clear separation between **Infrastructure** (K8s integration, storage) and **ControlPlane** (policy logic). Policies flow from Kubernetes CRDs through watchers, into the policy repository, affecting endpoint regeneration, and finally syncing to BPF maps for kernel enforcement. Adding new policy types requires coordinated changes across API types, validation, compilation logic, and BPF integration.
