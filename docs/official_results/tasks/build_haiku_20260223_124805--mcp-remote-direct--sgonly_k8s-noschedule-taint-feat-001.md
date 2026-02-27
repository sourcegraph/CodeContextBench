# sgonly_k8s-noschedule-taint-feat-001 (mcp-remote-direct)

- Run: `build_haiku_20260223_124805`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/build_haiku_20260223_124805--mcp-remote-direct--sgonly_k8s-noschedule-taint-feat-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 7021.8 |
| Agent execution seconds | 4383.3 |
| Input tokens | 22,879,663 |
| Output tokens | 481 |
| Cache tokens | 22,878,646 |
| Tool calls (total) | 104 |
| Tool calls (MCP) | 29 |
| Tool calls (local) | 75 |
| MCP ratio | 0.279 |
| keyword_search calls | 12 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `cf26484cce1ea33e0cd28f6c43284b80d950c578c8843b5e9ecdaa28f9fd133b` |
| `trajectory.json` SHA256 | `5b7f04342d284009f696a1bb29fbdb2558ba800287a7f8bb5e2855ed7d7c1001` |
| transcript SHA256 | `8f05d2b0de1cc234b3373b6cccdefa35352e7a20f15740bcf2b6ad089ca902a1` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 38 |
| `mcp__sourcegraph__sg_read_file` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 12 |
| `TaskOutput` | 7 |
| `Write` | 7 |
| `Grep` | 6 |
| `TodoWrite` | 5 |
| `Read` | 4 |
| `TaskStop` | 3 |
| `Edit` | 2 |
| `Glob` | 2 |
| `Task` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
