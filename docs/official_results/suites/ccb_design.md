# csb_sdlc_design

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [design_haiku_20260301_071227](../runs/design_haiku_20260301_071227.md) | `baseline-local-direct` | 20 | 0.770 | 1.000 |
| [design_haiku_20260301_071227](../runs/design_haiku_20260301_071227.md) | `mcp-remote-direct` | 20 | 0.699 | 0.950 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [camel-routing-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--camel-routing-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 4 | 0.000 |
| [sgonly_camel-routing-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_camel-routing-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.730 | 4 | 0.971 |
| [django-modeladmin-impact-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--django-modeladmin-impact-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_django-modeladmin-impact-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_django-modeladmin-impact-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.875 |
| [django-orm-query-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--django-orm-query-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.790 | 4 | 0.000 |
| [sgonly_django-orm-query-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_django-orm-query-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.850 | 4 | 0.967 |
| [django-pre-validate-signal-design-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--django-pre-validate-signal-design-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_django-pre-validate-signal-design-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_django-pre-validate-signal-design-001.html) | — | `mcp-remote-direct` | `passed` | 0.900 | 4 | 0.369 |
| [django-rate-limit-design-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--django-rate-limit-design-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_django-rate-limit-design-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_django-rate-limit-design-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.278 |
| [envoy-routeconfig-dep-chain-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--envoy-routeconfig-dep-chain-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_envoy-routeconfig-dep-chain-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_envoy-routeconfig-dep-chain-001.html) | — | `mcp-remote-direct` | `passed` | 0.670 | 4 | 0.889 |
| [envoy-stream-aggregated-sym-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--envoy-stream-aggregated-sym-001.html) | — | `baseline-local-direct` | `passed` | 0.810 | 4 | 0.000 |
| [sgonly_envoy-stream-aggregated-sym-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_envoy-stream-aggregated-sym-001.html) | — | `mcp-remote-direct` | `passed` | 0.450 | 4 | 0.955 |
| [etcd-grpc-api-upgrade-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--etcd-grpc-api-upgrade-001.html) | — | `baseline-local-direct` | `passed` | 0.771 | 4 | 0.000 |
| [sgonly_etcd-grpc-api-upgrade-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_etcd-grpc-api-upgrade-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 4 | 0.378 |
| [flink-checkpoint-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--flink-checkpoint-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.400 | 4 | 0.000 |
| [sgonly_flink-checkpoint-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_flink-checkpoint-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.780 | 4 | 0.964 |
| [flipt-protobuf-metadata-design-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--flipt-protobuf-metadata-design-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_flipt-protobuf-metadata-design-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_flipt-protobuf-metadata-design-001.html) | — | `mcp-remote-direct` | `passed` | 0.750 | 3 | 0.313 |
| [flipt-transitive-deps-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--flipt-transitive-deps-001.html) | — | `baseline-local-direct` | `passed` | 0.778 | 4 | 0.000 |
| [sgonly_flipt-transitive-deps-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_flipt-transitive-deps-001.html) | — | `mcp-remote-direct` | `passed` | 0.467 | 4 | 0.977 |
| [k8s-crd-lifecycle-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--k8s-crd-lifecycle-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.660 | 4 | 0.000 |
| [sgonly_k8s-crd-lifecycle-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_k8s-crd-lifecycle-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.680 | 4 | 0.955 |
| [k8s-dra-allocation-impact-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--k8s-dra-allocation-impact-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_k8s-dra-allocation-impact-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_k8s-dra-allocation-impact-001.html) | — | `mcp-remote-direct` | `passed` | 0.900 | 4 | 0.958 |
| [k8s-scheduler-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--k8s-scheduler-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.700 | 4 | 0.000 |
| [sgonly_k8s-scheduler-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_k8s-scheduler-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.680 | 4 | 0.944 |
| [k8s-sharedinformer-sym-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--k8s-sharedinformer-sym-001.html) | — | `baseline-local-direct` | `passed` | 0.610 | 4 | 0.000 |
| [sgonly_k8s-sharedinformer-sym-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_k8s-sharedinformer-sym-001.html) | — | `mcp-remote-direct` | `passed` | 0.690 | 4 | 0.980 |
| [k8s-typemeta-dep-chain-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--k8s-typemeta-dep-chain-001.html) | — | `baseline-local-direct` | `passed` | 0.330 | 4 | 0.000 |
| [sgonly_k8s-typemeta-dep-chain-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_k8s-typemeta-dep-chain-001.html) | — | `mcp-remote-direct` | `passed` | 0.670 | 4 | 0.889 |
| [kafka-flink-streaming-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--kafka-flink-streaming-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.960 | 4 | 0.000 |
| [sgonly_kafka-flink-streaming-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_kafka-flink-streaming-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.690 | 4 | 0.974 |
| [postgres-query-exec-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--postgres-query-exec-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.780 | 4 | 0.000 |
| [sgonly_postgres-query-exec-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_postgres-query-exec-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.930 | 4 | 0.974 |
| [quantlib-barrier-pricing-arch-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--quantlib-barrier-pricing-arch-001.html) | — | `baseline-local-direct` | `passed` | 0.870 | 4 | 0.000 |
| [sgonly_quantlib-barrier-pricing-arch-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_quantlib-barrier-pricing-arch-001.html) | — | `mcp-remote-direct` | `passed` | 0.920 | 4 | 0.963 |
| [terraform-provider-iface-sym-001](../tasks/design_haiku_20260301_071227--baseline-local-direct--terraform-provider-iface-sym-001.html) | — | `baseline-local-direct` | `passed` | 0.140 | 4 | 0.000 |
| [sgonly_terraform-provider-iface-sym-001](../tasks/design_haiku_20260301_071227--mcp-remote-direct--sgonly_terraform-provider-iface-sym-001.html) | — | `mcp-remote-direct` | `passed` | 0.230 | 4 | 0.884 |

## Multi-Run Variance

Tasks with multiple valid runs (28 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| camel-routing-arch-001 | — | `baseline-local-direct` | 4 | 0.835 | 0.030 | 0.860, 0.860, 0.820, 0.800 |
| camel-routing-arch-001 | — | `mcp-remote-direct` | 4 | 0.660 | 0.174 | 0.400, 0.750, 0.760, 0.730 |
| django-orm-query-arch-001 | — | `baseline-local-direct` | 4 | 0.820 | 0.036 | 0.840, 0.790, 0.860, 0.790 |
| django-orm-query-arch-001 | — | `mcp-remote-direct` | 4 | 0.900 | 0.037 | 0.900, 0.940, 0.910, 0.850 |
| django-pre-validate-signal-design-001 | — | `baseline-local-direct` | 4 | 0.975 | 0.050 | 0.900, 1.000, 1.000, 1.000 |
| django-pre-validate-signal-design-001 | — | `mcp-remote-direct` | 4 | 0.925 | 0.050 | 1.000, 0.900, 0.900, 0.900 |
| django-rate-limit-design-001 | — | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| django-rate-limit-design-001 | — | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| envoy-routeconfig-dep-chain-001 | — | `baseline-local-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| envoy-routeconfig-dep-chain-001 | — | `mcp-remote-direct` | 4 | 0.752 | 0.165 | 0.670, 1.000, 0.670, 0.670 |
| envoy-stream-aggregated-sym-001 | — | `baseline-local-direct` | 4 | 0.685 | 0.148 | 0.470, 0.720, 0.740, 0.810 |
| envoy-stream-aggregated-sym-001 | — | `mcp-remote-direct` | 4 | 0.537 | 0.068 | 0.520, 0.580, 0.600, 0.450 |
| etcd-grpc-api-upgrade-001 | — | `baseline-local-direct` | 4 | 0.771 | 0.000 | 0.771, 0.771, 0.771, 0.771 |
| etcd-grpc-api-upgrade-001 | — | `mcp-remote-direct` | 4 | 0.436 | 0.371 | 0.714, 0.771, 0.257, 0.000 |
| flink-checkpoint-arch-001 | — | `baseline-local-direct` | 4 | 0.583 | 0.212 | 0.400, 0.790, 0.740, 0.400 |
| flink-checkpoint-arch-001 | — | `mcp-remote-direct` | 4 | 0.748 | 0.033 | 0.710, 0.770, 0.730, 0.780 |
| flipt-protobuf-metadata-design-001 | — | `baseline-local-direct` | 4 | 0.750 | 0.500 | 1.000, 0.000, 1.000, 1.000 |
| flipt-protobuf-metadata-design-001 | — | `mcp-remote-direct` | 3 | 0.833 | 0.144 | 1.000, 0.750, 0.750 |
| flipt-transitive-deps-001 | — | `baseline-local-direct` | 4 | 0.736 | 0.108 | 0.711, 0.600, 0.856, 0.778 |
| flipt-transitive-deps-001 | — | `mcp-remote-direct` | 4 | 0.672 | 0.161 | 0.711, 0.656, 0.856, 0.467 |
| k8s-crd-lifecycle-arch-001 | — | `baseline-local-direct` | 4 | 0.590 | 0.136 | 0.590, 0.710, 0.400, 0.660 |
| k8s-crd-lifecycle-arch-001 | — | `mcp-remote-direct` | 4 | 0.708 | 0.059 | 0.640, 0.770, 0.740, 0.680 |
| k8s-typemeta-dep-chain-001 | — | `baseline-local-direct` | 4 | 0.667 | 0.274 | 0.670, 1.000, 0.670, 0.330 |
| k8s-typemeta-dep-chain-001 | — | `mcp-remote-direct` | 4 | 0.670 | 0.000 | 0.670, 0.670, 0.670, 0.670 |
| kafka-flink-streaming-arch-001 | — | `baseline-local-direct` | 4 | 0.950 | 0.035 | 0.980, 0.900, 0.960, 0.960 |
| kafka-flink-streaming-arch-001 | — | `mcp-remote-direct` | 4 | 0.472 | 0.145 | 0.400, 0.400, 0.400, 0.690 |
| postgres-query-exec-arch-001 | — | `baseline-local-direct` | 4 | 0.818 | 0.043 | 0.780, 0.860, 0.850, 0.780 |
| postgres-query-exec-arch-001 | — | `mcp-remote-direct` | 4 | 0.895 | 0.105 | 1.000, 0.900, 0.750, 0.930 |
