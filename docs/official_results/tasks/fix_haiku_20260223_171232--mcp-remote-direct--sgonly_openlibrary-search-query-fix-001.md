# sgonly_openlibrary-search-query-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 942.6 |
| Agent execution seconds | 816.4 |
| Input tokens | 25,177,048 |
| Output tokens | 575 |
| Cache tokens | 25,175,990 |
| Tool calls (total) | 111 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 94 |
| MCP ratio | 0.153 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `657d18697bcc356ef2f775def486825015f5e430ad6b56740f1f1502a2eb3bda` |
| `trajectory.json` SHA256 | `e1b27086f8320d34293ba23bedefb829d897859d18b7cb431a00aa62d2e91536` |
| transcript SHA256 | `03a8cddbbccee48057ff6669b106485664afdf0115cf53f5d2857239424eff43` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 50 |
| `Edit` | 18 |
| `Write` | 15 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `Read` | 7 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
