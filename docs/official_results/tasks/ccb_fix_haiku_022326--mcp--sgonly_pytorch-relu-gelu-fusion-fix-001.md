# sgonly_pytorch-relu-gelu-fusion-fix-001 (mcp)

- Run: `ccb_fix_haiku_022326`
- Status: `passed`
- Reward: `0.5608`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_pytorch-relu-gelu-fusion-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_fix_haiku_022326--mcp--sgonly_pytorch-relu-gelu-fusion-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 948.5 |
| Agent execution seconds | 186.5 |
| Input tokens | 6,007,585 |
| Output tokens | 179 |
| Cache tokens | 6,006,931 |
| Tool calls (total) | 46 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 29 |
| MCP ratio | 0.370 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `6807037e8b39dcca22f4ec14eca56c4bf6c0552eaf165f7e19745f1c75a1435e` |
| `trajectory.json` SHA256 | `66583f1673a2b4ea1184b623d8378a63066502c7c60bc8bb4c4648cc66ac00fb` |
| transcript SHA256 | `f75dfd0d0661abae7b61e0a650a9f76cd05025947c59f2bd76c6bc9310475122` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 17 |
| `mcp__sourcegraph__sg_read_file` | 10 |
| `Read` | 7 |
| `Edit` | 3 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_compare_revisions` | 2 |
| `Grep` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_commit_search` |
| `mcp__sourcegraph__sg_compare_revisions` |
| `Read` |
| `Read` |
| `Grep` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
