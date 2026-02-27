# sgonly_test-integration-001 (mcp-remote-direct)

- Run: `test_haiku_20260223_235732`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/test_haiku_20260223_235732--mcp-remote-direct--sgonly_test-integration-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 170.2 |
| Agent execution seconds | 116.1 |
| Input tokens | 3,717,022 |
| Output tokens | 80 |
| Cache tokens | 3,716,431 |
| Tool calls (total) | 30 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 13 |
| MCP ratio | 0.567 |
| keyword_search calls | 5 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `54725dae5906eae8855ff2f2e58b9bbdfe3db5bc3f5754dc5ef87165105b2a16` |
| `trajectory.json` SHA256 | `b8775f1f3c4d8c01b8b6174026209e228185a744ab30230e0fcff90861af6bec` |
| transcript SHA256 | `a6e01d098192a85e6459d78cdf43b65772c4e88054789621a7faa2de2ef51052` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 10 |
| `mcp__sourcegraph__sg_read_file` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Read` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
