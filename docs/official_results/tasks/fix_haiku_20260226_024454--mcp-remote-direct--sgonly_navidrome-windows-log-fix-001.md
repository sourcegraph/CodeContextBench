# sgonly_navidrome-windows-log-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260226_024454`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_navidrome-windows-log-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_navidrome-windows-log-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 613.7 |
| Agent execution seconds | 518.8 |
| Input tokens | 3,004,960 |
| Output tokens | 8,056 |
| Cache tokens | 3,004,282 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 8 |
| Tool calls (local) | 19 |
| MCP ratio | 0.286 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `522760170cac5c2da0c956ae60799ec759f231ef4f83e1fafb8657531fa752ae` |
| `trajectory.json` SHA256 | `e140011faa10ef5849a2aa037eecd6e245e8635f1a77f5402fe5ea18a3f5b951` |
| transcript SHA256 | `701bbe73a5fef169579c43a050ad4366431f7d5693d07f2dc54ad6aff48f205d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 15 |
| `Read` | 4 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `bash` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
