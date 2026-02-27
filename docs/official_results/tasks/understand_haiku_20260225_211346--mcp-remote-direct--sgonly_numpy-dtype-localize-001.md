# sgonly_numpy-dtype-localize-001 (mcp-remote-direct)

- Run: `understand_haiku_20260225_211346`
- Status: `passed`
- Reward: `1.0000`
- Audit JSON: [link](../audits/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_numpy-dtype-localize-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/understand_haiku_20260225_211346--mcp-remote-direct--sgonly_numpy-dtype-localize-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 291.8 |
| Agent execution seconds | 181.4 |
| Input tokens | 6,107,348 |
| Output tokens | 209 |
| Cache tokens | 6,106,324 |
| Tool calls (total) | 47 |
| Tool calls (MCP) | 45 |
| Tool calls (local) | 2 |
| MCP ratio | 0.957 |
| keyword_search calls | 18 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `6e7d279be19a83aeafea5f0c340ab12271deeb7c4f0e6a3f850da78d9c1d6761` |
| `trajectory.json` SHA256 | `a065ddb750c96602b3822e06f017142e2d3133a0cff7c9ef6c747dd9541ce063` |
| transcript SHA256 | `bb65b42a603cf35d44929cda40fd08a4cf0e07739536c091d0dd477de3a45d41` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 21 |
| `mcp__sourcegraph__sg_keyword_search` | 18 |
| `mcp__sourcegraph__sg_list_repos` | 4 |
| `mcp__sourcegraph__sg_list_files` | 2 |
| `Bash` | 1 |
| `Write` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
