# sgonly_flink-pricing-window-feat-001 (mcp-remote-direct)

- Run: `build_haiku_20260223_124805`
- Status: `passed`
- Reward: `0.5100`
- Audit JSON: [link](../audits/build_haiku_20260223_124805--mcp-remote-direct--sgonly_flink-pricing-window-feat-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1000.6 |
| Agent execution seconds | 195.2 |
| Input tokens | 6,509,648 |
| Output tokens | 225 |
| Cache tokens | 6,508,927 |
| Tool calls (total) | 46 |
| Tool calls (MCP) | 26 |
| Tool calls (local) | 20 |
| MCP ratio | 0.565 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `5ed67e0cd0bd7776aab11b23d5b29bca0da210421e556e6c4c333ca93327d991` |
| `trajectory.json` SHA256 | `fb89c91e3b4a853e90a755f632679d1f9058ac83f837920ee7526b1788a49c3f` |
| transcript SHA256 | `3cc9d400012de22a92ace915b4d2ee77a66ae0732adaa50cd5d5149c97833c13` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 11 |
| `Bash` | 10 |
| `mcp__sourcegraph__sg_list_files` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `Write` | 4 |
| `Read` | 3 |
| `TodoWrite` | 3 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
