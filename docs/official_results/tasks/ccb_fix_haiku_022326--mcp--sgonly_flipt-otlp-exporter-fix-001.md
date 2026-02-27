# sgonly_flipt-otlp-exporter-fix-001 (mcp-remote-direct)

- Run: `ccb_fix_haiku_022326`
- Status: `passed`
- Reward: `0.9790`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_flipt-otlp-exporter-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_fix_haiku_022326--mcp--sgonly_flipt-otlp-exporter-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1073.5 |
| Agent execution seconds | 503.6 |
| Input tokens | 10,963,788 |
| Output tokens | 408 |
| Cache tokens | 10,962,817 |
| Tool calls (total) | 77 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 59 |
| MCP ratio | 0.221 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f11ad4d9f7bfe693fddfed28441488115bf1e9744eb902fc4ef2c42e4357f933` |
| `trajectory.json` SHA256 | `30214223134762df3ba4b6117488c842bdd038d72cb6379c23419d1a6b55c096` |
| transcript SHA256 | `3fdcb4df27f55fd65bc767872b9cecdf7f55dce3a89e008471e4ba195bfb8db3` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 42 |
| `Read` | 10 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Edit` | 1 |
| `Write` | 1 |
| `bash` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `bash` |
