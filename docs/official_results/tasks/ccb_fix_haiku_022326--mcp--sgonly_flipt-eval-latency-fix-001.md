# sgonly_flipt-eval-latency-fix-001 (mcp)

- Run: `ccb_fix_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_flipt-eval-latency-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1245.8 |
| Agent execution seconds | 380.6 |
| Input tokens | 13,830,255 |
| Output tokens | 397 |
| Cache tokens | 13,829,183 |
| Tool calls (total) | 65 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 52 |
| MCP ratio | 0.200 |
| keyword_search calls | - |
| nls_search calls | - |
| deepsearch calls | - |
| `result.json` SHA256 | `dff3bb71ebbf71c59667492d530bbd9bcfcf7aed9f4d4f2982c1923031ebaf8f` |
| `trajectory.json` SHA256 | `5ad2691b5e60de37889da2ef1c3afd66907b3c6b244a3622b212c5e6c37654a1` |
| transcript SHA256 | `1143fcafdf806e78ecc35aaab272cb36e49a77c73223f37dd338e4cde14ed07d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Write` | 19 |
| `Bash` | 17 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `Edit` | 6 |
| `Read` | 6 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `Bash` |
| `Bash` |
| `Bash` |
