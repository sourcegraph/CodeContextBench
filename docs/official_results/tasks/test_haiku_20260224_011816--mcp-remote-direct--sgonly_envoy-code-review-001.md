# sgonly_envoy-code-review-001 (mcp-remote-direct)

- Run: `test_haiku_20260224_011816`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/test_haiku_20260224_011816--mcp-remote-direct--sgonly_envoy-code-review-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/test_haiku_20260224_011816--mcp-remote-direct--sgonly_envoy-code-review-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 484.1 |
| Agent execution seconds | 239.8 |
| Input tokens | 3,189,061 |
| Output tokens | 97 |
| Cache tokens | 3,188,698 |
| Tool calls (total) | 18 |
| Tool calls (MCP) | 13 |
| Tool calls (local) | 5 |
| MCP ratio | 0.722 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `8c5fa63dcc576934c399387a55b6d74fc82f4ac72ef08a0b8f9277ed1eb18458` |
| `trajectory.json` SHA256 | `abd3336cda08a2e23a3903f7d7dec8b59954e40147a3eb932cddee1a6458ede6` |
| transcript SHA256 | `b5a4d17b67fb9de70e4c722d7b608fce7702f7d47e002c3883f9f6b474a956a0` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 11 |
| `Bash` | 3 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Grep` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Grep` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
