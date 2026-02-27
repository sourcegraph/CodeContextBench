# mcp_CCX-vuln-remed-105_1RoC5v (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035617`
- Status: `passed`
- Reward: `0.8095`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-vuln-remed-105_1RoC5v.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 334.3 |
| Agent execution seconds | 79.0 |
| Input tokens | 2,391,070 |
| Output tokens | 6,745 |
| Cache tokens | 2,390,640 |
| Tool calls (total) | 24 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 1 |
| MCP ratio | 0.958 |
| keyword_search calls | 11 |
| nls_search calls | 4 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `fce76203dd86eba473aa08c328b0dbab3b87e13b1341ae3157f865e5a6de6663` |
| `trajectory.json` SHA256 | `ca386ace652bc6aa1d0763b6dcc4834a62f5f43f64ba818ad9a896b10f390f73` |
| transcript SHA256 | `3f598446da57e560c5ccb191a1d1306f252cb7899cb35b97db66a3e1a7a3428b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `mcp__sourcegraph__sg_nls_search` | 4 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
