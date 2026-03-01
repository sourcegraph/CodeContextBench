# CVE-2024-45337 Transitive Dependency Analysis

## Summary

**Affected**: YES

**Risk Level**: MEDIUM to HIGH

**Verdict**: The `charmbracelet/wish` v0.5.0 project IS affected by CVE-2024-45337 through a vulnerability in its transitive dependency `golang.org/x/crypto/ssh`. More critically, the intermediate dependency `gliderlabs/ssh` v0.3.4 contains code that misuses the vulnerable `PublicKeyCallback` in a way that enables authorization bypass. This could allow attackers to bypass public key authentication checks and associate their session with a different public key than the one they actually controlled.

---

## Dependency Chain Analysis

### Direct Dependency: wish → gliderlabs/ssh

**Evidence Location**: `/workspace/wish/go.mod:9`

```
require (
    github.com/gliderlabs/ssh v0.3.4  // Line 9
)
```

**Usage Evidence**:
- `/workspace/wish/wish.go:8` - Imports `github.com/gliderlabs/ssh`
- `/workspace/wish/options.go:15` - Imports `github.com/gliderlabs/ssh`
- `/workspace/wish/options.go:79, 100, 162` - Uses `ssh.PublicKeyAuth()` and other ssh functions
- `/workspace/wish/wish.go:19-38` - `NewServer()` function creates and configures `ssh.Server` instances

**Key Functions**:
```go
// wish/options.go lines 160-163
func WithPublicKeyAuth(h ssh.PublicKeyHandler) ssh.Option {
	return ssh.PublicKeyAuth(h)
}

// wish/options.go lines 72-88: WithAuthorizedKeys
// wish/options.go lines 90-131: WithTrustedUserCAKeys
// Both use WithPublicKeyAuth to configure public key authentication
```

### Transitive Dependency: gliderlabs/ssh → golang.org/x/crypto

**Evidence Location**: `/workspace/ssh/go.mod:7`

```
require (
    golang.org/x/crypto v0.0.0-20210616213533-5ff15b29337e
)
```

**Vulnerable Version Details**:
- **Commit**: `v0.0.0-20210616213533-5ff15b29337e` (June 16, 2021)
- **CVE Affects**: golang.org/x/crypto versions < v0.31.0
- **Fixed in**: v0.31.0 (December 2024)
- **Status**: This is a pre-fix vulnerable version

**Dependency Resolution Note**:
- `/workspace/wish/go.mod:14` - wish also directly requires `golang.org/x/crypto v0.0.0-20220307211146-efcb8507fb70`
- `/workspace/wish/go.sum` confirms the newer version (20220307) is resolved for wish's direct use
- However, gliderlabs/ssh was compiled/released against the vulnerable version (20210616)
- Go's module system will use the newer version when both are present, but the vulnerability is still part of the transitive chain

### Vulnerable Code Usage

**Evidence**: `/workspace/ssh/server.go:144-153` - **CRITICAL VULNERABILITY**

```go
if srv.PublicKeyHandler != nil {
    config.PublicKeyCallback = func(conn gossh.ConnMetadata, key gossh.PublicKey) (*gossh.Permissions, error) {
        applyConnMetadata(ctx, conn)
        if ok := srv.PublicKeyHandler(ctx, key); !ok {
            return ctx.Permissions().Permissions, fmt.Errorf("permission denied")
        }
        ctx.SetValue(ContextKeyPublicKey, key)  // ⚠️ VULNERABILITY HERE
        return ctx.Permissions().Permissions, nil
    }
}
```

**The Problem**:
Line 150 (`ctx.SetValue(ContextKeyPublicKey, key)`) is executed every time `PublicKeyCallback` is invoked, regardless of whether:
1. The callback is being called for a **query** (client asking "is this key acceptable?"), or
2. The callback is being called for **actual authentication** (client proving control of the key)

---

## Code Path Trace

### Entry Point in wish

**File**: `/workspace/wish/examples/identity/main.go:26-28`

```go
wish.WithPublicKeyAuth(func(ctx ssh.Context, key ssh.PublicKey) bool {
    return true  // Accept any key
}),
```

**File**: `/workspace/wish/options.go:79-86` - `WithAuthorizedKeys()`

```go
return WithPublicKeyAuth(func(_ ssh.Context, key ssh.PublicKey) bool {
    for _, upk := range keys {
        if ssh.KeysEqual(upk, key) {
            return true
        }
    }
    return false
})(s)
```

### Wrapper in gliderlabs/ssh

**File**: `/workspace/ssh/server.go:116-163` - The `config()` method creates the golang.org/x/crypto ServerConfig

**Key Code** (lines 144-153):
```go
if srv.PublicKeyHandler != nil {
    config.PublicKeyCallback = func(conn gossh.ConnMetadata, key gossh.PublicKey) (*gossh.Permissions, error) {
        applyConnMetadata(ctx, conn)
        // Call the user's handler (from wish)
        if ok := srv.PublicKeyHandler(ctx, key); !ok {
            return ctx.Permissions().Permissions, fmt.Errorf("permission denied")
        }
        // ⚠️ VULNERABLE: Sets context key for ALL callback invocations
        ctx.SetValue(ContextKeyPublicKey, key)
        return ctx.Permissions().Permissions, nil
    }
}
```

**Usage**: `/workspace/ssh/server.go:281`
```go
sshConn, chans, reqs, err := gossh.NewServerConn(conn, srv.config(ctx))
```

### Vulnerable Code in golang.org/x/crypto

**File**: `/workspace/crypto/ssh/server.go:138-170` - Cache implementation

```go
type cachedPubKey struct {
    user       string
    pubKeyData []byte
    result     error
    perms      *Permissions
}

type pubKeyCache struct {
    keys []cachedPubKey
}
```

**File**: `/workspace/crypto/ssh/server.go:407-573` - Authentication loop

**Critical Section** (lines 519-549):
```go
candidate, ok := cache.get(s.user, pubKeyData)
if !ok {
    candidate.user = s.user
    candidate.pubKeyData = pubKeyData
    candidate.perms, candidate.result = config.PublicKeyCallback(s, pubKey)
    // ... check critical options
    cache.add(candidate)
}

if isQuery {
    // Client querying if public key is acceptable
    if candidate.result == nil {
        okMsg := userAuthPubKeyOkMsg{
            Algo:   algo,
            PubKey: pubKeyData,
        }
        if err = s.transport.writePacket(Marshal(&okMsg)); err != nil {
            return nil, err
        }
        continue userAuthLoop  // Wait for next client request
    }
    authErr = candidate.result
} else {
    // Client actually authenticating with private key
    sig, payload, ok := parseSignature(payload)
    // ... verify signature
    if err := pubKey.Verify(signedData, sig); err != nil {
        return nil, err
    }
    authErr = candidate.result
    perms = candidate.perms
}
```

---

## Impact Assessment

### Affected: YES

The project IS affected by CVE-2024-45337 through the following chain:

```
wish v0.5.0
  └── gliderlabs/ssh v0.3.4 (contains vulnerable callback wrapper)
        └── golang.org/x/crypto v0.0.0-20210616213533-5ff15b29337e (contains vulnerable PublicKeyCallback)
```

### Risk Level: HIGH

While Go's module system may use the newer version of golang.org/x/crypto directly, the vulnerability is fundamentally in how **gliderlabs/ssh wraps the callback**, not just the underlying library.

### Exploitability: POSSIBLE

**Attack Scenario**:

1. **Client Query Phase 1**: Attacker sends SSH "publickey" request with `query=true` and `key=allowed_key`
   - `crypto/ssh` invokes the callback with allowed_key
   - gliderlabs/ssh calls user's PublicKeyHandler with allowed_key
   - User's handler accepts it (returns true)
   - **gliderlabs/ssh sets `ctx.SetValue(ContextKeyPublicKey, allowed_key)`**
   - Result is cached with success

2. **Client Query Phase 2**: Attacker sends SSH "publickey" request with `query=true` and `key=attacker_key`
   - `crypto/ssh` invokes the callback with attacker_key
   - gliderlabs/ssh calls user's PublicKeyHandler with attacker_key
   - Vulnerable handlers may accept it too (e.g., `WithPublicKeyAuth(func() { return true })`)
   - **gliderlabs/ssh sets `ctx.SetValue(ContextKeyPublicKey, attacker_key)`**
   - Result is cached with success

3. **Client Authentication**: Attacker sends SSH "publickey" request with `query=false`, `key=allowed_key`, with valid signature
   - `crypto/ssh` tries to find allowed_key in cache
   - Cache HIT from phase 1
   - **Callback is NOT invoked again**
   - **gliderlabs/ssh does NOT update `ctx.SetValue(ContextKeyPublicKey, key)`**
   - Signature verification succeeds (because it's signed by allowed_key which is valid)
   - **Session starts with `PublicKey()` returning `attacker_key` but signature was from `allowed_key`**

4. **Authorization Bypass**: Application session handler calls `s.PublicKey()` expecting it to match the authenticated key
   - But it returns `attacker_key` instead of `allowed_key`
   - See `/workspace/wish/examples/identity/main.go:37`: `ssh.KeysEqual(s.PublicKey(), carlos)`
   - This check would fail or give wrong identity

**Evidence**: `/workspace/wish/examples/identity/main.go:36-41`
```go
switch {
case ssh.KeysEqual(s.PublicKey(), carlos):
    wish.Println(s, "Hey Carlos!")
default:
    wish.Println(s, "Hey, I don't know who you are!")
}
```

### Mitigations: NONE IN CURRENT CODE

- No version pins to safe versions
- No documented workarounds
- No application-level mitigation in wish codebase
- The vulnerability is in the library wrapper, not in wish's usage

---

## Remediation

### Immediate Actions (Priority: HIGH)

1. **Upgrade gliderlabs/ssh**: Update from v0.3.4 to a patched version (if available)
   - OR update golang.org/x/crypto to v0.31.0 or later

2. **Fix gliderlabs/ssh Source** (if upgrading gliderlabs/ssh itself):
   - Only call `ctx.SetValue(ContextKeyPublicKey, key)` after successful signature verification, not during query phase
   - Modify `/workspace/ssh/server.go` to track whether this is a query vs. actual auth

3. **In wish** (mitigations):
   - Pin golang.org/x/crypto to v0.31.0 or later
   - Upgrade gliderlabs/ssh to a version that fixes this issue
   - Add integration tests that verify `s.PublicKey()` returns the correct key during session

### Recommended go.mod Changes

```go
// wish/go.mod
require (
    github.com/gliderlabs/ssh v0.3.5  // or later patched version
    golang.org/x/crypto v0.31.0        // or later
)
```

### Alternative: Fix in gliderlabs/ssh Wrapper

If gliderlabs/ssh cannot be upgraded, the callback in `/workspace/ssh/server.go` should be modified:

```go
if srv.PublicKeyHandler != nil {
    config.PublicKeyCallback = func(conn gossh.ConnMetadata, key gossh.PublicKey) (*gossh.Permissions, error) {
        applyConnMetadata(ctx, conn)
        if ok := srv.PublicKeyHandler(ctx, key); !ok {
            return ctx.Permissions().Permissions, fmt.Errorf("permission denied")
        }
        // DON'T set ContextKeyPublicKey here - it will be set after sig verification in golang.org/x/crypto
        // ctx.SetValue(ContextKeyPublicKey, key)  // REMOVED
        return ctx.Permissions().Permissions, nil
    }
}
```

But this requires changes to how the key is passed back from the SSH library, which would need upstream fixes in golang.org/x/crypto or gliderlabs/ssh.

---

## Summary Timeline

- **June 2021**: golang.org/x/crypto v0.0.0-20210616 released (vulnerable)
- **v0.5.0 Release**: charmbracelet/wish v0.5.0 released, depends on gliderlabs/ssh v0.3.4
- **December 2024**: golang.org/x/crypto v0.31.0 released with fix for CVE-2024-45337
- **Now**: wish is still using vulnerable transitive dependency
- **Action Required**: Update dependencies to patched versions

---

## Conclusion

CVE-2024-45337 affects `charmbracelet/wish` v0.5.0 through:
1. Direct transitive dependency on vulnerable golang.org/x/crypto
2. Vulnerable wrapper code in gliderlabs/ssh that misuses PublicKeyCallback
3. Potential for authorization bypass if an attacker can query multiple keys

**Status**: Requires dependency updates and/or upstream patches
