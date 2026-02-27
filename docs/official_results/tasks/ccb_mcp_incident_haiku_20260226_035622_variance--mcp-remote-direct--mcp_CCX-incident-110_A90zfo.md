# mcp_CCX-incident-110_A90zfo (mcp-remote-direct)

- Run: `ccb_mcp_incident_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.9231`
- Audit JSON: [link](../audits/ccb_mcp_incident_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-incident-110_A90zfo.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 652.9 |
| Agent execution seconds | 73.0 |
| Input tokens | 806,796 |
| Output tokens | 3,567 |
| Cache tokens | 806,590 |
| Tool calls (total) | 10 |
| Tool calls (MCP) | 9 |
| Tool calls (local) | 1 |
| MCP ratio | 0.900 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9e4207373413a2e78cb944cffca9da559daebf253aff02668f674c545cbf6c30` |
| `trajectory.json` SHA256 | `65079bb8b765dbaeef924ce8403744d3a0186eebc08c9e6be5e01c3b36e7ada3` |
| transcript SHA256 | `ca899a0cad5fbfb3700a2e26b470f739a1bb07ce071add118f0794c6aeec995f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
