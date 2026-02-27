# sgonly_envoy-arch-doc-gen-001 (mcp-remote-direct)

- Run: `document_haiku_20260223_164240`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/document_haiku_20260223_164240--mcp-remote-direct--sgonly_envoy-arch-doc-gen-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 191.6 |
| Agent execution seconds | 124.2 |
| Input tokens | 1,816,721 |
| Output tokens | 70 |
| Cache tokens | 1,816,370 |
| Tool calls (total) | 18 |
| Tool calls (MCP) | 15 |
| Tool calls (local) | 3 |
| MCP ratio | 0.833 |
| keyword_search calls | 6 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `bda7902b843d31d379805655160cda6f3997c65fa28ade601eb54f377d52b224` |
| `trajectory.json` SHA256 | `ec11f6a80f1a9dff9b04c0694ddaac146d52099f3eac5ed566f1096bca6e23cc` |
| transcript SHA256 | `6ea0b531202a1397b0c6d696474bda2b75d4c4b0b75f8c93841a77cada8ae98e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `mcp__sourcegraph__sg_read_file` | 6 |
| `Bash` | 2 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
