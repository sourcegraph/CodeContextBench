# sgonly_teleport-ssh-regression-prove-001 (mcp-remote-direct)

- Run: `ccb_debug_haiku_022326`
- Status: `failed`
- Reward: `0.0000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_teleport-ssh-regression-prove-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_teleport-ssh-regression-prove-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 866.7 |
| Agent execution seconds | 727.4 |
| Input tokens | 10,622,621 |
| Output tokens | 285 |
| Cache tokens | 10,621,527 |
| Tool calls (total) | 54 |
| Tool calls (MCP) | 20 |
| Tool calls (local) | 34 |
| MCP ratio | 0.370 |
| keyword_search calls | 8 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `694a6101b4632f8463e1c95189ee284af0ded50565c21cd123b1cb5486046a75` |
| `trajectory.json` SHA256 | `fbfa7767cd979a693ac26c8248434fda7a481251e8f93fda7f62f487b01e7619` |
| transcript SHA256 | `41da11cb04a11b64ce0382d6fa48420c43ce73cb71ea4494f8ae658becb5a4a5` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 24 |
| `mcp__sourcegraph__sg_read_file` | 11 |
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `Write` | 4 |
| `Edit` | 3 |
| `TodoWrite` | 2 |
| `Read` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
