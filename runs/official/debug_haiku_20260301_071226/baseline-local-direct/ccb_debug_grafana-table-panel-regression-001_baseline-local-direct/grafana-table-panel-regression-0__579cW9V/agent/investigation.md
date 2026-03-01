# Investigation Report: Dashboard Migration v38 Table Panel Regression

## Summary

The v38 table panel migration (displayMode → cellOptions conversion) fails to process field override configurations when the dashboard lacks an explicit `fieldConfig.defaults.custom` object. This causes table cell display modes in field overrides to remain unmigrated, resulting in the frontend ignoring these override properties entirely.

## Root Cause

**File:** `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go` (lines 110-137)

**Mechanism:** The `processPanelsV38()` function contains a conditional check that causes the entire panel to be skipped if `defaults.custom` doesn't exist:

```go
// Line 110-123 in v38.go
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
    continue  // EARLY RETURN - CRITICAL BUG
}

// Line 135: This call is never reached if custom doesn't exist
migrateOverrides(fieldConfig)
```

When a table panel from v10.3 (schema v37) lacks an explicitly-set `fieldConfig.defaults.custom` object:
1. The type assertion at line 120 fails
2. The function returns with `continue` at line 123
3. The `migrateOverrides()` function is never called
4. Field override properties referencing `custom.displayMode` are never migrated to `custom.cellOptions`

## Evidence

**v38 Backend Code (Go):**
- Location: `/workspace/apps/dashboard/pkg/migration/schemaversion/v38.go:110-137`
- Problem: Early return at line 123 prevents override migration
- Missing migration path for panels without explicit custom configuration

**Frontend Implementation (TypeScript):**
- Location: `/workspace/public/app/features/dashboard/state/DashboardMigrator.ts:644-674`
- Lines 646-656: Frontend checks if `displayMode !== undefined` before processing defaults
- Lines 659-669: Frontend **still processes overrides** regardless of whether `displayMode` exists in defaults
- The frontend's approach is more lenient and correctly handles missing `defaults.custom`

**Contrast:** The frontend migration code processes overrides independently of whether a `displayMode` exists in defaults (line 647-650 checks for undefined), but the backend refuses to process overrides if `custom` doesn't exist.

## Affected Components

1. **Backend Migration Pipeline**
   - Package: `github.com/grafana/grafana/apps/dashboard/pkg/migration/schemaversion`
   - Function: `V38()` → `processPanelsV38()` → `migrateOverrides()`
   - Scope: All table panels in schema versions 37 → 38 and higher

2. **Migration Tracking System**
   - File: `/workspace/apps/dashboard/pkg/migration/frontend_defaults.go` (lines 1138-1169)
   - Function: `trackOriginalFieldConfigCustom()`
   - Impact: Panels without explicit custom are not marked, and cleanup logic doesn't preserve empty custom objects

3. **Affected Dashboard Types**
   - Table panels created/saved without explicit field configuration in v10.3
   - Any dashboard relying on field override configurations for cell display modes
   - Tables with column-specific formatting applied via overrides

## Why Dashboards with Explicit Custom Config Are Unaffected

Dashboards that explicitly include `fieldConfig.defaults.custom` in their saved JSON:
1. Pass the type assertion at line 120
2. Continue to line 126 where defaults are migrated
3. Reach line 135 where `migrateOverrides()` is called
4. Field overrides are correctly migrated from `custom.displayMode` to `custom.cellOptions`

**Example of working configuration (from v38_test.go):**
```json
"fieldConfig": {
  "defaults": {
    "custom": {
      "displayMode": "basic"
    }
  },
  "overrides": []
}
```

## Schema Version Mapping

- **Schema v37:** Last version before table panel restructuring (v10.3)
- **Schema v38:** Introduces displayMode → cellOptions migration (v10.4)
- The migration is mandatory for proper table panel rendering in v10.4+

## Recommendation

The fix requires one of two approaches:

**Option 1 (Minimum):** Move the `migrateOverrides()` call outside the custom existence check
- Ensures field overrides are migrated even when defaults.custom doesn't exist
- Changes line 123 logic to not prevent override processing

**Option 2 (Defensive):** Create default custom object if processing overrides
- Initialize `defaults.custom` as empty map if it doesn't exist
- Call `migrateOverrides()` unconditionally
- Preserves empty custom object through cleanup phase

**Verification:** Current test suite (v38_test.go) only covers dashboards with explicit `fieldConfig.defaults.custom`, missing the regression case. Test coverage should be expanded to include panels without explicit custom configuration.

## Files and Functions Involved

1. **Backend Migration:**
   - `v38.go:V38()` - Entry point
   - `v38.go:processPanelsV38()` - Panel processing (lines 90-137) **[ROOT CAUSE]**
   - `v38.go:migrateOverrides()` - Override migration (lines 140-180) **[UNREACHED]**
   - `v38.go:migrateTableDisplayModeToCellOptions()` - Conversion logic (lines 183-213)

2. **Frontend Migration (Reference):**
   - `DashboardMigrator.ts:644-674` - Frontend v38 handler **[COMPARISON]**

3. **Tracking/Cleanup System:**
   - `frontend_defaults.go:trackOriginalFieldConfigCustom()` - Tracks custom presence (lines 1140-1169)
   - `frontend_defaults.go:filterDefaultValues()` - Cleanup logic (lines 557-662) **[CONSEQUENCE]**

4. **Test Coverage:**
   - `v38_test.go` - Unit tests (covers explicit custom only)
   - Missing: Integration test for panels without explicit custom
