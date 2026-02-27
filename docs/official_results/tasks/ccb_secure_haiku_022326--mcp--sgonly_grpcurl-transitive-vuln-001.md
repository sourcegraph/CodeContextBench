# sgonly_grpcurl-transitive-vuln-001 (mcp)

- Run: `ccb_secure_haiku_022326`
- Status: `passed`
- Reward: `0.6700`
- Audit JSON: [link](../audits/ccb_secure_haiku_022326--mcp--sgonly_grpcurl-transitive-vuln-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 146.0 |
| Agent execution seconds | 85.5 |
| Input tokens | 2,434,268 |
| Output tokens | 106 |
| Cache tokens | 2,433,739 |
| Tool calls (total) | 21 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 1 |
| MCP ratio | 0.952 |
| keyword_search calls | 6 |
| nls_search calls | 3 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `875d53cd0e9f9f5e8eac0c6fc1625b7b166650a990cf36a80e4eb46139be9839` |
| `trajectory.json` SHA256 | `a4ea9b4b2b08de78358ce5a7ba49c5b6f57c2f54c0a903c8de618d596b1a9b9c` |
| transcript SHA256 | `3a2ed8e41a5be0de55fbf6632f9f75d17644e84bdd9a506a3730a86e760c18c7` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `mcp__sourcegraph__sg_nls_search` | 3 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
