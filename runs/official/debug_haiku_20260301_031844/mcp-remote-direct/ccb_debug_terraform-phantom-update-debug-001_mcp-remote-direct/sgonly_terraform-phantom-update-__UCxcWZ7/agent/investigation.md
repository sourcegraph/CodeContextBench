# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place update changes for resources with provider-schema-defined sensitive attributes because of an asymmetry in how sensitivity marks are applied and stored. Values stored in state contain only marks from sensitive variable references, but when those values are retrieved from state for expression evaluation, schema-defined sensitive marks are added back. This mark difference, detected at the plan comparison phase, triggers a spurious `Update` action despite unchanged attribute values.

## Root Cause

The root cause is a **multi-layer sensitivity mark gap** spanning state serialization, graph evaluation, and plan comparison:

### Layer 1: State Serialization Drops Schema Marks
**File**: `internal/states/instance_object.go:94-137` (`Encode` method)
- When a resource value is written to state, the `Encode()` method unmarksthe value and extracts `PathValueMarks`
- It saves only those extracted marks to `AttrSensitivePaths` (line 131)
- **Gap**: The saved marks only include paths from sensitive variable references. Provider-schema-defined sensitive attributes have never been marked on the value because providers don't apply marks—that's Terraform's responsibility
- **Result**: State's `AttrSensitivePaths` is incomplete, missing schema-defined sensitivities

### Layer 2: Asymmetric Mark Application During Evaluation
**File**: `internal/terraform/evaluate.go:718-723` (in `GetResource()` method)
- When values are read from state for expression evaluation, the `Decode()` method re-applies `AttrSensitivePaths` marks (instance_object_src.go:89-91)
- **But then** at lines 718-723, schema-defined sensitive marks are **also** applied via `schema.ValueMarks(val, nil)`
- This happens specifically because `schema.ContainsSensitive()` is true
- **Result**: Values returned by `GetResource()` for expression evaluation have BOTH variable-reference marks AND schema-defined marks

### Layer 3: Plan Comparison Uses Only Variable Marks
**File**: `internal/terraform/node_resource_abstract_instance.go:725-1251` (in `plan()` method)
- The plan method reads the prior state value from `currentState.Value` (line 814)
- This value from state has only variable-reference marks, not schema marks
- At line 869, this value is unmarked: `unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()`
- `priorPaths` captures only the marks that were in state
- The provider's response (`plannedNewVal`) comes without any schema marks
- At lines 998-1000, the planned value is re-marked with `unmarkedPaths` (which contain only variable-reference marks)
- At line 1208, a critical check compares marks:
  ```go
  if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
      action = plans.Update
  }
  ```
- Even though `unmarkedPlannedNewVal.Equals(unmarkedPriorVal)` is true (line 1082), the mark comparison detects a difference

### The Asymmetry

| Context | Marks Applied | Missing Schema Marks? |
|---------|---------------|----------------------|
| State file (`AttrSensitivePaths`) | Variable references only | ✓ Yes |
| Evaluator `GetResource()` output | Variable refs + schema marks | ✗ No (complete) |
| Plan comparison (`plan()` method) | Variable references only | ✓ Yes |

The evaluator is the **only** place that applies schema marks, and this is compensatory—it patches the incomplete mark information from state. But the plan comparison doesn't have this compensation.

### Refresh Path Compounds the Issue
**File**: `internal/terraform/node_resource_abstract_instance.go:620-720` (in `refresh()` method)
- During refresh, the prior value is unmarked before calling the provider (lines 624-625)
- The provider returns a new state without marks
- At lines 718-720, the response is re-marked with the same prior marks
- **Gap**: These prior marks don't include schema-defined marks, so the refreshed value remains incomplete
- On next plan, the incomplete marks persist

## Evidence

### Code References

1. **State serialization loses schema marks**:
   - `internal/states/instance_object.go:94-137` - `Encode()` saves only extracted marks
   - `internal/states/instance_object_src.go:77-104` - `Decode()` re-applies stored marks (line 90)

2. **Evaluator applies schema marks**:
   - `internal/terraform/evaluate.go:718-723` - `schema.ValueMarks()` applied to values from state
   - `internal/terraform/evaluate.go:689-695` - For planned objects, schema marks also added via `schema.ValueMarks()`

3. **Plan comparison detects mark difference**:
   - `internal/terraform/node_resource_abstract_instance.go:1082-1083` - Unmarked equality check passes (values identical)
   - `internal/terraform/node_resource_abstract_instance.go:1208-1210` - **Phantom update triggered by mark inequality**:
     ```go
     if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
         action = plans.Update
     }
     ```

4. **JSON output manifestation**:
   - `internal/command/jsonstate/state.go` - Reads `sensitive_attributes` from state's `AttrSensitivePaths`
   - `internal/command/jsonplan/plan.go` - Includes resource changes with incomplete sensitivity maps
   - `internal/states/statefile/version4.go:717-720` - `AttributeSensitivePaths` stored in JSON, missing schema marks

5. **Refresh preserves incomplete marks**:
   - `internal/terraform/node_resource_abstract_instance.go:620-625` - Unmark before provider call
   - `internal/terraform/node_resource_abstract_instance.go:718-720` - Re-mark with old marks (schema marks missing)

## Affected Components

1. **`internal/terraform/`** (Graph Evaluation)
   - `node_resource_abstract_instance.go`: `plan()` method performs mark comparison without schema marks
   - `node_resource_abstract_instance.go`: `refresh()` method loses schema marks during provider round-trip
   - `evaluate.go`: `GetResource()` method applies schema marks, creating asymmetry
   - `marks.go`: `marksEqual()` and `filterMarks()` utility functions used in comparison

2. **`internal/states/`** (State Serialization)
   - `instance_object.go`: `Encode()` saves incomplete `AttrSensitivePaths`
   - `instance_object_src.go`: `Decode()` re-applies stored marks without schema marks

3. **`internal/command/`** (JSON Output)
   - `jsonstate/state.go`: Outputs `sensitive_attributes` from incomplete state marks
   - `jsonplan/plan.go`: Includes phantom changes in plan output
   - `statefile/version4.go`: State file format stores incomplete sensitivity

4. **Provider Interaction Boundary**
   - Providers return responses without sensitivity marks (correct design)
   - Terraform must track sensitivities separately via schema and state

## Causal Chain

1. **Initial State Creation**: Resource apply writes state via `instance_object.Encode()` which extracts marks from the value. Provider responses have no marks, and schema marks were never applied during provider interaction, so only variable-reference marks are saved.

2. **State Storage**: `AttrSensitivePaths` in state file contains only variable-reference paths, missing schema-defined sensitivities.

3. **Subsequent Refresh**: In `node_resource_abstract_instance.refresh()`, the prior value is unmarked, losing its reference marks. Provider returns response without marks. The original reference marks are re-applied, but schema marks are still missing. Refreshed state persists with incomplete marks.

4. **Planning Phase**: In `node_resource_abstract_instance.plan()`, the prior value from state is obtained without schema marks. The provider's planned response also lacks schema marks. Both are re-marked with the incomplete prior marks. The unmarked values compare as equal (line 1082), but the mark comparison at line 1208 detects a difference.

5. **Phantom Update Detection**: The condition at line 1208 checks if marks have changed despite action being `NoOp`. Due to the mark gap, the check fails and action is changed to `Update`, creating a phantom change.

6. **JSON Output Manifestation**: When `terraform show -json` is executed, the state's incomplete `AttrSensitivePaths` is serialized as `sensitive_attributes` in the JSON output, showing only variable-reference sensitivities, missing schema-defined ones.

7. **Refresh-Only Amplification**: `terraform plan -refresh-only` also shows phantom changes because the same gap exists in the refresh comparison.

8. **Import Amplification**: `terraform import` followed by `terraform plan` shows phantom updates because the imported state also goes through the same incomplete mark storage mechanism.

## Recommendation

The root fix requires **applying schema-defined sensitive marks during state storage**, not only during evaluation retrieval:

### Fix Strategy

1. **When Encoding to State**: Before unmarking in `instance_object.Encode()`, apply schema-defined sensitive marks using the schema. These should be merged with the extracted variable-reference marks before saving to `AttrSensitivePaths`.

2. **Eliminate Compensatory Workaround**: Once schema marks are stored correctly, the compensatory logic in `evaluate.go` GetResource() that re-applies schema marks becomes redundant and can be cleaned up or verified as correct.

3. **Refresh Consistency**: Ensure `refresh()` preserves all marks (both variable-reference and schema) by passing the schema information to the refresh logic so marks can be properly restored.

### Diagnostic Steps

1. Compare `AttrSensitivePaths` in state file for a sensitive attribute before and after the fix
2. Verify that `terraform show -json` correctly reports all sensitive attributes, including schema-defined ones
3. Confirm that `terraform plan` after successful apply shows `No changes. Your infrastructure matches the configuration.`
4. Run `terraform plan -refresh-only` and verify no phantom changes appear
5. Test `terraform import` followed by `terraform plan` to verify no phantom changes

## Impact

This bug affects any Terraform user with resources that have provider-schema-defined sensitive attributes:
- VPN tunnels with sensitive cryptographic material
- Database resources with password attributes marked sensitive in the schema
- API resources with secret keys defined as sensitive in the schema
- Any managed resource where the provider schema declares `Sensitive: true` on attributes

The phantom updates don't cause functional issues (apply is a no-op), but they create false signals in planning and confuse users about infrastructure drift.
