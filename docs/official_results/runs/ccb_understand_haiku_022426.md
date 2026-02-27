# ccb_understand_haiku_022426

## baseline

- Valid tasks: `13`
- Mean reward: `0.592`
- Pass rate: `0.692`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [argocd-arch-orient-001](../tasks/ccb_understand_haiku_022426--baseline--argocd-arch-orient-001.md) | `failed` | 0.000 | 0.000 | 187 | traj, tx |
| [cilium-project-orient-001](../tasks/ccb_understand_haiku_022426--baseline--cilium-project-orient-001.md) | `failed` | 0.000 | 0.000 | 59 | traj, tx |
| [envoy-request-routing-qa-001](../tasks/ccb_understand_haiku_022426--baseline--envoy-request-routing-qa-001.md) | `failed` | 0.000 | 0.000 | 57 | traj, tx |
| [terraform-plan-pipeline-qa-001](../tasks/ccb_understand_haiku_022426--baseline--terraform-plan-pipeline-qa-001.md) | `failed` | 0.000 | 0.000 | 5 | traj, tx |
| [argocd-sync-reconcile-qa-001](../tasks/ccb_understand_haiku_022426--baseline--argocd-sync-reconcile-qa-001.md) | `passed` | 0.920 | 0.000 | 203 | traj, tx |
| [cilium-ebpf-datapath-handoff-001](../tasks/ccb_understand_haiku_022426--baseline--cilium-ebpf-datapath-handoff-001.md) | `passed` | 1.000 | 0.000 | 150 | traj, tx |
| [cilium-ebpf-fault-qa-001](../tasks/ccb_understand_haiku_022426--baseline--cilium-ebpf-fault-qa-001.md) | `passed` | 0.770 | 0.000 | 58 | traj, tx |
| [django-template-inherit-recall-001](../tasks/ccb_understand_haiku_022426--baseline--django-template-inherit-recall-001.md) | `passed` | 0.250 | 0.000 | 94 | traj, tx |
| [envoy-contributor-workflow-001](../tasks/ccb_understand_haiku_022426--baseline--envoy-contributor-workflow-001.md) | `passed` | 0.970 | 0.000 | 45 | traj, tx |
| [envoy-filter-chain-qa-001](../tasks/ccb_understand_haiku_022426--baseline--envoy-filter-chain-qa-001.md) | `passed` | 0.970 | 0.000 | 45 | traj, tx |
| [istio-xds-serving-qa-001](../tasks/ccb_understand_haiku_022426--baseline--istio-xds-serving-qa-001.md) | `passed` | 1.000 | 0.000 | 88 | traj, tx |
| [kafka-contributor-workflow-001](../tasks/ccb_understand_haiku_022426--baseline--kafka-contributor-workflow-001.md) | `passed` | 0.950 | 0.000 | 23 | traj, tx |
| [kafka-message-lifecycle-qa-001](../tasks/ccb_understand_haiku_022426--baseline--kafka-message-lifecycle-qa-001.md) | `passed` | 0.860 | 0.000 | 78 | traj, tx |

## mcp

- Valid tasks: `13`
- Mean reward: `0.841`
- Pass rate: `1.000`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_argocd-arch-orient-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_argocd-arch-orient-001.md) | `passed` | 0.810 | 0.977 | 44 | traj, tx |
| [sgonly_argocd-sync-reconcile-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_argocd-sync-reconcile-qa-001.md) | `passed` | 0.830 | 0.970 | 33 | traj, tx |
| [sgonly_cilium-ebpf-datapath-handoff-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_cilium-ebpf-datapath-handoff-001.md) | `passed` | 0.830 | 0.968 | 31 | traj, tx |
| [sgonly_cilium-ebpf-fault-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_cilium-ebpf-fault-qa-001.md) | `passed` | 0.820 | 0.973 | 37 | traj, tx |
| [sgonly_cilium-project-orient-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_cilium-project-orient-001.md) | `passed` | 0.960 | 0.974 | 39 | traj, tx |
| [sgonly_django-template-inherit-recall-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_django-template-inherit-recall-001.md) | `passed` | 0.250 | 0.143 | 98 | traj, tx |
| [sgonly_envoy-contributor-workflow-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_envoy-contributor-workflow-001.md) | `passed` | 0.910 | 0.955 | 22 | traj, tx |
| [sgonly_envoy-filter-chain-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_envoy-filter-chain-qa-001.md) | `passed` | 0.880 | 0.967 | 30 | traj, tx |
| [sgonly_envoy-request-routing-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_envoy-request-routing-qa-001.md) | `passed` | 0.870 | 0.971 | 35 | traj, tx |
| [sgonly_istio-xds-serving-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_istio-xds-serving-qa-001.md) | `passed` | 1.000 | 0.971 | 34 | traj, tx |
| [sgonly_kafka-contributor-workflow-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_kafka-contributor-workflow-001.md) | `passed` | 0.820 | 0.955 | 22 | traj, tx |
| [sgonly_kafka-message-lifecycle-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_kafka-message-lifecycle-qa-001.md) | `passed` | 1.000 | 0.972 | 36 | traj, tx |
| [sgonly_terraform-plan-pipeline-qa-001](../tasks/ccb_understand_haiku_022426--mcp--sgonly_terraform-plan-pipeline-qa-001.md) | `passed` | 0.950 | 0.971 | 35 | traj, tx |
