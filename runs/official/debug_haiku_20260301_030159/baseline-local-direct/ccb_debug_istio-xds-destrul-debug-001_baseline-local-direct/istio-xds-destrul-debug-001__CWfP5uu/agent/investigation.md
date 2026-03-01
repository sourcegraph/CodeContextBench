# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update in Istio

## Summary

When multiple DestinationRules (DRs) for the same host are merged during PushContext initialization, only the metadata (name/namespace) of the first merged DR is retained in the consolidated configuration. When a different contributing DR is updated, its ConfigKey fails to match the registered dependency, causing `DependsOnConfig()` to return false and the xDS push to be incorrectly skipped, leaving Envoy sidecars with stale configuration.

## Root Cause

The root cause spans two interacting mechanisms in the PushContext and SidecarScope layers:

### 1. **Identity Loss During Merging** (`pilot/pkg/model/destination_rule.go`, `mergeDestinationRule()`)

When `mergeDestinationRule()` processes multiple DestinationRules for the same host:
- If a DR for a given host already exists in `consolidatedDestRules[host]`, the function deep copies the **existing** DR and merges the incoming DR's subsets and traffic policies **into** it
- The merged result retains only the existing DR's `config.Config` metadata (name, namespace, creation timestamp)
- Contributing DRs whose metadata is not retained lose their identity in the consolidated structure
- The `consolidatedDestRules` structure contains only a single `[]*config.Config` list per hostname, not a per-DR tracking of contributors

**Relevant code** (`destination_rule.go:38-109`):
```go
func (ps *PushContext) mergeDestinationRule(p *consolidatedDestRules, destRuleConfig config.Config, exportToMap map[visibility.Instance]bool) {
    if mdrList, exists := p.destRules[resolvedHost]; exists {
        for i, mdr := range mdrList {
            existingRule := mdr.Spec.(*networking.DestinationRule)
            // ... selector matching logic ...
            copied := mdr.DeepCopy()  // Deep copy EXISTING rule
            p.destRules[resolvedHost][i] = &copied  // Update with merged content
            mergedRule := copied.Spec.(*networking.DestinationRule)
            // Merge subsets from incoming rule into the copied existing rule
            for _, subset := range rule.Subsets {
                if _, ok := existingSubset[subset.Name]; !ok {
                    mergedRule.Subsets = append(mergedRule.Subsets, subset)
                }
            }
            // ... traffic policy merge ...
        }
    }
    if addRuleToProcessedDestRules {
        p.destRules[resolvedHost] = append(p.destRules[resolvedHost], &destRuleConfig)
    }
}
```

The problem: After merging, `p.destRules[resolvedHost]` contains config.Config objects, but their metadata reflects only some of the contributing DRs, not all.

### 2. **Incomplete Dependency Registration** (`pilot/pkg/model/sidecar.go`, `AddConfigDependencies()`)

When a SidecarScope is built, `AddConfigDependencies()` registers config dependencies based on the DRs returned by `ps.destinationRule()`:

**Relevant code** (`sidecar.go:219-227` in `DefaultSidecarScopeForNamespace()`):
```go
for _, drList := range out.destinationRules {
    for _, dr := range drList {
        out.AddConfigDependencies(ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      dr.Name,              // <-- Metadata from merged DR
            Namespace: dr.Namespace,          // <-- May not include all contributors
        })
    }
}
```

And similarly at `sidecar.go:410-416` in `ConvertToSidecarScope()`:
```go
for _, dr := range drList {
    out.AddConfigDependencies(ConfigKey{
        Kind:      gvk.DestinationRule,
        Name:      dr.Name,                  // <-- Only the "winning" DR's name
        Namespace: dr.Namespace,              // <-- Only the "winning" DR's namespace
    })
}
```

**The issue**: `drList` comes from `ps.destinationRule(configNamespace, s)`, which returns the merged configuration from `consolidatedDestRules`. Each config.Config in this list was created by merging multiple original DRs, but only retains one DR's metadata.

### 3. **Push Filter Failure** (`pilot/pkg/xds/proxy_dependencies.go`, `checkProxyDependencies()`)

When a DestinationRule is updated in Kubernetes:

**Relevant code** (`proxy_dependencies.go:60-74`):
```go
func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
    switch proxy.Type {
    case model.SidecarProxy:
        if proxy.SidecarScope.DependsOnConfig(config) {
            return true
        } else if proxy.PrevSidecarScope != nil && proxy.PrevSidecarScope.DependsOnConfig(config) {
            return true
        }
    }
    return false
}
```

This calls `DependsOnConfig()` in `sidecar.go:521-540`:
```go
func (sc *SidecarScope) DependsOnConfig(config ConfigKey) bool {
    // ...
    _, exists := sc.configDependencies[config.HashCode()]
    return exists
}
```

**The problem**:
- When DR2 (reviews-subsets) is updated, a ConfigKey `{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}` is created
- This ConfigKey's hash is looked up in `sc.configDependencies`
- But `sc.configDependencies` only contains the hash of DR1's ConfigKey (because DR1's metadata was retained during merging)
- The lookup fails, and `DependsOnConfig()` returns `false`
- The proxy is not marked as needing a push

### 4. **Metadata Resolution in Networking Layers** (`pilot/pkg/networking/core/v1alpha3/cluster_builder.go`)

The networking layer builds caches that reference the DR metadata:

**Relevant code** (`cluster_builder.go`, `DependentConfigs()`):
```go
func (t clusterCache) DependentConfigs() []model.ConfigKey {
    configs := []model.ConfigKey{}
    if t.destinationRule != nil {
        configs = append(configs, model.ConfigKey{
            Kind:      gvk.DestinationRule,
            Name:      t.destinationRule.Name,      // <-- Only one DR's name
            Namespace: t.destinationRule.Namespace, // <-- Only one DR's namespace
        })
    }
    // ...
    return configs
}
```

This creates a cache dependency on the DR whose metadata is retained. Updates to other DRs that contributed to the merge are not tracked.

## Evidence

### File References with Line Numbers

1. **`pilot/pkg/model/destination_rule.go:38-109`** - `mergeDestinationRule()` function where merged DR loses contributing DR metadata
   - Line 65: `copied := mdr.DeepCopy()` - Only existing DR is deep copied
   - Line 67: `mergedRule := copied.Spec.(*networking.DestinationRule)` - Merged result uses existing metadata

2. **`pilot/pkg/model/push_context.go:251-256`** - `consolidatedDestRules` structure definition
   - Stores map from hostname to list of `[]*config.Config`
   - No tracking of contributing DRs per config

3. **`pilot/pkg/model/push_context.go:1672-1744`** - `SetDestinationRules()` where merging is orchestrated
   - Line 1716: `ps.mergeDestinationRule(namespaceLocalDestRules[configs[i].Namespace], configs[i], exportToMap)` - Merges multiple DRs for same host

4. **`pilot/pkg/model/sidecar.go:219-227`** (DefaultSidecarScopeForNamespace) and **`pilot/pkg/model/sidecar.go:410-416`** (ConvertToSidecarScope)
   - Lines that register dependencies only from the returned merged DRs
   - Lost DRs' ConfigKeys are never added

5. **`pilot/pkg/model/sidecar.go:521-540`** - `DependsOnConfig()` method
   - Line 538: `_, exists := sc.configDependencies[config.HashCode()]` - Looks up config hash
   - Returns `false` if the hash is not found

6. **`pilot/pkg/xds/proxy_dependencies.go:60-74`** - `checkProxyDependencies()` and `ConfigAffectsProxy()`
   - Line 64: `if proxy.SidecarScope.DependsOnConfig(config)` - Uses DependsOnConfig to filter pushes
   - Line 52: `if affected && checkProxyDependencies(proxy, config)` - Returns true only if dependency exists

7. **`pilot/pkg/networking/core/v1alpha3/cluster_builder.go`, `DependentConfigs()`** - Builds ConfigKeys from DR metadata
   - Creates dependency only on the DR whose metadata is retained during merging

## Affected Components

1. **`pilot/pkg/model/`**
   - `destination_rule.go` - Merges DRs, losing metadata
   - `sidecar.go` - Registers incomplete dependencies
   - `push_context.go` - Stores consolidated DRs without tracking contributors

2. **`pilot/pkg/xds/`**
   - `proxy_dependencies.go` - Filters pushes based on incomplete dependency check

3. **`pilot/pkg/networking/core/v1alpha3/`**
   - `cluster_builder.go` - Builds ConfigKeys from incomplete DR metadata
   - `route/route_cache.go` - Similar dependency tracking issue

4. **`pilot/pkg/config/`**
   - Config change events trigger PushRequests with ConfigKeys that don't match registered dependencies

## Causal Chain

1. **Symptom**: Updating a DestinationRule fails to trigger xDS push to Envoy sidecars; configuration remains stale

2. → **Intermediate: PushRequest generated but push filtered out**
   - When `reviews-subsets` DR is updated in Kubernetes, a config change event creates `PushRequest{ConfigsUpdated: {ConfigKey{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}}}`
   - This PushRequest reaches `ConfigAffectsProxy()`

3. → **Intermediate: DependsOnConfig returns false**
   - `checkProxyDependencies()` calls `proxy.SidecarScope.DependsOnConfig(config)`
   - `config` is `ConfigKey{Name: "reviews-subsets", Namespace: "default"}`
   - `sc.configDependencies` only contains the hash of `ConfigKey{Name: "reviews-traffic-policy", Namespace: "default"}`
   - Lookup fails; `DependsOnConfig()` returns `false`

4. → **Intermediate: Proxy not marked for push**
   - `checkProxyDependencies()` returns `false`
   - Proxy is not added to the set of proxies needing update

5. → **Intermediate: SidecarScope has incomplete dependencies**
   - When `DefaultSidecarScopeForNamespace()` or `ConvertToSidecarScope()` builds the SidecarScope:
   - It calls `ps.destinationRule(configNamespace, s)` which returns the merged DRs
   - Each merged DR only has metadata from one of the contributing DRs
   - `AddConfigDependencies()` only registers the "winning" DR's ConfigKey

6. → **Root Cause: Only "winning" DR's metadata retained during merge**
   - In `mergeDestinationRule()`, when multiple DRs exist for the same host:
   - The function deep copies the **existing** (first) DR
   - Merges the incoming DR's subsets/policies into the copy
   - The merged result in `consolidatedDestRules[host]` has only the first DR's metadata
   - Subsequent DRs' metadata is lost; they no longer have an identity in the consolidated structure

## Recommendation

### Fix Strategy

The root cause must be addressed in the merging and dependency tracking layers:

1. **Option A: Track All Contributing DRs (Recommended)**
   - Modify `consolidatedDestRules` to include metadata about all contributing DRs, not just one
   - When building SidecarScope, register ConfigKeys for all contributing DRs
   - Requires changes to:
     - `destination_rule.go`: Store contributor metadata
     - `sidecar.go`: Register all contributors' ConfigKeys
     - `push_context.go`: Update consolidatedDestRules structure

2. **Option B: Don't Merge, Return Full List**
   - Return a full list of all DRs per hostname instead of merging them
   - Merge subsets/policies at generation time instead of storage time
   - More memory usage but no identity loss
   - Requires changes throughout the CDS/RDS generation pipeline

3. **Option C: Use DR Host Instead of Name/Namespace**
   - Use the destination hostname as the dependency key instead of DR name/namespace
   - All DRs for the same host are treated as one logical entity
   - Simpler but loses granularity (all DRs for a host must push together)

### Diagnostic Steps

1. **Enable debug logging** for DestinationRule merging in `SetDestinationRules()`
2. **Log contributor tracking**: Add logging when a DR is merged to show which metadata is retained
3. **Verify SidecarScope dependencies**: Use `/debug/config_dependencies` endpoint to list registered ConfigKeys per SidecarScope
4. **Trace PushRequest filtering**: Add logging to `ConfigAffectsProxy()` and `checkProxyDependencies()` to see why pushes are filtered
5. **Monitor config events**: Log all config change events that create PushRequests with DestinationRule ConfigKeys
6. **Compare ConfigKeys**: When a push is filtered, log both the incoming ConfigKey and the registered ConfigKeys to identify the mismatch

### Verification

After implementing a fix:

1. Verify that updating ANY DestinationRule for a given host triggers an xDS push to relevant sidecars
2. Verify that Envoy config dump reflects the updated DR configuration without pod restart
3. Add test case: Multiple DRs for same host → update one → verify push is sent
4. Add observability: Log which contributing DRs are tracked for each consolidated DR
5. Add test validation: Verify all contributing DR ConfigKeys are in SidecarScope.configDependencies
