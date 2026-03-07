# Task Selection Methodology

## Overview

Selected **0 tasks** from 0 available across 7 benchmarks, stratified by SDLC phase with MCP benefit scoring.

## SDLC Phase Coverage

| SDLC Phase | Tasks | Benchmarks |
|------------|-------|------------|
| Requirements & Discovery | 0 |  |
| Architecture & Design | 0 |  |
| Implementation (feature) | 0 |  |
| Implementation (bug fix) | 0 |  |
| Implementation (refactoring) | 0 |  |
| Testing & QA | 0 |  |
| Documentation | 0 |  |
| Maintenance | 0 |  |

## Benchmark Coverage

| Benchmark | Available | Selected | Strategy |
|-----------|-----------|----------|----------|
| csb_sdlc_k8sdocs | — | 0 | All selected (small benchmark) |
| csb_sdlc_largerepo | — | 0 | All selected (small benchmark) |
| csb_sdlc_locobench | — | 0 | Priority: arch > refactoring > bug, by MCP score |
| csb_sdlc_pytorch | — | 0 | Prefer hard difficulty, then most files modified |
| csb_sdlc_swebenchpro | — | 0 | Proportional by repo, prefer most files changed |
| csb_sdlc_sweperf | — | 0 | All selected (small benchmark) |
| csb_sdlc_tac | — | 0 | All selected (small benchmark) |

## Language Distribution

| Language | Tasks |
|----------|-------|

## Difficulty Distribution

CodeScaleBench tasks are intentionally concentrated at the hard and expert difficulty levels because the benchmark targets enterprise-scale software engineering scenarios that challenge frontier AI agents.

| Difficulty | Count | Percentage |
|-----------|-------|------------|
| hard      | 371   | 91.8%      |
| expert    | 21    | 5.2%       |
| medium    | 12    | 3.0%       |
| **Total** | **404** | **100%** |

### Why 97% Hard or Expert

1. **Enterprise-scale targeting**: Tasks are drawn from large, real-world codebases (1GB+) where even locating the relevant code requires significant reasoning. Easy tasks in these repositories would not meaningfully differentiate agent capabilities.

2. **Cross-file and cross-repo complexity**: Most tasks require navigating multiple files or repositories, understanding dependency chains, and synthesizing information across codebases.

3. **Ceiling avoidance**: If tasks were easier, current agents would score near-perfectly, leaving no room to measure improvement. Hard tasks ensure the benchmark remains discriminative as agent capabilities advance.

4. **Org-suite uniformity**: The 11 organization-scale suites (csb_org_*) are uniformly hard because they all involve multi-repository analysis, compliance audits, incident investigation, or migration planning.

5. **SDLC-suite variance**: The 9 SDLC suites have more difficulty diversity (medium through expert) because they include both single-repo bug fixes (some medium) and complex architectural tasks (expert).

## MCP Benefit Scoring

Each task receives an MCP benefit score in [0.0, 1.0] computed as:

```
score = 0.25 * context_complexity
      + 0.30 * cross_file_deps
      + 0.20 * semantic_search_potential
      + 0.25 * task_category_weight
```

**Average MCP benefit score:** 0.0000

### Component Definitions

- **context_complexity**: Derived from codebase token count (LoCoBench `context_length`) or benchmark-level proxy. Normalized: 1M+ tokens = 1.0
- **cross_file_deps**: From `files_count`, `solution_files_changed`, or parsed from instruction.md. Normalized: 20+ files = 1.0
- **semantic_search_potential**: High for large repos (csb_sdlc_largerepo=0.9), find-in-codebase tasks (0.8), large context (0.7)
- **task_category_weight**: Per-category MCP affinity (architectural_understanding=1.0, cross_file_refactoring=0.9, etc.)

## Per-Benchmark Selection Strategies

### SWE-Bench Pro (~35 tasks)
Proportional allocation by repository, ensuring at least 1 task per repo. Within each repo, tasks with the most files changed in their solution patch are preferred. Language corrections applied (e.g., NodeBB -> javascript, navidrome -> go). Diversity check ensures >=3 tasks each for Go, TypeScript, and JavaScript language families.

### LoCoBench Agent (~25 tasks)
All bug_investigation tasks (3) selected first, then all cross_file_refactoring (13), then top architectural_understanding tasks by MCP score to fill remaining budget. All tasks have >700K token context and 70+ files.

### GitHub Mined (~12 tasks)
All PyTorch cross-module tasks. Selection prioritizes hard difficulty, then tasks with the most files modified in the ground truth PR.

### Small Benchmarks (all selected)
csb_sdlc_largerepo (4), csb_sdlc_k8sdocs (5), csb_sdlc_tac (8), csb_sdlc_sweperf (3) — all tasks selected due to small size.

