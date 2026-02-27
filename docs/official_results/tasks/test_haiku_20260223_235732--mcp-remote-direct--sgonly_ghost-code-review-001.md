# sgonly_ghost-code-review-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `passed`
- Reward: `0.8800`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_ghost-code-review-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 499.8 |
| Agent execution seconds | 271.6 |
| Input tokens | 1,429,634 |
| Output tokens | 45 |
| Cache tokens | 1,429,366 |
| Tool calls (total) | 10 |
| Tool calls (MCP) | 8 |
| Tool calls (local) | 2 |
| MCP ratio | 0.800 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `c22310242651911368b88adbc1cbeceb36d63ea3066c952ca88e64af5546f8cc` |
| `trajectory.json` SHA256 | `09c080625ef80d15208fff7b0f37229011596dc6b4e89f77542cdc363e839a2c` |
| transcript SHA256 | `6320eef27062a14413f00f7111a2b4ba9e8005ef12d4deae8c84b1153d6fe68f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Bash` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
