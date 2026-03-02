# csb_sdlc_secure

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [csb_sdlc_secure_haiku_20260224_213146](../runs/csb_sdlc_secure_haiku_20260224_213146.md) | `mcp-remote-direct` | 2 | 0.250 | 0.500 |
| [csb_sdlc_secure_haiku_20260228_124521](../runs/csb_sdlc_secure_haiku_20260228_124521.md) | `mcp-remote-direct` | 2 | 0.555 | 1.000 |
| [csb_sdlc_secure_haiku_20260302_221730](../runs/csb_sdlc_secure_haiku_20260302_221730.md) | `baseline-local-direct` | 7 | 0.491 | 0.714 |
| [csb_sdlc_secure_haiku_20260302_221730](../runs/csb_sdlc_secure_haiku_20260302_221730.md) | `mcp-remote-direct` | 12 | 0.537 | 0.667 |
| [csb_sdlc_secure_haiku_20260302_224010](../runs/csb_sdlc_secure_haiku_20260302_224010.md) | `baseline-local-direct` | 5 | 0.676 | 1.000 |
| [csb_sdlc_secure_haiku_20260302_224010](../runs/csb_sdlc_secure_haiku_20260302_224010.md) | `mcp-remote-direct` | 4 | 0.627 | 1.000 |
| [csb_sdlc_secure_haiku_20260302_232613](../runs/csb_sdlc_secure_haiku_20260302_232613.md) | `mcp-remote-direct` | 1 | 0.700 | 1.000 |
| [secure_haiku_20260301_071231](../runs/secure_haiku_20260301_071231.md) | `baseline-local-direct` | 8 | 0.777 | 1.000 |
| [secure_haiku_20260301_071231](../runs/secure_haiku_20260301_071231.md) | `mcp-remote-direct` | 20 | 0.767 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [curl-cve-triage-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--curl-cve-triage-001.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-cve-triage-001) | `baseline-local-direct` | `passed` | 0.940 | 5 | 0.000 |
| [mcp_curl-cve-triage-001_nkn2ep](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_curl-cve-triage-001_nkn2ep.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-cve-triage-001) | `mcp-remote-direct` | `passed` | 0.940 | 6 | 0.833 |
| [mcp_curl-cve-triage-001_x1ddf6](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_curl-cve-triage-001_x1ddf6.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-cve-triage-001) | `mcp-remote-direct` | `passed` | 0.940 | 6 | 0.818 |
| [sgonly_curl-cve-triage-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_curl-cve-triage-001.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-cve-triage-001) | `mcp-remote-direct` | `passed` | 0.940 | 6 | 0.750 |
| [curl-vuln-reachability-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--curl-vuln-reachability-001.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-vuln-reachability-001) | `baseline-local-direct` | `passed` | 0.850 | 6 | 0.000 |
| [mcp_curl-vuln-reachability-001_bzcvms](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_curl-vuln-reachability-001_bzcvms.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-vuln-reachability-001) | `mcp-remote-direct` | `passed` | 0.710 | 5 | 0.892 |
| [sgonly_curl-vuln-reachability-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_curl-vuln-reachability-001.html) | [source](../../../benchmarks/csb_sdlc_secure/curl-vuln-reachability-001) | `mcp-remote-direct` | `passed` | 0.760 | 5 | 0.962 |
| [django-audit-trail-implement-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-audit-trail-implement-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-audit-trail-implement-001) | `baseline-local-direct` | `passed` | 0.800 | 5 | 0.000 |
| [mcp_django-audit-trail-implement-001_7oa3dz](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-audit-trail-implement-001_7oa3dz.html) | [source](../../../benchmarks/csb_sdlc_secure/django-audit-trail-implement-001) | `mcp-remote-direct` | `failed` | 0.000 | 5 | - |
| [sgonly_django-audit-trail-implement-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-audit-trail-implement-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-audit-trail-implement-001) | `mcp-remote-direct` | `passed` | 0.550 | 5 | 0.358 |
| [django-cross-team-boundary-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-cross-team-boundary-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-cross-team-boundary-001) | `baseline-local-direct` | `passed` | 0.300 | 5 | 0.000 |
| [mcp_django-cross-team-boundary-001_oxflgu](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-cross-team-boundary-001_oxflgu.html) | [source](../../../benchmarks/csb_sdlc_secure/django-cross-team-boundary-001) | `mcp-remote-direct` | `passed` | 0.800 | 5 | 0.244 |
| [sgonly_django-cross-team-boundary-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-cross-team-boundary-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-cross-team-boundary-001) | `mcp-remote-direct` | `passed` | 0.300 | 5 | 0.361 |
| [django-csrf-session-audit-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--django-csrf-session-audit-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 4 | 0.000 |
| [sgonly_django-csrf-session-audit-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-csrf-session-audit-001.html) | — | `mcp-remote-direct` | `passed` | 0.810 | 4 | 0.957 |
| [django-legacy-dep-vuln-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-legacy-dep-vuln-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-legacy-dep-vuln-001) | `baseline-local-direct` | `failed` | 0.000 | 5 | - |
| [mcp_django-legacy-dep-vuln-001_kgnuuj](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-legacy-dep-vuln-001_kgnuuj.html) | [source](../../../benchmarks/csb_sdlc_secure/django-legacy-dep-vuln-001) | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.262 |
| [sgonly_django-legacy-dep-vuln-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-legacy-dep-vuln-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-legacy-dep-vuln-001) | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.279 |
| [django-policy-enforcement-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--django-policy-enforcement-001.html) | — | `baseline-local-direct` | `passed` | 0.850 | 4 | 0.000 |
| [sgonly_django-policy-enforcement-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-policy-enforcement-001.html) | — | `mcp-remote-direct` | `passed` | 0.900 | 4 | 0.169 |
| [django-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-repo-scoped-access-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-repo-scoped-access-001) | `baseline-local-direct` | `passed` | 1.000 | 5 | 0.000 |
| [mcp_django-repo-scoped-access-001_nuvyyn](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-repo-scoped-access-001_nuvyyn.html) | [source](../../../benchmarks/csb_sdlc_secure/django-repo-scoped-access-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [mcp_django-repo-scoped-access-001_cinbn0](../tasks/csb_sdlc_secure_haiku_20260302_232613--mcp-remote-direct--mcp_django-repo-scoped-access-001_cinbn0.html) | [source](../../../benchmarks/csb_sdlc_secure/django-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 0.700 | 6 | 0.179 |
| [sgonly_django-repo-scoped-access-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-repo-scoped-access-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.570 |
| [django-role-based-access-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-role-based-access-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-role-based-access-001) | `baseline-local-direct` | `passed` | 0.400 | 5 | 0.000 |
| [mcp_django-role-based-access-001_3ryxq7](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-role-based-access-001_3ryxq7.html) | [source](../../../benchmarks/csb_sdlc_secure/django-role-based-access-001) | `mcp-remote-direct` | `passed` | 0.900 | 5 | 0.323 |
| [mcp_django-role-based-access-001_2ERzmK](../tasks/csb_sdlc_secure_haiku_20260224_213146--mcp-remote-direct--mcp_django-role-based-access-001_2ERzmK.html) | [source](../../../benchmarks/csb_sdlc_secure/django-role-based-access-001) | `mcp-remote-direct` | `failed` | 0.000 | 5 | 0.452 |
| [sgonly_django-role-based-access-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-role-based-access-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-role-based-access-001) | `mcp-remote-direct` | `passed` | 0.700 | 5 | 0.364 |
| [django-sensitive-file-exclusion-001](../tasks/csb_sdlc_secure_haiku_20260302_221730--baseline-local-direct--django-sensitive-file-exclusion-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-sensitive-file-exclusion-001) | `baseline-local-direct` | `failed` | 0.000 | 5 | - |
| [mcp_django-sensitive-file-exclusion-001_c7krv8](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_django-sensitive-file-exclusion-001_c7krv8.html) | [source](../../../benchmarks/csb_sdlc_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.178 |
| [mcp_django-sensitive-file-exclusion-001_I216lD](../tasks/csb_sdlc_secure_haiku_20260224_213146--mcp-remote-direct--mcp_django-sensitive-file-exclusion-001_I216lD.html) | [source](../../../benchmarks/csb_sdlc_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | `passed` | 0.500 | 5 | 0.352 |
| [sgonly_django-sensitive-file-exclusion-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_django-sensitive-file-exclusion-001.html) | [source](../../../benchmarks/csb_sdlc_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.254 |
| [envoy-cve-triage-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--envoy-cve-triage-001.html) | — | `baseline-local-direct` | `passed` | 0.900 | 4 | 0.000 |
| [sgonly_envoy-cve-triage-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_envoy-cve-triage-001.html) | — | `mcp-remote-direct` | `passed` | 0.940 | 4 | 0.913 |
| [envoy-vuln-reachability-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--envoy-vuln-reachability-001.html) | — | `baseline-local-direct` | `passed` | 0.500 | 4 | 0.000 |
| [mcp_envoy-vuln-reachability-001_xNDUVv](../tasks/csb_sdlc_secure_haiku_20260228_124521--mcp-remote-direct--mcp_envoy-vuln-reachability-001_xNDUVv.html) | — | `mcp-remote-direct` | `passed` | 0.660 | 5 | 0.944 |
| [sgonly_envoy-vuln-reachability-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_envoy-vuln-reachability-001.html) | — | `mcp-remote-direct` | `passed` | 0.660 | 5 | 0.889 |
| [flipt-degraded-context-fix-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--flipt-degraded-context-fix-001.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-degraded-context-fix-001) | `baseline-local-direct` | `passed` | 0.250 | 6 | 0.000 |
| [mcp_flipt-degraded-context-fix-001_zka1nq](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_flipt-degraded-context-fix-001_zka1nq.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-degraded-context-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [mcp_flipt-degraded-context-fix-001_glgbpu](../tasks/csb_sdlc_secure_haiku_20260228_124521--mcp-remote-direct--mcp_flipt-degraded-context-fix-001_glgbpu.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-degraded-context-fix-001) | `mcp-remote-direct` | `passed` | 0.450 | 6 | 0.271 |
| [sgonly_flipt-degraded-context-fix-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_flipt-degraded-context-fix-001.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-degraded-context-fix-001) | `mcp-remote-direct` | `passed` | 0.600 | 6 | 0.468 |
| [flipt-repo-scoped-access-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--flipt-repo-scoped-access-001.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-repo-scoped-access-001) | `baseline-local-direct` | `passed` | 0.850 | 6 | 0.000 |
| [mcp_flipt-repo-scoped-access-001_prpacb](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_flipt-repo-scoped-access-001_prpacb.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 0.500 | 6 | 0.212 |
| [mcp_flipt-repo-scoped-access-001_ledgw0](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_flipt-repo-scoped-access-001_ledgw0.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 0.500 | 6 | 0.190 |
| [sgonly_flipt-repo-scoped-access-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_flipt-repo-scoped-access-001.html) | [source](../../../benchmarks/csb_sdlc_secure/flipt-repo-scoped-access-001) | `mcp-remote-direct` | `passed` | 0.500 | 6 | 0.118 |
| [golang-net-cve-triage-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--golang-net-cve-triage-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 4 | 0.000 |
| [sgonly_golang-net-cve-triage-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_golang-net-cve-triage-001.html) | — | `mcp-remote-direct` | `passed` | 0.800 | 4 | 0.917 |
| [grpcurl-transitive-vuln-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--grpcurl-transitive-vuln-001.html) | [source](../../../benchmarks/csb_sdlc_secure/grpcurl-transitive-vuln-001) | `baseline-local-direct` | `passed` | 0.670 | 6 | 0.000 |
| [mcp_grpcurl-transitive-vuln-001_6gpxwc](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_grpcurl-transitive-vuln-001_6gpxwc.html) | [source](../../../benchmarks/csb_sdlc_secure/grpcurl-transitive-vuln-001) | `mcp-remote-direct` | `passed` | 0.590 | 6 | 0.952 |
| [mcp_grpcurl-transitive-vuln-001_rzkvha](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_grpcurl-transitive-vuln-001_rzkvha.html) | [source](../../../benchmarks/csb_sdlc_secure/grpcurl-transitive-vuln-001) | `mcp-remote-direct` | `passed` | 0.670 | 6 | 0.952 |
| [sgonly_grpcurl-transitive-vuln-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_grpcurl-transitive-vuln-001.html) | [source](../../../benchmarks/csb_sdlc_secure/grpcurl-transitive-vuln-001) | `mcp-remote-direct` | `passed` | 0.670 | 6 | 0.889 |
| [kafka-sasl-auth-audit-001](../tasks/csb_sdlc_secure_haiku_20260302_224010--baseline-local-direct--kafka-sasl-auth-audit-001.html) | [source](../../../benchmarks/csb_sdlc_secure/kafka-sasl-auth-audit-001) | `baseline-local-direct` | `passed` | 0.760 | 6 | 0.000 |
| [mcp_kafka-sasl-auth-audit-001_2qqvgn](../tasks/csb_sdlc_secure_haiku_20260302_221730--mcp-remote-direct--mcp_kafka-sasl-auth-audit-001_2qqvgn.html) | [source](../../../benchmarks/csb_sdlc_secure/kafka-sasl-auth-audit-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [mcp_kafka-sasl-auth-audit-001_6xs9ox](../tasks/csb_sdlc_secure_haiku_20260302_224010--mcp-remote-direct--mcp_kafka-sasl-auth-audit-001_6xs9ox.html) | [source](../../../benchmarks/csb_sdlc_secure/kafka-sasl-auth-audit-001) | `mcp-remote-direct` | `passed` | 0.400 | 6 | 0.960 |
| [sgonly_kafka-sasl-auth-audit-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_kafka-sasl-auth-audit-001.html) | [source](../../../benchmarks/csb_sdlc_secure/kafka-sasl-auth-audit-001) | `mcp-remote-direct` | `passed` | 0.860 | 6 | 0.960 |
| [kafka-vuln-reachability-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--kafka-vuln-reachability-001.html) | — | `baseline-local-direct` | `passed` | 0.880 | 4 | 0.000 |
| [sgonly_kafka-vuln-reachability-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_kafka-vuln-reachability-001.html) | — | `mcp-remote-direct` | `passed` | 0.900 | 4 | 0.955 |
| [postgres-client-auth-audit-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--postgres-client-auth-audit-001.html) | — | `baseline-local-direct` | `passed` | 0.730 | 4 | 0.000 |
| [sgonly_postgres-client-auth-audit-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_postgres-client-auth-audit-001.html) | — | `mcp-remote-direct` | `passed` | 0.790 | 4 | 0.925 |
| [wish-transitive-vuln-001](../tasks/secure_haiku_20260301_071231--baseline-local-direct--wish-transitive-vuln-001.html) | — | `baseline-local-direct` | `passed` | 0.760 | 4 | 0.000 |
| [sgonly_wish-transitive-vuln-001](../tasks/secure_haiku_20260301_071231--mcp-remote-direct--sgonly_wish-transitive-vuln-001.html) | — | `mcp-remote-direct` | `passed` | 0.670 | 4 | 0.923 |

## Multi-Run Variance

Tasks with multiple valid runs (24 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| curl-cve-triage-001 | [source](../../../benchmarks/csb_sdlc_secure/curl-cve-triage-001) | `baseline-local-direct` | 4 | 0.705 | 0.470 | 0.940, 0.000, 0.940, 0.940 |
| curl-cve-triage-001 | [source](../../../benchmarks/csb_sdlc_secure/curl-cve-triage-001) | `mcp-remote-direct` | 5 | 0.940 | 0.000 | 0.940, 0.940, 0.940, 0.940, 0.940 |
| curl-vuln-reachability-001 | [source](../../../benchmarks/csb_sdlc_secure/curl-vuln-reachability-001) | `baseline-local-direct` | 4 | 0.865 | 0.030 | 0.910, 0.850, 0.850, 0.850 |
| curl-vuln-reachability-001 | [source](../../../benchmarks/csb_sdlc_secure/curl-vuln-reachability-001) | `mcp-remote-direct` | 4 | 0.733 | 0.100 | 0.850, 0.610, 0.760, 0.710 |
| django-audit-trail-implement-001 | [source](../../../benchmarks/csb_sdlc_secure/django-audit-trail-implement-001) | `baseline-local-direct` | 4 | 0.725 | 0.218 | 0.550, 1.000, 0.550, 0.800 |
| django-audit-trail-implement-001 | [source](../../../benchmarks/csb_sdlc_secure/django-audit-trail-implement-001) | `mcp-remote-direct` | 3 | 0.550 | 0.000 | 0.550, 0.550, 0.550 |
| django-cross-team-boundary-001 | [source](../../../benchmarks/csb_sdlc_secure/django-cross-team-boundary-001) | `baseline-local-direct` | 4 | 0.475 | 0.350 | 0.300, 1.000, 0.300, 0.300 |
| django-cross-team-boundary-001 | [source](../../../benchmarks/csb_sdlc_secure/django-cross-team-boundary-001) | `mcp-remote-direct` | 4 | 0.475 | 0.236 | 0.500, 0.300, 0.300, 0.800 |
| django-legacy-dep-vuln-001 | [source](../../../benchmarks/csb_sdlc_secure/django-legacy-dep-vuln-001) | `baseline-local-direct` | 3 | 0.967 | 0.058 | 0.900, 1.000, 1.000 |
| django-legacy-dep-vuln-001 | [source](../../../benchmarks/csb_sdlc_secure/django-legacy-dep-vuln-001) | `mcp-remote-direct` | 4 | 0.912 | 0.175 | 0.650, 1.000, 1.000, 1.000 |
| django-repo-scoped-access-001 | [source](../../../benchmarks/csb_sdlc_secure/django-repo-scoped-access-001) | `baseline-local-direct` | 4 | 0.875 | 0.250 | 0.500, 1.000, 1.000, 1.000 |
| django-repo-scoped-access-001 | [source](../../../benchmarks/csb_sdlc_secure/django-repo-scoped-access-001) | `mcp-remote-direct` | 4 | 0.775 | 0.150 | 0.700, 0.700, 1.000, 0.700 |
| django-role-based-access-001 | [source](../../../benchmarks/csb_sdlc_secure/django-role-based-access-001) | `baseline-local-direct` | 5 | 0.420 | 0.249 | 0.200, 0.200, 0.500, 0.800, 0.400 |
| django-role-based-access-001 | [source](../../../benchmarks/csb_sdlc_secure/django-role-based-access-001) | `mcp-remote-direct` | 4 | 0.650 | 0.451 | 0.000, 1.000, 0.700, 0.900 |
| django-sensitive-file-exclusion-001 | [source](../../../benchmarks/csb_sdlc_secure/django-sensitive-file-exclusion-001) | `baseline-local-direct` | 4 | 0.900 | 0.116 | 0.800, 0.800, 1.000, 1.000 |
| django-sensitive-file-exclusion-001 | [source](../../../benchmarks/csb_sdlc_secure/django-sensitive-file-exclusion-001) | `mcp-remote-direct` | 5 | 0.800 | 0.274 | 1.000, 0.500, 0.500, 1.000, 1.000 |
| flipt-degraded-context-fix-001 | [source](../../../benchmarks/csb_sdlc_secure/flipt-degraded-context-fix-001) | `baseline-local-direct` | 5 | 0.320 | 0.157 | 0.600, 0.250, 0.250, 0.250, 0.250 |
| flipt-degraded-context-fix-001 | [source](../../../benchmarks/csb_sdlc_secure/flipt-degraded-context-fix-001) | `mcp-remote-direct` | 4 | 0.438 | 0.144 | 0.250, 0.450, 0.450, 0.600 |
| flipt-repo-scoped-access-001 | [source](../../../benchmarks/csb_sdlc_secure/flipt-repo-scoped-access-001) | `baseline-local-direct` | 5 | 0.540 | 0.216 | 0.600, 0.500, 0.250, 0.500, 0.850 |
| flipt-repo-scoped-access-001 | [source](../../../benchmarks/csb_sdlc_secure/flipt-repo-scoped-access-001) | `mcp-remote-direct` | 5 | 0.540 | 0.055 | 0.600, 0.600, 0.500, 0.500, 0.500 |
| grpcurl-transitive-vuln-001 | [source](../../../benchmarks/csb_sdlc_secure/grpcurl-transitive-vuln-001) | `baseline-local-direct` | 4 | 0.502 | 0.335 | 0.000, 0.670, 0.670, 0.670 |
| grpcurl-transitive-vuln-001 | [source](../../../benchmarks/csb_sdlc_secure/grpcurl-transitive-vuln-001) | `mcp-remote-direct` | 5 | 0.654 | 0.036 | 0.670, 0.670, 0.670, 0.590, 0.670 |
| kafka-sasl-auth-audit-001 | [source](../../../benchmarks/csb_sdlc_secure/kafka-sasl-auth-audit-001) | `baseline-local-direct` | 5 | 0.724 | 0.185 | 0.860, 0.800, 0.400, 0.800, 0.760 |
| kafka-sasl-auth-audit-001 | [source](../../../benchmarks/csb_sdlc_secure/kafka-sasl-auth-audit-001) | `mcp-remote-direct` | 4 | 0.720 | 0.218 | 0.760, 0.860, 0.860, 0.400 |
