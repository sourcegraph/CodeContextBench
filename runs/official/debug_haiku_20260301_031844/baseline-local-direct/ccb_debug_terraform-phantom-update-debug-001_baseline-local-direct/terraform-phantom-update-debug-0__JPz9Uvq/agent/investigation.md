# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place updates for resources with provider-schema-defined sensitive attributes because the plan comparison logic detects a mismatch in sensitivity marks, not attribute values. The root cause is an asymmetry in how and when sensitivity marks from the provider schema are applied: they are omitted from state serialization, stored state never includes them, but the plan comparison logic expects them to match against configuration-based marks.

## Root Cause

The fundamental issue is a **three-layer mark application gap** in the code:

1. **State Storage Gap**: When state is persisted to disk (`internal/states/instance_object.go`), the Encode method only extracts marks that already exist on the value (line 98). Provider-schema-defined sensitive attributes are never marked on values before state is written, so these marks are lost at serialization time.

2. **State Retrieval Gap**: When state is deserialized from disk (`internal/states/instance_object_src.go` lines 77-104), the Decode method only re-applies marks from `AttrSensitivePaths` which come from the state file. These paths contain only marks from sensitive *variable references*, not from the provider schema's `Sensitive: true` declarations.

3. **Plan Comparison Gap**: The plan function (`internal/terraform/node_resource_abstract_instance.go` lines 1208-1210) compares marks using logic that assumes both the prior state marks and planned state marks are complete. It doesn't account for the fact that prior state marks are incomplete (missing schema-based marks).

The evaluator's `GetResource()` method (`internal/terraform/evaluate.go` lines 714-723) was introduced as a **compensating workaround** to apply schema marks when reading values for expression evaluation. However, this happens *after* the plan has already been created and written, producing an asymmetry.

## Evidence

### 1. State Serialization (No Schema Marks Applied)

**File**: `internal/states/instance_object.go:94-137` (Encode method)

```go
func (o *ResourceInstanceObject) Encode(ty cty.Type, schemaVersion uint64) (*ResourceInstanceObjectSrc, error) {
    // Line 98: Extract marks from the value as-is
    val, pvm := o.Value.UnmarkDeepWithPaths()

    // ...

    // Line 131: Store only the marks extracted above
    return &ResourceInstanceObjectSrc{
        SchemaVersion:       schemaVersion,
        AttrsJSON:           src,
        AttrSensitivePaths:  pvm,  // Only includes variable-based marks!
        Private:             o.Private,
        Status:              o.Status,
        Dependencies:        dependencies,
        CreateBeforeDestroy: o.CreateBeforeDestroy,
    }, nil
}
```

**Key Issue**: The value `o.Value` is never marked with schema-defined sensitive paths before extraction. Those marks are only applied during expression evaluation, not during state persistence.

### 2. State Deserialization (Incomplete Marks Re-applied)

**File**: `internal/states/instance_object_src.go:77-104` (Decode method)

```go
func (os *ResourceInstanceObjectSrc) Decode(ty cty.Type) (*ResourceInstanceObject, error) {
    var val cty.Value
    if os.AttrsFlat != nil {
        // ...
    } else {
        val, err = ctyjson.Unmarshal(os.AttrsJSON, ty)
        // Lines 89-90: Only apply stored marks (from variables, not schema)
        if os.AttrSensitivePaths != nil {
            val = val.MarkWithPaths(os.AttrSensitivePaths)
        }
        if err != nil {
            return nil, err
        }
    }
    return &ResourceInstanceObject{
        Value:               val,
        Status:              os.Status,
        Dependencies:        os.Dependencies,
        Private:             os.Private,
        CreateBeforeDestroy: os.CreateBeforeDestroy,
    }, nil
}
```

**Key Issue**: The Decode method has no access to the provider schema and cannot apply schema-defined sensitive marks.

### 3. State Reading During Plan

**File**: `internal/terraform/node_resource_abstract.go:438-475` (readResourceInstanceState method)

```go
func (n *NodeAbstractResource) readResourceInstanceState(ctx EvalContext, addr addrs.AbsResourceInstance) (*states.ResourceInstanceObject, tfdiags.Diagnostics) {
    // ...
    src := ctx.State().ResourceInstanceObject(addr, addrs.NotDeposed)  // Line 448
    // ...
    obj, err := src.Decode(schema.ImpliedType())  // Line 469
    // Decode is called with schema, but schema marks are NOT applied here!
    return obj, diags
}
```

**Key Issue**: Although `schema` is available (line 455), it is not used to apply sensitivity marks during the decode operation.

### 4. Plan Comparison Detecting Mark Mismatch

**File**: `internal/terraform/node_resource_abstract_instance.go:868-870, 995-1000, 1208-1210` (plan method)

```go
// Line 869: Extract marks from prior state
unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()

// ...

// Lines 998-1000: Re-apply marks from config (contains config variable marks)
if len(unmarkedPaths) > 0 {
    plannedNewVal = plannedNewVal.MarkWithPaths(unmarkedPaths)
}

// Lines 1208-1210: THE PHANTOM UPDATE TRIGGER
if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
    action = plans.Update  // Changed from NoOp to Update!
}
```

**Key Issue**: This comparison assumes:
- `plannedNewVal` has the correct set of marks (config marks via `unmarkedPaths`)
- `priorPaths` extracted from prior state has all relevant marks

However, `priorPaths` is incomplete because it comes from a state that never had schema marks applied.

### 5. Evaluator's Compensating Workaround

**File**: `internal/terraform/evaluate.go:665-696, 714-723` (GetResource method)

```go
// Lines 691-692: Schema marks applied during evaluation of PlannedState
if schema.ContainsSensitive() {
    afterMarks = append(afterMarks, schema.ValueMarks(val, nil)...)
}
instances[key] = val.MarkWithPaths(afterMarks)

// Lines 718-723: Schema marks applied during evaluation of actual state
if schema.ContainsSensitive() {
    var marks []cty.PathValueMarks
    val, marks = val.UnmarkDeepWithPaths()
    marks = append(marks, schema.ValueMarks(val, nil)...)
    val = val.MarkWithPaths(marks)
}
instances[key] = val
```

**Key Issue**: This is a **defensive layer** added to handle the missing schema marks when evaluating expressions. It works for expression evaluation but doesn't help the plan comparison, which happens earlier.

### 6. JSON Output Manifestation

**File**: `internal/command/jsonstate/state.go:402-411` (marshalResources method)

```go
value, marks := riObj.Value.UnmarkDeepWithPaths()
if schema.ContainsSensitive() {
    marks = append(marks, schema.ValueMarks(value, nil)...)
}
s := SensitiveAsBool(value.MarkWithPaths(marks))
v, err := ctyjson.Marshal(s, s.Type())
if err != nil {
    return nil, err
}
current.SensitiveValues = v
```

**Key Issue**: The JSON output correctly applies schema marks (line 404) when marshaling for display. This produces the **correct** `sensitive_values` in `terraform show -json`, but this mark application happens too late—after the plan has already been created with phantom updates.

## Affected Components

1. **`internal/terraform/node_resource_abstract_instance.go`**: Plan comparison logic (lines 868-870, 995-1000, 1208-1210) that triggers phantom updates when mark sets differ
2. **`internal/states/instance_object.go`**: State encoding (lines 94-137) that omits schema-based marks during serialization
3. **`internal/states/instance_object_src.go`**: State decoding (lines 77-104) that cannot apply schema marks without provider schema
4. **`internal/terraform/node_resource_abstract.go`**: State reading (lines 438-475) that doesn't apply schema marks to decoded values
5. **`internal/terraform/evaluate.go`**: Expression evaluator (lines 714-723) that applies schema marks, but only after plan creation
6. **`internal/command/jsonstate/state.go`**: JSON output generation (lines 402-411) that correctly applies schema marks for display

## Causal Chain

1. **Provider response** → Provider returns resource attributes without any marks (marks are Terraform's responsibility)
2. **State encoding** → Value is encoded and written to state WITHOUT schema marks applied (they've never been applied to the value)
3. **State file written** → State file contains `sensitive_attributes` with only marks from variable references, NOT schema declarations
4. **State loading** → `readResourceInstanceState()` reads from state, decodes it, applies only stored marks (variable marks)
5. **Prior state with incomplete marks** → Prior value has no schema marks, only variable marks in `priorPaths`
6. **Config evaluation** → Configuration is evaluated, creating `unmarkedPaths` with variable marks from config expressions
7. **Planned value marking** → Planned value from provider gets marked with `unmarkedPaths` (config variable marks)
8. **Mark comparison** → Plan logic compares `plannedNewVal` marks (config marks + schema marks??? NO—only config marks!) against `priorPaths` (only variable marks)
9. **Asymmetry detected** → Mark sets differ: planned has some marks from config, prior has different marks from state
10. **Phantom update** → Logic changes action from NoOp to Update because mark sets don't match, even though values are identical
11. **Evaluator compensation** → Later, `GetResource()` applies schema marks to values when evaluating expressions, but the plan is already created
12. **JSON output correct** → When generating JSON output, schema marks are properly applied (lines 402-411), but plan output shows phantom change

## Recommendation

**Fix Strategy**: Apply schema-defined sensitive marks to the prior state's value after it is decoded but before it is used in the plan comparison.

The fix should be in `readResourceInstanceState()` in `internal/terraform/node_resource_abstract.go`, immediately after calling `Decode()`:

1. After line 469 (`obj, err := src.Decode(schema.ImpliedType())`), check if schema declares sensitive attributes
2. If `schema.ContainsSensitive()` is true, apply schema marks to `obj.Value` using `schema.ValueMarks(unmarkedValue, nil)`
3. This will ensure `priorPaths` extracted in the plan function includes both variable marks AND schema marks, matching the marks on `plannedNewVal`

**Alternative Approach** (Defensive): Modify the mark comparison logic at line 1208 to account for schema-defined sensitive attributes by:
1. Extracting what schema marks *should* be applied to both `plannedNewVal` and `priorVal`
2. Normalizing both mark sets to include schema marks before comparison
3. This ensures the comparison is "apples-to-apples" with complete mark sets

**Diagnostic Steps** to verify the issue:
1. Enable detailed logging for mark extraction and comparison in plan logic (node_resource_abstract_instance.go:869 and 1208)
2. Log the actual mark paths in `priorPaths` and filtered `plannedNewVal` marks
3. Verify that schema-defined sensitive attributes are missing from `priorPaths`
4. Confirm that the marks would match if schema marks were applied to prior state
