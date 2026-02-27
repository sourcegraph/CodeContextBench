# sgonly_openlibrary-search-query-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260226_024454`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 384.7 |
| Agent execution seconds | 322.2 |
| Input tokens | 11,884,934 |
| Output tokens | 21,736 |
| Cache tokens | 11,883,992 |
| Tool calls (total) | 80 |
| Tool calls (MCP) | 14 |
| Tool calls (local) | 66 |
| MCP ratio | 0.175 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `24dfd003613ad88e5fcb05cc6082b915496424f37386fb8faa731e69b42f1740` |
| `trajectory.json` SHA256 | `1a2b27d7dee546d5c774dc261b69ad66b038271d96badfed84b18218f61eef6d` |
| transcript SHA256 | `889730f78c186f1201017bc53f5bc81752c3500c2337bc9be53e890dae9ab889` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 57 |
| `mcp__sourcegraph__sg_read_file` | 8 |
| `Write` | 5 |
| `Read` | 3 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_list_repos` | 2 |
| `Edit` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `Bash` |
