# Cilium Codebase Orientation

## 1. Main Entry Point

The cilium-agent binary starts execution at **`daemon/main.go`**:

```go
func main() {
    agentHive := hive.New(cmd.Agent)
    cmd.Execute(cmd.NewAgentCmd(agentHive))
}
```

### Key Components:

1. **Hive Dependency Injection Framework**: Cilium uses [Hive](https://github.com/cilium/hive), a custom dependency injection framework built on Go concepts. This is critical for understanding component initialization and wiring.

2. **CLI Initialization**: The `cmd.Agent` module defines the agent's dependency injection cells (modules). This is then passed to `hive.New()` to create the dependency graph. Finally, `cmd.NewAgentCmd()` creates a Cobra CLI command that wraps the hive, and `cmd.Execute()` runs it.

3. **Agent Module Structure** (`daemon/cmd/cells.go`):
   - **Agent Cell**: The root module composed of `Infrastructure` and `ControlPlane`
   - **Infrastructure**: External services (K8s client, metrics, API server, data stores)
   - **ControlPlane**: Pure business logic (policy, endpoints, services, networking)

### Initialization Flow:

1. `daemon/main.go` → creates hive with `cmd.Agent`
2. `cmd.Agent` module loads all dependency cells
3. Hive resolves dependencies and starts components via `Invoke()` hooks
4. Policy watchers, endpoint managers, and datapath orchestrators become active

---

## 2. Core Packages

| Package | Responsibility |
|---------|-----------------|
| **pkg/policy** | Policy repository, rule storage, rule evaluation for endpoints |
| **pkg/endpoint** | Endpoint lifecycle (creation, policy regeneration, BPF compilation) |
| **pkg/datapath** | Datapath abstraction layer; Linux eBPF loader and orchestrator |
| **pkg/k8s** | Kubernetes API watchers, resource synchronization, CRD handling |
| **pkg/ipam** | IP address allocation and management for pods |

### Detailed Descriptions:

**pkg/policy/** (`pkg/policy/repository.go`, `pkg/policy/k8s/`)
- Central policy repository storing all network policy rules
- Policy rules are added via `PolicyAdd()` method (called by policy watchers)
- Rules are evaluated against endpoints during policy generation
- Maintains selector cache for fast label matching

**pkg/endpoint/** (`pkg/endpoint/endpoint.go`, `pkg/endpoint/policy.go`, `pkg/endpoint/bpf.go`)
- Represents a single workload/pod running on the node
- Endpoint regeneration: triggered by policy/identity changes
- `regeneratePolicy()` → calculates which peers endpoint can communicate with
- `regenerateBPF()` → compiles and loads eBPF programs for the endpoint
- Lives in several states: `waiting-for-identity` → `waiting-to-regenerate` → `regenerating` → `ready`

**pkg/datapath/** (`pkg/datapath/linux/datapath.go`, `pkg/datapath/loader/`)
- Linux-specific eBPF datapath implementation
- Loader compiles endpoint-specific eBPF programs from templates
- Orchestrator manages device detection, eBPF program loading, and map synchronization
- Creates BPF maps for policy enforcement, connection tracking, NAT

**pkg/k8s/** (`daemon/k8s/`, `pkg/k8s/watchers/`, `pkg/policy/k8s/`)
- Watches Kubernetes resources (Pods, CiliumNetworkPolicy, Services, Endpoints)
- Translates K8s objects into Cilium internal representations
- `policyWatcher` (in `pkg/policy/k8s/`) watches CiliumNetworkPolicy and calls `policyManager.PolicyAdd()`

**pkg/ipam/** (`pkg/ipam/`)
- Allocates IPs for pods from node's pod CIDR
- Supports multiple IPAM modes (Kubernetes, cloud provider, delegated)
- Stores IP allocations in BPF maps for datapath lookup

---

## 3. Configuration Loading

### Configuration Pipeline:

1. **Config Format**: YAML, JSON, and command-line flags
2. **Config Library**: [Viper](https://github.com/spf13/viper) - configuration management library
3. **Main Config Struct**: `option.DaemonConfig` in `pkg/option/config.go`

### Initialization Sequence:

1. **Command-line flags** are registered in `daemon/cmd/daemon_main.go` (see `registerDaemonConfigurationFlags()` function)
2. **Viper instance** is created to bind flags, environment variables, and config files
3. **Hive cell** `cell.Provide(func() *option.DaemonConfig { return option.Config })` provides the config to all components
4. **Dynamic updates**: Runtime config changes are handled via the `/config` API endpoint (see `daemon/cmd/config.go`)

### Key Configuration Modules:

- **Flag Binding**: Uses `option.BindEnv()` to bind viper to individual flags
- **Config Override Merging**: Via `config PatchConfigParams` API handler
- **File Storage**: Config can be persisted to disk via `option.StoreViperInFile()`

### Config Fields of Interest:

- `Opts`: Runtime-changeable options (policy enforcement mode, feature flags)
- `BpfDir`, `LibDir`, `RunDir`: Filesystem paths for BPF, libraries, runtime files
- `DatapathMode`: Direct/tunnel/ipvlan mode
- `PolicyEnforcement`: Always/default/never
- Various feature flags: EnableIPv6, EnableIPv4, EnableBPFMasquerading, etc.

---

## 4. Test Structure

Cilium uses multiple testing approaches:

### 1. **Unit Tests** (`pkg/*/test.go` or `*_test.go`)
- Standard Go testing with `testing.T`
- Example: `pkg/policy/policy_test.go`
- Run with: `go test ./pkg/...`
- Some are marked as privileged (require root/capabilities)

### 2. **Integration Tests** (also `*_test.go` with build tag)
- Marked with `// +build integration` or environment variable `INTEGRATION_TESTS=true`
- Require kvstore (etcd/consul) running
- Run with: `INTEGRATION_TESTS=true make integration-tests`
- Examples: `daemon/cmd/daemon_test.go` (uses DaemonSuite helper)

### 3. **Privileged Tests** (`*_privileged_test.go`)
- Require elevated privileges (CAP_SYS_ADMIN, CAP_NET_ADMIN)
- Skipped by default in `go test`
- Run with: `sudo go test` or via privileged test runner
- Example: `daemon/cmd/daemon_privileged_test.go` (eBPF-related tests)

### 4. **BPF Unit Tests** (`test/bpf/`)
- Test eBPF datapath independently
- Use `BPF_PROG_RUN` mechanism for kernel testing
- Defined in C with special `TEST()` macros
- Run with: `make -C bpf tests`

### 5. **End-to-End (E2E) Tests** (`test/k8s/`, `test/standalone/`)
- Full integration tests in actual Kubernetes clusters
- Use Ginkgo test framework
- Run on KinD, EKS, GKE clusters
- Located in `test/k8s/`, `test/runtime/`, etc.

### Test Organization Structure:

- **`test/k8s/`**: Kubernetes-focused E2E tests (CNP, KNP, connectivity)
- **`test/bpf/`**: eBPF datapath unit tests
- **`test/helpers/`**: Test utilities and client helpers
- **`test/controlplane/`**: Control plane integration tests (no kernel/eBPF required)
- **`daemon/cmd/daemon_test.go`**: Daemon unit tests using DaemonSuite helper

---

## 5. Network Policy Pipeline: CRD to eBPF

### Complete Flow from CiliumNetworkPolicy to eBPF Enforcement:

#### **Stage 1: CRD Definition & K8s Watcher**
- User creates a `CiliumNetworkPolicy` resource in Kubernetes
- Type defined in: `pkg/k8s/apis/cilium.io/v2/cnp_types.go`
- K8s watcher in `pkg/k8s/watchers/watcher.go` observes the resource
- Events routed to `pkg/policy/k8s/policyWatcher` via `ResourceWatch` interface

#### **Stage 2: Policy Parsing & Normalization**
- File: `pkg/policy/k8s/cilium_network_policy.go` → `upsertCiliumNetworkPolicyV2()`
- CNP is parsed: `rules, err := cnp.Parse()` → produces `api.Rules`
- Rules include ingress, egress, deny rules with selectors, L4/L7 specifications
- External references resolved (e.g., CiliumCIDRGroups, ToServices)

#### **Stage 3: Policy Repository Update**
- File: `daemon/cmd/policy.go` → `PolicyAdd()` method
- Rules are added to the policy repository: `pkg/policy/repository.go`
- Repository stores rules, maintains selector cache
- Repository revision is incremented (triggers endpoint regeneration)

#### **Stage 4: Endpoint Regeneration**
- File: `pkg/endpoint/policy.go` → `regeneratePolicy()`
- All endpoints re-evaluate their policies against updated repository
- Policy calculation determines which peers each endpoint can communicate with
- Results stored in `EndpointPolicy` with L3/L4/L7 rules

#### **Stage 5: BPF Program Compilation**
- File: `pkg/endpoint/bpf.go` → `regenerateBPF()`
- Endpoint-specific configuration passed to datapath loader
- Loader: `pkg/datapath/loader/loader.go` → `CompileAndLoad()`
- Template BPF programs from `bpf/` are compiled with endpoint configuration
- eBPF source depends on: policy, identity, NAT configuration, etc.

#### **Stage 6: BPF Map Sync & Enforcement**
- Compiled eBPF programs attached to network interfaces
- BPF maps populated: policy maps, connection tracking, session affinity, NAT maps
- Policy map entry format: `(src_identity, dst_identity) → policy_action`
- Datapath enforces policies at packet ingress/egress on veth interfaces

### Key Components in Flow:

- **CiliumNetworkPolicy CRD**: `pkg/k8s/apis/cilium.io/v2/cnp_types.go` (Spec: `*api.Rule`)
- **Policy Repository**: `pkg/policy/repository.go` (AddPolicy, AddRules, search methods)
- **PolicyManager Interface**: `pkg/policy/k8s/cell.go` (implemented by Daemon)
- **Endpoint Manager**: `pkg/endpointmanager/manager.go` (coordinates regeneration)
- **Datapath Loader**: `pkg/datapath/loader/loader.go` (eBPF compilation and loading)
- **BPF Templates**: `bpf/` directory (C-based eBPF program templates)

### Policy Revision Mechanism:

- Policy repository maintains `revision` (atomic uint64)
- Endpoints track their `policyRevision` (last policy revision applied)
- When policy changes, `BumpRevision()` signals all endpoints to regenerate
- Event queues serialize policy changes and endpoint regenerations

---

## 6. Adding a New Network Policy Type

### Scenario: Adding a New L7 Protocol Filter (e.g., gRPC)

#### **Files to Modify:**

1. **API Definition** (`pkg/policy/api/l7.go` or new file `pkg/policy/api/grpc.go`)
   - Define `PortRuleGRPC` struct with gRPC-specific match fields
   - Example fields: `Service`, `Method`, `Metadata` patterns
   - Implement `Exists()` method for deduplication

2. **L7Rules Union** (`pkg/policy/api/l7.go`)
   - Add `GRPC []PortRuleGRPC` field to `L7Rules` struct
   - Update `IsEmpty()` to check gRPC rules
   - Update rule counting logic

3. **CiliumNetworkPolicy CRD** (`pkg/k8s/apis/cilium.io/v2/cnp_types.go`)
   - Already supports `api.Rule` spec; no change needed if using L7Rules
   - If adding cluster-wide policy, also update CCNP type

4. **Rule Parsing & Validation** (`pkg/policy/api/rule_validation.go`)
   - Add validation for gRPC rule syntax in `PortRule.sanitize()`
   - Ensure gRPC rules only apply to TCP ports

5. **Policy Evaluation** (`pkg/policy/rule.go`)
   - Add gRPC rule handling in `createL4IngressFilter()` and `createL4EgressFilter()`
   - Merge conflicting gRPC rules appropriately

6. **Envoy Configuration** (`pkg/envoy/xds_server.go`)
   - If gRPC rules require Envoy redirection:
   - Implement `GetEnvoyGRPCRules()` function
   - Convert gRPC rules to Envoy protobuf format (`cilium.GRPCNetworkPolicyRules`)
   - Register in L4PolicyMap for proxy redirect

7. **Policy L4 Layer** (`pkg/policy/l4.go`)
   - Add gRPC to `ParserType` constants: `ParserTypeGRPC L7ParserType = "grpc"`
   - Handle gRPC in L4 policy filter creation logic

8. **eBPF Datapath** (`bpf/lib/l4.h`, `bpf/lib/lb.h`)
   - If packet-level gRPC filtering needed (unlikely), update eBPF programs
   - Most L7 filtering done in userspace proxy (Envoy)

9. **Tests** (create `pkg/policy/api/grpc_test.go`, `pkg/policy/grpc_policy_test.go`)
   - Test gRPC rule parsing and validation
   - Test gRPC rule merging and conflict resolution
   - Test policy evaluation with gRPC rules
   - Add integration test in `daemon/cmd/policy_test.go`

#### **Sequence of Changes:**

1. **Phase 1**: Define structures (files 1-2)
2. **Phase 2**: Add validation and parsing (files 4-5)
3. **Phase 3**: Integrate into policy evaluation (file 5)
4. **Phase 4**: Add Envoy support if L7 enforcement needed (file 6)
5. **Phase 5**: Update parsers/constants (file 7)
6. **Phase 6**: Update eBPF if necessary (file 8)
7. **Phase 7**: Write comprehensive tests (file 9)
8. **Phase 8**: Update CRD schema documentation and OpenAPI spec

#### **Example: HTTP Rule Reference**

For reference, existing HTTP rules are defined in:
- **Type**: `pkg/policy/api/http.go` → `PortRuleHTTP` struct
- **L7Rules**: `pkg/policy/api/l7.go` → `L7Rules.HTTP []PortRuleHTTP`
- **Envoy Integration**: `pkg/envoy/xds_server.go` → `GetEnvoyHTTPRules()`
- **Parser Constant**: `pkg/policy/l4.go` → `ParserTypeHTTP`

#### **Testing Strategy:**

1. Unit tests for rule validation and parsing
2. Integration tests for policy repository acceptance
3. End-to-end tests with actual gRPC traffic in K8s cluster
4. Verify eBPF compilation succeeds (if needed)
5. Performance tests for large numbers of gRPC rules

#### **Documentation Updates:**

- Update `Documentation/security/policy/language.rst` with gRPC rule syntax
- Add example YAML CiliumNetworkPolicy with gRPC rules
- Update API reference documentation

---

## Summary

The Cilium architecture separates concerns into discrete layers:
- **K8s Watcher Layer**: Observes policy resources
- **Policy Repository Layer**: Stores and evaluates rules
- **Endpoint Management Layer**: Tracks workloads and triggers regeneration
- **eBPF Datapath Layer**: Compiles and enforces policies at packet level

Understanding this layering is key to extending Cilium with new functionality. Adding features typically involves modifying multiple layers in sequence, ensuring consistency at each level. The Hive dependency injection framework ties these layers together, allowing clean interfaces and testability.
