# sgonly_django-modelchoice-fk-fix-001 (mcp)

- Run: `ccb_fix_haiku_022326`
- Status: `passed`
- Reward: `0.4500`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_django-modelchoice-fk-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1053.5 |
| Agent execution seconds | 531.1 |
| Input tokens | 11,478,604 |
| Output tokens | 311 |
| Cache tokens | 11,477,318 |
| Tool calls (total) | 58 |
| Tool calls (MCP) | 38 |
| Tool calls (local) | 20 |
| MCP ratio | 0.655 |
| keyword_search calls | 11 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `352acc446fd0f6a2132e31f259fd3055ab8e4dfa75531114e321680d9da1e9f7` |
| `trajectory.json` SHA256 | `2cff8e1cefd1e878fa6de8ae6c20c4845b94af80f8d48feb8550e5bc79f90f3b` |
| transcript SHA256 | `13ec5afbcf7691b1e7c9c098657bd3401dcfbb87bf28300987e632069a0e6411` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 22 |
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `Bash` | 10 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Write` | 4 |
| `TodoWrite` | 3 |
| `Task` | 2 |
| `Read` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `mcp__sourcegraph__sg_keyword_search` |
