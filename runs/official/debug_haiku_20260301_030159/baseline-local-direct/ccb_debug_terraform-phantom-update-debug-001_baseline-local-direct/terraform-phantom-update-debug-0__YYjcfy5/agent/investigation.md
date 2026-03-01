# Investigation Report: Phantom In-Place Updates for Resources with Sensitive Attributes

## Summary

Terraform generates phantom in-place update changes for resources with provider-schema-defined sensitive attributes because the graph evaluator and state system fail to preserve sensitivity marks from the provider schema, creating an asymmetry between what's stored in state (incomplete marks) and what's compared during planning (mixed mark sources).

## Root Cause

The root cause is a multi-layer **sensitivity mark gap** spanning the provider interaction boundary, state serialization, and plan comparison:

1. **Provider responses have no marks** - providers return unmarked values
2. **State serialization loses schema marks** - only variable-reference marks are persisted
3. **Refresh doesn't restore schema marks** - re-applies only marks from prior state
4. **Plan comparison uses incomplete marks** - causes phantom updates when marks differ

## Evidence

### 1. State Serialization Incompleteness: `internal/states/instance_object.go`

**File:** `/workspace/internal/states/instance_object.go:94-137` (Encode method)

```go
// Line 98: Removes ALL marks before serialization
val, pvm := o.Value.UnmarkDeepWithPaths()

// Line 131: Only saves marks that were ON the value
AttrSensitivePaths:  pvm,
```

**Problem:** When encoding state for storage, only marks physically present on the value are persisted in `AttrSensitivePaths`. These marks come from:
- Variable references marked as sensitive (e.g., `var.db_password` is a `sensitive` variable)
- NOT marks defined in the provider schema (e.g., `Sensitive: true` on schema attributes)

**File:** `/workspace/internal/states/instance_object_src.go:77-104` (Decode method)

```go
// Line 89-90: Re-applies only the stored marks
if os.AttrSensitivePaths != nil {
    val = val.MarkWithPaths(os.AttrSensitivePaths)
}
```

When state is decoded, it re-applies ONLY the marks stored in `AttrSensitivePaths` - missing schema marks entirely.

### 2. Refresh Doesn't Add Schema Marks: `internal/terraform/node_resource_abstract_instance.go`

**File:** `/workspace/internal/terraform/node_resource_abstract_instance.go:579-723` (refresh function)

```go
// Line 623-626: Extract marks from prior state before sending to provider
var priorPaths []cty.PathValueMarks
if priorVal.ContainsMarked() {
    priorVal, priorPaths = priorVal.UnmarkDeepWithPaths()
}

// Line 636-641: Provider receives UNMARKED value, returns UNMARKED response
resp = provider.ReadResource(providers.ReadResourceRequest{
    TypeName:     n.Addr.Resource.Resource.Type,
    PriorState:   priorVal,  // unmarked
    Private:      state.Private,
    ProviderMeta: metaConfigVal,
})

// Line 718-720: Re-applies ONLY the marks extracted from priorVal
if len(priorPaths) > 0 {
    ret.Value = ret.Value.MarkWithPaths(priorPaths)
}
```

**Problem:** The refresh function:
1. Unmarks the prior value to extract sensitivity marks
2. Sends unmarked value to provider
3. Re-applies ONLY the marks from priorPaths (variable marks from state)
4. **Does NOT apply schema-defined marks** - these are never added back

Result: Refreshed state has variable marks but missing schema marks.

### 3. Plan Doesn't Add Schema Marks: `internal/terraform/node_resource_abstract_instance.go`

**File:** `/workspace/internal/terraform/node_resource_abstract_instance.go:725-1000` (plan function)

```go
// Line 868-869: Extract marks from config and prior state
unmarkedConfigVal, unmarkedPaths := configValIgnored.UnmarkDeepWithPaths()
unmarkedPriorVal, priorPaths := priorVal.UnmarkDeepWithPaths()

// Line 902-909: Provider receives UNMARKED values
resp = provider.PlanResourceChange(providers.PlanResourceChangeRequest{
    TypeName:         n.Addr.Resource.Resource.Type,
    Config:           unmarkedConfigVal,
    PriorState:       unmarkedPriorVal,
    ProposedNewState: proposedNewVal,
    PriorPrivate:     priorPrivate,
    ProviderMeta:     metaConfigVal,
})

// Line 998-1000: Re-applies ONLY config-derived marks
if len(unmarkedPaths) > 0 {
    plannedNewVal = plannedNewVal.MarkWithPaths(unmarkedPaths)
}
```

**Problem:** The plan function:
1. Unmarks both config and prior value to extract marks
2. Sends unmarked values to provider
3. Re-applies ONLY the marks from the config (unmarkedPaths)
4. **Does NOT apply schema marks**

Result: Planned state has only variable marks, missing schema marks.

### 4. Evaluator's Compensating Workaround: `internal/terraform/evaluate.go`

**File:** `/workspace/internal/terraform/evaluate.go:541-725` (GetResource function)

```go
// Line 718-723: When reading current state for expression evaluation
if schema.ContainsSensitive() {
    var marks []cty.PathValueMarks
    val, marks = val.UnmarkDeepWithPaths()
    marks = append(marks, schema.ValueMarks(val, nil)...)  // Add schema marks
    val = val.MarkWithPaths(marks)
}
instances[key] = val
```

**Critical Insight:** Schema marks are ONLY applied in `GetResource()` when values are read for expression evaluation. This is **NOT** the same value used in:
- Plan state comparison (lines 1208-1210 in node_resource_abstract_instance.go)
- State serialization (instance_object.go:Encode)
- Plan changes (lines 1236-1252 in node_resource_abstract_instance.go)

Result: **Asymmetry** - when expressions reference the resource, they get schema marks applied. But planned/stored values don't have these marks.

### 5. Plan Comparison Detects Mark Differences: `internal/terraform/node_resource_abstract_instance.go`

**File:** `/workspace/internal/terraform/node_resource_abstract_instance.go:1199-1210`

```go
// Line 1208-1210: Converts NoOp to Update if marks changed
if action == plans.NoOp && !marksEqual(filterMarks(plannedNewVal, unmarkedPaths), priorPaths) {
    action = plans.Update
}
```

**Problem:** This comparison detects mark differences even when attribute VALUES are identical. If:
- `priorPaths` has variable marks only (from state)
- `plannedNewVal` re-applies config marks (variable only)
- But one side somehow has schema marks applied

Then this comparison triggers and converts NoOp to Update.

### 6. JSON Output Manifestation: `internal/command/jsonplan/values.go`

**File:** `/workspace/internal/command/jsonplan/values.go:207-235`

```go
// Line 207: Decodes plan change, applying stored marks
changeV, err := r.Decode(schema.ImpliedType())

// Line 213: Uses marked After value
markedAfter := changeV.After

// Line 230-235: Converts marks to sensitivity representation
s := jsonstate.SensitiveAsBool(markedAfter)
v, err := ctyjson.Marshal(s, s.Type())
resource.SensitiveValues = v
```

**Problem:** The `markedAfter` value was stored in the plan with incomplete marks (variable marks only). The JSON output shows incomplete `sensitive_values` - missing the schema-defined sensitive attributes.

## Affected Components

1. **`internal/terraform/node_resource_abstract_instance.go`**
   - `refresh()`: Returns state with variable marks only
   - `plan()`: Creates plan changes with variable marks only
   - Line 1208: Comparison that detects mark asymmetry

2. **`internal/states/`** (state serialization)
   - `instance_object.go:Encode()`: Loses schema marks during serialization
   - `instance_object_src.go:Decode()`: Re-applies only stored marks

3. **`internal/terraform/evaluate.go`**
   - `GetResource()`: ONLY place that applies schema marks (for expression evaluation)
   - Creates asymmetry between evaluated values and stored/planned values

4. **`internal/command/jsonplan/values.go`**
   - `marshalPlanResources()`: Produces incomplete `sensitive_values` from plan marks

5. **`internal/terraform/marks.go`**
   - `marksEqual()`: Detects mark differences without considering mark sources

## Causal Chain

1. **Trigger:** Resource with schema-defined sensitive attributes (e.g., `password: true`)
2. **Apply succeeds:** State written with variable-reference marks (incomplete)
3. **Next plan runs:** Refresh called
4. **Refresh flow:** State decoded → variable marks re-applied → no schema marks → sent to provider → response unmarked → variable marks re-applied
5. **Planned state:** Has variable marks only (missing schema marks)
6. **Before stored:** State has variable marks only
7. **Comparison:** Mark comparison at line 1208 may detect asymmetry if one side gets schema marks applied elsewhere
8. **Result:** NoOp converted to Update despite identical attribute values
9. **Display:** "will be updated in-place" shown with no visible attribute changes
10. **JSON output:** `sensitive_values` incomplete - missing schema-defined sensitive paths

## Recommendation

### Fix Strategy

The fix requires applying schema marks at the point where they're needed for accurate comparisons:

1. **In `refresh()`** - After provider response, apply schema marks to the returned value:
   ```go
   if schema.ContainsSensitive() {
       // Add schema marks to the refreshed value
       var marks []cty.PathValueMarks
       ret.Value, marks = ret.Value.UnmarkDeepWithPaths()
       marks = append(marks, schema.ValueMarks(ret.Value, nil)...)
       ret.Value = ret.Value.MarkWithPaths(marks)
   }
   ```

2. **In `plan()`** - After provider response, apply schema marks:
   ```go
   if schema.ContainsSensitive() {
       var marks []cty.PathValueMarks
       plannedNewVal, marks = plannedNewVal.UnmarkDeepWithPaths()
       marks = append(marks, schema.ValueMarks(plannedNewVal, nil)...)
       plannedNewVal = plannedNewVal.MarkWithPaths(marks)
   }
   ```

3. **State serialization consistency** - Ensure schema marks are re-applied consistently whether values come from state or from plan comparisons.

### Diagnostic Steps

1. **Confirm incomplete marks in state:**
   ```
   terraform show -json | jq '.values.resources[].sensitive_attributes'
   ```
   Should show all sensitive attributes from schema, not just variable references.

2. **Check plan mark difference:**
   Add logging to line 1208 in `node_resource_abstract_instance.go` to capture:
   - `filterMarks(plannedNewVal, unmarkedPaths)` contents
   - `priorPaths` contents
   - Why they differ

3. **Verify schema sensitivity:**
   ```
   terraform providers schema -json | jq '.provider_schemas[].resource_schemas[].attributes[] | select(.sensitive)'
   ```
   Confirm which attributes are marked sensitive in provider schema.

4. **Compare before/after apply:**
   - Save state after apply
   - Save state after immediate refresh
   - Compare `sensitive_attributes` in both
   - Should be identical, but schema marks are lost

## Impact

- **Users see phantom update actions** even when no actual changes occurred
- **terraform apply** would re-apply resources unnecessarily
- **terraform import** followed by `terraform plan` shows phantom changes
- **terraform show -json** displays incomplete sensitivity information
- **State drift detection** becomes unreliable for sensitive attributes
- **Provider SDK upgrades** that add schema-defined sensitive attributes cause spurious plan changes
