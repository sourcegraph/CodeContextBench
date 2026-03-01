# Django ADMINS/MANAGERS Settings Format Migration Audit Report

## Summary

Django is planning to migrate the `ADMINS` and `MANAGERS` settings from the current tuple format `[(name, email), ...]` to a simple string list format `[email, ...]`. This audit identifies all code dependencies on the current format across the codebase, tests, and documentation. The migration requires changes to validation logic, 18 test fixtures, and 10 documentation files.

## Root Cause

The core dependency exists in `/workspace/django/core/mail/__init__.py` in the `_send_server_message()` function (lines 135-142), which:

1. **Validates** the tuple format: `if not all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients)`
2. **Extracts emails** using positional indexing: `to=[a[1] for a in recipients]`
3. **Raises an error** if the format doesn't match: `ValueError(f"The {setting_name} setting must be a list of 2-tuples.")`

This single function is used by both `mail_admins()` and `mail_managers()` functions, making it the critical point of migration.

## Evidence

### Files Reading ADMINS/MANAGERS Settings

#### Core Code (3 files)

1. **django/core/mail/__init__.py** (CRITICAL)
   - Line 131: `recipients = getattr(settings, setting_name)`
   - Line 135-136: Tuple format validation (2-tuple check)
   - Line 142: Email extraction using `a[1]` indexing
   - Functions affected: `_send_server_message()`, `mail_admins()`, `mail_managers()`

2. **django/utils/log.py**
   - Line 97: Empty check `if (not settings.ADMINS and ...)`
   - Line 138-139: Calls `mail.mail_admins()` which depends on tuple format

3. **django/core/management/commands/sendtestemail.py**
   - Lines 43, 46: Calls `mail_managers()` and `mail_admins()` (indirect dependency)

#### Global Settings Definition (1 file)

4. **django/conf/global_settings.py**
   - Line 25: Comment documenting tuple format: `[('Full Name', 'email@example.com'), ...]`
   - Line 26: `ADMINS = []` (empty default)
   - Line 174: `MANAGERS = ADMINS` (inherits from ADMINS)

#### Middleware (1 file)

5. **django/middleware/common.py** (BrokenLinkEmailsMiddleware)
   - Calls `mail_managers()` indirectly (no direct setting access)

### Test Files Using Old Format (7 files, 22+ test fixtures)

1. **tests/mail/tests.py**
   - Line 1142: `ADMINS=[("nobody", "nobody@example.com")]`
   - Line 1155: `MANAGERS=[("nobody", "nobody@example.com")]`
   - Line 1805: `MANAGERS=[("nobody", "nobody@example.com")]`
   - Line 1820: `ADMINS=[("nobody", "nobody@example.com")]`
   - Line 1836-1837: Both ADMINS and MANAGERS with tuple format
   - Line 1851: `ADMINS=[], MANAGERS=[]` (empty, compatible)

2. **tests/logging_tests/tests.py**
   - Lines 251, 283, 322, 344, 375: ADMINS with tuple format
   - Lines 396: MANAGERS with tuple format
   - Lines 438, 452, 570: ADMINS with tuple format
   - Total: 8 occurrences of tuple format

3. **tests/mail/test_sendtestemail.py**
   - Lines 7-14: ADMINS and MANAGERS as tuples with multiple entries
   - Test class `SendTestEmailManagementCommand` uses both settings

4. **tests/middleware/tests.py**
   - Line 392: `MANAGERS=[("PHD", "PHB@dilbert.com")]`

5. **tests/view_tests/tests/test_debug.py**
   - Lines 1454, 1490, 1533: `ADMINS=[("Admin", "admin@fattie-breakie.com")]`

### Documentation Files (10 files)

1. **docs/ref/settings.txt** (CRITICAL)
   - Lines 43-57: `ADMINS` setting documentation with tuple format example
   - Lines 2067-2075: `MANAGERS` setting documentation
   - Shows exact format: `[("John", "john@example.com"), ("Mary", "mary@example.com")]`

2. **docs/topics/email.txt**
   - Line 170: References `ADMINS` setting
   - Line 191: References `MANAGERS` setting
   - No format examples shown (safe)

3. **docs/topics/logging.txt**
   - References `ADMINS` setting
   - No format examples shown (safe)

4. **docs/ref/logging.txt**
   - References `ADMINS` setting with AdminEmailHandler
   - No format examples shown (safe)

5. **docs/ref/middleware.txt**
   - References `MANAGERS` setting for BrokenLinkEmailsMiddleware
   - No format examples shown (safe)

6. **docs/ref/django-admin.txt**
   - References sendtestemail command
   - No format examples shown (safe)

7. **docs/howto/error-reporting.txt**
   - References `ADMINS` and `MANAGERS` settings
   - No format examples shown (safe)

8. **docs/howto/deployment/checklist.txt**
   - References `ADMINS` setting
   - No format examples shown (safe)

9. **docs/internals/contributing/writing-documentation.txt**
   - References settings
   - No format examples shown (safe)

10. **docs/releases/3.0.txt**
    - Historical reference, no format examples shown (safe)

11. **docs/man/django-admin.1**
    - Man page, minimal references (safe)

## Affected Components

### Core Modules
- **django.core.mail** - Primary impact: validation and email extraction logic
- **django.utils.log** - Secondary impact: logging handler checks ADMINS
- **django.middleware.common** - Secondary impact: calls mail_managers()

### Management Commands
- **django.core.management.commands.sendtestemail** - Calls mail_admins/mail_managers

### Testing Infrastructure
- All email-related test files
- Logging test files
- View test files
- Middleware test files

### Documentation
- Settings reference (critical)
- Email topic guide
- Logging configuration guide
- Error reporting guide
- Middleware reference

## Specific Code Changes Required

### 1. Core Logic Changes

**File**: `/workspace/django/core/mail/__init__.py` (lines 122-147)

**Current logic**:
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

    mail = EmailMultiAlternatives(
        subject="%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        body=message,
        from_email=settings.SERVER_EMAIL,
        to=[a[1] for a in recipients],  # EXTRACTION: Get second element (email)
        connection=connection,
    )
```

**Required change**:
- Remove tuple validation logic (line 135-136)
- Remove indexing extraction; use string directly (line 142)
- Add validation for list of strings format

### 2. Documentation Updates Required

**File**: `/workspace/docs/ref/settings.txt` (lines 43-57)

**Current example**:
```
.. setting:: ADMINS

``ADMINS``
----------

Default: ``[]`` (Empty list)

A list of all the people who get code error notifications. When
:setting:`DEBUG=False <DEBUG>` and :class:`~django.utils.log.AdminEmailHandler`
is configured in :setting:`LOGGING` (done by default), Django emails these
people the details of exceptions raised in the request/response cycle.

Each item in the list should be a tuple of (Full name, email address). Example::

    [("John", "john@example.com"), ("Mary", "mary@example.com")]
```

**Required change**:
- Update "tuple of (Full name, email address)" to "email address string"
- Update example to `["john@example.com", "mary@example.com"]`
- Similar change needed for MANAGERS setting (lines 2067-2075)

### 3. Global Settings Update

**File**: `/workspace/django/conf/global_settings.py`

**Lines 24-26**:
- Update comment from `[('Full Name', 'email@example.com'), ...]` to `['email@example.com', ...]`

**Line 174**:
- Comment/context may need update: `MANAGERS = ADMINS`

### 4. Test File Updates (7 files)

All 22+ test fixtures need format conversion:

**Example change**:
```python
# Before:
@override_settings(ADMINS=[("Admin", "admin@example.com")])

# After:
@override_settings(ADMINS=["admin@example.com"])
```

Affected test files:
1. tests/mail/tests.py (6 occurrences)
2. tests/logging_tests/tests.py (8 occurrences)
3. tests/mail/test_sendtestemail.py (1 class definition with 2 settings)
4. tests/middleware/tests.py (1 occurrence)
5. tests/view_tests/tests/test_debug.py (3 occurrences)

## Third-Party Compatibility Concerns

### Breaking Change Impact

1. **User Configuration Breaking**
   - Any Django application with `ADMINS` or `MANAGERS` settings using the old tuple format will break
   - Error message will be: `ValueError: The ADMINS setting must be a list of 2-tuples.` → (new error if not list of strings)

2. **Migration Path Options**
   - **Option A (Abrupt)**: Just change validation, users must update immediately
   - **Option B (Graceful)**: Support both formats temporarily with deprecation warning
   - **Option C (Strict Gradual)**: Release deprecation warning first, then enforce new format

3. **Affected User Code**
   - Production settings files with ADMINS/MANAGERS configuration
   - Test files in third-party Django projects
   - Any custom management commands or utilities that create ADMINS/MANAGERS settings dynamically

4. **Detection Mechanism**
   - New validation should check if item is string (new format) vs tuple (old format)
   - Could provide helpful error message: "ADMINS should be a list of email address strings, not tuples"

## Migration Checklist

### Phase 1: Core Implementation (Priority: CRITICAL)

- [ ] **django/core/mail/__init__.py**
  - Remove tuple validation (line 135-136)
  - Change email extraction from `a[1]` to just `a` (line 142)
  - Add new validation for list of strings format
  - Update error message to clarify expected format

### Phase 2: Documentation Updates (Priority: HIGH)

- [ ] **docs/ref/settings.txt**
  - Update ADMINS section (lines 43-57): Change format description and example
  - Update MANAGERS section (lines 2067-2075): Change format description and example
  - Add migration note if needed

- [ ] **docs/topics/email.txt**
  - Review for any implicit format references

- [ ] **docs/howto/error-reporting.txt**
  - Review for any implicit format references

- [ ] **docs/ref/logging.txt**
  - Review for any implicit format references

### Phase 3: Settings Definition Updates (Priority: MEDIUM)

- [ ] **django/conf/global_settings.py**
  - Update comment on line 25 from tuple format to string format

### Phase 4: Test File Updates (Priority: HIGH)

These must be updated to match the new format:

1. [ ] **tests/mail/tests.py** - 6 occurrences to update
   - Line 1142: ADMINS fixture
   - Line 1155: MANAGERS fixture
   - Line 1805: MANAGERS fixture
   - Line 1820: ADMINS fixture
   - Line 1836-1837: Both ADMINS and MANAGERS
   - Line 1851: Empty lists (already compatible)

2. [ ] **tests/logging_tests/tests.py** - 8 occurrences to update
   - Lines 251, 283, 322, 344, 375, 438, 452, 570: ADMINS or MANAGERS tuples

3. [ ] **tests/mail/test_sendtestemail.py** - 1 class definition
   - Lines 7-14: Update both ADMINS and MANAGERS class-level settings
   - Expected result: recipients list should only contain email strings

4. [ ] **tests/middleware/tests.py** - 1 occurrence
   - Line 392: MANAGERS fixture

5. [ ] **tests/view_tests/tests/test_debug.py** - 3 occurrences
   - Lines 1454, 1490, 1533: ADMINS fixtures

### Phase 5: Validation & Testing (Priority: CRITICAL)

- [ ] **Run all mail tests** to verify `mail_admins()` and `mail_managers()` work with new format
- [ ] **Run all logging tests** to verify AdminEmailHandler works with new format
- [ ] **Run sendtestemail command tests** to verify management command works
- [ ] **Run middleware tests** to verify BrokenLinkEmailsMiddleware works
- [ ] **Run view debug tests** to verify error reporting emails work
- [ ] **Verify backward compatibility consideration**: Decide on migration path (abrupt vs graceful)

### Phase 6: Migration Documentation (Priority: MEDIUM)

- [ ] Create migration guide in release notes explaining:
  - What changed: format of ADMINS and MANAGERS settings
  - Why: simplification, removes unnecessary name field
  - How to migrate: show before/after examples
  - Timeline: when support for old format ends

### Phase 7: Optional Enhancements (Priority: LOW)

- [ ] **Add system check** to validate ADMINS/MANAGERS format and suggest corrections
- [ ] **Add deprecation warning** if old format is detected (if using graceful migration)
- [ ] **Update AdminEmailHandler docstring** if format is referenced

## File-by-File Summary Table

| File | Type | Changes Needed | Priority | Details |
|------|------|-----------------|----------|---------|
| django/core/mail/__init__.py | Code | Critical | CRITICAL | Validation & extraction logic |
| docs/ref/settings.txt | Docs | High | HIGH | Update format examples & description |
| tests/mail/tests.py | Tests | Medium | HIGH | 6 fixtures to update |
| tests/logging_tests/tests.py | Tests | Medium | HIGH | 8 fixtures to update |
| tests/mail/test_sendtestemail.py | Tests | Medium | HIGH | Class-level settings |
| tests/view_tests/tests/test_debug.py | Tests | Medium | HIGH | 3 fixtures to update |
| tests/middleware/tests.py | Tests | Low | MEDIUM | 1 fixture to update |
| django/conf/global_settings.py | Code | Low | MEDIUM | Comment update only |
| django/utils/log.py | Code | None | NONE | Just calls mail_admins() |
| django/core/management/commands/sendtestemail.py | Code | None | NONE | Just calls functions |

## Validation Strategy

Before completing the migration:

1. **Backward Compatibility Test**: Create test with old format to verify helpful error message
2. **Forward Compatibility Test**: Verify all tests pass with new format
3. **Integration Test**: Test full flow: settings → validation → email sending
4. **Documentation Consistency**: Verify all docs match the new format
5. **Release Notes**: Include clear before/after migration examples

## Conclusion

The migration is **well-scoped and achievable**. The primary change is in a single function (`_send_server_message`), with straightforward updates needed across tests and documentation. The main consideration is the user-facing breaking change, which requires either a graceful deprecation path or clear migration documentation. All affected code has been identified and mapped.
