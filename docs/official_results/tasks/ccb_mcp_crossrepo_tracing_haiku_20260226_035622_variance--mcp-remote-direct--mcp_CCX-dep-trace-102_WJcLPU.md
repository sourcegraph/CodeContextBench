# mcp_CCX-dep-trace-102_WJcLPU (mcp-remote-direct)

- Run: `ccb_mcp_crossrepo_tracing_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.8667`
- Audit JSON: [link](../audits/ccb_mcp_crossrepo_tracing_haiku_20260226_035622_variance--mcp-remote-direct--mcp_CCX-dep-trace-102_WJcLPU.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 765.3 |
| Agent execution seconds | 104.3 |
| Input tokens | 2,332,288 |
| Output tokens | 5,789 |
| Cache tokens | 2,331,800 |
| Tool calls (total) | 21 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 1 |
| MCP ratio | 0.952 |
| keyword_search calls | 6 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `27d354d6082bfac15808866943d623cfc389480cac820a42e52698db63f4e8d5` |
| `trajectory.json` SHA256 | `b7c7d5121b763db99d0789e2b76a56f5c67941209dfd508ecb7cf476e3746947` |
| transcript SHA256 | `d6a5bcb6c2fae6d79e9129f6571a9fdf02d2ee7167518319c1ea7f62617d6397` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
