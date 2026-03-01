# Investigation Report: Django ADMINS/MANAGERS Settings Format Migration Audit

## Summary

Django is transitioning the `ADMINS` and `MANAGERS` settings from `[(name, email), ...]` tuple format to simple `[email, ...]` string list format. The codebase currently supports both formats (with deprecation warnings for the old format) and will remove tuple support in Django 7.0. This audit identifies all code locations requiring migration and validates the transition strategy.

## Root Cause

The core issue is in the mail handling system. The `_send_server_message()` function in `django/core/mail/__init__.py` (lines 127-167) is the central processing point that reads and validates `ADMINS` and `MANAGERS` settings. It currently:

1. Detects the old tuple format with: `all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients)`
2. Issues a deprecation warning: `RemovedInDjango70Warning`
3. Extracts addresses from tuples: `recipients = [a[1] for a in recipients]`
4. Validates the final format as a list of email strings
5. Sends via `EmailMultiAlternatives`

This centralized handling means the migration requires changes only to functions that call `_send_server_message()` and to their test fixtures.

## Evidence

### 1. Core Functions Reading ADMINS/MANAGERS

#### **File: `django/core/mail/__init__.py` (Lines 127-194)**
- `_send_server_message()` (lines 127-167): Central function that reads settings, detects tuple format, issues deprecation warning, and extracts email addresses
- `mail_admins()` (lines 169-180): Wrapper calling `_send_server_message(setting_name="ADMINS")`
- `mail_managers()` (lines 183-194): Wrapper calling `_send_server_message(setting_name="MANAGERS")`

**Key Logic (lines 141-148):**
```python
if all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
    warnings.warn(
        f"Using (name, address) pairs in the {setting_name} setting is deprecated."
        " Replace with a list of email address strings.",
        RemovedInDjango70Warning,
        stacklevel=2,
    )
    recipients = [a[1] for a in recipients]
```

#### **File: `django/utils/log.py` (Lines 79-100)**
- `AdminEmailHandler.emit()` (lines 94-135): Logs exceptions by calling `mail_admins()`
- Early return at line 97 checks: `if not settings.ADMINS`
- Calls `self.send_mail()` which delegates to `mail.mail_admins()` at line 138

#### **File: `django/middleware/common.py` (Lines 118-141)**
- `BrokenLinkEmailsMiddleware.process_response()` (lines 119-144): Handles 404 errors by calling `mail_managers()` at line 129
- No direct reading of settings; uses `mail_managers()` wrapper

#### **File: `django/core/management/commands/sendtestemail.py`**
- Command implementation uses `mail_admins()` and `mail_managers()` with `--admins` and `--managers` flags
- No direct settings access; delegates to wrapper functions

### 2. Settings Definition & Documentation

#### **File: `django/conf/global_settings.py` (Lines 20-174)**
- Line 25: `ADMINS = []` - Default setting definition (with old format in comment on line 25: `# [('Full Name', 'email@example.com'), ...]`)
- Line 174: `MANAGERS = ADMINS` - Default (mirrors ADMINS)

#### **File: `docs/ref/settings.txt`**
- Lines 43-62 (ADMINS): Documents current format as list of email strings with example: `["john@example.com", '\"Ng, Mary\" <mary@example.com>']`
- Lines 2070-2084 (MANAGERS): References ADMINS format documentation
- Both include `versionchanged:: 6.0` noting tuple format was removed in favor of email strings

### 3. Type Validation & Format Checking

#### **File: `django/core/mail/__init__.py` (Lines 150-155)**
Validation happens after tuple conversion:
```python
if not isinstance(recipients, (list, tuple)) or not all(
    isinstance(address, (str, Promise)) for address in recipients
):
    raise ImproperlyConfigured(
        f"The {setting_name} setting must be a list of email address strings."
    )
```

This validation:
- Accepts both lists and tuples (interchangeable)
- Requires each element to be a string or lazy string (`Promise`)
- Raises `ImproperlyConfigured` if format is invalid
- Does NOT validate email address format itself

### 4. Test Files Using Old/New Format

#### **File: `tests/mail/tests.py`**

**Test: `test_mail_admins_and_managers()` (lines 1782-1805)**
- Tests NEW format: string list `['\"Name, Full\" <test@example.com>']`
- Tests both lists and tuples as valid: `["test@example.com", "other@example.com"]` and tuple version
- Tests lazy strings: `[gettext_lazy("test@example.com")]`
- Validates that email addresses are properly formatted in message headers

**Test: `test_deprecated_admins_managers_tuples()` (lines 1865-1888)**
- Tests OLD format: `[("nobody", "nobody@example.com"), ("other", "other@example.com")]`
- Also tests list variant: `[["nobody", "nobody@example.com"], ["other", "other@example.com"]]`
- Verifies deprecation warning is issued: `RemovedInDjango70Warning`
- Verifies tuple address is correctly extracted: `[str(address) for _, address in value]`

**Test: `test_wrong_admins_managers()` (lines 1890-1913)**
- Tests invalid formats:
  - String instead of list: `"test@example.com"` (rejected)
  - Lazy string instead of list: `gettext_lazy("test@example.com")` (rejected)
  - 3-tuple: `[("name", "test", "example.com")]` (rejected)
  - Malformed tuple: `[("Name <test@example.com",)]` (rejected)
  - Empty list in list: `[[]]` (rejected)
- Verifies `ImproperlyConfigured` exception is raised

#### **File: `tests/mail/test_sendtestemail.py`**
- Uses NEW string format throughout
- Line 7: `ADMINS=["admin@example.com", "admin_and_manager@example.com"]`
- Line 8: `MANAGERS=["manager@example.com", "admin_and_manager@example.com"]`
- Tests verify recipients list correctly matches settings

#### **File: `tests/logging_tests/tests.py`**

**Test: `AdminEmailHandlerTest.test_accepts_args()` (lines 250-280)**
- Line 251: `ADMINS=[\"admin@example.com\"]` - new string format
- Verifies admin email receives exception logs

**Test: `AdminEmailHandlerTest.test_accepts_args_and_request()` (lines 282-319)**
- Line 283: `ADMINS=[\"admin@example.com\"]` - new string format

**Test: `AdminEmailHandlerTest.test_subject_accepts_newlines()` (lines 321-341)**
- Line 343: `ADMINS=[\"admin@example.com\"]` - new string format

**Test: `AdminEmailHandlerTest.test_uses_custom_email_backend()` (lines 343-372)**
- Line 344: `ADMINS=[\"admin@example.com\"]` - new string format

**Test: `AdminEmailHandlerTest.test_emit_non_ascii()` (lines 374-384)**
- Line 375: `ADMINS=[\"admin@example.com\"]` - new string format

**Test: `AdminEmailHandlerTest.test_emit_no_admins()` (lines 474-490)**
- Line 474: `@override_settings(ADMINS=[])` - explicitly empty, no emails sent

#### **File: `tests/middleware/tests.py`**
- Line 392: `MANAGERS=[\"manager@example.com\"]` - new string format
- Tests `BrokenLinkEmailsMiddleware` with managers setting

### 5. Email Address Formatting

#### **File: `django/core/mail/message.py` (Lines 79-120)**
- `sanitize_address()` function handles email formatting
- Lines 84-103: Distinguishes between string addresses and tuple format
- If tuple: unpacks as `(name, address)` - this function still supports OLD format
- If string: parses email address to extract name and domain parts
- Used internally by `EmailMessage` for all recipient processing

This function will need NO changes during migration - it already handles string-only format properly via RFC 5322 parsing (lines 87-95).

### 6. Documentation References

#### **File: `docs/ref/settings.txt`**
- **ADMINS setting** (lines 42-62):
  - Documents new format as list of email strings
  - Includes versionchanged note for 6.0
  - Example: `ADMINS = ["john@example.com", '\"Ng, Mary\" <mary@example.com>']`

- **MANAGERS setting** (lines 2070-2084):
  - References ADMINS format
  - Includes versionchanged note for 6.0

- **SERVER_EMAIL** (lines 2554-2559):
  - References ADMINS/MANAGERS for error email source

#### **File: `docs/topics/email.txt`**
- **`mail_admins()` function** (lines 167-177):
  - Documents that it sends to "site admins, as defined in the :setting:`ADMINS` setting"
  - No explicit format documentation (relies on settings.txt)

- **`mail_managers()` function** (lines 188-192):
  - Documents that it sends to "site managers, as defined in the :setting:`MANAGERS` setting"
  - No explicit format documentation

#### **File: `docs/howto/error-reporting.txt`**
- Documents error email recipients but references settings documentation
- No format examples

#### **File: `docs/releases/6.0.txt` (Lines 331-334)**
- Documents deprecation: "Setting :setting:`ADMINS` or :setting:`MANAGERS` to a list of (name, address) tuples is deprecated"
- Provides migration guidance:
  - Use list of email address strings
  - To include name: format as `'\"Name\" <address>'` or use `email.utils.formataddr`

#### **File: `docs/internals/deprecation.txt` (Lines 31-32)**
- Lists removal for Django 7.0: "Support for setting the ``ADMINS`` or ``MANAGERS`` settings to a list of (name, address) tuples will be removed"

#### **File: `docs/ref/django-admin.txt` (Lines 1051-1059)**
- Documents `sendtestemail` command `--admins` and `--managers` flags
- References settings but no format specification

### 7. Global Settings Comment

#### **File: `django/conf/global_settings.py` (Line 25)**
- Comment shows OLD format: `# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]`
- Needs update to show NEW format examples

## Affected Components

### Direct Users (Read Settings)
1. **django.core.mail** (5 functions)
   - `_send_server_message()` - central processor
   - `mail_admins()`
   - `mail_managers()`
   - `send_mail()` - indirectly (creates EmailMessage)
   - `send_mass_mail()` - indirectly (creates EmailMessage)

2. **django.utils.log**
   - `AdminEmailHandler.emit()` - via `mail_admins()`
   - `AdminEmailHandler.send_mail()` - calls `mail.mail_admins()`

3. **django.middleware.common**
   - `BrokenLinkEmailsMiddleware.process_response()` - calls `mail_managers()`

4. **django.core.management.commands**
   - `sendtestemail` - calls `mail_admins()` and `mail_managers()`

### Test Suites (6 test files)
1. `tests/mail/tests.py` - MailTestCase (600+ lines of email tests)
2. `tests/mail/test_sendtestemail.py` - SendTestEmailManagementCommand
3. `tests/logging_tests/tests.py` - AdminEmailHandlerTest
4. `tests/middleware/tests.py` - BrokenLinkEmailsMiddlewareTest
5. `tests/views/test_debug.py` - Potential error reporting tests
6. Various other test files using `@override_settings(ADMINS=...)`

### Documentation (3 files)
1. `docs/ref/settings.txt` - ADMINS/MANAGERS/SERVER_EMAIL settings
2. `docs/topics/email.txt` - mail_admins()/mail_managers() functions
3. `docs/howto/error-reporting.txt` - Error email setup
4. `docs/howto/deployment/checklist.txt` - Email configuration checklist
5. `docs/ref/django-admin.txt` - sendtestemail command
6. Release notes already documented

## Third-Party Compatibility Concerns

### Impact When Django 7.0 Removes Support

1. **User Projects with Old Format**
   - Projects using tuple format will raise `ImproperlyConfigured` exception
   - No gradual degradation - immediate failure
   - Error message is clear and actionable

2. **Third-Party Apps Reading Settings**
   - Apps that directly import and read `settings.ADMINS` or `settings.MANAGERS` will break if they expect tuples
   - Example: custom logging handlers, email notification systems
   - **Recommendation**: Document migration path in Django 7.0 release notes

3. **Monkey-Patched Settings**
   - Tests monkey-patching `mail.mail_admins` should continue working (seen in `logging_tests/tests.py` lines 361-372)
   - No breaking changes to function signatures

4. **Email Backend Compatibility**
   - Email backends receive recipients as list of strings - fully compatible
   - No backend changes needed

## Migration Checklist

### Phase 1: Code Changes (Removal of Deprecation Code)
Target: Django 7.0

| File | Change Needed | Line(s) | Type | Priority |
|------|---------------|---------|------|----------|
| `django/core/mail/__init__.py` | Remove deprecation warning and tuple detection logic | 141-148 | Remove code | HIGH |
| `django/core/mail/__init__.py` | Remove fallback extraction logic: `recipients = [a[1] for a in recipients]` | 148 | Remove code | HIGH |
| `django/core/mail/__init__.py` | Update validation to reject any tuple format | 150-155 | Modify validation | HIGH |
| `django/core/mail/message.py` | Verify `sanitize_address()` still works with string-only input | 79-103 | Test coverage | MEDIUM |
| `django/conf/global_settings.py` | Update comment example from tuple format to string format | 25 | Documentation | LOW |

### Phase 2: Test Updates
Target: After code changes

| File | Change Needed | Current Tests | Action |
|------|---------------|----------------|--------|
| `tests/mail/tests.py` | Remove `test_deprecated_admins_managers_tuples()` | Lines 1865-1888 | Delete test |
| `tests/mail/tests.py` | Update `test_wrong_admins_managers()` | Lines 1890-1913 | Remove tuple examples (lines 1896-1897 commented) |
| All test files | Verify all `@override_settings(ADMINS=...)` use string format | Various | Audit + fix |
| `tests/logging_tests/tests.py` | Verify string format used | Lines 251, 283, 343, 375 | No changes needed ✓ |
| `tests/mail/test_sendtestemail.py` | Verify string format used | Lines 7-8 | No changes needed ✓ |
| `tests/middleware/tests.py` | Verify string format used | Line 392 | No changes needed ✓ |

### Phase 3: Documentation Updates
Target: Django 6.0 release notes (already partially done)

| File | Change Needed | Content | Priority |
|------|---------------|---------|----------|
| `docs/releases/6.0.txt` | Verify deprecation notice is clear | Lines 331-334 | No changes needed ✓ |
| `docs/internals/deprecation.txt` | Ensure Django 7.0 removal is documented | Lines 31-32 | No changes needed ✓ |
| `docs/ref/settings.txt` | Verify examples use new format | Lines 55-57, 2077-2079 | No changes needed ✓ |
| Django 7.0 release notes | Add removal section | TBD | Will need to create |

### Phase 4: User Migration (Guidance)

Provide clear migration path in documentation:

**For users with old tuple format:**
```python
# Old (Django < 6.0)
ADMINS = [("John Admin", "john@example.com"), ("Jane Admin", "jane@example.com")]

# New (Django 6.0+)
ADMINS = ["john@example.com", "jane@example.com"]

# With names (if needed)
ADMINS = ['"John Admin" <john@example.com>', '"Jane Admin" <jane@example.com>']

# Or using email.utils.formataddr
from email.utils import formataddr
ADMINS = [
    formataddr(("John Admin", "john@example.com")),
    formataddr(("Jane Admin", "jane@example.com")),
]
```

## Recommendation

The migration is **low-risk and straightforward**:

1. **Current State (Django 6.0)**: Full backward compatibility with deprecation warnings
2. **Django 6.x**: All code already handles both formats; test suite uses new format
3. **Django 7.0**: Simple removal of 6 lines of deprecation logic and tuple handling

**Blockers Identified**: None - all migration infrastructure is already in place

**Required Actions**:
1. ✅ Remove deprecation warning code from `_send_server_message()` (lines 141-148)
2. ✅ Remove tuple extraction logic (line 148)
3. ✅ Ensure validation rejects tuples
4. ✅ Remove `test_deprecated_admins_managers_tuples()` test
5. ✅ Update comment in `global_settings.py` line 25

**Timeline**: Can be implemented in any Django 7.0 minor release with no upstream or downstream impact on third-party apps that have already migrated to the new format.
