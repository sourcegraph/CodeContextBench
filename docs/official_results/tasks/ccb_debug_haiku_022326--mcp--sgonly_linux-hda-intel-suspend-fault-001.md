# sgonly_linux-hda-intel-suspend-fault-001 (mcp)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `0.7000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_linux-hda-intel-suspend-fault-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 316.3 |
| Agent execution seconds | 247.4 |
| Input tokens | 5,475,903 |
| Output tokens | 200 |
| Cache tokens | 5,475,346 |
| Tool calls (total) | 49 |
| Tool calls (MCP) | 44 |
| Tool calls (local) | 5 |
| MCP ratio | 0.898 |
| keyword_search calls | 26 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `7640b5620b36699590eace5a4ec08323b256b20631d0399b0ce5e45905d5e5fd` |
| `trajectory.json` SHA256 | `e991812ff4b03bbe9c166c0fd4a426b441b334c3add820bc5e042caf21730213` |
| transcript SHA256 | `af449a57756b5e2a3cdbe50c843c0218bde02bd036202dafe4cd7983264dd31e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 26 |
| `mcp__sourcegraph__sg_read_file` | 15 |
| `Bash` | 3 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_commit_search` | 1 |
| `mcp__sourcegraph__sg_diff_search` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
