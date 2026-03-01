# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update in Istio

## Summary
When multiple DestinationRules exist for the same host in Istio, updating one of them fails to trigger an xDS push to Envoy sidecars. This occurs because the merging process loses the identity metadata of contributing DestinationRules, causing the dependency tracking system to miss configuration changes on those DRs.

## Root Cause
The root cause spans four interconnected layers:

1. **DestinationRule Merging (destination_rule.go)**: Multiple DRs targeting the same FQDN host are merged into a single config that combines their subsets and traffic policies, but **only one DR's metadata (Name/Namespace) is retained** in the merged config.

2. **Dependency Tracking Loss (sidecar.go)**: When SidecarScope builds its config dependencies, it only registers the metadata from the merged config's Name/Namespace fields, completely losing track of the other contributing DRs.

3. **Push Filtering (proxy_dependencies.go)**: When a config update occurs, the xDS layer checks if a proxy depends on that config using `DependsOnConfig()`, which fails if the updated DR's metadata was lost during merging.

4. **Metadata Obscuration (push_context.go)**: The `destinationRule()` method returns the merged config from the index, making it impossible for downstream code to know which DRs contributed to it.

## Evidence

### 1. Merging Process Loses Metadata
**File: `pilot/pkg/model/destination_rule.go:38-109`**

The `mergeDestinationRule()` function merges multiple DRs for the same host:
- Lines 41-104: When a DR for the same host already exists, it enters the merge logic
- Line 65-66: Deep copies the first DR and stores it back at index i
- Lines 77-87: Appends subsets from the incoming DR to the copied first DR
- **Critical**: The deep copied first DR retains **its original metadata (Name/Namespace)**, not the incoming DR's metadata
- Line 59-61: When both DRs have no workload selector, `addRuleToProcessedDestRules = false`
- **Result**: The second DR is NOT appended as a separate entry; it's merged into the first DR, losing its identity

### 2. Dependency Registration Only Captures One DR's Metadata
**File: `pilot/pkg/model/sidecar.go:219-227` and `410-416`**

When building SidecarScope, the code iterates through destination rules:

```go
// Lines 219-227 in DefaultSidecarScopeForNamespace
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,           // ← Uses ONLY merged config's metadata
            Namespace: dr.Namespace,      // ← Other DRs' metadata is lost
        })
    }
}
```

The same pattern appears in `ConvertToSidecarScope()` at lines 410-416.

For the scenario with two DRs (reviews-traffic-policy and reviews-subsets):
- If reviews-traffic-policy is created first, it gets merged into
- When reviews-subsets arrives, it's merged into the first DR
- **Only** `ConfigKey{Name: "reviews-traffic-policy", Namespace: "default"}` is registered
- **Never** `ConfigKey{Name: "reviews-subsets", Namespace: "default"}`

### 3. Push Filtering Fails to Match Merged DRs
**File: `pilot/pkg/xds/proxy_dependencies.go:32-74`**

When a config update event occurs:

```go
// Line 52: Calls checkProxyDependencies for each updated config
if affected && checkProxyDependencies(proxy, config) {
    return true
}

// Lines 60-68: checkProxyDependencies
func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
    switch proxy.Type {
    case model.SidecarProxy:
        if proxy.SidecarScope.DependsOnConfig(config) {  // ← Checks dependency
            return true
        }
    }
    return false
}
```

If `config` is `{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}`, but only `"reviews-traffic-policy"` is registered in `configDependencies`, this returns **false** and the push is skipped.

### 4. DependsOnConfig Uses Hash-Based Lookup
**File: `pilot/pkg/model/sidecar.go:521-540` and `pilot/pkg/model/config.go:60-74`**

The `DependsOnConfig()` method checks if a config is in the dependency map:

```go
// pilot/pkg/model/sidecar.go:538
_, exists := sc.configDependencies[config.HashCode()]
return exists

// pilot/pkg/model/config.go:60-74
func (key ConfigKey) HashCode() uint64 {
    hash := md5.New()
    for _, v := range []string{
        key.Name,        // ← Hash includes Name
        key.Namespace,   // ← Hash includes Namespace
        key.Kind.Kind,
        key.Kind.Group,
        key.Kind.Version,
    } {
        hash.Write([]byte(v))
    }
    ...
}
```

Since the hash is computed from Name and Namespace, an updated DR with a different Name than what was registered will have a different hash and won't be found.

### 5. PushContext.destinationRule() Obscures Merged Origins
**File: `pilot/pkg/model/push_context.go:989-1066`**

The `destinationRule()` method returns configs from the `destinationRuleIndex`, which was populated by `SetDestinationRules()` that called `mergeDestinationRule()`:

- Lines 1006-1010: Returns `ps.destinationRuleIndex.namespaceLocal[...].destRules[hostname]`
- This returns the **merged config(s)**, with only the first DR's metadata

Callers cannot determine that multiple DRs contributed to the merged result.

## Affected Components

1. **pilot/pkg/model/destination_rule.go**: Implements the merging logic that loses metadata
2. **pilot/pkg/model/push_context.go**: Builds the destinationRuleIndex and provides `destinationRule()` lookup
3. **pilot/pkg/model/sidecar.go**: Builds SidecarScope and registers config dependencies
4. **pilot/pkg/xds/proxy_dependencies.go**: Filters xDS pushes based on dependency checking

## Causal Chain

1. **Symptom**: Updating a DestinationRule (e.g., reviews-subsets) produces no xDS update to proxies
2. **→ Push filtering skips the proxy**: `ConfigAffectsProxy()` returns false for the updated DR
3. **→ Dependency lookup fails**: `checkProxyDependencies()` calls `DependsOnConfig()` which returns false
4. **→ Updated DR not in dependency map**: Only the first DR's metadata was registered in `configDependencies`
5. **→ Merged config loses second DR's metadata**: During `mergeDestinationRule()`, the second DR is merged into the first without appending as a separate entry
6. **→ Only first DR's metadata retained**: The deep-copied merged config at lines 65-66 keeps only the first DR's Name/Namespace
7. **→ Root cause**: When both DRs lack workload selectors, `addRuleToProcessedDestRules` is set to false (line 59-61), preventing the second DR from being tracked as a separate entity

## Affected Code Flow

```
SetDestinationRules() [push_context.go:1672]
    ↓
mergeDestinationRule() [destination_rule.go:38]
    ↓ (for 2nd DR with same host, no workload selector)
    ↓ bothWithoutSelector=true → addRuleToProcessedDestRules=false
    ↓ Merges subsets into first DR, keeps first DR's metadata
    ↓ Returns WITHOUT appending second DR
    ↓
destinationRuleIndex populated with merged config [only first DR's Name/Namespace]
    ↓
DefaultSidecarScopeForNamespace() / ConvertToSidecarScope() [sidecar.go]
    ↓
Iterates destinationRules and calls AddConfigDependencies()
    ↓ Registers ONLY first DR's ConfigKey
    ↓
ProxyDependencies.checkProxyDependencies()
    ↓ (when second DR is updated)
    ↓ Calls DependsOnConfig(second_DR's_ConfigKey)
    ↓ Second DR's ConfigKey hash NOT in configDependencies
    ↓
Push is SKIPPED, Envoy remains with stale config
```

## Recommendation

### Fix Strategy

The root cause must be addressed at the dependency tracking level. Possible approaches:

1. **Track All Contributing DRs**: Modify `consolidatedDestRules` to maintain a list of all contributing DR metadata, not just the merged config's metadata. Register all of them in `configDependencies`.

2. **Separate Metadata Storage**: Create a side-map that tracks which original DRs were merged into each merged config, then during dependency registration, register all contributing DRs.

3. **Prevent Merging for Cross-DR Updates**: Only merge DRs if they are guaranteed to always be updated together (unlikely).

### Diagnostic Steps

To verify this bug in a cluster:

1. Create two DestinationRules for the same host (e.g., one with traffic policy, one with subsets)
2. Apply both to the cluster
3. Check the pilot xDS cache: Use `/debug/config_dump` on a sidecar to confirm merged config
4. Update the second DR (add a new subset)
5. Verify sidecar config dump is NOT updated (stale config)
6. Check pilot logs for config updates - should show the DR was processed
7. Enable pilot debug logging for `proxy_dependencies` to see `DependsOnConfig()` returning false for the second DR

### Key Insight

The bug occurs at the intersection of three systems:
- **Merging**: Consolidates multiple DRs but loses identity
- **Dependency Tracking**: Only tracks the merged identity
- **Push Filtering**: Uses ConfigKeys to match changes to tracked dependencies

The disconnect happens because `mergeDestinationRule()` assumes that only one DR's metadata will be tracked, but in reality, users can independently update any of the contributing DRs at any time.
