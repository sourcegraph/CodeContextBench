# Django CSRF Protection and Session Handling Security Analysis

## Files Examined

### Middleware & Core
- `django/middleware/csrf.py` — CSRF middleware implementation (token generation, masking, validation)
- `django/contrib/sessions/middleware.py` — Session middleware (session loading, saving, cookie handling)

### Session Backends & Storage
- `django/contrib/sessions/backends/base.py` — Base session class (encode/decode, session lifecycle)
- `django/contrib/sessions/backends/signed_cookies.py` — Cookie-based session storage
- `django/contrib/sessions/backends/db.py` — Database-backed sessions

### Cryptographic Infrastructure
- `django/utils/crypto.py` — Cryptographic utilities (HMAC, random generation, constant-time comparison)
- `django/core/signing.py` — Signing infrastructure (Signer, TimestampSigner, JSON serialization)

### Request/Response Handling
- `django/http/request.py` — HTTP request parsing (cookie extraction, POST data)
- `django/http/cookie.py` — Cookie parsing utilities
- `django/http/response.py` — Cookie setting in responses

---

## Entry Points

### 1. **HTTP Cookie Parsing** (`django/http/request.py:WSGIRequest.COOKIES`)
- **Source**: Untrusted HTTP `Cookie:` header from client
- **Location**: `django/http/request.py:99-102` (WSGIRequest class)
- **Processing**:
  ```python
  @cached_property
  def COOKIES(self):
      raw_cookie = get_str_from_wsgi(self.environ, "HTTP_COOKIE", "")
      return parse_cookie(raw_cookie)
  ```
- **Parser**: `django/http/cookie.py:parse_cookie()` — splits on `;` and `=`, uses `cookies._unquote()` for value unquoting

### 2. **CSRF Token from POST Data** (`django/middleware/csrf.py:CsrfViewMiddleware._check_token()`)
- **Source**: Untrusted form POST parameter `csrfmiddlewaretoken`
- **Location**: `django/middleware/csrf.py:368`
- **Processing**: `request.POST.get("csrfmiddlewaretoken", "")`
- **Format**: Can be masked (64 chars) or unmasked (32 chars)
- **Validation**: `_check_token_format()` checks length and character set (alphanumeric only)

### 3. **CSRF Token from HTTP Header** (`django/middleware/csrf.py:CsrfViewMiddleware._check_token()`)
- **Source**: Untrusted HTTP header (typically `X-CSRFToken` or custom header)
- **Location**: `django/middleware/csrf.py:384`
- **Processing**: `request.META[settings.CSRF_HEADER_NAME]`
- **Format**: Can be masked (64 chars) or unmasked (32 chars)
- **Validation**: Same as POST token

### 4. **CSRF Cookie** (`django/middleware/csrf.py:CsrfViewMiddleware._get_secret()`)
- **Source**: Untrusted HTTP cookie `djangocsrftoken` (configurable via `CSRF_COOKIE_NAME`)
- **Location**: `django/middleware/csrf.py:240`
- **Processing**:
  ```python
  csrf_secret = request.COOKIES[settings.CSRF_COOKIE_NAME]
  _check_token_format(csrf_secret)
  # Unmask if needed (legacy Django <4.0)
  if len(csrf_secret) == CSRF_TOKEN_LENGTH:
      csrf_secret = _unmask_cipher_token(csrf_secret)
  ```
- **Validation**: Format check (32 or 64 chars, alphanumeric only)

### 5. **Session Cookie** (`django/contrib/sessions/middleware.py:SessionMiddleware.process_request()`)
- **Source**: Untrusted HTTP cookie `sessionid` (configurable)
- **Location**: `django/contrib/sessions/middleware.py:19`
- **Processing**:
  ```python
  session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
  request.session = self.SessionStore(session_key)
  ```
- **Later Access Trigger**: `_session` property in `backends/base.py:237-250` calls `load()` on first access

### 6. **Origin Header** (`django/middleware/csrf.py:CsrfViewMiddleware._origin_verified()`)
- **Source**: Untrusted HTTP header `Origin`
- **Location**: `django/middleware/csrf.py:272`
- **Processing**: URL parsing and domain matching against `CSRF_TRUSTED_ORIGINS`

### 7. **Referer Header** (`django/middleware/csrf.py:CsrfViewMiddleware._check_referer()`)
- **Source**: Untrusted HTTP header `Referer`
- **Location**: `django/middleware/csrf.py:298`
- **Processing**: URL parsing, scheme validation, domain matching

---

## Data Flow

### Flow 1: CSRF Token Generation and Masking

**Purpose**: Create a token that can be sent to the client and later verified against the server's secret.

1. **Source**: `django/middleware/csrf.py:get_token()` — Entry point for getting/creating token
   - Called by template tag `{% csrf_token %}`
   - Called by `get_token(request)` utility function

2. **Secret Generation**: `django/middleware/csrf.py:_get_new_csrf_string()`
   - Generates 32 random alphanumeric characters using `get_random_string(32, CSRF_ALLOWED_CHARS)`
   - Uses cryptographically secure RNG from `secrets` module
   - Stored in `request.META["CSRF_COOKIE"]`

3. **Token Masking**: `django/middleware/csrf.py:_mask_cipher_secret(secret)`
   - Input: 32-char secret
   - Process:
     ```python
     mask = _get_new_csrf_string()  # Generate random 32-char mask
     # For each position i:
     #   token[i] = CSRF_ALLOWED_CHARS[(secret[i] + mask[i]) % 62]
     #   token[32+i] = mask[i]
     cipher = "".join(chars[(x + y) % len(chars)] for x, y in pairs)
     return mask + cipher  # 64-char masked token
     ```
   - Result: 64-character token = 32-char mask + 32-char cipher
   - Security: Uses simple modular addition cipher to prevent BREACH attacks (compression won't reveal secret)

4. **Client Receipt**: Token sent in HTML form or accessible via cookie

5. **Sink**: `django/middleware/csrf.py:process_response()` — Sets cookie on response
   - Location: `django/middleware/csrf.py:253-269`
   - Sets `djangocsrftoken` cookie if `CSRF_COOKIE_NEEDS_UPDATE` flag is set
   - Uses configured cookie security attributes: `secure`, `httponly`, `samesite`

---

### Flow 2: CSRF Token Validation

**Purpose**: Verify that token in request matches the secret stored on server.

1. **Source - Server Secret**: `django/middleware/csrf.py:_get_secret(request)`
   - From session: `request.session.get("_csrftoken")` if `CSRF_USE_SESSIONS=True`
   - From cookie: `request.COOKIES[CSRF_COOKIE_NAME]` if `CSRF_USE_SESSIONS=False`
   - Validates format: must be exactly 32 or 64 chars, all alphanumeric
   - If 64 chars (masked), unmasks to get 32-char secret

2. **Source - Client Token**: From POST or HTTP header
   - Extracted in `django/middleware/csrf.py:_check_token()`
   - Validated for format (32 or 64 chars, alphanumeric)

3. **Transform - Token Unmasking**: `django/middleware/csrf.py:_unmask_cipher_token(token)`
   - If token is 64 chars:
     ```python
     mask = token[:32]
     cipher = token[32:]
     secret = "".join(chars[x - y] for x, y in pairs)
     ```
   - If token is 32 chars, use as-is (unmasked token)

4. **Comparison**: `django/middleware/csrf.py:_does_token_match(request_csrf_token, csrf_secret)`
   - Unmask token if needed
   - Compare with `constant_time_compare()` — timing-attack safe
   - Location: `django/middleware/csrf.py:157`

5. **Sink - Validation Result**:
   - Match: `process_view()` calls `_accept()` and request proceeds
   - Mismatch: `process_view()` calls `_reject()` which invokes `CSRF_FAILURE_VIEW` (default: 403 Forbidden)

---

### Flow 3: Session Data Encoding and Signing

**Purpose**: Serialize session data and sign it for client-side storage or cookie embedding.

1. **Source - Session Data**: User modifies `request.session` dict
   - Any key-value pair: `request.session["user_id"] = 123`
   - Automatically marked as modified

2. **Transform - Serialization**: `django/contrib/sessions/backends/base.py:encode()`
   - Serializes session dict to JSON using configured `SESSION_SERIALIZER`
   - Calls `signing.dumps()` with:
     ```python
     signing.dumps(
         session_dict,
         salt="django.contrib.sessions.DatabaseSessionStore",
         serializer=self.serializer,
         compress=True
     )
     ```

3. **Transform - Signing**: `django/core/signing.py:dumps()` and `TimestampSigner.sign_object()`
   - Serializes dict to JSON
   - Optionally compresses with zlib
   - Base64-encodes compressed data
   - Adds timestamp token
   - Signs with HMAC-SHA256
   - Format: `base64_json:timestamp:signature`

4. **Cryptographic Details** (`django/utils/crypto.py:salted_hmac()`):
   ```python
   key_salt = b"django.contrib.sessions" + salt_from_signer
   key = SHA1(key_salt + SECRET_KEY)  # Key derivation
   signature = HMAC_SHA256(key, value_with_timestamp)
   ```

5. **Sink - Cookie Storage**:
   - **Signed Cookies Backend**: Entire signed value becomes cookie value
   - **DB Backend**: Signed value stored in database, session_key (random 32 chars) sent as cookie
   - **Cache Backend**: Similar to DB backend

---

### Flow 4: Session Data Decoding and Verification

**Purpose**: Client sends session cookie; server deserializes and verifies signature.

1. **Source**: `django/contrib/sessions/middleware.py:process_request()`
   - Extracts `sessionid` cookie
   - Creates `SessionStore` instance with session_key

2. **Lazy Loading Trigger**: First access to `request.session` property
   - Calls `_get_session()` in `django/contrib/sessions/backends/base.py:237-250`
   - If `session_key` exists, calls backend-specific `load()` method

3. **Transform - Signature Verification**: `django/core/signing.py:TimestampSigner.unsign()`
   - Splits value on `:` to extract data, timestamp, signature
   - Tries to verify signature with main key and all fallback keys
   - Uses `constant_time_compare()` for timing-attack safe comparison
   - Checks timestamp age against `max_age` parameter

4. **Transform - Deserialization**: `django/contrib/sessions/backends/base.py:decode()`
   ```python
   try:
       return signing.loads(
           session_data,
           salt=self.key_salt,
           serializer=self.serializer
       )
   except signing.BadSignature:
       logger.warning("Session data corrupted")
       return {}
   ```
   - Base64-decodes and optionally decompresses
   - Parses JSON back to dict
   - If signature fails, returns empty dict (session reset)

5. **Sink - Session Data Access**: Deserialized dict available as `request.session`
   - Attacker-controlled if signature verification passes (but sig fails before this)

---

### Flow 5: CSRF Middleware Process Sequence

1. **process_request()** (`django/middleware/csrf.py:401-412`)
   - Tries to load CSRF secret from cookie/session
   - If secret doesn't exist or is malformed, generates new one via `_add_new_csrf_cookie()`
   - Stores in `request.META["CSRF_COOKIE"]`

2. **process_view()** (`django/middleware/csrf.py:414-469`)
   - Skips "safe" methods (GET, HEAD, OPTIONS, TRACE)
   - For unsafe methods (POST, PUT, DELETE, PATCH):
     - Checks Origin header (if present) against whitelist
     - If no Origin, checks Referer header (for HTTPS requests)
     - Extracts and validates CSRF token from POST data or header
     - Compares token with secret using constant-time comparison
   - Returns 403 Forbidden on any failure

3. **process_response()** (`django/middleware/csrf.py:471-483`)
   - If `CSRF_COOKIE_NEEDS_UPDATE` flag set, calls `_set_csrf_cookie()`
   - Sets cookie with configured security attributes

---

### Flow 6: Session Middleware Process Sequence

1. **process_request()** (`django/contrib/sessions/middleware.py:18-20`)
   - Gets session key from cookie
   - Creates `SessionStore` instance (doesn't load yet)

2. **During request handling**:
   - First access to `request.session` triggers lazy load
   - `load()` method deserializes and verifies signature
   - Attacker-provided session cookie fails verification and resets session

3. **process_response()** (`django/contrib/sessions/middleware.py:22-77`)
   - Checks if session was modified
   - If modified and not empty:
     - Calls `request.session.save()` to serialize/sign new data
     - Sets new session cookie
   - If empty, deletes session cookie

---

## Dependency Chain

### CSRF Token Processing Chain
1. `django/http/cookie.py:parse_cookie()` — parses raw cookie string
2. `django/middleware/csrf.py:_check_token_format()` — validates token format (length, charset)
3. `django/middleware/csrf.py:_unmask_cipher_token()` — decrypts masked token
4. `django/middleware/csrf.py:_does_token_match()` — compares tokens
5. `django/utils/crypto.py:constant_time_compare()` — timing-safe comparison

### Session Data Processing Chain
1. `django/http/cookie.py:parse_cookie()` — parses session key from cookie
2. `django/contrib/sessions/backends/base.py:_get_session()` — lazy-loads session
3. `django/contrib/sessions/backends/*/load()` — backend-specific load
4. `django/core/signing.py:TimestampSigner.unsign()` — verifies signature
5. `django/core/signing.py:TimestampSigner.unsign_object()` — decompresses and deserializes
6. `django/contrib/sessions/backends/base.py:decode()` — parses JSON

### Cryptographic Chain
1. `django/utils/crypto.py:salted_hmac()` — HMAC key derivation and signing
2. `django/core/signing.py:base64_hmac()` — base64-encodes HMAC result
3. `django/utils/crypto.py:constant_time_compare()` — timing-safe signature verification
4. `django/utils/crypto.py:get_random_string()` — cryptographically secure RNG

---

## Analysis

### 1. CSRF Protection Mechanism

#### Token Masking Scheme (BREACH Attack Mitigation)
- **Vulnerability Addressed**: BREACH (Brotli/GZIP compression + Exploit Response)
  - Attacker can compress responses and use compression ratio changes to infer secret token content
- **Solution**: Mask secret with random value before sending to client
  - Server stores: `SECRET` (32 chars)
  - Client receives: `MASK + CIPHER(SECRET, MASK)` (64 chars)
  - On validation, server unmasks: `SECRET = CIPHER^{-1}(TOKEN[32:], TOKEN[:32])`
- **Security Property**: Compression cannot reveal `SECRET` because `MASK` changes every request
- **Weakness**: Masking is NOT encryption
  - Uses simple modular addition cipher: `cipher[i] = (secret[i] + mask[i]) % 62`
  - Technically breaks on many requests if same secret is reused (but new mask each time prevents this)

#### Cookie vs. Session Storage
- **CSRF_USE_SESSIONS=False** (default): Secret stored in cookie (untrusted, but signed)
  - Cookie value: raw secret (32 alphanumeric chars)
  - No signing; security relies on randomness + Same-Origin Policy
  - **Risk**: Secret can be exfiltrated via XSS if not HttpOnly

- **CSRF_USE_SESSIONS=True**: Secret stored in server-side session
  - Cookie: only session ID (signed)
  - Server stores secret in signed session data
  - **Better**: Secret cannot be exfiltrated via XSS
  - **Still Vulnerable**: To CSRF if session cookie can be forged/reused

#### Origin/Referer Validation
- **For HTTPS requests without Origin header**: Validates Referer header
- **Purpose**: Prevent MITM attacks from downgrading to HTTP
- **Validation Steps**:
  1. Parses URL format
  2. Checks scheme (must be HTTPS if request is HTTPS)
  3. Domain matching against `CSRF_TRUSTED_ORIGINS` and `CSRF_COOKIE_DOMAIN`
- **Bypass Potential**:
  - Misconfigured `CSRF_TRUSTED_ORIGINS` or `CSRF_COOKIE_DOMAIN`
  - Wildcard subdomains (`*.example.com`) are vulnerable to subdomain takeover

---

### 2. Session Handling Security

#### Signed Cookies Backend
- **Storage**: Entire session dict signed and stored in cookie
- **Format**: `base64_json:timestamp:hmac_signature`
- **Advantages**:
  - No server-side storage needed
  - Stateless design suitable for horizontally scaled systems
- **Security Properties**:
  - Data is not encrypted (base64 is encoding, not encryption)
  - **Risk**: Session data is visible to attacker if intercepted
  - Signature prevents modification but not reading
  - Solution: Use HTTPS to encrypt in transit

- **Cryptographic Details**:
  ```python
  key = SHA1(b"django.contrib.sessions.backends.signed_cookies" + SECRET_KEY)
  signature = HMAC_SHA256(key, json_base64 + ":" + timestamp)
  ```

#### Database Backend
- **Storage**: Session data stored in database, only session_key sent as cookie
- **Session Key**: 32 random characters generated via `get_random_string(32)`
- **Database Schema**: `session_key`, `session_data` (JSON), `expire_date`
- **Security Properties**:
  - Session data not visible in cookie (if HTTPS)
  - Vulnerable to session fixation if session key can be controlled
  - SQL injection risk in model queries (mitigated by ORM)

#### Timestamp Validation
- **Purpose**: Prevent replay attacks and enforce session expiration
- **Implementation**: `TimestampSigner.unsign(value, max_age=...)`
  - Appends current timestamp (base62-encoded) to signed value
  - On unsign, compares current time - timestamp > max_age
  - Max age typically set to `SESSION_COOKIE_AGE` (2 weeks default)
- **Effectiveness**: Prevents using old session cookies after max_age

#### Compression
- **Used In**: Session encoding (`compress=True` in `signing.dumps()`)
- **Purpose**: Reduce cookie size
- **Risk**: BREACH-like attacks if compression is used with secrets
  - Django mitigates by not including secrets in session dict itself
  - Session data is user-controlled (attacker can influence size)
  - **Mitigation**: Compress at application layer, not at TLS (configure server)

---

### 3. Cryptographic Security Properties

#### Random Number Generation
- **Source**: `django/utils/crypto.py:get_random_string()`
  - Uses `secrets.choice()` for each character
  - `secrets` module provides cryptographically secure RNG
  - Entropy: `log2(62^32) ≈ 190 bits` for CSRF secret, `log2(62^64) ≈ 379 bits` for masked token

#### HMAC Key Derivation
- **Function**: `django/utils/crypto.py:salted_hmac(key_salt, value, secret)`
  - `key = SHA1(key_salt + SECRET_KEY)`
  - Uses SHA1 for key derivation (not for message authentication)
  - **Weakness**: SHA1 is deprecated for cryptographic use, but used for key derivation here
  - **Not Weakness**: Message authentication uses SHA256 (see `Signer` class)
  - **Note**: Key length is 20 bytes from SHA1, fed to HMAC

- **Key Material**:
  - Primary: `settings.SECRET_KEY` (should be >50 chars, high entropy)
  - Fallback: `settings.SECRET_KEY_FALLBACKS` (for key rotation)

#### Message Authentication
- **Algorithm**: HMAC-SHA256 (in `Signer.signature()`)
- **Salt**: Different for each use case
  - CSRF: None (uses bare cookie)
  - Sessions: `"django.contrib.sessions.backends.signed_cookies"` or `"django.contrib.sessions.DatabaseSessionStore"`
- **Purpose of Salt**: Namespace different uses of signing to prevent cross-context forgeries

#### Constant-Time Comparison
- **Function**: `django/utils/crypto.py:constant_time_compare()`
  - Uses `secrets.compare_digest()` from stdlib
  - Prevents timing attacks that could distinguish valid from invalid tokens
  - Example: Attacker sends tokens with different prefixes, measures response time
  - Constant-time: all comparisons take same time regardless of mismatch position

---

### 4. Attack Surface

#### Entry Point: Cookie Parsing
- **Risk**: Attacker-controlled cookie values parsed without prior validation
- **Mitigation**:
  - Format validation in `_check_token_format()`
  - Signature verification in session deserialization
  - Constant-time comparison prevents timing attacks

#### Entry Point: POST Data
- **Risk**: CSRF token from untrusted POST parameter
- **Mitigation**:
  - Token generation is server-controlled (not user-provided)
  - Format validation (length, charset)
  - Comparison uses constant-time method

#### Entry Point: HTTP Headers (Origin, Referer)
- **Risk**: Attacker controls these headers in browser (from same origin) or from MITM
- **Mitigation**:
  - URL parsing with error handling
  - Domain whitelisting
  - Scheme validation (HTTPS required for Referer on HTTPS requests)
- **Bypass**: Misconfigured whitelists, subdomain takeover, open redirects

#### Entry Point: Session Data
- **Risk**: Attacker provides crafted signed session data
- **Mitigation**:
  - Signature verification with constant-time comparison
  - Timestamp validation
  - Failed deserialization resets session
  - Compression bombs prevented by base64 size limits

---

### 5. Configuration Issues

#### CSRF_COOKIE_SECURE
- **Default**: `False` (insecure)
- **Risk**: Cookie sent over HTTP (if protocol is HTTP)
- **Recommendation**: Set to `True` in production

#### CSRF_COOKIE_HTTPONLY
- **Default**: `True` (secure)
- **Effect**: Cookie not accessible to JavaScript
- **Benefit**: Prevents XSS exfiltration of CSRF token

#### CSRF_COOKIE_SAMESITE
- **Default**: `"Lax"` (secure)
- **Values**:
  - `"Strict"`: Cookie not sent on cross-site requests (even form submissions)
  - `"Lax"`: Cookie sent on top-level navigation from other sites, but not on sub-requests
  - `"None"`: Cookie sent on all requests (requires `Secure=True`)
- **SameSite=None**: Defeats some CSRF protection; should not be used for session/CSRF cookies

#### SESSION_COOKIE_HTTPONLY
- **Default**: `True` (secure)
- **Effect**: Session cookie not accessible to JavaScript

#### SESSION_COOKIE_SECURE
- **Default**: `False` (insecure)
- **Risk**: Cookie sent over HTTP
- **Recommendation**: Set to `True` in production

#### SESSION_COOKIE_SAMESITE
- **Default**: `"Lax"` (secure)
- **Same considerations as CSRF_COOKIE_SAMESITE**

#### SECRET_KEY
- **Usage**: Master key for all signing operations
- **Risk**: If compromised, attacker can forge CSRF tokens and sessions
- **Recommendation**: >50 chars, high entropy, never committed to version control

---

### 6. Known Issues and Mitigations

#### Issue 1: BREACH Attack on Compressed Content
- **Vulnerability**: If response is compressed (gzip/brotli) and contains CSRF token + attacker-controlled data
- **Mitigation in Django**:
  - CSRF token masking (changes every request)
  - Server-side mitigation: disable compression or use rate limiting
- **Not Addressed**: Attacker-controlled session data compression

#### Issue 2: CSRF Token Reuse
- **Scenario**: Attacker captures CSRF token in N requests, uses it in (N+1)th request
- **Protection**: Token must match current server-side secret
- **Weakness**: If token is masked, multiple masks could produce same secret (unlikely but possible with poor randomness)

#### Issue 3: Subdomain CSRF
- **Scenario**: Attacker controls `evil.example.com`, main app at `example.com`
- **Risk**: If `CSRF_COOKIE_DOMAIN = ".example.com"`, cookie is shared across subdomains
- **Mitigation**: Set `CSRF_COOKIE_DOMAIN = None` (exact domain match) or validate subdomains

#### Issue 4: SameSite Bypass via Navigations
- **Scenario**: Attacker tricks user into clicking link to malicious form submission
- **SameSite=Lax**: Cookie sent on top-level navigations (form submission from attacker's site)
- **Mitigation**: CSRF token still required; SameSite is defense-in-depth

#### Issue 5: Session Fixation
- **Scenario**: Attacker sets user's session cookie to a known value, user logs in
- **Mitigation**: Django's `rotate_token()` called on login changes CSRF token
- **Note**: Session key (for DB backend) is also regenerated on login

#### Issue 6: Timing Attacks on Session Signature
- **Scenario**: Attacker modifies session signature byte-by-byte, measures response time
- **Mitigation**: `constant_time_compare()` makes all comparisons take same time
- **Effectiveness**: Timing is constant with respect to signature content, not to signature validity (still detects early that sig is invalid)

---

## Summary

Django's CSRF protection and session handling employ multiple layers of defense:

1. **CSRF Protection**:
   - Token masking prevents BREACH attacks by ensuring secrets are not compressible
   - Origin/Referer validation prevents same-origin-policy bypasses on HTTPS
   - Constant-time comparison prevents timing attacks on token validation
   - Cryptographically secure randomness ensures tokens cannot be predicted

2. **Session Security**:
   - HMAC-SHA256 signatures prevent forged session data (TimestampSigner adds replay protection)
   - Timestamp validation prevents using expired sessions
   - Constant-time comparison prevents timing attacks on signature verification
   - HttpOnly and Secure flags prevent XSS exfiltration and HTTP interception (if configured)

3. **Cryptographic Foundations**:
   - Key derivation via HMAC prevents key recovery
   - Salted HMAC prevents cross-context forgeries
   - Base62 encoding and timestamps protect against replay attacks
   - Optional compression (with zlib) reduces cookie size but doesn't encrypt data

4. **Remaining Risks**:
   - Configuration errors (SECURE=False, SAMESITE="None", weak SECRET_KEY)
   - Subdomain takeover if CSRF_COOKIE_DOMAIN uses wildcard
   - Side-channel attacks from compression if attacker controls both plaintext and token
   - SameSite is defense-in-depth; CSRF token validation is primary defense

The design is secure-by-default for most configurations, with strong cryptographic foundations and multiple validation layers. The primary attack vectors are configuration errors and compromised SECRET_KEY, not cryptographic weaknesses.

