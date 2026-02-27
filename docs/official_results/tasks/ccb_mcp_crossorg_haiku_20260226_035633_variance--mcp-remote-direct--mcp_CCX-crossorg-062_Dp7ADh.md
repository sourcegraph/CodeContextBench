# mcp_CCX-crossorg-062_Dp7ADh (mcp-remote-direct)

- Run: `ccb_mcp_crossorg_haiku_20260226_035633_variance`
- Status: `passed`
- Reward: `0.7111`
- Audit JSON: [link](../audits/ccb_mcp_crossorg_haiku_20260226_035633_variance--mcp-remote-direct--mcp_CCX-crossorg-062_Dp7ADh.json)
- Trajectory available: `True`
- Transcript available: `True`

## Metrics

| Field | Value |
|---|---:|
| Wall clock seconds | 1554.7 |
| Agent execution seconds | 175.8 |
| Input tokens | 3,031,518 |
| Output tokens | 9,856 |
| Cache tokens | 3,031,005 |
| Tool calls (total) | 28 |
| Tool calls (MCP) | 26 |
| Tool calls (local) | 2 |
| MCP ratio | 0.929 |
| keyword_search calls | 10 |
| nls_search calls | 1 |
| deepsearch calls | 0 |
| `result.json` SHA256 | `f100e6d26a44937be9f4ed5e9a6cf54d27a8e7f4ee62b65306081e564fcf305f` |
| `trajectory.json` SHA256 | `4f8f7e3c809175c87d6af96782fe9ed5f7508cf1a193afc1a76549bb89e49522` |
| transcript SHA256 | `712a3d0b36a69906f54b49ccb64f47fda0b41f9974a5c1cfbe55696d678a147b` |

## Tool Breakdown

| Tool | Calls |
|---|---:|
| `mcp__sourcegraph__sg_keyword_search` | 10 |
| `mcp__sourcegraph__sg_read_file` | 10 |
| `mcp__sourcegraph__sg_list_files` | 5 |
| `Read` | 1 |
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
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
| `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_read_file` |
