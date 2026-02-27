# mcp_django-sensitive-file-exclusion-001_I216lD (mcp-remote-direct)

- Run: `ccb_secure_haiku_20260224_213146`
- Status: `passed`
- Reward: `0.5000`
- Audit JSON: [link](../audits/ccb_secure_haiku_20260224_213146--mcp-remote-direct--mcp_django-sensitive-file-exclusion-001_I216lD.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 609.8 |
| Agent execution seconds | 556.7 |
| Input tokens | 12,254,210 |
| Output tokens | 293 |
| Cache tokens | 12,253,350 |
| Tool calls (total) | 54 |
| Tool calls (MCP) | 19 |
| Tool calls (local) | 35 |
| MCP ratio | 0.352 |
| keyword_search calls | 4 |
| nls_search calls | 0 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `a06f0ef28ded052c9fe9a4e0d21fc031d4d8cb6319b4b230bdbbb2f62f27ee72` |
| `trajectory.json` SHA256 | `60b90131fcf199a94c78fc0487b0edf7b5c65cf7ffc0386dfb2f4b59a327723d` |
| transcript SHA256 | `c28f059394852865b380f430c3efa4906826045b6598b1b8bbb6e94eabcefa00` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `Bash` | 25 |
| `mcp__sourcegraph__sg_read_file` | 10 |
| `Write` | 5 |
| `mcp__sourcegraph__sg_keyword_search` | 4 |
| `TodoWrite` | 3 |
| `mcp__sourcegraph__sg_list_files` | 3 |
| `Read` | 2 |
| `mcp__sourcegraph__sg_find_references` | 1 |
| `mcp__sourcegraph__sg_list_repos` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `Bash` |
| `Bash` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_list_repos` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_find_references` |
| `mcp__sourcegraph__sg_read_file` |
| `Bash` |
| `Bash` |
| `mcp__sourcegraph__sg_list_files` |
