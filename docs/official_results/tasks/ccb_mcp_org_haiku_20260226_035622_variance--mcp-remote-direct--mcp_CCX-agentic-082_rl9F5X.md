# mcp_CCX-agentic-082_rl9F5X (mcp-remote-direct)

- Run: `ccb_mcp_org_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.3301`
- Audit JSON: [link](../audits/ccb_mcp_org_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-agentic-082_rl9F5X.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 274.8 |
| Agent execution seconds | 85.8 |
| Input tokens | 2,142,472 |
| Output tokens | 8,416 |
| Cache tokens | 2,142,049 |
| Tool calls (total) | 21 |
| Tool calls (MCP) | 16 |
| Tool calls (local) | 5 |
| MCP ratio | 0.762 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9fef04675f7ba3ee114f65f2775167dd1610be0df843d4f85cbd8529cc11553d` |
| `trajectory.json` SHA256 | `b12f7b9c06e234b765113f6d56ba5a6157f64ce48e2c52af5ab1cb283f15ecfb` |
| transcript SHA256 | `cfea2508c209331233a3b11266cb9d26fd1a40b5c182d2ee60fd988dcc5e8f3f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_files` | 7 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `Read` | 2 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Bash` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
