# csb_sdlc_secure_haiku_20260302_224010

## baseline-local-direct

- Valid tasks: `5`
- Mean reward: `0.676`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [curl-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--curl-vuln-reachability-001.html) | `passed` | 0.850 | 0.000 | 24 | traj, tx |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--flipt-degraded-context-fix-001.html) | `passed` | 0.250 | 0.000 | 116 | traj, tx |
| [flipt-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--flipt-repo-scoped-access-001.html) | `passed` | 0.850 | 0.000 | 36 | traj, tx |
| [grpcurl-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--grpcurl-transitive-vuln-001.html) | `passed` | 0.670 | 0.000 | 36 | traj, tx |
| [kafka-sasl-auth-audit-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--kafka-sasl-auth-audit-001.html) | `passed` | 0.760 | 0.000 | 30 | traj, tx |

## mcp-remote-direct

- Valid tasks: `4`
- Mean reward: `0.627`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [mcp_curl-cve-triage-001_x1ddf6](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_curl-cve-triage-001_x1ddf6.html) | `passed` | 0.940 | 0.818 | 11 | traj, tx |
| [mcp_flipt-repo-scoped-access-001_ledgw0](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_flipt-repo-scoped-access-001_ledgw0.html) | `passed` | 0.500 | 0.190 | 42 | traj, tx |
| [mcp_grpcurl-transitive-vuln-001_rzkvha](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_grpcurl-transitive-vuln-001_rzkvha.html) | `passed` | 0.670 | 0.952 | 21 | traj, tx |
| [mcp_kafka-sasl-auth-audit-001_6xs9ox](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_kafka-sasl-auth-audit-001_6xs9ox.html) | `passed` | 0.400 | 0.960 | 25 | traj, tx |
