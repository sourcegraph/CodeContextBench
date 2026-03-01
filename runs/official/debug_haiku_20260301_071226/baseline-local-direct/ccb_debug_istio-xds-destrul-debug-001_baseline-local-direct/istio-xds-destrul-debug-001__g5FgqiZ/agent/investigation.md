# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update

## Summary

When multiple DestinationRules for the same host are merged during configuration initialization, only the first DR's ConfigKey is registered in the proxy's dependency tracking. When the second (or subsequent) DR is updated, the xDS push filter incorrectly skips the update because the updated DR's identity was lost during merging, resulting in stale Envoy configuration.

## Root Cause

The root cause is a **mismatch between the merging process and the dependency tracking mechanism**. The `mergeDestinationRule()` function in `pilot/pkg/model/destination_rule.go` consolidates multiple DRs into a single entry while discarding the identity of non-primary DRs, but the dependency tracking in `pilot/pkg/model/sidecar.go` only registers the surviving DR's ConfigKey, not all contributing DRs.

## Evidence

### 1. DestinationRule Merging (pilot/pkg/model/destination_rule.go)

**Function**: `mergeDestinationRule()` (lines 38-109)

The function merges multiple DRs for the same host by:
- At lines 41-104: Iterating through existing DRs (`mdrList`) for the resolved host
- At lines 44-60: Checking if the incoming DR should be merged with an existing one
- At lines 63-100: When `bothWithoutSelector` (both DRs lack workload selectors), the incoming DR's subsets are **added** to the existing DR (line 80), but the incoming DR itself is **not** appended to the list (line 101 skips addition when `addRuleToProcessedDestRules = false`)
- At lines 101-103: Only if `addRuleToProcessedDestRules = true` is the incoming DR added as a separate entry

**Key observation**: When two DRs without workload selectors target the same host, the second DR's specifications are merged into the first DR's object, but the second DR's `config.Config` metadata is lost. The `destRuleIndex[hostname]` list contains only one entry.

### 2. Consolidated DestRules Structure (pilot/pkg/model/push_context.go)

**Type**: `consolidatedDestRules` (lines 251-256)

```go
type consolidatedDestRules struct {
    exportTo  map[host.Name]map[visibility.Instance]bool
    destRules map[host.Name][]*config.Config  // Maps hostname to list of DRs
}
```

This structure stores DRs by hostname, keyed in `destRules`. After `SetDestinationRules()` calls `mergeDestinationRule()`, this map contains only one DR entry per hostname when multiple DRs are merged.

### 3. SidecarScope Dependency Registration (pilot/pkg/model/sidecar.go)

**DefaultSidecarScopeForNamespace()** (lines 219-227):
```go
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,              // Only first DR's name registered
            Namespace: dr.Namespace,         // Only first DR's namespace registered
        })
    }
}
```

**ConvertToSidecarScope()** (lines 410-416):
```go
for _, dr := range drList {
    out.AddConfigDependencies(ConfigKey{
        Kind:      gvk.DestinationRule,
        Name:      dr.Name,                 // Only first DR's name registered
        Namespace: dr.Namespace,            // Only first DR's namespace registered
    })
}
```

**Key observation**: The code iterates through `drList` (which should contain all DRs for that hostname), but after merging, the list contains only the first DR. The ConfigKey for the second DR is never registered.

### 4. The DependsOnConfig Check (pilot/pkg/model/sidecar.go, pilot/pkg/xds/proxy_dependencies.go)

**DependsOnConfig()** (lines 523-540 in sidecar.go):
```go
func (sc *SidecarScope) DependsOnConfig(config ConfigKey) bool {
    // ...
    _, exists := sc.configDependencies[config.HashCode()]
    return exists
}
```

**ConfigAffectsProxy()** (lines 32-58 in proxy_dependencies.go):
```go
func ConfigAffectsProxy(req *model.PushRequest, proxy *model.Proxy) bool {
    if len(req.ConfigsUpdated) == 0 {
        return true
    }
    for config := range req.ConfigsUpdated {
        // ...
        if affected && checkProxyDependencies(proxy, config) {
            return true
        }
    }
    return false
}
```

**checkProxyDependencies()** (lines 60-74 in proxy_dependencies.go):
```go
func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
    switch proxy.Type {
    case model.SidecarProxy:
        if proxy.SidecarScope.DependsOnConfig(config) {
            return true                      // Push will be sent
        }
    }
    return false                             // Push will be skipped
}
```

**Key observation**: When a config change event occurs (e.g., updating the second DR), `ConfigAffectsProxy()` checks `DependsOnConfig()` with the updated DR's ConfigKey. If that ConfigKey was never registered due to merging, `DependsOnConfig()` returns false, and the entire push is skipped.

### 5. Push Filtering (pilot/pkg/xds/ads.go)

**pushConnection()** (lines 680-712):
```go
if !s.ProxyNeedsPush(con.proxy, pushRequest) {
    log.Debugf("Skipping push to %v, no updates required", con.conID)
    return nil  // Push is skipped
}
```

**ProxyNeedsPush** is set to `DefaultProxyNeedsPush()` (discovery.go line 191), which calls `ConfigAffectsProxy()` → `checkProxyDependencies()` → `DependsOnConfig()`.

**Key observation**: If `DependsOnConfig()` returns false for the updated DR, the push is silently skipped at line 689, and the proxy never receives the configuration update.

### 6. Scenario: Two DestinationRules for Same Host

**Initial state:**
- `reviews-traffic-policy` DR created (defines trafficPolicy)
- `reviews-subsets` DR created (defines subsets)
- Both target `reviews.default.svc.cluster.local` with no workload selector

**After SetDestinationRules():**
- In `mergeDestinationRule()`, when processing `reviews-subsets`, it finds `reviews-traffic-policy` already in the list
- Since both lack workload selectors, it merges the subsets into `reviews-traffic-policy`
- `p.destRules[hostname]` = `[reviews-traffic-policy with merged subsets]`
- `reviews-subsets` ConfigKey is discarded

**When SidecarScope is built:**
- Only `reviews-traffic-policy`'s ConfigKey is registered in `configDependencies`

**When reviews-subsets is updated (e.g., adding v3 subset):**
- ConfigUpdate event fires with ConfigKey `{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}`
- ConfigAffectsProxy checks if any proxy depends on this config
- DependsOnConfig looks for this ConfigKey in configDependencies
- **ConfigKey not found** (only "reviews-traffic-policy" is registered)
- Returns false
- **Push is skipped**
- Envoy continues serving stale configuration

## Affected Components

1. **pilot/pkg/model/destination_rule.go**
   - `mergeDestinationRule()` - Loses identity of merged DRs
   - No tracking of which DRs contributed to a merged config

2. **pilot/pkg/model/sidecar.go**
   - `DefaultSidecarScopeForNamespace()` - Only registers ConfigKeys from visible DRs in consolidated list
   - `ConvertToSidecarScope()` - Same issue
   - `DependsOnConfig()` - Correctly checks dependencies but receives incomplete registration

3. **pilot/pkg/model/push_context.go**
   - `SetDestinationRules()` - Calls `mergeDestinationRule()` and builds index
   - `mergeDestinationRule()` - Called here at lines 1716, 1739
   - `destinationRule()` - Returns merged DRs without indicating that multiple DRs contributed

4. **pilot/pkg/xds/proxy_dependencies.go**
   - `ConfigAffectsProxy()` - Uses incomplete dependency information
   - `checkProxyDependencies()` - Relies on `DependsOnConfig()` which has incomplete data
   - `DefaultProxyNeedsPush()` - Uses `ConfigAffectsProxy()`

5. **pilot/pkg/xds/ads.go**
   - `pushConnection()` - Line 688 calls ProxyNeedsPush which may incorrectly skip pushes
   - Uses the proxy dependency filter to decide whether to send updates

6. **pilot/pkg/xds/discovery.go**
   - `ProxyNeedsPush` function pointer set to `DefaultProxyNeedsPush`

## Causal Chain

1. **Symptom**: Updating `reviews-subsets` DestinationRule does not trigger xDS push to sidecar
   - Evidence: `/debug/config_dump` on sidecar shows old configuration even after DR update in API server

2. **Intermediate Hop 1**: ConfigAffectsProxy returns false for the updated DR
   - Code path: `pushConnection()` (ads.go:688) → `ProxyNeedsPush()` → `ConfigAffectsProxy()` (proxy_dependencies.go:32) → returns false

3. **Intermediate Hop 2**: checkProxyDependencies returns false because DependsOnConfig returns false
   - Code path: `ConfigAffectsProxy()` (proxy_dependencies.go:38-54) → `checkProxyDependencies()` (proxy_dependencies.go:60) → `DependsOnConfig()` (sidecar.go:523)

4. **Intermediate Hop 3**: DependsOnConfig cannot find the updated DR's ConfigKey in configDependencies
   - Code path: `DependsOnConfig()` (sidecar.go:538) → looks for `config.HashCode()` in `sc.configDependencies` → **not found**

5. **Root Cause Mechanism**: The ConfigKey for the updated DR was never registered in configDependencies
   - Root cause: `DefaultSidecarScopeForNamespace()` / `ConvertToSidecarScope()` (sidecar.go:219-227, 410-416) iterate through `out.destinationRules[hostname]` and register ConfigKeys
   - But after `SetDestinationRules()` calls `mergeDestinationRule()` (push_context.go:1716, 1739), only the first DR remains in the list
   - The second DR's metadata is lost during `mergeDestinationRule()` (destination_rule.go:38-109) when `addRuleToProcessedDestRules = false` (line 60) and the DR is not appended (line 102-103)

6. **Root Cause**: In `mergeDestinationRule()`, when two DRs without workload selectors target the same host:
   - The incoming DR's subsets are merged into the existing DR (line 80)
   - The incoming DR is not added to the list as a separate entry (line 101-103)
   - Only the first DR's ConfigKey survives; subsequent DRs' identities are discarded
   - **This violates the assumption of the dependency tracking layer**, which expects all DRs contributing to a service's configuration to be tracked

## Recommendation

### Fix Strategy

The core issue is that the merging process destroys the identity of contributing DRs. The fix should restore identity tracking:

1. **Option A - Track Contributing DRs**: Modify `consolidatedDestRules` to store a list of contributing ConfigKeys in addition to the merged DR. When SidecarScope registers dependencies, register all contributing DRs, not just the merged one.

2. **Option B - Preserve DR Identity**: Change the merging strategy to keep all DR ConfigKeys in the list, not just the merged one. Modify the merging logic to avoid modifying the first DR in-place but instead create a synthetic merged DR that tracks all contributions.

3. **Option C - Detect Updates on Merged Specs**: When a DestinationRule is updated, even if its ConfigKey is not in configDependencies, check if any dependency targets the same host and trigger a push for those proxies.

### Diagnostic Steps

1. **Monitor dependency registration**:
   - Add logging in `DefaultSidecarScopeForNamespace()` and `ConvertToSidecarScope()` to log all registered ConfigKeys
   - Verify that both DRs' ConfigKeys are registered when two DRs exist for the same host

2. **Trace the config update path**:
   - Add logging in `ConfigAffectsProxy()` to log which configs are checked and their dependency status
   - Add logging in `DependsOnConfig()` to show which ConfigKeys are in configDependencies

3. **Verify the merging process**:
   - Add logging in `mergeDestinationRule()` to show when DRs are merged vs. kept as separate entries
   - Log the resulting `destRules` index to show which ConfigKeys survive the merge

4. **Test incremental updates**:
   - Create two DRs for the same host
   - Update the second DR
   - Trace the ConfigUpdate event to see which ConfigKey is sent
   - Verify that SidecarScope.DependsOnConfig returns true for that ConfigKey

