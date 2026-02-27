# sgonly_prometheus-queue-reshard-debug-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.6000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_prometheus-queue-reshard-debug-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_prometheus-queue-reshard-debug-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 240.6 |
| Agent execution seconds | 156.5 |
| Input tokens | 2,188,126 |
| Output tokens | 85 |
| Cache tokens | 2,187,697 |
| Tool calls (total) | 19 |
| Tool calls (MCP) | 18 |
| Tool calls (local) | 1 |
| MCP ratio | 0.947 |
| keyword_search calls | 7 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a75af3c02dc43283a3c53b9cac003aadde425d4176b808c13b390703db0a669d` |
| `trajectory.json` SHA256 | `4d7d4ab52419ec6bf938612ceb00373d20fbe88bf4d4d9e152ba290a520cc31c` |
| transcript SHA256 | `c988b4a3c9b26ec537280d101b045c50677753abaf43bad62d964ccacfb10543` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_commit_search` |
