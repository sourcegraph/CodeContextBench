# sgonly_test-integration-002 (mcp-remote-direct)

- Run: `ccb_test_haiku_20260226_015500_backfill`
- Status: `passed`
- Reward: `0.9000`
- Audit JSON: [link](../audits/ccb_test_haiku_20260226_015500_backfill--mcp-remote-direct--sgonly_test-integration-002.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_test_haiku_20260226_015500_backfill--mcp-remote-direct--sgonly_test-integration-002/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 119.1 |
| Agent execution seconds | 78.0 |
| Input tokens | 2,899,536 |
| Output tokens | 60 |
| Cache tokens | 2,898,994 |
| Tool calls (total) | 27 |
| Tool calls (MCP) | 21 |
| Tool calls (local) | 6 |
| MCP ratio | 0.778 |
| keyword_search calls | 6 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `511535f56e1514703179ee8657d8f95354609074f2f9951e5a9d8929d20b2bf2` |
| `trajectory.json` SHA256 | `5d2a2b03d52763b75b2d7e72d82701139fdb9d60b3beac476f3d91a004bdd340` |
| transcript SHA256 | `ec49f4c985ba7018fd3fe4b0357df05043a68ccae2b6fa1f3e60cdce00382e8c` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 12 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `Bash` | 3 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Read` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
