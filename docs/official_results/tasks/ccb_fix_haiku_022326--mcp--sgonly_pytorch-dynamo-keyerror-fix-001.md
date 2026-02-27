# sgonly_pytorch-dynamo-keyerror-fix-001 (mcp-remote-direct)

- Run: `ccb_fix_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_pytorch-dynamo-keyerror-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_fix_haiku_022326--mcp--sgonly_pytorch-dynamo-keyerror-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 578.9 |
| Agent execution seconds | 245.1 |
| Input tokens | 11,801,061 |
| Output tokens | 259 |
| Cache tokens | 11,800,462 |
| Tool calls (total) | 56 |
| Tool calls (MCP) | 35 |
| Tool calls (local) | 20 |
| MCP ratio | 0.625 |
| keyword_search calls | 6 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `55790d6c0d4163a93718c05900d9e0da12347438f7480674fc6d28aba55b1c2a` |
| `trajectory.json` SHA256 | `39f4c7e2f72b5b5a2b8acf9589247426bb05d830bfeb18f68d0bdc30075ffb6a` |
| transcript SHA256 | `a4c58c851d1d3abccb9adf16ff9cab545813424c902dc87fc3a85b9386607693` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 21 |
| `Bash` | 14 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_commit_search` | 2 |
| `mcp__sourcegraph__sg_compare_revisions` | 2 |
| `bash` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
