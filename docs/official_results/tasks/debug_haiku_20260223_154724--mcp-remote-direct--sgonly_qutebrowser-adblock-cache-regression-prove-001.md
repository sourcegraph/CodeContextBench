# sgonly_qutebrowser-adblock-cache-regression-prove-001 (mcp-remote-direct)

- Run: `debug_haiku_20260223_154724`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_qutebrowser-adblock-cache-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_qutebrowser-adblock-cache-regression-prove-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 391.2 |
| Agent execution seconds | 297.7 |
| Input tokens | 8,335,894 |
| Output tokens | 279 |
| Cache tokens | 8,334,748 |
| Tool calls (total) | 53 |
| Tool calls (MCP) | 11 |
| Tool calls (local) | 42 |
| MCP ratio | 0.208 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `275b85fb65bfdaacace895bd40d1be9f3cd941a5a2339012a9fb2f05596486e4` |
| `trajectory.json` SHA256 | `7ddbaa5edbcfc04cea19b5a756572830ce1fe60e5816f2c2043d744b866b1a7e` |
| transcript SHA256 | `06019f31646b06868b0ecf6935588ebadb982116da7c28195dd9c74ddf1c2bbb` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 37 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `Write` | 4 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Read` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
| `Bash` |
| `Bash` |
