# Envoy Contributor Guide

## 1. Build Prerequisites

Envoy requires the following tools and dependencies before building:

### Core Tools
- **Bazel/Bazelisk**: The Envoy project uses Bazel as its build system. It's recommended to use [Bazelisk](https://github.com/bazelbuild/bazelisk) which automatically manages Bazel versions.
  - **Linux**: Install via `sudo wget -O /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-$([ $(uname -m) = "aarch64" ] && echo "arm64" || echo "amd64")` and `sudo chmod +x /usr/local/bin/bazel`
  - **macOS**: Install via `brew install bazelisk`
  - **Windows**: Download from [Bazelisk releases](https://github.com/bazelbuild/bazelisk/releases) and add to PATH

### Build Dependencies
The following are required for building Envoy in production environments. For development, Docker containers are recommended (see section on CI Docker images).

- C++ compiler (Clang 14 or GCC 9+)
- Python 3.6+
- Git

### Development Docker Images
For a self-contained development environment, use the official Envoy build Docker images:
- **Linux**: `envoyproxy/envoy-build-ubuntu` (based on Ubuntu 20.04)
- **CentOS**: `envoyproxy/envoy-build-centos` (experimental, based on CentOS 7)
- **Windows**: `envoyproxy/envoy-build-windows2019` (official Windows support ended August 2023)

Retrieve the specific image SHA from `ci/envoy_build_sha.sh`.

### Setup Development Support Toolchain
Before contributing, install the development support toolchain for automatic DCO signoff and pre-commit format checking:

```bash
./support/bootstrap
```

This installs Git hooks from `support/hooks/` that:
- Automatically append DCO signoff to commits
- Run format and lint checks before push

Documentation: See `support/README.md`

---

## 2. Build System

Envoy uses **Bazel** as its build system. All build configuration is defined in `BUILD` files and `.bazelrc` configuration files.

### Key Build Concepts
- **BUILD files**: Located throughout the codebase, define build targets using Bazel rules
- **.bazelrc**: Main configuration file in the repository root
- **Bazel rules**: Custom Envoy-specific rules defined in `bazel/` directory (e.g., `envoy_cc_library`, `envoy_cc_extension`, etc.)

### Building for Development

#### Using Docker (Recommended)
The easiest way to build for development is using the provided Docker script:

```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

This builds Envoy with fastbuild configuration inside a standardized container. Output binary: `/tmp/envoy-docker-build/envoy/source/exe/envoy-fastbuild`

Control output directory with environment variable:
```bash
ENVOY_DOCKER_BUILD_DIR=~/build ./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

#### Direct Bazel Commands (Linux/macOS)
If you have build dependencies installed locally:

```bash
# Development build (fastbuild, fastest)
bazel build -c fastbuild //source/exe:envoy-static

# Release build (optimized)
bazel build -c opt //source/exe:envoy-static

# Debug build (with symbols)
bazel build -c dbg //source/exe:envoy-static

# Build a specific test
bazel build //test/common/network:connection_test
```

### Build Configurations Available

#### Via `./ci/do_ci.sh <TARGET>` in Docker:
- **dev** — fastbuild with tests
- **dev <test>** — fastbuild for specific test
- **debug** — dbg configuration with tests
- **debug <test>** — dbg for specific test
- **release** — opt configuration with tests
- **release <test>** — opt for specific test
- **release.server_only** — opt configuration, binary only
- **debug.server_only** — dbg configuration, binary only
- **asan** — ASAN sanitizer build with tests
- **msan** — MSAN sanitizer build with tests
- **tsan** — TSAN sanitizer build with tests
- **coverage** — coverage build with gcc
- **compile_time_options** — test various compile flags
- **format** — run formatting and linting
- **clang_tidy** — run clang-tidy analysis

### Building Extensions and Specific Components

To build only specific packages (not the entire repo):

```bash
# Build HTTP connection manager filter
bazel build //source/extensions/filters/network/http_connection_manager:config_lib

# Build and test HTTP filters
bazel test //source/extensions/filters/http/...
```

### Build File Structure

Core Bazel rules used in Envoy:
- `envoy_cc_library` — C++ library
- `envoy_cc_binary` — C++ binary
- `envoy_cc_test` — C++ unit test
- `envoy_cc_extension` — Extension (filter, etc.)
- `envoy_integration_test` — Integration test
- `envoy_benchmark_test` — Benchmark test

Location: `bazel/envoy_build_system.bzl` and `bazel/DEVELOPER.md`

---

## 3. Running Tests

Envoy uses **Google Test** framework for unit tests and a custom integration test framework for end-to-end testing.

### Test Frameworks

1. **Google Test (gtest)**: Unit tests using Google Test macros (EXPECT_*, ASSERT_*)
2. **Google Mock (gmock)**: Mocking and matchers for unit tests
3. **Integration Test Framework**: Custom framework in `test/integration/` for downstream-Envoy-upstream testing
4. **Benchmark Tests**: Performance testing via Google Benchmark

### Running All Tests

#### Using Docker (Recommended):
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

#### Direct Bazel:
```bash
# Run all tests in fastbuild
bazel test -c fastbuild //test/...

# Run with test args (e.g., verbose output)
bazel test -c fastbuild //test/... --test_arg="-l trace"

# Run with multiple jobs for parallelization
bazel test -c fastbuild //test/... --jobs 60
```

### Running Specific Tests

```bash
# Run all tests in a directory
bazel test //test/common/network:*

# Run a specific test file
bazel test //test/common/network:connection_test

# Run a specific test case
bazel test //test/common/network:connection_test --test_filter="ConnectionTest.Accepted"

# Run integration tests
bazel test //test/integration:http_integration_test
```

### Integration Tests

Integration tests validate end-to-end downstream-Envoy-upstream communication. They're located in `test/integration/`:

```bash
bazel test //test/integration:http_integration_test
bazel test //test/integration:http2_upstream_integration_test
```

Integration tests can be parameterized to run with different configurations (IPv4/IPv6, HTTP/1.1, HTTP/2, etc.).

### Test Coverage

Envoy requires **100% test coverage for added code**. Generate coverage reports:

```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh coverage'
```

Coverage output: `$ENVOY_DOCKER_BUILD_DIR/envoy/generated/coverage/coverage.html`

Or for a specific test:
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh coverage //test/common/network:connection_test'
```

### Test Utilities and Helpers

Key test utilities located in `test/`:
- `test/test_common/` — Common test utilities
- `test/mocks/` — Mock implementations of core interfaces
- `test/integration/` — Integration test framework
- `test/config/` — Configuration utilities for tests

Important test macros and patterns (from `test/README.md`):
- `EXPECT_THAT()` with `HeaderValueOf()`, `HttpStatusIs()`, etc. for HTTP testing
- `SimulatedTimeSystem` for deterministic time-based tests
- `Event::TestTimeSystem` for controlling time in tests

---

## 4. CI Pipeline

Envoy uses **Azure Pipelines** as the primary CI system, with additional tooling for distributed testing.

### CI Platform: Azure Pipelines

Azure Pipelines automatically runs on all pull requests to `envoyproxy/envoy`. Access it at:
https://dev.azure.com/cncf/envoy/_build

### CI Configuration Files

- **`.azure-pipelines/`** — Main CI configuration directory (not present in this version but referenced in README.md)
- **`ci/do_ci.sh`** — Main CI script that orchestrates builds and tests
- **`ci/run_envoy_docker.sh`** — Docker runner for local CI reproduction
- **`ci/mac_ci_steps.sh`** — macOS-specific build and test steps
- **`ci/mac_ci_setup.sh`** — macOS dependency installation via Homebrew
- **`ci/windows_ci_steps.sh`** — Windows build and test steps (deprecated)

### CI Checks Run on Pull Requests

1. **Compilation**: Build Envoy with multiple configurations (fastbuild, opt, dbg)
2. **Testing**: Run full unit and integration test suite
3. **Sanitizers**: ASAN, MSAN, TSAN builds and tests
4. **Format Checking**: Code formatting, clang-tidy, proto format validation
5. **Coverage**: Coverage build and analysis
6. **Platform-Specific**: macOS builds via Azure Pipelines

### CI Targets

All CI targets can be run locally via:
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh <TARGET>'
```

Where `<TARGET>` is one of: `api`, `asan`, `debug`, `dev`, `dev.contrib`, `release`, `sizeopt`, `coverage`, `msan`, `tsan`, `fuzz`, `compile_time_options`, `clang_tidy`, `format`, `check_proto_format`, `docs`.

### CI Timing

- Typical full CI run: **30-45 minutes**
- Can be parallelized across multiple machines/jobs
- PRs are checked against main branch

### Triggering CI Reruns

To rerun CI without making code changes:

1. **Retest failed tasks**: Add comment `/retest` to PR
2. **Full rerun**: Push empty commit: `git commit -s --allow-empty -m 'Kick CI' && git push` (or use alias from `.gitconfig`)

### Distributed Testing Infrastructure

- **Remote Build Cache**: Optional for faster rebuilds
- **RBE (Remote Build Execution)**: Can be configured for distributed test execution
- **Bazel CI Integration**: `.bazelci/` directory contains Bazel-specific CI configs

---

## 5. Code Review Process

### Contribution Workflow

1. **Discuss major features**: Before starting work on features >100 LOC or behavior changes, open a GitHub issue to discuss with maintainers
2. **Small patches**: Bug fixes and small patches don't require prior discussion
3. **Fork and branch**: Fork the repository and create a feature branch
4. **Local hooks**: Run `./support/bootstrap` to install pre-commit hooks
5. **Code and test**: Write code and tests (100% coverage required)
6. **Documentation**: Update docs and release notes for user-facing changes
7. **Commit message**: Follow format: `subsystem: description`
8. **Create PR**: Push to your fork and create PR against `main` branch

### Pull Request Requirements

**Before submitting:**
- All tests pass locally
- 100% test coverage for new code
- Code follows `STYLE.md` guidelines
- Commit has DCO signoff (automatic via `./support/bootstrap`)
- Release notes added to `changelogs/current.yaml` if user-facing
- Documentation updated in `docs/` if applicable

**PR Title Format:**
- Lowercase component/subsystem name followed by colon
- Examples:
  - `docs: fix grammar error`
  - `http conn man: add new feature`
  - `router: add x-envoy-overloaded header`

**PR Description Fields** (see `PULL_REQUEST_TEMPLATE.md`):
- **Commit Message**: What the PR does, behavior changes, bug fixes
- **Additional Description**: Extra context for reviewers
- **Risk Level**: Low, Medium, or High
- **Testing**: What testing was performed
- **Documentation**: Documentation changes
- **Release Notes**: User-facing impact
- **Issues**: Link with `Fixes #XXX` to auto-close issues

### Code Style

**File:** `STYLE.md`

Key requirements:
- **Formatting**: clang-format (checked automatically)
- **Line length**: Max 100 columns
- **Naming**: camelCase for functions (lowercase start), PascalCase for enums, `foo_` for member variables
- **Language**: Google C++ style guide with Envoy deviations
- **Tests**: Default to StrictMock for Google Mock
- **Comments**: Use GitHub username in TODOs, e.g., `TODO(username): description`
- **Inclusive Language**: No whitelist/blacklist/master/slave terminology

### Code Review and Merging

**Review Process:**
- PR assigned to maintainer automatically
- Expected turnaround: within one business day
- Typically requires one senior maintainer review + domain expert
- For new extensions: at least one approval from different organization than author
- Anyone can review, but maintainers must approve

**Before Merging:**
- All tests pass in CI
- All comments resolved
- **Don't rebase after review starts** — use merge instead (CI will squash on merge)
- PR title and description cleaned up by maintainer
- Original PR author's DCO signoff preserved

### DCO Sign-off (Developer Certificate of Origin)

All commits must be signed off with DCO. This is automatic if you run `./support/bootstrap`.

**Manual sign-off:**
```bash
git commit -s -m "message"
# Or set up aliases
git config --add alias.c "commit -s"
git config --add alias.amend "commit -s --amend"
```

**If DCO check fails**, squash commits and add signoff:
```bash
git rebase -i HEAD^^
# Then fix signoff and force push (only for DCO fixes)
git push origin -f
```

### Breaking Changes and Deprecation

- **API deprecation**: Must implement conversion and add tests with `DEPRECATED_FEATURE_TEST()` macro
- **Configuration deprecation**: Must document in `changelogs/current.yaml`
- **Breaking changes**: Clear deprecation path (warn, then fail) with runtime override option
- **Runtime guarding**: High-risk changes should be guarded with `Runtime::runtimeFeatureEnabled("envoy.reloadable_features.feature_name")`

For details, see `CONTRIBUTING.md` Breaking Change Policy section.

### Getting Help

- **Mailing Lists**:
  - `envoy-dev@groups.google.com` — Developer discussion
  - `envoy-announce@groups.google.com` — Announcements
  - `envoy-users@groups.google.com` — User discussion
  - `envoy-maintainers@groups.google.com` — Reach all maintainers

- **Slack**: https://envoyproxy.slack.com/ (get invite at https://communityinviter.com/apps/envoyproxy/envoy)
- **Issues**: Use GitHub Issues for bugs and feature discussions
- **CODEOWNERS**: See `CODEOWNERS` file to find domain experts

---

## 6. Developer Workflow Example

### Concrete Example: Fix HTTP Connection Manager Bug

This example walks through fixing a bug in the HTTP connection manager filter from cloning to PR merge.

#### Step 1: Setup

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/envoy.git
cd envoy

# Install development toolchain
./support/bootstrap

# Create feature branch
git checkout -b bugfix/http-connman-fix

# Make sure you're on the latest main
git checkout main
git pull origin main
git checkout bugfix/http-connman-fix
git merge main
```

#### Step 2: Locate the Code

The HTTP connection manager filter is in:
- **Source**: `source/extensions/filters/network/http_connection_manager/`
- **Headers**: `envoy/extensions/filters/network/http_connection_manager/http_connection_manager.h`
- **Tests**: `test/extensions/filters/network/http_connection_manager/`
- **Config proto**: `api/envoy/extensions/filters/network/http_connection_manager/v3/`

Start by exploring the test files to understand existing behavior:
```bash
# Run existing tests
bazel test //test/extensions/filters/network/http_connection_manager:*
```

#### Step 3: Write Tests First

Create or modify test in `test/extensions/filters/network/http_connection_manager/conn_manager_test.cc`:

```cpp
#include "test/extensions/filters/network/http_connection_manager/config_test_base.h"
#include "test/mocks/http/mocks.h"

// Add test for the bug
TEST(HttpConnectionManagerTest, FixedBugBehavior) {
  // Arrange: Set up test fixtures
  // Act: Trigger the bug scenario
  // Assert: Verify expected behavior after fix
}
```

Run the test to confirm it fails:
```bash
bazel test //test/extensions/filters/network/http_connection_manager:conn_manager_test --test_filter="HttpConnectionManagerTest.FixedBugBehavior"
```

#### Step 4: Implement the Fix

Edit the source code:
```bash
# Main source files
vi source/extensions/filters/network/http_connection_manager/conn_manager_impl.cc
vi source/extensions/filters/network/http_connection_manager/conn_manager_impl.h
```

Run tests to verify fix:
```bash
bazel test //test/extensions/filters/network/http_connection_manager:conn_manager_test --test_filter="HttpConnectionManagerTest.FixedBugBehavior"
```

#### Step 5: Verify Full Test Coverage

Ensure 100% coverage for modified code:
```bash
# Run all HTTP connection manager tests
bazel test //test/extensions/filters/network/http_connection_manager:*

# Run broader test suite
bazel test //test/extensions/filters/network/...
```

#### Step 6: Format Code

Auto-format and check for issues:
```bash
# Using support toolchain hooks (automatic on commit)
# Or manually:
bazel run //tools/code_format:check_format -- fix

# Check clang-tidy
bazel run //tools/code:check -- fix -s main -v warn
```

Or in Docker:
```bash
./ci/run_envoy_docker.sh './ci/do_ci.sh format'
```

#### Step 7: Documentation and Release Notes

If this is a user-facing fix:

1. **Update release notes** in `changelogs/current.yaml`:
```yaml
- area: http
  change: |
    Fixed HTTP connection manager bug where [description]. This can be reverted with runtime guard
    `envoy.reloadable_features.fixed_http_connman_bug` if needed.
```

2. **Update docs** if API changes:
   - Proto inline docs in `api/envoy/extensions/filters/network/http_connection_manager/v3/`
   - User docs in `docs/root/configuration/listeners/`

#### Step 8: Commit and Push

```bash
# Stage changes
git add source/extensions/filters/network/http_connection_manager/
git add test/extensions/filters/network/http_connection_manager/
git add changelogs/current.yaml
git add docs/

# Commit with DCO sign-off (automatic via bootstrap hook)
git commit -m "http conn man: fix bug with connection handling

Fixes a critical bug where [specific issue] was causing [impact].

The fix ensures that [how it's fixed].

Fixes #1234"

# Push to your fork
git push origin bugfix/http-connman-fix
```

#### Step 9: Create Pull Request

On GitHub:
1. Go to your fork, create PR against `main` branch
2. Fill in PR template:
   - **Title**: `http conn man: fix connection handling bug`
   - **Risk**: `Medium` (fixes existing code path)
   - **Testing**: "All unit and integration tests pass. Added test case `FixedBugBehavior` to verify fix."
   - **Documentation**: Updated `changelogs/current.yaml` with release notes
   - **Release Notes**: Added to changelogs/current.yaml

#### Step 10: CI Verification

GitHub automatically runs full CI suite:
- Wait for all checks to pass (typically 30-45 minutes)
- If failures occur, check error messages and iterate:
  ```bash
  git log --oneline -1
  # Make fix
  git commit -s --amend
  git push origin bugfix/http-connman-fix --force-with-lease
  ```

  **Important**: Don't force push after a maintainer starts reviewing

#### Step 11: Code Review

1. Maintainer assigned automatically
2. May request changes or clarifications
3. Update code if needed without rebasing (add new commits instead)
4. Maintainer cleans up title/message and merges

#### Step 12: Post-Merge

1. PR is squash-merged to `main`
2. Your branch can be deleted
3. Monitor for any issues in releases

---

## Additional Resources

### Key Documentation Files

- **DEVELOPER.md** — Developer setup and workflows
- **CONTRIBUTING.md** — Full contribution guidelines
- **STYLE.md** — Code style and best practices
- **REPO_LAYOUT.md** — Repository structure
- **bazel/README.md** — Bazel build system documentation
- **test/README.md** — Testing frameworks and utilities
- **test/integration/README.md** — Integration testing guide
- **support/README.md** — Development support toolchain
- **ci/README.md** — CI system details and Docker usage
- **PULL_REQUESTS.md** — PR template field explanations

### Extension Development

For developers adding new extensions:
- See `CONTRIBUTING.md` "Adding new extensions" section
- Use existing extensions as templates
- API files in `api/envoy/extensions/`
- Source in `source/extensions/`
- Configuration in BUILD files with `envoy_cc_extension` rule
- For contrib extensions, see `EXTENSION_POLICY.md`

### Performance and Advanced Topics

- **Remote build caching**: Configure in `.bazelrc` with `--remote_cache`
- **Distributed testing**: RBE configuration in `.bazelci/`
- **Profiling**: See `bazel/PPROF.md` for tcmalloc/pprof profiling
- **Code generation**: `bazel/EXTERNAL_DEPS.md` for managing dependencies

### Community

- **Bi-weekly community meeting**: Check [public calendar](https://goo.gl/PkDijT) and [meeting minutes](https://goo.gl/5Cergb)
- **Code owners**: Check `CODEOWNERS` file for maintainers by subsystem
- **OWNERS**: See `OWNERS.md` for list of committers

