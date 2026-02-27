# ccx-vuln-remed-011 (mcp)

- Run: `ccb_mcp_security_haiku_022126`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_022126--mcp--ccx-vuln-remed-011.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_security_haiku_022126--mcp--ccx-vuln-remed-011/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1138.4 |
| Agent execution seconds | 1078.0 |
| Input tokens | 3,044,873 |
| Output tokens | 102 |
| Cache tokens | 3,044,063 |
| Tool calls (total) | 35 |
| Tool calls (MCP) | 34 |
| Tool calls (local) | 1 |
| MCP ratio | 0.971 |
| keyword_search calls | 21 |
| nls_search calls | 3 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9196c58faf08254867041bb3719b8e34adf331a5c7b0a3ad4da2b5c971b09496` |
| `trajectory.json` SHA256 | `413ab38d60fbddefc78323f962974ac117b5bb2cca0df620364e9c4c57ee4fa0` |
| transcript SHA256 | `bb91414eda2ab8a9d9abaeddb800f8237333e63bb6afb47fad59aaad20873b23` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 21 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `mcp__sourcegraph__sg_list_repos` | 4 |
| `mcp__sourcegraph__sg_nls_search` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
