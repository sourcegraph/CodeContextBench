# mcp_CCX-vuln-remed-105_JZsxbp (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035633_variance`
- Status: `passed`
- Reward: `0.7374`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-105_JZsxbp.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 294.1 |
| Agent execution seconds | 83.5 |
| Input tokens | 2,625,631 |
| Output tokens | 6,290 |
| Cache tokens | 2,625,108 |
| Tool calls (total) | 22 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 2 |
| MCP ratio | 0.909 |
| keyword_search calls | 6 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `ce786cdc7abbae8e150767baf1288f7750925a2ef383c0f0be6faa8b929c8ef4` |
| `trajectory.json` SHA256 | `a131860ca51a35653f8e8b6cffdb43f5719a26d6e06a072588b225216d67f36e` |
| transcript SHA256 | `6f828c02b76b8a179385c60a9da281cb19472e5b2c5e3b93831b24d82240d104` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Read` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
