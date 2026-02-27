# sgonly_k8s-dra-scheduler-event-fix-001 (mcp)

- Run: `ccb_fix_haiku_022326`
- Status: `passed`
- Reward: `0.7500`
- Audit JSON: [link](../audits/ccb_fix_haiku_022326--mcp--sgonly_k8s-dra-scheduler-event-fix-001.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 249.0 |
| Agent execution seconds | 122.7 |
| Input tokens | 4,053,837 |
| Output tokens | 137 |
| Cache tokens | 4,053,276 |
| Tool calls (total) | 21 |
| Tool calls (MCP) | 17 |
| Tool calls (local) | 4 |
| MCP ratio | 0.810 |
| keyword_search calls | 6 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `82e7c42c7cc3e32cf053f3539e8aa7263792e8e9729d874e567ced37abd48ae6` |
| `trajectory.json` SHA256 | `ac666dec93d8edaadac06e4e5bde361c04006c4521ba4b468f6fb845adf8c153` |
| transcript SHA256 | `e14fefe2804ef58b0369a4b65ea01107115261829c12f1cfe329dd1fd570d1a0` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_read_file` | 9 |
| `mcp__sourcegraph__sg_keyword_search` | 6 |
| `TodoWrite` | 2 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_list_files` | 1 |
| `mcp__sourcegraph__sg_nls_search` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_list_files` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_keyword_search` |
