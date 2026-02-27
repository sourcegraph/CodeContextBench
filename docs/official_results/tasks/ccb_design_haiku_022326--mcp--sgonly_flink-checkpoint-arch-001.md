# sgonly_flink-checkpoint-arch-001 (mcp-remote-direct)

- Run: `ccb_design_haiku_022326`
- Status: `passed`
- Reward: `0.7300`
- Audit JSON: [link](../audits/ccb_design_haiku_022326--mcp--sgonly_flink-checkpoint-arch-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_design_haiku_022326--mcp--sgonly_flink-checkpoint-arch-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 296.6 |
| Agent execution seconds | 113.0 |
| Input tokens | 2,862,635 |
| Output tokens | 99 |
| Cache tokens | 2,862,167 |
| Tool calls (total) | 24 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 1 |
| MCP ratio | 0.958 |
| keyword_search calls | 5 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `96d965a646947c297076893dd3bf626c98a7e4acb8a964f4cfffefc930463b2a` |
| `trajectory.json` SHA256 | `6025d4ac2a6166af76a1e56f7b58872c37e2b7aceb1780f9c7abcc80f704a6db` |
| transcript SHA256 | `9f671d7a803dae91aba55ef7564502aac3f5a6494f2a176fe94aa9a2fafb49f1` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 14 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
