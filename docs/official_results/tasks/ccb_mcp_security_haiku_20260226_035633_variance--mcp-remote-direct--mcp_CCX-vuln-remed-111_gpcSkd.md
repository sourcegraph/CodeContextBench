# mcp_CCX-vuln-remed-111_gpcSkd (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035633_variance`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-vuln-remed-111_gpcSkd.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 294.2 |
| Agent execution seconds | 53.5 |
| Input tokens | 992,490 |
| Output tokens | 5,567 |
| Cache tokens | 992,213 |
| Tool calls (total) | 13 |
| Tool calls (MCP) | 11 |
| Tool calls (local) | 2 |
| MCP ratio | 0.846 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e69bfe7813ac714638f5998bb2bec4adde1852d299d4f80ab6e9e02978765151` |
| `trajectory.json` SHA256 | `39722683c7dd8f762a9fe4c0e39b08121ec7b48114ded981acef2e56d4fb4e24` |
| transcript SHA256 | `dfbe7b86628546ca530cf6a49618f13da36de20eddb3556aaf5a167d28c9a7b7` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `Write` |
