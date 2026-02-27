# sgonly_flipt-flagexists-refactor-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.7500`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_flipt-flagexists-refactor-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_build_haiku_022326--mcp--sgonly_flipt-flagexists-refactor-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1751.3 |
| Agent execution seconds | 1021.2 |
| Input tokens | 13,478,836 |
| Output tokens | 7,411 |
| Cache tokens | 13,477,667 |
| Tool calls (total) | 71 |
| Tool calls (MCP) | 25 |
| Tool calls (local) | 46 |
| MCP ratio | 0.352 |
| keyword_search calls | 5 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `9a706465e4c57d2310bdc6d6dd06c11b793ac3cd424be4f0b2557d0f3381a758` |
| `trajectory.json` SHA256 | `c8f9daeb78e8b176a77ca91b1d7c77cea7af1bce0c5aead400acdb6d6b39d4d8` |
| transcript SHA256 | `92095831683b0fe7c32acc43124d712392802fd0d93c5a1479bda70f7e938d94` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 25 |
| `mcp__sourcegraph__sg_read_file` | 14 |
| `TodoWrite` | 7 |
| `Write` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `TaskOutput` | 3 |
| `TaskStop` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Edit` | 1 |
| `Glob` | 1 |
| `Grep` | 1 |
| `Task` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
