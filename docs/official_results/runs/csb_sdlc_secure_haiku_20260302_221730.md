# csb_sdlc_secure_haiku_20260302_221730

## baseline-local-direct

- Valid tasks: `12`
- Mean reward: `0.416`
- Pass rate: `0.667`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [curl-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--curl-vuln-reachability-001.html) | `failed` | 0.000 | - | - | traj, tx |
| [django-legacy-dep-vuln-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-legacy-dep-vuln-001.html) | `failed` | 0.000 | - | - | traj, tx |
| [django-sensitive-file-exclusion-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-sensitive-file-exclusion-001.html) | `failed` | 0.000 | - | - | traj, tx |
| [grpcurl-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--grpcurl-transitive-vuln-001.html) | `failed` | 0.000 | - | - | traj, tx |
| [curl-cve-triage-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--curl-cve-triage-001.html) | `passed` | 0.940 | 0.000 | 9 | traj, tx |
| [django-audit-trail-implement-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-audit-trail-implement-001.html) | `passed` | 0.800 | 0.000 | 67 | traj, tx |
| [django-cross-team-boundary-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-cross-team-boundary-001.html) | `passed` | 0.300 | 0.000 | 52 | traj, tx |
| [django-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-repo-scoped-access-001.html) | `passed` | 1.000 | 0.000 | 55 | traj, tx |
| [django-role-based-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-role-based-access-001.html) | `passed` | 0.400 | 0.000 | 94 | traj, tx |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--flipt-degraded-context-fix-001.html) | `passed` | 0.250 | 0.000 | 107 | traj, tx |
| [flipt-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--flipt-repo-scoped-access-001.html) | `passed` | 0.500 | 0.000 | 32 | traj, tx |
| [kafka-sasl-auth-audit-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--kafka-sasl-auth-audit-001.html) | `passed` | 0.800 | 0.000 | 30 | traj, tx |

## mcp-remote-direct

- Valid tasks: `12`
- Mean reward: `0.537`
- Pass rate: `0.667`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [mcp_django-audit-trail-implement-001_7oa3dz](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-audit-trail-implement-001_7oa3dz.html) | `failed` | 0.000 | - | - | traj, tx |
| [mcp_django-repo-scoped-access-001_nuvyyn](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-repo-scoped-access-001_nuvyyn.html) | `failed` | 0.000 | - | - | traj, tx |
| [mcp_flipt-degraded-context-fix-001_zka1nq](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_flipt-degraded-context-fix-001_zka1nq.html) | `failed` | 0.000 | - | - | traj, tx |
| [mcp_kafka-sasl-auth-audit-001_2qqvgn](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_kafka-sasl-auth-audit-001_2qqvgn.html) | `failed` | 0.000 | - | - | traj, tx |
| [mcp_curl-cve-triage-001_nkn2ep](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_curl-cve-triage-001_nkn2ep.html) | `passed` | 0.940 | 0.833 | 6 | traj, tx |
| [mcp_curl-vuln-reachability-001_bzcvms](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_curl-vuln-reachability-001_bzcvms.html) | `passed` | 0.710 | 0.892 | 37 | traj, tx |
| [mcp_django-cross-team-boundary-001_oxflgu](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-cross-team-boundary-001_oxflgu.html) | `passed` | 0.800 | 0.244 | 78 | traj, tx |
| [mcp_django-legacy-dep-vuln-001_kgnuuj](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-legacy-dep-vuln-001_kgnuuj.html) | `passed` | 1.000 | 0.262 | 42 | traj, tx |
| [mcp_django-role-based-access-001_3ryxq7](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-role-based-access-001_3ryxq7.html) | `passed` | 0.900 | 0.323 | 93 | traj, tx |
| [mcp_django-sensitive-file-exclusion-001_c7krv8](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-sensitive-file-exclusion-001_c7krv8.html) | `passed` | 1.000 | 0.178 | 101 | traj, tx |
| [mcp_flipt-repo-scoped-access-001_prpacb](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_flipt-repo-scoped-access-001_prpacb.html) | `passed` | 0.500 | 0.212 | 52 | traj, tx |
| [mcp_grpcurl-transitive-vuln-001_6gpxwc](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_grpcurl-transitive-vuln-001_6gpxwc.html) | `passed` | 0.590 | 0.952 | 21 | traj, tx |
