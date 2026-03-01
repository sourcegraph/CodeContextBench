# Kafka Contributor Guide

A comprehensive guide for contributing to the Apache Kafka project. This document covers the tools, processes, and workflows needed to build, test, and submit code changes.

---

## 1. Build Prerequisites

### Supported Java Versions
- **Supported**: Java 8, 11, 17, and 21
- **Default/Recommended**: Java 11 or 17 (Java 8 and 11 support for broker/tools are deprecated and will be removed in Kafka 4.0)
- **Note**: Spotless code formatter has issues with Java 21, so use JDK 11 or 17 for `spotlessCheck` and `spotlessApply`

Install Java:
```bash
# Check current Java version
java -version

# On Ubuntu/Debian
sudo apt-get install openjdk-17-jdk

# On macOS with Homebrew
brew install openjdk@17
```

### Scala Version
- **Supported**: Scala 2.12 and 2.13
- **Default**: Scala 2.13.14 (as of version 3.9.0)
- **Note**: Scala 2.12 support is deprecated and will be removed in Kafka 4.0

You don't need to install Scala manually; Gradle manages it through dependencies.

### Gradle Wrapper
The project includes a **Gradle wrapper** (`gradlew`), so you don't need to install Gradle separately:
- `./gradlew` - Automatically downloads and uses the correct Gradle version
- `./gradlewAll` - Runs tasks with all supported Scala versions

### Docker (Optional, for system tests)
- Docker 1.12.3 or higher is required to run system integration tests locally
- System tests use the [ducktape](https://github.com/confluentinc/ducktape) framework

### No Other Dependencies Required
The build system will automatically download all other dependencies (Maven Central).

---

## 2. Gradle Build System

### Project Structure
The Kafka codebase is organized as a **Gradle multi-project build** with the following key modules:

**Core Modules:**
- `clients` - Kafka client libraries (producer, consumer)
- `core` - Kafka broker implementation
- `server` - Server-specific components
- `server-common` - Shared server utilities
- `streams` - Kafka Streams
- `connect` - Kafka Connect (with sub-modules for API, runtime, connectors)
- `metadata` - KRaft metadata functionality
- `raft` - KRaft consensus protocol

**Supporting Modules:**
- `storage` - Tiered storage implementation
- `group-coordinator` - Group coordination protocol
- `examples` - Example applications
- `jmh-benchmarks` - JMH microbenchmarks
- `generator` - Code generation utilities
- `shell` - Interactive shell tools

See `settings.gradle` for the complete list of modules.

### Essential Gradle Commands

#### Build JAR
```bash
# Build all JARs
./gradlew jar

# Build JAR for a specific module
./gradlew core:jar
./gradlew clients:jar
./gradlew streams:jar
```

#### Code Quality Checks
```bash
# Run checkstyle (enforces consistent coding style)
./gradlew checkstyleMain checkstyleTest

# Run spotbugs (static analysis for potential bugs)
./gradlew spotbugsMain spotbugsTest -x test

# Check and fix import ordering (spotless)
./gradlew spotlessCheck
./gradlew spotlessApply  # Automatically fixes imports
```

#### Build Documentation
```bash
# Build all Javadoc and Scaladoc
./gradlew javadoc scaladoc

# Build aggregated Javadoc
./gradlew aggregatedJavadoc

# Build JAR files with documentation
./gradlew javadocJar scaladocJar docsJar
```

#### Build Source JAR
```bash
./gradlew srcJar
```

#### Clean Build
```bash
./gradlew clean
```

#### List All Available Tasks
```bash
./gradlew tasks
```

### Building with Different Scala Versions
```bash
# Build with Scala 2.12
./gradlew -PscalaVersion=2.12 jar
./gradlew -PscalaVersion=2.12 test

# Build with all supported Scala versions (2.12 and 2.13)
./gradlewAll jar
./gradlewAll test
```

### Common Build Options (with -P flag)

```bash
# Set maximum parallel test forks (default: number of processors)
./gradlew test -PmaxParallelForks=2

# Ignore test failures
./gradlew test -PignoreFailures=true

# Set maximum Scalac compiler threads
./gradlew -PmaxScalacThreads=4 jar

# Show test standard output
./gradlew test -PshowStandardStreams=true

# Control heap size
./gradlew -Dorg.gradle.jvmargs="-Xmx4g" jar
```

### Useful Gradle Diagnostics
```bash
# Show dependency tree for a module
./gradlew clients:dependencies
./gradlew clients:dependencyInsight --configuration runtimeClasspath --dependency com.fasterxml.jackson.core:jackson-databind

# Recursively show all dependencies
./gradlew allDeps
./gradlew allDepInsight --configuration runtimeClasspath --dependency <groupId:artifactId>

# Check for dependency updates
./gradlew dependencyUpdates
```

### Build Caching
The project uses Gradle Enterprise build caching (disabled in CI, enabled locally for faster builds):
```bash
# Build cache is automatically used for local builds
# No special configuration needed
./gradlew build  # Uses build cache
```

---

## 3. Running Tests

### Test Types
- **Unit Tests**: Fast, in-process tests (Gradle task: `unitTest`)
- **Integration Tests**: Longer-running tests that may start services (Gradle task: `integrationTest`)
- **System Tests**: Full-stack tests using ducktape framework in `tests/` directory

### Running All Tests

```bash
# Run all unit and integration tests
./gradlew test

# Run only unit tests
./gradlew unitTest

# Run only integration tests
./gradlew integrationTest

# Run tests for a specific module
./gradlew core:test
./gradlew clients:test
./gradlew streams:testAll  # For Streams multi-project
```

### Running Specific Tests

```bash
# Run a specific test class
./gradlew clients:test --tests RequestResponseTest
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest

# Run a specific test method
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest.testCannotSendToInternalTopic

# Run tests matching a pattern
./gradlew test --tests "*MetadataTest*"
```

### Running Tests with Options

```bash
# Force re-running tests (ignore cache)
./gradlew test --rerun
./gradlew clients:test --tests RequestResponseTest --rerun

# Run with fail-fast (stop on first failure)
./gradlew test --fail-fast

# Run repeatedly until failure
I=0; while ./gradlew clients:test --tests RequestResponseTest --rerun --fail-fast; do
  (( I=$I+1 )); echo "Completed run: $I"; sleep 1;
done

# Run with specific logging level (modify log4j.properties in module)
./gradlew cleanTest clients:test --tests NetworkClientTest

# Show test output (default is minimal)
./gradlew test -PshowStandardStreams=true
./gradlew test -PtestLoggingEvents=started,passed,skipped,failed
```

### Test Retries
By default, each failed test is retried once (max 5 retries per run):
```bash
# Customize test retries
./gradlew test -PmaxTestRetries=2 -PmaxTestRetryFailures=5
```

### Code Coverage Reports

```bash
# Generate coverage for the entire project
./gradlew reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# Generate coverage for a single module
./gradlew clients:reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false
```

### System Integration Tests (ducktape)

System tests are located in the `tests/` directory and use [ducktape](https://github.com/confluentinc/ducktape).

**Prerequisites**: Docker 1.12.3+ and `./gradlew clean systemTestLibs`

```bash
# Build system test libraries first
./gradlew clean systemTestLibs

# Run all system tests using Docker
bash tests/docker/run_tests.sh

# Run a subset of tests
TC_PATHS="tests/kafkatest/tests/streams tests/kafkatest/tests/tools" bash tests/docker/run_tests.sh

# Run a specific test file
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py" bash tests/docker/run_tests.sh

# Run a specific test class
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest" bash tests/docker/run_tests.sh

# Run a specific test method
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest.test_start_stop" bash tests/docker/run_tests.sh

# Run with debug output
_DUCKTAPE_OPTIONS="--debug" bash tests/docker/run_tests.sh | tee debug_logs.txt

# Run with a different JVM
bash tests/docker/ducker-ak up -j 'openjdk:11'
bash tests/docker/run_tests.sh

# Run with native mode
_DUCKTAPE_OPTIONS="--globals '{\"kafka_mode\":\"native\"}'" bash tests/docker/run_tests.sh

# Remove Docker containers
bash tests/docker/ducker-ak down -f
```

### JMH Microbenchmarks

```bash
# See jmh-benchmarks/README.md for detailed instructions
./gradlew jmh-benchmarks:jmh
```

---

## 4. CI Pipeline

### CI Systems Used

**Primary CI:**
- **Jenkins** - Main CI system that runs on pull requests and commits
- Configuration: `Jenkinsfile` (in repository root)
- PR Triggering: Whitelisted users can trigger builds (see `.asf.yaml`)

**Secondary CI:**
- **GitHub Actions** - Used for Docker-related tasks and releases
- Configuration: `.github/workflows/*.yml`
  - `docker_build_and_test.yml` - Build and test Docker images
  - `docker_official_image_build_and_test.yml` - Official image tests
  - `docker_promote.yml` - Docker image promotion
  - `docker_rc_release.yml` - Release candidate Docker builds
  - `docker_scan.yml` - Security scanning

### Jenkins Build Pipeline (`Jenkinsfile`)

The Jenkinsfile defines the CI pipeline stages:

1. **Validation** (`doValidation()`)
   - Runs `check` task (excluding tests)
   - Code quality checks: checkstyle, spotbugs, import validation
   - Uses `spotlessCheck`, SpotBugs reports

2. **Testing** (`doTest()`)
   - Runs full test suite: unit and integration tests
   - Configuration:
     - `maxParallelForks=2` - Runs 2 test processes in parallel
     - `maxTestRetries=1` - Retries failed tests once
     - `maxTestRetryFailures=10` - Max 10 retry failures per run
   - Collects JUnit XML results: `**/build/test-results/**/TEST-*.xml`

3. **Streams Archetype**
   - Verifies Kafka Streams quickstart archetype compiles

4. **Multiple Scala Versions**
   - Runs builds with both Scala 2.12 and 2.13

### PR Triggering

PR builds are triggered on:
- New PRs from whitelisted users (see `.asf.yaml`)
- Commits to PRs
- Comments on PRs

**Whitelisted users** (can trigger CI):
Located in `.asf.yaml`:
- FrankYang0529, kamalcph, apoorvmittal10, lianetm, brandboat
- kirktrue, nizhikov, OmniaGM, dongnuo123, frankvicky

For non-whitelisted users, a whitelisted user must trigger the build.

### CI Configuration Files

**Key Files:**
- `/Jenkinsfile` - Main Jenkins pipeline configuration
- `/.asf.yaml` - GitHub integration and Jenkins whitelisting
- `/.github/workflows/` - GitHub Actions workflows
- `/gradle.properties` - Version and Gradle configuration

### Required Checks Before Merging

Before a PR can be merged, these checks must pass:

1. ✅ Jenkins build succeeds
2. ✅ All tests pass
3. ✅ Code quality checks pass (checkstyle, spotbugs, spotless)
4. ✅ Code review approval from committer
5. ✅ CI build status shows green

### Local CI Emulation

To catch CI failures locally before pushing:

```bash
# Run the same validation checks as CI
./gradlew clean check -x test --profile --continue

# Run full test suite
./gradlew test --profile --continue

# Check code style
./gradlew checkstyleMain checkstyleTest spotlessCheck

# Run spotbugs analysis
./gradlew spotbugsMain spotbugsTest -x test

# Full CI-like build (takes longer)
./gradlew clean check --profile --continue
```

---

## 5. Code Review Process

### Where to Find Issues

1. **JIRA Issue Tracker**: https://issues.apache.org/jira/browse/KAFKA
   - Browse open tickets
   - Filter by component, assignee, or fix version
   - Good first issues: Look for issues marked as "good first issue" or low complexity

2. **GitHub Issues**: https://github.com/apache/kafka/issues
   - Discussion and tracking
   - PRs can reference issues with `Fixes KAFKA-XXXXX` or `Related to KAFKA-XXXXX`

### Finding an Issue to Work On

1. Visit https://issues.apache.org/jira/browse/KAFKA
2. Filter by status: Open, In Progress (unclaimed)
3. Look for issues marked:
   - "good first issue" - Suitable for new contributors
   - "help-wanted" - Actively seeking contributions
   - Lower priority/complexity for easier problems

4. Comment on the issue: "I'd like to work on this"
5. A committer may assign it to you

**Note**: You don't need to be assigned, but commenting prevents duplicate work.

### Branch Naming Conventions

While not strictly enforced, follow this convention:

```bash
# For JIRA issues
git checkout -b KAFKA-XXXXX

# For feature branches (if not tied to JIRA)
git checkout -b feature/short-description
git checkout -b bugfix/short-description

# Example
git checkout -b KAFKA-15123
git checkout -b feature/improve-consumer-lag
```

### Development Workflow

#### Step 1: Clone and Setup
```bash
git clone https://github.com/apache/kafka.git
cd kafka
git checkout main
git pull origin main  # Ensure latest
```

#### Step 2: Create and Checkout Branch
```bash
git checkout -b KAFKA-XXXXX
# Or your branch name
```

#### Step 3: Make Changes
- Edit source files
- Add/update tests
- Follow code style (see section below)

#### Step 4: Test Locally
```bash
# Run affected module tests
./gradlew core:test --tests YourTestClass

# Run code quality checks
./gradlew checkstyleMain checkstyleTest spotlessCheck
./gradlew spotlessApply  # Auto-fix imports

# Run full check suite
./gradlew check -x test
```

#### Step 5: Commit Changes
```bash
git add <files>
git commit -m "KAFKA-XXXXX: Brief description of change

Longer explanation of what the change does and why.
Can span multiple lines."
```

**Commit Message Format:**
- Line 1: `KAFKA-XXXXX: Short description` (50 chars max)
- Blank line
- Detailed explanation (wrapped at 72 chars)
- Reference issues: `Fixes KAFKA-XXXXX` or `Related to KAFKA-XXXXX`

#### Step 6: Push and Create PR
```bash
git push origin KAFKA-XXXXX
```

GitHub will show a prompt to create a PR. Use the template provided.

#### Step 7: PR Description

Use the **PR template** from `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
*Brief description of your change*

*More detailed description if necessary. The PR title and message
become the squashed commit message, so use a separate comment
to ping reviewers.*

*Summary of testing strategy (including rationale) for the feature
or bug fix. Unit and/or integration tests are expected for any
behaviour change and system tests should be considered for larger
changes.*
```

**PR Title Format:**
- Same as commit message: `KAFKA-XXXXX: Brief description`
- Must match because PR is squash-merged (title becomes commit message)

### Code Style and Formatting

#### Checkstyle (Code Style Enforcement)
```bash
# Check for style violations
./gradlew checkstyleMain checkstyleTest

# Reports are in: build/reports/checkstyle/

# Key rules enforced:
# - Line length: 120 characters max
# - Indentation: 4 spaces (no tabs)
# - Naming conventions: camelCase for variables/methods
# - No wildcard imports
# - Consistent spacing and braces
```

See `/checkstyle/checkstyle.xml` for complete rules.

#### Spotless (Import Ordering)
```bash
# Check import order
./gradlew spotlessCheck

# Auto-fix imports (requires JDK 11+)
./gradlew spotlessApply

# Common issues:
# - Imports should be sorted alphabetically
# - Static imports separate from regular imports
```

#### Spotbugs (Bug Detection)
```bash
# Run static analysis
./gradlew spotbugsMain spotbugsTest -x test

# Reports are in: build/reports/spotbugs/
# Fix reported issues before submitting PR
```

#### Scala Formatting (`.scalafmt.conf`)
The project uses Scalafmt for Scala code formatting. While not enforced in CI, keep it consistent with Java style.

### Code Review Expectations

**What Reviewers Look For:**

1. ✅ **Correctness**: Code solves the stated problem correctly
2. ✅ **Tests**: Adequate test coverage (unit and/or integration)
3. ✅ **Style**: Follows code style guidelines (checkstyle passes)
4. ✅ **Documentation**: Javadoc for public APIs, comments for complex logic
5. ✅ **Performance**: No performance regressions; consider impact on latency-sensitive code
6. ✅ **Backwards Compatibility**: No breaking changes unless intentional (document in PR)

**Responding to Reviews:**

1. Address all comments
2. Make requested changes and commit with message: `Address review feedback`
3. Mark conversations as resolved in GitHub
4. Request re-review from reviewer

### Approval and Merge

**Who Can Merge:**
- Apache Kafka committers
- Requires at least one approval from a committer

**Merge Process:**
1. PR passes all CI checks
2. At least one committer approval
3. No ongoing discussions/requested changes
4. Committer clicks "Squash and merge"
   - Squash merges all commits into single commit
   - PR title becomes commit message
   - Therefore, PR title must be properly formatted

**After Merge:**
- Branch is automatically deleted
- Your name appears in commit history
- Issue is typically closed automatically if referenced with `Fixes KAFKA-XXXXX`

---

## 6. Developer Workflow Example

### Scenario: Fix a Consumer Lag Calculation Bug

This example walks through a complete contributor workflow from issue discovery to merge.

#### Phase 1: Preparation (30 min)

**Step 1.1: Find the Issue**
```
1. Go to https://issues.apache.org/jira/browse/KAFKA
2. Search for "consumer lag" or find KAFKA-12345 (example)
3. Read the issue description and any linked PRs
4. Comment: "I'd like to work on this"
```

**Step 1.2: Set Up Your Environment**
```bash
# Clone the repository
git clone https://github.com/apache/kafka.git
cd kafka

# Verify Java version (use 11 or 17)
java -version

# Test that Gradle works
./gradlew --version

# Run a quick sanity test
./gradlew clients:compileJava

# Should complete without errors
```

**Step 1.3: Create a Branch**
```bash
# Update main to latest
git checkout main
git pull origin main

# Create feature branch (follow convention)
git checkout -b KAFKA-12345

# (Or if you're not assigned to a JIRA: feature/fix-consumer-lag)
git checkout -b bugfix/consumer-lag-calculation
```

#### Phase 2: Implementation (1-2 hours)

**Step 2.1: Understand the Code**
```bash
# Find the relevant code
grep -r "consumerLag" clients/src/main/java/

# For clients module, check these key files:
# - clients/src/main/java/org/apache/kafka/clients/consumer/internals/
# - clients/src/main/java/org/apache/kafka/clients/consumer/

# Read the code and understand the bug
```

**Step 2.2: Write a Failing Test First**
```bash
# Create a test file
# File: clients/src/test/java/org/apache/kafka/clients/consumer/internals/ConsumerLagTest.java

package org.apache.kafka.clients.consumer.internals;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class ConsumerLagTest {
    @Test
    public void testConsumerLagCalculation() {
        // This test demonstrates the bug
        long lag = ConsumerLag.calculate(100, 50);  // offset 100, latest 150
        assertEquals(50, lag, "Consumer lag should be 50");
    }
}

# Run the test to verify it fails
./gradlew clients:test --tests ConsumerLagTest.testConsumerLagCalculation
# Should FAIL (this is expected - demonstrates the bug)
```

**Step 2.3: Implement the Fix**
```
1. Open the relevant source file
2. Locate the buggy code
3. Fix the calculation logic
4. Add comments explaining the fix if non-obvious

Example fix:
// BEFORE (buggy)
long lag = latestOffset - currentOffset;  // Wrong if offset > latest

// AFTER (fixed)
long lag = Math.max(0, latestOffset - currentOffset);  // Handle edge case
```

**Step 2.4: Verify the Test Now Passes**
```bash
# Run the specific test
./gradlew clients:test --tests ConsumerLagTest.testConsumerLagCalculation
# Should PASS

# Run all related tests
./gradlew clients:test --tests "*ConsumerLag*"
```

#### Phase 3: Quality Assurance (30 min)

**Step 3.1: Run Code Quality Checks**
```bash
# Check style
./gradlew checkstyleMain checkstyleTest
# Should pass with no warnings

# Auto-fix import ordering
./gradlew spotlessApply

# Run spotbugs (bug detection)
./gradlew spotbugsMain spotbugsTest -x test
# Should show no new issues related to your change

# Run full validation (like CI)
./gradlew check -x test --continue
# All checks should pass
```

**Step 3.2: Run Full Test Suite**
```bash
# Run all tests in the affected module
./gradlew clients:test
# May take 5-10 minutes

# If you made widespread changes, also test:
./gradlew core:test
./gradlew streams:test
```

**Step 3.3: Manual Testing (if applicable)**
```bash
# Build the JAR
./gradlew jar

# Test manually (if possible)
# For consumer changes, you could test with:
# - bin/kafka-console-consumer.sh with your fixed code
# - Custom Java test script
```

#### Phase 4: Commit and Push (10 min)

**Step 4.1: Review Your Changes**
```bash
# See what you changed
git diff

# See files that will be committed
git status

# Stage your changes (files only, not build artifacts)
git add clients/src/main/java/...
git add clients/src/test/java/...

# Do NOT stage build/ or .gradle/ directories
```

**Step 4.2: Commit**
```bash
git commit -m "KAFKA-12345: Fix consumer lag calculation for edge cases

The consumer lag calculation had a bug where it didn't handle
the case where the consumer offset was ahead of the latest offset.
This caused incorrect lag values.

The fix:
- Added null check for edge case
- Return 0 instead of negative value when offset >= latest
- Added test case to prevent regression

Testing:
- Added ConsumerLagTest with 3 new test methods
- All existing consumer tests pass
- Manually tested with custom consumer script"
```

**Step 4.3: Push to GitHub**
```bash
# Push the branch
git push origin KAFKA-12345
# (or your branch name)

# You should see output like:
# remote: Create a pull request for 'KAFKA-12345' by visiting:
# remote: https://github.com/apache/kafka/pull/12345
```

#### Phase 5: Create Pull Request (10 min)

**Step 5.1: Open the PR**
- GitHub shows a link to create PR
- Or go to https://github.com/apache/kafka/pulls and click "New Pull Request"

**Step 5.2: Fill in PR Details**

```markdown
**Title:** (Auto-filled from commit, verify it's correct)
KAFKA-12345: Fix consumer lag calculation for edge cases

**Description:**

## Summary
Fixes a bug in consumer lag calculation where offset >= latest
returns incorrect negative values.

## Testing
- Added ConsumerLagTest with comprehensive edge case coverage
- Ran `./gradlew clients:test` - all 450+ tests pass
- Ran code quality checks: checkstyle, spotbugs - all pass
- Manually tested with custom consumer script

## Changes
- `ConsumerLag.java` - Fixed edge case handling in calculation
- `ConsumerLagTest.java` - Added 3 new test methods for edge cases

## Documentation
- Updated Javadoc comment to clarify lag >= 0 always
- No API changes, internal fix only
```

**Step 5.3: Watch for CI**
- GitHub will run Jenkins CI automatically
- You'll see status checks: "✅ continuous-integration/jenkins/pr-merge"
- Wait 10-30 minutes for CI to complete

#### Phase 6: Address Review Feedback (1-2 hours)

**Step 6.1: Wait for Reviews**
- Usually reviewers comment within 24 hours
- Committers may request changes

**Step 6.2: Common Feedback Examples**

Example feedback:
```
@yourname - Can you also add a test for when offset is negative?
That could be another edge case.
```

Response:
```bash
# Add the additional test case
# Edit ConsumerLagTest.java

# Verify it passes
./gradlew clients:test --tests ConsumerLagTest

# Commit (new commit, not amend)
git commit -m "Address review feedback: add test for negative offset"

# Push
git push origin KAFKA-12345

# In GitHub, reply: "Added test for negative offset case in
# latest commit."
```

**Step 6.3: Re-request Review**
- Click "Re-request review" button next to reviewer's name
- They'll be notified

#### Phase 7: Merge (Automatic)

**Step 7.1: Approval**
Once committer approves and CI passes:
- Status shows "✅ All checks have passed"
- Reviewer clicks "Approve" (if they haven't already)

**Step 7.2: Committer Merges**
- A committer clicks "Squash and merge"
- PR is automatically closed
- Branch is deleted
- Your commit appears in main branch

**Step 7.3: Cleanup (Local)**
```bash
# Switch back to main
git checkout main

# Update local main
git pull origin main
# You should see your commit in the log

# Delete your local branch (optional)
git branch -d KAFKA-12345

# Or delete from remote if it's still there (shouldn't be)
git push origin --delete KAFKA-12345
```

**Step 7.4: Verify**
```bash
# See your commit in the log
git log --oneline | head -5
# Should show: "KAFKA-12345: Fix consumer lag calculation for edge cases"

# See your name in contributors
git log --grep="KAFKA-12345"

# The JIRA ticket should be closed/marked as Done
# Go to https://issues.apache.org/jira/browse/KAFKA-12345
```

#### Summary of Time Investment
- **Research**: 30 min
- **Implementation**: 1-2 hours
- **Testing & QA**: 30 min
- **Commit & PR**: 10 min
- **Waiting for CI**: 10-30 min
- **Code review feedback**: 1-2 hours (spread over 1-2 days)
- **Waiting for merge**: A few hours to a day
- **Total**: 4-7 hours of actual work, 1-3 days calendar time

### Key Points for This Example

✅ **Do:**
- Test locally before pushing
- Write tests for your fix
- Address all review feedback
- Keep commits focused on one issue
- Push early to get CI feedback

❌ **Don't:**
- Push without testing
- Ignore checkstyle warnings
- Ask "Is this OK?" without showing work
- Commit large amounts of unrelated code
- Skip documentation for public APIs

---

## Additional Resources

### Official Kafka Documentation
- **Main Site**: https://kafka.apache.org
- **Contributing Guide**: https://kafka.apache.org/contributing.html
- **Code Changes Guide**: https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes
- **Design Documents**: https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals

### Community Communication
- **Mailing Lists**: https://kafka.apache.org/contact.html
  - user@kafka.apache.org - User questions
  - dev@kafka.apache.org - Development discussions
- **JIRA**: https://issues.apache.org/jira/browse/KAFKA
- **GitHub**: https://github.com/apache/kafka

### Related Documentation
- `README.md` - Build commands reference
- `tests/README.md` - System testing with ducktape
- `docker/README.md` - Docker build information
- `jmh-benchmarks/README.md` - Microbenchmark running
- `vagrant/README.md` - Vagrant testing setup

### Kafka Architecture
- **KIP (Kafka Improvement Proposals)**: https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals
- **Design Documents**: Track implementation of major features

---

## Troubleshooting

### "Permission denied" when running gradlew
```bash
chmod +x ./gradlew
```

### Tests fail with "Cannot read schema"
```bash
# Rebuild message schemas
./gradlew processMessages processTestMessages
```

### OutOfMemory errors during build
```bash
# Increase heap size
export _JAVA_OPTIONS="-Xmx4g"
./gradlew test
```

### Spotless fails with Java 21
```bash
# Use Java 11 or 17 for spotlessCheck
jenv shell 17  # if using jenv
./gradlew spotlessCheck
```

### Jenkins build passes locally but fails in CI
- Check that you're using same Java version as CI (usually 11 or 17)
- Run full test suite: `./gradlew test`
- Run code checks: `./gradlew check -x test`

### "Gradle sync failed" in IDE
```bash
# Refresh IDE's Gradle cache
./gradlew cleanBuild
# Then refresh IDE (IntelliJ: File > Sync with Gradle)
```

---

**Last Updated**: March 2026 | Kafka 3.9.0
