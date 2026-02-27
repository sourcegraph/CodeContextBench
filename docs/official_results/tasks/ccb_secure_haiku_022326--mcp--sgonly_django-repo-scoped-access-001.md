# sgonly_django-repo-scoped-access-001 (mcp)

- Run: `ccb_secure_haiku_022326`
- Status: `passed`
- Reward: `0.7000`
- Audit JSON: [link](../audits/ccb_secure_haiku_022326--mcp--sgonly_django-repo-scoped-access-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 431.7 |
| Agent execution seconds | 349.0 |
| Input tokens | 15,237,220 |
| Output tokens | 462 |
| Cache tokens | 15,236,658 |
| Tool calls (total) | 98 |
| Tool calls (MCP) | 55 |
| Tool calls (local) | 43 |
| MCP ratio | 0.561 |
| keyword_search calls | 28 |
| nls_search calls | 3 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `45316721a1aa44ad1d74ebbf2bbe8f9770563dc4fc2f6d4023772cbc14f97fef` |
| `trajectory.json` SHA256 | `db6d186107270b018837b53d65159be70f306ccf064e42b35e81e192cca54f23` |
| transcript SHA256 | `d86516b224391431cb7897479a8e25df67f885e4dd530ddec872bffeddb3f92f` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 29 |
| `mcp__sourcegraph__sg_keyword_search` | 28 |
| `mcp__sourcegraph__sg_read_file` | 20 |
| `Read` | 5 |
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `mcp__sourcegraph__sg_nls_search` | 3 |
| `Write` | 2 |
| `Edit` | 1 |
| `Grep` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_read_file` |
| `Grep` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
