# ccx-onboard-050-ds (mcp)

- Run: `ccb_mcp_onboarding_haiku_022126`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/ccb_mcp_onboarding_haiku_022126--mcp--ccx-onboard-050-ds.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_onboarding_haiku_022126--mcp--ccx-onboard-050-ds/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1411.2 |
| Agent execution seconds | 1143.2 |
| Input tokens | 3,297,274 |
| Output tokens | 110 |
| Cache tokens | 3,296,750 |
| Tool calls (total) | 24 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 1 |
| MCP ratio | 0.958 |
| keyword_search calls | 7 |
| nls_search calls | 5 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `fde50769609d71cf1cee8d597bb1a0fd06198033dd62a93c239b7739854b07ca` |
| `trajectory.json` SHA256 | `87814c62b28d1378b31780583eba69496ea36ecdb5322259b83cafc54af7c4e4` |
| transcript SHA256 | `b386f946645d9e6f8ee94607854dda855a19bf9d3cf77cdb19d1175238a3d98f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_nls_search` | 5 |
| `mcp__sourcegraph__sg_list_repos` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
