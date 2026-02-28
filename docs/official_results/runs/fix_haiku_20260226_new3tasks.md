# fix_haiku_20260226_new3tasks

## baseline-local-direct

- Valid tasks: `3`
- Mean reward: `0.727`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [envoy-dfp-host-leak-fix-001](../tasks/fix_haiku_20260226_new3tasks--baseline-local-direct--envoy-dfp-host-leak-fix-001.html) | `passed` | 0.727 | 0.000 | 37 | traj, tx |
| [envoy-udp-proxy-cds-fix-001](../tasks/fix_haiku_20260226_new3tasks--baseline-local-direct--envoy-udp-proxy-cds-fix-001.html) | `passed` | 0.755 | 0.000 | 18 | traj, tx |
| [terraform-plan-null-unknown-fix-001](../tasks/fix_haiku_20260226_new3tasks--baseline-local-direct--terraform-plan-null-unknown-fix-001.html) | `passed` | 0.699 | 0.000 | 91 | traj, tx |

## mcp-remote-direct

- Valid tasks: `3`
- Mean reward: `0.801`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_envoy-dfp-host-leak-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-dfp-host-leak-fix-001.html) | `passed` | 0.665 | 0.345 | 29 | traj, tx |
| [sgonly_envoy-udp-proxy-cds-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-udp-proxy-cds-fix-001.html) | `passed` | 0.784 | 0.485 | 33 | traj, tx |
| [sgonly_terraform-plan-null-unknown-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_terraform-plan-null-unknown-fix-001.html) | `passed` | 0.955 | 0.193 | 83 | traj, tx |
