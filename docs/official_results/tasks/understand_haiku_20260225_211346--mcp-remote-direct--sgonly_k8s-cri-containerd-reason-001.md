# sgonly_k8s-cri-containerd-reason-001 (mcp-remote-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `0.8500`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_k8s-cri-containerd-reason-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 280.8 |
| Agent execution seconds | 142.6 |
| Input tokens | 3,097,973 |
| Output tokens | 101 |
| Cache tokens | 3,097,337 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 24 |
| Tool calls (local) | 4 |
| MCP ratio | 0.857 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `eb8d3dd7e9bcee3548e8ee02cde8b1c5be92ccb3264ab67cfe5862f49d4cf361` |
| `trajectory.json` SHA256 | `472a7ed271486ffd8d2d54047328f3e55f4df61485b6f1e7d4f32c8db77c814c` |
| transcript SHA256 | `ba69e0c5447e29509cd8793edde3414637e8fff9838ec42d8ae75444f7fbd29e` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_list_files` | 12 |
| `mcp__sourcegraph__sg_read_file` | 7 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `Grep` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `Read` |
| `Grep` |
| `Grep` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
