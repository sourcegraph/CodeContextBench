# sgonly_k8s-dra-allocation-impact-001 (mcp)

- Run: `ccb_design_haiku_022326`
- Status: `passed`
- Reward: `0.9000`
- Audit JSON: [link](../audits/ccb_design_haiku_022326--mcp--sgonly_k8s-dra-allocation-impact-001.json)
- Trajectory available: `True`
- Transcript available: `True`
- Bundled trajectory: [link](../traces/ccb_design_haiku_022326--mcp--sgonly_k8s-dra-allocation-impact-001/trajectory.json)

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 188.5 |
| Agent execution seconds | 89.2 |
| Input tokens | 3,559,112 |
| Output tokens | 113 |
| Cache tokens | 3,558,626 |
| Tool calls (total) | 23 |
| Tool calls (MCP) | 21 |
| Tool calls (local) | 2 |
| MCP ratio | 0.913 |
| keyword_search calls | 8 |
| nls_search calls | 6 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `3d9bc69bd91ddca9fa6c935a8a70f786c4ceb4e9215e0150621da5f9986ca60c` |
| `trajectory.json` SHA256 | `fafaa0b89c2c6a59639aea7ea18ec0004adfd09e33792668292973e5968341eb` |
| transcript SHA256 | `359e3c88325754326c6767dfbf7ef2ec20a53d2e8da5fb7c64c78d173adba5ed` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 8 |
| `mcp__sourcegraph__sg_nls_search` | 6 |
| `mcp__sourcegraph__sg_read_file` | 6 |
| `Read` | 1 |
| `Write` | 1 |
| `mcp__sourcegraph__sg_find_references` | 1 |

## Parsed Trace Samples

| Tool |
|---|
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_find_references` |
