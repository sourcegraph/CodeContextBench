# Security Reachability Analysis: curl SOCKS5 Proxy Handler

## 1. Summary

This analysis examines the reachability of the `do_SOCKS5()` function in curl's SOCKS5 proxy implementation. The function is responsible for handling the SOCKS5 handshake protocol and processing responses from SOCKS5 proxy servers.

**Conclusion: REACHABLE from external network input**

The `do_SOCKS5()` function is directly reachable and exploitable through a compromised or malicious SOCKS5 proxy server. An attacker controlling or performing a man-in-the-middle (MITM) attack on a proxy can craft malicious SOCKS5 responses that trigger code execution paths in this function. However, the current buffer allocation (16384 bytes) mitigates potential buffer overflow attacks through careful bounds management.

---

## 2. Affected Code

### Function
- **Function Name**: `do_SOCKS5()`
- **Location**: `/workspace/lib/socks.c`, lines 548–1054
- **Type**: Static function (internal to socks.c)

### Purpose
The `do_SOCKS5()` function implements the complete SOCKS5 (RFC 1928) handshake protocol. It:
1. Sends the initial client greeting with available authentication methods
2. Negotiates authentication with the proxy server (username/password or GSS-API)
3. Constructs and sends the connection request with destination hostname/IP
4. Receives and validates the proxy's response
5. Reads variable-length response data based on the address type in the response

### Key Characteristics
- Processes binary protocol data received from a remote SOCKS5 proxy server
- Uses a fixed-size buffer (`data->state.buffer`) for sending and receiving protocol messages
- Implements a state machine with multiple states to handle asynchronous non-blocking I/O
- Performs minimal validation on proxy responses before processing them

---

## 3. Attack Path

### Complete Call Chain

```
User Application (curl CLI or libcurl API)
  ↓
curl_easy_perform() [easy.c:786]
  ↓
easy_perform() [easy.c:721]
  ↓
easy_transfer() or easy_events() [easy.c:769]
  ↓
Multi loop (multi.c) driving transfers
  ↓
Curl_connect() [url.c:3895]
  ↓
create_conn() → Curl_setup_conn() [url.c:3921]
  ↓
Curl_conn_setup() [url.c:3888]
  ↓
Curl_cf_setup_insert_after() [connect.c:1398]
  ↓
cf_setup_connect() [connect.c:1186] (filter's connect callback)
  ↓
Checks: if(cf->conn->bits.socksproxy)
  ↓
Curl_cf_socks_proxy_insert_after() [connect.c:1218, socks.c:1240]
  ↓
socks_proxy_cf_connect() [socks.c:1103]
  ↓
connect_SOCKS() [socks.c:1056]
  ↓
do_SOCKS5() [socks.c:548] ← VULNERABLE FUNCTION
```

### Function Roles in Call Chain

1. **curl_easy_perform()** (easy.c:786)
   - Public API entry point
   - User calls this after setting proxy with `CURLOPT_PROXY` or CLI `--proxy`

2. **easy_perform()** (easy.c:721)
   - Sets up the multi handle
   - Calls the transfer engine

3. **Curl_connect()** (url.c:3895)
   - Main connection initiator
   - Calls `Curl_setup_conn()` to establish the connection chain

4. **Curl_conn_setup()** (url.c:3888)
   - Initializes the connection filter chain
   - Calls `Curl_cf_setup_insert_after()` to insert the setup filter

5. **cf_setup_connect()** (connect.c:1186)
   - Connection setup state machine filter
   - **Critical Check**: `if(ctx->state < CF_SETUP_CNNCT_SOCKS && cf->conn->bits.socksproxy)`
   - If true, calls `Curl_cf_socks_proxy_insert_after()` (line 1218)

6. **socks_proxy_cf_connect()** (socks.c:1103)
   - Top-level SOCKS proxy connection filter
   - Initializes the SOCKS state machine
   - Calls `connect_SOCKS()` to begin the handshake

7. **connect_SOCKS()** (socks.c:1056)
   - Routes to the appropriate SOCKS version handler
   - For SOCKS5: calls `do_SOCKS5(cf, sxstate, data)` (line 1067)

### External Input Entry Point

**Where external input enters the system:**

The `do_SOCKS5()` function receives data from the SOCKS5 proxy server at lines 646-647 and 952-953:

```c
// Line 646-647 (initial greeting response)
presult = socks_state_recv(cf, sx, data, CURLPX_RECV_CONNECT,
                           "initial SOCKS5 response");

// Line 952-953 (connection request response)
presult = socks_state_recv(cf, sx, data, CURLPX_RECV_REQACK,
                           "SOCKS5 connect request ack");
```

The `socks_state_recv()` function (lines 232–261) calls `Curl_conn_cf_recv()` which reads data from the network socket into the `socksreq` buffer (which is `data->state.buffer`).

**Data source**: Network data received from the SOCKS5 proxy server

---

## 4. Severity Assessment

### Reachability: YES - FULLY REACHABLE

The `do_SOCKS5()` function **is reachable from external input** with the following conditions:

#### Required Attacker Actions

1. **Control the SOCKS5 proxy server**, OR
2. **Perform a man-in-the-middle (MITM) attack** on the connection between curl and a legitimate SOCKS5 proxy

#### Trigger Conditions

The function is reached when:
```
1. User configures a SOCKS5 proxy:
   - CLI: curl --proxy socks5://proxy:1080 https://example.com
   - API: curl_easy_setopt(handle, CURLOPT_PROXY, "socks5://proxy:1080")

2. User initiates an HTTP/HTTPS request through the proxy

3. The curl client connects to the proxy server

4. The proxy server (controlled by attacker) sends responses
```

#### Attack Vector

**Scenario**: Attacker controls or intercepts a SOCKS5 proxy connection

```
curl client                Proxy Server (Attacker Controlled)
    |                            |
    |--- Send SOCKS5 ----->     |
    |     greeting               |
    |                            |
    |<---- Send malicious ------|
    |     SOCKS5 response        |
    |     (do_SOCKS5 processes)  |
    |                            |
    |<---- More responses -------|
    |     (crafted to trigger     |
    |      code paths)           |
```

**External Input that Reaches the Function**:
- SOCKS5 proxy server's responses (completely attacker-controlled)
- Proxy response format: `[VER|REP|RSV|ATYP|BND.ADDR|BND.PORT]`
- Each field can be crafted by the attacker

### Attack Vector Details

The attacker can influence the code path by manipulating:

1. **Authentication Method Selection** (lines 658–689)
   - By sending `socksreq[1]` value, control whether authentication is required
   - Possible values: 0 (none), 1 (GSS-API), 2 (username/password), 255 (no acceptable method)

2. **Address Type in Response** (line 1005–1020)
   - Set `socksreq[3]` to 1 (IPv4), 3 (domain), or 4 (IPv6)
   - Controls how much data is read from the response

3. **Domain Name Length** (line 1007)
   - If ATYP = 3, `socksreq[4]` specifies domain name length
   - Allows attacker to craft response with length 0–255
   - Controls how many bytes are read at line 1028–1030

### Potential Vulnerabilities

#### 1. Buffer Overflow in Response Parsing (Mitigated)

**Location**: Lines 1005–1030

```c
if(socksreq[3] == 3) {
  int addrlen = (int) socksreq[4];
  len = 5 + addrlen + 2;
}

if(len > 10) {
  sx->outstanding = len - 10; /* get the rest */
  sx->outp = &socksreq[10];
  sxstate(sx, data, CONNECT_REQ_READ_MORE);
}
```

**Risk**: If `addrlen` is large, `len` could exceed buffer capacity.

**Current Status**: **MITIGATED**
- Maximum `addrlen`: 255 (single byte in SOCKS5 protocol)
- Maximum `len`: 5 + 255 + 2 = 262 bytes
- Buffer size: 16384 bytes (CURL_MAX_WRITE_SIZE, default)
- Buffer is allocated with adequate margin (262 << 16384)

**However**: No explicit bounds check in code. Buffer overflow would occur if:
- Buffer size was reduced below 262 bytes
- Code logic changes without updating buffer checks
- Integer truncation during cast

#### 2. Hostname Length Cast Vulnerability (Mitigated)

**Location**: Line 906

```c
socksreq[len++] = (char) hostname_len;  /* one byte address length */
```

**Risk**: `hostname_len` (size_t) cast to `char` could truncate.

**Current Status**: **MITIGATED**
- Check at lines 589–592 enforces `hostname_len <= 255` when sending
- If `hostname_len > 255`, code forces local DNS resolution
- Domain name is never sent to proxy with truncated length

#### 3. Unvalidated Response Structure (PARTIAL CONCERN)

**Location**: Lines 654–692 (authentication response validation)

```c
else if(socksreq[1] == 0) {
  /* DONE! No authentication needed */
  sxstate(sx, data, CONNECT_REQ_INIT);
  goto CONNECT_REQ_INIT;
}
```

**Risk**: Proxy can send unexpected authentication method values.

**Current Status**: **MITIGATED**
- Invalid authentication methods are detected at lines 678–692
- Function returns error code for unsupported methods

### Exploitability Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| **Reachability** | ✅ YES | Network-accessible through SOCKS5 proxy responses |
| **Attack Trigger** | ✅ YES | User must configure SOCKS5 proxy (no unexpected trigger) |
| **External Input** | ✅ YES | Complete protocol response controlled by proxy server |
| **Code Execution** | ⚠️ LIMITED | Current buffer size prevents overflow, but parsing is unvalidated |
| **Information Disclosure** | ⚠️ POSSIBLE | Could leak buffer contents if response processing is incomplete |
| **Denial of Service** | ⚠️ POSSIBLE | Malformed responses could cause infinite loops in state machine |

---

## 5. Remediation

### Defense-in-Depth Improvements

Even though the current buffer allocation mitigates overflow, the following improvements would strengthen the code:

#### 1. Explicit Buffer Bounds Checking (RECOMMENDED)

Add bounds validation before reading response data:

```c
/* Calculate real packet size */
if(socksreq[3] == 3) {
  int addrlen = (int) socksreq[4];
  len = 5 + addrlen + 2;

  /* Validate calculated size against buffer */
  if(len > READBUFFER_SIZE) {
    failf(data, "SOCKS5 response packet too large");
    return CURLPX_BAD_OUTBUF;
  }
}
```

#### 2. Timeout Protection for Variable-Length Reads (RECOMMENDED)

Add timeout handling for reads waiting for variable-length response data:

```c
case CONNECT_REQ_READ_MORE:
  /* Add timeout check before reading */
  timediff_t timeout_ms = Curl_timeleft(data, NULL, FALSE);
  if(timeout_ms <= 0) {
    failf(data, "SOCKS5 response timeout");
    return CURLPX_TIMEOUT;
  }
  presult = socks_state_recv(cf, sx, data, ...);
```

#### 3. Validate Response Version (ALREADY DONE)

Good: Lines 654–656 validate SOCKS5 version in response:
```c
else if(socksreq[0] != 5) {
  failf(data, "Received invalid version in initial SOCKS5 response.");
  return CURLPX_BAD_VERSION;
}
```

#### 4. Maximum Hostname Length Enforcement (ALREADY DONE)

Good: Lines 589–592 enforce RFC 1928 compliance:
```c
if(!socks5_resolve_local && hostname_len > 255) {
  infof(data, "SOCKS5: server resolving disabled for hostnames of "
        "length > 255 [actual len=%zu]", hostname_len);
  socks5_resolve_local = TRUE;
}
```

#### 5. Add Response Sanity Checks

Validate that response fields match expected protocol format:

```c
/* After reading first 10 bytes, validate structure */
if(socksreq[2] != 0) {  /* RSV field must be 0 */
  failf(data, "SOCKS5 reserved field non-zero");
  return CURLPX_BAD_REPLY;
}

/* For domain name responses, ensure length is reasonable */
if(socksreq[3] == 3) {
  int addrlen = (int) socksreq[4];
  if(addrlen == 0) {
    failf(data, "SOCKS5 domain name length cannot be zero");
    return CURLPX_BAD_REPLY;
  }
}
```

### Summary of Current Protections

✅ **Adequate**:
- Buffer size (16384 bytes) prevents overflow from max SOCKS5 response (262 bytes)
- Hostname length validation before sending
- Version validation in response
- Invalid ATYP handling with error return

⚠️ **Could be improved**:
- No explicit bounds check on calculated packet size
- No timeout protection for variable-length reads
- Minimal validation of response field values beyond version and ATYP

---

## 6. Conclusion

The `do_SOCKS5()` function in `/workspace/lib/socks.c` is **REACHABLE from external network input** through SOCKS5 proxy server responses. An attacker controlling a SOCKS5 proxy or performing a MITM attack can send crafted protocol messages that trigger various code paths in this function.

**Current Risk Level**: **LOW to MEDIUM**

The immediate buffer overflow risk is mitigated by the large default buffer allocation (16384 bytes) relative to the maximum response size (262 bytes for domain name responses). However, the parsing logic lacks explicit bounds checking, which could become problematic if:
- Buffer size is changed
- Protocol parsing logic is modified
- Additional response types are supported

**Recommended Actions**:
1. Add explicit buffer bounds validation before calculating response sizes
2. Implement timeout protection for variable-length reads
3. Add protocol field sanity checks (RSV field, minimum domain name length)
4. Document the maximum expected SOCKS5 response size in comments
5. Consider using safer parsing functions that enforce bounds

**No immediate code fix is required** if buffer allocation is guaranteed to remain ≥ 262 bytes, but defense-in-depth improvements are recommended for long-term maintainability and robustness.
