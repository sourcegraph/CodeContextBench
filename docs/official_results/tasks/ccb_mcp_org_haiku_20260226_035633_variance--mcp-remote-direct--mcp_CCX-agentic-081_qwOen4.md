# mcp_CCX-agentic-081_qwOen4 (mcp-remote-direct)

- Run: `ccb_mcp_org_haiku_20260226_035633_variance`
- Status: `passed`
- Reward: `0.6000`
- Audit JSON: [link](../audits/ccb_mcp_org_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-agentic-081_qwOen4.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 297.5 |
| Agent execution seconds | 58.8 |
| Input tokens | 1,045,179 |
| Output tokens | 6,039 |
| Cache tokens | 1,044,954 |
| Tool calls (total) | 9 |
| Tool calls (MCP) | 7 |
| Tool calls (local) | 2 |
| MCP ratio | 0.778 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `fa8668c867ef9e7621347d4de079c78022cc93798ccd2884a2e48637fd19f99e` |
| `trajectory.json` SHA256 | `d4dd7bafb2f5990e58fe1fdb81934cad0f958f5a0ebfd508932a3e04e8afb5a6` |
| transcript SHA256 | `3478c9e29bce7970156416e5f00c807210f8bef8dbd98bf6170844be9adb8982` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `Write` | 2 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
| `Write` |
