# mcp_ccx-incident-037_2kxTW3 (mcp-remote-direct)

- Run: `ccb_mcp_incident_haiku_20260226_035628_variance`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/ccb_mcp_incident_haiku_20260226_035628_variance--mcp-remote-direct--mcp_ccx-incident-037_2kxTW3.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 718.8 |
| Agent execution seconds | 95.2 |
| Input tokens | 1,296,470 |
| Output tokens | 4,220 |
| Cache tokens | 1,296,200 |
| Tool calls (total) | 12 |
| Tool calls (MCP) | 11 |
| Tool calls (local) | 1 |
| MCP ratio | 0.917 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `37eb7b36a76ccdc7fd89e01b97d1e30ff3f206cfdb6faf88877325aa94b0ee82` |
| `trajectory.json` SHA256 | `9ba3603c648c1b778b71b6411d50a4b3dc92e4eda97aa8ace78c5711a7609aaf` |
| transcript SHA256 | `48ea2455878a5d7d97e538d30a88e66b934d7a6f18ee5093d2345a1d6722386a` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 7 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

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
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
