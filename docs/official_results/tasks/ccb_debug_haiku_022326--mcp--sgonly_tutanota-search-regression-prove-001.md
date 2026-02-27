# sgonly_tutanota-search-regression-prove-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_tutanota-search-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_tutanota-search-regression-prove-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1131.5 |
| Agent execution seconds | 944.3 |
| Input tokens | 7,084,258 |
| Output tokens | 188 |
| Cache tokens | 7,083,375 |
| Tool calls (total) | 40 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 17 |
| MCP ratio | 0.575 |
| keyword_search calls | 8 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `97c5081c917ced785da1352554250f2cfe31932c1fd40c9d7f41a0a831f9da41` |
| `trajectory.json` SHA256 | `2a8fd65d05ddb41bcec9bb410bd471dbdca93e1204b51f9677e3a234a7d3c542` |
| transcript SHA256 | `dcdef712d76926a25545c937648e4567da1aa7ee0018ea60337e4f1727dc0c47` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 10 |
| `Bash` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `Write` | 6 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Read` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Edit` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Read` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
