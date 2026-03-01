# PostgreSQL Client Authentication Pipeline Security Analysis

## Files Examined

The following files comprise the authentication data flow from TCP connection acceptance through session establishment:

### Connection Acceptance & Startup Packet Processing
- **src/backend/tcop/backend_startup.c** — Accepts TCP connections, processes startup packet, parses client-supplied username/database
- **src/backend/libpq/pqcomm.c** — Network communication primitives (pq_getbytes, pq_getmessage)
- **src/backend/libpq/pqformat.c** — Message parsing utilities (pq_getmsgstring, pq_getmsgint)

### HBA Configuration Matching
- **src/backend/libpq/hba.c** — Host-Based Authentication rule matching, configuration parsing, database/role validation
- **src/include/libpq/hba.h** — HBA data structures and function declarations

### Authentication Dispatch & Password Verification
- **src/backend/libpq/auth.c** — Main authentication dispatcher (ClientAuthentication), password handlers (CheckPasswordAuth, CheckPWChallengeAuth), password packet reception
- **src/backend/libpq/crypt.c** — Password lookup from pg_authid catalog (get_role_password), password type detection

### SASL/SCRAM Implementation
- **src/backend/libpq/auth-sasl.c** — SASL framework that orchestrates message exchange with client
- **src/backend/libpq/auth-scram.c** — SCRAM-SHA-256 mechanism implementation with client proof verification

### Session Initialization
- **src/backend/utils/init/postinit.c** — Backend initialization, calls ClientAuthentication in context of transaction setup
- **src/backend/utils/init/miscinit.c** — Miscellaneous initialization (possibly role context)

### Related Infrastructure
- **src/backend/postmaster/postmaster.c** — Postmaster process that spawns backend processes
- **src/backend/libpq/be-secure.c** — SSL/TLS encryption (establishes secure channel before authentication)
- **src/include/libpq/libpq-be.h** — Backend-side protocol definitions and Port structure

---

## Entry Points

Entry points are functions that accept untrusted client data:

### 1. TCP Connection Acceptance & Startup Packet Reception
**File**: `src/backend/tcop/backend_startup.c:492` (`ProcessStartupPacket`)
- **Input**: Raw TCP stream from untrusted client
- **Data received**:
  - Protocol version (4 bytes, network byte order)
  - Parameter pairs: "user"→username, "database"→database_name, "options"→cmdline_options, etc.
  - All as null-terminated strings within a packet
- **Untrusted data types**: Username, database name, options, application name
- **No validation at this point**: Packet is checked for length bounds but parameter values are accepted as-is

### 2. Password Packet Reception (Plaintext Auth)
**File**: `src/backend/libpq/auth.c:707` (`recv_password_packet`)
- **Input**: PqMsg_PasswordMessage from untrusted client
- **Data received**: Plaintext password as null-terminated string
- **Validation**: Length check (strlen + 1 == buf.len), non-empty check, max length (PG_MAX_AUTH_TOKEN_LENGTH)
- **No character validation**: Password bytes are accepted as-is for MD5/SCRAM processing

### 3. SASL/SCRAM Token Reception
**File**: `src/backend/libpq/auth-sasl.c:78-145` (`CheckSASLAuth`)
- **Input**: PqMsg_SASLResponse messages containing:
  - Initial: Selected mechanism name (string) + optional client response (length-prefixed bytes)
  - Subsequent: Raw SASL payload (length-prefixed bytes)
- **Data validation**: Message length checked (mech->max_message_length)
- **Untrusted processing**: Mechanism name from client used to select SCRAM implementation

### 4. MD5/Challenge Auth Challenge Response
**File**: `src/backend/libpq/auth.c:897-899` (within `CheckMD5Auth`)
- **Input**: MD5 password response from client after salt challenge
- **Passed through**: `recv_password_packet()` same as plaintext auth

---

## Data Flow

### Flow 1: TCP Connection → HBA Rule Matching → Password Lookup

```
Entry Point: TCP Accept
    ↓
Backend spawned by postmaster
    ↓
BackendInitialize() [backend_startup.c]
    ↓
ProcessStartupPacket() [backend_startup.c:492]
    │   - pq_getbytes() receives raw packet
    │   - Packet length validated (>= sizeof(ProtocolVersion), <= MAX_STARTUP_PACKET_LENGTH)
    │   - Null terminator added to ensure safe string parsing
    │   - Loops through parameter pairs: nameptr, valptr
    │   - UNTRUSTED DATA ENTRY: port->user_name = pstrdup(valptr) [line 749]
    │   - UNTRUSTED DATA ENTRY: port->database_name = pstrdup(valptr) [line 747]
    │   - Truncates to NAMEDATALEN (63 chars) [line 842-843]
    ↓
postinit.c:253: InitPostgresPhase1/2/3
    │   (Sets up transaction, catalog access)
    ↓
ClientAuthentication(port) [auth.c:379]
    │
    ├─→ hba_getauthmethod(port) [auth.c:390]
    │       │
    │       └─→ check_hba(port) [hba.c:3112]
    │           │   - get_role_oid(port->user_name, true) [hba.c:2538]
    │           │     (Returns OID or InvalidOid, doesn't error if user doesn't exist)
    │           │
    │           │   Loop through parsed_hba_lines:
    │           │   - Check connection type (local/TCP/SSL/GSS)
    │           │   - Check IP address (mask, hostname, same_host, same_net)
    │           │   - Check database name: check_db(port->database_name, ...) [hba.c:2615]
    │           │   - Check role: check_role(port->user_name, ...) [hba.c:2619]
    │           │     (Supports +groupname syntax)
    │           │   - On match: Set port->hba = matched_rule, return
    │           │   - On no match: Create uaImplicitReject rule
    │
    └─→ Switch on port->hba->auth_method [auth.c:422]

Data Flow Summary:
- client packet → port->user_name, port->database_name (strings)
- These are passed to catalog lookups without intermediate validation
- Database/username used to match HBA rules
- After HBA match, authentication method is determined
```

### Flow 2: Password-Based Authentication (Plaintext & MD5)

```
ClientAuthentication() → uaPassword case [auth.c:592]
    ↓
CheckPasswordAuth(port, &logdetail) [auth.c:788]
    │
    ├─→ sendAuthRequest(port, AUTH_REQ_PASSWORD, NULL, 0)
    │   (Tells client to send plaintext password)
    │
    ├─→ recv_password_packet(port) [auth.c:796]
    │   - pq_getbyte() reads message type (expecting PqMsg_PasswordMessage='p')
    │   - pq_getmessage(&buf, PG_MAX_AUTH_TOKEN_LENGTH) reads message body
    │   - Validates: strlen(buf.data) + 1 == buf.len (no embedded nulls)
    │   - Validates: buf.len != 1 (not empty password)
    │   - Returns buf.data (plaintext password)
    │   - UNTRUSTED DATA: Client-supplied plaintext password
    │
    ├─→ get_role_password(port->user_name, logdetail) [auth.c:800]
    │   [TRANSFORM: Database lookup]
    │   - SearchSysCache1(AUTHNAME, PointerGetDatum(port->user_name))
    │     (Uses untrusted username to look up pg_authid)
    │   - If tuple found: Extract rolpassword attribute (the hash)
    │   - If not found: Return NULL, set logdetail
    │   - If expired (rolvaliduntil < now): Return NULL
    │   - Returns: shadow_pass (MD5 hash or SCRAM secret from database)
    │   - SECURITY NOTE: Password lookup ALWAYS happens, even if user doesn't exist
    │     (Mitigates timing attacks by doing same work either way)
    │
    ├─→ plain_crypt_verify(port->user_name, shadow_pass, passwd, logdetail) [auth.c:803]
    │   [SENSITIVE OPERATION: Password comparison]
    │   - Compares plaintext client password against stored hash
    │   - Returns STATUS_OK if match, STATUS_ERROR if not
    │
    └─→ set_authn_id(port, port->user_name) on success [auth.c:814]
        (Logs successful authentication)

Plaintext Auth Summary:
Entry: client plaintext password
Transform: Stored password hash from pg_authid via untrusted username
Sink: Cryptographic comparison (plain_crypt_verify)
Risk: Password transmitted in plaintext over network (mitigated by SSL/TLS requirement)
```

### Flow 3: MD5 Challenge-Response Authentication

```
ClientAuthentication() → uaMD5 case [auth.c:587-590]
    ↓
CheckPWChallengeAuth(port, &logdetail) [auth.c:823]
    │
    ├─→ get_role_password(port->user_name, logdetail) [auth.c:833]
    │   (Same as plaintext: catalog lookup via untrusted username)
    │
    ├─→ get_password_type(shadow_pass) [auth.c:847]
    │   - Detects if password is MD5 hash or SCRAM secret
    │   - For MD5: Verifies "md5" prefix + length 32 + valid hex chars
    │
    ├─→ CheckMD5Auth(port, shadow_pass, logdetail) [auth.c:860] (if MD5 password)
    │   - pg_strong_random(md5Salt, 4) generates 4-byte salt
    │   - sendAuthRequest(port, AUTH_REQ_MD5, md5Salt, 4)
    │     (Sends salt to client)
    │   - recv_password_packet(port) [auth.c:899]
    │     (Receives MD5(MD5(password + username) + salt) from client)
    │     (UNTRUSTED DATA: Client-supplied response)
    │   - md5_crypt_verify(port->user_name, shadow_pass, passwd, md5Salt, 4)
    │     [SENSITIVE OPERATION: Challenge response verification]
    │     - Hashes stored password hash with salt
    │     - Compares with client response
    │     - Returns STATUS_OK/ERROR
    │
    └─→ Return auth result

MD5 Challenge Summary:
Entry: Client response (network-based, not plaintext password)
Transform: Stored password hash from database, salt generated by server
Sink: Cryptographic comparison (md5_crypt_verify)
Vulnerability: MD5 is deprecated; vulnerable to timing attacks in comparison
Mitigation: Used only if password stored as MD5 (legacy)
```

### Flow 4: SCRAM-SHA-256 Authentication

```
ClientAuthentication() → uaSCRAM case [auth.c:588-590]
    ↓
CheckPWChallengeAuth(port, &logdetail) [auth.c:823]
    │
    ├─→ get_role_password(port->user_name, logdetail) [auth.c:833]
    │   (Catalog lookup via untrusted username)
    │   (Returns SCRAM secret: "SCRAM-SHA-256$iterations:salt$stored_key:server_key")
    │
    └─→ CheckSASLAuth(&pg_be_scram_mech, port, shadow_pass, logdetail) [auth.c:862]
        │
        ├─→ mech->get_mechanisms(port, &sasl_mechs)
        │   (Advertises SCRAM-SHA-256)
        │
        ├─→ sendAuthRequest(port, AUTH_REQ_SASL, sasl_mechs, len)
        │   (Sends list of mechanisms to client)
        │
        └─→ Loop through SASL message exchange [auth-sasl.c:78-185]:
            │
            ├─ Iteration 1: Initial Response
            │  ├─→ pq_getbyte() reads PqMsg_SASLResponse ('p')
            │  ├─→ pq_getmessage(&buf, mech->max_message_length)
            │  │   (UNTRUSTED DATA: SASL initial response)
            │  ├─→ selected_mech = pq_getmsgrawstring(&buf)
            │  │   (UNTRUSTED DATA: Client-selected mechanism name)
            │  ├─→ mech->init(port, selected_mech, shadow_pass)
            │  │   (Initializes SCRAM state machine)
            │  │   [scram_init in auth-scram.c]
            │  │
            │  │   scram_init() [auth-scram.c]:
            │  │   - Parses stored password: parse_scram_secret()
            │  │   - Extracts: iterations, hash_type, key_length, encoded_salt,
            │  │     stored_key, server_key
            │  │   - If user doesn't exist or password invalid:
            │  │     Creates fake salt/iterations (mock authentication)
            │  │     Sets doomed=true (auth will fail, but timing same)
            │  │   - Initializes ClientKey, ClientSignature, ServerSignature
            │  │   - Returns opaque state struct
            │  │
            │  ├─→ inputlen = pq_getmsgint(&buf, 4)
            │  ├─→ input = pq_getmsgbytes(&buf, inputlen)
            │  │   (UNTRUSTED DATA: Initial client response)
            │  │   (Contains: channel-binding-flag, authzid, client-first-message)
            │  │
            │  └─→ mech->exchange(opaq, input, inputlen, &output, ...)
            │      (Calls scram_exchange to process client message)
            │
            ├─ scram_exchange() processes SASLprep, channel binding, nonce
            │  │
            │  ├─→ Verifies nonce from client matches server nonce
            │  ├─→ Processes channel-binding-data (if using TLS)
            │  ├─→ Extracts username from client first message (usually empty)
            │  ├─→ Verifies username matches authenticated user (if provided)
            │  │
            │  └─→ Computes:
            │      - SaltedPassword = PBKDF2(password, salt, iterations, hash_length)
            │      - ClientKey = HMAC(SaltedPassword, "Client Key")
            │      - StoredKey = H(ClientKey)
            │      - ClientSignature = HMAC(StoredKey, auth-message)
            │      - ClientProof = ClientKey XOR ClientSignature
            │      - ServerSignature = HMAC(ServerKey, auth-message)
            │
            ├─ Iteration 2: Client Final Message
            │  ├─→ Receives channel-binding-input and client-proof
            │  │   (UNTRUSTED DATA: Proof from client)
            │  ├─→ Verifies ClientProof = received_proof
            │  │   [SENSITIVE OPERATION: Cryptographic verification]
            │  │   - Extracts ClientKey = ClientProof XOR ClientSignature
            │  │   - Hashes: H(ClientKey) and compares with StoredKey
            │  │   - If matches: AUTH SUCCESS
            │  │   - If not: AUTH FAILURE
            │  │
            │  └─→ Returns ServerSignature to client
            │      (In AUTH_REQ_SASL_FIN or AUTH_REQ_SASL_CONT)
            │
            └─ Client verifies ServerSignature
               (Client-side verification, not shown here)

SCRAM-SHA-256 Summary:
Entry 1: Client mechanism selection (untrusted string)
Entry 2: SCRAM initial response and proof (untrusted bytes)
Transform: Password parsing (parse_scram_secret), PBKDF2, HMAC-SHA256, SASLprep
Sink: ClientProof verification via HMAC comparison
Security: Strongest authentication method; password never transmitted; immune to MITM
Mitigations:
  - Iterative hashing (PBKDF2) resists brute force
  - Channel binding prevents certain MITM attacks
  - Mock authentication for non-existent users (timing attack prevention)
```

---

## Dependency Chain

The authentication pipeline follows this dependency order:

1. **Network I/O Layer**
   - `src/backend/libpq/pqcomm.c` — Low-level socket read/write
   - `src/backend/libpq/pqformat.c` — Message framing, type-safe parsing
   - `src/backend/libpq/be-secure.c` — TLS encryption (establishes secure channel)

2. **Startup Packet Processing**
   - `src/backend/tcop/backend_startup.c` — Receives startup packet
   - Calls ProcessStartupPacket → parses username/database
   - Populates Port struct with client metadata

3. **Catalog Access Initialization** (in postinit.c)
   - Opens database and system catalogs
   - Enables cache lookups (SearchSysCache1)

4. **HBA Rule Matching**
   - `src/backend/libpq/hba.c` (check_hba)
   - Uses client IP, database name, username to select auth method
   - Depends on: Port struct (from startup), parsed_hba_lines (from load_hba)

5. **Authentication Dispatch**
   - `src/backend/libpq/auth.c` (ClientAuthentication)
   - Routes to appropriate auth handler based on HBA auth_method

6. **Password-Based Authentication Chain**
   ```
   Plaintext: recv_password_packet → get_role_password
              → plain_crypt_verify

   MD5:       recv_password_packet → get_role_password
              → CheckMD5Auth → md5_crypt_verify

   SCRAM:     CheckSASLAuth → CheckSASLAuth → scram_init
              → scram_exchange (iterative HMAC verification)
   ```

7. **Cryptographic Operations**
   - `src/backend/libpq/crypt.c` — Password hash handling
   - `src/backend/libpq/auth-scram.c` — SCRAM implementation
   - Crypto libraries: HMAC-SHA256, SHA256, MD5, PBKDF2

8. **Session Establishment**
   - `src/backend/utils/init/postinit.c` — Final backend initialization
   - Sets authenticated user context
   - Prepares connection for query processing

---

## Analysis

### Authentication Architecture

PostgreSQL uses a three-stage authentication model:

1. **Stage 1: Connection Acceptance & HBA Matching**
   - Postmaster spawns backend for each TCP connection
   - Backend reads startup packet containing username and database
   - HBA rules matched against: connection type, IP, database, username
   - Auth method determined (trust, password, md5, scram, gss, ldap, pam, etc.)
   - This stage has NO cryptographic verification; only config-based routing

2. **Stage 2: Method-Specific Authentication**
   - **Trust**: No password required (if HBA says so)
   - **Password**: Client sends plaintext → compared against stored hash
   - **MD5**: Server sends salt → client hashes password+salt → server verifies
   - **SCRAM-SHA-256**: Multi-round challenge-response with cryptographic proof
   - **GSS/SSPI/LDAP/PAM**: Delegated to external systems

3. **Stage 3: Session Initialization**
   - After authentication success, authenticated user context set
   - Backend connects to requested database
   - Transaction processing begins

### Attack Surface & Entry Points

**Untrusted Data Entry Points:**

1. **StartupPacket (backend_startup.c:499-550)**
   - Network source: Untrusted client
   - Data: username, database_name, options, application_name
   - Length: username/database capped at NAMEDATALEN (63 bytes)
   - Validation: Packet length checked, null termination added
   - Risk: SQL injection in database/username? → **NO**, only used for catalog lookups in syscache

2. **Password Packet (auth.c:707-775)**
   - Network source: Untrusted client
   - Data: Plaintext password (only for plaintext & MD5 challenge response methods)
   - Validation:
     - Length checked (strlen + 1 == message length)
     - Non-empty check
     - Max length (PG_MAX_AUTH_TOKEN_LENGTH = 16KB)
   - Risk: Buffer overflow? → **NO**, bounded read; memory allocated by StringInfo
   - Risk: Plaintext password sniffing? → Mitigated by SSL/TLS requirement

3. **SASL Tokens (auth-sasl.c:78-145)**
   - Network source: Untrusted client
   - Data: Mechanism name (initial), SASL response bytes
   - Validation: Message length checked (max_message_length per mechanism)
   - Risk: Mechanism name injection? → Limited (matched against hardcoded list)
   - Risk: SASL parsing bugs? → Possible in SCRAM implementation

4. **Catalog Lookups (crypt.c:38-84)**
   - Parameter: role name (from untrusted startup packet)
   - Operation: SearchSysCache1(AUTHNAME, PointerGetDatum(role))
   - Risk: Username used as cache key; if not validated, could match wrong user
   - Mitigation: Username verified against startup packet; no case folding issues documented

### Security Properties

**Strengths:**

1. **Timing Attack Resistance (SCRAM)**
   - Mock authentication for non-existent users
   - Same computational work regardless of user existence
   - Prevents username enumeration via timing side-channels

2. **Password Never Transmitted (SCRAM & MD5)**
   - SCRAM: Client never sends plaintext; only cryptographic proof
   - MD5: Client sends hash (not plaintext password)
   - Plaintext: Only when explicitly configured (legacy)

3. **Cryptographic Verification**
   - SCRAM: HMAC-SHA256 with 4096+ iterations (PBKDF2)
   - MD5: Single MD5(MD5(password+user)+salt) (deprecated)
   - Plaintext: byte-wise comparison (no hashing, highest risk)

4. **HBA-Based Authorization**
   - IP-based access control before authentication
   - Database/role-based filtering
   - Can reject connections before password verification

5. **Channel Binding (SCRAM with TLS)**
   - Prevents connection hijacking via MITM
   - Verifies client is on same TLS connection as server
   - Protects against credential disclosure on compromised network

6. **Configuration-Driven Security**
   - pg_hba.conf allows fine-grained access control
   - Can require SSL for certain connections
   - Can use external auth (LDAP, GSS)
   - Can enforce strong auth methods (reject MD5)

**Weaknesses & Vulnerabilities:**

1. **Username Field Not Validated (CWE-601: URL Redirection)**
   - Username from startup packet used directly in:
     - Catalog lookups: SearchSysCache1(AUTHNAME, ...)
     - Log messages: errmsg(...user \"%s\"...)
   - If username contains special chars/nulls, could affect:
     - Log parsing (if unescaped)
     - Error messages displayed to client
   - **Mitigation Present**: Username truncated to NAMEDATALEN; treated as opaque key

2. **Case Folding in Username Comparison**
   - Startup packet username compared against HBA role list (case-sensitive by default)
   - PostgreSQL treats role names as case-insensitive internally
   - Could allow "admin" and "ADMIN" to match different HBA rules
   - **Known behavior**: Case-folding applied consistently in catalog

3. **MD5 Authentication Deprecated**
   - MD5 is broken for collision resistance (though collision not helpful for auth)
   - Single-round hashing (no PBKDF2)
   - Vulnerable to brute-force with rainbow tables
   - **Mitigation**: SCRAM-SHA-256 strongly preferred; MD5 must be explicitly enabled in hba.conf

4. **Plaintext Password in Transit (if plaintext auth)**
   - "password" auth method sends plaintext over network
   - **Mitigation**: Requires SSL/TLS in production (enforced via HBA "hostssl" type)
   - **Acceptable for**: Unix domain socket connections (localhost, trusted)

5. **SCRAM-SHA-256 Iteration Count**
   - Iterations stored in password hash, not configurable per-password
   - Current default: 4096 (may be low by modern standards)
   - **Mitigation**: Configurable via password_encryption GUC; 15000+ recommended

6. **Role Lookup Happens Even If User Doesn't Exist**
   - get_role_oid(role, true) in check_hba [hba.c:2538]
   - If role doesn't exist, OidIsValid returns false, continue HBA matching
   - **Intent**: Allow HBA rules to match even for non-existent roles (e.g., reject rule)
   - **Potential Issue**: Malicious user can probe for role existence via connection attempts
   - **Mitigation**: Mock authentication for non-existent users ensures same timing

7. **No Rate Limiting on Authentication Attempts**
   - Multiple failed password attempts not rate-limited by server
   - Attacker can brute-force weak passwords
   - **Mitigation**: Authentication timeout (AuthenticationTimeout GUC) limits hanging connections
   - **Recommendation**: Use pgbouncer or pg_stat_statements to detect brute-force

8. **SASLprep Processing Lenient**
   - auth-scram.c comments note: "If password isn't valid UTF-8, raw bytes used"
   - Could allow different passwords to normalize to same value
   - **Mitigation**: Consistent application; no known collision attacks
   - **Impact**: Minimal security risk; affects only non-UTF8 passwords

9. **Client Encoding Undefined During Auth**
   - auth-scram.c:46: "encoding being used during authentication is undefined"
   - Username/password encoding may be misinterpreted
   - **Mitigation**: SCRAM uses UTF-8 by standard; lenient fallback for non-UTF8
   - **Impact**: Could allow encoding-based username spoofing
   - **Example**: Different bytes interpreted as different characters in different encodings

10. **No Mutual Authentication (Server Authentication)**
    - Client receives server challenges but doesn't verify server identity
    - Client connected to wrong server wouldn't know
    - **Mitigation**: TLS certificates provide server authentication
    - **Risk**: If TLS not used, MITM can intercept all credentials

### Existing Mitigations

| Vulnerability | Mitigation |
|---|---|
| Username enumeration via timing | Mock auth for non-existent users; same computational load |
| Plaintext password in transit | SSL/TLS encryption layer; "hostssl" in HBA |
| Weak hashing (MD5) | SCRAM-SHA-256 available; MD5 deprecated |
| Brute-force password guessing | PBKDF2 iterations (4096+); authentication timeout |
| Connection hijacking (SCRAM) | Channel binding via TLS server certificate fingerprint |
| Log injection | Username truncated, but not escaped in error messages |
| Buffer overflow in password parsing | StringInfo with bounds checking |
| Null-terminated string issues | Startup packet padded with null byte; length checks |

### Attack Scenarios

**Scenario 1: Username Enumeration**
- Attacker tries login attempts with common usernames
- For non-existent user: server goes through mock authentication (same timing)
- For existent user with wrong password: server goes through real authentication (same timing)
- **Result**: Cannot distinguish via timing alone

**Scenario 2: Dictionary Attack on Weak Password**
- Attacker captures SCRAM exchange (can be done in clear if TLS not used)
- Tries to brute-force ClientProof by hashing common passwords
- PBKDF2 with 4096 iterations makes each attempt ~4000x slower
- **Result**: Slow; impractical for weak passwords

**Scenario 3: MITM Attack (Plaintext Auth)**
- Attacker intercepts TCP connection, impersonates server
- Client sends plaintext password
- **Result**: Attacker captures password
- **Mitigation**: SSL/TLS prevents this; plaintext auth requires hostnossl in HBA

**Scenario 4: Role Name Spoofing via Case Variation**
- Attacker uses username "Admin" when HBA rule specifies "admin"
- PostgreSQL treats role names as case-insensitive in catalog
- HBA rule matching is case-sensitive (string comparison)
- **Result**: Could bypass role-based HBA rules
- **Mitigation**: Administrators use lowercase in HBA rules; PostgreSQL folds names consistently

**Scenario 5: Encoding-Based Username Spoofing**
- Attacker sends username in non-UTF8 encoding
- Server interprets bytes differently than intended
- Could match different role name
- **Result**: Possible privilege escalation
- **Mitigation**: Limited; client encoding should be validated before auth

### Recommended Hardening

1. **Enforce SCRAM-SHA-256**: Disable MD5 and plaintext auth in pg_hba.conf
2. **Use SSL/TLS**: Require "hostssl" for all non-localhost connections
3. **Enable Channel Binding**: Use "scram-sha-256-plus" if TLS is used
4. **Increase PBKDF2 Iterations**: Alter user password after increasing password_encryption setting
5. **Log Authentication Failures**: Monitor auth logs for brute-force attempts
6. **Use Connection Pooling**: pgbouncer can rate-limit connections per user
7. **Restrict HBA Access**: Use narrow IP ranges and explicit database/role lists
8. **Validate Client Encoding**: Ensure client_encoding is set before authentication
9. **Monitor Failed Connections**: Use pg_stat_activity + custom monitoring

---

## Summary

PostgreSQL's authentication pipeline follows a well-structured flow from TCP acceptance through cryptographic verification:

1. **Connection → Startup Packet**: Untrusted username and database received
2. **HBA Matching**: Connection type, IP, database, and role matched against configuration
3. **Authentication Method**: Determined from HBA rule; routed to appropriate handler
4. **Password Verification**:
   - MD5/Plaintext: Password compared against stored hash
   - SCRAM: Multi-round cryptographic proof exchange
5. **Session Establishment**: Authenticated user context prepared for query processing

**Attack Surface**: Limited to startup packet fields, password/SASL payloads, and HBA configuration. Catalog lookups use untrusted parameters as keys, but internally validated by PostgreSQL. No SQL injection in auth subsystem due to use of parameterized cache lookups.

**Security Properties**: Strong for SCRAM-SHA-256 (timing-resistant, no plaintext, PBKDF2 iterations). Weak for MD5 (single-round hashing) and plaintext auth (network exposure). Channel binding via TLS prevents connection hijacking. Mock authentication prevents username enumeration via timing side-channels.

**Mitigations**: Present and effective for known vulnerabilities. Primary defense is SCRAM-SHA-256 + TLS; legacy auth methods (MD5, plaintext) should be disabled in production. Configuration-driven security allows administrators to enforce strong auth and fine-grained access control via pg_hba.conf.

**Remaining Risks**: Brute-force attacks (password strength + PBKDF2 iterations), encoding-based spoofing (rare; consistent handling), case-sensitivity in HBA matching (best practice: lowercase roles). No fundamental cryptographic weaknesses in SCRAM implementation; design follows RFC 5802 closely.
