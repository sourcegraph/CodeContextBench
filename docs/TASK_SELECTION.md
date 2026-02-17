# Task Selection Methodology

## Overview

Selected **186 tasks** across 17 active benchmarks, stratified by SDLC phase with MCP benefit scoring. An additional 30 tasks from archived suites (ccb_locobench, ccb_k8sdocs) remain in `selected_benchmark_tasks.json` for historical reference but are excluded from official evaluation.

## SDLC Phase Coverage

| SDLC Phase | Tasks | Benchmarks |
|------------|-------|------------|
| Requirements & Discovery | 28 | ccb_investigation, ccb_nlqa, ccb_onboarding, ccb_security, ccb_tac, ccb_crossrepo |
| Architecture & Design | 5 | ccb_crossrepo |
| Implementation (feature) | 30 | ccb_largerepo, ccb_pytorch, ccb_tac, ccb_dibench, ccb_enterprise, ccb_governance |
| Implementation (bug fix) | 54 | ccb_pytorch, ccb_swebenchpro, ccb_crossrepo, ccb_enterprise, ccb_governance, ccb_linuxflbench |
| Implementation (refactoring) | 4 | ccb_crossrepo, ccb_enterprise |
| Analysis & Debugging | 26 | ccb_navprove, ccb_nlqa, ccb_largerepo |
| Testing & QA | 14 | ccb_sweperf, ccb_tac, ccb_codereview |
| Documentation | 13 | ccb_docgen |
| Planning (impact analysis) | 4 | ccb_enterprise |
| Maintenance | 2 | ccb_tac |
| Security review | 6 | ccb_largerepo, ccb_security |

## Benchmark Coverage

| Benchmark | Selected | Strategy |
|-----------|----------|----------|
| ccb_swebenchpro | 36 | Proportional by repo, prefer most files changed |
| ccb_largerepo | 25 | Expanded from original 4 with new repos and task types |
| ccb_docgen | 13 | All selected (supersedes ccb_k8sdocs with broader scope) |
| ccb_crossrepo | 12 | Expanded from original 5 with additional task types |
| ccb_enterprise | 12 | All selected (new suite) |
| ccb_pytorch | 11 | Prefer hard difficulty, then most files modified |
| ccb_navprove | 9 | All selected (new suite) |
| ccb_codereview | 8 | All selected (expanded from original 3) |
| ccb_dibench | 8 | 2 per language (python, rust, javascript, csharp) |
| ccb_governance | 8 | All selected (new suite) |
| ccb_nlqa | 8 | All selected (new suite) |
| ccb_onboarding | 8 | All selected (new suite) |
| ccb_security | 8 | All selected (new suite) |
| ccb_tac | 8 | All selected (small benchmark) |
| ccb_linuxflbench | 5 | All selected (small benchmark) |
| ccb_investigation | 4 | All selected (new suite) |
| ccb_sweperf | 3 | All selected (small benchmark) |

## Language Distribution

| Language | Tasks |
|----------|-------|
| go | 60+ |
| python | 30+ |
| cpp/c | 25+ |
| java | 20+ |
| typescript | 15+ |
| javascript | 10+ |
| rust | 5+ |
| csharp | 5+ |

## MCP Benefit Scoring

Each task receives an MCP benefit score in [0.0, 1.0] computed as:

```
score = 0.25 * context_complexity
      + 0.30 * cross_file_deps
      + 0.20 * semantic_search_potential
      + 0.25 * task_category_weight
```

### Component Definitions

- **context_complexity**: Derived from codebase token count or benchmark-level proxy. Normalized: 1M+ tokens = 1.0
- **cross_file_deps**: From `files_count`, `solution_files_changed`, or parsed from instruction.md. Normalized: 20+ files = 1.0
- **semantic_search_potential**: High for large repos (ccb_largerepo=0.9), find-in-codebase tasks (0.8), large context (0.7)
- **task_category_weight**: Per-category MCP affinity (architectural_understanding=1.0, cross_file_refactoring=0.9, etc.)

## Per-Benchmark Selection Strategies

### SWE-Bench Pro (~36 tasks)
Proportional allocation by repository, ensuring at least 1 task per repo. Within each repo, tasks with the most files changed in their solution patch are preferred. Language corrections applied (e.g., NodeBB -> javascript, navidrome -> go). Diversity check ensures >=3 tasks each for Go, TypeScript, and JavaScript language families.

### GitHub Mined / PyTorch (~11 tasks)
All PyTorch cross-module tasks. Selection prioritizes hard difficulty, then tasks with the most files modified in the ground truth PR.

### DI-Bench (8 tasks)
2 per language (Python, Rust, JavaScript, C#) from the 387 regular-difficulty instances. Selected for single build file, moderate patch size (3-12 dependency additions), and well-known repositories. Tasks use syntax + dependency presence validators instead of full CI/CD execution.

### Small Benchmarks (all selected)
ccb_linuxflbench (5), ccb_tac (8), ccb_sweperf (3), ccb_investigation (4) -- all tasks selected due to small size.

### New Suites (all selected)
ccb_docgen (13), ccb_enterprise (12), ccb_governance (8), ccb_navprove (9), ccb_nlqa (8), ccb_onboarding (8), ccb_security (8) -- all tasks selected.

## Archived Suites

The following suites are no longer part of official evaluation:

- **ccb_locobench** (25 tasks) -- Removed from official evaluation
- **ccb_repoqa** (10 tasks) -- Ceiling saturation (1.000/1.000 baseline vs SG_full)
- **ccb_k8sdocs** (5 tasks) -- Superseded by ccb_docgen
- **ccb_dependeval** (32 tasks) -- Superseded by ccb_dibench and ccb_enterprise dependency tasks
