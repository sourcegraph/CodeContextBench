# sgonly_test-coverage-gap-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `passed`
- Reward: `0.8600`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_test-coverage-gap-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/test_haiku_20260223_235732--mcp-remote-direct--sgonly_test-coverage-gap-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 233.2 |
| Agent execution seconds | 109.7 |
| Input tokens | 2,860,333 |
| Output tokens | 88 |
| Cache tokens | 2,859,731 |
| Tool calls (total) | 24 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 1 |
| MCP ratio | 0.958 |
| keyword_search calls | 7 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `1827f1237551afb9a5392517d27d7d6aa08ba7773c918d1089482840a7bd0699` |
| `trajectory.json` SHA256 | `f92c13c941a7c734007402d65c3a41746c4c93cf11dfeb9d654a260ef2924899` |
| transcript SHA256 | `39f60c4cd1d480fc233efc5f8ef96bd0f323c045a66366e595452fb870a82f6d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 13 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
