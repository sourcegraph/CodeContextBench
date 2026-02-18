# Task: Generate Comprehensive Docstrings for Django SecurityMiddleware

## Objective

Generate comprehensive, PEP 257-compliant docstrings for Django's `SecurityMiddleware` module located at `django/middleware/security.py`. The existing docstrings have been removed and you must write new ones based on your understanding of the code.

## Target Module

The file `django/middleware/security.py` contains the `SecurityMiddleware` class, which provides several HTTP security features:

- **SSL Redirect**: Redirects HTTP requests to HTTPS based on `SECURE_SSL_REDIRECT`
- **HSTS (HTTP Strict Transport Security)**: Sets the `Strict-Transport-Security` header via `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, and `SECURE_HSTS_PRELOAD`
- **X-Content-Type-Options**: Sets the `X-Content-Type-Options: nosniff` header via `SECURE_CONTENT_TYPE_NOSNIFF`
- **Referrer-Policy**: Sets the `Referrer-Policy` header via `SECURE_REFERRER_POLICY`
- **Cross-Origin-Opener-Policy**: Sets the `Cross-Origin-Opener-Policy` header via `SECURE_CROSS_ORIGIN_OPENER_POLICY`

## Requirements

### What to Document

1. **Class-level docstring** for `SecurityMiddleware`: Describe its purpose, the security headers it manages, and how it integrates into Django's middleware stack.

2. **`__init__` method**: Document the `get_response` callable parameter and how the middleware initializes its configuration from Django settings.

3. **`process_request` method**: Document the `request` parameter (an `HttpRequest` object), the SSL redirect logic, the role of `SECURE_SSL_REDIRECT`, `SECURE_SSL_HOST`, and `SECURE_REDIRECT_EXEMPT`, and the `HttpResponsePermanentRedirect` return behavior.

4. **`process_response` method**: Document both the `request` and `response` parameters, and explain how each security header is conditionally added to the response based on the corresponding Django setting.

5. **HSTS details**: Explain the interaction between `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, and `SECURE_HSTS_PRELOAD` and how they compose the `Strict-Transport-Security` header value.

### Style Requirements

- Use PEP 257 conventions: triple double-quote delimiters (`"""`), imperative mood for summary lines (e.g., "Redirect HTTP requests to HTTPS" not "Redirects HTTP requests")
- Include parameter documentation using one of: `:param name:` / `:type name:` (Sphinx style) or `Args:` / `Returns:` (Google style)
- Include return type documentation
- Provide usage examples showing relevant Django settings configuration (e.g., `SECURE_SSL_REDIRECT = True`, HSTS settings, Referrer-Policy values)

### Quality Requirements

- Reference specific Django settings names (e.g., `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`) -- do not use vague descriptions
- Explain interactions between related settings (e.g., how `SECURE_HSTS_INCLUDE_SUBDOMAINS` modifies the HSTS header only when `SECURE_HSTS_SECONDS` is nonzero)
- Do not fabricate settings that do not exist in Django
- Do not simply copy text from Django's official documentation website -- write original docstrings based on the code's behavior

## Output

Write your complete documentation to `/workspace/documentation.md`. The file should contain all docstrings organized by class and method, with examples and behavioral notes.
