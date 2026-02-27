# sgonly_vscode-stale-diagnostics-feat-001 (mcp)

- Run: `ccb_build_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_build_haiku_022326--mcp--sgonly_vscode-stale-diagnostics-feat-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_build_haiku_022326--mcp--sgonly_vscode-stale-diagnostics-feat-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 523.9 |
| Agent execution seconds | 304.1 |
| Input tokens | 7,260,980 |
| Output tokens | 410 |
| Cache tokens | 7,260,195 |
| Tool calls (total) | 32 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 12 |
| MCP ratio | 0.625 |
| keyword_search calls | 6 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `fd1fbd655b37555b786c610c4a9dcd6066654475b58ee3e88d77f3c47c8936a3` |
| `trajectory.json` SHA256 | `d892d4e891d6e136806d70e0e869b50aa30b18cced51ee1c308079f1ecbeeb0d` |
| transcript SHA256 | `eab1af9a52948ccd23cdfdb18dcdaad1113663d307f6465f20844eca4a3517f7` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 10 |
| `Bash` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `Read` | 2 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `mcp__sourcegraph__sg_list_files` |
| `Bash` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
