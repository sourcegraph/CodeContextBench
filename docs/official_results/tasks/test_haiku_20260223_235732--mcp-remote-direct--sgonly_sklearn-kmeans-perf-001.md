# sgonly_sklearn-kmeans-perf-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_sklearn-kmeans-perf-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 405.6 |
| Agent execution seconds | 252.1 |
| Input tokens | 4,484,085 |
| Output tokens | 192 |
| Cache tokens | 4,483,398 |
| Tool calls (total) | 27 |
| Tool calls (MCP) | 7 |
| Tool calls (local) | 20 |
| MCP ratio | 0.259 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `2a172ba825b05c170a247f63ba32949c8d75071fe1b4c822e9a30d03d0535b1c` |
| `trajectory.json` SHA256 | `ae0a25a79b09324a8d93db0ddee47934df85fc138cd9a203e5a90e4b92c98418` |
| transcript SHA256 | `2662702f8a7be53d52869356818652c6873292dfa532ef1c235b93f324b37126` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 14 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `TodoWrite` | 3 |
| `Read` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `Bash` |
| `Bash` |
| `Write` |
| `TodoWrite` |
