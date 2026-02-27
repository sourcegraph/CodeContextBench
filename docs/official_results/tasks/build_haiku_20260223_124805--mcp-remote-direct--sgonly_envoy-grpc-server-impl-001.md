# sgonly_envoy-grpc-server-impl-001 (mcp-remote-direct)

- Run: `build_haiku_20260223_124805`
- Status: `passed`
- Reward: `0.4400`
- Audit JSON: [link](../audits/build_haiku_20260223_124805--mcp-remote-direct--sgonly_envoy-grpc-server-impl-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 260.2 |
| Agent execution seconds | 89.3 |
| Input tokens | 4,383,580 |
| Output tokens | 101 |
| Cache tokens | 4,382,886 |
| Tool calls (total) | 32 |
| Tool calls (MCP) | 30 |
| Tool calls (local) | 2 |
| MCP ratio | 0.938 |
| keyword_search calls | 16 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `38adc34c0c10b4f6d4435adcf6e93ba1b56d86cd2b9162ab5fb3a2e045559fbe` |
| `trajectory.json` SHA256 | `4fbac3b956d842816a6eabc0b7668995c955fdb63aa3c39da626ce60e4b88f31` |
| transcript SHA256 | `e410f942d871aab86f4cc0dacdd06afba6a786c4aeceae1f9619932e6f3f5c8a` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 16 |
| `mcp__sourcegraph__sg_read_file` | 10 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_go_to_definition` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
