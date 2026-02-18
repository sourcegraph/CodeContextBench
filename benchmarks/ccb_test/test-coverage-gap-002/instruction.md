# Test Coverage Gap Analysis: Kafka Consumer Group Coordinator

## Objective

Identify test coverage gaps in Apache Kafka's consumer group coordinator implementation and propose concrete regression tests for each uncovered failure mode.

## Repository

The Kafka repository is cloned at `/workspace`. Focus your analysis on the consumer group coordinator code in:

```
clients/src/main/java/org/apache/kafka/clients/consumer/internals/
```

### Key Source Files

- `ConsumerCoordinator.java` -- main coordinator logic (join group, sync group, offset commits, rebalance handling)
- `AbstractCoordinator.java` -- base coordinator (heartbeat management, coordinator discovery, group membership lifecycle)
- `Heartbeat.java` -- heartbeat timing and session timeout tracking
- `ConsumerGroupMetadata.java` -- group generation, member ID, protocol metadata

### Existing Test Files

Review the existing tests in `clients/src/test/java/org/apache/kafka/clients/consumer/internals/` to understand what is already covered before identifying gaps. Key test files include `ConsumerCoordinatorTest.java`, `AbstractCoordinatorTest.java`, and `HeartbeatTest.java`.

## Requirements

Produce a coverage analysis document at `/workspace/coverage_analysis.md` that addresses the following three areas:

### 1. Failure Mode Mapping (40% of score)

Map untested or under-tested failure modes across these categories:

- **Rebalance timeout scenarios**: What happens when `max.poll.interval.ms` expires during rebalance? When the rebalance callback itself times out? When a `RebalanceTimeoutException` is thrown?
- **Heartbeat failure scenarios**: Heartbeat thread failure, `SessionExpiredException`, heartbeat timeout edge cases, heartbeat thread lifecycle during rebalance.
- **Coordinator discovery failure**: `FindCoordinator` request failures, `GroupCoordinatorNotAvailable` errors, coordinator not available during startup or after broker failover.
- **Offset commit failure**: `CommitFailedException` scenarios, offset commit timeout, partial commit failures, commit retries after rebalance.
- **Metadata refresh failure**: Topic metadata refresh failures, partition not found after topic deletion, metadata staleness.
- **Network partition scenarios**: Broker disconnect during rebalance, connection lost mid-heartbeat, coordinator broker unavailable.
- **Concurrent rebalance race conditions**: Generation mismatch (`IllegalGenerationException`), concurrent `JoinGroup` requests, race between heartbeat and poll threads.
- **Cooperative rebalance edge cases**: Incremental rebalance with `COOPERATIVE` protocol, revocation callback failures, partial assignment during cooperative rebalance.

For each failure mode, explain what specific code paths are not exercised by existing tests.

### 2. Proposed Regression Tests (30% of score)

For each identified gap, propose a concrete regression test with:

- **Test class name** (e.g., `ConsumerCoordinatorRebalanceTimeoutTest`)
- **`@Test` method name** (e.g., `testRebalanceTimeoutDuringCallbackExecution`)
- **Mock setup**: Which objects to mock (e.g., `ConsumerNetworkClient`, `MockTime`, `SubscriptionState`), what `when(...).thenReturn(...)` or `doThrow(...)` stubs are needed.
- **Assertions**: What to `assertEquals`, `assertThrows`, or `verify(...)` to confirm the failure mode is correctly handled.
- **Timer/timeout mock patterns**: How to use `MockTime` or `advanceTime` to simulate timeout conditions.

Reference actual patterns from the existing test files. Use `RequestFuture`, `ConsumerNetworkClient` mocking, and `SubscriptionState` setup patterns consistent with the existing test suite.

### 3. Coverage Estimation (30% of score)

For each failure mode area, estimate:

- **Current coverage**: What is already tested (reference specific test file names and methods).
- **Coverage gaps**: What is not covered, with an explanation of the untested branch or error condition.
- **Priority ranking**: Which gaps are highest impact and should be tested first? Identify the critical gaps.
- **Branch coverage discussion**: Identify specific `if/else` branches or error-handling blocks that are untested.

## Quality Bar

- Reference specific Java methods, exception types, and class names from the source code.
- Propose mock setups that use patterns from the existing test suite (e.g., `Mockito.mock()`, `@Mock` annotations, `MockTime`).
- Include `assertThrows`, `assertEquals`, and `verify()` calls appropriate to each scenario.
- Reference existing test files by name (e.g., `ConsumerCoordinatorTest.java`) when discussing current coverage.

## Anti-Requirements

- Do NOT propose tests for well-tested happy paths (e.g., basic join-group, basic offset commit success).
- Focus exclusively on error paths, edge cases, and failure modes.
- Do NOT write or compile actual Java code -- this is an analysis task producing a Markdown document.

## Output

Write your complete analysis to `/workspace/coverage_analysis.md`.
