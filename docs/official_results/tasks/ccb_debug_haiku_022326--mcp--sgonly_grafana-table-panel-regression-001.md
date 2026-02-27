# sgonly_grafana-table-panel-regression-001 (mcp)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.9000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_grafana-table-panel-regression-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_grafana-table-panel-regression-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 166.1 |
| Agent execution seconds | 109.2 |
| Input tokens | 1,839,708 |
| Output tokens | 67 |
| Cache tokens | 1,839,363 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 1 |
| MCP ratio | 0.929 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `2111ecdb6c682a172e97d6354a3407ea8f7fe9fce6a2fac32d026c426751b94d` |
| `trajectory.json` SHA256 | `23b8cf4c713903b14d8ebbf7c527437bcd14cd42195785c285e30320173d8d52` |
| transcript SHA256 | `d0c169e00ac21316d2e85bcd5c8ee5f6228ddd90e9f2be45d5d0b8c4a7235cb8` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
