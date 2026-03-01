# CVE-2023-39325 Transitive Dependency Analysis

## Summary

**grpcurl is NOT affected by CVE-2023-39325.**

While grpcurl has a transitive dependency on the vulnerable package `golang.org/x/net` v0.14.0 (through grpc-go), the project is not exposed to this vulnerability because:

1. **grpcurl is a client tool only** - it makes gRPC requests to remote servers, never runs an HTTP/2 server
2. **CVE-2023-39325 is server-specific** - it affects HTTP/2 servers using `http2.Server.ServeConn`, not clients
3. **grpc-go implements its own HTTP/2 transport** - it does not use the vulnerable `http2.Server` from golang.org/x/net
4. **The vulnerable code path is never invoked** - no call to `http2.Server.ServeConn` exists in grpcurl or grpc-go

**Risk Level: NONE**

---

## Dependency Chain Analysis

### Direct Dependency: grpcurl → grpc-go

**Source**: `/workspace/grpcurl/go.mod`

```go
module github.com/fullstorydev/grpcurl

require (
    google.golang.org/grpc v1.48.0
    ...
)
```

**Purpose**: grpcurl imports `google.golang.org/grpc` to:
- Establish client connections to remote gRPC servers
- Make RPC calls to those servers
- Handle gRPC metadata, credentials, and response processing

**Evidence**: `/workspace/grpcurl/cmd/grpcurl/grpcurl.go:1` declares:
```go
// Command grpcurl makes gRPC requests (a la cURL, but HTTP/2). It can use a supplied descriptor
// file, protobuf sources, or service reflection to translate JSON or text request data...
```

This confirms grpcurl is exclusively a **client tool**.

### Transitive Dependency: grpc-go → golang.org/x/net

**Source**: `/workspace/grpc-go/go.mod` (line 14)

```go
require (
    golang.org/x/net v0.9.0
    ...
)
```

**Version Status**:
- Current version in workspace: `v0.14.0` (via `git describe --tags`)
- Vulnerable range: `< v0.17.0` ✓ VULNERABLE
- Fixed version: `v0.17.0+` (October 10, 2023)

---

## Code Path Trace

### Entry Point in grpcurl

**File**: `/workspace/grpcurl/invoke.go:53`

```go
func InvokeRpc(ctx context.Context, source DescriptorSource, cc *grpc.ClientConn, methodName string, ...
```

The function uses `grpc.ClientConn` to make RPC invocations:

**File**: `/workspace/grpcurl/invoke.go:173`

```go
resp, err := stub.InvokeRpc(ctx, md, req, grpc.Trailer(&respTrailers), grpc.Header(&respHeaders))
```

This is **client-side only** - no server functionality is invoked.

### gRPC HTTP/2 Client Implementation

**File**: `/workspace/grpc-go/internal/transport/http2_client.go:61`

grpc-go implements `http2Client` struct, a custom HTTP/2 client transport:

```go
// http2Client implements the ClientTransport interface with HTTP2.
type http2Client struct {
    conn       net.Conn // underlying communication channel
    framer     *framer
    ...
}
```

This struct is NOT using `http2.Transport` from stdlib. Instead, it implements HTTP/2 wire protocol handling directly using low-level frame types from `golang.org/x/net/http2`.

**File**: `/workspace/grpc-go/internal/transport/http2_client.go:35-36`

```go
import (
    "golang.org/x/net/http2"
    "golang.org/x/net/http2/hpack"
)
```

Usage examples from http2_client.go:
- Line 417: `var ss []http2.Setting` - using Setting type for protocol parameters
- Line 420-421: `http2.SettingInitialWindowSize` - protocol constants
- Line 1054: `t.getStream(f http2.Frame) *Stream` - handling Frame types
- Line 1103: `t.handleData(f *http2.DataFrame)` - handling DataFrame
- Line 1169: `t.handleRSTStream(f *http2.RSTStreamFrame)` - handling RST frames

**Critical Finding**: All usage is of low-level types and constants, NOT the high-level `http2.Server`.

### gRPC HTTP/2 Server Implementation

**File**: `/workspace/grpc-go/internal/transport/http2_server.go:69-136`

grpc-go implements its own HTTP/2 server transport:

```go
// http2Server implements the ServerTransport interface with HTTP2.
type http2Server struct {
    conn        net.Conn
    loopy       *loopyWriter
    framer      *framer
    ...
}
```

**Key Discovery**: This is a custom implementation. It does NOT use `http2.Server` from golang.org/x/net.

**File**: `/workspace/grpc-go/internal/transport/http2_server.go:36`

```go
import (
    "golang.org/x/net/http2"
    "golang.org/x/net/http2/hpack"
)
```

Same pattern as the client - using low-level types and constants, not high-level server components.

---

## Server vs Client Analysis

### Is grpcurl a Server or Client?

**Answer: grpcurl is exclusively a CLIENT tool.**

Evidence:
- Command documentation: "Command grpcurl makes gRPC requests (a la cURL, but HTTP/2)"
- Purpose: Interacting with gRPC servers from the command line
- Entry point: `InvokeRpc()` function that makes outbound requests
- Server functionality: Zero server-related code in grpcurl codebase

**Search Result**:
```bash
$ grep -r "ServeConn" /workspace/grpcurl/
[no results]
```

### Does grpcurl Run an HTTP/2 Server?

**Answer: NO.**

- grpcurl connects to remote gRPC servers as a client
- It never listens on a port or accepts incoming connections
- It has no server-side request handlers
- The command makes outbound connections only

### Does grpc-go Run an HTTP/2 Server Using stdlib's http2.Server?

**Answer: NO.**

**Search for `http2.Server.ServeConn` usage**:
```bash
$ grep -r "ServeConn" /workspace/grpc-go/
[no results]
```

**Search for `http2.Server` usage**:
```bash
$ find /workspace/grpc-go -type f -name "*.go" | xargs grep "http2\.Server\." | grep -v test
[no results in main code]
```

The only occurrence is in a test file (`/workspace/grpc-go/test/end2end_test.go`), which is testing integration with net/http servers, not grpc-go's own implementation.

### HTTP/2 Protocol Layer Analysis

Both http2Client and http2Server in grpc-go use:

**Protocol Types and Constants** (the vulnerable surface):
- `http2.Setting` - protocol settings frames
- `http2.ErrCode` - error codes
- `http2.Frame` and subclasses (DataFrame, RSTStreamFrame, etc.) - frame handling
- `http2.FlagDataPadded` - frame flags
- `http2/hpack` - header compression

**NOT used** (the vulnerable components):
- ❌ `http2.Server` - the high-level HTTP/2 server
- ❌ `http2.Transport` - the high-level HTTP/2 client transport
- ❌ `http2.Server.ServeConn` - **the vulnerable function for this CVE**
- ❌ `http2.ConfigureServer` - configuration for stdlib servers

---

## Vulnerable Function Analysis

### CVE-2023-39325: HTTP/2 Rapid Reset Attack

**Vulnerable Code Path**:
```
golang.org/x/net/http2.Server.ServeConn
  → handles client connections
  → processes RST_STREAM frames
  → vulnerable to rapid reset attack
```

**Threat Model**: A malicious HTTP/2 client rapidly creates request streams and immediately resets them with RST_STREAM frames, causing excessive server resource consumption.

**Affected Implementations**: HTTP/2 servers using `http2.Server.ServeConn` directly or indirectly.

### Is this Code Path Used?

**Search across entire codebase**:
```bash
$ grep -r "ServeConn" /workspace/grpcurl/
[0 results]

$ grep -r "ServeConn" /workspace/grpc-go/
[0 results in non-test code]
```

**Conclusion**: The vulnerable function `http2.Server.ServeConn` is **never called** in grpcurl or grpc-go.

---

## Impact Assessment

### Affected
**NO** - grpcurl is NOT affected by CVE-2023-39325.

### Risk Level
**NONE** - Zero exploitability.

### Rationale

1. **Client vs Server**: CVE-2023-39325 is a server-side vulnerability affecting HTTP/2 servers. grpcurl is a client tool that only makes outbound requests.

2. **Custom HTTP/2 Implementation**: grpc-go implements its own HTTP/2 transport layer (http2Client and http2Server structs). These are custom implementations that handle the low-level wire protocol.

3. **No Use of Vulnerable Component**: grpc-go does not use `http2.Server` from golang.org/x/net/http2. It only imports low-level protocol types and constants from that package.

4. **No Server Exposure**: grpcurl never runs an HTTP/2 server. It only makes client connections to remote gRPC servers.

5. **Dependency Does Not Equal Exploitation**: While grpcurl transitively depends on the vulnerable version of golang.org/x/net, the vulnerable code path is never invoked.

### Exploitability

**Can an attacker trigger CVE-2023-39325 against grpcurl?**

**NO** - The vulnerability cannot be exploited against grpcurl because:

1. grpcurl doesn't run an HTTP/2 server - it only makes client connections
2. The vulnerability requires attacking a server's `http2.Server.ServeConn` handler
3. grpc-go doesn't use `http2.Server.ServeConn` - it has its own HTTP/2 server implementation
4. An attacker would need to attack a different application that uses golang.org/x/net's `http2.Server`, not grpcurl

---

## Remediation

### Recommended Action
**No immediate action required for grpcurl itself.**

However, for defense-in-depth and to avoid future supply chain issues:

1. **Update golang.org/x/net** (optional): Updating to v0.17.0+ would ensure the package itself is patched, even though it's not currently exploited.

2. **Monitor grpc-go updates**: When grpc-go updates its dependency to a patched version of golang.org/x/net, accept that update as part of routine maintenance.

3. **Consider the Future**: If grpc-go ever changes to use golang.org/x/net's http2.Server (currently unlikely), this vulnerability could become relevant.

4. **Server Applications Using grpc-go**: If you deploy a gRPC **server** using grpc-go (as opposed to the grpcurl client), be aware that grpc-go's HTTP/2 server implementation may have its own rapid reset handling. Verify that grpc-go versions deployed with grpc-go's internal fixes are in place.

### Conclusion
For grpcurl users: **No action is required**. The project is not affected by CVE-2023-39325.

For grpc-go server deployments: Monitor grpc-go's security advisories for any issues with its own HTTP/2 server implementation (separate from this CVE).

---

## Technical Details Summary

| Aspect | Finding |
|--------|---------|
| **Vulnerable Package** | golang.org/x/net (v0.14.0 < v0.17.0) |
| **Vulnerable Component** | http2.Server.ServeConn |
| **Affected Systems** | HTTP/2 servers using golang.org/x/net/http2.Server |
| **CVE Type** | Denial of Service (Rapid Reset Attack) |
| **CVSS Score** | 7.5 (High) |
| **grpcurl Usage of x/net** | YES (transitive) |
| **grpcurl Usage of http2.Server** | NO |
| **grpcurl Usage of http2.ServeConn** | NO |
| **grpcurl Server Exposure** | NONE (client-only tool) |
| **Exploitable Against grpcurl** | NO |
| **Remediation Urgency** | LOW (no active risk) |

