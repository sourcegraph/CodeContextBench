# sgonly_envoy-ext-authz-handoff-001 (mcp-remote-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `0.8300`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 219.3 |
| Agent execution seconds | 117.0 |
| Input tokens | 2,232,684 |
| Output tokens | 66 |
| Cache tokens | 2,232,222 |
| Tool calls (total) | 25 |
| Tool calls (MCP) | 24 |
| Tool calls (local) | 1 |
| MCP ratio | 0.960 |
| keyword_search calls | 1 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `b1beaba051f8a53fac19ba1043d7a58c95699a875f3dec89c2f3abf3d60e3635` |
| `trajectory.json` SHA256 | `513a9342260f47d18e2d82fe3d9cd6d910e118854164e17375fc3884ebb10262` |
| transcript SHA256 | `73af9fc8e16db41516bf4dedde1061398b9daa7029f653f22859649b455e6aa0` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 17 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
