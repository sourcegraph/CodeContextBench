# sgonly_docgen-runbook-002 (mcp-remote-direct)

- Run: `document_haiku_20260223_164240`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-runbook-002.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-runbook-002/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 200.4 |
| Agent execution seconds | 143.0 |
| Input tokens | 2,721,519 |
| Output tokens | 83 |
| Cache tokens | 2,720,904 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 24 |
| Tool calls (local) | 4 |
| MCP ratio | 0.857 |
| keyword_search calls | 11 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `ee415ac87eaf9b56aed59f9395b8f6760dfff5fbff39b19b38a49bf7b5770df8` |
| `trajectory.json` SHA256 | `5b8392fa89122767e7dd652f62ebedef44e8a76d58b110b1be4f6798b514b1fe` |
| transcript SHA256 | `1fa42aa800e81e6adf4d6fe36d9338535e90924c1f12b9f2710b32db2371325e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `TodoWrite` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
