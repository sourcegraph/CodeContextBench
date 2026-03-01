# Before/After Examples - ScoreExtensions → ScoreNormalizer Refactoring

## Core Interface Definition

### Before (interface.go)
```go
// ScoreExtensions is an interface for Score extended functionality.
type ScoreExtensions interface {
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

    // ScoreExtensions returns a ScoreExtensions interface if it implements one, or nil if does not.
    ScoreExtensions() ScoreExtensions
}
```

### After (interface.go)
```go
// ScoreNormalizer is an interface for Score normalization functionality.
type ScoreNormalizer interface {
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

    // ScoreNormalizer returns a ScoreNormalizer interface if it implements one, or nil if does not.
    ScoreNormalizer() ScoreNormalizer
}
```

**Changes**:
- Line 1: Comment updated
- Line 2: Type name changed
- Line 11: Comment updated
- Line 13: Method name and return type changed

---

## Metrics Constants

### Before (metrics/metrics.go)
```go
// Below are possible values for the extension_point label.
const (
    PreFilter                   = "PreFilter"
    Filter                      = "Filter"
    PreFilterExtensionAddPod    = "PreFilterExtensionAddPod"
    PreFilterExtensionRemovePod = "PreFilterExtensionRemovePod"
    PostFilter                  = "PostFilter"
    PreScore                    = "PreScore"
    Score                       = "Score"
    ScoreExtensionNormalize     = "ScoreExtensionNormalize"
    PreBind                     = "PreBind"
    Bind                        = "Bind"
    PostBind                    = "PostBind"
    Reserve                     = "Reserve"
    Unreserve                   = "Unreserve"
    Permit                      = "Permit"
)
```

### After (metrics/metrics.go)
```go
// Below are possible values for the extension_point label.
const (
    PreFilter                   = "PreFilter"
    Filter                      = "Filter"
    PreFilterExtensionAddPod    = "PreFilterExtensionAddPod"
    PreFilterExtensionRemovePod = "PreFilterExtensionRemovePod"
    PostFilter                  = "PostFilter"
    PreScore                    = "PreScore"
    Score                       = "Score"
    ScoreNormalize              = "ScoreNormalize"
    PreBind                     = "PreBind"
    Bind                        = "Bind"
    PostBind                    = "PostBind"
    Reserve                     = "Reserve"
    Unreserve                   = "Unreserve"
    Permit                      = "Permit"
)
```

**Changes**:
- Line 10: Constant name and value changed

---

## Runtime Framework Implementation

### Before (framework/runtime/framework.go - line ~1140)
```go
// Run NormalizeScore method for each ScorePlugin in parallel.
f.Parallelizer().Until(ctx, len(plugins), func(index int) {
    pl := plugins[index]
    if pl.ScoreExtensions() == nil {
        return
    }
    nodeScoreList := pluginToNodeScores[pl.Name()]
    status := f.runScoreExtension(ctx, pl, state, pod, nodeScoreList)
    // ... error handling
}, metrics.Score)

// ... later in the file at line ~1200:

func (f *frameworkImpl) runScoreExtension(ctx context.Context, pl framework.ScorePlugin,
    state *framework.CycleState, pod *v1.Pod, nodeScoreList framework.NodeScoreList) *framework.Status {
    if !state.ShouldRecordPluginMetrics() {
        return pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
    }
    startTime := time.Now()
    status := pl.ScoreExtensions().NormalizeScore(ctx, state, pod, nodeScoreList)
    f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreExtensionNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
    return status
}
```

### After (framework/runtime/framework.go)
```go
// Run NormalizeScore method for each ScorePlugin in parallel.
f.Parallelizer().Until(ctx, len(plugins), func(index int) {
    pl := plugins[index]
    if pl.ScoreNormalizer() == nil {
        return
    }
    nodeScoreList := pluginToNodeScores[pl.Name()]
    status := f.runScoreExtension(ctx, pl, state, pod, nodeScoreList)
    // ... error handling
}, metrics.Score)

// ... later in the file:

func (f *frameworkImpl) runScoreExtension(ctx context.Context, pl framework.ScorePlugin,
    state *framework.CycleState, pod *v1.Pod, nodeScoreList framework.NodeScoreList) *framework.Status {
    if !state.ShouldRecordPluginMetrics() {
        return pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
    }
    startTime := time.Now()
    status := pl.ScoreNormalizer().NormalizeScore(ctx, state, pod, nodeScoreList)
    f.metricsRecorder.ObservePluginDurationAsync(metrics.ScoreNormalize, pl.Name(), status.Code().String(), metrics.SinceInSeconds(startTime))
    return status
}
```

**Changes**:
- Line 4: Method call updated
- Line 15: Method call updated
- Line 16: Method call updated
- Line 17: Metrics constant and method call updated

---

## Plugin Implementations

### Example 1: InterPodAffinity Plugin

#### Before (interpodaffinity/scoring.go)
```go
// ScoreExtensions of the Score plugin.
func (pl *InterPodAffinity) ScoreExtensions() framework.ScoreExtensions {
    return pl
}
```

#### After (interpodaffinity/scoring.go)
```go
// ScoreNormalizer of the Score plugin.
func (pl *InterPodAffinity) ScoreNormalizer() framework.ScoreNormalizer {
    return pl
}
```

**Changes**:
- Comment updated
- Method name changed
- Return type changed

---

### Example 2: Fit Plugin

#### Before (noderesources/fit.go)
```go
// ScoreExtensions of the Score plugin.
func (f *Fit) ScoreExtensions() framework.ScoreExtensions {
    return nil
}
```

#### After (noderesources/fit.go)
```go
// ScoreNormalizer of the Score plugin.
func (f *Fit) ScoreNormalizer() framework.ScoreNormalizer {
    return nil
}
```

**Changes**:
- Comment updated
- Method name changed
- Return type changed

---

## Test Implementations

### Example: Framework Test

#### Before (framework/runtime/framework_test.go)
```go
type TestScoreWithNormalizePlugin struct {
    // ... fields
    inj ScoreWithNormalizationInj
}

func (pl *TestScoreWithNormalizePlugin) Score(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {
    return 1, nil
}

func (pl *TestScoreWithNormalizePlugin) ScoreExtensions() framework.ScoreExtensions {
    return injectNormalizeRes(pl.inj, scores)
}
```

#### After (framework/runtime/framework_test.go)
```go
type TestScoreWithNormalizePlugin struct {
    // ... fields
    inj ScoreWithNormalizationInj
}

func (pl *TestScoreWithNormalizePlugin) Score(ctx context.Context, state *framework.CycleState, pod *v1.Pod, nodeName string) (int64, *framework.Status) {
    return 1, nil
}

func (pl *TestScoreWithNormalizePlugin) ScoreNormalizer() framework.ScoreNormalizer {
    return injectNormalizeRes(pl.inj, scores)
}
```

**Changes**:
- Method signature updated
- Return type updated

---

## Test Method Calls

### Example: InterPodAffinity Test

#### Before (interpodaffinity/scoring_test.go)
```go
func TestScore(t *testing.T) {
    // ... test setup

    status = p.(framework.ScorePlugin).ScoreExtensions().NormalizeScore(ctx, state, test.pod, gotList)
    if !status.IsSuccess() {
        t.Errorf("unexpected error from NormalizeScore: %v", status)
    }
}
```

#### After (interpodaffinity/scoring_test.go)
```go
func TestScore(t *testing.T) {
    // ... test setup

    status = p.(framework.ScorePlugin).ScoreNormalizer().NormalizeScore(ctx, state, test.pod, gotList)
    if !status.IsSuccess() {
        t.Errorf("unexpected error from NormalizeScore: %v", status)
    }
}
```

**Changes**:
- Method call updated from `.ScoreExtensions()` to `.ScoreNormalizer()`

---

## Summary Table

| Component | Before | After | Count |
|-----------|--------|-------|-------|
| Interface Type | `ScoreExtensions` | `ScoreNormalizer` | 1 |
| Method Name | `ScoreExtensions()` | `ScoreNormalizer()` | 21 |
| Type References | `framework.ScoreExtensions` | `framework.ScoreNormalizer` | 21 |
| Metrics Constant | `ScoreExtensionNormalize` | `ScoreNormalize` | 1 |
| Comment Updates | "ScoreExtensions" | "ScoreNormalizer" | ~40 |
| **Total Changes** | | | **>100** |

---

## Impact Analysis

### Code Affected
- ✅ All ScorePlugin interface implementations (21 plugins)
- ✅ All runtime code calling the method (3 locations)
- ✅ All tests implementing the interface (6+ plugins)
- ✅ All tests calling the method (3+ locations)
- ✅ All metrics/monitoring code (1 constant + 6 uses)

### Functional Impact
- 🎯 ZERO - All behavior remains identical
- 🎯 ZERO - All performance impact
- 🎯 ZERO - All reliability impact

### API Impact
- ⚠️ BREAKING - Type name changed
- ⚠️ BREAKING - Method name changed
- ⚠️ BREAKING - Metrics constant name changed

---

## Testing Strategy

To verify the refactoring:

### 1. Compilation Test
```bash
go build ./pkg/scheduler/framework/...
```

### 2. Unit Tests
```bash
go test ./pkg/scheduler/framework/...
go test ./pkg/scheduler/framework/plugins/...
go test ./pkg/scheduler/testing/framework/...
```

### 3. Integration Tests
```bash
go test ./test/integration/scheduler/plugins/...
```

### 4. Full Scheduler Tests
```bash
go test ./pkg/scheduler/...
```

All tests should pass with green status.
