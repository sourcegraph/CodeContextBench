# sgonly_linux-ssd-trim-timeout-fault-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_linux-ssd-trim-timeout-fault-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_linux-ssd-trim-timeout-fault-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 140.5 |
| Agent execution seconds | 72.1 |
| Input tokens | 2,134,964 |
| Output tokens | 90 |
| Cache tokens | 2,134,555 |
| Tool calls (total) | 15 |
| Tool calls (MCP) | 11 |
| Tool calls (local) | 4 |
| MCP ratio | 0.733 |
| keyword_search calls | 7 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `ece40f90e6d10cc26220d0d8537a84ee333e769bba5b6fb94904b9ad4c428913` |
| `trajectory.json` SHA256 | `8a4199a020c40deb7720ad281bf5581b2a87aa6e193b71cb55a9eac1c714bdb5` |
| transcript SHA256 | `77b860928d03cbdb86749efea758278d340488d0e5494e33082db93c4f294714` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 7 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `Bash` | 2 |
| `Read` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
| `Bash` |
| `Bash` |
| `Read` |
| `mcp__sourcegraph__sg_keyword_search` |
