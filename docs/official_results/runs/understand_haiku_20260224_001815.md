# understand_haiku_20260224_001815

## baseline-local-direct

- Valid tasks: `20`
- Mean reward: `0.533`
- Pass rate: `0.650`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [argocd-arch-orient-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--argocd-arch-orient-001.md) | `failed` | 0.000 | 0.000 | 187 | traj, tx |
| [cilium-project-orient-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--cilium-project-orient-001.md) | `failed` | 0.000 | 0.000 | 59 | traj, tx |
| [envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-ext-authz-handoff-001.md) | `failed` | 0.000 | - | - | traj, tx |
| [envoy-request-routing-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-request-routing-qa-001.md) | `failed` | 0.000 | 0.000 | 57 | traj, tx |
| [numpy-dtype-localize-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--numpy-dtype-localize-001.md) | `failed` | 0.000 | - | - | traj, tx |
| [terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--terraform-plan-pipeline-qa-001.md) | `failed` | 0.000 | 0.000 | 5 | traj, tx |
| [terraform-state-backend-handoff-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--terraform-state-backend-handoff-001.md) | `failed` | 0.000 | - | - | traj, tx |
| [argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--argocd-sync-reconcile-qa-001.md) | `passed` | 0.920 | 0.000 | 203 | traj, tx |
| [cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--cilium-ebpf-datapath-handoff-001.md) | `passed` | 1.000 | 0.000 | 150 | traj, tx |
| [cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--cilium-ebpf-fault-qa-001.md) | `passed` | 0.770 | 0.000 | 58 | traj, tx |
| [django-composite-field-recover-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--django-composite-field-recover-001.md) | `passed` | 0.400 | 0.000 | 68 | traj, tx |
| [django-template-inherit-recall-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--django-template-inherit-recall-001.md) | `passed` | 0.250 | 0.000 | 94 | traj, tx |
| [envoy-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-contributor-workflow-001.md) | `passed` | 0.970 | 0.000 | 45 | traj, tx |
| [envoy-filter-chain-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--envoy-filter-chain-qa-001.md) | `passed` | 0.970 | 0.000 | 45 | traj, tx |
| [istio-xds-serving-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--istio-xds-serving-qa-001.md) | `passed` | 1.000 | 0.000 | 88 | traj, tx |
| [k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--k8s-cri-containerd-reason-001.md) | `passed` | 0.850 | 0.000 | 90 | traj, tx |
| [kafka-build-orient-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--kafka-build-orient-001.md) | `passed` | 0.720 | 0.000 | 224 | traj, tx |
| [kafka-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--kafka-contributor-workflow-001.md) | `passed` | 0.950 | 0.000 | 23 | traj, tx |
| [kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--kafka-message-lifecycle-qa-001.md) | `passed` | 0.860 | 0.000 | 78 | traj, tx |
| [vscode-ext-host-qa-001](../tasks/understand_haiku_20260224_001815--baseline-local-direct--vscode-ext-host-qa-001.md) | `passed` | 1.000 | 0.000 | 38 | traj, tx |

## mcp-remote-direct

- Valid tasks: `20`
- Mean reward: `0.679`
- Pass rate: `0.850`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_k8s-cri-containerd-reason-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_k8s-cri-containerd-reason-001.md) | `failed` | 0.000 | - | - | traj, tx |
| [sgonly_kafka-build-orient-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_kafka-build-orient-001.md) | `failed` | 0.000 | - | - | traj, tx |
| [sgonly_vscode-ext-host-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_vscode-ext-host-qa-001.md) | `failed` | 0.000 | - | - | traj, tx |
| [sgonly_argocd-arch-orient-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_argocd-arch-orient-001.md) | `passed` | 0.810 | 0.977 | 44 | traj, tx |
| [sgonly_argocd-sync-reconcile-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_argocd-sync-reconcile-qa-001.md) | `passed` | 0.830 | 0.970 | 33 | traj, tx |
| [sgonly_cilium-ebpf-datapath-handoff-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_cilium-ebpf-datapath-handoff-001.md) | `passed` | 0.830 | 0.968 | 31 | traj, tx |
| [sgonly_cilium-ebpf-fault-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_cilium-ebpf-fault-qa-001.md) | `passed` | 0.820 | 0.973 | 37 | traj, tx |
| [sgonly_cilium-project-orient-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_cilium-project-orient-001.md) | `passed` | 0.960 | 0.974 | 39 | traj, tx |
| [sgonly_django-composite-field-recover-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_django-composite-field-recover-001.md) | `passed` | 0.250 | - | - | traj, tx |
| [sgonly_django-template-inherit-recall-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_django-template-inherit-recall-001.md) | `passed` | 0.250 | 0.143 | 98 | traj, tx |
| [sgonly_envoy-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-contributor-workflow-001.md) | `passed` | 0.910 | 0.955 | 22 | traj, tx |
| [sgonly_envoy-ext-authz-handoff-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-ext-authz-handoff-001.md) | `passed` | 0.830 | 0.955 | 22 | traj, tx |
| [sgonly_envoy-filter-chain-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-filter-chain-qa-001.md) | `passed` | 0.880 | 0.967 | 30 | traj, tx |
| [sgonly_envoy-request-routing-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_envoy-request-routing-qa-001.md) | `passed` | 0.870 | 0.971 | 35 | traj, tx |
| [sgonly_istio-xds-serving-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_istio-xds-serving-qa-001.md) | `passed` | 1.000 | 0.971 | 34 | traj, tx |
| [sgonly_kafka-contributor-workflow-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_kafka-contributor-workflow-001.md) | `passed` | 0.820 | 0.955 | 22 | traj, tx |
| [sgonly_kafka-message-lifecycle-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_kafka-message-lifecycle-qa-001.md) | `passed` | 1.000 | 0.972 | 36 | traj, tx |
| [sgonly_numpy-dtype-localize-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_numpy-dtype-localize-001.md) | `passed` | 0.933 | 0.966 | 29 | traj, tx |
| [sgonly_terraform-plan-pipeline-qa-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_terraform-plan-pipeline-qa-001.md) | `passed` | 0.950 | 0.971 | 35 | traj, tx |
| [sgonly_terraform-state-backend-handoff-001](../tasks/understand_haiku_20260224_001815--mcp-remote-direct--sgonly_terraform-state-backend-handoff-001.md) | `passed` | 0.630 | 0.964 | 28 | traj, tx |
