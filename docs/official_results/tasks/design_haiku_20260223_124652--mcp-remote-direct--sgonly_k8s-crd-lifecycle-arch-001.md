# sgonly_k8s-crd-lifecycle-arch-001 (mcp-remote-direct)

- Run: `design_haiku_20260223_124652`
- Status: `passed`
- Reward: `0.7700`
- Audit JSON: [link](../audits/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-crd-lifecycle-arch-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-crd-lifecycle-arch-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 281.6 |
| Agent execution seconds | 109.5 |
| Input tokens | 3,484,580 |
| Output tokens | 108 |
| Cache tokens | 3,483,894 |
| Tool calls (total) | 35 |
| Tool calls (MCP) | 29 |
| Tool calls (local) | 6 |
| MCP ratio | 0.829 |
| keyword_search calls | 11 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e8cf2e42c2495d15b56ba0a08479a50db28850663051ac9db8015592b7820f07` |
| `trajectory.json` SHA256 | `cfaf7afec0c474da66d69d2f6a633960eef6f34ed029ee0f86489365905a145f` |
| transcript SHA256 | `8e1ca060cbec663bb7f20de908629d7697d25a747a66b4d3c18468d2ca72e93e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `mcp__sourcegraph__sg_list_files` | 11 |
| `mcp__sourcegraph__sg_read_file` | 7 |
| `TodoWrite` | 5 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
