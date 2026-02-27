# sgonly_envoy-filter-chain-qa-001 (mcp)

- Run: `ccb_understand_haiku_022426`
- Status: `passed`
- Reward: `0.8800`
- Audit JSON: [link](../audits/ccb_understand_haiku_022426--mcp--sgonly_envoy-filter-chain-qa-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_understand_haiku_022426--mcp--sgonly_envoy-filter-chain-qa-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 291.4 |
| Agent execution seconds | 89.7 |
| Input tokens | 3,720,134 |
| Output tokens | 78 |
| Cache tokens | 3,719,508 |
| Tool calls (total) | 30 |
| Tool calls (MCP) | 29 |
| Tool calls (local) | 1 |
| MCP ratio | 0.967 |
| keyword_search calls | 11 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `fb9ca5ebac4b772b213d147a7ddeb34ff3b6fdff2f4dbc67fc5eefb4ad547ef3` |
| `trajectory.json` SHA256 | `9da9e3a5697db060306f83cec0c38be0cfd7878ea227fd412c5eef20b1466d66` |
| transcript SHA256 | `9f92e6e1b8f6a7f1015fbac1d9a7255fdeb8a6ad9254398928e199bfd7cc6d0c` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
