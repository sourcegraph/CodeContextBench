# sgonly_linux-nfs-inode-revalidate-fault-001 (mcp-remote-direct)

- Run: `debug_haiku_20260223_154724`
- Status: `passed`
- Reward: `0.3000`
- Audit JSON: [link](../audits/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_linux-nfs-inode-revalidate-fault-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/debug_haiku_20260223_154724--mcp-remote-direct--sgonly_linux-nfs-inode-revalidate-fault-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 230.0 |
| Agent execution seconds | 159.1 |
| Input tokens | 8,559,831 |
| Output tokens | 213 |
| Cache tokens | 8,558,927 |
| Tool calls (total) | 57 |
| Tool calls (MCP) | 53 |
| Tool calls (local) | 4 |
| MCP ratio | 0.930 |
| keyword_search calls | 30 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `0cbd0e912dbb82f0ba23008d49feb65078f02d456e7f9fdf1b943fab9f32271c` |
| `trajectory.json` SHA256 | `df4135fc87d776931b91aa52bd506a670821e4894daffe6a74e5b5d60daeffb9` |
| transcript SHA256 | `789f0c16995d868ca416ab2569335828ed78863a6ba3c74ad07fa85ca9721421` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 30 |
| `mcp__sourcegraph__sg_read_file` | 20 |
| `Bash` | 2 |
| `mcp__sourcegraph__sg_nls_search` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
