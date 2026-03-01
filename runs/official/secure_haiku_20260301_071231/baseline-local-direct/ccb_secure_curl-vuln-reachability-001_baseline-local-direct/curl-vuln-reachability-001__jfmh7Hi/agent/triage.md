# Security Reachability Analysis: curl SOCKS5 Proxy Handler (`do_SOCKS5()`)

## Summary

The `do_SOCKS5()` function implemented in `lib/socks.c` is **REACHABLE** from external input when using a SOCKS5 proxy. This function is directly reachable when:
1. A user specifies a SOCKS5 proxy configuration via the `--proxy socks5://...` command-line flag or the `CURLOPT_PROXY` API
2. The curl client attempts to establish a connection through the specified SOCKS5 proxy
3. The SOCKS5 proxy server (which may be attacker-controlled) sends responses that are parsed by this function

The `do_SOCKS5()` function processes SOCKS5 proxy handshake and authentication, including parsing server responses that contain attacker-controlled data.

---

## Affected Code

**Function**: `do_SOCKS5()`
**File**: `/workspace/lib/socks.c:548-1054`
**Description**:
- Implements SOCKS5 proxy authentication and connection negotiation per RFC 1928
- Handles the complete SOCKS5 handshake including:
  - Initial protocol version negotiation
  - Authentication method selection (none, username/password, or GSSAPI)
  - Username/password authentication exchange
  - Connection request to remote host
  - Parsing of server responses (including variable-length address fields)
- Processes responses from the SOCKS5 proxy server, which are potentially attacker-controlled

---

## Attack Path

### Complete Call Chain

```
curl_easy_perform() / curl_multi_perform()
  ↓
multi_runsingle() [lib/multi.c:1868]
  ↓
Curl_connect() [lib/url.c:3895]
  ↓
create_conn() → Curl_setup_conn()
  ↓
Curl_conn_setup() [lib/connect.c]
  ↓
cf_setup_connect() [lib/connect.c:1186]
  ↓
Curl_cf_socks_proxy_insert_after() [lib/socks.c:1240]
  ↓
socks_proxy_cf_connect() [lib/socks.c:1103]
  ↓
connect_SOCKS() [lib/socks.c:1056]
  ↓
do_SOCKS5() [lib/socks.c:548] ← VULNERABLE FUNCTION
```

### Function Roles in Call Chain

1. **curl_easy_perform() / curl_multi_perform()** (user entry point)
   - Main user-facing API that initiates the transfer
   - User specifies proxy via `--proxy` flag or CURLOPT_PROXY option

2. **multi_runsingle()** [lib/multi.c:1868]
   - Main state machine for transfer operations
   - Orchestrates connection establishment and protocol handling
   - Calls `Curl_connect()` when in MSTATE_CONNECT state (line 1962)

3. **Curl_connect()** [lib/url.c:3895]
   - High-level connection coordinator
   - Initiates connection setup via `Curl_setup_conn()`

4. **Curl_conn_setup()** [lib/connect.c]
   - Validates proxy configuration and DNS information
   - Sets up filter chain for the connection

5. **cf_setup_connect()** [lib/connect.c:1186]
   - Connection filter setup state machine
   - Determines which filters to insert based on proxy type
   - **Key decision point** (line 1217): If `cf->conn->bits.socksproxy` is true, calls `Curl_cf_socks_proxy_insert_after()`

6. **Curl_cf_socks_proxy_insert_after()** [lib/socks.c:1240]
   - Creates and inserts the SOCKS proxy connection filter
   - Allocates the socks_state structure

7. **socks_proxy_cf_connect()** [lib/socks.c:1103]
   - Connection filter's connect handler
   - Initializes socks_state with target hostname and port
   - **Key data sources** (line 1133-1146):
     - `sx->hostname` ← User-provided hostname from HTTP/HTTPS request
     - `sx->remote_port` ← User-provided port
     - `sx->proxy_user` ← Proxy credentials from proxy URL
     - `sx->proxy_password` ← Proxy credentials from proxy URL
   - Calls `connect_SOCKS()` to perform SOCKS negotiation

8. **connect_SOCKS()** [lib/socks.c:1056]
   - Dispatcher function that routes to the appropriate SOCKS handler
   - **Decision point** (line 1064-1073): Routes to `do_SOCKS5()` if proxy type is SOCKS5 or SOCKS5_HOSTNAME

9. **do_SOCKS5()** [lib/socks.c:548] ← **VULNERABLE FUNCTION**
   - Executes SOCKS5 protocol state machine
   - **External input received here**:
     - SOCKS5 server responses (lines 645-692): authentication method selection
     - SOCKS5 server authentication challenge responses (line 762-776)
     - SOCKS5 server connection response (line 951-1049): includes BND.ADDR field with variable length

---

## Severity Assessment

### Reachability: YES - REACHABLE

**Conditions for Reaching `do_SOCKS5()`:**

1. **User Action**: User must specify a SOCKS5 proxy:
   ```bash
   curl https://example.com --proxy socks5://proxy.example.com:1080
   # OR via API
   curl_easy_setopt(handle, CURLOPT_PROXY, "socks5://proxy.example.com:1080");
   ```

2. **Network Condition**:
   - The SOCKS5 proxy must be reachable from the client
   - A TCP connection to the proxy's port must be established
   - The proxy must respond with SOCKS5 protocol messages

### Attack Vector

An attacker can trigger `do_SOCKS5()` execution by:

1. **Controlling the SOCKS5 proxy server**
   - Deploy a malicious SOCKS5 proxy on a network path
   - Intercept traffic to a legitimate proxy (MITM attack)
   - Compromise a legitimate proxy server

2. **Social engineering**
   - Trick users into configuring curl to use an attacker-controlled proxy
   - Distribute scripts/configurations that specify malicious proxy

3. **Supply chain compromise**
   - Inject proxy configuration in shared scripts or deployment tools
   - Modify environment variables or proxy auto-config (PAC) files

### External Input Reaching `do_SOCKS5()`

The following data from the SOCKS5 proxy server reaches `do_SOCKS5()`:

1. **Authentication Method Response** (line 645):
   ```c
   /* socksreq[1] contains the selected authentication method */
   socksreq[0]  // Protocol version (expected: 5)
   socksreq[1]  // Selected auth method (0, 1, 2, or 255)
   ```
   **Source**: Untrusted SOCKS5 server response
   **Impact**: Determines authentication path; invalid values handled with error checks

2. **Authentication Response** (line 762):
   ```c
   /* For username/password authentication */
   socksreq[0]  // Subnegotiation version
   socksreq[1]  // Status (0 = success, non-zero = failure)
   ```
   **Source**: Untrusted SOCKS5 server response
   **Impact**: Determines if authentication succeeds; invalid responses cause connection termination

3. **Connection Response - Variable Length Address** (line 1005-1020):
   ```c
   if(socksreq[3] == 3) {
     /* domain name: length is in socksreq[4] */
     int addrlen = (int) socksreq[4];  // ← ATTACKER-CONTROLLED VALUE
     len = 5 + addrlen + 2;
   }
   else if(socksreq[3] == 4) {
     /* IPv6: 16 bytes */
     len = 4 + 16 + 2;
   }
   else if(socksreq[3] == 1) {
     /* IPv4: 4 bytes */
     len = 4 + 4 + 2;
   }
   ```
   **Source**: SOCKS5 server response (BND.ADDR field), specifically ATYP field
   **Impact**: Determines how many bytes to read from the response stream
   **Attacker Control**: Complete control over `socksreq[3]` and `socksreq[4]` values

### Vulnerability Analysis

**Potential Issue: Integer Overflow / Underflow**

At line 1007, the code casts an unsigned char to a signed int:
```c
int addrlen = (int) socksreq[4];  // socksreq[4] is unsigned char (0-255)
len = 5 + addrlen + 2;
```

**Assessment**: NOT VULNERABLE
- `socksreq[4]` is an unsigned char, range 0-255
- Casting to signed int cannot produce negative values
- Maximum `len = 5 + 255 + 2 = 262 bytes`
- Buffer (data->state.buffer) is guaranteed ≥ 1024 bytes (READBUFFER_MIN)
- 262 bytes is well within buffer bounds

**Potential Issue: Hostname Length Truncation**

At line 906, during remote resolution:
```c
socksreq[len++] = (char) hostname_len;  /* one byte address length */
memcpy(&socksreq[len], sx->hostname, hostname_len);
```

**Assessment**: PROTECTED
- Code explicitly checks for hostname_len > 255 at line 589:
```c
if(!socks5_resolve_local && hostname_len > 255) {
  infof(data, "SOCKS5: server resolving disabled for hostnames of "
        "length > 255 [actual len=%zu]", hostname_len);
  socks5_resolve_local = TRUE;
}
```
- If hostname exceeds 255 bytes, switches to local resolution to avoid this code path
- No buffer overflow possible

**Actual Issue: Denial of Service / Protocol Desynchronization**

While not a code execution vulnerability, there is a potential DoS issue:

At lines 1027-1030:
```c
if(len > 10) {
  sx->outstanding = len - 10;  /* bytes to read */
  sx->outp = &socksreq[10];
  sxstate(sx, data, CONNECT_REQ_READ_MORE);
}
```

If a malicious SOCKS5 server:
1. Sends `socksreq[3] = 3` (domain name type)
2. Sets `socksreq[4] = 255` (claim 255 bytes of domain)
3. Only sends partial data (e.g., 5 bytes)
4. Closes or stalls the connection

Then curl would either:
- **Hang indefinitely** waiting for 252 bytes that never arrive (socket timeout depending on curl settings)
- **Or timeout** if a read timeout is configured

**Impact**: Denial of Service (hang/timeout), not remote code execution

---

## Remediation

### Current State: PARTIALLY MITIGATED

The code already includes some safety measures:

1. **Hostname length validation** (line 589-592)
   - Prevents truncation of long hostnames
   - Switches to local resolution if hostname exceeds 255 bytes

2. **Buffer size guarantee** (line 287)
   - `DEBUGASSERT(READBUFFER_MIN >= 600)` ensures minimum 1024-byte buffer
   - Maximum possible packet size (262 bytes) is well within bounds

3. **Protocol validation** (line 654, 960-963)
   - Validates SOCKS5 version field
   - Returns error if version != 5

### Recommended Additional Hardening

**If code execution or memory corruption is the concern:**
- Current mitigations appear adequate
- The buffer size guarantee and hostname length check prevent overflow scenarios
- The maximum address field length (255 bytes) is inherently bounded by SOCKS5 RFC 1928

**If protocol robustness is the concern (prevent DoS/hang):**

1. **Add maximum response packet size validation**:
   ```c
   /* Calculate real packet size */
   if(socksreq[3] == 3) {
     int addrlen = (int) socksreq[4];
     len = 5 + addrlen + 2;
     /* Verify length is reasonable (add bounds check) */
     if(len > data->set.buffer_size) {
       failf(data, "SOCKS5 response packet too large");
       return CURLPX_GENERAL_SERVER_FAILURE;
     }
   }
   ```

2. **Add explicit timeout handling** for partial responses (already handled by curl's timeout system)

3. **Add logging of suspicious responses**:
   ```c
   if(len > 100) {  /* arbitrary threshold */
     infof(data, "SOCKS5: large response size %zu (addrlen=%d)", len, addrlen);
   }
   ```

### Assessment Summary

- **Buffer overflow**: NOT POSSIBLE - maximum response is 262 bytes, buffer is 1024+ bytes
- **Integer overflow**: NOT POSSIBLE - unsigned char to int cast is safe
- **Hostname truncation**: PROTECTED - code switches to local resolution for long hostnames
- **Denial of Service**: POSSIBLE - malicious server can send truncated responses causing hang
- **Remote Code Execution**: NOT POSSIBLE - no exploit path identified

---

## Conclusion

The `do_SOCKS5()` function is **REACHABLE from external input** when a user specifies a SOCKS5 proxy. However, **NO REMOTE CODE EXECUTION VULNERABILITY** is present in the current implementation. The code includes sufficient bounds checking and buffer management to prevent buffer overflow attacks.

A potential **Denial of Service** vulnerability exists if a malicious SOCKS5 proxy sends truncated responses, but this would result in socket timeout/hang, not code execution.

**Risk Level**: LOW to MEDIUM (depending on whether DoS is a concern for the deployment)

**Affected Code**: `/workspace/lib/socks.c:548-1054` (`do_SOCKS5()` function)

**Mitigation Status**: Partially mitigated through buffer size guarantees and hostname length validation
