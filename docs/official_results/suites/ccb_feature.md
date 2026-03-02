# csb_sdlc_feature

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [feature_haiku_20260228_220733](../runs/feature_haiku_20260228_220733.md) | `mcp-remote-direct` | 1 | 0.000 | 0.000 |
| [feature_haiku_20260301_071229](../runs/feature_haiku_20260301_071229.md) | `baseline-local-direct` | 20 | 0.656 | 0.900 |
| [feature_haiku_20260301_071229](../runs/feature_haiku_20260301_071229.md) | `mcp-remote-direct` | 19 | 0.608 | 0.895 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [bustub-hyperloglog-impl-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--bustub-hyperloglog-impl-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [sgonly_bustub-hyperloglog-impl-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_bustub-hyperloglog-impl-001.html) | — | `mcp-remote-direct` | `passed` | 0.167 | 4 | 0.165 |
| [camel-fix-protocol-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--camel-fix-protocol-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.330 | 4 | 0.000 |
| [sgonly_camel-fix-protocol-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_camel-fix-protocol-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.340 | 5 | 0.605 |
| [cilium-policy-audit-logger-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--cilium-policy-audit-logger-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_cilium-policy-audit-logger-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_cilium-policy-audit-logger-feat-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.426 |
| [cilium-policy-quota-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--cilium-policy-quota-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_cilium-policy-quota-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_cilium-policy-quota-feat-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.361 |
| [curl-http3-priority-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--curl-http3-priority-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.833 | 5 | 0.000 |
| [sgonly_curl-http3-priority-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_curl-http3-priority-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.833 | 4 | 0.266 |
| [django-rate-limit-middleware-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--django-rate-limit-middleware-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_django-rate-limit-middleware-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_django-rate-limit-middleware-feat-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.171 |
| [envoy-custom-header-filter-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--envoy-custom-header-filter-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 5 | 0.000 |
| [sgonly_envoy-custom-header-filter-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_envoy-custom-header-filter-feat-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.510 |
| [envoy-grpc-server-impl-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--envoy-grpc-server-impl-001.html) | — | `baseline-local-direct` | `passed` | 0.440 | 3 | 0.000 |
| [sgonly_envoy-grpc-server-impl-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_envoy-grpc-server-impl-001.html) | — | `mcp-remote-direct` | `passed` | 0.500 | 3 | 0.938 |
| [flink-pricing-window-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--flink-pricing-window-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.480 | 4 | 0.000 |
| [sgonly_flink-pricing-window-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_flink-pricing-window-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.380 | 4 | 0.253 |
| [k8s-noschedule-taint-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--k8s-noschedule-taint-feat-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 5 | 0.000 |
| [sgonly_k8s-noschedule-taint-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_k8s-noschedule-taint-feat-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 4 | 0.441 |
| [k8s-runtime-object-impl-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--k8s-runtime-object-impl-001.html) | — | `baseline-local-direct` | `passed` | 0.120 | 3 | 0.000 |
| [sgonly_k8s-runtime-object-impl-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_k8s-runtime-object-impl-001.html) | — | `mcp-remote-direct` | `passed` | 0.130 | 3 | 0.706 |
| [numpy-rolling-median-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--numpy-rolling-median-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_numpy-rolling-median-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_numpy-rolling-median-feat-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.379 |
| [pandas-merge-asof-indicator-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--pandas-merge-asof-indicator-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.667 | 3 | 0.000 |
| [sgonly_pandas-merge-asof-indicator-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_pandas-merge-asof-indicator-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.667 | 4 | 0.278 |
| [prometheus-silence-bulk-api-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--prometheus-silence-bulk-api-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.833 | 3 | 0.000 |
| [sgonly_prometheus-silence-bulk-api-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_prometheus-silence-bulk-api-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.833 | 3 | 0.514 |
| [pytorch-gradient-noise-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--pytorch-gradient-noise-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.833 | 3 | 0.000 |
| [sgonly_pytorch-gradient-noise-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_pytorch-gradient-noise-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.833 | 3 | 0.368 |
| [servo-scrollend-event-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--servo-scrollend-event-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.500 | 3 | 0.000 |
| [sgonly_servo-scrollend-event-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_servo-scrollend-event-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.500 | 3 | 0.709 |
| [strata-cds-tranche-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--strata-cds-tranche-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.390 | 5 | 0.000 |
| [sgonly_strata-cds-tranche-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_strata-cds-tranche-feat-001.html) | — | `mcp-remote-direct` | `passed` | 0.370 | 5 | 0.400 |
| [tensorrt-mxfp4-quant-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--tensorrt-mxfp4-quant-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_tensorrt-mxfp4-quant-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_tensorrt-mxfp4-quant-feat-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 4 | 0.390 |
| [terraform-compact-diff-fmt-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--terraform-compact-diff-fmt-feat-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 3 | 0.000 |
| [sgonly_terraform-compact-diff-fmt-feat-001](../tasks/feature_haiku_20260301_071229--mcp-remote-direct--sgonly_terraform-compact-diff-fmt-feat-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.604 |
| [vscode-stale-diagnostics-feat-001](../tasks/feature_haiku_20260301_071229--baseline-local-direct--vscode-stale-diagnostics-feat-001.html) | — | `baseline-local-direct` | `passed` | 0.700 | 6 | 0.000 |
| [sgonly_vscode-stale-diagnostics-feat-001](../tasks/feature_haiku_20260228_220733--mcp-remote-direct--sgonly_vscode-stale-diagnostics-feat-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.120 |

## Multi-Run Variance

Tasks with multiple valid runs (40 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| bustub-hyperloglog-impl-001 | — | `baseline-local-direct` | 3 | 0.222 | 0.255 | 0.167, 0.500, 0.000 |
| bustub-hyperloglog-impl-001 | — | `mcp-remote-direct` | 4 | 0.167 | 0.000 | 0.167, 0.167, 0.167, 0.167 |
| camel-fix-protocol-feat-001 | — | `baseline-local-direct` | 4 | 0.320 | 0.164 | 0.470, 0.390, 0.090, 0.330 |
| camel-fix-protocol-feat-001 | — | `mcp-remote-direct` | 5 | 0.332 | 0.130 | 0.450, 0.140, 0.280, 0.450, 0.340 |
| cilium-policy-audit-logger-feat-001 | — | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| cilium-policy-audit-logger-feat-001 | — | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| cilium-policy-quota-feat-001 | — | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| cilium-policy-quota-feat-001 | — | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| curl-http3-priority-feat-001 | — | `baseline-local-direct` | 5 | 0.833 | 0.000 | 0.833, 0.833, 0.833, 0.833, 0.833 |
| curl-http3-priority-feat-001 | — | `mcp-remote-direct` | 4 | 0.667 | 0.333 | 0.167, 0.833, 0.833, 0.833 |
| django-rate-limit-middleware-feat-001 | — | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| django-rate-limit-middleware-feat-001 | — | `mcp-remote-direct` | 3 | 1.000 | 0.000 | 1.000, 1.000, 1.000 |
| envoy-custom-header-filter-feat-001 | — | `baseline-local-direct` | 5 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000, 1.000 |
| envoy-custom-header-filter-feat-001 | — | `mcp-remote-direct` | 5 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000, 1.000 |
| envoy-grpc-server-impl-001 | — | `baseline-local-direct` | 3 | 0.440 | 0.000 | 0.440, 0.440, 0.440 |
| envoy-grpc-server-impl-001 | — | `mcp-remote-direct` | 3 | 0.387 | 0.147 | 0.220, 0.440, 0.500 |
| flink-pricing-window-feat-001 | — | `baseline-local-direct` | 4 | 0.487 | 0.071 | 0.540, 0.540, 0.390, 0.480 |
| flink-pricing-window-feat-001 | — | `mcp-remote-direct` | 4 | 0.395 | 0.079 | 0.490, 0.410, 0.300, 0.380 |
| k8s-noschedule-taint-feat-001 | — | `baseline-local-direct` | 5 | 0.420 | 0.383 | 0.700, 0.700, 0.700, 0.000, 0.000 |
| k8s-noschedule-taint-feat-001 | — | `mcp-remote-direct` | 4 | 0.125 | 0.250 | 0.500, 0.000, 0.000, 0.000 |
| k8s-runtime-object-impl-001 | — | `baseline-local-direct` | 3 | 0.117 | 0.006 | 0.120, 0.110, 0.120 |
| k8s-runtime-object-impl-001 | — | `mcp-remote-direct` | 2 | 0.065 | 0.092 | 0.000, 0.130 |
| numpy-rolling-median-feat-001 | — | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| numpy-rolling-median-feat-001 | — | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| pandas-merge-asof-indicator-feat-001 | — | `baseline-local-direct` | 3 | 0.667 | 0.000 | 0.667, 0.667, 0.667 |
| pandas-merge-asof-indicator-feat-001 | — | `mcp-remote-direct` | 4 | 0.667 | 0.000 | 0.667, 0.667, 0.667, 0.667 |
| prometheus-silence-bulk-api-feat-001 | — | `baseline-local-direct` | 3 | 0.833 | 0.000 | 0.833, 0.833, 0.833 |
| prometheus-silence-bulk-api-feat-001 | — | `mcp-remote-direct` | 3 | 0.833 | 0.000 | 0.833, 0.833, 0.833 |
| pytorch-gradient-noise-feat-001 | — | `baseline-local-direct` | 3 | 0.833 | 0.000 | 0.833, 0.833, 0.833 |
| pytorch-gradient-noise-feat-001 | — | `mcp-remote-direct` | 3 | 0.833 | 0.000 | 0.833, 0.833, 0.833 |
| servo-scrollend-event-feat-001 | — | `baseline-local-direct` | 3 | 0.500 | 0.000 | 0.500, 0.500, 0.500 |
| servo-scrollend-event-feat-001 | — | `mcp-remote-direct` | 3 | 0.500 | 0.000 | 0.500, 0.500, 0.500 |
| strata-cds-tranche-feat-001 | — | `baseline-local-direct` | 5 | 0.492 | 0.146 | 0.690, 0.600, 0.350, 0.430, 0.390 |
| strata-cds-tranche-feat-001 | — | `mcp-remote-direct` | 5 | 0.354 | 0.195 | 0.360, 0.610, 0.370, 0.060, 0.370 |
| tensorrt-mxfp4-quant-feat-001 | — | `baseline-local-direct` | 4 | 0.500 | 0.577 | 0.000, 0.000, 1.000, 1.000 |
| tensorrt-mxfp4-quant-feat-001 | — | `mcp-remote-direct` | 4 | 0.750 | 0.500 | 1.000, 1.000, 1.000, 0.000 |
| terraform-compact-diff-fmt-feat-001 | — | `baseline-local-direct` | 3 | 1.000 | 0.000 | 1.000, 1.000, 1.000 |
| terraform-compact-diff-fmt-feat-001 | — | `mcp-remote-direct` | 3 | 1.000 | 0.000 | 1.000, 1.000, 1.000 |
| vscode-stale-diagnostics-feat-001 | — | `baseline-local-direct` | 6 | 0.367 | 0.294 | 0.000, 0.000, 0.500, 0.500, 0.500, 0.700 |
| vscode-stale-diagnostics-feat-001 | — | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
