# sgonly_pytorch-cudnn-version-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-cudnn-version-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 674.2 |
| Agent execution seconds | 184.1 |
| Input tokens | 7,770,540 |
| Output tokens | 207 |
| Cache tokens | 7,769,841 |
| Tool calls (total) | 29 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 12 |
| MCP ratio | 0.586 |
| keyword_search calls | 7 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `d531869e7e508543bf82a0e6a387640d198814c8e97202620623e68cda0c54e7` |
| `trajectory.json` SHA256 | `74d492e1301d59bbf5d3b03f1093a1c4c14a7c825831a000da475130180e4530` |
| transcript SHA256 | `e544c58a69a5c8ba90cef43e5e612941fcbf59a9eb2ebb63100cfbb4bea41080` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 9 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `Write` | 2 |
| `Read` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
