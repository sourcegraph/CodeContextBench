# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place updates for resources with provider-schema-defined sensitive attributes because sensitivity marks from the provider schema are not persisted in state files. When the value is read back during planning, it lacks these schema-defined marks. The plan comparison at `node_resource_abstract_instance.go:1208` detects a difference in sensitivity metadata (even though underlying values are identical), triggering an Update action instead of NoOp. Additionally, the JSON state output shows incomplete `sensitive_values` because the state file only records marks from sensitive variable references, not from the schema.

## Root Cause

The root cause is a **fundamental asymmetry in how sensitivity marks are handled between state persistence and runtime evaluation**:

1. **State persistence ignores schema-defined sensitive attributes**: When a resource is encoded to state via `ResourceInstanceObject.Encode()`, only marks present on the value object itself are saved to `AttrSensitivePaths`. These marks come from sensitive variable references (e.g., `var.db_password` marked as sensitive), but NOT from the provider schema's `Sensitive: true` declarations.

2. **Runtime evaluation compensates with dynamic mark application**: When values are read for expression evaluation in `GetResource()`, the evaluator re-applies schema-defined marks every time, creating marks that exist only in memory, not in persisted state.

3. **Plan comparison detects the mark difference**: When creating a plan, the code compares refreshed state (which has incomplete marks from state) against the planned state (which also has incomplete marks). However, the comparison logic at line 1208 can detect a sensitivity-only difference and incorrectly convert a NoOp to an Update.

## Evidence

### File: `internal/terraform/node_resource_abstract_instance.go`

**Refresh Path (lines 578-723)**:
- Line 625: Provider value is unmarked: `priorVal, priorPaths = priorVal.UnmarkDeepWithPaths()`
- Line 636-641: Provider's ReadResource() is called, returns response WITHOUT any marks
- Line 718-720: Only prior marks (from variable references) are re-applied, NOT schema marks:
  ```go
  if len(priorPaths) > 0 {
      ret.Value = ret.Value.MarkWithPaths(priorPaths)
  }
  ```

**Plan Path (lines 725-1268)**:
- Lines 868-869: Configuration and prior state are unmarked:
  ```go
  unmarkedConfigVal, unmarkedPaths := configValIgnored.UnmarkDeepWithPaths()
  unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()
  ```
- Line 902-910: Provider.PlanResourceChange() receives unmarked values, returns unmarked planned state
- Line 998-1000: Only configuration marks are re-applied:
  ```go
  if len(unmarkedPaths) > 0 {
      plannedNewVal = plannedNewVal.MarkWithPaths(unmarkedPaths)
  }
  ```
- **Line 1208 - THE PHANTOM DIFF TRIGGER**:
  ```go
  if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
      action = plans.Update
  }
  ```
  This line compares marks from the planned value (configuration marks) with marks from prior state (variable reference marks). If they differ due to schema-defined marks missing from `priorPaths`, it incorrectly triggers an Update.

### File: `internal/states/instance_object.go`

**State Encoding (lines 94-137)**:
- Line 98: Marks are extracted via UnmarkDeepWithPaths:
  ```go
  val, pvm := o.Value.UnmarkDeepWithPaths()
  ```
- Line 131: Only extracted marks are saved to state:
  ```go
  AttrSensitivePaths:  pvm,
  ```
  This `pvm` (PathValueMarks) contains ONLY marks that were on the value object, which come from sensitive variable references. Schema-defined marks are NOT on the value at this point.

### File: `internal/states/instance_object_src.go`

**State Decoding (lines 77-104)**:
- Lines 89-91: When decoding, marks are restored from state:
  ```go
  if os.AttrSensitivePaths != nil {
      val = val.MarkWithPaths(os.AttrSensitivePaths)
  }
  ```
  These are ONLY the marks that were in state (variable reference marks), not schema marks.

### File: `internal/terraform/evaluate.go`

**The Compensating Workaround (lines 714-723)**:
```go
// If our schema contains sensitive values, mark those as sensitive.
// Since decoding the instance object can also apply sensitivity marks,
// we must remove and combine those before remarking to avoid a double-
// mark error.
if schema.ContainsSensitive() {
    var marks []cty.PathValueMarks
    val, marks = val.UnmarkDeepWithPaths()
    marks = append(marks, schema.ValueMarks(val, nil)...)
    val = val.MarkWithPaths(marks)
}
instances[key] = val
```

This is the ONLY place in the codebase where schema-defined sensitive marks are re-applied to a value read from state. This happens ONLY during expression evaluation (GetResource), NOT during plan creation.

### File: `internal/command/jsonplan/values.go`

**JSON Output Manifestation (lines 212-235)**:
```go
// copy the marked After values so we can use these in marshalSensitiveValues
markedAfter := changeV.After

// ... unmark for JSON output ...
changeV.After, _ = changeV.After.UnmarkDeep()

// ... marshal values ...

s := jsonstate.SensitiveAsBool(markedAfter)
v, err := ctyjson.Marshal(s, s.Type())
resource.SensitiveValues = v
```

The `sensitive_values` in JSON output uses `markedAfter` from the change object. If the change object never had schema marks applied (because it came from the provider response without those marks), the JSON output will be incomplete.

## Affected Components

1. **`internal/terraform/node_resource_abstract_instance.go`** - Refresh and plan phases don't apply schema marks
2. **`internal/states/instance_object.go`** - State encoding loses schema mark information
3. **`internal/states/instance_object_src.go`** - State decoding only restores partial marks
4. **`internal/terraform/evaluate.go`** - Compensating workaround applies schema marks only at expression evaluation time
5. **`internal/terraform/marks.go`** - Utility functions for comparing and filtering marks
6. **`internal/command/jsonplan/values.go`** - JSON output generation relies on incomplete marks

## Causal Chain

1. **Initial state**: Resource with `password` attribute (marked sensitive in provider schema) is successfully applied
   - Value written to state via `Encode()` → only variable-reference marks are saved

2. **Immediate plan**: `terraform plan` is run with no configuration changes
   - Resource is refreshed via `refresh()` → provider returns unmarked value
   - Prior marks from state are re-applied (variable references only)
   - Planned value from provider is also unmarked
   - Configuration marks are applied to planned value

3. **Phantom diff detection**: Plan comparison at line 1208
   - `plannedNewVal` has configuration marks (unmarkedPaths)
   - `priorVal` has variable-reference marks (priorPaths)
   - If schema marks would differ, comparison detects "change" in sensitivity
   - Action incorrectly becomes Update instead of NoOp

4. **User observation**:
   - `terraform plan` shows "will be updated in-place" despite no actual value changes
   - `terraform show -json` has incomplete `sensitive_values` (missing schema-defined paths)
   - `terraform plan -refresh-only` still shows phantom changes
   - `terraform import` followed by `terraform plan` shows even more phantom updates

## Recommendation

### Fix Strategy

The root issue must be addressed at the state persistence layer. There are two approaches:

**Approach 1 (Preferred): Store schema-defined marks in state**
- Modify `Encode()` in `instance_object.go` to accept the provider schema and apply `schema.ValueMarks()` before calling `UnmarkDeepWithPaths()`
- This ensures `AttrSensitivePaths` in state contains ALL sensitive paths (both from references and schema)
- Eliminates the need for the compensating workaround in `evaluate.go`
- Makes state the single source of truth for sensitivity information
- **Impact**: Schema migrations required, potential state file format changes

**Approach 2: Apply schema marks in plan phase**
- Modify the `plan()` method in `node_resource_abstract_instance.go` to apply schema marks to planned values before comparison (similar to what GetResource does)
- This makes the plan comparison aware of schema-defined marks without changing state persistence
- Simpler scope than Approach 1, but maintains the asymmetry
- **Impact**: Phantom diffs might still occur if state lacks schema marks

### Diagnostic Steps

1. Compare `AttrSensitivePaths` in state file before and after refresh:
   - Should have expanded to include schema-defined paths if fixed

2. Verify plan comparison logic:
   - Add logging to `marksEqual()` call at line 1208 to show what marks are being compared

3. Check JSON output:
   - `terraform show -json` should include ALL sensitive paths (schema + variable reference)
   - Compare against provider schema to verify completeness

4. Test with `terraform plan -refresh-only`:
   - Should show no changes if only schema marks differ
