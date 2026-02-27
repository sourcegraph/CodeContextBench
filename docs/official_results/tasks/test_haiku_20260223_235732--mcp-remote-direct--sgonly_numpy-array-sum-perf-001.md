# sgonly_numpy-array-sum-perf-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_numpy-array-sum-perf-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 432.6 |
| Agent execution seconds | 229.5 |
| Input tokens | 6,373,816 |
| Output tokens | 198 |
| Cache tokens | 6,373,161 |
| Tool calls (total) | 40 |
| Tool calls (MCP) | 16 |
| Tool calls (local) | 24 |
| MCP ratio | 0.400 |
| keyword_search calls | 4 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `c513197de2cc49542267e9f8d5c9be138bad74adc5c8c0fcf9ffcf1a23b8f876` |
| `trajectory.json` SHA256 | `6b8aea640a1aaf88c9509e2343e7b19996ce72c7adc7e9d00835d039aedea011` |
| transcript SHA256 | `8815d6fbfb0fde1591cb4e11faf2f7c0691ac268fa57d1a0c12a6ea047bee4bd` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 16 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `Read` | 4 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Edit` | 2 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `Bash` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
