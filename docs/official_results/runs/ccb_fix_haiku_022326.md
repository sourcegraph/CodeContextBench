# ccb_fix_haiku_022326

## baseline-local-direct

- Valid tasks: `17`
- Mean reward: `0.535`
- Pass rate: `0.706`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [nodebb-notif-dropdown-fix-001](../tasks/ccb_fix_haiku_022326--baseline--nodebb-notif-dropdown-fix-001.html) | `failed` | 0.000 | 0.000 | 155 | traj, tx |
| [pytorch-cudnn-version-fix-001](../tasks/ccb_fix_haiku_022326--baseline--pytorch-cudnn-version-fix-001.html) | `failed` | 0.000 | 0.000 | 104 | traj, tx |
| [pytorch-dynamo-keyerror-fix-001](../tasks/ccb_fix_haiku_022326--baseline--pytorch-dynamo-keyerror-fix-001.html) | `failed` | 0.000 | 0.000 | 53 | traj, tx |
| [pytorch-release-210-fix-001](../tasks/ccb_fix_haiku_022326--baseline--pytorch-release-210-fix-001.html) | `failed` | 0.000 | 0.000 | 89 | traj, tx |
| [pytorch-tracer-graph-cleanup-fix-001](../tasks/ccb_fix_haiku_022326--baseline--pytorch-tracer-graph-cleanup-fix-001.html) | `failed` | 0.000 | 0.000 | 95 | traj, tx |
| [ansible-abc-imports-fix-001](../tasks/ccb_fix_haiku_022326--baseline--ansible-abc-imports-fix-001.html) | `passed` | 0.943 | 0.000 | 96 | traj, tx |
| [ansible-module-respawn-fix-001](../tasks/ccb_fix_haiku_022326--baseline--ansible-module-respawn-fix-001.html) | `passed` | 0.471 | 0.000 | 171 | traj, tx |
| [django-modelchoice-fk-fix-001](../tasks/ccb_fix_haiku_022326--baseline--django-modelchoice-fk-fix-001.html) | `passed` | 0.450 | 0.000 | 93 | traj, tx |
| [django-select-for-update-fix-001](../tasks/ccb_fix_haiku_022326--baseline--django-select-for-update-fix-001.html) | `passed` | 0.670 | 0.000 | 53 | traj, tx |
| [flipt-cockroachdb-backend-fix-001](../tasks/ccb_fix_haiku_022326--baseline--flipt-cockroachdb-backend-fix-001.html) | `passed` | 0.973 | 0.000 | 79 | traj, tx |
| [flipt-ecr-auth-oci-fix-001](../tasks/ccb_fix_haiku_022326--baseline--flipt-ecr-auth-oci-fix-001.html) | `passed` | 0.987 | 0.000 | 95 | traj, tx |
| [flipt-eval-latency-fix-001](../tasks/ccb_fix_haiku_022326--baseline--flipt-eval-latency-fix-001.html) | `passed` | 0.550 | 0.000 | 27 | traj, tx |
| [flipt-otlp-exporter-fix-001](../tasks/ccb_fix_haiku_022326--baseline--flipt-otlp-exporter-fix-001.html) | `passed` | 0.978 | 0.000 | 104 | traj, tx |
| [flipt-trace-sampling-fix-001](../tasks/ccb_fix_haiku_022326--baseline--flipt-trace-sampling-fix-001.html) | `passed` | 0.987 | 0.000 | 102 | traj, tx |
| [k8s-dra-scheduler-event-fix-001](../tasks/ccb_fix_haiku_022326--baseline--k8s-dra-scheduler-event-fix-001.html) | `passed` | 0.680 | 0.000 | 28 | traj, tx |
| [openlibrary-fntocli-adapter-fix-001](../tasks/ccb_fix_haiku_022326--baseline--openlibrary-fntocli-adapter-fix-001.html) | `passed` | 0.667 | 0.000 | 36 | traj, tx |
| [pytorch-relu-gelu-fusion-fix-001](../tasks/ccb_fix_haiku_022326--baseline--pytorch-relu-gelu-fusion-fix-001.html) | `passed` | 0.739 | 0.000 | 50 | traj, tx |

## mcp-remote-direct

- Valid tasks: `17`
- Mean reward: `0.538`
- Pass rate: `0.647`

| Task | Status | Reward | MCP Ratio | Tool Calls | Trace |
|---|---|---:|---:|---:|---|
| [sgonly_flipt-eval-latency-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_flipt-eval-latency-fix-001.html) | `failed` | 0.000 | 0.200 | 65 | traj, tx |
| [sgonly_nodebb-notif-dropdown-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_nodebb-notif-dropdown-fix-001.html) | `failed` | 0.000 | 0.446 | 83 | traj, tx |
| [sgonly_pytorch-cudnn-version-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_pytorch-cudnn-version-fix-001.html) | `failed` | 0.000 | 0.586 | 29 | traj, tx |
| [sgonly_pytorch-dynamo-keyerror-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_pytorch-dynamo-keyerror-fix-001.html) | `failed` | 0.000 | 0.625 | 56 | traj, tx |
| [sgonly_pytorch-release-210-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_pytorch-release-210-fix-001.html) | `failed` | 0.000 | 0.241 | 87 | traj, tx |
| [sgonly_pytorch-tracer-graph-cleanup-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_pytorch-tracer-graph-cleanup-fix-001.html) | `failed` | 0.000 | 0.217 | 120 | traj, tx |
| [sgonly_ansible-abc-imports-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_ansible-abc-imports-fix-001.html) | `passed` | 1.000 | 0.299 | 77 | traj, tx |
| [sgonly_django-modelchoice-fk-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_django-modelchoice-fk-fix-001.html) | `passed` | 0.450 | 0.655 | 58 | traj, tx |
| [sgonly_django-select-for-update-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_django-select-for-update-fix-001.html) | `passed` | 0.780 | 0.711 | 38 | traj, tx |
| [sgonly_flipt-cockroachdb-backend-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_flipt-cockroachdb-backend-fix-001.html) | `passed` | 0.973 | 0.508 | 65 | traj, tx |
| [sgonly_flipt-ecr-auth-oci-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_flipt-ecr-auth-oci-fix-001.html) | `passed` | 0.995 | 0.139 | 79 | traj, tx |
| [sgonly_flipt-otlp-exporter-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_flipt-otlp-exporter-fix-001.html) | `passed` | 0.979 | 0.221 | 77 | traj, tx |
| [sgonly_flipt-trace-sampling-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_flipt-trace-sampling-fix-001.html) | `passed` | 0.985 | 0.119 | 135 | traj, tx |
| [sgonly_k8s-dra-scheduler-event-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_k8s-dra-scheduler-event-fix-001.html) | `passed` | 0.750 | 0.810 | 21 | traj, tx |
| [sgonly_openlibrary-fntocli-adapter-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_openlibrary-fntocli-adapter-fix-001.html) | `passed` | 1.000 | 0.108 | 37 | traj, tx |
| [sgonly_openlibrary-solr-boolean-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_openlibrary-solr-boolean-fix-001.html) | `passed` | 0.667 | - | - | tx |
| [sgonly_pytorch-relu-gelu-fusion-fix-001](../tasks/ccb_fix_haiku_022326--mcp--sgonly_pytorch-relu-gelu-fusion-fix-001.html) | `passed` | 0.561 | 0.370 | 46 | traj, tx |
