# sgonly_ghost-code-review-001 (mcp-remote-direct)

- Run: `test_haiku_20260224_011816`
- Status: `passed`
- Reward: `0.6200`
- Audit JSON: [link](../audits/test_haiku_20260224_011816--mcp-remote-direct--sgonly_ghost-code-review-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 536.5 |
| Agent execution seconds | 351.2 |
| Input tokens | 3,613,891 |
| Output tokens | 118 |
| Cache tokens | 3,613,297 |
| Tool calls (total) | 23 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 3 |
| MCP ratio | 0.870 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `81704926ca1da648d9075b6e87613ace2318505070e5322b41f19b43a08d87c4` |
| `trajectory.json` SHA256 | `5322c8c54948f63ef989fac6ba35583357dbdca3bf77e37720e140884affd579` |
| transcript SHA256 | `82cde015e926efc1b31320787fd2ab71b907573f8fa7128ea082cd137d667956` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 11 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Bash` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
