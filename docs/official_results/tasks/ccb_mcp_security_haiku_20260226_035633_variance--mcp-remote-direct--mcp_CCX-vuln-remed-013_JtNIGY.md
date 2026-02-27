# mcp_CCX-vuln-remed-013_JtNIGY (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035633_variance`
- Status: `passed`
- Reward: `0.6237`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-013_JtNIGY.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 295.6 |
| Agent execution seconds | 73.8 |
| Input tokens | 2,352,680 |
| Output tokens | 7,621 |
| Cache tokens | 2,352,211 |
| Tool calls (total) | 24 |
| Tool calls (MCP) | 23 |
| Tool calls (local) | 1 |
| MCP ratio | 0.958 |
| keyword_search calls | 7 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `de96a6e1610ba4779f6d63ccdb9f7b0fba8e1042c52a2b877299419d42a26073` |
| `trajectory.json` SHA256 | `faf39919393c983231ed09c054db8a8d29c830653a97b35ccb17a653f6e64960` |
| transcript SHA256 | `fa41f1a0f8732c8261766f6f5d2466a458535d558c72aac62ddb612aed76fd26` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
