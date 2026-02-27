# sgonly_docgen-runbook-001 (mcp)

- Run: `ccb_document_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_document_haiku_022326--mcp--sgonly_docgen-runbook-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_document_haiku_022326--mcp--sgonly_docgen-runbook-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 184.7 |
| Agent execution seconds | 122.5 |
| Input tokens | 2,399,690 |
| Output tokens | 65 |
| Cache tokens | 2,399,241 |
| Tool calls (total) | 22 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 5 |
| MCP ratio | 0.773 |
| keyword_search calls | 8 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a589f4d2bcb95c3a26d713a17645bf9a31144b482b40364bce2465126297527c` |
| `trajectory.json` SHA256 | `9cba68a9e7ec5c53f0d314692da9ef4543a841a2b42e685394472abaaffd05ab` |
| transcript SHA256 | `b536400a6f365ada2293e10ab4b104a4645224f29ac7c71dba6f27759e1c30c6` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `TodoWrite` | 4 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
