# sgonly_ansible-galaxy-tar-regression-prove-001 (mcp)

- Run: `ccb_debug_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_ansible-galaxy-tar-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 699.8 |
| Agent execution seconds | 613.1 |
| Input tokens | 6,596,949 |
| Output tokens | 225 |
| Cache tokens | 6,596,047 |
| Tool calls (total) | 43 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 23 |
| MCP ratio | 0.465 |
| keyword_search calls | 11 |
| nls_search calls | 2 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `4d72a9ce5001de6ca4aef2a2d3e45316ca2b4716d5662f6910294aac96349322` |
| `trajectory.json` SHA256 | `6cd9001ddf1c101871033a24abfd1319527c9bf5ca4b68d519e2be32361b4ee4` |
| transcript SHA256 | `9e8c02c118df391eaa0aeea35162ac67903ea437fe085af662cedd554e6a7ce6` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 15 |
| `mcp__sourcegraph__sg_keyword_search` | 11 |
| `mcp__sourcegraph__sg_read_file` | 7 |
| `Write` | 5 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_nls_search` | 2 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
