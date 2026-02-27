# mcp_ccx-compliance-051_rSkovg (mcp-remote-direct)

- Run: `ccb_mcp_compliance_haiku_20260226_035515_variance`
- Status: `passed`
- Reward: `0.4615`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260226_035515_variance--mcp-remote-direct--mcp_ccx-compliance-051_rSkovg.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 241.5 |
| Agent execution seconds | 121.2 |
| Input tokens | 3,728,266 |
| Output tokens | 7,295 |
| Cache tokens | 3,727,702 |
| Tool calls (total) | 35 |
| Tool calls (MCP) | 34 |
| Tool calls (local) | 1 |
| MCP ratio | 0.971 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `598f929ead54ac2efae1019b1302a46266ecc19df4229cde791abc3e649d862a` |
| `trajectory.json` SHA256 | `3043932671f8eb68f28e77fa7d6a0d1d2067086d0db3bb5aa1505496fff8e649` |
| transcript SHA256 | `3f279604179a804b963be3634780c520d42ed828ae7b029fee3ff22ef695eedc` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 12 |
| `mcp__sourcegraph__sg_keyword_search` | 9 |
| `mcp__sourcegraph__sg_nls_search` | 9 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
