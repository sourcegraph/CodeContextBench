# sgonly_k8s-scheduler-arch-001 (mcp-remote-direct)

- Run: `design_haiku_20260223_124652`
- Status: `passed`
- Reward: `0.7200`
- Audit JSON: [link](../audits/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-scheduler-arch-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/design_haiku_20260223_124652--mcp-remote-direct--sgonly_k8s-scheduler-arch-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 945.8 |
| Agent execution seconds | 125.2 |
| Input tokens | 3,896,423 |
| Output tokens | 116 |
| Cache tokens | 3,895,903 |
| Tool calls (total) | 22 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 4 |
| MCP ratio | 0.773 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `30bdc160816dbeb7f2c2b0cad4076a4583928a4324b33c2a7708dc398efe1429` |
| `trajectory.json` SHA256 | `698b688aee3563797d504d82ca70292be7e6af738252dbf9b2cf540bd940d1ca` |
| transcript SHA256 | `c8b1d31f13850e37b2a301375d086a404b9d8571c0ebaec85cde6797455d87f2` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 11 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `Read` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Bash` | 1 |
| `Write` | 1 |
| `bash` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
