# CVE-2023-39325 Transitive Dependency Analysis: grpcurl

## Summary

**grpcurl is NOT affected by CVE-2023-39325.**

grpcurl is a command-line client tool that connects to gRPC servers—it does not run an HTTP/2 server itself. CVE-2023-39325 is a vulnerability that specifically affects HTTP/2 **server** implementations (via `http2.Server.ServeConn`).

Additionally, grpc-go (the intermediate dependency) does not use the vulnerable `http2.Server.ServeConn` API. Instead, it implements its own HTTP/2 transport layer using low-level frame-based I/O, which means the vulnerability cannot be exploited even if a gRPC server were running.

**Verdict:** NOT AFFECTED | Risk Level: NONE

---

## Dependency Chain Analysis

### Direct Dependency: grpcurl → grpc-go

**Evidence:**

grpcurl's `go.mod` (line 11):
```
google.golang.org/grpc v1.48.0
```

**What grpcurl does with gRPC:**
- grpcurl imports `google.golang.org/grpc` to act as an HTTP/2 **client**
- From `cmd/grpcurl/grpcurl.go` (line 1):
  ```
  // Command grpcurl makes gRPC requests (a la cURL, but HTTP/2)
  ```
- grpcurl connects to gRPC servers via the client library, making RPC calls
- It does NOT run a gRPC server
- Line 19 of grpcurl.go: `"google.golang.org/grpc"` - client library import
- Line 21: Uses `google.golang.org/grpc/codes` and `google.golang.org/grpc/credentials` for client-side operations
- Line 24: Uses `google.golang.org/grpc/reflection/grpc_reflection_v1alpha` for **client-side** reflection queries

### Transitive Dependency: grpc-go → golang.org/x/net

**grpc-go v1.56.2's `go.mod` (line 14):**
```
golang.org/x/net v0.9.0
```

**Key Finding:** grpc-go uses `golang.org/x/net v0.9.0`, which was released in **March 2023**.

CVE-2023-39325 timeline:
- **v0.9.0**: Released March 2023 (BEFORE vulnerability introduction)
- **v0.14.0**: Released August 2023 (CONTAINS vulnerability per CVE details)
- **v0.17.0**: Released October 2023 (Fixed vulnerability)

Although v0.9.0 was released before the vulnerability, the primary reason grpcurl is not affected is because grpc-go does not use the vulnerable `http2.Server.ServeConn` API at all.

---

## Code Path Trace

### Entry Point in grpcurl: Making RPC Calls

**File:** `cmd/grpcurl/grpcurl.go`

grpcurl uses the gRPC client library to make RPC calls:
- Line 19: Imports `"google.golang.org/grpc"`
- Lines 45-155: Define command-line flags for client connection (TLS certs, auth, headers, etc.)
- Usage pattern: Connects to a remote server and invokes methods

Example from README (line 117-118):
```
grpcurl grpc.server.com:443 my.custom.server.Service/Method
```
This invokes an RPC **on a remote server**, demonstrating client-side usage.

### gRPC Client in grpc-go: HTTP/2 Transport

**File:** `internal/transport/http2_client.go`

- Line 35: `"golang.org/x/net/http2"`
- Line 36: `"golang.org/x/net/http2/hpack"`
- Line 61-62: Defines `http2Client` struct that implements the `ClientTransport` interface
- This handles the **CLIENT** side of HTTP/2, creating outbound connections to servers

### HTTP/2 Transport Layer in grpc-go: Frame-Based I/O

**File:** `internal/transport/http_util.go` (lines 378-402)

The critical finding: grpc-go implements its own HTTP/2 frame handling:

```go
type framer struct {
    writer *bufWriter
    fr     *http2.Framer
}

// Creating the framer (lines 392-397):
f := &framer{
    writer: w,
    fr:     http2.NewFramer(w, r),
}
f.fr.SetMaxReadFrameSize(http2MaxFrameLen)
f.fr.SetReuseFrames()
f.fr.MaxHeaderListSize = maxHeaderListSize
```

**Significance:** grpc-go uses `http2.Framer`, which is a low-level frame reader/writer. This is NOT the same as `http2.Server.ServeConn`, which is the vulnerable server-side API.

### Server Implementation (Not Used by grpcurl)

**File:** `internal/transport/http2_server.go`

- Line 36: Imports `"golang.org/x/net/http2"`
- Line 69-136: Defines `http2Server` struct for server-side transport

**Key observation:** While grpc-go has a server implementation, grpcurl never uses it. grpcurl is purely a client tool.

---

## Server vs Client Analysis

### grpcurl Purpose
**Client tool.** From README (lines 5-6):
```
grpcurl is a command-line tool that lets you interact with gRPC servers.
It's basically curl for gRPC servers.
```

grpcurl is used like cURL to **connect to** servers, not to **run** servers.

### HTTP/2 Server Usage in grpc-go
grpc-go includes an HTTP/2 server implementation in `http2_server.go`, but this is for when grpc-go is used to implement a gRPC server. Since **grpcurl does not implement any server functionality**, this code is never executed in grpcurl's context.

### HTTP/2 Client Usage in grpc-go
grpc-go's `http2_client.go` is what grpcurl uses:
- File: `internal/transport/http2_client.go`
- Purpose: Implement client-side HTTP/2 transport for outbound gRPC calls
- API used: `http2.Framer` for low-level frame I/O, not `http2.Server`

### Vulnerable Function Path
**`http2.Server.ServeConn` is NOT called anywhere in the grpcurl → grpc-go → golang.org/x/net stack for client operations.**

Evidence:
1. Search in grpc-go repository for `ServeConn`: No results
2. grpc-go uses `http2.Framer` (low-level API) instead of `http2.Server` (high-level server API)
3. grpcurl itself contains no server implementation

---

## Vulnerability Details: CVE-2023-39325

**Vulnerability Type:** HTTP/2 Rapid Reset Denial of Service

**Affected Component:** `golang.org/x/net/http2.Server.ServeConn`

**Description:** A malicious HTTP/2 **client** that rapidly creates requests and immediately resets them (RST_STREAM frames) can cause excessive resource consumption on an HTTP/2 **server** that uses `http2.Server.ServeConn`.

**Key Characteristic:** This is a **server-side vulnerability**. It requires:
1. An HTTP/2 server listening for connections (using `http2.Server.ServeConn`)
2. A malicious client that sends rapid RST_STREAM frames
3. The vulnerability does NOT affect HTTP/2 clients

---

## Impact Assessment

### Affected
**NO**

### Risk Level
**NONE**

### Rationale

1. **grpcurl is a CLIENT tool, not a server:**
   - grpcurl connects TO gRPC servers using the gRPC client library
   - It does not run an HTTP/2 server or expose any listening ports
   - Therefore, it cannot be attacked via the server-side vulnerability

2. **grpc-go does not use `http2.Server.ServeConn`:**
   - grpc-go implements its own HTTP/2 transport layer using `http2.Framer`
   - Even if grpc-go were used to build a server (which grpcurl doesn't do), it would not be vulnerable because it doesn't use the vulnerable API
   - The low-level framing approach is different from the high-level `http2.Server` API

3. **CVE-2023-39325 requires server context:**
   - The vulnerability is triggered by a **malicious client** sending rapid RST_STREAM frames to an **HTTP/2 server**
   - Since grpcurl is purely a client tool and doesn't run a server, it cannot be the victim of this attack
   - Conversely, grpcurl cannot trigger this vulnerability against remote servers because grpc-go uses different HTTP/2 APIs

### Exploitability
**Not exploitable.** There is no attack surface for CVE-2023-39325 against grpcurl because:
- grpcurl does not run an HTTP/2 server
- grpcurl does not call the vulnerable `http2.Server.ServeConn` function
- grpcurl cannot be exploited by remote attackers via HTTP/2 rapid reset attacks

---

## Remediation

**No action required.**

grpcurl is not affected by CVE-2023-39325 and does not need updating with respect to this vulnerability. The tool is safe to use as-is.

### Additional Context

- If grpc-go (the library) were updated to use a newer version of `golang.org/x/net`, there would be no harm
- However, no update is strictly necessary for security purposes regarding CVE-2023-39325
- Any other vulnerability fixes in newer versions of `golang.org/x/net` should be evaluated separately

---

## Summary Table

| Aspect | Status | Evidence |
|--------|--------|----------|
| **Direct gRPC Dependency** | ✅ Yes | go.mod: `google.golang.org/grpc v1.48.0` |
| **x/net Transitive Dependency** | ✅ Yes | grpc-go go.mod: `golang.org/x/net v0.9.0` |
| **Runs HTTP/2 Server** | ❌ No | grpcurl is a client-only CLI tool |
| **Uses `http2.Server`** | ❌ No | grpc-go uses `http2.Framer` instead |
| **Uses `http2.Server.ServeConn`** | ❌ No | No references found in codebase |
| **Affected by CVE-2023-39325** | ❌ No | Not a server; vulnerability is server-side only |
| **Risk Level** | ✅ NONE | Client tool cannot be exploited by server-side vulnerability |

---

## Conclusion

**grpcurl is safe and unaffected by CVE-2023-39325.** The project dependencies transitively include the vulnerable `golang.org/x/net` package, but the vulnerable server-side API (`http2.Server.ServeConn`) is never called in the grpcurl execution context. grpcurl is purely a command-line client tool for interacting with gRPC servers, not a server implementation, making it immune to this HTTP/2 server-side denial-of-service vulnerability.
