# CVE-2024-45337 Transitive Dependency Analysis

## Summary

**AFFECTED: YES - HIGH RISK**

The `charmbracelet/wish` project v0.5.0 is affected by CVE-2024-45337 through its transitive dependency on a vulnerable version of `golang.org/x/crypto/ssh`. The vulnerability is exposed in real application code that uses `session.PublicKey()` to make authorization decisions, including the bundled Git middleware and example code. An attacker can manipulate public key authentication by querying multiple keys before authenticating, causing the framework to return the wrong public key to the application's authorization logic.

## Dependency Chain Analysis

### Direct Dependency: wish → gliderlabs/ssh

**Evidence:**
- File: `/workspace/wish/go.mod` (line 9)
- Declaration: `github.com/gliderlabs/ssh v0.3.4`

The `charmbracelet/wish` project directly depends on `gliderlabs/ssh` v0.3.4. This dependency is used extensively throughout wish:
- Wrapper functions in `/workspace/wish/options.go` (lines 73-163) - provides public key authentication helpers
- SSH server creation in `/workspace/wish/wish.go` (lines 19-39) - creates gliderlabs/ssh servers
- Examples and middleware throughout the codebase use gliderlabs/ssh

### Transitive Dependency: gliderlabs/ssh → golang.org/x/crypto

**Evidence:**
- File: `/workspace/ssh/go.mod` (line 7)
- Declaration: `golang.org/x/crypto v0.0.0-20210616213533-5ff15b29337e` (June 16, 2021)

This is the **vulnerable version**. It is from June 2021 and predates the fix which was released in v0.31.0 (December 2024).

Additionally, `charmbracelet/wish` directly specifies:
- File: `/workspace/wish/go.mod` (line 14)
- Declaration: `golang.org/x/crypto v0.0.0-20220307211146-efcb8507fb70` (March 7, 2022)

While wish's direct dependency is newer, the transitive dependency through gliderlabs/ssh remains vulnerable, and both versions predate the December 2024 fix.

### Vulnerable Code Usage

**Evidence:**

The vulnerable code path is `golang.org/x/crypto/ssh` ServerConfig.PublicKeyCallback mechanism (`/workspace/crypto/ssh/server.go`, lines 488-573):

1. **When client queries a key** (`isQuery=true`, lines 532-550):
   - PublicKeyCallback is invoked to check if the key is acceptable
   - Result is cached by (username, pubKeyData) pair
   - Server responds with acceptance

2. **When client authenticates** (`isQuery=false`, lines 551-573):
   - Cached result is reused if key was previously queried
   - Signature is verified
   - Authentication succeeds without calling PublicKeyCallback again

The vulnerability manifests because clients can query multiple public keys before attempting authentication with one of them, but the cache and context state in gliderlabs/ssh implementation don't track which key was actually used.

## Code Path Trace

### Entry Point in wish: Public Key Authorization

**Files with vulnerable usage:**

1. **`/workspace/wish/git/git.go` (lines 76-77, 86, 100)** - PRIMARY VULNERABILITY
   ```go
   pk := s.PublicKey()
   access := gh.AuthRepo(repo, pk)
   // ... later ...
   gh.Push(repo, pk)
   gh.Fetch(repo, pk)
   ```
   The Git middleware retrieves the public key from the session and passes it to authorization hooks. If a client queries multiple keys, `s.PublicKey()` returns the last queried key, not the authenticated key. This leads to incorrect authorization decisions for repository access.

2. **`/workspace/wish/examples/identity/main.go` (lines 33-43)** - EXAMPLE DEMONSTRATING VULNERABILITY
   ```go
   switch {
   case ssh.KeysEqual(s.PublicKey(), carlos):
       wish.Println(s, "Hey Carlos!")
   default:
       wish.Println(s, "Hey, I don't know who you are!")
   }
   ```
   This example code identifies users by comparing the public key returned from the session. Due to CVE-2024-45337, if an attacker queries Carlos's key and then their own key before authenticating with Carlos's key, the application will incorrectly report "I don't know who you are!"

3. **`/workspace/wish/logging/logging.go` (line 19)** - NOT VULNERABLE
   Only checks if PublicKey is nil, doesn't use the actual key value for decisions.

### Wrapper in gliderlabs/ssh: PublicKeyCallback Integration

**File: `/workspace/ssh/server.go` (lines 144-153)**

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

**The vulnerability mechanism:**
1. gliderlabs/ssh wraps the user-provided `PublicKeyHandler` into golang.org/x/crypto's `ServerConfig.PublicKeyCallback`
2. Each time PublicKeyCallback is invoked (once per queried key), it calls `ctx.SetValue(ContextKeyPublicKey, key)` to store the key in the context
3. The context persists across the entire authentication attempt
4. When the client queries multiple keys:
   - Key1 is queried → PublicKeyCallback called → ContextKeyPublicKey set to Key1
   - Key2 is queried → PublicKeyCallback called → ContextKeyPublicKey overwritten with Key2
   - Authentication with Key1 → PublicKeyCallback NOT called (cached result used) → ContextKeyPublicKey remains as Key2
5. The session's `PublicKey()` method (in `/workspace/ssh/session.go`) returns the wrong key

### Vulnerable Code in golang.org/x/crypto

**File: `/workspace/crypto/ssh/server.go` (lines 519-573)**

The vulnerability is in the public key authentication flow:

```go
// Lines 519-530: Check cache and call callback
candidate, ok := cache.get(s.user, pubKeyData)
if !ok {
    candidate.user = s.user
    candidate.pubKeyData = pubKeyData
    candidate.perms, candidate.result = config.PublicKeyCallback(s, pubKey)  // Called per key
    cache.add(candidate)
}

// Lines 532-550: Query handling
if isQuery {
    if candidate.result == nil {
        okMsg := userAuthPubKeyOkMsg{...}
        s.transport.writePacket(Marshal(&okMsg))
        continue userAuthLoop  // Wait for next key or authentication
    }
    authErr = candidate.result
}

// Lines 551-573: Authentication handling
} else {
    // Verify signature
    if err := pubKey.Verify(signedData, sig); err != nil {
        return nil, err
    }
    authErr = candidate.result  // Uses cached result
    perms = candidate.perms     // Uses cached perms
}
```

The issue: when multiple keys are queried before authentication, each callback invocation in the wrapper code sets the context value, but only the last one persists. On actual authentication, the cached result is used without re-invoking the callback, so the context contains the wrong key.

## Impact Assessment

**Affected**: YES

**Risk Level**: HIGH

**Exploitability**:

A practical attack scenario:
1. Attacker has two SSH keys: `attacker_key` (with no access) and `alice_key` (with admin access to repos)
2. Attacker obtains alice's public key (e.g., from GitHub, GitLab, or a public server)
3. Attacker initiates SSH connection and queries `alice_key` first (server responds with OK)
4. Attacker queries `attacker_key` next (server responds with rejection or OK depending on configuration)
5. Attacker authenticates using `attacker_key` (signature verification succeeds because they have the private key)
6. The wish application receives `s.PublicKey()` returning `alice_key` (the last queried key)
7. Git middleware calls `gh.AuthRepo(repo, alice_key)` and grants admin access based on alice's key
8. Attacker can now push code to restricted repositories as if they were alice

**Attack Requirements:**
- Access to the remote SSH server running wish
- Knowledge of a legitimate user's public key (easily obtainable)
- Possession of a private key that can authenticate to the server (via password, other key, keyboard-interactive)

**Mitigations in Code:**

None currently exist in the wish/gliderlabs/ssh code. The vulnerability is in the underlying golang.org/x/crypto/ssh library's design, which caches public key callback results by key data rather than tracking which key was actually used for authentication.

## Remediation

### Recommended Actions:

1. **Immediate (Urgent):**
   - Upgrade `golang.org/x/crypto` to v0.31.0 or later in both wish and gliderlabs/ssh dependencies
   - This is a transitive dependency, but requiring it will force the upgrade
   - In wish/go.mod: `require golang.org/x/crypto v0.31.0` (or latest)
   - Run `go mod tidy` to cascade the upgrade

2. **Short-term (Before upgrading):**
   - Applications using wish should NOT use `session.PublicKey()` for authorization decisions if they support multiple public keys per user
   - Instead, implement custom authorization that doesn't rely on the public key from the session context
   - For Git middleware: store the authorized user identity in a custom context value during the PublicKeyAuth handler, not at session time

3. **Testing:**
   - Add test cases that verify authorization behavior when clients query multiple keys
   - Test that `session.PublicKey()` returns the correct key even when multiple keys are queried
   - Examples: `/workspace/crypto/ssh/test/multi_auth_test.go` shows multi-key authentication testing

### Version Requirements:

The fix requires upgrading golang.org/x/crypto to v0.31.0 or later. This version was released December 10, 2024.

The vulnerable versions currently in use:
- gliderlabs/ssh: golang.org/x/crypto v0.0.0-20210616213533-5ff15b29337e (June 16, 2021)
- wish: golang.org/x/crypto v0.0.0-20220307211146-efcb8507fb70 (March 7, 2022)

Both are 2-3+ years old and well before the December 2024 fix.

### Code Changes Needed:

While the library is updated, applications should consider:
1. Not relying on `session.PublicKey()` for authorization
2. Storing the authenticated user identity in a separate context value in the PublicKeyAuth callback
3. Using that stored value instead of `session.PublicKey()` for authorization decisions
