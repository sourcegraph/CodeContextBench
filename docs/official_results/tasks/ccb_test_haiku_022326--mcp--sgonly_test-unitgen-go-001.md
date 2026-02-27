# sgonly_test-unitgen-go-001 (mcp)

- Run: `ccb_test_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_022326--mcp--sgonly_test-unitgen-go-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 157.1 |
| Agent execution seconds | 99.8 |
| Input tokens | 1,869,857 |
| Output tokens | 61 |
| Cache tokens | 1,869,467 |
| Tool calls (total) | 16 |
| Tool calls (MCP) | 5 |
| Tool calls (local) | 11 |
| MCP ratio | 0.312 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `1f801689a1aadad3843fed569cc1ab532096429eb3b27ddbaef6f15abc579503` |
| `trajectory.json` SHA256 | `9fb215322fe668c46cf5a4af11077107aeff79f54faf474fd02c31031bc298c0` |
| transcript SHA256 | `cd3c7cd91c27cb51c8179485d8219921bdae3ad26353617519a8e5242b5c57fd` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 9 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
