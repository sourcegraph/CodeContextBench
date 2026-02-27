# sgonly_envoy-code-review-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `passed`
- Reward: `0.6700`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_envoy-code-review-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/test_haiku_20260223_235732--mcp-remote-direct--sgonly_envoy-code-review-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 457.3 |
| Agent execution seconds | 238.9 |
| Input tokens | 1,991,071 |
| Output tokens | 96 |
| Cache tokens | 1,990,722 |
| Tool calls (total) | 16 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 3 |
| MCP ratio | 0.812 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `d7aba18565fa99c41504de7b29105e983f222f80eb6f4a270f9a7feaea4b760a` |
| `trajectory.json` SHA256 | `f35963bb7bfb560a318e9247a13d955df94b166d837cea003a3bd0b359deb5d9` |
| transcript SHA256 | `990aa71e6ce32234e77f08af54f9927496fcc7a22787403b632a61421d96a05a` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Grep` | 1 |
| `Read` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Read` |
| `Grep` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
