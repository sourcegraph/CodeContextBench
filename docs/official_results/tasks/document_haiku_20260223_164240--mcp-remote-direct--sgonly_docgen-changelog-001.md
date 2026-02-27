# sgonly_docgen-changelog-001 (mcp-remote-direct)

- Run: `document_haiku_20260223_164240`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-changelog-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-changelog-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 157.6 |
| Agent execution seconds | 88.9 |
| Input tokens | 3,084,091 |
| Output tokens | 136 |
| Cache tokens | 3,083,400 |
| Tool calls (total) | 38 |
| Tool calls (MCP) | 35 |
| Tool calls (local) | 3 |
| MCP ratio | 0.921 |
| keyword_search calls | 4 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `34261f963ee29fd7cf61f9735d48bc926da57f71646d7a91b28d300f920a5a5a` |
| `trajectory.json` SHA256 | `3f4b20ecbd93d0e4ab5b66141b82a8db029fbb131c9b58acfc8558973f77af1e` |
| transcript SHA256 | `d591e7c742d21e546f948b8661674dcd7f764ff8c924192b7479517159dc1096` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 22 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Read` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |
| `mcp__sourcegraph__sg_diff_search` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_commit_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_diff_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
