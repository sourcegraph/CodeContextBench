# sgonly_envoy-routeconfig-dep-chain-001 (mcp)

- Run: `ccb_design_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_design_haiku_022326--mcp--sgonly_envoy-routeconfig-dep-chain-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 170.2 |
| Agent execution seconds | 67.6 |
| Input tokens | 1,158,068 |
| Output tokens | 490 |
| Cache tokens | 1,157,796 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 12 |
| Tool calls (local) | 2 |
| MCP ratio | 0.857 |
| keyword_search calls | 4 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b481eb5622eb299828559fbac600a6d62d0812e01b8f7d9e812b7fea6380ddf1` |
| `trajectory.json` SHA256 | `c140175eb5bfedf526e9e3a02b7dcb626a2203106d0a1ffc3eaf98238a7382dc` |
| transcript SHA256 | `814d811f9a7acb3b712c8001cdc895e892eb9439d8d028df80d8a990af4b6884` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
