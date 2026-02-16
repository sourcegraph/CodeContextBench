# CodeContextBench Evaluation Report

Generated: 2026-02-16T14:43:19.258630+00:00
Report ID: eval_20260216_144319

## Run Inventory

| Benchmark                               | Config                   | Model                              | MCP Mode         | Tasks | Timestamp           |
| --------------------------------------- | ------------------------ | ---------------------------------- | ---------------- | ----- | ------------------- |
| ccb_crossrepo                           | baseline                 | anthropic/claude-opus-4-6          | none             | 5     | 2026-02-07 17-13-08 |
| ccb_crossrepo                           | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-07 17-51-36 |
| ccb_dibench                             | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 8     | 2026-02-03 16-43-09 |
| ccb_dibench                             | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-09 18-26-45 |
| ccb_k8sdocs                             | baseline                 | anthropic/claude-opus-4-6          | none             | 5     | 2026-02-10 23-14-36 |
| ccb_k8sdocs                             | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-10 23-27-15 |
| ccb_largerepo                           | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 4     | 2026-02-05 22-53-51 |
| ccb_largerepo                           | sourcegraph_base_latest  | anthropic/claude-opus-4-6          | sourcegraph_base | 1     | 2026-02-10 16-44-09 |
| ccb_largerepo                           | sourcegraph_base_precise | anthropic/claude-opus-4-6          | sourcegraph_base | 1     | 2026-02-10 17-07-44 |
| ccb_largerepo                           | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 4     | 2026-02-08 18-45-22 |
| ccb_pytorch                             | baseline                 | anthropic/claude-opus-4-6          | none             | 11    | 2026-02-10 16-40-10 |
| ccb_pytorch                             | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 11    | 2026-02-08 14-51-56 |
| ccb_swebenchpro                         | baseline                 | anthropic/claude-opus-4-6          | none             | 36    | 2026-02-12 11-10-31 |
| ccb_swebenchpro                         | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 36    | 2026-02-12 11-59-48 |
| ccb_sweperf                             | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 3     | 2026-02-05 01-04-11 |
| ccb_sweperf                             | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 3     | 2026-02-12 10-43-25 |
| ccb_tac                                 | baseline                 | anthropic/claude-opus-4-6          | none             | 8     | 2026-02-07 16-38-41 |
| ccb_tac                                 | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-07 17-52-41 |
| codereview                              | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 3     | 2026-02-06 15-53-56 |
| codereview                              | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 3     | 2026-02-08 21-07-39 |
| enterprise                              | baseline                 | anthropic/claude-opus-4-6          | none             | 12    | 2026-02-16 04-03-20 |
| enterprise                              | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 12    | 2026-02-16 03-45-25 |
| governance                              | baseline                 | anthropic/claude-opus-4-6          | none             | 8     | 2026-02-16 03-45-26 |
| governance                              | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-16 03-45-29 |
| investigation                           | baseline                 | anthropic/claude-opus-4-6          | none             | 4     | 2026-02-16 13-14-43 |
| investigation                           | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 4     | 2026-02-16 13-14-44 |
| largerepo                               | baseline                 | anthropic/claude-opus-4-6          | none             | 25    | 2026-02-16 04-44-23 |
| largerepo                               | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 25    | 2026-02-16 07-06-21 |
| linuxflbench                            | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 5     | 2026-02-06 16-28-49 |
| linuxflbench                            | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-08 21-35-42 |
| paired_rerun                            | baseline                 | anthropic/claude-opus-4-6          | none             | 119   | 2026-02-15 03-42-27 |
| paired_rerun                            | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 119   | 2026-02-15 03-42-28 |
| paired_rerun_crossrepo                  | baseline                 | anthropic/claude-opus-4-6          | none             | 5     | 2026-02-15 12-55-41 |
| paired_rerun_crossrepo                  | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-15 12-55-42 |
| paired_rerun_dibench                    | baseline                 | anthropic/claude-opus-4-6          | none             | 8     | 2026-02-15 12-46-07 |
| paired_rerun_dibench                    | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-15 12-46-08 |
| paired_rerun_pytorch                    | baseline                 | anthropic/claude-opus-4-6          | none             | 11    | 2026-02-14 16-51-56 |
| paired_rerun_pytorch                    | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 11    | 2026-02-14 16-51-58 |
| preamble_test_v3_single_20260214_132306 | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 1     | 2026-02-14 13-23-14 |
| preamble_test_v3_single_20260214_133204 | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 1     | 2026-02-14 13-32-11 |
| preamble_test_v3_single_20260214_135239 | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 1     | 2026-02-14 13-52-46 |
| preamble_test_v3_single_20260214_140737 | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 1     | 2026-02-14 14-07-44 |
| preamble_test_v3_single_20260214_141814 | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 1     | 2026-02-14 14-18-21 |

## Aggregate Performance

| Config                   | Mean Reward | Pass Rate | Tasks |
| ------------------------ | ----------- | --------- | ----- |
| baseline                 | 0.581       | 0.730     | 280   |
| sourcegraph_base_latest  | 0.700       | 1.000     | 1     |
| sourcegraph_base_precise | 0.700       | 1.000     | 1     |
| sourcegraph_full         | 0.611       | 0.754     | 285   |

## Per-Benchmark Breakdown (Mean Reward)

| Benchmark                               | baseline | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| --------------------------------------- | -------- | ----------------------- | ------------------------ | ---------------- |
| ccb_crossrepo                           | 0.571    | -                       | -                        | 0.387            |
| ccb_dibench                             | 0.500    | -                       | -                        | 0.500            |
| ccb_k8sdocs                             | 0.920    | -                       | -                        | 0.920            |
| ccb_largerepo                           | 0.250    | 0.700                   | 0.700                    | 0.425            |
| ccb_pytorch                             | 0.273    | -                       | -                        | 0.265            |
| ccb_swebenchpro                         | 0.722    | -                       | -                        | 0.824            |
| ccb_sweperf                             | 0.591    | -                       | -                        | 0.484            |
| ccb_tac                                 | 0.492    | -                       | -                        | 0.544            |
| codereview                              | 0.933    | -                       | -                        | 1.000            |
| enterprise                              | 0.821    | -                       | -                        | 0.756            |
| governance                              | 0.550    | -                       | -                        | 0.544            |
| investigation                           | 0.960    | -                       | -                        | 0.985            |
| largerepo                               | 0.000    | -                       | -                        | 0.425            |
| linuxflbench                            | 0.860    | -                       | -                        | 0.880            |
| paired_rerun                            | 0.558    | -                       | -                        | 0.590            |
| paired_rerun_crossrepo                  | 0.507    | -                       | -                        | 0.571            |
| paired_rerun_dibench                    | 0.500    | -                       | -                        | 0.500            |
| paired_rerun_pytorch                    | 0.273    | -                       | -                        | 0.270            |
| preamble_test_v3_single_20260214_132306 | -        | -                       | -                        | 0.900            |
| preamble_test_v3_single_20260214_133204 | -        | -                       | -                        | 0.900            |
| preamble_test_v3_single_20260214_135239 | -        | -                       | -                        | 0.900            |
| preamble_test_v3_single_20260214_140737 | -        | -                       | -                        | 0.900            |
| preamble_test_v3_single_20260214_141814 | -        | -                       | -                        | 0.900            |

## Efficiency

| Benchmark                               | Config                   | Mean Input Tokens | Mean Output Tokens | Mean Cache Tokens | Mean Task Time (s) | Mean Wall Clock (s) | Mean Cost (USD) |
| --------------------------------------- | ------------------------ | ----------------- | ------------------ | ----------------- | ------------------ | ------------------- | --------------- |
| ccb_crossrepo                           | baseline                 | 1,725             | 17,789             | 3,270,335         | 501.9              | 584.5               | $2.6890         |
| ccb_crossrepo                           | sourcegraph_full         | 57                | 18,011             | 4,102,584         | 489.1              | 620.1               | $3.9049         |
| ccb_dibench                             | baseline                 | 35                | 2,679              | 861,473           | 167.5              | 275.1               | $0.7194         |
| ccb_dibench                             | sourcegraph_full         | 22                | 3,589              | 1,066,031         | 135.4              | 170.7               | $0.9261         |
| ccb_k8sdocs                             | baseline                 | 1,387             | 4,316              | 464,890           | 197.6              | 332.5               | $0.6624         |
| ccb_k8sdocs                             | sourcegraph_full         | 16                | 5,365              | 903,269           | 196.1              | 359.8               | $0.8107         |
| ccb_largerepo                           | baseline                 | 85                | 23,860             | 7,356,855         | 997.2              | 2903.4              | $5.4184         |
| ccb_largerepo                           | sourcegraph_base_latest  | 5,803,848         | 491                | 5,803,759         | 587.1              | 1406.0              | $195.9150       |
| ccb_largerepo                           | sourcegraph_base_precise | 74                | 19,906             | 5,276,890         | 1494.6             | 2170.2              | $3.6124         |
| ccb_largerepo                           | sourcegraph_full         | 1,693             | 26,879             | 8,073,793         | 2247.1             | 3931.5              | $5.7837         |
| ccb_pytorch                             | baseline                 | 1,783             | 9,481              | 2,533,532         | 268.7              | 977.7               | $1.8711         |
| ccb_pytorch                             | sourcegraph_full         | 224               | 12,449             | 3,742,737         | 685.4              | 2954.1              | $2.5841         |
| ccb_swebenchpro                         | baseline                 | 403               | 10,459             | 2,912,192         | 426.8              | 763.1               | $2.2214         |
| ccb_swebenchpro                         | sourcegraph_full         | 443               | 10,907             | 2,908,117         | 421.1              | 1537.6              | $2.1028         |
| ccb_sweperf                             | baseline                 | 2                 | 18,896             | 5,061,122         | 452.7              | 795.7               | $3.8225         |
| ccb_sweperf                             | sourcegraph_full         | 81                | 30,733             | 6,675,402         | 773.4              | 881.3               | $4.7614         |
| ccb_tac                                 | baseline                 | 53                | 14,563             | 3,253,165         | 619.9              | 1483.0              | $2.5536         |
| ccb_tac                                 | sourcegraph_full         | 435               | 16,705             | 3,041,064         | 614.1              | 1087.3              | $2.4761         |
| codereview                              | baseline                 | 2                 | 4,360              | 622,987           | 90.4               | 185.9               | $0.5640         |
| codereview                              | sourcegraph_full         | 21                | 6,338              | 978,964           | 116.4              | 209.0               | $0.8254         |
| enterprise                              | baseline                 | 240               | 6,187              | 921,836           | 679.1              | 1256.2              | $2.5200         |
| enterprise                              | sourcegraph_full         | 57                | 22,980             | 4,966,936         | 813.5              | 1370.8              | $4.5353         |
| governance                              | baseline                 | 387               | 20,654             | 3,853,032         | 1074.4             | 2192.5              | $3.2935         |
| governance                              | sourcegraph_full         | 207               | 18,448             | 3,678,853         | 919.8              | 2056.0              | $2.7275         |
| investigation                           | baseline                 | 210               | 6,361              | 1,027,994         | 253.6              | 511.5               | $2.0043         |
| investigation                           | sourcegraph_full         | 28                | 9,943              | 2,175,810         | 218.9              | 475.2               | $1.8773         |
| largerepo                               | baseline                 | 18,064            | 8,811              | 1,298,281         | 876.1              | 2210.0              | $3.3219         |
| largerepo                               | sourcegraph_full         | 697,947           | 11,836             | 3,105,234         | 1268.4             | 2231.1              | $27.2613        |
| linuxflbench                            | baseline                 | 41                | 6,408              | 1,324,768         | 232.5              | 568.4               | $1.0380         |
| linuxflbench                            | sourcegraph_full         | 25                | 6,471              | 1,399,965         | 228.9              | 414.4               | $1.3659         |
| paired_rerun                            | baseline                 | 8,731             | 8,712              | 1,282,295         | 336.0              | 670.0               | $1.8825         |
| paired_rerun                            | sourcegraph_full         | 82                | 10,437             | 2,101,860         | 363.8              | 679.4               | $2.0729         |
| paired_rerun_crossrepo                  | baseline                 | 411               | 14,916             | 3,117,290         | 373.8              | 457.3               | $2.6481         |
| paired_rerun_crossrepo                  | sourcegraph_full         | 38                | 12,895             | 2,471,379         | 474.6              | 570.5               | $3.7486         |
| paired_rerun_dibench                    | baseline                 | 44                | 3,810              | 653,077           | 160.9              | 300.7               | $0.6517         |
| paired_rerun_dibench                    | sourcegraph_full         | 44                | 6,802              | 2,312,329         | 260.4              | 398.0               | $1.6099         |
| paired_rerun_pytorch                    | baseline                 | 161               | 12,103             | 2,458,265         | 425.4              | 1090.5              | $2.0063         |
| paired_rerun_pytorch                    | sourcegraph_full         | 61                | 13,078             | 3,909,063         | 461.2              | 1144.4              | $2.6803         |
| preamble_test_v3_single_20260214_132306 | sourcegraph_full         | 399               | 5,885              | 945,505           | 150.5              | 298.9               | $0.9120         |
| preamble_test_v3_single_20260214_133204 | sourcegraph_full         | 4,310             | 2,816              | 265,846           | 546.6              | 669.6               | $0.7096         |
| preamble_test_v3_single_20260214_135239 | sourcegraph_full         | 11                | 3,406              | 401,985           | 142.1              | 260.3               | $0.7092         |
| preamble_test_v3_single_20260214_140737 | sourcegraph_full         | 21                | 5,278              | 994,096           | 247.1              | 341.1               | $0.8192         |
| preamble_test_v3_single_20260214_141814 | sourcegraph_full         | 15                | 4,476              | 933,998           | 227.5              | 320.7               | $0.8694         |

## Tool Utilization

| Benchmark                               | Config                   | Mean Total Calls | Mean MCP Calls | Mean Local Calls | Mean MCP Ratio |
| --------------------------------------- | ------------------------ | ---------------- | -------------- | ---------------- | -------------- |
| ccb_crossrepo                           | baseline                 | 68.4             | 0.0            | 68.4             | 0.000          |
| ccb_crossrepo                           | sourcegraph_full         | 72.2             | 1.4            | 70.8             | 0.018          |
| ccb_dibench                             | baseline                 | 25.9             | 0.0            | 25.9             | 0.000          |
| ccb_dibench                             | sourcegraph_full         | 29.4             | 12.2           | 17.1             | 0.415          |
| ccb_k8sdocs                             | baseline                 | 17.4             | 0.0            | 17.4             | 0.000          |
| ccb_k8sdocs                             | sourcegraph_full         | 24.8             | 15.0           | 9.8              | 0.605          |
| ccb_largerepo                           | baseline                 | 86.0             | 0.0            | 86.0             | 0.000          |
| ccb_largerepo                           | sourcegraph_base_latest  | 60.0             | 8.0            | 52.0             | 0.133          |
| ccb_largerepo                           | sourcegraph_base_precise | 104.0            | 4.0            | 100.0            | 0.038          |
| ccb_largerepo                           | sourcegraph_full         | 107.5            | 5.0            | 102.5            | 0.050          |
| ccb_pytorch                             | baseline                 | 58.4             | 0.0            | 58.4             | 0.000          |
| ccb_pytorch                             | sourcegraph_full         | 65.5             | 12.9           | 52.5             | 0.169          |
| ccb_swebenchpro                         | baseline                 | 50.8             | 0.0            | 50.8             | 0.000          |
| ccb_swebenchpro                         | sourcegraph_full         | 51.2             | 7.0            | 44.2             | 0.158          |
| ccb_sweperf                             | baseline                 | 60.7             | 0.0            | 60.7             | 0.000          |
| ccb_sweperf                             | sourcegraph_full         | 90.7             | 5.7            | 85.0             | 0.065          |
| ccb_tac                                 | baseline                 | 56.9             | 0.0            | 56.9             | 0.000          |
| ccb_tac                                 | sourcegraph_full         | 49.9             | 5.5            | 44.4             | 0.156          |
| codereview                              | baseline                 | 21.7             | 0.0            | 21.7             | 0.000          |
| codereview                              | sourcegraph_full         | 34.7             | 9.7            | 25.0             | 0.287          |
| enterprise                              | baseline                 | 55.8             | 0.0            | 55.8             | 0.000          |
| enterprise                              | sourcegraph_full         | 77.8             | 10.5           | 67.3             | 0.205          |
| governance                              | baseline                 | 72.9             | 0.0            | 72.9             | 0.000          |
| governance                              | sourcegraph_full         | 63.4             | 6.9            | 56.5             | 0.117          |
| investigation                           | baseline                 | 41.2             | 0.0            | 41.2             | 0.000          |
| investigation                           | sourcegraph_full         | 48.5             | 29.0           | 19.5             | 0.596          |
| largerepo                               | baseline                 | 45.4             | 0.0            | 45.4             | 0.000          |
| largerepo                               | sourcegraph_full         | 82.1             | 25.1           | 57.0             | 0.432          |
| linuxflbench                            | baseline                 | 31.6             | 0.0            | 31.6             | 0.000          |
| linuxflbench                            | sourcegraph_full         | 33.0             | 17.8           | 15.2             | 0.434          |
| paired_rerun                            | baseline                 | 30.5             | 0.0            | 30.5             | 0.000          |
| paired_rerun                            | sourcegraph_full         | 38.8             | 8.3            | 30.5             | 0.276          |
| paired_rerun_crossrepo                  | baseline                 | 57.8             | 0.0            | 57.8             | 0.000          |
| paired_rerun_crossrepo                  | sourcegraph_full         | 88.6             | 1.6            | 87.0             | 0.022          |
| paired_rerun_dibench                    | baseline                 | 29.0             | 0.0            | 29.0             | 0.000          |
| paired_rerun_dibench                    | sourcegraph_full         | 44.6             | 2.4            | 42.2             | 0.083          |
| paired_rerun_pytorch                    | baseline                 | 64.2             | 0.0            | 64.2             | 0.000          |
| paired_rerun_pytorch                    | sourcegraph_full         | 70.5             | 10.3           | 60.3             | 0.120          |
| preamble_test_v3_single_20260214_132306 | sourcegraph_full         | 29.0             | 0.0            | 29.0             | 0.000          |
| preamble_test_v3_single_20260214_133204 | sourcegraph_full         | 7.0              | 0.0            | 7.0              | 0.000          |
| preamble_test_v3_single_20260214_135239 | sourcegraph_full         | 12.0             | 0.0            | 12.0             | 0.000          |
| preamble_test_v3_single_20260214_140737 | sourcegraph_full         | 31.0             | 4.0            | 27.0             | 0.129          |
| preamble_test_v3_single_20260214_141814 | sourcegraph_full         | 26.0             | 2.0            | 24.0             | 0.077          |

## Search Patterns

| Benchmark                               | Config                   | Mean Keyword Searches | Mean NLS Searches | Mean Deep Searches | Mean DS/KW Ratio |
| --------------------------------------- | ------------------------ | --------------------- | ----------------- | ------------------ | ---------------- |
| ccb_crossrepo                           | baseline                 | -                     | -                 | -                  | -                |
| ccb_crossrepo                           | sourcegraph_full         | 7.0                   | 0.0               | 0.0                | 0.000            |
| ccb_dibench                             | baseline                 | -                     | -                 | -                  | -                |
| ccb_dibench                             | sourcegraph_full         | 2.6                   | 0.0               | 0.0                | 0.000            |
| ccb_k8sdocs                             | baseline                 | -                     | -                 | -                  | -                |
| ccb_k8sdocs                             | sourcegraph_full         | 4.4                   | 0.2               | 0.0                | 0.000            |
| ccb_largerepo                           | baseline                 | -                     | -                 | -                  | -                |
| ccb_largerepo                           | sourcegraph_base_latest  | 7.0                   | 1.0               | 0.0                | 0.000            |
| ccb_largerepo                           | sourcegraph_base_precise | 3.0                   | 0.0               | 0.0                | 0.000            |
| ccb_largerepo                           | sourcegraph_full         | 3.8                   | 0.5               | 0.0                | 0.000            |
| ccb_pytorch                             | baseline                 | -                     | -                 | -                  | -                |
| ccb_pytorch                             | sourcegraph_full         | 6.9                   | 0.2               | 0.0                | 0.000            |
| ccb_swebenchpro                         | baseline                 | -                     | -                 | -                  | -                |
| ccb_swebenchpro                         | sourcegraph_full         | 3.7                   | 0.0               | 0.0                | 0.000            |
| ccb_sweperf                             | baseline                 | -                     | -                 | -                  | -                |
| ccb_sweperf                             | sourcegraph_full         | 3.3                   | 0.0               | 0.0                | 0.000            |
| ccb_tac                                 | baseline                 | -                     | -                 | -                  | -                |
| ccb_tac                                 | sourcegraph_full         | 2.4                   | 0.0               | 0.0                | 0.000            |
| codereview                              | baseline                 | -                     | -                 | -                  | -                |
| codereview                              | sourcegraph_full         | 5.7                   | 0.0               | 0.0                | 0.000            |
| enterprise                              | baseline                 | -                     | -                 | -                  | -                |
| enterprise                              | sourcegraph_full         | 4.2                   | 0.7               | 0.0                | 0.000            |
| governance                              | baseline                 | -                     | -                 | -                  | -                |
| governance                              | sourcegraph_full         | 3.6                   | 0.4               | 0.0                | 0.000            |
| investigation                           | baseline                 | -                     | -                 | -                  | -                |
| investigation                           | sourcegraph_full         | 12.5                  | 1.5               | 0.0                | 0.000            |
| largerepo                               | baseline                 | -                     | -                 | -                  | -                |
| largerepo                               | sourcegraph_full         | 10.7                  | 0.9               | 0.0                | 0.000            |
| linuxflbench                            | baseline                 | -                     | -                 | -                  | -                |
| linuxflbench                            | sourcegraph_full         | 10.2                  | 0.0               | 0.0                | 0.000            |
| paired_rerun                            | baseline                 | -                     | -                 | -                  | -                |
| paired_rerun                            | sourcegraph_full         | 2.9                   | 0.8               | 0.5                | 0.340            |
| paired_rerun_crossrepo                  | baseline                 | -                     | -                 | -                  | -                |
| paired_rerun_crossrepo                  | sourcegraph_full         | 0.7                   | 0.0               | 1.0                | 0.778            |
| paired_rerun_dibench                    | baseline                 | -                     | -                 | -                  | -                |
| paired_rerun_dibench                    | sourcegraph_full         | -                     | -                 | -                  | -                |
| paired_rerun_pytorch                    | baseline                 | -                     | -                 | -                  | -                |
| paired_rerun_pytorch                    | sourcegraph_full         | 4.6                   | 0.6               | 0.1                | 0.006            |
| preamble_test_v3_single_20260214_132306 | sourcegraph_full         | -                     | -                 | -                  | -                |
| preamble_test_v3_single_20260214_133204 | sourcegraph_full         | -                     | -                 | -                  | -                |
| preamble_test_v3_single_20260214_135239 | sourcegraph_full         | -                     | -                 | -                  | -                |
| preamble_test_v3_single_20260214_140737 | sourcegraph_full         | 3.0                   | 0.0               | 0.0                | 0.000            |
| preamble_test_v3_single_20260214_141814 | sourcegraph_full         | 1.0                   | 0.0               | 0.0                | 0.000            |

## Code Changes

| Benchmark                               | Config                   | Mean Files Modified | Mean Lines Added | Mean Lines Removed |
| --------------------------------------- | ------------------------ | ------------------- | ---------------- | ------------------ |
| ccb_crossrepo                           | baseline                 | 2.4                 | 525.6            | 0.6                |
| ccb_crossrepo                           | sourcegraph_full         | 1.4                 | 129.0            | 0.6                |
| ccb_dibench                             | baseline                 | 1.0                 | 9.0              | 4.5                |
| ccb_dibench                             | sourcegraph_full         | 1.0                 | 9.4              | 4.4                |
| ccb_k8sdocs                             | baseline                 | 1.0                 | 130.2            | 0.0                |
| ccb_k8sdocs                             | sourcegraph_full         | 1.0                 | 133.6            | 0.0                |
| ccb_largerepo                           | baseline                 | 5.2                 | 434.0            | 204.8              |
| ccb_largerepo                           | sourcegraph_base_latest  | 12.0                | 251.0            | 71.0               |
| ccb_largerepo                           | sourcegraph_base_precise | 9.0                 | 206.0            | 92.0               |
| ccb_largerepo                           | sourcegraph_full         | 7.5                 | 331.2            | 143.0              |
| ccb_pytorch                             | baseline                 | 3.0                 | 130.0            | 106.0              |
| ccb_pytorch                             | sourcegraph_full         | 3.5                 | 188.1            | 77.2               |
| ccb_swebenchpro                         | baseline                 | 4.6                 | 129.2            | 67.0               |
| ccb_swebenchpro                         | sourcegraph_full         | 5.1                 | 170.4            | 68.7               |
| ccb_sweperf                             | baseline                 | 2.3                 | 452.0            | 104.7              |
| ccb_sweperf                             | sourcegraph_full         | 2.7                 | 668.7            | 108.0              |
| ccb_tac                                 | baseline                 | 3.0                 | 254.3            | 24.7               |
| ccb_tac                                 | sourcegraph_full         | 4.0                 | 405.7            | 10.0               |
| codereview                              | baseline                 | 3.7                 | 64.7             | 27.7               |
| codereview                              | sourcegraph_full         | 3.7                 | 58.3             | 16.0               |
| enterprise                              | baseline                 | 4.8                 | 81.9             | 47.2               |
| enterprise                              | sourcegraph_full         | 3.2                 | 179.0            | 65.5               |
| governance                              | baseline                 | 2.2                 | 135.4            | 71.0               |
| governance                              | sourcegraph_full         | 1.9                 | 68.8             | 26.8               |
| investigation                           | baseline                 | 1.0                 | 155.8            | 0.0                |
| investigation                           | sourcegraph_full         | 1.0                 | 165.5            | 0.0                |
| largerepo                               | baseline                 | 4.6                 | 419.3            | 24.3               |
| largerepo                               | sourcegraph_full         | 5.7                 | 456.2            | 45.8               |
| linuxflbench                            | baseline                 | 1.0                 | 7.0              | 0.0                |
| linuxflbench                            | sourcegraph_full         | 1.0                 | 8.6              | 0.2                |
| paired_rerun                            | baseline                 | 2.9                 | 308.0            | 47.4               |
| paired_rerun                            | sourcegraph_full         | 3.2                 | 278.6            | 46.0               |
| paired_rerun_crossrepo                  | baseline                 | 2.0                 | 136.0            | 1.4                |
| paired_rerun_crossrepo                  | sourcegraph_full         | 5.4                 | 156.4            | 28.4               |
| paired_rerun_dibench                    | baseline                 | 1.0                 | 9.1              | 4.5                |
| paired_rerun_dibench                    | sourcegraph_full         | 1.0                 | 14.4             | 8.9                |
| paired_rerun_pytorch                    | baseline                 | 4.1                 | 145.6            | 83.1               |
| paired_rerun_pytorch                    | sourcegraph_full         | 2.9                 | 96.6             | 70.4               |
| preamble_test_v3_single_20260214_132306 | sourcegraph_full         | 1.0                 | 137.0            | 0.0                |
| preamble_test_v3_single_20260214_133204 | sourcegraph_full         | 1.0                 | 118.0            | 0.0                |
| preamble_test_v3_single_20260214_135239 | sourcegraph_full         | 1.0                 | 127.0            | 0.0                |
| preamble_test_v3_single_20260214_140737 | sourcegraph_full         | 1.0                 | 102.0            | 0.0                |
| preamble_test_v3_single_20260214_141814 | sourcegraph_full         | 1.0                 | 115.0            | 0.0                |

## Cache Efficiency

| Benchmark                               | Config                   | Mean Cache Hit Rate | Mean Input/Output Ratio | Mean Cost (USD) |
| --------------------------------------- | ------------------------ | ------------------- | ----------------------- | --------------- |
| ccb_crossrepo                           | baseline                 | 0.967               | 0.2                     | $2.6890         |
| ccb_crossrepo                           | sourcegraph_full         | 0.955               | 0.0                     | $3.9049         |
| ccb_dibench                             | baseline                 | 0.958               | 0.0                     | $0.7194         |
| ccb_dibench                             | sourcegraph_full         | 0.963               | 0.0                     | $0.9261         |
| ccb_k8sdocs                             | baseline                 | 0.945               | 0.4                     | $0.6624         |
| ccb_k8sdocs                             | sourcegraph_full         | 0.958               | 0.0                     | $0.8107         |
| ccb_largerepo                           | baseline                 | 0.979               | 0.0                     | $5.4184         |
| ccb_largerepo                           | sourcegraph_base_latest  | -                   | 11820.5                 | $195.9150       |
| ccb_largerepo                           | sourcegraph_base_precise | 0.986               | 0.0                     | $3.6124         |
| ccb_largerepo                           | sourcegraph_full         | 0.986               | 0.1                     | $5.7837         |
| ccb_pytorch                             | baseline                 | 0.977               | 0.1                     | $1.8711         |
| ccb_pytorch                             | sourcegraph_full         | 0.981               | 0.0                     | $2.5841         |
| ccb_swebenchpro                         | baseline                 | 0.969               | 0.1                     | $2.2214         |
| ccb_swebenchpro                         | sourcegraph_full         | 0.975               | 0.0                     | $2.1028         |
| ccb_sweperf                             | baseline                 | 0.974               | 0.0                     | $3.8225         |
| ccb_sweperf                             | sourcegraph_full         | 0.986               | 0.0                     | $4.7614         |
| ccb_tac                                 | baseline                 | 0.975               | 0.0                     | $2.5536         |
| ccb_tac                                 | sourcegraph_full         | 0.972               | 0.0                     | $2.4761         |
| codereview                              | baseline                 | 0.960               | 0.0                     | $0.5640         |
| codereview                              | sourcegraph_full         | 0.970               | 0.0                     | $0.8254         |
| enterprise                              | baseline                 | 0.842               | 0.0                     | $2.5200         |
| enterprise                              | sourcegraph_full         | 0.759               | 0.0                     | $4.5353         |
| governance                              | baseline                 | 0.887               | 0.1                     | $3.2935         |
| governance                              | sourcegraph_full         | 0.981               | 0.0                     | $2.7275         |
| investigation                           | baseline                 | 0.963               | 0.0                     | $2.0043         |
| investigation                           | sourcegraph_full         | 0.954               | 0.0                     | $1.8773         |
| largerepo                               | baseline                 | 0.747               | 232.2                   | $3.3219         |
| largerepo                               | sourcegraph_full         | 0.895               | 880.9                   | $27.2613        |
| linuxflbench                            | baseline                 | 0.967               | 0.0                     | $1.0380         |
| linuxflbench                            | sourcegraph_full         | 0.968               | 0.0                     | $1.3659         |
| paired_rerun                            | baseline                 | 0.949               | 146.8                   | $1.8825         |
| paired_rerun                            | sourcegraph_full         | 0.959               | 0.0                     | $2.0729         |
| paired_rerun_crossrepo                  | baseline                 | 0.972               | 0.0                     | $2.6481         |
| paired_rerun_crossrepo                  | sourcegraph_full         | 0.982               | 0.0                     | $3.7486         |
| paired_rerun_dibench                    | baseline                 | 0.967               | 0.0                     | $0.6517         |
| paired_rerun_dibench                    | sourcegraph_full         | 0.973               | 0.0                     | $1.6099         |
| paired_rerun_pytorch                    | baseline                 | 0.981               | 0.0                     | $2.0063         |
| paired_rerun_pytorch                    | sourcegraph_full         | 0.983               | 0.0                     | $2.6803         |
| preamble_test_v3_single_20260214_132306 | sourcegraph_full         | 0.950               | 0.1                     | $0.9120         |
| preamble_test_v3_single_20260214_133204 | sourcegraph_full         | 0.961               | 1.5                     | $0.7096         |
| preamble_test_v3_single_20260214_135239 | sourcegraph_full         | 0.968               | 0.0                     | $0.7092         |
| preamble_test_v3_single_20260214_140737 | sourcegraph_full         | 0.971               | 0.0                     | $0.8192         |
| preamble_test_v3_single_20260214_141814 | sourcegraph_full         | 0.949               | 0.0                     | $0.8694         |

## SWE-Bench Pro Partial Scores

| Config           | Mean Partial Score | Tasks |
| ---------------- | ------------------ | ----- |
| baseline         | 0.816              | 36    |
| sourcegraph_full | 0.824              | 36    |

## Performance by SDLC Phase

| SDLC Phase                   | Tasks | baseline | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| ---------------------------- | ----- | -------- | ----------------------- | ------------------------ | ---------------- |
| Analysis                     | 8     | -        | -                       | -                        | -                |
| Architecture & Design        | 26    | 0.759    | -                       | -                        | 0.760            |
| Debugging                    | 3     | -        | -                       | -                        | -                |
| Documentation                | 5     | 0.920    | -                       | -                        | 0.913            |
| Implementation (bug fix)     | 62    | 0.547    | -                       | -                        | 0.576            |
| Implementation (feature)     | 44    | 0.457    | 0.700                   | 0.700                    | 0.535            |
| Implementation (refactor)    | 2     | 0.725    | -                       | -                        | 0.725            |
| Implementation (refactoring) | 15    | 0.377    | -                       | -                        | 0.352            |
| Maintenance                  | 2     | 0.200    | -                       | -                        | 0.200            |
| Planning (impact analysis)   | 2     | 0.928    | -                       | -                        | 0.839            |
| Refactoring                  | 4     | -        | -                       | -                        | -                |
| Requirements & Discovery     | 16    | 0.758    | -                       | -                        | 0.774            |
| Security review              | 3     | -        | -                       | -                        | -                |
| Testing & QA                 | 8     | 0.754    | -                       | -                        | 0.714            |

## Performance by Language

| Language   | Tasks | baseline | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| ---------- | ----- | -------- | ----------------------- | ------------------------ | ---------------- |
| c          | 14    | 0.698    | -                       | -                        | 0.694            |
| cpp        | 19    | 0.267    | -                       | -                        | 0.303            |
| csharp     | 6     | 0.384    | -                       | -                        | 0.386            |
| go         | 38    | 0.755    | 0.700                   | 0.700                    | 0.769            |
| java       | 20    | 0.721    | -                       | -                        | 0.809            |
| javascript | 14    | 0.725    | -                       | -                        | 0.893            |
| python     | 55    | 0.573    | -                       | -                        | 0.557            |
| python,cpp | 1     | 1.000    | -                       | -                        | 1.000            |
| rust       | 13    | 0.549    | -                       | -                        | 0.552            |
| typescript | 20    | 0.669    | -                       | -                        | 0.721            |

## Performance by MCP Benefit Score

| MCP Benefit Score   | Tasks | baseline | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| ------------------- | ----- | -------- | ----------------------- | ------------------------ | ---------------- |
| 0.0-0.4 (low)       | 0     | -        | -                       | -                        | -                |
| 0.4-0.6 (medium)    | 34    | 0.459    | -                       | -                        | 0.524            |
| 0.6-0.8 (high)      | 73    | 0.616    | -                       | -                        | 0.658            |
| 0.8-1.0 (very high) | 72    | 0.641    | 0.700                   | 0.700                    | 0.640            |

