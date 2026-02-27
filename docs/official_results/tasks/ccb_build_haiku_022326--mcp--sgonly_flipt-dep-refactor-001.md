# sgonly_flipt-dep-refactor-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.0300`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_flipt-dep-refactor-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_build_haiku_022326--mcp--sgonly_flipt-dep-refactor-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1502.6 |
| Agent execution seconds | 545.9 |
| Input tokens | 12,183,390 |
| Output tokens | 3,301 |
| Cache tokens | 12,182,139 |
| Tool calls (total) | 122 |
| Tool calls (MCP) | 51 |
| Tool calls (local) | 71 |
| MCP ratio | 0.418 |
| keyword_search calls | 3 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `4ab0b6f344436e5aa29a347c503a65287b7f9877f3356fc0533af7ba49be0304` |
| `trajectory.json` SHA256 | `0469bcf90b46ce4c66e77dace9c1c4d5b1800ddc52d37152c9f06fddc2b7cd33` |
| transcript SHA256 | `085da042240b9bcc52b303aefc7988717bc44341656038ef0b97b091198748a5` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 43 |
| `Bash` | 27 |
| `Read` | 24 |
| `Write` | 11 |
| `TodoWrite` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `Task` | 2 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Edit` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Bash` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
