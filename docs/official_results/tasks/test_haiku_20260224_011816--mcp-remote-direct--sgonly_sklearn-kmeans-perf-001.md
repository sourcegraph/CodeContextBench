# sgonly_sklearn-kmeans-perf-001 (mcp-remote-direct)

- Run: `test_haiku_20260224_011816`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/test_haiku_20260224_011816--mcp-remote-direct--sgonly_sklearn-kmeans-perf-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 267.4 |
| Agent execution seconds | 220.1 |
| Input tokens | 2,023,847 |
| Output tokens | 54 |
| Cache tokens | 2,023,451 |
| Tool calls (total) | 13 |
| Tool calls (MCP) | 4 |
| Tool calls (local) | 9 |
| MCP ratio | 0.308 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `8612db4d40bffa2867e5d37cd9b135625c846841eb2bbecb45035cd6067e59df` |
| `trajectory.json` SHA256 | `487dcc7416ac5e1f9ee4676791084912c4b7a8e58e70d0672d683097291dccb5` |
| transcript SHA256 | `3129b4c8846f69200de75fd92f42236b51b645cfb477943ead888e322b705cee` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `Bash` | 2 |
| `Write` | 2 |
| `Read` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `Write` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Read` |
| `Write` |
| `Bash` |
