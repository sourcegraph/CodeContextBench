# sgonly_strata-cds-tranche-feat-001 (mcp-remote-direct)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.2800`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_strata-cds-tranche-feat-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_build_haiku_022326--mcp--sgonly_strata-cds-tranche-feat-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 987.9 |
| Agent execution seconds | 315.8 |
| Input tokens | 4,106,610 |
| Output tokens | 11,034 |
| Cache tokens | 4,106,076 |
| Tool calls (total) | 30 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 13 |
| MCP ratio | 0.567 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `2678ae1a1ddf27d5bf60e8459bc5abbc5eda2b9c3e503df3f9139184f7ed105a` |
| `trajectory.json` SHA256 | `77596bef8dff3d011ee9276a333a3a393df76861346b53b120931db60e776c9c` |
| transcript SHA256 | `dbf2ce1a3baa3b94a4103813e73f9c44ddb92ba59b70cb258c6cb917972e8af0` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 8 |
| `Write` | 7 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `Bash` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Edit` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
