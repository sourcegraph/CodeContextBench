# sgonly_docgen-inline-001 (mcp-remote-direct)

- Run: `ccb_document_haiku_022326`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/ccb_document_haiku_022326--mcp--sgonly_docgen-inline-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_document_haiku_022326--mcp--sgonly_docgen-inline-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 181.3 |
| Agent execution seconds | 87.3 |
| Input tokens | 1,482,661 |
| Output tokens | 88 |
| Cache tokens | 1,482,270 |
| Tool calls (total) | 14 |
| Tool calls (MCP) | 5 |
| Tool calls (local) | 9 |
| MCP ratio | 0.357 |
| keyword_search calls | 1 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `769b48cb08ab4bdf71b631f05223a1f5f6d688b811dda28f3e6931eec2cf15ba` |
| `trajectory.json` SHA256 | `24e9addcce85dee88395a8c815381e16b339eae6b2358462ec4bb4689d3d9895` |
| transcript SHA256 | `dacf8d6285ae7897e21286d1f8afb483eddaf4d21f5d10c8b5d1e771747e6886` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Read` | 5 |
| `mcp__sourcegraph__sg_read_file` | 4 |
| `Write` | 2 |
| `Bash` | 1 |
| `Edit` | 1 |
| `mcp__sourcegraph__sg_keyword_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `Edit` |
| `Bash` |
| `Write` |
| `Write` |
| `Read` |
| `Read` |
| `Read` |
