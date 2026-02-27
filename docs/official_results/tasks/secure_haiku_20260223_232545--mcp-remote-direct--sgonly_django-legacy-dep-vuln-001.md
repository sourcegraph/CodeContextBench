# sgonly_django-legacy-dep-vuln-001 (mcp-remote-direct)

- Run: `secure_haiku_20260223_232545`
- Status: `passed`
- Reward: `0.6500`
- Audit JSON: [link](../audits/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_django-legacy-dep-vuln-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 395.8 |
| Agent execution seconds | 234.0 |
| Input tokens | 7,799,527 |
| Output tokens | 249 |
| Cache tokens | 7,798,724 |
| Tool calls (total) | 44 |
| Tool calls (MCP) | 10 |
| Tool calls (local) | 34 |
| MCP ratio | 0.227 |
| keyword_search calls | 2 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `0a0d8e1303cf119917a0f401534580d3d42e55252dae9412cbf3e0e6379e0af8` |
| `trajectory.json` SHA256 | `e759a2f7bea130704f7885e03f9aa79effdb9babfe06b397aa87b73c20554978` |
| transcript SHA256 | `588edb855b8e83db84ae098aef0018b524c40203b392cee7953afcbc0b4c6bd3` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 24 |
| `Read` | 4 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Edit` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Bash` |
| `TodoWrite` |
