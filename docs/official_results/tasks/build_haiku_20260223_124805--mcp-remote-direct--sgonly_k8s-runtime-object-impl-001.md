# sgonly_k8s-runtime-object-impl-001 (mcp-remote-direct)

- Run: `build_haiku_20260223_124805`
- Status: `passed`
- Reward: `0.1200`
- Audit JSON: [link](../audits/build_haiku_20260223_124805--mcp-remote-direct--sgonly_k8s-runtime-object-impl-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/build_haiku_20260223_124805--mcp-remote-direct--sgonly_k8s-runtime-object-impl-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 341.9 |
| Agent execution seconds | 242.9 |
| Input tokens | 3,579,196 |
| Output tokens | 98 |
| Cache tokens | 3,578,651 |
| Tool calls (total) | 77 |
| Tool calls (MCP) | 64 |
| Tool calls (local) | 13 |
| MCP ratio | 0.831 |
| keyword_search calls | 4 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `dce50fba947d3fd9860d184c7f885157ba9995f9a26c80a713a1fd2866d1587f` |
| `trajectory.json` SHA256 | `484547a27c8bcdad0315b0988fd1880cffaa2d6217edb867e349e9603c858cc4` |
| transcript SHA256 | `c1b3f13abb98f7271454327962e6a2a57a3f6a7b3f064c0c942b09d708e8f6c7` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 24 |
| `mcp__sourcegraph__sg_keyword_search` | 20 |
| `mcp__sourcegraph__sg_list_files` | 10 |
| `Bash` | 8 |
| `mcp__sourcegraph__sg_nls_search` | 7 |
| `mcp__sourcegraph__sg_list_repos` | 3 |
| `Grep` | 2 |
| `Task` | 2 |
| `Glob` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `Task` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
