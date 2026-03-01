# Kafka SASL Authentication Flow Security Analysis

## Files Examined

- `clients/src/main/java/org/apache/kafka/common/network/ChannelBuilders.java` — Main entry point for creating channel builders; orchestrates configuration of SASL channel builder with mechanisms, credential caches, and JAAS contexts
- `clients/src/main/java/org/apache/kafka/common/network/SaslChannelBuilder.java` — Creates SASL channels with configured authenticators; manages LoginManagers, JAAS contexts, and callback handlers for each mechanism
- `clients/src/main/java/org/apache/kafka/common/network/SaslChannelBuilder.java` — Creates SaslServerAuthenticator instances on channel build
- `clients/src/main/java/org/apache/kafka/common/network/Authenticator.java` — Interface defining authentication contract; principal() method returns KafkaPrincipal for authorization
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/SaslServerAuthenticator.java` — Server-side SASL authenticator; handles handshake, mechanism selection, and SASL exchange state machine
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/DefaultKafkaPrincipalBuilder.java` — Extracts KafkaPrincipal from SaslServer.getAuthorizationID() for PLAIN/SCRAM; applies optional short-naming for GSSAPI
- `clients/src/main/java/org/apache/kafka/common/security/auth/KafkaPrincipal.java` — Principal representation (type + name); used in request context for authorization
- `clients/src/main/java/org/apache/kafka/common/security/auth/SaslAuthenticationContext.java` — Encapsulates SaslServer, security protocol, client address, and listener name for principal builder
- `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainSaslServer.java` — SASL/PLAIN mechanism; parses [authzid] NUL authcid NUL passwd from client bytes
- `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainServerCallbackHandler.java` — PLAIN credential verification; retrieves expected password from JAAS config with key "user_<username>"
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramSaslServer.java` — SASL/SCRAM(-SHA-256) mechanism; multi-round HMAC-based challenge-response
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramServerCallbackHandler.java` — SCRAM credential callback; retrieves stored salt, iterations, salted password from credential cache
- `clients/src/main/java/org/apache/kafka/server/authorizer/Authorizer.java` — Authorization interface; authorize() method checks ACLs against KafkaPrincipal

## Entry Points

1. **ChannelBuilders.serverChannelBuilder()** — Accepts `AbstractConfig config` containing all broker security settings; entry point for untrusted cluster configuration
   - Line 96-107: Public method signature
   - Triggers JAAS context loading for each enabled SASL mechanism (line 137-140)

2. **SaslChannelBuilder.buildChannel()** — Accepts `SelectionKey key` (network socket); creates SaslServerAuthenticator supplier lambda
   - Line 215-250: Builds transport layer and authenticator
   - Creates per-channel authenticator instances

3. **SaslServerAuthenticator.handleKafkaRequest()** — Receives raw client bytes in `byte[] requestBytes` from socket read
   - Line 507: Method signature
   - Line 509-510: Parses bytes as RequestHeader (first untrusted data parse)
   - Line 515-516: Validates API key to prevent handling unexpected request types
   - Calls RequestContext.parseRequest() which parses SaslHandshakeRequest or ApiVersionsRequest

4. **SaslServerAuthenticator.handleSaslToken()** — Receives raw SASL mechanism bytes in `byte[] clientToken`
   - Line 421: Method signature
   - Line 423, 462: Calls saslServer.evaluateResponse(clientToken) — **mechanism-specific data parsing**
   - Line 461-462: For Kafka header format (SaslAuthenticateRequest), extracts auth bytes via Utils.copyArray()

5. **PlainSaslServer.evaluateResponse()** — Receives raw mechanism bytes in `byte[] responseBytes`
   - Line 71: Method signature
   - Line 85: **Converts bytes to String using UTF-8 without validation** → untrusted data decode
   - Line 86: Calls extractTokens() which splits on NUL character
   - **Entry point: receives `[authzid] NUL authcid NUL passwd` from client**

6. **ScramSaslServer.evaluateResponse()** — Receives raw mechanism bytes in `byte[] response`
   - Line 96: Method signature
   - Line 100: **Parses ClientFirstMessage from bytes** (untrusted SCRAM message parse)
   - Line 108: Extracts saslName from ClientFirstMessage
   - **Entry point: receives ClientFirstMessage with embedded username**

7. **SaslServerAuthenticator.authenticate()** — Main authentication loop
   - Line 250: Method signature
   - Line 264: Reads from transportLayer (socket receive)
   - Line 272-273: Extracts bytes from NetworkReceive payload
   - Line 281, 286: Routes to handleKafkaRequest or handleSaslToken based on state

## Data Flow

### Flow 1: PLAIN Mechanism (RFC 4616)

**Entry Point:** Client TCP connection → SocketServer → Selector → KafkaChannel → SaslServerAuthenticator

1. **Source (untrusted input enters):** `PlainSaslServer.evaluateResponse()` line 71
   - Input: Raw bytes from network socket (client-controlled)
   - Source: NetworkReceive payload from socket read
   - Format: Binary bytes representing "[authzid] NUL authcid NUL passwd" in UTF-8

2. **Transform (parsing without validation):** `PlainSaslServer.evaluateResponse()` line 85-89
   ```
   String response = new String(responseBytes, StandardCharsets.UTF_8);
   List<String> tokens = extractTokens(response);
   String authorizationIdFromClient = tokens.get(0);  // Untrusted
   String username = tokens.get(1);                   // Untrusted
   String password = tokens.get(2);                   // Untrusted (in memory)
   ```
   - **Vulnerability: No length validation before UTF-8 decode** (large payloads could cause memory pressure)
   - **Vulnerability: No null/empty check before extractTokens()** (but handled in line 91-96)
   - Tokens are extracted by splitting on NUL (line 120, 125)
   - If split yields != 3 tokens, SaslAuthenticationException thrown (line 129-131)

3. **Transform (credential verification):** `PlainServerCallbackHandler.authenticate()` line 61-70
   ```
   String expectedPassword = JaasContext.configEntryOption(jaasConfigEntries,
       JAAS_USER_PREFIX + username,  // Untrusted username used as key
       PlainLoginModule.class.getName());
   return expectedPassword != null && Utils.isEqualConstantTime(password, expectedPassword.toCharArray());
   ```
   - **Mitigation: NameCallback + PlainAuthenticateCallback are used to invoke custom handlers**
   - **Mitigation: Constant-time comparison (Utils.isEqualConstantTime) prevents timing attacks**
   - **Vulnerability: Username used directly to lookup JAAS config key ("user_<username>")**
     - If username contains special characters or is very long, lookup may fail silently or cause issues
     - No injection protection; relies on JAAS config being trustworthy

4. **Transform (principal extraction):** `DefaultKafkaPrincipalBuilder.build()` line 79-84
   ```
   SaslServer saslServer = ((SaslAuthenticationContext) context).server();
   if (SaslConfigs.GSSAPI_MECHANISM.equals(saslServer.getMechanismName()))
       return applyKerberosShortNamer(saslServer.getAuthorizationID());
   else
       return new KafkaPrincipal(KafkaPrincipal.USER_TYPE, saslServer.getAuthorizationID());
   ```
   - **Principal name comes directly from SaslServer.getAuthorizationID()**
   - For PLAIN: `PlainSaslServer.getAuthorizationID()` returns `authorizationId` field set at line 110
   - This is the username extracted from the SASL exchange (untrusted origin)
   - **No validation of principal name format** (but stored in KafkaPrincipal safely)

5. **Sink (sensitive operation):** `RequestContext` is built with principal
   - Line 437-438 in SaslServerAuthenticator.handleSaslToken():
   ```
   RequestContext requestContext = new RequestContext(header, connectionId, clientAddress(),
       Optional.of(clientPort()), KafkaPrincipal.ANONYMOUS, listenerName, ...)
   ```
   - Request context is passed to request handlers
   - Principal is extracted via authenticator.principal() call
   - **Authorization sink:** `Authorizer.authorize(AuthorizableRequestContext, List<Action>)` line 107 in Authorizer.java
     - Authorizer checks KafkaPrincipal against ACL bindings
     - If no ACL matches, request is denied
     - If ACL matches, request proceeds

### Flow 2: SCRAM Mechanism (RFC 5802 / Kafka KIP-86)

**Entry Point:** Client TCP connection → SocketServer → Selector → KafkaChannel → SaslServerAuthenticator

1. **Source (untrusted input enters):** `ScramSaslServer.evaluateResponse()` line 96
   - Input: Raw bytes from network socket (client-controlled)
   - First call in state RECEIVE_CLIENT_FIRST_MESSAGE
   - Format: Binary SCRAM ClientFirstMessage with embedded username and nonce

2. **Transform (SCRAM ClientFirstMessage parsing):** `ScramSaslServer.evaluateResponse()` line 99-109
   ```
   ClientFirstMessage clientFirstMessage = new ClientFirstMessage(response);  // Parses bytes
   String saslName = clientFirstMessage.saslName();
   String username = ScramFormatter.username(saslName);  // Extracts username from saslName
   ```
   - **ClientFirstMessage constructor parses binary data (untrusted)**
   - ClientFirstMessage line 100 indicates binary parse (format: gs2-header || client-first-without-proof)
   - ScramFormatter.username() applies SASLprep to extract authorization identity

3. **Transform (credential retrieval):** `ScramSaslServer.evaluateResponse()` line 110-126
   ```
   NameCallback nameCallback = new NameCallback("username", username);
   ScramCredentialCallback credentialCallback = new ScramCredentialCallback();
   callbackHandler.handle(new Callback[]{nameCallback, credentialCallback});
   this.scramCredential = credentialCallback.scramCredential();
   if (scramCredential == null)
       throw new SaslException("Authentication failed: Invalid user credentials");
   ```
   - **Callback handler retrieves stored credential** from credential cache
   - Stored credential contains: salt, iterations, StoredKey, ServerKey
   - **Mitigation: Credential lookup uses username as key; if not found, generic error thrown**
   - **Vulnerability: Large iterations value could cause DoS if no limit enforced** (line 133 checks minimum, but no maximum shown)

4. **Transform (challenge-response verification):** `ScramSaslServer.evaluateResponse()` line 147-156
   ```
   ClientFinalMessage clientFinalMessage = new ClientFinalMessage(response);
   if (!clientFinalMessage.nonce().equals(serverFirstMessage.nonce())) {
       throw new SaslException("Invalid client nonce in the final client message.");
   }
   verifyClientProof(clientFinalMessage);  // HMAC verification
   ```
   - **Nonce must match** (prevents replay attacks)
   - verifyClientProof() line 227-236: Verifies client proof using HMAC
   ```
   byte[] expectedStoredKey = scramCredential.storedKey();
   byte[] clientSignature = formatter.clientSignature(expectedStoredKey, ...);
   byte[] computedStoredKey = formatter.storedKey(clientSignature, clientFinalMessage.proof());
   if (!MessageDigest.isEqual(computedStoredKey, expectedStoredKey))
       throw new SaslException("Invalid client credentials");
   ```
   - **Mitigation: MessageDigest.isEqual() provides constant-time comparison**
   - **Mitigation: Proof verification prevents credential brute-force attacks offline**

5. **Transform (principal extraction):** `DefaultKafkaPrincipalBuilder.build()` line 79-84
   - Same as PLAIN flow
   - KafkaPrincipal.USER_TYPE + SaslServer.getAuthorizationID()

6. **Sink (sensitive operation):** Same as PLAIN flow
   - RequestContext passed to Authorizer.authorize()
   - ACL checks performed

### Flow 3: GSSAPI Mechanism (Kerberos)

**Entry Point:** Client TCP connection → SocketServer → Selector → KafkaChannel → SaslServerAuthenticator

1. **Source:** `SaslServerAuthenticator.createSaslKerberosServer()` line 219-239
   - Creates javax.security.sasl.SaslServer with Sasl.createSaslServer()
   - KerberosClientCallbackHandler handles GSSAPI token exchange

2. **Transform (Kerberos token parsing):**
   - Java GSS library parses Kerberos tokens (outside Kafka code)
   - Token format: ASN.1 DER encoded KRB_AP_REQ message

3. **Transform (principal extraction):** `DefaultKafkaPrincipalBuilder.applyKerberosShortNamer()` line 90-99
   ```
   KerberosName kerberosName = KerberosName.parse(authorizationId);
   String shortName = kerberosShortNamer.shortName(kerberosName);
   return new KafkaPrincipal(KafkaPrincipal.USER_TYPE, shortName);
   ```
   - **Mitigation: Optional KerberosShortNamer applies name rewrite rules** (configured via SASL_KERBEROS_PRINCIPAL_TO_LOCAL_RULES_CONFIG)
   - Rule-based transformation prevents injection

4. **Sink:** Same as PLAIN/SCRAM

### Flow 4: OAUTHBEARER Mechanism (KIP-140)

Similar to other mechanisms; OAuthBearerUnsecuredValidatorCallbackHandler or custom handler validates JWT token.

## Dependency Chain

From untrusted input to authorization decision:

1. **Entry:** Socket receive (SocketChannel.read())
2. **SaslServerAuthenticator.authenticate()** (line 250)
   - Calls transportLayer.readFrom() → reads NetworkReceive from socket
3. **SaslServerAuthenticator.handleKafkaRequest()** (line 507)
   - Parses RequestHeader from bytes (line 510)
   - Routes to handleHandshakeRequest() or handleApiVersionsRequest()
4. **SaslServerAuthenticator.handleSaslToken()** (line 421) or step 3 → SaslHandshakeRequest
5. **SaslChannelBuilder.createServerCallbackHandlers()** (line 317-335)
   - Creates PlainServerCallbackHandler, ScramServerCallbackHandler, etc.
6. **Sasl.createSaslServer()** (line 208-209 or 234-235)
   - Creates PlainSaslServer, ScramSaslServer, or Kerberos SaslServer
7. **PlainSaslServer.evaluateResponse()** or **ScramSaslServer.evaluateResponse()** (line 71 or 96)
   - **Parses untrusted mechanism bytes**
8. **PlainServerCallbackHandler.authenticate()** or **ScramServerCallbackHandler.handle()** (line 61 or equivalent)
   - Verifies credentials using JAAS config or credential cache
9. **SaslServerAuthenticator.principal()** (line 307-317)
   - Calls DefaultKafkaPrincipalBuilder.build()
10. **DefaultKafkaPrincipalBuilder.build()** (line 69-88)
    - Extracts KafkaPrincipal from SaslServer.getAuthorizationID()
11. **RequestContext.build()** (line 437-438 in SaslServerAuthenticator)
    - Embeds KafkaPrincipal in request context
12. **Request handler** (in core/src/main/scala/kafka/server/)
    - Calls Authorizer.authorize(RequestContext, List<Action>)
13. **StandardAuthorizer.authorize()** (metadata/src/main/java/org/apache/kafka/metadata/authorizer/)
    - Checks ACL bindings against principal
    - Denies if no matching ALLOW ACL found

## Analysis

### SASL Handshake Protocol

The SASL authentication flow follows the Kafka protocol:

1. **ApiVersionsRequest** (optional): Client sends supported API versions
   - Server responds with ApiVersionsResponse
   - Informs client of supported SASL mechanisms

2. **SaslHandshakeRequest**: Client selects mechanism
   - Format: SaslHandshakeRequest { mechanism: "PLAIN" | "SCRAM-SHA-256" | "GSSAPI" }
   - Server responds with SaslHandshakeResponse { supported_mechanisms, error_code }
   - Error if client mechanism not enabled on broker

3. **SaslAuthenticateRequest/Response** (Kafka v1+): SASL token exchange
   - Client sends: SaslAuthenticateRequest { auth_bytes }
   - Server responds: SaslAuthenticateResponse { error_code, auth_bytes, session_lifetime_ms }
   - Multiple rounds until authentication complete or error

4. **Legacy Format** (Kafka v0): Size-prefixed SASL tokens without Kafka headers
   - 4-byte size + opaque SASL token

### Mechanism-Specific Data Flows

#### PLAIN (RFC 4616)
- **Single round**: Client sends complete credentials in one message
- **Format**: `[authzid] UTF8NUL authcid UTF8NUL passwd`
- **Key vulnerability**: **No length limit on credentials before UTF-8 decode**
  - `new String(responseBytes, StandardCharsets.UTF_8)` at line 85 of PlainSaslServer.java
  - Could accept megabyte-sized payloads, causing memory exhaustion if not bounded elsewhere
  - **Mitigation**: `saslAuthRequestMaxReceiveSize` config (line 195 of SaslServerAuthenticator.java) limits overall SASL request size
  - **Mitigation**: NetworkReceive(saslAuthRequestMaxReceiveSize, connectionId) enforces size limit

- **Key strength**: Constant-time password comparison (Utils.isEqualConstantTime)
  - Prevents timing-based password guessing attacks

#### SCRAM-SHA-256/SCRAM-SHA-512 (RFC 5802)
- **Multiple rounds**: 3-way exchange (ClientFirstMessage → ServerFirstMessage → ClientFinalMessage → ServerFinalMessage)
- **Key vulnerabilities**:
  1. **Iterations DoS**: If attacker can control iterations value in SCRAM credentials
     - Line 133-134 checks minimum iterations: `if (scramCredential.iterations() < mechanism.minIterations())`
     - **No maximum iterations limit shown** → attacker could slow down authentication by using credentials with very high iteration counts
     - However, iterations are stored server-side in credential cache (not client-controlled)

  2. **Nonce reuse attack**: Mitigated by server nonce comparison (line 150)

  3. **Credential cache poisoning**: If credential cache can be modified by attacker, SCRAM keys could be replaced
     - **Mitigation**: Credential cache is populated from broker's credential store (ZK or metadata log)
     - Requires broker to be compromised or admin credentials leaked

- **Key strength**: HMAC-based proof verification with constant-time comparison
  - Prevents offline password brute-force attacks
  - Stored key protects salted password (salted password is never transmitted)

#### GSSAPI (Kerberos)
- **Multiple rounds**: GSS token exchange with Kerberos KDC
- **Key mitigations**:
  1. **Kerberos ticketing**: Mutual authentication between client and server
  2. **Optional short-naming**: KerberosShortNamer applies rewrite rules to principal name
  3. **Principal format enforcement**: KerberosName.parse() validates principal format (line 224)

#### OAUTHBEARER (KIP-140)
- **Single round**: Client sends Bearer token
- **Key dependencies**: JWT validation (signature, expiry, etc.)
  - Handled by custom callback handler (OAuthBearerUnsecuredValidatorCallbackHandler or enterprise)

### Authentication to Authorization Transition

After SASL completes:

1. **SaslServerAuthenticator.authenticate()** returns when `saslState == COMPLETE` (line 325-327)

2. **SaslServerAuthenticator.principal()** is called (line 307-317)
   ```
   SaslAuthenticationContext context = new SaslAuthenticationContext(saslServer, ...);
   KafkaPrincipal principal = principalBuilder.build(context);
   ```
   - Principal is extracted at this point (after authentication succeeds)

3. **RequestContext is built** with principal (line 520-521)
   ```
   RequestContext requestContext = new RequestContext(header, connectionId, clientAddress(),
       Optional.of(clientPort()), KafkaPrincipal.ANONYMOUS, ...);
   ```
   - Note: At this point, principal is still ANONYMOUS in RequestContext constructor
   - Principal is retrieved later via `authenticator.principal()` call in request handler

4. **Request handler invokes Authorizer.authorize()** (in core/src/main/scala/kafka/server/)
   - Checks if principal has permission for requested action on resource

### Existing Mitigations

| Vulnerability Class | Mitigation | Strength |
|---|---|---|
| Timing attacks (password guessing) | Constant-time comparison (Utils.isEqualConstantTime, MessageDigest.isEqual) | Strong |
| Nonce reuse attacks (SCRAM/GSSAPI) | Server-generated nonce verification | Strong |
| Credentials in transit (PLAIN) | Must use SASL_SSL or SASL_PLAINTEXT with TLS | Admin-dependent |
| Offline password brute-force (SCRAM) | Stored Key approach (salted password never transmitted) | Strong |
| Mechanism forcing | SaslHandshakeRequest validates client-selected mechanism against enabled list | Strong |
| Large payload DoS | NetworkReceive size limit (saslAuthRequestMaxReceiveSize) | Medium |
| Principal name injection | KafkaPrincipal constructor validates type/name are non-null; format stored safely | Medium |
| Username-based credential lookup | JAAS config lookup is static; no dynamic evaluation | Medium |

### Gaps and Potential Issues

1. **PLAIN mechanism exposes authentication in logs**
   - If password is included in error messages or logs, it could leak
   - Mitigation: Line 487-495 carefully redacts error messages for SCRAM/GSSAPI
   - **Issue**: PlainSaslServer line 103 includes exception that may expose implementation details

2. **No rate limiting on authentication attempts**
   - A client can attempt unlimited SASL exchanges on same connection
   - Each failed attempt costs CPU (callback handler invocation, HMAC computation for SCRAM)
   - Mitigation: Broker-level connection handling may close connections after repeated failures, but not explicit in SASL code

3. **No protection against credential cache deserialization attacks**
   - If credential cache (CredentialCache) is populated from untrusted source, could be exploited
   - However, cache is populated from broker's own persistent store (ZK/metadata log), so risk is lower

4. **SASL extensions validation (ScramExtensions) is incomplete**
   - Line 102-105 of ScramSaslServer: Only known extensions are processed
   - Unknown extensions are silently ignored (logged at debug level)
   - **Potential issue**: Future extension could bypass validation if not properly registered

5. **Re-authentication mechanism allows principal change** (in some configurations)
   - Line 463-464: Principal is verified to match original during re-auth
   - However, re-auth with different mechanism could change principal representation
   - Mitigation: Line 532-535 checks if mechanism unchanged

6. **No explicit validation of principal name length**
   - KafkaPrincipal stores name as String (immutable, but unbounded)
   - Very long usernames could cause memory issues or affect lookup performance
   - Mitigation: Implicit limit from SASL mechanisms (RFC 4616 allows up to 255 octets for username)

### Attack Scenarios

#### Scenario 1: Credential Enumeration via Timing Side-Channel (PLAIN)

**Attack**: Attacker sends PLAIN credentials with different usernames to measure response time and enumerate valid usernames.

**Why mitigated**:
- Constant-time comparison is used (Utils.isEqualConstantTime)
- JAAS callback handler is invoked regardless of whether username exists
- Server doesn't reveal whether username exists or password was wrong

**Residual risk**: If custom callback handler logs failures, timing could be observable via log latency.

#### Scenario 2: Brute-Force Attack (PLAIN)

**Attack**: Attacker sends many PLAIN credentials with guessed passwords.

**Why partially mitigated**:
- TLS encryption prevents password sniffing (if SASL_SSL is used)
- Constant-time comparison prevents timing attacks
- **Not fully mitigated**: No rate limiting per connection or per username

**Recommendation**: Implement rate limiting on authentication failures per username or per connection.

#### Scenario 3: Large Credential Injection DoS (PLAIN)

**Attack**: Attacker sends PLAIN credential with 1 MB password field.

**Why mitigated**:
- saslAuthRequestMaxReceiveSize config limits SASL request size (default: 12 KB based on comment)
- NetworkReceive enforces this limit via InvalidReceiveException (line 265-266)

**Strength**: Medium (requires proper configuration; default should be safe)

#### Scenario 4: Malformed SCRAM Tokens (Re-authentication)

**Attack**: Attacker re-authenticates with malformed ClientFirstMessage.

**Why mitigated**:
- ClientFirstMessage constructor validates format
- Exception thrown if parse fails (line 141-144)
- Error is caught and returned to client

**Strength**: Strong

#### Scenario 5: Token Expiry Bypass (SCRAM with Delegation Tokens)

**Attack**: Attacker attempts to use expired delegation token.

**Why protected**:
- Token expiry is checked in callback handler (ScramServerCallbackHandler)
- tokenExpiryTimestamp is recorded (line 119)
- If token expired, callback handler should throw exception

**Strength**: Dependent on token storage implementation (ZK/metadata log)

#### Scenario 6: ACL Bypass via Principal Name Manipulation

**Attack**: Attacker crafts username with special characters (e.g., "User:admin") to match different principal.

**Why mitigated**:
- KafkaPrincipal is immutable; type and name are separate fields
- ACL matching uses exact string comparison on principal.toString() or field comparison
- No parsing of ":" character in principal name (it's a separator only in string representation)

**Strength**: Strong (but depends on Authorizer implementation)

## Credential Storage Architecture

### PLAIN Credentials
- **Location**: JAAS configuration (jaas.conf file or system properties)
- **Format**: `user_<username> = <password>`
- **Risk**: Plaintext passwords in configuration file
- **Mitigation**: File permissions on JAAS config (OS-level)

### SCRAM Credentials
- **Location**: Broker credential cache (CredentialCache) → ZK or metadata log
- **Format**: ScramCredential { salt, iterations, storedKey, serverKey }
- **Risk**: Stored key could be used to forge proofs if compromised
- **Mitigation**: Access control on ZK/metadata log; stored key ≠ salted password

### Delegation Token Credentials
- **Location**: Broker token cache (DelegationTokenCache) → metadata log
- **Format**: Token { owner, principalType, expiryTime, ... }
- **Risk**: Token could be used by attacker if intercepted
- **Mitigation**: Tokens are short-lived (default: 1 hour); TLS encryption required

## Summary

The Apache Kafka SASL authentication flow implements defense-in-depth security:

1. **Untrusted data entry points are explicitly handled**:
   - PLAIN: RFC 4616 message parsing with size limits
   - SCRAM: RFC 5802 multi-round challenge-response
   - GSSAPI: Kerberos tokenization via Java GSS library
   - OAUTHBEARER: JWT token validation

2. **Credential verification is cryptographically sound**:
   - PLAIN: Constant-time password comparison
   - SCRAM: HMAC-based proof verification with stored key (salted password never transmitted)
   - GSSAPI: Mutual authentication via Kerberos
   - OAUTHBEARER: JWT signature verification

3. **Principal extraction is controlled**:
   - DefaultKafkaPrincipalBuilder maps authentication context to immutable KafkaPrincipal
   - Optional short-naming for GSSAPI (rule-based transformation)

4. **Authorization is enforced**:
   - KafkaPrincipal is passed to Authorizer.authorize() for ACL checking
   - No implicit permissions; all actions require explicit ACL grant

5. **Remaining risks are primarily operational**:
   - Credential storage security (PLAIN passwords in files; SCRAM keys in ZK)
   - Rate limiting on authentication attempts (not implemented in code)
   - Configuration of size limits (saslAuthRequestMaxReceiveSize)
   - TLS enforcement for PLAIN mechanism (not enforced in SASL code)

**Severity assessment**: **LOW for protocol implementation, MEDIUM for operational deployment**
- The SASL mechanisms themselves are correctly implemented per RFC standards
- Weaknesses exist primarily in credential storage and lack of rate limiting
- TLS + SCRAM/GSSAPI provides strong security; PLAIN is inherently weak and requires admin discipline
