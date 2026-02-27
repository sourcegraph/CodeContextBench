# sgonly_envoy-udp-proxy-cds-fix-001 (mcp-remote-direct)

- Run: `fix_haiku_20260226_new3tasks`
- Status: `passed`
- Reward: `0.7838`
- Audit JSON: [link](../audits/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-udp-proxy-cds-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 264.2 |
| Agent execution seconds | 101.7 |
| Input tokens | 5,149,818 |
| Output tokens | 7,683 |
| Cache tokens | 5,149,249 |
| Tool calls (total) | 33 |
| Tool calls (MCP) | 16 |
| Tool calls (local) | 17 |
| MCP ratio | 0.485 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e7f737228ec5b0a5a4aba94bbf9b7f769b81ec487dfecebe083a67951a9e465a` |
| `trajectory.json` SHA256 | `06c835ca955226942e7868f0a19d1d8d464b2c91b24b9c704a815048bdf75c9c` |
| transcript SHA256 | `1a73d669a398f3be54cacdc5b19da0d6a6d13bc8d0f264ada28df688bdc51012` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 10 |
| `Bash` | 8 |
| `Read` | 6 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Edit` | 3 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
