# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place update plans for resources with provider-schema-defined sensitive attributes because the state serialization layer only preserves sensitivity marks from sensitive variable references, but not from the provider schema's `Sensitive: true` declarations. During planning, the evaluator applies schema marks when reading from state for expression evaluation, but the plan layer doesn't, creating an asymmetry that triggers spurious update detection based on mark differences rather than value differences.

## Root Cause

The root cause spans three layers with an asymmetry between state storage and plan comparison:

1. **State Serialization Gap** (`internal/states/instance_object.go:94-137`): When encoding a resource instance to state, only marks from `UnmarkDeepWithPaths()` are captured in `AttrSensitivePaths`. These marks come exclusively from sensitive variable references. Provider schema-defined sensitivity marks are never included.

2. **Refresh Without Schema Marks** (`internal/terraform/node_resource_abstract_instance.go:578-723`): After the provider returns a refreshed state via `ReadResource()`, the refresh code (line 718-720) only re-applies marks from the prior state's `priorPaths`. Since the state file never stored schema-defined marks, they are lost after refresh.

3. **Plan Without Schema Marks on Planned Value** (`internal/terraform/node_resource_abstract_instance.go:850-1268`): When planning, the code unmarkes the config value to get `unmarkedPaths` (line 868), sends unmarked values to the provider (line 902-910), and re-applies `unmarkedPaths` to the planned value (line 999). However, schema-defined marks are never applied to the planned value.

4. **Asymmetric Evaluator Workaround** (`internal/terraform/evaluate.go:541-750`): The evaluator's `GetResource()` method (lines 689-695 and 714-723) compensates by applying schema marks when values are read FROM state for expression evaluation. This creates an asymmetry: values used in expressions have schema marks, but values in the plan do not.

5. **Phantom Diff Trigger** (`internal/terraform/node_resource_abstract_instance.go:1208`): The critical line that generates phantom updates:
   ```go
   if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
       action = plans.Update
   }
   ```
   When `plannedNewVal` (from provider response) lacks schema marks but `priorPaths` (from evaluator-marked state) has them, this check sees "different marks" and incorrectly changes NoOp to Update.

## Evidence

### File: `internal/states/instance_object.go`
- **Lines 94-137** (`Encode` method): Only captures and saves `pvm` (PathValueMarks) from `UnmarkDeepWithPaths()`:
  ```go
  val, pvm := o.Value.UnmarkDeepWithPaths()
  ...
  return &ResourceInstanceObjectSrc{
      AttrsJSON:          src,
      AttrSensitivePaths: pvm,  // ONLY from variable references
      ...
  }
  ```

### File: `internal/states/instance_object_src.go`
- **Lines 77-104** (`Decode` method): Re-applies only the stored marks, never adds schema marks:
  ```go
  if os.AttrSensitivePaths != nil {
      val = val.MarkWithPaths(os.AttrSensitivePaths)
  }
  ```

### File: `internal/terraform/node_resource_abstract_instance.go`
- **Lines 618-720** (refresh method): Unmarkes prior state, sends to provider, gets unmarked response, then only re-applies `priorPaths`:
  ```go
  var priorPaths []cty.PathValueMarks
  if priorVal.ContainsMarked() {
      priorVal, priorPaths = priorVal.UnmarkDeepWithPaths()
  }
  resp = provider.ReadResource(...)
  if len(priorPaths) > 0 {
      ret.Value = ret.Value.MarkWithPaths(priorPaths)  // Only prior marks
  }
  ```

- **Lines 868-870** (plan method): Captures `unmarkedPaths` from config (variable marks only):
  ```go
  unmarkedConfigVal, unmarkedPaths := configValIgnored.UnmarkDeepWithPaths()
  unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()
  ```

- **Lines 997-1000**: Re-applies config marks to planned value, but these don't include schema marks:
  ```go
  if len(unmarkedPaths) > 0 {
      plannedNewVal = plannedNewVal.MarkWithPaths(unmarkedPaths)
  }
  ```

- **Line 1208** (critical check that triggers phantom Update):
  ```go
  if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
      action = plans.Update  // PHANTOM UPDATE TRIGGERED HERE
  }
  ```

### File: `internal/terraform/evaluate.go`
- **Lines 689-695** (GetResource for planned state): Applies schema marks to planned value from change:
  ```go
  afterMarks := change.AfterValMarks
  if schema.ContainsSensitive() {
      afterMarks = append(afterMarks, schema.ValueMarks(val, nil)...)
  }
  instances[key] = val.MarkWithPaths(afterMarks)
  ```

- **Lines 714-723** (GetResource for current state): Applies schema marks to state value:
  ```go
  val, marks = val.UnmarkDeepWithPaths()
  if schema.ContainsSensitive() {
      marks = append(marks, schema.ValueMarks(val, nil)...)
  }
  val = val.MarkWithPaths(marks)
  instances[key] = val
  ```

### File: `internal/command/jsonstate/state.go`
- **Lines 402-406** (marshalResources for current instances): Correctly applies schema marks for JSON serialization:
  ```go
  value, marks := riObj.Value.UnmarkDeepWithPaths()
  if schema.ContainsSensitive() {
      marks = append(marks, schema.ValueMarks(value, nil)...)
  }
  s := SensitiveAsBool(value.MarkWithPaths(marks))
  ```

### File: `internal/command/jsonplan/plan.go`
- **Lines 117-123**: Documents that BeforeSensitive and AfterSensitive should represent sensitivity, but the data source for these comes from incomplete state marks.

## Affected Components

1. **`internal/terraform/node_resource_abstract_instance.go`**
   - `refresh()` method: Loses schema marks after provider call
   - `plan()` method: Never applies schema marks to planned values, triggers phantom update at line 1208

2. **`internal/states/instance_object.go` and `instance_object_src.go`**
   - `Encode()` method: Only captures variable reference marks
   - `Decode()` method: Only restores variable reference marks

3. **`internal/terraform/evaluate.go`**
   - `GetResource()` method: Only place where schema marks are applied during graph evaluation, creating compensating asymmetry

4. **`internal/command/jsonstate/state.go` and `jsonplan/plan.go`**
   - Manifestation layer that produces incomplete `sensitive_values` and `*_sensitive` fields in JSON output

5. **State storage layer** (`internal/states/`)
   - ResourceInstanceObject and ResourceInstanceObjectSrc: No storage mechanism for schema-defined sensitivity

## Causal Chain

1. **Provider returns response** → Provider never marks values, response is unmarked
2. **Refresh applies prior marks only** → `priorPaths` from state only has variable marks (schema marks were never stored)
3. **Marks lost after refresh** → Refreshed state lacks schema marks that came from the schema
4. **Plan sends unmarked values to provider** → Config marks extracted, but only variable marks
5. **Planned value lacks schema marks** → Re-applies only `unmarkedPaths` (variable marks)
6. **Evaluator reads state with schema marks** → `GetResource()` compensates by adding schema marks for expressions
7. **Asymmetry in mark comparison** → Plan value has NO schema marks, but priorPaths (from evaluator) HAS schema marks
8. **Mark equality check fails** → Line 1208 sees different marks and changes NoOp → Update
9. **Phantom update generated** → Plan shows resource "will be updated in-place" with no actual value changes
10. **Incomplete JSON sensitivity** → JSON output has `sensitive_values` missing schema-defined paths because state never stored them

## Recommendation

### Fix Strategy

The core fix requires making sensitivity mark handling explicit and symmetric:

1. **Store schema-defined marks in state** (`internal/states/instance_object.go`):
   - During `Encode()`, after capturing variable reference marks via `UnmarkDeepWithPaths()`, the code should iterate through the schema and add paths for schema-defined sensitive attributes before storing in `AttrSensitivePaths`

2. **Apply schema marks during state decode** (`internal/states/instance_object_src.go`):
   - During `Decode()`, after re-applying stored marks, the code should NOT apply schema marks at this layer (schema doesn't exist here)
   - Instead, schema marks should be applied only at the point of use

3. **Move schema mark application to consistent location** (`internal/terraform/node_resource_abstract_instance.go`):
   - After `refresh()` returns, explicitly apply schema marks to the refreshed value
   - After `plan()` processes the planned value, explicitly apply schema marks before comparison
   - Ensure schema marks are applied BOTH to planned values AND prior values before the mark equality check at line 1208

4. **Remove evaluator workaround** (optional, after fixing above):
   - Once marks are properly maintained throughout the flow, the compensating logic in `evaluate.go` lines 691-693 and 718-723 becomes redundant
   - However, this layer should remain for defensive purposes

### Diagnostic Steps

1. Enable TRACE logging for mark operations by adding logs at:
   - `refresh()` return point (line 722)
   - `plan()` prior value unmarking (line 869)
   - `plan()` planned value re-marking (line 999)
   - Mark comparison check (line 1208)

2. Create test case:
   - Schema with `password` marked `Sensitive: true`
   - Config using literal value (not variable)
   - Run `apply` successfully
   - Run `plan` again immediately
   - Verify plan shows NoOp, not Update
   - Verify `terraform show -json` shows correct `sensitive_values` with schema marks included

3. Trace mark flow:
   - Starting with refreshed state (after ReadResource)
   - Through plan evaluation
   - Into mark comparison
   - To final change action

The key insight is that sensitivity is a schema property, not just a variable property, and must be preserved independently throughout all state transformations and plan comparisons.
