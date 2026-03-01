# understand_haiku_20260301_031852

## baseline-local-direct

- Valid tasks: `20`
- Mean reward: `0.728`
- Pass rate: `0.850`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [django-composite-field-recover-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--django-composite-field-recover-001.html) | `failed` | 0.000 | 0.000 | 27 | traj, tx |
| [k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--k8s-cri-containerd-reason-001.html) | `failed` | 0.000 | - | - | traj, tx |
| [kafka-build-orient-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--kafka-build-orient-001.html) | `failed` | 0.000 | 0.000 | 98 | traj, tx |
| [argocd-arch-orient-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--argocd-arch-orient-001.html) | `passed` | 0.710 | 0.000 | 44 | traj, tx |
| [argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--argocd-sync-reconcile-qa-001.html) | `passed` | 0.870 | 0.000 | 36 | traj, tx |
| [cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--cilium-ebpf-datapath-handoff-001.html) | `passed` | 0.780 | 0.000 | 30 | traj, tx |
| [cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--cilium-ebpf-fault-qa-001.html) | `passed` | 0.870 | 0.000 | 52 | traj, tx |
| [cilium-project-orient-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--cilium-project-orient-001.html) | `passed` | 0.910 | 0.000 | 47 | traj, tx |
| [django-template-inherit-recall-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--django-template-inherit-recall-001.html) | `passed` | 0.800 | 0.000 | 61 | traj, tx |
| [envoy-contributor-workflow-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--envoy-contributor-workflow-001.html) | `passed` | 0.980 | 0.000 | 24 | traj, tx |
| [envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--envoy-ext-authz-handoff-001.html) | `passed` | 0.890 | 0.000 | 33 | traj, tx |
| [envoy-filter-chain-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--envoy-filter-chain-qa-001.html) | `passed` | 0.930 | 0.000 | 59 | traj, tx |
| [envoy-request-routing-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--envoy-request-routing-qa-001.html) | `passed` | 0.910 | 0.000 | 47 | traj, tx |
| [istio-xds-serving-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--istio-xds-serving-qa-001.html) | `passed` | 1.000 | 0.000 | 59 | traj, tx |
| [kafka-contributor-workflow-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--kafka-contributor-workflow-001.html) | `passed` | 0.920 | 0.000 | 25 | traj, tx |
| [kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--kafka-message-lifecycle-qa-001.html) | `passed` | 1.000 | 0.000 | 50 | traj, tx |
| [numpy-dtype-localize-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--numpy-dtype-localize-001.html) | `passed` | 0.417 | 0.000 | 57 | traj, tx |
| [terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--terraform-plan-pipeline-qa-001.html) | `passed` | 0.950 | 0.000 | 41 | traj, tx |
| [terraform-state-backend-handoff-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--terraform-state-backend-handoff-001.html) | `passed` | 0.630 | 0.000 | 48 | traj, tx |
| [vscode-ext-host-qa-001](../tasks/understand_haiku_20260301_031852--baseline-local-direct--vscode-ext-host-qa-001.html) | `passed` | 1.000 | 0.000 | 24 | traj, tx |

## mcp-remote-direct

- Valid tasks: `20`
- Mean reward: `0.832`
- Pass rate: `0.950`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_django-template-inherit-recall-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_django-template-inherit-recall-001.html) | `failed` | 0.000 | - | - | traj, tx |
| [sgonly_argocd-arch-orient-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_argocd-arch-orient-001.html) | `passed` | 0.770 | 0.976 | 41 | traj, tx |
| [sgonly_argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_argocd-sync-reconcile-qa-001.html) | `passed` | 0.880 | 0.969 | 32 | traj, tx |
| [sgonly_cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_cilium-ebpf-datapath-handoff-001.html) | `passed` | 0.930 | 0.968 | 31 | traj, tx |
| [sgonly_cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_cilium-ebpf-fault-qa-001.html) | `passed` | 1.000 | 0.963 | 27 | traj, tx |
| [sgonly_cilium-project-orient-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_cilium-project-orient-001.html) | `passed` | 0.920 | 0.971 | 35 | traj, tx |
| [sgonly_django-composite-field-recover-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_django-composite-field-recover-001.html) | `passed` | 0.400 | 0.318 | 85 | traj, tx |
| [sgonly_envoy-contributor-workflow-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_envoy-contributor-workflow-001.html) | `passed` | 0.960 | 0.864 | 22 | traj, tx |
| [sgonly_envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.html) | `passed` | 0.830 | 0.958 | 24 | traj, tx |
| [sgonly_envoy-filter-chain-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_envoy-filter-chain-qa-001.html) | `passed` | 1.000 | 0.955 | 22 | traj, tx |
| [sgonly_envoy-request-routing-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_envoy-request-routing-qa-001.html) | `passed` | 0.910 | 0.957 | 23 | traj, tx |
| [sgonly_istio-xds-serving-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_istio-xds-serving-qa-001.html) | `passed` | 1.000 | 0.974 | 39 | traj, tx |
| [sgonly_k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_k8s-cri-containerd-reason-001.html) | `passed` | 0.850 | 0.826 | 23 | traj, tx |
| [sgonly_kafka-build-orient-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_kafka-build-orient-001.html) | `passed` | 0.910 | 0.964 | 28 | traj, tx |
| [sgonly_kafka-contributor-workflow-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_kafka-contributor-workflow-001.html) | `passed` | 0.820 | 0.957 | 23 | traj, tx |
| [sgonly_kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_kafka-message-lifecycle-qa-001.html) | `passed` | 0.910 | 0.971 | 34 | traj, tx |
| [sgonly_numpy-dtype-localize-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_numpy-dtype-localize-001.html) | `passed` | 1.000 | 0.912 | 34 | traj, tx |
| [sgonly_terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_terraform-plan-pipeline-qa-001.html) | `passed` | 0.950 | 0.952 | 21 | traj, tx |
| [sgonly_terraform-state-backend-handoff-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001.html) | `passed` | 0.710 | 0.941 | 34 | traj, tx |
| [sgonly_vscode-ext-host-qa-001](../tasks/understand_haiku_20260301_031852--mcp-remote-direct--sgonly_vscode-ext-host-qa-001.html) | `passed` | 0.890 | 0.955 | 22 | traj, tx |
