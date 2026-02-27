# mcp_CCX-vuln-remed-013_WOkHxn (mcp-remote-direct)

- Run: `ccb_mcp_security_haiku_20260226_035617`
- Status: `passed`
- Reward: `0.7046`
- Audit JSON: [link](../audits/ccb_mcp_security_haiku_20260226_035617--mcp-remote-direct--mcp_CCX-vuln-remed-013_WOkHxn.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 294.5 |
| Agent execution seconds | 72.5 |
| Input tokens | 2,310,908 |
| Output tokens | 8,278 |
| Cache tokens | 2,310,381 |
| Tool calls (total) | 27 |
| Tool calls (MCP) | 25 |
| Tool calls (local) | 2 |
| MCP ratio | 0.926 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `328d5ab62bc8e69706e757de4566d7f29bf705a5fbfeb510168ee8163077a006` |
| `trajectory.json` SHA256 | `7fd68414cab34a522067cfc8b497c14241c25cb080c45854fdc20da7019d7a6a` |
| transcript SHA256 | `101142b147395502d074a1499b32385ca2eafffafec8842378c5cd618ec1a5fe` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 17 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
