# ccx-dep-trace-004 (mcp)

- Run: `ccb_mcp_crossrepo_tracing_haiku_022126`
- Status: `passed`
- Reward: `0.8750`
- Audit JSON: [link](../audits/ccb_mcp_crossrepo_tracing_haiku_022126--mcp--ccx-dep-trace-004.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1430.3 |
| Agent execution seconds | 1215.7 |
| Input tokens | 1,806,460 |
| Output tokens | 83 |
| Cache tokens | 1,806,062 |
| Tool calls (total) | 16 |
| Tool calls (MCP) | 14 |
| Tool calls (local) | 2 |
| MCP ratio | 0.875 |
| keyword_search calls | 0 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `256273d0b651da9b9a614aac6f03761e0ba12541faded656d35419cb5c72b1b9` |
| `trajectory.json` SHA256 | `7689958b5da13eaaa64a545a80bb0adeb293326132969f85c12e33067a9d3f1c` |
| transcript SHA256 | `bfe0d369f5fef07780dbfe3645ae8e8e01916e25defd9382897bfe00bb1121ee` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 6 |
| `mcp__sourcegraph__sg_find_references` | 3 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_find_references` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_find_references` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
