# Apache Kafka Contributor Guide

This guide provides step-by-step instructions for contributing to Apache Kafka, from building the project to submitting your changes for review.

## 1. Build Prerequisites

### System Requirements
- **Git**: For cloning and managing the repository
- **Java**: Multiple versions supported
  - Java 8, 11, 17, and 21 are all tested and supported
  - Java 8 support deprecated since Kafka 3.0; planned removal in 4.0
  - Java 11 broker/tools support deprecated since Kafka 3.7
  - Default: Use Java 11 or 17 for best experience

### Scala Support
- **Scala 2.12** and **2.13** are supported
  - Scala 2.13 is the default
  - Scala 2.12 support deprecated since Kafka 3.0; planned removal in 4.0
- Both versions can be used by passing `-PscalaVersion=2.12` or `-PscalaVersion=2.13`

### Required Tools
- **Gradle**: The build system (managed via `./gradlew` wrapper)
- **Maven**: Required for Kafka Streams quickstart archetype testing

### Optional Tools for Code Quality
- Code quality checks use **Checkstyle** and **SpotBugs** (automatically run during builds)
- **Spotless** (requires JDK 11+) for import ordering and formatting

---

## 2. Gradle Build System

Kafka uses Gradle as its build system. The project is organized as a multi-project build with the following major modules:

### Main Modules
- `clients` - Kafka producer/consumer client libraries
- `core` - Kafka broker and server components
- `streams` - Kafka Streams framework (and sub-projects)
- `connect` - Kafka Connect framework
- `tools` - Command-line tools
- `server`, `server-common`, `group-coordinator`, `transaction-coordinator` - Coordinator and server components
- `storage`, `metadata`, `raft` - Storage and replication components
- `shell` - Shell/REPL support
- `examples` - Example applications
- `jmh-benchmarks` - Performance microbenchmarks
- `trogdor` - Workload generator for system tests

### Key Gradle Commands

#### Building
```bash
# Build JAR artifacts
./gradlew jar

# Build source JAR
./gradlew srcJar

# Build Javadoc (all modules)
./gradlew aggregatedJavadoc

# Build documentation
./gradlew javadoc                    # Javadoc
./gradlew scaladoc                   # Scaladoc
./gradlew javadocJar                 # Javadoc JARs for each module
./gradlew scaladocJar                # Scaladoc JARs for each module
./gradlew docsJar                    # Both javadoc and scaladoc JARs
```

#### Module-Specific Builds
```bash
# Build specific module (e.g., clients)
./gradlew clients:jar
./gradlew clients:test

# Streams sub-projects
./gradlew :streams:testAll           # Run all Streams tests

# Core module
./gradlew core:jar
./gradlew core:test
```

#### Scala Version Variants
```bash
# Build with specific Scala version (2.12 or 2.13)
./gradlew -PscalaVersion=2.12 jar
./gradlew -PscalaVersion=2.12 test

# Build with all supported Scala versions
./gradlewAll test
./gradlewAll jar
./gradlewAll releaseTarGz
```

#### Message Code Generation
```bash
# Regenerate RPC message classes (needed when switching branches)
./gradlew processMessages processTestMessages
```

#### Release/Packaging
```bash
# Build binary release tarball
./gradlew clean releaseTarGz
# Output: core/build/distributions/

# Publish to local Maven repository
./gradlewAll publishToMavenLocal

# Publish to Maven central/snapshot repository
./gradlewAll publish
```

#### IDE Support
```bash
# Generate IDE project files (optional - IntelliJ has good Gradle support)
./gradlew eclipse
./gradlew idea
```

#### Dependency Analysis
```bash
# List all dependencies for the project
./gradlew allDeps

# Check specific dependency insights
./gradlew allDepInsight --configuration runtimeClasspath --dependency com.fasterxml.jackson.core:jackson-databind

# Check for dependency updates
./gradlew dependencyUpdates
```

### Important Build Options

Pass these using `-P` flag (e.g., `./gradlew -PmaxParallelForks=2 test`):

- `commitId`: Custom git commit ID (overrides .git/HEAD)
- `mavenUrl`: Maven repository URL for publishing
- `maxParallelForks`: Max parallel test processes (default: number of available processors)
- `maxScalacThreads`: Scala compiler threads (default: min(8, processors), range: 1-16)
- `ignoreFailures`: Continue on test failures
- `showStandardStreams`: Show test stdout/stderr on console
- `skipSigning`: Skip artifact signing
- `testLoggingEvents`: Test events to log (e.g., `started,passed,skipped,failed`)
- `xmlSpotBugsReport`: Generate XML SpotBugs reports instead of HTML
- `maxTestRetries`: Max test retries on failure (default: 1)
- `maxTestRetryFailures`: Max test failures before disabling retries (default: 5)
- `enableTestCoverage`: Enable test coverage (adds ~15-20% overhead)
- `keepAliveMode`: Gradle daemon keep-alive mode (`daemon` or `session`)
- `scalaOptimizerMode`: Scala optimizer level (`none`, `method`, `inline-kafka`, `inline-scala`)

---

## 3. Running Tests

Kafka uses **JUnit 5 (Jupiter)** as the testing framework with **Mockito** for mocking.

### Unit and Integration Tests

#### Run All Tests
```bash
./gradlew test                       # Both unit and integration tests
./gradlew unitTest                   # Unit tests only
./gradlew integrationTest            # Integration tests only
```

#### Run Tests for a Specific Module
```bash
./gradlew clients:test
./gradlew core:test
./gradlew streams:test               # Or use :streams:testAll for all Streams tests
```

#### Run a Specific Test Class
```bash
./gradlew clients:test --tests RequestResponseTest
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest
```

#### Run a Specific Test Method
```bash
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest.testCannotSendToInternalTopic
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate
```

#### Repeatedly Run a Test
```bash
I=0; while ./gradlew clients:test --tests RequestResponseTest --rerun --fail-fast; do (( I=$I+1 )); echo "Completed run: $I"; sleep 1; done
```

#### Re-run Tests Without Code Changes
```bash
./gradlew test --rerun
./gradlew unitTest --rerun
./gradlew integrationTest --rerun
```

#### Configure Test Logging
By default, minimal logs are shown. Modify test configuration:

1. Edit `src/test/resources/log4j.properties` in the module
2. Change log level (e.g., `log4j.logger.org.apache.kafka=INFO`)
3. Run tests with output redirection:

```bash
./gradlew cleanTest clients:test --tests NetworkClientTest
```

Logs appear in `<module>/build/test-results/test/` directory.

#### Test Retry Configuration
```bash
# Customize retry behavior
./gradlew test -PmaxTestRetries=2 -PmaxTestRetryFailures=10
```

See [Test Retry Gradle Plugin docs](https://github.com/gradle/test-retry-gradle-plugin) for details.

### Test Coverage

```bash
# Generate coverage report for entire project
./gradlew reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# Generate coverage for specific module
./gradlew clients:reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false
```

### System Integration Tests

System tests use **ducktape** (distributed testing framework) and can be run with Docker:

#### Prerequisites
```bash
# Build Kafka and system test libraries
./gradlew clean systemTestLibs
```

#### Run All System Tests
```bash
bash tests/docker/run_tests.sh
```

#### Run Subset of Tests
```bash
TC_PATHS="tests/kafkatest/tests/streams" bash tests/docker/run_tests.sh
```

#### Run Specific Test File
```bash
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py" bash tests/docker/run_tests.sh
```

#### Run Specific Test Class
```bash
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest" bash tests/docker/run_tests.sh
```

#### Run Specific Test Method
```bash
TC_PATHS="tests/kafkatest/tests/streams/streams_upgrade_test.py::StreamsUpgradeTest.test_metadata_upgrade" bash tests/docker/run_tests.sh
```

#### Debug System Tests
```bash
# Run with debug logging
_DUCKTAPE_OPTIONS="--debug" bash tests/docker/run_tests.sh | tee debug_logs.txt

# Run in VS Code debugger (attach mode)
tests/docker/ducker-ak up
tests/docker/ducker-ak test tests/kafkatest/tests/core/security_test.py --debug
```

#### Manage Docker Containers
```bash
# Start containers
bash tests/docker/ducker-ak up

# Start with native Kafka binary
bash tests/docker/ducker-ak up -m native

# Stop containers
bash tests/docker/ducker-ak down -f
```

See [tests/README.md](https://github.com/apache/kafka/blob/trunk/tests/README.md) for full details.

---

## 4. Code Quality Checks

### Checkstyle
Ensures consistent coding style:

```bash
./gradlew checkstyleMain checkstyleTest spotlessCheck
```

Reports appear in `reports/checkstyle/reports/main.html` and `test.html` in each module's build directory.

⚠️ **Note**: `spotlessCheck` has issues with Java 21; run with JDK 11 or 17.

### Spotless (Import Ordering)
Optimize import statements in Java code:

```bash
./gradlew spotlessApply
```

⚠️ **Note**: `spotlessApply` also has issues with Java 21; run with JDK 11 or 17.

### SpotBugs
Static analysis to find potential bugs:

```bash
./gradlew spotbugsMain spotbugsTest -x test
```

Reports in `reports/spotbugs/main.html` and `test.html`. Use `-PxmlSpotBugsReport=true` for XML output.

### Run All Checks
Before submitting PR:
```bash
./gradlew check -x test          # All checks except tests
./gradlew spotlessApply          # Fix import ordering (JDK 11/17 only)
./gradlew test                   # Run all tests
```

---

## 5. CI Pipeline

### Jenkins (Primary)
Apache Kafka uses **Jenkins** for the main CI pipeline.

**Location**: Jenkins file at repository root: `Jenkinsfile`

**Pipeline Overview**:
The build matrix tests across multiple Java and Scala versions in parallel:

1. **JDK 8 + Scala 2.12**
   - Validation (checks except tests)
   - All unit and integration tests
   - Kafka Streams archetype validation
   - Timeout: 8 hours

2. **JDK 11 + Scala 2.13**
   - Validation (checks except tests)
   - Tests only on dev branches
   - Timeout: 8 hours

3. **JDK 17 + Scala 2.13**
   - Validation (checks except tests)
   - Tests only on dev branches
   - Timeout: 8 hours

4. **JDK 21 + Scala 2.13**
   - Validation (checks except tests)
   - All unit and integration tests
   - Timeout: 8 hours

**Key Jenkins Tasks**:
- `check -x test`: Code quality checks (SpotBugs, Checkstyle)
- `test`: All unit and integration tests
- Archetype test: Validates Kafka Streams quickstart artifact
- Email notifications to `dev@kafka.apache.org` on failures

**Build Scan**: Kafka uses [Gradle Enterprise](https://ge.apache.org) for build analytics.

### GitHub Actions (Docker/Release)
GitHub Actions handles Docker image builds and releases:
- Docker image build and test (`.github/workflows/docker_build_and_test.yml`)
- Official Docker image builds (`.github/workflows/docker_official_image_build_and_test.yml`)
- Release promotion (`.github/workflows/docker_promote.yml`)
- RC release builds (`.github/workflows/docker_rc_release.yml`)

### Pull Request Checks
All pull requests undergo:
1. **Validation Stage**: Code quality checks (SpotBugs, Checkstyle, import ordering)
2. **Test Stage**:
   - Unit and integration tests across Java versions
   - Test output parsed and reported as JUnit XML
3. **Archetype Test** (JDK 8 only): Validates Kafka Streams Maven archetype
4. **Build Artifacts**: Profiles and build scans available in Jenkins

---

## 6. Code Review Process

### Finding and Claiming Issues

1. **Browse JIRA**: Issues tracked at https://issues.apache.org/jira/browse/KAFKA
   - Filter by status: `Open` (not yet assigned)
   - Filter by component area (clients, broker, streams, etc.)
   - Look for `good-first-issue` label for beginner contributions

2. **Claim the Issue**:
   - Log in with Apache account (create if needed)
   - Click "Assign to me" on the JIRA ticket
   - Leave a comment indicating you'll work on it

3. **Review Related KIPs**: Some changes require a Kafka Improvement Proposal (KIP)
   - Check JIRA for linked KIPs at https://cwiki.apache.org/confluence/display/KAFKA
   - Read KIP discussion for design rationale

### Branch Naming
While not strictly enforced, consider using:
- `KAFKA-XXXXX` (issue number) as branch name for clarity
- Example: `git checkout -b KAFKA-16428`

### Creating a Pull Request

1. **Prepare Your Work**:
   ```bash
   # Make sure your branch is up-to-date
   git fetch upstream
   git rebase upstream/main

   # Run local checks before pushing
   ./gradlew check spotlessApply
   ./gradlew test
   ```

2. **Commit Your Changes**:
   - Write clear, concise commit messages
   - Reference the JIRA issue: `KAFKA-XXXXX; Brief description`
   - One logical change per commit
   - Include `Co-Authored-By` trailers for team work

3. **Push and Create PR**:
   ```bash
   git push origin KAFKA-XXXXX
   ```

4. **Fill the PR Template** (auto-populated from `PULL_REQUEST_TEMPLATE.md`):
   - **Title**: Should be suitable as commit message
   - **Description**:
     - Link to JIRA issue
     - Explain what changed and why
     - Summary of testing strategy (unit, integration, or system tests added)
   - **Testing Checklist**:
     - [ ] Unit tests added/modified
     - [ ] Integration tests added/modified
     - [ ] System tests considered (for larger changes)
     - [ ] Documentation updated
   - **Committer Checklist** (for review):
     - Verify design and implementation
     - Verify test coverage and CI
     - Verify documentation

### Code Review Expectations

#### What Reviewers Look For
- **Correctness**: Code logic is correct and handles edge cases
- **Testing**: Adequate unit, integration, or system tests included
- **Performance**: No regressions; benchmarks considered for performance-critical code
- **API Design**: Backwards compatible or justified breaking changes
- **Documentation**: Code comments and user-facing docs are clear
- **Style**: Follows Kafka conventions (Checkstyle passes)
- **JMH Benchmarks**: Added for performance-sensitive changes

#### Getting Review
- Kafka committers are volunteers; be patient
- Tag reviewers if known (@username in PR)
- Ask in [dev mailing list](http://kafka.apache.org/contact.html) for visibility
- Small, focused PRs get reviewed faster

#### Addressing Feedback
- Push new commits to the same branch (don't force-push)
- Respond to all comments
- Re-request review after making changes
- Iterations are normal; don't be discouraged

#### Merge
- Committer will squash commits and apply PR title as commit message
- PR must pass all CI checks before merge
- Must have at least one approval from a committer
- Merged to `main` branch

---

## 7. Developer Workflow Example

### Scenario: Fix a Bug in the Producer Client

#### Step 1: Find and Claim the Issue
```bash
# Browse https://issues.apache.org/jira/browse/KAFKA
# Find issue KAFKA-16428: "Producer fails with null pointer in edge case"
# Click "Assign to me"
```

#### Step 2: Set Up Your Local Environment
```bash
# Clone if you haven't already
git clone https://github.com/apache/kafka.git
cd kafka

# Add upstream if forking
git remote add upstream https://github.com/apache/kafka.git

# Create and checkout feature branch
git fetch upstream
git checkout -b KAFKA-16428 upstream/main
```

#### Step 3: Understand the Issue
- Read the JIRA description carefully
- Check if there's a linked KIP
- Review related code and tests
- Reproduce the bug locally if possible

#### Step 4: Implement the Fix
```bash
# Edit relevant files (e.g., clients/src/main/java/org/apache/kafka/clients/producer/...)
# Add/modify code and write unit tests

# Example: Writing a test
# File: clients/src/test/java/org/apache/kafka/clients/producer/ProducerTest.java
```

#### Step 5: Run Local Tests
```bash
# Test the specific module
./gradlew clients:test --tests ProducerTest

# Run code quality checks
./gradlew checkstyleMain checkstyleTest spotlessCheck spotlessApply

# Run broader test suite
./gradlew clients:test

# If it's a critical path, run longer tests
./gradlew test -PmaxParallelForks=1
```

#### Step 6: Verify Your Changes Compile
```bash
# Clean build to catch any issues
./gradlew clean clients:jar

# Check for dependency issues
./gradlew allDeps
```

#### Step 7: Commit Your Work
```bash
# Stage your changes
git add clients/src/main/java/org/apache/kafka/clients/producer/Producer.java
git add clients/src/test/java/org/apache/kafka/clients/producer/ProducerTest.java

# Write a clear commit message
git commit -m "KAFKA-16428; Fix null pointer exception in Producer

- Added null check in processCallback method
- Added unit test to verify edge case handling
- Verified no performance regression"
```

#### Step 8: Push to Your Fork
```bash
# If forking
git push origin KAFKA-16428

# Or push to a personal fork
git push https://github.com/<your-username>/kafka.git KAFKA-16428
```

#### Step 9: Create Pull Request
1. Go to https://github.com/apache/kafka
2. Click "New Pull Request"
3. Choose your branch and fill the template:

```
## Description

This PR fixes KAFKA-16428: Producer fails with null pointer in edge case.

### Changes
- Added null check in `Producer.processCallback()` to handle case where
  callback is null due to concurrent modification
- Validates fix doesn't break existing functionality

### Testing
- Added `ProducerTest.testProcessCallbackWithNull()` unit test
- Ran full `clients:test` suite: 234 tests pass
- No regressions in performance benchmarks

### Committer Checklist
- [ ] Verify design and implementation
- [ ] Verify test coverage and CI build status
- [ ] Verify documentation (if needed)
```

#### Step 10: Address Code Review
```bash
# Reviewer suggests: "Add javadoc to the new null-handling code"

# Make the change
# Edit Producer.java and add javadoc

git add clients/src/main/java/org/apache/kafka/clients/producer/Producer.java
git commit -m "KAFKA-16428; Add javadoc for null check in processCallback"
git push origin KAFKA-16428

# GitHub will auto-update the PR
# Re-request review in PR conversation
```

#### Step 11: Wait for Merge
- CI pipeline runs automatically
- Committer reviews and approves
- Once approved, committer merges to main
- Your commit is squashed and merged

#### Step 12: Clean Up
```bash
# Switch back to main
git checkout main

# Pull latest changes
git pull upstream main

# Delete your branch locally and on remote
git branch -d KAFKA-16428
git push origin --delete KAFKA-16428
```

---

## Additional Resources

### Official Documentation
- **Contributing Guide**: https://kafka.apache.org/contributing.html
- **Contributing Code Changes**: https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes
- **Developer Mailing List**: dev@kafka.apache.org (subscribe at http://kafka.apache.org/contact.html)
- **Jira**: https://issues.apache.org/jira/browse/KAFKA

### Build and Testing Resources
- **README.md**: See the project README for all build commands
- **tests/README.md**: Detailed system testing guide
- **JMH Benchmarks**: jmh-benchmarks/README.md

### Kafka Improvement Proposals (KIPs)
- Browse at: https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals
- Large features typically require a KIP first

### Common Issues
- **SpotBugs/Spotless Issues on Java 21**: Use JDK 11 or 17 for code quality checks
- **Long Builds**: Use `-PmaxParallelForks=2` to reduce memory usage
- **Test Flakes**: Use `-PmaxTestRetries=2 -PmaxTestRetryFailures=10` to auto-retry

---

## Quick Reference Cheat Sheet

```bash
# Initial setup
git clone https://github.com/apache/kafka.git
cd kafka
git checkout -b KAFKA-XXXXX

# Build and test
./gradlew clients:jar                          # Build module
./gradlew clients:test                         # Test module
./gradlew checkstyleMain spotlessApply         # Code style fixes
./gradlew test                                 # Full test suite

# Before submitting PR
./gradlew check -x test                        # All checks except tests
./gradlew test -PmaxParallelForks=2            # Run tests

# Commit and push
git add <files>
git commit -m "KAFKA-XXXXX; Description"
git push origin KAFKA-XXXXX

# Clean up after merge
git checkout main
git pull upstream main
git branch -d KAFKA-XXXXX
```

Good luck contributing to Apache Kafka!
