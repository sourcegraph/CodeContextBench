# csb_sdlc_understand

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [csb_sdlc_understand_haiku_20260227_132300](../runs/csb_sdlc_understand_haiku_20260227_132300.md) | `baseline-local-direct` | 7 | 1.000 | 1.000 |
| [csb_sdlc_understand_haiku_20260227_132300](../runs/csb_sdlc_understand_haiku_20260227_132300.md) | `mcp-remote-direct` | 12 | 0.858 | 0.917 |
| [csb_sdlc_understand_haiku_20260227_132304](../runs/csb_sdlc_understand_haiku_20260227_132304.md) | `baseline-local-direct` | 7 | 0.857 | 0.857 |
| [csb_sdlc_understand_haiku_20260227_132304](../runs/csb_sdlc_understand_haiku_20260227_132304.md) | `mcp-remote-direct` | 12 | 0.942 | 1.000 |
| [csb_sdlc_understand_haiku_20260228_124521](../runs/csb_sdlc_understand_haiku_20260228_124521.md) | `mcp-remote-direct` | 4 | 0.823 | 1.000 |
| [csb_sdlc_understand_haiku_20260302_221730](../runs/csb_sdlc_understand_haiku_20260302_221730.md) | `baseline-local-direct` | 2 | 0.860 | 1.000 |
| [csb_sdlc_understand_haiku_20260302_221730](../runs/csb_sdlc_understand_haiku_20260302_221730.md) | `mcp-remote-direct` | 10 | 0.551 | 0.700 |
| [csb_sdlc_understand_haiku_20260302_224010](../runs/csb_sdlc_understand_haiku_20260302_224010.md) | `baseline-local-direct` | 8 | 0.818 | 1.000 |
| [csb_sdlc_understand_haiku_20260302_224010](../runs/csb_sdlc_understand_haiku_20260302_224010.md) | `mcp-remote-direct` | 3 | 0.857 | 1.000 |
| [understand_haiku_20260301_071233](../runs/understand_haiku_20260301_071233.md) | `baseline-local-direct` | 10 | 0.894 | 1.000 |
| [understand_haiku_20260301_071233](../runs/understand_haiku_20260301_071233.md) | `mcp-remote-direct` | 20 | 0.850 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [argocd-arch-orient-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--argocd-arch-orient-001.html) | [source](../../../benchmarks/csb_sdlc_understand/argocd-arch-orient-001) | `baseline-local-direct` | `passed` | 0.850 | 6 | 0.000 |
| [mcp_argocd-arch-orient-001_gz699w](../tasks/csb_sdlc_understand_haiku_20260302_224010--mcp-remote-direct--mcp_argocd-arch-orient-001_gz699w.html) | [source](../../../benchmarks/csb_sdlc_understand/argocd-arch-orient-001) | `mcp-remote-direct` | `passed` | 0.770 | 6 | 0.976 |
| [mcp_argocd-arch-orient-001_opacrn](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_argocd-arch-orient-001_opacrn.html) | [source](../../../benchmarks/csb_sdlc_understand/argocd-arch-orient-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [sgonly_argocd-arch-orient-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_argocd-arch-orient-001.html) | [source](../../../benchmarks/csb_sdlc_understand/argocd-arch-orient-001) | `mcp-remote-direct` | `passed` | 0.770 | 6 | 0.973 |
| [argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--argocd-sync-reconcile-qa-001.html) | — | `baseline-local-direct` | `passed` | 0.820 | 4 | 0.000 |
| [sgonly_argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_argocd-sync-reconcile-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.870 | 4 | 0.969 |
| [cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--cilium-ebpf-datapath-handoff-001.html) | — | `baseline-local-direct` | `passed` | 0.830 | 4 | 0.000 |
| [sgonly_cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_cilium-ebpf-datapath-handoff-001.html) | — | `mcp-remote-direct` | `passed` | 0.900 | 4 | 0.935 |
| [cilium-ebpf-fault-qa-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--cilium-ebpf-fault-qa-001.html) | [source](../../../benchmarks/csb_sdlc_understand/cilium-ebpf-fault-qa-001) | `baseline-local-direct` | `passed` | 0.940 | 6 | 0.000 |
| [mcp_cilium-ebpf-fault-qa-001_nnyhvi](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_cilium-ebpf-fault-qa-001_nnyhvi.html) | [source](../../../benchmarks/csb_sdlc_understand/cilium-ebpf-fault-qa-001) | `mcp-remote-direct` | `passed` | 0.800 | 5 | 0.966 |
| [sgonly_cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_cilium-ebpf-fault-qa-001.html) | [source](../../../benchmarks/csb_sdlc_understand/cilium-ebpf-fault-qa-001) | `mcp-remote-direct` | `passed` | 0.850 | 5 | 0.963 |
| [cilium-project-orient-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--cilium-project-orient-001.html) | [source](../../../benchmarks/csb_sdlc_understand/cilium-project-orient-001) | `baseline-local-direct` | `passed` | 0.920 | 6 | 0.000 |
| [mcp_cilium-project-orient-001_ffmygj](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_cilium-project-orient-001_ffmygj.html) | [source](../../../benchmarks/csb_sdlc_understand/cilium-project-orient-001) | `mcp-remote-direct` | `passed` | 0.970 | 5 | 0.963 |
| [sgonly_cilium-project-orient-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_cilium-project-orient-001.html) | [source](../../../benchmarks/csb_sdlc_understand/cilium-project-orient-001) | `mcp-remote-direct` | `passed` | 0.910 | 5 | 0.923 |
| [django-composite-field-recover-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--django-composite-field-recover-001.html) | [source](../../../benchmarks/csb_sdlc_understand/django-composite-field-recover-001) | `baseline-local-direct` | `passed` | 0.400 | 6 | 0.000 |
| [mcp_django-composite-field-recover-001_frtplc](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_django-composite-field-recover-001_frtplc.html) | [source](../../../benchmarks/csb_sdlc_understand/django-composite-field-recover-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [mcp_django-composite-field-recover-001_48TtoY](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_django-composite-field-recover-001_48TtoY.html) | [source](../../../benchmarks/csb_sdlc_understand/django-composite-field-recover-001) | `mcp-remote-direct` | `passed` | 0.400 | 6 | 0.163 |
| [sgonly_django-composite-field-recover-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_django-composite-field-recover-001.html) | [source](../../../benchmarks/csb_sdlc_understand/django-composite-field-recover-001) | `mcp-remote-direct` | `passed` | 0.400 | 6 | 0.279 |
| [django-template-inherit-recall-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--django-template-inherit-recall-001.html) | [source](../../../benchmarks/csb_sdlc_understand/django-template-inherit-recall-001) | `baseline-local-direct` | `passed` | 0.900 | 6 | 0.000 |
| [mcp_django-template-inherit-recall-001_gvxsja](../tasks/csb_sdlc_understand_haiku_20260302_224010--mcp-remote-direct--mcp_django-template-inherit-recall-001_gvxsja.html) | [source](../../../benchmarks/csb_sdlc_understand/django-template-inherit-recall-001) | `mcp-remote-direct` | `passed` | 0.800 | 6 | 0.253 |
| [mcp_django-template-inherit-recall-001_bbepsu](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_django-template-inherit-recall-001_bbepsu.html) | [source](../../../benchmarks/csb_sdlc_understand/django-template-inherit-recall-001) | `mcp-remote-direct` | `passed` | 0.250 | 6 | 0.150 |
| [sgonly_django-template-inherit-recall-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_django-template-inherit-recall-001.html) | [source](../../../benchmarks/csb_sdlc_understand/django-template-inherit-recall-001) | `mcp-remote-direct` | `passed` | 0.800 | 6 | 0.309 |
| [envoy-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-contributor-workflow-001.html) | — | `baseline-local-direct` | `passed` | 0.940 | 4 | 0.000 |
| [sgonly_envoy-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-contributor-workflow-001.html) | — | `mcp-remote-direct` | `passed` | 0.940 | 4 | 0.900 |
| [envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-ext-authz-handoff-001.html) | — | `baseline-local-direct` | `passed` | 0.890 | 4 | 0.000 |
| [sgonly_envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.html) | — | `mcp-remote-direct` | `passed` | 0.830 | 4 | 0.950 |
| [envoy-filter-chain-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-filter-chain-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_envoy-filter-chain-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-filter-chain-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.960 | 4 | 0.973 |
| [envoy-pool-ready-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--envoy-pool-ready-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_envoy-pool-ready-search-001_EwEb4o](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_envoy-pool-ready-search-001_EwEb4o.html) | — | `mcp-remote-direct` | `passed` | 0.300 | 2 | 0.000 |
| [mcp_envoy-pool-ready-search-001_HxPKch](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_envoy-pool-ready-search-001_HxPKch.html) | — | `mcp-remote-direct` | `passed` | 0.300 | 2 | 0.000 |
| [envoy-request-routing-qa-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--envoy-request-routing-qa-001.html) | [source](../../../benchmarks/csb_sdlc_understand/envoy-request-routing-qa-001) | `baseline-local-direct` | `passed` | 0.950 | 6 | 0.000 |
| [mcp_envoy-request-routing-qa-001_7dwajw](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_envoy-request-routing-qa-001_7dwajw.html) | [source](../../../benchmarks/csb_sdlc_understand/envoy-request-routing-qa-001) | `mcp-remote-direct` | `passed` | 0.910 | 5 | 0.972 |
| [sgonly_envoy-request-routing-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-request-routing-qa-001.html) | [source](../../../benchmarks/csb_sdlc_understand/envoy-request-routing-qa-001) | `mcp-remote-direct` | `passed` | 0.910 | 5 | 0.975 |
| [envoy-retry-eval-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--envoy-retry-eval-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_envoy-retry-eval-search-001_QkEHtp](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_envoy-retry-eval-search-001_QkEHtp.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_envoy-retry-eval-search-001_pwYQ4g](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_envoy-retry-eval-search-001_pwYQ4g.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [firefox-cache-race-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--firefox-cache-race-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.200 |
| [mcp_firefox-cache-race-search-001_1v6Sie](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_firefox-cache-race-search-001_1v6Sie.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.667 |
| [firefox-http-response-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--firefox-http-response-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_firefox-http-response-search-001_QRqYdt](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_firefox-http-response-search-001_QRqYdt.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.857 |
| [grafana-field-calcs-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--grafana-field-calcs-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_grafana-field-calcs-search-001_B5oEI1](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_grafana-field-calcs-search-001_B5oEI1.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_grafana-field-calcs-search-001_LFZ6hQ](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_grafana-field-calcs-search-001_LFZ6hQ.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [istio-xds-serving-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--istio-xds-serving-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_istio-xds-serving-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_istio-xds-serving-qa-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.968 |
| [k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--k8s-cri-containerd-reason-001.html) | — | `baseline-local-direct` | `passed` | 0.850 | 4 | 0.000 |
| [sgonly_k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_k8s-cri-containerd-reason-001.html) | — | `mcp-remote-direct` | `passed` | 0.850 | 4 | 0.846 |
| [k8s-eviction-sync-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--k8s-eviction-sync-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_k8s-eviction-sync-search-001_KmypBE](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_k8s-eviction-sync-search-001_KmypBE.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.714 |
| [mcp_k8s-eviction-sync-search-001_auPFDM](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_k8s-eviction-sync-search-001_auPFDM.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.625 |
| [k8s-scheduler-filter-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--k8s-scheduler-filter-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_k8s-scheduler-filter-search-001_1B4q1U](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_k8s-scheduler-filter-search-001_1B4q1U.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.667 |
| [mcp_k8s-scheduler-filter-search-001_XRD3ip](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_k8s-scheduler-filter-search-001_XRD3ip.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.800 |
| [kafka-assign-handler-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--kafka-assign-handler-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_kafka-assign-handler-search-001_VyIRYg](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_kafka-assign-handler-search-001_VyIRYg.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.833 |
| [mcp_kafka-assign-handler-search-001_1PpNNb](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_kafka-assign-handler-search-001_1PpNNb.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.778 |
| [kafka-batch-drain-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--kafka-batch-drain-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_kafka-batch-drain-search-001_ZYGXDh](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_kafka-batch-drain-search-001_ZYGXDh.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.600 |
| [mcp_kafka-batch-drain-search-001_tJsbqz](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_kafka-batch-drain-search-001_tJsbqz.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.800 |
| [kafka-build-orient-001](../tasks/csb_sdlc_understand_haiku_20260302_221730--baseline-local-direct--kafka-build-orient-001.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-build-orient-001) | `baseline-local-direct` | `passed` | 0.770 | 5 | 0.000 |
| [mcp_kafka-build-orient-001_ifrnit](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_kafka-build-orient-001_ifrnit.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-build-orient-001) | `mcp-remote-direct` | `passed` | 0.840 | 5 | 0.962 |
| [sgonly_kafka-build-orient-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_kafka-build-orient-001.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-build-orient-001) | `mcp-remote-direct` | `passed` | 0.770 | 5 | 0.963 |
| [kafka-contributor-workflow-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--kafka-contributor-workflow-001.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-contributor-workflow-001) | `baseline-local-direct` | `passed` | 0.950 | 6 | 0.000 |
| [mcp_kafka-contributor-workflow-001_v352ni](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_kafka-contributor-workflow-001_v352ni.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-contributor-workflow-001) | `mcp-remote-direct` | `passed` | 0.890 | 6 | 0.947 |
| [mcp_kafka-contributor-workflow-001_M1NQMf](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_kafka-contributor-workflow-001_M1NQMf.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-contributor-workflow-001) | `mcp-remote-direct` | `passed` | 0.890 | 6 | 0.944 |
| [sgonly_kafka-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_kafka-contributor-workflow-001.html) | [source](../../../benchmarks/csb_sdlc_understand/kafka-contributor-workflow-001) | `mcp-remote-direct` | `passed` | 0.820 | 6 | 0.944 |
| [kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--kafka-message-lifecycle-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_kafka-message-lifecycle-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.890 | 4 | 0.967 |
| [numpy-dtype-localize-001](../tasks/csb_sdlc_understand_haiku_20260302_224010--baseline-local-direct--numpy-dtype-localize-001.html) | [source](../../../benchmarks/csb_sdlc_understand/numpy-dtype-localize-001) | `baseline-local-direct` | `passed` | 0.633 | 6 | 0.000 |
| [mcp_numpy-dtype-localize-001_st1kho](../tasks/csb_sdlc_understand_haiku_20260302_224010--mcp-remote-direct--mcp_numpy-dtype-localize-001_st1kho.html) | [source](../../../benchmarks/csb_sdlc_understand/numpy-dtype-localize-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.957 |
| [mcp_numpy-dtype-localize-001_hauwan](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_numpy-dtype-localize-001_hauwan.html) | [source](../../../benchmarks/csb_sdlc_understand/numpy-dtype-localize-001) | `mcp-remote-direct` | `passed` | 0.850 | 6 | 0.906 |
| [sgonly_numpy-dtype-localize-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_numpy-dtype-localize-001.html) | [source](../../../benchmarks/csb_sdlc_understand/numpy-dtype-localize-001) | `mcp-remote-direct` | `passed` | 0.850 | 6 | 0.939 |
| [pandas-pivot-internal-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--pandas-pivot-internal-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_pandas-pivot-internal-search-001_tnxuuD](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_pandas-pivot-internal-search-001_tnxuuD.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_pandas-pivot-internal-search-001_9DdhSm](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_pandas-pivot-internal-search-001_9DdhSm.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [rust-liveness-gen-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--rust-liveness-gen-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_rust-liveness-gen-search-001_DJr9ub](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_rust-liveness-gen-search-001_DJr9ub.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_rust-liveness-gen-search-001_Aru7f4](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_rust-liveness-gen-search-001_Aru7f4.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [rust-type-tests-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--rust-type-tests-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_rust-type-tests-search-001_4Sg2dg](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_rust-type-tests-search-001_4Sg2dg.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_rust-type-tests-search-001_OKq7k3](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_rust-type-tests-search-001_OKq7k3.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.833 |
| [sklearn-fastica-fit-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132300--baseline-local-direct--sklearn-fastica-fit-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_sklearn-fastica-fit-search-001_KSnBCG](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_sklearn-fastica-fit-search-001_KSnBCG.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [mcp_sklearn-fastica-fit-search-001_unhAKu](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_sklearn-fastica-fit-search-001_unhAKu.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |
| [terraform-plan-pipeline-qa-001](../tasks/csb_sdlc_understand_haiku_20260302_221730--baseline-local-direct--terraform-plan-pipeline-qa-001.html) | [source](../../../benchmarks/csb_sdlc_understand/terraform-plan-pipeline-qa-001) | `baseline-local-direct` | `passed` | 0.950 | 5 | 0.000 |
| [mcp_terraform-plan-pipeline-qa-001_txjd9y](../tasks/csb_sdlc_understand_haiku_20260302_221730--mcp-remote-direct--mcp_terraform-plan-pipeline-qa-001_txjd9y.html) | [source](../../../benchmarks/csb_sdlc_understand/terraform-plan-pipeline-qa-001) | `mcp-remote-direct` | `failed` | 0.000 | 5 | - |
| [sgonly_terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_terraform-plan-pipeline-qa-001.html) | [source](../../../benchmarks/csb_sdlc_understand/terraform-plan-pipeline-qa-001) | `mcp-remote-direct` | `passed` | 0.950 | 5 | 0.935 |
| [terraform-state-backend-handoff-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--terraform-state-backend-handoff-001.html) | — | `baseline-local-direct` | `passed` | 0.660 | 4 | 0.000 |
| [sgonly_terraform-state-backend-handoff-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001.html) | — | `mcp-remote-direct` | `passed` | 0.730 | 4 | 0.903 |
| [vscode-ext-host-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--vscode-ext-host-qa-001.html) | — | `baseline-local-direct` | `passed` | 0.950 | 4 | 0.000 |
| [sgonly_vscode-ext-host-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_vscode-ext-host-qa-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.957 |
| [vscode-keybinding-merge-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--vscode-keybinding-merge-search-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | 0.000 |
| [mcp_vscode-keybinding-merge-search-001_yI3kCw](../tasks/csb_sdlc_understand_haiku_20260227_132300--mcp-remote-direct--mcp_vscode-keybinding-merge-search-001_yI3kCw.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.000 |
| [mcp_vscode-keybinding-merge-search-001_ZZiuGd](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_vscode-keybinding-merge-search-001_ZZiuGd.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.000 |

## Multi-Run Variance

Tasks with multiple valid runs (20 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| argocd-arch-orient-001 | [source](../../../benchmarks/csb_sdlc_understand/argocd-arch-orient-001) | `baseline-local-direct` | 5 | 0.604 | 0.343 | 0.000, 0.710, 0.750, 0.710, 0.850 |
| argocd-arch-orient-001 | [source](../../../benchmarks/csb_sdlc_understand/argocd-arch-orient-001) | `mcp-remote-direct` | 4 | 0.780 | 0.020 | 0.810, 0.770, 0.770, 0.770 |
| cilium-ebpf-fault-qa-001 | [source](../../../benchmarks/csb_sdlc_understand/cilium-ebpf-fault-qa-001) | `baseline-local-direct` | 5 | 0.850 | 0.067 | 0.770, 0.870, 0.800, 0.870, 0.940 |
| cilium-ebpf-fault-qa-001 | [source](../../../benchmarks/csb_sdlc_understand/cilium-ebpf-fault-qa-001) | `mcp-remote-direct` | 4 | 0.868 | 0.091 | 0.820, 1.000, 0.850, 0.800 |
| cilium-project-orient-001 | [source](../../../benchmarks/csb_sdlc_understand/cilium-project-orient-001) | `baseline-local-direct` | 4 | 0.698 | 0.466 | 0.000, 0.910, 0.960, 0.920 |
| cilium-project-orient-001 | [source](../../../benchmarks/csb_sdlc_understand/cilium-project-orient-001) | `mcp-remote-direct` | 4 | 0.940 | 0.029 | 0.960, 0.920, 0.910, 0.970 |
| django-composite-field-recover-001 | [source](../../../benchmarks/csb_sdlc_understand/django-composite-field-recover-001) | `baseline-local-direct` | 6 | 0.417 | 0.286 | 0.400, 0.400, 0.000, 0.900, 0.400, 0.400 |
| django-composite-field-recover-001 | [source](../../../benchmarks/csb_sdlc_understand/django-composite-field-recover-001) | `mcp-remote-direct` | 4 | 0.487 | 0.175 | 0.750, 0.400, 0.400, 0.400 |
| django-template-inherit-recall-001 | [source](../../../benchmarks/csb_sdlc_understand/django-template-inherit-recall-001) | `baseline-local-direct` | 5 | 0.710 | 0.261 | 0.250, 0.800, 0.800, 0.800, 0.900 |
| django-template-inherit-recall-001 | [source](../../../benchmarks/csb_sdlc_understand/django-template-inherit-recall-001) | `mcp-remote-direct` | 4 | 0.525 | 0.318 | 0.250, 0.800, 0.250, 0.800 |
| envoy-request-routing-qa-001 | [source](../../../benchmarks/csb_sdlc_understand/envoy-request-routing-qa-001) | `baseline-local-direct` | 4 | 0.705 | 0.470 | 0.000, 0.910, 0.960, 0.950 |
| envoy-request-routing-qa-001 | [source](../../../benchmarks/csb_sdlc_understand/envoy-request-routing-qa-001) | `mcp-remote-direct` | 4 | 0.900 | 0.020 | 0.870, 0.910, 0.910, 0.910 |
| kafka-build-orient-001 | [source](../../../benchmarks/csb_sdlc_understand/kafka-build-orient-001) | `baseline-local-direct` | 5 | 0.634 | 0.358 | 0.720, 0.840, 0.000, 0.840, 0.770 |
| kafka-build-orient-001 | [source](../../../benchmarks/csb_sdlc_understand/kafka-build-orient-001) | `mcp-remote-direct` | 4 | 0.848 | 0.059 | 0.870, 0.910, 0.770, 0.840 |
| kafka-contributor-workflow-001 | [source](../../../benchmarks/csb_sdlc_understand/kafka-contributor-workflow-001) | `baseline-local-direct` | 4 | 0.943 | 0.015 | 0.950, 0.920, 0.950, 0.950 |
| kafka-contributor-workflow-001 | [source](../../../benchmarks/csb_sdlc_understand/kafka-contributor-workflow-001) | `mcp-remote-direct` | 5 | 0.848 | 0.038 | 0.820, 0.890, 0.820, 0.820, 0.890 |
| numpy-dtype-localize-001 | [source](../../../benchmarks/csb_sdlc_understand/numpy-dtype-localize-001) | `baseline-local-direct` | 5 | 0.710 | 0.213 | 1.000, 0.417, 0.783, 0.717, 0.633 |
| numpy-dtype-localize-001 | [source](../../../benchmarks/csb_sdlc_understand/numpy-dtype-localize-001) | `mcp-remote-direct` | 6 | 0.939 | 0.073 | 0.933, 1.000, 1.000, 0.850, 0.850, 1.000 |
| terraform-plan-pipeline-qa-001 | [source](../../../benchmarks/csb_sdlc_understand/terraform-plan-pipeline-qa-001) | `baseline-local-direct` | 4 | 0.725 | 0.484 | 0.000, 0.950, 1.000, 0.950 |
| terraform-plan-pipeline-qa-001 | [source](../../../benchmarks/csb_sdlc_understand/terraform-plan-pipeline-qa-001) | `mcp-remote-direct` | 3 | 0.950 | 0.000 | 0.950, 0.950, 0.950 |
