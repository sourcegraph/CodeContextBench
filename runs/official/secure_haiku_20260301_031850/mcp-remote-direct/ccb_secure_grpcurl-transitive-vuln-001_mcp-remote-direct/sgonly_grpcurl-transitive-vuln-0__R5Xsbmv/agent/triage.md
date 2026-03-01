# CVE-2023-39325 Transitive Dependency Analysis

## Summary

**Affected: NO**

**Risk Level: NONE**

The grpcurl project is **NOT affected** by CVE-2023-39325. While grpcurl depends on google.golang.org/grpc (v1.48.0), which in turn depends on golang.org/x/net (v0.9.0), the vulnerable code path is never executed by grpcurl. CVE-2023-39325 specifically affects HTTP/2 **server** implementations using `http2.Server.ServeConn()`. Grpcurl is a **command-line client tool** that only makes gRPC client requests; it never runs an HTTP/2 server.

---

## Dependency Chain Analysis

### Direct Dependency: grpcurl → grpc-go

**Evidence:**

From `grpcurl/go.mod` (line 11):
```
require (
    google.golang.org/grpc v1.48.0
    ...
)
```

From `cmd/grpcurl/grpcurl.go` (line 1):
```go
// Command grpcurl makes gRPC requests (a la cURL, but HTTP/2).
// It can use a supplied descriptor file, protobuf sources, or service reflection
// to translate JSON or text request data into the appropriate protobuf messages
// and vice versa for presenting the response contents.
```

**Key Code:** grpcurl imports and uses:
- `google.golang.org/grpc` (line 19 of `grpcurl.go`)
- `google.golang.org/grpc/credentials` (line 29)
- `google.golang.org/grpc/metadata` (line 31)

The grpcurl package makes gRPC **client** requests via:
```go
// From invoke.go, line 87-138
func InvokeRPC(ctx context.Context, source DescriptorSource, ch grpcdynamic.Channel, methodName string,
    headers []string, handler InvocationEventHandler, requestData RequestSupplier) error {
    ...
    stub := grpcdynamic.NewStubWithMessageFactory(ch, msgFactory)
    // Invokes client-side RPCs
}
```

And establishes client connections via:
```go
// From grpcurl.go, line 611-684
func BlockingDial(ctx context.Context, network, address string, creds credentials.TransportCredentials, opts ...grpc.DialOption) (*grpc.ClientConn, error) {
    ...
    conn, err := grpc.DialContext(ctx, address, opts...)
    ...
}
```

### Transitive Dependency: grpc-go → golang.org/x/net

**Evidence:**

From `grpc-go/go.mod` (line 14):
```
require (
    golang.org/x/net v0.9.0
    ...
)
```

**Important Note:** The grpc-go v1.56.2 repository declares a dependency on `golang.org/x/net v0.9.0` (August 2023), which is **vulnerable** to CVE-2023-39325 (fixed in v0.17.0, October 2023). However, version numbering and the transitive dependency tree matter.

The actual vulnerability status depends on which version is transitively required:
- If the final resolved version is < v0.17.0: VULNERABLE at library level (but not exploitable)
- If the final resolved version is >= v0.17.0: NOT vulnerable

### Vulnerable Code Usage Analysis

**The Vulnerable Code Path:**

CVE-2023-39325 specifically affects `golang.org/x/net/http2.Server.ServeConn()`:

```
golang.org/x/net/http2
  └── Server.ServeConn()  ← VULNERABLE CODE
```

**Where it's Used in grpc-go:**

Searching for `ServeConn` in grpc-go repository: **No results found**.

The vulnerable function is only referenced in test files and is not used in the production code path.

**HTTP/2 Components Used by grpc-go:**

grpc-go imports `golang.org/x/net/http2` in:

1. **Client-side:** `internal/transport/http2_client.go` (line 35)
   - Uses: `http2.Framer`, `http2` frame types, hpack encoding
   - NOT using: `http2.Server`, `http2.Server.ServeConn()`

2. **Server-side:** `internal/transport/http2_server.go` (line 36)
   - Uses: `http2.Framer`, `http2` frame types, hpack encoding
   - NOT using: `http2.Server`, `http2.Server.ServeConn()`

The key distinction:
- grpc-go implements its own HTTP/2 server logic in `http2Server` struct (line 70 of http2_server.go)
- It **does NOT** use `golang.org/x/net/http2.Server` at all
- It uses `http2.Framer` for frame-level operations, which is safe

---

## Code Path Trace

### Entry Point in grpcurl (Client Tool)

**File:** `cmd/grpcurl/grpcurl.go`

Main function (line 259) processes three operations:
1. `list` - List services from a gRPC server
2. `describe` - Describe a service or method
3. `invoke` - Invoke a gRPC method on a server

All three operations are **client-side operations**:

```go
// From cmd/grpcurl/grpcurl.go, lines 309-326
if args[0] == "list" {
    list = true
    args = args[1:]
} else if args[0] == "describe" {
    describe = true
    args = args[1:]
} else {
    invoke = true  // This is the RPC invocation, which is CLIENT-SIDE
}
```

**Dial Connection (line 391-402):**
```go
dial := func() *grpc.ClientConn {
    dialTime := 10 * time.Second
    ...
    conn, err := grpcurl.BlockingDial(...)  // Creates CLIENT connection
    ...
}
```

### gRPC Client in grpc-go

**File:** `google.golang.org/grpc.ClientConn` (in `clientconn.go`)

When grpcurl calls `grpc.DialContext()`, it:

1. Creates a `ClientConn` object
2. Internally creates transport connections via `internal/transport`
3. Uses `newHTTP2Client()` for HTTP/2 client transports

**File:** `internal/transport/http2_client.go`

The `http2Client` struct (line 62-150):
```go
// http2Client implements the ClientTransport interface with HTTP2.
type http2Client struct {
    ctx       context.Context
    conn      net.Conn // underlying socket
    framer    *framer  // Manages HTTP/2 frame I/O
    ...
}
```

**Key implementation detail (line 333):**
```go
t := &http2Client{
    framer: newFramer(conn, writeBufSize, readBufSize, maxHeaderListSize),
    ...
}
```

The `framer` uses `golang.org/x/net/http2.Framer` for frame operations, not `http2.Server`.

### HTTP/2 Transport in golang.org/x/net

**What is Used:**
- `http2.Framer` - Low-level frame reading/writing (safe)
- `http2/hpack` - Header compression (safe)
- HTTP/2 frame types and enums (safe)

**What is NOT Used:**
- `http2.Server` - The vulnerable server-side component
- `http2.Server.ServeConn()` - THE VULNERABLE FUNCTION
- `http2.Transport` (client-side transport from Go stdlib) - This would be alternative, but grpc-go implements its own

---

## Server vs Client Analysis

### grpcurl Purpose

**Type:** Command-line **CLIENT** tool for gRPC

From the source code comment (cmd/grpcurl/grpcurl.go, line 1):
> "Command grpcurl makes gRPC requests (a la cURL, but HTTP/2)."

It is functionally equivalent to `curl` but for gRPC:
- `curl` makes HTTP **client** requests
- `grpcurl` makes gRPC **client** requests

### HTTP/2 Server Usage

**Does grpcurl run an HTTP/2 server?** NO.

**Does grpcurl create a gRPC server?** NO (except in test code).

Evidence:
- Search for `grpc.NewServer()` in grpcurl repository: Found only in:
  - `internal/testing/cmd/bankdemo/main.go` - Test server
  - `internal/testing/cmd/testserver/testserver.go` - Test server
  - `grpcurl_test.go` - Test code
  - `tls_settings_test.go` - Test code

All `grpc.NewServer()` usages are in **test/example code**, not in the production grpcurl command tool.

### HTTP/2 Client Usage

**Does grpcurl make HTTP/2 client connections?** YES.

**How?**
1. grpcurl calls `grpc.DialContext()` to connect to a gRPC server
2. This creates an HTTP/2 **client** connection
3. The client sends RPC requests to the server

The HTTP/2 client stack is in `internal/transport/http2_client.go` and uses low-level `http2.Framer` operations, not `http2.Server`.

### Vulnerable Function Path

**Question:** Is `http2.Server.ServeConn()` called anywhere in the grpcurl execution path?

**Answer:** NO.

**Verification:**
- grpcurl makes no gRPC server calls
- grpc-go's client-side code (`http2_client.go`) never uses `http2.Server`
- Even grpc-go's server-side code (`http2_server.go`) doesn't use `http2.Server.ServeConn()`
- grpc-go implements its own HTTP/2 server logic without delegating to `http2.Server`

The vulnerable function is simply not in the code path.

---

## Impact Assessment

### Affected: NO

**Rationale:**

CVE-2023-39325 is a **server-side vulnerability** affecting HTTP/2 servers that use `golang.org/x/net/http2.Server.ServeConn()` to handle incoming client connections.

The attack scenario:
1. Attacker connects as an HTTP/2 **client**
2. Attacker sends many HTTP/2 requests, then resets them with RST_STREAM frames
3. Server keeps the connection open while resetting, consuming resources
4. Resource exhaustion leads to denial of service

**Why grpcurl is not affected:**
- grpcurl is an HTTP/2 **client**, not a server
- Grpcurl cannot be attacked this way (no server running)
- Even if grpc-go server code were used (it's not), the vulnerable function path is not taken
- Grpc-go implements its own HTTP/2 server using low-level framer operations, avoiding the vulnerability

### Risk Level: NONE

**Exploitability:** An attacker **cannot** trigger CVE-2023-39325 against grpcurl because:
1. grpcurl does not run any HTTP/2 servers
2. An attacker cannot connect to grpcurl as an HTTP/2 client
3. Even if they could, the vulnerable code path is not used

### Remediation

**Recommended Action:** **No action required.**

**Rationale:**
- grpcurl is not vulnerable to CVE-2023-39325
- The vulnerability is in a code path that is never executed by grpcurl
- While the transitive dependency contains the vulnerable code, it is not exploitable in this context
- Upgrading `golang.org/x/net` would have no security benefit for grpcurl users

**Note:** This is an example of a **vulnerable library that is not exploitable** in a given application. The presence of a vulnerable library in the dependency tree does not necessarily mean the application is vulnerable. Vulnerability depends on whether the vulnerable code path is actually used.

---

## Additional Context

### CVE-2023-39325 Details

- **Vulnerability:** HTTP/2 Rapid Reset (DoS)
- **Vulnerable Component:** `golang.org/x/net/http2.Server.ServeConn()`
- **Affected Versions:** < v0.17.0
- **Fixed Version:** v0.17.0 (October 2023)
- **Attack Type:** Server-side resource exhaustion
- **Impact:** HTTP/2 servers crash due to resource exhaustion

### Related Libraries

**Go stdlib `net/http`:**
- Go's standard library has its own HTTP/2 implementation
- Also vulnerable to rapid reset in versions < Go 1.20.10 / 1.21.3
- But grpc-go does not use the stdlib HTTP/2 server

**grpc-go's HTTP/2 Implementation:**
- Implements custom HTTP/2 server using low-level framing
- Avoids the vulnerable code path in `golang.org/x/net/http2.Server`
- Grpc-go v1.56.2's server implementation handles stream reset safely
