# Investigation Report: Stale Envoy Route Configuration After DestinationRule Update in Istio

## Summary

When multiple DestinationRules target the same host, Istio's merge pipeline preserves only the first rule's identity metadata (name/namespace). Subsequently updated DRs lose their metadata during the merge, causing their ConfigKeys to never be registered in SidecarScope's configDependencies. When those DRs are updated, the xDS push filter—which checks `SidecarScope.DependsOnConfig(configKey)`—returns false and incorrectly skips the xDS push to sidecars, leaving them serving stale configuration.

## Root Cause

The root cause is a **metadata loss during DestinationRule merging** combined with **incomplete dependency registration** in the SidecarScope, resulting in a **broken xDS push filter decision** that skips required updates.

### Specific Gap: Lost ConfigKey Registration

When two DestinationRules for the same host are merged in `pilot/pkg/model/destination_rule.go::mergeDestinationRule()`, the function modifies the first rule in-place and discards the second rule's metadata. Later, when SidecarScope builds its configDependencies in `pilot/pkg/model/sidecar.go`, it only registers the name/namespace of the merged (surviving) DR. If the discarded DR is subsequently updated, its ConfigKey is not found in configDependencies, `DependsOnConfig()` returns false, and the push is silently skipped.

## Evidence

### 1. DestinationRule Merge loses metadata (`destination_rule.go:38-109`)

```
File: pilot/pkg/model/destination_rule.go
Lines: 38-109 (mergeDestinationRule function)

Key excerpts:
  Line 38:  func (ps *PushContext) mergeDestinationRule(p *consolidatedDestRules, destRuleConfig config.Config, exportToMap map[visibility.Instance]bool)
  Line 41:  if mdrList, exists := p.destRules[resolvedHost]; exists {
  Line 44:    for i, mdr := range mdrList {
  Line 59-61:  if bothWithoutSelector || (rule.GetWorkloadSelector() != nil && selectorsMatch) {
                  addRuleToProcessedDestRules = false
  Line 65:    copied := mdr.DeepCopy()
  Line 66:    p.destRules[resolvedHost][i] = &copied  ← First DR kept, in-place modification
  Line 67:    mergedRule := copied.Spec.(*networking.DestinationRule)
  Line 77-87:   for _, subset := range rule.Subsets {
                  // Subsets from NEW rule merged INTO copied rule
  Line 91-93:   if mergedRule.TrafficPolicy == nil && rule.TrafficPolicy != nil {
                  mergedRule.TrafficPolicy = rule.TrafficPolicy
  Line 101-103: if addRuleToProcessedDestRules {
                  p.destRules[resolvedHost] = append(p.destRules[resolvedHost], &destRuleConfig)
```

**Issue**: When two DRs for the same host without a workload selector are encountered:
- The first DR (at index i in mdrList) is deep-copied and modified in-place (line 65-66)
- The second DR's properties (subsets, traffic policy) are merged INTO the first
- Only the first DR's config.Config object (with first DR's name/namespace) survives in the list
- The second DR's name/namespace metadata is completely lost

### 2. SidecarScope registers only visible (merged) DR's ConfigKey (`sidecar.go:219-227, 408-416`)

```
File: pilot/pkg/model/sidecar.go
Lines: 173-227 (DefaultSidecarScopeForNamespace function)

Key excerpts:
  Line 209:   if dr := ps.destinationRule(configNamespace, s); dr != nil {
                out.destinationRules[s.Hostname] = dr  ← Gets MERGED DRs
  Line 219-227:
             for _, drList := range out.destinationRules {
               for _, dr := range drList {
                 out.AddConfigDependencies(ConfigKey{
                   Kind:      gvk.DestinationRule,
                   Name:      dr.Name,              ← Only FIRST merged DR's name
                   Namespace: dr.Namespace,         ← Only FIRST merged DR's namespace
                 })
               }
             }

Lines: 408-416 (ConvertToSidecarScope function)
  Line 408:   if drList := ps.destinationRule(configNamespace, s); drList != nil {
                out.destinationRules[s.Hostname] = drList
  Line 410-416:
             for _, dr := range drList {
               out.AddConfigDependencies(ConfigKey{
                 Kind:      gvk.DestinationRule,
                 Name:      dr.Name,              ← Only FIRST merged DR's name
                 Namespace: dr.Namespace,         ← Only FIRST merged DR's namespace
               })
             }
```

**Issue**: The `ps.destinationRule()` call returns the merged DRs from consolidatedDestRules (which contains only one config.Config per host after merging). When AddConfigDependencies is called, it registers only the name/namespace of the surviving merged DR. The ConfigKey for any discarded DRs is never registered.

### 3. DestinationRule merging consolidates into single entry (`push_context.go:251-256, 1660-1760`)

```
File: pilot/pkg/model/push_context.go
Lines: 251-256 (consolidatedDestRules structure)

  type consolidatedDestRules struct {
    exportTo map[host.Name]map[visibility.Instance]bool
    destRules map[host.Name][]*config.Config  ← Key insight: destRules per host
  }

Lines: 1660-1763 (InitDestinationRules builds this index)
  Line 1661:  func newProcessedDestRules() *consolidatedDestRules {
  Line 1716:  ps.mergeDestinationRule(namespaceLocalDestRules[configs[i].Namespace], configs[i], exportToMap)
  Line 1739:  ps.mergeDestinationRule(exportedDestRulesByNamespace[configs[i].Namespace], configs[i], exportToMap)
  Line 1742:  ps.mergeDestinationRule(rootNamespaceLocalDestRules, configs[i], exportToMap)
```

**Issue**: All DRs for the same host in the same namespace are progressively merged via repeated calls to mergeDestinationRule(). The consolidatedDestRules.destRules[host] array shrinks as DRs are merged: it starts with one entry per DR, but as merges occur, multiple entries become one.

### 4. SidecarScope.DependsOnConfig checks for ConfigKey in dependencies (`sidecar.go:521-540`)

```
File: pilot/pkg/model/sidecar.go
Lines: 521-540 (DependsOnConfig method)

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

    _, exists := sc.configDependencies[config.HashCode()]  ← Checks if ConfigKey's hash is in dependencies
    return exists
  }
```

**Issue**: For DestinationRule kind, DependsOnConfig does a hash lookup in configDependencies. The hash is computed from Name/Namespace (line 60-74 in config.go). If a DR was merged and lost its metadata, its ConfigKey's hash will never be found in this map, and DependsOnConfig returns false.

### 5. xDS Push Filter uses DependsOnConfig (`proxy_dependencies.go:30-74`)

```
File: pilot/pkg/xds/proxy_dependencies.go
Lines: 30-74 (ConfigAffectsProxy and checkProxyDependencies)

  func ConfigAffectsProxy(req *model.PushRequest, proxy *model.Proxy) bool {
    if len(req.ConfigsUpdated) == 0 {
      return true
    }

    for config := range req.ConfigsUpdated {
      affected := true

      if kindAffectedTypes, f := configKindAffectedProxyTypes[config.Kind]; f {
        affected = false
        for _, t := range kindAffectedTypes {
          if t == proxy.Type {
            affected = true
            break
          }
        }
      }

      if affected && checkProxyDependencies(proxy, config) {
        return true
      }
    }

    return false
  }

  func checkProxyDependencies(proxy *model.Proxy, config model.ConfigKey) bool {
    switch proxy.Type {
    case model.SidecarProxy:
      if proxy.SidecarScope.DependsOnConfig(config) {      ← Critical check here
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

**Issue**: When a DestinationRule is updated in Kubernetes, a PushRequest is created with that DR's ConfigKey in ConfigsUpdated. For each proxy, ConfigAffectsProxy iterates through ConfigsUpdated and calls checkProxyDependencies. If the DR's ConfigKey (now orphaned after merging) is not in configDependencies, DependsOnConfig returns false, checkProxyDependencies returns false, and the push is skipped entirely.

## Affected Components

1. **`pilot/pkg/model/destination_rule.go`** — Implements mergeDestinationRule(), which modifies the first rule in-place and loses the second DR's metadata
2. **`pilot/pkg/model/sidecar.go`** — Implements DefaultSidecarScopeForNamespace() and ConvertToSidecarScope(), which register only visible (merged) DR ConfigKeys
3. **`pilot/pkg/model/push_context.go`** — Implements InitDestinationRules() and merges DRs via consolidatedDestRules; also implements destinationRule() method
4. **`pilot/pkg/xds/proxy_dependencies.go`** — Implements ConfigAffectsProxy() and checkProxyDependencies() which use DependsOnConfig() to decide whether to push
5. **`pilot/pkg/model/config.go`** — Defines ConfigKey and its HashCode() computation

## Causal Chain

1. **Symptom**: User updates a DestinationRule (e.g., reviews-subsets); Envoy sidecar's configuration does not change; `/debug/config_dump` shows stale config

2. **Intermediate Hop 1 - Merge Loss**: When Istio processes the DestinationRules for "reviews.default.svc.cluster.local" during PushContext initialization:
   - reviews-traffic-policy is processed first → added to consolidatedDestRules.destRules[reviews-fqdn]
   - reviews-subsets is processed second → merged WITH reviews-traffic-policy via mergeDestinationRule()
   - Only reviews-traffic-policy's name/namespace survives; reviews-subsets' metadata is discarded

3. **Intermediate Hop 2 - Dependency Gap**: When DefaultSidecarScopeForNamespace() builds the sidecar scope:
   - It calls ps.destinationRule() which returns the merged config.Config (with reviews-traffic-policy's name/namespace)
   - It registers only reviews-traffic-policy's ConfigKey in configDependencies via AddConfigDependencies()
   - reviews-subsets' ConfigKey is never registered

4. **Intermediate Hop 3 - Push Filter Failure**: When user updates reviews-subsets in the Kubernetes API:
   - Pilot receives a PushRequest with ConfigKey{Kind: DestinationRule, Name: "reviews-subsets", Namespace: "default"}
   - For each sidecar proxy, xDS calls ConfigAffectsProxy(req, proxy)
   - Inside checkProxyDependencies(), it calls proxy.SidecarScope.DependsOnConfig(reviews-subsets-ConfigKey)
   - DependsOnConfig looks up the ConfigKey's HashCode in configDependencies
   - The hash lookup FAILS (reviews-subsets was never registered)
   - DependsOnConfig returns false
   - checkProxyDependencies returns false
   - ConfigAffectsProxy returns false

5. **Root Cause**: The push is completely skipped because the updated DR's ConfigKey was never registered in the SidecarScope's configDependencies due to metadata loss during merging.

## Relationship between Components

```
┌─────────────────────────────────────────────────────────────────┐
│ Kubernetes API Server                                           │
│  updates reviews-subsets DestinationRule                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Pilot - PushRequest triggered with ConfigsUpdated               │
│  = {ConfigKey{reviews-subsets, default, DestinationRule}}      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │ ConfigAffectsProxy()     │
         │ (proxy_dependencies.go) │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │ checkProxyDependencies()│
         │ for SidecarProxy        │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────────────────────┐
         │ SidecarScope.DependsOnConfig()           │
         │ (sidecar.go line 538)                    │
         │ Checks: reviews-subsets.HashCode()       │
         │   in configDependencies map              │
         │ RETURNS: false (not found!)              │
         └────────────┬────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │ Push is SKIPPED         │
         │ (no xDS config sent)    │
         └────────────────────────┘

BUT configDependencies contains only:
  reviews-traffic-policy.HashCode()
  (from mergeDestinationRule() in destination_rule.go)

Missing:
  reviews-subsets.HashCode()
  (lost during merge at destination_rule.go:66)
```

## Recommendation

To fix this issue, the dependency tracking must account for ALL contributing DestinationRules when multiple DRs are merged, not just the surviving one.

### Proposed Fix Strategy

1. **Track Merged Sources**: When mergeDestinationRule() merges two DRs, store metadata about ALL contributing DRs in the merged config.Config object. This could be done via a custom field or by maintaining a side mapping.

2. **Register All Contributors**: When SidecarScope.AddConfigDependencies() is called for a merged DR, register ConfigKeys for ALL contributing DRs, not just the merged result's name/namespace.

3. **Alternative: Register at Merge Time**: Instead of registering dependencies when SidecarScope is built, register them immediately when the merge happens in mergeDestinationRule(). This ensures no contributor is lost.

### Diagnostic Steps

1. **Add logging** in destination_rule.go::mergeDestinationRule() to log which DRs are being merged and which metadata is being discarded.

2. **Add logging** in sidecar.go::AddConfigDependencies() to log all registered ConfigKeys, comparing against the actual DRs that contributed.

3. **Add logging** in proxy_dependencies.go::DependsOnConfig() to log cache misses when a DR ConfigKey is not found.

4. **Test Case**: Create two DestinationRules for the same host in the same namespace, update the non-first one, and verify the sidecar receives updated configuration.

5. **Verify configDependencies**: After building a SidecarScope, inspect which DestinationRule ConfigKeys are registered and cross-reference against all actual DRs in the namespace.
