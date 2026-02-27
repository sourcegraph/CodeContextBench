# ccx-incident-031 (mcp)

- Run: `ccb_mcp_incident_haiku_022126`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_incident_haiku_022126--mcp--ccx-incident-031.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1801.6 |
| Agent execution seconds | 1634.5 |
| Input tokens | 492,848 |
| Output tokens | 50 |
| Cache tokens | 492,687 |
| Tool calls (total) | 6 |
| Tool calls (MCP) | 5 |
| Tool calls (local) | 1 |
| MCP ratio | 0.833 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e00c5ba41dba4101e1f53e367d83b5280affa82dab76a5d972f602a46308b0d0` |
| `trajectory.json` SHA256 | `20eb7a251c4859cdccc0aed2795f7a2764447810d5847d1e3d5829f512bdd798` |
| transcript SHA256 | `b8ad5ca6e48074f252a21b209ffb22b778da2f6965ec1ba2cdae48241b114b29` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_read_file` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
