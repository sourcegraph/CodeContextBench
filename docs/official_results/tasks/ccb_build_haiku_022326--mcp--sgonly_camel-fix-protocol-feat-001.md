# sgonly_camel-fix-protocol-feat-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `passed`
- Reward: `0.1300`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_camel-fix-protocol-feat-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 852.0 |
| Agent execution seconds | 220.3 |
| Input tokens | 5,328,557 |
| Output tokens | 238 |
| Cache tokens | 5,327,764 |
| Tool calls (total) | 40 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 20 |
| MCP ratio | 0.500 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `7b586b516fec9632e9e6c339f320b610e50e2c1ef87077453a71c13fd73c638e` |
| `trajectory.json` SHA256 | `b27ddd637ec622adb25320bc690b082aa136a927bba321f22fa5c8c9af35af0e` |
| transcript SHA256 | `d9f01fe0dea559cd12094a0b2f64f3ec75df4eadeb10a40ecd045fe84142c10e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Write` | 9 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `Bash` | 8 |
| `mcp__sourcegraph__sg_list_files` | 7 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
