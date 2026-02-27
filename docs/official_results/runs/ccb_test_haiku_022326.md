# ccb_test_haiku_022326

## baseline

- Valid tasks: `9`
- Mean reward: `0.472`
- Pass rate: `0.778`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [llamacpp-context-window-search-001](../tasks/ccb_test_haiku_022326--baseline--llamacpp-context-window-search-001.md) | `failed` | 0.000 | 0.000 | 20 | traj, tx |
| [llamacpp-file-modify-search-001](../tasks/ccb_test_haiku_022326--baseline--llamacpp-file-modify-search-001.md) | `failed` | 0.000 | 0.000 | 43 | traj, tx |
| [kafka-security-review-001](../tasks/ccb_test_haiku_022326--baseline--kafka-security-review-001.md) | `passed` | 0.440 | 0.000 | 7 | traj, tx |
| [openhands-search-file-test-001](../tasks/ccb_test_haiku_022326--baseline--openhands-search-file-test-001.md) | `passed` | 0.400 | 0.000 | 33 | traj, tx |
| [test-coverage-gap-002](../tasks/ccb_test_haiku_022326--baseline--test-coverage-gap-002.md) | `passed` | 0.940 | 0.000 | 87 | traj, tx |
| [test-integration-001](../tasks/ccb_test_haiku_022326--baseline--test-integration-001.md) | `passed` | 1.000 | 0.000 | 26 | traj, tx |
| [test-integration-002](../tasks/ccb_test_haiku_022326--baseline--test-integration-002.md) | `passed` | 0.370 | 0.000 | 56 | traj, tx |
| [test-unitgen-go-001](../tasks/ccb_test_haiku_022326--baseline--test-unitgen-go-001.md) | `passed` | 0.620 | 0.000 | 21 | traj, tx |
| [test-unitgen-py-001](../tasks/ccb_test_haiku_022326--baseline--test-unitgen-py-001.md) | `passed` | 0.480 | 0.000 | 10 | traj, tx |

## mcp

- Valid tasks: `8`
- Mean reward: `0.555`
- Pass rate: `0.625`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_llamacpp-context-window-search-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_llamacpp-context-window-search-001.md) | `failed` | 0.000 | 1.000 | 4 | traj, tx |
| [sgonly_llamacpp-file-modify-search-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_llamacpp-file-modify-search-001.md) | `failed` | 0.000 | 0.036 | 28 | traj, tx |
| [sgonly_openhands-search-file-test-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_openhands-search-file-test-001.md) | `failed` | 0.000 | 0.119 | 42 | traj, tx |
| [sgonly_kafka-security-review-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_kafka-security-review-001.md) | `passed` | 0.440 | 0.857 | 7 | traj, tx |
| [sgonly_test-coverage-gap-002](../tasks/ccb_test_haiku_022326--mcp--sgonly_test-coverage-gap-002.md) | `passed` | 1.000 | 0.964 | 28 | traj, tx |
| [sgonly_test-integration-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_test-integration-001.md) | `passed` | 1.000 | 0.567 | 30 | traj, tx |
| [sgonly_test-unitgen-go-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_test-unitgen-go-001.md) | `passed` | 1.000 | 0.312 | 16 | traj, tx |
| [sgonly_test-unitgen-py-001](../tasks/ccb_test_haiku_022326--mcp--sgonly_test-unitgen-py-001.md) | `passed` | 1.000 | 0.333 | 3 | traj, tx |
