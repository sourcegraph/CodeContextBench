# CodeContextBench Task Catalog

A detailed reference for every benchmark task in CodeContextBench. This document covers all 17 active benchmark suites totaling 186 tasks.

**Selection methodology:** Tasks were chosen via stratified sampling across benchmarks, covering all SDLC phases. Each task is scored for MCP benefit using a weighted combination of context complexity (0.25), cross-file dependencies (0.30), semantic search potential (0.20), and tool-chain weight (0.25). See `docs/TASK_SELECTION.md` for full scoring methodology.

---

## Table of Contents

1. [SWE-bench Pro (36 tasks)](#1-swe-bench-pro--real-world-software-engineering)
2. [LargeRepo (25 tasks)](#2-largerepo--large-codebase-navigation)
3. [DocGen (13 tasks)](#3-docgen--documentation-generation)
4. [CrossRepo (12 tasks)](#4-crossrepo--cross-repository-reasoning)
5. [Enterprise (12 tasks)](#5-enterprise--enterprise-codebase-challenges)
6. [PyTorch (11 tasks)](#6-pytorch--pytorch-pr-level-tasks)
7. [NavProve (9 tasks)](#7-navprove--navigation--provenance-reasoning)
8. [CodeReview (8 tasks)](#8-codereview--ai-code-review)
9. [DIBench (8 tasks)](#9-dibench--dependency-installation)
10. [Governance (8 tasks)](#10-governance--access-control--policy-enforcement)
11. [NLQA (8 tasks)](#11-nlqa--natural-language-code-qa)
12. [Onboarding (8 tasks)](#12-onboarding--codebase-onboarding)
13. [Security (8 tasks)](#13-security--security-analysis)
14. [TAC (8 tasks)](#14-tac--the-agent-company)
15. [LinuxFLBench (5 tasks)](#15-linuxflbench--linux-kernel-fault-localization)
16. [Investigation (4 tasks)](#16-investigation--deep-investigation)
17. [SWE-Perf (3 tasks)](#17-swe-perf--performance-optimization)
18. [Archived Suites](#appendix-archived-suites)

---

## 1. SWE-bench Pro -- Real-World Software Engineering

**Focus:** Fix real bugs from production open-source repositories. Each task corresponds to an actual GitHub issue and its resolution.
**Difficulty:** hard (all tasks) | **SDLC Phase:** Implementation (bug fix)

### By Repository

| Repository | Language | Tasks | MCP Score Range |
|------------|----------|-------|-----------------|
| NodeBB/NodeBB | JavaScript | 3 | 0.573 - 0.938 |
| ansible/ansible | Python | 5 | 0.476 - 0.698 |
| element-hq/element-web | TypeScript | 2 | 0.493 - 0.805 |
| flipt-io/flipt | Go | 4 | 0.634 - 0.819 |
| future-architect/vuls | Go | 3 | 0.509 - 0.650 |
| gravitational/teleport | Go | 4 | 0.439 - 0.763 |
| internetarchive/openlibrary | Python | 4 | 0.635 - 0.719 |
| navidrome/navidrome | Go | 2 | 0.600 - 0.671 |
| protonmail/webclients | TypeScript | 4 | 0.779 - 0.938 |
| qutebrowser/qutebrowser | Python | 4 | 0.403 - 0.588 |
| tutao/tutanota | TypeScript | 1 | 0.514 |

---

## 2. LargeRepo -- Large Codebase Navigation

**Focus:** Implement features, analyze architecture, fix bugs, and review security in 1GB+ open-source repositories requiring deep navigation of distributed code patterns.
**Difficulty:** hard (all tasks)

| Task | Language | Repository | SDLC Phase |
|------|----------|------------|------------|
| big-code-k8s-001 | Go | kubernetes/kubernetes | Feature impl |
| big-code-servo-001 | Rust | servo/servo | Feature impl |
| big-code-trt-001 | Python, C++ | NVIDIA/TensorRT-LLM | Feature impl |
| big-code-vsc-001 | TypeScript | microsoft/vscode | Feature impl |
| big-code-camel-arch-001 | Java | apache/camel | Analysis |
| big-code-camel-feat-001 | Java | apache/camel | Feature impl |
| big-code-cross-capmarkets-arch-001 | Java | Strata/capital-markets | Analysis |
| big-code-cross-k8s-arch-001 | Go | kubernetes/kubernetes | Analysis |
| big-code-django-arch-001 | Python | django/django | Analysis |
| big-code-django-bug-001 | Python | django/django | Debugging |
| big-code-django-sec-001 | Python | django/django | Security |
| big-code-flink-arch-001 | Java | apache/flink | Analysis |
| big-code-flink-feat-001 | Java | apache/flink | Feature impl |
| big-code-k8s-arch-001 | Go | kubernetes/kubernetes | Analysis |
| big-code-k8s-bug-001 | Go | kubernetes/kubernetes | Debugging |
| big-code-k8s-refac-001 | Go | kubernetes/kubernetes | Refactoring |
| big-code-kafka-bug-001 | Java | apache/kafka | Debugging |
| big-code-kafka-refac-001 | Java | apache/kafka | Refactoring |
| big-code-kafka-sec-001 | Java | apache/kafka | Security |
| big-code-pg-arch-001 | C | postgres/postgres | Analysis |
| big-code-pg-sec-001 | C | postgres/postgres | Security |
| big-code-quantlib-arch-001 | C++ | QuantLib/QuantLib | Analysis |
| big-code-rust-refac-001 | Rust | servo/servo | Refactoring |
| big-code-strata-feat-001 | Java | Strata/strata | Feature impl |
| big-code-strata-refac-001 | Java | Strata/strata | Refactoring |

---

## 3. DocGen -- Documentation Generation

**Focus:** Generate accurate API documentation, architecture guides, and migration plans by reading and understanding source code. Supersedes the archived ccb_k8sdocs suite.
**Difficulty:** hard (all tasks) | **SDLC Phase:** Documentation

| Task | Language | Focus |
|------|----------|-------|
| docgen-api-001 | TypeScript | API reference documentation |
| docgen-api-002 | Go | API reference documentation |
| docgen-api-003 | Java | API reference documentation |
| docgen-arch-001 | C++ | Architecture documentation |
| docgen-arch-002 | Go | Architecture documentation |
| docgen-arch-003 | Go | Architecture documentation |
| docgen-k8s-apiserver-001 | Go | K8s apiserver package docs |
| docgen-k8s-applyconfig-001 | Go | K8s apply configurations docs |
| docgen-k8s-clientgo-001 | Go | K8s client-go library docs |
| docgen-k8s-cm-001 | Go | K8s container manager docs |
| docgen-k8s-fairqueuing-001 | Go | K8s fair queuing algorithm docs |
| docgen-migration-001 | Go | Migration guide documentation |
| docgen-migration-002 | C++ | Migration guide documentation |

---

## 4. CrossRepo -- Cross-Repository Reasoning

**Focus:** Tasks that span multiple repositories, testing the ability to trace interactions, APIs, and data flows across codebases.
**Languages:** Go, C++

| Task | Difficulty | Description |
|------|-----------|-------------|
| api_upgrade_01 | hard | Migrate deprecated gRPC Dial calls across etcd, kubernetes, containerd |
| bug_localization_01 | hard | Trace cross-library dtype bug across numpy, pandas, scikit-learn |
| cross_file_reasoning_01 | hard | Trace Kubernetes CRI to containerd implementation |
| crossrepo-chain-001 | very_hard | Multi-hop dependency chain analysis |
| crossrepo-chain-002 | very_hard | Multi-hop dependency chain analysis |
| crossrepo-impl-001 | hard | Cross-repo implementation task |
| crossrepo-impl-002 | hard | Cross-repo implementation task |
| crossrepo-sym-001 | hard | Cross-repo symbol tracing |
| crossrepo-sym-002 | hard | Cross-repo symbol tracing (C++) |
| crossrepo-sym-003 | hard | Cross-repo symbol tracing |
| refactor_rename_01 | hard | Standardize HTTP Request class naming across Django, Flask, requests |
| simple_test_01 | easy | Pipeline smoke test |

---

## 5. Enterprise -- Enterprise Codebase Challenges

**Focus:** Enterprise-grade challenges involving dependency discovery, impact analysis, multi-team ownership, knowledge fragmentation, and legacy dependencies.
**Languages:** Go, Python | **Difficulty:** hard (all tasks)

| Task | Language | Category |
|------|----------|----------|
| conflicting-docs-001 | Python | Conflicting documentation resolution |
| dep-discovery-001 | Go | Dependency discovery |
| dep-impact-001 | Python | Dependency impact analysis |
| dep-refactor-001 | Go | Dependency refactoring |
| dep-refactor-002 | Go | Dependency refactoring |
| institutional-memory-001 | Python | Institutional memory recovery |
| knowledge-fragmentation-001 | Python | Knowledge fragmentation |
| legacy-dependency-001 | Python | Legacy dependency management |
| multi-team-ownership-001 | Python | Multi-team ownership |
| multi-team-ownership-002 | Go | Multi-team ownership |
| polyglot-ecosystem-001 | Go | Polyglot ecosystem analysis |
| stale-architecture-001 | Python | Stale architecture assessment |

---

## 6. PyTorch -- PyTorch PR-Level Tasks

**Focus:** Reproduce actual PyTorch pull request changes -- bug fixes and feature additions in the compiler, runtime, and distributed systems.
**Language:** C++ (PyTorch internals) | **Repository:** pytorch/pytorch | **Time Limit:** 10 min per task

| Task | Difficulty | Category | MCP Score |
|------|-----------|----------|-----------|
| sgt-001 | medium | bug fix | 0.553 |
| sgt-002 | medium | bug fix | 0.568 |
| sgt-003 | hard | bug fix | 0.583 |
| sgt-005 | medium | feature | 0.555 |
| sgt-008 | hard | bug fix | 0.808 |
| sgt-009 | medium | bug fix | 0.553 |
| sgt-010 | hard | bug fix | 0.613 |
| sgt-012 | medium | bug fix | 0.553 |
| sgt-014 | medium | bug fix | 0.568 |
| sgt-016 | medium | bug fix | 0.553 |
| sgt-021 | medium | bug fix | 0.568 |

---

## 7. NavProve -- Navigation & Provenance Reasoning

**Focus:** Navigate through complex codebases to trace provenance, locate behaviors, and prove hypotheses about code behavior. Tests deep code comprehension and navigation ability.
**Difficulty:** hard (all tasks) | **SDLC Phase:** Debugging

| Task | Language | Repository Context |
|------|----------|--------------------|
| navprove-ansible-vault-001 | Python | ansible/ansible |
| navprove-flipt-cache-001 | Go | flipt-io/flipt |
| navprove-qb-bookmark-001 | Python | qutebrowser/qutebrowser |
| navprove-qb-download-001 | Python | qutebrowser/qutebrowser |
| navprove-qb-tab-001 | Python | qutebrowser/qutebrowser |
| navprove-qb-url-001 | Python | qutebrowser/qutebrowser |
| navprove-teleport-ssh-001 | Go | gravitational/teleport |
| navprove-tutanota-search-001 | TypeScript | tutao/tutanota |
| navprove-vuls-oval-001 | Go | future-architect/vuls |

---

## 8. CodeReview -- AI Code Review

**Focus:** Review real pull requests with injected defects -- find bugs, compliance violations, and fix them. Tests both detection accuracy and fix quality using hybrid scoring.
**Difficulty:** hard (all tasks) | **SDLC Phase:** Testing & QA

| Task | Language | MCP Score |
|------|----------|-----------|
| cr-aspnetcore-001 | C# | 0.840 |
| cr-calcom-001 | TypeScript | 0.830 |
| cr-envoy-001 | C++ | 0.720 |
| cr-ghost-001 | JavaScript | 0.820 |
| cr-security-001 | C | 0.720 |
| cr-security-002 | Java | 0.720 |
| cr-terraform-001 | Go | 0.720 |
| cr-vscode-001 | TypeScript | 0.720 |

Each task clones a real open-source repository at a pinned PR merge commit, then injects realistic defects across multiple source files. The agent must detect defects (producing structured `review.json`) and fix them (committing corrected code).

**Scoring:** `0.5 * detection_F1 + 0.5 * fix_score`

---

## 9. DIBench -- Dependency Installation

**Focus:** Infer and add missing dependencies to build files by analyzing source code imports. The agent must not modify source code -- only edit dependency configuration files.
**Difficulty:** medium (all tasks)

| Task | Language | Project | Build File |
|------|----------|---------|------------|
| dibench-csharp-dotnetkoans | C# | DotNetKoans | `DotNetKoans.csproj` |
| dibench-csharp-irongut-codecoveragesummary | C# | irongut/CodeCoverageSummary | `CodeCoverageSummary.csproj` |
| dibench-js-eslint-markdown | JavaScript | eslint/markdown | `package.json` |
| dibench-js-motdotla-dotenv-expand | JavaScript | motdotla/dotenv-expand | `package.json` |
| dibench-python-inducer-cgen | Python | inducer/cgen | `pyproject.toml` |
| dibench-python-rhinosec-iamactionhunter | Python | RhinoSecurityLabs/IAMActionHunter | `pyproject.toml` |
| dibench-rust-mitsuhiko-similar-asserts | Rust | mitsuhiko/similar-asserts | `Cargo.toml` |
| dibench-rust-rusticata-pcap-parser | Rust | rusticata/pcap-parser | `Cargo.toml` |

---

## 10. Governance -- Access Control & Policy Enforcement

**Focus:** Implement and enforce access control, audit trails, and policy enforcement in codebases that require security-conscious development patterns.
**Languages:** Go, Python

| Task | Language | Difficulty | Focus |
|------|----------|-----------|-------|
| audit-trail-001 | Python | hard | Audit trail implementation |
| cross-team-boundary-001 | Python | hard | Cross-team boundary enforcement |
| degraded-context-001 | Go | hard | Degraded context handling |
| policy-enforcement-001 | Python | hard | Policy enforcement |
| repo-scoped-access-001 | Python | medium | Repository-scoped access |
| repo-scoped-access-002 | Go | hard | Repository-scoped access |
| role-based-access-001 | Python | hard | Role-based access control |
| sensitive-file-exclusion-001 | Python | medium | Sensitive file exclusion |

---

## 11. NLQA -- Natural-Language Code Q&A

**Focus:** Answer natural-language questions about code architecture, data flow, and debugging scenarios. Tests deep comprehension and the ability to explain code behavior.
**Languages:** Go, C++, Java, TypeScript | **Difficulty:** hard (all tasks)

| Task | Language | Category |
|------|----------|----------|
| nlqa-arch-001 | C++ | Architecture question |
| nlqa-arch-002 | Go | Architecture question |
| nlqa-arch-003 | Go | Architecture question |
| nlqa-debug-001 | TypeScript | Debugging question |
| nlqa-debug-002 | Go | Debugging question |
| nlqa-flow-001 | Java | Data flow question |
| nlqa-flow-002 | C++ | Data flow question |
| nlqa-flow-003 | Go | Data flow question |

---

## 12. Onboarding -- Codebase Onboarding

**Focus:** Onboarding to unfamiliar codebases: understanding team handoffs, orienting within large projects, and grasping development workflows.
**Languages:** Go, C++, Java | **Difficulty:** hard (all tasks) | **SDLC Phase:** Requirements & Discovery

| Task | Language | Category |
|------|----------|----------|
| onboard-handoff-001 | C++ | Team handoff comprehension |
| onboard-handoff-002 | Go | Team handoff comprehension |
| onboard-handoff-003 | Go | Team handoff comprehension |
| onboard-orient-001 | Go | Codebase orientation |
| onboard-orient-002 | Go | Codebase orientation |
| onboard-orient-003 | Java | Codebase orientation |
| onboard-workflow-001 | C++ | Workflow understanding |
| onboard-workflow-002 | Java | Workflow understanding |

---

## 13. Security -- Security Analysis

**Focus:** CVE analysis, reachability assessment, and transitive dependency security analysis. Tests the agent's ability to reason about security vulnerabilities in real codebases.
**Languages:** Go, C, C++, Java | **Difficulty:** hard (all tasks) | **SDLC Phase:** Requirements & Discovery

| Task | Language | Category |
|------|----------|----------|
| sec-cve-001 | C | CVE analysis |
| sec-cve-002 | C++ | CVE analysis |
| sec-cve-003 | Go | CVE analysis |
| sec-reach-001 | C | Reachability assessment |
| sec-reach-002 | C++ | Reachability assessment |
| sec-reach-003 | Java | Reachability assessment |
| sec-transitive-001 | Go | Transitive dependency analysis |
| sec-transitive-002 | Go | Transitive dependency analysis |

---

## 14. TAC -- The Agent Company

**Focus:** Tasks from The Agent Company (TAC) benchmark, requiring agents to use external tools, navigate unfamiliar repositories, and interact with services (GitLab, RocketChat) beyond just editing code.
**Prerequisites:** TAC server infrastructure (GitLab, RocketChat, API server). See `benchmarks/ccb_tac/README.md` for setup.

| Task | Language | Difficulty | Category | MCP Score |
|------|----------|-----------|----------|-----------|
| tac-buffer-pool-manager | C++ | hard | implement | 0.490 |
| tac-dependency-change | Python | medium | dependency | 0.440 |
| tac-find-in-codebase-1 | C++ | medium | find-in-codebase | 0.575 |
| tac-find-in-codebase-2 | C++ | medium | find-in-codebase | 0.575 |
| tac-implement-hyperloglog | C++ | hard | implement | 0.490 |
| tac-write-unit-test | Python | medium | unit-test | 0.465 |

**Excluded tasks (2):**
- `tac-copilot-arena-endpoint` -- copilot-arena-server repo not present in TAC GitLab backup data
- `tac-troubleshoot-dev-setup` -- same repo dependency; task fails at clone

---

## 15. LinuxFLBench -- Linux Kernel Fault Localization

**Focus:** Locate the root cause of real Linux kernel bugs from Bugzilla reports. The agent must identify the exact source file(s) and function(s) responsible for hardware/driver failures across kernel subsystems.
**Language:** C | **Difficulty:** expert (all tasks) | **Time Limit:** 30 min per task
**Repository:** linux (kernel source tree) | **Build Timeout:** 30 min (kernel partial clone ~2GB)

| Task | Subsystem | Description |
|------|-----------|-------------|
| lfl-acpi-207835 | ACPI | Backlight brightness control does not work on Acer TravelMate 5735Z |
| lfl-nfs-117651 | NFS | Root NFS and autofs mount disappears due to inode revalidate failure |
| lfl-sata-203475 | SATA | Samsung 860 EVO queued TRIM causes timeout errors in libata |
| lfl-sound-53441 | Sound | HDA Intel sound stops working after suspend to RAM |
| lfl-wifi-206661 | WiFi | iwlwifi missing PCI subdevice entries causing firmware load failure |

---

## 16. Investigation -- Deep Investigation

**Focus:** Deep debugging, interaction tracing, and impact analysis requiring thorough codebase investigation. Tests the agent's ability to follow complex logic paths and produce accurate analysis.
**Languages:** Go, Python | **SDLC Phase:** Requirements & Discovery

| Task | Language | Difficulty | Focus |
|------|----------|-----------|-------|
| inv-debug-001 | Go | hard | Deep debugging |
| inv-impact-001 | Go | hard | Impact analysis |
| inv-migration-001 | Python | medium | Migration investigation |
| inv-regression-001 | Go | hard | Regression investigation |

---

## 17. SWE-Perf -- Performance Optimization

**Focus:** Optimize specific functions in major Python scientific computing libraries. Agents must profile, identify bottlenecks, and apply targeted optimizations while preserving correctness.
**Language:** Python | **Agent Timeout:** 60 min | **Verifier Timeout:** 10 min

| Task | Repository | Target Function | Difficulty | MCP Score |
|------|-----------|----------------|-----------|-----------|
| sweperf-001 | NumPy | `numpy.core.multiarray.array_sum` | medium | 0.458 |
| sweperf-002 | scikit-learn | `sklearn.cluster._k_means._kmeans_single_elkan` | hard | 0.458 |
| sweperf-003 | Pandas | `pandas.core.groupby.ops.GroupBy._aggregate_series_fast` | medium | 0.458 |

**Scoring:** `runtime_reduction = 1 - (optimized_runtime / baseline_runtime)`. A score of 0.5 means 2x speedup.

---

## Appendix: Archived Suites

The following suites are archived and not included in official evaluation. Task definitions are preserved for reference in `benchmarks/archive/`.

### LoCoBench (25 tasks, ARCHIVED)
**Reason:** Removed from official evaluation.
**Focus:** Expert-level tasks on synthetically generated codebases with 1M+ tokens across 75-85 files. Tests architectural reasoning, cross-file refactoring, and bug investigation at scale.
**Languages:** C, C++, C#, Python, Rust, TypeScript | **Difficulty:** expert

### RepoQA (10 tasks, ARCHIVED)
**Reason:** Ceiling saturation -- scores 1.000/1.000 on both baseline and SG_full configs.
**Focus:** Find functions by behavioral description alone. Tests semantic search capability.
**Languages:** Python, C++, Java, Rust, TypeScript | **Difficulty:** hard

### DependEval (32 tasks, ARCHIVED)
**Reason:** Superseded by ccb_dibench and ccb_enterprise dependency tasks.
**Focus:** Identify and correctly order dependencies in real-world repositories.
**Languages:** Java, JavaScript, Python, TypeScript | **Difficulty:** medium

### K8s Docs (5 tasks, ARCHIVED)
**Reason:** Superseded by ccb_docgen with broader language and task-type coverage.
**Focus:** Generate doc.go package documentation for Kubernetes packages.
**Language:** Go

---

## Summary Statistics

| Benchmark | Tasks | Difficulty Range | Language(s) | Avg MCP Score |
|-----------|-------|-----------------|-------------|---------------|
| SWE-bench Pro | 36 | hard | Go, TS, Python, JS | 0.660 |
| LargeRepo | 25 | hard | Go, Rust, Python/C++, Java, C, TS | 0.882 |
| DocGen | 13 | hard | Go, C++, Java, TS | 0.855 |
| CrossRepo | 12 | easy - very_hard | Go, C++ | 0.873 |
| Enterprise | 12 | hard | Go, Python | 0.850 |
| PyTorch | 11 | medium - hard | C++ | 0.588 |
| NavProve | 9 | hard | Go, Python, TS | 0.824 |
| CodeReview | 8 | hard | 7 languages | 0.761 |
| DIBench | 8 | medium | Python, Rust, JS, C# | -- |
| Governance | 8 | medium - hard | Go, Python | 0.805 |
| NLQA | 8 | hard | Go, C++, Java, TS | 0.839 |
| Onboarding | 8 | hard | Go, C++, Java | 0.826 |
| Security | 8 | hard | Go, C, C++, Java | 0.869 |
| TAC | 8 | medium - hard | C++, Python | 0.506 |
| LinuxFLBench | 5 | expert | C | -- |
| Investigation | 4 | medium - hard | Go, Python | 0.903 |
| SWE-Perf | 3 | medium - hard | Python | 0.458 |

**Total active tasks:** 186
**Languages covered:** C, C++, C#, Go, Java, JavaScript, Python, Rust, TypeScript
**SDLC phases covered:** Requirements & Discovery, Architecture & Design, Implementation (feature, bug fix, refactoring), Testing & QA, Documentation, Maintenance, Security review, Impact analysis, Debugging
