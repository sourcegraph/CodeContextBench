# sgonly_qutebrowser-url-regression-prove-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_qutebrowser-url-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_qutebrowser-url-regression-prove-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 465.1 |
| Agent execution seconds | 373.4 |
| Input tokens | 8,367,110 |
| Output tokens | 275 |
| Cache tokens | 8,366,173 |
| Tool calls (total) | 47 |
| Tool calls (MCP) | 5 |
| Tool calls (local) | 42 |
| MCP ratio | 0.106 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8dfb600514178fa9a7e156df8d3ff2a4c642399d936626e8f1bbbad15d970604` |
| `trajectory.json` SHA256 | `1abc4985970fefcb676c4c490bc7b95c78f2977884b42847373c0e695903dc88` |
| transcript SHA256 | `d22786224a31c7d09edd7591f9484d9572428e8bb6db7f9d27c9afe155c879f3` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 35 |
| `Write` | 5 |
| `mcp__sourcegraph__sg_read_file` | 3 |
| `Read` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
