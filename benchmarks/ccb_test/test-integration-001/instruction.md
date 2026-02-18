# Write Integration Tests for Flipt Feature Flag Evaluation API

## Objective

Write integration tests for Flipt's feature flag evaluation API. The Flipt repository is cloned at `/workspace`. Your tests should exercise the evaluation endpoints at the API level, covering both gRPC and HTTP interfaces.

## Target File

Write your test file to:

```
/workspace/internal/server/evaluation/evaluation_integration_test.go
```

## Repository Context

Flipt is a feature flag management system written in Go. The evaluation logic lives in `internal/server/evaluation/`. The evaluation API accepts requests to evaluate flags against entities with optional context, and returns match results including variant assignments and boolean outcomes.

Key source files to study before writing tests:

- `internal/server/evaluation/` -- core evaluation server implementation
- `rpc/flipt/evaluation/` -- protobuf definitions for evaluation requests/responses
- `internal/server/` -- parent server package with shared patterns

## Scenarios to Cover

Your integration tests must cover the following scenarios:

1. **Boolean flag evaluation** -- Test evaluating boolean-type flags in both enabled and disabled states. Include cases with and without entity context.

2. **Variant flag evaluation** -- Test evaluating variant-type flags that use distribution rules and match expressions to select variants. Verify the correct variant key is returned.

3. **Batch evaluation** -- Test evaluating multiple flags in a single request. Verify that the response contains results for each flag in the batch.

4. **Error cases** -- Test evaluation with a nonexistent flag key, an invalid or missing namespace, and a malformed request. Verify appropriate error codes or error responses are returned.

5. **Evaluation with entity context** -- Test evaluation requests that include entity ID and context attributes used by constraints and segment matching rules.

## Protocol Coverage

Your tests must exercise both communication protocols:

- **gRPC**: Use gRPC client stubs generated from the Flipt protobuf definitions. Connect to the evaluation service and make typed RPC calls.
- **HTTP**: Use Go's `net/http` package to send HTTP requests to the evaluation REST endpoints. Parse and validate JSON responses.

## Requirements

- Use Go testing patterns with proper setup and teardown (e.g., `TestMain`, helper functions, or `t.Cleanup`)
- Use **table-driven tests** with `t.Run()` subtests where appropriate
- Include both success assertions (`require.NoError`, `require.Equal`, or standard library equivalents) and error assertions (`require.Error`, status code checks)
- Tests must compile cleanly with `go vet`
- Declare the package as `package evaluation` or `package evaluation_test`
- Import the standard `testing` package and any necessary Flipt internal packages

## Anti-Requirements

- Do **not** write unit tests for internal helper functions. Focus exclusively on API-level integration testing.
- Do **not** mock the evaluation logic. Tests should exercise the real evaluation code path as much as possible.
- Do **not** rely on external services or network access beyond the test process itself.

## Quality Bar

- Every scenario listed above should have at least one dedicated test
- Tests should be self-contained and not depend on test execution order
- Use clear variable names, descriptive test case names, and comments explaining non-obvious setup
- Reference real Flipt types from the `rpc/flipt/evaluation` package for request/response structures
