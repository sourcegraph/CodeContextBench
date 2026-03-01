# Envoy Contributor Guide

## 1. Build Prerequisites

### Required Tools and Dependencies

Before building Envoy, you must install the following:

**Bazel Build System:**
- **Bazel version:** 6.5.0 (specified in `.bazelversion`)
- **Installation:** Use [Bazelisk](https://github.com/bazelbuild/bazelisk) to automatically manage Bazel versions

  Linux (x86_64/ARM64):
  ```bash
  sudo wget -O /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-$([ $(uname -m) = "aarch64" ] && echo "arm64" || echo "amd64")
  sudo chmod +x /usr/local/bin/bazel
  ```

  macOS:
  ```bash
  brew install bazelisk
  ```

**C++ Compiler Toolchain:**
- **Ubuntu (primary CI environment):** GCC 9, Clang 14, based on Ubuntu 20.04 (Focal)
- **CI Image:** `envoyproxy/envoy-build-ubuntu` with hash specified in `ci/envoy_build_sha.sh`

**C++ Standard Library:**
- Official releases use **libc++** on Linux (as of v1.21.0)
- Override via environment: `export ENVOY_STDLIB=libc++` or `export ENVOY_STDLIB=libstdc++`

**System Dependencies:**
- Documented in [Envoy's official build documentation](https://www.envoyproxy.io/docs/envoy/latest/start/building#requirements)
- In production, install independently; for development, use Docker containers

**Development Support Toolchain (Recommended):**
- Install via: `./support/bootstrap` (from repo root)
- Provides Git hooks for:
  - Automatic DCO sign-off generation
  - Pre-push format validation
  - Documentation: `support/README.md`

## 2. Build System

### Build System: Bazel

Envoy uses **Bazel** as its primary build system. All code is organized as Bazel targets with explicit dependencies.

### Key Build Commands

**Quick Start (Developer Build with Tests):**
```bash
# Using Docker (recommended for consistent environment)
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

**Native Build (with dependencies installed):**
```bash
# Optimized build
bazel build -c opt envoy

# Debug build
bazel build -c dbg envoy

# Fastbuild (development, fastest)
bazel build -c fastbuild envoy
```

**Build Specific Components:**
```bash
# Build a specific test
bazel test //path/to:test_target

# Build a specific library
bazel build //path/to:library_target

# Build with all contrib extensions
./ci/run_envoy_docker.sh './ci/do_ci.sh dev.contrib'
```

### Build Configurations

**Production/Release:**
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh release.server_only'
# Output: `/tmp/envoy-docker-build/envoy/source/exe/envoy` (or custom `$ENVOY_DOCKER_BUILD_DIR`)
```

**Debug Build:**
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh debug.server_only'
# Output: `/tmp/envoy-docker-build/envoy/source/exe/envoy-debug`
```

**Size-Optimized:**
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh sizeopt.server_only'
```

### Docker-Based Development

The recommended approach for consistent builds is using Docker:

```bash
# Basic invocation
./ci/run_envoy_docker.sh './ci/do_ci.sh <target>'

# Custom build directory
ENVOY_DOCKER_BUILD_DIR=~/build ./ci/run_envoy_docker.sh './ci/do_ci.sh dev'

# Force Docker image refresh
ENVOY_DOCKER_PULL=true ./ci/run_envoy_docker.sh './ci/do_ci.sh dev'

# Interactive Docker session
./ci/run_envoy_docker.sh 'bash'
```

**Available Docker Images:**
- `envoyproxy/envoy-build-ubuntu` (default, Ubuntu 20.04)
- `envoyproxy/envoy-build-centos` (experimental)
- Set via: `IMAGE_NAME=envoyproxy/envoy-build-ubuntu ./ci/run_envoy_docker.sh ...`

### Build Configuration Files

- `WORKSPACE`: Bazel workspace definition
- `.bazelrc`: Bazel configuration (format, test options, etc.)
- `bazel/`: Bazel rules and configurations
- `BUILD`: Top-level Bazel build file

## 3. Running Tests

### Test Frameworks

Envoy uses:
- **Unit Tests:** [Google Test (GTest)](https://github.com/google/googletest) + [Google Mock](https://github.com/google/googletest/blob/master/googlemock/README.md)
- **Integration Tests:** Custom framework for testing downstream-Envoy-upstream communication
- **Fuzz Tests:** libFuzzer-based tests with ASAN instrumentation
- **Benchmark Tests:** Google Benchmark for microbenchmarks

### Running Tests via Docker (Recommended)

**All tests:**
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

**Specific test:**
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh dev //test/common/http:http_test'
```

**Test coverage report:**
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh coverage'
# Output: `$ENVOY_DOCKER_BUILD_DIR/envoy/generated/coverage/coverage.html`
```

### Running Tests Natively (With Dependencies)

```bash
# Run all tests
bazel test //...

# Run specific test
bazel test //test/common/http:http_test

# Run test with debug symbols
bazel test -c dbg //test/common/http:http_test

# Run test matching pattern
bazel test --test_tag_filters=tag //...
```

### Specialized Test Targets (via Docker)

- `asan` — AddressSanitizer (memory errors)
- `msan` — MemorySanitizer (uninitialized memory)
- `tsan` — ThreadSanitizer (race conditions)
- `fuzz` — libFuzzer-based fuzz tests
- `compile_time_options` — Test with non-default compile flags
- `coverage` — Generate coverage reports

Example:
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh asan'
./ci/run_envoy_docker.sh './ci/do_ci.sh tsan //test/common/http:http_test'
```

### Test Utilities and Helpers

**Location:** `test/` directory mirrors `source/` structure
- Unit tests: `test/common/`, `test/server/`, `test/exe/`
- Integration tests: `test/integration/` with framework in `test/integration/integration.h`
- Mocks: `test/mocks/` (mock implementations of core interfaces)
- Test infrastructure: `test/test_common/` (time system, utilities)

**Integration Test Framework:**
- See: `test/integration/README.md`
- Key helper: `ConfigHelper` (in `test/config/utility.h`) for modifying test configs
- Autonomous upstream mode for simplified testing: set `autonomous_upstream_ = true`

**Custom GTest Matchers:**
- `HeaderValueOf()` — Check specific header values
- `HttpStatusIs()` — Check HTTP status codes
- `HeaderMapEqual()` / `HeaderMapEqualRef()` — Compare headers
- `ProtoEq()` / `ProtoEqIgnoringField()` — Compare protobufs

## 4. CI Pipeline

### CI Platform

**Primary:** [Azure Pipelines](https://dev.azure.com/cncf/envoy/_build)
- Organization: `cncf`
- Definition ID: 11
- **Status badge:** [![Azure Pipelines](https://dev.azure.com/cncf/envoy/_apis/build/status/11?branchName=main)](https://dev.azure.com/cncf/envoy/_build/latest?definitionId=11&branchName=main)

**Additional CI Systems:**
- **Jenkins:** ppc64le builds (OSUOSL), s390x builds (OSUOSL)
- **OSS-Fuzz:** Continuous fuzzing (Google)
- **Zuul:** Additional platform-specific builds (referenced in `.zuul/`, `.zuul.yaml`)

### CI Configuration Files

- `.azure-pipelines/` — Azure Pipelines YAML configs
- `ci/do_ci.sh` — Master build script (invoked by CI)
- `ci/run_envoy_docker.sh` — Docker execution wrapper
- `ci/mac_ci_setup.sh` / `ci/mac_ci_steps.sh` — macOS build
- `ci/windows_ci_steps.sh` — Windows build (legacy, official support ended Aug 2023)
- `ci/envoy_build_sha.sh` — Docker image hashes
- `repokitteh.star` — Automation rules (GitHub checks, retesting)

### CI Checks on Pull Requests

**Standard checks:**
1. **Build** — All supported platforms (Linux/Ubuntu, CentOS, macOS; ~~Windows~~)
2. **Unit tests** — Google Test suite with multiple sanitizers (ASAN, MSAN, TSAN)
3. **Integration tests** — End-to-end Envoy networking tests
4. **Code coverage** — 100% coverage required for new code
5. **Code formatting** — clang-format validation
6. **Linting** — clang-tidy checks (error-level)
7. **API/Proto checks** — Proto format and API versioning
8. **Documentation** — Build and render docs

**Typical CI run duration:** 1-2 hours (varies by change scope)

### Triggering CI Retests

**Rerun failed Azure Pipelines checks:**
```
/retest
```
(Comment on PR)

**Force full CI re-run:**
```bash
git commit -s --allow-empty -m 'Kick CI'
git push
```

Or use git alias:
```bash
git config --add alias.kick-ci "!git commit -s --allow-empty -m 'Kick CI' && git push"
git kick-ci
```

### Remote Cache (Optional)

Accelerate builds via Bazel remote cache:

```bash
# In .bazelrc or user.bazelrc:
build:my-remote-cache --remote_cache=grpcs://remotecache.googleapis.com
build:my-remote-cache --remote_cache_header=Authorization="Bearer <token>"

# Use in build:
export BAZEL_BUILD_EXTRA_OPTIONS=--config=my-remote-cache
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

## 5. Code Review Process

### Communication Before Starting Major Work

**Required for significant changes (>100 LOC, user-facing behavior):**
1. **Open a GitHub issue** to discuss the feature/bug
2. **Get maintainer agreement** before coding
3. **Prevents:** wasted effort, design disagreements, duplicate work

**Not required for:** Small bug fixes, docs changes

**For new extensions:** See `EXTENSION_POLICY.md` for policy and requirements

**Relevant mailing lists:**
- `envoy-dev@googlegroups.com` — Discussions, design proposals
- `envoy-announce@googlegroups.com` — Announcements (for deprecations/breaking changes)
- `envoy-security@googlegroups.com` — Security vulnerabilities

### Submitting a Pull Request

**Setup:**
```bash
# Fork repo on GitHub
# Clone and install git hooks
git clone https://github.com/YOUR_USERNAME/envoy.git
cd envoy
./support/bootstrap  # Installs git hooks for DCO + format checks
```

**Create PR:**
1. **Branch off `main`:** `git checkout -b your-feature-branch`
2. **Write code** with tests (100% coverage for new code)
3. **Commit with DCO sign-off:**
   ```bash
   git commit -s -m "component: description"
   # or auto-added by support/bootstrap hook
   ```
4. **Push to your fork** and open PR on GitHub

### PR Title and Message Format

**Title format:** `component: description` (lowercase)

Examples:
- `docs: fix grammar error`
- `http conn man: add new feature`
- `router: add x-envoy-overloaded header`
- `tls: add support for TLS session ticket keys`

**Commit message:**
- Explain what changed and why
- If fixing issue: `Fixes #XXX`
- For behavioral changes: document before/after behavior
- For deprecations: list what's deprecated

**Use pull request template:** Automatically filled in when you open a PR
- **Risk level:** Low | Medium | High
- **Testing:** Describe testing performed
- **Documentation:** Link to docs/release notes changes
- **Release notes:** Update `changelogs/current.yaml` for user-facing changes
- **API changes:** Reference [API Review Checklist](api/review_checklist.md)

### DCO Sign-Off

All commits must be signed off with Developer Certificate of Origin:

```bash
git commit -s  # Adds: Signed-off-by: Your Name <your.email@example.com>
```

Auto-signup via git alias:
```bash
git config --add alias.c "commit -s"
```

**Fix DCO errors on existing PR:**
```bash
git rebase -i HEAD~N  # Squash commits
git commit -s --amend  # Add sign-off
git push origin -f  # Force push (acceptable only for DCO fixes)
```

### PR Review Requirements

- **Tests must pass** — No PRs merge with failing tests
- **100% code coverage** — All new code must be covered by tests (or justified)
- **Cross-company reviews** — For new extensions: at least one approver from a different organization than the author
- **Senior maintainer review** — Core code requires senior maintainer approval
- **Domain expert review** — Code should be reviewed by area expert (not necessarily maintainer)

**Maintainers and reviewers:** See `OWNERS.md` for area experts

### Coding Standards

**Format:** Automatically enforced via clang-format
- Line limit: 100 characters
- Run fixes: `bazel run //tools/code_format:check_format -- fix`

**Style:** [Google C++ style guide](https://google.github.io/styleguide/cppguide.html) with Envoy deviations:
- Function names: camelCase starting lowercase (e.g., `doFoo()`)
- Member variables: trailing underscore (e.g., `foo_`)
- Enum values: PascalCase (e.g., `RoundRobin`)
- Smart pointers: type aliased (e.g., `using FooPtr = std::unique_ptr<Foo>;`)
- `#pragma once` for header guards
- Code inside `Envoy` namespace
- Anonymous namespaces preferred over `static`
- Inclusive language policy: no "whitelist"/"blacklist"/"master"/"slave" terms

**Linting:** clang-tidy (error-level enforced)

**Inclusive language:**
- ❌ "whitelist" → ✅ "allowlist"
- ❌ "blacklist" → ✅ "denylist"/"blocklist"
- ❌ "master" → ✅ "primary"/"main"
- ❌ "slave" → ✅ "secondary"/"replica"

### Important PR Guidelines

- **Don't rebase after review starts** — GitHub forces reviewers to re-review everything
- Use merge to pull main changes:
  ```bash
  git checkout main && git pull && git checkout your-branch && git merge main
  ```
- **Format checks:** Run pre-push checks locally via `./support/bootstrap`
- **Don't use `--no-verify`** for hooks unless absolutely necessary (bypasses critical checks)
- **Stale PRs:** PRs with >7 days of inactivity may be closed; can be reopened
- **Pro-actively work on PR** — Don't abandon after opening
- **Don't force push** after review starts (exception: DCO sign-off fixes)

### PR Review Timeline

- **Expected response:** Within one business day
- **Senior maintainer:** Reviews all core code changes
- **Domain experts:** Should review relevant areas (may not be maintainers)
- **Anyone can review:** Community reviews welcome

### Merging

**Before merge:**
1. All tests pass
2. Coverage ≥100% for new code
3. All documentation updated
4. Release notes added (if user-facing)
5. PR title/body cleaned up by maintainer

**After merge:**
- If PR has deprecations: notification sent to `envoy-announce@`
- Squash merge used (commit history cleaned)
- Maintainer ensures final commit message is correct

### Runtime Guarding (High-Risk Changes)

Some changes (major refactors, behavioral changes to HTTP processing) require runtime guards:

```cpp
if (Runtime::runtimeFeatureEnabled("envoy.reloadable_features.my_feature_name")) {
  [new code path]
} else {
  [old_code_path]
}
```

- Both paths must have 100% coverage
- May be enabled by default or after testing period
- See: `source/common/runtime/runtime_features.cc`
- Reference: `CONTRIBUTING.md` "Runtime Guarding" section

## 6. Developer Workflow Example

### Scenario: Fix bug in HTTP Connection Manager filter

**Step 1: Discuss with community**
```
1. Search existing issues: Is this already tracked?
2. If not, open GitHub issue: "HTTP Connection Manager: [description of bug]"
3. Wait for confirmation from maintainers that it's not in progress
```

**Step 2: Set up development environment**
```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/envoy.git
cd envoy
./support/bootstrap

# Create feature branch
git checkout -b fix/http-conn-man-bug
```

**Step 3: Understand the codebase**
```bash
# HTTP Connection Manager code locations:
# - Core: source/common/http/conn_manager_impl.cc/h
# - Tests: test/common/http/conn_manager_impl_test.cc
# - Integration: test/integration/ (various HTTP tests)

# Search for references:
grep -r "conn_manager_impl" source/
```

**Step 4: Write tests first**
```bash
# Add failing test to test/common/http/conn_manager_impl_test.cc
# Build and verify it fails
./ci/run_envoy_docker.sh './ci/do_ci.sh dev //test/common/http:conn_manager_impl_test'
```

**Step 5: Implement the fix**
```bash
# Edit source/common/http/conn_manager_impl.cc
# Follow style guide and coding standards
```

**Step 6: Run full test suite locally**
```bash
# Run all HTTP-related tests
./ci/run_envoy_docker.sh './ci/do_ci.sh dev //test/common/http/...'

# Run with sanitizers
./ci/run_envoy_docker.sh './ci/do_ci.sh asan'

# Check code formatting
bazel run //tools/code_format:check_format -- fix
```

**Step 7: Commit and push**
```bash
# Commit with DCO sign-off
git add source/common/http/conn_manager_impl.{cc,h} test/common/http/conn_manager_impl_test.cc
git commit -s -m "http conn man: fix [specific issue]

Fixes #ISSUE_NUMBER

This commit fixes the HTTP connection manager by [explanation of fix].
The bug occurred when [reproduction steps]. This is now fixed by
[explanation of solution]."

# Push to fork
git push origin fix/http-conn-man-bug
```

**Step 8: Open PR on GitHub**
```
1. Go to: https://github.com/envoyproxy/envoy/compare/main...YOUR_USERNAME:fix/http-conn-man-bug
2. Fill in PR template:
   - Title: "http conn man: fix [issue]"
   - Risk: Low (if small fix) | Medium (if moderate) | High (if major)
   - Testing: "Added unit test in test/common/http/conn_manager_impl_test.cc"
   - Documentation: "N/A" or link to docs changes
   - Release notes: Add entry to changelogs/current.yaml
   - Issues: "Fixes #ISSUE_NUMBER"
3. Submit PR
```

**Step 9: Wait for CI and review**
```
1. Azure Pipelines runs (1-2 hours):
   - Builds on Linux (Ubuntu, CentOS)
   - macOS build
   - All tests run
   - Coverage checked
   - Code formatting verified
2. Maintainers and domain experts review
3. Address feedback (new commits, don't rebase)
```

**Step 10: Merge**
```
1. All tests pass ✓
2. All reviews approved ✓
3. Maintainer merges with squash
4. Your fix is in main!
5. Celebrate! 🎉
```

### Key Commands Cheat Sheet

```bash
# Setup
git clone https://github.com/YOUR_USERNAME/envoy.git && cd envoy
./support/bootstrap

# Development
git checkout -b feature-name

# Build and test (Docker)
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
./ci/run_envoy_docker.sh './ci/do_ci.sh dev //test/specific:test_target'
./ci/run_envoy_docker.sh './ci/do_ci.sh asan'  # AddressSanitizer
./ci/run_envoy_docker.sh './ci/do_ci.sh coverage'

# Format
bazel run //tools/code_format:check_format -- fix

# Commit
git add [files]
git commit -s -m "component: description"

# Push
git push origin feature-name

# Rebase incoming changes (don't force push)
git checkout main && git pull
git checkout feature-name && git merge main

# Rerun CI
# (comment on PR): /retest
# Or: git commit -s --allow-empty -m 'Kick CI' && git push
```

---

## Additional Resources

- **Build:** `bazel/README.md`
- **Tests:** `test/README.md`, `test/integration/README.md`
- **External dependencies:** `bazel/EXTERNAL_DEPS.md`
- **Bazel rules guide:** `bazel/DEVELOPER.md`
- **Extension policy:** `EXTENSION_POLICY.md`
- **API versioning:** `api/API_VERSIONING.md`
- **API review checklist:** `api/review_checklist.md`
- **Repository layout:** `REPO_LAYOUT.md`
- **Development toolchain:** `support/README.md`
- **VS Code setup:** `tools/vscode/README.md`

## Community

- **Slack:** https://envoyproxy.slack.com/ (for quick questions)
- **Mailing lists:** envoy-dev@, envoy-users@, envoy-announce@ (for announcements)
- **Community meeting:** Bi-weekly on Tuesdays at 9am PT (see public [calendar](https://goo.gl/PkDijT))
- **Code of conduct:** `CODE_OF_CONDUCT.md`
