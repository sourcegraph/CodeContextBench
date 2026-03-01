# PostgreSQL Client Authentication Pipeline Security Analysis

## Files Examined

- `src/backend/libpq/auth.c` — Main authentication entry point and dispatcher for all authentication methods
- `src/backend/libpq/auth-scram.c` — SCRAM-SHA-256 SASL mechanism implementation
- `src/backend/libpq/auth-sasl.c` — SASL framework for challenge-response authentication
- `src/backend/libpq/crypt.c` — Password cryptography and verification (plaintext, MD5, SCRAM)
- `src/backend/libpq/hba.c` — Host-Based Authentication (HBA) configuration parsing and rule matching
- `src/backend/libpq/pqcomm.c` — Protocol communication and message I/O
- `src/backend/tcop/backend_startup.c` — Startup packet processing and initial connection setup
- `src/backend/libpq/be-secure.c` — SSL/TLS security layer
- `src/backend/postmaster/postmaster.c` — Postmaster main loop and connection acceptance
- `src/include/libpq/auth.h` — Authentication subsystem public header

## Entry Points

1. **src/backend/postmaster/postmaster.c:BackendStartup** — Accepts TCP connections from clients via `AcceptConnection()` and initiates backend startup
   - Accepts: Raw TCP connection from the network
   - No validation at this stage; raw socket accepted

2. **src/backend/tcop/backend_startup.c:ProcessStartupPacket (lines 492-850)** — Receives and parses the PostgreSQL startup message
   - Accepts: Untrusted startup packet containing protocol version, user name, database name, options
   - Extracts: `port->user_name`, `port->database_name`, `port->cmdline_options`, `port->application_name`
   - Validation: Checks packet length (535-542), validates protocol version (705-713), validates user name is provided (827-830), truncates names to NAMEDATALEN

3. **src/backend/libpq/hba.c:hba_getauthmethod (line 3110)** → **check_hba (lines 2531-2631)** — HBA rule matching and authentication method selection
   - Accepts: `port->user_name` and `port->database_name` from startup packet
   - Performs role lookup via `get_role_oid(port->user_name, true)` (line 2538)
   - Matches HBA rules based on: connection type, IP address, database name, role
   - Assigns `port->hba->auth_method` for use in ClientAuthentication

4. **src/backend/libpq/auth.c:ClientAuthentication (lines 379-670)** — Main authentication dispatcher
   - Accepts: Connection Port structure with user_name, database_name, HBA rule
   - Routes to appropriate authentication method based on `port->hba->auth_method`
   - Methods: uaPassword, uaMD5, uaSCRAM, uaGSS, uaSSPI, uaPeer, uaIdent, uaLDAP, uaRADIUS, uaPAM, uaBSD, uaCert, uaTrust, uaOAuth

5. **src/backend/libpq/auth.c:recv_password_packet (lines 706-776)** — Receives password from client
   - Accepts: Untrusted password message from network
   - Reads message type from `pq_getbyte()` (line 715)
   - Reads password via `pq_getmessage(&buf, PG_MAX_AUTH_TOKEN_LENGTH)` (line 732)
   - Validation: Checks message type is PqMsg_PasswordMessage, validates packet length matches string length, rejects empty passwords
   - **Critical entry point**: Raw client password enters here, not yet validated

6. **src/backend/libpq/auth.c:CheckPasswordAuth (lines 787-817)** — Plaintext password authentication
   - Entry point for `uaPassword` method
   - Calls `recv_password_packet()` to get untrusted client password
   - Calls `get_role_password(port->user_name)` to retrieve stored password hash
   - Calls `plain_crypt_verify()` to verify password

7. **src/backend/libpq/auth.c:CheckPWChallengeAuth (lines 822-880)** — MD5 and SCRAM-SHA-256 challenge-response authentication
   - Entry point for `uaMD5` and `uaSCRAM` methods
   - Calls `get_role_password()` to retrieve stored password
   - Routes to `CheckMD5Auth()` for MD5 or `CheckSASLAuth(&pg_be_scram_mech)` for SCRAM

8. **src/backend/libpq/auth.c:CheckMD5Auth (lines 882-912)** — MD5 challenge-response authentication
   - Generates random salt via `pg_strong_random(md5Salt, 4)` (line 890)
   - Sends salt to client via `sendAuthRequest()` (line 897)
   - Calls `recv_password_packet()` to receive MD5-hashed response (line 899)
   - Calls `md5_crypt_verify()` to verify response

9. **src/backend/libpq/auth-sasl.c:CheckSASLAuth (lines 43-194)** — SASL framework for SCRAM-SHA-256 and other mechanisms
   - Entry point for SASL-based authentication
   - Sends `AUTH_REQ_SASL` with mechanism list to client
   - Receives SASL tokens via `pq_getmessage(&buf, mech->max_message_length)` (line 98)
   - **Critical entry point**: Untrusted SASL tokens from network
   - Calls `mech->init()` to initialize the selected mechanism (line 131)
   - Calls `mech->exchange()` to process SASL tokens (line 157)
   - Continues until SASL exchange succeeds

10. **src/backend/libpq/auth-scram.c:scram_init (lines 239-333)** — SCRAM-SHA-256 mechanism initialization
    - Parses selected SASL mechanism name from untrusted client (line 117: `pq_getmsgrawstring(&buf)`)
    - Validates mechanism is SCRAM-SHA-256 or SCRAM-SHA-256-PLUS (lines 258-267)
    - Parses stored SCRAM secret via `parse_scram_secret()` (lines 278-282)
    - **Security mitigation**: If user doesn't exist, creates mock secret via `mock_scram_secret()` (line 325) to prevent user enumeration
    - Sets `state->doomed = true` to ensure authentication fails without revealing reason (line 329)

## Data Flow

### Flow 1: Plaintext Password Authentication
1. **Source**: `src/backend/tcop/backend_startup.c:ProcessStartupPacket` (lines 746-749) — Untrusted user_name extracted from startup packet
2. **Transform**: `src/backend/libpq/hba.c:check_hba` (line 2538) — Role lookup via `get_role_oid()`, HBA rule matching
3. **Transform**: `src/backend/libpq/auth.c:ClientAuthentication` (line 593) — Routes to `CheckPasswordAuth` based on HBA rule
4. **Source**: `src/backend/libpq/auth.c:recv_password_packet` (line 732) — Untrusted password received from network
5. **Transform**: `src/backend/libpq/crypt.c:get_role_password` (line 47) — Database lookup: `SearchSysCache1(AUTHNAME, PointerGetDatum(role))` retrieves stored password hash from pg_authid
6. **Transform**: `src/backend/libpq/crypt.c:plain_crypt_verify` (lines 255-321) — Password verification
   - For SCRAM-SHA-256: Calls `scram_verify_plain_password()` (line 271)
   - For MD5: Hashes client password with `pg_md5_encrypt()` (line 286), compares with stored hash
7. **Sink**: `src/backend/libpq/auth.c:set_authn_id` (line 814) — Session establishment: Records authenticated identity in `MyClientConnectionInfo.authn_id`

### Flow 2: MD5 Challenge-Response Authentication
1. **Source**: `src/backend/tcop/backend_startup.c:ProcessStartupPacket` — Untrusted user_name from startup packet
2. **Transform**: `src/backend/libpq/hba.c:check_hba` — Role lookup, HBA rule matching
3. **Transform**: `src/backend/libpq/auth.c:ClientAuthentication` (line 589) — Routes to `CheckPWChallengeAuth`
4. **Transform**: `src/backend/libpq/auth.c:CheckPWChallengeAuth` (line 833) — Calls `get_role_password()` database lookup
5. **Transform**: `src/backend/libpq/auth.c:CheckMD5Auth` (line 890) — Generates random salt via `pg_strong_random()`
6. **Transform**: `src/backend/libpq/auth.c:sendAuthRequest` (line 897) — Sends salt to client
7. **Source**: `src/backend/libpq/auth.c:recv_password_packet` (line 899) — Receives untrusted MD5-hashed response from network
8. **Transform**: `src/backend/libpq/crypt.c:md5_crypt_verify` (lines 201-242) — Password verification
   - Verifies password type is MD5 (line 213)
   - Computes expected hash: `pg_md5_encrypt(shadow_pass + 3, md5_salt, 4)` (line 225)
   - Compares client response with expected hash (line 233)
9. **Sink**: `src/backend/libpq/auth.c:set_authn_id` — Session establishment

### Flow 3: SCRAM-SHA-256 Challenge-Response Authentication
1. **Source**: `src/backend/tcop/backend_startup.c:ProcessStartupPacket` — Untrusted user_name from startup packet
2. **Transform**: `src/backend/libpq/hba.c:check_hba` — Role lookup, HBA rule matching
3. **Transform**: `src/backend/libpq/auth.c:ClientAuthentication` (line 589) — Routes to `CheckPWChallengeAuth`
4. **Transform**: `src/backend/libpq/auth.c:CheckPWChallengeAuth` (line 862) — Routes to `CheckSASLAuth(&pg_be_scram_mech)`
5. **Transform**: `src/backend/libpq/auth-sasl.c:CheckSASLAuth` (line 68) — Sends `AUTH_REQ_SASL` with mechanism list
6. **Source**: `src/backend/libpq/auth-sasl.c:CheckSASLAuth` (line 98) — Receives untrusted SASL tokens from network via `pq_getmessage()`
7. **Transform**: `src/backend/libpq/auth-sasl.c:CheckSASLAuth` (line 117) — Parses selected mechanism from untrusted client data via `pq_getmsgrawstring()`
8. **Transform**: `src/backend/libpq/auth-scram.c:scram_init` (line 131) — Initializes SCRAM mechanism
   - Validates selected mechanism is SCRAM-SHA-256 or SCRAM-SHA-256-PLUS (lines 258-267)
   - Database lookup: `get_password_type(shadow_pass)` (line 274)
   - If user exists and has valid SCRAM secret: `parse_scram_secret()` (line 278) extracts iterations, salt, StoredKey, ServerKey from password hash
   - **CRITICAL MITIGATION**: If user doesn't exist or password invalid: `mock_scram_secret()` (line 325) creates fake salt, iterations, StoredKey, ServerKey to prevent user enumeration
9. **Transform**: `src/backend/libpq/auth-sasl.c:CheckSASLAuth` (line 157) — Calls `mech->exchange()` to process SASL tokens (loops until success)
10. **Transform**: `src/backend/libpq/auth-scram.c:scram_exchange` — Processes SCRAM client messages, verifies client proof
    - Parses client final message
    - Verifies channel binding (if SCRAM-SHA-256-PLUS)
    - Computes ClientKey = HMAC(SaltedPassword, "Client Key")
    - Computes ClientSignature = HMAC(StoredKey, ClientAuthMessage)
    - Extracts ClientProof from client message
    - Verifies: ClientKey = ClientProof XOR ClientSignature (constant-time comparison)
11. **Sink**: `src/backend/libpq/auth.c:set_authn_id` — Session establishment

### Flow 4: User Enumeration Prevention (SCRAM and MD5)
1. **Entry**: Client attempts authentication with non-existent user
2. **Transform**: `src/backend/libpq/hba.c:check_hba` (line 2538) — `get_role_oid(port->user_name, true)` returns NULL for non-existent user (missing_ok=true)
3. **Transform**: `src/backend/libpq/auth.c:CheckPWChallengeAuth` (line 833) — `get_role_password()` returns NULL for non-existent user
4. **CRITICAL MITIGATION**:
   - For SCRAM: `src/backend/libpq/auth-scram.c:scram_init` (lines 323-329) — Creates mock secret via `mock_scram_secret()` instead of failing early
   - For MD5: `src/backend/libpq/auth.c:CheckPWChallengeAuth` (line 845) — Uses `Password_encryption` setting to choose mock password type
5. **Transform**: Authentication proceeds with mock credentials
6. **Sink**: Authentication fails identically to incorrect password case, no user enumeration leak

## Dependency Chain

```
Postmaster (raw TCP acceptance)
    ↓
ProcessStartupPacket (startup packet received)
    ├→ Extracts user_name, database_name, application_name [ENTRY POINT 1]
    ├→ Validates packet structure
    └→ Stores in Port structure
        ↓
    ClientAuthentication (main auth dispatcher)
        ├→ hba_getauthmethod
        │   ├→ check_hba [ENTRY POINT 2]
        │   │   ├→ get_role_oid(user_name) [database lookup]
        │   │   ├→ Matches HBA rules
        │   │   └→ Selects auth_method
        │   └→ Returns auth_method
        │
        ├→ Switch on auth_method:
        │
        ├→ uaPassword:
        │   └→ CheckPasswordAuth [ENTRY POINT 3]
        │       ├→ sendAuthRequest(AUTH_REQ_PASSWORD)
        │       ├→ recv_password_packet [ENTRY POINT 4]
        │       ├→ get_role_password(user_name) [database lookup]
        │       ├→ plain_crypt_verify
        │       │   ├→ For SCRAM: scram_verify_plain_password
        │       │   └→ For MD5: pg_md5_encrypt
        │       └→ set_authn_id [session establishment]
        │
        ├→ uaMD5 / uaSCRAM:
        │   └→ CheckPWChallengeAuth
        │       ├→ get_role_password(user_name) [database lookup]
        │       ├→ get_password_type(shadow_pass)
        │       │
        │       ├→ For MD5:
        │       │   └→ CheckMD5Auth
        │       │       ├→ pg_strong_random(salt)
        │       │       ├→ sendAuthRequest(AUTH_REQ_MD5, salt)
        │       │       ├→ recv_password_packet [ENTRY POINT 5]
        │       │       ├→ md5_crypt_verify
        │       │       │   └→ pg_md5_encrypt
        │       │       └→ set_authn_id
        │       │
        │       └→ For SCRAM:
        │           └→ CheckSASLAuth(&pg_be_scram_mech) [ENTRY POINT 6]
        │               ├→ sendAuthRequest(AUTH_REQ_SASL, mechanism_list)
        │               ├→ Loop SASL exchange:
        │               │   ├→ recv SASLResponse [ENTRY POINT 7]
        │               │   ├→ scram_init [ENTRY POINT 8]
        │               │   │   ├→ Parse selected_mech from client [ENTRY POINT 9]
        │               │   │   ├→ get_password_type(shadow_pass)
        │               │   │   ├→ If valid: parse_scram_secret
        │               │   │   │   └→ Extracts iterations, salt, StoredKey, ServerKey
        │               │   │   └→ If invalid: mock_scram_secret [MITIGATION]
        │               │   │       └→ Sets doomed=true
        │               │   └→ scram_exchange
        │               │       ├→ Parse client message
        │               │       ├→ Verify channel binding
        │               │       ├→ Compute ClientSignature = HMAC(StoredKey, ClientAuthMessage)
        │               │       ├→ Verify ClientProof (constant-time comparison)
        │               │       └→ Generate server proof
        │               └→ set_authn_id [session establishment]
        │
        └→ Other methods (GSS, SSPI, Peer, Ident, LDAP, RADIUS, PAM, BSD, OAuth)
```

## Analysis

### 1. Authentication Architecture

PostgreSQL implements a modular authentication system where the authentication method is determined by the pg_hba.conf configuration file matching against the client's IP address, port, database, and user. The authentication pipeline has multiple entry points where untrusted client data enters:

1. **Startup packet parsing**: User name, database name, application name
2. **Password reception**: Plaintext password for `password` method
3. **Challenge response**: MD5-hashed password for `md5` method
4. **SASL/SCRAM tokens**: Binary SASL protocol messages for `scram-sha-256` method

Each entry point has different validation and processing:
- **Startup packet**: Validated for length and structure, names truncated to NAMEDATALEN
- **Plaintext password**: No structural validation (arbitrary string)
- **MD5 response**: Expected to be MD5 hash (32 hex chars)
- **SCRAM tokens**: Binary SASL protocol with format validation in SCRAM implementation

### 2. Role Validation

The role lookup happens via `get_role_oid(port->user_name, true)` in `check_hba()` with `missing_ok=true`. This is critical because:

1. It allows the user_name to be validated against the pg_authid catalog
2. However, the `missing_ok=true` flag means **non-existent users do not cause immediate failure**
3. This is intentional to support user enumeration prevention through dummy authentication

The security model relies on never revealing whether a user exists or whether a password is correct for a non-existent user.

### 3. Password Verification Mechanisms

#### Plaintext Authentication (uaPassword)
- **Flow**: Client sends password in plaintext → recv_password_packet → plain_crypt_verify
- **Verification**:
  - For SCRAM-SHA-256 passwords: Client password is hashed using stored salt and iterations, compared with StoredKey
  - For MD5 passwords: Client password is hashed with user name, compared with stored hash
- **Risk**: Password sent in plaintext over network (only safe if SSL/TLS encrypted)

#### MD5 Challenge-Response (uaMD5)
- **Flow**: Server sends random salt → Client responds with MD5(MD5(password + username) + salt) → md5_crypt_verify
- **Verification**: Server computes same hash and compares
- **Advantage**: Password not sent in plaintext (but salt is public)
- **Disadvantage**: MD5 is cryptographically weak; vulnerability in 1-iteration MD5

#### SCRAM-SHA-256 Challenge-Response (uaSCRAM)
- **Flow**: Multi-message SASL exchange with HMAC-SHA-256 based proof
- **Verification**:
  - Server sends iterations, salt, ServerSignature
  - Client computes SaltedPassword = PBKDF2-SHA-256(password, salt, iterations)
  - Client sends ClientProof = ClientKey XOR ClientSignature
  - Server verifies ClientProof using stored ClientKey
- **Advantages**:
  - Password not exposed (uses key derivation)
  - Salted and iterated hashing (PBKDF2)
  - Two-way authentication (server provides ServerSignature)
  - Channel binding support (SCRAM-SHA-256-PLUS)

### 4. User Enumeration Prevention

PostgreSQL implements "dummy authentication" to prevent user enumeration attacks:

**SCRAM Implementation** (auth-scram.c:scram_init lines 323-329):
```c
if (!got_secret) {
    mock_scram_secret(state->port->user_name, &state->hash_type,
                      &state->iterations, &state->key_length,
                      &state->salt,
                      state->StoredKey, state->ServerKey);
    state->doomed = true;
}
```

**MD5/SCRAM Selection** (auth.c:CheckPWChallengeAuth lines 844-845):
```c
if (!shadow_pass)
    pwtype = Password_encryption;  // Use configured default
else
    pwtype = get_password_type(shadow_pass);
```

**Effect**:
- Authentication always proceeds with valid-looking (but incorrect) credentials
- Authentication fails identically for non-existent users and wrong passwords
- No timing differences reveal user existence
- An attacker cannot enumerate valid usernames

### 5. HBA Rule Matching

The HBA matching pipeline (hba.c:check_hba):

1. **Connection type matching**: Check if connection is local (Unix socket), host, hostssl, or hostnossl
2. **IP address matching**: If remote, verify client IP matches HBA rule's address/netmask using check_ip()
3. **Hostname matching**: Optional reverse DNS lookup and hostname matching
4. **Database matching**: Check if client's requested database matches HBA rule (or wildcard)
5. **Role matching**: Check if authenticated role matches HBA rule (or wildcard)
6. **First match wins**: Rules are processed in order; first match determines auth method

**Security properties**:
- Rules are configuration-based and static (loaded at startup or via SIGHUP reload)
- Rules are evaluated in file order, allowing defaults and overrides
- Implicit reject if no rule matches (uaImplicitReject)
- Explicit reject allows security rules to be clear

### 6. Data Validation at Entry Points

#### Startup Packet (ProcessStartupPacket)
- **Validation**: Length check (536 <= len <= MAX_STARTUP_PACKET_LENGTH), protocol version validation
- **Truncation**: User name and database name truncated to NAMEDATALEN (63 bytes)
- **Application name**: Cleaned via `pg_clean_ascii()` to prevent log injection
- **GUC options**: Stored for later processing but not yet validated

#### Password Packet (recv_password_packet)
- **Validation**: Message type check, packet length validation, empty password rejection
- **No encoding validation**: Passwords are treated as raw bytes (encoding determined later)
- **Length limit**: PG_MAX_AUTH_TOKEN_LENGTH (typically 1GB or large value)

#### SASL Tokens (CheckSASLAuth)
- **Length limit**: mech->max_message_length (SCRAM uses 262144 bytes)
- **Format validation**: Delegated to SASL mechanism implementation

### 7. Vulnerability Classes and Mitigations

#### User Enumeration (Timing-Based)
- **Attack**: Measure response time differences to infer user existence
- **Mitigation**: Dummy authentication - invalid users always proceed through full authentication exchange with mock credentials
- **Residual risk**: SCRAM iteration count and salt generation timing could leak user existence with extreme precision
- **Impact**: Network timing is dominated by random variation; differential timing < 1ms is hard to exploit

#### User Enumeration (Information Leakage)
- **Attack**: Inspect error messages to determine if user exists
- **Mitigation**: Error messages don't differentiate between "user doesn't exist" and "wrong password"
- **Implementation**: Errors logged to server log (not sent to client) via logdetail parameter

#### Password Exposure in Transit
- **Attack**: Plaintext password captured on network
- **Mitigation**: SSL/TLS encryption required (uaPassword method highly discouraged without SSL)
- **Better alternatives**: SCRAM-SHA-256 (challenge-response, password never sent)

#### Dictionary Attacks / Brute Force
- **Attack**: Attacker tries many passwords
- **Mitigation**: SCRAM-SHA-256 uses PBKDF2 with iteration count (server-side rate limiting not implemented)
- **Residual risk**: PostgreSQL doesn't implement connection rate limiting or attempt counting at authentication stage
- **Recommended**: Configure firewall/proxy to rate-limit authentication attempts

#### MITM Attack (Password Exposure)
- **Attack**: Attacker intercepts MD5 challenge-response exchange
- **Risk**: MD5 is weak; reversing password from hash may be feasible for weak passwords
- **Mitigation**: SCRAM-SHA-256 uses salted PBKDF2 (iteration count × password strength required)
- **Better mitigation**: Enforce SSL/TLS for all connections

#### Channel Binding (TLS Hijacking)
- **Attack**: Attacker hijacks TLS session after authentication
- **Mitigation**: SCRAM-SHA-256-PLUS includes channel binding (tls-server-end-point)
- **Implementation**: Binds SCRAM authentication to TLS certificate (prevents MitM)
- **Requirement**: Must use SCRAM-SHA-256-PLUS variant (not default)

#### Role Privilege Escalation
- **Attack**: Authenticated user tries to access another role's data/privileges
- **Mitigation**: Session role is set to authenticated user (set_authn_id); authorization checks use this role
- **Scope**: Authentication only verifies user identity; authorization is separate (GRANT/REVOKE)

### 8. Existing Mitigations Summary

| Vulnerability | Mitigation | Strength |
|---|---|---|
| User enumeration | Dummy authentication (SCRAM, MD5) | Strong |
| Password in transit | SSL/TLS encryption + SCRAM | Strong if TLS enforced |
| Weak password hashing | PBKDF2 + salt + iterations (SCRAM) | Strong |
| MD5 weakness | Deprecated but still supported | Weak (legacy) |
| Plaintext password method | Deprecated but configurable | Weak (legacy) |
| MITM / channel hijacking | SCRAM-SHA-256-PLUS + channel binding | Strong if PLUS variant used |
| Timing attacks | Constant-time HMAC comparison | Strong (implementation detail) |
| Log injection via password | Passwords not logged | Strong |
| Log injection via application_name | Sanitized with pg_clean_ascii() | Strong |
| Invalid SCRAM secret | Graceful fallback to dummy | Strong |
| User doesn't exist | Dummy authentication (no error) | Strong |

### 9. Attack Scenarios

#### Scenario 1: User Enumeration Attack
**Attacker goal**: Determine valid usernames

**Attack attempt**:
1. Connect to PostgreSQL with user "admin"
2. Send random password
3. Check if error message differs from connecting with "nonexistent_user"

**Defense**:
- Error messages don't differentiate: both receive "authentication failed"
- Authentication always proceeds with valid-looking (but incorrect) credentials
- Timing is identical (within network variation)
- **Result**: Attack fails; attacker cannot enumerate users

#### Scenario 2: Brute Force Password Attack
**Attacker goal**: Guess password for known user

**Attack attempt**:
1. Connect with user "postgres"
2. Try 10,000 passwords rapidly

**Defense**:
- PostgreSQL doesn't implement built-in rate limiting
- Each password attempt requires full SCRAM exchange (computational cost on server)
- SCRAM uses PBKDF2 with ~4096 iterations (default)
- Network latency dominates
- **Recommended mitigation**: Firewall/proxy implements rate limiting, fail2ban, or PgBouncer

#### Scenario 3: MITM Password Hijacking
**Attacker goal**: Capture password for offline cracking

**Attack attempt**:
1. Position MITM between client and server
2. Intercept authentication exchange

**Defense**:
- SCRAM-SHA-256: Password not transmitted; hash of password transmitted
- SCRAM-SHA-256-PLUS: Binds to TLS certificate; MITM causes different channel binding value
- **If SSL/TLS not enforced**: Plaintext MD5 challenge-response vulnerable
- **Recommended mitigation**: Require SSL/TLS for all connections (force_ssl=on)

#### Scenario 4: Timing-Based User Enumeration
**Attacker goal**: Detect user existence via response timing

**Attack attempt**:
1. Measure response time for "user doesn't exist" case
2. Measure response time for "wrong password" case
3. Correlate timing differences

**Defense**:
- Dummy authentication ensures both paths take similar time
- SCRAM iteration count is fixed per password type
- Salt generation (random) occurs regardless
- **Residual risk**: Iteration count could theoretically leak user existence with statistical analysis over many attempts
- **Mitigation effectiveness**: Network jitter (~10ms) overwhelms auth timing differences (~0.1ms)

#### Scenario 5: HBA Rule Bypass
**Attacker goal**: Bypass HBA rules by spoofing IP address

**Attack attempt**:
1. Attempt connection from different IP address
2. Claim to be from trusted network

**Defense**:
- HBA matching occurs after TCP connection is established
- Client's real IP (from socket) is used; client cannot claim different IP
- Source IP verification is provided by OS-level networking
- **Additional defense**: Firewall can enforce network segmentation

#### Scenario 6: SASL Mechanism Downgrade
**Attacker goal**: Force downgrade to weaker SCRAM-SHA-256 variant without channel binding

**Attack attempt**:
1. Advertise both SCRAM-SHA-256 and SCRAM-SHA-256-PLUS
2. Client selects SCRAM-SHA-256 (no channel binding)
3. Continue with weaker authentication

**Defense**:
- Server advertises only mechanisms supported for the connection
- If SSL/TLS in use: Server advertises SCRAM-SHA-256-PLUS
- If no SSL/TLS: Server advertises SCRAM-SHA-256 (no channel binding possible)
- Client cannot select mechanism that server didn't advertise
- **Mitigations**:
  - Use SSL/TLS for all connections
  - Require SCRAM-SHA-256-PLUS if possible

### 10. Gaps and Recommendations

#### Gap 1: No Built-in Rate Limiting
- **Current**: PostgreSQL has no per-user or per-IP authentication attempt limit
- **Recommendation**:
  - Use PgBouncer connection pooling with built-in rate limiting
  - Deploy fail2ban or similar on host
  - Implement firewall rules (ip_based_gatekeeper, iptables, cloud WAF)

#### Gap 2: Legacy Authentication Methods
- **Current**: `password` (plaintext) and `md5` methods still supported
- **Risk**: Weak protection if SSL/TLS not enforced
- **Recommendation**:
  - Upgrade to SCRAM-SHA-256 for all roles
  - Disable uaPassword and uaMD5 methods in pg_hba.conf
  - Set password_encryption = scram-sha-256 globally

#### Gap 3: SCRAM-SHA-256-PLUS Adoption
- **Current**: PLUS variant (channel binding) available but not required
- **Risk**: Vulnerable to MITM if only SCRAM-SHA-256 is used
- **Recommendation**:
  - Require SSL/TLS for all connections (ssl=on in postgresql.conf)
  - Prefer SCRAM-SHA-256-PLUS when available
  - Monitor server logs for PLUS variant usage

#### Gap 4: User Enumeration via Indirect Channels
- **Current**: Direct authentication reveals no user info, but other channels might
- **Risk**: Database schema queries, role listing, replication slot names can reveal roles
- **Recommendation**:
  - Restrict access to system catalogs for unauthenticated connections
  - Use views to hide sensitive role information
  - Monitor unusual query patterns for probing

#### Gap 5: No Cryptographic Hardware Acceleration for PBKDF2
- **Current**: PBKDF2 computation is CPU-bound
- **Risk**: Slow brute-force attacks remain slow (not an exploit, but defense could be stronger)
- **Recommendation**:
  - Increase iteration count for SCRAM-SHA-256 (if acceptable for performance)
  - Use HSM or dedicated crypto accelerator if available
  - Monitor SCRAM authentication latency

#### Gap 6: Application Name Injection Prevention Only
- **Current**: Only application_name is sanitized; user_name and database_name are not
- **Risk**: Multiline log entries could be injected if parsed unsafely
- **Recommendation**:
  - Server logs application_name (sanitized) but logs are trusted source
  - No identified vulnerability; mitigation is already in place

## Summary

PostgreSQL's client authentication pipeline is well-designed with multiple security layers:

1. **Entry points** are clearly defined and validated:
   - Startup packet: Length and structure validation
   - Password/SASL tokens: Delegated to authentication method
   - HBA matching: Configuration-based, not client input

2. **Data flow** is clear and controlled:
   - Untrusted input → Database lookup → Verification → Session establishment
   - Password never stored in plaintext
   - Passwords compared via cryptographic hashes

3. **User enumeration** is prevented via dummy authentication:
   - Non-existent users proceed through full authentication exchange
   - Identical failure modes for missing users and wrong passwords
   - Timing differences minimized

4. **Password verification** uses strong cryptography:
   - SCRAM-SHA-256: PBKDF2-SHA-256 with salt and iterations
   - MD5: Weak but salted challenge-response (deprecated)
   - Plaintext: Only safe over SSL/TLS

5. **Security architecture** is modular:
   - Multiple authentication methods selectable per HBA rule
   - Methods are isolated and cannot interfere
   - Fallback to implicit reject if no rule matches

**Key vulnerabilities to monitor**:
- Insufficient rate limiting (external mitigation required)
- Legacy authentication methods (must be disabled manually)
- MITM exposure without SSL/TLS (must be enforced)
- User enumeration via indirect channels (schema introspection)

**Recommended deployment**:
1. Enforce SSL/TLS for all connections
2. Migrate all users to SCRAM-SHA-256 passwords
3. Disable `password` and `md5` authentication methods
4. Implement firewall-level rate limiting
5. Monitor authentication logs for anomalous patterns
6. Use PgBouncer or similar for connection pooling and additional security controls
