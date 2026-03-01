# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update in Istio

## Summary

When multiple DestinationRules target the same host without workload selectors, Istio's merge pipeline collapses them into a single consolidated rule that retains metadata from only one of the contributors. Subsequent updates to non-retained DRs are filtered out by the xDS push mechanism because the proxy's SidecarScope only tracks dependencies for the DR whose metadata survived the merge. This causes Envoy sidecars to silently fail to receive configuration updates.

---

## Root Cause

The root cause spans four layers of the Istio codebase:

### 1. **DestinationRule Merging** (`pilot/pkg/model/destination_rule.go:38-109`)

The `mergeDestinationRule()` function implements a **lossy merge** of multiple DestinationRules into a consolidated structure:

- **Scenario**: Two DestinationRules (DR-1 and DR-2) target the same host (e.g., `reviews.default.svc.cluster.local`) and both have no workload selector
- **First DR processed** (DR-1: traffic policy):
  - Line 41: Check if `destRules[resolvedHost]` exists → No
  - Line 107: Append DR-1 to the consolidated rules list
  - Result: `destRules[reviews.default.svc.cluster.local] = [DR-1_config]`

- **Second DR processed** (DR-2: subsets):
  - Line 41: Check if `destRules[resolvedHost]` exists → Yes (contains DR-1)
  - Line 46: Both DRs have no workload selector → `bothWithoutSelector = true`
  - Line 59: Match condition satisfied → `addRuleToProcessedDestRules = false`
  - Line 65: Deep copy the existing DR-1
  - Lines 77-87: Merge DR-2's subsets into the copied DR-1
  - Line 66: Store the modified copy back: `destRules[resolvedHost][0] = &copied` (replaces DR-1)
  - Line 101-103: Since `addRuleToProcessedDestRules = false`, DR-2 is **not appended**
  - Result: `destRules[reviews.default.svc.cluster.local] = [merged_DR_with_DR1_metadata_and_DR2_subsets]`

**Critical Loss**: The merged DR contains subsets from DR-2 but retains the `config.Config` metadata (Name="reviews-traffic-policy", Namespace="default") from DR-1. DR-2's identity is completely lost.

---

### 2. **SidecarScope Dependency Registration** (`pilot/pkg/model/sidecar.go:209-227`)

When a SidecarScope is constructed, it registers config dependencies for all destination rules it needs to track:

```go
// Lines 219-227 in DefaultSidecarScopeForNamespace
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,              // <-- Problem: Only one DR's name survives
            Namespace: dr.Namespace,          // <-- Problem: Only one DR's namespace survives
        })
    }
}
```

- **What happens**: For the reviews service, `out.destinationRules[reviews.default.svc.cluster.local]` contains only the merged DR
- **What's registered**: `ConfigKey{Kind: DestinationRule, Name: "reviews-traffic-policy", Namespace: "default"}`
- **What's missing**: `ConfigKey{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}`

The dependency tracker thus has a **blind spot**: it doesn't know the proxy depends on the "reviews-subsets" DR because its metadata was discarded during merging.

---

### 3. **xDS Push Filtering** (`pilot/pkg/xds/proxy_dependencies.go:60-74`)

When a configuration change occurs, the xDS layer decides whether to push to each proxy:

```go
// Lines 60-74 in checkProxyDependencies
func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
    switch proxy.Type {
    case model.SidecarProxy:
        if proxy.SidecarScope.DependsOnConfig(config) {  // <-- DependsOnConfig lookup
            return true
        } else if proxy.PrevSidecarScope != nil && proxy.PrevSidecarScope.DependsOnConfig(config) {
            return true
        }
    default:
        return true
    }
    return false
}
```

**The filter mechanism** (`SidecarScope.DependsOnConfig()` in `sidecar.go:523-540`):

```go
func (sc *SidecarScope) DependsOnConfig(config ConfigKey) bool {
    if sc == nil {
        return true
    }
    if _, f := clusterScopedConfigTypes[config.Kind]; f {
        return config.Namespace == sc.RootNamespace || config.Namespace == sc.Namespace
    }
    if _, f := sidecarScopeKnownConfigTypes[config.Kind]; !f {
        return true
    }
    _, exists := sc.configDependencies[config.HashCode()]  // <-- Hash lookup
    return exists
}
```

- **When DR-1 is updated**: ConfigKey hash matches → `exists = true` → Push proceeds ✓
- **When DR-2 is updated**: ConfigKey hash doesn't match (DR-2's name/namespace never registered) → `exists = false` → **Push is skipped** ✗

---

### 4. **PushContext DestinationRule Retrieval** (`pilot/pkg/model/push_context.go:989-1050`)

The `destinationRule()` method in PushContext retrieves the consolidated rules from the `destinationRuleIndex`:

```go
// Lines 1006-1010 in destinationRule
if ps.destinationRuleIndex.namespaceLocal[proxyNameSpace] != nil {
    if hostname, ok := MostSpecificHostMatch(service.Hostname,
        ps.destinationRuleIndex.namespaceLocal[proxyNameSpace].destRules,
    ); ok {
        return ps.destinationRuleIndex.namespaceLocal[proxyNameSpace].destRules[hostname]
    }
}
```

This returns the merged DR from the `consolidatedDestRules.destRules` map, obscuring the fact that multiple original DRs contributed to it. The loss of metadata happens here—only the consolidated DR's metadata is visible to dependency tracking.

---

## Evidence

### File References

| Component | File | Function | Lines |
|-----------|------|----------|-------|
| Merging | `pilot/pkg/model/destination_rule.go` | `mergeDestinationRule()` | 38–109 |
| Dependency Registration | `pilot/pkg/model/sidecar.go` | `DefaultSidecarScopeForNamespace()` | 172–251 |
| Dependency Registration | `pilot/pkg/model/sidecar.go` | `AddConfigDependencies()` | 544–555 |
| Dependency Checking | `pilot/pkg/model/sidecar.go` | `DependsOnConfig()` | 523–540 |
| Push Filtering | `pilot/pkg/xds/proxy_dependencies.go` | `checkProxyDependencies()` | 60–74 |
| Push Filtering | `pilot/pkg/xds/proxy_dependencies.go` | `ConfigAffectsProxy()` | 32–58 |
| Consolidation | `pilot/pkg/model/push_context.go` | `SetDestinationRules()` | 1672–1760 |
| Retrieval | `pilot/pkg/model/push_context.go` | `destinationRule()` | 989–1050 |

### Key Code Sections

**Merge loses second DR's metadata** (`destination_rule.go:59-66`):
```go
if bothWithoutSelector || (rule.GetWorkloadSelector() != nil && selectorsMatch) {
    addRuleToProcessedDestRules = false  // Second DR will NOT be added separately
}
// ...
copied := mdr.DeepCopy()
p.destRules[resolvedHost][i] = &copied  // Replaced with merged copy using first DR's metadata
```

**Dependency tracking only records merged DR** (`sidecar.go:219-227`):
```go
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,        // Only merged DR's name recorded
            Namespace: dr.Namespace,   // Only merged DR's namespace recorded
        })
    }
}
```

**Push skipped for non-retained DR** (`proxy_dependencies.go:64`):
```go
if proxy.SidecarScope.DependsOnConfig(config) {  // Returns false for "reviews-subsets"
    return true
}
```

---

## Affected Components

1. **`pilot/pkg/model/destination_rule.go`**
   - Merging logic loses metadata of non-retained DRs
   - No tracking of which original DRs contributed to a merged DR

2. **`pilot/pkg/model/sidecar.go`**
   - Dependency registration only sees the consolidated DR, not original contributors
   - `AddConfigDependencies()` cannot register dependencies for lost metadata

3. **`pilot/pkg/xds/proxy_dependencies.go`**
   - Push filtering correctly checks registered dependencies
   - But registration is incomplete due to upstream merging

4. **`pilot/pkg/model/push_context.go`**
   - The `consolidatedDestRules` structure and `destinationRule()` retrieval mechanism obscures the contribution of multiple original DRs
   - No mechanism to track the lineage of merged DRs back to their original sources

5. **`pilot/pkg/networking/core/v1alpha3/cluster.go` and `route.go`** (indirectly)
   - These consumers of the DestinationRule receive the merged version
   - They have no way to know that changes to the contributing DRs might be relevant

---

## Causal Chain

1. **Trigger**: Operator creates two DestinationRules with the same host but different content (one with traffic policy, one with subsets)

2. **Merging**: During `SetDestinationRules()` (line 1672), `mergeDestinationRule()` is called for each DR
   - First DR added normally
   - Second DR's content merged into the first, but second DR's identity is **discarded**

3. **Consolidation**: `consolidatedDestRules.destRules[host]` now contains only **one** `config.Config` with metadata from the first DR

4. **Dependency Gap**: When `DefaultSidecarScopeForNamespace()` registers dependencies (line 219), it only knows about the **one** surviving DR's metadata

5. **Update Event**: Operator updates the second DR (e.g., adds a v3 subset)
   - Kubernetes API server updated successfully
   - Istio's config watchers fire an update event for `{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}`

6. **Push Decision**: xDS layer calls `ConfigAffectsProxy()` (line 32 in `proxy_dependencies.go`)
   - For each proxy with a SidecarScope, it calls `checkProxyDependencies(proxy, configKey)`
   - Line 64: `DependsOnConfig()` is called for `{Name: "reviews-subsets"}`
   - Hash of "reviews-subsets" is NOT in `configDependencies` (only "reviews-traffic-policy" is)
   - Returns `false` → **Push is skipped**

7. **Stale Config**: Envoy sidecar receives no update event
   - `/debug/config_dump` shows the old merged configuration
   - Only a pod restart (which rebuilds everything) picks up the change

---

## Recommendation

### Fix Strategy

**Option A: Preserve all original DR metadata in consolidation** (Preferred)
- Modify the `consolidatedDestRules` structure to track all contributing DRs, not just the merged result
- Example: Add a `sourceConfigs []config.Config` field to track which original DRs were merged
- When registering dependencies in `DefaultSidecarScopeForNamespace()`, register **all** contributing DRs, not just the merged one
- Impact: Medium complexity, fixes the root cause cleanly

**Option B: Rebuild dependency on DR metadata changes**
- Detect when a DR's metadata has changed (name/namespace)
- Trigger a full SidecarScope rebuild for affected proxies
- Impact: High overhead, works around the issue

**Option C: Track DR lineage through unique identifiers**
- Instead of discarding a DR when merged, maintain a mapping from the consolidated DR back to all original DRs
- Register all original DRs' identifiers in the dependency tracker
- Impact: Medium complexity, maintains backward compatibility

### Diagnostic Steps

To verify this issue in a cluster:

1. **Inspect consolidated DRs**:
   ```bash
   kubectl exec -it <pilot-pod> -n istio-system -- \
     curl localhost:9876/debug/config_dump | jq '.configs[] | select(.Kind=="DestinationRule")'
   ```
   - Look for a single merged DR where two original DRs were expected

2. **Check sidecar dependencies** (requires adding debug output):
   - Add logging in `DefaultSidecarScopeForNamespace()` to print registered ConfigKeys
   - Verify that only one DR's metadata is registered when two should be

3. **Monitor xDS push decisions**:
   - Add logging in `checkProxyDependencies()` to trace which DRs are checked
   - Confirm that the second DR's update returns `false` for `DependsOnConfig()`

4. **Replay scenario**:
   - Create two DRs for the same host
   - Update only the second one
   - Observe that `/debug/config_dump` on the sidecar doesn't reflect the change
   - Restart the pod and confirm the change is now present

---

## Impact Assessment

- **Severity**: High—silently loses configuration updates
- **Affected Scenarios**: Multi-DestinationRule deployments where DRs have complementary content (e.g., one defines traffic policy, another defines subsets)
- **User Workaround**: Restart affected pods or consolidate all DestinationRules into a single resource per host
- **Scope**: Affects all proxies whose SidecarScope depends on merged DestinationRules
