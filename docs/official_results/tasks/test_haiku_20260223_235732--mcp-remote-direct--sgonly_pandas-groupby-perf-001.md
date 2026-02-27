# sgonly_pandas-groupby-perf-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_pandas-groupby-perf-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 536.6 |
| Agent execution seconds | 478.6 |
| Input tokens | 10,328,763 |
| Output tokens | 385 |
| Cache tokens | 10,328,232 |
| Tool calls (total) | 115 |
| Tool calls (MCP) | 59 |
| Tool calls (local) | 56 |
| MCP ratio | 0.513 |
| keyword_search calls | 11 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `cb94cb87ae9fa0a0579707ef87d8f671125d13dc9c937665b359f00aeab8ab3e` |
| `trajectory.json` SHA256 | `c0b07f1c5ee88e91767a5dbf6a157d68c872ad9c883242fa272d94646f4c8c1f` |
| transcript SHA256 | `2e95008a0abe796211c6ac8c61d959b325bd85592e1f8b6bef900e4814bbfc98` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 42 |
| `mcp__sourcegraph__sg_read_file` | 23 |
| `mcp__sourcegraph__sg_keyword_search` | 18 |
| `Read` | 6 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `mcp__sourcegraph__sg_nls_search` | 4 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_commit_search` | 3 |
| `Grep` | 2 |
| `mcp__sourcegraph__sg_compare_revisions` | 2 |
| `Edit` | 1 |
| `Glob` | 1 |
| `Task` | 1 |
| `mcp__sourcegraph__sg_deepsearch` | 1 |
| `mcp__sourcegraph__sg_deepsearch_read` | 1 |
| `mcp__sourcegraph__sg_diff_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Grep` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Task` |
| `Grep` |
| `Glob` |
| `Bash` |
