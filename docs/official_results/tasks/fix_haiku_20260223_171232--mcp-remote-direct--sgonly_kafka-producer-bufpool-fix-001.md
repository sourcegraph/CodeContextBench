# sgonly_kafka-producer-bufpool-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `passed`
- Reward: `0.7800`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_kafka-producer-bufpool-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 317.6 |
| Agent execution seconds | 185.4 |
| Input tokens | 1,811,593 |
| Output tokens | 77 |
| Cache tokens | 1,811,250 |
| Tool calls (total) | 16 |
| Tool calls (MCP) | 15 |
| Tool calls (local) | 1 |
| MCP ratio | 0.938 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8c48767980b8a03fdf14010a73934f0b7c4a64b33e7ad347e34e3606a5a75c47` |
| `trajectory.json` SHA256 | `0ab290f35df4dc32087493539963b253f9b5bd0afbc7d56b780c1e80e6f19141` |
| transcript SHA256 | `b92f97408fd51c4aa6a964848f90ed1c3122b432a0c5f1746188e2b83f6c5c30` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 10 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
