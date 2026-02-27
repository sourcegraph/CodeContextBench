# ccx-config-trace-010 (mcp)

- Run: `ccb_mcp_crossrepo_tracing_haiku_022126`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_mcp_crossrepo_tracing_haiku_022126--mcp--ccx-config-trace-010.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_mcp_crossrepo_tracing_haiku_022126--mcp--ccx-config-trace-010/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1810.4 |
| Agent execution seconds | 1713.2 |
| Input tokens | 399,009 |
| Output tokens | 44 |
| Cache tokens | 398,874 |
| Tool calls (total) | 4 |
| Tool calls (MCP) | 3 |
| Tool calls (local) | 1 |
| MCP ratio | 0.750 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `e5ea3ffa4cbf6ee3cf34ec6db6f9200f196f8928bf565436569fa958b2cb1bcc` |
| `trajectory.json` SHA256 | `939edf331cff34b60cd8b130a73dcae17a63bd676cbd350e69aa6edc7793d889` |
| transcript SHA256 | `d40dcfa92464f78edaae810943a14def631e9046667eaaad671cdab2101a1ca6` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Write` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |
| `mcp__sourcegraph__sg_read_file` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `Write` |
