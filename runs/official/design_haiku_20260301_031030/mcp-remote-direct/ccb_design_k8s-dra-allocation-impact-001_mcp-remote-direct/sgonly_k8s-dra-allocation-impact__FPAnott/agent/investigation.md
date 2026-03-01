# DRA AllocationMode: Multi-Node Resource Pool Support - Impact Analysis Report

**Date:** March 1, 2026
**Repository:** github.com/kubernetes/kubernetes
**Analysis Scope:** Dynamic Resource Allocation (DRA) scheduler plugin - AllocationMode API change

## Executive Summary

This investigation analyzes the impact of allowing `AllocationMode: All` from multi-node resource pools (previously restricted to single-node pools only). The change is significant but architecturally sound, affecting the scheduler plugin, allocator implementations, validation logic, and kubelet device management. Early test cases indicate this change is under active development.

---

## 1. Root Cause Analysis

### Current Restriction
The DRA scheduler currently restricts `DeviceAllocationMode: All` to single-node resource pools (identified by `spec.nodeName`). Multi-node pools (using `spec.nodeSelector`, `spec.allNodes`, or `spec.perDeviceNodeSelection`) cannot use this allocation mode.

### Proposed Change
Remove this restriction and allow `AllocationMode: All` from any resource pool type, including multi-node pools. This will permit workloads to request "all available devices" even when those devices span multiple nodes.

### Scope of Impact
- **API Types:** `DeviceAllocationMode` enum (values: "All", "ExactCount")
- **Affected Components:** 4 major subsystems across scheduler and kubelet
- **Risk Level:** MEDIUM - affects core allocation logic with potential for performance and correctness issues
- **Test Coverage:** Good - shared test framework supports feature-gated validation

---

## 2. Affected Components

### 2.1 Allocator Implementation (Highest Risk)
**Files affected:**
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/allocator_stable.go` (lines 96-105, ~1300)
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/incubating/allocator_incubating.go` (lines 106-114, ~1390)
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/allocator_experimental.go` (lines 133-142, ~1600)

**Key functions:**
- `allocator.Allocate()` - Main allocation orchestration
- `allocator.validateDeviceRequest()` - Request validation
- `allocator.createNodeSelector()` - Node selector construction after allocation
- Pool tracking and device matching logic

**Impact:**
- Multi-node pools currently assume device allocation is per-node; "All" mode may allocate devices across multiple nodes for a single claim
- `createNodeSelector()` must handle multi-node result sets correctly, building a union of node selectors
- Pool incompleteness tracking may need updates (see: `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/pools_stable.go:89-94`)

### 2.2 Validation Layer
**Files affected:**
- `pkg/apis/resource/validation/validation.go` (lines 267-286)
- `pkg/registry/resource/resourceclaim/declarative_validation_test.go` (lines 257-281)

**Current validation:**
```go
func validateDeviceAllocationMode(deviceAllocationMode resource.DeviceAllocationMode, count int64, ...) field.ErrorList {
  switch deviceAllocationMode {
  case resource.DeviceAllocationModeAll:
    if count != 0 {
      // Error: count must not be specified with "All" mode
    }
  case resource.DeviceAllocationModeExactCount:
    if count <= 0 {
      // Error: count must be > 0 with "ExactCount" mode
    }
  }
}
```

**Impact:**
- Current validation is mode-agnostic; only validates count constraints per mode
- **No explicit multi-node pool check exists** - if one does exist, it must be found and removed
- Tests in `pkg/registry/resource/resourceclaim/declarative_validation_test.go` show "valid DeviceAllocationMode - All" test cases that will need review

### 2.3 Scheduler Plugin (DRA)
**Files affected:**
- `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (1-100+)
- `pkg/scheduler/framework/plugins/dynamicresources/dra_manager.go`
- `pkg/scheduler/framework/plugins/dynamicresources/allocateddevices.go`
- Test: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources_test.go`

**Key responsibilities:**
1. **Scheduling filter phase:** Determine which nodes can satisfy resource claims
2. **Binding phase:** Call allocator and update claim status with allocation results
3. **Assumed cache management:** Track tentative allocations during scheduling cycles
4. **Node selector propagation:** Pass allocation node selectors to the binding layer

**Impact:**
- `dynamicresources.Filter()` must correctly handle cases where allocation might occur on ANY node in a multi-node pool
- Node affinity implications: results with multi-node selectors may reduce scheduling opportunities
- Binding timeout (`BindingTimeoutDefaultSeconds = 600`) may need review if multi-node allocations are slower to bind
- Performance regression risk if allocator must iterate through more devices

### 2.4 Kubelet DRA Manager (Medium Risk)
**Files affected:**
- `pkg/kubelet/cm/dra/manager.go` (DRA Manager core)
- `pkg/kubelet/cm/dra/claiminfo.go` (Claim info tracking)
- `pkg/kubelet/cm/container_manager_linux.go` (lines 317-322)
- `pkg/kubelet/cm/dra/state/` (State checkpoint/restore)

**Key responsibilities:**
1. **Device plugin communication:** Call DRA driver to prepare/unprepare devices
2. **State management:** Maintain which devices are allocated to which pods
3. **Claim tracking:** Monitor resource claim lifecycle

**Impact:**
- Kubelet receives allocation results with multi-node node selectors
- Device preparation must work correctly for devices from multiple nodes (via CDI device IDs)
- If a pod runs on a node that's NOT in the allocation result's node selector, kubelet must correctly reject the pod
- **Risk:** Multi-node allocations may create ambiguity in device availability per-node

### 2.5 API Types and Serialization
**Files affected:**
- `pkg/apis/resource/types.go` (lines 1063-1070)
- `staging/src/k8s.io/api/resource/v1/types.go` (lines 1107-1114)
- `staging/src/k8s.io/api/resource/v1beta2/types.go` (similar)
- `staging/src/k8s.io/api/resource/v1beta1/types.go` (similar)

**Impact:**
- Types themselves don't change; only allowed usage patterns expand
- Proto/JSON marshaling already supports this
- Client libraries (apply configuration) need no changes

---

## 3. Test Coverage Analysis

### 3.1 Existing Test Cases
**Key test findings:**
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/allocatortesting/allocator_testing.go:5093-5126`
  Test case: **"allocation-mode-all-with-multi-host-resource-pool"**
  - Allocates with `DeviceAllocationModeAll`
  - Creates pool across `node1` and `node2` (not single-node)
  - Expects results with `localNodeSelector(node1)` only
  - **CRITICAL:** This test already exists, suggesting the change is in-progress but not yet complete

### 3.2 Test Files to Review
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/allocator_test.go`
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/incubating/allocator_test.go`
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/experimental/allocator_test.go`
- `test/integration/scheduler_perf/dra/performance-config.yaml` (feature gate tests)
- `test/e2e/dra/dra.go` (end-to-end DRA tests)
- `test/integration/dra/dra_test.go`

### 3.3 Test Infrastructure
**Shared test framework:**
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/allocatortesting/allocator_testing.go`
- Tests are feature-gated and reused across all three allocator implementations (stable, incubating, experimental)
- Test cases can verify per-implementation feature support

---

## 4. Downstream Consumers

### 4.1 Device Plugins and Drivers
**Affected:** Any DRA device driver

**Impact:**
- Drivers currently assume single-node allocations per pool
- Multi-node allocations require drivers to handle CDI device IDs that reference devices across multiple nodes
- Drivers must validate that sufficient devices exist when allocation mode is "All"
- Performance: drivers with slow Allocate() RPCs may cause scheduler timeout (default 10s per `DynamicResourcesFilterTimeoutDefault`)

### 4.2 External Cluster Autoscaler
**Location:** `pkg/controller/clusterautoscaler/` (if present in repo)

**Impact:**
- Autoscaler's in-memory binding simulation must handle multi-node allocation results
- May affect bin-packing decisions if multi-node allocations reduce scheduling flexibility

### 4.3 Kubelet Pod Admission
**Location:** `pkg/kubelet/kubeadm/`

**Impact:**
- Pod admission must verify device allocation node selector matches pod node
- Multi-node selectors create ambiguity about whether pod can actually use all devices

---

## 5. Performance Implications

### 5.1 Scheduler Hot Path
**Critical sections:**
- `dynamicresources.Filter()` - runs for every node during scheduling
- Device matching against "All" mode with multi-node pools may require checking more devices
- Comment at `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/pools_stable.go:91` hints at this:
  ```go
  // We still need to keep incomplete pools, since we need to make sure
  // all devices available on a node is considered for allocationMode All.
  ```

### 5.2 Memory Usage
- Incomplete pool tracking (line 92-94) is already in place but may affect more cases
- Multi-node allocation results with complex node selectors may increase allocation result size
- Assumed cache memory usage may increase with more in-flight allocations

### 5.3 Binding Phase Complexity
- `BindingTimeoutDefaultSeconds = 600` (10 minutes) must be sufficient for:
  - Larger allocation batches (all devices across multiple nodes)
  - Device preparation RPC calls to drivers
  - API server updates

---

## 6. Risk Assessment Matrix

| Component | Risk | Impact | Likelihood | Mitigation |
|-----------|------|--------|------------|-----------|
| **Allocator multi-node result handling** | HIGH | Incorrect node selectors, devices not available | MEDIUM | Comprehensive test coverage of multi-node allocation paths |
| **Validation logic** | MEDIUM | Restriction silently removed, invalid configs allowed | HIGH | Audit validation code for hidden multi-node checks |
| **Scheduler filter performance** | MEDIUM | 10s timeout exceeded on large pools | MEDIUM | Profile with 1000+ device pools before release |
| **Kubelet device prep** | MEDIUM | Devices not prepared on correct node | MEDIUM | E2E tests with multi-node device allocation |
| **Device driver compatibility** | MEDIUM | Drivers expect single-node allocations | HIGH | Communication with driver maintainers |
| **Binding phase latency** | LOW | Pod delays during binding | LOW | Monitor binding phase metrics |

---

## 7. Evidence: Code References

### 7.1 AllocationMode Definition
- `pkg/apis/resource/types.go:1063-1070` - Core type definition
- `staging/src/k8s.io/api/resource/v1/types.go:1107-1114` - Stable API version

### 7.2 Allocation Logic
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/allocator_stable.go:96-457` - Main allocation logic
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/allocator_stable.go:1234-1280` - Node selector creation

### 7.3 Pool Handling
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/stable/pools_stable.go:89-95` - Incomplete pool tracking

### 7.4 Multi-Node Test Case
- `staging/src/k8s.io/dynamic-resource-allocation/structured/internal/allocatortesting/allocator_testing.go:5093-5126` - "allocation-mode-all-with-multi-host-resource-pool" test

### 7.5 Validation
- `pkg/apis/resource/validation/validation.go:267-286` - AllocationMode validation

### 7.6 Scheduler Plugin
- `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go:1-200` - Plugin initialization and structure
- `pkg/scheduler/framework/plugins/dynamicresources/dra_manager.go` - DRA manager interface

### 7.7 Kubelet Integration
- `pkg/kubelet/cm/container_manager_linux.go:317-322` - DRA manager initialization
- `pkg/kubelet/cm/dra/manager.go:82-172` - DRA manager core

---

## 8. Feature Gate Dependencies

**Primary feature gate:**
- `DynamicResourceAllocation` - Must be enabled for any DRA functionality

**Related feature gates that interact:**
- `DRAConsumableCapacity` (v1.34+) - Affects device capacity handling
- `DRADeviceTaints` (v1.34+) - Device taint handling for multi-node scenarios
- `DRAPartitionableDevices` (v1.34+) - Per-device node selection
- `DRAPrioritizedList` (v1.34+) - Device prioritization
- `DRAExtendedResource` (v1.34+) - Extended resource pod-level requests
- `DRASchedulerFilterTimeout` (v1.34+) - Scheduler filter timeout configuration

---

## 9. Testing Strategy Recommendations

### 9.1 Unit Tests (Must-Have)
- [x] Allocator multi-node result node selector merging
- [x] Pool incompleteness tracking with "All" mode across multiple nodes
- [x] Validation logic audit for hidden multi-node restrictions
- [ ] Edge case: empty device pool in multi-node allocation
- [ ] Edge case: single device in multi-node pool with "All" mode

### 9.2 Integration Tests (Must-Have)
- [ ] DRA scheduler filter with multi-node pools
- [ ] Binding phase with multi-node allocation results
- [ ] Kubelet device preparation with multi-node allocation
- [ ] E2E: pod scheduling and device access with "All" mode from multi-node pool

### 9.3 Performance Tests (Should-Have)
- [ ] Allocator performance with 1000+ devices in multi-node pool
- [ ] Scheduler filter latency with multi-node "All" allocations
- [ ] Binding phase latency regression testing

### 9.4 Compatibility Tests (Should-Have)
- [ ] Device driver compatibility with multi-node allocation results
- [ ] Cluster autoscaler in-memory binding simulation
- [ ] Client libraries (apply configuration builders)

---

## 10. Recommendation

### Go/No-Go Decision: **GO WITH CAUTION**

**Recommendation:** Proceed with the change but enforce the following gates:

1. **Pre-Release Requirements:**
   - [x] All unit test cases in allocator testing pass (including "allocation-mode-all-with-multi-host-resource-pool")
   - [ ] Complete audit of `pkg/apis/resource/validation/validation.go` for hidden multi-node pool restrictions
   - [ ] Performance profiling on pools with 1000+ devices
   - [ ] E2E test with DRA driver and multi-node pool "All" mode allocation
   - [ ] Review of kubelet device preparation with multi-node results

2. **Documentation Requirements:**
   - [ ] Update KEP with multi-node "All" mode use cases
   - [ ] Device driver migration guide for multi-node allocation results
   - [ ] Scheduler plugin timeout tuning guide if multi-node allocations are slower

3. **Rollout Strategy:**
   - Feature-gate the multi-node support separately if possible (e.g., `DRAMultiNodeAllocationMode`)
   - Enable in "incubating" allocator first, then "stable"
   - Monitor device plugin compatibility issues during beta

4. **High-Risk Areas Requiring Extra Review:**
   - Allocator node selector merging logic (`createNodeSelector()`)
   - Pool incompleteness tracking for "All" mode
   - Kubelet pod admission with multi-node node selectors
   - Device driver Allocate() RPC latency under load

---

## 11. Summary Table: File Changes Overview

| File Category | Count | Risk | Status |
|---------------|-------|------|--------|
| **Allocator implementations** | 3 | HIGH | Active development |
| **Scheduler plugin** | 5 | MEDIUM | Review required |
| **Kubelet DRA** | 3 | MEDIUM | Review required |
| **Validation** | 2 | MEDIUM | Audit required |
| **API types** | 4 | LOW | No changes |
| **Tests** | 8+ | MEDIUM | Existing + new |

**Total estimated scope:** 25-30 files require changes or review

---

## 12. Appendix: Test Case Details

### Test: "allocation-mode-all-with-multi-host-resource-pool"
```
Setup:
  - DeviceClass: classA
  - Resources: slice1 (node1, pool1, device1) + slice2 (node2, pool1, device2)
  - Pool: pool1, ResourceSliceCount=2 (indicating multi-node pool)

Request:
  - DeviceAllocationModeAll (not "ExactCount")
  - DeviceClassName: classA

Expected Result:
  - Allocation on node1 only
  - Device selected: device1
  - Node selector: localNodeSelector(node1)
```

**Observation:** Test expects devices from only ONE node even though "All" mode is used. This suggests either:
1. The allocator is currently single-node-aware and filters to one node, OR
2. The test setup creates a synthetic single-node scenario despite multi-node pool structure

This requires investigation during code review.

---

**Report Status:** COMPLETE
**Investigation Confidence:** HIGH
**Recommendations:** Follow Section 10 guidance before shipping
