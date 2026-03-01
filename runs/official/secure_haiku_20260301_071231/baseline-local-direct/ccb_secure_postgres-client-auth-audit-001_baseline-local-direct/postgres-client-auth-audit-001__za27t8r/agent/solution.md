# PostgreSQL Client Authentication Pipeline Security Analysis

## Files Examined

### Primary Authentication Files
- `src/backend/libpq/auth.c` — Main authentication entry point and dispatcher for all auth methods
- `src/backend/libpq/auth-sasl.c` — SASL framework implementation for challenge-response auth
- `src/backend/libpq/auth-scram.c` — SCRAM-SHA-256 SASL mechanism implementation
- `src/backend/libpq/auth-oauth.c` — OAuth SASL mechanism implementation
- `src/backend/libpq/crypt.c` — Password storage and verification (MD5, SCRAM, plaintext)
- `src/backend/libpq/hba.c` — HBA configuration parsing, loading, and rule matching

### Connection Startup Files
- `src/backend/tcop/backend_startup.c` — Initial TCP connection handling and startup packet parsing
- `src/backend/postmaster/postmaster.c` — Postmaster TCP acceptance and backend spawning

### Password Retrieval
- `src/backend/libpq/crypt.c:get_role_password()` — Role password lookup from pg_authid catalog

### Certificate & SSL/GSSAPI
- `src/backend/libpq/be-secure.c` — SSL/TLS connection setup
- `src/backend/libpq/be-secure-gssapi.c` — GSSAPI/Kerberos encryption setup
- `src/backend/libpq/be-gssapi-common.c` — Shared GSSAPI utilities

### Network Communication
- `src/backend/libpq/pqcomm.c` — Low-level socket I/O, message framing
- `src/backend/libpq/pqformat.c` — Protocol message formatting and parsing

---

## Entry Points

### 1. **src/backend/tcop/backend_startup.c:ProcessStartupPacket()** (Line 492)
   - **Type**: Receives initial startup message (untrusted client data)
   - **Untrusted Input**:
     - Full startup packet buffer from wire
     - Protocol version (int32 from wire)
     - Arbitrary key-value pairs including:
       - `user` — Username (parsed at line 748-749)
       - `database` — Database name (parsed at line 746-747)
       - `options` — Command-line options
       - `replication` — Replication flag
       - Arbitrary GUC options (parsed at line 784-791)
   - **Input Constraints**:
     - Packet length validated (lines 535-542, max `MAX_STARTUP_PACKET_LENGTH`)
     - Username required (lines 827-830)
     - Database name defaults to username (lines 833-834)
     - Names truncated to `NAMEDATALEN-1` (lines 840-843)
   - **Output**: Populates `Port->user_name` and `Port->database_name` as C strings

### 2. **src/backend/utils/init/postinit.c:PerformAuthentication()** (Line 194)
   - **Type**: Wrapper that loads HBA/ident configs and dispatches to authentication
   - **Input**: `Port` structure with user_name, database_name from startup packet
   - **Calls**: `load_hba()` (EXEC_BACKEND mode) to reload HBA config
   - **Calls**: `ClientAuthentication(port)` at line 253
   - **Post-Auth** (lines 901-905): On success, calls `InitializeSessionUserId()` and `InitializeSystemUser()`

### 3. **src/backend/libpq/auth.c:ClientAuthentication()** (Line 379)
   - **Type**: Main authentication dispatcher after startup packet is parsed
   - **Input**: `Port` structure with user_name, database_name, source IP, SSL state
   - **First Operation** (line 390): Calls `hba_getauthmethod(port)` to determine auth method
   - **Initiates** all downstream authentication flows

### 4. **src/backend/libpq/auth.c:recv_password_packet()** (Line 707)
   - **Type**: Receives password message (0x70 'p') from client during auth
   - **Untrusted Input**:
     - Message type byte (line 715)
     - Raw password bytes (line 732, max `PG_MAX_AUTH_TOKEN_LENGTH`)
   - **Validation**:
     - Message type checked (lines 715-729)
     - Length consistency verified (lines 744-747)
     - Empty password rejected (lines 762-765)
   - **Output**: Null-terminated C string with password

### 5. **src/backend/libpq/auth-sasl.c:CheckSASLAuth()** (Line 44)
   - **Type**: Receives SASL response messages during challenge-response exchange
   - **Untrusted Input**:
     - Message type (lines 80-94, expects `PqMsg_SASLResponse`)
     - SASL initial response with selected mechanism name (line 117)
     - Arbitrary SASL token bytes (lines 133-145, max `mech->max_message_length`)
   - **Exchanges** with mechanism implementation (SCRAM or OAuth)

### 6. **src/backend/libpq/auth-scram.c** (Entry functions via CheckSASLAuth)
   - **Type**: SCRAM-SHA-256 mechanism receives client first message and responses
   - **Untrusted Input**:
     - Client-first-message with username claim and client-nonce (from SASL token)
     - Client-final-message with proof (channel binding, nonce, proof) (from SASL token)
   - **SASLprep Processing**: Password is run through SASLprep if valid UTF-8; otherwise raw bytes used (lines 37-59 in comments)

### 7. **src/backend/libpq/hba.c:check_hba()** (Line 2531)
   - **Type**: Matches HBA rules to determine if connection is allowed and which auth method to use
   - **Input**:
     - `port->user_name` (from startup packet)
     - `port->database_name` (from startup packet)
     - `port->raddr.addr` (client socket address)
     - `port->ssl_in_use` (SSL state flag)
   - **Processed Against**: `parsed_hba_lines` global list (pre-loaded from pg_hba.conf)
   - **Output**: Sets `port->hba` to matching HbaLine or implicit reject rule

---

## Data Flow

### Flow 1: Plaintext Password Authentication

```
TCP Connection Accepted
    ↓
[ENTRY POINT] ProcessStartupPacket()
    ├─ Receives: Startup message containing user, database
    ├─ Untrusted: Client-supplied user/database names
    ├─ Transform: Parsed as key-value pairs, null-terminated, truncated to NAMEDATALEN
    └─ Output: Port->user_name, Port->database_name

[ENTRY POINT] ClientAuthentication()
    ├─ Input: Port with user_name, database_name, IP, SSL state
    ├─ Calls: hba_getauthmethod(port) → check_hba(port)
    │   ├─ Matches port->user_name against HBA rules
    │   ├─ Matches port->database_name against HBA rules
    │   ├─ Matches port->raddr (client IP) against HBA CIDR/hostname
    │   └─ Sets port->hba to matching auth method
    │
    ├─ (case uaPassword) Calls: CheckPasswordAuth(port)
    │   ├─ Sends: AUTH_REQ_PASSWORD to client
    │   ├─ [ENTRY POINT] recv_password_packet()
    │   │   ├─ Receives: Startup message with password
    │   │   ├─ Untrusted: Client password bytes
    │   │   ├─ Validates: Message type, length consistency, not empty
    │   │   └─ Output: C string with password
    │   │
    │   ├─ [TRANSFORM] get_role_password(port->user_name)
    │   │   ├─ Untrusted Input: port->user_name from client
    │   │   ├─ Query: Looks up pg_authid.rolpassword for user
    │   │   ├─ Catalog Lookup: SearchSysCache1(AUTHNAME, username)
    │   │   ├─ Checks: Password not null, not expired (rolvaliduntil)
    │   │   ├─ Sensitive: Leaks user existence, password expiry to logs
    │   │   └─ Output: Encrypted password hash or NULL
    │   │
    │   ├─ [TRANSFORM] plain_crypt_verify(port->user_name, shadow_pass, passwd)
    │   │   ├─ Input: Username, stored password hash, client password
    │   │   ├─ Dispatches: Based on get_password_type(shadow_pass):
    │   │   │   ├─ PASSWORD_TYPE_SCRAM_SHA_256 → scram_verify_plain_password()
    │   │   │   ├─ PASSWORD_TYPE_MD5 → pg_md5_encrypt(client_pass with username salt)
    │   │   │   └─ PASSWORD_TYPE_PLAINTEXT → error
    │   │   ├─ Comparison: strcmp() on hashes
    │   │   └─ Output: STATUS_OK or STATUS_ERROR
    │   │
    │   ├─ [SINK] set_authn_id(port, port->user_name)
    │   │   ├─ Sets: MyClientConnectionInfo.authn_id = port->user_name
    │   │   ├─ Sets: MyClientConnectionInfo.auth_method
    │   │   ├─ Logs: Connection authenticated (if log_connections set)
    │   │   └─ Output: Logs, session globals set
    │   │
    │   └─ [SINK] sendAuthRequest(port, AUTH_REQ_OK)
    │       └─ Sends: Authentication success to client
    │
    └─ All paths converge: auth_failed() or success message sent
```

**Dependency Chain**: ProcessStartupPacket → BackendMain → InitPostgres → PerformAuthentication → load_hba/ClientAuthentication → hba_getauthmethod/check_hba → CheckPasswordAuth → recv_password_packet + get_role_password → plain_crypt_verify → set_authn_id → InitializeSessionUserId

---

### Flow 2: Challenge-Response Authentication (MD5 and SCRAM-SHA-256)

```
TCP Connection Accepted
    ↓
[ENTRY POINT] ProcessStartupPacket()
    └─ (same as Flow 1)

[ENTRY POINT] ClientAuthentication()
    ├─ Input: Port with user_name, database_name, IP
    ├─ Calls: hba_getauthmethod(port) → check_hba(port)
    │   └─ Sets: port->hba->auth_method = uaMD5 or uaSCRAM
    │
    ├─ (case uaMD5 or uaSCRAM) Calls: CheckPWChallengeAuth(port)
    │   ├─ [TRANSFORM] get_role_password(port->user_name)
    │   │   └─ (same as Flow 1, retrieves shadow_pass)
    │   │
    │   ├─ [TRANSFORM] get_password_type(shadow_pass)
    │   │   ├─ Checks: Prefix and format of stored password
    │   │   ├─ Parses SCRAM: parse_scram_secret() extracts iterations, salt, keys
    │   │   └─ Output: PASSWORD_TYPE_MD5 or PASSWORD_TYPE_SCRAM_SHA_256
    │   │
    │   ├─ If MD5: Calls CheckMD5Auth(port, shadow_pass)
    │   │   ├─ [TRANSFORM] pg_strong_random() generates 4-byte salt
    │   │   ├─ Sends: AUTH_REQ_MD5 with salt to client
    │   │   ├─ [ENTRY POINT] recv_password_packet()
    │   │   │   ├─ Receives: Client-computed MD5(MD5(password + username) + salt)
    │   │   │   └─ Output: Challenge response string
    │   │   │
    │   │   ├─ [TRANSFORM] md5_crypt_verify()
    │   │   │   ├─ Inputs: Username, stored "md5"-prefixed hash, client response
    │   │   │   ├─ Recomputes: MD5(stored_hash_without_prefix + server_salt)
    │   │   │   ├─ Comparison: strcmp(client_response, computed_hash)
    │   │   │   └─ Output: STATUS_OK or STATUS_ERROR
    │   │   │
    │   │   └─ [SINK] set_authn_id() (on success)
    │   │
    │   └─ Else (SCRAM): Calls CheckSASLAuth(&pg_be_scram_mech, port, shadow_pass)
    │       ├─ Sends: AUTH_REQ_SASL with mechanism list
    │       ├─ [ENTRY POINT] CheckSASLAuth() message exchange loop
    │       │   │
    │       │   ├─ [ENTRY POINT] pq_getbyte() receives message type
    │       │   │   └─ Untrusted: Client message type
    │       │   │
    │       │   ├─ [ENTRY POINT] pq_getmessage() receives SASL payload
    │       │   │   ├─ Untrusted: Full SASL token from client
    │       │   │   ├─ Max size: mech->max_message_length
    │       │   │   └─ For SCRAM: SCRAM_MAX_MESSAGE_LENGTH
    │       │   │
    │       │   ├─ [FIRST MESSAGE - INITIAL] pq_getmsgrawstring()
    │       │   │   ├─ Extracts: Selected mechanism name
    │       │   │   ├─ [TRANSFORM] scram_init()
    │       │   │   │   ├─ Inputs: Port, selected mechanism, shadow_pass
    │       │   │   │   ├─ Creates: scram_state with "doomed" flag if user not found
    │       │   │   │   ├─ Creates: Fake salt/iterations if doomed (timing attack mitigation)
    │       │   │   │   └─ Output: opaq state handle
    │       │   │   │
    │       │   │   ├─ [ENTRY POINT] pq_getmsgint() gets client-first message length
    │       │   │   │   ├─ Untrusted: Length value (int32)
    │       │   │   │   └─ Can be -1 (no initial response) or actual length
    │       │   │   │
    │       │   │   └─ [ENTRY POINT] pq_getmsgbytes() receives client-first message
    │       │   │       ├─ Untrusted: Client-first message bytes
    │       │   │       ├─ Format: gs2-header (channel binding) + client-first-bare
    │       │   │       │          = "[y|n|p=type],,[username=...,[authzid=...],nonce=...,"
    │       │   │       │            "reserved-mext=...,client-ext=...]"
    │       │   │       ├─ Parsed: Username claim, nonce, extensions
    │       │   │       └─ Note: Username from SASL is ignored (uses port->user_name instead)
    │       │   │
    │       │   ├─ [SUBSEQUENT MESSAGES]
    │       │   │   └─ [ENTRY POINT] pq_getmsgbytes() receives client-final message
    │       │   │       ├─ Untrusted: Client-final message bytes
    │       │   │       ├─ Format: channel-binding-input, nonce, proof, extensions
    │       │   │       └─ Parsed: Client nonce, channel binding, client proof
    │       │   │
    │       │   ├─ [TRANSFORM] mech->exchange() = scram_exchange()
    │       │   │   ├─ STAGE 1 (client-first):
    │       │   │   │   ├─ Parses: Client-first message
    │       │   │   │   ├─ Validates: Nonce format (printable ASCII, no comma)
    │       │   │   │   ├─ Validates: Channel binding request (tls-server-end-point)
    │       │   │   │   ├─ Generates: Server nonce (client nonce + random suffix)
    │       │   │   │   ├─ Prepares: Server-first message with salt, iterations
    │       │   │   │   └─ Output: server-first message, continue flag
    │       │   │   │
    │       │   │   ├─ STAGE 2 (client-final):
    │       │   │   │   ├─ [TRANSFORM] Verifies channel binding (if TLS, check tls-server-end-point)
    │       │   │   │   ├─ [TRANSFORM] Nonce validation (server_nonce == client_nonce + server_suffix)
    │       │   │   │   ├─ [TRANSFORM] SASLprep(password, shadow_pass) or raw bytes
    │       │   │   │   │   ├─ Inputs: Plaintext password from FIRST message, stored secret
    │       │   │   │   │   ├─ Applies: UTF-8 validation, SASLprep normalization
    │       │   │   │   │   ├─ If invalid UTF-8: Use raw bytes instead
    │       │   │   │   │   └─ Note: Password never sent over wire in SCRAM
    │       │   │   │   │
    │       │   │   │   ├─ [TRANSFORM] HMAC-SHA-256(SaltedPassword, "Client Key")
    │       │   │   │   │   ├─ SaltedPassword = PBKDF2(password, salt, iterations)
    │       │   │   │   │   ├─ ClientKey = HMAC-SHA-256(SaltedPassword, "Client Key")
    │       │   │   │   │   ├─ ClientSignature = HMAC-SHA-256(StoredKey, AuthMessage)
    │       │   │   │   │   ├─ ProofVerify = ClientProof XOR ClientSignature
    │       │   │   │   │   └─ Compare ProofVerify with original ClientKey
    │       │   │   │   │
    │       │   │   │   ├─ [TRANSFORM] On success: Compute ServerKey
    │       │   │   │   │   ├─ ServerKey = HMAC-SHA-256(SaltedPassword, "Server Key")
    │       │   │   │   │   ├─ ServerSignature = HMAC-SHA-256(ServerKey, AuthMessage)
    │       │   │   │   │   └─ Return in server-final message
    │       │   │   │   │
    │       │   │   │   └─ Output: STATUS_OK or STATUS_ERROR, server-final message
    │       │   │   │
    │       │   │   └─ Error handling: If doomed flag set, still send server messages but fail at end
    │       │   │       (timing attack mitigation: doesn't reveal user existence)
    │       │   │
    │       │   ├─ [SINK] sendAuthRequest()
    │       │   │   ├─ AUTH_REQ_SASL_CONT: Send server message, loop continues
    │       │   │   └─ AUTH_REQ_SASL_FIN: Send final server message, exchange done
    │       │   │
    │       │   └─ Loop exits on: PG_SASL_EXCHANGE_SUCCESS or PG_SASL_EXCHANGE_FAILURE
    │       │
    │       └─ [SINK] set_authn_id() and success path
    │
    └─ All paths: Auth success or auth_failed()
```

**Dependency Chain**: ProcessStartupPacket → BackendMain → InitPostgres → PerformAuthentication → ClientAuthentication → CheckPWChallengeAuth → get_role_password → (CheckMD5Auth OR CheckSASLAuth with SCRAM) → password verification → set_authn_id → InitializeSessionUserId

---

### Flow 3: HBA Configuration Matching Pipeline

```
[LOADING PHASE - At Server Startup/Reload]
load_hba()
    ├─ open_auth_file(HbaFileName) reads pg_hba.conf from disk
    ├─ [TRANSFORM] tokenize_auth_file()
    │   ├─ Reads: Raw file lines
    │   ├─ Parses: Tokenizes each line (whitespace/comma separated)
    │   ├─ Stores: TokenizedAuthLine list with line numbers
    │   └─ Output: List of tokens (not validated yet)
    │
    ├─ [TRANSFORM] parse_hba_line() for each token list
    │   ├─ Validates: Connection type (local, host, hostssl, hostnossl, hostgss, hostnogss)
    │   ├─ Parses: Database names (list or "all")
    │   ├─ Parses: User names (list, regex with +, or "all")
    │   ├─ Parses: Address (CIDR, hostname, or "all")
    │   ├─ Parses: Authentication method (trust, reject, password, md5, scram-sha-256, etc.)
    │   ├─ Parses: Options (clientcert=verify-full, etc.)
    │   ├─ Validates: CIDR/hostname format
    │   ├─ Regex compilation: If regex user entry ("+name"), compile for later matching
    │   └─ Output: HbaLine structure
    │
    ├─ [STORE] Replace parsed_hba_lines global with new configuration
    ├─ [STORE] parsed_hba_context holds memory for all parsed rules
    └─ Output: parsed_hba_lines list ready for matching

[MATCHING PHASE - During Each Connection Authentication]
check_hba(port)
    ├─ [TRANSFORM] get_role_oid(port->user_name, true)
    │   ├─ Untrusted Input: port->user_name from client startup packet
    │   ├─ Query: SearchSysCache(AUTHNAME, username) — catalog lookup
    │   ├─ Output: Role OID or InvalidOid if not found
    │   └─ Note: Does not error on non-existent user (passes doomed flag)
    │
    ├─ foreach(line, parsed_hba_lines)
    │   │
    │   ├─ Connection type check
    │   │   ├─ ctLocal: Match only if AF_UNIX socket
    │   │   ├─ ctHost/ctHostSSL/ctHostNoSSL: Match TCP based on SSL state
    │   │   └─ ctHostGSS/ctHostNoGSS: Match based on GSSAPI encryption state
    │   │
    │   ├─ SSL state check
    │   │   └─ Skip if rule requires SSL but connection not SSL (or vice versa)
    │   │
    │   ├─ GSSAPI encryption state check
    │   │   └─ Skip if rule requires/forbids GSSAPI encryption
    │   │
    │   ├─ [TRANSFORM] IP address matching (4 methods)
    │   │   ├─ ipCmpMask (most common):
    │   │   │   ├─ If hostname in rule:
    │   │   │   │   ├─ [TRANSFORM] check_hostname(port, hba->hostname)
    │   │   │   │   │   ├─ Performs: Hostname lookup of client IP (reverse DNS)
    │   │   │   │   │   ├─ Matches: Against rule hostname with regex or literal
    │   │   │   │   │   ├─ Caches: Hostname resolution with TTL
    │   │   │   │   │   └─ Output: Match/no-match boolean
    │   │   │   │   └─ Continue if no match
    │   │   │   └─ Else (CIDR address):
    │   │   │       ├─ [TRANSFORM] check_ip(port->raddr, hba->addr, hba->mask)
    │   │   │       │   ├─ Compares: Client IP against CIDR block
    │   │   │       │   └─ Output: Match/no-match
    │   │   │       └─ Continue if no match
    │   │   │
    │   │   ├─ ipCmpAll: Always match any IP
    │   │   │
    │   │   └─ ipCmpSameHost/ipCmpSameNet: Compare client to server interfaces
    │   │       └─ [TRANSFORM] check_same_host_or_net(port->raddr)
    │   │
    │   ├─ [TRANSFORM] Database name matching
    │   │   └─ [TRANSFORM] check_db(port->database_name, port->user_name, roleid, hba->databases)
    │   │       ├─ Untrusted: port->database_name from startup packet
    │   │       ├─ Matches: Against "all" or list of allowed database names
    │   │       ├─ Note: "@include_file" expansion in database list
    │   │       └─ Output: Match/no-match
    │   │
    │   ├─ [TRANSFORM] User name matching
    │   │   └─ [TRANSFORM] check_role(port->user_name, roleid, hba->roles, false)
    │   │       ├─ Untrusted: port->user_name from startup packet
    │   │       ├─ Matches: Against "all", user list, or regex (if "+name")
    │   │       ├─ Regex matching: Matches role OID membership if regex is "+group_name"
    │   │       └─ Output: Match/no-match
    │   │
    │   └─ If all conditions match:
    │       ├─ port->hba = hba (matching rule found)
    │       └─ return (stop searching)
    │
    └─ If no match:
        ├─ Create implicit reject HbaLine
        ├─ port->hba = hba (implicit reject)
        └─ return
```

**Dependency Chain**: load_hba (at startup) → tokenize_auth_file → parse_hba_line → later: check_hba → get_role_oid + check_db + check_role + check_ip/check_hostname

---

## Vulnerability Analysis

### Vulnerability Class: **Authentication Bypass / Information Disclosure**

#### 1. User Existence Enumeration

**Location**: `src/backend/libpq/crypt.c:get_role_password()` and logs

**Mechanism**:
- `get_role_password()` returns different log messages for:
  - Non-existent users: "Role X does not exist"
  - Users with no password: "User X has no password assigned"
  - Expired passwords: "User X has an expired password"
  - Valid password: (password returned)
- These messages appear in server logs, and timing differences can occur

**Mitigation in SCRAM**: The SCRAM implementation uses a "doomed" flag (lines 73-74 in auth-scram.c comments) where fake salt/iterations are generated even if the user doesn't exist, and the exchange proceeds to completion before failing. This prevents timing attacks revealing user existence during the SCRAM exchange itself.

**Mitigation Gap**: Log messages still leak user existence if admin can read logs. The `logdetail` parameter is not sent to the client (good), but internal error codes/timing may differ.

#### 2. SCRAM Challenge Recovery (Offline Attack Surface)

**Location**: `src/backend/libpq/auth-scram.c`

**Mechanism**:
- The stored SCRAM secret contains:
  - Salt (transmitted to client in server-first-message)
  - Iteration count (transmitted to client in server-first-message)
  - StoredKey and ServerKey (not transmitted)
- Attacker with network access observes:
  - Salt + iterations + client-first-message + server-first-message + client-final-message (proof)
- Attacker can attempt offline brute-force:
  - Takes client proof and attempts to derive ClientKey via password guessing
  - For each guess: SaltedPassword = PBKDF2(guess, salt, iterations)
  - Computes: ClientKey = HMAC-SHA-256(SaltedPassword, "Client Key")
  - Hashes: StoredKey = SHA-256(ClientKey)
  - Checks if proof matches

**Existing Mitigations**:
1. Iteration count (default 4096, configurable) increases brute-force cost
2. Strong salt (random 16 bytes) prevents rainbow tables
3. TLS encryption (when used) prevents offline capture
4. SASLprep normalization (if valid UTF-8) increases entropy

**Limitations**:
- Plaintext connections transmit everything unencrypted (if "password" auth used)
- Iteration count stored in server-first-message (attacker knows exact cost)

#### 3. MD5 Authentication Weaknesses

**Location**: `src/backend/libpq/auth.c:CheckMD5Auth()` and `src/backend/libpq/crypt.c:md5_crypt_verify()`

**Mechanism**:
- Client-side hash: `MD5(MD5(password + username) + server_salt)`
- Server verifies: Recomputes expected hash and compares
- Server salt: Only 4 bytes, generated per connection (good)
- Stored password: "md5" prefix + 32-char hex (MD5 of password + username)

**Weaknesses**:
1. MD5 is cryptographically broken
2. Client can brute-force without seeing stored password (offline attack on captured packets)
3. Server salt only 4 bytes (28 bits entropy) — weak for limiting precomputed tables

**Mitigations Noted**: Deprecation warnings logged when MD5 password found (crypt.c:28)

#### 4. Plaintext Password Transmission

**Location**: `src/backend/libpq/auth.c:CheckPasswordAuth()` and `recv_password_packet()`

**Mechanism**:
- Client sends password in plaintext in password message (0x70)
- Should only be used over SSL (documented recommendation)
- Server compares against hash (MD5 or SCRAM-SHA-256)

**Mitigations**:
- Documentation recommends SSL-only
- No code-level enforcement (reliant on HBA configuration)
- Captured passwords can be directly tested against stored hashes

**Vulnerability**: If not over TLS, network attacker sees plaintext password.

---

### Vulnerability Class: **Logical/State Issues**

#### 5. HBA Regex Denial of Service

**Location**: `src/backend/libpq/hba.c:parse_hba_line()` and `check_role()`

**Mechanism**:
- User entries in pg_hba.conf can use regex patterns: `+name` for role membership
- Regex patterns compiled at startup: `pg_regcomp()` in hba.c
- At connection time, regex checked against username: `pg_regexec()`
- Malicious HBA config with catastrophic backtracking regex could:
  - Block all new connections (matching phase times out)
  - All connections wait for hba_getauthmethod() to timeout

**Mitigations**:
- Regex compilation happens once at startup (not per-connection)
- Only administrators can modify pg_hba.conf
- Timeout enforced by StartupPacketTimeoutHandler (src/backend/tcop/backend_startup.c:66)

**Risk**: Low (admin-controlled input), but affects availability.

#### 6. Startup Packet Buffer Overflow Risk (Mitigated)

**Location**: `src/backend/tcop/backend_startup.c:ProcessStartupPacket()`

**Mechanism**:
- Startup packet length validated (lines 535-542):
  - Check: `len < sizeof(ProtocolVersion)` — minimum size
  - Check: `len > MAX_STARTUP_PACKET_LENGTH` — maximum size (8 KB)
- Buffer allocated: `palloc(len + 1)` (line 549)
- Extra byte zeroed for null-termination (line 550)
- All strings guaranteed null-terminated due to extra zero byte

**Mitigations**:
1. Length validation enforced
2. Heap allocator (palloc) used, not stack
3. Excess byte for null-termination
4. Username/database truncated to NAMEDATALEN (line 840-843)

**Status**: Properly mitigated.

#### 7. Command-Line Options Injection

**Location**: `src/backend/tcop/backend_startup.c:ProcessStartupPacket()` (line 750-751)

**Mechanism**:
- Client can supply arbitrary "options" in startup packet
- Stored in `port->cmdline_options`
- Later applied as GUC settings during InitPostgres

**Potential Issues**:
- Options set before authentication completes?
- Could set `search_path` to inject code?

**Status**: Requires deeper analysis into when GUC options are applied relative to role initialization and authentication completion. Likely mitigated by applying GUCs in separate phase, but worth checking.

---

### Vulnerability Class: **Information Disclosure**

#### 8. Error Message Leakage to Client

**Location**: `src/backend/libpq/auth.c:auth_failed()` (line 48, referenced at 669)

**Mechanism**:
- `logdetail` strings contain information like:
  - "Password does not match for user X"
  - "User X does not exist"
- Should not be sent to client (ereport uses ERROR, which the code should not expose)
- Protected by: Error handling sends generic message to client, detail to logs

**Status**: Appears mitigated, but requires checking ErrorResponse protocol behavior.

#### 9. Hostname Reverse-DNS Side Channel

**Location**: `src/backend/libpq/hba.c:check_hostname()`

**Mechanism**:
- If HBA rule uses hostname (not CIDR), server performs reverse DNS lookup
- Attacker can observe timing of:
  - Failed hostname lookup (unresolvable IP)
  - Successful but non-matching hostname
  - Successful and matching hostname
- Could leak information about server's network position

**Mitigations**: Caching to reduce variability (but cache still depends on first lookup)

---

## Summary of Security Properties

### Strong Protections Implemented

1. **SCRAM-SHA-256 Default**: Modern cryptographic authentication with proper key derivation (PBKDF2 with configurable iterations)
2. **Timing Attack Mitigation**: "Doomed" flag in SCRAM ensures failed auth takes same time as successful (masks user enumeration)
3. **Channel Binding**: SCRAM supports tls-server-end-point binding to prevent MITM
4. **Proper Salt Generation**: `pg_strong_random()` used for all salts/nonces
5. **Length Validation**: Startup packet length validated; strings truncated safely
6. **No Stack Buffers**: Dynamic allocation for potentially unbounded input (startup packet)
7. **Logdetail Separation**: Error details logged server-side only, not sent to client
8. **HBA Flexibility**: Per-connection auth method selection based on IP/user/database

### Known Weaknesses

1. **MD5 Authentication**: Still supported, cryptographically broken
2. **Plaintext Passwords**: Allowed on unencrypted connections (relies on HBA config to enforce TLS)
3. **Log File Leakage**: User existence can be determined from logs
4. **Startup Packet Options**: GUC options set before role verification (scope needs clarification)

### Critical Data Flows

1. **Untrusted Input → HBA Match → Auth Method**: User/database from startup packet used for HBA matching; uses role OID lookup for regex matching
2. **Untrusted Input → Password Verification**: User/database/password all from client; verified against pg_authid catalog
3. **Auth Success → Session Globals**: On success, authenticated identity set in MyClientConnectionInfo

---

## Files in Attack Surface

### Critical Authentication Files (9)
- `src/backend/libpq/auth.c` — Auth dispatcher, plaintext/challenge auth
- `src/backend/libpq/auth-sasl.c` — SASL framework
- `src/backend/libpq/auth-scram.c` — SCRAM-SHA-256 mechanism
- `src/backend/libpq/auth-oauth.c` — OAuth SASL mechanism
- `src/backend/libpq/crypt.c` — Password hash verification
- `src/backend/libpq/hba.c` — HBA parsing and matching
- `src/backend/tcop/backend_startup.c` — Startup packet parsing
- `src/backend/postmaster/postmaster.c` — TCP acceptance
- `src/backend/libpq/pqcomm.c` — Message I/O

### Supporting Files (4)
- `src/backend/libpq/pqformat.c` — Protocol message formatting
- `src/backend/libpq/be-secure.c` — SSL/TLS setup
- `src/backend/libpq/be-secure-gssapi.c` — GSSAPI encryption
- `src/backend/libpq/ifaddr.c` — Network interface utilities

---

## Recommendations

1. **Deprecate MD5 Authentication**: Consider removing in future version; migrate users to SCRAM-SHA-256
2. **Increase MD5 Salt Size**: If kept, increase 4-byte salt to 16 bytes for SCRAM parity
3. **Enforce TLS for Non-SCRAM Auth**: Add code-level check (not just config) for plaintext password over unencrypted connections
4. **Audit GUC Options Timing**: Verify `options` from startup packet are not applied before role verification
5. **Minimize Log Information**: Consider adding option to reduce user-existence leakage in logs
6. **SCRAM Iteration Count Hardening**: Consider increasing default from 4096 iterations (match or exceed OWASP recommendations)

