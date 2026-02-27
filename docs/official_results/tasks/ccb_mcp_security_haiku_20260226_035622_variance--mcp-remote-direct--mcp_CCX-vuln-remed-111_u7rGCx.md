# mcp_CCX-vuln-remed-111_u7rGCx (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-vuln-remed-111_u7rGCx.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 275.3 |
| Agent execution seconds | 56.0 |
| Input tokens | 1,094,240 |
| Output tokens | 5,560 |
| Cache tokens | 1,093,940 |
| Tool calls (total) | 13 |
| Tool calls (MCP) | 11 |
| Tool calls (local) | 2 |
| MCP ratio | 0.846 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `013aeec937c09606540c0254cd5b08925d49e57e8ab4f2f57cceab3c36721b27` |
| `trajectory.json` SHA256 | `325ea810fd062882887de34907d9d11c64936f743328b6e11efcd9dcf22f8310` |
| transcript SHA256 | `ff31d6d262e6af12fa67b2a94338bfc3c21f971841e736246ca5bb495a0c0293` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Write` |
