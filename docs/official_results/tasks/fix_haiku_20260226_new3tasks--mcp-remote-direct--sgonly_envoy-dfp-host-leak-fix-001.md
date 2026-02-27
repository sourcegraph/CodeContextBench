# sgonly_envoy-dfp-host-leak-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260226_new3tasks`
- Status: `passed`
- Reward: `0.6647`
- Audit JSON: [link](../audits/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-dfp-host-leak-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 604.3 |
| Agent execution seconds | 292.4 |
| Input tokens | 5,809,412 |
| Output tokens | 37,527 |
| Cache tokens | 5,808,877 |
| Tool calls (total) | 29 |
| Tool calls (MCP) | 10 |
| Tool calls (local) | 19 |
| MCP ratio | 0.345 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `3c117c2a9a2b9f467faf9d5eb1353f98d28ea92abb4b9be3c526911ebce3255c` |
| `trajectory.json` SHA256 | `c36eed763eb9183c8c01a841faa08516832e16e0f488560d4bc4e6db6af1813b` |
| transcript SHA256 | `44282ae8e8b01e9bb7b94ed633dc1171720f400d1125a0e1b4d9575042a1c41f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 12 |
| `mcp__sourcegraph__sg_read_file` | 6 |
| `Write` | 3 |
| `Edit` | 2 |
| `Read` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
