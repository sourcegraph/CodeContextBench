# sgonly_kafka-producer-bufpool-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260224_011821`
- Status: `passed`
- Reward: `0.7800`
- Audit JSON: [link](../audits/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_kafka-producer-bufpool-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_kafka-producer-bufpool-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 253.1 |
| Agent execution seconds | 204.5 |
| Input tokens | 3,810,956 |
| Output tokens | 123 |
| Cache tokens | 3,810,364 |
| Tool calls (total) | 30 |
| Tool calls (MCP) | 27 |
| Tool calls (local) | 2 |
| MCP ratio | 0.900 |
| keyword_search calls | 13 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `7dba713a4c32a83ff737fc69fc0b6a3958c0a101ddebb6605d6a27272337f9bf` |
| `trajectory.json` SHA256 | `2a7d0b6265048874931f427ed7ffb79ef58f89f888c8b5a5c72bbfa9fc603547` |
| transcript SHA256 | `9d721942bc10c03383a0a4bc27795a6f81ae6087d20207d9d195217841136897` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 13 |
| `mcp__sourcegraph__sg_read_file` | 12 |
| `Read` | 1 |
| `Write` | 1 |
| `bash` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
