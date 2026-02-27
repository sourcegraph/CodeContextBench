# sgonly_k8s-score-normalizer-refac-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.7800`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_k8s-score-normalizer-refac-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_build_haiku_022326--mcp--sgonly_k8s-score-normalizer-refac-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 839.2 |
| Agent execution seconds | 310.2 |
| Input tokens | 7,260,801 |
| Output tokens | 252 |
| Cache tokens | 7,259,857 |
| Tool calls (total) | 39 |
| Tool calls (MCP) | 15 |
| Tool calls (local) | 24 |
| MCP ratio | 0.385 |
| keyword_search calls | 6 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `cdb06a740570ac3a7ce14933bff0ec629b00ff56c4f1f3f916101552e33d77b1` |
| `trajectory.json` SHA256 | `3154ff9ecdbc456c5b91d7024d1507672e4916dc14d8cebebc256f73fb9b35dd` |
| transcript SHA256 | `98276cdc748f6876f3287c87b188c784447e650c148f48ffa21341eea0c2ee09` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 14 |
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `TodoWrite` | 4 |
| `Edit` | 2 |
| `Read` | 2 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
