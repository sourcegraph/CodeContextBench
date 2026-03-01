# Kafka Contributor Guide

A comprehensive guide for contributing to Apache Kafka, covering build prerequisites, the Gradle build system, testing procedures, CI pipeline, code review process, and a step-by-step developer workflow example.

---

## 1. Build Prerequisites

Apache Kafka is primarily written in Java and Scala. The following prerequisites are required to build from source:

### Required Software

- **Java Development Kit (JDK)**: Java 8, 11, 17, or 21
  - Kafka is built and tested against all these versions
  - Java 8 support is deprecated since Kafka 3.0 and will be removed in Kafka 4.0
  - Java 11 support for the broker and tools has been deprecated since Kafka 3.7 and will be removed in Kafka 4.0
  - **Recommended for new contributors**: Use Java 11, 17, or 21

- **Scala**: Version 2.12.x or 2.13.x
  - Scala 2.13.14 is used by default
  - Scala 2.12 support has been deprecated since Kafka 3.0 and will be removed in Kafka 4.0
  - See below for how to build with a specific Scala version

- **Gradle**: 6.8+ (included via gradlew wrapper)
  - The `./gradlew` wrapper script automatically handles Gradle distribution

- **Maven**: For building some subsystems like Kafka Streams Quickstart
  - Maven 3.x is recommended

### Optional Dependencies (for advanced use)

- **Docker**: Version 1.12.3+ (required for system/integration tests)
- **Vagrant**: 1.6.4+ (for local VM-based system testing)
- **Python 3.x**: For system tests (ducktape framework)

### Installation Quick Reference

```bash
# Ubuntu/Debian
sudo apt-get install default-jdk python3 python3-pip maven

# macOS (using Homebrew)
brew install openjdk maven python3

# Verify installations
java -version
javac -version
python3 --version
```

---

## 2. Gradle Build System

Kafka uses **Gradle** as its primary build tool, organized as a multi-module project. The build system is configured in `build.gradle` (root) and individual `build.gradle` files in each module.

### Key Project Structure

The settings.gradle file defines the main modules:

**Core modules:**
- `clients` - Kafka client libraries
- `core` - Kafka broker and core server code
- `streams` - Kafka Streams library
- `connect` - Kafka Connect framework (with submodules: api, runtime, file, json, mirror, transforms, etc.)
- `tools` - Administrative and development tools
- `examples` - Example code and quickstart projects

**Additional modules:**
- `group-coordinator` - Group coordination logic
- `raft` - Raft consensus implementation
- `storage` - Storage abstraction layer
- `server`, `server-common` - Server infrastructure
- `metadata` - Metadata management
- `transaction-coordinator` - Transaction coordination
- `jmh-benchmarks` - JMH performance benchmarks
- `log4j-appender` - Log4j integration
- `trogdor` - Workload generation and testing framework
- `generator` - Code generation utilities

### Core Gradle Commands

**Building the project:**

```bash
# Build JAR files for all modules
./gradlew jar

# Build source JAR files
./gradlew srcJar

# Build javadoc and scaladoc
./gradlew aggregatedJavadoc  # Combined javadoc for all modules
./gradlew javadoc             # Individual javadoc for each module
./gradlew scaladoc            # Individual scaladoc for each module
./gradlew javadocJar          # Javadoc JAR for each module
./gradlew scaladocJar         # Scaladoc JAR for each module
./gradlew docsJar             # Both javadoc and scaladoc JARs (if applicable)
```

**Building specific modules:**

```bash
# Build a specific module (e.g., clients, core, streams)
./gradlew core:jar
./gradlew clients:jar
./gradlew streams:jar

# Run tasks for specific modules
./gradlew core:build
./gradlew clients:test
./gradlew streams:testAll  # For Streams with multiple sub-projects
```

**Cleaning the build:**

```bash
# Clean build artifacts
./gradlew clean

# Clean and rebuild
./gradlew clean jar
```

### Using Different Scala Versions

```bash
# Build with Scala 2.12
./gradlew -PscalaVersion=2.12 jar
./gradlew -PscalaVersion=2.12 test

# Build with Scala 2.13 (default)
./gradlew -PscalaVersion=2.13 jar

# Build with all supported Scala versions (2.12 and 2.13)
./gradlewAll jar
./gradlewAll test
```

### Code Quality and Static Analysis

```bash
# Checkstyle (enforces consistent coding style)
./gradlew checkstyleMain checkstyleTest spotlessCheck

# Apply automatic code formatting (Spotless)
./gradlew spotlessApply
# Note: spotlessApply has issues with Java 21; use JDK 11 or 17

# SpotBugs (static bug analysis)
./gradlew spotbugsMain spotbugsTest -x test

# Run all checks (excluding tests)
./gradlew check -x test

# Combined code quality checks
./gradlew checkstyleMain checkstyleTest spotlessCheck spotbugsMain spotbugsTest -x test
```

**Important**: Format your code before committing:
- Run `./gradlew spotlessApply` to fix import order and formatting (requires JDK 11+)
- Run `./gradlew checkstyleMain checkstyleTest spotlessCheck` to verify compliance

### Common Build Options

Build options are specified with the `-P` flag:

```bash
# Common options
./gradlew -PmaxParallelForks=1 test          # Limit test parallelism
./gradlew -PskipSigning=true jar             # Skip artifact signing
./gradlew -PscalaVersion=2.12 test           # Use Scala 2.12
./gradlew -PkeepAliveMode=session build      # Gradle daemon keep-alive
./gradlew -PmaxTestRetries=1 test            # Retry failed tests once
./gradlew -enableTestCoverage=true test      # Enable code coverage

# Show all available Gradle tasks
./gradlew tasks
```

### Multi-Project Dependencies

Kafka is organized as a multi-project Gradle build:

```bash
# List all dependencies for a module
./gradlew allDeps

# Analyze specific dependencies
./gradlew allDepInsight --configuration runtimeClasspath --dependency com.fasterxml.jackson.core:jackson-databind

# Check for available dependency updates
./gradlew dependencyUpdates
```

---

## 3. Running Tests

Kafka has comprehensive test coverage with unit tests, integration tests, and system tests. Tests are distributed across modules and use different testing frameworks.

### Unit and Integration Tests

```bash
# Run all unit and integration tests
./gradlew test

# Run only unit tests
./gradlew unitTest

# Run only integration tests
./gradlew integrationTest

# Force re-run tests without code changes
./gradlew test --rerun
./gradlew unitTest --rerun
./gradlew integrationTest --rerun
```

### Testing Specific Modules

```bash
# Run tests for a specific module
./gradlew clients:test
./gradlew core:test
./gradlew streams:test
./gradlew streams:testAll  # For Streams sub-projects

# Run tests matching a pattern
./gradlew clients:test --tests RequestResponseTest
./gradlew clients:test --tests "*.kafka.clients.MetadataTest"
```

### Testing Specific Test Classes and Methods

```bash
# Run a specific test class
./gradlew clients:test --tests RequestResponseTest

# Run a specific test method
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest.testCannotSendToInternalTopic
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate

# Run with different test logging levels
./gradlew cleanTest clients:test --tests NetworkClientTest
# Edit clients/src/test/resources/log4j.properties to adjust logging level
```

### Test Retries and Reliability

```bash
# Configure test retries (default: 1 retry, max 5 retries per test run)
./gradlew test -PmaxTestRetries=1 -PmaxTestRetryFailures=5

# Show test events (started, passed, skipped, failed)
./gradlew test -PtestLoggingEvents=started,passed,skipped,failed
```

### Test Coverage Reports

Generate code coverage reports with JaCoCo:

```bash
# Generate coverage for entire project (disable parallelization)
./gradlew reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# Generate coverage for a single module
./gradlew clients:reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# View reports in: <module>/build/reports/jacoco/test/html/index.html
```

### System and Integration Tests

Kafka also has system integration tests using the **ducktape** framework. These are located in `tests/kafkatest/`:

```bash
# Build system test libraries
./gradlew systemTestLibs

# Run system tests with Docker (from tests directory)
bash tests/docker/run_tests.sh

# Run specific system test categories
TC_PATHS="tests/kafkatest/tests/streams" bash tests/docker/run_tests.sh
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py" bash tests/docker/run_tests.sh

# Run specific test class or method
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest" bash tests/docker/run_tests.sh
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest.test_start_stop" bash tests/docker/run_tests.sh

# Clean up Docker containers
bash tests/docker/ducker-ak down -f
```

### Repeatedly Running a Test

Useful for identifying flaky tests:

```bash
# Continuously run a test until it fails
I=0; while ./gradlew clients:test --tests RequestResponseTest --rerun --fail-fast; do (( I=$I+1 )); echo "Completed run: $I"; sleep 1; done
```

---

## 4. CI Pipeline

Kafka uses **Jenkins** as its primary CI system, with additional support for **GitHub Actions** for Docker builds. The main pipeline is defined in the repository root.

### Jenkins Pipeline (Primary CI)

**Location**: `Jenkinsfile` (root directory)

**Pipeline Overview**:

The main Jenkins pipeline runs in parallel across multiple configurations:

1. **JDK 8 with Scala 2.12**
   - Runs validation (checkstyle, spotbugs)
   - Runs full test suite
   - Tests Kafka Streams Quickstart archetype
   - Timeout: 8 hours

2. **JDK 11 with Scala 2.13**
   - Runs validation (checkstyle, spotbugs)
   - Runs tests on dev/PR branches
   - Skips archetype testing
   - Timeout: 8 hours

3. **JDK 17 with Scala 2.13**
   - Runs validation
   - Runs tests on dev/PR branches
   - Skips archetype testing
   - Timeout: 8 hours

4. **JDK 21 with Scala 2.13**
   - Runs validation
   - Runs full test suite
   - Skips archetype testing
   - Timeout: 8 hours

### CI Validation Tasks

The pipeline runs these core validation tasks:

```bash
# Validation (clean check without tests)
./gradlew -PscalaVersion=$SCALA_VERSION clean check -x test \
    --profile --continue -PxmlSpotBugsReport=true -PkeepAliveMode="session"

# Testing (with retries and parallel limits)
./gradlew -PscalaVersion=$SCALA_VERSION test \
    --profile --continue -PkeepAliveMode="session" \
    -PtestLoggingEvents=started,passed,skipped,failed \
    -PignoreFailures=true -PmaxParallelForks=2 \
    -PmaxTestRetries=1 -PmaxTestRetryFailures=10
```

### GitHub Actions Workflows

**Location**: `.github/workflows/`

GitHub Actions workflows are used for Docker-related operations:

- `docker_build_and_test.yml` - Build and test Docker images
- `docker_official_image_build_and_test.yml` - Official image builds
- `docker_promote.yml` - Docker image promotion
- `docker_rc_release.yml` - Release candidate builds
- `docker_scan.yml` - Security scanning
- Other auxiliary workflows for image preparation and staleness checks

### PR Checks

When you open a pull request on GitHub:

1. Jenkins automatically triggers CI builds for your PR
2. The pipeline runs parallel builds for all JDK/Scala combinations
3. Test results are reported back to the GitHub PR
4. All checks must pass before merging is approved

**Build Status**: Check GitHub PR page for Jenkins build status and logs

---

## 5. Code Review Process

Apache Kafka follows the Apache Software Foundation's standard contribution workflow. The process involves JIRA tickets, pull requests on GitHub, and approval from project committers.

### Finding and Claiming Issues

1. **Browse JIRA** at https://issues.apache.org/jira/browse/KAFKA
2. **Filter for open issues**: Look for issues with status "Open" or "In Progress"
3. **Claim a ticket**: Comment on the issue to indicate you're working on it (not a formal claim, but good etiquette)
4. **Check for existing PRs**: Verify no one else is already working on it by searching for linked PRs

### Creating a Pull Request

1. **Fork the repository** (if you haven't already)
   ```bash
   # Clone your fork
   git clone https://github.com/<your-username>/kafka.git
   cd kafka

   # Add Apache Kafka remote as upstream
   git remote add upstream https://github.com/apache/kafka.git
   ```

2. **Create a feature branch** (naming conventions):
   - Branch from `master` (development branch)
   - No strict naming convention, but descriptive names are appreciated
   - Example: `KAFKA-12345-fix-null-pointer` or `metrics-improvement`

   ```bash
   git fetch upstream
   git checkout -b KAFKA-12345-fix-null-pointer upstream/master
   ```

3. **Make your changes**:
   - Write clean, focused commits
   - Include meaningful commit messages
   - One logical change per commit

4. **Format your code** before committing:
   ```bash
   # Apply automatic code formatting (requires JDK 11+)
   ./gradlew spotlessApply

   # Verify code quality
   ./gradlew checkstyleMain checkstyleTest spotlessCheck
   ```

5. **Run tests locally**:
   ```bash
   # Run tests for modified modules
   ./gradlew clients:test      # if you modified clients
   ./gradlew core:test         # if you modified core
   ./gradlew streams:test      # if you modified streams

   # Run full test suite (optional, but recommended)
   ./gradlew test
   ```

6. **Push to your fork**:
   ```bash
   git push origin KAFKA-12345-fix-null-pointer
   ```

7. **Open a Pull Request** on GitHub:
   - Go to https://github.com/apache/kafka
   - Click "New Pull Request"
   - Select your branch and fill in the PR template
   - Include:
     - **Title**: Briefly describe the change (will become commit message)
     - **Description**: Explain the "why" and implementation approach
     - **Testing**: Describe testing strategy and test coverage
     - **JIRA**: Link to the relevant JIRA ticket (e.g., "Closes KAFKA-12345")

### Pull Request Template

The PULL_REQUEST_TEMPLATE.md provides the expected format:

```markdown
*More detailed description of your change,
if necessary. The PR title and PR message become
the squashed commit message, so use a separate
comment to ping reviewers.*

*Summary of testing strategy (including rationale)
for the feature or bug fix. Unit and/or integration
tests are expected for any behaviour change and
system tests should be considered for larger changes.*

### Committer Checklist (excluded from commit message)
- [ ] Verify design and implementation
- [ ] Verify test coverage and CI build status
- [ ] Verify documentation (including upgrade notes)
```

### Code Review Expectations

**What reviewers look for:**

1. **Design and Architecture**: Is the solution appropriate?
2. **Test Coverage**: Are tests included? Do they cover the change?
3. **Code Quality**: Does it follow Kafka style guidelines?
4. **Documentation**: Are javadocs, comments, and upgrade notes added if needed?
5. **Backwards Compatibility**: Does it break existing APIs or behavior?
6. **Performance**: Are there any performance implications?

**How to request reviews:**

- Comment on the PR to @mention reviewers
- Look at recent commits to identify active contributors in the area you changed
- Check `reviewers.py` for suggested reviewers by module
- Post on the Apache Kafka mailing list for visibility

### Approval and Merging

1. **PR Checks Must Pass**:
   - Jenkins CI pipeline passes for all JDK/Scala combinations
   - Automated code quality checks pass (checkstyle, spotbugs)
   - Tests pass (unit, integration)

2. **Code Review Approval**:
   - At least one committer must review and approve the PR
   - On GitHub, this is indicated by a "LGTM" (Looks Good To Me) comment or approved review
   - For larger changes, multiple reviewers may be required

3. **Squash and Merge**:
   - Committers use the `kafka-merge-pr.py` script to merge PRs
   - Commits are typically squashed into a single commit
   - The PR title becomes the commit message
   - Reviewer names are added to the commit

4. **Commit Message Format**:
   - Uses the PR title as the main message
   - Includes "Reviewers:" field with reviewer names/emails
   - May include merge conflict resolution notes
   - Follows standard commit message conventions

**Committer Checklist** (for committers merging the PR):
- [ ] Verify design and implementation
- [ ] Verify test coverage and CI build status
- [ ] Verify documentation (including upgrade notes)

### Responding to Feedback

1. **Address all comments**: Request clarification if needed
2. **Push new commits**: Don't force-push; let reviewers see the iteration
3. **Re-request review**: After addressing feedback, add a comment requesting re-review
4. **Be patient**: Code review takes time; expect back-and-forth discussion

---

## 6. Developer Workflow Example

This section provides a complete end-to-end example of contributing a bug fix to Kafka.

### Scenario: Fixing a Null Pointer Exception in the Broker

**JIRA Ticket**: KAFKA-16789 (hypothetical) - "NullPointerException when processing metadata updates in broker"

### Step 1: Find and Prepare

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/<your-username>/kafka.git
cd kafka

# Add upstream remote
git remote add upstream https://github.com/apache/kafka.git

# Fetch latest changes
git fetch upstream
git checkout master
git pull upstream master
```

### Step 2: Create a Feature Branch

```bash
# Create and switch to a feature branch
git checkout -b KAFKA-16789-fix-metadata-npe upstream/master

# Verify you're on the right branch and up-to-date
git branch -v
git log --oneline -5
```

### Step 3: Locate and Understand the Bug

```bash
# Use grep to find relevant code
grep -r "metadata" core/src/main --include="*.java" --include="*.scala"

# Look at the test files to understand expected behavior
find . -name "*MetadataTest*" -o -name "*metadata*test*.java"

# Read related documentation
./gradlew javadoc  # Generate javadocs if needed
```

### Step 4: Fix the Bug

Edit the relevant file (e.g., `core/src/main/scala/kafka/server/MetadataManager.scala`):

```scala
// Bad: can throw NullPointerException
def processMetadata(update: MetadataUpdate): Unit = {
    val metadata = update.getMetadata
    metadata.doSomething()  // NPE if metadata is null
}

// Good: handle null case
def processMetadata(update: MetadataUpdate): Unit = {
    val metadata = update.getMetadata
    if (metadata != null) {
        metadata.doSomething()
    }
}
```

### Step 5: Add or Update Tests

Create or modify a test file (e.g., `core/src/test/scala/unit/kafka/server/MetadataManagerTest.scala`):

```scala
@Test
def testProcessMetadataWithNullMetadata(): Unit = {
    val update = new MetadataUpdate()
    update.setMetadata(null)

    // Should not throw NullPointerException
    manager.processMetadata(update)
}

@Test
def testProcessMetadataWithValidMetadata(): Unit = {
    val update = new MetadataUpdate()
    update.setMetadata(new Metadata())

    manager.processMetadata(update)
    // Assert expected behavior
}
```

### Step 6: Run Tests Locally

```bash
# Run tests for the core module to verify your fix
./gradlew core:test --tests "*MetadataManagerTest*"

# Run specific test method
./gradlew core:test --tests kafka.server.MetadataManagerTest.testProcessMetadataWithNullMetadata

# Run broader test suite to check for regressions
./gradlew core:test

# Check code quality
./gradlew spotlessApply   # Auto-format code (JDK 11+ required)
./gradlew checkstyleMain checkstyleTest spotlessCheck
```

### Step 7: Commit Your Changes

```bash
# Stage your changes
git add core/src/main/scala/kafka/server/MetadataManager.scala
git add core/src/test/scala/unit/kafka/server/MetadataManagerTest.scala

# Create a clear commit message
git commit -m "KAFKA-16789: Fix NullPointerException in MetadataManager.processMetadata()

- Add null check before calling methods on metadata object
- Add unit tests to verify null metadata is handled gracefully
- Prevents crashes when metadata updates contain null values"

# View your commits
git log --oneline origin/master..HEAD
```

### Step 8: Push and Create a Pull Request

```bash
# Push your branch to your fork
git push origin KAFKA-16789-fix-metadata-npe

# Create PR on GitHub at: https://github.com/apache/kafka/compare/master...your-username:KAFKA-16789-fix-metadata-npe
```

**PR Title**: `KAFKA-16789: Fix NullPointerException in MetadataManager.processMetadata()`

**PR Description**:

```markdown
## Summary

Fixes a NullPointerException that occurs when MetadataManager.processMetadata()
receives a null metadata object. This can happen during certain metadata update
scenarios, causing broker crashes.

## Root Cause

The processMetadata() method assumes the metadata object is non-null and directly
calls methods on it without validation.

## Solution

Added null check before accessing the metadata object:
```scala
if (metadata != null) {
    metadata.doSomething()
}
```

## Testing Strategy

- Added 2 new unit tests:
  - `testProcessMetadataWithNullMetadata()` - verifies null metadata is handled
  - `testProcessMetadataWithValidMetadata()` - verifies normal operation still works
- All existing core module tests pass
- No breaking changes to public APIs

## Documentation

- Updated javadoc for processMetadata() to clarify null handling
- No upgrade notes needed (bug fix only)

## Checklist

- [x] Code follows Kafka style guidelines (ran spotlessApply)
- [x] Tests added/updated (unit tests included)
- [x] All tests passing locally
- [x] No new TODOs introduced
- [x] Ready for review
```

### Step 9: Wait for CI and Review

1. Jenkins automatically runs CI on your PR
2. Check build status on the GitHub PR page
3. Address any CI failures (test failures, style issues, etc.)

If tests fail:

```bash
# Identify the failing test
# Find the failing test output in Jenkins logs

# Fix the issue locally
# Re-run the test locally first
./gradlew core:test --tests FailingTestName

# Commit the fix
git commit -am "Fix failing test XYZ"

# Push to update the PR
git push origin KAFKA-16789-fix-metadata-npe
```

### Step 10: Address Review Feedback

When reviewers comment:

1. **Read feedback carefully** - understand the concern
2. **Respond on GitHub** - acknowledge the comment
3. **Make changes** if needed
4. **Commit new changes** to the same branch
5. **Push updates**
6. **Request re-review** with a comment like: "Updated based on feedback. Ready for another review."

```bash
# Make a change addressing feedback
# Edit the file as suggested

# Create a new commit (don't force-push)
git add core/src/main/scala/kafka/server/MetadataManager.scala
git commit -m "Address review feedback: Add additional null check in validateMetadata()"

# Push the new commit
git push origin KAFKA-16789-fix-metadata-npe

# Comment on GitHub: "Updated based on feedback. Ready for another look."
```

### Step 11: Merge (for Committers Only)

Once approved, a Kafka committer uses the merge script:

```bash
# Only committers can merge
./kafka-merge-pr.py

# Script prompts for:
# - PR number (from GitHub)
# - Scala version to use
# - Reviewers' names and emails
# - Handles merge, conflict resolution, and push to Apache Git

# Result:
# - Commit squashed into single commit
# - Commit message includes PR title and reviewer info
# - Changes pushed to apache/kafka repository
```

### Step 12: Cleanup

After your PR is merged:

```bash
# Update your local master
git fetch upstream
git checkout master
git pull upstream master

# Delete your local feature branch
git branch -d KAFKA-16789-fix-metadata-npe

# Delete your remote feature branch
git push origin -d KAFKA-16789-fix-metadata-npe
```

---

## Quick Reference: Common Tasks

### Build Commands Cheat Sheet

```bash
./gradlew jar                              # Build all JARs
./gradlew -PscalaVersion=2.12 jar          # Build with Scala 2.12
./gradlew core:jar                         # Build specific module
./gradlew spotlessApply                    # Auto-format code
./gradlew checkstyleMain spotlessCheck     # Check code style
./gradlew test                             # Run all tests
./gradlew core:test                        # Run module tests
./gradlew test --tests TestClassName       # Run specific test
./gradlew clean                            # Clean build
```

### Git Workflow Cheat Sheet

```bash
git fetch upstream                                      # Get latest
git checkout -b branch-name upstream/master             # Create branch
git add <files>                                         # Stage changes
git commit -m "Description"                             # Commit
git push origin branch-name                             # Push to fork
# Create PR on GitHub
git fetch upstream && git rebase upstream/master        # Keep branch updated
git push -f origin branch-name                          # Force push after rebase
```

### Testing Cheat Sheet

```bash
./gradlew test --rerun                     # Force test re-run
./gradlew test -PmaxParallelForks=1        # Run tests sequentially
./gradlew clients:test --tests "*.RequestResponseTest"   # Specific tests
./gradlew test -PtestLoggingEvents=started,passed,failed # Show test events
bash tests/docker/run_tests.sh              # Run system tests
```

---

## Resources

- **Apache Kafka Website**: https://kafka.apache.org
- **Contribution Guidelines**: https://kafka.apache.org/contributing.html
- **Contributing Code Changes**: https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes
- **JIRA Issue Tracker**: https://issues.apache.org/jira/browse/KAFKA
- **Apache Mailing Lists**: http://kafka.apache.org/contact.html
- **GitHub Repository**: https://github.com/apache/kafka
- **Build & Test README**: See README.md in Kafka repository root
- **System Tests README**: See tests/README.md
- **Vagrant Testing**: See vagrant/README.md

---

## Tips for Success

1. **Start small**: Begin with simple bug fixes or documentation improvements
2. **Communicate early**: Comment on JIRA issues to show interest and get feedback
3. **Follow the style**: Use `spotlessApply` to format code before committing
4. **Write tests**: All behavior changes need test coverage
5. **Read existing code**: Study similar code to understand Kafka conventions
6. **Ask questions**: The Kafka community is helpful; don't hesitate to ask on mailing lists or GitHub
7. **Be patient**: Code review takes time; reviewers are volunteers
8. **Keep commits focused**: One logical change per commit makes review easier
9. **Test thoroughly**: Run tests locally before pushing to GitHub
10. **Document your changes**: Add javadocs and comments for non-obvious code

---

**Last Updated**: March 2026
**Kafka Version**: 3.9.0
