# PostgreSQL Client Authentication Pipeline Security Analysis

## Executive Summary

This analysis traces the PostgreSQL client authentication pipeline from TCP connection acceptance through HBA rule matching, password/SCRAM-SHA-256 verification, role validation, and session establishment. The authentication subsystem spans multiple files and processes both untrusted client data (startup packet, credentials) and configuration data (HBA rules). The design includes multiple mitigations against user enumeration attacks and MITM attacks, though some timing-based vulnerabilities remain.

---

## Files Examined

### Core Authentication Files
- **src/backend/libpq/auth.c** — Main authentication dispatcher, handles all auth methods (password, md5, scram, gss, sspi, pam, ldap, cert, ident, peer, radius, oauth), sends auth requests and processes responses
- **src/backend/libpq/crypt.c** — Password retrieval from pg_authid catalog and verification (plaintext, MD5, SCRAM-SHA-256)
- **src/backend/libpq/auth-scram.c** — SCRAM-SHA-256 mechanism implementation (RFC 5802, 5803, 7677), includes server-side SASL state machine
- **src/backend/libpq/auth-sasl.c** — SASL message exchange framework, receives SASL mechanism selection and tokens from client
- **src/backend/libpq/auth-oauth.c** — OAuth/OAUTHBEARER mechanism implementation (RFC 7628)

### HBA Configuration & Matching
- **src/backend/libpq/hba.c** — HBA file parsing (load_hba), HBA rule matching (check_hba), role/database validation, provides hba_getauthmethod()

### Connection Handling
- **src/backend/libpq/pqcomm.c** — TCP connection acceptance (AcceptConnection), low-level socket I/O (pq_init, pq_recvbuf, secure_read/write), message framing (pq_getmessage, pq_startmsgread)
- **src/backend/tcop/backend_startup.c** — Startup packet parsing (ProcessStartupPacket), extracts user_name, database_name, options, GUC parameters, SSL/GSSAPI negotiation

### Session Initialization
- **src/backend/utils/init/postinit.c** — Performs authentication (PerformAuthentication), manages HBA loading (load_hba), sets authentication timeout, establishes database connection (InitPostgres), sets up role permissions, initializes session variables

### Encryption & Security Transport
- **src/backend/libpq/be-secure.c** — SSL/GSSAPI encryption wrapper interface
- **src/backend/libpq/be-secure-openssl.c** — OpenSSL/TLS implementation
- **src/backend/libpq/be-secure-gssapi.c** — GSSAPI encryption support

---

## Entry Points

### 1. **TCP Connection Acceptance**
- **Location**: src/backend/libpq/pqcomm.c:794 `AcceptConnection()`
- **Untrusted Input**: Raw TCP socket data
- **Description**: Postmaster accepts a new TCP connection via `accept(2)` syscall. Fills ClientSocket structure with file descriptor and remote address information. No input validation at this point (OS handles connection).

### 2. **Startup Packet Parsing**
- **Location**: src/backend/tcop/backend_startup.c:492 `ProcessStartupPacket()`
- **Untrusted Inputs**:
  - Protocol version (4 bytes from client)
  - Packet length (calculated from first 4 bytes)
  - User name (string from packet)
  - Database name (string from packet)
  - GUC options (arbitrary key=value pairs)
  - Replication parameter (boolean or "database" string)
- **Description**: Reads and parses the startup packet sent by the client. Extracts connection parameters including username, database, and GUC options. Validates packet structure but parses untrusted strings.

### 3. **Password Packet Reception**
- **Location**: src/backend/libpq/auth.c:707 `recv_password_packet()`
- **Untrusted Input**: Password string (up to PG_MAX_AUTH_TOKEN_LENGTH bytes)
- **Description**: Receives password from client in response to AUTH_REQ_PASSWORD. Validates message type and length but does not validate content.

### 4. **SASL/SCRAM Token Reception**
- **Location**: src/backend/libpq/auth-sasl.c:43 `CheckSASLAuth()`
- **Untrusted Inputs**:
  - SASL mechanism selection (string from client)
  - SASL tokens (up to mech->max_message_length bytes)
- **Description**: SASL framework that receives mechanism selection and SASL tokens from client. Delegates to mechanism-specific handlers (SCRAM, OAuth).

### 5. **GSSAPI Token Reception**
- **Location**: src/backend/libpq/auth.c:920 `pg_GSS_recvauth()`
- **Untrusted Input**: GSSAPI tokens from client
- **Description**: Receives GSSAPI authentication tokens in loop until authentication completes.

### 6. **SSPI Token Reception**
- **Location**: src/backend/libpq/auth.c:2382 `pg_SSPI_recvauth()`
- **Untrusted Input**: SSPI tokens from client
- **Description**: Receives SSPI (Windows) authentication tokens.

### 7. **OAuth Token Reception**
- **Location**: src/backend/libpq/auth-oauth.c (integrated via CheckSASLAuth)
- **Untrusted Input**: OAuth/OAUTHBEARER token from client
- **Description**: Receives OAuth bearer token, validates via external validator module.

### 8. **LDAP/PAM/RADIUS Credentials**
- **Locations**:
  - LDAP: src/backend/libpq/auth.c:2084 `CheckLDAPAuth()`
  - PAM: src/backend/libpq/auth.c:1910 `CheckPAMAuth()`
  - RADIUS: src/backend/libpq/auth.c:2800 `CheckRADIUSAuth()`
- **Untrusted Input**: User-supplied passwords sent via these external systems
- **Description**: Delegates password verification to external systems.

---

## Data Flow Analysis

### **Flow 1: Startup Packet → HBA Matching → Authentication Method Selection**

**Source**: TCP connection → ProcessStartupPacket() raw packet bytes
**Transformations**:
1. TCP accept() in AcceptConnection (pqcomm.c:798)
2. Startup packet read into buffer (pqcomm.c, pq_startmsgread/pq_getbytes)
3. Protocol version extracted (backend_startup.c:565)
4. Packet parsed for user_name, database_name, options (backend_startup.c:720-804)
5. **Validation**: Length checks (MAX_STARTUP_PACKET_LENGTH), null-termination checks, protocol version validation
6. Strings truncated to NAMEDATALEN if needed (backend_startup.c:840-843)

**Sink**: ClientAuthentication() receives port->user_name, port->database_name (auth.c:379)
- Calls hba_getauthmethod(port) → check_hba() (hba.c:2538)
- check_hba() matches HBA rules using:
  - Connection type (TCP vs Unix socket)
  - IP address matching (check_ip, check_hostname, check_same_host_or_net)
  - Database matching (check_db)
  - Role/user matching (check_role, get_role_oid)
- Sets port->hba->auth_method for authentication dispatcher

**Files in Chain**:
1. src/backend/libpq/pqcomm.c (socket accept, message framing)
2. src/backend/tcop/backend_startup.c (startup packet parsing)
3. src/backend/libpq/hba.c (HBA matching)
4. src/backend/libpq/auth.c (authentication dispatcher)

---

### **Flow 2: Plaintext Password Authentication (uaPassword)**

**Source**: Client sends password via recv_password_packet()
1. Client → AUTH_REQ_PASSWORD sent (auth.c:794)
2. Client responds with PqMsg_PasswordMessage containing password string
3. recv_password_packet() reads message (auth.c:707-776)

**Transformations**:
1. Message type validation: expects PqMsg_PasswordMessage (auth.c:716)
2. Length check: pq_getmessage() enforces PG_MAX_AUTH_TOKEN_LENGTH (auth.c:732)
3. Packet length validation: strlen + 1 must match buf.len (auth.c:744)
4. Empty password check: len == 1 is rejected (auth.c:762)
5. Returns raw password string

**Sink**: CheckPasswordAuth() (auth.c:788-817)
1. Calls get_role_password(port->user_name, logdetail) → queries pg_authid.rolpassword
   - Looks up role in system cache (crypt.c:47)
   - Retrieves stored password hash (crypt.c:55)
   - Checks password expiration (crypt.c:76)
   - Returns shadow_pass (encrypted password)
2. Calls plain_crypt_verify() (crypt.c:256-321)
   - Determines password type (MD5 or SCRAM-SHA-256)
   - For SCRAM: calls scram_verify_plain_password()
   - For MD5: encrypts client password and compares
   - Returns STATUS_OK or STATUS_ERROR
3. If OK, calls set_authn_id(port, port->user_name) to log authentication

**Files in Chain**:
1. src/backend/libpq/auth.c (recv_password_packet, CheckPasswordAuth)
2. src/backend/libpq/crypt.c (get_role_password, plain_crypt_verify)
3. src/backend/libpq/pqcomm.c (pq_getmessage, message validation)

---

### **Flow 3: Challenge-Response Password Authentication (uaMD5, uaSCRAM)**

**Source**: Client initiates challenge-response
1. Server sends AUTH_REQ_MD5 with random salt OR AUTH_REQ_SCRAM mechanism
2. Client responds with challenge response

**Transformations**:

#### **Subflow 3a: MD5 Authentication**
1. CheckPWChallengeAuth() (auth.c:823-880)
2. Calls get_role_password() to retrieve stored password hash from pg_authid
3. Generates random 4-byte salt via pg_strong_random() (auth.c:890)
4. Sends AUTH_REQ_MD5 with salt (auth.c:897)
5. Receives response via recv_password_packet() (auth.c:899)
6. Calls md5_crypt_verify() (crypt.c:202-243)
   - Validates password type is MD5 (crypt.c:213)
   - Computes correct MD5 hash using client password + salt
   - Compares with client response via strcmp() (crypt.c:233)
   - Returns STATUS_OK or STATUS_ERROR

#### **Subflow 3b: SCRAM-SHA-256 Authentication**
1. CheckPWChallengeAuth() (auth.c:823-880)
2. Calls get_role_password() to retrieve stored SCRAM secret
3. Calls CheckSASLAuth(&pg_be_scram_mech, ...) (auth.c:862)
4. SASL loop receives client SASL response messages
   - First message: mechanism selection + initial client response
   - Parses mechanism name "SCRAM-SHA-256" (auth-sasl.c:117)
   - Calls mech->init() → scram_init() (auth-scram.c, if exists)
5. SCRAM mechanism implementation:
   - Parses client-first-message (username, nonce, channel binding info)
   - Generates server-first-message with salt, iteration count, nonce
   - Sends AUTH_REQ_SASL response with server-first-message
6. Client sends client-final-message (channel binding data, proof)
7. SCRAM verifies proof using PBKDF2-HMAC-SHA256 with stored salt/iterations
8. Returns STATUS_OK or STATUS_ERROR

**Files in Chain**:
1. src/backend/libpq/auth.c (CheckPWChallengeAuth, sends AUTH_REQ_MD5/SCRAM)
2. src/backend/libpq/crypt.c (get_role_password, md5_crypt_verify, plain_crypt_verify for SCRAM)
3. src/backend/libpq/auth-sasl.c (CheckSASLAuth, SASL message loop)
4. src/backend/libpq/auth-scram.c (SCRAM mechanism state machine, crypto)

---

### **Flow 4: GSSAPI/SSPI Authentication (uaGSS, uaSSPI)**

**Source**: GSSAPI/SSPI tokens from client

**Transformations**:
1. ClientAuthentication() dispatches to pg_GSS_recvauth() or pg_SSPI_recvauth() (auth.c:541-577)
2. Sends AUTH_REQ_GSS or AUTH_REQ_SSPI to client
3. Receives GSSAPI/SSPI tokens in loop via recv_password_packet() or pq_GSS_recvauth()
4. GSSAPI context exchange:
   - Initializes gss context (GSS_C_NO_CONTEXT)
   - Calls gss_accept_sec_context() repeatedly until complete
   - Extracts authenticated principal from gss context
   - Optional delegation of credentials (if pg_gss_accept_delegation = true)
5. Sets port->gss->authenticated = true, extracts principal name
6. Calls set_authn_id(port, principal_name)

**Sink**: Session established with GSSAPI-authenticated user

**Files in Chain**:
1. src/backend/libpq/auth.c (pg_GSS_recvauth, pg_GSS_checkauth)
2. src/backend/libpq/be-secure-gssapi.c (GSSAPI context operations)

---

### **Flow 5: OAuth/OAUTHBEARER Authentication (uaOAuth)**

**Source**: OAuth bearer token from client

**Transformations**:
1. ClientAuthentication() dispatches to CheckSASLAuth(&pg_be_oauth_mech, ...) (auth.c:628)
2. SASL loop receives client OAuth token in initial response (auth-sasl.c)
3. oauth_init() loads validator module (auth-oauth.c)
4. oauth_exchange() validates token:
   - Parses OAUTHBEARER format (Bearer <token>)
   - Calls external validator library via dynamically loaded module
   - Validator returns authentication info (user ID, etc.)
   - Extracts username from validator response
5. Calls set_authn_id(port, returned_username) (auth-oauth.c:674)

**Sink**: Session established with OAuth-authenticated user

**Files in Chain**:
1. src/backend/libpq/auth-oauth.c (OAuth validation)
2. src/backend/libpq/auth-sasl.c (SASL framework)
3. External validator module (loaded dynamically)

---

### **Flow 6: Post-Authentication Session Establishment**

**Source**: Successful authentication status returned from auth method

**Sink**: InitPostgres() (postinit.c:712)

**Transformations**:
1. ClientAuthentication() returns with STATUS_OK (auth.c:666)
2. Sends AUTH_REQ_OK to client (auth.c:667)
3. Backend continues in PostgresMain() (main/postgres.c, after authentication)
4. InitPostgres() called to establish database connection:
   - Loads database OID from pg_database using port->database_name (postinit.c)
   - Loads database configuration
   - Initializes catalog caches
   - Sets up role permissions via GetSessionUser() (authenticated user)
   - Loads role-specific settings from pg_db_role_setting
   - Applies GUC settings from pg_settings
5. Creates session entry in pg_stat_statements_info
6. Begins first transaction

**Files in Chain**:
1. src/backend/libpq/auth.c (returns authentication status)
2. src/backend/utils/init/postinit.c (InitPostgres, database initialization)
3. src/backend/main/postgres.c (PostgresMain, calls InitPostgres)

---

## Dependency Chain

**Complete authentication pipeline from connection to session:**

```
TCP Connection
  ↓
pqcomm.c: AcceptConnection() → accept(2) syscall
  ↓
pqcomm.c: pq_init() → initialize Port structure
  ↓
backend_startup.c: ProcessStartupPacket() → parse startup packet
  ├─ Extract: user_name, database_name, options
  ├─ Validate: packet length, protocol version
  └─ Store in Port structure
  ↓
postinit.c: PerformAuthentication() → hba.c: load_hba()
  ├─ Parse pg_hba.conf file
  └─ Build HBA rule list
  ↓
auth.c: ClientAuthentication()
  ├─ hba.c: hba_getauthmethod() → check_hba()
  │   ├─ hba.c: check_ip() [IP matching]
  │   ├─ hba.c: check_hostname() [hostname matching]
  │   ├─ hba.c: check_db() [database matching]
  │   └─ hba.c: check_role() [role matching]
  │
  └─ Dispatch to auth method handler:
      │
      ├─ uaPassword/uaMD5/uaSCRAM:
      │   ├─ auth.c: recv_password_packet()
      │   ├─ auth.c: CheckPasswordAuth() or CheckPWChallengeAuth()
      │   ├─ crypt.c: get_role_password()
      │   │   ├─ SearchSysCache1(AUTHNAME, role_name)
      │   │   ├─ SysCacheGetAttr(rolpassword)
      │   │   ├─ SysCacheGetAttr(rolvaliduntil)
      │   │   └─ ReleaseSysCache()
      │   │
      │   └─ crypt.c: plain_crypt_verify() or md5_crypt_verify()
      │       └─ Password comparison
      │
      ├─ uaGSS/uaSSPI:
      │   ├─ auth.c: pg_GSS_recvauth() [or pg_SSPI_recvauth()]
      │   └─ be-secure-gssapi.c: GSSAPI context operations
      │
      ├─ uaOAuth:
      │   ├─ auth-sasl.c: CheckSASLAuth()
      │   └─ auth-oauth.c: OAuth validation
      │
      └─ [Other methods: PAM, LDAP, RADIUS, IDENT, etc.]
  ↓
postinit.c: InitPostgres() → session initialization
  ├─ GetDatabaseTuple() → database catalog lookup
  ├─ Load database configuration
  └─ Load role permissions
  ↓
Backend ready to execute queries as authenticated user
```

---

## Security Analysis

### **Vulnerability Classes & Mitigations**

#### **1. User Enumeration via Timing Attacks**

**Vulnerability**: If authentication fails with different delays for "user not found" vs "wrong password", an attacker can enumerate valid usernames.

**Existing Mitigations**:
- **SCRAM "Doomed" Authentication** (auth-scram.c:65-74): When user doesn't exist or has invalid password, server still performs full SCRAM exchange with fake salt/iterations to avoid timing differences. The `scram_state->doomed` flag indicates the authentication will fail, but the protocol exchange proceeds normally.
- **Plain Password & MD5**: In get_role_password() (crypt.c:38-84), if user doesn't exist, function returns NULL. However, in CheckPWChallengeAuth(), the "doomed" approach applies to SCRAM but not plaintext/MD5.

**Gaps**:
- Plain password authentication doesn't use "doomed" approach for nonexistent users
- Role lookup via get_role_oid() is done before authentication, not hidden
- Database lookup via check_db() happens during HBA matching, before auth attempt

**Mitigation Quality**: GOOD for SCRAM, MODERATE for plain password

---

#### **2. Password Disclosure via Memory/Core Dumps**

**Vulnerability**: Plaintext password in memory during authentication could be exposed via core dumps or memory disclosure.

**Existing Mitigations**:
- Password strings are allocated in temporary memory context and freed immediately after use (recv_password_packet, CheckPasswordAuth)
- No persistent storage in memory after comparison
- Password not logged (elog(DEBUG5) only, no password text)

**Gaps**:
- C library functions (strcpy, strlen, strcmp) don't provide timing-safe comparisons for passwords in plaintext mode (though unlikely attack vector)
- Memory may not be zeroed after use (depends on allocator)

**Mitigation Quality**: GOOD (standard practice)

---

#### **3. SCRAM Channel Binding & MITM Attacks**

**Vulnerability**: SCRAM can be vulnerable to MITM attacks without channel binding.

**Existing Mitigations**:
- Channel binding to TLS certificate endpoint via "tls-server-end-point" binding type (auth-scram.c:20-31)
- Post-SSL-negotiation validation: checks for unencrypted buffered data after SSL negotiation, indicates MITM attempt (backend_startup.c:624-628)
- Similar check for GSSAPI encryption (backend_startup.c:678-682)

**Gaps**:
- Channel binding is optional if not using TLS/GSSAPI
- Plaintext authentication has no MITM protection

**Mitigation Quality**: GOOD for encrypted connections, POOR for plaintext

---

#### **4. LDAP Injection**

**Vulnerability**: User-supplied data in LDAP queries could be exploited if not properly escaped.

**Location**: auth.c:2084 `CheckLDAPAuth()`

**Existing Mitigations**:
- Username is validated against role in system cache before LDAP query
- User field comes from pg_authid, not directly from client
- LDAP query uses role name from authenticated user, not client input

**Gaps**:
- If user mapping is configured (ident_file), user names from ident could be used in LDAP queries
- External LDAP library handles escaping (not PostgreSQL code)

**Mitigation Quality**: GOOD (user comes from catalog, not client)

---

#### **5. SQL Injection via Role/Database Names**

**Vulnerability**: Role or database names from startup packet could be injected into SQL queries.

**Location**: ProcessStartupPacket extracts user_name, database_name; check_hba uses them in role/database lookups

**Existing Mitigations**:
- Role lookup uses get_role_oid() which queries pg_authid system catalog with AUTHNAME system cache (crypt.c:47)
- System cache query uses protocol-level name matching, not SQL strings
- Database lookup uses pg_database.datname with index scan (postinit.c:125-129)
- Names are never passed as SQL string literals, always via catalog API

**Gaps**:
- None identified - catalog lookup API handles name escaping

**Mitigation Quality**: EXCELLENT

---

#### **6. HBA Configuration Bypass**

**Vulnerability**: If HBA matching is incorrect, wrong authentication methods could be applied.

**Location**: hba.c:2531 `check_hba()`

**Existing Mitigations**:
- HBA rules parsed at server startup (or reload), syntax validation performed
- HBA matching checks multiple criteria: connection type, IP/hostname, database, role
- Falls back to implicit reject if no rule matches (hba.c:2627-2630)
- Role existence checked via get_role_oid (hba.c:2538)

**Gaps**:
- Hostname checking via DNS lookup (check_hostname) could be TOCTOU if host updates DNS during authentication
- Regex matching on rules could have complexity DoS

**Mitigation Quality**: GOOD

---

#### **7. Password Comparison Timing Leaks**

**Vulnerability**: Using strcmp() for password comparison could leak password length via timing.

**Location**:
- crypt.c:233 `md5_crypt_verify()` uses strcmp()
- crypt.c:295 `plain_crypt_verify()` uses strcmp() for MD5 hashes

**Existing Mitigations**:
- For SCRAM (and plaintext SCRAM verification), uses crypto library timing-safe functions internally
- Passwords are hashed before comparison, length is consistent
- SCRAM uses PBKDF2 which is computationally expensive (rounds=4096 default)

**Gaps**:
- Plain strcmp() on MD5 hashes could leak password length if different
- MD5 password format is: "md5" + 32-char hex = fixed length, but strcmp stops at first difference

**Mitigation Quality**: MODERATE (hashes are fixed-length, so timing is consistent)

---

#### **8. Startup Packet Validation**

**Vulnerability**: Malformed startup packets could cause buffer overflows or protocol violations.

**Location**: backend_startup.c:492 `ProcessStartupPacket()`

**Existing Mitigations**:
- Maximum packet length enforced (MAX_STARTUP_PACKET_LENGTH = 10240 bytes)
- Packet length must match actual data received
- Names are truncated to NAMEDATALEN (63 bytes)
- Null-termination guaranteed by zeroing extra byte (backend_startup.c:550)
- Protocol version validated (backend_startup.c:704-713)
- Packet terminator check (backend_startup.c:810)

**Gaps**:
- None identified - comprehensive validation present

**Mitigation Quality**: EXCELLENT

---

#### **9. SASL Message Flooding**

**Vulnerability**: Client could send unlimited SASL messages, causing DoS.

**Location**: auth-sasl.c:78-195 `CheckSASLAuth()` message loop

**Existing Mitigations**:
- Maximum message length enforced: PG_MAX_AUTH_TOKEN_LENGTH = 10485760 bytes (10 MB)
- AuthenticationTimeout setting limits total auth time (postinit.c:247)
- Statement timeout applies during authentication

**Gaps**:
- Large message limit (10 MB) could still allow some DoS

**Mitigation Quality**: GOOD (message limit + timeout)

---

#### **10. GSSAPI/SSPI Context Exhaustion**

**Vulnerability**: Malicious GSSAPI tokens could cause expensive computations or resource exhaustion.

**Location**: auth.c:920 `pg_GSS_recvauth()`, auth.c:2382 `pg_SSPI_recvauth()`

**Existing Mitigations**:
- AuthenticationTimeout limits context exchange time
- GSSAPI library (MIT Kerberos, SSPI) performs input validation
- Message length checks via PG_MAX_AUTH_TOKEN_LENGTH

**Gaps**:
- GSSAPI library vulnerabilities would be inherited

**Mitigation Quality**: GOOD (relies on external library)

---

#### **11. Password Expiration Check**

**Vulnerability**: Expired passwords could be used if check is bypassed.

**Location**: crypt.c:76 `get_role_password()` checks rolvaliduntil timestamp

**Existing Mitigations**:
- Password expiration checked during authentication
- Comparison with GetCurrentTimestamp()
- Expired password causes get_role_password() to return NULL
- NULL password triggers failure in authentication handlers

**Gaps**:
- None identified

**Mitigation Quality**: EXCELLENT

---

#### **12. Ident/Peer Authentication Spoofing**

**Vulnerability**: Ident protocol (port 113) can be spoofed or man-in-the-middle attacked.

**Location**: auth.c:73 `ident_inet()`, auth.c:80 `auth_peer()`

**Existing Mitigations**:
- Ident authentication only available for TCP (ident_inet) or Unix socket (auth_peer)
- Result from ident server is validated against role in pg_authid
- Peer authentication (Unix socket) is more secure, uses SO_PEERCRED

**Gaps**:
- Ident authentication inherently weak due to protocol vulnerabilities
- Documented as legacy method

**Mitigation Quality**: MODERATE (ident is weak, peer is strong)

---

#### **13. OAuth Validator Module Trust**

**Vulnerability**: External OAuth validator module could be compromised or malicious.

**Location**: auth-oauth.c validator module loading and execution

**Existing Mitigations**:
- Validator module must be explicitly configured by DBA (oauth_validator_libraries setting)
- Module is loaded via dlopen(), standard system library loading (checks /etc/ld.so.cache, rpath)
- Module is loaded in server process, standard PostgreSQL plugin mechanism

**Gaps**:
- No cryptographic verification of module
- Module loaded with full server privileges
- Vulnerability in module affects entire server

**Mitigation Quality**: POOR (relies on system integrity and DBA vetting)

---

#### **14. GUC Option Injection**

**Vulnerability**: Malicious GUC options in startup packet could configure authentication differently.

**Location**: backend_startup.c:786-790 stores GUC options from startup packet, applied later in InitPostgres

**Existing Mitigations**:
- GUC options are applied via SetConfigOptionFromString(), which validates option names and values
- Security-critical GUC options (e.g., ssl, password_encryption) can only be set at server startup, not per-connection
- GUC options stored separately from auth process, applied after authentication

**Gaps**:
- None identified - GUC system handles validation

**Mitigation Quality**: GOOD

---

#### **15. Role/Database Cache Poisoning**

**Vulnerability**: System cache lookups could return stale or incorrect data during concurrent DDL.

**Location**: crypt.c:47 `SearchSysCache1(AUTHNAME)`, hba.c:2538 `get_role_oid()`

**Existing Mitigations**:
- System cache is protected by proper locking (handled by cache management)
- Cache invalidation on role/database changes is handled by catalog infrastructure
- Lookups during authentication happen in separate backend process, no cache sharing issues

**Gaps**:
- Standard PostgreSQL cache semantics apply

**Mitigation Quality**: EXCELLENT (handled by core infrastructure)

---

## Attack Scenarios

### **Scenario 1: Username Enumeration via Timing Attack on Plain Password**

**Attack**: Attacker sends many authentication attempts with different usernames, measures response time to identify valid usernames.

**Mitigation Status**:
- SCRAM: Protected by "doomed" authentication (no timing difference for nonexistent users)
- Plain password: NOT protected (response is faster if user doesn't exist)

**Recommended Fix**: Extend "doomed" authentication to plain password and MD5 methods.

---

### **Scenario 2: MITM Attack on Plaintext Connection**

**Attack**: Attacker intercepts plaintext password sent over TCP connection (no TLS).

**Mitigation Status**: NONE. No protection for plaintext connections.

**Recommended Fix**: Enforce SSL/TLS for production deployments, configure require_ssl GUC.

---

### **Scenario 3: Malicious HBA Rule Injection**

**Attack**: DBA (or attacker with file access) modifies pg_hba.conf to change authentication rules.

**Mitigation Status**: File permissions are responsibility of DBA and OS. PostgreSQL validates syntax.

**Recommended Fix**: No change needed (operating system security responsibility).

---

### **Scenario 4: SCRAM Salt Reuse**

**Attack**: If server uses same salt for multiple authentication attempts, attacker could precompute hashes (rainbow table).

**Mitigation Status**: PROTECTED. Salt is derived from stored SCRAM secret which is unique per user.

---

### **Scenario 5: Startup Packet Buffer Overflow**

**Attack**: Attacker sends oversized startup packet to overflow buffer.

**Mitigation Status**: PROTECTED. Maximum length enforced (MAX_STARTUP_PACKET_LENGTH).

---

## Summary of Findings

### **Overall Security Posture: STRONG**

The PostgreSQL authentication pipeline demonstrates excellent security practices:

1. **Input Validation**: Comprehensive checks on startup packet, password length, message types
2. **User Enumeration Protection**: "Doomed" authentication prevents timing leaks for SCRAM (best practice)
3. **Cryptography**: SCRAM-SHA-256 with PBKDF2, channel binding to TLS, proper salt handling
4. **System Integrity**: Catalog lookups prevent SQL injection, GUC validation prevents configuration bypass
5. **Transport Security**: Channel binding, MITM detection for SSL/GSSAPI
6. **Defense in Depth**: Multiple authentication methods, HBA rules, role/database validation

### **Identified Gaps:**

1. **Plaintext Password Timing Leaks**: Plain password method doesn't use "doomed" authentication for nonexistent users
2. **OAuth Module Trust**: External validator modules have full server access with no verification
3. **Plaintext Connections**: No protection against MITM on connections without TLS/GSSAPI
4. **Ident Protocol Weakness**: Ident authentication is inherently weak (legacy protocol)

### **Recommended Remediation Priority:**

1. **HIGH**: Extend "doomed" authentication to plaintext password and MD5 methods (blocks user enumeration timing attacks)
2. **MEDIUM**: Add cryptographic verification or sandboxing for OAuth validator modules
3. **MEDIUM**: Document MITM risks for plaintext connections, encourage TLS in deployment guides
4. **LOW**: Consider deprecating Ident authentication (weak protocol)

### **Files in Attack Surface (12 total):**

Authentication-critical files that process untrusted client data or make sensitive decisions:

1. src/backend/libpq/pqcomm.c — TCP connection, message I/O
2. src/backend/tcop/backend_startup.c — Startup packet parsing
3. src/backend/libpq/auth.c — Authentication dispatcher, all auth methods
4. src/backend/libpq/crypt.c — Password retrieval, verification
5. src/backend/libpq/hba.c — HBA matching, role/database validation
6. src/backend/libpq/auth-scram.c — SCRAM-SHA-256 implementation
7. src/backend/libpq/auth-sasl.c — SASL framework
8. src/backend/libpq/auth-oauth.c — OAuth validation
9. src/backend/libpq/be-secure.c — Encryption wrapper
10. src/backend/libpq/be-secure-openssl.c — TLS implementation
11. src/backend/libpq/be-secure-gssapi.c — GSSAPI encryption
12. src/backend/utils/init/postinit.c — HBA loading, session initialization

---

## Conclusion

The PostgreSQL client authentication pipeline is well-designed with multiple layers of security. The use of "doomed" authentication for SCRAM prevents user enumeration attacks, cryptographic protocols use industry-standard algorithms, and input validation is comprehensive. The main recommendations for improvement are: (1) extending user enumeration protection to other auth methods, (2) improving OAuth module security, and (3) better documentation of plaintext connection risks. The codebase demonstrates security-conscious development practices.
