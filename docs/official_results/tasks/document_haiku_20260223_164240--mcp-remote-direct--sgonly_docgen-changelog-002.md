# sgonly_docgen-changelog-002 (mcp-remote-direct)

- Run: `document_haiku_20260223_164240`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-changelog-002.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/document_haiku_20260223_164240--mcp-remote-direct--sgonly_docgen-changelog-002/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 141.2 |
| Agent execution seconds | 95.5 |
| Input tokens | 2,614,129 |
| Output tokens | 85 |
| Cache tokens | 2,613,673 |
| Tool calls (total) | 22 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 2 |
| MCP ratio | 0.909 |
| keyword_search calls | 4 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `4a899c67b393d18ffb15cd2be228c78d792be2e7327606932eb896d855dc1c8d` |
| `trajectory.json` SHA256 | `30106d0f015db6abd70eac36edfb5c3e3a65380712af10a90199947775f60251` |
| transcript SHA256 | `70d838d8145dd9aa12a56970920823f50134d79f24dbeb14e6ff97863c92196d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |
| `mcp__sourcegraph__sg_compare_revisions` | 1 |
| `mcp__sourcegraph__sg_diff_search` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_commit_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
