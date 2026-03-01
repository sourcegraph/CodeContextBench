# Apache Kafka SASL Authentication Flow Security Analysis

## Files Examined

### Core Entry Points
- `clients/src/main/java/org/apache/kafka/common/network/ChannelBuilders.java` — Factory for creating channel builders
- `clients/src/main/java/org/apache/kafka/common/network/SaslChannelBuilder.java` — SASL channel builder that instantiates authenticators

### SASL Authenticators
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/SaslServerAuthenticator.java` — Server-side SASL state machine that processes SASL handshakes and token exchanges
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/SaslClientAuthenticator.java` — Client-side SASL state machine

### PLAIN Mechanism
- `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainSaslServer.java` — RFC 4616 PLAIN mechanism implementation
- `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainServerCallbackHandler.java` — Credential lookup for PLAIN

### SCRAM Mechanism
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramSaslServer.java` — RFC 5802 SCRAM mechanism implementation
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramServerCallbackHandler.java` — Credential lookup for SCRAM
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramMessages.java` — SCRAM message parsing (ClientFirstMessage, ServerFirstMessage, ClientFinalMessage, ServerFinalMessage)

### OAuth Bearer Mechanism
- `clients/src/main/java/org/apache/kafka/common/security/oauthbearer/internals/unsecured/OAuthBearerUnsecuredValidatorCallbackHandler.java` — OAuth Bearer token validation

### Principal & Authorization
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/DefaultKafkaPrincipalBuilder.java` — Extracts KafkaPrincipal from authenticated context
- `clients/src/main/java/org/apache/kafka/common/security/auth/KafkaPrincipal.java` — Principal representation
- `clients/src/main/java/org/apache/kafka/server/authorizer/Authorizer.java` — Authorization interface for ACL enforcement

### Supporting Components
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/CredentialCache.java` — Server-side credential cache
- `clients/src/main/java/org/apache/kafka/common/security/JaasContext.java` — JAAS configuration context
- `clients/src/main/java/org/apache/kafka/common/security/auth/SaslAuthenticationContext.java` — Context passed to principal builder

---

## Entry Points

### 1. ChannelBuilders.serverChannelBuilder()
**Location:** `clients/src/main/java/org/apache/kafka/common/network/ChannelBuilders.java:96`

**Untrusted Input:** Configuration parameters, enabled SASL mechanisms, credential stores

**Role:** Factory method that creates `SaslChannelBuilder` for server-side connections. Loads JAAS contexts for all enabled mechanisms and creates credential/token caches.

### 2. ChannelBuilders.clientChannelBuilder()
**Location:** `clients/src/main/java/org/apache/kafka/common/network/ChannelBuilders.java:64`

**Untrusted Input:** SASL mechanism specified by client configuration

**Role:** Factory for client-side channel builders with specific SASL mechanism.

### 3. SaslChannelBuilder.buildChannel()
**Location:** `clients/src/main/java/org/apache/kafka/common/network/SaslChannelBuilder.java:215`

**Untrusted Input:** SelectionKey from socket, initiating network connection

**Role:** Creates KafkaChannel with SaslServerAuthenticator or SaslClientAuthenticator suppliers.

### 4. SaslServerAuthenticator.authenticate()
**Location:** `clients/src/main/java/org/apache/kafka/common/security/authenticator/SaslServerAuthenticator.java:250`

**Untrusted Input:** Raw bytes from network socket (`netInBuffer.readFrom(transportLayer)`)

**Role:** State machine that processes initial SASL handshake requests and SASL tokens from clients. Accepts:
- ApiVersionsRequest (untrusted header and version info)
- SaslHandshakeRequest (mechanism name as untrusted string)
- SaslAuthenticateRequest (SASL token bytes)

### 5. PlainSaslServer.evaluateResponse()
**Location:** `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainSaslServer.java:71`

**Untrusted Input:** PLAIN SASL response bytes `[authzid]\0authcid\0passwd`

**Role:** Parses and validates PLAIN credentials. Extracts username and password, invokes callback handler.

### 6. ScramSaslServer.evaluateResponse()
**Location:** `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramSaslServer.java:96`

**Untrusted Input:** SCRAM message bytes (ClientFirstMessage or ClientFinalMessage)

**Role:** Parses SCRAM protocol messages via regex patterns in ScramMessages.ClientFirstMessage and ScramMessages.ClientFinalMessage.

### 7. ScramMessages.ClientFirstMessage constructor
**Location:** `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramMessages.java:81`

**Untrusted Input:** Raw SCRAM client first message bytes

**Role:** Parses SCRAM client first message using regex pattern. Extracts saslName, nonce, authorizationId, and extensions.

---

## Data Flow

### Flow 1: PLAIN Mechanism Authentication

**1. Source:** `SaslServerAuthenticator.authenticate()` at line 264
   - Raw network bytes received via `netInBuffer.readFrom(transportLayer)`
   - Entire payload extracted as `clientToken = netInBuffer.payload()`

**2. Transform - SASL Token Processing:** `SaslServerAuthenticator.handleSaslToken()` at line 421
   - If not using SaslAuthenticateHeaders: passes `clientToken` directly to `saslServer.evaluateResponse(clientToken)`
   - If using SaslAuthenticateHeaders: parses RequestHeader, extracts SaslAuthenticateRequest, extracts `authBytes()` field

**3. Transform - PLAIN Parsing:** `PlainSaslServer.evaluateResponse()` at line 71
   - Input: raw SASL bytes representing `[authzid]\0authcid\0passwd`
   - Converts bytes to UTF-8 string: `new String(responseBytes, StandardCharsets.UTF_8)`
   - Calls `extractTokens(response)` using indexOf("\u0000") to split on NUL bytes
   - **VALIDATION:** Checks tokens not empty (lines 91-96)
   - Extracts 3 fields: authorizationId, username, password

**4. Transform - Credential Verification:** `PlainServerCallbackHandler.authenticate()` at line 61
   - JAAS lookup via `JaasContext.configEntryOption()` for key `user_<username>`
   - Expected password retrieved from JAAS config
   - Constant-time comparison: `Utils.isEqualConstantTime(password, expectedPassword.toCharArray())`

**5. Sink - Principal Extraction:** `DefaultKafkaPrincipalBuilder.build()` at line 84
   - For non-GSSAPI mechanisms: `new KafkaPrincipal(KafkaPrincipal.USER_TYPE, saslServer.getAuthorizationID())`
   - Directly uses username from PLAIN mechanism as principal name

**6. Sink - Authorization:** `Authorizer.authorize()` (interface at line 107)
   - KafkaPrincipal used to query ACL bindings for resource and operation
   - Returns `AuthorizationResult.ALLOWED` or `DENIED`

---

### Flow 2: SCRAM Mechanism Authentication

**1. Source:** `SaslServerAuthenticator.authenticate()` at line 264
   - Raw network bytes via `netInBuffer.readFrom(transportLayer)`

**2. Transform - SASL Request Parsing:** `SaslServerAuthenticator.handleSaslToken()` at line 421
   - Extracts SaslAuthenticateRequest and calls `saslServer.evaluateResponse(clientToken)` where `clientToken = requestData.authBytes()`

**3. Transform - SCRAM ClientFirstMessage Parsing:** `ScramSaslServer.evaluateResponse()` at line 96-100
   - Creates `ClientFirstMessage clientFirstMessage = new ClientFirstMessage(response)` where response is raw SCRAM bytes

**4. Transform - SCRAM Message Validation:** `ScramMessages.ClientFirstMessage` constructor at line 81
   - **CRITICAL REGEX PARSING:** Uses Pattern.compile() with regex pattern (lines 68-74):
     ```
     n,(a=(?<authzid>%s))?,%sn=(?<saslname>%s),r=(?<nonce>%s)(?<extensions>%s)
     ```
   - Regex substitutions use constants: SASLNAME, RESERVED, PRINTABLE, EXTENSIONS
   - Pattern matches structure but doesn't validate all semantic requirements
   - **VALIDATION:** Pattern must match or throws `SaslException`
   - Extracts authzid (optional), saslName, nonce, extensions from regex groups

**5. Transform - Credential Lookup:** `ScramSaslServer.evaluateResponse()` at line 107-126
   - Extracts username from saslName: `String username = ScramFormatter.username(saslName)`
   - Creates NameCallback with username
   - Calls callback handler: `callbackHandler.handle(new Callback[]{nameCallback, credentialCallback})`
   - Callback handler retrieves credential from cache: `credentialCache.get(username)`

**6. Transform - Credential Verification:** `ScramSaslServer.evaluateResponse()` at line 147-170
   - Parses `ClientFinalMessage clientFinalMessage = new ClientFinalMessage(response)`
   - Verifies nonce matches: `clientFinalMessage.nonce().equals(serverFirstMessage.nonce())`
   - Computes client proof: HMAC-based proof verification
   - **VALIDATION:** Checks proof matches expected value

**7. Sink - Principal Extraction:** `DefaultKafkaPrincipalBuilder.build()` at line 84
   - `new KafkaPrincipal(KafkaPrincipal.USER_TYPE, saslServer.getAuthorizationID())`
   - Calls `saslServer.getAuthorizationID()` which returns SCRAM username

**8. Sink - Authorization:** Same as PLAIN (Flow 1, step 6)

---

### Flow 3: OAuth Bearer Mechanism Authentication

**1. Source:** `SaslServerAuthenticator.authenticate()` at line 264
   - Raw OAuth Bearer SASL bytes from network

**2. Transform - Token Extraction:** OAuth Bearer protocol (implicit in mechanism)
   - Client sends JWT or token bytes

**3. Transform - Token Validation:** `OAuthBearerUnsecuredValidatorCallbackHandler.handle()`
   - Parses JWT claims
   - Validates expiration time claim "exp"
   - Validates optional "iat" (issued at) and "nbf" (not before) claims
   - Extracts principal from configured claim (default "sub")
   - **VALIDATION:** Token structure and claims validation

**4. Sink - Principal Extraction:** Principal extracted from JWT "sub" claim

**5. Sink - Authorization:** Same as other mechanisms

---

### Flow 4: GSSAPI/Kerberos Mechanism Authentication

**1. Source:** `SaslServerAuthenticator.authenticate()` at line 264
   - Raw Kerberos SASL bytes from network (AP-REQ token)

**2. Transform - Kerberos Server Creation:** `SaslServerAuthenticator.createSaslKerberosServer()` at line 219
   - Extracts service principal from server Subject
   - Calls `Sasl.createSaslServer(saslMechanism, servicePrincipalName, serviceHostname, ...)`
   - Delegates to JGSS implementation

**3. Transform - Token Evaluation:** JGSS processes AP-REQ token
   - Validates Kerberos token structure and cryptographic properties
   - Extracts client principal from token

**4. Transform - Principal Name Transformation:** `DefaultKafkaPrincipalBuilder.applyKerberosShortNamer()` at line 90
   - Parses authorization ID via `KerberosName.parse(authorizationId)`
   - Applies short name transformation rules: `kerberosShortNamer.shortName(kerberosName)`
   - Returns transformed principal

**5. Sink - Authorization:** Same as other mechanisms

---

## Dependency Chain

### PLAIN Mechanism Chain
1. `SaslServerAuthenticator.authenticate()` [untrusted bytes enter here]
2. `SaslServerAuthenticator.handleSaslToken()`
3. `PlainSaslServer.evaluateResponse()` [PLAIN-specific parsing]
4. `PlainSaslServer.extractTokens()` [splits on NUL byte]
5. `PlainServerCallbackHandler.authenticate()` [credential verification]
6. `JaasContext.configEntryOption()` [credential lookup]
7. `DefaultKafkaPrincipalBuilder.build()` [principal creation]
8. `Authorizer.authorize()` [ACL enforcement]

### SCRAM Mechanism Chain
1. `SaslServerAuthenticator.authenticate()` [untrusted bytes enter here]
2. `SaslServerAuthenticator.handleSaslToken()`
3. `ScramSaslServer.evaluateResponse()` [SCRAM state machine]
4. `ScramMessages.ClientFirstMessage()` [regex parsing of client first message]
5. `ScramMessages.ClientFirstMessage.saslName()` [username extraction]
6. `ScramServerCallbackHandler.handle()` [credential lookup from cache]
7. `ScramSaslServer.evaluateResponse()` [proof verification - continued]
8. `DefaultKafkaPrincipalBuilder.build()` [principal creation]
9. `Authorizer.authorize()` [ACL enforcement]

### OAuth Bearer Mechanism Chain
1. `SaslServerAuthenticator.authenticate()` [untrusted bytes enter]
2. `SaslServerAuthenticator.handleSaslToken()`
3. `OAuthBearerSaslServer` [implicit OAuth Bearer mechanism]
4. `OAuthBearerUnsecuredValidatorCallbackHandler.handle()` [JWT validation]
5. `DefaultKafkaPrincipalBuilder.build()` [principal creation]
6. `Authorizer.authorize()` [ACL enforcement]

### GSSAPI Mechanism Chain
1. `SaslServerAuthenticator.authenticate()` [untrusted Kerberos token enters]
2. `SaslServerAuthenticator.handleSaslToken()`
3. `SaslServerAuthenticator.createSaslKerberosServer()` [JGSS delegation]
4. JGSS library (javax.security.sasl.Sasl) [Kerberos token validation]
5. `DefaultKafkaPrincipalBuilder.applyKerberosShortNamer()` [name transformation]
6. `Authorizer.authorize()` [ACL enforcement]

---

## Analysis

### Vulnerability Class: SASL Data Injection and Parsing

**Description:** The SASL subsystem accepts untrusted client data from network sockets and processes it through multiple parsing layers with varying validation rigor. The data flow spans from raw network bytes through mechanism-specific parsers to credential verification and principal extraction.

### Mechanism-Specific Security Properties

#### PLAIN Mechanism Security Analysis

**Strengths:**
- Credentials validated with constant-time comparison (`Utils.isEqualConstantTime()`)
- Simple, transparent parsing via NUL-byte splitting
- No cryptographic operations prone to timing attacks on credential matching

**Weaknesses:**
- Credentials stored in plaintext in JAAS configuration
- No salting or hashing of passwords
- Sensitive to JAAS config disclosure
- Authorization ID extraction directly from network data without validation of cross-principal authorization requests
- Line 107-108 checks if authzid != username, but doesn't prevent username spoofing attacks if callback handler misconfigured

**Attack Scenarios:**
1. **JAAS Config Disclosure:** If JAAS configuration file is readable, all PLAIN passwords exposed
2. **Username Enumeration:** `PlainServerCallbackHandler.authenticate()` returns false for both missing user and wrong password, limiting enumeration
3. **Authorization ID Bypass:** Client can request different authzid; server only rejects if authzid != username, so cannot assume principal from username alone

**Existing Mitigations:**
- Constant-time password comparison prevents timing attacks
- UTF-8 validation implicit in String constructor
- Empty username/password checks (lines 91-96)

**Gaps:**
- JAAS configuration must be protected at OS level (file permissions)
- No rate limiting on failed authentication attempts
- No protection against credential extraction from memory

---

#### SCRAM Mechanism Security Analysis

**Strengths:**
- Passwords stored as salted PBKDF2 hashes, not plaintext
- Challenge-response protocol prevents plaintext transmission
- Nonce validation prevents replay attacks (`clientFinalMessage.nonce().equals(serverFirstMessage.nonce())`)
- Proof verification using HMAC prevents tampering
- Iteration count configurable and enforced (line 133-134: `mechanism.minIterations()`)

**Weaknesses:**
- Regex parsing in `ScramMessages.ClientFirstMessage` is complex:
  - Pattern: `n,(a=(?<authzid>%s))?,%sn=(?<saslname>%s),r=(?<nonce>%s)(?<extensions>%s)`
  - SASLNAME constant includes Unicode escapes that may behave unexpectedly
  - SCRAM extension parsing not fully validated
  - No explicit validation of username format after regex extraction
- Username extraction via `ScramFormatter.username(saslName)` performs encoding/decoding; potential for inconsistency
- Credential cache lookup (`credentialCache.get(username)`) vulnerable to cache poisoning if cache not properly isolated
- Re-authentication allows principal to change hands if callback handler misconfigured

**Attack Scenarios:**
1. **Regex-Based Bypass:** Malformed SCRAM message crafted to match regex pattern but violate RFC 5802 semantics could bypass validation (though subsequent crypto verification would catch most)
2. **Extension Injection:** SCRAM extensions parsed but potentially ignored, allowing man-in-the-middle to inject extensions
3. **Nonce Collision:** Attacker sends ClientFinalMessage with fabricated nonce; nonce comparison at line 150 would fail, but no attempt to exploit this alone

**Existing Mitigations:**
- Regex pattern matching provides basic format validation
- Cryptographic proof verification (HMAC-SHA256 or HMAC-SHA512) ensures client knows password
- Nonce provided by server prevents predictability

**Gaps:**
- SCRAM extensions (token authentication) are parsed but not fully validated in all cases
- No validation that username in SCRAM matches username in callback handler response
- Dictionary lookup of credential via username vulnerable to user enumeration if timing varies
- No rate limiting on failed attempts

---

#### OAuth Bearer Mechanism Security Analysis

**Strengths:**
- Token validation includes signature verification (in secured mode)
- Expiration time validation prevents use of expired tokens
- Clock skew allowance (`unsecuredValidatorAllowableClockSkewMs`) prevents clock synchronization issues

**Weaknesses:**
- Default implementation (`OAuthBearerUnsecuredValidatorCallbackHandler`) uses **unsecured/unencrypted JWT tokens** without signature verification
- No built-in token revocation mechanism
- Principal extracted from JWT claim without broker-side verification of token issuer
- Extensions parsed but potentially not validated

**Attack Scenarios:**
1. **Unsecured Token Forgery:** In default unsecured mode, attacker can craft any JWT with any claims and use it for authentication
2. **Token Tampering:** Unsecured mode provides no cryptographic guarantee token hasn't been modified
3. **Missing Token Validation:** If custom validator misconfigured, arbitrary claims could be trusted

**Existing Mitigations:**
- Expiration validation in `OAuthBearerUnsecuredValidatorCallbackHandler`
- Clock skew tolerance prevents edge cases
- Documentation states unsecured mode not suitable for production

**Gaps:**
- Default implementation extremely permissive (intended for development only, but risks production use)
- No built-in rate limiting on token validation
- Extension validation deferred to implementation-specific code

---

#### GSSAPI/Kerberos Mechanism Security Analysis

**Strengths:**
- Delegates to Java GSS/JGSS, which provides cryptographic validation of Kerberos tokens
- Token includes authentication timestamp and client principal
- Mutual authentication available (server validates client, client can validate server)
- Principal name transformation via `KerberosShortNamer` provides flexibility

**Weaknesses:**
- JGSS complexity makes local auditing difficult
- Service principal must be in Subject; extraction is basic string parsing without validation
- Name transformation rules (`principalToLocalRules`) can be misconfigured, leading to principal spoofing
- No validation that Kerberos token and SASL mechanism match
- Kerberos infrastructure security depends on external KDC

**Attack Scenarios:**
1. **Short Name Collision:** If short name transformation rules misconfigured, two different Kerberos principals could map to same username
2. **Service Principal Mismatch:** If service principal in code doesn't match Kerberos database, authentication fails silently
3. **Token Replay:** If JGSS replay detection disabled (configuration), tokens could be replayed

**Existing Mitigations:**
- JGSS cryptographic validation prevents token forgery
- Token contains timestamp (prevents old token reuse in mutual auth scenarios)
- Principal name mapping logged for audit

**Gaps:**
- JAAS KerberosLogin configuration required; no validation of krb5.conf consistency
- No built-in rate limiting
- KDC communication network security depends on infrastructure

---

### Cross-Mechanism Vulnerabilities

#### 1. Principal Extraction Path (`SaslServerAuthenticator.principal()` at line 307)

**Issue:** Principal built via `principalBuilder.build(context)` without validation that context actually corresponds to authenticated client.

**Analysis:**
- `DefaultKafkaPrincipalBuilder.build()` extracts authorization ID from `saslServer.getAuthorizationID()`
- No validation that this authorization ID was cryptographically verified
- If callback handler misconfigured or returns wrong value, principal will be wrong
- Authorization decisions made with incorrect principal

**Mitigation Gaps:**
- No assertion that SASL authentication completed successfully before principal extraction
- No principal format validation (could contain special characters, very long names)

#### 2. Re-authentication Mechanism (`SaslServerAuthenticator.reauthenticate()` at line 343)

**Issue:** Re-authentication creates new SaslServer but must verify principal unchanged.

**Analysis:**
- `reauthInfo.ensurePrincipalUnchanged()` at line 427 and 464 validates re-authentication principal matches original
- If re-authentication uses different mechanism, new principal could be different
- Server blocks this at line 532: `if (!reauthInfo.reauthenticating() || reauthInfo.saslMechanismUnchanged(clientMechanism))`
- But if callback handler returns different principal for same username, check passes

**Mitigation Gaps:**
- No validation of callback handler consistency across re-authentications
- Mechanism restriction enforced only by code, not cryptographically

#### 3. Callback Handler Interface (`AuthenticateCallbackHandler.handle()`)

**Issue:** Callback handler is untrusted code (potentially user-provided).

**Analysis:**
- Each mechanism delegates credential verification to callback handler
- PLAIN: `PlainServerCallbackHandler` hardcoded; looks up in JAAS config
- SCRAM: `ScramServerCallbackHandler` looks up in `credentialCache`
- OAuth Bearer: `OAuthBearerUnsecuredValidatorCallbackHandler` default
- GSSAPI: Generic `SaslServerCallbackHandler` default
- Custom handler can be configured via `sasl.server.callback.handler.class` config
- No validation of returned credentials

**Mitigation Gaps:**
- Custom handler could return any principal
- No type checking on credential returned
- No validation that username matches callback request

#### 4. Credential Cache Isolation (`SaslChannelBuilder.configure()` at line 145)

**Issue:** Single `CredentialCache` shared across all connections and mechanisms.

**Analysis:**
- `credentialCache` passed to all SCRAM mechanisms (line 329)
- Cache must be thread-safe and isolated per mechanism
- If cache implementation leaks across mechanisms or users, credentials could be accessed inappropriately

**Mitigation Gaps:**
- Cache implementation details not audited
- No per-connection cache isolation for PLAIN (uses JAAS config directly)

---

### SASL Handshake Protocol Vulnerabilities

#### Mechanism Negotiation (`SaslServerAuthenticator.handleHandshakeRequest()` at line 549)

**Issue:** Client specifies SASL mechanism, server validates against enabled mechanisms.

**Analysis:**
- Client sends `SaslHandshakeRequest` with mechanism name (line 550)
- Server checks `enabledMechanisms.contains(clientMechanism)` (line 554)
- If mechanism not enabled, returns error with list of enabled mechanisms
- But error message reveals all supported mechanisms to unauthenticated clients
- Information disclosure: attackers learn what authentication methods are available

**Scenario:** Attacker learns system supports PLAIN and SCRAM; focuses attacks on weaker PLAIN mechanism

**Mitigation Gaps:**
- No rate limiting on mechanism probing
- Enabled mechanisms revealed in error response

#### Early ApiVersions Request (`SaslServerAuthenticator.handleApiVersionsRequest()` at line 572)

**Issue:** Client can probe server capabilities before authentication.

**Analysis:**
- Accepts `ApiVersionsRequest` in `HANDSHAKE_OR_VERSIONS_REQUEST` state (line 573)
- Registers client information (line 581) before authentication
- Returns `ApiVersionsResponse` (line 583) which could leak version information
- No authentication required to probe API versions

**Mitigation Gaps:**
- No rate limiting on ApiVersions requests
- Potential for information leakage via version negotiation

---

### Token Handling Vulnerabilities

#### 1. SaslAuthenticateRequest Token Extraction (`SaslServerAuthenticator.handleSaslToken()` at line 462)

**Issue:** Token extracted from request via `Utils.copyArray(saslAuthenticateRequest.data().authBytes())`.

**Analysis:**
- `authBytes()` is untrusted binary data from network
- Copied via `Utils.copyArray()` which allocates new byte array
- No validation of token size before evaluation
- `saslServer.evaluateResponse()` called with copied array

**Potential Issue:** Large token could cause out-of-memory if evaluateResponse doesn't bound processing

**Mitigation:**
- `SaslAuthRequestMaxReceiveSize` config (line 195-197) limits receive buffer
- Default `DEFAULT_SASL_SERVER_MAX_RECEIVE_SIZE` bounds token size

#### 2. Error Message Information Leakage (`SaslServerAuthenticator.handleSaslToken()` at line 488-491)

**Issue:** PLAIN and SCRAM errors potentially leak information about authentication.

**Analysis:**
- Line 488-491: Catches `SaslException` and checks for Kerberos errors
- For non-Kerberos: returns generic error "Authentication failed during ... due to invalid credentials"
- But PLAIN throws `SaslAuthenticationException` with specific messages:
  - Line 92: "username not specified"
  - Line 94: "password not specified"
  - Line 106: "Invalid username or password"
  - Line 107: "Client requested an authorization id that is different from username"
- These messages reveal whether username or password was wrong

**Attack:** Attackers can enumerate valid usernames via response message analysis

**Mitigation Gaps:**
- PLAIN returns user-facing error messages
- No message normalization for PLAIN mechanism

---

### Data Flow Security Issues

#### Character Encoding Handling

**PLAIN Mechanism:**
- Line 85: `String response = new String(responseBytes, StandardCharsets.UTF_8)`
- Assumes bytes are valid UTF-8; if not, characters are replaced with replacement character
- Could lead to bypasses if encoding validation not strict

**SCRAM Mechanism:**
- Line 82: `String message = toMessage(messageBytes)` uses UTF-8
- Regex operates on UTF-8 string; Unicode characters in saslName allowed per RFC
- Potential for homograph attacks if different scripts used

**OAuth Bearer:**
- JWT typically UTF-8 encoded; claims parsed from JSON

---

### Authorization Integration Issues

#### Principal-to-ACL Mapping (`Authorizer.authorize()`)

**Issue:** Once principal created, authorization relies entirely on Authorizer implementation.

**Analysis:**
- `SaslServerAuthenticator.principal()` at line 307 calls `principalBuilder.build(context)`
- `DefaultKafkaPrincipalBuilder.build()` returns `new KafkaPrincipal(KafkaPrincipal.USER_TYPE, saslServer.getAuthorizationID())`
- Principal string used in ACL lookups; no escaping or validation of string format
- If principal contains special characters (though unlikely), could interact with ACL matching

**Mitigation Gaps:**
- Principal string format not enforced (could be very long, contain whitespace, etc.)
- No validation that principal matches expected format for mechanism

#### ANONYMOUS Principal in Unauthenticated State

**Issue:** During handshake, `KafkaPrincipal.ANONYMOUS` used (line 438, 521).

**Analysis:**
- Before SASL completes, if request received, context built with ANONYMOUS principal
- If request handler checks principal before auth completes, sees ANONYMOUS
- But SASL authenticator validates SASL state prevents non-auth requests in auth states

**Mitigation:** Code appears sound; ANONYMOUS principal only used during handshake when no auth expected

---

## Summary

The Apache Kafka SASL authentication flow implements multiple authentication mechanisms (PLAIN, SCRAM, OAuth Bearer, GSSAPI) with varying security properties. The architecture funnels untrusted client data from network sockets through:

1. **Protocol parsing layers** (SaslServerAuthenticator → mechanism-specific servers)
2. **Credential verification** (callback handlers consulting JAAS config or credential cache)
3. **Principal extraction** (DefaultKafkaPrincipalBuilder)
4. **Authorization enforcement** (Authorizer with ACLs)

**Key Security Findings:**

1. **PLAIN Mechanism Risks:** Credentials in plaintext in JAAS configuration; relies on OS-level file permissions for security. Suitable only for development/testing.

2. **SCRAM Mechanism Strengths:** Uses salted hashed credentials and challenge-response protocol. Regex parsing is adequate but complex; cryptographic verification provides strong integrity guarantees.

3. **OAuth Bearer Weaknesses:** Default implementation accepts unsecured JWT without signature verification. Production deployments must use secured validator with proper key management.

4. **GSSAPI Complexity:** Delegates to JGSS for cryptographic validation; auditing requires JGSS expertise. Principal name transformation rules must be carefully configured.

5. **Cross-Mechanism Issues:**
   - Information leakage via error messages and mechanism disclosure
   - Credential cache isolation must be enforced
   - Callback handler is untrusted code boundary requiring validation
   - No rate limiting on authentication attempts across all mechanisms
   - Principal extraction relies on callback handler correctness

6. **Re-authentication:** Principal consistency enforced, but depends on callback handler returning consistent results.

7. **Authorization Integration:** Principal format not strictly enforced; ACL matching depends on Authorizer implementation.

**Recommended Remediation:**

1. **Input Validation:** Add stricter validation of principal format after extraction from authentication context
2. **Rate Limiting:** Implement per-connection rate limiting on authentication attempts and handshake requests
3. **Error Message Normalization:** Return consistent error messages for all mechanisms (currently PLAIN leaks information)
4. **Callback Handler Validation:** Add runtime validation that callback handlers return credentials matching requested username
5. **Credential Cache Isolation:** Enforce per-mechanism credential isolation and add access logging
6. **OAuth Bearer Documentation:** Strengthen warnings about unsecured validator; consider removing default unsecured handler
7. **SCRAM Extensions:** Add stricter validation of extension semantics, not just regex matching
8. **Mechanism Downgrade Protection:** Consider preventing mechanism changes on re-authentication sessions at SASL layer
