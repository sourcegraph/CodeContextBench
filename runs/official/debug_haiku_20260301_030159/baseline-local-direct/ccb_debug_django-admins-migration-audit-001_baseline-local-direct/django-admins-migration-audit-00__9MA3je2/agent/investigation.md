# Investigation Report: Django ADMINS/MANAGERS Settings Format Migration (Ticket #36138)

## Summary

Django currently defines `ADMINS` and `MANAGERS` settings as lists of 2-tuples in the format `[(name, email), ...]`. The migration to change these to simple email string lists `[email, ...]` requires code changes in 6 core Django files, 5 test files, and updates to 10+ documentation files. The most critical code path is `django.core.mail._send_server_message()` which validates and unpacks the tuple format.

## Root Cause

The tuple format `(name, email)` is consumed in three core locations:

1. **Validation**: `django.core.mail._send_server_message()` line 135 validates that each item is a 2-tuple
2. **Email Extraction**: `django.core.mail._send_server_message()` line 142 unpacks and extracts the email address via `a[1]`
3. **Reference Checks**: `django.utils.log.AdminEmailHandler.emit()` line 97 performs a boolean check on `settings.ADMINS`

## Evidence

### Core Files Reading/Processing Settings

#### 1. **django/core/mail/__init__.py**
   - **Lines 131-143**: `_send_server_message()` function
     - Line 131: `recipients = getattr(settings, setting_name)` - Reads ADMINS/MANAGERS
     - Line 135: `if not all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):` - **CRITICAL**: Validates 2-tuple format
     - Line 136: `raise ValueError(f"The {setting_name} setting must be a list of 2-tuples.")` - Error message for old format validation
     - Line 142: `to=[a[1] for a in recipients]` - **CRITICAL**: Unpacks and extracts email from second position of tuple
   - Lines 150-175: `mail_admins()` and `mail_managers()` functions call `_send_server_message()`

#### 2. **django/utils/log.py**
   - **Lines 97-101**: `AdminEmailHandler.emit()` method
     - Line 97: `if (not settings.ADMINS and self.send_mail.__func__ is AdminEmailHandler.send_mail):` - Boolean check only (no unpacking)
     - Line 138: `mail.mail_admins()` - Calls mail_admins function which uses _send_server_message

#### 3. **django/conf/global_settings.py**
   - **Line 26**: `ADMINS = []` - Default definition
   - **Lines 24-25**: Comment states: `# People who get code error notifications. In the format # [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]` - **DOCUMENTATION**: Shows old tuple format
   - **Line 50+ (not shown)**: `MANAGERS` setting with similar documentation

#### 4. **django/core/management/commands/sendtestemail.py**
   - **Lines 42-46**: Uses `mail_managers()` and `mail_admins()` functions indirectly
   - Does NOT directly access or unpack ADMINS/MANAGERS settings
   - Command-line options reference settings but no direct format dependency

#### 5. **django/middleware/common.py**
   - **Lines 129-142**: `BrokenLinkEmailsMiddleware.process_response()`
   - **Line 129**: `mail_managers()` function call - Indirect consumption, no direct unpacking

### Test Files Using Old Format

#### 1. **tests/mail/test_sendtestemail.py**
   - **Lines 7-14**: `@override_settings()` decorator uses tuple format
     ```python
     ADMINS=(
         ("Admin", "admin@example.com"),
         ("Admin and Manager", "admin_and_manager@example.com"),
     ),
     MANAGERS=(
         ("Manager", "manager@example.com"),
         ("Admin and Manager", "admin_and_manager@example.com"),
     ),
     ```
   - Multiple test methods depend on this fixture format

#### 2. **tests/mail/tests.py**
   - **Lines 1780-1803**: `test_mail_admins_and_managers()` method
     - Tests multiple tuple format variations:
       ```python
       [("Name, Full", "test@example.com")],
       [["Name, Full", "test@example.com"], ["ignored", "other@example.com"]],
       (("", "test@example.com"), ("", "other@example.com")),
       [(gettext_lazy("Name, Full"), gettext_lazy("test@example.com"))],
       ```
     - Line 1802: `expected_to = ", ".join([str(address) for _, address in value])` - **Unpacks tuple with underscore pattern**
   - **Lines 1806-1828**: `test_html_mail_managers()` and `test_html_mail_admins()` - Use `@override_settings` with tuple format
   - **Lines 1144-1161**: `test_connection_arg_mail_admins()` and `test_connection_arg_mail_managers()` - Indirect usage via mail functions

#### 3. **tests/middleware/tests.py**
   - **Line 392**: `MANAGERS=[("PHD", "PHB@dilbert.com")]` - Override with tuple format

#### 4. **tests/view_tests/tests/test_debug.py**
   - **Lines 1454, 1490, 1533**: `@override_settings(ADMINS=[("Admin", "admin@fattie-breakie.com")])` - Three locations with tuple format

#### 5. **tests/logging_tests/tests.py**
   - No explicit override found but may use DEFAULT_LOGGING which references AdminEmailHandler

### Documentation Files with Old Format Examples

#### 1. **docs/ref/settings.txt**
   - **Lines 43-57**: `ADMINS` setting documentation
     - Line 55: `Each item in the list should be a tuple of (Full name, email address). Example::` - **DOCUMENTATION REQUIREMENT**
     - Line 57: Example: `[("John", "john@example.com"), ("Mary", "mary@example.com")]`
   - **Lines 2066-2073**: `MANAGERS` setting documentation
     - Line 2073: `A list in the same format as :setting:`ADMINS`...` - Cross-reference

#### 2. **docs/topics/email.txt**
   - **Lines 170-191**: `mail_admins()` and `mail_managers()` function documentation
   - Line 170: References `:setting:`ADMINS` setting`

#### 3. **docs/howto/error-reporting.txt**
   - **Lines 22, 25, 45**: Multiple references to ADMINS setting
   - Lines 22-27: Describes error notification process
   - No explicit format shown but implies tuple unpacking in explanation

#### 4. **docs/topics/logging.txt**
   - **Lines 333-409**: DEFAULT_LOGGING configuration reference
   - Line 393-394: Documents `mail_admins` handler: "emails any `ERROR` (or higher) message to the site :setting:`ADMINS`"

#### 5. **docs/ref/logging.txt**
   - **Lines 95-99**: Default logging configuration example
   - References AdminEmailHandler which depends on format

#### 6. **docs/howto/deployment/checklist.txt**
   - References settings but specific format unclear from grep

#### 7. **docs/ref/django-admin.txt**
   - References sendtestemail command

#### Additional documentation files found but content not fully examined:
   - docs/releases/3.0.txt
   - docs/ref/middleware.txt

## Affected Components

### Core Components
1. **django.core.mail** - Email delivery infrastructure
   - `_send_server_message()` - Validation and unpacking logic
   - `mail_admins()` - Admin email dispatch
   - `mail_managers()` - Manager email dispatch

2. **django.utils.log** - Logging and error reporting
   - `AdminEmailHandler` - Email-based error logging

3. **django.conf** - Settings and configuration
   - Global settings defaults

4. **django.middleware.common** - Request/response processing
   - `BrokenLinkEmailsMiddleware` - 404 error reporting

5. **django.core.management** - Management commands
   - `sendtestemail` command - Manual email testing

### Testing Infrastructure
- Mail-related test modules
- Logging test modules
- Debug/error view test modules
- Middleware test modules

### Documentation
- Settings reference documentation
- Email topics documentation
- Error reporting how-to documentation
- Logging reference and topics documentation

## Third-Party Compatibility Concerns

### Breaking Changes for Users
1. **Existing user code** with old format will immediately fail at validation:
   - Error message: `"The {setting_name} setting must be a list of 2-tuples."`
   - No graceful degradation or backward compatibility

2. **Tuple unpacking patterns** in user code:
   - User code like `for name, email in settings.ADMINS` will break
   - User code accessing `admins[i][0]` or `admins[i][1]` will fail with IndexError

3. **Migration path** requirements:
   - Must provide clear deprecation warning in earlier version
   - Need migration guide documentation
   - Should support both formats during transition period

### Third-Party Packages
- Django extensions and admin packages may have their own tuple unpacking
- User code in custom email handlers or logging configurations
- Third-party logging handlers that read these settings

## Recommendation: Migration Checklist

### Phase 1: Deprecation (Current/Next Release)
- [ ] Add deprecation warning in `_send_server_message()` when tuple format detected
- [ ] Update documentation to note upcoming format change
- [ ] Create migration guide document

### Phase 2: Format Validation Updates (After deprecation period)

#### Core Code Changes
- [ ] **django/core/mail/__init__.py**
  - Line 135-142: Replace validation and tuple unpacking with simple string format check
  - Change: `if not all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):`
  - To: `if not all(isinstance(a, str) for a in recipients):`
  - Change: `to=[a[1] for a in recipients]`
  - To: `to=recipients` (recipients is now direct email list)
  - Update error message to reflect new format requirement

- [ ] **django/conf/global_settings.py**
  - Line 24-25: Update comment from tuple format to string format
  - From: `# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]`
  - To: `# ['email1@example.com', 'email2@example.com']`

- [ ] **django/utils/log.py**
  - Line 97: No code change needed (boolean check works with both formats)
  - May need to update related documentation in function docstrings

#### Test File Updates
- [ ] **tests/mail/test_sendtestemail.py**
  - Lines 7-14: Convert @override_settings from tuple format to string list:
    ```python
    ADMINS=("admin@example.com", "admin_and_manager@example.com"),
    MANAGERS=("manager@example.com", "admin_and_manager@example.com"),
    ```

- [ ] **tests/mail/tests.py**
  - Lines 1780-1803: Update test cases to use string format
  - Line 1802: Simplify tuple unpacking to simple string iteration
  - Lines 1806-1828: Update @override_settings decorators
  - Update assertions that expect tuple format

- [ ] **tests/middleware/tests.py**
  - Line 392: Change `MANAGERS=[("PHD", "PHB@dilbert.com")]` to `MANAGERS=["PHB@dilbert.com"]`

- [ ] **tests/view_tests/tests/test_debug.py**
  - Lines 1454, 1490, 1533: Update all three @override_settings calls to string format

- [ ] **tests/logging_tests/tests.py**
  - Verify no direct tuple format dependencies

#### Documentation Updates
- [ ] **docs/ref/settings.txt**
  - Line 55-57: Update ADMINS setting documentation
    - Change description from "tuple of (Full name, email address)"
    - To: "email address string"
    - Update example: `[("John", "john@example.com"), ("Mary", "mary@example.com")]`
    - To: `["john@example.com", "mary@example.com"]`
  - Lines 2066-2073: Update MANAGERS setting similarly

- [ ] **docs/topics/email.txt**
  - No specific format shown but verify all references are accurate
  - May need to update implicit descriptions

- [ ] **docs/howto/error-reporting.txt**
  - No explicit format change needed but verify instructions

- [ ] **docs/topics/logging.txt**
  - Verify AdminEmailHandler documentation is compatible

- [ ] **docs/ref/logging.txt**
  - Verify no examples show tuple format

- [ ] **docs/howto/deployment/checklist.txt**
  - Check for any format-specific references

- [ ] **docs/releases/X.Y.txt** (Next major version release notes)
  - Add section documenting the breaking change
  - Explain migration path from tuple to string format
  - Provide examples of before/after

### Phase 3: Code Cleanup (Optional, Post-Migration)
- [ ] Remove any deprecated tuple format validation code
- [ ] Remove any warning/logging about format conversion
- [ ] Simplify `_send_server_message()` implementation

### Validation Strategy
1. Run full test suite after each change
2. Verify `mail_admins()` and `mail_managers()` work with string list format
3. Verify email recipients extracted correctly
4. Verify AdminEmailHandler still functions
5. Verify BrokenLinkEmailsMiddleware still works
6. Verify sendtestemail management command still works

### Risk Areas
- **AdminEmailHandler**: Relies on empty list check (line 97) - Low risk, works with both formats
- **BrokenLinkEmailsMiddleware**: Indirect usage through mail_managers() - Low risk
- **User Code**: Highest risk - users with custom handlers or format assumptions will break
- **Third-party Packages**: Unknown risk - packages may have their own tuple unpacking

## Notes on Implementation Order

1. **Validation function first**: Update `_send_server_message()` validation logic
2. **Test files second**: Update tests to use new format before running them
3. **Documentation third**: Update all references to old format
4. **Release notes**: Document as breaking change in next major version

## Additional Considerations

- The `sendtestemail` command help text (lines 24, 29) references the old setting names but not the format
- User-facing error messages need to be clear about the new required format
- Consider providing a management command or utility to migrate user settings from old to new format
- Consider adding a check/validation command to warn about non-compliant settings files
