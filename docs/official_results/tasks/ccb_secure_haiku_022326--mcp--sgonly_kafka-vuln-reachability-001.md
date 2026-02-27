# sgonly_kafka-vuln-reachability-001 (mcp)

- Run: `ccb_secure_haiku_022326`
- Status: `passed`
- Reward: `0.9200`
- Audit JSON: [link](../audits/ccb_secure_haiku_022326--mcp--sgonly_kafka-vuln-reachability-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 215.3 |
| Agent execution seconds | 147.6 |
| Input tokens | 2,547,431 |
| Output tokens | 82 |
| Cache tokens | 2,546,912 |
| Tool calls (total) | 18 |
| Tool calls (MCP) | 12 |
| Tool calls (local) | 6 |
| MCP ratio | 0.667 |
| keyword_search calls | 6 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8cc737284983ce2eba2c234e4a8e1760e6996ef46775e588074c01bb290b4ccd` |
| `trajectory.json` SHA256 | `000cbb0f5f9732f70731ba6260f9788efbfd71c87c6f2906d658ee3b788bfa6c` |
| transcript SHA256 | `e1d95afa017e79adc1c3d99737e077ea14c139cf59931e5c1aa86c4b0d372fd1` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `mcp__sourcegraph__sg_read_file` | 6 |
| `TodoWrite` | 5 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
