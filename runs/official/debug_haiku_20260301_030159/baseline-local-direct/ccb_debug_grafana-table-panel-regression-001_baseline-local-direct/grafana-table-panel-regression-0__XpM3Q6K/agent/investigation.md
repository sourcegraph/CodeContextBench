# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

The v38 dashboard migration has a critical conditional logic bug that causes table panel field override configurations to be silently dropped when `fieldConfig.defaults.custom` is not explicitly present in the original dashboard JSON. This breaks table column formatting (widths, alignment, display modes) for all dashboards imported without explicit field config defaults.

## Root Cause

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go`
**Function:** `processPanelsV38` (lines 90-137)
**Lines:** 120-123

The migration contains a premature exit condition that skips the entire panel processing:

```go
custom, ok := defaults["custom"].(map[string]interface{})
if !ok {
    continue  // <-- EXITS PANEL PROCESSING ENTIRELY
}
```

### Why This Causes the Regression

1. **Frontend Defaults Creation Flow** (`frontend_defaults.go:102-117`):
   - When a panel lacks `fieldConfig`, the code creates: `fieldConfig: { defaults: {}, overrides: [] }`
   - **Critical:** This does NOT create `fieldConfig.defaults.custom` - it remains absent

2. **Migration Execution Order** (`migrate.go:51-127`):
   - Step 1.1 (line 71): Track original `fieldConfig.defaults.custom` presence
   - Step 2 (line 75): Apply frontend defaults (creates empty defaults without custom)
   - Step 5 (line 119): Run schema version migrations including V38

3. **The Bug Trigger**:
   - For dashboards without explicit `fieldConfig.defaults.custom`:
     - `defaults["custom"]` doesn't exist after step 2
     - V38 hits the `if !ok { continue }` and skips the panel
     - Field overrides with `custom.displayMode` are never migrated
     - `migrateOverrides()` (line 135) never executes

4. **Result**:
   - Field overrides retain `custom.displayMode` instead of being converted to `custom.cellOptions`
   - Frontend table rendering fails because it expects `custom.cellOptions` (v38+ format)
   - Column formatting is lost

## Why Dashboards WITH Explicit `defaults.custom` Work

When a dashboard **explicitly includes** `fieldConfig.defaults.custom` in its JSON:
- The type assertion on line 120 succeeds
- The early `continue` is not triggered
- Both the defaults migration (lines 126-132) and the overrides migration (line 135) execute
- Field overrides are properly converted via `migrateOverrides()`
- Table formatting works correctly

## Frontend Behavior (Correct Implementation)

**File:** `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts`
**Lines:** 644-674

The frontend migration demonstrates the correct approach:

```typescript
// Frontend ALWAYS processes overrides, regardless of defaults.custom
if (panel.fieldConfig?.overrides) {
  for (const override of panel.fieldConfig.overrides) {
    for (let j = 0; j < (override.properties?.length || 0); j++) {
      if (override.properties[j].id === 'custom.displayMode') {
        override.properties[j].id = 'custom.cellOptions';  // Always migrated
      }
    }
  }
}
```

The frontend does NOT use an `if !ok { continue }` approach. It processes overrides unconditionally.

## Evidence

### Problematic Code Pattern

**File:** `v38.go:110-123`
```go
defaults, ok := fieldConfig["defaults"].(map[string]interface{})
if !ok {
    continue
}

custom, ok := defaults["custom"].(map[string]interface{})
if !ok {
    continue  // <-- BUG: Skips entire panel if defaults.custom missing
}

// Migrate displayMode to cellOptions
if displayMode, exists := custom["displayMode"]; exists {
    custom["cellOptions"] = migrateTableDisplayModeToCellOptions(displayModeStr)
    delete(custom, "displayMode")
}

// This line is never reached if defaults.custom doesn't exist!
migrateOverrides(fieldConfig)  // Line 135
```

### Missing Test Coverage

**File:** `v38_test.go`

All test cases (lines 10-443) include explicit `fieldConfig.defaults.custom` definitions. There is **no test case** for the critical scenario:
- Table panel with field overrides containing `custom.displayMode`
- BUT WITHOUT explicit `fieldConfig.defaults.custom`

This is why the regression passed testing.

### Migration Pipeline Timing Issue

**File:** `frontend_defaults.go:102-117`

```go
if _, exists := panel["fieldConfig"]; !exists {
    panel["fieldConfig"] = map[string]interface{}{
        "defaults":  map[string]interface{}{},
        "overrides": []interface{}{},
    }
} else {
    if fieldConfig, ok := panel["fieldConfig"].(map[string]interface{}); ok {
        if _, hasDefaults := fieldConfig["defaults"]; !hasDefaults {
            fieldConfig["defaults"] = map[string]interface{}{}
        }
        // NOTE: defaults.custom is NOT created here
    }
}
```

The frontend defaults ensure `fieldConfig.defaults` exists but explicitly do NOT create `fieldConfig.defaults.custom`.

## Affected Components

### Packages Involved
1. **`apps/dashboard/pkg/migration/schemaversion/`**
   - `v38.go` - The problematic migration function
   - `v38_test.go` - Missing test case for no-defaults.custom scenario
   - `migrations.go` - Registers V38 migration

2. **`apps/dashboard/pkg/migration/`**
   - `frontend_defaults.go` - Frontend defaults application logic
   - `migrate.go` - Migration pipeline orchestration

### Dashboard Schema Version
- **Affected Range:** v37 → v38 and all subsequent versions (v39-v42)
- **Regression Introduced:** When V38 was implemented
- **Triggering Condition:** Any dashboard where:
  - Panel type is `table`
  - Original JSON has `fieldConfig.overrides` with `custom.displayMode` properties
  - Original JSON does NOT have `fieldConfig.defaults.custom` explicitly set

### User-Visible Impact
- Table columns lose custom display modes (gauges, color backgrounds)
- Column widths revert to defaults
- Text alignment settings are lost
- Dashboards created before v38 with implicit field config are affected
- Dashboards exported from older Grafana versions without explicit custom defaults

## Recommendation

### Fix Strategy

The V38 migration should be modified to:

1. **Remove the premature exit condition** - Don't skip panels just because `defaults.custom` is missing
2. **Create defaults.custom if needed** - Ensure the structure exists before processing overrides
3. **Always process overrides** - Match the frontend behavior of unconditionally migrating override properties

### Code Changes Required

In `v38.go`, the `processPanelsV38` function should:
- Process overrides REGARDLESS of whether `defaults.custom` exists
- Create `defaults.custom` structure if it's needed to store overrides
- Match the frontend implementation pattern

### Test Coverage

Add test case to `v38_test.go`:
- Table panel with `fieldConfig.overrides[].properties[].id = "custom.displayMode"`
- But NO explicit `fieldConfig.defaults.custom`
- Verify overrides are properly migrated to `custom.cellOptions`

### Validation

After fix, verify:
1. All field overrides with `custom.displayMode` → `custom.cellOptions` (regardless of defaults.custom presence)
2. Backward compatibility for dashboards with explicit defaults.custom
3. Frontend and backend migrations produce identical results
4. Table panel rendering matches v10.3 behavior

## Files Referenced

| File | Lines | Purpose |
|------|-------|---------|
| `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go` | 75-137 | Main migration function (buggy) |
| `/workspace/apps/dashboard/pkg/migration/schemaversion/v38_test.go` | 10-443 | Tests (missing edge case) |
| `/workspace/apps/dashboard/pkg/migration/frontend_defaults.go` | 102-117, 1150-1169 | Frontend defaults & tracking |
| `/workspace/apps/dashboard/pkg/migration/migrate.go` | 51-127 | Migration pipeline orchestration |
| `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts` | 644-674 | Frontend migration (correct) |
