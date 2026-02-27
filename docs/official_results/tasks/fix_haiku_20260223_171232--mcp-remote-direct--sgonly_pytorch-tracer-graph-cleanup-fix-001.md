# sgonly_pytorch-tracer-graph-cleanup-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-tracer-graph-cleanup-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-tracer-graph-cleanup-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 2865.0 |
| Agent execution seconds | 494.1 |
| Input tokens | 7,173,156 |
| Output tokens | 388 |
| Cache tokens | 7,172,705 |
| Tool calls (total) | 120 |
| Tool calls (MCP) | 26 |
| Tool calls (local) | 94 |
| MCP ratio | 0.217 |
| keyword_search calls | 9 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `4a31d8b529c9b540b9b908dd1d08491331d70000065f0f7af3f21a3ff2333dc4` |
| `trajectory.json` SHA256 | `29ff8debcd442d0d798f35dc0b17be7c6dc2fe485d864da1fe2d9cfc5e293770` |
| transcript SHA256 | `805a06b7cd5b4cca5cffdd3eba06d613c8b12b70210dca4c5c6a6c268b46616c` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 44 |
| `WebSearch` | 19 |
| `Read` | 13 |
| `WebFetch` | 13 |
| `mcp__sourcegraph__sg_read_file` | 13 |
| `mcp__sourcegraph__sg_keyword_search` | 9 |
| `TodoWrite` | 3 |
| `Task` | 2 |
| `mcp__sourcegraph__sg_find_references` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Task` |
| `WebSearch` |
| `WebSearch` |
| `WebSearch` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
