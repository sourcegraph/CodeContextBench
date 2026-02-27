# sgonly_envoy-migration-doc-gen-001 (mcp)

- Run: `ccb_document_haiku_022326`
- Status: `passed`
- Reward: `0.7900`
- Audit JSON: [link](../audits/ccb_document_haiku_022326--mcp--sgonly_envoy-migration-doc-gen-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 189.7 |
| Agent execution seconds | 123.1 |
| Input tokens | 2,359,347 |
| Output tokens | 145 |
| Cache tokens | 2,358,842 |
| Tool calls (total) | 23 |
| Tool calls (MCP) | 19 |
| Tool calls (local) | 4 |
| MCP ratio | 0.826 |
| keyword_search calls | 2 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a4d914fcaf3e988afd9be60499ba502d0eded3fbdbc6424e5fe530af8445eb6d` |
| `trajectory.json` SHA256 | `04cafaa9d0c25eb908a42c325fed1371c76ee0a796246f25519b004093c7a05b` |
| transcript SHA256 | `52c2048d1cb89e51a7551052ab987dbcf1ec9d15828d021e1c5771b9e49f6ce4` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 12 |
| `mcp__sourcegraph__sg_list_files` | 4 |
| `Bash` | 2 |
| `mcp__sourcegraph__sg_keyword_search` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
