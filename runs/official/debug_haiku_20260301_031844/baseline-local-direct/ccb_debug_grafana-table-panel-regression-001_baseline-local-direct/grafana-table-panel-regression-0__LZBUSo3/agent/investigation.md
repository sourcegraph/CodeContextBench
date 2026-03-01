# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

The V38 schema migration for table panels has a critical bug where field configuration override migrations are skipped when `fieldConfig.defaults.custom` is not explicitly set in saved dashboard JSON. This causes field overrides referencing `custom.displayMode` to remain unmigrated while the frontend expects `custom.cellOptions`, resulting in broken table formatting.

## Root Cause

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go`
**Function:** `processPanelsV38()` (lines 90-137)
**Buggy Code:** Lines 120-123

```go
custom, ok := defaults["custom"].(map[string]interface{})
if !ok {
    continue  // <-- PREMATURE EXIT: Skips migrateOverrides() call
}

// ... field migration logic ...

migrateOverrides(fieldConfig)  // Line 135: Only reached if custom exists
```

### The Logic Flaw

The `processPanelsV38()` function has a sequential chain of conditional checks that cause early exit if any level is missing:

1. **Line 110-113:** Check if `fieldConfig` exists → if not, skip panel
2. **Line 115-118:** Check if `fieldConfig.defaults` exists → if not, skip panel
3. **Line 120-123:** Check if `defaults.custom` exists → **if not, skip panel** ← **BUG**
4. **Line 135:** Call `migrateOverrides()` → only reached if step 3 passes

The critical error: **`migrateOverrides()` is only called if `defaults.custom` exists**, but field overrides can exist independently of defaults configuration.

## Evidence

### Code Reference: v38.go Lines 110-137

```go
fieldConfig, ok := p["fieldConfig"].(map[string]interface{})
if !ok {
    continue
}

defaults, ok := fieldConfig["defaults"].(map[string]interface{})
if !ok {
    continue
}

custom, ok := defaults["custom"].(map[string]interface{})
if !ok {
    continue  // PREMATURE EXIT - Blocks override migration
}

// Migrate displayMode to cellOptions
if displayMode, exists := custom["displayMode"]; exists {
    if displayModeStr, ok := displayMode.(string); ok {
        custom["cellOptions"] = migrateTableDisplayModeToCellOptions(displayModeStr)
    }
    delete(custom, "displayMode")
}

// Update any overrides referencing the cell display mode
migrateOverrides(fieldConfig)  // Never reached if custom doesn't exist
```

### Comparison with Frontend Implementation

**File:** `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts`
**Lines:** 644-674

The frontend migration correctly handles overrides **independently** of defaults:

```typescript
if (oldVersion < 38 && finalTargetVersion >= 38) {
  panelUpgrades.push((panel: PanelModel) => {
    if (panel.type === 'table' && panel.fieldConfig !== undefined) {
      const displayMode = panel.fieldConfig.defaults?.custom?.displayMode;

      // Update field configuration (conditional on defaults.custom existing)
      if (displayMode !== undefined) {
        panel.fieldConfig.defaults.custom.cellOptions = migrateTableDisplayModeToCellOptions(displayMode);
        delete panel.fieldConfig.defaults.custom.displayMode;
      }

      // Update any overrides (DECOUPLED - runs regardless of defaults.custom)
      if (panel.fieldConfig?.overrides) {  // ← Independent check
        for (const override of panel.fieldConfig.overrides) {
          for (let j = 0; j < (override.properties?.length || 0); j++) {
            if (override.properties[j].id === 'custom.displayMode') {
              override.properties[j].id = 'custom.cellOptions';
              override.properties[j].value = migrateTableDisplayModeToCellOptions(overrideDisplayMode);
            }
          }
        }
      }
    }
  });
}
```

**Key Difference:** Lines 659-669 check `if (panel.fieldConfig?.overrides)` directly, not nested under the defaults.custom condition. The backend code incorrectly nests the override migration inside the custom existence check.

### Test Coverage Gap

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38_test.go`

All test cases (lines 10-442) include explicit `defaults.custom` configuration. There is **no test case** covering the scenario where:
- Table panel has `fieldConfig` and `fieldConfig.overrides`
- `fieldConfig.defaults.custom` is **missing entirely**
- Overrides contain `custom.displayMode` properties that need migration

This explains why the bug was not caught during testing.

## Affected Components

1. **Backend Migration:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go`
   - Function: `processPanelsV38()` (lines 90-137)
   - Function: `migrateOverrides()` (lines 140-180) [dependency, not called]

2. **Schema Version Registry:** `/workspace/apps/dashboard/pkg/migration/schemaversion/migrations.go`
   - Line 74: V38 registered in migration map
   - LATEST_VERSION constant shows v38 exists in active migration chain

3. **Frontend Equivalent:** `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts`
   - Lines 644-674: Implements correct override-independent migration logic
   - Lines 659-669: Override processing with correct independent conditional

## Affected Dashboard Scenarios

Dashboards are affected **if and only if**:

1. Schema version < 38 (created in Grafana v10.3 or earlier)
2. Contains table panels with `fieldConfig.overrides`
3. At least one override has property `id: "custom.displayMode"`
4. **AND** `fieldConfig.defaults.custom` is **not explicitly set** in the original JSON

### Why Some Dashboards Work

Dashboards with explicit `defaults.custom` work correctly because they pass the type assertion at line 120 (`custom, ok := defaults["custom"].(map[string]interface{})`), allowing the code to proceed to the `migrateOverrides()` call at line 135.

### Why the Bug Appears After v10.3→v10.4

When dashboards created in v10.3 (or earlier) are imported into v10.4:
1. Backend V38 migration runs during import/save
2. Backend skips tables without `defaults.custom`
3. Dashboard is saved as schema v38 but with unmigrated overrides
4. Frontend table rendering code expects `custom.cellOptions` but finds deprecated `custom.displayMode`
5. Table formatting (column widths, text alignment, cell display modes) fails to apply

## Specific Schema Version

- **Affected Schema Version:** v38
- **Introduced In:** Grafana v10.4 (based on migration presence)
- **Related Schema Versions:** v37 (prior, unaffected) and v39 (posterior)
- **Migration Chain Location:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go`

## Recommendation

**Fix Strategy:** Decouple override migration from defaults migration.

The `migrateOverrides(fieldConfig)` call at line 135 should be executed **regardless of whether `defaults.custom` exists**. The override migration is self-contained and handles missing overrides gracefully (see lines 141-143 of migrateOverrides).

**Proposed Fix Location:** Move the `migrateOverrides(fieldConfig)` call outside the `if !ok { continue }` block that checks for `defaults.custom`. It should be called whenever:
- `fieldConfig` exists (line 110 check passes)
- Panel type is "table" (line 106 check passes)

This aligns the backend behavior with the frontend's independent override handling strategy.

**Test Coverage Addition:** Add regression test case in v38_test.go covering:
```
Test Case: "Table panel without defaults.custom but with displayMode overrides"
- Panel has fieldConfig.overrides with custom.displayMode properties
- Panel has NO fieldConfig.defaults.custom
- Expected: Overrides should be migrated to custom.cellOptions
```

## Files to Review During Fix

1. `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go` (primary fix location)
2. `/workspace/apps/dashboard/pkg/migration/schemaversion/v38_test.go` (add test coverage)
3. `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts` (reference implementation)
