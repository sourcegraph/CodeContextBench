# Apache Kafka SASL Authentication Flow Security Analysis

## Files Examined

### Core Network & Channel Building
- `clients/src/main/java/org/apache/kafka/common/network/ChannelBuilders.java` — Factory for creating channel builders and selecting appropriate security implementations
- `clients/src/main/java/org/apache/kafka/common/network/SaslChannelBuilder.java` — Constructs SASL-enabled channels, initializes LoginManagers and callback handlers for each mechanism
- `clients/src/main/java/org/apache/kafka/common/network/Authenticator.java` — Interface defining authentication lifecycle and principal extraction
- `clients/src/main/java/org/apache/kafka/common/network/NetworkReceive.java` — Receives untrusted bytes from socket with size-delimited protocol

### SASL Server-Side Authenticator
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/SaslServerAuthenticator.java` — Main entry point for SASL authentication; handles SASL handshake protocol state machine

### Authentication Callbacks & Handlers
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/SaslServerCallbackHandler.java` — Default callback handler for SASL realm and GSSAPI authorization callbacks
- `clients/src/main/java/org/apache/kafka/common/security/auth/AuthenticateCallbackHandler.java` — Interface for mechanism-specific callback handlers

### PLAIN Authentication Mechanism
- `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainSaslServer.java` — Parses PLAIN protocol; calls callback handler for credential verification
- `clients/src/main/java/org/apache/kafka/common/security/plain/internals/PlainServerCallbackHandler.java` — Verifies plaintext credentials against JAAS configuration

### SCRAM Authentication Mechanism
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramSaslServer.java` — Implements RFC 5802 SCRAM challenge-response; processes ClientFirstMessage and ClientFinalMessage
- `clients/src/main/java/org/apache/kafka/common/security/scram/internals/ScramServerCallbackHandler.java` — Retrieves SCRAM credentials and delegation token information from credential cache

### OAUTHBEARER Authentication Mechanism
- `clients/src/main/java/org/apache/kafka/common/security/oauthbearer/internals/OAuthBearerSaslServer.java` — Validates JWT bearer tokens via callback handler; extracts principal from token claims

### Principal & Authorization
- `clients/src/main/java/org/apache/kafka/common/security/auth/KafkaPrincipal.java` — Immutable representation of authenticated principal (type + name)
- `clients/src/main/java/org/apache/kafka/common/security/authenticator/DefaultKafkaPrincipalBuilder.java` — Builds KafkaPrincipal from authentication context; applies GSSAPI short-name rules
- `clients/src/main/java/org/apache/kafka/common/security/auth/SaslAuthenticationContext.java` — Authentication context carrying SaslServer and client metadata (IP, listener, SSL session)
- `clients/src/main/java/org/apache/kafka/common/security/auth/KafkaPrincipalBuilder.java` — Interface for pluggable principal builders

---

## Entry Points

### 1. **Channel Creation Entry Point**
**File**: `ChannelBuilders.java:64-81`
**Method**: `clientChannelBuilder()` / `serverChannelBuilder()`
**Input**: `SecurityProtocol`, JAAS context type, client SASL mechanism
**Untrusted Data**: Configuration values from broker/client config; mechanism name from client
- Creates `SaslChannelBuilder` which prepares callback handlers and JAAS contexts for each enabled mechanism

### 2. **Network Data Reception Entry Point**
**File**: `NetworkReceive.java:82-115`
**Method**: `readFrom(ScatteringByteChannel channel)`
**Input**: Raw bytes from socket
**Untrusted Data**: 4-byte size prefix followed by N bytes of payload
- Reads size-delimited messages from network; validates size against `maxSize` limit
- Size is extracted via `ByteBuffer.getInt()` at line 91

### 3. **SASL Handshake Parsing Entry Point**
**File**: `SaslServerAuthenticator.java:250-304`
**Method**: `authenticate()`
**Input**: Serialized Kafka protocol requests
**Untrusted Data**: Raw client bytes containing ApiVersionsRequest or SaslHandshakeRequest
- Entry point for initial authentication state machine
- Reads client token from network receive buffer (line 272-273)
- Passes to `handleKafkaRequest(clientToken)` or `handleSaslToken(clientToken)` depending on state

### 4. **SASL Mechanism Name Entry Point**
**File**: `SaslServerAuthenticator.java:549-565`
**Method**: `handleHandshakeRequest(RequestContext context, SaslHandshakeRequest handshakeRequest)`
**Input**: `SaslHandshakeRequest` containing client-provided mechanism name
**Untrusted Data**: Mechanism name string from client (line 550: `handshakeRequest.data().mechanism()`)
- Client provides mechanism name; validated against enabled mechanisms list (line 554)
- If not supported, error response sent (lines 559-563)
- **CRITICAL**: Determines which callback handler and SASL server implementation will process subsequent tokens

### 5. **SASL Token Processing Entry Point**
**File**: `SaslServerAuthenticator.java:421-499`
**Method**: `handleSaslToken(byte[] clientToken)`
**Input**: Mechanism-specific SASL token bytes
**Untrusted Data**: Raw bytes from client
- Directs to mechanism-specific `SaslServer.evaluateResponse()` implementation
- For legacy SASL (no headers): token passed directly to `saslServer.evaluateResponse()` (line 423)
- For Kafka-wrapped SASL: parses as `SaslAuthenticateRequest` and extracts `authBytes()` field (line 462)

### 6. **PLAIN Mechanism Entry Point**
**File**: `PlainSaslServer.java:70-114`
**Method**: `evaluateResponse(byte[] responseBytes)`
**Input**: SASL PLAIN payload: `[authzid]\0[authcid]\0[passwd]`
**Untrusted Data**: All three components are client-controlled; strings in UTF-8
- Parses response by splitting on NUL byte (line 85, `StandardCharsets.UTF_8`)
- Extracts username and password (lines 87-89)
- Validates non-empty username/password (lines 91-96)
- Calls `callbackHandler.handle()` passing username and password (line 101)

### 7. **SCRAM Mechanism Entry Point**
**File**: `ScramSaslServer.java:95-172`
**Method**: `evaluateResponse(byte[] response)`
**Input**: RFC 5802 SCRAM message (ClientFirstMessage or ClientFinalMessage)
**Untrusted Data**: Client-provided SASL name, nonce, channel binding, and proof
- Parses `ClientFirstMessage` at line 100: extracts SASL name, authorization ID, extensions, nonce
- Retrieves credentials via callback handler (lines 110-122)
- Validates nonce match (line 150)
- Verifies client proof via HMAC comparison (line 153)

### 8. **OAUTHBEARER Mechanism Entry Point**
**File**: `OAuthBearerSaslServer.java:85-102`
**Method**: `evaluateResponse(byte[] response)`
**Input**: OAUTHBEARER token payload
**Untrusted Data**: Client-provided JWT token string
- Parses response into `OAuthBearerClientInitialResponse` (line 95)
- Extracts token value and authorization ID
- Passes to `process()` method which invokes callback handler for JWT validation

### 9. **Principal Extraction Entry Point**
**File**: `SaslServerAuthenticator.java:306-317`
**Method**: `principal()`
**Input**: Authenticated `SaslServer` instance
**Untrusted Data**: Authorization ID from `SaslServer.getAuthorizationID()`
- Creates `SaslAuthenticationContext` with SaslServer and client metadata
- Calls `principalBuilder.build(context)` to derive KafkaPrincipal
- For GSSAPI: applies KerberosShortNamer transformation (DefaultKafkaPrincipalBuilder line 90-98)
- Result: `KafkaPrincipal(type, name)` used for subsequent authorization checks

---

## Data Flow

### Flow 1: PLAIN Authentication Token Exchange

```
1. Source: NetworkReceive.readFrom() [SaslServerAuthenticator.java:264]
   - Untrusted input: Raw socket bytes containing size-delimited SASL token
   - No initial validation of content, only size bounds checked

2. Transform: SaslServerAuthenticator.authenticate() [line 250-304]
   - Reads completed NetworkReceive payload into clientToken[] (lines 272-273)
   - Passes to handleSaslToken(clientToken) [line 286]

3. Transform: handleSaslToken(byte[] clientToken) [line 421-499]
   - For non-Kafka-wrapped SASL: directly passes to saslServer.evaluateResponse() [line 423]
   - For Kafka-wrapped SASL (v1+): parses as SaslAuthenticateRequest [line 458]
   - Extracts authBytes from request [line 462: Utils.copyArray(saslAuthenticateRequest.data().authBytes())]

4. Transform: PlainSaslServer.evaluateResponse(byte[] responseBytes) [line 71-114]
   - Converts bytes to String using UTF-8 [line 85]
   - Parses token string by splitting on NUL character [line 86: extractTokens()]
   - Validates token count = 3 [lines 129-131]
   - Extracts [authzid, username, password] components

5. Validation: PlainServerCallbackHandler.handle(Callback[] callbacks) [line 47-59]
   - Receives NameCallback with username
   - Receives PlainAuthenticateCallback with password
   - Calls authenticate(username, password) [line 54]

6. Credential Verification: PlainServerCallbackHandler.authenticate() [line 61-70]
   - Looks up expected password in JAAS configuration [line 65-67]
   - Key format: "user_" + username
   - Compares with Utils.isEqualConstantTime() [line 68]
   - Returns boolean authenticated flag

7. Authorization ID Extraction: PlainSaslServer.getAuthorizationID() [line 136-141]
   - Returns username stored during evaluateResponse [line 110]

8. Sink: SaslServerAuthenticator.principal() [line 307-317]
   - Creates SaslAuthenticationContext(saslServer, protocol, clientAddress, listener, sslSession)
   - Calls principalBuilder.build(context)
   - For PLAIN: DefaultKafkaPrincipalBuilder.build() returns KafkaPrincipal(USER_TYPE, authorizationId)
   - Returned KafkaPrincipal used for ACL authorization in broker
```

**Dependency Chain (PLAIN)**:
1. NetworkReceive (network I/O boundary)
2. SaslServerAuthenticator.authenticate() (state machine)
3. SaslServerAuthenticator.handleSaslToken()
4. PlainSaslServer.evaluateResponse() (protocol parsing)
5. PlainServerCallbackHandler.authenticate() (credential lookup)
6. DefaultKafkaPrincipalBuilder.build() (principal extraction)
7. Authorizer.authorize(principal, action, resource) (ACL enforcement, outside this flow)

### Flow 2: SCRAM Authentication Token Exchange

```
1. Source: NetworkReceive.readFrom() [SaslServerAuthenticator.java:264]
   - Untrusted input: Raw socket bytes containing ClientFirstMessage or ClientFinalMessage
   - Size validated against limit only

2. Transform: SaslServerAuthenticator.authenticate() [line 250-304]
   - Reads NetworkReceive payload into clientToken[]
   - Passes to handleSaslToken(clientToken) [line 286]

3. Transform: handleSaslToken() routes to SaslServer.evaluateResponse()
   - Unwrapped SASL: direct call [line 423]
   - Kafka-wrapped SASL: extract from SaslAuthenticateRequest [line 462]

4. Transform: ScramSaslServer.evaluateResponse(byte[] response) [line 95-172]
   - State machine handling:

   ** State.RECEIVE_CLIENT_FIRST_MESSAGE:
   - Parses ClientFirstMessage from response bytes [line 100]
   - Extracts: saslName, authorizationId, nonce, extensions
   - saslName is untrusted string from client [line 108]
   - Parses SASL name to extract username [line 109: ScramFormatter.username(saslName)]

5. Callback: ScramServerCallbackHandler.handle() [line 52-71]
   - Receives NameCallback with extracted username
   - Handles ScramCredentialCallback [line 65-67]
   - Looks up credential in credentialCache.get(username) [line 67]
   - Returns ScramCredential containing: salt, storedKey, serverKey, iterations

6. Validation: ScramSaslServer continues processing [line 127-138]
   - Validates scramCredential is not null [lines 127-128]
   - Validates iterations >= minimum [lines 133-134]
   - Returns ServerFirstMessage with nonce, salt, iterations
   - Transitions to State.RECEIVE_CLIENT_FINAL_MESSAGE

7. Transform: ScramSaslServer.evaluateResponse() **State.RECEIVE_CLIENT_FINAL_MESSAGE** [line 147-162]
   - Parses ClientFinalMessage [line 149]
   - Validates nonce matches ServerFirstMessage nonce [line 150-152]
   - Calls verifyClientProof(clientFinalMessage) [line 153]

8. Verification: ScramSaslServer.verifyClientProof() [line 227-237]
   - Retrieves expected storedKey from credential [line 229]
   - Computes clientSignature using HMAC [line 230]
   - XORs clientSignature with clientProof to get computedStoredKey [line 231]
   - Constant-time comparison: MessageDigest.isEqual(computedStoredKey, expectedStoredKey) [line 232]
   - Throws SaslException if mismatch [line 233]

9. Authorization ID Extraction: ScramSaslServer.getAuthorizationID() [line 174-179]
   - Returns authorizationId set in RECEIVE_CLIENT_FIRST_MESSAGE state [line 123 or 118]
   - For delegation tokens: returns tokenCallback.tokenOwner() [line 118]
   - For regular auth: returns username [line 123]

10. Sink: SaslServerAuthenticator.principal() [line 307-317]
    - Creates SaslAuthenticationContext
    - Calls principalBuilder.build(context)
    - Returns KafkaPrincipal used for authorization
```

**Dependency Chain (SCRAM)**:
1. NetworkReceive (network I/O boundary)
2. SaslServerAuthenticator.authenticate() (state machine)
3. SaslServerAuthenticator.handleSaslToken()
4. ScramSaslServer.evaluateResponse() (RFC 5802 message parsing)
5. ScramServerCallbackHandler.handle() (credential cache lookup)
6. ScramSaslServer.verifyClientProof() (HMAC verification)
7. DefaultKafkaPrincipalBuilder.build() (principal extraction)

### Flow 3: OAUTHBEARER Authentication Token Exchange

```
1. Source: NetworkReceive.readFrom() [SaslServerAuthenticator.java:264]
   - Untrusted input: Raw socket bytes

2-3. Transform: Same as PLAIN/SCRAM flows through SaslServerAuthenticator

4. Transform: OAuthBearerSaslServer.evaluateResponse(byte[] response) [line 85-102]
   - Parses OAuthBearerClientInitialResponse [line 95]
   - Extracts: tokenValue (JWT string), authorizationId, extensions
   - tokenValue is untrusted client-provided JWT [line 101]

5. Callback: OAuthBearerValidatorCallbackHandler.handle()
   - Receives OAuthBearerValidatorCallback
   - Validates JWT token signature and claims
   - Can be customized per deployment; default is OAuthBearerUnsecuredValidatorCallbackHandler

6. Token Extraction: OAuthBearerSaslServer.getAuthorizationID() [line 104-109]
   - Returns tokenForNegotiatedProperty.principalName()
   - principalName() extracted from JWT claims during validation

7. Sink: SaslServerAuthenticator.principal()
    - Creates SaslAuthenticationContext
    - Calls principalBuilder.build(context)
    - Returns KafkaPrincipal based on JWT token principal
```

---

## SASL Handshake Protocol Flow

1. **ApiVersionsRequest** (Optional, KIP-43)
   - File: `SaslServerAuthenticator.java:572-586`
   - Client sends ApiVersionsRequest to discover supported API versions
   - Server responds with ApiVersionsResponse
   - Transitions state to HANDSHAKE_REQUEST

2. **SaslHandshakeRequest**
   - File: `SaslServerAuthenticator.java:549-565`
   - Client specifies SASL mechanism name
   - **CRITICAL ENTRY POINT**: Mechanism name is client-controlled string
   - Server validates against enabled mechanisms list
   - Server responds with SaslHandshakeResponse containing supported mechanisms
   - If mechanism not supported: UnsupportedSaslMechanismException thrown

3. **SaslAuthenticate Requests (Optional, KIP-152)**
   - File: `SaslServerAuthenticator.java:433-499`
   - For SASL protocol v1+: authentication tokens wrapped in Kafka SaslAuthenticateRequest
   - Header format allows client to specify protocol version
   - Server extracts authBytes and processes via mechanism handler

4. **Legacy SASL (Pre-KIP-43)**
   - File: `SaslServerAuthenticator.java:422-432`
   - Tokens sent as raw size-delimited bytes
   - Passed directly to SaslServer.evaluateResponse()

---

## Analysis

### Vulnerability Class: Principal Injection & Spoofing

#### Path 1: Mechanism Selection → Callback Handler Dispatch

**Risk**: Attacker provides unsupported mechanism name → server rejects gracefully (correct)

**Code**: `SaslServerAuthenticator.handleHandshakeRequest()` [line 549-565]
- Mechanism name from `handshakeRequest.data().mechanism()` is untrusted
- Validation: `if (enabledMechanisms.contains(clientMechanism))` [line 554]
- Enabled mechanisms configured server-side in BrokerSecurityConfigs.SASL_ENABLED_MECHANISMS_CONFIG
- **Mitigation**: Whitelist-based validation prevents arbitrary mechanism names
- **Gap**: No mitigation against selecting a weaker mechanism if multiple are enabled (e.g., PLAIN vs SCRAM)

#### Path 2: PLAIN Credential Parsing → SQL/Code Injection

**Risk**: Malformed PLAIN token could bypass parsing validation

**Code**: `PlainSaslServer.evaluateResponse()` [line 85-114]
```java
String response = new String(responseBytes, StandardCharsets.UTF_8);
List<String> tokens = extractTokens(response);  // Split by NUL
```

**Untrusted Input**: Full UTF-8 string from client including [authzid]\0[authcid]\0[passwd]
- Username component can contain any UTF-8 characters (RFC 4616 allows any SAFE chars)
- JAAS configuration lookup: `"user_" + username` [PlainServerCallbackHandler line 66]

**Mitigation**:
- Token parsing is strict (exactly 3 tokens required) [PlainSaslServer:129-131]
- Lookup is via configuration entry (static, no injection possible)
- Credential comparison uses constant-time function [PlainServerCallbackHandler:68]

**Actual Risk**: Username is directly exposed in JAAS config; no escaping of special characters
- If JAAS config allows shell interpolation or other dynamic features, untrusted username could exploit
- However, JAAS entries are static AppConfigurationEntry objects, not shell-parsed

#### Path 3: SCRAM Message Parsing → Nonce Validation Bypass

**Risk**: Client provides mismatched nonce → authentication failure (correct)

**Code**: `ScramSaslServer.evaluateResponse()` [line 147-162]
```java
if (!clientFinalMessage.nonce().equals(serverFirstMessage.nonce())) {
    throw new SaslException("Invalid client nonce in the final client message.");
}
```

**Mitigation**: Server generates random nonce; client must echo it back
- Nonce comparison is equality check (timing-safe String.equals in Java)
- Prevents replay of stale tokens

**Gap**: If serverFirstMessage.nonce() is predictable or reused, attacker could forge token
- But nonce is generated via `formatter.secureRandomString()` [line 106]
- ScramFormatter should use SecureRandom (needs code inspection)

#### Path 4: SCRAM Proof Verification → Timing Attack

**Risk**: Non-constant-time comparison of HMAC could leak credential via timing

**Code**: `ScramSaslServer.verifyClientProof()` [line 232]
```java
if (!MessageDigest.isEqual(computedStoredKey, expectedStoredKey))
    throw new SaslException("Invalid client credentials");
```

**Mitigation**: Uses `MessageDigest.isEqual()` which is constant-time [Java spec guarantees]
- Introduced in Java 6 for exactly this purpose
- Compares every byte regardless of match

**Strength**: Properly mitigated for SCRAM

#### Path 5: OAUTHBEARER Token Validation → Missing Validation

**Risk**: Default validator is "unsecured" (debug-only)

**Code**: `SaslChannelBuilder.createServerCallbackHandlers()` [line 330-331]
```java
else if (mechanism.equals(OAuthBearerLoginModule.OAUTHBEARER_MECHANISM))
    callbackHandler = new OAuthBearerUnsecuredValidatorCallbackHandler();
```

**Untrusted Input**: Client-provided JWT token string

**Mitigation**:
- Uses OAuthBearerUnsecuredValidatorCallbackHandler as DEFAULT
- Name suggests it's unsecured; suitable only for development
- Production deployments MUST replace with proper validator (via config)
- Callback handler can be customized via: `sasl.oauthbearer.token.endpoint.url`

**Gap**: Easy to accidentally deploy with unsecured validator
- Documentation must strongly warn against production use
- No runtime check to prevent production deployment with unsecured validator

### Vulnerability Class: Authorization ID Confusion

#### Path: Multiple SASL Mechanisms → Principal Name Variation

**Risk**: Same username under different mechanisms could have different security properties

**Example**:
- PLAIN: "admin" (transmitted in cleartext if not TLS)
- SCRAM: "admin" (hashed salt/iterations stored server-side)
- OAUTHBEARER: "admin@org.example" (JWT token with claims)

**Code**: `DefaultKafkaPrincipalBuilder.build()` [line 79-84]
```java
else if (context instanceof SaslAuthenticationContext) {
    SaslServer saslServer = ((SaslAuthenticationContext) context).server();
    if (SaslConfigs.GSSAPI_MECHANISM.equals(saslServer.getMechanismName()))
        return applyKerberosShortNamer(saslServer.getAuthorizationID());
    else
        return new KafkaPrincipal(KafkaPrincipal.USER_TYPE, saslServer.getAuthorizationID());
}
```

**Untrusted Input**: AuthorizationID from SaslServer.getAuthorizationID()
- PLAIN: Directly from client SASL response
- SCRAM: Parsed from ClientFirstMessage
- OAUTHBEARER: From JWT principalName claim
- GSSAPI: Parsed Kerberos principal

**Mitigation**:
- AuthorizationID is validated at protocol level (non-empty, matches authenticationID in some cases)
- SCRAM-specific: Authorization ID validation at line 130-131 (ScramSaslServer)
  ```java
  if (!authorizationIdFromClient.isEmpty() && !authorizationIdFromClient.equals(username))
      throw new SaslAuthenticationException("...authorization id that is different from username");
  ```
- PLAIN-specific: Same validation at PlainSaslServer line 107-108

**Gap**: No cross-mechanism validation
- If admin configured PLAIN but attacker uses SCRAM with same username, could bypass intended PLAIN-only security policy
- Mitigation: Configure sasl.enabled.mechanisms per listener to enforce mechanism restrictions

### Vulnerability Class: Information Disclosure → Error Messages

#### Path: Authentication Failure Error Messages

**Risk**: Overly detailed error messages leak information to unauthenticated clients

**Code**: `SaslServerAuthenticator.handleSaslToken()` [line 481-497]
```java
catch (SaslException e) {
    KerberosError kerberosError = KerberosError.fromException(e);
    if (kerberosError != null && kerberosError.retriable()) {
        throw e;
    } else {
        // DO NOT include error message from the `SaslException` in the client response since it may
        // contain sensitive data like the existence of the user.
        String errorMessage = "Authentication failed during "
            + reauthInfo.authenticationOrReauthenticationText()
            + " due to invalid credentials with SASL mechanism " + saslMechanism;
        buildResponseOnAuthenticateFailure(...);
        throw new SaslAuthenticationException(errorMessage, e);
    }
}
```

**Mitigation**:
- Original SaslException message is NOT sent to client [line 488 comment]
- Generic message sent instead: "Authentication failed... due to invalid credentials"
- Prevents leaking usernames, password hints, or internal state

**Strength**: Properly mitigated for non-Kerberos mechanisms

**Gap for PLAIN**:
- `PlainSaslServer.evaluateResponse()` can throw custom exceptions with info [line 92-108]
  ```java
  if (username.isEmpty()) {
      throw new SaslAuthenticationException("Authentication failed: username not specified");
  }
  ```
- These are caught and wrapped by SaslServerAuthenticator, so not leaked [line 295]
- **Mitigation**: Exception wrapping prevents leakage

**Gap for SCRAM**:
- Credential callback can fail with detailed message
- Wrapped at line 295: `catch (AuthenticationException e)`

### Vulnerability Class: Denial of Service → Resource Exhaustion

#### Path: Large SASL Token Receives

**Risk**: Client sends extremely large SASL token → exhausts memory/CPU

**Code**: `SaslServerAuthenticator.authenticate()` [line 261]
```java
if (netInBuffer == null)
    netInBuffer = new NetworkReceive(saslAuthRequestMaxReceiveSize, connectionId);
```

**Size Limit**: `saslAuthRequestMaxReceiveSize` configured via:
- BrokerSecurityConfigs.SASL_SERVER_MAX_RECEIVE_SIZE_CONFIG [line 195]
- Defaults to BrokerSecurityConfigs.DEFAULT_SASL_SERVER_MAX_RECEIVE_SIZE

**Code**: `NetworkReceive.readFrom()` [line 94-95]
```java
if (maxSize != UNLIMITED && receiveSize > maxSize)
    throw new InvalidReceiveException("Invalid receive (size = " + receiveSize + " larger than " + maxSize + ")");
```

**Mitigation**:
- Size checked against configurable limit before allocation
- Invalid size throws exception, closes connection
- Prevents unbounded memory allocation

**Strength**: Properly mitigated

### Vulnerability Class: Re-authentication → Principal Change

#### Path: Session Hijacking via Re-authentication

**Risk**: Client re-authenticates with different mechanism/username → changes principal

**Code**: `SaslServerAuthenticator.reauthenticate()` [line 343-357]
```java
SaslServerAuthenticator previousSaslServerAuthenticator = (SaslServerAuthenticator) reauthenticationContext.previousAuthenticator();
reauthInfo.reauthenticating(previousSaslServerAuthenticator.saslMechanism,
        previousSaslServerAuthenticator.principal(), reauthenticationContext.reauthenticationBeginNanos());
```

**Mechanism Check**: `SaslServerAuthenticator.handleHandshakeRequest()` [line 532]
```java
if (!reauthInfo.reauthenticating() || reauthInfo.saslMechanismUnchanged(clientMechanism)) {
    createSaslServer(clientMechanism);
    setSaslState(SaslState.AUTHENTICATE);
}
```

**Principal Check**: `SaslServerAuthenticator.handleSaslToken()` [line 463-464]
```java
if (reauthInfo.reauthenticating() && saslServer.isComplete())
    reauthInfo.ensurePrincipalUnchanged(principal());
```

**Mitigation**:
1. Mechanism must remain unchanged [line 656-664]
   ```java
   public boolean saslMechanismUnchanged(String clientMechanism) {
       if (previousSaslMechanism.equals(clientMechanism))
           return true;
       badMechanismErrorMessage = String.format(
           "SASL mechanism '%s' requested by client is not supported for re-authentication of mechanism '%s'",
           clientMechanism, previousSaslMechanism);
       return false;
   }
   ```

2. Principal must remain unchanged [line 642-649]
   ```java
   public void ensurePrincipalUnchanged(KafkaPrincipal reauthenticatedKafkaPrincipal) throws SaslAuthenticationException {
       if (!previousKafkaPrincipal.equals(reauthenticatedKafkaPrincipal)) {
           throw new SaslAuthenticationException(String.format(
               "Cannot change principals during re-authentication from %s.%s: %s.%s",
               ...
           ));
       }
   }
   ```

**Strength**: Properly mitigated; prevents principal change on re-auth

---

## Summary

### Overall Authentication Architecture

The Apache Kafka SASL authentication system uses a **multi-stage gateway pattern**:

1. **Untrusted Data Boundary**: NetworkReceive accepts size-delimited bytes from socket
2. **Protocol Parsing**: RequestHeader.parse() identifies API type; SaslHandshakeRequest selects mechanism
3. **Mechanism Dispatch**: Selected mechanism's SaslServer handles token exchange
   - PLAIN: Parses [authzid]\0[username]\0[password]; credential lookup via JAAS
   - SCRAM: RFC 5802 challenge-response; HMAC-based proof verification
   - OAUTHBEARER: JWT token validation via callback handler
   - GSSAPI: Java SASL delegation to system libraries
4. **Principal Extraction**: KafkaPrincipalBuilder converts mechanism-specific AuthorizationID to KafkaPrincipal
5. **Authorization Enforcement**: Broker checks KafkaPrincipal against ACL store (outside SASL subsystem)

### Security Properties

**Strengths**:
- **Mechanism Whitelisting**: Only enabled mechanisms accepted; prevents downgrade attacks
- **Credential Comparison**: Constant-time password comparison (PLAIN) and message digest comparison (SCRAM)
- **Token Validation**: SCRAM nonce validation prevents replay; OAUTHBEARER supports JWT validation
- **Error Suppression**: Authentication exception details not leaked to clients
- **Size Limits**: SASL token receive size bounded to prevent memory exhaustion
- **Re-authentication Protection**: Mechanism and principal must remain unchanged during session re-authentication

**Gaps & Weaknesses**:
1. **OAUTHBEARER Default**: Unsecured validator in default configuration; easy misdeployment risk
2. **Mechanism Downgrade**: If multiple mechanisms enabled, attacker can select weaker one
3. **Principal Name Injection**: While validated at protocol level, principal names are user-controlled and passed to KafkaPrincipalBuilder; custom builders must handle carefully
4. **PLAIN over Unencrypted Protocol**: PLAIN credentials sent in cleartext unless TLS enabled; misconfiguration risk
5. **Authorization ID Confusion**: No validation that same username under different mechanisms has same privileges
6. **Kerberos Short-Name Transformation**: DefaultKafkaPrincipalBuilder applies regex transformations; malformed principal could fail transformation (caught at line 95-97, but error handling worth auditing)

### Recommended Mitigations

1. **Configuration Hardening**:
   - Use SCRAM-SHA-256 or OAUTHBEARER in production (not PLAIN)
   - Require SASL_SSL (not SASL_PLAINTEXT) to encrypt credentials
   - Disable PLAIN mechanism if not needed

2. **OAUTHBEARER Deployment**:
   - Replace OAuthBearerUnsecuredValidatorCallbackHandler with proper JWT validator
   - Validate token signature, expiration, and claims
   - Use custom KafkaPrincipalBuilder if token structure differs from expectations

3. **Kerberos (GSSAPI) Hardening**:
   - Configure Kerberos short-name rules to prevent principal confusion
   - Test short-name rules thoroughly with all expected principal formats
   - Monitor for principal transformation errors in logs

4. **ACL Configuration**:
   - Audit ACL rules when changing authentication mechanisms
   - Ensure principal names match between auth and ACL systems
   - Use custom Authorizer if complex authorization logic needed

5. **Network Segmentation**:
   - Restrict SASL_PLAINTEXT usage to internal networks
   - Monitor for PLAIN mechanism usage; log and alert if detected

---

## Reference Implementation Flow Diagram

```
┌─────────────────┐
│  Client Socket  │
└────────┬────────┘
         │ raw bytes (size-delimited)
         ▼
┌──────────────────────────────┐
│   NetworkReceive.readFrom()  │ ◄── ENTRY POINT 1: Untrusted data
│   (max size validated)       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ SaslServerAuthenticator.authenticate()│ ◄── ENTRY POINT 2: State machine
│ (switches on saslState)              │
└─────┬──────────────────┬─────────────┘
      │                  │
      ▼ (HANDSHAKE)      ▼ (AUTHENTICATE)
┌──────────────────────┐ ┌────────────────────────┐
│ handleKafkaRequest() │ │ handleSaslToken()      │
│ - Parse ApiVersions  │ │ - Extract token        │
│ - Parse SaslHandshake│ │ - Route to SaslServer  │
└──────────┬───────────┘ └────────┬───────────────┘
           │                      │
           │ (gets mechanism)     │
           │                      ▼
           └─────────────────────► ┌──────────────────────────────┐
                                   │ SaslServer.evaluateResponse()  │
                                   │ (mechanism-specific)          │
                                   └─────┬──────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
              ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
              │ PlainSaslServer  │ │ ScramSaslServer  │ │OAuthBearerServer │
              │ - Parse 3-tuple  │ │ - RFC 5802 msgs  │ │ - Parse JWT      │
              │ - Call callback  │ │ - HMAC verify    │ │ - Callback valid │
              └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────────┐
                              │ getAuthorizationID()        │
                              │ (extract principal name)    │
                              └────────────┬────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────────┐
                              │ SaslAuthenticationContext   │ ◄── ENTRY POINT 3: Auth context
                              │ (carries SaslServer + meta) │
                              └────────────┬────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────────┐
                              │ KafkaPrincipalBuilder.build()│ ◄── ENTRY POINT 4: Principal build
                              │ (DefaultKafkaPrincipalBuilder)
                              └────────────┬────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────────┐
                              │ KafkaPrincipal              │
                              │ (USER_TYPE, name, ...)     │
                              └────────────┬────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────────┐
                              │ Authorizer.authorize()      │
                              │ [Outside SASL subsystem]    │
                              └─────────────────────────────┘
```
