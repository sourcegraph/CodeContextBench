# sgonly_strata-fx-european-refac-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.8000`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_strata-fx-european-refac-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_build_haiku_022326--mcp--sgonly_strata-fx-european-refac-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1067.1 |
| Agent execution seconds | 558.7 |
| Input tokens | 9,198,337 |
| Output tokens | 797 |
| Cache tokens | 9,197,698 |
| Tool calls (total) | 48 |
| Tool calls (MCP) | 15 |
| Tool calls (local) | 33 |
| MCP ratio | 0.312 |
| keyword_search calls | 8 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9c4ecfc64f2ef17164163083a4125f505e1a4f7d8996a33aa93e84a5c52b06e2` |
| `trajectory.json` SHA256 | `05471b4badd4972de57aafe8ec3691959df5416f50eae134f15d401e80c697df` |
| transcript SHA256 | `85e687f001ede84e8f88136bb066f94741039439c96024cc0314afa0dbadad3e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 24 |
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `Edit` | 2 |
| `TaskOutput` | 2 |
| `TodoWrite` | 2 |
| `Read` | 1 |
| `TaskStop` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
