# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update in Istio

## Summary

When multiple DestinationRules (DRs) target the same host without workload selectors, Istio's merging logic combines them into a single consolidated rule but retains only the first DR's config metadata. When a subsequently merged DR is updated, the xDS push mechanism fails to propagate changes because the updated DR's ConfigKey was never registered in the proxy's dependency tracking, resulting in the proxy receiving stale configuration.

---

## Root Cause

The root cause is a **metadata identity loss during DestinationRule merging** that creates a gap between:

1. **What gets stored** (the merged rule with only one DR's metadata)
2. **What gets tracked as a dependency** (only that one DR's ConfigKey)
3. **What triggers updates** (any of the original contributing DRs)

When a second DR is updated after being merged, its ConfigKey is not found in the proxy's `configDependencies` map, causing the xDS push filter to incorrectly skip the update.

---

## Evidence

### 1. The Merging Mechanism (`pilot/pkg/model/destination_rule.go:38-109`)

The `mergeDestinationRule()` function implements this logic:

**Lines 41-104**: When a new DR arrives for a host that already has a DR:
- **Line 46**: Checks if both DRs lack workload selectors: `bothWithoutSelector := rule.GetWorkloadSelector() == nil && existingRule.GetWorkloadSelector() == nil`
- **Line 59-60**: If both lack selectors, marks the new DR as NOT to be added: `addRuleToProcessedDestRules = false`
- **Lines 65-93**: Deep copies the existing rule and merges subsets and traffic policies from the new DR into it
- **Lines 101-103**: The conditional `if addRuleToProcessedDestRules` prevents the new DR from being appended to the list

**Key Issue**: After merging, `p.destRules[resolvedHost]` contains only the first DR's `config.Config` object (with its Name/Namespace), not the second DR's. The second DR's identity is discarded.

### 2. The Consolidated Structure (`pilot/pkg/model/push_context.go:251-256`)

```go
type consolidatedDestRules struct {
    exportTo map[host.Name]map[visibility.Instance]bool
    destRules map[host.Name][]*config.Config  // Only contains *one* config per host after merging
}
```

**Line 255**: The `destRules` map stores `[]*config.Config` — but after merging multiple DRs for the same host, this slice contains only one entry with only one DR's metadata.

### 3. Dependency Registration (`pilot/pkg/model/sidecar.go:410-418`)

When a SidecarScope is constructed, it registers dependencies via:

```go
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,           // Only the merged DR's name
            Namespace: dr.Namespace,      // Only the merged DR's namespace
        })
    }
}
```

**Lines 411-417**: Iterates over destination rules and adds each as a dependency. But `drList` is the result of `ps.destinationRule()` which returns the merged consolidated rules — containing only one `config.Config` per hostname.

**The Gap**: Only the first DR's ConfigKey is registered. The second DR's ConfigKey is never added to `sc.configDependencies`.

### 4. The ConfigKey Identity (`pilot/pkg/model/config.go`)

```go
type ConfigKey struct {
    Kind      config.GroupVersionKind
    Name      string
    Namespace string
}

func (key ConfigKey) HashCode() uint64 {
    hash := md5.New()
    for _, v := range []string{
        key.Name,
        key.Namespace,
        // ... Kind also included
    }
```

The hash includes **Name and Namespace** — making each DR's ConfigKey unique. If a second DR (e.g., `reviews-subsets`) is merged into the first (`reviews-traffic-policy`), their ConfigKeys are different and only one is registered.

### 5. The xDS Push Filter (`pilot/pkg/xds/proxy_dependencies.go:60-74`)

When a config update occurs:

```go
func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
    switch proxy.Type {
    case model.SidecarProxy:
        if proxy.SidecarScope.DependsOnConfig(config) {  // ← Critical check
            return true
        } else if proxy.PrevSidecarScope != nil && proxy.PrevSidecarScope.DependsOnConfig(config) {
            return true
        }
    }
    return false
}
```

**Line 64**: Calls `proxy.SidecarScope.DependsOnConfig(config)` where `config` is the updated DR's ConfigKey (e.g., `{Kind: DestinationRule, Name: reviews-subsets, Namespace: default}`).

### 6. The Dependency Check (`pilot/pkg/model/sidecar.go:521-540`)

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

    _, exists := sc.configDependencies[config.HashCode()]  // ← Returns false for second DR
    return exists
}
```

**Line 538**: Looks up the config's hash in `sc.configDependencies`. If the updated DR (e.g., `reviews-subsets`) was never registered, this returns `false`, causing the proxy to be skipped from the push.

### 7. The Lookup Path (`pilot/pkg/model/push_context.go:1006-1010`)

When building a SidecarScope, `ps.destinationRule()` is called to fetch DRs:

```go
if ps.destinationRuleIndex.namespaceLocal[proxyNameSpace] != nil {
    if hostname, ok := MostSpecificHostMatch(service.Hostname,
        ps.destinationRuleIndex.namespaceLocal[proxyNameSpace].destRules,
    );  ok {
        return ps.destinationRuleIndex.namespaceLocal[proxyNameSpace].destRules[hostname]  // ← Returns only one config
    }
}
```

**Line 1010**: Returns the merged consolidated DR(s) — but the slice contains only one entry due to the merging logic.

---

## Affected Components

1. **`pilot/pkg/model/destination_rule.go`**
   - Function: `mergeDestinationRule()` (lines 38-109)
   - Issue: Merging logic discards second DR's config.Config

2. **`pilot/pkg/model/push_context.go`**
   - Type: `consolidatedDestRules` (line 251-256)
   - Functions: `SetDestinationRules()` (lines 1672-1766), `destinationRule()` (lines 990-1066)
   - Issue: Stores merged rules with only first DR's metadata; lookup returns incomplete dependency list

3. **`pilot/pkg/model/sidecar.go`**
   - Functions: `ConvertToSidecarScope()` (dependency registration at lines 410-418), `DependsOnConfig()` (lines 521-540), `AddConfigDependencies()` (lines 544-555)
   - Issue: Only registers dependencies for DRs in the merged consolidated list, missing secondary contributing DRs

4. **`pilot/pkg/xds/proxy_dependencies.go`**
   - Function: `checkProxyDependencies()` (lines 60-74), `ConfigAffectsProxy()` (lines 32-58)
   - Issue: Correctly implements filtering logic, but receives incomplete dependency information from SidecarScope

5. **`pilot/pkg/config/`**
   - Config cache and update notification system
   - Issue: Correctly triggers updates for all DRs, but the dependency filtering silently drops updates for merged-away DRs

---

## Causal Chain

1. **Symptom**: Operator updates `reviews-subsets` DR; Envoy sidecar doesn't receive config update
2. **→** Push system calls `ConfigAffectsProxy()` with `ConfigKey{Name: reviews-subsets, ...}`
3. **→** `checkProxyDependencies()` calls `proxy.SidecarScope.DependsOnConfig(ConfigKey{Name: reviews-subsets, ...})`
4. **→** `DependsOnConfig()` looks up the hash of `reviews-subsets` in `sc.configDependencies`
5. **→** Hash lookup fails (returns `false`) because `reviews-subsets` ConfigKey was never added
6. **Intermediate Hop**: Why wasn't `reviews-subsets` added to dependencies?
7. **→** `ConvertToSidecarScope()` calls `ps.destinationRule()` to fetch DRs for each service
8. **→** `destinationRule()` returns merged consolidated DRs from `ps.destinationRuleIndex`
9. **→** The consolidated DR list contains only one entry: `{Name: reviews-traffic-policy, Namespace: default}`
10. **Intermediate Hop**: Why does consolidated list have only one entry?
11. **→** `SetDestinationRules()` calls `mergeDestinationRule()` for each DR
12. **→** When `reviews-subsets` arrives after `reviews-traffic-policy`:
13. **→** Both have same host and no workload selector
14. **→** `mergeDestinationRule()` sets `addRuleToProcessedDestRules = false`
15. **→** Merges subsets/policies into `reviews-traffic-policy`'s copy
16. **→** Does NOT append `reviews-subsets` to the consolidated list
17. **Root Cause**: Only `reviews-traffic-policy`'s config.Config remains in `destRules[hostname]`; `reviews-subsets`'s ConfigKey is never registered as a dependency
18. **→** When `reviews-subsets` is later updated, its ConfigKey doesn't match any registered dependency
19. **→** The proxy is filtered out and doesn't receive the xDS push

---

## Relationship Between Components

### The Merge Pipeline

```
SetDestinationRules()
  → mergeDestinationRule()
    → Merges incoming DR into existing one if hostname/selector match
    → Only first DR's config.Config survives in destRules[hostname]
    → Second DR's config identity lost
  → ps.destinationRuleIndex.[namespace/exported]DestRules updated
```

### The Dependency Pipeline

```
InitializeContext()
  → ConvertToSidecarScope()
    → ps.destinationRule() looks up consolidated DRs
    → Returns only merged DRs (incomplete list)
    → AddConfigDependencies() for each DR in the returned list
    → Only first DR's ConfigKey registered
  → SidecarScope.configDependencies populated
```

### The Push Pipeline

```
Config Update Event (reviews-subsets changed)
  → PushRequest created with ConfigKey{Name: reviews-subsets, ...}
  → For each proxy: ConfigAffectsProxy(req, proxy)
    → checkProxyDependencies(proxy, ConfigKey{Name: reviews-subsets, ...})
      → DependsOnConfig(ConfigKey{Name: reviews-subsets, ...})
        → Look up hash in configDependencies
        → Not found (never registered)
        → Returns false
      → Proxy filtered out, no push sent
```

---

## Diagnostic Evidence

To verify this hypothesis:

1. **In Istio Pilot logs**, search for `mergeDestinationRule` or `DuplicatedSubsets` metrics — if you see these, DRs are being merged.

2. **On a sidecar**, run `curl localhost:15000/debug/config_dump` and look at:
   - The CDS cluster definitions — they may have stale subset or traffic policy information
   - The RDS routes — they may reference outdated cluster subsets

3. **Create two DRs for the same host without workload selectors** (matching the scenario):
   - First DR: `traffic-policy` with connection pool settings
   - Second DR: `subsets` with v1/v2/v3 subsets
   - Update the `subsets` DR to add a `v4` subset
   - **Expected (broken)**: Envoy doesn't pick up the new v4 subset
   - **Root cause**: Only `traffic-policy`'s ConfigKey is in the proxy's dependencies

4. **Add workload selectors to the DRs**:
   - They will NOT be merged (different selectors)
   - Both ConfigKeys will be registered as separate entries in `destRules[hostname]`
   - Both update events will properly trigger pushes
   - **This avoids the bug** because merged-away identity is not an issue

---

## Recommendation

### Fix Strategy

The root cause can be addressed by:

1. **Option A (Preserve Merged DR Identity)**:
   - Modify `consolidatedDestRules` to track all contributing DRs, not just the merged result
   - Store a map from hostname to a list of all original DRs + the merged config
   - Register dependencies for all original DRs, not just the merged one
   - This requires changes to `destination_rule.go` and `sidecar.go`

2. **Option B (Explicit Merging with Identity Tracking)**:
   - Instead of merging by modifying a single config.Config, create an explicit merge record
   - Keep references to all contributing DRs in the merged structure
   - Modify `AddConfigDependencies()` to follow these references
   - This is a more invasive architectural change

3. **Option C (Prevent Merging for Separate Concerns)**:
   - Document and enforce a pattern where DRs for the same host should use workload selectors to avoid unintended merging
   - This is a user-facing workaround, not a fix

### Short-term Diagnostic Steps

1. Check `pilot/pkg/model/metrics.go` for the `DuplicatedSubsets` metric — if it fires, DRs are being merged
2. Instrument `SidecarScope.AddConfigDependencies()` to log all registered ConfigKeys for debugging
3. Instrument `DependsOnConfig()` to log lookup misses for DestinationRule kinds
4. Compare the config identities in `destRuleIndex` against all DRs in the kube API server

---

## Files to Review for Implementation

- `pilot/pkg/model/destination_rule.go`: merging logic
- `pilot/pkg/model/sidecar.go`: dependency registration
- `pilot/pkg/model/push_context.go`: consolidated storage and lookup
- `pilot/pkg/xds/proxy_dependencies.go`: dependency checking (this is correct, but relies on incomplete data)
- `pilot/pkg/config/kube/crdclient/cache_handler.go`: update event handling
