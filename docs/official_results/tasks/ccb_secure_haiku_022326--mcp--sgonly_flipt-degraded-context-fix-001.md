# sgonly_flipt-degraded-context-fix-001 (mcp)

- Run: `ccb_secure_haiku_022326`
- Status: `passed`
- Reward: `0.2500`
- Audit JSON: [link](../audits/ccb_secure_haiku_022326--mcp--sgonly_flipt-degraded-context-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 599.2 |
| Agent execution seconds | 371.3 |
| Input tokens | 6,603,489 |
| Output tokens | 267 |
| Cache tokens | 6,602,538 |
| Tool calls (total) | 36 |
| Tool calls (MCP) | 12 |
| Tool calls (local) | 24 |
| MCP ratio | 0.333 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `9641be6eac049dd1c821f22bf206b6d95edd691696783e23a77114e1bbf3a967` |
| `trajectory.json` SHA256 | `995583a8cee467f837e21ebba395fba34d14a155098d0b9dc93e5b94fd23611b` |
| transcript SHA256 | `b506154f332c7910d8705373dd5a27b9aa3a69bf01dcd51a584d9df65d324523` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 15 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `Write` | 4 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Edit` | 1 |
| `Read` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `Write` |
| `Read` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
