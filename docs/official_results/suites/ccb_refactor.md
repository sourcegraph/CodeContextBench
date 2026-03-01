# ccb_refactor

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [refactor_haiku_20260301_031849](../runs/refactor_haiku_20260301_031849.md) | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [refactor_haiku_20260301_071230](../runs/refactor_haiku_20260301_071230.md) | `baseline-local-direct` | 20 | 0.789 | 0.950 |
| [refactor_haiku_20260301_071230](../runs/refactor_haiku_20260301_071230.md) | `mcp-remote-direct` | 19 | 0.713 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [cilium-endpoint-manager-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--cilium-endpoint-manager-refac-001.html) | [source](../../../benchmarks/ccb_refactor/cilium-endpoint-manager-refac-001) | `baseline-local-direct` | `passed` | 0.333 | 3 | 0.000 |
| [sgonly_cilium-endpoint-manager-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_cilium-endpoint-manager-refac-001.html) | [source](../../../benchmarks/ccb_refactor/cilium-endpoint-manager-refac-001) | `mcp-remote-direct` | `passed` | 0.500 | 5 | 0.518 |
| [curl-multi-process-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--curl-multi-process-refac-001.html) | [source](../../../benchmarks/ccb_refactor/curl-multi-process-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_curl-multi-process-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_curl-multi-process-refac-001.html) | [source](../../../benchmarks/ccb_refactor/curl-multi-process-refac-001) | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.250 |
| [django-request-factory-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--django-request-factory-refac-001.html) | [source](../../../benchmarks/ccb_refactor/django-request-factory-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_django-request-factory-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_django-request-factory-refac-001.html) | [source](../../../benchmarks/ccb_refactor/django-request-factory-refac-001) | `mcp-remote-direct` | `passed` | 0.667 | 5 | 0.381 |
| [envoy-listener-manager-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--envoy-listener-manager-refac-001.html) | [source](../../../benchmarks/ccb_refactor/envoy-listener-manager-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 3 | 0.000 |
| [sgonly_envoy-listener-manager-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_envoy-listener-manager-refac-001.html) | [source](../../../benchmarks/ccb_refactor/envoy-listener-manager-refac-001) | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.119 |
| [etcd-raft-storage-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--etcd-raft-storage-refac-001.html) | [source](../../../benchmarks/ccb_refactor/etcd-raft-storage-refac-001) | `baseline-local-direct` | `passed` | 0.833 | 4 | 0.000 |
| [sgonly_etcd-raft-storage-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_etcd-raft-storage-refac-001.html) | [source](../../../benchmarks/ccb_refactor/etcd-raft-storage-refac-001) | `mcp-remote-direct` | `passed` | 0.833 | 5 | 0.171 |
| [flipt-dep-refactor-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--flipt-dep-refactor-001.html) | [source](../../../benchmarks/ccb_refactor/flipt-dep-refactor-001) | `baseline-local-direct` | `passed` | 0.500 | 4 | 0.000 |
| [sgonly_flipt-dep-refactor-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_flipt-dep-refactor-001.html) | [source](../../../benchmarks/ccb_refactor/flipt-dep-refactor-001) | `mcp-remote-direct` | `passed` | 0.180 | 5 | 0.338 |
| [flipt-flagexists-refactor-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--flipt-flagexists-refactor-001.html) | [source](../../../benchmarks/ccb_refactor/flipt-flagexists-refactor-001) | `baseline-local-direct` | `passed` | 0.850 | 4 | 0.000 |
| [sgonly_flipt-flagexists-refactor-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_flipt-flagexists-refactor-001.html) | [source](../../../benchmarks/ccb_refactor/flipt-flagexists-refactor-001) | `mcp-remote-direct` | `passed` | 0.550 | 4 | 0.207 |
| [istio-discovery-server-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--istio-discovery-server-refac-001.html) | [source](../../../benchmarks/ccb_refactor/istio-discovery-server-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_istio-discovery-server-refac-001](../tasks/refactor_haiku_20260301_031849--mcp-remote-direct--sgonly_istio-discovery-server-refac-001.html) | [source](../../../benchmarks/ccb_refactor/istio-discovery-server-refac-001) | `mcp-remote-direct` | `passed` | 0.500 | 4 | 0.062 |
| [k8s-score-normalizer-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--k8s-score-normalizer-refac-001.html) | [source](../../../benchmarks/ccb_refactor/k8s-score-normalizer-refac-001) | `baseline-local-direct` | `passed` | 0.660 | 4 | 0.000 |
| [sgonly_k8s-score-normalizer-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_k8s-score-normalizer-refac-001.html) | [source](../../../benchmarks/ccb_refactor/k8s-score-normalizer-refac-001) | `mcp-remote-direct` | `passed` | 0.760 | 5 | 0.230 |
| [kafka-batch-accumulator-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--kafka-batch-accumulator-refac-001.html) | [source](../../../benchmarks/ccb_refactor/kafka-batch-accumulator-refac-001) | `baseline-local-direct` | `passed` | 0.790 | 3 | 0.000 |
| [sgonly_kafka-batch-accumulator-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_kafka-batch-accumulator-refac-001.html) | [source](../../../benchmarks/ccb_refactor/kafka-batch-accumulator-refac-001) | `mcp-remote-direct` | `passed` | 0.530 | 4 | 0.097 |
| [kubernetes-scheduler-profile-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--kubernetes-scheduler-profile-refac-001.html) | [source](../../../benchmarks/ccb_refactor/kubernetes-scheduler-profile-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_kubernetes-scheduler-profile-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_kubernetes-scheduler-profile-refac-001.html) | [source](../../../benchmarks/ccb_refactor/kubernetes-scheduler-profile-refac-001) | `mcp-remote-direct` | `passed` | 0.833 | 5 | 0.603 |
| [numpy-array-dispatch-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--numpy-array-dispatch-refac-001.html) | [source](../../../benchmarks/ccb_refactor/numpy-array-dispatch-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_numpy-array-dispatch-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_numpy-array-dispatch-refac-001.html) | [source](../../../benchmarks/ccb_refactor/numpy-array-dispatch-refac-001) | `mcp-remote-direct` | `passed` | 0.667 | 5 | 0.667 |
| [pandas-index-engine-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--pandas-index-engine-refac-001.html) | [source](../../../benchmarks/ccb_refactor/pandas-index-engine-refac-001) | `baseline-local-direct` | `passed` | 0.667 | 4 | 0.000 |
| [sgonly_pandas-index-engine-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_pandas-index-engine-refac-001.html) | [source](../../../benchmarks/ccb_refactor/pandas-index-engine-refac-001) | `mcp-remote-direct` | `passed` | 0.667 | 5 | 0.138 |
| [prometheus-query-engine-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--prometheus-query-engine-refac-001.html) | [source](../../../benchmarks/ccb_refactor/prometheus-query-engine-refac-001) | `baseline-local-direct` | `passed` | 0.833 | 4 | 0.000 |
| [sgonly_prometheus-query-engine-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_prometheus-query-engine-refac-001.html) | [source](../../../benchmarks/ccb_refactor/prometheus-query-engine-refac-001) | `mcp-remote-direct` | `passed` | 0.833 | 5 | 0.421 |
| [python-http-class-naming-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--python-http-class-naming-refac-001.html) | [source](../../../benchmarks/ccb_refactor/python-http-class-naming-refac-001) | `baseline-local-direct` | `passed` | 0.920 | 4 | 0.000 |
| [sgonly_python-http-class-naming-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_python-http-class-naming-refac-001.html) | [source](../../../benchmarks/ccb_refactor/python-http-class-naming-refac-001) | `mcp-remote-direct` | `passed` | 0.920 | 5 | 0.077 |
| [pytorch-optimizer-foreach-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--pytorch-optimizer-foreach-refac-001.html) | [source](../../../benchmarks/ccb_refactor/pytorch-optimizer-foreach-refac-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [sgonly_pytorch-optimizer-foreach-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_pytorch-optimizer-foreach-refac-001.html) | [source](../../../benchmarks/ccb_refactor/pytorch-optimizer-foreach-refac-001) | `mcp-remote-direct` | `passed` | 0.167 | 5 | 0.371 |
| [rust-subtype-relation-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--rust-subtype-relation-refac-001.html) | [source](../../../benchmarks/ccb_refactor/rust-subtype-relation-refac-001) | `baseline-local-direct` | `passed` | 0.820 | 4 | 0.000 |
| [sgonly_rust-subtype-relation-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_rust-subtype-relation-refac-001.html) | [source](../../../benchmarks/ccb_refactor/rust-subtype-relation-refac-001) | `mcp-remote-direct` | `passed` | 0.840 | 6 | 0.414 |
| [scikit-learn-estimator-tags-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--scikit-learn-estimator-tags-refac-001.html) | [source](../../../benchmarks/ccb_refactor/scikit-learn-estimator-tags-refac-001) | `baseline-local-direct` | `passed` | 0.833 | 4 | 0.000 |
| [sgonly_scikit-learn-estimator-tags-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_scikit-learn-estimator-tags-refac-001.html) | [source](../../../benchmarks/ccb_refactor/scikit-learn-estimator-tags-refac-001) | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.206 |
| [strata-fx-european-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--strata-fx-european-refac-001.html) | [source](../../../benchmarks/ccb_refactor/strata-fx-european-refac-001) | `baseline-local-direct` | `passed` | 0.740 | 3 | 0.000 |
| [sgonly_strata-fx-european-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_strata-fx-european-refac-001.html) | [source](../../../benchmarks/ccb_refactor/strata-fx-european-refac-001) | `mcp-remote-direct` | `passed` | 0.770 | 4 | 0.367 |
| [terraform-eval-context-refac-001](../tasks/refactor_haiku_20260301_071230--baseline-local-direct--terraform-eval-context-refac-001.html) | [source](../../../benchmarks/ccb_refactor/terraform-eval-context-refac-001) | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_terraform-eval-context-refac-001](../tasks/refactor_haiku_20260301_071230--mcp-remote-direct--sgonly_terraform-eval-context-refac-001.html) | [source](../../../benchmarks/ccb_refactor/terraform-eval-context-refac-001) | `mcp-remote-direct` | `passed` | 0.833 | 4 | 0.305 |

## Multi-Run Variance

Tasks with multiple valid runs (40 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| cilium-endpoint-manager-refac-001 | [source](../../../benchmarks/ccb_refactor/cilium-endpoint-manager-refac-001) | `baseline-local-direct` | 3 | 0.389 | 0.096 | 0.333, 0.500, 0.333 |
| cilium-endpoint-manager-refac-001 | [source](../../../benchmarks/ccb_refactor/cilium-endpoint-manager-refac-001) | `mcp-remote-direct` | 5 | 0.433 | 0.091 | 0.500, 0.333, 0.500, 0.333, 0.500 |
| curl-multi-process-refac-001 | [source](../../../benchmarks/ccb_refactor/curl-multi-process-refac-001) | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| curl-multi-process-refac-001 | [source](../../../benchmarks/ccb_refactor/curl-multi-process-refac-001) | `mcp-remote-direct` | 5 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000, 1.000 |
| django-request-factory-refac-001 | [source](../../../benchmarks/ccb_refactor/django-request-factory-refac-001) | `baseline-local-direct` | 4 | 0.875 | 0.083 | 0.833, 0.833, 0.833, 1.000 |
| django-request-factory-refac-001 | [source](../../../benchmarks/ccb_refactor/django-request-factory-refac-001) | `mcp-remote-direct` | 5 | 0.700 | 0.074 | 0.667, 0.667, 0.667, 0.833, 0.667 |
| envoy-listener-manager-refac-001 | [source](../../../benchmarks/ccb_refactor/envoy-listener-manager-refac-001) | `baseline-local-direct` | 3 | 1.000 | 0.000 | 1.000, 1.000, 1.000 |
| envoy-listener-manager-refac-001 | [source](../../../benchmarks/ccb_refactor/envoy-listener-manager-refac-001) | `mcp-remote-direct` | 4 | 0.917 | 0.096 | 0.833, 1.000, 0.833, 1.000 |
| etcd-raft-storage-refac-001 | [source](../../../benchmarks/ccb_refactor/etcd-raft-storage-refac-001) | `baseline-local-direct` | 4 | 0.917 | 0.096 | 0.833, 1.000, 1.000, 0.833 |
| etcd-raft-storage-refac-001 | [source](../../../benchmarks/ccb_refactor/etcd-raft-storage-refac-001) | `mcp-remote-direct` | 5 | 0.767 | 0.346 | 0.167, 1.000, 0.833, 1.000, 0.833 |
| flipt-dep-refactor-001 | [source](../../../benchmarks/ccb_refactor/flipt-dep-refactor-001) | `baseline-local-direct` | 4 | 0.487 | 0.266 | 0.150, 0.800, 0.500, 0.500 |
| flipt-dep-refactor-001 | [source](../../../benchmarks/ccb_refactor/flipt-dep-refactor-001) | `mcp-remote-direct` | 5 | 0.296 | 0.120 | 0.500, 0.270, 0.280, 0.250, 0.180 |
| flipt-flagexists-refactor-001 | [source](../../../benchmarks/ccb_refactor/flipt-flagexists-refactor-001) | `baseline-local-direct` | 4 | 0.637 | 0.266 | 0.300, 0.850, 0.550, 0.850 |
| flipt-flagexists-refactor-001 | [source](../../../benchmarks/ccb_refactor/flipt-flagexists-refactor-001) | `mcp-remote-direct` | 4 | 0.532 | 0.193 | 0.550, 0.750, 0.280, 0.550 |
| istio-discovery-server-refac-001 | [source](../../../benchmarks/ccb_refactor/istio-discovery-server-refac-001) | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| istio-discovery-server-refac-001 | [source](../../../benchmarks/ccb_refactor/istio-discovery-server-refac-001) | `mcp-remote-direct` | 4 | 0.875 | 0.250 | 1.000, 1.000, 1.000, 0.500 |
| k8s-score-normalizer-refac-001 | [source](../../../benchmarks/ccb_refactor/k8s-score-normalizer-refac-001) | `baseline-local-direct` | 4 | 0.738 | 0.059 | 0.800, 0.760, 0.730, 0.660 |
| k8s-score-normalizer-refac-001 | [source](../../../benchmarks/ccb_refactor/k8s-score-normalizer-refac-001) | `mcp-remote-direct` | 5 | 0.692 | 0.144 | 0.710, 0.450, 0.830, 0.710, 0.760 |
| kafka-batch-accumulator-refac-001 | [source](../../../benchmarks/ccb_refactor/kafka-batch-accumulator-refac-001) | `baseline-local-direct` | 3 | 0.747 | 0.131 | 0.850, 0.600, 0.790 |
| kafka-batch-accumulator-refac-001 | [source](../../../benchmarks/ccb_refactor/kafka-batch-accumulator-refac-001) | `mcp-remote-direct` | 4 | 0.630 | 0.071 | 0.680, 0.630, 0.680, 0.530 |
| kubernetes-scheduler-profile-refac-001 | [source](../../../benchmarks/ccb_refactor/kubernetes-scheduler-profile-refac-001) | `baseline-local-direct` | 4 | 0.792 | 0.417 | 1.000, 1.000, 0.167, 1.000 |
| kubernetes-scheduler-profile-refac-001 | [source](../../../benchmarks/ccb_refactor/kubernetes-scheduler-profile-refac-001) | `mcp-remote-direct` | 5 | 0.933 | 0.091 | 0.833, 1.000, 1.000, 1.000, 0.833 |
| numpy-array-dispatch-refac-001 | [source](../../../benchmarks/ccb_refactor/numpy-array-dispatch-refac-001) | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| numpy-array-dispatch-refac-001 | [source](../../../benchmarks/ccb_refactor/numpy-array-dispatch-refac-001) | `mcp-remote-direct` | 5 | 0.800 | 0.074 | 0.833, 0.833, 0.833, 0.833, 0.667 |
| pandas-index-engine-refac-001 | [source](../../../benchmarks/ccb_refactor/pandas-index-engine-refac-001) | `baseline-local-direct` | 4 | 0.667 | 0.000 | 0.667, 0.667, 0.667, 0.667 |
| pandas-index-engine-refac-001 | [source](../../../benchmarks/ccb_refactor/pandas-index-engine-refac-001) | `mcp-remote-direct` | 5 | 0.533 | 0.298 | 0.667, 0.000, 0.667, 0.667, 0.667 |
| prometheus-query-engine-refac-001 | [source](../../../benchmarks/ccb_refactor/prometheus-query-engine-refac-001) | `baseline-local-direct` | 4 | 0.875 | 0.083 | 0.833, 1.000, 0.833, 0.833 |
| prometheus-query-engine-refac-001 | [source](../../../benchmarks/ccb_refactor/prometheus-query-engine-refac-001) | `mcp-remote-direct` | 5 | 0.700 | 0.398 | 0.833, 1.000, 0.000, 0.833, 0.833 |
| python-http-class-naming-refac-001 | [source](../../../benchmarks/ccb_refactor/python-http-class-naming-refac-001) | `baseline-local-direct` | 4 | 0.840 | 0.160 | 0.600, 0.920, 0.920, 0.920 |
| python-http-class-naming-refac-001 | [source](../../../benchmarks/ccb_refactor/python-http-class-naming-refac-001) | `mcp-remote-direct` | 5 | 0.512 | 0.340 | 0.280, 0.200, 0.840, 0.320, 0.920 |
| pytorch-optimizer-foreach-refac-001 | [source](../../../benchmarks/ccb_refactor/pytorch-optimizer-foreach-refac-001) | `baseline-local-direct` | 3 | 0.056 | 0.096 | 0.000, 0.167, 0.000 |
| pytorch-optimizer-foreach-refac-001 | [source](../../../benchmarks/ccb_refactor/pytorch-optimizer-foreach-refac-001) | `mcp-remote-direct` | 5 | 0.233 | 0.149 | 0.167, 0.500, 0.167, 0.167, 0.167 |
| rust-subtype-relation-refac-001 | [source](../../../benchmarks/ccb_refactor/rust-subtype-relation-refac-001) | `baseline-local-direct` | 4 | 0.828 | 0.057 | 0.750, 0.860, 0.880, 0.820 |
| rust-subtype-relation-refac-001 | [source](../../../benchmarks/ccb_refactor/rust-subtype-relation-refac-001) | `mcp-remote-direct` | 6 | 0.825 | 0.041 | 0.790, 0.790, 0.820, 0.810, 0.900, 0.840 |
| scikit-learn-estimator-tags-refac-001 | [source](../../../benchmarks/ccb_refactor/scikit-learn-estimator-tags-refac-001) | `baseline-local-direct` | 4 | 0.958 | 0.083 | 1.000, 1.000, 1.000, 0.833 |
| scikit-learn-estimator-tags-refac-001 | [source](../../../benchmarks/ccb_refactor/scikit-learn-estimator-tags-refac-001) | `mcp-remote-direct` | 5 | 0.967 | 0.074 | 1.000, 1.000, 1.000, 0.833, 1.000 |
| strata-fx-european-refac-001 | [source](../../../benchmarks/ccb_refactor/strata-fx-european-refac-001) | `baseline-local-direct` | 3 | 0.590 | 0.269 | 0.280, 0.750, 0.740 |
| strata-fx-european-refac-001 | [source](../../../benchmarks/ccb_refactor/strata-fx-european-refac-001) | `mcp-remote-direct` | 4 | 0.738 | 0.146 | 0.640, 0.930, 0.610, 0.770 |
| terraform-eval-context-refac-001 | [source](../../../benchmarks/ccb_refactor/terraform-eval-context-refac-001) | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| terraform-eval-context-refac-001 | [source](../../../benchmarks/ccb_refactor/terraform-eval-context-refac-001) | `mcp-remote-direct` | 4 | 0.625 | 0.316 | 0.667, 0.167, 0.833, 0.833 |
