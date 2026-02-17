# CodeContextBench Benchmarks

This directory contains all benchmark task definitions for evaluating coding agents with and without Sourcegraph MCP. The canonical task selection is defined in [`selected_benchmark_tasks.json`](../configs/selected_benchmark_tasks.json) (186 tasks across 17 active benchmarks). Archived suites are in `archive/`.

See [`docs/TASK_SELECTION.md`](../docs/TASK_SELECTION.md) for the selection methodology.

---

## Active Benchmarks

### 1. [ccb_swebenchpro/](ccb_swebenchpro/) - Multi-Language Bug Fixing
**Tasks**: 36
**Languages**: Go, TypeScript, Python, JavaScript
**SDLC Phase**: Implementation (bug fix)
**Focus**: Long-horizon software engineering on production codebases
**Repositories**: flipt-io/flipt, tutao/tutanota, internetarchive/openlibrary, ansible/ansible, and more
**Task Format**: Harbor (via adapter, pre-generated)

---

### 2. [ccb_largerepo/](ccb_largerepo/) - Large Codebase Navigation
**Tasks**: 25
**Languages**: Go, Rust, C/C++, Java, Python, TypeScript
**SDLC Phases**: Feature implementation, Analysis, Debugging, Refactoring, Security review
**Focus**: Feature implementation, analysis, and debugging in very large codebases (1GB+)
**Repositories**: Kubernetes, Servo, TensorRT-LLM, VS Code, Django, Kafka, PostgreSQL, and more
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 3. [ccb_docgen/](ccb_docgen/) - Documentation Generation
**Tasks**: 13
**Languages**: Go, C++, Java, TypeScript
**SDLC Phase**: Documentation
**Focus**: Generate accurate API documentation, architecture guides, and migration plans by reading source code. Supersedes `ccb_k8sdocs` with broader language and task-type coverage.
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 4. [ccb_crossrepo/](ccb_crossrepo/) - Cross-Repository Reasoning
**Tasks**: 12
**Languages**: Go, C++
**SDLC Phases**: Architecture & Design, Bug fix, Refactoring, Discovery, Testing & QA
**Focus**: API migration, bug localization, cross-file reasoning, and symbol tracing across multiple repositories
**Task Format**: Harbor (task.toml, instruction.md, tests/)
**Note**: Requires `harbor-ccb_crossrepo:base` Docker image built from `base/` directory.

---

### 5. [ccb_enterprise/](ccb_enterprise/) - Enterprise Codebase Challenges
**Tasks**: 12
**Languages**: Go, Python
**SDLC Phases**: Impact analysis, Feature implementation, Bug fix, Refactoring
**Focus**: Enterprise-grade challenges: dependency discovery, impact analysis, multi-team ownership, knowledge fragmentation, legacy dependencies
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 6. [ccb_pytorch/](ccb_pytorch/) - Real PyTorch Pull Requests
**Tasks**: 11
**Languages**: C++ (PyTorch)
**SDLC Phase**: Implementation (bug fix, feature)
**Focus**: Multi-file code changes on real production codebase
**Repository**: PyTorch (pytorch/pytorch)
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 7. [ccb_navprove/](ccb_navprove/) - Navigation & Provenance Reasoning
**Tasks**: 9
**Languages**: Go, Python, TypeScript
**SDLC Phase**: Debugging
**Focus**: Navigation through complex codebases to trace provenance, locate behaviors, and prove hypotheses about code behavior
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 8. [ccb_codereview/](ccb_codereview/) - AI Code Review
**Tasks**: 8
**Languages**: C, C++, C#, Go, Java, JavaScript, TypeScript
**SDLC Phase**: Testing & QA
**Focus**: Review real pull requests with injected defects -- find bugs, compliance violations, and fix them
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 9. [ccb_dibench/](ccb_dibench/) - Dependency Inference
**Tasks**: 8
**Languages**: Python, Rust, JavaScript, C#
**SDLC Phase**: Implementation (feature)
**Focus**: Infer and configure missing dependencies in build files by analyzing source code
**Source**: Microsoft DI-Bench (https://github.com/microsoft/DI-Bench)
**Task Format**: Harbor (task.toml, instruction.md, tests/)
**Note**: Each task includes the full project repo with dependencies stripped from build files.

---

### 10. [ccb_governance/](ccb_governance/) - Access Control & Policy Enforcement
**Tasks**: 8
**Languages**: Go, Python
**SDLC Phases**: Implementation (feature, bug fix)
**Focus**: Repo-scoped access control, audit trails, policy enforcement, cross-team boundaries, sensitive file exclusion
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 11. [ccb_nlqa/](ccb_nlqa/) - Natural-Language Code Q&A
**Tasks**: 8
**Languages**: Go, C++, Java, TypeScript
**SDLC Phases**: Debugging, Requirements & Discovery
**Focus**: Answer natural-language questions about code architecture, data flow, and debugging scenarios
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 12. [ccb_onboarding/](ccb_onboarding/) - Codebase Onboarding
**Tasks**: 8
**Languages**: Go, C++, Java
**SDLC Phase**: Requirements & Discovery
**Focus**: Onboarding to unfamiliar codebases: orientation, handoff comprehension, workflow understanding
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 13. [ccb_security/](ccb_security/) - Security Analysis
**Tasks**: 8
**Languages**: Go, C, C++, Java
**SDLC Phase**: Requirements & Discovery
**Focus**: CVE analysis, reachability assessment, and transitive dependency security analysis
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 14. [ccb_tac/](ccb_tac/) - TheAgentCompany Tasks
**Tasks**: 8
**Languages**: C++, Python
**SDLC Phases**: Requirements & Discovery, Implementation (feature), Testing & QA, Maintenance
**Focus**: Diverse SDE tasks (codebase search, implementation, unit testing, troubleshooting)
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 15. [ccb_linuxflbench/](ccb_linuxflbench/) - Linux Kernel Fault Localization
**Tasks**: 5
**Languages**: C
**SDLC Phase**: Implementation (bug fix)
**Focus**: Locate root cause of real Linux kernel bugs from Bugzilla reports
**Task Format**: Harbor (task.toml, instruction.md, tests/)
**Note**: Docker image build is slow (~10 min) due to Linux kernel partial clone (~2GB).

---

### 16. [ccb_investigation/](ccb_investigation/) - Deep Investigation
**Tasks**: 4
**Languages**: Go, Python
**SDLC Phase**: Requirements & Discovery
**Focus**: Deep debugging, interaction tracing, and impact analysis requiring thorough codebase investigation
**Task Format**: Harbor (task.toml, instruction.md, tests/)

---

### 17. [ccb_sweperf/](ccb_sweperf/) - Performance Testing
**Tasks**: 3
**Languages**: Python
**SDLC Phase**: Testing & QA
**Focus**: Performance-oriented software engineering tasks
**Task Format**: Harbor (via adapter, pre-generated)

---

## Benchmark Summary

| Benchmark | Tasks | Languages | SDLC Phase |
|-----------|------:|-----------|------------|
| ccb_swebenchpro | 36 | Go, TypeScript, Python, JavaScript | Bug fixing |
| ccb_largerepo | 25 | Go, Rust, C/C++, Java, Python, TypeScript | Feature impl, Analysis, Security |
| ccb_docgen | 13 | Go, C++, Java, TypeScript | Documentation |
| ccb_crossrepo | 12 | Go, C++ | Architecture, Bug fix, Refactoring |
| ccb_enterprise | 12 | Go, Python | Impact analysis, Feature impl, Bug fix |
| ccb_pytorch | 11 | C++ | Bug fixing, Feature impl |
| ccb_navprove | 9 | Go, Python, TypeScript | Debugging |
| ccb_codereview | 8 | 7 languages | Testing & QA |
| ccb_dibench | 8 | Python, Rust, JavaScript, C# | Dependency inference |
| ccb_governance | 8 | Go, Python | Feature impl, Bug fix |
| ccb_nlqa | 8 | Go, C++, Java, TypeScript | Debugging, Discovery |
| ccb_onboarding | 8 | Go, C++, Java | Discovery |
| ccb_security | 8 | Go, C, C++, Java | Discovery |
| ccb_tac | 8 | C++, Python | Mixed (4 phases) |
| ccb_linuxflbench | 5 | C | Fault localization |
| ccb_investigation | 4 | Go, Python | Discovery |
| ccb_sweperf | 3 | Python | Testing & QA |
| **Total** | **186** | | |

---

## Archived Benchmarks

Archived suites are not included in official evaluation. Task files are preserved for reference.

### [archive/ccb_dependeval/](archive/ccb_dependeval/) - Dependency Ordering (ARCHIVED)
**Reason**: Superseded by ccb_dibench and ccb_enterprise dependency tasks.
**Tasks**: 32 | **Languages**: Java, JavaScript, Python, TypeScript

### [archive/ccb_repoqa/](archive/ccb_repoqa/) - Semantic Code Navigation (ARCHIVED)
**Reason**: Ceiling saturation -- scores 1.000/1.000 on both baseline and SG_full configs, providing zero discriminative signal.
**Tasks**: 10 | **Languages**: Python, C++, Java, Rust, TypeScript

### [archive/ccb_k8sdocs/](archive/ccb_k8sdocs/) - K8s Documentation (ARCHIVED)
**Reason**: Superseded by ccb_docgen, which provides broader language coverage and more task types.
**Tasks**: 5 | **Languages**: Go

### [archive/ccb_locobench/](archive/ccb_locobench/) - Long-Context Agent Tasks (ARCHIVED)
**Reason**: Removed from official evaluation.
**Tasks**: 25 | **Languages**: C, C++, C#, Python, Rust, TypeScript

---

## Running Benchmarks

### 3-Config Comparison (Recommended)

Each benchmark has a shell runner in [`configs/`](../configs/) that executes selected tasks across the 3-config matrix (Baseline, MCP-Base, MCP-Full):

```bash
# Run all selected tasks for all benchmarks
bash configs/run_selected_tasks.sh

# Run only baseline config
bash configs/run_selected_tasks.sh --baseline-only

# Per-suite example
bash configs/swebenchpro_2config.sh
bash configs/largerepo_2config.sh
bash configs/docgen_2config.sh
```

### Single Task Run

```bash
harbor run --path benchmarks/ccb_largerepo/big-code-vsc-001 \
  --agent-import-path agents.claude_baseline_agent:BaselineClaudeCodeAgent \
  --model anthropic/claude-haiku-4-5-20251001 \
  -n 1
```

See [`docs/CONFIGS.md`](../docs/CONFIGS.md) for the full tool-by-tool breakdown of each config.

---

## Results & Analysis

After running benchmarks, generate evaluation reports:

```bash
python3 scripts/generate_eval_report.py \
  --runs-dir /path/to/runs/official/ \
  --output-dir ./eval_reports/
```

See the root [README.md](../README.md) for the full metrics extraction pipeline.
