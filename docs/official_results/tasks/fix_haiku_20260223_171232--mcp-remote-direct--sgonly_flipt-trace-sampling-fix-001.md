# sgonly_flipt-trace-sampling-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `passed`
- Reward: `0.9845`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-trace-sampling-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 2096.1 |
| Agent execution seconds | 1444.6 |
| Input tokens | 24,433,496 |
| Output tokens | 707 |
| Cache tokens | 24,432,675 |
| Tool calls (total) | 135 |
| Tool calls (MCP) | 16 |
| Tool calls (local) | 117 |
| MCP ratio | 0.119 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b8537526a377b45a16076ce00dbac5615baf5663d731a467c95b4a9aa0b78bb3` |
| `trajectory.json` SHA256 | `ac2421c40955b0d35fa8364eb5f25668e3e6a20d67a359112fc7c3232b39be97` |
| transcript SHA256 | `d5d9fa98b9a6376474a3853174726bcde61a6a4cc92bb158d1360216c46881ed` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 78 |
| `Read` | 16 |
| `Edit` | 14 |
| `mcp__sourcegraph__sg_read_file` | 10 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `TaskOutput` | 3 |
| `bash` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `TaskStop` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `TaskOutput` |
