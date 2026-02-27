# sgonly_ansible-module-respawn-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_ansible-module-respawn-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_ansible-module-respawn-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 2057.7 |
| Agent execution seconds | 1139.2 |
| Input tokens | 19,037,150 |
| Output tokens | 566 |
| Cache tokens | 19,035,828 |
| Tool calls (total) | 117 |
| Tool calls (MCP) | 34 |
| Tool calls (local) | 83 |
| MCP ratio | 0.291 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a1f4c1115828cbc0d6e28eda0d8648107f102e979fc2e9c245ef2d0b68e33206` |
| `trajectory.json` SHA256 | `24ac0504d858efba0a204d0595e0c2be98157f585618332478da4c40f205837e` |
| transcript SHA256 | `06ed858d536feb16cb50d6c480cf280d92494f2d74b565b66ca3d9cc5f25baf1` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 66 |
| `mcp__sourcegraph__sg_read_file` | 20 |
| `mcp__sourcegraph__sg_list_files` | 8 |
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `Read` | 4 |
| `Write` | 4 |
| `Edit` | 3 |
| `Task` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_repos` |
| `Bash` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
