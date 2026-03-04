# CodeScaleBench: Testing Coding Agents on Large Codebases and Multi-Repo Software Engineering Tasks

_Alternate title: "Existing benchmarks are weak for evaluating enterprise-scale coding agents, so I built my own."_  

In January I wrote about my frustrations with coding-agent benchmarks and why most of them do not answer the practical questions I care about. CodeScaleBench is the result: a benchmark designed to test coding agents on large codebases, multi-repo workflows, and tasks across the full software development lifecycle (SDLC), not just bug-fix micro-slices.

## Why I Built This

Most benchmark suites are strong in one narrow direction and weak in the rest:
- small or single-repo scope
- mostly one language family (often Python-heavy)
- weak or gameable verification
- poor auditability (limited or no transcript-level inspection)
- leaderboard-friendly summaries that hide important failure modes

What I wanted:
1. Large codebases (ideally 1M+ LOC, including very large repos).
2. Multi-language coverage.
3. Multi-repo tasks.
4. SDLC coverage: understand, design, feature, fix, test, docs, refactor, secure, debug.
5. Retrieval-aware evaluation (did the agent find the right context, and did that help?).

## What CodeScaleBench Is

CodeScaleBench is currently:
- **370 paired tasks total**
- **CodeScaleBench-SDLC**: 150 tasks across SDLC phases (direct code/task verifiers)
- **CodeScaleBench-Org**: 220 org-scale discovery tasks (artifact verifier on `answer.json`)
- **9 languages** across **40+ repositories**

Two run conditions per task:
- **Baseline**: local code + standard local tools
- **MCP-augmented**: no local source, Sourcegraph MCP tools required

This is intentionally conservative for MCP: baseline has complete local access, while MCP must retrieve context remotely.

## Setup Summary

I evaluate the same task under baseline vs MCP to isolate retrieval/access-method effects.

For MCP runs:
- repositories are mirrored at pinned commits to ensure exact-version retrieval
- the agent gets Sourcegraph MCP tools (keyword search, semantic search, symbol navigation, dependency tracing, file reads, etc.)

## What I Adapted vs. What I Dropped

| Benchmark | Status | Notes |
|---|---|---|
| SWE-Bench Pro | Adapted | Useful issue-resolution tasks across languages. |
| LinuxFLBench | Adapted | Large-codebase fault-localization stress tests. |
| Qodo Code Review | Adapted | Used with synthetic defect injection. |
| TheAgentCompany | Adapted | One task retained (`bustub-hyperloglog-impl-001`). |
| RepoQA | Concepts reused | Ceiling saturation; replaced by harder large-repo tasks. |
| ContextBench | Used for curation | Used to calibrate curator-agent GT automation. |
| DIBench / DependEval / LoCoBench | Dropped | Not suitable for repo-grounded MCP evaluation in this framework. |

Most SDLC tasks and all Org tasks are original, pinned to real repository states.

## Headline Outcome (Current Analysis Snapshot)

From the current analysis set:
- **Overall reward delta (MCP - baseline): +0.0349**
- **SDLC delta: +0.0363**
- **Org delta: +0.0339**

Single-number summaries are directionally useful, but not sufficient. The value is task-type dependent.

## Where MCP Shows the Most Value

Largest suite-level gains are concentrated in retrieval-heavy work:
- SDLC: strongest gains in **Understand**, **Refactor**, **Fix**
- Org: strongest gains in **Incident** and **Security**; these are often cross-repo and high-context tasks

This aligns with the expected value proposition: MCP helps most when relevant context is distributed and non-local.

## Updated Retrieval Breakdown (Newly Curated Ground Truth, `runs/analysis`)

I recomputed retrieval metrics for overlap tasks with both pre-existing and curated ground truth variants.  
Source artifact: `results/ir/baseline_vs_mcp_breakdown_org_sdlc_runs_analysis_20260304.json`.

Scored tasks in this slice:
- Org: 206
- SDLC: 123
- Combined: 329

### Curated GT (`ground_truth_agent.json` / `oracle_answer_agent.json`)

| Group | n | P@5 (BL/MCP) | R@5 (BL/MCP) | F1@5 (BL/MCP) | P@10 (BL/MCP) | R@10 (BL/MCP) | F1@10 (BL/MCP) | Total File Recall (BL/MCP) |
|---|---:|---|---|---|---|---|---|---|
| Org | 206 | 0.000 / 0.365 | 0.000 / 0.262 | 0.000 / 0.275 | 0.001 / 0.245 | 0.001 / 0.314 | 0.001 / 0.246 | 0.001 / 0.322 |
| SDLC | 123 | 0.361 / 0.455 | 0.272 / 0.373 | 0.268 / 0.350 | 0.242 / 0.293 | 0.327 / 0.431 | 0.239 / 0.297 | 0.345 / 0.438 |
| Combined | 329 | 0.135 / 0.399 | 0.102 / 0.304 | 0.100 / 0.303 | 0.091 / 0.263 | 0.123 / 0.358 | 0.090 / 0.265 | 0.129 / 0.365 |

### Pre-existing GT (`ground_truth.json` / `oracle_answer.json`)

| Group | n | P@5 (BL/MCP) | R@5 (BL/MCP) | F1@5 (BL/MCP) | P@10 (BL/MCP) | R@10 (BL/MCP) | F1@10 (BL/MCP) | Total File Recall (BL/MCP) |
|---|---:|---|---|---|---|---|---|---|
| Org | 206 | 0.000 / 0.122 | 0.000 / 0.121 | 0.000 / 0.113 | 0.000 / 0.074 | 0.000 / 0.137 | 0.000 / 0.090 | 0.000 / 0.139 |
| SDLC | 123 | 0.296 / 0.379 | 0.288 / 0.405 | 0.262 / 0.347 | 0.192 / 0.231 | 0.335 / 0.458 | 0.216 / 0.274 | 0.347 / 0.471 |
| Combined | 329 | 0.111 / 0.218 | 0.108 / 0.227 | 0.098 / 0.200 | 0.072 / 0.133 | 0.125 / 0.257 | 0.081 / 0.159 | 0.130 / 0.263 |

## MCP Value Highlights from the New Retrieval Slices

### 1) Multi-repo tasks benefit more than single-repo tasks

Curated GT deltas (`MCP - baseline`, combined):
- `single_repo` (n=159): **F1@10 +0.1075**, **Total Recall +0.1658**
- `multi_repo` (n=170): **F1@10 +0.2387**, **Total Recall +0.3017**

### 2) Gains persist across size bins, with strongest lift in 1M-5M proxy bucket

Curated GT deltas (`MCP - baseline`):
- `<1M`: F1@10 +0.1047, Total +0.1736
- `1M-5M`: F1@10 +0.3417, Total +0.4148
- `5M-20M`: F1@10 +0.0696, Total +0.0960
- `>20M`: F1@10 +0.1653, Total +0.2104

Interpretation: retrieval lift is not uniform, but MCP shows clear upside where task context is more distributed and retrieval-heavy.

## Cost and Speed

Current paired means:
- mean cost delta: **+$0.040/task**
- wall-clock delta: **-36.22s**
- agent execution delta: **-101.06s**

So the current tradeoff is: slightly higher spend, materially faster completion.

## Tool-Use Pattern

Agents heavily favor keyword search and file reads. Deep Search remains rarely used organically.

This suggests prompt/tool-policy design still matters: better capability exists than what default behavior frequently exploits.

## Auditing Matters

Every run emits:
- `result.json` (score, timing, metadata)
- full trajectory/transcript with tool calls

These traces are essential. They exposed benchmark bugs, prompt contamination, verifier issues, and environment loopholes (including a git-history bypass incident) that would have silently distorted results if not audited.

## Quality Assurance Is Most of the Work

Benchmark quality gates check:
1. Task validity
2. Outcome validity
3. Reporting completeness
4. Reproducibility
5. Tool effectiveness
6. Statistical validity

Without this, benchmark claims become fragile very quickly.

## What This Means

The current signal is not “MCP always wins.”  
The signal is:
- MCP has measurable value, especially in cross-repo and context-heavy discovery tasks.
- The effect is heterogeneous across task families.
- Retrieval quality improvements do not always map linearly to reward outcomes.

That is exactly why this benchmark is structured around SDLC and org-use-case slices instead of a single aggregate score.

## What’s Next

Planned next steps:
1. Expand multi-run coverage to reduce non-determinism noise.
2. Evaluate additional harnesses (Codex, Cursor, Gemini, Copilot, OpenHands).
3. Compare alternate MCP providers on the same task set.
4. Run tool-policy experiments (especially semantic/deep-search nudges).
5. Continue tightening verifier and QA infrastructure before final white paper publication.

