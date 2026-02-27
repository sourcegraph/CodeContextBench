# ccx-explore-091-ds (mcp)

- Run: `ccb_mcp_platform_haiku_022126`
- Status: `passed`
- Reward: `0.9285`
- Audit JSON: [link](../audits/ccb_mcp_platform_haiku_022126--mcp--ccx-explore-091-ds.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 932.6 |
| Agent execution seconds | 865.1 |
| Input tokens | 1,139,575 |
| Output tokens | 72 |
| Cache tokens | 1,139,234 |
| Tool calls (total) | 15 |
| Tool calls (MCP) | 14 |
| Tool calls (local) | 1 |
| MCP ratio | 0.933 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `55ac853ab6d51e49f5d9575393c87baea825e05d608b29dbb1db6fbfa0c5d93d` |
| `trajectory.json` SHA256 | `232c1dcca32d08244d1fbc60672ec66c92acd5222f22fe60b1bb2d9529a73d2f` |
| transcript SHA256 | `b64a247cb7ffb39806178037b7ce684b05475c3e9001b95e741275774db1bc27` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_files` | 5 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
