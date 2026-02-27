# ccx-onboard-041 (mcp)

- Run: `ccb_mcp_onboarding_haiku_022126`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_onboarding_haiku_022126--mcp--ccx-onboard-041.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_onboarding_haiku_022126--mcp--ccx-onboard-041/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 577.1 |
| Agent execution seconds | 498.9 |
| Input tokens | 1,597,218 |
| Output tokens | 85 |
| Cache tokens | 1,596,910 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 1 |
| MCP ratio | 0.929 |
| keyword_search calls | 8 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f2db977c63bf015fbfbcd4cb7d166732ce96bd88572d358dedb73acd2a5597ed` |
| `trajectory.json` SHA256 | `b10c785e008da9f6486c9047d888996c92761606f63a0f717ff0fda65167be18` |
| transcript SHA256 | `1b6f67f84f3e6469227aa60676a7ec3477444c8bbcad482e89b582d2a7d0c12f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
