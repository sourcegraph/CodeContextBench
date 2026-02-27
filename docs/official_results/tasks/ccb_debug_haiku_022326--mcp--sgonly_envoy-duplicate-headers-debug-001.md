# sgonly_envoy-duplicate-headers-debug-001 (mcp)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.9200`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_envoy-duplicate-headers-debug-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_envoy-duplicate-headers-debug-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 290.6 |
| Agent execution seconds | 221.2 |
| Input tokens | 5,114,024 |
| Output tokens | 149 |
| Cache tokens | 5,113,352 |
| Tool calls (total) | 32 |
| Tool calls (MCP) | 30 |
| Tool calls (local) | 2 |
| MCP ratio | 0.938 |
| keyword_search calls | 10 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `89f3c8804a67e63a428f81b9d2140158777b52f488a9c7009d51dbe679612a34` |
| `trajectory.json` SHA256 | `50c4d6673d93339ffa60321fe74f578b761235ca58da87dd4c09e86ba0f56845` |
| transcript SHA256 | `3b3a3f7cd1b7943f95c35197b5e4e3623c8d6abadab81a7b7724c9c3e011850b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 10 |
| `mcp__sourcegraph__sg_grep` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Grep` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
