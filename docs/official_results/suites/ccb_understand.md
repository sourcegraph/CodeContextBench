# csb_sdlc_understand

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [csb_sdlc_understand_haiku_20260227_132304](../runs/csb_sdlc_understand_haiku_20260227_132304.md) | `baseline-local-direct` | 14 | 0.864 | 0.929 |
| [csb_sdlc_understand_haiku_20260227_132304](../runs/csb_sdlc_understand_haiku_20260227_132304.md) | `mcp-remote-direct` | 4 | 1.000 | 1.000 |
| [csb_sdlc_understand_haiku_20260228_124521](../runs/csb_sdlc_understand_haiku_20260228_124521.md) | `mcp-remote-direct` | 4 | 0.823 | 1.000 |
| [understand_haiku_20260301_071233](../runs/understand_haiku_20260301_071233.md) | `baseline-local-direct` | 20 | 0.884 | 1.000 |
| [understand_haiku_20260301_071233](../runs/understand_haiku_20260301_071233.md) | `mcp-remote-direct` | 20 | 0.850 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [argocd-arch-orient-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--argocd-arch-orient-001.html) | — | `baseline-local-direct` | `passed` | 0.750 | 3 | 0.000 |
| [sgonly_argocd-arch-orient-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_argocd-arch-orient-001.html) | — | `mcp-remote-direct` | `passed` | 0.770 | 3 | 0.973 |
| [argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--argocd-sync-reconcile-qa-001.html) | — | `baseline-local-direct` | `passed` | 0.820 | 3 | 0.000 |
| [sgonly_argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_argocd-sync-reconcile-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.870 | 3 | 0.969 |
| [cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--cilium-ebpf-datapath-handoff-001.html) | — | `baseline-local-direct` | `passed` | 0.830 | 3 | 0.000 |
| [sgonly_cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_cilium-ebpf-datapath-handoff-001.html) | — | `mcp-remote-direct` | `passed` | 0.900 | 3 | 0.935 |
| [cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--cilium-ebpf-fault-qa-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 3 | 0.000 |
| [sgonly_cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_cilium-ebpf-fault-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.850 | 3 | 0.963 |
| [cilium-project-orient-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--cilium-project-orient-001.html) | — | `baseline-local-direct` | `passed` | 0.960 | 3 | 0.000 |
| [sgonly_cilium-project-orient-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_cilium-project-orient-001.html) | — | `mcp-remote-direct` | `passed` | 0.910 | 3 | 0.923 |
| [django-composite-field-recover-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--django-composite-field-recover-001.html) | — | `baseline-local-direct` | `passed` | 0.900 | 4 | 0.000 |
| [mcp_django-composite-field-recover-001_48TtoY](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_django-composite-field-recover-001_48TtoY.html) | — | `mcp-remote-direct` | `passed` | 0.400 | 5 | 0.163 |
| [sgonly_django-composite-field-recover-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_django-composite-field-recover-001.html) | — | `mcp-remote-direct` | `passed` | 0.400 | 5 | 0.279 |
| [django-template-inherit-recall-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--django-template-inherit-recall-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 3 | 0.000 |
| [sgonly_django-template-inherit-recall-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_django-template-inherit-recall-001.html) | — | `mcp-remote-direct` | `passed` | 0.800 | 3 | 0.309 |
| [envoy-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-contributor-workflow-001.html) | — | `baseline-local-direct` | `passed` | 0.940 | 3 | 0.000 |
| [sgonly_envoy-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-contributor-workflow-001.html) | — | `mcp-remote-direct` | `passed` | 0.940 | 3 | 0.900 |
| [envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-ext-authz-handoff-001.html) | — | `baseline-local-direct` | `passed` | 0.890 | 4 | 0.000 |
| [sgonly_envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.html) | — | `mcp-remote-direct` | `passed` | 0.830 | 4 | 0.950 |
| [envoy-filter-chain-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-filter-chain-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 3 | 0.000 |
| [sgonly_envoy-filter-chain-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-filter-chain-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.960 | 3 | 0.973 |
| [envoy-pool-ready-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--envoy-pool-ready-search-001.html) | — | `baseline-local-direct` | `passed` | 0.300 | 1 | 0.000 |
| [envoy-request-routing-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--envoy-request-routing-qa-001.html) | — | `baseline-local-direct` | `passed` | 0.960 | 3 | 0.000 |
| [sgonly_envoy-request-routing-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_envoy-request-routing-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.910 | 3 | 0.975 |
| [envoy-retry-eval-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--envoy-retry-eval-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [firefox-cache-race-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--firefox-cache-race-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.200 |
| [mcp_firefox-cache-race-search-001_1v6Sie](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_firefox-cache-race-search-001_1v6Sie.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.667 |
| [firefox-http-response-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--firefox-http-response-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_firefox-http-response-search-001_QRqYdt](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_firefox-http-response-search-001_QRqYdt.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.857 |
| [grafana-field-calcs-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--grafana-field-calcs-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [istio-xds-serving-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--istio-xds-serving-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 3 | 0.000 |
| [sgonly_istio-xds-serving-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_istio-xds-serving-qa-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.968 |
| [k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--k8s-cri-containerd-reason-001.html) | — | `baseline-local-direct` | `passed` | 0.850 | 4 | 0.000 |
| [sgonly_k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_k8s-cri-containerd-reason-001.html) | — | `mcp-remote-direct` | `passed` | 0.850 | 4 | 0.846 |
| [k8s-eviction-sync-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--k8s-eviction-sync-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_k8s-eviction-sync-search-001_auPFDM](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_k8s-eviction-sync-search-001_auPFDM.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.625 |
| [k8s-scheduler-filter-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--k8s-scheduler-filter-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_k8s-scheduler-filter-search-001_XRD3ip](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_k8s-scheduler-filter-search-001_XRD3ip.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.800 |
| [kafka-assign-handler-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--kafka-assign-handler-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_kafka-assign-handler-search-001_1PpNNb](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_kafka-assign-handler-search-001_1PpNNb.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.778 |
| [kafka-batch-drain-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--kafka-batch-drain-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [mcp_kafka-batch-drain-search-001_tJsbqz](../tasks/csb_sdlc_understand_haiku_20260227_132304--mcp-remote-direct--mcp_kafka-batch-drain-search-001_tJsbqz.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 1 | 0.800 |
| [kafka-build-orient-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--kafka-build-orient-001.html) | — | `baseline-local-direct` | `passed` | 0.840 | 4 | 0.000 |
| [sgonly_kafka-build-orient-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_kafka-build-orient-001.html) | — | `mcp-remote-direct` | `passed` | 0.770 | 4 | 0.963 |
| [kafka-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--kafka-contributor-workflow-001.html) | — | `baseline-local-direct` | `passed` | 0.950 | 3 | 0.000 |
| [mcp_kafka-contributor-workflow-001_M1NQMf](../tasks/csb_sdlc_understand_haiku_20260228_124521--mcp-remote-direct--mcp_kafka-contributor-workflow-001_M1NQMf.html) | — | `mcp-remote-direct` | `passed` | 0.890 | 4 | 0.944 |
| [sgonly_kafka-contributor-workflow-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_kafka-contributor-workflow-001.html) | — | `mcp-remote-direct` | `passed` | 0.820 | 4 | 0.944 |
| [kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--kafka-message-lifecycle-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 3 | 0.000 |
| [sgonly_kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_kafka-message-lifecycle-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.890 | 3 | 0.967 |
| [numpy-dtype-localize-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--numpy-dtype-localize-001.html) | — | `baseline-local-direct` | `passed` | 0.783 | 4 | 0.000 |
| [sgonly_numpy-dtype-localize-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_numpy-dtype-localize-001.html) | — | `mcp-remote-direct` | `passed` | 0.850 | 4 | 0.939 |
| [pandas-pivot-internal-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--pandas-pivot-internal-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [rust-liveness-gen-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--rust-liveness-gen-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [rust-type-tests-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--rust-type-tests-search-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 1 | 0.000 |
| [sklearn-fastica-fit-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--sklearn-fastica-fit-search-001.html) | — | `baseline-local-direct` | `passed` | 0.800 | 1 | 0.000 |
| [terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--terraform-plan-pipeline-qa-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 3 | 0.000 |
| [sgonly_terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_terraform-plan-pipeline-qa-001.html) | — | `mcp-remote-direct` | `passed` | 0.950 | 3 | 0.935 |
| [terraform-state-backend-handoff-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--terraform-state-backend-handoff-001.html) | — | `baseline-local-direct` | `passed` | 0.660 | 4 | 0.000 |
| [sgonly_terraform-state-backend-handoff-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001.html) | — | `mcp-remote-direct` | `passed` | 0.730 | 4 | 0.903 |
| [vscode-ext-host-qa-001](../tasks/understand_haiku_20260301_071233--baseline-local-direct--vscode-ext-host-qa-001.html) | — | `baseline-local-direct` | `passed` | 0.950 | 4 | 0.000 |
| [sgonly_vscode-ext-host-qa-001](../tasks/understand_haiku_20260301_071233--mcp-remote-direct--sgonly_vscode-ext-host-qa-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.957 |
| [vscode-keybinding-merge-search-001](../tasks/csb_sdlc_understand_haiku_20260227_132304--baseline-local-direct--vscode-keybinding-merge-search-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 1 | 0.000 |

## Multi-Run Variance

Tasks with multiple valid runs (20 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| argocd-arch-orient-001 | — | `baseline-local-direct` | 3 | 0.487 | 0.422 | 0.000, 0.710, 0.750 |
| argocd-arch-orient-001 | — | `mcp-remote-direct` | 3 | 0.783 | 0.023 | 0.810, 0.770, 0.770 |
| cilium-ebpf-fault-qa-001 | — | `baseline-local-direct` | 3 | 0.813 | 0.051 | 0.770, 0.870, 0.800 |
| cilium-ebpf-fault-qa-001 | — | `mcp-remote-direct` | 3 | 0.890 | 0.096 | 0.820, 1.000, 0.850 |
| cilium-project-orient-001 | — | `baseline-local-direct` | 3 | 0.623 | 0.540 | 0.000, 0.910, 0.960 |
| cilium-project-orient-001 | — | `mcp-remote-direct` | 3 | 0.930 | 0.026 | 0.960, 0.920, 0.910 |
| django-composite-field-recover-001 | — | `baseline-local-direct` | 4 | 0.425 | 0.369 | 0.400, 0.400, 0.000, 0.900 |
| django-composite-field-recover-001 | — | `mcp-remote-direct` | 4 | 0.487 | 0.175 | 0.750, 0.400, 0.400, 0.400 |
| django-template-inherit-recall-001 | — | `baseline-local-direct` | 3 | 0.617 | 0.318 | 0.250, 0.800, 0.800 |
| django-template-inherit-recall-001 | — | `mcp-remote-direct` | 2 | 0.525 | 0.389 | 0.250, 0.800 |
| envoy-request-routing-qa-001 | — | `baseline-local-direct` | 3 | 0.623 | 0.540 | 0.000, 0.910, 0.960 |
| envoy-request-routing-qa-001 | — | `mcp-remote-direct` | 3 | 0.897 | 0.023 | 0.870, 0.910, 0.910 |
| kafka-build-orient-001 | — | `baseline-local-direct` | 4 | 0.600 | 0.404 | 0.720, 0.840, 0.000, 0.840 |
| kafka-build-orient-001 | — | `mcp-remote-direct` | 3 | 0.850 | 0.072 | 0.870, 0.910, 0.770 |
| kafka-contributor-workflow-001 | — | `baseline-local-direct` | 3 | 0.940 | 0.017 | 0.950, 0.920, 0.950 |
| kafka-contributor-workflow-001 | — | `mcp-remote-direct` | 4 | 0.838 | 0.035 | 0.820, 0.890, 0.820, 0.820 |
| numpy-dtype-localize-001 | — | `baseline-local-direct` | 3 | 0.733 | 0.295 | 1.000, 0.417, 0.783 |
| numpy-dtype-localize-001 | — | `mcp-remote-direct` | 4 | 0.946 | 0.071 | 0.933, 1.000, 1.000, 0.850 |
| terraform-plan-pipeline-qa-001 | — | `baseline-local-direct` | 3 | 0.650 | 0.564 | 0.000, 0.950, 1.000 |
| terraform-plan-pipeline-qa-001 | — | `mcp-remote-direct` | 3 | 0.950 | 0.000 | 0.950, 0.950, 0.950 |
