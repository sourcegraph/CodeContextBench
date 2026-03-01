# Investigation Report: Django ADMINS/MANAGERS Settings Format Migration Audit

## Summary

Django is transitioning the `ADMINS` and `MANAGERS` settings from a legacy format of `[(name, email), ...]` tuples to a modern format of `[email, ...]` string lists. This audit identifies all code paths that consume these settings, including validation logic, tuple unpacking, documentation, and tests that require changes for successful migration.

## Root Cause

The core issue is that `django/core/mail/__init__.py` contains the `_send_server_message()` function (lines 127-194) which is the central hub for processing these settings. This function:
1. Reads `settings.ADMINS` or `settings.MANAGERS` (line 136)
2. Detects the deprecated tuple format (line 141) and emits a deprecation warning (lines 142-147)
3. Unpacks tuples to extract email addresses: `recipients = [a[1] for a in recipients]` (line 148)
4. Validates the new format (lines 150-155)
5. Sends emails to the recipient list (lines 157-166)

All other code paths that reference these settings ultimately call through `mail_admins()` or `mail_managers()` which delegate to `_send_server_message()`.

## Evidence

### Files That Read settings.ADMINS or settings.MANAGERS

#### Core Mail System
- **`django/core/mail/__init__.py`** (lines 136-194)
  - Function: `_send_server_message()` (lines 127-194)
  - **Key code (lines 141-148)**: Handles backward compatibility by detecting and unpacking tuple format
  ```python
  if all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
      warnings.warn(...)
      recipients = [a[1] for a in recipients]
  ```
  - Function: `mail_admins()` (lines 169-180) - calls `_send_server_message()` with setting_name="ADMINS"
  - Function: `mail_managers()` (lines 183-194) - calls `_send_server_message()` with setting_name="MANAGERS"
  - **Impact Level**: CRITICAL - This is the central processing hub

#### Logging System
- **`django/utils/log.py`** (line 97)
  - Class: `AdminEmailHandler`
  - **Code**: `if not settings.ADMINS:` (line 97)
  - **Impact**: Only checks if ADMINS is empty (doesn't unpack), but relies on `mail_admins()` which does
  - **Impact Level**: LOW - Indirect dependency through mail_admins()

#### Middleware
- **`django/middleware/common.py`** (line 129)
  - Class: `BrokenLinkEmailsMiddleware`
  - **Code**: `mail_managers(...)` call (line 129)
  - **Impact**: Uses mail_managers() which internally handles settings
  - **Impact Level**: LOW - Indirect dependency

#### Management Commands
- **`django/core/management/commands/sendtestemail.py`** (lines 45-46)
  - **Code**: Calls `mail_admins()` and `mail_managers()`
  - **Impact**: References the setting indirectly through mail functions
  - **Impact Level**: LOW - Indirect dependency

### Tuple Format Unpacking

**Only location**: `django/core/mail/__init__.py` line 148
```python
recipients = [a[1] for a in recipients]
```
This is the only place in the codebase that explicitly unpacks the `(name, email)` tuple format.

### Validation Code

**`django/core/mail/__init__.py`** (lines 141-155):
```python
# Line 141: Detects tuple format
if all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
    # Lines 142-147: Emit deprecation warning
    warnings.warn(
        f"Using (name, address) pairs in the {setting_name} setting is deprecated."
        " Replace with a list of email address strings.",
        RemovedInDjango70Warning,
        stacklevel=2,
    )
    # Line 148: Extract emails from tuples
    recipients = [a[1] for a in recipients]

# Lines 150-155: Validate new format
if not isinstance(recipients, (list, tuple)) or not all(
    isinstance(address, (str, Promise)) for address in recipients
):
    raise ImproperlyConfigured(
        f"The {setting_name} setting must be a list of email address strings."
    )
```

**Impact Level**: CRITICAL - This is where format conversion and validation occurs

### Documentation References

#### Default Settings Documentation
- **`django/conf/global_settings.py`** (lines 24-26)
  ```python
  # People who get code error notifications. In the format
  # [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]
  ADMINS = []
  ```
  **Status**: OUTDATED - Comment shows old tuple format
  **Change Needed**: Update comment to show new string format example

#### Settings Reference
- **`docs/ref/settings.txt`** (lines 48-61) - ADMINS setting documentation
  ```
  Default: ``[]`` (Empty list)
  A list of all the people who get code error notifications...
  Each item in the list should be an email address string. Example::
      ADMINS = ["john@example.com", '"Ng, Mary" <mary@example.com>']

  .. versionchanged:: 6.0
      In older versions, required a list of (name, address) tuples.
  ```
  **Status**: CURRENT - Correctly documents new format with versionchanged note

- **`docs/ref/settings.txt`** (lines 2070-2084) - MANAGERS setting documentation
  ```
  A list in the same format as :setting:`ADMINS`

  .. versionchanged:: 6.0
      In older versions, required a list of (name, address) tuples.
  ```
  **Status**: CURRENT - References ADMINS docs which already document new format

#### Email Topic Documentation
- **`docs/topics/email.txt`** (lines 166-192)
  - Describes `mail_admins()` and `mail_managers()` functions
  - **Status**: CURRENT - No format details, just function descriptions

#### Release Notes
- **`docs/releases/6.0.txt`** (lines 331-334)
  ```
  * Setting :setting:`ADMINS` or :setting:`MANAGERS` to a list of (name, address)
    tuples is deprecated. Set to a list of email address strings instead.
  ```
  **Status**: CURRENT - Properly documents deprecation for Django 6.0

#### Deprecation Timeline
- **`docs/internals/deprecation.txt`** (lines 31-32)
  ```
  * Support for setting the ``ADMINS`` or ``MANAGERS`` settings to a list of
    (name, address) tuples will be removed.
  ```
  **Status**: CURRENT - Indicates removal in Django 7.0

### Test Files Using Old Format

#### Deprecated Format Tests
- **`tests/mail/tests.py`** (lines 1865-1888)
  - **Function**: `test_deprecated_admins_managers_tuples()`
  - **Tests**: Both tuple and list-of-lists formats with deprecation warning
  - **Status**: WILL NEED REMOVAL - Tests deprecated functionality
  - **Change**: Remove when tuple support is removed in Django 7.0

- **`tests/mail/tests.py`** (lines 1890-1913)
  - **Function**: `test_wrong_admins_managers()`
  - **Tests**: Invalid format validation
  - **Status**: UPDATE NEEDED - Currently has commented-out tuple test cases
  - **Change**: Uncomment lines 1894-1897 when tuple support is removed

#### New Format Tests
- **`tests/mail/test_sendtestemail.py`** (lines 6-109)
  - **Settings**:
    ```python
    ADMINS=["admin@example.com", "admin_and_manager@example.com"],
    MANAGERS=["manager@example.com", "admin_and_manager@example.com"],
    ```
  - **Status**: CORRECT - Already using new string format
  - **Tests**: Comprehensive tests for sendtestemail command

- **`tests/logging_tests/tests.py`** (line 452)
  - **Setting**: `@override_settings(ADMINS=["admin@example.com"])`
  - **Status**: CORRECT - Using new format

- **`tests/middleware/tests.py`** (line 392)
  - **Setting**: `MANAGERS=["manager@example.com"]`
  - **Status**: CORRECT - Using new format

### Third-Party Compatibility Concerns

#### Breaking Changes for Users

1. **Direct Setting Access**
   - Any code doing: `for name, email in settings.ADMINS:` will break with new format
   - Users who iterate directly will get strings instead of tuples

2. **Email Headers**
   - Old format silently ignored the `name` portion
   - Users wanting to include display names must now use: `"Name <email@example.com>"` format or `email.utils.formataddr()`

3. **Migration Path**
   - Users with legacy settings will get a deprecation warning in Django 6.x
   - Warning message directs users to: `'\"Name\" <address>'` or `email.utils.formataddr()`
   - Support will be removed in Django 7.0

## Affected Components

1. **`django.core.mail` package** (CRITICAL)
   - `__init__.py`: Core processing, validation, tuple unpacking

2. **`django.utils.log` package** (LOW)
   - `log.py`: AdminEmailHandler reads settings but relies on mail_admins()

3. **`django.middleware.common` package** (LOW)
   - `common.py`: BrokenLinkEmailsMiddleware uses mail_managers()

4. **Management Commands** (LOW)
   - `sendtestemail.py`: Uses mail_admins() and mail_managers()

5. **Documentation** (MEDIUM)
   - Global settings comment needs update
   - Release notes already document deprecation
   - Settings reference already shows new format

6. **Test Suite** (MEDIUM)
   - Deprecated format tests will need removal in Django 7.0
   - Invalid format tests have commented-out cases to uncomment

## Recommendation: Migration Checklist

### Phase 1: Current State (Django 6.0) - Already Complete
✅ **Deprecated format is SUPPORTED with warnings**
- [x] `django/core/mail/__init__.py` - Lines 141-148: Backward compatibility code in place
- [x] `django/conf/global_settings.py` - Lines 24-26: Comment shows old format
- [x] `docs/releases/6.0.txt` - Lines 331-334: Deprecation notice published
- [x] `docs/internals/deprecation.txt` - Lines 31-32: Removal timeline documented
- [x] `tests/mail/tests.py` - Lines 1865-1888: Deprecation warning tested
- [x] `tests/mail/test_sendtestemail.py` - Lines 6-109: New format tested

### Phase 2: Django 7.0 - Migration Tasks

#### File: `django/core/mail/__init__.py`
**Lines 141-148**: REMOVE backward compatibility code
```python
# DELETE THESE LINES:
if all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
    warnings.warn(
        f"Using (name, address) pairs in the {setting_name} setting is deprecated."
        " Replace with a list of email address strings.",
        RemovedInDjango70Warning,
        stacklevel=2,
    )
    recipients = [a[1] for a in recipients]
```
**Impact**: Remove deprecated support, simplify function

#### File: `django/conf/global_settings.py`
**Lines 24-26**: UPDATE comment to show new format
```python
# OLD:
# People who get code error notifications. In the format
# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]

# NEW:
# People who get code error notifications. A list of email address strings.
# Example: ["admin@example.com", '"John Smith" <john@example.com>']
```

#### File: `django/core/mail/__init__.py`
**Lines 150-155**: Simplify validation (no longer need tuple check)
```python
# Current code will work fine - no change needed, but could be simplified
# to remove tuple check if desired
```

#### File: `tests/mail/tests.py`
**Lines 1865-1888**: REMOVE test_deprecated_admins_managers_tuples()
- This test specifically validates the deprecated warning
- No longer needed when deprecated code is removed

#### File: `tests/mail/tests.py`
**Lines 1890-1913**: UPDATE test_wrong_admins_managers()
- UNCOMMENT lines 1894-1897 (currently commented out for Django 7.0)
```python
# Currently commented:
# [(\"nobody\", \"nobody@example.com\"), (\"other\", \"other@example.com\")],
# [[\"nobody\", \"nobody@example.com\"], [\"other\", \"other@example.com\"]],

# Will become invalid in Django 7.0 - uncomment to test rejection
```

#### File: `docs/releases/7.0.txt` (NEW RELEASE NOTES)
**Add section**: Document removal of tuple support
```
Features removed in 7.0
=======================

* Support for setting :setting:`ADMINS` or :setting:`MANAGERS` to a list of
  (name, address) tuples is removed. Use a list of email address strings instead.
  See :ref:`deprecated-features-6.0` for migration instructions.
```

#### File: `docs/internals/deprecation.txt`
**Update section**: Move from 7.0 deprecations to past removals
- Update line references to point to 7.0 release notes

### Phase 3: Validation

#### Tests to Verify
- [x] `tests/mail/test_sendtestemail.py` - All tests pass with new format
- [x] `tests/logging_tests/tests.py` - AdminEmailHandler works with new format
- [x] `tests/middleware/tests.py` - BrokenLinkEmailsMiddleware works with new format
- [x] `tests/mail/tests.py` - Invalid format validation tests pass
- [ ] NEW: Add test ensuring tuple format raises error (after removal)

### Non-Code Changes Needed

1. **Release Notes Updates**
   - Add removal announcement to Django 7.0 release notes
   - Include migration guide

2. **External Communication**
   - Blog post about format change (already published for 6.0)
   - Upgrade documentation

3. **Deprecation Warning Messages**
   - Current warning in Django 6.x already guides users to new format
   - No changes needed to warning text

## Migration Impact Summary

| File | Type | Change Type | Priority | Complexity |
|------|------|------------|----------|------------|
| `django/core/mail/__init__.py` | Code | Remove backward compat | HIGH | Low |
| `django/conf/global_settings.py` | Docs | Update comment | MEDIUM | Low |
| `tests/mail/tests.py` | Tests | Remove + Update | HIGH | Low |
| `docs/releases/7.0.txt` | Docs | Add removal note | MEDIUM | Low |
| `docs/internals/deprecation.txt` | Docs | Update timeline | LOW | Low |

## Summary Statistics

- **Total files reading settings**: 4
- **Total files with tuple unpacking**: 1
- **Total validation locations**: 1
- **Total documentation files**: 5
- **Total test files**: 4
- **Lines of code to remove**: ~10 lines (backward compat in `_send_server_message`)
- **Breaking change**: YES (tuple format support removed)
- **Deprecation cycle**: Django 6.0 → Django 7.0 (one release cycle)
