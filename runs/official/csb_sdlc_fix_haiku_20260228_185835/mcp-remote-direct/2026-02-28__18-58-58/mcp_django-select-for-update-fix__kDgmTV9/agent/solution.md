# Django select_for_update(of) Crash with Annotation Expressions - Root Cause Analysis

## Files Examined

- **django/db/models/sql/compiler.py** — examined for the `get_select_for_update_of_arguments()` method (entry point)
- **django/db/models/sql/query.py** — examined for `set_values()` method to understand how `selected` dict is built
- **django/db/models/query.py** — examined for `values_list()` and `_values()` methods to understand the call chain
- **django/db/models/expressions.py** — examined for the `Col` class to understand expression types
- **django/db/models/sql/compiler.py** — examined for `get_select()` method to understand what gets populated in `self.select`

## Dependency Chain

1. **Symptom observed in**: User code calls `Person.objects.select_for_update(of=("self",)).values_list(Concat(Value("Dr. "), F("name")), "born")`

2. **Called from (QuerySet methods)**:
   - `django/db/models/query.py:1369` — `QuerySet.values_list()` method
   - `django/db/models/query.py:1355` — `QuerySet._values()` method
   - `django/db/models/query.py:1363-1364` — `QuerySet.values()` method
   - `django/db/models/sql/query.py:2492` — `Query.set_values()` method

3. **SQL Compilation (where bug is triggered)**:
   - `django/db/models/sql/compiler.py:74-76` — `SQLCompiler.setup_query()` calls `get_select()`
   - `django/db/models/sql/compiler.py:230-333` — `SQLCompiler.get_select()` populates `self.select` list
   - `django/db/models/sql/compiler.py:880-886` — `SQLCompiler.as_sql()` calls `get_select_for_update_of_arguments()`
   - **BUG TRIGGERED AT**: `django/db/models/sql/compiler.py:1405` — `SQLCompiler.get_select_for_update_of_arguments()`

4. **Bug Location**:
   - `django/db/models/sql/compiler.py:1424-1425` — First problematic access to `.target.model`
   - `django/db/models/sql/compiler.py:1440` — Second problematic access to `.target.model`

## Root Cause

### File: `django/db/models/sql/compiler.py`
### Function: `get_select_for_update_of_arguments()`
### Lines: ~1424-1425 and ~1440

### Explanation

The bug occurs because the `get_select_for_update_of_arguments()` method assumes all expressions in `self.select` are `Col` (column reference) objects, which have a `.target` attribute that provides access to the model field.

**Problematic Code (line 1424-1425)**:
```python
if (
    self.select[select_index][0].target.model == parent_model
    or self.select[select_index][0].target.model in all_parents
)
```

**Problematic Code (line 1440)**:
```python
if self.select[select_index][0].target.model == concrete_model:
```

**Why it crashes:**

When `values_list()` is combined with annotation expressions (like `Concat(Value("Dr. "), F("name"))`), the `self.select` list contains these annotation expressions mixed with column references.

Annotation expressions are NOT `Col` objects - they are instances of expression classes like `Concat`, `Value`, `F`, etc. These expression types do NOT have a `.target` attribute.

According to the code analysis:
- `django/db/models/expressions.py:1287-1295` shows that only `Col` class has a `.target` attribute initialized in `__init__`
- Other expression types like `Concat`, `Cast`, `F`, `Value` don't have this attribute
- When the code tries to access `.target.model` on these non-Col expressions, it raises an `AttributeError`

**Historical context (from task description):**

Prior to the `values()`/`values_list()` field ordering change, model field columns were always placed first in the SELECT clause. Model columns (which are `Col` objects with `.target` attribute) would come before annotation expressions, so the code would never try to access `.target.model` on non-Col objects.

After the change, annotations can appear before model field columns in the SELECT clause (as determined by their order in `values_list()`). This means `self.select` might start with annotation expressions that don't have a `.target` attribute, causing the crash when the code iterates through `select_fields`.

## Proposed Fix

The solution is to add a check before accessing the `.target` attribute to verify the expression actually has this attribute. If it doesn't (meaning it's not a column reference), skip it.

```diff
--- a/django/db/models/sql/compiler.py
+++ b/django/db/models/sql/compiler.py
@@ -1419,10 +1419,12 @@ class SQLCompiler:
                     "select_fields": [
                         select_index
                         for select_index in klass_info["select_fields"]
                         # Selected columns from a model or its parents.
-                        if (
-                            self.select[select_index][0].target.model == parent_model
-                            or self.select[select_index][0].target.model in all_parents
-                        )
+                        if (
+                            hasattr(self.select[select_index][0], "target")
+                            and (
+                                self.select[select_index][0].target.model == parent_model
+                                or self.select[select_index][0].target.model in all_parents
+                            )
+                        )
                     ],
                 }

@@ -1437,7 +1439,7 @@ class SQLCompiler:
             concrete_model = klass_info["model"]._meta.concrete_model
             for select_index in klass_info["select_fields"]:
-                if self.select[select_index][0].target.model == concrete_model:
+                if hasattr(self.select[select_index][0], "target") and self.select[select_index][0].target.model == concrete_model:
                     return self.select[select_index][0]

         def _get_field_choices():
```

## Analysis

### Why This Fix Works

1. **Safety Check**: The `hasattr(self.select[select_index][0], "target")` check ensures we only attempt to access `.target.model` on expressions that actually have a `.target` attribute (i.e., `Col` objects).

2. **Proper Filtering**: When iterating through `select_fields`, the code in `_get_parent_klass_info()` now correctly filters to only include columns that belong to the parent model. Non-Col expressions (annotations) will be excluded because they don't have a `.target` attribute.

3. **Correct Semantics**: Only model columns should be locked in a `SELECT FOR UPDATE OF` clause. Annotation expressions are computed values and shouldn't be part of the lock target, so excluding them is the correct behavior.

4. **Backward Compatible**: This change doesn't break existing code because:
   - When `values_list()` doesn't include annotations, the behavior remains unchanged
   - `Col` objects still get processed correctly
   - Queries without `values_list()` are unaffected

### How the Bug Manifests

1. User calls: `Person.objects.select_for_update(of=("self",)).values_list(Concat(...), "born")`

2. `values_list()` calls `_values()` which calls `annotate()` then `set_values()`

3. `set_values()` creates `self.selected` dict with the annotation expression as an entry

4. When the query is compiled, `get_select()` populates `self.select` with mixed expression types

5. During SQL compilation, `get_select_for_update_of_arguments()` is called

6. The code tries to iterate through indices to find columns, but crashes when accessing `.target` on the `Concat` expression

### The Fix in Context

The fix maintains the original intent of `get_select_for_update_of_arguments()` which is to:
- Find columns selected from the locked model and its parents
- Generate the appropriate `SELECT FOR UPDATE OF` clause based on database features

By filtering to only Col objects (those with `.target` attribute), we correctly identify model field columns while safely skipping annotation expressions that can't be part of the FOR UPDATE OF clause.

### Precedent in the Codebase

This pattern of checking `hasattr(expr, "target")` is already established in the same file at line 213:

```python
# From django/db/models/sql/compiler.py:213-216
if (
    hasattr(expr, "target")
    and expr.target.primary_key
    and self.connection.features.allows_group_by_selected_pks_on_model(
        expr.target.model
    )
)
```

This confirms that the fix approach is consistent with existing Django coding patterns - defensive checks using `hasattr()` before accessing the `.target` attribute on expressions.
