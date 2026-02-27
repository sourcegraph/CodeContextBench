# sgonly_ansible-abc-imports-fix-001 (mcp)

- Run: `ccb_fix_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_ansible-abc-imports-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1386.0 |
| Agent execution seconds | 1135.3 |
| Input tokens | 7,727,552 |
| Output tokens | 303 |
| Cache tokens | 7,726,565 |
| Tool calls (total) | 77 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 54 |
| MCP ratio | 0.299 |
| keyword_search calls | 4 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9ca552360f617e7e6f1faada441465a6190830a37ab9ebf463654f480873056f` |
| `trajectory.json` SHA256 | `78ae74302d53b45f258b12e1e58849fa63fa5316c555eecf60812339f61b8795` |
| transcript SHA256 | `0dafe5006620624443f2669acff293b8e399235945ce179299b04cf705eb955b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 28 |
| `Read` | 13 |
| `mcp__sourcegraph__sg_keyword_search` | 9 |
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `Edit` | 4 |
| `Grep` | 3 |
| `mcp__sourcegraph__sg_nls_search` | 3 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Task` | 1 |
| `mcp__sourcegraph__sg_diff_search` | 1 |
| `mcp__sourcegraph__sg_find_references` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `Task` |
| `Grep` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
