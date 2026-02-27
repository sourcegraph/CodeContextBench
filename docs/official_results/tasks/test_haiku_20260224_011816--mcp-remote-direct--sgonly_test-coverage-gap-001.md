# sgonly_test-coverage-gap-001 (mcp-remote-direct)

- Run: `test_haiku_20260224_011816`
- Status: `passed`
- Reward: `0.9400`
- Audit JSON: [link](../audits/test_haiku_20260224_011816--mcp-remote-direct--sgonly_test-coverage-gap-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 230.1 |
| Agent execution seconds | 156.2 |
| Input tokens | 3,449,774 |
| Output tokens | 145 |
| Cache tokens | 3,449,189 |
| Tool calls (total) | 29 |
| Tool calls (MCP) | 28 |
| Tool calls (local) | 1 |
| MCP ratio | 0.966 |
| keyword_search calls | 9 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `11094826a1b9c16c78b7187ced826908699a6a619dc82f5861bc5f01dd5686b1` |
| `trajectory.json` SHA256 | `957d4a2f613d67ab097667226b550c6b5f708da53cbc779a3790f7cf56a27912` |
| transcript SHA256 | `b8d7ebedf1186a56b23f7cc8c5babe5c9fbb7ec5a5c26d4fd08f3d113fb639a9` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 16 |
| `mcp__sourcegraph__sg_keyword_search` | 9 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
