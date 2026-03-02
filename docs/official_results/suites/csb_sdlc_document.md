# csb_sdlc_document

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [csb_sdlc_document_haiku_20260224_174311](../runs/csb_sdlc_document_haiku_20260224_174311.md) | `mcp-remote-direct` | 5 | 0.720 | 1.000 |
| [csb_sdlc_document_haiku_20260228_025547](../runs/csb_sdlc_document_haiku_20260228_025547.md) | `mcp-remote-direct` | 18 | 0.887 | 1.000 |
| [csb_sdlc_document_haiku_20260228_124521](../runs/csb_sdlc_document_haiku_20260228_124521.md) | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_document_haiku_20260302_221730](../runs/csb_sdlc_document_haiku_20260302_221730.md) | `baseline-local-direct` | 13 | 0.483 | 0.692 |
| [csb_sdlc_document_haiku_20260302_221730](../runs/csb_sdlc_document_haiku_20260302_221730.md) | `mcp-remote-direct` | 13 | 0.585 | 0.692 |
| [document_haiku_20260301_071228](../runs/document_haiku_20260301_071228.md) | `baseline-local-direct` | 7 | 0.997 | 1.000 |
| [document_haiku_20260301_071228](../runs/document_haiku_20260301_071228.md) | `mcp-remote-direct` | 20 | 0.898 | 1.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Runs | MCP Ratio |
|---|---|---|---|---:|---:|---:|
| [cilium-api-doc-gen-001](../tasks/document_haiku_20260301_071228--baseline-local-direct--cilium-api-doc-gen-001.html) | — | `baseline-local-direct` | `passed` | 0.980 | 5 | 0.000 |
| [mcp_cilium-api-doc-gen-001_091CkA](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_cilium-api-doc-gen-001_091CkA.html) | — | `mcp-remote-direct` | `passed` | 0.970 | 5 | 0.958 |
| [sgonly_cilium-api-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_cilium-api-doc-gen-001.html) | — | `mcp-remote-direct` | `passed` | 0.960 | 5 | 0.950 |
| [docgen-changelog-001](../tasks/document_haiku_20260301_071228--baseline-local-direct--docgen-changelog-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 5 | 0.000 |
| [mcp_docgen-changelog-001_dAdbQw](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_docgen-changelog-001_dAdbQw.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.970 |
| [sgonly_docgen-changelog-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-changelog-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.935 |
| [docgen-changelog-002](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--docgen-changelog-002.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-changelog-002) | `baseline-local-direct` | `passed` | 1.000 | 6 | 0.000 |
| [mcp_docgen-changelog-002_FL0OCX](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_docgen-changelog-002_FL0OCX.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-changelog-002) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.704 |
| [mcp_docgen-changelog-002_elc2uw](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_docgen-changelog-002_elc2uw.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-changelog-002) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [sgonly_docgen-changelog-002](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-changelog-002.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-changelog-002) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.913 |
| [docgen-inline-001](../tasks/document_haiku_20260301_071228--baseline-local-direct--docgen-inline-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [mcp_docgen-inline-001_Iah13n](../tasks/csb_sdlc_document_haiku_20260228_124521--mcp-remote-direct--mcp_docgen-inline-001_Iah13n.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.100 |
| [sgonly_docgen-inline-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-inline-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.500 |
| [docgen-inline-002](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--docgen-inline-002.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-inline-002) | `baseline-local-direct` | `passed` | 1.000 | 6 | 0.000 |
| [mcp_docgen-inline-002_5i12ae](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_docgen-inline-002_5i12ae.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-inline-002) | `mcp-remote-direct` | `passed` | 0.880 | 6 | 0.261 |
| [mcp_docgen-inline-002_l0mqf7](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_docgen-inline-002_l0mqf7.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-inline-002) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.368 |
| [sgonly_docgen-inline-002](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-inline-002.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-inline-002) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.353 |
| [docgen-onboard-001](../tasks/document_haiku_20260301_071228--baseline-local-direct--docgen-onboard-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 5 | 0.000 |
| [mcp_docgen-onboard-001_hukfPp](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_docgen-onboard-001_hukfPp.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.958 |
| [sgonly_docgen-onboard-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-onboard-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.947 |
| [docgen-runbook-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--docgen-runbook-001.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-runbook-001) | `baseline-local-direct` | `passed` | 0.070 | 6 | - |
| [mcp_docgen-runbook-001_jYeNEv](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_docgen-runbook-001_jYeNEv.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-runbook-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.941 |
| [mcp_docgen-runbook-001_im4s9i](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_docgen-runbook-001_im4s9i.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-runbook-001) | `mcp-remote-direct` | `passed` | 0.920 | 6 | 0.966 |
| [sgonly_docgen-runbook-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-runbook-001.html) | [source](../../../benchmarks/csb_sdlc_document/docgen-runbook-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.680 |
| [docgen-runbook-002](../tasks/document_haiku_20260301_071228--baseline-local-direct--docgen-runbook-002.html) | — | `baseline-local-direct` | `passed` | 1.000 | 5 | 0.000 |
| [mcp_docgen-runbook-002_DNuQLB](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_docgen-runbook-002_DNuQLB.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.944 |
| [sgonly_docgen-runbook-002](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_docgen-runbook-002.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.889 |
| [envoy-arch-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--envoy-arch-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-arch-doc-gen-001) | `baseline-local-direct` | `passed` | 0.930 | 6 | 0.000 |
| [mcp_envoy-arch-doc-gen-001_uEBdoF](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_envoy-arch-doc-gen-001_uEBdoF.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.955 |
| [mcp_envoy-arch-doc-gen-001_gjcnoi](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_envoy-arch-doc-gen-001_gjcnoi.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-arch-doc-gen-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [sgonly_envoy-arch-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_envoy-arch-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.960 | 6 | 0.900 |
| [envoy-migration-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--envoy-migration-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-migration-doc-gen-001) | `baseline-local-direct` | `failed` | 0.000 | 6 | - |
| [mcp_envoy-migration-doc-gen-001_RmzLDJ](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_envoy-migration-doc-gen-001_RmzLDJ.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-migration-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.630 | 6 | 0.917 |
| [mcp_envoy-migration-doc-gen-001_neszpz](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_envoy-migration-doc-gen-001_neszpz.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-migration-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.760 | 6 | 0.905 |
| [sgonly_envoy-migration-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_envoy-migration-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/envoy-migration-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.720 | 6 | 0.947 |
| [istio-arch-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--istio-arch-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/istio-arch-doc-gen-001) | `baseline-local-direct` | `passed` | 1.000 | 6 | 0.000 |
| [mcp_istio-arch-doc-gen-001_TsE9lp](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_istio-arch-doc-gen-001_TsE9lp.html) | [source](../../../benchmarks/csb_sdlc_document/istio-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.960 | 6 | 0.947 |
| [mcp_istio-arch-doc-gen-001_nhlp1o](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_istio-arch-doc-gen-001_nhlp1o.html) | [source](../../../benchmarks/csb_sdlc_document/istio-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.950 | 6 | 0.964 |
| [sgonly_istio-arch-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_istio-arch-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/istio-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.960 | 6 | 0.958 |
| [k8s-apiserver-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--k8s-apiserver-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `baseline-local-direct` | `passed` | 0.520 | 6 | 0.000 |
| [mcp_k8s-apiserver-doc-gen-001_G2WWxT](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_k8s-apiserver-doc-gen-001_G2WWxT.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.770 | 6 | 0.971 |
| [mcp_k8s-apiserver-doc-gen-001_9vexvn](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_k8s-apiserver-doc-gen-001_9vexvn.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [mcp_k8s-apiserver-doc-gen-001_e9qHQA](../tasks/csb_sdlc_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-apiserver-doc-gen-001_e9qHQA.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 6 | 0.875 |
| [sgonly_k8s-apiserver-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_k8s-apiserver-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 6 | 0.962 |
| [k8s-applyconfig-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--k8s-applyconfig-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `baseline-local-direct` | `passed` | 0.790 | 6 | 0.000 |
| [mcp_k8s-applyconfig-doc-gen-001_KXIqYx](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_k8s-applyconfig-doc-gen-001_KXIqYx.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.947 |
| [mcp_k8s-applyconfig-doc-gen-001_4vndvw](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_k8s-applyconfig-doc-gen-001_4vndvw.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.958 |
| [mcp_k8s-applyconfig-doc-gen-001_JHZsM3](../tasks/csb_sdlc_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-applyconfig-doc-gen-001_JHZsM3.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.958 |
| [sgonly_k8s-applyconfig-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_k8s-applyconfig-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.960 | 6 | 0.958 |
| [k8s-clientgo-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--k8s-clientgo-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `baseline-local-direct` | `failed` | 0.000 | 6 | - |
| [mcp_k8s-clientgo-doc-gen-001_rKIpaI](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_k8s-clientgo-doc-gen-001_rKIpaI.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.974 |
| [mcp_k8s-clientgo-doc-gen-001_19q4yj](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_k8s-clientgo-doc-gen-001_19q4yj.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.960 | 6 | 0.933 |
| [mcp_k8s-clientgo-doc-gen-001_uV7Ssw](../tasks/csb_sdlc_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-clientgo-doc-gen-001_uV7Ssw.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 6 | 0.868 |
| [sgonly_k8s-clientgo-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_k8s-clientgo-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.970 |
| [k8s-fairqueuing-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--k8s-fairqueuing-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `baseline-local-direct` | `passed` | 0.320 | 6 | 0.000 |
| [mcp_k8s-fairqueuing-doc-gen-001_62urr3](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_k8s-fairqueuing-doc-gen-001_62urr3.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.520 | 6 | 0.882 |
| [mcp_k8s-fairqueuing-doc-gen-001_gwwdpd](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_k8s-fairqueuing-doc-gen-001_gwwdpd.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.420 | 6 | 0.955 |
| [mcp_k8s-fairqueuing-doc-gen-001_eRPJdR](../tasks/csb_sdlc_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-fairqueuing-doc-gen-001_eRPJdR.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 6 | 0.957 |
| [sgonly_k8s-fairqueuing-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_k8s-fairqueuing-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.450 | 6 | 0.964 |
| [k8s-kubelet-cm-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--k8s-kubelet-cm-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `baseline-local-direct` | `passed` | 0.650 | 6 | 0.000 |
| [mcp_k8s-kubelet-cm-doc-gen-001_n6VqU9](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_k8s-kubelet-cm-doc-gen-001_n6VqU9.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 6 | 0.952 |
| [mcp_k8s-kubelet-cm-doc-gen-001_c7mukj](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_k8s-kubelet-cm-doc-gen-001_c7mukj.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | `failed` | 0.000 | 6 | - |
| [mcp_k8s-kubelet-cm-doc-gen-001_mVr2Xz](../tasks/csb_sdlc_document_haiku_20260224_174311--mcp-remote-direct--mcp_k8s-kubelet-cm-doc-gen-001_mVr2Xz.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.650 | 6 | 0.968 |
| [sgonly_k8s-kubelet-cm-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_k8s-kubelet-cm-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.620 | 6 | 0.917 |
| [kafka-api-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--kafka-api-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/kafka-api-doc-gen-001) | `baseline-local-direct` | `failed` | 0.000 | 6 | - |
| [mcp_kafka-api-doc-gen-001_Kv6biZ](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_kafka-api-doc-gen-001_Kv6biZ.html) | [source](../../../benchmarks/csb_sdlc_document/kafka-api-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.990 | 6 | 0.938 |
| [mcp_kafka-api-doc-gen-001_cznegq](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_kafka-api-doc-gen-001_cznegq.html) | [source](../../../benchmarks/csb_sdlc_document/kafka-api-doc-gen-001) | `mcp-remote-direct` | `passed` | 1.000 | 6 | 0.824 |
| [sgonly_kafka-api-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_kafka-api-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/kafka-api-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.910 | 6 | 0.952 |
| [terraform-arch-doc-gen-001](../tasks/csb_sdlc_document_haiku_20260302_221730--baseline-local-direct--terraform-arch-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/terraform-arch-doc-gen-001) | `baseline-local-direct` | `failed` | 0.000 | 6 | - |
| [mcp_terraform-arch-doc-gen-001_4HxL3B](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_terraform-arch-doc-gen-001_4HxL3B.html) | [source](../../../benchmarks/csb_sdlc_document/terraform-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.590 | 6 | 0.920 |
| [mcp_terraform-arch-doc-gen-001_fvj949](../tasks/csb_sdlc_document_haiku_20260302_221730--mcp-remote-direct--mcp_terraform-arch-doc-gen-001_fvj949.html) | [source](../../../benchmarks/csb_sdlc_document/terraform-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.590 | 6 | 0.889 |
| [sgonly_terraform-arch-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_terraform-arch-doc-gen-001.html) | [source](../../../benchmarks/csb_sdlc_document/terraform-arch-doc-gen-001) | `mcp-remote-direct` | `passed` | 0.770 | 6 | 0.967 |
| [terraform-migration-doc-gen-001](../tasks/document_haiku_20260301_071228--baseline-local-direct--terraform-migration-doc-gen-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 5 | 0.000 |
| [mcp_terraform-migration-doc-gen-001_XjPeYr](../tasks/csb_sdlc_document_haiku_20260228_025547--mcp-remote-direct--mcp_terraform-migration-doc-gen-001_XjPeYr.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.857 |
| [sgonly_terraform-migration-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_terraform-migration-doc-gen-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 5 | 0.963 |
| [vscode-api-doc-gen-001](../tasks/document_haiku_20260301_071228--baseline-local-direct--vscode-api-doc-gen-001.html) | — | `baseline-local-direct` | `passed` | 1.000 | 4 | 0.000 |
| [sgonly_vscode-api-doc-gen-001](../tasks/document_haiku_20260301_071228--mcp-remote-direct--sgonly_vscode-api-doc-gen-001.html) | — | `mcp-remote-direct` | `passed` | 1.000 | 4 | 0.941 |

## Multi-Run Variance

Tasks with multiple valid runs (26 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| docgen-changelog-002 | [source](../../../benchmarks/csb_sdlc_document/docgen-changelog-002) | `baseline-local-direct` | 5 | 0.880 | 0.164 | 0.700, 1.000, 1.000, 0.700, 1.000 |
| docgen-changelog-002 | [source](../../../benchmarks/csb_sdlc_document/docgen-changelog-002) | `mcp-remote-direct` | 4 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000 |
| docgen-inline-002 | [source](../../../benchmarks/csb_sdlc_document/docgen-inline-002) | `baseline-local-direct` | 5 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000, 1.000 |
| docgen-inline-002 | [source](../../../benchmarks/csb_sdlc_document/docgen-inline-002) | `mcp-remote-direct` | 5 | 0.976 | 0.054 | 1.000, 0.880, 1.000, 1.000, 1.000 |
| docgen-runbook-001 | [source](../../../benchmarks/csb_sdlc_document/docgen-runbook-001) | `baseline-local-direct` | 4 | 0.970 | 0.060 | 1.000, 1.000, 1.000, 0.880 |
| docgen-runbook-001 | [source](../../../benchmarks/csb_sdlc_document/docgen-runbook-001) | `mcp-remote-direct` | 5 | 0.984 | 0.036 | 1.000, 1.000, 1.000, 1.000, 0.920 |
| envoy-arch-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/envoy-arch-doc-gen-001) | `baseline-local-direct` | 5 | 0.960 | 0.030 | 1.000, 0.930, 0.970, 0.970, 0.930 |
| envoy-arch-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/envoy-arch-doc-gen-001) | `mcp-remote-direct` | 4 | 0.983 | 0.021 | 1.000, 1.000, 0.970, 0.960 |
| envoy-migration-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/envoy-migration-doc-gen-001) | `baseline-local-direct` | 4 | 0.738 | 0.154 | 0.650, 0.960, 0.620, 0.720 |
| envoy-migration-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/envoy-migration-doc-gen-001) | `mcp-remote-direct` | 5 | 0.738 | 0.067 | 0.790, 0.630, 0.790, 0.720, 0.760 |
| istio-arch-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/istio-arch-doc-gen-001) | `baseline-local-direct` | 5 | 1.000 | 0.000 | 1.000, 1.000, 1.000, 1.000, 1.000 |
| istio-arch-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/istio-arch-doc-gen-001) | `mcp-remote-direct` | 5 | 0.966 | 0.019 | 1.000, 0.960, 0.960, 0.960, 0.950 |
| k8s-apiserver-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `baseline-local-direct` | 6 | 0.605 | 0.145 | 0.650, 0.470, 0.520, 0.870, 0.600, 0.520 |
| k8s-apiserver-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-apiserver-doc-gen-001) | `mcp-remote-direct` | 5 | 0.666 | 0.098 | 0.520, 0.650, 0.770, 0.740, 0.650 |
| k8s-applyconfig-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `baseline-local-direct` | 6 | 0.882 | 0.072 | 0.900, 1.000, 0.900, 0.830, 0.870, 0.790 |
| k8s-applyconfig-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-applyconfig-doc-gen-001) | `mcp-remote-direct` | 6 | 0.935 | 0.141 | 0.650, 1.000, 1.000, 1.000, 0.960, 1.000 |
| k8s-clientgo-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `baseline-local-direct` | 5 | 0.896 | 0.156 | 1.000, 0.650, 1.000, 1.000, 0.830 |
| k8s-clientgo-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-clientgo-doc-gen-001) | `mcp-remote-direct` | 6 | 0.877 | 0.176 | 0.650, 0.650, 1.000, 1.000, 1.000, 0.960 |
| k8s-fairqueuing-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `baseline-local-direct` | 6 | 0.390 | 0.113 | 0.240, 0.550, 0.450, 0.330, 0.450, 0.320 |
| k8s-fairqueuing-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-fairqueuing-doc-gen-001) | `mcp-remote-direct` | 6 | 0.435 | 0.219 | 0.020, 0.650, 0.520, 0.550, 0.450, 0.420 |
| k8s-kubelet-cm-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `baseline-local-direct` | 6 | 0.645 | 0.046 | 0.730, 0.620, 0.650, 0.600, 0.620, 0.650 |
| k8s-kubelet-cm-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/k8s-kubelet-cm-doc-gen-001) | `mcp-remote-direct` | 5 | 0.574 | 0.154 | 0.300, 0.650, 0.650, 0.650, 0.620 |
| kafka-api-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/kafka-api-doc-gen-001) | `baseline-local-direct` | 4 | 0.975 | 0.026 | 0.940, 0.990, 0.970, 1.000 |
| kafka-api-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/kafka-api-doc-gen-001) | `mcp-remote-direct` | 5 | 0.956 | 0.038 | 0.940, 0.990, 0.940, 0.910, 1.000 |
| terraform-arch-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/terraform-arch-doc-gen-001) | `baseline-local-direct` | 4 | 0.365 | 0.075 | 0.420, 0.430, 0.340, 0.270 |
| terraform-arch-doc-gen-001 | [source](../../../benchmarks/csb_sdlc_document/terraform-arch-doc-gen-001) | `mcp-remote-direct` | 5 | 0.626 | 0.081 | 0.590, 0.590, 0.590, 0.770, 0.590 |
