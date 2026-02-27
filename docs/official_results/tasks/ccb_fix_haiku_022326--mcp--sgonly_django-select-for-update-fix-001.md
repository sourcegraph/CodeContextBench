# sgonly_django-select-for-update-fix-001 (mcp)

- Run: `ccb_fix_haiku_022326`
- Status: `passed`
- Reward: `0.7800`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_django-select-for-update-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_fix_haiku_022326--mcp--sgonly_django-select-for-update-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 257.3 |
| Agent execution seconds | 134.5 |
| Input tokens | 5,337,206 |
| Output tokens | 198 |
| Cache tokens | 5,336,426 |
| Tool calls (total) | 38 |
| Tool calls (MCP) | 27 |
| Tool calls (local) | 11 |
| MCP ratio | 0.711 |
| keyword_search calls | 12 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8dfb232448d64ed86ff4fba9065afb76a08903268003373d14d608e4a97b1738` |
| `trajectory.json` SHA256 | `e9a38bf7b81601ee759b6032faedf6facce4b95f99cc8bf9418e83738c7fa5e1` |
| transcript SHA256 | `55ac67d9ccd7a8054bc485002f7d12812a6f073efa027e540fe8d0a685f5e4d8` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 13 |
| `mcp__sourcegraph__sg_keyword_search` | 12 |
| `Bash` | 4 |
| `Edit` | 2 |
| `Grep` | 2 |
| `Read` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Grep` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
