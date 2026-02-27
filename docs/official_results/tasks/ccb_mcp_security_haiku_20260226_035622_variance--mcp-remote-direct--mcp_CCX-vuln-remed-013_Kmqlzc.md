# mcp_CCX-vuln-remed-013_Kmqlzc (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.1049`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-013_Kmqlzc.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-013_Kmqlzc/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 286.6 |
| Agent execution seconds | 91.7 |
| Input tokens | 3,237,336 |
| Output tokens | 10,211 |
| Cache tokens | 3,236,586 |
| Tool calls (total) | 35 |
| Tool calls (MCP) | 34 |
| Tool calls (local) | 1 |
| MCP ratio | 0.971 |
| keyword_search calls | 5 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f53bd9956b0659463ef5da9097ad2640f61bb16bce630e7b46515dd99a5684c2` |
| `trajectory.json` SHA256 | `f5d587300309c6404f31c0dffad8da65e8a46d8ffd0bc6869ad21f4de7a4a899` |
| transcript SHA256 | `938f5bf6f1a55a99a6e1901bbe655f0be24f988b39dc74167e5077cc4631281d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 19 |
| `mcp__sourcegraph__sg_list_files` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
