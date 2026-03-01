# Refactoring: Rename ScoreExtensions to ScoreNormalizer

## Files Examined

### Core Interface Definition
- **pkg/scheduler/framework/interface.go** — Contains the `ScoreExtensions` interface definition (lines 482-488) and the `ScorePlugin` interface that returns it (lines 490-501). This is the primary definition that needs to be renamed.

### Metrics Constants
- **pkg/scheduler/metrics/metrics.go** — Defines the `ScoreExtensionNormalize` metrics constant (line 50) used for recording plugin execution metrics.

### Runtime Framework
- **pkg/scheduler/framework/runtime/framework.go** — Core scheduler runtime that:
  - Calls `ScoreExtensions()` method to check if plugin implements normalization (line 1141)
  - Calls `ScoreExtensions().NormalizeScore()` to execute the normalization (lines 1202, 1205)
  - Uses `metrics.ScoreExtensionNormalize` constant for metrics recording (line 1206)

### Score Plugin Implementations (10 production plugins + 3 test plugins)
- **pkg/scheduler/framework/plugins/imagelocality/image_locality.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil (lines 72-75)
- **pkg/scheduler/framework/plugins/interpodaffinity/scoring.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning self (lines 299-302)
- **pkg/scheduler/framework/plugins/nodeaffinity/node_affinity.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning self (lines 276-279)
- **pkg/scheduler/framework/plugins/noderesources/balanced_allocation.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil (lines 111-114)
- **pkg/scheduler/framework/plugins/noderesources/fit.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil (lines 95-98)
- **pkg/scheduler/framework/plugins/podtopologyspread/scoring.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning self (lines 268-271)
- **pkg/scheduler/framework/plugins/tainttoleration/taint_toleration.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning self (lines 161-164)
- **pkg/scheduler/framework/plugins/volumebinding/volume_binding.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil (lines 324-327)
- **pkg/scheduler/testing/framework/fake_extender.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil (lines 135-138)
- **pkg/scheduler/testing/framework/fake_plugins.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil (lines 264-267)
- **test/integration/scheduler/plugins/plugins_test.go** — Implements `ScoreExtensions() framework.ScoreExtensions` returning nil/self (lines 343, 367)

### Test Files
- **pkg/scheduler/framework/runtime/framework_test.go** — Test plugin implementations (lines 134, 156, 196)
- **pkg/scheduler/framework/plugins/interpodaffinity/scoring_test.go** — Test calls to `ScoreExtensions().NormalizeScore()` (lines 810, 973)
- **pkg/scheduler/framework/plugins/nodeaffinity/node_affinity_test.go** — Test call to `ScoreExtensions().NormalizeScore()` (line 1223)
- **pkg/scheduler/framework/plugins/tainttoleration/taint_toleration_test.go** — Test call to `ScoreExtensions().NormalizeScore()` (line 259)
- **pkg/scheduler/schedule_one_test.go** — Test plugin implementations (lines 173, 197, 220, 257, 371)
- **test/integration/scheduler/plugins/plugins_test.go** — Test plugin implementations (lines 343, 367)

## Dependency Chain

1. **Definition**: `pkg/scheduler/framework/interface.go` (lines 482-488)
   - Defines the `ScoreExtensions` interface with a single `NormalizeScore()` method

2. **Interface Reference**: `pkg/scheduler/framework/interface.go` (lines 490-501)
   - The `ScorePlugin` interface's `ScoreExtensions()` method returns this type

3. **Direct Uses - Implementations**:
   - 10 plugin files implement the `ScoreExtensions()` method
   - 2 testing framework files implement it
   - 1 test file implements it

4. **Direct Uses - Runtime Framework**:
   - `pkg/scheduler/framework/runtime/framework.go` calls `pl.ScoreExtensions()` to get the interface
   - `pkg/scheduler/framework/runtime/framework.go` calls `pl.ScoreExtensions().NormalizeScore()` to execute

5. **Metrics Usage**:
   - `pkg/scheduler/framework/runtime/framework.go` uses `metrics.ScoreExtensionNormalize` constant
   - `pkg/scheduler/metrics/metrics.go` defines the constant

6. **Test Direct Uses**:
   - 4 test files call `ScoreExtensions().NormalizeScore()` directly
   - 6 test files implement the `ScoreExtensions()` method

## Code Changes

### 1. pkg/scheduler/framework/interface.go

```diff
-// ScoreExtensions is an interface for Score extended functionality.
-type ScoreExtensions interface {
+// ScoreNormalizer is an interface for Score normalization functionality.
+type ScoreNormalizer interface {
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

-	// ScoreExtensions returns a ScoreExtensions interface if it implements one, or nil if does not.
-	ScoreExtensions() ScoreExtensions
+	// ScoreNormalizer returns a ScoreNormalizer interface if it implements one, or nil if does not.
+	ScoreNormalizer() ScoreNormalizer
 }
```

### 2. pkg/scheduler/metrics/metrics.go

```diff
 // Below are possible values for the extension_point label.
 const (
 	PreFilter                   = "PreFilter"
 	Filter                      = "Filter"
 	PreFilterExtensionAddPod    = "PreFilterExtensionAddPod"
 	PreFilterExtensionRemovePod = "PreFilterExtensionRemovePod"
 	PostFilter                  = "PostFilter"
 	PreScore                    = "PreScore"
 	Score                       = "Score"
-	ScoreExtensionNormalize     = "ScoreExtensionNormalize"
+	ScoreNormalize              = "ScoreNormalize"
 	PreBind                     = "PreBind"
 	Bind                        = "Bind"
 	PostBind                    = "PostBind"
 	Reserve                     = "Reserve"
 	Unreserve                   = "Unreserve"
 	Permit                      = "Permit"
 )
```

### 3. pkg/scheduler/framework/runtime/framework.go

```diff
 	// Run NormalizeScore method for each ScorePlugin in parallel.
 	f.Parallelizer().Until(ctx, len(plugins), func(index int) {
 		pl := plugins[index]
-		if pl.ScoreExtensions() == nil {
+		if pl.ScoreNormalizer() == nil {
 			return
 		}
 		nodeScoreList := pluginToNodeScores[pl.Name()]
 		status := f.runScoreExtension(ctx, pl, state, pod, nodeScoreList)
 		if !status.IsSuccess() {
 			err := fmt.Errorf("plugin %q failed with: %w", pl.Name(), status.AsError())
 			errCh.SendErrorWithCancel(err, cancel)
 			return
 		}
 	}, metrics.Score)
 	if err := errCh.ReceiveError(); err != nil {
-		return nil, framework.AsStatus(fmt.Errorf("running Normalize on Score plugins: %w", err))
+		return nil, framework.AsStatus(fmt.Errorf("running Normalize on Score plugins: %w", err))
 	}

 ...

 func (f *frameworkImpl) runScoreExtension(ctx context.Context, pl framework.ScorePlugin, state *framework.CycleState, pod *v1.Pod, nodeScoreList framework.NodeScoreList) *framework.Status {
 	if !state.ShouldRecordPluginMetrics() {
-		return pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
+		return pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
 	}
 	startTime := time.Now()
-	status := pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
-	f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreExtensionNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
+	status := pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
+	f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
 	return status
 }
```

### 4. Plugin Implementation Files (10 files)

**Pattern for all 10 plugin files - change method signature and return type:**

```diff
-// ScoreExtensions of the Score plugin.
-func (pl *PluginName) ScoreExtensions() framework.ScoreExtensions {
+// ScoreNormalizer of the Score plugin.
+func (pl *PluginName) ScoreNormalizer() framework.ScoreNormalizer {
 	return nil  // or return pl for plugins that implement normalization
 }
```

**Files to update (production plugins):**
- pkg/scheduler/framework/plugins/imagelocality/image_locality.go (lines 72-75)
- pkg/scheduler/framework/plugins/interpodaffinity/scoring.go (lines 299-302)
- pkg/scheduler/framework/plugins/nodeaffinity/node_affinity.go (lines 276-279)
- pkg/scheduler/framework/plugins/noderesources/balanced_allocation.go (lines 111-114)
- pkg/scheduler/framework/plugins/noderesources/fit.go (lines 95-98)
- pkg/scheduler/framework/plugins/podtopologyspread/scoring.go (lines 268-271)
- pkg/scheduler/framework/plugins/tainttoleration/taint_toleration.go (lines 161-164)
- pkg/scheduler/framework/plugins/volumebinding/volume_binding.go (lines 324-327)

**Files to update (test plugins):**
- pkg/scheduler/testing/framework/fake_extender.go (lines 135-138)
- pkg/scheduler/testing/framework/fake_plugins.go (lines 264-267)
- test/integration/scheduler/plugins/plugins_test.go (lines 343, 367)

### 5. Test Files

**Pattern for test implementations - change method signature and return type:**

```diff
-func (pl *TestPluginName) ScoreExtensions() framework.ScoreExtensions {
+func (pl *TestPluginName) ScoreNormalizer() framework.ScoreNormalizer {
 	return nil  // or return pl for plugins that implement normalization
 }
```

**Pattern for test calls - change method call:**

```diff
-status = p.(framework.ScorePlugin).ScoreExtensions().NormalizeScore(ctx, state, test.pod, gotList)
+status = p.(framework.ScorePlugin).ScoreNormalizer().NormalizeScore(ctx, state, test.pod, gotList)
```

**Files and affected lines (by modification type):**

*Plugin implementations in test files:*
- pkg/scheduler/framework/runtime/framework_test.go (lines 134, 156, 196)
- pkg/scheduler/schedule_one_test.go (lines 173, 197, 220, 257, 371)
- test/integration/scheduler/plugins/plugins_test.go (lines 343, 367)

*Direct method calls in test files:*
- pkg/scheduler/framework/plugins/interpodaffinity/scoring_test.go (lines 810, 973)
- pkg/scheduler/framework/plugins/nodeaffinity/node_affinity_test.go (line 1223)
- pkg/scheduler/framework/plugins/tainttoleration/taint_toleration_test.go (line 259)

## Analysis

### Refactoring Strategy

This refactoring improves code clarity by:
1. **Better naming**: `ScoreNormalizer` is more specific than `ScoreExtensions` - it clearly indicates the interface is for score normalization, not generic extensions.
2. **Single responsibility**: The interface has only one method (`NormalizeScore`), making `ScoreNormalizer` a more accurate name.
3. **Consistency**: The renamed metric constant `ScoreNormalize` is more concise and mirrors the plugin method name pattern.

### Scope and Affected Areas

**Total files requiring changes: 23**
- 1 interface definition file
- 1 metrics file
- 1 runtime framework file
- 11 plugin implementation files (10 production + 1 test)
- 10 test files

**Changes are straightforward:**
- Interface/type renames: 1 interface definition + 11 return type declarations = 12 locations
- Method renames: 12 method implementations + 1 interface definition = 13 locations
- Method calls: 3 call sites in framework + 4 test call sites = 7 locations
- Metrics constant: 2 locations (definition + 1 usage)
- Comments: 11 method comment updates

### Total Changes Required: ~45 individual text replacements across 23 files

### Verification Approach

1. **Compilation verification**: The Go compiler will catch any missed references to old names.
2. **Interface satisfaction**: All plugin implementations must implement the new `ScoreNormalizer()` method signature.
3. **Test execution**: All existing tests should pass without modification once the refactoring is complete.
4. **No behavioral changes**: This is a pure refactoring - functionality remains identical.

### Risk Assessment

**Low Risk:**
- This is a purely syntactic change with no behavioral impact.
- The Go type system will catch all missed conversions.
- All changes are localized to scheduler framework code.
- No external API changes (all changes are internal to pkg/scheduler).

### Implementation Order

Recommended order to minimize compilation errors:
1. Update interface definition (interface.go)
2. Update metrics constant (metrics.go)
3. Update all plugin implementations (11 files: 10 production + 1 test framework)
4. Update runtime framework (framework.go)
5. Update test files (9 additional test files)

This order ensures that once the interface is defined with its new signature, all implementations and callers will properly report compilation errors that need to be fixed.
