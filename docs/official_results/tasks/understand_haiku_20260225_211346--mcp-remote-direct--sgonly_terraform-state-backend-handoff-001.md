# sgonly_terraform-state-backend-handoff-001 (mcp-remote-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `0.8300`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 217.3 |
| Agent execution seconds | 143.7 |
| Input tokens | 2,973,389 |
| Output tokens | 119 |
| Cache tokens | 2,972,770 |
| Tool calls (total) | 32 |
| Tool calls (MCP) | 31 |
| Tool calls (local) | 1 |
| MCP ratio | 0.969 |
| keyword_search calls | 8 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f33de82969ae75f9941de292a99ea328f79880b22dfd0f55d630ab7f64b523cf` |
| `trajectory.json` SHA256 | `5ff1436d45f7bad1b1eed862e104ab60ef0655991986a75137db447899cea842` |
| transcript SHA256 | `7c63a8390f1158abe9ed1a5fdd9c8a963e11ab6fdc4f92c1c84a51778dce5cac` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 16 |
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `mcp__sourcegraph__sg_list_files` | 6 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
