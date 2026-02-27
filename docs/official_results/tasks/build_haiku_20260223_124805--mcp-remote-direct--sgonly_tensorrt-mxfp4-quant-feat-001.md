# sgonly_tensorrt-mxfp4-quant-feat-001 (mcp-remote-direct)

- Run: `build_haiku_20260223_124805`
- Status: `passed`
- Reward: `0.7000`
- Audit JSON: [link](../audits/build_haiku_20260223_124805--mcp-remote-direct--sgonly_tensorrt-mxfp4-quant-feat-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 863.8 |
| Agent execution seconds | 354.5 |
| Input tokens | 7,485,022 |
| Output tokens | 223 |
| Cache tokens | 7,484,089 |
| Tool calls (total) | 41 |
| Tool calls (MCP) | 22 |
| Tool calls (local) | 19 |
| MCP ratio | 0.537 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e88ba2db857f52ac9f72065667964c1fd53be65c37f99dc95a87e657820e1c9f` |
| `trajectory.json` SHA256 | `4ad69ce9acd09909bca9e630e72df632e165b81d2c4eebaaec0922701e3d80bc` |
| transcript SHA256 | `8ba77fbe43a48da6dea96d04f55d86269e2e1d711ef91bf822ae65650219fb59` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 15 |
| `Write` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `TodoWrite` | 5 |
| `Bash` | 4 |
| `Read` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
