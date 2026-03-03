# csb_sdlc/csb_sdlc_secure

## baseline-local-direct

- Valid tasks: `17`
- Mean reward: `0.639`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [curl-cve-triage-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--curl-cve-triage-001--acd70b483e.html) | `passed` | 0.940 | 0.000 | 27 | traj, tx |
| [curl-vuln-reachability-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--curl-vuln-reachability-001--75070f864d.html) | `passed` | 0.850 | 0.000 | 24 | traj, tx |
| [django-audit-trail-implement-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-audit-trail-implement-001--50fb4a68e6.html) | `passed` | 0.750 | 0.000 | 39 | traj, tx |
| [django-audit-trail-implement-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-audit-trail-implement-001--fd11ec01b0.html) | `passed` | 0.550 | 0.000 | 73 | traj, tx |
| [django-cross-team-boundary-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-cross-team-boundary-001--8d891fd048.html) | `passed` | 0.500 | 0.000 | 56 | traj, tx |
| [django-cross-team-boundary-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-cross-team-boundary-001--57036164d0.html) | `passed` | 0.300 | 0.000 | 83 | traj, tx |
| [django-legacy-dep-vuln-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-legacy-dep-vuln-001--7103dab446.html) | `passed` | 1.000 | 0.000 | 32 | traj, tx |
| [django-legacy-dep-vuln-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-legacy-dep-vuln-001--21ddda9bfb.html) | `passed` | 0.900 | 0.000 | 31 | traj, tx |
| [django-repo-scoped-access-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-repo-scoped-access-001--4e4d1e8acd.html) | `passed` | 0.700 | 0.000 | 71 | traj, tx |
| [django-repo-scoped-access-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-repo-scoped-access-001--d693cdae22.html) | `passed` | 0.500 | 0.000 | 44 | traj, tx |
| [django-role-based-access-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-role-based-access-001--17558a8eb9.html) | `passed` | 0.200 | 0.000 | 132 | traj, tx |
| [django-sensitive-file-exclusion-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--django-sensitive-file-exclusion-001--3855f5509e.html) | `passed` | 0.800 | 0.000 | 86 | traj, tx |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--flipt-degraded-context-fix-001--7bdc2a2958.html) | `passed` | 0.250 | 0.000 | 116 | traj, tx |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--flipt-degraded-context-fix-001--0bcdddd7d4.html) | `passed` | 0.600 | 0.000 | 54 | traj, tx |
| [flipt-repo-scoped-access-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--flipt-repo-scoped-access-001--02f85ccde7.html) | `passed` | 0.600 | 0.000 | 26 | traj, tx |
| [grpcurl-transitive-vuln-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--grpcurl-transitive-vuln-001--6126cdfb7a.html) | `passed` | 0.670 | 0.000 | 36 | traj, tx |
| [kafka-sasl-auth-audit-001](../tasks/csb_sdlc-csb_sdlc_secure--baseline--kafka-sasl-auth-audit-001--92ce893a9e.html) | `passed` | 0.760 | 0.000 | 30 | traj, tx |

## mcp-remote-direct

- Valid tasks: `17`
- Mean reward: `0.598`
- Pass rate: `0.941`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [mcp_django-role-based-access-001_2ERzmK](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_django-role-based-access-001_2ERzmK--77b3576281.html) | `failed` | 0.000 | 0.452 | 84 | traj, tx |
| [mcp_django-audit-trail-implement-001_vnpld0](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_django-audit-trail-implement-001_vnpld0--af0f46f6f4.html) | `passed` | 0.550 | 0.236 | 123 | traj, tx |
| [mcp_django-cross-team-boundary-001_kmm7u4](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_django-cross-team-boundary-001_kmm7u4--50a00db7a1.html) | `passed` | 0.500 | 0.153 | 85 | traj, tx |
| [mcp_django-legacy-dep-vuln-001_ey2oju](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_django-legacy-dep-vuln-001_ey2oju--7f89c65a0d.html) | `passed` | 1.000 | 0.170 | 53 | traj, tx |
| [mcp_django-repo-scoped-access-001_ln2iim](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_django-repo-scoped-access-001_ln2iim--99b4d8e0a8.html) | `passed` | 0.700 | 0.476 | 82 | traj, tx |
| [mcp_django-sensitive-file-exclusion-001_I216lD](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_django-sensitive-file-exclusion-001_I216lD--a6d4935fe6.html) | `passed` | 0.500 | 0.352 | 54 | traj, tx |
| [mcp_flipt-degraded-context-fix-001_glgbpu](../tasks/csb_sdlc-csb_sdlc_secure--mcp--mcp_flipt-degraded-context-fix-001_glgbpu--863f85fe3c.html) | `passed` | 0.450 | 0.271 | 48 | traj, tx |
| [sgonly_curl-cve-triage-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_curl-cve-triage-001--dac2e6e373.html) | `passed` | 0.940 | 0.889 | 9 | traj, tx |
| [sgonly_curl-vuln-reachability-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_curl-vuln-reachability-001--1cfadbc38b.html) | `passed` | 0.850 | 0.960 | 25 | traj, tx |
| [sgonly_django-audit-trail-implement-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_django-audit-trail-implement-001--43015f4fbb.html) | `passed` | 0.550 | 0.351 | 57 | traj, tx |
| [sgonly_django-cross-team-boundary-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_django-cross-team-boundary-001--89eb12183f.html) | `passed` | 0.500 | 0.232 | 56 | traj, tx |
| [sgonly_django-legacy-dep-vuln-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_django-legacy-dep-vuln-001--31ee937e38.html) | `passed` | 0.650 | 0.227 | 44 | traj, tx |
| [sgonly_django-repo-scoped-access-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_django-repo-scoped-access-001--74aed605e2.html) | `passed` | 0.700 | 0.561 | 98 | traj, tx |
| [sgonly_flipt-degraded-context-fix-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_flipt-degraded-context-fix-001--ac399aca7a.html) | `passed` | 0.250 | 0.333 | 36 | traj, tx |
| [sgonly_flipt-repo-scoped-access-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_flipt-repo-scoped-access-001--582f8d59e7.html) | `passed` | 0.600 | 0.184 | 38 | traj, tx |
| [sgonly_grpcurl-transitive-vuln-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_grpcurl-transitive-vuln-001--0434b02744.html) | `passed` | 0.670 | 0.952 | 21 | traj, tx |
| [sgonly_kafka-sasl-auth-audit-001](../tasks/csb_sdlc-csb_sdlc_secure--mcp--sgonly_kafka-sasl-auth-audit-001--b034f79fc9.html) | `passed` | 0.760 | 0.960 | 25 | traj, tx |
