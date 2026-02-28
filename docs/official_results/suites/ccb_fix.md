# ccb_fix

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [ccb_fix_haiku_20260224_203138](../runs/ccb_fix_haiku_20260224_203138.md) | `mcp-remote-direct` | 1 | 0.740 | 1.000 |
| [ccb_fix_haiku_20260228_185835](../runs/ccb_fix_haiku_20260228_185835.md) | `baseline-local-direct` | 25 | 0.471 | 0.640 |
| [ccb_fix_haiku_20260228_185835](../runs/ccb_fix_haiku_20260228_185835.md) | `mcp-remote-direct` | 25 | 0.592 | 0.720 |
| [fix_haiku_20260223_171232](../runs/fix_haiku_20260223_171232.md) | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [fix_haiku_20260223_171232](../runs/fix_haiku_20260223_171232.md) | `mcp-remote-direct` | 18 | 0.508 | 0.611 |
| [fix_haiku_20260224_011821](../runs/fix_haiku_20260224_011821.md) | `baseline-local-direct` | 2 | 0.000 | 0.000 |
| [fix_haiku_20260224_011821](../runs/fix_haiku_20260224_011821.md) | `mcp-remote-direct` | 3 | 0.260 | 0.333 |
| [fix_haiku_20260226_024454](../runs/fix_haiku_20260226_024454.md) | `mcp-remote-direct` | 3 | 0.000 | 0.000 |
| [fix_haiku_20260226_new3tasks](../runs/fix_haiku_20260226_new3tasks.md) | `mcp-remote-direct` | 3 | 0.801 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [ansible-abc-imports-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--ansible-abc-imports-fix-001.html) | [source](../../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `baseline-local-direct` | `passed` | 0.943 | 3 | 0.000 |
| [mcp_ansible-abc-imports-fix-001_4HZCfw](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_ansible-abc-imports-fix-001_4HZCfw.html) | [source](../../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.289 |
| [sgonly_ansible-abc-imports-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_ansible-abc-imports-fix-001.html) | [source](../../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.299 |
| [ansible-module-respawn-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--ansible-module-respawn-fix-001.html) | [source](../../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `baseline-local-direct` | `passed` | 0.471 | 4 | 0.000 |
| [mcp_ansible-module-respawn-fix-001_Hgtxog](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_ansible-module-respawn-fix-001_Hgtxog.html) | [source](../../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 2 | 0.296 |
| [sgonly_ansible-module-respawn-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_ansible-module-respawn-fix-001.html) | [source](../../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 2 | 0.291 |
| [django-modelchoice-fk-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--django-modelchoice-fk-fix-001.html) | [source](../../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `baseline-local-direct` | `passed` | 0.450 | 3 | 0.000 |
| [mcp_django-modelchoice-fk-fix-001_rCYt5Z](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_django-modelchoice-fk-fix-001_rCYt5Z.html) | [source](../../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `mcp-remote-direct` | `passed` | 0.850 | 3 | 0.605 |
| [sgonly_django-modelchoice-fk-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_django-modelchoice-fk-fix-001.html) | [source](../../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `mcp-remote-direct` | `passed` | 0.450 | 3 | 0.655 |
| [django-select-for-update-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--django-select-for-update-fix-001.html) | [source](../../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `baseline-local-direct` | `passed` | 0.670 | 3 | 0.000 |
| [mcp_django-select-for-update-fix-001_H0nMDL](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_django-select-for-update-fix-001_H0nMDL.html) | [source](../../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `mcp-remote-direct` | `passed` | 0.820 | 3 | 0.789 |
| [sgonly_django-select-for-update-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_django-select-for-update-fix-001.html) | [source](../../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `mcp-remote-direct` | `passed` | 0.780 | 3 | 0.711 |
| [envoy-dfp-host-leak-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--envoy-dfp-host-leak-fix-001.html) | [source](../../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `baseline-local-direct` | `passed` | 0.791 | 2 | 0.000 |
| [mcp_envoy-dfp-host-leak-fix-001_FnvD2P](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_envoy-dfp-host-leak-fix-001_FnvD2P.html) | [source](../../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `mcp-remote-direct` | `passed` | 0.593 | 2 | 0.306 |
| [sgonly_envoy-dfp-host-leak-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-dfp-host-leak-fix-001.html) | [source](../../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `mcp-remote-direct` | `passed` | 0.665 | 2 | 0.345 |
| [envoy-udp-proxy-cds-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--envoy-udp-proxy-cds-fix-001.html) | [source](../../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `baseline-local-direct` | `passed` | 0.740 | 2 | 0.000 |
| [mcp_envoy-udp-proxy-cds-fix-001_KFbv1E](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_envoy-udp-proxy-cds-fix-001_KFbv1E.html) | [source](../../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `mcp-remote-direct` | `passed` | 0.669 | 2 | 0.279 |
| [sgonly_envoy-udp-proxy-cds-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_envoy-udp-proxy-cds-fix-001.html) | [source](../../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `mcp-remote-direct` | `passed` | 0.784 | 2 | 0.485 |
| [flipt-cockroachdb-backend-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--flipt-cockroachdb-backend-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `baseline-local-direct` | `passed` | 0.973 | 3 | 0.000 |
| [mcp_flipt-cockroachdb-backend-fix-001_O93D7t](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_flipt-cockroachdb-backend-fix-001_O93D7t.html) | [source](../../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `mcp-remote-direct` | `passed` | 0.973 | 3 | 0.205 |
| [sgonly_flipt-cockroachdb-backend-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-cockroachdb-backend-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `mcp-remote-direct` | `passed` | 0.973 | 3 | 0.508 |
| [flipt-ecr-auth-oci-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--flipt-ecr-auth-oci-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `baseline-local-direct` | `passed` | 0.987 | 3 | 0.000 |
| [mcp_flipt-ecr-auth-oci-fix-001_8o7G78](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_flipt-ecr-auth-oci-fix-001_8o7G78.html) | [source](../../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `mcp-remote-direct` | `passed` | 0.995 | 3 | 0.185 |
| [sgonly_flipt-ecr-auth-oci-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-ecr-auth-oci-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `mcp-remote-direct` | `passed` | 0.995 | 3 | 0.139 |
| [flipt-eval-latency-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--flipt-eval-latency-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `baseline-local-direct` | `passed` | 0.250 | 3 | 0.000 |
| [mcp_flipt-eval-latency-fix-001_gQ5wnj](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_flipt-eval-latency-fix-001_gQ5wnj.html) | [source](../../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `mcp-remote-direct` | `passed` | 0.550 | 3 | 0.140 |
| [sgonly_flipt-eval-latency-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-eval-latency-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.200 |
| [flipt-otlp-exporter-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--flipt-otlp-exporter-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `baseline-local-direct` | `passed` | 0.978 | 3 | 0.000 |
| [mcp_flipt-otlp-exporter-fix-001_aZH2yD](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_flipt-otlp-exporter-fix-001_aZH2yD.html) | [source](../../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `mcp-remote-direct` | `passed` | 0.979 | 3 | 0.355 |
| [sgonly_flipt-otlp-exporter-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-otlp-exporter-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `mcp-remote-direct` | `passed` | 0.979 | 3 | 0.221 |
| [flipt-trace-sampling-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--flipt-trace-sampling-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `baseline-local-direct` | `passed` | 0.984 | 3 | 0.000 |
| [mcp_flipt-trace-sampling-fix-001_HHLWjw](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_flipt-trace-sampling-fix-001_HHLWjw.html) | [source](../../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `mcp-remote-direct` | `passed` | 0.985 | 3 | 0.353 |
| [sgonly_flipt-trace-sampling-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_flipt-trace-sampling-fix-001.html) | [source](../../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `mcp-remote-direct` | `passed` | 0.985 | 3 | 0.119 |
| [k8s-dra-scheduler-event-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--k8s-dra-scheduler-event-fix-001.html) | [source](../../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `baseline-local-direct` | `passed` | 0.730 | 3 | 0.000 |
| [mcp_k8s-dra-scheduler-event-fix-001_VRGt4l](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_k8s-dra-scheduler-event-fix-001_VRGt4l.html) | [source](../../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `mcp-remote-direct` | `passed` | 0.810 | 3 | 0.885 |
| [sgonly_k8s-dra-scheduler-event-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_k8s-dra-scheduler-event-fix-001.html) | [source](../../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `mcp-remote-direct` | `passed` | 0.750 | 3 | 0.810 |
| [kafka-producer-bufpool-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--kafka-producer-bufpool-fix-001.html) | [source](../../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `baseline-local-direct` | `passed` | 0.650 | 3 | 0.000 |
| [mcp_kafka-producer-bufpool-fix-001_B3DWiu](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_kafka-producer-bufpool-fix-001_B3DWiu.html) | [source](../../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | `passed` | 0.690 | 4 | 0.780 |
| [mcp_kafka-producer-bufpool-fix-001_2pvDVv](../tasks/ccb_fix_haiku_20260224_203138--mcp-remote-direct--mcp_kafka-producer-bufpool-fix-001_2pvDVv.html) | [source](../../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | `passed` | 0.740 | 4 | 0.955 |
| [sgonly_kafka-producer-bufpool-fix-001](../tasks/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_kafka-producer-bufpool-fix-001.html) | [source](../../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | `passed` | 0.780 | 4 | 0.900 |
| [navidrome-windows-log-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--navidrome-windows-log-fix-001.html) | [source](../../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_navidrome-windows-log-fix-001_QfarEE](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_navidrome-windows-log-fix-001_QfarEE.html) | [source](../../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.310 |
| [sgonly_navidrome-windows-log-fix-001](../tasks/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_navidrome-windows-log-fix-001.html) | [source](../../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.286 |
| [nodebb-notif-dropdown-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--nodebb-notif-dropdown-fix-001.html) | [source](../../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_nodebb-notif-dropdown-fix-001_fbthJ3](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_nodebb-notif-dropdown-fix-001_fbthJ3.html) | [source](../../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.274 |
| [sgonly_nodebb-notif-dropdown-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_nodebb-notif-dropdown-fix-001.html) | [source](../../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.446 |
| [nodebb-plugin-validate-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--nodebb-plugin-validate-fix-001.html) | [source](../../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_nodebb-plugin-validate-fix-001_r0VSJI](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_nodebb-plugin-validate-fix-001_r0VSJI.html) | [source](../../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.100 |
| [sgonly_nodebb-plugin-validate-fix-001](../tasks/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_nodebb-plugin-validate-fix-001.html) | [source](../../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.125 |
| [openlibrary-fntocli-adapter-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--openlibrary-fntocli-adapter-fix-001.html) | [source](../../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `baseline-local-direct` | `passed` | 0.667 | 3 | 0.000 |
| [mcp_openlibrary-fntocli-adapter-fix-001_IMvWES](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_openlibrary-fntocli-adapter-fix-001_IMvWES.html) | [source](../../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.193 |
| [sgonly_openlibrary-fntocli-adapter-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-fntocli-adapter-fix-001.html) | [source](../../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `mcp-remote-direct` | `passed` | 1.000 | 3 | 0.108 |
| [openlibrary-search-query-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--openlibrary-search-query-fix-001.html) | [source](../../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_openlibrary-search-query-fix-001_wxswww](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_openlibrary-search-query-fix-001_wxswww.html) | [source](../../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.203 |
| [sgonly_openlibrary-search-query-fix-001](../tasks/fix_haiku_20260226_024454--mcp-remote-direct--sgonly_openlibrary-search-query-fix-001.html) | [source](../../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.175 |
| [openlibrary-solr-boolean-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--openlibrary-solr-boolean-fix-001.html) | [source](../../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 4 | 0.000 |
| [mcp_openlibrary-solr-boolean-fix-001_TeGlod](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_openlibrary-solr-boolean-fix-001_TeGlod.html) | [source](../../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `mcp-remote-direct` | `passed` | 0.667 | 4 | - |
| [sgonly_openlibrary-solr-boolean-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_openlibrary-solr-boolean-fix-001.html) | [source](../../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `mcp-remote-direct` | `passed` | 0.667 | 4 | - |
| [protonmail-conv-testhooks-fix-001](../tasks/fix_haiku_20260223_171232--baseline-local-direct--protonmail-conv-testhooks-fix-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 1 | - |
| [protonmail-dropdown-sizing-fix-001](../tasks/fix_haiku_20260224_011821--baseline-local-direct--protonmail-dropdown-sizing-fix-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | - |
| [sgonly_protonmail-dropdown-sizing-fix-001](../tasks/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_protonmail-dropdown-sizing-fix-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [protonmail-holiday-calendar-fix-001](../tasks/fix_haiku_20260224_011821--baseline-local-direct--protonmail-holiday-calendar-fix-001.html) | — | `baseline-local-direct` | `failed` | 0.000 | 2 | - |
| [sgonly_protonmail-holiday-calendar-fix-001](../tasks/fix_haiku_20260224_011821--mcp-remote-direct--sgonly_protonmail-holiday-calendar-fix-001.html) | — | `mcp-remote-direct` | `failed` | 0.000 | 1 | - |
| [pytorch-cudnn-version-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--pytorch-cudnn-version-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_pytorch-cudnn-version-fix-001_5MmKdu](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_pytorch-cudnn-version-fix-001_5MmKdu.html) | [source](../../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.590 |
| [sgonly_pytorch-cudnn-version-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-cudnn-version-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.586 |
| [pytorch-dynamo-keyerror-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--pytorch-dynamo-keyerror-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_pytorch-dynamo-keyerror-fix-001_ufG1h3](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_pytorch-dynamo-keyerror-fix-001_ufG1h3.html) | [source](../../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.507 |
| [sgonly_pytorch-dynamo-keyerror-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-dynamo-keyerror-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.625 |
| [pytorch-release-210-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--pytorch-release-210-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_pytorch-release-210-fix-001_VZFTMM](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_pytorch-release-210-fix-001_VZFTMM.html) | [source](../../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `mcp-remote-direct` | `passed` | 0.787 | 3 | 0.208 |
| [sgonly_pytorch-release-210-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-release-210-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.241 |
| [pytorch-relu-gelu-fusion-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--pytorch-relu-gelu-fusion-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `baseline-local-direct` | `passed` | 0.654 | 3 | 0.000 |
| [mcp_pytorch-relu-gelu-fusion-fix-001_FMIUaS](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_pytorch-relu-gelu-fusion-fix-001_FMIUaS.html) | [source](../../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `mcp-remote-direct` | `passed` | 0.656 | 3 | 0.448 |
| [sgonly_pytorch-relu-gelu-fusion-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-relu-gelu-fusion-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `mcp-remote-direct` | `passed` | 0.561 | 3 | 0.370 |
| [pytorch-tracer-graph-cleanup-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--pytorch-tracer-graph-cleanup-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `baseline-local-direct` | `failed` | 0.000 | 3 | 0.000 |
| [mcp_pytorch-tracer-graph-cleanup-fix-001_o7Q3V3](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_pytorch-tracer-graph-cleanup-fix-001_o7Q3V3.html) | [source](../../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.485 |
| [sgonly_pytorch-tracer-graph-cleanup-fix-001](../tasks/fix_haiku_20260223_171232--mcp-remote-direct--sgonly_pytorch-tracer-graph-cleanup-fix-001.html) | [source](../../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `mcp-remote-direct` | `failed` | 0.000 | 3 | 0.217 |
| [terraform-plan-null-unknown-fix-001](../tasks/ccb_fix_haiku_20260228_185835--baseline-local-direct--terraform-plan-null-unknown-fix-001.html) | [source](../../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `baseline-local-direct` | `passed` | 0.841 | 2 | 0.000 |
| [mcp_terraform-plan-null-unknown-fix-001_A0MbH8](../tasks/ccb_fix_haiku_20260228_185835--mcp-remote-direct--mcp_terraform-plan-null-unknown-fix-001_A0MbH8.html) | [source](../../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `mcp-remote-direct` | `passed` | 0.775 | 2 | 0.434 |
| [sgonly_terraform-plan-null-unknown-fix-001](../tasks/fix_haiku_20260226_new3tasks--mcp-remote-direct--sgonly_terraform-plan-null-unknown-fix-001.html) | [source](../../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `mcp-remote-direct` | `passed` | 0.955 | 2 | 0.193 |

## Multi-Run Variance

Tasks with multiple valid runs (50 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| ansible-abc-imports-fix-001 | [source](../../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `baseline-local-direct` | 2 | 0.943 | 0.000 | 0.943, 0.943 |
| ansible-abc-imports-fix-001 | [source](../../../benchmarks/ccb_fix/ansible-abc-imports-fix-001) | `mcp-remote-direct` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| ansible-module-respawn-fix-001 | [source](../../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `baseline-local-direct` | 3 | 0.471 | 0.000 | 0.471, 0.471, 0.471 |
| ansible-module-respawn-fix-001 | [source](../../../benchmarks/ccb_fix/ansible-module-respawn-fix-001) | `mcp-remote-direct` | 2 | 0.500 | 0.707 | 0.000, 1.000 |
| django-modelchoice-fk-fix-001 | [source](../../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `baseline-local-direct` | 2 | 0.450 | 0.000 | 0.450, 0.450 |
| django-modelchoice-fk-fix-001 | [source](../../../benchmarks/ccb_fix/django-modelchoice-fk-fix-001) | `mcp-remote-direct` | 2 | 0.650 | 0.283 | 0.450, 0.850 |
| django-select-for-update-fix-001 | [source](../../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `baseline-local-direct` | 2 | 0.670 | 0.000 | 0.670, 0.670 |
| django-select-for-update-fix-001 | [source](../../../benchmarks/ccb_fix/django-select-for-update-fix-001) | `mcp-remote-direct` | 2 | 0.800 | 0.028 | 0.780, 0.820 |
| envoy-dfp-host-leak-fix-001 | [source](../../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `baseline-local-direct` | 2 | 0.759 | 0.045 | 0.727, 0.791 |
| envoy-dfp-host-leak-fix-001 | [source](../../../benchmarks/ccb_fix/envoy-dfp-host-leak-fix-001) | `mcp-remote-direct` | 2 | 0.629 | 0.051 | 0.665, 0.593 |
| envoy-udp-proxy-cds-fix-001 | [source](../../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `baseline-local-direct` | 2 | 0.748 | 0.011 | 0.755, 0.740 |
| envoy-udp-proxy-cds-fix-001 | [source](../../../benchmarks/ccb_fix/envoy-udp-proxy-cds-fix-001) | `mcp-remote-direct` | 2 | 0.726 | 0.082 | 0.784, 0.669 |
| flipt-cockroachdb-backend-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `baseline-local-direct` | 2 | 0.973 | 0.000 | 0.973, 0.973 |
| flipt-cockroachdb-backend-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-cockroachdb-backend-fix-001) | `mcp-remote-direct` | 2 | 0.973 | 0.000 | 0.973, 0.973 |
| flipt-ecr-auth-oci-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `baseline-local-direct` | 2 | 0.987 | 0.000 | 0.987, 0.987 |
| flipt-ecr-auth-oci-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-ecr-auth-oci-fix-001) | `mcp-remote-direct` | 2 | 0.995 | 0.000 | 0.995, 0.995 |
| flipt-eval-latency-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `baseline-local-direct` | 2 | 0.400 | 0.212 | 0.550, 0.250 |
| flipt-eval-latency-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-eval-latency-fix-001) | `mcp-remote-direct` | 2 | 0.275 | 0.389 | 0.000, 0.550 |
| flipt-otlp-exporter-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `baseline-local-direct` | 2 | 0.978 | 0.000 | 0.978, 0.978 |
| flipt-otlp-exporter-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-otlp-exporter-fix-001) | `mcp-remote-direct` | 2 | 0.979 | 0.000 | 0.979, 0.979 |
| flipt-trace-sampling-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `baseline-local-direct` | 2 | 0.986 | 0.002 | 0.987, 0.984 |
| flipt-trace-sampling-fix-001 | [source](../../../benchmarks/ccb_fix/flipt-trace-sampling-fix-001) | `mcp-remote-direct` | 2 | 0.985 | 0.000 | 0.985, 0.985 |
| k8s-dra-scheduler-event-fix-001 | [source](../../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `baseline-local-direct` | 2 | 0.705 | 0.035 | 0.680, 0.730 |
| k8s-dra-scheduler-event-fix-001 | [source](../../../benchmarks/ccb_fix/k8s-dra-scheduler-event-fix-001) | `mcp-remote-direct` | 2 | 0.780 | 0.042 | 0.750, 0.810 |
| kafka-producer-bufpool-fix-001 | [source](../../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `baseline-local-direct` | 2 | 0.680 | 0.042 | 0.710, 0.650 |
| kafka-producer-bufpool-fix-001 | [source](../../../benchmarks/ccb_fix/kafka-producer-bufpool-fix-001) | `mcp-remote-direct` | 4 | 0.748 | 0.043 | 0.780, 0.780, 0.740, 0.690 |
| navidrome-windows-log-fix-001 | [source](../../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `baseline-local-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| navidrome-windows-log-fix-001 | [source](../../../benchmarks/ccb_fix/navidrome-windows-log-fix-001) | `mcp-remote-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| nodebb-notif-dropdown-fix-001 | [source](../../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| nodebb-notif-dropdown-fix-001 | [source](../../../benchmarks/ccb_fix/nodebb-notif-dropdown-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| nodebb-plugin-validate-fix-001 | [source](../../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `baseline-local-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| nodebb-plugin-validate-fix-001 | [source](../../../benchmarks/ccb_fix/nodebb-plugin-validate-fix-001) | `mcp-remote-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| openlibrary-fntocli-adapter-fix-001 | [source](../../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `baseline-local-direct` | 2 | 0.667 | 0.000 | 0.667, 0.667 |
| openlibrary-fntocli-adapter-fix-001 | [source](../../../benchmarks/ccb_fix/openlibrary-fntocli-adapter-fix-001) | `mcp-remote-direct` | 2 | 1.000 | 0.000 | 1.000, 1.000 |
| openlibrary-search-query-fix-001 | [source](../../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `baseline-local-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| openlibrary-search-query-fix-001 | [source](../../../benchmarks/ccb_fix/openlibrary-search-query-fix-001) | `mcp-remote-direct` | 3 | 0.000 | 0.000 | 0.000, 0.000, 0.000 |
| openlibrary-solr-boolean-fix-001 | [source](../../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `baseline-local-direct` | 4 | 0.000 | 0.000 | 0.000, 0.000, 0.000, 0.000 |
| openlibrary-solr-boolean-fix-001 | [source](../../../benchmarks/ccb_fix/openlibrary-solr-boolean-fix-001) | `mcp-remote-direct` | 3 | 0.667 | 0.000 | 0.667, 0.667, 0.667 |
| pytorch-cudnn-version-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| pytorch-cudnn-version-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-cudnn-version-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| pytorch-dynamo-keyerror-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| pytorch-dynamo-keyerror-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-dynamo-keyerror-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| pytorch-release-210-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| pytorch-release-210-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-release-210-fix-001) | `mcp-remote-direct` | 2 | 0.393 | 0.556 | 0.000, 0.787 |
| pytorch-relu-gelu-fusion-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `baseline-local-direct` | 2 | 0.697 | 0.060 | 0.739, 0.654 |
| pytorch-relu-gelu-fusion-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-relu-gelu-fusion-fix-001) | `mcp-remote-direct` | 2 | 0.608 | 0.067 | 0.561, 0.656 |
| pytorch-tracer-graph-cleanup-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `baseline-local-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| pytorch-tracer-graph-cleanup-fix-001 | [source](../../../benchmarks/ccb_fix/pytorch-tracer-graph-cleanup-fix-001) | `mcp-remote-direct` | 2 | 0.000 | 0.000 | 0.000, 0.000 |
| terraform-plan-null-unknown-fix-001 | [source](../../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `baseline-local-direct` | 2 | 0.770 | 0.100 | 0.699, 0.841 |
| terraform-plan-null-unknown-fix-001 | [source](../../../benchmarks/ccb_fix/terraform-plan-null-unknown-fix-001) | `mcp-remote-direct` | 2 | 0.865 | 0.127 | 0.955, 0.775 |
