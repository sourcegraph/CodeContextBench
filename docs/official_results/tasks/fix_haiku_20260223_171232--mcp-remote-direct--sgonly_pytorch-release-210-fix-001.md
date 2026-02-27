# sgonly_pytorch-release-210-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-release-210-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-release-210-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 819.9 |
| Agent execution seconds | 440.8 |
| Input tokens | 21,020,616 |
| Output tokens | 537 |
| Cache tokens | 21,019,971 |
| Tool calls (total) | 87 |
| Tool calls (MCP) | 21 |
| Tool calls (local) | 66 |
| MCP ratio | 0.241 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `50f546ca9fba2aafd04e523301a94c7cb3e991d986e8a6b0fdd7346e476c850d` |
| `trajectory.json` SHA256 | `503d3c0c62dbc116f5e72ede08ce4b23b546f8d3204c78572dcdf0d6fdfdc72d` |
| transcript SHA256 | `c9586c12882acea2f8984a05fedc333974dbdec16fcf55410b1946f3bda5e441` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 47 |
| `Edit` | 10 |
| `mcp__sourcegraph__sg_read_file` | 10 |
| `Read` | 8 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_commit_search` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `TaskOutput` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_commit_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Bash` |
