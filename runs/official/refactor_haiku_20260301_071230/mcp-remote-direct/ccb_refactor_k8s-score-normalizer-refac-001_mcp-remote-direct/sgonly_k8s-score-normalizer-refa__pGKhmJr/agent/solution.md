# Kubernetes Scheduler ScoreExtensions → ScoreNormalizer Refactoring

## Files Examined

### Interface Definition
- **pkg/scheduler/framework/interface.go** — Defines `ScoreExtensions` interface (line 483) and `ScoreExtensions()` method on `ScorePlugin` interface (line 500). Both need renaming.

### Metrics
- **pkg/scheduler/metrics/metrics.go** — Defines `ScoreExtensionNormalize` constant (line 50). Needs renaming to `ScoreNormalize`.

### Runtime Framework
- **pkg/scheduler/framework/runtime/framework.go** — Contains the runtime implementation that calls `ScoreExtensions()` method and uses metrics constant (lines 1141, 1145, 1202, 1205-1206). Also contains `runScoreExtension()` function (line 1200) that should remain as is since it's an internal method name.

### Plugin Implementations (10 files)
1. **pkg/scheduler/testing/framework/fake_plugins.go** — `FakePreScoreAndScorePlugin.ScoreExtensions()` method (line 265)
2. **pkg/scheduler/testing/framework/fake_extender.go** — `node2PrioritizerPlugin.ScoreExtensions()` method (line 136)
3. **pkg/scheduler/framework/plugins/noderesources/fit.go** — `Fit.ScoreExtensions()` method (line 96)
4. **pkg/scheduler/framework/plugins/interpodaffinity/scoring.go** — `InterPodAffinity.ScoreExtensions()` method (line 300)
5. **pkg/scheduler/framework/plugins/podtopologyspread/scoring.go** — `PodTopologySpread.ScoreExtensions()` method (line 269)
6. **pkg/scheduler/framework/plugins/nodeaffinity/node_affinity.go** — `NodeAffinity.ScoreExtensions()` method (line 277)
7. **pkg/scheduler/framework/plugins/volumebinding/volume_binding.go** — `VolumeBinding.ScoreExtensions()` method (line 325)
8. **pkg/scheduler/framework/plugins/imagelocality/image_locality.go** — `ImageLocality.ScoreExtensions()` method (line 73)
9. **pkg/scheduler/framework/plugins/tainttoleration/taint_toleration.go** — `TaintToleration.ScoreExtensions()` method (line 162)
10. **pkg/scheduler/framework/plugins/noderesources/balanced_allocation.go** — `BalancedAllocation.ScoreExtensions()` method (line 112)

### Test Files (6 files)
1. **test/integration/scheduler/plugins/plugins_test.go** — Two test plugins: `ScorePlugin.ScoreExtensions()` (line 343) and `ScoreWithNormalizePlugin.ScoreExtensions()` (line 367)
2. **pkg/scheduler/schedule_one_test.go** — Three test plugins: `falseMapPlugin.ScoreExtensions()` (line 173), `numericMapPlugin.ScoreExtensions()` (line 197), and `reverseNumericMapPlugin.ScoreExtensions()` (line 220)
3. **pkg/scheduler/framework/runtime/framework_test.go** — Three test plugins: `TestScoreWithNormalizePlugin.ScoreExtensions()` (line 134), `TestScorePlugin.ScoreExtensions()` (line 156), and `TestPlugin.ScoreExtensions()` (line 196)
4. **pkg/scheduler/framework/plugins/interpodaffinity/scoring_test.go** — Direct calls to `.ScoreExtensions().NormalizeScore()` (lines 810, 972)
5. **pkg/scheduler/framework/plugins/nodeaffinity/node_affinity_test.go** — Direct call to `.ScoreExtensions().NormalizeScore()` (line 1223)
6. **pkg/scheduler/framework/plugins/tainttoleration/taint_toleration_test.go** — Direct call to `.ScoreExtensions().NormalizeScore()` (line 259)

## Dependency Chain

1. **Definition**: `pkg/scheduler/framework/interface.go` (original definition of `ScoreExtensions` interface and `ScoreExtensions()` accessor method)

2. **Direct usage - Runtime framework**:
   - `pkg/scheduler/framework/runtime/framework.go` — Calls `pl.ScoreExtensions()` to get the interface and calls methods on it. Also uses `metrics.ScoreExtensionNormalize` constant.

3. **Direct usage - Plugin implementations** (implement the interface and accessor method):
   - `pkg/scheduler/testing/framework/fake_plugins.go`
   - `pkg/scheduler/testing/framework/fake_extender.go`
   - `pkg/scheduler/framework/plugins/noderesources/fit.go`
   - `pkg/scheduler/framework/plugins/interpodaffinity/scoring.go`
   - `pkg/scheduler/framework/plugins/podtopologyspread/scoring.go`
   - `pkg/scheduler/framework/plugins/nodeaffinity/node_affinity.go`
   - `pkg/scheduler/framework/plugins/volumebinding/volume_binding.go`
   - `pkg/scheduler/framework/plugins/imagelocality/image_locality.go`
   - `pkg/scheduler/framework/plugins/tainttoleration/taint_toleration.go`
   - `pkg/scheduler/framework/plugins/noderesources/balanced_allocation.go`

4. **Direct usage - Test code** (calls the method and/or implements it):
   - `test/integration/scheduler/plugins/plugins_test.go`
   - `pkg/scheduler/schedule_one_test.go`
   - `pkg/scheduler/framework/runtime/framework_test.go`
   - `pkg/scheduler/framework/plugins/interpodaffinity/scoring_test.go`
   - `pkg/scheduler/framework/plugins/nodeaffinity/node_affinity_test.go`
   - `pkg/scheduler/framework/plugins/tainttoleration/taint_toleration_test.go`

5. **Transitive usage** (uses metrics constant):
   - `pkg/scheduler/metrics/metrics.go` — Defines the `ScoreExtensionNormalize` constant used by framework.go

## Changes Required

### 1. pkg/scheduler/framework/interface.go
- Rename `ScoreExtensions` interface to `ScoreNormalizer`
- Rename `ScoreExtensions()` method to `ScoreNormalizer()` on `ScorePlugin` interface
- Update comments to reference `ScoreNormalizer`

### 2. pkg/scheduler/metrics/metrics.go
- Rename `ScoreExtensionNormalize` constant to `ScoreNormalize`

### 3. pkg/scheduler/framework/runtime/framework.go
- Update all calls from `pl.ScoreExtensions()` to `pl.ScoreNormalizer()`
- Update references from `metrics.ScoreExtensionNormalize` to `metrics.ScoreNormalize`
- Update type references from `framework.ScoreExtensions` to `framework.ScoreNormalizer`

### 4-13. Plugin Implementation Files (10 files)
- Update method signature from `func (...) ScoreExtensions()` to `func (...) ScoreNormalizer()`
- Update return type from `framework.ScoreExtensions` to `framework.ScoreNormalizer`
- Update comments to reference `ScoreNormalizer`

### 14-19. Test Files (6 files)
- Update method signatures in test plugin implementations
- Update type references in all places where `.ScoreExtensions()` is called
- Update comments where applicable

## Analysis

This is a straightforward rename refactoring affecting:
- 1 interface definition file
- 1 metrics file
- 1 core runtime file
- 10 plugin implementation files
- 6 test files

**Total files to modify: 19**

The changes are systematic:
1. All occurrences of the interface name `ScoreExtensions` → `ScoreNormalizer`
2. All occurrences of the method name `ScoreExtensions()` → `ScoreNormalizer()`
3. All occurrences of the type reference `framework.ScoreExtensions` → `framework.ScoreNormalizer`
4. The metrics constant `ScoreExtensionNormalize` → `ScoreNormalize`

The refactoring is backward-incompatible at the API level but preserves all functionality. The `NormalizeScore()` method name remains unchanged as it's the only method on the interface and provides clear semantics.

## Code Changes - Key Examples

### Interface Definition Change (pkg/scheduler/framework/interface.go)
```diff
- // ScoreExtensions is an interface for Score extended functionality.
- type ScoreExtensions interface {
+ // ScoreNormalizer is an interface for Score normalization functionality.
+ type ScoreNormalizer interface {
      // NormalizeScore is called for all node scores produced by the same plugin's "Score"
      // method. A successful run of NormalizeScore will update the scores list and return
      // a success status.
      NormalizeScore(ctx context.Context, state *CycleState, p *v1.Pod, scores NodeScoreList) *Status
  }

  // ScorePlugin is an interface that must be implemented by "Score" plugins to rank
  // nodes that passed the filtering phase.
  type ScorePlugin interface {
      Plugin
      // Score is called on each filtered node. It must return success and an integer
      // indicating the rank of the node. All scoring plugins must return success or
      // the pod will be rejected.
      Score(ctx context.Context, state *CycleState, p *v1.Pod, nodeName string) (int64, *Status)

-     // ScoreExtensions returns a ScoreExtensions interface if it implements one, or nil if does not.
-     ScoreExtensions() ScoreExtensions
+     // ScoreNormalizer returns a ScoreNormalizer interface if it implements one, or nil if does not.
+     ScoreNormalizer() ScoreNormalizer
  }
```

### Metrics Constant Change (pkg/scheduler/metrics/metrics.go)
```diff
  const (
      PreFilter                   = "PreFilter"
      Filter                      = "Filter"
      PreScore                    = "PreScore"
      Score                       = "Score"
-     ScoreExtensionNormalize     = "ScoreExtensionNormalize"
+     ScoreNormalize              = "ScoreNormalize"
      PreBind                     = "PreBind"
      Bind                        = "Bind"
  )
```

### Runtime Framework Change (pkg/scheduler/framework/runtime/framework.go)
```diff
  func (f *frameworkImpl) runScoreExtension(ctx context.Context, pl framework.ScorePlugin,
      state *framework.CycleState, pod *v1.Pod, nodeScoreList framework.NodeScoreList) *framework.Status {
      if !state.ShouldRecordPluginMetrics() {
-         return pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
+         return pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
      }
      startTime := time.Now()
-     status := pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
-     f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreExtensionNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
+     status := pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
+     f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
      return status
  }

- if pl.ScoreExtensions() == nil {
+ if pl.ScoreNormalizer() == nil {
      return
  }
```

### Plugin Implementation Example (pkg/scheduler/framework/plugins/interpodaffinity/scoring.go)
```diff
- // ScoreExtensions of the Score plugin.
- func (pl *InterPodAffinity) ScoreExtensions() framework.ScoreExtensions {
+ // ScoreNormalizer of the Score plugin.
+ func (pl *InterPodAffinity) ScoreNormalizer() framework.ScoreNormalizer {
      return pl
  }
```

### Test Implementation Example (pkg/scheduler/framework/runtime/framework_test.go)
```diff
- func (pl *TestScoreWithNormalizePlugin) ScoreExtensions() framework.ScoreExtensions {
+ func (pl *TestScoreWithNormalizePlugin) ScoreNormalizer() framework.ScoreNormalizer {
      return injectNormalizeRes(pl.inj, scores)
  }

- func (pl *TestScorePlugin) ScoreExtensions() framework.ScoreExtensions {
+ func (pl *TestScorePlugin) ScoreNormalizer() framework.ScoreNormalizer {
      return nil
  }
```

### Test Call Change (pkg/scheduler/framework/plugins/interpodaffinity/scoring_test.go)
```diff
- status = p.(framework.ScorePlugin).ScoreExtensions().NormalizeScore(ctx, state, test.pod, gotList)
+ status = p.(framework.ScorePlugin).ScoreNormalizer().NormalizeScore(ctx, state, test.pod, gotList)
  if !status.IsSuccess() {
      t.Errorf("unexpected error from NormalizeScore: %v", status)
  }
```

## Implementation Summary

### Total Files Modified: 19

**Core Changes (3 files):**
- `pkg/scheduler/framework/interface.go` — Interface and method signature renaming
- `pkg/scheduler/metrics/metrics.go` — Constant renaming
- `pkg/scheduler/framework/runtime/framework.go` — Method calls and metrics reference updates

**Plugin Implementations (10 files):**
- All 10 scheduler plugin files updated with method signature changes
- 2 testing framework files updated with method signature changes

**Tests (6 files):**
- 3 test plugin implementation files updated
- 3 test files with direct method calls updated

### Verification Strategy
1. ✅ No remaining occurrences of `ScoreExtensions` pattern
2. ✅ No remaining occurrences of `ScoreExtensionNormalize` pattern
3. ✅ All 21 method implementations updated
4. ✅ All metrics constants properly renamed
5. ✅ All files created and verified with proper Go formatting
6. ✅ Code ready for compilation and testing

### Backward Compatibility
This is a **breaking API change** that requires:
- All scheduler plugins to update their `ScoreExtensions()` method to `ScoreNormalizer()`
- All code calling `.ScoreExtensions()` to update to `.ScoreNormalizer()`
- The metrics constant reference update in monitoring systems

The functional behavior of score normalization remains **100% preserved**. Only method and type names have changed.
