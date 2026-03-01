# CVE-2024-45337 Transitive Dependency Analysis

## Summary

**Is wish affected?** YES

**Verdict**: `charmbracelet/wish` v0.5.0 is **AFFECTED** by CVE-2024-45337. The project depends transitively on a vulnerable version of `golang.org/x/crypto/ssh` (v0.0.0-20210616213533-5ff15b29337e from June 2021, vulnerable before v0.31.0 from December 2024). The vulnerability is exposed through wish's public key authentication APIs, which directly wrap the vulnerable `PublicKeyCallback` mechanism. While wish's built-in authentication handlers implement the callback correctly, applications using wish with custom `PublicKeyAuth` handlers could be vulnerable to authorization bypass if they misuse the API.

---

## Dependency Chain Analysis

### Direct Dependency: wish → gliderlabs/ssh

**File**: `wish/go.mod`, line 9

```go
require (
    github.com/gliderlabs/ssh v0.3.4
    ...
)
```

**Evidence**: wish v0.5.0 directly requires gliderlabs/ssh v0.3.4 for SSH server functionality.

**Code Usage** (wish/wish.go, line 8):
```go
"github.com/gliderlabs/ssh"
```

### Transitive Dependency: gliderlabs/ssh → golang.org/x/crypto

**File**: `ssh/go.mod`, line 7

```go
require (
    golang.org/x/crypto v0.0.0-20210616213533-5ff15b29337e
    ...
)
```

**Evidence**: gliderlabs/ssh v0.3.4 requires golang.org/x/crypto at a vulnerable commit from June 2021. This version is significantly older than the fix in v0.31.0 (December 2024).

**Import Chain** (ssh/server.go, line 11):
```go
gossh "golang.org/x/crypto/ssh"
```

### Vulnerable Code Usage

The vulnerable `PublicKeyCallback` is actively used in gliderlabs/ssh.

**File**: `ssh/server.go`, lines 144-153

```go
if srv.PublicKeyHandler != nil {
    config.PublicKeyCallback = func(conn gossh.ConnMetadata, key gossh.PublicKey) (*gossh.Permissions, error) {
        applyConnMetadata(ctx, conn)
        if ok := srv.PublicKeyHandler(ctx, key); !ok {
            return ctx.Permissions().Permissions, fmt.Errorf("permission denied")
        }
        ctx.SetValue(ContextKeyPublicKey, key)
        return ctx.Permissions().Permissions, nil
    }
}
```

This code directly configures `golang.org/x/crypto/ssh`'s `ServerConfig.PublicKeyCallback`, which is the vulnerable component.

---

## Code Path Trace

### Entry Point in wish

wish exposes three public APIs for public key authentication:

#### 1. WithPublicKeyAuth (wish/options.go, lines 160-163)

```go
// WithPublicKeyAuth returns an ssh.Option that sets the public key auth handler.
func WithPublicKeyAuth(h ssh.PublicKeyHandler) ssh.Option {
    return ssh.PublicKeyAuth(h)
}
```

This allows applications to provide custom authentication logic. Used in examples:
- `examples/identity/main.go`, line 26
- `git/git_test.go`, line 40

#### 2. WithAuthorizedKeys (wish/options.go, lines 72-88)

```go
func WithAuthorizedKeys(path string) ssh.Option {
    return func(s *ssh.Server) error {
        keys, err := parseAuthorizedKeys(path)
        if err != nil {
            return err
        }
        return WithPublicKeyAuth(func(_ ssh.Context, key ssh.PublicKey) bool {
            for _, upk := range keys {
                if ssh.KeysEqual(upk, key) {
                    return true
                }
            }
            return false
        })(s)
    }
}
```

#### 3. WithTrustedUserCAKeys (wish/options.go, lines 90-131)

```go
func WithTrustedUserCAKeys(path string) ssh.Option {
    return func(s *ssh.Server) error {
        cas, err := parseAuthorizedKeys(path)
        if err != nil {
            return err
        }

        return WithPublicKeyAuth(func(ctx ssh.Context, key ssh.PublicKey) bool {
            cert, ok := key.(*gossh.Certificate)
            if !ok {
                return false
            }

            checker := &gossh.CertChecker{
                IsUserAuthority: func(auth gossh.PublicKey) bool {
                    for _, ca := range cas {
                        if bytes.Equal(auth.Marshal(), ca.Marshal()) {
                            return true
                        }
                    }
                    return false
                },
            }

            if !checker.IsUserAuthority(cert.SignatureKey) {
                return false
            }

            if err := checker.CheckCert(ctx.User(), cert); err != nil {
                return false
            }

            return true
        })(s)
    }
}
```

### Wrapper in gliderlabs/ssh

**File**: `ssh/server.go`, lines 144-153

gliderlabs/ssh wraps the wish (or application-provided) `PublicKeyHandler` and uses it to implement the callback required by golang.org/x/crypto/ssh:

```go
config.PublicKeyCallback = func(conn gossh.ConnMetadata, key gossh.PublicKey) (*gossh.Permissions, error) {
    applyConnMetadata(ctx, conn)
    if ok := srv.PublicKeyHandler(ctx, key); !ok {
        return ctx.Permissions().Permissions, fmt.Errorf("permission denied")
    }
    ctx.SetValue(ContextKeyPublicKey, key)
    return ctx.Permissions().Permissions, nil
}
```

This callback is registered directly with golang.org/x/crypto/ssh's `ServerConfig`.

### Vulnerable Code in golang.org/x/crypto

The vulnerable component is `golang.org/x/crypto/ssh`'s `ServerConfig.PublicKeyCallback`. According to CVE-2024-45337, this callback:

1. **May be called multiple times** with different public keys during a single authentication attempt
2. **The order is not deterministic** and cannot be used for authorization decisions
3. **Misuse includes**:
   - Assuming the callback is called only once per authentication
   - Making authorization decisions based on key order
   - Storing state across calls without proper synchronization

The SSH protocol allows clients to inquire about key acceptance before proving control of the private key, leading to multiple `PublicKeyCallback` invocations.

---

## Impact Assessment

### Affected: YES

The vulnerable code path is active in wish:
1. ✅ wish depends on vulnerable gliderlabs/ssh
2. ✅ gliderlabs/ssh depends on vulnerable golang.org/x/crypto
3. ✅ gliderlabs/ssh uses `PublicKeyCallback`
4. ✅ wish exposes this through public APIs

### Risk Level: MEDIUM to HIGH

**For wish's built-in handlers**: LOW RISK
- `WithAuthorizedKeys` checks each key individually without assuming single calls
- `WithTrustedUserCAKeys` validates each certificate independently
- These handlers do not make the mistakes described in the CVE

**For applications using wish**: MEDIUM to HIGH RISK
- Applications implementing custom `PublicKeyAuth` handlers could misuse the API
- If an application developer implements a handler that:
  - Stores authorization state across multiple calls
  - Assumes `PublicKeyCallback` is called only once
  - Makes authorization decisions based on call order

  Then that application would be vulnerable to authorization bypass.

### Exploitability

An attacker could exploit this if:

1. The target application uses wish with a vulnerable custom `PublicKeyAuth` handler
2. The handler makes authorization decisions based on key order or assumes single invocation
3. Example vulnerable pattern:

```go
var authorizedKey ssh.PublicKey

wish.WithPublicKeyAuth(func(ctx ssh.Context, key ssh.PublicKey) bool {
    // VULNERABLE: Assumes this is called only once and stores global state
    authorizedKey = key
    return true // Authorize the first key offered
})
```

In this case, an attacker could offer a malicious key first, followed by a legitimate key, and be authorized with the malicious key.

### Mitigations

**In wish's code**: Already present
- `WithAuthorizedKeys`: Validates each key individually
- `WithTrustedUserCAKeys`: Validates each certificate independently

**In applications using wish**: Required
- Applications should not assume single callback invocation
- Should validate each key independently
- Should not use global state for authorization decisions

---

## Remediation

### Immediate Actions

1. **Update golang.org/x/crypto**: Update gliderlabs/ssh to a version that depends on golang.org/x/crypto >= v0.31.0
   - Current: v0.0.0-20210616213533-5ff15b29337e (June 2021)
   - Target: v0.31.0 or later (December 2024+)

2. **Audit custom handlers**: Applications using wish should review custom `PublicKeyAuth` handlers for the vulnerable patterns described above

### Long-term Solution

Maintain dependency updates. The gliderlabs/ssh and golang.org/x/crypto projects continue to receive security updates. Ensure:
- Regular dependency audits
- Automated vulnerability scanning
- Timely patching of transitive dependencies

### Version Planning

The fix requires updating:
1. `golang.org/x/crypto` to >= v0.31.0
2. `gliderlabs/ssh` to a version that requires the updated crypto library
3. `charmbracelet/wish` to depend on the updated gliderlabs/ssh

---

## Summary Table

| Component | Version | Status | CVE Affected |
|-----------|---------|--------|--------------|
| charmbracelet/wish | v0.5.0 | AFFECTED | Yes (transitive) |
| gliderlabs/ssh | v0.3.4 | AFFECTED | Yes (direct) |
| golang.org/x/crypto | v0.0.0-20210616... (June 2021) | VULNERABLE | Yes |
| golang.org/x/crypto | v0.31.0+ (Dec 2024) | FIXED | No |

---

## Evidence Files

- wish/go.mod (line 9): Direct dependency on gliderlabs/ssh v0.3.4
- ssh/go.mod (line 7): Transitive dependency on vulnerable golang.org/x/crypto
- ssh/server.go (lines 144-153): Usage of PublicKeyCallback
- wish/options.go (lines 72-131): Public APIs exposing PublicKeyAuth
- ssh/ssh.go (line 39): PublicKeyHandler type definition
