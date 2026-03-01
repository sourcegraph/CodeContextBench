# Investigation Report: Django ADMINS/MANAGERS Settings Format Migration

## Summary

Django's `ADMINS` and `MANAGERS` settings currently use a tuple format `[(name, email), ...]` that is validated, unpacked, and used across multiple code paths. A comprehensive audit reveals 5 primary source files and 10+ test files that depend on this format. The core unpacking occurs in `django/core/mail/__init__.py:142` where `a[1]` extracts the email address. Migration requires changes to validation logic, documentation, test fixtures, and backwards-compatibility handling.

## Root Cause Analysis

### Core Code Paths That Consume Tuple Format

The tuple format dependency centers on the `_send_server_message()` function in `django/core/mail/__init__.py` (lines 122-147):

```python
def _send_server_message(
    *,
    setting_name,
    subject,
    message,
    html_message=None,
    fail_silently=False,
    connection=None,
):
    recipients = getattr(settings, setting_name)
    if not recipients:
        return

    # VALIDATION: Expects 2-tuples
    if not all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
        raise ValueError(f"The {setting_name} setting must be a list of 2-tuples.")

    # UNPACKING: Extracts email address at index [1]
    mail = EmailMultiAlternatives(
        subject="%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        body=message,
        from_email=settings.SERVER_EMAIL,
        to=[a[1] for a in recipients],  # <-- Direct tuple unpacking
        connection=connection,
    )
```

This function is invoked by:
- `mail_admins()` (line 150-161)
- `mail_managers()` (line 164-175)

Which are called by:
- `django/core/management/commands/sendtestemail.py` - admin command for testing
- `django/utils/log.py:138` - `AdminEmailHandler.send_mail()`
- `django/middleware/common.py:131` - `BrokenLinkEmailsMiddleware.process_response()`

## Evidence: File-by-File Analysis

### Source Files That Read/Unpack ADMINS/MANAGERS

#### 1. **django/core/mail/__init__.py** (PRIMARY)
- **Line 135**: Validation that checks for 2-tuple format
- **Line 142**: Unpacks tuple index `[1]` to extract email: `to=[a[1] for a in recipients]`
- **Lines 150-175**: `mail_admins()` and `mail_managers()` wrappers
- **Impact**: Core unpacking logic; migration requires rewriting validation and extraction

#### 2. **django/utils/log.py** (SECONDARY - CONSUMER)
- **Line 97**: Boolean check: `if not settings.ADMINS`
- **Line 138**: Calls `mail.mail_admins()` which triggers unpacking
- **Impact**: No direct unpacking here; logic flows through core mail module
- **Note**: `AdminEmailHandler` doesn't validate format directly

#### 3. **django/core/management/commands/sendtestemail.py** (CONSUMER)
- **Line 3**: Imports `mail_admins, mail_managers`
- **Lines 43, 46**: Calls `mail_managers()`, `mail_admins()`
- **Impact**: No direct unpacking; consumer of mail functions
- **Note**: Command itself takes string email arguments, not tuple config

#### 4. **django/middleware/common.py** (CONSUMER)
- **Line 131**: `BrokenLinkEmailsMiddleware` calls `mail_managers()`
- **Impact**: No direct unpacking; consumer of mail functions

#### 5. **django/conf/global_settings.py** (DEFAULTS)
- **Line 24-26**: Comment documents tuple format: `[('Full Name', 'email@example.com'), ...]`
- **Line 26**: `ADMINS = []`
- **Line 174**: `MANAGERS = ADMINS`
- **Impact**: Documentation and default values; requires comment/default update

### Test Files With Tuple Format Dependencies

#### Fixture/Configuration Files Using Tuple Format:

1. **tests/mail/test_sendtestemail.py** (CRITICAL)
   - **Lines 7-14**: Decorators with tuple format:
     ```python
     @override_settings(
         ADMINS=(("Admin", "admin@example.com"), ("Admin and Manager", "admin_and_manager@example.com")),
         MANAGERS=(("Manager", "manager@example.com"), ("Admin and Manager", "admin_and_manager@example.com")),
     )
     ```
   - **Lines 70-91**: Assertions expecting emails from tuple `[1]` index
   - **Impact**: All 4 test methods in `SendTestEmailManagementCommand` class need fixture updates

2. **tests/mail/tests.py** (EXTENSIVE)
   - **Line 1142**: `@override_settings(ADMINS=[("nobody", "nobody@example.com")])`
   - **Line 1155**: `@override_settings(MANAGERS=[("nobody", "nobody@example.com")])`
   - **Lines 1782-1803**: `test_mail_admins_and_managers()` - comprehensive test with 4 format variations:
     - Tuple format
     - Mixed list/tuple format
     - Lazy string tuples
     - All assertions unpack with `[_, address]` pattern
   - **Lines 1805-1818**: `test_html_mail_managers()`, `test_html_mail_admins()`
   - **Lines 1836-1849**: `test_manager_and_admin_mail_prefix()` with tuple fixtures
   - **Lines 1851-1860**: `test_empty_admins()`
   - **Lines 1862-1890**: `test_wrong_admins_managers()` - validation error test
     ```python
     msg = "The %s setting must be a list of 2-tuples." % setting
     ```
   - **Impact**: 30+ test assertions dependent on tuple unpacking; validation test checks exact error message

3. **tests/logging_tests/tests.py** (EXTENSIVE)
   - **Lines ~50-200**: Multiple test decorators with tuple fixtures:
     - `@override_settings(ADMINS=[("whatever admin", "admin@example.com")])`
     - `@override_settings(ADMINS=[("admin", "admin@example.com")])`
     - `@override_settings(MANAGERS=[("manager", "manager@example.com")])`
   - **Methods**: 10+ test methods using these fixtures
   - **Impact**: All fixtures and related assertions need updates

4. **tests/middleware/tests.py** (AFFECTED)
   - **Lines ~15**: `@override_settings(MANAGERS=[("PHD", "PHB@dilbert.com")])`
   - **Class**: `BrokenLinkEmailsMiddlewareTest`
   - **Impact**: Fixture updates needed for ~5 test methods

### Documentation Files

#### 1. **docs/ref/settings.txt** (PRIMARY DOCUMENTATION)
- **Lines ~820-840**: ADMINS setting definition with example:
  ```
  Each item in the list should be a tuple of (Full name, email address). Example::

      [("John", "john@example.com"), ("Mary", "mary@example.com")]
  ```
- **Lines ~850-865**: MANAGERS setting cross-references ADMINS format
- **Impact**: Example code must be updated; format description must change

#### 2. **docs/topics/email.txt** (FUNCTIONAL DOCUMENTATION)
- **Lines ~40-80**: `mail_admins()`, `mail_managers()` documentation
- **No explicit format shown** but links to :setting:`ADMINS` and :setting:`MANAGERS`
- **Impact**: May need cross-references updated

#### 3. **docs/howto/deployment/checklist.txt**
- **References** :setting:`ADMINS` and :setting:`MANAGERS` but no format examples
- **Impact**: No code changes needed

#### 4. **docs/howto/error-reporting.txt**
- **References** ADMINS/MANAGERS settings
- **No format examples shown**
- **Impact**: No code changes needed

#### 5. **docs/ref/logging.txt**
- **References** AdminEmailHandler and ADMINS setting
- **No format examples shown**
- **Impact**: No code changes needed

#### 6. **docs/ref/django-admin.txt**
- **References** sendtestemail command with MANAGERS/ADMINS
- **No format examples shown**
- **Impact**: No code changes needed

### Type Checking & Validation

#### Validation Error Message
- **File**: `django/core/mail/__init__.py:136`
- **Current Error**: `"The {setting_name} setting must be a list of 2-tuples."`
- **Impact**: Error message must be rewritten; test `test_wrong_admins_managers()` checks exact message

#### No Type Stubs Found
- Searched for `.pyi` files - none exist for settings type hints
- Django settings are dynamically typed
- **Impact**: No type stub files to update

## Affected Components

### 1. **django.core.mail** (CRITICAL)
   - `__init__.py`: Core `_send_server_message()` function
   - Impacts: `mail_admins()`, `mail_managers()` functions

### 2. **django.utils.log** (SECONDARY)
   - `AdminEmailHandler.emit()` - boolean check only, delegates to mail module
   - No direct changes needed if mail module handles migration

### 3. **django.core.management.commands** (CONSUMER)
   - `sendtestemail.py` - command implementation
   - No direct changes needed (uses mail module functions)

### 4. **django.middleware.common** (CONSUMER)
   - `BrokenLinkEmailsMiddleware` - uses `mail_managers()`
   - No direct changes needed (uses mail module functions)

### 5. **django.conf** (CONFIGURATION)
   - `global_settings.py` - default values and documentation

### 6. **Tests** (EXTENSIVE)
   - `tests/mail/` - 30+ assertions
   - `tests/logging_tests/` - 10+ fixtures
   - `tests/middleware/` - 5+ fixtures

### 7. **Documentation**
   - `docs/ref/settings.txt` - primary format documentation
   - `docs/topics/email.txt` - functional documentation

## Third-Party Compatibility Concerns

### Breaking Changes for Existing Users

When the migration is completed (assuming settings change from tuples to strings):

1. **Old-format settings will break**
   - Code using `ADMINS = [("Name", "email@example.com")]` will fail
   - Error: `The ADMINS setting must be a list of strings` (new validation)

2. **Custom code unpacking tuples will break**
   - Third-party packages accessing `settings.ADMINS` and unpacking as `name, email`
   - Users with custom middleware inheriting from `AdminEmailHandler`
   - Users with custom logging handlers reading settings directly

3. **Configuration management tools affected**
   - Ansible/Terraform/Chef roles that generate Django settings with tuple format
   - Documentation and examples in third-party projects

### Migration Strategy for Users

- **Deprecation period needed**: Add warning in version N
- **Removal in version N+2**: Remove tuple format validation
- **Backwards compatibility option**: Accept both formats temporarily with warnings
  - Check if item is string → use as-is
  - Check if item is 2-tuple → extract `[1]` and warn

### Example User Code That Will Break

```python
# Old code that will break
for name, email in settings.ADMINS:
    print(f"Send to {name} ({email})")

# New code after migration
for email in settings.ADMINS:
    print(f"Send to {email}")
```

## Migration Checklist

### Phase 1: Preparation (No Breaking Changes)

- [ ] **Add backwards-compatibility layer to `_send_server_message()`**
  - Accept both tuple and string formats
  - Issue `DeprecationWarning` when tuple format is detected
  - Logic: `if isinstance(a, (list, tuple)): extract_and_warn(a[1]); else: use_directly(a)`

- [ ] **Update validation in `django/core/mail/__init__.py:135`**
  - New validation: Allow strings OR 2-tuples (both valid during transition)
  - Keep old error message for tuple-format validation
  - Add new validation for string format

- [ ] **Add deprecation documentation**
  - Release notes for next version: Mark tuple format as deprecated
  - Settings documentation: Add "Deprecated" note with migration instructions

### Phase 2: Code Changes (Core Logic)

#### 2.1 **django/core/mail/__init__.py** (HIGHEST PRIORITY)
```python
# Line 135-142 changes:
# Old: if not all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
# New: Add helper to detect format and extract email

def _get_email_address(recipient):
    """Extract email from recipient (string or tuple)"""
    if isinstance(recipient, str):
        return recipient
    elif isinstance(recipient, (list, tuple)) and len(recipient) == 2:
        import warnings
        warnings.warn(
            f"Passing ({recipient[0]!r}, {recipient[1]!r}) as a recipient is "
            "deprecated. Pass the email address as a string instead.",
            DeprecationWarning,
            stacklevel=4
        )
        return recipient[1]
    else:
        raise ValueError(...)
```

#### 2.2 **django/conf/global_settings.py** (LOW PRIORITY)
- [ ] Update comment on line 24-25 to document both formats during deprecation period
- [ ] Example: Add comment `# Deprecated format: [("Full Name", "email@example.com")]`
- [ ] Example: Add comment `# New format: ["email@example.com", ...]`

### Phase 3: Test Updates

#### 3.1 **tests/mail/test_sendtestemail.py**
- [ ] Update all `@override_settings` decorators (lines 7-14)
  - From: `ADMINS=(("Admin", "admin@example.com"), ...)`
  - To: `ADMINS=["admin@example.com", ...]` OR leave as-is if testing backwards-compat

- [ ] Update assertions (lines 70-91)
  - If only emails now: assertions already match email extraction

#### 3.2 **tests/mail/tests.py** (EXTENSIVE)
- [ ] `test_mail_admins_and_managers()` method (lines 1780-1803)
  - Update test fixtures to use string format
  - Or: Add separate test method for backwards compatibility
  - Change line 1802: `expected_to = ", ".join([str(address) for _, address in value])`
  - To: `expected_to = ", ".join([str(address) for address in value])`

- [ ] `test_html_mail_managers()` (lines 1805-1818)
  - Update decorator `@override_settings(MANAGERS=[("nobody", "nobody@example.com")])`
  - To: `@override_settings(MANAGERS=["nobody@example.com"])`

- [ ] `test_html_mail_admins()` (lines 1820-1833)
  - Similar update as above

- [ ] `test_manager_and_admin_mail_prefix()` (lines 1835-1849)
  - Update decorators with string format

- [ ] `test_wrong_admins_managers()` (lines 1862-1890)
  - **CRITICAL**: This test validates the error message
  - Update expected error: `msg = "The %s setting must be..."`
  - Add new test case for invalid string format

#### 3.3 **tests/logging_tests/tests.py** (EXTENSIVE)
- [ ] Find all `@override_settings(ADMINS=...`, `@override_settings(MANAGERS=...)`
  - Count: ~10+ instances
  - Update all from tuple format to string format
  - Or use fixture method to generate both formats for backwards-compat tests

#### 3.4 **tests/middleware/tests.py**
- [ ] Update `@override_settings(MANAGERS=[("PHD", "PHB@dilbert.com")])`
  - To: `@override_settings(MANAGERS=["PHB@dilbert.com"])`

### Phase 4: Documentation Updates

#### 4.1 **docs/ref/settings.txt** (PRIMARY)
- [ ] Find "ADMINS" section (around line 820)
- [ ] Update example code:
  ```
  Old:
  [("John", "john@example.com"), ("Mary", "mary@example.com")]

  New:
  ["john@example.com", "mary@example.com"]
  ```
- [ ] Update description: "A list of email addresses..." (not "list of tuples")

- [ ] Find "MANAGERS" section
- [ ] Update cross-reference and description

#### 4.2 **docs/conf/global_settings.py** (IN-FILE DOCUMENTATION)
- [ ] Update comment lines 24-25
  ```python
  # People who get code error notifications. List of email addresses.
  ADMINS = []
  ```

#### 4.3 **docs/topics/email.txt** (SECONDARY)
- [ ] Review for any format examples (likely none to update)

### Phase 5: Validation & Testing

- [ ] Run `tests/mail/tests.py` - all mail tests should pass
- [ ] Run `tests/mail/test_sendtestemail.py` - command should work
- [ ] Run `tests/logging_tests/tests.py` - logging with email should work
- [ ] Run `tests/middleware/tests.py::BrokenLinkEmailsMiddlewareTest` - middleware tests
- [ ] Test backwards compatibility with old tuple format (if keeping during deprecation)
- [ ] Test new string format works correctly
- [ ] Verify deprecation warnings appear when using old format

### Phase 6: Deprecation Timeline (Release Planning)

- [ ] **Version N**: Accept both formats, emit `DeprecationWarning` for tuples
- [ ] **Version N+1**: Tuple format still works but clearly marked as deprecated in docs
- [ ] **Version N+2**: Remove tuple format support completely; only strings accepted

## Summary of Changes Required

| Component | File | Changes | Complexity |
|-----------|------|---------|-----------|
| Core Mail | `django/core/mail/__init__.py` | Rewrite validation (lines 135-142) and unpacking logic | HIGH |
| Defaults | `django/conf/global_settings.py` | Update comments (lines 24-25) | LOW |
| Management | `django/core/management/commands/sendtestemail.py` | No direct changes (uses mail module) | NONE |
| Middleware | `django/middleware/common.py` | No direct changes (uses mail module) | NONE |
| Logging | `django/utils/log.py` | No direct changes (uses mail module) | NONE |
| Docs | `docs/ref/settings.txt` | Update examples and descriptions | MEDIUM |
| Tests | `tests/mail/test_sendtestemail.py` | Update 4 fixtures and assertions | MEDIUM |
| Tests | `tests/mail/tests.py` | Update 30+ assertions across 6+ test methods | HIGH |
| Tests | `tests/logging_tests/tests.py` | Update 10+ fixtures | MEDIUM |
| Tests | `tests/middleware/tests.py` | Update 1 fixture | LOW |

## Risk Assessment

### High Risk
1. `_send_server_message()` - core unpacking logic affects all admin/manager emails
2. `test_wrong_admins_managers()` - must update validation error message carefully
3. Backwards compatibility - need to support both formats during deprecation

### Medium Risk
1. Test fixtures in multiple test modules
2. Documentation examples must be clear about old vs new format
3. User code patterns relying on tuple unpacking

### Low Risk
1. Default values in `global_settings.py`
2. Comments and documentation-only changes

## Recommendations

1. **Implement backwards compatibility layer first**
   - Accept both formats with deprecation warning
   - Plan 2+ version deprecation period

2. **Test thoroughly across all affected code paths**
   - Mail sending (core)
   - Admin error handling (logging)
   - Broken link notifications (middleware)
   - Management command testing

3. **Clear user migration path**
   - Release notes with "Before" and "After" examples
   - Deprecation warning message with suggested fix
   - Consider automated fixer/tool if possible

4. **Update documentation early**
   - Add migration guide in release notes
   - Cross-reference old/new format in settings documentation
   - Examples should show modern string-only format

5. **Phased rollout**
   - Phase 1 (This PR): Add backwards compatibility layer
   - Phase 2 (Next version): Mark tuple format as deprecated
   - Phase 3 (Version+2): Remove tuple format support entirely
