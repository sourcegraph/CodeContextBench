# ccx-crossorg-066 (mcp)

- Run: `ccb_mcp_crossorg_haiku_022126`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_crossorg_haiku_022126--mcp--ccx-crossorg-066.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_crossorg_haiku_022126--mcp--ccx-crossorg-066/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1969.1 |
| Agent execution seconds | 1272.3 |
| Input tokens | 579,806 |
| Output tokens | 74 |
| Cache tokens | 579,612 |
| Tool calls (total) | 7 |
| Tool calls (MCP) | 6 |
| Tool calls (local) | 1 |
| MCP ratio | 0.857 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8452d504161f08d4c6b182f54046a540fa718a71acdb012bc2d165e8595286be` |
| `trajectory.json` SHA256 | `aaaaa03c33312e6dd0ee531dd88459ba17f846dd5dae7f8d7655bec970c56eab` |
| transcript SHA256 | `a0a9b65244a0ecdb5b034360588a5eb19a88e589324d907a063cf363cec5d203` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_repos` | 3 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_read_file` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
