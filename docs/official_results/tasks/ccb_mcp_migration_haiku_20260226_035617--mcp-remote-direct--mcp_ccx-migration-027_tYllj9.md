# mcp_ccx-migration-027_tYllj9 (mcp-remote-direct)

- Run: `ccb_mcp_migration_haiku_20260226_035617`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_migration_haiku_20260226_035617--mcp-remote-direct--mcp_ccx-migration-027_tYllj9.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 438.3 |
| Agent execution seconds | 53.7 |
| Input tokens | 1,038,641 |
| Output tokens | 2,980 |
| Cache tokens | 1,038,335 |
| Tool calls (total) | 11 |
| Tool calls (MCP) | 9 |
| Tool calls (local) | 2 |
| MCP ratio | 0.818 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f9bf9461108d83ac2d4764a04e931fb26642e6064b848d1f4d359ebd158d3254` |
| `trajectory.json` SHA256 | `260b1f29d40cf34a9fe00d505713971e637f52e2134e7884d261d7a5988e72f4` |
| transcript SHA256 | `b0b5c50f58a3d2e291c238f50fa8a2e0eddfe3f2627fc2de23e0c0f1f8b04939` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
| `Read` |
