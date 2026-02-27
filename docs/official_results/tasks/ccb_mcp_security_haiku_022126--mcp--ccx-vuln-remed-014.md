# ccx-vuln-remed-014 (mcp)

- Run: `ccb_mcp_security_haiku_022126`
- Status: `passed`
- Reward: `0.6429`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_022126--mcp--ccx-vuln-remed-014.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1163.0 |
| Agent execution seconds | 1074.1 |
| Input tokens | 3,280,963 |
| Output tokens | 129 |
| Cache tokens | 3,280,081 |
| Tool calls (total) | 41 |
| Tool calls (MCP) | 40 |
| Tool calls (local) | 1 |
| MCP ratio | 0.976 |
| keyword_search calls | 9 |
| nls_search calls | 4 |
| deepsearch calls | 2 |
| `result.json` SHA256 | `4439f54790b0a64aa59e1a18e743f8b7015deeaabc8ef1af6d668b23bafde01d` |
| `trajectory.json` SHA256 | `298ed7b3aa4403a89dcf9f2aae5f12a5029a1d5d507e0f577fb5e0c798dcccfa` |
| transcript SHA256 | `2291a9091665aecfda20086d7ddc73e9acb29d6d603f6248431d3320fc01cef3` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 14 |
| `mcp__sourcegraph__sg_keyword_search` | 9 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `mcp__sourcegraph__sg_nls_search` | 4 |
| `mcp__sourcegraph__sg_deepsearch_read` | 3 |
| `mcp__sourcegraph__sg_deepsearch` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
