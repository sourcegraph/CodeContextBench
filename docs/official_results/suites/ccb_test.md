# csb_sdlc_test

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [test_haiku_20260224_011816](../runs/test_haiku_20260224_011816.md) | `mcp-remote-direct` | 7 | 0.277 | 0.571 |
| [test_haiku_20260301_071232](../runs/test_haiku_20260301_071232.md) | `baseline-local-direct` | 16 | 0.560 | 0.812 |
| [test_haiku_20260301_071232](../runs/test_haiku_20260301_071232.md) | `mcp-remote-direct` | 8 | 0.780 | 1.000 |
| [test_haiku_20260301_192246](../runs/test_haiku_20260301_192246.md) | `baseline-local-direct` | 4 | 0.128 | 0.250 |
| [test_haiku_20260301_192246](../runs/test_haiku_20260301_192246.md) | `mcp-remote-direct` | 3 | 0.000 | 0.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [aspnetcore-code-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--aspnetcore-code-review-001.html) | — | `baseline-local-direct` | `passed` | 0.570 | 3 | 0.000 |
| [sgonly_aspnetcore-code-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_aspnetcore-code-review-001.html) | — | `mcp-remote-direct` | `passed` | 0.460 | 1 | 0.600 |
| [calcom-code-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--calcom-code-review-001.html) | — | `baseline-local-direct` | `passed` | 0.750 | 3 | 0.000 |
| [sgonly_calcom-code-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_calcom-code-review-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [curl-security-review-001](../tasks/test_haiku_20260301_192246--baseline-local-direct--curl-security-review-001.html) | — | `baseline-local-direct` | `passed` | 0.510 | 4 | 0.000 |
| [sgonly_curl-security-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_curl-security-review-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [envoy-code-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--envoy-code-review-001.html) | — | `baseline-local-direct` | `passed` | 0.650 | 3 | 0.000 |
| [sgonly_envoy-code-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_envoy-code-review-001.html) | — | `mcp-remote-direct` | `passed` | 0.500 | 1 | 0.722 |
| [ghost-code-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--ghost-code-review-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 3 | 0.000 |
| [sgonly_ghost-code-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_ghost-code-review-001.html) | — | `mcp-remote-direct` | `passed` | 0.620 | 1 | 0.870 |
| [kafka-security-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--kafka-security-review-001.html) | — | `baseline-local-direct` | `passed` | 0.440 | 2 | 0.000 |
| [sgonly_kafka-security-review-001](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_kafka-security-review-001.html) | — | `mcp-remote-direct` | `passed` | 0.290 | 2 | 0.800 |
| [llamacpp-context-window-search-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--llamacpp-context-window-search-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [llamacpp-file-modify-search-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--llamacpp-file-modify-search-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [numpy-array-sum-perf-001](../tasks/test_haiku_20260301_192246--baseline-local-direct--numpy-array-sum-perf-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_numpy-array-sum-perf-001](../tasks/test_haiku_20260301_192246--mcp-remote-direct--sgonly_numpy-array-sum-perf-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.404 |
| [openhands-search-file-test-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--openhands-search-file-test-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_openhands-search-file-test-001](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_openhands-search-file-test-001.html) | — | `mcp-remote-direct` | `passed` | 0.200 | 4 | 0.269 |
| [pandas-groupby-perf-001](../tasks/test_haiku_20260301_192246--baseline-local-direct--pandas-groupby-perf-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_pandas-groupby-perf-001](../tasks/test_haiku_20260301_192246--mcp-remote-direct--sgonly_pandas-groupby-perf-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.269 |
| [sklearn-kmeans-perf-001](../tasks/test_haiku_20260301_192246--baseline-local-direct--sklearn-kmeans-perf-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [sgonly_sklearn-kmeans-perf-001](../tasks/test_haiku_20260301_192246--mcp-remote-direct--sgonly_sklearn-kmeans-perf-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.250 |
| [terraform-code-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--terraform-code-review-001.html) | — | `baseline-local-direct` | `passed` | 0.570 | 3 | 0.000 |
| [sgonly_terraform-code-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_terraform-code-review-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [test-coverage-gap-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--test-coverage-gap-001.html) | — | `baseline-local-direct` | `passed` | 0.860 | 3 | 0.000 |
| [sgonly_test-coverage-gap-001](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_test-coverage-gap-001.html) | — | `mcp-remote-direct` | `passed` | 0.860 | 3 | 0.880 |
| [test-coverage-gap-002](../tasks/test_haiku_20260301_071232--baseline-local-direct--test-coverage-gap-002.html) | — | `baseline-local-direct` | `passed` | 0.940 | 2 | 0.000 |
| [sgonly_test-coverage-gap-002](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_test-coverage-gap-002.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.914 |
| [test-integration-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--test-integration-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [sgonly_test-integration-001](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_test-integration-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.568 |
| [test-integration-002](../tasks/test_haiku_20260301_071232--baseline-local-direct--test-integration-002.html) | — | `baseline-local-direct` | `passed` | 0.370 | 2 | 0.000 |
| [sgonly_test-integration-002](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_test-integration-002.html) | — | `mcp-remote-direct` | `passed` | 0.890 | 2 | 0.560 |
| [test-unitgen-go-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--test-unitgen-go-001.html) | — | `baseline-local-direct` | `passed` | 0.960 | 2 | 0.000 |
| [sgonly_test-unitgen-go-001](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_test-unitgen-go-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.556 |
| [test-unitgen-py-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--test-unitgen-py-001.html) | — | `baseline-local-direct` | `passed` | 0.600 | 2 | 0.000 |
| [sgonly_test-unitgen-py-001](../tasks/test_haiku_20260301_071232--mcp-remote-direct--sgonly_test-unitgen-py-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.938 |
| [vscode-code-review-001](../tasks/test_haiku_20260301_071232--baseline-local-direct--vscode-code-review-001.html) | — | `baseline-local-direct` | `passed` | 0.450 | 3 | 0.000 |
| [sgonly_vscode-code-review-001](../tasks/test_haiku_20260224_011816--mcp-remote-direct--sgonly_vscode-code-review-001.html) | — | `mcp-remote-direct` | `passed` | 0.360 | 1 | 0.875 |

## Multi-Run Variance

Tasks with multiple valid runs (36 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| aspnetcore-code-review-001 | — | `baseline-local-direct` | 5 | 0.554 | 0.009 | 0.550, 0.550, 0.570, 0.550, 0.550 |
| aspnetcore-code-review-001 | — | `mcp-remote-direct` | 3 | 0.490 | 0.052 | 0.460, 0.460, 0.550 |
| calcom-code-review-001 | — | `baseline-local-direct` | 7 | 0.717 | 0.043 | 0.750, 0.650, 0.750, 0.750, 0.680, 0.690, 0.750 |
| calcom-code-review-001 | — | `mcp-remote-direct` | 3 | 0.377 | 0.023 | 0.390, 0.390, 0.350 |
| curl-security-review-001 | — | `baseline-local-direct` | 8 | 0.590 | 0.090 | 0.670, 0.670, 0.510, 0.720, 0.510, 0.510, 0.620, 0.510 |
| curl-security-review-001 | — | `mcp-remote-direct` | 3 | 0.620 | 0.100 | 0.520, 0.620, 0.720 |
| envoy-code-review-001 | — | `baseline-local-direct` | 6 | 0.717 | 0.041 | 0.700, 0.700, 0.750, 0.650, 0.750, 0.750 |
| envoy-code-review-001 | — | `mcp-remote-direct` | 3 | 0.527 | 0.074 | 0.500, 0.610, 0.470 |
| ghost-code-review-001 | — | `baseline-local-direct` | 5 | 0.816 | 0.036 | 0.800, 0.800, 0.800, 0.800, 0.880 |
| ghost-code-review-001 | — | `mcp-remote-direct` | 3 | 0.633 | 0.071 | 0.620, 0.710, 0.570 |
| kafka-security-review-001 | — | `baseline-local-direct` | 5 | 0.464 | 0.033 | 0.440, 0.440, 0.500, 0.500, 0.440 |
| kafka-security-review-001 | — | `mcp-remote-direct` | 5 | 0.282 | 0.072 | 0.170, 0.290, 0.290, 0.370, 0.290 |
| numpy-array-sum-perf-001 | — | `baseline-local-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| numpy-array-sum-perf-001 | — | `mcp-remote-direct` | 4 | 0.000 | 0.000 | 0.000, 0.000, 0.000, 0.000 |
| openhands-search-file-test-001 | — | `baseline-local-direct` | 5 | 0.080 | 0.110 | 0.000, 0.000, 0.000, 0.200, 0.200 |
| openhands-search-file-test-001 | — | `mcp-remote-direct` | 5 | 0.240 | 0.219 | 0.000, 0.200, 0.200, 0.200, 0.600 |
| pandas-groupby-perf-001 | — | `baseline-local-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| pandas-groupby-perf-001 | — | `mcp-remote-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| sklearn-kmeans-perf-001 | — | `baseline-local-direct` | 4 | 0.000 | 0.000 | 0.000, 0.000, 0.000, 0.000 |
| sklearn-kmeans-perf-001 | — | `mcp-remote-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| terraform-code-review-001 | — | `baseline-local-direct` | 7 | 0.624 | 0.067 | 0.620, 0.670, 0.670, 0.570, 0.670, 0.670, 0.500 |
| terraform-code-review-001 | — | `mcp-remote-direct` | 3 | 0.407 | 0.029 | 0.390, 0.390, 0.440 |
| test-coverage-gap-001 | — | `baseline-local-direct` | 3 | 0.860 | 0.000 | 0.860, 0.860, 0.860 |
| test-coverage-gap-001 | — | `mcp-remote-direct` | 4 | 0.875 | 0.050 | 0.940, 0.880, 0.820, 0.860 |
| test-coverage-gap-002 | — | `baseline-local-direct` | 5 | 0.940 | 0.000 | 0.940, 0.940, 0.940, 0.940, 0.940 |
| test-coverage-gap-002 | — | `mcp-remote-direct` | 4 | 0.970 | 0.035 | 0.940, 1.000, 1.000, 0.940 |
| test-integration-001 | — | `baseline-local-direct` | 5 | 0.984 | 0.022 | 1.000, 1.000, 0.960, 0.960, 1.000 |
| test-integration-001 | — | `mcp-remote-direct` | 4 | 0.980 | 0.023 | 1.000, 0.960, 1.000, 0.960 |
| test-integration-002 | — | `baseline-local-direct` | 3 | 0.370 | 0.000 | 0.370, 0.370, 0.370 |
| test-integration-002 | — | `mcp-remote-direct` | 3 | 0.930 | 0.061 | 0.900, 1.000, 0.890 |
| test-unitgen-go-001 | — | `baseline-local-direct` | 5 | 0.960 | 0.000 | 0.960, 0.960, 0.960, 0.960, 0.960 |
| test-unitgen-go-001 | — | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| test-unitgen-py-001 | — | `baseline-local-direct` | 5 | 0.576 | 0.054 | 0.600, 0.600, 0.600, 0.600, 0.480 |
| test-unitgen-py-001 | — | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| vscode-code-review-001 | — | `baseline-local-direct` | 6 | 0.458 | 0.020 | 0.450, 0.450, 0.500, 0.450, 0.450, 0.450 |
| vscode-code-review-001 | — | `mcp-remote-direct` | 3 | 0.330 | 0.030 | 0.360, 0.300, 0.330 |
