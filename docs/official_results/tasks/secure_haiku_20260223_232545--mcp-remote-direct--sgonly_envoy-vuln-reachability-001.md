# sgonly_envoy-vuln-reachability-001 (mcp-remote-direct)

- Run: `secure_haiku_20260223_232545`
- Status: `passed`
- Reward: `0.5600`
- Audit JSON: [link](../audits/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_envoy-vuln-reachability-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/secure_haiku_20260223_232545--mcp-remote-direct--sgonly_envoy-vuln-reachability-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 274.9 |
| Agent execution seconds | 132.9 |
| Input tokens | 2,932,295 |
| Output tokens | 129 |
| Cache tokens | 2,931,715 |
| Tool calls (total) | 26 |
| Tool calls (MCP) | 24 |
| Tool calls (local) | 2 |
| MCP ratio | 0.923 |
| keyword_search calls | 12 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `3acf1c77faaeaf02fb53797652d3f146b5a8449b9e12b393ac7dc9e92d01b916` |
| `trajectory.json` SHA256 | `ca3c91fb34ed45959efb5ae2993d1baf7cd3ac87d3e90b11b4db4a509d19a7f5` |
| transcript SHA256 | `d8e0fb69ff4bf9ff299d4314a01d292be59c7ea0bf7877e934853e713a1690d3` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 12 |
| `mcp__sourcegraph__sg_read_file` | 11 |
| `Bash` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
