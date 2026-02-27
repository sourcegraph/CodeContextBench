# sgonly_terraform-phantom-update-debug-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.9300`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_terraform-phantom-update-debug-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_terraform-phantom-update-debug-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 226.6 |
| Agent execution seconds | 144.6 |
| Input tokens | 5,299,909 |
| Output tokens | 178 |
| Cache tokens | 5,299,110 |
| Tool calls (total) | 33 |
| Tool calls (MCP) | 31 |
| Tool calls (local) | 2 |
| MCP ratio | 0.939 |
| keyword_search calls | 11 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `ba816d1229b8bd987eaeed870852d0f21e3097a3a1437dbfcc6797cbcf66d0a0` |
| `trajectory.json` SHA256 | `39e4bf824d574b241ddfd443f1f780fbc38ca7296cec2a760df8b3f1f67e8fe6` |
| transcript SHA256 | `6e5c62d0afc39015ca30d45b4a3aa391c5446a3d6081b7fa5b3d0c02e5943eca` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 17 |
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Bash` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
