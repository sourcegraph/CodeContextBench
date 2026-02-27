# ccx-dep-trace-001 (mcp)

- Run: `ccb_mcp_crossrepo_tracing_haiku_022126`
- Status: `passed`
- Reward: `0.8235`
- Audit JSON: [link](../audits/ccb_mcp_crossrepo_tracing_haiku_022126--mcp--ccx-dep-trace-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1036.9 |
| Agent execution seconds | 824.2 |
| Input tokens | 583,308 |
| Output tokens | 35 |
| Cache tokens | 583,112 |
| Tool calls (total) | 7 |
| Tool calls (MCP) | 6 |
| Tool calls (local) | 1 |
| MCP ratio | 0.857 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `c650b1f7ff4a4c1f7048091f15c8d355a642947b6383b1d9d309bffba4882b0e` |
| `trajectory.json` SHA256 | `3e23c898f9cd0d7e6f205610c1382d8c64b829499ec8c9ab48c8c516715d4ef3` |
| transcript SHA256 | `dd264bcbb24a962971be6070ccbdfac7eca49b8348216c22d46e7106a89f84c6` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_files` | 4 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `Write` |
