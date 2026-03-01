# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place update diffs for resources with schema-defined sensitive attributes because the state serialization layer omits schema-defined sensitivity marks, storing only marks from variable references. The evaluator compensates by re-applying schema marks at display/evaluation time, but this asymmetry between what's stored in state and what's shown during planning creates mismatches when values are refreshed and re-planned.

## Root Cause

The root cause is an **architectural asymmetry in how sensitivity marks flow through the system**:

1. **Provider responses are unmarked** (`internal/terraform/node_resource_abstract_instance.go:636-641`): Providers return values without any marks—they have no knowledge of which paths should be sensitive.

2. **State serialization discards schema marks** (`internal/states/instance_object.go:94-136`): When encoding a `ResourceInstanceObject` to state, only marks from `priorPaths` (extracted at line 98) are preserved. These paths come exclusively from **variable reference sensitivity**, not from the provider schema's `Sensitive: true` declarations. The schema marks are never captured and stored.

3. **The evaluator applies compensating marks** (`internal/terraform/evaluate.go:689-695, 714-723`): When reading resource values back from state or from planned changes during expression evaluation, the code explicitly applies schema-defined marks via `schema.ValueMarks()` and `schema.ContainsSensitive()`. This is a **one-off compensation** that only happens in specific evaluation contexts.

4. **Plan comparisons inherit the mark asymmetry**: During the plan phase, the refreshed prior state contains only variable-reference marks (lines 814-815 in `node_resource_abstract_instance.go`), while the planned response from the provider has only config variable marks re-applied (lines 998-1000). Neither has schema marks at this stage of comparison.

5. **Display-time mark re-application masks the issue**: When plans are displayed as JSON (via `internal/command/jsonplan/plan.go:418-421, 446-450`) or state is shown (via `internal/command/jsonstate/state.go:402-411`), schema marks are re-applied. This makes the output look correct, but the underlying plan object itself never had those marks, only having them applied transiently for display.

## Evidence

### 1. Provider Response Unmarking and Selective Mark Re-application (Refresh Path)

**File**: `internal/terraform/node_resource_abstract_instance.go:580-722`

Lines 620-626 (Refresh method):
```go
priorVal := state.Value
var priorPaths []cty.PathValueMarks
if priorVal.ContainsMarked() {
    priorVal, priorPaths = priorVal.UnmarkDeepWithPaths()  // Extract ONLY variable marks
}
```

Lines 636-641: Provider returns unmarked response:
```go
resp = provider.ReadResource(providers.ReadResourceRequest{
    TypeName:     n.Addr.Resource.Resource.Type,
    PriorState:   priorVal,  // Unmarked value sent to provider
    ...
})
```

Lines 717-720: Only prior marks (variable refs) are re-applied:
```go
if len(priorPaths) > 0 {
    ret.Value = ret.Value.MarkWithPaths(priorPaths)  // Schema marks NOT restored
}
```

**Why this matters**: `priorPaths` from `UnmarkDeepWithPaths()` contains only marks that existed in the prior state. If the prior state was built from configuration without sensitive variable references, those paths won't include schema-defined sensitive paths. Schema marks are permanently lost.

### 2. State Serialization Omits Schema Marks

**File**: `internal/states/instance_object.go:94-136`

Lines 98, 131:
```go
func (o *ResourceInstanceObject) Encode(ty cty.Type, schemaVersion uint64) (*ResourceInstanceObjectSrc, error) {
    val, pvm := o.Value.UnmarkDeepWithPaths()  // Line 98: Extracts existing marks
    ...
    return &ResourceInstanceObjectSrc{
        ...
        AttrSensitivePaths:  pvm,  // Line 131: Only existing marks stored, schema marks NOT added
        ...
    }
}
```

**Evidence of the gap**: The `Encode` method never consults the schema. It only extracts and stores marks that **already exist** in the value. Schema-defined sensitivity (declared with `Sensitive: true` in provider schema) is never embedded in state.

When decoding (`internal/states/instance_object_src.go:77-104`), the reverse happens:
```go
if os.AttrSensitivePaths != nil {
    val = val.MarkWithPaths(os.AttrSensitivePaths)  // Line 90: Only variable marks restored
}
```

### 3. The Evaluator's Compensating Workaround

**File**: `internal/terraform/evaluate.go:689-695` (For planned objects)
```go
if schema.ContainsSensitive() {
    afterMarks = append(afterMarks, schema.ValueMarks(val, nil)...)  // Schema marks applied here
}
```

**File**: `internal/terraform/evaluate.go:714-723` (For state-stored objects)
```go
if schema.ContainsSensitive() {
    var marks []cty.PathValueMarks
    val, marks = val.UnmarkDeepWithPaths()
    marks = append(marks, schema.ValueMarks(val, nil)...)  // Schema marks appended
    val = val.MarkWithPaths(marks)
}
```

**Why this is a compensating workaround**: This code only runs when **explicitly evaluating** resource references in expressions. It does NOT run during:
- State encoding/decoding (happens before evaluation)
- Plan comparison (uses unmarked values at line 1082 in `node_resource_abstract_instance.go`)
- Change storage (marks are extracted and stored separately at `internal/plans/changes.go:565, 573`)

### 4. How Sensitivity Marks Are Computed from Schema

**File**: `internal/configs/configschema/marks.go:25-91`

```go
func (b *Block) ValueMarks(val cty.Value, path cty.Path) []cty.PathValueMarks {
    var pvm []cty.PathValueMarks
    for name, attrS := range b.Attributes {
        if attrS.Sensitive {  // Schema declares this attribute as sensitive
            attrPath := copyAndExtendPath(path, cty.GetAttrStep{Name: name})
            pvm = append(pvm, cty.PathValueMarks{
                Path:  attrPath,
                Marks: cty.NewValueMarks(marks.Sensitive),
            })
        }
    }
    // ... recursive descent into nested types ...
    return pvm
}
```

This function computes the sensitivity paths that **should** be marked based on schema, but these paths are:
- Never stored in state
- Never present during plan comparison
- Only applied transiently during expression evaluation and display rendering

### 5. Plan Storage and Retrieval

**File**: `internal/plans/changes.go:560-593` (Encoding a plan change)

```go
var beforeVM, afterVM []cty.PathValueMarks
unmarkedBefore := c.Before
unmarkedAfter := c.After

if c.Before.ContainsMarked() {
    unmarkedBefore, beforeVM = c.Before.UnmarkDeepWithPaths()  // Line 565
}
...
if c.After.ContainsMarked() {
    unmarkedAfter, afterVM = c.After.UnmarkDeepWithPaths()  // Line 573
}

return &ChangeSrc{
    ...
    BeforeValMarks:  beforeVM,  // Line 589: Stores extracted marks only
    AfterValMarks:   afterVM,   // Line 590: Schema marks NOT included
}
```

When plan values are created in `node_resource_abstract_instance.go:1236-1252`, they already lack schema marks:
- `Before: priorVal` at line 1243 has only variable reference marks from refresh
- `After: plannedNewVal` at line 1247 has only config variable reference marks

## Affected Components

1. **`internal/terraform/` (Graph evaluation and marking)**
   - `node_resource_abstract_instance.go`: Refresh and plan methods don't apply schema marks
   - `evaluate.go`: Only applies schema marks during expression evaluation, not during storage
   - `marks.go`: Provides mark comparison utilities, but no schema mark injection during planning

2. **`internal/states/` (State serialization)**
   - `instance_object.go`: Encode() method never consults schema; only stores existing marks
   - `instance_object_src.go`: Decode() applies only stored marks, missing schema marks

3. **`internal/plans/` (Plan storage)**
   - `changes.go`: Stores only extracted marks, no schema mark enhancement
   - `changes_src.go`: Retrieves only stored marks; schema marks added only at display time

4. **`internal/configs/configschema/` (Schema definition)**
   - `marks.go`: Computes schema sensitivity marks, but these are never stored

5. **`internal/command/` (Output rendering)**
   - `jsonstate/state.go:402-411`: Applies schema marks during JSON serialization (compensating)
   - `jsonplan/plan.go:418-421, 446-450`: Applies schema marks during JSON rendering (compensating)

## Causal Chain

1. **Symptom**: User sees phantom in-place update diffs for resources with schema-defined sensitive attributes (e.g., `password`, `secret_key`) even when no actual values changed.

2. **Intermediate Hop 1 - State Storage**: During `terraform apply`, when the resource state is encoded and persisted (`instance_object.go:Encode()`), only variable-reference marks are stored in `AttrSensitivePaths`. Schema-defined sensitivity marks are never captured.

3. **Intermediate Hop 2 - State Restoration**: When state is read back (during `terraform plan` or `terraform refresh`), the `Decode()` method (`instance_object_src.go:Decode()`) only restores the stored marks, which lack schema marks.

4. **Intermediate Hop 3 - Refresh Phase**: During `terraform refresh`, the provider returns unmarked values. The `refresh()` method (`node_resource_abstract_instance.go:717-720`) only re-applies the marks that were in the prior state (variable reference marks), which still lacks schema marks.

5. **Intermediate Hop 4 - Plan Creation**: During the plan phase, `plan()` receives the refreshed state as `currentState`. The prior value used for comparison has only variable reference marks. The provider's response also lacks schema marks. Both go through the equality test (`node_resource_abstract_instance.go:1082`) unmarked, correctly determining no change.

6. **Intermediate Hop 5 - Plan Storage**: The change is stored with `BeforeValMarks` and `AfterValMarks` containing only variable reference marks (`plans/changes.go:589-590`).

7. **Intermediate Hop 6 - Display Time Compensation**: When the plan is displayed as JSON or text, the output rendering code (`jsonplan/plan.go:418-450`, `jsonstate/state.go:402-411`) applies schema marks transiently. However, if there's any code path that compares the stored marks (Before vs After) without re-applying schema marks, or if expressions are evaluated with state values that haven't had schema marks applied, the missing marks cause visible issues.

8. **Root Cause**: The fundamental issue is that the system assumes sensitivity marks set during planning will be persisted in state, but schema-defined marks are never set during planning—they're only set during expression evaluation. This creates a gap where:
   - State stores incomplete sensitivity information
   - Plan changes have incomplete sensitivity information
   - Comparisons and evaluations that don't explicitly apply schema marks see the incomplete information

## Recommendation

### Fix Strategy

The root issue requires making schema marks **persistent** rather than **transient**:

1. **Apply schema marks during planning** (before storing in `ResourceInstanceChange`):
   - Modify `node_resource_abstract_instance.go` to apply schema marks to both `priorVal` and `plannedNewVal` before creating the `ResourceInstanceChange` object
   - Ensure schema marks are included in both `Before` and `After` values at the moment of change creation

2. **Store schema marks with plan changes**:
   - Modify `plans/changes.go` to distinguish between marks from variable references and marks from schema
   - Or ensure schema marks are included in the stored `BeforeValMarks` and `AfterValMarks`

3. **Include schema marks in state serialization** (optional, but more correct):
   - Modify `instance_object.go:Encode()` to accept schema and apply `schema.ValueMarks()` before storing
   - This makes state files self-contained regarding sensitivity information

### Diagnostic Steps

To confirm this is the root cause:

1. **Check stored marks**: Examine a state file for a resource with schema-sensitive attributes. The `sensitive_attributes` section should include paths for schema-declared sensitive attributes, but will only show variable reference paths.

2. **Compare refresh paths**: Run `terraform refresh` and examine whether attributes marked as `Sensitive: true` in the schema show up in `terraform show -json` output's `sensitive_values` section. They will only appear if they also came from sensitive variable references.

3. **Trace mark application**: Add logging to `configschema/marks.go:ValueMarks()` and observe that:
   - It's called during `GetResource()` evaluation (in expression evaluation contexts)
   - It's NOT called during state encoding (`Encode()`)
   - It's NOT called during plan change creation (`node_resource_abstract_instance.go:plan()`)
   - It IS called during JSON display rendering (compensating)

4. **Test with mixed sensitivity**: Create a test resource where:
   - One attribute is sensitive only via variable reference (e.g., `password = var.db_password` where `var.db_password` is `sensitive = true`)
   - Another attribute is sensitive via schema only (e.g., `secret_key` is marked `Sensitive: true` in the provider schema)
   - Apply, then immediately plan
   - Observe that the variable-sensitive attribute shows correctly in output, but the schema-sensitive attribute's sensitivity is missing from internal comparisons
