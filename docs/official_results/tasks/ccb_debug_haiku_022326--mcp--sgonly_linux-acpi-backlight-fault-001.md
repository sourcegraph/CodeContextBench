# sgonly_linux-acpi-backlight-fault-001 (mcp)

- Run: `ccb_debug_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_debug_haiku_022326--mcp--sgonly_linux-acpi-backlight-fault-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_debug_haiku_022326--mcp--sgonly_linux-acpi-backlight-fault-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 210.3 |
| Agent execution seconds | 145.2 |
| Input tokens | 3,250,556 |
| Output tokens | 111 |
| Cache tokens | 3,249,953 |
| Tool calls (total) | 21 |
| Tool calls (MCP) | 10 |
| Tool calls (local) | 11 |
| MCP ratio | 0.476 |
| keyword_search calls | 5 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `03e37837ff895b6b293e9c737145cabab629a7c298369999b95cb21afd5c7eba` |
| `trajectory.json` SHA256 | `361b8bdfcb3bc360afb6c606edd14e8c2241fc106df1ab85b43235ca83e05e13` |
| transcript SHA256 | `a310b9b0ae01225577399cebb3059f14b861675412bc041e369b24dc03fc3e8d` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `TodoWrite` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 5 |
| `mcp__sourcegraph__sg_read_file` | 5 |
| `Bash` | 4 |
| `Read` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `TodoWrite` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
