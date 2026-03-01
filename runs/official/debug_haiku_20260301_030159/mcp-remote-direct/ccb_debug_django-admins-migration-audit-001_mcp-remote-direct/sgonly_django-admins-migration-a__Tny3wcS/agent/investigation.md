# Investigation Report: Django ADMINS/MANAGERS Settings Format Migration Audit

## Summary

Django is migrating the `ADMINS` and `MANAGERS` settings from tuple format `(name, email)` to simple email address strings. This audit identifies all code that consumes these settings and must be updated or is already prepared for the migration. Deprecation warnings are already in place (Django 6.0), with removal planned for Django 7.0 (RemovedInDjango70Warning).

## Root Cause

The tuple format `[(name, email), ...]` for ADMINS/MANAGERS settings is being deprecated because Django never used the name portion—only the email address. The new format is simply `[email, ...]` where email addresses can optionally include a display name in RFC 5322 format (e.g., `'"Name" <email@example.com>'`).

## Evidence: File-by-File Analysis

### 1. Core Mail Module (`django/core/mail/__init__.py`)

**Lines 127-166: `_send_server_message()` function**

This is the key function that processes ADMINS and MANAGERS settings:

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

    # RemovedInDjango70Warning (lines 140-148)
    if all(isinstance(a, (list, tuple)) and len(a) == 2 for a in recipients):
        warnings.warn(
            f"Using (name, address) pairs in the {setting_name} setting is deprecated."
            " Replace with a list of email address strings.",
            RemovedInDjango70Warning,
            stacklevel=2,
        )
        recipients = [a[1] for a in recipients]  # Extract email (second element)

    if not isinstance(recipients, (list, tuple)) or not all(
        isinstance(address, (str, Promise)) for address in recipients
    ):
        raise ImproperlyConfigured(
            f"The {setting_name} setting must be a list of email address strings."
        )

    mail = EmailMultiAlternatives(
        subject="%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        body=message,
        from_email=settings.SERVER_EMAIL,
        to=recipients,
        connection=connection,
    )
    if html_message:
        mail.attach_alternative(html_message, "text/html")
    mail.send(fail_silently=fail_silently)
```

**Key Points:**
- Lines 141-148: Detects deprecated tuple format via `isinstance(a, (list, tuple)) and len(a) == 2`
- Automatically extracts email from second position: `recipients = [a[1] for a in recipients]`
- Raises `RemovedInDjango70Warning` when deprecated format detected
- Lines 150-155: Validates recipients are list/tuple of email strings (after deprecation path)

**Called by:**
- `mail_admins()` (line 169-180) - passes `setting_name="ADMINS"`
- `mail_managers()` (line 183-194) - passes `setting_name="MANAGERS"`

### 2. Middleware: Broken Link Notifications (`django/middleware/common.py`)

**Lines 118-141: `BrokenLinkEmailsMiddleware.process_response()`**

```python
class BrokenLinkEmailsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        """Send broken link emails for relevant 404 NOT FOUND responses."""
        if response.status_code == 404 and not settings.DEBUG:
            domain = request.get_host()
            path = request.get_full_path()
            referer = request.META.get("HTTP_REFERER", "")

            if not self.is_ignorable_request(request, path, domain, referer):
                ua = request.META.get("HTTP_USER_AGENT", "<none>")
                ip = request.META.get("REMOTE_ADDR", "<none>")
                mail_managers(
                    "Broken %slink on %s" % (...),
                    "Referrer: %s\nRequested URL: %s\nUser agent: %s\nIP address: %s\n" % (...)
                )
```

**Key Point:** Calls `mail_managers()` at line 129. Will automatically benefit from the deprecation handling in `_send_server_message()`.

### 3. Logging: Error Email Handler (`django/utils/log.py`)

**Lines 79-140: `AdminEmailHandler` class**

```python
class AdminEmailHandler(logging.Handler):
    """An exception log handler that emails log entries to site admins."""

    def emit(self, record):
        # Early return when no email will be sent.
        if (
            not settings.ADMINS
            # Method not overridden.
            and self.send_mail.__func__ is AdminEmailHandler.send_mail
        ):
            return
        # ... processing ...
        self.send_mail(subject, message, fail_silently=True, html_message=html_message)

    def send_mail(self, subject, message, *args, **kwargs):
        mail.mail_admins(
            subject, message, *args, connection=self.connection(), **kwargs
        )
```

**Key Points:**
- Line 97: Checks `not settings.ADMINS` to early-return if no recipients
- Line 138: Calls `mail.mail_admins()` which uses `_send_server_message()` internally

### 4. Management Command (`django/core/management/commands/sendtestemail.py`)

**Lines 1-46: `sendtestemail` command**

```python
def handle(self, *args, **kwargs):
    # Lines 35-40: Regular email sending
    send_mail(
        subject=subject,
        message="If you're reading this, it was successful.",
        from_email=None,
        recipient_list=kwargs["email"],
    )

    if kwargs["managers"]:
        mail_managers(subject, "This email was sent to the site managers.")  # Line 43

    if kwargs["admins"]:
        mail_admins(subject, "This email was sent to the site admins.")  # Line 46
```

**Key Points:**
- Lines 43, 46: Calls `mail_managers()` and `mail_admins()` which use the deprecation-aware `_send_server_message()`

### 5. Default Settings Definition (`django/conf/global_settings.py`)

**Lines 24-26:**

```python
# People who get code error notifications. In the format
# [('Full Name', 'email@example.com'), ('Full Name', 'anotheremail@example.com')]
ADMINS = []
```

**Lines 171-174:**

```python
# Not-necessarily-technical managers of the site. They get broken link
# notifications and other various emails.
MANAGERS = ADMINS
```

**Issue:** Comment on lines 24-25 still documents the old tuple format. This should be updated to show the new string format.

### 6. Test Files

#### `tests/mail/tests.py`

**Lines 1782-1806: `test_mail_admins_and_managers()`** - Tests NEW format (email strings):
```python
def test_mail_admins_and_managers(self):
    tests = (
        # The ADMINS and MANAGERS settings are lists of email strings.
        ['\"Name, Full\" <test@example.com>'],
        # Lists and tuples are interchangeable.
        ["test@example.com", "other@example.com"],
        (\"test@example.com\", \"other@example.com\"),
        # Lazy strings are supported.
        [gettext_lazy(\"test@example.com\")],
    )
```

**Lines 1864-1888: `test_deprecated_admins_managers_tuples()`** - Tests OLD format with deprecation:
```python
# RemovedInDjango70Warning.
def test_deprecated_admins_managers_tuples(self):
    tests = (
        [(\"nobody\", \"nobody@example.com\"), (\"other\", \"other@example.com\")],
        [[\"nobody\", \"nobody@example.com\"], [\"other\", \"other@example.com\"]],
    )
    for setting, mail_func in (
        (\"ADMINS\", mail_admins),
        (\"MANAGERS\", mail_managers),
    ):
        msg = (
            f\"Using (name, address) pairs in the {setting} setting is deprecated.\"
            \" Replace with a list of email address strings.\"
        )
        for value in tests:
            self.flush_mailbox()
            with (...):
                with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
                    mail_func(\"subject\", \"content\")
```

**Lines 1890-1900: `test_wrong_admins_managers()`** - Tests invalid formats:
```python
def test_wrong_admins_managers(self):
    tests = (
        \"test@example.com\",
        gettext_lazy(\"test@example.com\"),
        # RemovedInDjango70Warning: uncomment these cases when support for
        # deprecated (name, address) tuples is removed.
        #    [(\"nobody\", \"nobody@example.com\"), (\"other\", \"other@example.com\")],
        #    [[\"nobody\", \"nobody@example.com\"], [\"other\", \"other@example.com\"]],
        [(\"name\", \"test\", \"example.com\")],  # Invalid: 3-tuple
        [(\"Name <test@example.com\",)],  # Invalid: 1-tuple
        [[]],  # Invalid: empty list
```

**Lines 1822-1835, 1837-1851, 1853-1862:** Additional tests using NEW format with `@override_settings(ADMINS=[...], MANAGERS=[...])`

#### `tests/mail/test_sendtestemail.py`

**Lines 6-9: Uses NEW format:**
```python
@override_settings(
    ADMINS=[\"admin@example.com\", \"admin_and_manager@example.com\"],
    MANAGERS=[\"manager@example.com\", \"admin_and_manager@example.com\"],
)
```

All tests in this file expect email strings.

#### `tests/logging_tests/tests.py`

**Lines 235-280: `AdminEmailHandlerTest` class**

Uses NEW format: `@override_settings(ADMINS=[\"admin@example.com\"])`

### 7. Documentation Files

#### `docs/conf/global_settings.py` (lines 24-26)
- **Issue:** Comment shows old tuple format
- **Status:** Needs update to show new string format

#### `docs/ref/settings.txt`

**Lines 42-62: ADMINS setting documentation**
```
Default: [] (Empty list)

A list of all the people who get code error notifications. When
DEBUG=False and AdminEmailHandler is configured...

Each item in the list should be an email address string. Example::

    ADMINS = [\"john@example.com\", '\"Ng, Mary\" <mary@example.com>']

.. versionchanged:: 6.0

    In older versions, required a list of (name, address) tuples.
```

**Status:** ✅ Already documents new format with versionchanged note

**Lines 2070-2084: MANAGERS setting documentation**
```
Default: [] (Empty list)

A list in the same format as :setting:`ADMINS` that specifies who should get
broken link notifications...

.. versionchanged:: 6.0

    In older versions, required a list of (name, address) tuples.
```

**Status:** ✅ Already documents new format with versionchanged note

#### `docs/releases/6.0.txt` (lines 331-334)

**Deprecation notice:**
```
* Setting :setting:`ADMINS` or :setting:`MANAGERS` to a list of (name, address)
  tuples is deprecated. Set to a list of email address strings instead. Django
  never used the name portion. To include a name, format the address string as
  ``'\"Name\" <address>'`` or use Python's :func:`email.utils.formataddr`.
```

**Status:** ✅ Deprecation documented

#### `docs/internals/deprecation.txt` (lines 31-32)

**Removal schedule:**
```
* Support for setting the ``ADMINS`` or ``MANAGERS`` settings to a list of
  (name, address) tuples will be removed.
```

**Status:** ✅ Removal scheduled for Django 7.0

#### `docs/topics/email.txt` (lines 166-193)

Documents `mail_admins()` and `mail_managers()` functions. No tuple format shown.

**Status:** ✅ Documentation is correct

#### `docs/howto/error-reporting.txt` (lines 44-45, 20-23, 64-65)

References to ADMINS and MANAGERS in error reporting context. No tuple format examples.

**Status:** ✅ Documentation is correct

#### `docs/howto/deployment/checklist.txt` (lines 251-252)

References to ADMINS and MANAGERS in deployment context.

**Status:** ✅ Documentation is correct

## Affected Components

1. **Core Mail System** (`django.core.mail`)
   - `_send_server_message()` - Already handles both old and new formats with deprecation
   - `mail_admins()` - Already compatible
   - `mail_managers()` - Already compatible

2. **Middleware** (`django.middleware.common`)
   - `BrokenLinkEmailsMiddleware` - Already compatible (calls mail_managers)

3. **Logging** (`django.utils.log`)
   - `AdminEmailHandler` - Already compatible (calls mail_admins)

4. **Management Commands** (`django.core.management.commands`)
   - `sendtestemail` - Already compatible (calls mail_admins/mail_managers)

5. **Settings** (`django.conf`)
   - `global_settings.py` - Comment needs update (the code is already fine)

6. **Tests** (`tests/`)
   - `tests/mail/tests.py` - Has comprehensive coverage for both formats
   - `tests/mail/test_sendtestemail.py` - Uses new format
   - `tests/logging_tests/tests.py` - Uses new format

7. **Documentation** (`docs/`)
   - Most documentation already updated for 6.0 migration
   - Minor comment in global_settings.py needs update

## Third-Party Compatibility Concerns

### Current State (Django 6.0+)
- **Backward Compatible:** ✅ Old tuple format still works with deprecation warning
- **Users can use:** Either format without code breakage
- **Deprecation Path:** RemovedInDjango70Warning is emitted in Django 6.0+

### After Django 7.0 Removal
- **Breaking Change:** ❌ Code using old format will raise `ImproperlyConfigured`
- **Error Message:** "The ADMINS/MANAGERS setting must be a list of email address strings."
- **User Migration Required:** Projects must update their settings.py

### Migration Path for Users
1. **Now (Django 6.0+):** Update settings to use string format, address deprecation warnings
2. **Old format:** `ADMINS = [('John', 'john@example.com')]`
3. **New format:** `ADMINS = ['john@example.com']` or `ADMINS = ['"John" <john@example.com>']`

## Validation & Type Checking

### Current Validation (`django/core/mail/__init__.py` lines 150-155)

```python
if not isinstance(recipients, (list, tuple)) or not all(
    isinstance(address, (str, Promise)) for address in recipients
):
    raise ImproperlyConfigured(
        f"The {setting_name} setting must be a list of email address strings."
    )
```

**Status:** ✅ Validation already in place for new format

**Supports:**
- List or tuple of email strings
- Lazy strings (Promise objects)
- Display names in RFC 5322 format: `'"Name" <email@example.com>'`

## Migration Checklist: Files That Need Changes

### Priority 1: Must Change Before Django 7.0 Removal

| File | Line(s) | Change Needed | Status |
|------|---------|---------------|--------|
| `django/conf/global_settings.py` | 24-25 | Update comment to show new string format instead of tuple format | ⚠️ Comment outdated |
| `tests/mail/tests.py` | 1894-1897 | Uncomment invalid format test cases (tuple-related) when deprecation is removed | 📋 Todo for 7.0 |

### Priority 2: Information Only (No Changes Needed)

| File | Line(s) | Reason | Status |
|------|---------|--------|--------|
| `django/core/mail/__init__.py` | 140-148 | Remove deprecation check and tuple-to-string conversion | 📋 Todo for 7.0 |
| `django/utils/deprecation.py` | 11 | Remove RemovedInDjango70Warning class | 📋 Todo for 7.0 |
| `tests/mail/tests.py` | 1864-1888 | Remove `test_deprecated_admins_managers_tuples()` test | 📋 Todo for 7.0 |
| `docs/releases/6.0.txt` | 331-334 | Update to reflect removal (move to 7.0 release notes) | 📋 Todo for 7.0 |
| `docs/internals/deprecation.txt` | 31-32 | Remove from 7.0 removal list after code changes | 📋 Todo for 7.0 |

### Priority 3: Already Correct (No Changes Needed)

| File | Status | Reason |
|------|--------|--------|
| `django/core/mail/__init__.py` - `mail_admins()` | ✅ | Already compatible with new format |
| `django/core/mail/__init__.py` - `mail_managers()` | ✅ | Already compatible with new format |
| `django/middleware/common.py` | ✅ | Uses mail_managers() which is compatible |
| `django/utils/log.py` | ✅ | Uses mail_admins() which is compatible |
| `django/core/management/commands/sendtestemail.py` | ✅ | Uses compatible functions |
| `docs/ref/settings.txt` | ✅ | Already documents new format with versionchanged |
| `docs/releases/6.0.txt` | ✅ | Deprecation properly documented |
| `docs/topics/email.txt` | ✅ | No tuple format shown |
| `docs/howto/error-reporting.txt` | ✅ | Correct documentation |
| `tests/mail/tests.py` - `test_mail_admins_and_managers()` | ✅ | Tests new format correctly |
| `tests/mail/test_sendtestemail.py` | ✅ | Uses new format in tests |
| `tests/logging_tests/tests.py` | ✅ | Uses new format in tests |

## Recommendation

### For Django 6.x (Current Deprecation Phase)

1. **Update comment in `django/conf/global_settings.py` lines 24-25**
   - Change: Show new email string format instead of tuple format
   - Rationale: Reduces confusion for new Django users reading defaults

### For Django 7.0 (Removal Phase)

1. **Remove tuple handling from `django/core/mail/__init__.py` lines 140-148**
   - Delete the deprecation check that detects and converts old format
   - Keep validation (lines 150-155) that requires email strings

2. **Remove `test_deprecated_admins_managers_tuples()` from `tests/mail/tests.py`**
   - This test specifically checks deprecated behavior
   - No longer needed in Django 7.0+

3. **Update `test_wrong_admins_managers()` in `tests/mail/tests.py` lines 1894-1897**
   - Uncomment the tuple-related invalid format tests
   - These should now raise `ImproperlyConfigured` instead of being converted

4. **Clean up deprecation infrastructure**
   - Remove `RemovedInDjango70Warning` from `django/utils/deprecation.py` if no other uses exist
   - Remove from `tests/runtests.py` line 49 if applicable

5. **Update documentation**
   - Move deprecation notice from `docs/releases/6.0.txt` to `docs/releases/7.0.txt`
   - Remove from `docs/internals/deprecation.txt`
   - Update `docs/ref/settings.txt` to remove the versionchanged note

## Conclusion

The codebase is **well-prepared** for the ADMINS/MANAGERS format migration. The deprecation infrastructure is already in place with appropriate warnings and backward compatibility handling. The main task for Django 7.0 will be removing the deprecation code path and updating tests, not making sweeping changes across the codebase.

**Current Status:** All code paths that consume ADMINS/MANAGERS settings are already compatible with the new string format while maintaining backward compatibility with the old tuple format through deprecation warnings.
