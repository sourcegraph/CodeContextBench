# sgonly_openlibrary-fntocli-adapter-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260223_171232`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-fntocli-adapter-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-fntocli-adapter-fix-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 3016.0 |
| Agent execution seconds | 2352.7 |
| Input tokens | 3,801,793 |
| Output tokens | 206 |
| Cache tokens | 3,801,266 |
| Tool calls (total) | 37 |
| Tool calls (MCP) | 4 |
| Tool calls (local) | 33 |
| MCP ratio | 0.108 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `1138fb2b7f43a5fbb977734d32f937c1ca66148051a57ad7bed73a1df821b8da` |
| `trajectory.json` SHA256 | `0b02e97f8719f6848c61fabfbcdc5ab2ee9f13c71003dce40db0fa86cd85cf05` |
| transcript SHA256 | `38cd68025d04ce78bbfc56b1ca6377482ec0f8a52c9a97f5392ec06a7e24717e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 19 |
| `Edit` | 6 |
| `Read` | 4 |
| `TodoWrite` | 4 |
| `mcp__sourcegraph__sg_read_file` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
