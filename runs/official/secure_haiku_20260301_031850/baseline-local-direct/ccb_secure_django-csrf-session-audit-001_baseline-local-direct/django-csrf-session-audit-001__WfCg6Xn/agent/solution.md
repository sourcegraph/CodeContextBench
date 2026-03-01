# Django CSRF Protection and Session Handling Security Analysis

## Executive Summary

This analysis traces the complete Django CSRF protection and session handling pipeline from HTTP request reception through token validation and response cookie setting. The system implements a multi-layered defense combining cryptographic signing, token masking, origin validation, and secure cookie attributes. While generally secure, several design choices merit discussion regarding attack surface and mitigation effectiveness.

---

## Files Examined

### CSRF Middleware and Related Files
- **django/middleware/csrf.py** (484 lines) — Main CSRF protection middleware implementing token generation, masking, validation, and cookie setting
- **django/views/decorators/csrf.py** (70 lines) — Decorator-based CSRF protection (csrf_protect, csrf_exempt, ensure_csrf_cookie)
- **django/views/csrf.py** — CSRF failure response handler

### Session Middleware and Backends
- **django/contrib/sessions/middleware.py** (78 lines) — Session middleware reading/writing session cookies and managing session lifecycle
- **django/contrib/sessions/backends/base.py** (350+ lines) — Abstract base session class with encode/decode methods
- **django/contrib/sessions/backends/db.py** (199 lines) — Database-backed session store using signed encoding
- **django/contrib/sessions/backends/signed_cookies.py** (104 lines) — Client-side session store with full data signing
- **django/contrib/sessions/backends/file.py** — File-based session store
- **django/contrib/sessions/backends/cache.py** — Cache-based session store
- **django/contrib/sessions/models.py** — Session database model

### Cryptographic Foundation
- **django/core/signing.py** (278 lines) — Core signing infrastructure (Signer, TimestampSigner, dumps/loads functions)
- **django/utils/crypto.py** (78 lines) — Low-level cryptographic utilities (salted_hmac, constant_time_compare, get_random_string)

### HTTP Layer
- **django/http/request.py** — HTTP request parsing (COOKIES, POST, META dictionaries)
- **django/http/response.py** — HTTP response and cookie setting (set_cookie, delete_cookie, set_signed_cookie)
- **django/http/cookie.py** — Cookie parsing and serialization

### Configuration and Checks
- **django/conf/global_settings.py** — Default security configuration settings
- **django/core/checks/security/csrf.py** — Security checks for CSRF configuration

---

## Entry Points

Entry points are locations where untrusted external data enters the CSRF/session subsystem:

### 1. HTTP Cookie Parsing — `django/http/request.py:__init__` + `django/middleware/csrf.py:_get_secret`
- **Input Type:** Raw HTTP Cookie header (untrusted)
- **Attack Surface:** CSRF secret can be crafted/replayed; session_key can be forged
- **Handler:** `CsrfViewMiddleware._get_secret()` reads `request.COOKIES[CSRF_COOKIE_NAME]`
- **Handler:** `SessionMiddleware.process_request()` reads `request.COOKIES[SESSION_COOKIE_NAME]`

### 2. POST Form Data — `django/http/request.py:POST` + `django/middleware/csrf.py:_check_token`
- **Input Type:** Raw POST body parameter `csrfmiddlewaretoken` (untrusted)
- **Attack Surface:** Attacker can submit arbitrary token values for mismatch detection
- **Handler:** `CsrfViewMiddleware._check_token()` at line 368 reads `request.POST.get("csrfmiddlewaretoken")`

### 3. HTTP Headers (Origin/Referer) — `django/middleware/csrf.py:_origin_verified`, `_check_referer`
- **Input Type:** HTTP Origin and Referer headers (untrusted for cross-origin requests)
- **Attack Surface:** Attacker can forge Origin/Referer headers from same-origin perspective
- **Handler:** `_origin_verified()` line 272 reads `request.META["HTTP_ORIGIN"]`
- **Handler:** `_check_referer()` line 298 reads `request.META["HTTP_REFERER"]`

### 4. Custom CSRF Header — `django/middleware/csrf.py:_check_token`
- **Input Type:** HTTP X-CSRFToken header value (untrusted)
- **Attack Surface:** Alternative token submission method for AJAX; same format requirements
- **Handler:** Line 384 reads `request.META[settings.CSRF_HEADER_NAME]` (default: `HTTP_X_CSRFTOKEN`)

### 5. Session Data in Cookie — `django/contrib/sessions/backends/signed_cookies.py:load`
- **Input Type:** Full session dictionary in cookie value (signed but untrusted)
- **Attack Surface:** Attacker can submit tampered session cookies; signature validation is critical
- **Handler:** `SessionStore.load()` line 13 calls `signing.loads(self.session_key, ...)`

### 6. Session Data in Database — `django/contrib/sessions/backends/db.py:load`
- **Input Type:** Signed session data from database (signed but untrusted from network perspective)
- **Attack Surface:** Stored session data can be tampered if database is compromised; decoding step
- **Handler:** `SessionStore.load()` line 56 calls `self.decode(s.session_data)`

### 7. Settings and Configuration — `django/conf/settings.py`
- **Input Type:** Deployment configuration values (trusted, but defaults matter)
- **Attack Surface:** Misconfiguration can disable protections (CSRF_USE_SESSIONS, CSRF_COOKIE_SECURE, etc.)
- **Handler:** `settings.CSRF_COOKIE_NAME`, `settings.CSRF_COOKIE_SECURE`, `settings.CSRF_USE_SESSIONS`

---

## Data Flow

### Flow 1: CSRF Protection Pipeline (Safe-Method Request)

```
1. Source: HTTP Request
   - Line: django/middleware/csrf.py:401-412 (process_request)
   - Data: Raw cookie from request.COOKIES or request.session

2. Transform: CSRF Secret Extraction
   - File: django/middleware/csrf.py:221-251 (_get_secret)
   - Operation: Reads CSRF secret from cookie/session
   - Validation: Checks token format (length and allowed characters)
   - Exception: InvalidTokenFormat if validation fails
   - Unmasking: Unmasks if token is CSRF_TOKEN_LENGTH (64 chars)

3. Storage: Request Metadata
   - File: django/middleware/csrf.py:412
   - Data: Stores unmasked secret in request.META["CSRF_COOKIE"]

4. Sink: Token Generation
   - File: django/middleware/csrf.py:96-114 (get_token)
   - Operation: Calls _mask_cipher_secret() to generate masked token for template
   - Output: Returns masked token (64 chars) for use in HTML form
```

### Flow 2: CSRF Protection Pipeline (Unsafe-Method Request - GET not processed for CSRF)

```
1. Source: HTTP Request (POST/PUT/DELETE/PATCH)
   - File: django/middleware/csrf.py:414-469 (process_view)
   - Request contains: CSRF token (from POST field or X-CSRFToken header)

2. Transform: Origin/Referer Validation
   - File: django/middleware/csrf.py:436-462
   - Check 1: If HTTP_ORIGIN header present, validate against allowed origins
   - Check 2: If HTTPS and no Origin header, validate HTTP_REFERER
   - Validation: Checks domain matching and scheme consistency
   - Rejection: Returns 403 Forbidden if validation fails

3. Transform: Token Format Validation
   - File: django/middleware/csrf.py:349-400 (_check_token)
   - Step 1: Retrieve CSRF secret via _get_secret() (lines 353-356)
   - Step 2: Extract token from POST data or X-CSRFToken header (lines 365-389)
   - Step 3: Validate token format using _check_token_format() (lines 391-395)
   - Exception: InvalidTokenFormat raises RejectRequest

4. Transform: Token Matching
   - File: django/middleware/csrf.py:143-157 (_does_token_match)
   - Operation: Unmask token if necessary (line 155: _unmask_cipher_token)
   - Comparison: Constant-time comparison of unmasked token to secret (line 157)
   - Function: Uses django.utils.crypto.constant_time_compare
   - Result: Boolean indicating match/mismatch

5. Sink: Request Acceptance/Rejection
   - File: django/middleware/csrf.py:464-469
   - Accept: request.csrf_processing_done = True (line 206)
   - Reject: Calls _reject() which returns 403 response with reason logged
```

### Flow 3: CSRF Cookie Setting Pipeline

```
1. Source: Response Handler
   - File: django/middleware/csrf.py:471-483 (process_response)
   - Trigger: Check request.META.get("CSRF_COOKIE_NEEDS_UPDATE")

2. Transform: Cookie Security Configuration
   - File: django/middleware/csrf.py:253-269 (_set_csrf_cookie)
   - Storage Decisions:
     - If CSRF_USE_SESSIONS: Store in session backend (line 256)
     - Else: Set HTTP cookie with security attributes (lines 258-267)

3. Cookie Attributes (if not using sessions):
   - name: settings.CSRF_COOKIE_NAME (default: "csrftoken")
   - value: request.META["CSRF_COOKIE"] (unmasked 32-char secret)
   - max_age: settings.CSRF_COOKIE_AGE (default: 1 year)
   - domain: settings.CSRF_COOKIE_DOMAIN (default: None = request domain)
   - path: settings.CSRF_COOKIE_PATH (default: "/")
   - secure: settings.CSRF_COOKIE_SECURE (default: False ⚠️)
   - httponly: settings.CSRF_COOKIE_HTTPONLY (default: False ⚠️)
   - samesite: settings.CSRF_COOKIE_SAMESITE (default: "Lax")

4. Sink: HTTP Response
   - File: django/http/response.py:214-276 (set_cookie)
   - Output: Set-Cookie header in HTTP response
```

### Flow 4: Session Middleware Pipeline (Request Phase)

```
1. Source: HTTP Request
   - File: django/contrib/sessions/middleware.py:18-20 (process_request)
   - Input: request.COOKIES[settings.SESSION_COOKIE_NAME]

2. Transform: Session Backend Instantiation
   - Line 20: self.SessionStore(session_key)
   - Action: Instantiates appropriate session backend based on settings.SESSION_ENGINE
   - Example: django.contrib.sessions.backends.db.SessionStore
   - Result: Creates request.session object (empty until accessed)

3. Storage: Lazy Loading
   - File: django/contrib/sessions/backends/base.py:237-250 (_get_session)
   - Trigger: Accessed when request.session[key] is read
   - Operation: Calls backend-specific load() method
```

### Flow 5: Session Data Decoding Pipeline (Database Backend)

```
1. Source: Database
   - File: django/contrib/sessions/backends/db.py:32-42 (_get_session_from_db)
   - Query: SELECT session_data FROM sessions WHERE session_key=? AND expire_date > NOW()

2. Transform: Session Data Deserialization
   - File: django/contrib/sessions/backends/base.py:131-143 (decode)
   - Call: signing.loads(session_data, salt=key_salt, serializer=serializer)

3. Signing Pipeline (Critical):
   - File: django/core/signing.py:155-174 (loads function)
   - Creates: TimestampSigner instance
   - Calls: TimestampSigner.unsign_object()

   a) Unsign Step (django/core/signing.py:206-213):
      - Split on separator: "data:signature" -> (data, sig)
      - Iterate through keys: [primary_key, *fallback_keys]
      - For each key, compute: signature(data, key)
      - Compare: constant_time_compare(provided_sig, computed_sig)
      - Exception: BadSignature if no keys match

   b) Decode Step (django/core/signing.py:240-251):
      - Base64 decode the data
      - Check for compression flag (leading ".")
      - If compressed: zlib.decompress()
      - JSONSerializer().loads() for final deserialization

4. Error Handling:
   - BadSignature: Logged as "Session data corrupted"
   - Other Exceptions: Return empty dict {}

5. Sink: request.session Dictionary
   - Result: Dictionary of session key-value pairs
   - Modifications: Marked with request.session.modified = True
```

### Flow 6: Session Data Encoding Pipeline (Response Phase)

```
1. Source: Request Handler
   - File: django/contrib/sessions/middleware.py:22-77 (process_response)
   - Trigger: Check modified flag (line 30)

2. Transform: Session Encoding
   - File: django/contrib/sessions/backends/base.py:122-129 (encode)
   - Call: signing.dumps(session_dict, salt=key_salt, serializer=serializer, compress=True)

3. Signing Pipeline:
   - File: django/core/signing.py:131-152 (dumps function)
   - Creates: TimestampSigner instance
   - Calls: sign_object()

   a) Serialization (django/core/signing.py:215-238):
      - JSONSerializer().dumps(obj) -> JSON bytes
      - Optional zlib.compress()
      - Base64 encode
      - Prepend "." if compressed

   b) Signing (django/core/signing.py:258-260):
      - Append separator ":" and timestamp (base62 encoded current time)
      - Call parent Signer.sign()

   c) HMAC Generation (django/core/signing.py:199-201):
      - salt: "django.contrib.sessions." + class name
      - Generate signature via base64_hmac()
      - HMAC algorithm: SHA256 (default, configurable)
      - Key derivation: salted_hmac() function

4. Cookie Setting:
   - File: django/contrib/sessions/middleware.py:66-76 (process_response)
   - Set-Cookie header with session_key (the signed data)

5. Sink: HTTP Response with Set-Cookie header
```

### Flow 7: Signed Cookies Session Backend (Direct Cookie Storage)

```
1. Source: HTTP Request
   - File: django/contrib/sessions/backends/signed_cookies.py:6-24 (load)
   - Input: self.session_key (which is the entire signed session data in cookie)

2. Transform: Direct Deserialization
   - Operation: signing.loads(self.session_key, max_age=cookie_age, ...)
   - No database access; data is in the cookie itself
   - Timestamp check: max_age parameter validates cookie age

3. Save Pipeline (django/contrib/sessions/backends/signed_cookies.py:39-46):
   - Call: _get_session_key()
   - Operation: signing.dumps(self._session, compress=True, ...)
   - Result: Entire session dict becomes session_key (the cookie value)
   - Note: Cookie value can be very large if session contains much data

4. Sink: Set-Cookie header with signed session data as value
```

---

## Dependency Chain

From Entry to Cryptographic Operations:

### Request → CSRF Validation
1. **Entry:** `django/http/request.py` — WSGI server calls with environ dict
2. **Parsing:** `django/http/request.py` — Parses environ to populate request.COOKIES, request.POST, request.META
3. **Cookie Reading:** `django/middleware/csrf.py:_get_secret()` — Extracts CSRF_COOKIE_NAME or uses session
4. **Validation:** `django/middleware/csrf.py:_check_token_format()` — Validates token length/chars
5. **Unmasking:** `django/middleware/csrf.py:_unmask_cipher_token()` — XOR-based cipher reversal
6. **Comparison:** `django/middleware/csrf.py:_does_token_match()` — Calls constant_time_compare()
7. **Crypto:** `django/utils/crypto.py:constant_time_compare()` — Uses secrets.compare_digest()

### Request → Session Loading
1. **Entry:** `django/http/request.py` — WSGI request
2. **Parsing:** `django/http/request.py` — Parses cookies
3. **Session Read:** `django/contrib/sessions/middleware.py:process_request()` — Creates session object
4. **Session Load:** `django/contrib/sessions/backends/base.py:_get_session()` — Lazy load trigger
5. **Backend Load:** `django/contrib/sessions/backends/db.py:load()` — Retrieves from DB
6. **Deserialization:** `django/contrib/sessions/backends/base.py:decode()` — Calls signing.loads()
7. **Signing Verification:** `django/core/signing.py:unsign()` — HMAC validation
8. **Comparison:** `django/utils/crypto.py:constant_time_compare()` — Constant-time sig check
9. **Crypto:** `django/utils/crypto.py:salted_hmac()` — HMAC-SHA256 generation

### Response → Cookie Setting
1. **Response Handler:** `django/middleware/csrf.py:process_response()` — Checks CSRF_COOKIE_NEEDS_UPDATE
2. **Cookie Setting:** `django/http/response.py:set_cookie()` — Creates Set-Cookie header
3. **Security Attrs:** HttpOnly, Secure, SameSite flags applied per settings
4. **Output:** `django/http/response.py` — Serializes to HTTP response

### Response → Session Saving
1. **Response Handler:** `django/contrib/sessions/middleware.py:process_response()` — Checks modified flag
2. **Session Save:** `django/contrib/sessions/backends/db.py:save()` — Encodes and persists
3. **Encoding:** `django/contrib/sessions/backends/base.py:encode()` — Calls signing.dumps()
4. **Signing:** `django/core/signing.py:sign_object()` — HMAC generation
5. **Key Derivation:** `django/utils/crypto.py:salted_hmac()` — HMAC with derived key
6. **Cookie Setting:** `django/http/response.py:set_cookie()` — Creates Set-Cookie header

---

## Cryptographic Analysis

### CSRF Token Generation and Masking

**Function:** `django/middleware/csrf.py:_mask_cipher_secret()` (lines 59-68)

```python
def _mask_cipher_secret(secret):
    mask = _get_new_csrf_string()  # 32 random alphanumeric chars
    chars = CSRF_ALLOWED_CHARS  # "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    pairs = zip((chars.index(x) for x in secret), (chars.index(x) for x in mask))
    cipher = "".join(chars[(x + y) % len(chars)] for x, y in pairs)
    return mask + cipher  # 64-char token
```

**Security Properties:**
- **Type:** Modular addition cipher (Vigenère-like)
- **Key Material:** 32-character random mask
- **Algorithm:** For each position: `output[i] = chars[(secret_index[i] + mask_index[i]) % 62]`
- **Reversibility:** Can be unmasked since both mask and cipher are known: `secret[i] = chars[cipher_index[i] - mask_index[i]]`
- **Entropy:** log₂(62³²) ≈ 190 bits of randomness in mask
- **Threat Model:** Protects against BREACH attacks (compression attacks on HTTPS)
  - BREACH exploits: If attacker controls plaintext and compresses it with CSRF token, repeated bytes compress better
  - Mitigation: Masking randomizes token on every request, preventing oracle-based BREACH
- **Limitation:** Does NOT protect against attacker reading the token from DOM or network
- **Constants:**
  - CSRF_SECRET_LENGTH = 32 chars (~190 bits)
  - CSRF_TOKEN_LENGTH = 64 chars (32 mask + 32 cipher)
  - CSRF_ALLOWED_CHARS = 62 characters (no symbols to prevent XSS via URL encoding)

### HMAC-Based Session Signing

**Function:** `django/utils/crypto.py:salted_hmac()` (lines 19-45)

```python
def salted_hmac(key_salt, value, secret=None, *, algorithm="sha1"):
    secret = settings.SECRET_KEY  # default
    key_salt = force_bytes(key_salt)
    secret = force_bytes(secret)
    key = hasher(key_salt + secret).digest()  # Key derivation
    return hmac.new(key, msg=force_bytes(value), digestmod=hasher)
```

**Security Properties:**
- **Key Derivation:** HMAC uses SHA1/SHA256(key_salt || secret) as derived key
  - Purpose: Namespace different uses of HMAC (session vs cookie vs signing)
  - Rationale: Prevents key reuse across different domains
  - Note: If key_salt + secret > hash block size, HMAC module re-hashes anyway
- **Algorithm:** SHA256 for signing.py (configurable, default for Signer class)
- **HMAC Properties:** Cryptographically secure due to:
  - Python's hmac module uses constant-time comparison internally
  - SHA256 is collision-resistant (256-bit output)
  - Key material derives from settings.SECRET_KEY (must be ≥50 random chars)
- **Attack Resistance:**
  - Timing attack resistant: constant-time HMAC generation
  - Forgery resistant: Would require guessing SECRET_KEY
  - Replay protection: TimestampSigner includes timestamp in signed value

**Signer Implementation:** `django/core/signing.py:Signer.sign()` (lines 203-204)

```python
def signature(self, value, key=None):
    return base64_hmac(self.salt + "signer", value, key, algorithm=self.algorithm)

def sign(self, value):
    return "%s%s%s" % (value, self.sep, self.signature(value))
```

**Format:** `<base64_data>:<base64_signature>`
- Separator is ":" (must not be alphanumeric for safety)
- Signature is base64-encoded HMAC digest

### TimestampSigner

**Function:** `django/core/signing.py:TimestampSigner` (lines 254-277)

```python
class TimestampSigner(Signer):
    def sign(self, value):
        value = "%s%s%s" % (value, self.sep, self.timestamp())
        return super().sign(value)

    def unsign(self, value, max_age=None):
        result = super().unsign(value)
        value, timestamp = result.rsplit(self.sep, 1)
        timestamp = b62_decode(timestamp)
        if max_age is not None:
            age = time.time() - timestamp
            if age > max_age:
                raise SignatureExpired(...)
```

**Format:** `<data>:<timestamp>:<signature>`
- Timestamp is base62-encoded Unix time
- Provides defense against:
  - Old session cookie reuse (via max_age parameter)
  - Session hijacking from stale cookies

### Constant-Time Comparison

**Function:** `django/utils/crypto.py:constant_time_compare()` (lines 65-67)

```python
def constant_time_compare(val1, val2):
    return secrets.compare_digest(force_bytes(val1), force_bytes(val2))
```

**Security Properties:**
- **Implementation:** Uses Python's `secrets.compare_digest()` (standard library)
- **Timing Attack Prevention:** Compares all bytes even if early mismatch found
- **Used By:**
  - CSRF token matching (line 157 of csrf.py)
  - Session signature verification (line 211 of signing.py)
- **Vulnerability Class Prevented:** Timing-based oracle attacks
  - Example: If comparison returned early on first byte mismatch, attacker could use timing to guess token byte-by-byte

### Random String Generation

**Function:** `django/utils/crypto.py:get_random_string()` (lines 51-62)

```python
def get_random_string(length, allowed_chars=RANDOM_STRING_CHARS):
    return "".join(secrets.choice(allowed_chars) for i in range(length))
```

**Security Properties:**
- **RNG Source:** Python's `secrets` module (uses OS entropy source)
  - Linux: /dev/urandom
  - Windows: CryptGenRandom
- **Entropy:** log₂(62^length) bits for default 62-character set
  - 32 chars: ~190 bits
  - 64 chars: ~380 bits
- **Cryptographic Grade:** Suitable for security tokens
- **Used By:**
  - CSRF secret generation: 32 chars
  - CSRF mask generation: 32 chars per request
  - Session key generation: 32 chars
  - New session creation: random session_key

---

## Attack Scenarios and Mitigations

### Scenario 1: Traditional CSRF Attack (Mitigated by Token Validation)

**Attack:**
1. Attacker hosts example.com/attack.html
2. Victim logs into bank.com with CSRF cookie set
3. Victim visits attack.html (still logged into bank.com)
4. JavaScript on attack.html submits POST to bank.com/transfer with attacker-controlled form
5. Without CSRF protection: Browser automatically includes bank.com cookies, transfer succeeds

**Mitigation Chain:**
1. **Token Requirement:** POST requests require csrfmiddlewaretoken parameter (line 368 of csrf.py)
2. **Attacker Cannot Obtain Token:** Same-origin policy prevents JavaScript on attack.html from reading bank.com's CSRF cookie (HttpOnly cookies) or DOM
3. **Token Mismatch:** Attacker cannot forge token matching the bank.com CSRF secret
4. **Rejection:** _check_token() rejects with 403 Forbidden

**Residual Risk:**
- If CSRF_COOKIE_HTTPONLY=False (default), attacker can read token from DOM
- If CSRF_COOKIE_SECURE=False on HTTPS, attacker can intercept cookie via network (shouldn't happen but configuration risk)

### Scenario 2: BREACH Attack (Compression Oracle)

**Attack:**
1. Attacker can control some plaintext in victim's request (e.g., URL parameter reflected in response)
2. Attacker observes that when plaintext matches CSRF token bytes, response compresses smaller
3. Attacker can oracle CSRF token byte-by-byte via timing

**Mitigation:**
1. **Token Masking:** Every request gets new random mask (line 64 of csrf.py)
2. **Entropy:** New mask makes token different even if underlying secret is same
3. **Result:** Compression oracle cannot work because token changes per request

**Implementation:**
- Mask + Cipher format ensures different appearance of same secret token
- Without masking: Same secret token → Same bytes → Better compression with matching plaintext

### Scenario 3: Session Data Tampering

**Attack:**
1. Attacker intercepts session cookie (if not secure)
2. Attacker modifies session data (e.g., user_id field)
3. Attacker replays modified cookie

**Mitigation:**
1. **HMAC Signature:** Session data is signed with HMAC-SHA256
2. **Derived Key:** Key derived from SECRET_KEY + salt ensures tampering detection
3. **Constant-Time Comparison:** Signature verified without timing leak
4. **Timestamp:** TimestampSigner includes timestamp in signed data
5. **Max Age Check:** Session.load() validates max_age parameter (line 17 of signed_cookies.py)

**Residual Risk:**
- If SECRET_KEY is compromised, attacker can forge signatures
- If stored in database but database is compromised, attacker can still read/modify session data (but signature prevents modification detection)

### Scenario 4: Session Fixation Attack

**Attack:**
1. Attacker sets known session key in victim's browser
2. Victim logs in, session now contains authentication data
3. Attacker uses same known session key to impersonate victim

**Mitigation:**
1. **Session Rotation:** Django doesn't automatically rotate on login (application responsibility)
2. **Key Generation:** New session keys are cryptographically random (get_random_string at line 195 of base.py)
3. **Uniqueness Check:** _get_new_session_key() checks session doesn't already exist (line 196)

**Application Responsibility:**
- Application should call django.contrib.auth.login() which calls request.session.cycle_key()
- This creates new session_key with same data, invalidating fixated key

### Scenario 5: Cross-Subdomain Cookie Sharing

**Attack:**
1. If CSRF_COOKIE_DOMAIN=".example.com", cookie shared with sub.example.com
2. Attacker controls sub.example.com
3. Attacker can read CSRF cookie (if HTTPONLY=False) from sub.example.com
4. Attacker can send cross-origin requests from sub.example.com to main.example.com with valid CSRF token

**Mitigation:**
1. **Origin Checking:** _origin_verified() checks Origin header against current host (line 274)
2. **Referer Checking:** _check_referer() validates Referer header (line 298)
3. **Same-Origin Policy:** Browser doesn't send Referer for cross-subdomain requests if from HTTPS to HTTPS (but does from HTTP to HTTPS or HTTP to HTTP)
4. **SameSite Attribute:** Set to "Lax" by default (line 575 of global_settings.py)
   - Prevents cookie from being sent on cross-site POST requests
   - Still sent for top-level navigation

**Residual Risk:**
- If subdomain is compromised, it can construct Referer with valid origin
- SameSite=Lax still allows cookie on top-level navigation

---

## Cookie Security Attributes Analysis

### CSRF Cookie Configuration

**Default Settings** (from django/conf/global_settings.py:569-575):

```python
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52  # 1 year
CSRF_COOKIE_DOMAIN = None  # Request domain
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SECURE = False  # ⚠️ HTTP cookies allowed
CSRF_COOKIE_HTTPONLY = False  # ⚠️ Accessible to JavaScript
CSRF_COOKIE_SAMESITE = "Lax"
```

**Security Implications:**

| Attribute | Value | Security Impact |
|-----------|-------|-----------------|
| **SECURE** | False | ⚠️ CRITICAL: Allows transmission over HTTP, subject to MITM interception. Recommendation: Set to True in production. Django security check W016 warns about this. |
| **HTTPONLY** | False | ⚠️ HIGH: Allows JavaScript access, subject to XSS. Recommendation: Set to True unless AJAX needs direct access. Session cookie sets this to True by default. |
| **SAMESITE** | Lax | GOOD: Prevents cookie on cross-site POST (only top-level navigation). Protects against many CSRF variants. Lax is good balance; Strict would prevent more but break navigation. |
| **AGE** | 1 year | NORMAL: Long duration means long window for token compromise/reuse, but reasonable for security vs usability. |
| **PATH** | / | NORMAL: All paths can access cookie. Can restrict to /admin etc if needed. |
| **DOMAIN** | None | GOOD: Restricts to request domain, prevents subdomain sharing. Can be set to ".example.com" for sharing. |

### Session Cookie Configuration

**Default Settings** (from django/conf/global_settings.py:484-497):

```python
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 2  # 2 weeks
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_HTTPONLY = True  # ✓ Protected from JavaScript
SESSION_COOKIE_SAMESITE = "Lax"
```

**Security Comparison to CSRF Cookie:**
- **HTTPONLY=True:** Better protection than CSRF cookie; cannot be stolen via XSS
- **SECURE=False:** Same concern as CSRF cookie
- **SAMESITE=Lax:** Same as CSRF cookie

---

## Vulnerability Analysis

### V1: CSRF Cookie Not HttpOnly by Default

**Severity:** Medium
**CWE:** CWE-1004 (Sensitive Cookie in HTTPS Session Without 'Secure' Attribute)

**Details:**
- CSRF_COOKIE_HTTPONLY defaults to False
- Allows JavaScript (including XSS attacks) to read CSRF token
- Unlike session cookies which are marked HttpOnly by default

**Attack Scenario:**
```javascript
// XSS on bank.com
var token = document.querySelector('[name="csrfmiddlewaretoken"]').value;
// Or from cookie if not HttpOnly
var token = document.cookie.match(/csrftoken=([^;]+)/)[1];
// Attacker can now use token for cross-origin requests
```

**Mitigation:**
1. Django provides setting: `CSRF_COOKIE_HTTPONLY = True`
2. Security check: Django security check W016 warns if CSRF_COOKIE_SECURE=False
3. No check for HTTPONLY though

**Recommendation:**
- Deployments should set `CSRF_COOKIE_HTTPONLY = True` in settings
- Consider making this default in Django to match session cookie behavior
- Document the security implications more prominently

### V2: CSRF Cookie Not Secure by Default on HTTPS

**Severity:** High (in production)
**CWE:** CWE-614 (Sensitive Cookie in HTTPS Session Without 'Secure' Attribute)

**Details:**
- CSRF_COOKIE_SECURE defaults to False
- On HTTPS sites, allows cookie to be transmitted over HTTP if downgrade occurs
- Browser would send HTTPS cookie over HTTP if protocol downgrade happens (HTTPS Everywhere not universal)

**Attack Scenario:**
1. Victim on HTTPS bank.com
2. Attacker performs SSL stripping or downgrades connection
3. Browser sends CSRF cookie over HTTP
4. Attacker intercepts cookie and forges requests

**Mitigations Provided:**
1. Django security check W016: Warns if CSRF_COOKIE_SECURE=False and CSRF middleware enabled
2. Encourages setting to True: "Using a secure-only CSRF cookie makes it more difficult for network traffic sniffers to steal the CSRF token"

**Recommendation:**
- MUST set `CSRF_COOKIE_SECURE = True` in production (HTTPS-only sites)
- Consider default=True when DEBUG=False

### V3: CSRF Token Transmitted in POST Body

**Severity:** Low
**CWE:** CWE-200 (Information Exposure)

**Details:**
- CSRF token is sent in form POST field or X-CSRFToken header
- POST body is visible to attacker if they can MitM connection (but CSRF protection doesn't help then)
- Token in HTML form is readable by XSS

**Mitigations:**
1. X-CSRFToken header is alternative (line 384 of csrf.py)
   - Browser doesn't expose custom headers to attacker easily
   - Preferred for AJAX over POST field
2. Masked token ensures each request has different appearance
3. Token validation prevents unauthorized use

### V4: Session Timing Information Leakage

**Severity:** Very Low
**CWE:** CWE-208 (Observable Timing Discrepancy)

**Details:**
- TimestampSigner includes timestamp in signed data: `<data>:<timestamp>:<sig>`
- Timestamp encoded as base62, visible in cookie
- Attacker can determine when session was created/modified

**Mitigations:**
1. Timestamp is part of signed data, cannot be forged
2. Information leakage is minimal (only session creation time)
3. No cryptographic impact

**Recommendation:**
- Document that session timestamps are visible in cookies
- Not a concern in practice

### V5: CSRF Middleware Must Run Before SessionMiddleware

**Severity:** Medium
**CWE:** CWE-693 (Protection Mechanism Failure)

**Details:**
- If CSRF_USE_SESSIONS=True but SessionMiddleware doesn't run first
- CsrfViewMiddleware tries to access request.session and gets AttributeError (line 231-237)
- Raises ImproperlyConfigured, which is good, but deployment error

**Mitigations:**
1. Check raises ImproperlyConfigured with clear message (line 233-236)
2. Recommends SessionMiddleware before CsrfViewMiddleware
3. Django check W003 could be enhanced to verify ordering

**Recommendation:**
- Document middleware ordering requirements clearly
- Consider runtime check if SESSION_ENGINE check could be added

---

## Summary of Security Properties

### Strengths

1. **Cryptographically Sound:**
   - Uses standard HMAC-SHA256 with salted key derivation
   - Constant-time comparison prevents timing attacks
   - Secure randomness via secrets module

2. **Defense-in-Depth:**
   - Multiple validation layers: format check → unmask → signature verify
   - Token masking prevents BREACH compression attacks
   - Origin/Referer validation supplements token validation
   - SameSite cookies provide additional protection

3. **Session Integrity:**
   - Signed session data prevents tampering
   - Timestamps prevent old session reuse
   - Fallback keys support key rotation

4. **HttpOnly Session Cookies:**
   - Session cookies marked HttpOnly by default (unlike CSRF cookies)
   - Prevents XSS exfiltration of authentication tokens

5. **Flexible Configuration:**
   - Multiple session backends (DB, cache, file, signed cookies)
   - Easy to enable/disable features per deployment needs

### Weaknesses

1. **CSRF Cookie Not HttpOnly by Default:**
   - JavaScript can read CSRF token, enabling XSS-based CSRF
   - Inconsistent with session cookie security defaults

2. **CSRF Cookie Not Secure by Default:**
   - Allows HTTP transmission on HTTPS sites (with downgrade)
   - Security check W016 warns but doesn't fail

3. **Token Masking Adds Complexity:**
   - Increases code complexity for BREACH protection only
   - Unnecessary if TLS 1.3 compression disabled (no compression by default)
   - Could be simplified or optional

4. **Origin/Referer Validation Can Be Spoofed:**
   - Attacker can include valid Origin/Referer if compromised subdomain
   - Not a real weakness due to token validation, but adds redundancy

5. **No Built-in Session Rotation:**
   - Developers must explicitly call cycle_key() or auth.login()
   - Session fixation possible if forgotten
   - Could be automatic on privilege level changes

### Recommendations

1. **Defaults Enhancement:**
   - Consider `CSRF_COOKIE_HTTPONLY = True` by default
   - Consider `CSRF_COOKIE_SECURE = True` by default when DEBUG=False
   - Add Django check for CSRF_COOKIE_HTTPONLY

2. **Documentation:**
   - Highlight security implications of cookie attributes
   - Document recommended production settings
   - Explain BREACH attack and mitigation

3. **Simplification Opportunity:**
   - Token masking provides BREACH protection, but:
     - BREACH requires response compression (rare in modern TLS)
     - Adds unmasking complexity to every token validation
   - Consider optional masking or deprecation for TLS 1.3

4. **Session Handling:**
   - Document explicit session.cycle_key() requirement
   - Consider automatic rotation on authentication level changes
   - Add check for explicit cycle_key() in auth.login()

5. **Timing Attack Prevention:**
   - Audit all string comparisons use constant_time_compare()
   - Use secrets.compare_digest() consistently
   - Document timing attack risks

---

## Conclusion

Django's CSRF protection and session handling pipeline implements multiple layers of cryptographic protection and validation. The use of HMAC-SHA256, constant-time comparison, and secure randomness provides strong cryptographic foundations. Token masking defends against BREACH attacks, and origin/referer validation supplements token-based protection.

However, default cookie security configurations leave deployment concerns. The CSRF_COOKIE_HTTPONLY and CSRF_COOKIE_SECURE settings default to values that allow potential compromise vectors, though security checks attempt to warn developers.

The architecture is sound, but deployment security depends critically on properly configured settings. Django provides the tools for secure deployment; operators must use them correctly.
