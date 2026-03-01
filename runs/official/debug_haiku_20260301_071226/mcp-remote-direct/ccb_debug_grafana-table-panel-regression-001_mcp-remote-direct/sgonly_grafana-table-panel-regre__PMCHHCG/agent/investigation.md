# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

The v38 dashboard migration correctly converts table panel field overrides from `custom.displayMode` to `custom.cellOptions`. However, when the panel is persisted, all custom field overrides are filtered out by `PanelModel.getSaveModel()`, causing the field override configuration to be silently dropped during dashboard import/export cycles. The issue manifests specifically for dashboards where `fieldConfig.defaults.custom` was not explicitly set in the original v10.3 dashboard JSON.

## Root Cause

### Primary Issue: Custom Override Filtering in getSaveModel()

**Location**: `public/app/features/dashboard/state/PanelModel.ts:490`

```typescript
// filter out custom overrides
overrides: filterFieldConfigOverrides(this.fieldConfig.overrides, isStandardFieldProp),
```

When `PanelModel.getSaveModel()` is called, it filters the fieldConfig overrides using `isStandardFieldProp`. This function is defined in `packages/grafana-data/src/panel/getPanelOptionsWithDefaults.ts:243`:

```typescript
export function isStandardFieldProp(prop: DynamicConfigValue): boolean {
  return !isCustomFieldProp(prop);
}
```

And `isCustomFieldProp` (line 235) checks:

```typescript
export function isCustomFieldProp(prop: DynamicConfigValue): boolean {
  return prop.id.startsWith('custom.');
}
```

**This means all overrides with IDs starting with `custom.` are filtered out during save.** After the v38 migration converts `custom.displayMode` → `custom.cellOptions`, these migrated overrides are classified as custom properties and filtered out.

### Secondary Issue: Migration Order and Conditional Logic

**Backend v38 Migration** (`apps/dashboard/pkg/migration/schemaversion/v38.go:115-127`):

The backend migration only processes `defaults.custom` if it exists:

```go
// Process defaults.custom if it exists
if defaults, ok := fieldConfig["defaults"].(map[string]interface{}); ok {
    if custom, ok := defaults["custom"].(map[string]interface{}); ok {
        // Migrate displayMode to cellOptions in defaults
        if displayMode, exists := custom["displayMode"]; exists {
            if displayModeStr, ok := displayMode.(string); ok {
                custom["cellOptions"] = migrateTableDisplayModeToCellOptions(displayModeStr)
            }
            delete(custom, "displayMode")
        }
    }
}
```

This logic correctly handles the case where `defaults.custom` doesn't exist (it just skips the block). The migration then correctly processes overrides (line 131):

```go
// Update any overrides referencing the cell display mode
// This must be called regardless of whether defaults.custom exists
migrateOverrides(fieldConfig)
```

**Frontend v38 Migration** (`public/app/features/dashboard/state/DashboardMigrator.ts:644-669`):

The frontend migration mirrors the backend logic correctly.

### The Missing Link: Why Dashboards Without Explicit defaults.custom Are Affected

For dashboards where the original JSON **has no `defaults.custom` object**:

1. **Input state** (v10.3 dashboard):
   ```json
   {
     "fieldConfig": {
       "defaults": {},
       "overrides": [
         {
           "matcher": {"id": "byName", "options": "CPU"},
           "properties": [{"id": "custom.displayMode", "value": "gradient-gauge"}]
         }
       ]
     }
   }
   ```

2. **After v38 migration** (both backend and frontend):
   - `defaults.custom` remains absent (migration didn't create it)
   - Overrides are correctly migrated to `custom.cellOptions`
   - Result:
     ```json
     {
       "fieldConfig": {
         "defaults": {},
         "overrides": [
           {
             "matcher": {"id": "byName", "options": "CPU"},
             "properties": [{"id": "custom.cellOptions", "value": {"type": "gauge", "mode": "gradient"}}]
           }
         ]
       }
     }
     ```

3. **When panel is saved** (`PanelModel.getSaveModel()`):
   - Custom overrides (those with ids starting with `custom.`) are filtered out
   - Result: overrides array becomes empty `[]`
   - The entire fieldConfig object may be removed if it matches defaults

4. **Final persisted state**:
   ```json
   {
     "fieldConfig": {
       "defaults": {},
       "overrides": []
     }
   }
   ```

### Why Dashboards WITH Explicit defaults.custom Appear Unaffected

Dashboards with explicit `fieldConfig.defaults.custom` objects in the original JSON:

1. During v38 migration, the `defaults.custom` object receives the migrated `cellOptions`
2. The overrides are still filtered during `getSaveModel()`, BUT:
3. The presence of `defaults.custom` with content means the panel still has some configuration in its defaults
4. The field override functionality may degrade gracefully or the defaults provide fallback configuration
5. This creates the illusion that the panel "works" - it's rendering with default values rather than override values

## Evidence

### Key Files and Functions Involved

1. **Backend Migration** (`apps/dashboard/pkg/migration/schemaversion/v38.go`):
   - `V38()` - Lines 75-87: Main migration entry point
   - `processPanelsV38()` - Lines 90-133: Processes table panels and calls migrateOverrides
   - `migrateOverrides()` - Lines 136-176: Migrates override IDs from `custom.displayMode` to `custom.cellOptions`
   - `migrateTableDisplayModeToCellOptions()` - Lines 179-209: Converts display mode strings to cellOptions objects

2. **Frontend Migration** (`public/app/features/dashboard/state/DashboardMigrator.ts`):
   - Lines 644-674: v38 migration handler that mirrors backend logic

3. **Override Filtering** (`public/app/features/dashboard/state/PanelModel.ts`):
   - Line 490: Filters custom overrides in `getSaveModel()`
   - Imported from `packages/grafana-data/src/panel/getPanelOptionsWithDefaults.ts:235-245`

4. **Custom Property Detection** (`packages/grafana-data/src/panel/getPanelOptionsWithDefaults.ts`):
   - Lines 235-245: `isCustomFieldProp()` and `isStandardFieldProp()` functions that identify properties starting with `custom.`

5. **Backend Defaults Cleanup** (`apps/dashboard/pkg/migration/frontend_defaults.go`):
   - Lines 1150-1169: `trackPanelOriginalFieldConfigCustom()` marks panels that originally had custom objects
   - Lines 556-662: `filterDefaultValues()` preserves panels that originally had custom objects
   - The tracking mechanism attempts to preserve custom objects but doesn't account for the downstream filtering in getSaveModel()

### Dashboard Schema Version

- **Affected Version**: v38 (introduced the table panel `custom.displayMode` → `custom.cellOptions` migration)
- **Triggers on**: Dashboards being upgraded from v10.3 (schema < 38) to v10.4 (schema ≥ 38)

## Affected Components

### Direct Impact
- **Table panel** (`packages/grafana-ui/src/components/Table/`): Field override configuration for cell display modes
- **Field override system** (`packages/grafana-data/src/panel/`): Custom override filtering logic
- **Panel save model** (`public/app/features/dashboard/state/PanelModel.ts`): `getSaveModel()` method

### Indirect Impact
- **Dashboard migration pipeline** (`apps/dashboard/pkg/migration/`): Backend v38 migration
- **Dashboard migrator** (`public/app/features/dashboard/state/DashboardMigrator.ts`): Frontend v38 migration
- **Frontend defaults application** (`apps/dashboard/pkg/migration/frontend_defaults.go`): Cleanup and preservation logic

## Conditional Logic Failure

The mismatch occurs in the assumption chain:

1. **Migration Assumption**: Custom overrides migrated to `custom.cellOptions` will persist
   - Backend v38 converts IDs and values: ✓ Works correctly
   - Frontend v38 converts IDs and values: ✓ Works correctly

2. **Persistence Assumption**: All override properties are preserved during save
   - **This assumption fails** for properties starting with `custom.`
   - `PanelModel.getSaveModel()` filters them out unconditionally

3. **Reconstruction Assumption**: Panels without explicit defaults.custom can rely on overrides
   - This assumption fails because overrides are removed at save time
   - No fallback mechanism exists for custom overrides without matching defaults

## Why the Regression Is Visible in v38

The v38 migration is the first major change to field override naming in table panels from the user's perspective. While custom property overrides have always been filtered during save, this filtering becomes **critical** in v38 because:

1. The migration changes the property ID structure
2. Users with existing dashboards that relied on `custom.displayMode` overrides may not have noticed the override filtering before (the old property name worked or was ignored)
3. In v38, the migration correctly converts the property, but the conversion is immediately lost to filtering
4. The table panel's `cellOptions` structure is more critical for rendering than the legacy `displayMode`

## Recommendation

The root cause is in the `PanelModel.getSaveModel()` method filtering out all custom property overrides. The fix should either:

1. **Preserve Custom Overrides**: Modify `getSaveModel()` to preserve custom overrides that were actually migrated and have valid values in table panels
2. **Ensure defaults.custom Exists**: Modify the v38 migration to ensure `fieldConfig.defaults.custom` always exists for table panels, even if empty, so the backend cleanup logic preserves the structure
3. **Migrate Overrides to Defaults**: For table panels, move critical overrides into `defaults.custom` during v38 migration to ensure they survive the save cycle
4. **Add Override Restoration**: Modify the table panel's migration logic to restore custom overrides from a temporary marker or from cached plugin options

The fix requires careful coordination between the dashboard migration pipeline, the panel save logic, and the field override system to ensure that migrated custom properties are not silently dropped.
