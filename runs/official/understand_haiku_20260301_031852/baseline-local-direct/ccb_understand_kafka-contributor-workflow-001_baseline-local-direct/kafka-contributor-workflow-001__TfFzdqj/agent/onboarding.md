# Kafka Contributor Guide

This guide provides practical instructions for contributing to Apache Kafka. It covers the tools, build system, testing procedures, and the code review process used by Kafka maintainers.

## 1. Build Prerequisites

To build Kafka from source, you need the following tools and versions:

### Required Tools

- **Java Development Kit (JDK)**: Version 8, 11, 17, or 21
  - Kafka is built and tested with all these versions
  - The `release` parameter is set to `8` to ensure compatibility with Java 8+ (independent of compile version)
  - **Note**: Java 8 support is deprecated as of Kafka 3.0 and planned for removal in 4.0
  - **Note**: Java 11 broker support deprecated since Kafka 3.7, planned removal in 4.0

- **Scala**: Version 2.12 or 2.13 (2.13 is the default)
  - Scala 2.12 support is deprecated as of Kafka 3.0 and will be removed in 4.0
  - See section 2 for instructions on building with a specific Scala version

- **Gradle**: Uses Gradle wrapper (`./gradlew`) - no separate installation needed
  - The wrapper is included in the repository at `gradle/wrapper/`

- **Maven** (optional): Required only for Kafka Streams quickstart archetype testing
  - Needed for `streams/quickstart/` directory projects

### Optional Dependencies

- **IntelliJ IDEA** or **Eclipse**: For IDE support
  - Gradle can generate IDE project files (see section 2)

### System Requirements

- At least 2GB of heap memory (configured in `gradle.properties` as `org.gradle.jvmargs=-Xmx2g`)
- Modern CPU (Gradle uses parallel builds by default)

## 2. Gradle Build System

Kafka uses Gradle as its build system with a multi-module structure.

### Module Structure

The main modules are defined in `settings.gradle` and include:

- **clients**: Client libraries (producer, consumer, admin)
- **core**: Broker implementation
- **connect**: Apache Kafka Connect framework
- **streams**: Kafka Streams topology API
- **examples**: Example applications
- **generator**: Code generators
- **server**: Server-related code
- **storage**: Storage layer
- **raft**: RAFT consensus implementation
- Many other specialized modules

### Common Build Commands

#### Building the Entire Project

```bash
./gradlew jar                    # Build all JARs
./gradlew clean                  # Clean all build artifacts
./gradlew build                  # Full build (compile + test + package)
```

#### Building Specific Modules

```bash
./gradlew core:jar               # Build only the core module
./gradlew clients:jar            # Build only the clients module
./gradlew streams:jar            # Build only the streams module
./gradlew connect:runtime:jar    # Build a submodule within connect
```

#### Building with Specific Scala Version

By default, Kafka builds with Scala 2.13. To use Scala 2.12:

```bash
./gradlew -PscalaVersion=2.12 jar                # Build with Scala 2.12
./gradlew -PscalaVersion=2.12.7 jar              # Build with full version
./gradlewAll test                                 # Build and test with ALL Scala versions
./gradlewAll jar                                  # Build JAR with all Scala versions
```

#### Generating IDE Project Files

```bash
./gradlew idea                   # Generate IntelliJ IDEA project files
./gradlew eclipse                # Generate Eclipse project files
```

**Note**: IntelliJ IDEA has excellent built-in Gradle support, so this is usually not necessary.

#### Other Build Tasks

```bash
./gradlew tasks                  # List all available Gradle tasks
./gradlew srcJar                 # Build source JARs
./gradlew javadoc                # Build Javadoc
./gradlew scaladoc               # Build Scaladoc
./gradlew javadocJar             # Build javadoc JAR for each module
./gradlew scaladocJar            # Build scaladoc JAR for each module
./gradlew docsJar                # Build both javadoc and scaladoc JARs
./gradlew testJar                # Build test JARs
./gradlew releaseTarGz           # Build release tarball (output: `core/build/distributions/`)
./gradlew clean systemTestLibs   # Build system test libraries
```

#### Dependency Management

```bash
./gradlew allDeps                 # Show all dependencies for all projects
./gradlew allDepInsight --configuration runtimeClasspath --dependency com.example:artifact
./gradlew dependencyUpdates       # Check for available dependency updates
```

### Common Gradle Options

Configure builds with `-P` flags:

```bash
./gradlew -PmaxParallelForks=1 test              # Run tests serially (default: CPU count)
./gradlew -PskipSigning=true publish             # Skip artifact signing
./gradlew -PscalaVersion=2.12 jar                # Use specific Scala version
./gradlew -PkeepAliveMode=session clean test     # Keep Scala compiler daemon alive
./gradlew -PenableTestCoverage=true test         # Enable code coverage (slower)
./gradlew -PmaxTestRetries=2 test                # Retry failed tests (default: 0)
./gradlew -PmaxTestRetryFailures=5 test          # Max retries before giving up
```

### Build Performance Tips

- **Parallel builds**: Enabled by default in `gradle.properties`
- **Daemon reuse**: Use `-PkeepAliveMode=session` to keep compilers alive between builds
- **Incremental compilation**: Only recompiles changed code
- **Test caching**: Don't re-run passing tests (use `--rerun` to force)

## 3. Running Tests

Kafka has three types of tests:

1. **Unit Tests**: Fast, in-process tests
2. **Integration Tests**: Medium-speed tests that may use test brokers
3. **System Tests**: Full integration tests using Docker (in `tests/` directory)

### Unit and Integration Tests (Gradle)

#### Run All Tests

```bash
./gradlew test                   # Run all unit and integration tests
./gradlew unitTest               # Run only unit tests
./gradlew integrationTest        # Run only integration tests
```

#### Run Tests for Specific Modules

```bash
./gradlew clients:test           # All tests in clients module
./gradlew core:test              # All tests in core module
./gradlew streams:testAll        # All streams tests (includes multiple subprojects)
```

#### Run Specific Test Classes

```bash
./gradlew clients:test --tests RequestResponseTest
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest
```

#### Run Specific Test Methods

```bash
./gradlew clients:test --tests org.apache.kafka.clients.MetadataTest.testTimeToNextUpdate
./gradlew core:test --tests kafka.api.ProducerFailureHandlingTest.testCannotSendToInternalTopic
```

#### Run Tests Repeatedly

Force re-run without code changes:

```bash
./gradlew test --rerun           # Re-run all tests
./gradlew unitTest --rerun       # Re-run unit tests only
./gradlew clients:test --tests RequestResponseTest --rerun  # Re-run specific test
```

Continuously run a test until it passes (useful for flaky tests):

```bash
I=0; while ./gradlew clients:test --tests RequestResponseTest --rerun --fail-fast; do (( I=$I+1 )); echo "Completed run: $I"; sleep 1; done
```

#### Test Output and Configuration

Configure test parallelism and retries:

```bash
./gradlew test -PmaxParallelForks=2          # Run max 2 test processes in parallel
./gradlew test -PmaxTestRetries=2            # Retry each failed test up to 2 times
./gradlew test -PmaxTestRetryFailures=5      # Stop retrying after 5 total failures
./gradlew test -PignoreFailures=true         # Don't fail build on test failures
./gradlew test -PshowStandardStreams=true    # Print test stdout/stderr to console
./gradlew test -PtestLoggingEvents=started,passed,skipped,failed  # Log specific events
```

#### Test Logging Configuration

By default, minimal logging is shown during tests. To see more logs, modify the test logging configuration:

```bash
# Edit the log4j configuration for your module (example for clients):
# Edit clients/src/test/resources/log4j.properties
# Change: log4j.logger.org.apache.kafka=DEBUG  (or other levels)

./gradlew cleanTest clients:test --tests NetworkClientTest   # Clean cache, then run with new logging
```

#### Code Coverage Reports

Generate test coverage reports:

```bash
# For the whole project
./gradlew reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false

# For a single module
./gradlew clients:reportCoverage -PenableTestCoverage=true -Dorg.gradle.parallel=false
```

### System Integration Tests (Docker)

Located in `tests/` directory, these use the [ducktape](https://github.com/confluentinc/ducktape) testing framework.

#### Prerequisites

```bash
# Kafka must be built first
./gradlew clean systemTestLibs
```

#### Run System Tests

```bash
# Run all system tests
bash tests/docker/run_tests.sh

# Run all tests with debug logging
_DUCKTAPE_OPTIONS="--debug" bash tests/docker/run_tests.sh | tee debug_logs.txt

# Run a subset of tests
TC_PATHS="tests/kafkatest/tests/streams tests/kafkatest/tests/tools" bash tests/docker/run_tests.sh

# Run a specific test file
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py" bash tests/docker/run_tests.sh

# Run a specific test class
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest" bash tests/docker/run_tests.sh

# Run a specific test method
TC_PATHS="tests/kafkatest/tests/client/pluggable_test.py::PluggableConsumerTest.test_start_stop" bash tests/docker/run_tests.sh

# Run a specific test with parameters
TC_PATHS="tests/kafkatest/tests/streams/streams_upgrade_test.py::StreamsUpgradeTest.test_metadata_upgrade" _DUCKTAPE_OPTIONS='--parameters '\''{"from_version":"0.10.1.1","to_version":"2.6.0-SNAPSHOT"}'\' bash tests/docker/run_tests.sh
```

#### System Test Management

```bash
# Start ducker containers with native Kafka
bash tests/docker/ducker-ak up -m native

# Run tests with Kafka in native mode
_DUCKTAPE_OPTIONS="--globals '{\"kafka_mode\":\"native\"}'" TC_PATHS="tests/kafkatest/tests/" bash tests/docker/run_tests.sh

# Rebuild Kafka first, then run tests
REBUILD="t" bash tests/docker/run_tests.sh

# Remove ducker containers
bash tests/docker/ducker-ak down -f

# Debug tests in VS Code (test waits for debugger)
tests/docker/ducker-ak up
tests/docker/ducker-ak test tests/kafkatest/tests/core/security_test.py --debug
```

### Message Auto-Generation

When working with RPC messages, you may need to rebuild generated code:

```bash
./gradlew processMessages processTestMessages
```

This is sometimes necessary when switching branches due to code changes.

## 4. CI Pipeline

Kafka uses two CI systems:

### Jenkins (Primary)

**Configuration**: `Jenkinsfile` in repository root

**What it runs**:
- Validation checks (Checkstyle, Spotbugs, etc.) on all pull requests
- Unit and integration tests across multiple Java versions (8, 11, 17)
- System tests via ducktape
- Multiple Scala versions (2.12 and 2.13)
- Streams archetype compilation test

**Stages**:
- **JDK 8 + Scala 2.12**: Full validation and testing
- **JDK 11 + Scala 2.13**: Full validation, tests only on main branch
- **JDK 17 + Scala 2.13**: Full validation, tests only on main branch

**Key Jenkins Features**:
- Uses `retry_zinc` wrapper for compiler stability
- Runs with `PkeepAliveMode="session"` for faster Scala compilation
- Provides XML test reports in JUnit format
- Marked build as UNSTABLE (not FAILURE) for archetype test failures

**Whitelist**: PR builds are triggered by authorized users listed in `.asf.yaml`

### GitHub Actions

**Configuration**: `.github/workflows/*.yml`

**What it runs**:
- Docker image builds (manual trigger)
- Docker official image builds (manual trigger)
- CVE scanning with Trivy
- Docker image promotion (manual trigger)
- Stale issue/PR management

**Key GitHub features**:
- Automated security scanning of built images
- Multi-platform Docker builds (QEMU support)
- Upload of test reports and scan results as artifacts

### Code Quality Checks

The CI pipeline runs several code quality checks:

#### Checkstyle

Enforces consistent coding style:

```bash
./gradlew checkstyleMain checkstyleTest spotlessCheck

# Reports are in: reports/checkstyle/reports/{main,test}.html
```

**Note**: `spotlessCheck` has an issue with Java 21 - use JDK 11 or 17 for this.

#### Spotless (Import Optimization)

Optimizes Java import statements and formatting:

```bash
./gradlew spotlessApply        # Auto-fix import order (requires JDK 11+)
./gradlew spotlessCheck        # Check import order (not compatible with Java 21)
```

**Note**: `spotlessApply` also requires JDK 11+, not compatible with Java 21.

#### Spotbugs

Static analysis to find bugs:

```bash
./gradlew spotbugsMain spotbugsTest -x test

# HTML reports: reports/spotbugs/{main,test}.html
# Or with XML: -PxmlSpotBugsReport=true
```

## 5. Code Review Process

### Finding Work to Do

1. **Browse JIRA Issues**: https://issues.apache.org/jira/browse/KAFKA
   - Look for issues labeled `good-first-issue` or `help-wanted`
   - Check the status: unassigned issues are available to claim
   - Comment on the issue to indicate you want to work on it

2. **Mailing List**: https://kafka.apache.org/contact.html
   - Subscribe to `dev@kafka.apache.org` for discussions
   - Post questions about contributions here

3. **Confluence Wiki**: https://cwiki.apache.org/confluence/display/KAFKA/
   - Contains KIPs (Kafka Improvement Proposals)
   - Design discussions and architectural information

### Contributing Code

#### 1. Create a JIRA Issue (if needed)

- Go to https://issues.apache.org/jira/browse/KAFKA
- Create an issue or claim an existing one
- Take note of the JIRA issue key (e.g., `KAFKA-12345`)

#### 2. Fork and Clone the Repository

```bash
# If you haven't already, fork apache/kafka on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/kafka.git
cd kafka

# Add upstream remote for the official repository
git remote add upstream https://github.com/apache/kafka.git

# Keep your fork in sync (do this before starting work)
git fetch upstream
git checkout main
git rebase upstream/main
```

#### 3. Create a Feature Branch

Kafka doesn't have strict branch naming conventions, but it's good practice to include the JIRA issue:

```bash
git checkout -b KAFKA-12345-description-of-change

# Example
git checkout -b KAFKA-11111-fix-producer-timeout
```

#### 4. Make Your Changes

- Follow the coding style (Kafka uses Checkstyle for enforcement)
- Add unit tests for new functionality
- Add integration tests for significant changes
- Update documentation/javadocs as needed

```bash
# Run code quality checks before committing
./gradlew spotlessApply           # Fix import order
./gradlew checkstyleMain checkstyleTest spotlessCheck  # Check style
./gradlew spotbugsMain spotbugsTest -x test  # Check for bugs

# Run relevant tests
./gradlew core:test               # If you modified core
./gradlew clients:test            # If you modified clients
./gradlew streams:testAll         # If you modified streams
```

#### 5. Commit Your Changes

Write clear, descriptive commit messages following Apache Kafka conventions:

```bash
git add path/to/changed/files
git commit -m "KAFKA-12345: Brief description of change

Longer explanation of what the change does, why it's needed, and any
important implementation details.

Reviewers: @reviewer1, @reviewer2"
```

**Note**: Include the JIRA issue number at the start. The "Reviewers:" line is optional but helpful.

#### 6. Push to Your Fork and Create a Pull Request

```bash
git push origin KAFKA-12345-description-of-change
```

Then:
1. Go to https://github.com/apache/kafka
2. Click "New Pull Request"
3. Select your branch as the compare branch
4. Fill in the PR description (there's a template: `PULL_REQUEST_TEMPLATE.md`)
5. Submit

#### 7. PR Description Format

The PR title and description become the squashed commit message, so make them descriptive:

```markdown
**Title (becomes commit message subject)**:
KAFKA-12345: Brief description of change

**Description**:
More detailed explanation of what this PR does, including:
- Why this change is needed
- How it works
- Any relevant design decisions

**Testing Strategy**:
- What tests were added/modified
- What manual testing was done
- Rationale for test coverage

Example:
- Added unit tests in ProducerTest for timeout scenarios
- Verified with integration test on single-broker cluster
- Tested with both Scala 2.12 and 2.13
```

### Code Review Expectations

#### CI Checks (Automatic)

- **Jenkins**: Runs on all PRs from authorized contributors
  - If you're not authorized, a committer can trigger the build by commenting
  - Must pass Checkstyle, Spotbugs, and tests
  - Tests run on Java 8, 11, and 17; Scala 2.12 and 2.13

- **GitHub Actions**: Runs for Docker-related changes

#### Human Review

1. **Finding Reviewers**:
   - Use the `reviewers.py` script to suggest reviewers:
     ```bash
     ./reviewers.py
     ```
   - Look at recent commits in the area you modified:
     ```bash
     git log --oneline -- path/to/modified/file | head -10
     ```
   - Mention them in your PR description or comments

2. **Committer Checklist** (from `PULL_REQUEST_TEMPLATE.md`):
   - [ ] Design and implementation verified
   - [ ] Test coverage and CI build status verified
   - [ ] Documentation (including upgrade notes if needed) verified

3. **Code Review Process**:
   - Reviewers will comment on the PR
   - Make requested changes and push them to your branch (they auto-update the PR)
   - Address all comments before requesting re-review
   - **Do not force-push** to the main branch - that's only for final merge

4. **Approval and Merge**:
   - At least one committer must approve the PR
   - Once approved, a committer will merge the PR using `kafka-merge-pr.py`
   - Your PR title + description becomes the final commit message
   - The PR is squashed into a single commit on main

#### Formatting Requirements

Before finalizing, ensure:

```bash
# Fix import order and formatting (requires JDK 11 or 17, not 21)
./gradlew spotlessApply

# Check style compliance
./gradlew checkstyleMain checkstyleTest spotlessCheck

# Run relevant tests
./gradlew core:test          # for broker changes
./gradlew clients:test       # for client changes
./gradlew streams:testAll    # for streams changes
```

## 6. Developer Workflow Example

Here's a complete example of fixing a bug or implementing a small feature:

### Scenario: Fix Producer Timeout Issue (KAFKA-12345)

#### Step 1: Prepare Your Repository

```bash
cd ~/workspace/kafka
git fetch upstream
git checkout main
git rebase upstream/main

# Or if you just cloned:
git clone https://github.com/YOUR_USERNAME/kafka.git
cd kafka
git remote add upstream https://github.com/apache/kafka.git
```

#### Step 2: Create Feature Branch

```bash
git checkout -b KAFKA-12345-fix-producer-timeout
```

#### Step 3: Understand the Code

```bash
# Find relevant code
find clients -name "*.java" | xargs grep -l "producer.*timeout"

# Run existing tests to ensure your environment works
./gradlew clients:test --tests ProducerTest --rerun
```

#### Step 4: Make Your Changes

Edit files as needed. For this example, let's say we modify `clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java`

```bash
# Edit the file
vim clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java

# Add tests in clients/src/test/java/org/apache/kafka/clients/ProducerTest.java
vim clients/src/test/java/org/apache/kafka/clients/ProducerTest.java
```

#### Step 5: Test Your Changes

```bash
# Run the specific test you modified
./gradlew clients:test --tests ProducerTest.testProducerTimeout

# Run all producer-related tests
./gradlew clients:test --tests "*Producer*"

# Run all client tests to ensure no regressions
./gradlew clients:test

# Check code quality
./gradlew spotlessApply          # Fix formatting
./gradlew checkstyleMain         # Check style
./gradlew spotbugsMain -x test   # Check for bugs
```

#### Step 6: View Your Changes

```bash
git status                       # See modified files
git diff clients/                # View changes to clients module
```

#### Step 7: Commit with Message

```bash
git add clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java
git add clients/src/test/java/org/apache/kafka/clients/ProducerTest.java

git commit -m "KAFKA-12345: Fix producer timeout calculation

The producer was incorrectly calculating timeout values when
retrying messages, causing premature request failures.

This fix ensures that timeout is recalculated per retry attempt
rather than using the original request timeout.

Added test case: testProducerTimeoutPerRetry

Reviewers: @junrao, @ijuma"
```

#### Step 8: Push and Create Pull Request

```bash
git push origin KAFKA-12345-fix-producer-timeout
```

Go to https://github.com/apache/kafka and create a PR:

**Title**:
```
KAFKA-12345: Fix producer timeout calculation
```

**Description**:
```markdown
The producer was incorrectly calculating timeout values when retrying messages,
causing premature request failures.

This fix ensures that timeout is recalculated per retry attempt rather than
using the original request timeout.

### Testing
- Added unit test `testProducerTimeoutPerRetry` in ProducerTest
- Ran full client test suite: `./gradlew clients:test`
- Verified with Scala 2.12 and 2.13
- Manual test with retry scenario confirmed fix resolves the issue

### Reviewers
@junrao @ijuma
```

#### Step 9: Address Review Feedback

```bash
# Reviewer comments on the PR
# Make the requested changes
vim clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java

# Test again
./gradlew clients:test --tests ProducerTest.testProducerTimeoutPerRetry

# Commit (no need to amend, committer will squash)
git add clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java
git commit -m "Address review feedback: improve timeout calculation logic"

# Push to update PR
git push origin KAFKA-12345-fix-producer-timeout

# Comment on PR: "Addressed feedback in latest commit"
```

#### Step 10: Committer Merges PR

Once approved:
1. A committer clicks "Squash and merge" on GitHub
2. Or runs: `./kafka-merge-pr.py` locally
3. Your two commits become one on main with your PR title as the message
4. Your local main is now behind; sync it:

```bash
git fetch upstream
git checkout main
git rebase upstream/main
```

#### Step 11: Celebrate! 🎉

Your change is now part of Apache Kafka!

---

## Additional Resources

- **Official Contributing Guide**: https://kafka.apache.org/contributing.html
- **Contributing Code Changes**: https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes
- **Kafka Improvement Proposals (KIPs)**: https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals
- **Issue Tracker**: https://issues.apache.org/jira/browse/KAFKA
- **Mailing Lists**: https://kafka.apache.org/contact.html
- **Git Workflow**: https://cwiki.apache.org/confluence/display/KAFKA/Git+Workflow

## Quick Reference: Common Commands

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/kafka.git && cd kafka
git remote add upstream https://github.com/apache/kafka.git

# Start new feature
git checkout main && git pull upstream main
git checkout -b KAFKA-XXXXX-your-feature

# Build and test
./gradlew clean build
./gradlew spotlessApply && ./gradlew checkstyleMain
./gradlew core:test --tests YourTestClass

# Commit
git add .
git commit -m "KAFKA-XXXXX: Your change description

Longer explanation.

Reviewers: @reviewer1, @reviewer2"

# Push and PR
git push origin KAFKA-XXXXX-your-feature

# Keep in sync with upstream
git fetch upstream
git rebase upstream/main   # if on feature branch
git rebase upstream main   # if on main branch
```

Happy contributing! 🚀
