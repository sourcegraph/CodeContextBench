# sgonly_flipt-transitive-deps-001 (mcp)

- Run: `ccb_design_haiku_022326`
- Status: `passed`
- Reward: `0.7111`
- Audit JSON: [link](../audits/ccb_design_haiku_022326--mcp--sgonly_flipt-transitive-deps-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 387.5 |
| Agent execution seconds | 175.6 |
| Input tokens | 4,647,160 |
| Output tokens | 245 |
| Cache tokens | 4,646,362 |
| Tool calls (total) | 39 |
| Tool calls (MCP) | 37 |
| Tool calls (local) | 2 |
| MCP ratio | 0.949 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9035398a3b0341a9f2a4887f642c44663774b6ac4987c7fefa81008de45e5610` |
| `trajectory.json` SHA256 | `d4273f2e0f0270bd1062970e969335696d899240f73f45db5d325691434db1ce` |
| transcript SHA256 | `a66f24bbf7374f05146978e3944b2007d70658e370f3d1a65b9322b77c35a301` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 20 |
| `mcp__sourcegraph__sg_list_files` | 12 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `Read` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
