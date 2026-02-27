# sgonly_rust-subtype-relation-refac-001 (mcp-remote-direct)

- Run: `build_haiku_20260223_124805`
- Status: `passed`
- Reward: `0.7100`
- Audit JSON: [link](../audits/build_haiku_20260223_124805--mcp-remote-direct--sgonly_rust-subtype-relation-refac-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1834.3 |
| Agent execution seconds | 183.1 |
| Input tokens | 3,866,826 |
| Output tokens | 153 |
| Cache tokens | 3,866,190 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 15 |
| MCP ratio | 0.464 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `38823acf12a6a6e2cfbb254efefe2fee36d6e9cd897b1d894c831123603bc50d` |
| `trajectory.json` SHA256 | `e7a113bf57e6901f84cce1461009fe48067ae592e736f52ba45e2ef24e78804a` |
| transcript SHA256 | `6cffa4eb4bef04e4b61378479b526f8976520bac1a7e01571dfb2fcb4c96894d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 10 |
| `mcp__sourcegraph__sg_read_file` | 7 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `TodoWrite` | 3 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_find_references` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_find_references` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
