# mcp_pandas-groupby-perf-001_Tfai7M (mcp-remote-direct)

- Run: `ccb_test_haiku_20260224_180149`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_20260224_180149--mcp-remote-direct--mcp_pandas-groupby-perf-001_Tfai7M.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_test_haiku_20260224_180149--mcp-remote-direct--mcp_pandas-groupby-perf-001_Tfai7M/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 445.8 |
| Agent execution seconds | 369.7 |
| Input tokens | 12,325,618 |
| Output tokens | 426 |
| Cache tokens | 12,325,162 |
| Tool calls (total) | 90 |
| Tool calls (MCP) | 11 |
| Tool calls (local) | 79 |
| MCP ratio | 0.122 |
| keyword_search calls | 5 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `c7428da4615d3e51a84218335145e33a530fe77d1c3d1658112168bab069df87` |
| `trajectory.json` SHA256 | `12335c388975a701ba5ad43cc57a7886edf6c8306001933a2e5fba1e7f214e41` |
| transcript SHA256 | `0388e59b705a1c6104a16f8e803d9530cfa5c7bc23f86f75ab96e45327e8663e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 58 |
| `Read` | 16 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Grep` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Grep` |
| `Read` |
| `Bash` |
| `mcp__sourcegraph__sg_nls_search` |
