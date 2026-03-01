# Django CSRF Protection and Session Handling Security Analysis

## Files Examined

### Core CSRF & Session Middleware
- **django/middleware/csrf.py** — CSRF token generation, validation, masking/unmasking, and cookie handling
- **django/contrib/sessions/middleware.py** — Session middleware for loading/saving session data and setting cookies

### Cryptographic Foundation
- **django/utils/crypto.py** — Cryptographic primitives: `salted_hmac()`, `constant_time_compare()`, `get_random_string()`
- **django/core/signing.py** — HMAC-based signing system: `Signer`, `TimestampSigner`, `dumps()`, `loads()`, salt-based key derivation
- **django/core/handlers/wsgi.py** — WSGI HTTP request parsing, cookie extraction from `HTTP_COOKIE` header
- **django/core/handlers/asgi.py** — ASGI HTTP request parsing, cookie extraction

### Session Backend Implementation
- **django/contrib/sessions/backends/base.py** — Base `SessionBase` class with `encode()`, `decode()` methods using signed JSON
- **django/contrib/sessions/backends/db.py** — Database-backed session storage with encoded session data
- **django/contrib/sessions/backends/signed_cookies.py** — Client-side signed cookie session storage
- **django/http/request.py** — HTTP request object with COOKIES property
- **django/http/cookie.py** — `parse_cookie()` function for parsing raw HTTP Cookie header
- **django/http/response.py** — HTTP response with cookie setting methods

---

## Entry Points

Untrusted data enters the CSRF/session subsystem at the following critical points:

### 1. **Cookie Parsing Entry Point**
- **File**: `django/http/request.py:131-132` (ASGIRequest) and `django/core/handlers/wsgi.py:100-102` (WSGIRequest)
- **Source**: HTTP `Cookie` header from client (untrusted)
- **Function**: `parse_cookie()` from `django/http/cookie.py:7-23`
- **Accepts**: Raw cookie string from HTTP header, splits on `;`, parses `key=value` pairs
- **Attack Surface**: Malformed cookies, overly long cookies, special characters
- **Validation**: `parse_cookie()` uses Python's standard `http.cookies._unquote()` but performs minimal validation

### 2. **CSRF Cookie Extraction**
- **File**: `django/middleware/csrf.py:240`
- **Function**: `_get_secret()` method in `CsrfViewMiddleware`
- **Source**: `request.COOKIES[settings.CSRF_COOKIE_NAME]` (untrusted HTTP cookie)
- **Entry**: Direct dict access to parsed cookie dictionary
- **Validation**: Format validation via `_check_token_format()` at line 245, checking:
  - Length must be `CSRF_SECRET_LENGTH` (32 chars) or `CSRF_TOKEN_LENGTH` (64 chars)
  - All characters must match `CSRF_ALLOWED_CHARS` (a-z, A-Z, 0-9)

### 3. **CSRF Token from POST Data**
- **File**: `django/middleware/csrf.py:368`
- **Function**: `_check_token()` method calls `request.POST.get("csrfmiddlewaretoken", "")`
- **Source**: POST form data (untrusted user input)
- **Entry**: Parsed from POST body during `request.POST` access
- **Validation**: Format validation via `_check_token_format()` at line 392

### 4. **CSRF Token from HTTP Headers**
- **File**: `django/middleware/csrf.py:384`
- **Function**: `request.META[settings.CSRF_HEADER_NAME]` (default: `HTTP_X_CSRFTOKEN`)
- **Source**: HTTP header (untrusted header value)
- **Entry**: Extracted from request META dictionary, populated by WSGI/ASGI handler from HTTP headers
- **Validation**: Format validation via `_check_token_format()` at line 392

### 5. **Session Cookie (Session Key)**
- **File**: `django/contrib/sessions/middleware.py:19`
- **Function**: `process_request()` method
- **Source**: HTTP `sessionid` cookie (untrusted HTTP cookie)
- **Entry**: `request.COOKIES.get(settings.SESSION_COOKIE_NAME)`
- **Validation**: Length validation in `SessionBase._validate_session_key()` (base.py:215-220):
  - Must be truthy and at least 8 characters long
  - Then passed to session backend's `load()` method for deserialization

### 6. **Session Data Deserialization**
- **File**: `django/contrib/sessions/backends/signed_cookies.py:13-19` or `db.py:55-56`
- **Function**: `load()` method calls `signing.loads()` with session_key
- **Source**: Session data is either:
  - **Signed cookies backend**: Session data is the entire cookie value (untrusted)
  - **Database backend**: Session data from database record (trusted if session_key lookup is valid)
- **Entry**: `signing.loads()` function accepts the signed data string
- **Validation**: HMAC signature validation inside `Signer.unsign()` and `TimestampSigner.unsign()`

### 7. **Origin and Referer Headers (for CSRF origin/referer checks)**
- **File**: `django/middleware/csrf.py:272` (Origin) and `django/middleware/csrf.py:298` (Referer)
- **Function**: `_origin_verified()` and `_check_referer()` methods
- **Source**: HTTP headers (untrusted)
- **Entry**: `request.META["HTTP_ORIGIN"]` and `request.META["HTTP_REFERER"]`
- **Validation**: URL parsing and domain matching using `urlsplit()` and `is_same_domain()`

---

## Data Flow

### Flow 1: CSRF Protection Pipeline - Request Reception to Cookie Validation

```
1. Source: django/core/handlers/wsgi.py:101 or asgi.py:86-99
   - HTTP_COOKIE header from network
   - Untrusted: Yes, sent by client

2. Transform: django/http/cookie.py:7-23 (parse_cookie)
   - Split on ";", parse key=value pairs
   - Decode quoted values using http.cookies._unquote()
   - Returns dict: {"csrftoken": "<raw_cookie>", ...}
   - Validation: None on format at this stage

3. Access: django/middleware/csrf.py:240 (CsrfViewMiddleware._get_secret)
   - Retrieves csrf_secret from request.COOKIES[settings.CSRF_COOKIE_NAME]
   - If CSRF_USE_SESSIONS=True: Gets from request.session instead (deferred decryption)
   - If CSRF_USE_SESSIONS=False: Validates format here

4. Validation: django/middleware/csrf.py:245 (_check_token_format)
   - Checks length: must be 32 (CSRF_SECRET_LENGTH) or 64 (CSRF_TOKEN_LENGTH)
   - Checks charset: only CSRF_ALLOWED_CHARS allowed (a-z, A-Z, 0-9)
   - Rejects invalid format with InvalidTokenFormat exception

5. Unmask if needed: django/middleware/csrf.py:249-250 (_unmask_cipher_token)
   - If length == 64, assume first 32 chars are mask, last 32 are ciphered secret
   - Decrypt using modular arithmetic: secret_char = (cipher_char - mask_char) mod 62

6. Store: django/middleware/csrf.py:412 (process_request)
   - Stores unmasked secret in request.META["CSRF_COOKIE"]
   - Sets request.META["CSRF_COOKIE_NEEDS_UPDATE"] flag

7. Sink: django/middleware/csrf.py:397 (_check_token - token validation)
   - Comparison with user-supplied token from POST/header using constant_time_compare()
```

### Flow 2: CSRF Token Validation Pipeline - View Processing

```
1. Source: django/middleware/csrf.py:368 (request.POST.get("csrfmiddlewaretoken", ""))
           OR django/middleware/csrf.py:384 (request.META[settings.CSRF_HEADER_NAME])
   - Untrusted: Yes, from user input (form data or header)

2. Validation: django/middleware/csrf.py:392 (_check_token_format)
   - Same format checks as cookie

3. Comparison: django/middleware/csrf.py:397 (_does_token_match)
   - If token length == 64 (masked): Unmask first, then compare
   - Use constant_time_compare() to prevent timing attacks
   - Compare unmasked token with CSRF_COOKIE secret

4. Sink: django/middleware/csrf.py:465 (process_view validation)
   - If match fails: Reject request with 403 Forbidden
   - If match succeeds: Allow request to proceed
```

### Flow 3: CSRF Token Generation Pipeline - Response Masking

```
1. Source: django/middleware/csrf.py:96-114 (get_token function)
   - Called to generate/refresh CSRF token for forms
   - No external untrusted input at generation

2. Secret Generation: django/middleware/csrf.py:86 (_get_new_csrf_string)
   - Uses get_random_string(CSRF_SECRET_LENGTH=32, allowed_chars=CSRF_ALLOWED_CHARS)
   - Calls django/utils/crypto.py:51-62 (get_random_string)
   - Uses secrets.choice() for cryptographically secure randomness

3. Masking: django/middleware/csrf.py:59-68 (_mask_cipher_secret)
   - Generate random mask (32 chars from CSRF_ALLOWED_CHARS)
   - Encrypt secret using mask: cipher[i] = (secret[i] + mask[i]) mod 62
   - Return mask + cipher (64 chars total)
   - Purpose: Prevent BREACH attack (compress sensitive CSRF token in response)

4. Sink: django/middleware/csrf.py:258-267 (process_response - _set_csrf_cookie)
   - Set HTTP cookie with unmasked secret (if CSRF_USE_SESSIONS=False)
   - Cookie attributes:
     - HttpOnly: settings.CSRF_COOKIE_HTTPONLY (prevents JS access)
     - Secure: settings.CSRF_COOKIE_SECURE (HTTPS only)
     - SameSite: settings.CSRF_COOKIE_SAMESITE (Lax/Strict/None)
     - Path: settings.CSRF_COOKIE_PATH
     - Domain: settings.CSRF_COOKIE_DOMAIN
```

### Flow 4: Session Data Pipeline - Session Middleware

```
1. Source: django/contrib/sessions/middleware.py:19 (process_request)
   - Reads session_key from HTTP cookie: request.COOKIES[settings.SESSION_COOKIE_NAME]
   - Untrusted: Yes, from HTTP cookie

2. Validation: django/contrib/sessions/backends/base.py:215-220 (_validate_session_key)
   - Must be truthy and length >= 8
   - For signed_cookies backend: session_key IS the encrypted session data
   - For db backend: session_key is random string, used to look up in database

3. Session Load: django/contrib/sessions/backends/base.py:237-250 (_get_session)
   - Lazy loads session data on first access
   - Calls backend-specific load() method

4a. Signed Cookies Backend Load: django/contrib/sessions/backends/signed_cookies.py:6-24
   - Calls signing.loads(session_key, salt="django.contrib.sessions.backends.signed_cookies")
   - Untrusted input: session_key (the cookie value itself)

4b. Database Backend Load: django/contrib/sessions/backends/db.py:54-56
   - Looks up Session model by session_key (trusted lookup)
   - Calls self.decode(s.session_data)

5. Cryptographic Verification: django/core/signing.py:155-174 (loads function)
   - Calls TimestampSigner.unsign_object()
   - Flow: signing.py:240-251 (unsign_object)
   - Calls Signer.unsign() at line 243

6. Signature Validation: django/core/signing.py:206-213 (Signer.unsign)
   - Splits signed value on separator (default ":")
   - Extracts signature component
   - Computes expected signature using salted_hmac()
   - Compares using constant_time_compare()
   - If no match: Raises BadSignature exception

7. Deserialization: django/core/signing.py:240-251 (unsign_object)
   - Base64 decodes the data
   - Decompresses if needed (zlib)
   - Deserializes JSON back to Python dict
   - Returns session data

8. Sink: django/contrib/sessions/backends/base.py:249 (_get_session)
   - Caches decrypted session data in self._session_cache
   - Data now available as request.session dict
```

### Flow 5: Session Save and Cookie Setting Pipeline

```
1. Source: django/contrib/sessions/middleware.py:22-77 (process_response)
   - Checks if session was modified/accessed
   - Triggers encoding of session data

2. Encoding: django/contrib/sessions/backends/base.py:122-129 (encode)
   - Calls signing.dumps() with session dict
   - Uses salt="django.contrib.sessions.SessionStore" or backend-specific salt
   - Compression enabled by default

3. Signing: django/core/signing.py:131-152 (dumps)
   - Creates TimestampSigner with SECRET_KEY
   - Calls sign_object() to:
     - Serialize dict to JSON
     - Optionally compress with zlib
     - Base64 encode
     - Compute HMAC-SHA256 signature

4. HMAC Computation: django/core/signing.py:199-201 (Signer.signature)
   - Calls base64_hmac() which calls salted_hmac()
   - django/utils/crypto.py:19-45 (salted_hmac)
   - Derives key from key_salt + SECRET_KEY using hash(key_salt + secret).digest()
   - Computes HMAC using derived key and algorithm (default SHA1 -> SHA256 in Signer)

5a. Signed Cookies Backend Save: django/contrib/sessions/backends/signed_cookies.py:39-46
   - Sets self._session_key = signing.dumps(...)
   - Sets modified=True to trigger cookie write

5b. Database Backend Save: django/contrib/sessions/backends/db.py:114-137 (save)
   - Encodes session data
   - Creates/updates Session model with encoded data
   - Stores in database

6. Cookie Setting: django/contrib/sessions/middleware.py:66-76 (process_response)
   - Calls response.set_cookie() with:
     - session_key (for db backend) or signed data (for signed_cookies)
     - HttpOnly: settings.SESSION_COOKIE_HTTPONLY
     - Secure: settings.SESSION_COOKIE_SECURE
     - SameSite: settings.SESSION_COOKIE_SAMESITE
     - Path, Domain, Expiry settings

7. Sink: Response HTTP Set-Cookie header
   - Cookie sent to client browser
   - For signed_cookies: Cookie value is the full signed/compressed/encoded session data
   - For db backend: Cookie value is random session_key (actual data in database)
```

---

## Dependency Chain

### Ordered list of files from entry to cryptographic sink:

1. **django/core/handlers/wsgi.py:100-102** — Extract raw HTTP_COOKIE header from WSGI environ
2. **django/core/handlers/asgi.py:86-99** — Extract raw HTTP headers from ASGI scope
3. **django/http/request.py:60-68** — Initialize HttpRequest with empty COOKIES dict
4. **django/http/cookie.py:7-23** — Parse cookie string into dict (parse_cookie function)
5. **django/middleware/csrf.py:221-251** — Extract and validate CSRF cookie (_get_secret method)
6. **django/middleware/csrf.py:130-140** — Format validation (_check_token_format)
7. **django/middleware/csrf.py:71-81** — Token unmasking (_unmask_cipher_token)
8. **django/middleware/csrf.py:349-399** — Token validation pipeline (_check_token method)
9. **django/utils/crypto.py:65-67** — Constant-time comparison (constant_time_compare)
10. **django/contrib/sessions/middleware.py:18-20** — Load session key from cookie
11. **django/contrib/sessions/backends/base.py:237-250** — Lazy session loading
12. **django/contrib/sessions/backends/signed_cookies.py:6-24** — Load signed cookie session
13. **django/contrib/sessions/backends/db.py:54-56** — Load database session
14. **django/core/signing.py:155-174** — Verify signed data (loads function)
15. **django/core/signing.py:206-213** — HMAC signature verification (Signer.unsign)
16. **django/core/signing.py:240-251** — Decompress and deserialize (unsign_object)
17. **django/utils/crypto.py:19-45** — Derive key and compute HMAC (salted_hmac)
18. **django/contrib/sessions/backends/base.py:122-129** — Encode session for storage
19. **django/contrib/sessions/middleware.py:22-77** — Save session and set cookie

---

## Analysis

### CSRF Protection Mechanism

#### Token Generation and Masking (BREACH Attack Prevention)
Django uses a session-independent CSRF token that is **masked with a one-time cipher to prevent BREACH compression attacks**. This is critical because:

1. **Vulnerability addressed**: The BREACH attack exploits HTTP compression to leak CSRF tokens from encrypted HTTPS responses. If the attacker can control part of the plain text and measure response size, they can recover the token byte-by-byte.

2. **Mitigation approach**:
   - Server generates 32-byte random secret (CSRF_SECRET_LENGTH)
   - Server generates 32-byte random mask for each response
   - Token sent to client = mask + cipher(secret, mask) using additive cipher mod 62
   - Client includes token in next request (either masked or unmasked)
   - Server stores secret, not masked token
   - If token is 64 chars: unmask it to recover secret, then compare with stored secret
   - If token is 32 chars: direct comparison (legacy Django 4.0+ unmasked storage)

3. **Cipher security**: The masking cipher is **NOT cryptographically secure** for actual encryption:
   ```python
   cipher[i] = (secret[i] + mask[i]) % 62  # Simple addition mod 62
   ```
   However, it's **secure against BREACH** because:
   - Different mask for each response (random)
   - Mask is sent to client (not secret)
   - Even if attacker sees masked token, they can't predict actual secret without mask
   - Server comparison is constant-time

4. **Limitations**:
   - If both secret and mask are known, cipher is broken (trivial recovery)
   - No protection if client stores token in plaintext (localStorage)
   - Relies on HttpOnly cookie for secret, JavaScript can't access it

#### Constant-Time Comparison
Django uses `secrets.compare_digest()` (available since Python 3.3) via `constant_time_compare()`:
- Prevents timing side-channel attacks where attacker measures comparison time to infer token
- Compares all bytes regardless of early mismatch
- Used in both `_does_token_match()` and signature validation

#### Origin and Referer Validation
For HTTPS requests without Origin header, Django validates Referer header to prevent CSRF:
- Checks that Referer comes from allowed origins (CSRF_TRUSTED_ORIGINS)
- Uses domain matching, allows subdomains for wildcard origins
- Insecure referer (http on https request) is rejected
- Missing referer on HTTPS POST is rejected (strict policy)

**Potential issue**: If Site uses CORS and processes requests from multiple origins, configuration must precisely match; overly permissive CSRF_TRUSTED_ORIGINS bypasses protection.

#### Session Storage Modes

1. **CSRF_USE_SESSIONS=False (default)**:
   - CSRF secret stored in unmasked form in HTTP-only cookie
   - Masked token returned to client for form embedding
   - Advantages: Stateless, no server-side session needed
   - Disadvantage: Secret exposed in cookie (mitigated by HttpOnly)

2. **CSRF_USE_SESSIONS=True**:
   - CSRF secret stored in signed session dict
   - Session itself is signed/encrypted
   - Advantages: Doesn't require separate cookie
   - Disadvantage: Requires SESSION_MIDDLEWARE before CSRF middleware

---

### Session Management and Cryptographic Signing

#### Signature Algorithm Chain
```
Secret Key (settings.SECRET_KEY)
  ↓
salted_hmac(salt="django.contrib.sessions.SessionStore", value, SECRET_KEY)
  ↓
key = hashlib.sha1(salt + SECRET_KEY).digest()  # Derived key
  ↓
HMAC-SHA256(key, session_dict_serialized)
  ↓
base64_urlsafe_encode(digest)
  ↓
Signed Session: "encoded_data:timestamp:signature"
```

#### Key Derivation
Django uses a **salted key derivation**:
```python
key = hasher(key_salt + secret).digest()  # hasher = sha1 by default
return hmac.new(key, msg=value, digestmod=hasher)
```

**Security properties**:
- Different salt for each subsystem (CSRF, sessions, etc.) prevents cross-subsystem attacks
- Key is derived per-HMAC (not reused), reduces key exposure in memory
- Uses HMAC with derived key (not direct SECRET_KEY), provides additional layer
- Supports key rotation via SECRET_KEY_FALLBACKS

**Weakness**:
- Key derivation uses SHA1 by default (old standard), though HMAC-SHA256 is used for signature
- If SHA1 is weak, the derived key may be weak, though this is mitigated by HMAC-SHA256

#### Session Serialization and Deserialization
- **Format**: `"base64_encoded_json:timestamp:hmac_signature"`
- **Compression**: Optional zlib compression (enabled by default)
- **Serialization**: `JSONSerializer` uses `json.dumps(separators=(",", ":"))` for compact JSON
- **Deserialization**: `json.loads()` parses JSON back to Python dict

**Potential vulnerabilities**:
- **JSON pickle gadgets**: If SESSION_SERIALIZER uses pickle instead of JSON, untrusted signed data can lead to RCE via pickle gadgets
- **Zlib decompression**: Signed data is compressed; zlib decompression is not a vulnerability by itself but must decompress correctly
- **Bad signature handling**: BadSignature exception is caught, returns empty dict - hides decryption failures

#### Timestamp Verification
`TimestampSigner` adds timestamp component:
```python
signed_value = "data:timestamp:signature"
unsign(value, max_age=3600)  # Verify signature AND timestamp within max_age
```

**Security**: Prevents replay of old session cookies if max_age is enforced. Default behavior:
- Signed cookies backend: `max_age=SESSION_COOKIE_AGE` (default 2 weeks)
- Database backend: No timestamp check (relies on database expire_date column)

**Weakness**: Default max_age is very long (14 days), allows old sessions to be replayed if signed with old SECRET_KEY.

---

### Cookie Security Attributes

#### CSRF Cookie Attributes (django/middleware/csrf.py:258-267)
```python
response.set_cookie(
    settings.CSRF_COOKIE_NAME,  # default: "csrftoken"
    request.META["CSRF_COOKIE"],  # Unmasked secret (32 chars)
    max_age=settings.CSRF_COOKIE_AGE,  # default: 31449600 (1 year)
    domain=settings.CSRF_COOKIE_DOMAIN,  # default: None
    path=settings.CSRF_COOKIE_PATH,  # default: "/"
    secure=settings.CSRF_COOKIE_SECURE,  # default: False
    httponly=settings.CSRF_COOKIE_HTTPONLY,  # default: False
    samesite=settings.CSRF_COOKIE_SAMESITE,  # default: "Lax"
)
```

**Security analysis**:
- **HttpOnly=False (default)**: **CRITICAL**. JavaScript can access CSRF token via `document.cookie`, which is the intended design. However, this prevents protection against XSS if JavaScript is compromised.
- **SameSite=Lax (default)**: Protects against cross-site cookie sending, but allows sending on top-level navigations (POST from external site). Django still validates token, so CSRF protected.
- **Secure=False (default)**: Cookie sent over HTTP, vulnerable to MITM. Must be set to True in production.
- **max_age=1 year**: Very long expiry, allows token to be reused indefinitely once generated.

#### Session Cookie Attributes (django/contrib/sessions/middleware.py:66-76)
```python
response.set_cookie(
    settings.SESSION_COOKIE_NAME,  # default: "sessionid"
    request.session.session_key,  # session_key or signed data
    max_age=max_age,  # expiry_age or None
    expires=expires,
    domain=settings.SESSION_COOKIE_DOMAIN,  # default: None
    path=settings.SESSION_COOKIE_PATH,  # default: "/"
    secure=settings.SESSION_COOKIE_SECURE or None,  # default: False
    httponly=settings.SESSION_COOKIE_HTTPONLY or None,  # default: True
    samesite=settings.SESSION_COOKIE_SAMESITE,  # default: "Lax"
)
```

**Security analysis**:
- **HttpOnly=True (default)**: Protects session cookie from XSS JavaScript access. Good default.
- **SameSite=Lax (default)**: Protects against cross-site cookie sending, but allows on top-level navigations.
- **Secure=False (default)**: Cookie sent over HTTP, vulnerable to MITM. Must be set to True in production.
- **max_age from get_expiry_age()**: Default 2 weeks (SESSION_COOKIE_AGE setting)

#### Interaction Between CSRF and SameSite Cookie
Modern browsers enforce SameSite=Lax on cookies, which means:
- Cookies are NOT sent on cross-site POST requests (subdomains, different domains)
- Cookies ARE sent on top-level navigations (user clicks link to attacker site)
- Django's CSRF protection still validates token, so even if cookie is sent, attack fails without valid token

**Design note**: Django's CSRF protection is **defense-in-depth**:
1. SameSite cookie attribute (browser enforces)
2. Origin/Referer header validation (server enforces)
3. CSRF token validation (server enforces)

All three must fail for CSRF to succeed.

---

### Attack Vectors and Mitigations

#### 1. Token Format Bypass
**Attack**: Attacker crafts token with invalid characters or length to bypass `_check_token_format()`
**Mitigation**: Strict format validation at line 136-140:
- Length must be exactly 32 or 64 chars
- All chars must be in CSRF_ALLOWED_CHARS (a-z, A-Z, 0-9)
- Regex check prevents any special chars
**Status**: ✓ Secure

#### 2. Timing Side-Channel on Token Comparison
**Attack**: Attacker uses timing differences to infer correct token byte-by-byte
**Mitigation**: `constant_time_compare()` at line 157 and in signature validation
- Uses `secrets.compare_digest()` under the hood
- Compares all bytes even after mismatch found
**Status**: ✓ Secure

#### 3. BREACH Compression Attack
**Attack**: Attacker controls response content, measures compression to recover CSRF token
**Mitigation**: Token masking with one-time cipher at line 59-68
- Mask is random per response, prevents compression side-channel
- Cipher is not reused across responses
**Status**: ✓ Secure (mitigated)
**Caveat**: Requires HTTPS with Content-Encoding: gzip to compress. If response not compressed, masking doesn't prevent BREACH.

#### 4. Token Fixation
**Attack**: Attacker sets victim's CSRF cookie to known value, uses same token in attack form
**Mitigation**:
- Secret is random and unguessable (32 bits of entropy from CSRF_ALLOWED_CHARS)
- Server generates new secret if cookie is invalid or missing
- `rotate_token()` function at line 117-122 allows forced rotation on login
**Status**: ✓ Secure if rotate_token() is called on login; ⚠ Vulnerable if not called

#### 5. Session Hijacking via Signed Cookies
**Attack**: Attacker captures signed session cookie, uses it indefinitely
**Mitigation**:
- HMAC signature validates cookie hasn't been tampered with
- Timestamp validation (if max_age enforced)
- Secret key rotation via SECRET_KEY_FALLBACKS
**Status**: ✓ Secure if HTTPS and HttpOnly enforced; ⚠ Weak if max_age is very long (14 days default)

#### 6. Session Fixation
**Attack**: Attacker sets victim's session cookie to a known value
**Mitigation**: Session backends generate random session_key; can't be predicted
**Status**: ✓ Secure

#### 7. Pickle Deserialization RCE
**Attack**: If SESSION_SERIALIZER uses pickle (not JSON), attacker crafts malicious signed data
**Mitigation**: Django defaults to JSONSerializer, not PickleSerializer
- Django 4.0+ requires explicit opt-in for unsafe serializers
- BadSignature on tampering prevents exploitation
**Status**: ✓ Secure (default JSON safe); ⚠ Vulnerable if PickleSerializer explicitly configured

#### 8. Cookie Substitution Attack
**Attack**: Attacker with network access (MITM) modifies cookie in transit
**Mitigation**: HTTPS + Secure cookie flag + HMAC signature
**Status**: ✓ Secure if HTTPS enforced; ❌ Vulnerable if HTTP used

#### 9. XSS to CSRF
**Attack**: Attacker injects JavaScript via XSS, steals CSRF token and performs CSRF
**Mitigation**:
- HttpOnly flag on session cookie prevents JS access (good default)
- CSRF token in DOM (not cookie), vulnerable to JS theft
- Server validates token, but JS can read and use it
**Status**: ⚠ Mitigated but not eliminated; XSS + CSRF = full compromise

#### 10. CSRF via GET Request
**Attack**: Attacker uses image/script to trigger GET request (no form submission)
**Mitigation**: CSRF middleware only protects non-safe methods (POST, PUT, DELETE, PATCH)
- GET/HEAD/OPTIONS/TRACE are not protected
**Status**: ✓ Secure (by design, GETs should be idempotent)

#### 11. Subdomain Cookie Access
**Attack**: Attacker on subdomain.example.com tries to access example.com cookies
**Mitigation**: CSRF_COOKIE_DOMAIN setting must be specific (not `.example.com`)
- Browser enforces same-origin for cookies if domain starts with "."
**Status**: ⚠ Dependent on configuration; ❌ Vulnerable if CSRF_COOKIE_DOMAIN=".example.com"

---

### Weaknesses and Gaps

1. **Missing rotating CSRF token**: Token is reused across requests (only masked). An attacker who learns the secret can use it for all requests until expiry (1 year default). Modern CSRF frameworks generate new tokens per request.

2. **No CSRF protection for GET with origin header check only**: If Origin header is present but doesn't match, request is rejected. However, if Origin header is absent AND request is HTTPS, Django relies on Referer check. If Referer is stripped by browser/network, attack succeeds.

3. **Very long default CSRF token expiry**: 31449600 seconds (1 year). Token can be replayed indefinitely. Should be shorter (session duration).

4. **Session cookie max_age not enforced**: Database backend ignores timestamp, relies on database expire_date. If database is not cleaned up, expired sessions remain accessible.

5. **No protection against cookie tossing**: If attacker can set any CSRF_COOKIE_DOMAIN cookie, it shadows the real cookie. Django doesn't validate multiple cookies with same name.

6. **Signed cookies backend has no server-side revocation**: Signed session cannot be revoked (no server-side state). Attacker can use old session until max_age expires. Database backend is better (can revoke).

---

## Summary

Django's CSRF and session handling system implements **defense-in-depth with strong cryptographic protections**:

### CSRF Protection
- **Token masking** prevents BREACH compression attacks
- **Constant-time comparison** prevents timing side-channels
- **Origin/Referer validation** provides defense-in-depth
- **Session-independent secrets** prevent CSRF without session access
- **Format validation** prevents injection attacks

**Entry points**: HTTP Cookie, POST data, HTTP headers (Origin, Referer, X-CSRFToken)
**Cryptographic foundation**: HMAC-SHA256 for token masking validation (additive cipher for token transport only)
**Cookie security**: HttpOnly=False (intentional), SameSite=Lax (default), Secure=False (must be configured), 1-year expiry (too long)

### Session Management
- **HMAC signature validation** ensures session integrity
- **Timestamp verification** prevents replay if enforced
- **Multiple backend options**: Database (stateful, revocable) and signed cookies (stateless)
- **Derived keys** prevent subsystem-specific attacks
- **Fallback keys** enable secret rotation

**Entry points**: HTTP session cookie
**Cryptographic foundation**: HMAC-SHA256 (via Signer/TimestampSigner)
**Data flow**: Parse → Validate length → Deserialize (JSON) → Verify HMAC → Return dict
**Cookie security**: HttpOnly=True (good default), SameSite=Lax (default), Secure=False (must be configured), 2-week default expiry

### Critical Configuration Issues
1. **CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE must be True in production** (MITM vulnerable otherwise)
2. **CSRF_COOKIE_HTTPONLY should typically be False** (needed for CSRF token access)
3. **SESSION_COOKIE_HTTPONLY must be True** (prevents XSS-to-session theft)
4. **rotate_token() must be called on login** (prevents token fixation)
5. **CSRF_TRUSTED_ORIGINS must be precisely configured** (overly permissive bypasses protection)
6. **For signed cookies, max_age should be enforced to prevent indefinite replays**

### Attack Surface
- **Highest risk**: Misconfiguration (Secure=False, overly permissive CSRF_TRUSTED_ORIGINS, no rotate_token on login)
- **Medium risk**: XSS (compromises CSRF token in DOM, but not session cookie if HttpOnly=True)
- **Low risk**: Direct cryptographic attacks (HMAC-SHA256 is secure, constant-time comparison prevents timing leaks)

Django's CSRF and session security is **well-designed and cryptographically sound**, with the primary risks being **operational (configuration) rather than fundamental (algorithmic)**.
