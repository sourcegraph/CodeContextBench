# ccb_design_haiku_022326

## baseline-local-direct

- Valid tasks: `13`
- Mean reward: `0.770`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [django-modeladmin-impact-001](../tasks/ccb_design_haiku_022326--baseline--django-modeladmin-impact-001.html) | `passed` | 1.000 | 0.000 | 9 | traj, tx |
| [django-orm-query-arch-001](../tasks/ccb_design_haiku_022326--baseline--django-orm-query-arch-001.html) | `passed` | 0.910 | 0.000 | 53 | traj, tx |
| [django-pre-validate-signal-design-001](../tasks/ccb_design_haiku_022326--baseline--django-pre-validate-signal-design-001.html) | `passed` | 1.000 | 0.000 | 49 | traj, tx |
| [django-rate-limit-design-001](../tasks/ccb_design_haiku_022326--baseline--django-rate-limit-design-001.html) | `passed` | 0.900 | 0.000 | 12 | traj, tx |
| [envoy-routeconfig-dep-chain-001](../tasks/ccb_design_haiku_022326--baseline--envoy-routeconfig-dep-chain-001.html) | `passed` | 1.000 | 0.000 | 14 | traj, tx |
| [envoy-stream-aggregated-sym-001](../tasks/ccb_design_haiku_022326--baseline--envoy-stream-aggregated-sym-001.html) | `passed` | 0.570 | 0.000 | 90 | traj, tx |
| [flipt-protobuf-metadata-design-001](../tasks/ccb_design_haiku_022326--baseline--flipt-protobuf-metadata-design-001.html) | `passed` | 1.000 | 0.000 | 39 | traj, tx |
| [flipt-transitive-deps-001](../tasks/ccb_design_haiku_022326--baseline--flipt-transitive-deps-001.html) | `passed` | 0.856 | 0.000 | 53 | traj, tx |
| [k8s-sharedinformer-sym-001](../tasks/ccb_design_haiku_022326--baseline--k8s-sharedinformer-sym-001.html) | `passed` | 0.630 | 0.000 | 27 | traj, tx |
| [k8s-typemeta-dep-chain-001](../tasks/ccb_design_haiku_022326--baseline--k8s-typemeta-dep-chain-001.html) | `passed` | 0.330 | 0.000 | 22 | traj, tx |
| [postgres-query-exec-arch-001](../tasks/ccb_design_haiku_022326--baseline--postgres-query-exec-arch-001.html) | `passed` | 0.840 | 0.000 | 44 | traj, tx |
| [quantlib-barrier-pricing-arch-001](../tasks/ccb_design_haiku_022326--baseline--quantlib-barrier-pricing-arch-001.html) | `passed` | 0.850 | 0.000 | 37 | traj, tx |
| [terraform-provider-iface-sym-001](../tasks/ccb_design_haiku_022326--baseline--terraform-provider-iface-sym-001.html) | `passed` | 0.120 | 0.000 | 91 | traj, tx |

## mcp-remote-direct

- Valid tasks: `20`
- Mean reward: `0.718`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_camel-routing-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_camel-routing-arch-001.html) | `passed` | 0.730 | 0.966 | 29 | traj, tx |
| [sgonly_django-modeladmin-impact-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_django-modeladmin-impact-001.html) | `passed` | 1.000 | 0.939 | 33 | traj, tx |
| [sgonly_django-orm-query-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_django-orm-query-arch-001.html) | `passed` | 0.990 | 0.969 | 32 | traj, tx |
| [sgonly_django-pre-validate-signal-design-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_django-pre-validate-signal-design-001.html) | `passed` | 1.000 | 0.157 | 70 | traj, tx |
| [sgonly_django-rate-limit-design-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_django-rate-limit-design-001.html) | `passed` | 1.000 | 0.333 | 21 | traj, tx |
| [sgonly_envoy-routeconfig-dep-chain-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_envoy-routeconfig-dep-chain-001.html) | `passed` | 1.000 | 0.857 | 14 | traj, tx |
| [sgonly_envoy-stream-aggregated-sym-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_envoy-stream-aggregated-sym-001.html) | `passed` | 0.320 | 0.971 | 35 | traj, tx |
| [sgonly_etcd-grpc-api-upgrade-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_etcd-grpc-api-upgrade-001.html) | `passed` | 0.714 | 0.108 | 74 | traj, tx |
| [sgonly_flink-checkpoint-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_flink-checkpoint-arch-001.html) | `passed` | 0.730 | 0.958 | 24 | traj, tx |
| [sgonly_flipt-protobuf-metadata-design-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_flipt-protobuf-metadata-design-001.html) | `passed` | 0.330 | 0.345 | 55 | traj, tx |
| [sgonly_flipt-transitive-deps-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_flipt-transitive-deps-001.html) | `passed` | 0.711 | 0.949 | 39 | traj, tx |
| [sgonly_k8s-crd-lifecycle-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_k8s-crd-lifecycle-arch-001.html) | `passed` | 0.770 | 0.829 | 35 | traj, tx |
| [sgonly_k8s-dra-allocation-impact-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_k8s-dra-allocation-impact-001.html) | `passed` | 0.900 | 0.913 | 23 | traj, tx |
| [sgonly_k8s-scheduler-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_k8s-scheduler-arch-001.html) | `passed` | 0.720 | 0.773 | 22 | traj, tx |
| [sgonly_k8s-sharedinformer-sym-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_k8s-sharedinformer-sym-001.html) | `passed` | 0.620 | 0.967 | 60 | traj, tx |
| [sgonly_k8s-typemeta-dep-chain-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_k8s-typemeta-dep-chain-001.html) | `passed` | 0.670 | 0.833 | 18 | traj, tx |
| [sgonly_kafka-flink-streaming-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_kafka-flink-streaming-arch-001.html) | `passed` | 0.400 | 0.896 | 48 | traj, tx |
| [sgonly_postgres-query-exec-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_postgres-query-exec-arch-001.html) | `passed` | 0.830 | 0.976 | 42 | traj, tx |
| [sgonly_quantlib-barrier-pricing-arch-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_quantlib-barrier-pricing-arch-001.html) | `passed` | 0.830 | 0.968 | 31 | traj, tx |
| [sgonly_terraform-provider-iface-sym-001](../tasks/ccb_design_haiku_022326--mcp--sgonly_terraform-provider-iface-sym-001.html) | `passed` | 0.090 | 0.929 | 28 | traj, tx |
