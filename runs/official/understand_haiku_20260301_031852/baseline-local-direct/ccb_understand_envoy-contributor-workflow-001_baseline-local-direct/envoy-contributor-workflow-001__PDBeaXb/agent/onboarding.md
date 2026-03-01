# Envoy Contributor Guide

A comprehensive guide to contributing to the Envoy proxy project, covering build prerequisites, build system, testing, CI pipeline, and code review workflows.

## 1. Build Prerequisites

### System Requirements

Before you can build Envoy, install the following tools and dependencies:

#### Essential Tools
- **Bazel/Bazelisk**: Envoy uses Bazel as its build system. It's recommended to use [Bazelisk](https://github.com/bazelbuild/bazelisk) to avoid Bazel compatibility issues.
  - Linux: `sudo wget -O /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-$([ $(uname -m) = "aarch64" ] && echo "arm64" || echo "amd64") && sudo chmod +x /usr/local/bin/bazel`
  - macOS: `brew install bazelisk`
  - Windows: Download from GitHub releases and add to PATH

- **Clang 14 or GCC 9+**: Required compiler
  - Clang is preferred for CI (Clang 14 is the standard)
  - GCC 9 or later also works
  - C++17 support is required

#### Platform-Specific Dependencies

**Ubuntu (Focal 20.04 or later)**:
```bash
sudo apt-get install \
  autoconf \
  curl \
  libtool \
  patch \
  python3-pip \
  unzip \
  virtualenv
```

**Fedora**:
```bash
dnf install \
  aspell-en \
  libatomic \
  libstdc++ \
  libstdc++-static \
  libtool \
  lld \
  patch \
  python3-pip
```

**macOS**:
```bash
brew install coreutils wget libtool go bazelisk clang-format autoconf aspell
```
Note: Xcode (full version, not just Command Line Tools) is required.

**Windows 10/11**:
- Visual Studio 2019 Build Tools (with VC++ workload)
- MSYS2 bash shell
- Python 3 (windows-native version from python.org, not MSYS2)
- Windows SDK 1903+

#### Optional but Recommended
- **Docker**: For building with the same environment as CI
- **buildifier**: For BUILD file formatting (`go install github.com/bazelbuild/buildtools/buildifier@latest`)
- **addr2line**: For symbol resolution in stack traces

### Documentation References
- [Full Bazel setup documentation](https://github.com/envoyproxy/envoy/blob/main/bazel/README.md#quick-start-bazel-build-for-developers)
- [Envoy dependency policy](https://github.com/envoyproxy/envoy/blob/main/DEPENDENCY_POLICY.md)

---

## 2. Build System

Envoy uses **Bazel** as its build system. Bazel provides:
- Declarative build configuration via `BUILD` files
- Consistent builds across different machines
- Remote execution support
- Incremental builds with caching

### Key Build Commands

#### Building the Full Envoy Binary
```bash
# Development build (unoptimized, with debug symbols)
bazel build //source/exe:envoy-static

# Release/optimized build
bazel build -c opt //source/exe:envoy-static

# Debug build (fully instrumented)
bazel build -c dbg //source/exe:envoy-static

# Shorter alias (recommended)
bazel build envoy  # defaults to debug build
```

#### Building Specific Components
```bash
# Build a specific library
bazel build //source/common/http:http_lib

# Build a specific filter extension
bazel build //source/extensions/filters/http/router:router_lib

# Build a specific test
bazel build //test/common/http:async_client_impl_test
```

#### Build Configuration Options
- **-c opt**: Optimized release build
- **-c dbg**: Debug build with full symbols
- **--config=clang**: Use Clang compiler with libstdc++
- **--config=libc++**: Use Clang with libc++ (for compatibility testing)
- **--config=docker-clang**: Build in Docker sandbox (consistent environment)
- **--config=remote-clang**: Use GCP RBE remote execution

#### Running the Built Binary
```bash
# After building with: bazel build -c opt //source/exe:envoy-static
$(bazel info bazel-genfiles)/source/exe/envoy-static --config-path /path/to/config.yaml
```

### Build Architecture

The repository is organized as follows:
- **api/**: Protocol buffer definitions (data plane API)
- **source/common/**: Core Envoy implementation
- **source/extensions/**: Optional filter and extension implementations
- **envoy/**: Public interface headers (mostly abstract classes)
- **test/**: All test code (unit, integration, mocks)
- **bazel/**: Build configuration and Bazel rules

### Key Build Files
- **WORKSPACE**: Bazel workspace configuration and external dependency management
- **.bazelrc**: Bazel default build options
- **BUILD**: Build target definitions (one per directory with source files)
- **bazel/repositories.bzl**: External dependency versions
- **bazel/envoy_build_system.bzl**: Custom Envoy Bazel rules

### Custom Bazel Rules
Envoy defines custom build rules in `bazel/envoy_build_system.bzl`:
- **envoy_cc_library**: C++ libraries
- **envoy_cc_test**: C++ unit tests with Google Test
- **envoy_cc_binary**: C++ executables
- **envoy_cc_mock**: Mock implementations for testing
- **envoy_cc_extension**: Filter extensions with metadata

---

## 3. Running Tests

Envoy uses **Google Test** (gtest) and **Google Mock** for testing, organized into unit tests and integration tests.

### Running All Tests
```bash
# Run all tests
bazel test //test/...

# Run all tests with verbose output
bazel test --test_output=streamed //test/...
```

### Running Specific Tests
```bash
# Run a specific test file
bazel test //test/common/http:async_client_impl_test

# Run with streamed output (shows output in real-time)
bazel test --test_output=streamed //test/common/http:async_client_impl_test

# Run with additional test arguments
bazel test --test_output=streamed //test/common/http:async_client_impl_test --test_arg="-l trace"
```

### Test Environment Configuration

#### IP Version Testing
By default, tests exercise both IPv4 and IPv6:
```bash
# IPv4 only
bazel test //test/... --test_env=ENVOY_IP_TEST_VERSIONS=v4only

# IPv6 only
bazel test //test/... --test_env=ENVOY_IP_TEST_VERSIONS=v6only
```

#### Memory Leak Detection
Tests use gperftools heap checker by default:
```bash
# Disable heap checker
bazel test //test/... --test_env=HEAPCHECK=

# Use minimal mode (less strict)
bazel test //test/... --test_env=HEAPCHECK=minimal
```

#### Force Test Re-run
```bash
# Bypass test result cache
bazel test //test/common/http:async_client_impl_test --cache_test_results=no
```

### Test Organization

- **Unit tests**: Located in `test/` directories matching `source/` structure
  - Example: `test/common/http/` tests code in `source/common/http/`
- **Integration tests**: Located in `test/integration/`
  - End-to-end tests with real server code and fake clients/upstreams
- **Mocks**: Located in `test/mocks/`
  - Mock implementations of all core interfaces
- **Test utilities**: Located in `test/test_common/`
  - Shared testing utilities and helpers

### Test Frameworks and Tools

**Google Test**: Unit testing framework
- Macro-based tests: `TEST(TestClass, TestName) { ... }`
- Test fixtures: `TEST_F(FixtureName, TestName) { ... }`
- Assertions: `ASSERT_*` and `EXPECT_*` macros
- Reference: https://github.com/google/googletest

**Google Mock**: Mocking library
- `EXPECT_CALL(mock, method()).Times(...).WillOnce(...)`
- Matchers for flexible assertions
- Envoy defines custom matchers in `test/test_common/test_macros.h`

**Custom Matchers** (from test/README.md):
- `HeaderValueOf()`: Check HTTP headers
- `HttpStatusIs()`: Check HTTP status codes
- `ProtoEq()` / `ProtoEqIgnoringField()`: Protobuf comparison
- Reference: `test/README.md`

### Test Coverage

Envoy requires **100% test coverage** for new code:
```bash
# Generate coverage report (requires coverage build)
bazel test //test/... --config=coverage
```

If 100% coverage is not possible, you must explain why in the PR description.

### Debugging Tests

#### Running Under GDB
```bash
bazel build -c dbg //test/common/http:async_client_impl_test
bazel build -c dbg //test/common/http:async_client_impl_test.dwp
gdb bazel-bin/test/common/http/async_client_impl_test
```

#### Running in Sandbox
```bash
# Break out of sandbox (for running with local tools)
bazel test //test/common/http:async_client_impl_test --strategy=TestRunner=local --run_under=/path/to/tool.sh
```

#### Stack Traces
```bash
# With symbol resolution
bazel test -c dbg //test/server:backtrace_test \
  --run_under=//tools:stack_decode \
  --strategy=TestRunner=local \
  --cache_test_results=no \
  --test_output=all
```

---

## 4. CI Pipeline

Envoy uses **GitHub Actions workflows** for continuous integration, replacing the previous Azure Pipelines system.

### CI Platform and Configuration

**Platform**: GitHub Actions
- **Configuration location**: `.github/workflows/` and `.github/config.yml`
- **Build images**: `envoyproxy/envoy-build-ubuntu` Docker images
- **Current image SHA**: Specified in `.github/config.yml` under `build-image.sha`

### CI Workflow Structure

CI is organized around a request-response model:
- **request.yml**: Triggered by push/PR, triggers the main CI pipeline
- **_request.yml**: Reusable workflow that reads config and initiates checks
- **Check workflows**: Run on main branch but check out target branch/PR code

This design ensures:
- All CI logic lives on main (prevents bad actors in PRs from modifying CI)
- PRs can only change build image and version config
- Consistent execution across all branches

### Required Checks

The following checks must pass before merging (from `.github/config.yml`):

1. **Build Checks** (check-build, check-coverage, check-san)
   - `check-build`: Builds the project with standard configuration
   - `check-coverage`: Verifies code coverage meets requirements
   - `check-san`: Runs with sanitizers (AddressSanitizer, UndefinedBehaviorSanitizer)

2. **Prechecks** (precheck-deps, precheck-format, precheck-publish)
   - `precheck-format`: Code formatting (clang-format) and linting
   - `precheck-deps`: Dependency validation
   - `precheck-publish`: Documentation validation

3. **macOS Build** (build-macos)
   - Validates compilation on macOS

4. **Publish and Verify**
   - Verifies binary publishing and release artifacts

### CI Commands and Retesting

**Retesting a PR**:
```bash
# Comment on the PR:
/retest
```

**Kicking CI with an empty commit**:
```bash
# Create alias in .gitconfig:
[alias]
    kick-ci = !"git commit -s --allow-empty -m 'Kick CI' && git push"

# Then run:
git kick-ci
```

### Local CI Testing with Docker

Build and test locally using the same Docker image as CI:

```bash
# Development build
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'

# Run specific CI tasks
./ci/run_envoy_docker.sh './ci/do_ci.sh format'
./ci/run_envoy_docker.sh './ci/do_ci.sh clang_tidy'
./ci/run_envoy_docker.sh './ci/do_ci.sh coverage'
```

### CI Build Images

**Standard Linux Image** (`envoyproxy/envoy-build-ubuntu`):
- Based on Ubuntu 20.04 (Focal)
- GCC 9 and Clang 14 compilers
- All required build dependencies
- Current SHA in `.github/config.yml`

**Using CI Docker Image Locally**:
```bash
export IMAGE_NAME=envoyproxy/envoy-build-ubuntu
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'
```

### Coverage Builds

```bash
# Generate coverage report
bazel test //test/... --config=coverage

# View coverage HTML report
# Generated in bazel-out directory
```

### Typical CI Runtime

- Full CI run: 30-60 minutes (depending on parallelization)
- Building alone: 10-20 minutes
- Testing: 20-40 minutes
- Sanitizers (ASAN, UBSAN): Additional 10-15 minutes

---

## 5. Code Review Process

### Before You Start

**Communicate early for major features**:
- Major feature = >100 LOC or user-facing behavior changes
- Open a GitHub issue to discuss before implementing
- Prevents wasted effort and ensures design agreement

Reference: [CONTRIBUTING.md - Communication](https://github.com/envoyproxy/envoy/blob/main/CONTRIBUTING.md#communication)

### PR Requirements

**All PRs must satisfy**:
1. ✅ All tests pass (both new and existing)
2. ✅ 100% code coverage for new code
3. ✅ Proper code formatting (clang-format)
4. ✅ DCO sign-off on all commits
5. ✅ Meaningful commit message
6. ✅ Documentation updates (if user-facing)
7. ✅ Release notes (if user-impacting)

### Setting Up for Development

Install the development support toolchain:
```bash
./support/bootstrap
```

This sets up Git hooks for:
- Automatic DCO sign-off on commits
- Pre-push format and DCO verification
- Other development checks

Reference: [support/README.md](https://github.com/envoyproxy/envoy/blob/main/support/README.md)

### Code Style and Standards

**Coding Style**: See [STYLE.md](https://github.com/envoyproxy/envoy/blob/main/STYLE.md)

Key points:
- **Formatting**: Enforced by clang-format (auto-checked by CI)
- **Language**: Follow [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html) with Envoy-specific deviations
- **Line limit**: 100 columns
- **Naming**:
  - Functions: `camelCase()` starting with lowercase
  - Member variables: `_postfix` (e.g., `foo_`)
  - Enum values: `PascalCase`
  - Constants: `kConstantName` or `CONSTANT_NAME`
- **Formatting tools**:
  - clang-format: Automatic formatting
  - clang-tidy: Linting (enforced .clang-tidy config)
  - buildifier: BUILD file formatting

**Inclusive Language Policy**:
- ❌ Don't use: whitelist, blacklist, master, slave
- ✅ Use instead: allowlist, denylist/blocklist, primary/main, secondary/replica

### Inclusive Language Policy

The Envoy community requires inclusive language. Refer to [CONTRIBUTING.md - Inclusive Language Policy](https://github.com/envoyproxy/envoy/blob/main/CONTRIBUTING.md#inclusive-language-policy)

### PR Submission Checklist

1. **Create a fork** of the repository
2. **Install git hooks**:
   ```bash
   ./support/bootstrap
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b my-feature-branch
   ```
4. **Make changes and add tests** (100% coverage required)
5. **Format code**:
   ```bash
   bazel run //tools/code_format:check_format -- fix
   bazel run //tools/code:check -- fix -s main -v warn
   ```
6. **Run tests locally**:
   ```bash
   bazel test //test/... --cache_test_results=no
   ```
7. **Commit with message**:
   ```bash
   git commit -s  # -s adds DCO sign-off
   # Or configure aliases:
   git config --add alias.c "commit -s"
   ```
8. **Push and create PR**:
   ```bash
   git push origin my-feature-branch
   ```

### PR Title and Description Format

**Title Format**:
- Start with subsystem name in lowercase
- Format: `subsystem: brief description`
- Examples:
  - `docs: fix grammar error`
  - `http conn man: add new feature`
  - `router: fix header forwarding bug`

**Commit Message**:
- Used as the final PR merge commit message
- Should explain what and why (not just what)
- For bug fixes: describe the issue and solution
- For features: explain the feature and how to enable it

**PR Description Template** (auto-filled):
```
## Title
[PR title here]

## Commit Message
[Commit message - will be used as merge commit message]

## Additional Description
[Context useful to reviewers]

## Risk Level
[Low | Medium | High]

## Testing
[Describe testing performed]

## Documentation
[N/A | Description of docs changes]

## Release Notes
[N/A | Description for release notes in changelogs/current.yaml]

## Related Issues
[Fixes #XXX | Related to #XXX]
```

### Creating Release Notes

For user-impacting or extension-developer-impacting changes, add release notes:

```bash
# Edit changelogs/current.yaml
# Add entry under relevant section (bug_fixes, major_features, etc.)
```

### Dealing with Review Feedback

**During review**:
- Don't rebase your PR (makes review difficult)
- Instead, add new commits to address feedback
- Reviewer can still see what changed

```bash
# After addressing feedback:
git add .
git commit -s
git push  # Just push, don't force push
```

**Before merging**, maintainers will squash/clean up the commit message.

### DCO Sign-off

All commits must be signed off with the Developer Certificate of Origin:

```bash
# Automatic sign-off with git hooks (after ./support/bootstrap):
git commit -s

# Or set up aliases:
git config --add alias.c "commit -s"
git config --add alias.amend "commit -s --amend"

# Then: git c ... and git amend
```

If you forgot sign-off and need to fix it:
```bash
# Squash commits and force-push (only if pre-review):
git rebase -i HEAD~N  # squash commits
git commit --amend -s  # add sign-off
git push origin -f
```

Reference: [CONTRIBUTING.md - DCO](https://github.com/envoyproxy/envoy/blob/main/CONTRIBUTING.md#dco-sign-your-work)

### Review Policy

**Timeline**:
- Reviews typically turned around within one business day
- PRs become stale after 7 days with no activity and may be closed

**Reviewers**:
- Listed in [OWNERS.md](https://github.com/envoyproxy/envoy/blob/main/OWNERS.md)
- At least one senior maintainer for core code changes
- Domain expert review required
- For new features/extensions: at least one approval from different organization than author

**High-Risk Changes**:
May require runtime guarding - discuss with reviewers.
Reference: [CONTRIBUTING.md - Runtime Guarding](https://github.com/envoyproxy/envoy/blob/main/CONTRIBUTING.md#runtime-guarding)

---

## 6. Developer Workflow Example

### Scenario: Fix a Bug in HTTP Connection Manager Filter

Let's walk through a concrete example: fixing a bug in how the HTTP connection manager handles certain headers.

#### Step 1: Fork and Clone
```bash
# Fork on GitHub (web UI)

# Clone your fork
git clone https://github.com/YOUR-USERNAME/envoy.git
cd envoy

# Add upstream remote
git remote add upstream https://github.com/envoyproxy/envoy.git
```

#### Step 2: Set Up Development Environment
```bash
# Install development tools and git hooks
./support/bootstrap

# You can skip some hooks if you want
echo NO_VERIFY=1 >> .env
```

#### Step 3: Create a Feature Branch
```bash
# Make sure you're on main and up to date
git checkout main
git fetch upstream
git merge upstream/main

# Create feature branch
git checkout -b fix-http-header-handling
```

#### Step 4: Locate the Code to Change

The HTTP connection manager is in core code:
```bash
# Find the implementation
find source -name "*http*conn*man*" -type f | head -20

# Key files:
# - source/common/http/conn_manager_impl.h
# - source/common/http/conn_manager_impl.cc
# - test/common/http/conn_manager_impl_test.cc
```

#### Step 5: Make Changes and Write Tests

```bash
# Edit the implementation file(s)
vim source/common/http/conn_manager_impl.cc

# Add/update tests with 100% coverage
vim test/common/http/conn_manager_impl_test.cc

# Example test structure (using Google Test):
# TEST_F(HttpConnectionManagerImplTest, MyNewFixTest) {
#   // Setup
#   // Execute
#   // Assert
# }
```

#### Step 6: Run Tests Locally
```bash
# Run just the affected tests
bazel test //test/common/http:conn_manager_impl_test --cache_test_results=no

# Or run with verbose output
bazel test --test_output=streamed //test/common/http:conn_manager_impl_test

# Run all HTTP tests to ensure no regression
bazel test //test/common/http:* --cache_test_results=no

# Run full test suite (takes longer)
bazel test //test/... --cache_test_results=no
```

#### Step 7: Check Code Format
```bash
# Run formatting fixes
bazel run //tools/code_format:check_format -- fix
bazel run //tools/code:check -- fix -s main -v warn

# Or using Docker
./ci/run_envoy_docker.sh './ci/do_ci.sh format'
```

#### Step 8: Commit Your Changes
```bash
# Stage changes
git add source/common/http/conn_manager_impl.cc
git add test/common/http/conn_manager_impl_test.cc

# Commit with sign-off
git commit -s -m "http conn man: fix header handling bug

The HTTP connection manager was not properly validating headers
in the XXX scenario, causing requests with invalid headers to be
processed incorrectly.

This fix adds proper validation of headers before processing,
ensuring requests with invalid headers are rejected as per the
HTTP specification."

# Or without message (will open editor):
git commit -s
```

#### Step 9: Push to Your Fork
```bash
git push origin fix-http-header-handling
```

#### Step 10: Create Pull Request

On GitHub:
1. Click "Compare & pull request"
2. Fill in PR template:
   - Title: `http conn man: fix header handling bug`
   - Commit message: (already filled from commit)
   - Description: Additional context
   - Risk: `Low` (for simple bug fix)
   - Testing: Describe your testing
   - Documentation: `N/A`
   - Release notes: Add to `changelogs/current.yaml` if user-facing

#### Step 11: Wait for CI

- GitHub Actions automatically runs all checks
- Monitor the check status on the PR
- CI typically takes 30-60 minutes

#### Step 12: Address Review Feedback

```bash
# If reviewers request changes:

# Make additional changes to implementation
vim source/common/http/conn_manager_impl.cc

# Add/update tests
vim test/common/http/conn_manager_impl_test.cc

# Test again
bazel test //test/common/http:conn_manager_impl_test --cache_test_results=no

# Format
bazel run //tools/code_format:check_format -- fix

# Commit (don't rebase!)
git commit -s -m "Address review feedback: better error message"

# Push (don't force push)
git push origin fix-http-header-handling

# CI will run again automatically
```

#### Step 13: Merge

Once all reviews are approved and CI is green:
- A maintainer will merge your PR
- They will squash your commits and clean up the message
- Your commit will appear on main with a clean history

```bash
# After merge, update your local repo:
git checkout main
git fetch upstream
git merge upstream/main
git branch -d fix-http-header-handling  # Delete local branch
git push origin --delete fix-http-header-handling  # Delete remote branch
```

### Key Takeaways

1. **Communicate early** for major features (open an issue first)
2. **Write tests** with 100% coverage before/with your fix
3. **Format locally** before pushing
4. **Run CI tests** locally to catch issues early
5. **Don't rebase** once in review - just push new commits
6. **Follow the conventions** for commit messages and PR descriptions
7. **Be responsive** to review feedback (PRs go stale after 7 days)
8. **Sign off** all commits with DCO (`git commit -s`)

### Additional Resources

- **CONTRIBUTING.md**: Full contribution guidelines
- **PULL_REQUESTS.md**: Detailed PR submission guide
- **STYLE.md**: Code style and standards
- **REPO_LAYOUT.md**: Repository structure
- **OWNERS.md**: Maintainers for each area
- **test/README.md**: Testing framework documentation
- **test/integration/README.md**: Integration test framework

---

## Quick Reference

### Most Common Commands

```bash
# Setup
git clone https://github.com/YOUR-USERNAME/envoy.git
cd envoy
./support/bootstrap

# Development cycle
git checkout -b my-feature
# ... make changes ...
bazel test //test/... --cache_test_results=no
bazel run //tools/code_format:check_format -- fix
git commit -s
git push origin my-feature

# Testing
bazel test //test/common/http:async_client_impl_test
bazel test --test_output=streamed //test/common/http:async_client_impl_test

# Building
bazel build envoy  # debug build
bazel build -c opt envoy  # release build

# CI Testing (Docker)
./ci/run_envoy_docker.sh './ci/do_ci.sh dev'

# Format checking
bazel run //tools/code_format:check_format -- fix
```

### Useful Links

- **GitHub Repository**: https://github.com/envoyproxy/envoy
- **Official Documentation**: https://www.envoyproxy.io/
- **Slack Community**: https://envoyproxy.slack.com/
- **Mailing Lists**: https://groups.google.com/forum/#!forum/envoy-dev

---

## Troubleshooting

### Build Issues

**"Bazel command not found"**
- Install Bazelisk: See [Build Prerequisites](#build-prerequisites)

**"C++ compiler not found"**
- Install Clang 14 or GCC 9+
- On Linux: Use prebuilt LLVM packages or package manager

**"Tests failing with permission denied"**
- May need to run tests with elevated privileges
- Use: `tools/bazel-test-docker.sh <test-target>` for privileged tests

### Test Issues

**"Test results from cache"**
- Use `--cache_test_results=no` to force re-run

**"Heap leak detected"**
- This is often false positives in debug mode
- Use `--test_env=HEAPCHECK=` to disable

**"IPv6 tests failing"**
- Set `--test_env=ENVOY_IP_TEST_VERSIONS=v4only` if IPv6 unavailable

### Formatting Issues

**"Format check failed in CI"**
- Run: `bazel run //tools/code_format:check_format -- fix`
- Or in Docker: `./ci/run_envoy_docker.sh './ci/do_ci.sh format'`

**"DCO sign-off missing"**
- The pre-push hook should catch this
- Or fix with: `git commit --amend -s`

### CI Issues

**"PR stuck in CI"**
- Comment `/retest` to rerun failed checks
- Or create empty commit: `git commit --allow-empty -m "Kick CI" && git push`

**"Need different build image"**
- Edit `.github/config.yml` in your PR (only allowed change in CI config)
- Update `build-image.sha` to desired image hash

---

**Last updated**: March 2026
**Document version**: Envoy v1.32.1

