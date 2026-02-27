# mcp_CCX-vuln-remed-012_9JwGrW (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.3966`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-012_9JwGrW.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 355.1 |
| Agent execution seconds | 114.7 |
| Input tokens | 4,052,739 |
| Output tokens | 11,931 |
| Cache tokens | 4,051,920 |
| Tool calls (total) | 36 |
| Tool calls (MCP) | 32 |
| Tool calls (local) | 4 |
| MCP ratio | 0.889 |
| keyword_search calls | 13 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `310f6344dd8557054c1bf5183469638dc06789cefb9bd2041fe7c7b01aa02913` |
| `trajectory.json` SHA256 | `bb4461c0e0379972887ed7590ea76f09f86a5bf702ab90f629dc7c2a6137ea9f` |
| transcript SHA256 | `3be938b3823078a96b84f4248a0b035557e57aac4e6ff7a09ee0a241478c1788` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 13 |
| `mcp__sourcegraph__sg_read_file` | 11 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Bash` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
