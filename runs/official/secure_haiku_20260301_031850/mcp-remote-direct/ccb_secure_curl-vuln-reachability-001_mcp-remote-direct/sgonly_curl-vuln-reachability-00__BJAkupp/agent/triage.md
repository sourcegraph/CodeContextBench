# Security Reachability Analysis: do_SOCKS5() Function

## 1. Summary

This analysis examines whether the `do_SOCKS5()` function in curl's SOCKS5 proxy handler is reachable from external HTTP/HTTPS input during normal proxy operation.

**Conclusion: REACHABLE from external attacker-controlled input (proxy server responses and user-controlled hostname/port parameters)**

The `do_SOCKS5()` function is directly reachable when a user configures curl with a SOCKS5 proxy. External attacker-controlled data can reach this function through:
1. **Proxy server responses** - The function processes data received from the SOCKS5 proxy server
2. **User-specified hostname/port** - Configuration parameters flow through to this function

---

## 2. Affected Code

**Function:** `do_SOCKS5()`
**Location:** `lib/socks.c:548-1054`
**File:** `lib/socks.c`

### Function Purpose
Implements the SOCKS5 proxy protocol handshake as defined in RFC 1928. This function:
- Initiates SOCKS5 connection to proxy server
- Handles authentication (username/password, GSS-API)
- Sends connection request to remote host through proxy
- Processes and validates all proxy responses
- Performs state machine transitions through SOCKS5 protocol phases

---

## 3. Attack Path

### Complete Call Chain (HTTP/HTTPS Entry Point)

```
main()
  └─> curl_easy_perform()
      └─> multi_perform()
          └─> curl_multi_perform()
              └─> multi_socket()
                  └─> multi_socket_action()
                      └─> Curl_http_connect() [lib/http.c:1565]
                          └─> Curl_conn_connect() [lib/cfilters.c:333]
                              └─> cf->cft->do_connect(cf, data, blocking, done)
                                  └─> (connection filter chain)
                                      └─> cf_setup_h1_proxy() [lib/connect.c:1200+]
                                          └─> Curl_cf_socks_proxy_insert_after() [lib/socks.c:1240]
                                              └─> socks_proxy_cf_connect() [lib/socks.c:1103]
                                                  └─> connect_SOCKS() [lib/socks.c:1056]
                                                      └─> do_SOCKS5() [lib/socks.c:548]
```

### Key Intermediate Functions

| Function | Location | Role |
|----------|----------|------|
| `Curl_http_connect()` | lib/http.c:1565 | HTTP protocol handler entry point |
| `Curl_conn_connect()` | lib/cfilters.c:333 | Connection filter dispatcher |
| `cf_setup_h1_proxy()` | lib/connect.c:1174+ | Inserts proxy filters into connection chain |
| `Curl_cf_socks_proxy_insert_after()` | lib/socks.c:1240 | SOCKS filter factory function |
| `socks_proxy_cf_connect()` | lib/socks.c:1103 | SOCKS filter connection handler |
| `connect_SOCKS()` | lib/socks.c:1056 | Proxy type dispatcher (calls do_SOCKS5 or do_SOCKS4) |
| `do_SOCKS5()` | lib/socks.c:548 | SOCKS5 protocol implementation |

---

## 4. Severity Assessment

### Reachability Analysis

**YES - REACHABLE from external input**

The `do_SOCKS5()` function is reachable through the normal user-initiated connection flow when a SOCKS5 proxy is configured.

### Attack Vector & Trigger Conditions

**Attack Vector 1: Direct Proxy Server Response Processing (HIGH IMPACT)**
- **Requirement:** User specifies `curl https://example.com --proxy socks5://attacker-proxy:1080`
- **Attacker Control:** Malicious SOCKS5 server (attacker controls proxy endpoint)
- **Data Flow:**
  1. User provides proxy URL: `socks5://attacker-proxy:1080`
  2. Curl connects to proxy server at `attacker-proxy`
  3. `do_SOCKS5()` processes responses from proxy server
  4. Attacker sends crafted SOCKS5 protocol responses
- **Vulnerable Code Paths:**
  - Line 646-653: Initial SOCKS5 response parsing
  - Line 960-986: Connect request ACK response parsing
  - Line 1005-1020: Bind address response parsing
  - Lines 1004-1020: Address type parsing with variable-length fields

**Attack Vector 2: Hostname Length Handling (MEDIUM IMPACT)**
- **Requirement:** User specifies `curl https://[hostname] --proxy socks5h://proxy:1080`
- **Data Flow:**
  1. User provides target hostname
  2. Hostname flows through proxy configuration → `sx->hostname`
  3. Hostname length calculated: `hostname_len = strlen(sx->hostname)` (line 575)
  4. Hostname used in packet construction at line 906
- **Potential Issue:** Line 906 casts `hostname_len` (size_t) to `(char)` but line 589 enforces RFC 1928 limit
- **Mitigating Factor:** Explicit check at line 589 forces local resolution if hostname > 255 characters

**Attack Vector 3: Authentication Credential Processing (MEDIUM IMPACT)**
- **Requirement:** User provides proxy credentials: `curl --proxy-user user:pass --proxy socks5://proxy:1080`
- **Data Flow:**
  1. User provides credentials
  2. Credentials stored in `sx->proxy_user` and `sx->proxy_password` (line 703-743)
  3. User/password length validation at lines 727-729, 737-739
  4. Credentials sent to proxy in SOCKS5 subnegotiation packet

### External Input Reaching do_SOCKS5()

**Data Sources:**

1. **Proxy Server Network Responses** (Primary attack surface):
   - Initial server response (lines 645-657)
   - Authentication response (lines 762-776)
   - Connect request ACK (lines 951-986)
   - Bind address field (lines 1005-1020)
   - Address type field (socksreq[3], line 1005)
   - Address length field (socksreq[4], line 1007)

2. **User-Controlled Configuration** (Secondary attack surface):
   - Hostname parameter (from `curl https://hostname`)
   - Proxy server address (from `--proxy` flag)
   - Proxy credentials (from `--proxy-user` flag)
   - Port number (from target URL or `--proxy` flag)

3. **Command-Line Input**:
   - User can control hostname length
   - User can specify any SOCKS5 proxy endpoint
   - User can provide malformed proxy URLs

---

## 5. Remediation & Security Considerations

### Existing Protections Found

1. **RFC 1928 Hostname Length Check (Line 589)**
   ```c
   if(!socks5_resolve_local && hostname_len > 255) {
     socks5_resolve_local = TRUE;
   }
   ```
   **Effect:** Enforces RFC 1928 requirement that domain names in SOCKS5 packets cannot exceed 255 bytes

2. **Authentication Credential Length Validation (Lines 727-729, 737-739)**
   ```c
   if(proxy_user_len > 255) {
     failf(data, "Excessive user name length for proxy auth");
     return CURLPX_LONG_USER;
   }
   ```
   **Effect:** Prevents username/password from exceeding SOCKS5 protocol limits

3. **Protocol Version Validation (Lines 654-657)**
   ```c
   else if(socksreq[0] != 5) {
     failf(data, "Received invalid version in initial SOCKS5 response.");
     return CURLPX_BAD_VERSION;
   }
   ```
   **Effect:** Validates proxy response format

4. **Buffer Limits**
   - Line 287: `DEBUGASSERT(READBUFFER_MIN >= 600)` ensures adequate buffer space
   - Hostname maximum of 255 characters enforced by RFC 1928 check

### Potential Vulnerability Areas

1. **Variable-Length Field Parsing (Lines 1005-1020)**
   - Code calculates packet size based on `socksreq[3]` (address type) and `socksreq[4]` (length)
   - If proxy sends malformed address type or length values, parsing could be incorrect
   - However, bounds checking exists (lines 1014-1020)

2. **DNS Response Buffer (Line 822)**
   ```c
   char dest[MAX_IPADR_LEN] = "unknown";
   ```
   - Used for printable address formatting only (line 832)
   - Not a security concern

### Recommended Mitigation Strategies

**For Protocol Robustness:**

1. **Enhance Bind Address Validation**
   ```c
   // After calculating len from address type:
   if(len < 10 || len > data->set.buffer_size - 10) {
     failf(data, "Invalid SOCKS5 response packet size");
     return CURLPX_BAD_ADDRESS_TYPE;
   }
   ```

2. **Validate Address Type Field**
   ```c
   // Line 1005:
   if(socksreq[3] < 1 || socksreq[3] > 4) {
     failf(data, "SOCKS5 invalid address type: %d", socksreq[3]);
     return CURLPX_BAD_ADDRESS_TYPE;
   }
   ```

3. **Add Hostname Sanitization**
   - Already done well at line 589, maintain this check
   - Consider log warning for large hostnames

4. **Proxy Server Trust Verification**
   - Current code trusts proxy responses implicitly
   - Consider adding optional proxy certificate pinning for future enhancement
   - Add timeout protection for proxy responses

**For Attack Surface Reduction:**

1. **User Warning for Untrusted Proxies**
   - Display warning when connecting to proxy without HTTPS encryption
   - Suggest using HTTPS proxy URL when available

2. **Input Validation at Entry**
   - Hostname validation at proxy configuration time (not just at protocol level)
   - Pre-flight checks for obviously malformed targets

---

## 6. Conclusion

The `do_SOCKS5()` function is **REACHABLE from external attacker-controlled input** in the following scenarios:

1. **Malicious SOCKS5 Proxy Server** - An attacker who controls or intercepts the SOCKS5 proxy endpoint can send crafted protocol responses to trigger vulnerability code paths in `do_SOCKS5()`

2. **Legitimate Use with Untrusted Proxy** - A user connecting through an HTTP/HTTPS request through a public or untrusted SOCKS5 proxy is exposing their curl client to the proxy's control

3. **User-Supplied Hostname Attacks** - While protections exist, hostname parameters flow directly into `do_SOCKS5()` and are processed by the protocol handler

### Security Posture

- **Current Status:** Well-protected against common buffer overflow vectors
- **RFC 1928 Compliance:** Good (enforces 255-byte hostname limit)
- **Input Validation:** Adequate for protocol requirements
- **Recommended:** Add enhanced packet size validation and address type validation for defense-in-depth

The function is appropriate for its intended use case but users should be cautious about SOCKS5 proxy sources, as the proxy server has significant control over the protocol exchange.
