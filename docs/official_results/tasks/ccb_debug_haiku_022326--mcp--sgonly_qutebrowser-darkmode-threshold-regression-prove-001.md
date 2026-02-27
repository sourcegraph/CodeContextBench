# sgonly_qutebrowser-darkmode-threshold-regression-prove-001 (mcp)

- Run: `ccb_debug_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_qutebrowser-darkmode-threshold-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 635.8 |
| Agent execution seconds | 557.8 |
| Input tokens | 23,011,153 |
| Output tokens | 519 |
| Cache tokens | 23,009,793 |
| Tool calls (total) | 80 |
| Tool calls (MCP) | 21 |
| Tool calls (local) | 59 |
| MCP ratio | 0.263 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8c17f204a796be84def30d768166eeaed44572f013d19ddca6c3690b9d9025e3` |
| `trajectory.json` SHA256 | `c7609a630f8a140f9e92b92f84d486acb2a47902b82f38722e4adc9979e3c499` |
| transcript SHA256 | `3a83133e34537c8d3605031cfa607a6eed5a8dbef685f0baf7f623f4baeb0809` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 47 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `Write` | 6 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Edit` | 4 |
| `Read` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `Read` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Write` |
| `Write` |
| `Bash` |
| `Bash` |
| `Write` |
| `Bash` |
