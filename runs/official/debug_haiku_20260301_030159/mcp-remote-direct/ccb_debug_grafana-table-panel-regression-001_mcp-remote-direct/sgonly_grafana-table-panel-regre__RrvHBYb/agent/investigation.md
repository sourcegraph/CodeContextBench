# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

The table panel field override configuration is silently dropped during dashboard import when upgrading from v10.3 to v10.4 for dashboards that lack explicit `fieldConfig.defaults.custom` definitions. The schema v38 migration correctly converts `custom.displayMode` to `custom.cellOptions` in both field defaults and overrides, but subsequent frontend field config processing discards valid overrides due to a conditional logic failure that assumes `defaults.custom` must exist for overrides to be preserved.

## Root Cause

**Primary Issue**: Migration v38 backend logic mishandles field override migration when `fieldConfig.defaults` is present but `fieldConfig.defaults.custom` is absent.

**Location**: `apps/dashboard/pkg/migration/schemaversion/v38.go` lines 115-127

**Conditional Logic Failure**:
```go
// Process defaults.custom if it exists
if defaults, ok := fieldConfig["defaults"].(map[string]interface{}); ok {
  if custom, ok := defaults["custom"].(map[string]interface{}); ok {
    // Migrate displayMode to cellOptions in defaults
    if displayMode, exists := custom["displayMode"]; exists {
      // ... migration code ...
    }
  }
}

// Update any overrides referencing the cell display mode
// This must be called regardless of whether defaults.custom exists
migrateOverrides(fieldConfig)  // ← Line 131: Called unconditionally
```

The comment at line 130 states the intent correctly: override migration should happen regardless of `defaults.custom` existence. The `migrateOverrides()` function (lines 136-176) properly handles field overrides independently.

**Secondary Issue**: Frontend field config initialization in `packages/grafana-data/src/panel/getPanelOptionsWithDefaults.ts` lines 79-81 filters out overrides for properties not registered in the field config registry:

```typescript
// Filter out overrides for properties that cannot be found in registry
result.overrides = filterFieldConfigOverrides(result.overrides, (prop) => {
  return plugin.fieldConfigRegistry.getIfExists(prop.id) !== undefined;
});
```

If `custom.cellOptions` is not properly registered before override filtering occurs, valid overrides get discarded.

## Evidence

### Test Case (Backend)
File: `apps/dashboard/pkg/migration/schemaversion/v38_test.go` lines 444-602

Demonstrates the exact scenario:
- **Input Panel**: `fieldConfig.defaults` is empty (no `custom` object)
- **Field Overrides**: Present with `custom.displayMode` properties
- **Expected Output**: Overrides migrated to `custom.cellOptions` while defaults remain unchanged
- **Test Status**: Passes (backend migration is correct)

### Migration Chain Files

1. **Backend Dashboard Migration**: `apps/dashboard/pkg/migration/schemaversion/v38.go`
   - Lines 75-87: Main `V38()` migration function
   - Lines 90-133: Recursive panel processing
   - Lines 136-176: Override migration function (working correctly)
   - Lines 178-209: Display mode conversion helper

2. **Frontend Dashboard Migration**: `public/app/features/dashboard/state/DashboardMigrator.ts`
   - Lines 644-674: v38 schema upgrade handler
   - Line 647: Safe optional chaining `panel.fieldConfig.defaults?.custom?.displayMode`
   - Lines 658-669: Override property migration (independent of defaults.custom)

3. **Field Config Processing**: `packages/grafana-data/src/panel/getPanelOptionsWithDefaults.ts`
   - Lines 53-92: `applyFieldConfigDefaults()` - merges plugin defaults with existing config
   - Lines 112-139: `cleanProperties()` - removes unregistered properties from defaults
   - Lines 79-81: Override filtering by registry - **CRITICAL PATH**
   - Lines 98-110: `filterFieldConfigOverrides()` - removes unregistered override properties

4. **Table Panel Field Config**: `public/app/plugins/panel/table/panelcfg.cue`
   - Lines 47-49: Defines `FieldConfig` extending `ui.TableFieldOptions`
   - Custom properties imported from schema

## Affected Components

1. **Backend Migration**: `apps/dashboard/pkg/migration/schemaversion/v38.go`
   - Package: `schemaversion`
   - Functions: `V38()`, `processPanelsV38()`, `migrateOverrides()`, `migrateTableDisplayModeToCellOptions()`

2. **Frontend Migration**: `public/app/features/dashboard/state/DashboardMigrator.ts`
   - Class: `DashboardMigrator`
   - Method: `updateSchema()` lines 644-674

3. **Field Config Processing**: `packages/grafana-data/src/panel/getPanelOptionsWithDefaults.ts`
   - Function: `applyFieldConfigDefaults()`
   - Function: `filterFieldConfigOverrides()`
   - Function: `cleanProperties()`
   - Function: `restoreCustomOverrideRules()` (lines 204-229) - mishandles missing `defaults.custom`

4. **Panel Plugin**:
   - Plugin: `public/app/plugins/panel/table/`
   - Migration Handler: `tableMigrationHandler()` in `migrations.ts` line 23
   - Field Config Definition: `panelcfg.cue`

## Why Explicit `defaults.custom` Dashboards Work

Dashboards with explicit `fieldConfig.defaults.custom` work correctly because:

1. **v38 Backend Migration** (v38.go lines 116-127):
   - The inner `if custom, ok := defaults["custom"]...` condition succeeds
   - Defaults are properly migrated from `displayMode` to `cellOptions`
   - The conditional includes the property in the processing path

2. **Frontend Filtering** (getPanelOptionsWithDefaults.ts lines 79-81):
   - `custom.cellOptions` exists in `defaults`
   - Registry lookup finds the registered property path
   - Overrides with `custom.cellOptions` pass the filter because the property is known to the field config registry
   - Overrides are preserved in the output

## Recommendation

**Immediate Fix Strategy**:

1. **Ensure Registry Completeness**: Verify that `custom.cellOptions` is properly registered in the table panel's field config registry BEFORE the field config processing/filtering phase

2. **Decouple Override Processing from Defaults**: Modify `cleanProperties()` and `filterFieldConfigOverrides()` to handle custom override properties independently of whether the defaults contain those properties

3. **Conditional Override Restoration**: In `getPanelOptionsWithDefaults.ts`, ensure custom overrides are preserved even when `defaults.custom` is empty or undefined

4. **Fix** `restoreCustomOverrideRules()` (lines 204-229) to safely handle cases where `old.defaults.custom` is undefined:
   ```typescript
   custom: old.defaults?.custom // Use optional chaining
   ```

5. **Add Regression Test**: Ensure test coverage for table panels with:
   - Empty/missing `fieldConfig.defaults.custom`
   - Non-empty `fieldConfig.overrides` with custom properties
   - Verify overrides are preserved post-migration

**Root Cause of "Silent Drop"**: The overrides pass through the backend migration correctly, but the frontend field config initialization filters them out because the conditional logic pathway through `cleanProperties()` and `filterFieldConfigOverrides()` assumes defaults.custom existence as a prerequisite for validating custom override paths.
