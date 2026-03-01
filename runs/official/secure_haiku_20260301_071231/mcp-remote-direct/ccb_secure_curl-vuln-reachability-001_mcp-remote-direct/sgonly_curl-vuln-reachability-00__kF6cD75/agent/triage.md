# Security Reachability Analysis: curl SOCKS5 Proxy Handler

## Summary

This analysis examines the reachability of the `do_SOCKS5()` function in curl's SOCKS5 proxy implementation. The function is **REACHABLE** from external input when a user specifies a SOCKS5 proxy configuration. The function processes untrusted data from SOCKS5 proxy servers, presenting a potential attack surface for exploiting the proxy handshake implementation.

## Affected Code

**Function:** `do_SOCKS5()`
**Location:** `lib/socks.c:548-1054`
**Type:** Static function (internal)

**Description:** This function implements the SOCKS5 protocol handshake as defined in RFC 1928. It manages the multi-stage negotiation between curl and a SOCKS5 proxy server, including:
- Initial authentication method negotiation
- Username/password authentication (if required)
- Remote connection request to the target server
- Response validation and error handling

The function operates as a state machine with states including:
- `CONNECT_SOCKS_INIT`: Initialize SOCKS5 connection
- `CONNECT_SOCKS_SEND/READ`: Exchange initial auth methods
- `CONNECT_AUTH_INIT/SEND/READ`: Authenticate with proxy
- `CONNECT_REQ_INIT/SEND/READ`: Send connection request to target
- `CONNECT_DONE`: Successfully connected

## Attack Path

### Complete Call Chain

```
User executes curl → easy_perform() → multi_perform() →
multi_runsingle() → Curl_once_resolved() →
Curl_setup_conn() → Curl_conn_setup() →
cf_setup_add()/Curl_cf_setup_insert_after() →
cf_setup_create() → cf_setup_connect() [filter callback] →
Curl_cf_socks_proxy_insert_after() →
socks_proxy_cf_connect() [filter callback] →
connect_SOCKS() → do_SOCKS5()
```

### Intermediate Functions and Their Roles

1. **User Entry Point:** `curl_easy_perform()` / `curl_multi_perform()`
   - Public API entry point when user runs curl or calls the C library
   - Triggers the transfer initialization

2. **Transfer State Machine:** `multi_runsingle()` (lib/multi.c:1868)
   - Core state machine that orchestrates the entire transfer lifecycle
   - Processes states: MSTATE_INIT → MSTATE_CONNECT → MSTATE_WAITRESOLVE → MSTATE_PROTOCONNECT
   - Role: Routes control flow through DNS resolution and connection setup phases

3. **Post-DNS Resolution Handler:** `Curl_once_resolved()` (lib/hostip.c:1325)
   - Called after DNS resolution completes
   - Invokes connection setup
   - Role: Bridge between name resolution and connection setup

4. **Connection Setup Coordinator:** `Curl_setup_conn()` (lib/url.c:3858)
   - Checks connection configuration and prepares for data transfer
   - Initiates filter chain setup via `Curl_conn_setup()`
   - Role: Validates protocol handlers and initiates connection filters

5. **Public Connection Setup API:** `Curl_conn_setup()` (lib/connect.c:1416)
   - Creates and adds the connection filter chain
   - Calls `cf_setup_add()` to install the setup filter
   - Role: Public interface for filter chain initialization

6. **Filter Chain Builder:** `cf_setup_add()` (lib/connect.c:1364) / `Curl_cf_setup_insert_after()` (lib/connect.c:1398)
   - Creates the setup filter via `cf_setup_create()`
   - Adds it to the filter chain
   - Role: Instantiates the setup filter

7. **Filter Creator:** `cf_setup_create()` (lib/connect.c:1332)
   - Allocates setup filter context
   - Returns the setup filter instance
   - Role: Factory function for creating the setup filter

8. **Setup Filter's Connect Callback:** `cf_setup_connect()` (lib/connect.c:1186)
   - Part of the `Curl_cft_setup` filter type
   - Checks connection type and inserts protocol-specific filters
   - **Checks `cf->conn->bits.socksproxy` (line 1217)**
   - **Calls `Curl_cf_socks_proxy_insert_after()` if SOCKS proxy is configured (line 1218)**
   - Role: Orchestrates insertion of SOCKS proxy filter when needed

9. **SOCKS Proxy Filter Installer:** `Curl_cf_socks_proxy_insert_after()` (lib/socks.c:1240)
   - Creates a new SOCKS proxy filter instance
   - Inserts it into the filter chain
   - Role: Instantiates and installs the SOCKS filter

10. **SOCKS Proxy Filter's Connect Callback:** `socks_proxy_cf_connect()` (lib/socks.c:1103)
    - Called when the filter chain processes the connection
    - Initializes SOCKS state machine
    - **Calls `connect_SOCKS()` at line 1149**
    - Role: Filter's entry point that initiates SOCKS handshake

11. **SOCKS Protocol Dispatcher:** `connect_SOCKS()` (lib/socks.c:1056)
    - Dispatches to protocol-specific handler based on proxy type
    - Checks `conn->socks_proxy.proxytype` (lines 1064-1078)
    - **Calls `do_SOCKS5()` for CURLPROXY_SOCKS5 and CURLPROXY_SOCKS5_HOSTNAME (lines 1065-1068)**
    - Role: Routes to SOCKS4 or SOCKS5 handler

12. **SOCKS5 Protocol Handler:** `do_SOCKS5()` (lib/socks.c:548)
    - **Implements the SOCKS5 RFC 1928 protocol**
    - Processes server responses at lines 654-1049
    - Role: Core SOCKS5 state machine and protocol processor

### Key Configuration Points

**Where External Input Enters the System:**

1. **Command-Line/API Level:** User specifies proxy via:
   - Command line: `curl https://example.com --proxy socks5://proxy:1080`
   - C API: `curl_easy_setopt(handle, CURLOPT_PROXY, "socks5://proxy:1080")`
   - This sets: `data->set.str[STRING_PROXY]`

2. **Connection Initialization (lib/url.c:1509-1549):**
   - Function: `allocate_conn()` reads user's proxy setting
   - Code line 1540: `conn->bits.proxy = (data->set.str[STRING_PROXY] && *data->set.str[STRING_PROXY]) ? TRUE : FALSE`
   - Code line 1547: `conn->bits.socksproxy = (conn->bits.proxy && !conn->bits.httpproxy) ? TRUE : FALSE`
   - **Proxy type is determined from parsed proxy URL**: `data->set.proxytype`

3. **Filter Chain Setup (lib/connect.c:1217):**
   - Setup filter checks: `if(ctx->state < CF_SETUP_CNNCT_SOCKS && cf->conn->bits.socksproxy)`
   - **Only if user specified a SOCKS proxy does the chain insert SOCKS filter**

4. **Proxy Server Responses (lib/socks.c:645-1049):**
   - **SOCKS proxy server sends bytes received via network**
   - `do_SOCKS5()` processes these responses in the state machine
   - Lines 646, 763, 952: Calls to `socks_state_recv()` read proxy server's response
   - Lines 654-691: Response validation against RFC 1928 format
   - Lines 1005-1020: Parsing of variable-length address types

## Severity Assessment

### Reachability: YES - FULLY REACHABLE

The `do_SOCKS5()` function **IS reachable** from external attacker-controlled input under normal curl operation.

### Attack Vector

**Required User Action:**
```bash
curl https://example.com --proxy socks5://attacker-controlled-proxy:1080
```

Or via C API:
```c
curl_easy_setopt(handle, CURLOPT_PROXY, "socks5://attacker-controlled-proxy:1080");
curl_easy_perform(handle);
```

**Attack Prerequisites:**
1. User must configure curl to use a SOCKS5 proxy
2. Attacker must control or compromise the SOCKS5 proxy server
3. Attacker configures the proxy to send malformed SOCKS5 responses

### External Input Reaching the Function

**Untrusted Data Path:**
1. **Network data from proxy server** enters via socket read (lib/socks.c:241)
   - Function: `Curl_conn_cf_recv()` reads from proxy server socket
   - Data stored in: `socksreq` buffer (unsigned char array from `data->state.buffer`)
   - Size: Up to `data->set.buffer_size` bytes (default 16KB, configurable)

2. **Proxy server controls:**
   - Version byte (expected 0x05) - line 654
   - Authentication method byte - lines 658-689
   - Address type in response - lines 1005-1020
   - Address length field - line 1007
   - Address data - lines 1028-1042

3. **Attack-controllable fields in SOCKS5 response:**
   ```
   SOCKS5 Response Format:
   +----+-----+-------+------+----------+----------+
   |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
   +----+-----+-------+------+----------+----------+
   | 1  |  1  | X'00' |  1   | Variable |    2     |
   +----+-----+-------+------+----------+----------+
   ```
   - Bytes 0-3: Fixed fields
   - Byte 3 (ATYP): Determines address type (1=IPv4, 3=domain, 4=IPv6)
   - **Byte 4: Domain name length (if ATYP==3)** - potentially attacker-controlled
   - Bytes 4+: Address data - **potentially unbounded read vulnerability**

### Specific Vulnerability Points

**Line 1007 - Address Length Parsing:**
```c
if(socksreq[3] == 3) {
  /* domain name */
  int addrlen = (int) socksreq[4];  // <-- Attacker controls this byte
  len = 5 + addrlen + 2;
}
```
- If ATYP is 3 (domain name), the code reads byte 4 as the domain length
- This is **attacker-controlled** in a malicious proxy response
- The length is used to calculate expected packet size

**Line 1007-1008 - No Validation:**
```c
int addrlen = (int) socksreq[4];
len = 5 + addrlen + 2;  // Could be calculated as buffer overflow size
```
- No validation that `addrlen` is reasonable
- No check that `len <= remaining_buffer_size`
- If `addrlen` is large, subsequent reads at line 1028-1042 could be vulnerable

**Lines 1027-1031 - Potential Out-of-Bounds Access:**
```c
if(len > 10) {
  sx->outstanding = len - 10;  // len from attacker-controlled field
  sx->outp = &socksreq[10];
  sxstate(sx, data, CONNECT_REQ_READ_MORE);
}
```
- Subsequent read operation at line 1041-1042 uses this length

**Lines 1041-1042 - Buffer Read:**
```c
case CONNECT_REQ_READ_MORE:
  presult = socks_state_recv(cf, sx, data, CURLPX_RECV_ADDRESS,
                             "SOCKS5 connect request address");
```
- Reads `sx->outstanding` bytes (calculated from attacker field)
- Into buffer starting at `sx->outp` (pointer calculated from `socksreq`)

### Impact

The `do_SOCKS5()` function is **absolutely reachable** when a user specifies a SOCKS5 proxy. The untrusted SOCKS5 server response data reaches critical code paths with variable-length address type handling (ATYP field) that may have insufficient bounds checking.

**Severity Classification: CRITICAL**
- Reachability: Direct and intentional user action required, but straightforward
- Attack complexity: Attacker must control proxy server (network layer attack)
- Impact: Potential memory safety issues in address type parsing

## Remediation

### Input Validation Required

To securely handle SOCKS5 proxy responses:

1. **Add bounds validation for domain name length (line 1007-1008):**
   ```c
   if(socksreq[3] == 3) {
     /* domain name */
     int addrlen = (int) socksreq[4];

     // Validate: domain length must fit in remaining buffer
     if(addrlen < 1 || addrlen > 255) {  // RFC 1928: max 255 bytes
       failf(data, "Invalid domain length in SOCKS5 response: %d", addrlen);
       return CURLPX_BAD_ADDRESS_TYPE;
     }

     len = 5 + addrlen + 2;

     // Validate: total packet size must not exceed buffer
     if(len > READBUFFER_MIN) {  // or data->set.buffer_size
       failf(data, "SOCKS5 response packet size exceeds buffer");
       return CURLPX_BAD_ADDRESS_TYPE;
     }
   }
   ```

2. **Add validation before reading additional data:**
   ```c
   if(len > 10) {
     // Ensure we have already received at least 10 bytes
     if(sx->outstanding <= 0) {
       failf(data, "Invalid SOCKS5 response state");
       return CURLPX_RECV_REQACK;
     }

     sx->outstanding = len - 10;

     // Validate: don't read more than buffer can hold
     if(sx->outstanding > READBUFFER_MIN - 10) {
       failf(data, "SOCKS5 response would overflow buffer");
       return CURLPX_RECV_REQACK;
     }

     sx->outp = &socksreq[10];
     sxstate(sx, data, CONNECT_REQ_READ_MORE);
   }
   ```

3. **Add consistent bounds checking for IPv6 responses (line 1010-1012):**
   ```c
   else if(socksreq[3] == 4) {
     /* IPv6 - fixed size */
     len = 4 + 16 + 2;
     // IPv6 addresses are fixed 16 bytes, safe
   }
   ```

4. **Strict validation of ATYP field:**
   ```c
   if(socksreq[3] != 1 && socksreq[3] != 3 && socksreq[3] != 4) {
     failf(data, "SOCKS5 reply has unknown address type: %d", socksreq[3]);
     return CURLPX_BAD_ADDRESS_TYPE;
   }
   ```

### Summary

- **Function is REACHABLE**: Direct user action (--proxy socks5://) triggers the code path
- **External Input Path**: SOCKS5 proxy server responses enter via network sockets
- **Vulnerability Type**: Potential integer overflow or buffer bounds violation in variable-length address type parsing
- **Recommended Action**: Add RFC 1928 compliance validation for domain name length and total packet size before buffer operations
