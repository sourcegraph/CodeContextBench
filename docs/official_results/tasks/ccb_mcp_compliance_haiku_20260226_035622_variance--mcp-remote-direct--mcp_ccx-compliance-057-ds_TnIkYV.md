# mcp_ccx-compliance-057-ds_TnIkYV (mcp-remote-direct)

- Run: `ccb_mcp_compliance_haiku_20260226_035622_variance`
- Status: `passed`
- Reward: `0.9008`
- Audit JSON: [link](../audits/ccb_mcp_compliance_haiku_20260226_035622_variance--mcp-remote-direct--mcp_ccx-compliance-057-ds_TnIkYV.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 3414.4 |
| Agent execution seconds | 358.9 |
| Input tokens | 5,427,965 |
| Output tokens | 9,604 |
| Cache tokens | 5,427,096 |
| Tool calls (total) | 52 |
| Tool calls (MCP) | 51 |
| Tool calls (local) | 1 |
| MCP ratio | 0.981 |
| keyword_search calls | 10 |
| nls_search calls | 5 |
| deepsearch calls | 1 |
| `result.json` SHA256 | `716c2fd362e7760441ba27bac5f0db2e03394c4a9ed29fad4e71f6949f1918ad` |
| `trajectory.json` SHA256 | `46037e1b465d752ad1a9577565dba873a4055c2e9a75540fb5ce7157650593ee` |
| transcript SHA256 | `72321e7b207fbb5c9bc4489d2a6806dcf20e7791e46c4b48ca351ea7756ad146` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 18 |
| `mcp__sourcegraph__sg_list_files` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 10 |
| `mcp__sourcegraph__sg_nls_search` | 5 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_deepsearch` | 1 |
| `mcp__sourcegraph__sg_deepsearch_read` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_deepsearch` |
| `mcp__sourcegraph__sg_deepsearch_read` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
