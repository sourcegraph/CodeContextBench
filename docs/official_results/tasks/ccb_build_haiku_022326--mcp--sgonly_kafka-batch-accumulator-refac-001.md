# sgonly_kafka-batch-accumulator-refac-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.6800`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_kafka-batch-accumulator-refac-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 2587.8 |
| Agent execution seconds | 262.6 |
| Input tokens | 2,561,915 |
| Output tokens | 94 |
| Cache tokens | 2,561,486 |
| Tool calls (total) | 15 |
| Tool calls (MCP) | 5 |
| Tool calls (local) | 10 |
| MCP ratio | 0.333 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9a5aebe5adb80bd1e3d8619ad0156f9a00de54f974f4ce130b966b8170e13188` |
| `trajectory.json` SHA256 | `44ef457792ff149efe53311b04ff4eaab2b30b9c3fbc701639865527f74bff5f` |
| transcript SHA256 | `fdd5803e7a135112e46a9b68295cf600cf57d94c5431b094451273a8006cb50d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 4 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Read` | 1 |
| `TaskOutput` | 1 |
| `TaskStop` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `TodoWrite` |
| `Bash` |
| `TaskOutput` |
| `TaskStop` |
| `Bash` |
