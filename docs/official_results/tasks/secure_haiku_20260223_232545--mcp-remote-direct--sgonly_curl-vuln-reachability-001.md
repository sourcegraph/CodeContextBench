# sgonly_curl-vuln-reachability-001 (mcp-remote-direct)

- Run: `secure_haiku_20260223_232545`
- Status: `passed`
- Reward: `0.8500`
- Audit JSON: [link](../audits/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_curl-vuln-reachability-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_curl-vuln-reachability-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 232.4 |
| Agent execution seconds | 87.9 |
| Input tokens | 2,962,536 |
| Output tokens | 83 |
| Cache tokens | 2,962,045 |
| Tool calls (total) | 25 |
| Tool calls (MCP) | 24 |
| Tool calls (local) | 1 |
| MCP ratio | 0.960 |
| keyword_search calls | 9 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `bf84c912e90e35df8f09078f6c4c3665bb405453fc61c8c69c1f8af655fc1802` |
| `trajectory.json` SHA256 | `a3f1d978caee5bcec80846e7523c8e2275454c8b5492180d7e09bec54edc317a` |
| transcript SHA256 | `3c66172069f25ea89103a5f8e8aefd4067f1b5eb9c6fcf6c01e8abcbb8fc1599` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 9 |
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_find_references` | 5 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_find_references` |
| `mcp__sourcegraph__sg_find_references` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
