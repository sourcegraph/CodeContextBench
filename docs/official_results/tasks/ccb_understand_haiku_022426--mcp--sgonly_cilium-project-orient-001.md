# sgonly_cilium-project-orient-001 (mcp)

- Run: `ccb_understand_haiku_022426`
- Status: `passed`
- Reward: `0.9600`
- Audit JSON: [link](../audits/ccb_understand_haiku_022426--mcp--sgonly_cilium-project-orient-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_understand_haiku_022426--mcp--sgonly_cilium-project-orient-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 262.2 |
| Agent execution seconds | 110.8 |
| Input tokens | 3,648,915 |
| Output tokens | 119 |
| Cache tokens | 3,648,253 |
| Tool calls (total) | 39 |
| Tool calls (MCP) | 38 |
| Tool calls (local) | 1 |
| MCP ratio | 0.974 |
| keyword_search calls | 16 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `74cf4792049272bd4ca8715050f521fa8531c0532af7ded1540e0d814c7c8dca` |
| `trajectory.json` SHA256 | `258728e5498609dec4e857f463c5c535b8bf86ea7155493ea4de38c0b8ff1258` |
| transcript SHA256 | `44c398e0e34c65dbd920fbf875c679b9731e5edde09615f228a5c011215a4cc7` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 16 |
| `mcp__sourcegraph__sg_read_file` | 12 |
| `mcp__sourcegraph__sg_list_files` | 10 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
