# sgonly_django-rate-limit-design-001 (mcp)

- Run: `ccb_design_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_design_haiku_022326--mcp--sgonly_django-rate-limit-design-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_design_haiku_022326--mcp--sgonly_django-rate-limit-design-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1289.3 |
| Agent execution seconds | 133.7 |
| Input tokens | 2,254,657 |
| Output tokens | 161 |
| Cache tokens | 2,254,160 |
| Tool calls (total) | 21 |
| Tool calls (MCP) | 7 |
| Tool calls (local) | 14 |
| MCP ratio | 0.333 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9235e65a1114ad0a23f82774f079fb4cdbe639fb693c5ee3b15608a2f584c4f2` |
| `trajectory.json` SHA256 | `94d83a1e2c24be00582d4ea4c6d37ffa1fe12a1193a03c22228485b226f0819e` |
| transcript SHA256 | `0f3a7a1ad3619931ffc4bd19a14851d365ccf8b08b39794ee5b0d4777b773b15` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 11 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Glob` | 1 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Write` |
| `Glob` |
| `Bash` |
| `Bash` |
| `Bash` |
