# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

The v38 migration fails to preserve table panel field override configurations when dashboards don't have explicit `fieldConfig.defaults.custom` in the original JSON. During the cleanup phase, field overrides with `custom.displayMode` are correctly migrated to `custom.cellOptions` by the V38 backend migration, but the absence of `defaults.custom` causes the field override structure to be inconsistently preserved, resulting in a mismatch between override references and default configuration structure.

## Root Cause

The regression occurs due to an asymmetry in how the v38 migration and cleanup phase handle panels without explicit `fieldConfig.defaults.custom`:

### Migration Phase (v38.go:115-127)
```go
// Process defaults.custom if it exists
if defaults, ok := fieldConfig["defaults"].(map[string]interface{}); ok {
    if custom, ok := defaults["custom"].(map[string]interface{}); ok {
        // Only process if custom exists - custom is NOT created here
    }
}
// Field overrides ARE migrated regardless (line 131)
migrateOverrides(fieldConfig)
```

The V38 migration intentionally does NOT create `fieldConfig.defaults.custom` when it doesn't exist. Instead, it only migrates field overrides that reference `custom.displayMode` to `custom.cellOptions` (lines 129-131).

### Tracking Phase (frontend_defaults.go:1138-1169)
```go
// Track original presence of fieldConfig.defaults.custom
func trackOriginalFieldConfigCustom(dashboard map[string]interface{}) {
    // Only sets _originallyHadFieldConfigCustom = true if custom EXISTS
    // Does NOT set it if custom is missing
}
```

The tracking function marks panels with `_originallyHadFieldConfigCustom = true` ONLY if `defaults.custom` already exists in the input. For panels without explicit `custom`, this flag is never set.

### Cleanup Phase (frontend_defaults.go:606-620)
```go
if prop == "fieldConfig" {
    // Only preserves custom if panel["_originallyHadFieldConfigCustom"] == true
    if panel["_originallyHadFieldConfigCustom"] == true {
        // Recreate defaults.custom structure
    }
    delete(panel, prop)  // Deletes entire fieldConfig if not marked as original
}
```

During the cleanup phase, the logic depends on the `_originallyHadFieldConfigCustom` flag to decide whether to preserve the `fieldConfig.defaults.custom` structure. For panels that didn't originally have `custom`, this flag is false, so the preservation logic is skipped.

## The Failure Scenario

For a table panel with `fieldConfig: { defaults: {}, overrides: [{id: "custom.displayMode", value: "color-background"}] }`:

1. **trackOriginalFieldConfigCustom** runs: Since `defaults.custom` doesn't exist, it does NOT set `_originallyHadFieldConfigCustom = true`
2. **V38 migration** runs:
   - Skips defaults processing (line 116-127) because `defaults.custom` doesn't exist
   - Successfully migrates override from `custom.displayMode` to `custom.cellOptions` (line 131)
   - **Does NOT create `defaults.custom`** (intentional design)
3. **Cleanup phase** runs:
   - Checks if `_originallyHadFieldConfigCustom == true`: **FALSE** (because original didn't have it)
   - Preservation logic is skipped
   - Field overrides now reference `custom.cellOptions`, but `defaults.custom` is still missing
   - The fieldConfig structure becomes inconsistent: overrides reference `custom.*` properties, but defaults doesn't define `custom`

## Exact Conditional Logic Failure

**File:** `apps/dashboard/pkg/migration/schemaversion/v38.go`, lines 115-127

**Problem:** The condition `if custom, ok := defaults["custom"].(map[string]interface{})` only processes `defaults.custom` if it already exists. It does NOT create it.

```go
// Lines 115-127: Only processes if custom exists
if defaults, ok := fieldConfig["defaults"].(map[string]interface{}); ok {
    if custom, ok := defaults["custom"].(map[string]interface{}); ok {
        // Migrate displayMode to cellOptions ONLY if custom exists
        if displayMode, exists := custom["displayMode"]; exists {
            if displayModeStr, ok := displayMode.(string); ok {
                custom["cellOptions"] = migrateTableDisplayModeToCellOptions(displayModeStr)
            }
            delete(custom, "displayMode")
        }
    }
}
// Line 129-131: ALWAYS migrate overrides, but doesn't ensure defaults.custom exists
migrateOverrides(fieldConfig)
```

**Why dashboards with explicit `defaults.custom` work:** If the original dashboard had `defaults.custom`, the `trackOriginalFieldConfigCustom` function sets the flag to true, causing the cleanup phase to preserve/recreate the `custom` structure, maintaining structural consistency.

## Evidence

### Backend Code References
- **File:** `apps/dashboard/pkg/migration/schemaversion/v38.go`
  - Lines 75-87: V38 function entry point
  - Lines 115-127: Defaults.custom processing (conditional)
  - Lines 129-131: Override migration (unconditional)
  - Lines 136-176: migrateOverrides function

- **File:** `apps/dashboard/pkg/migration/frontend_defaults.go`
  - Lines 1138-1148: trackOriginalFieldConfigCustom (ONLY marks if custom exists)
  - Lines 606-620: Cleanup fieldConfig preservation (depends on _originallyHadFieldConfigCustom flag)

### Test Case Evidence
- **File:** `apps/dashboard/pkg/migration/schemaversion/v38_test.go`
  - Lines 444-554: Test case "table with missing defaults.custom but overrides with custom.displayMode"
  - This test documents the exact scenario where defaults.custom is missing but overrides have custom.displayMode
  - The test expects successful migration, indicating the backend code SHOULD handle this case

### Frontend Migration (for reference)
- **File:** `public/app/features/dashboard/state/DashboardMigrator.ts`
  - Lines 644-674: Frontend V38 migration
  - Lines 659-669: Override migration in frontend (also executed)
  - Frontend expects both defaults and overrides to be properly structured

## Affected Components

1. **Backend Dashboard Migration**: `apps/dashboard/pkg/migration/schemaversion/v38.go`
   - Table panel displayMode to cellOptions conversion
   - Only partially creates required data structures

2. **Frontend Defaults Application**: `apps/dashboard/pkg/migration/frontend_defaults.go`
   - `trackOriginalFieldConfigCustom()` function (lines 1138-1169)
   - `filterDefaultValues()` cleanup phase (lines 557-662)
   - Field structure preservation logic

3. **Dashboard Migration Pipeline**: `apps/dashboard/pkg/migration/migrate.go`
   - Migration execution order (tracking before defaults, defaults before migration, cleanup after migration)

4. **Test Coverage**: `apps/dashboard/pkg/migration/schemaversion/v38_test.go`
   - Test case correctly identifies the scenario but may not verify field override functionality

## Recommendation

**Fix Strategy:** Ensure that when V38 migration processes field overrides that reference `custom.*` properties, it must also ensure that `fieldConfig.defaults.custom` exists, even if it was not originally present in the input.

**Specific Action:** In `v38.go`, modify the migrateOverrides call to be preceded by ensuring defaults.custom structure exists:

```go
// Before migrating overrides, ensure defaults.custom exists
// if there are custom override properties
migrateOverridesWithDefaults(fieldConfig, panel)
```

This ensures structural consistency: if field overrides reference `custom.cellOptions`, the defaults must have a corresponding `custom` object, even if empty.

**Alternatively:** Modify the cleanup phase in `frontend_defaults.go` to preserve `fieldConfig.defaults.custom` for table panels if their overrides contain any `custom.*` property references, regardless of the `_originallyHadFieldConfigCustom` flag.

The core principle: **Field override and field default structures must be symmetrical** - if overrides reference `custom.*`, the defaults must provide the `custom` container object.
