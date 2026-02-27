# sgonly_pandas-groupby-perf-001 (mcp-remote-direct)

- Run: `test_haiku_20260224_011816`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/test_haiku_20260224_011816--mcp-remote-direct--sgonly_pandas-groupby-perf-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 322.7 |
| Agent execution seconds | 270.2 |
| Input tokens | 12,260,141 |
| Output tokens | 494 |
| Cache tokens | 12,259,610 |
| Tool calls (total) | 64 |
| Tool calls (MCP) | 38 |
| Tool calls (local) | 26 |
| MCP ratio | 0.594 |
| keyword_search calls | 20 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `bea18dcd38a1b0f18efb358d6cea04bbab395dd4a233d6ea8a5c4086519fad1e` |
| `trajectory.json` SHA256 | `1a71023a8abf3d2c287f9309aa8e81e41c7d12b136c262291474c9d6a56fc5cb` |
| transcript SHA256 | `e6f893184f564a1594dc28d1e51604140202e8a934bc27ac7604fa66961e3051` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 22 |
| `mcp__sourcegraph__sg_keyword_search` | 20 |
| `mcp__sourcegraph__sg_read_file` | 14 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Read` | 1 |
| `mcp__sourcegraph__sg_find_references` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Bash` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
