# sgonly_test-coverage-gap-002 (mcp)

- Run: `ccb_test_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_test_haiku_022326--mcp--sgonly_test-coverage-gap-002.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 217.9 |
| Agent execution seconds | 106.9 |
| Input tokens | 2,787,860 |
| Output tokens | 74 |
| Cache tokens | 2,787,300 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 27 |
| Tool calls (local) | 1 |
| MCP ratio | 0.964 |
| keyword_search calls | 5 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b95e0f4ceead4e2464b2cbc114add023b28e7a934774a43e708d19d7b5bab4a4` |
| `trajectory.json` SHA256 | `dfdf5e20df85a7eb23cbb59ffa780b5a2fafa560fde263237b79a09932c8bad9` |
| transcript SHA256 | `c76c1937de42bd9d28686ef43551b895cba22303a5590f6bfbb10fa5481fe593` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
