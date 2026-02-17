# Leaderboard Scoring Specification

This document defines how CodeContextBench ranks agent submissions on the leaderboard.

## Submissions

A **submission** is a set of task results from a single agent system. Each submission is identified by its agent name and configuration label — for example:

- `Claude Code (baseline)` — Claude Code with built-in tools only
- `Claude Code (Sourcegraph)` — Claude Code with Sourcegraph MCP tools
- `Codex (default)` — OpenAI Codex with its default configuration
- `Augment Code (custom MCP)` — Augment Code with a custom tool server

Different configurations of the same agent are treated as separate submissions. The leaderboard ranks all submissions against each other.

## Primary Metric: Mean Reward

Each task produces a **reward** value between 0.0 and 1.0 (stored in `result.json` as `verifier_result.rewards.reward`). The primary metric for a benchmark is the **mean reward** across all tasks in that benchmark:

```
mean_reward = sum(task_rewards) / task_count
```

## LLM Judge Score

In addition to the automated verifier reward, tasks may be evaluated by an LLM judge that reviews the full agent trace, instruction, ground truth solution, and agent output. The judge produces a composite score (0.0-1.0) based on the following rubric dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Correctness** | Is the agent's solution functionally correct? |
| **Completeness** | Does the solution address all requirements? |
| **Code Quality** | Is the code clean, idiomatic, and well-structured? |
| **Reasoning Quality** | How well did the agent reason about the problem? |
| **Tool Use Efficiency** | How efficiently did the agent use available tools? |

The judge score is a **complementary quality signal** — it does **not** affect ranking. The automated verifier reward remains the canonical ranking metric. Judge scores appear in a separate column on the leaderboard and display `---` when not available for a task.

The aggregate judge score is computed identically to the aggregate verifier score: the unweighted mean of per-benchmark mean judge scores over qualifying (complete) benchmarks.

## Error Handling

Tasks that error (agent crash, timeout, container failure) count as **reward = 0.0**. They are never excluded from the denominator. If a submission errors on 2 of 10 tasks and scores 1.0 on the other 8, its mean reward is `8.0 / 10 = 0.80`.

## Per-Benchmark Completeness

To qualify for a benchmark's leaderboard, a submission must include results for **all** tasks in that benchmark. The required task counts are:

| Benchmark | Tasks | Reward Type |
|-----------|-------|-------------|
| SWE-bench Pro | 36 | test_ratio |
| LargeRepo | 25 | checklist |
| DocGen | 13 | checklist |
| CrossRepo | 12 | semantic_similarity |
| Enterprise | 12 | checklist |
| PyTorch | 11 | diff_similarity |
| NavProve | 9 | checklist |
| CodeReview | 8 | checklist |
| DIBench | 8 | binary |
| Governance | 8 | checklist |
| NLQA | 8 | checklist |
| Onboarding | 8 | checklist |
| Security | 8 | checklist |
| TAC | 8 | checklist |
| LinuxFLBench | 5 | checklist |
| Investigation | 4 | checklist |
| SWE-Perf | 3 | test_ratio |

A submission with 34 of 36 SWE-bench Pro results does **not** appear on the SWE-bench Pro leaderboard. Partial results are retained in the data for analysis but excluded from rankings.

## Aggregate Score

The **CCB Aggregate Score** is the unweighted (macro) average of per-benchmark mean rewards:

```
ccb_aggregate = sum(per_benchmark_mean_rewards) / N_qualifying_benchmarks
```

All benchmarks carry equal weight regardless of task count. The aggregate score is computed over benchmarks where the submission has complete results. A submission with complete results for 10 of 17 benchmarks gets an aggregate over those 10. Submissions with more complete benchmarks are ranked higher when scores are close.

## Tie-Breaking

When two submissions have equal mean reward (to 3 decimal places), ties are broken in order:

1. **Benchmarks completed** — number of benchmarks with full task coverage (more is better)
2. **Pass rate** — fraction of tasks with reward > 0.0 (higher is better)
3. **Median reward** — median of per-task rewards (higher is better)
4. **Token efficiency** — total tokens used, `n_input_tokens + n_output_tokens` (lower is better)

## Interpreting Scores

Reward values are always 0.0–1.0, but the semantics differ by benchmark:

| Reward Type | Benchmarks | What 0.8 Means |
|-------------|-----------|-----------------|
| **test_ratio** | SWE-bench Pro, SWE-Perf | 80% of test cases pass |
| **diff_similarity** | PyTorch | Patch is 80% similar to the reference diff |
| **semantic_similarity** | CrossRepo | Agent output is 80% semantically similar to the reference answer |
| **checklist** | DocGen, LargeRepo, CodeReview, LinuxFLBench, TAC, Enterprise, Governance, NavProve, NLQA, Onboarding, Security, Investigation | 80% of weighted checklist items satisfied |
| **binary** | DIBench | Not applicable — reward is either 0.0 or 1.0 |

### Reward Type Details

- **test_ratio**: The fraction of repository test cases that pass after the agent's changes. Measures functional correctness.
- **diff_similarity**: Similarity between the agent's code diff and the expected reference diff. Measures implementation accuracy.
- **semantic_similarity**: Embedding-based similarity between the agent's output and the reference answer. Measures content accuracy.
- **checklist**: Weighted sum of discrete checks (file presence, pattern matching, structural correctness). Measures completeness.
- **binary**: Pass or fail — the task is either solved (1.0) or not (0.0). No partial credit.

## Calculation Example

An agent runs all 17 benchmarks and achieves:

| Benchmark | Mean Reward |
|-----------|-------------|
| SWE-bench Pro | 0.650 |
| LargeRepo | 0.250 |
| DocGen | 0.700 |
| CrossRepo | 0.400 |
| Enterprise | 0.350 |
| PyTorch | 0.100 |
| NavProve | 0.450 |
| CodeReview | 0.600 |
| DIBench | 0.500 |
| Governance | 0.400 |
| NLQA | 0.500 |
| Onboarding | 0.550 |
| Security | 0.400 |
| TAC | 0.250 |
| LinuxFLBench | 0.860 |
| Investigation | 0.300 |
| SWE-Perf | 0.600 |

**CCB Aggregate Score** = sum of means / 17 = **0.462**

**Benchmarks completed** = 17/17

**Pass rate** = tasks with reward > 0.0 / total tasks = e.g., 140 / 186 = 0.753
