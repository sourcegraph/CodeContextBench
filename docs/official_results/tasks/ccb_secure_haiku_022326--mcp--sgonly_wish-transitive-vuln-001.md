# sgonly_wish-transitive-vuln-001 (mcp-remote-direct)

- Run: `ccb_secure_haiku_022326`
- Status: `passed`
- Reward: `0.6600`
- Audit JSON: [link](../audits/ccb_secure_haiku_022326--mcp--sgonly_wish-transitive-vuln-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_secure_haiku_022326--mcp--sgonly_wish-transitive-vuln-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 128.2 |
| Agent execution seconds | 79.3 |
| Input tokens | 1,335,257 |
| Output tokens | 67 |
| Cache tokens | 1,334,908 |
| Tool calls (total) | 16 |
| Tool calls (MCP) | 15 |
| Tool calls (local) | 1 |
| MCP ratio | 0.938 |
| keyword_search calls | 3 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `2c89b34a3d65cbff0a5e2bdd0083844ac8ea0b1f22b5a397f0636d3a0e24db82` |
| `trajectory.json` SHA256 | `512ad8b99975a13a158a87f76afc9298325c9a8bf7da3a7eb98e56e26f38a77f` |
| transcript SHA256 | `362448606fdce3ec73f5380f3ec5237178ae0de96de1051b066224be0e627418` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 10 |
| `mcp__sourcegraph__sg_keyword_search` | 3 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
