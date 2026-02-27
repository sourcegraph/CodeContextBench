# mcp_sklearn-kmeans-perf-001_8vdgQ3 (mcp-remote-direct)

- Run: `ccb_test_haiku_20260224_180149`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_20260224_180149--mcp-remote-direct--mcp_sklearn-kmeans-perf-001_8vdgQ3.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 379.0 |
| Agent execution seconds | 319.3 |
| Input tokens | 7,111,992 |
| Output tokens | 237 |
| Cache tokens | 7,111,332 |
| Tool calls (total) | 43 |
| Tool calls (MCP) | 9 |
| Tool calls (local) | 34 |
| MCP ratio | 0.209 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `ea5f0957a7bdbd8964d5357804f94da72105badae697023498d3109ab2675d85` |
| `trajectory.json` SHA256 | `d99ecc5f626169470af0e34b7f062d249ac2f4b46fc5bfb0d787e7fd1d88e2f8` |
| transcript SHA256 | `c59b898d973ab06c57955307d32e7cf5165afb8fbe11f03981dfe197f5cda543` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 16 |
| `Read` | 6 |
| `mcp__sourcegraph__sg_read_file` | 6 |
| `TodoWrite` | 5 |
| `Write` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `Edit` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
