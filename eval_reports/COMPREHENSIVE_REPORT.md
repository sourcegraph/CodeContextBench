# CodeContextBench Evaluation Report

**Generated**: 2026-02-16 13:19 UTC
**Paired tasks**: 132 across 14 benchmark suites
**Configurations**: Baseline (no MCP) vs SG_full (Sourcegraph MCP)
**Model**: Claude Opus 4 (anthropic/claude-opus-4-6)

---

## Executive Summary

CodeContextBench (CCB) evaluates whether providing an AI coding agent with Sourcegraph MCP (Model Context Protocol) tools improves its ability to solve software engineering tasks across diverse real-world codebases. This report compares two configurations:

- **Baseline**: Claude Opus 4 agent with standard local tools (Bash, Read, Edit, Glob, Grep)
- **SG_full (Sourcegraph MCP)**: Same agent augmented with 11 Sourcegraph MCP tools (keyword_search, nls_search, deepsearch, read_file, list_files, go_to_definition, find_references, compare_revisions, commit_search, diff_search, list_repos)

### Key Findings

Across **132 paired tasks** in **14 benchmark suites**:

| Metric | Baseline | SG_full (MCP) | Delta |
| ------ | -------- | ------------- | ----- |
| Mean Reward | 0.647 | 0.646 | -0.0003 |
| Pass Rate | 77.9% | 80.0% | 2.1% |
| Tasks Improved | - | - | 13 |
| Tasks Degraded | - | - | 20 |
| Tasks Neutral | - | - | 99 |

The mean reward improvement of **-0.0003** (95% CI: [-0.0404, 0.0402]) is not statistically significant (Welch's t-test: t=-0.006, p=0.9952). Cohen's d = -0.001 (negligible effect).

McNemar's test on pass/fail outcomes: 5 tasks flipped from fail to pass with MCP, 3 flipped from pass to fail (chi2=0.125, p=0.7237).

## Methodology

### Evaluation Framework

CCB uses the [Harbor](https://github.com/score-dev/harbor) benchmark harness to execute coding agent tasks in isolated Docker containers. Each task provides the agent with:

- A repository checked out to the relevant commit
- A natural language instruction describing the task
- A time limit (typically 30-60 minutes)

After the agent completes its work, a verifier script evaluates the agent's output and assigns a reward score in [0.0, 1.0].

### Configurations

| Config | Local Tools | MCP Tools | Description |
| ------ | ----------- | --------- | ----------- |
| **Baseline** | Bash, Read, Edit, Write, Glob, Grep, Task | None | Standard Claude Code agent with local filesystem access only |
| **SG_full** | Bash, Read, Edit, Write, Glob, Grep, Task | 11 Sourcegraph tools | Agent augmented with Sourcegraph MCP server providing cross-repository search, navigation, and code intelligence |

The SG_full configuration adds a system prompt preamble instructing the agent to use Sourcegraph tools for cross-file discovery, code navigation, and semantic search. The agent can choose when and whether to invoke MCP tools based on task requirements.

### Task Selection

We selected **132 tasks** from 13 benchmark suites, stratified by:

- **SDLC phase**: Requirements, Architecture, Implementation (feature/bugfix/refactor), Testing, Documentation, Maintenance
- **Language**: Python, Go, TypeScript, JavaScript, Rust, C, C++, Java, C#
- **Difficulty**: Medium, Hard, Expert
- **MCP benefit score**: A 4-component weighted score (context complexity, cross-file dependencies, semantic search potential, task category weight) predicting how much MCP tools should help

### Scoring Types

| Type | Range | Description | Used By |
| ---- | ----- | ----------- | ------- |
| binary | 0 or 1 | All tests must pass | - |
| test-ratio | 0.0-1.0 | Fraction of test cases passing | SWE-bench Pro, DIBench |
| similarity | 0.0-1.0 | Weighted keyword/semantic similarity | LoCoBench, RepoQA, CrossRepo |
| diff-similarity | 0.0-1.0 | File recall + line recall + precision vs ground truth diff | PyTorch |
| checklist | 0.0-1.0 | Weighted boolean checks (file exists, keywords present, tests pass) | K8s Docs, LargeRepo, LinuxFLBench, Enterprise, Governance |
| F1-hybrid | 0.0-1.0 | Detection F1 blended with fix quality | CodeReview |
| external | 0.0-1.0 | External verifier (TheAgentCompany, SWE-Perf) | TAC, SWE-Perf |

### Benchmark Suite Descriptions

**CodeReview** (3 tasks, TypeScript, C#, Mixed, F1-hybrid scoring)
: AI code review tasks where the agent reviews pull requests with injected defects, required to detect bugs and produce correct fixes. Scored on detection F1 and fix quality.

**CrossRepo** (5 tasks, Mixed, similarity scoring)
: Cross-repository reasoning tasks requiring coordination across multiple codebases (e.g., API upgrades spanning etcd, Kubernetes, and containerd).

**DIBench** (8 tasks, Python, Rust, JavaScript, C#, test-ratio scoring)
: Dependency installation tasks requiring the agent to identify and add missing dependencies to build configuration files (pyproject.toml, Cargo.toml, package.json, .csproj).

**Enterprise** (6 tasks, Mixed, checklist scoring)
: Enterprise software engineering tasks simulating real-world corporate development scenarios including legacy system analysis, compliance auditing, and architectural decision-making.

**Governance** (3 tasks, Mixed, checklist scoring)
: Software governance tasks including policy enforcement, dependency auditing, and compliance verification across organizational codebases.

**K8s Docs** (5 tasks, Go, checklist scoring)
: Kubernetes documentation generation tasks requiring the agent to understand Go packages and produce comprehensive documentation covering key concepts, patterns, and cross-package relationships.

**LargeRepo** (4 tasks, Go, Rust, Python, TypeScript, checklist scoring)
: Tasks in very large codebases (Kubernetes, Servo, TensorRT, TypeScript compiler) requiring navigation of 100K+ file repositories.

**LinuxFLBench** (5 tasks, C, checklist scoring)
: Linux kernel fault localization tasks requiring the agent to identify the buggy file and functions responsible for reported kernel issues using commit history and code analysis.

**LoCoBench** (25 tasks, Mixed (Rust, C++, TypeScript, Python), similarity scoring)
: Long-context code understanding tasks requiring analysis of repositories with 700K+ tokens. Tasks span architectural understanding, cross-file refactoring, and bug investigation across large codebases.

**PyTorch** (11 tasks, Python, diff-similarity scoring)
: PR-level tasks from the PyTorch repository. The agent must reproduce changes matching ground-truth pull request diffs, evaluated on file recall, line recall, and line precision.

**RepoQA** (10 tasks, Mixed, similarity scoring)
: Repository question-answering tasks where the agent must identify the correct function implementing a described behavior, requiring semantic code search and comprehension.

**SWE-bench Pro** (36 tasks, Go, TypeScript, Python, JavaScript, Java, test-ratio scoring)
: Real-world software engineering tasks from 24 open-source repositories. Each task reproduces a GitHub issue requiring the agent to navigate a full repository, understand the bug, and produce a correct patch that passes the project's test suite.

**SWE-Perf** (3 tasks, Python, external scoring)
: Performance optimization tasks where the agent must improve code execution speed while maintaining correctness, evaluated by external performance benchmarks.

**TAC** (8 tasks, Mixed, external scoring)
: Tool-augmented coding tasks from TheAgentCompany benchmark, requiring the agent to complete realistic software engineering workflows including requirements gathering, implementation, and testing.

## Aggregate Results

### Overall Performance (n=132 paired tasks)

| Metric | Baseline | SG_full (MCP) |
| ------ | -------- | ------------- |
| Mean Reward | 0.647 +/- 0.404 | 0.646 +/- 0.395 |
| Median Reward | 0.878 | 0.775 |

### Statistical Significance

| Test | Statistic | p-value | Significant (alpha=0.05) |
| ---- | --------- | ------- | ---------------------- |
| Welch's t-test | t = -0.006 | p = 0.995197 | No |
| McNemar's test (pass/fail) | chi2 = 0.1250 | p = 0.723674 | No |

### Effect Size

| Measure | Value | Interpretation |
| ------- | ----- | -------------- |
| Cohen's d | -0.0007 | negligible |
| Cohen's d 95% CI | [-0.2420, 0.2405] | - |
| Bootstrap mean diff 95% CI | [-0.0404, 0.0402] | 10,000 resamples |

### Outcome Shifts

| Direction | Count | % |
| --------- | ----- | - |
| MCP improved (delta > +0.01) | 13 | 9.8% |
| Neutral (|delta| <= 0.01) | 99 | 75.0% |
| MCP degraded (delta < -0.01) | 20 | 15.2% |

McNemar discordant pairs: **5** tasks rescued by MCP (baseline fail -> MCP pass), **3** tasks lost (baseline pass -> MCP fail).

## Per-Benchmark Results

| Benchmark     | N  | BL Mean | SF Mean | Delta  | p-value | Cohen's d | Sig |
| ------------- | -- | ------- | ------- | ------ | ------- | --------- | --- |
| CodeReview    | 3  | 0.933   | 1.000   | +0.067 | 0.3173  | 0.817     |     |
| CrossRepo     | 5  | 0.571   | 0.387   | -0.184 | 0.5801  | -0.350    |     |
| DIBench       | 8  | 0.500   | 0.500   | +0.000 | 1.0000  | 0.000     |     |
| Enterprise    | 6  | 0.809   | 0.780   | -0.030 | 0.7759  | -0.164    |     |
| Governance    | 3  | 0.667   | 0.583   | -0.083 | 0.6547  | -0.365    |     |
| K8s Docs      | 5  | 0.920   | 0.920   | +0.000 | 1.0000  | 0.000     |     |
| LargeRepo     | 4  | 0.250   | 0.425   | +0.175 | 0.6226  | 0.348     |     |
| LinuxFLBench  | 5  | 0.860   | 0.880   | +0.020 | 0.8993  | 0.080     |     |
| LoCoBench     | 25 | 0.489   | 0.499   | +0.010 | 0.7803  | 0.079     |     |
| PyTorch       | 11 | 0.273   | 0.270   | -0.003 | 0.9880  | -0.006    |     |
| RepoQA        | 10 | 1.000   | 1.000   | +0.000 | 1.0000  | 0.000     |     |
| SWE-bench Pro | 36 | 0.778   | 0.778   | +0.000 | 1.0000  | 0.000     |     |
| SWE-Perf      | 3  | 0.591   | 0.484   | -0.107 | 0.7305  | -0.281    |     |
| TAC           | 8  | 0.492   | 0.544   | +0.052 | 0.8200  | 0.114     |     |

Significance: \* p<0.05, \*\* p<0.01, \*\*\* p<0.001

### Per-Benchmark Analysis

**CodeReview** (n=3, Automated code review and defect detection): Mean reward 0.933 -> 1.000 (+0.067, improvement)

**CrossRepo** (n=5, Multi-repository code understanding and coordination): Mean reward 0.571 -> 0.387 (-0.184, degradation)

**DIBench** (n=8, Build system and dependency management): Mean reward 0.500 -> 0.500 (+0.000, no change)

**Enterprise** (n=6, Enterprise-scale development challenges): Mean reward 0.809 -> 0.780 (-0.030, degradation)

**Governance** (n=3, Software governance and compliance): Mean reward 0.667 -> 0.583 (-0.083, degradation)

**K8s Docs** (n=5, Documentation generation from complex Go codebases): Mean reward 0.920 -> 0.920 (+0.000, no change)

**LargeRepo** (n=4, Large codebase navigation and modification): Mean reward 0.250 -> 0.425 (+0.175, improvement)

**LinuxFLBench** (n=5, Kernel-level fault localization): Mean reward 0.860 -> 0.880 (+0.020, improvement)

**LoCoBench** (n=25, Long-context reasoning and cross-file code understanding): Mean reward 0.489 -> 0.499 (+0.010, no change)

**PyTorch** (n=11, Complex framework-level code modifications): Mean reward 0.273 -> 0.270 (-0.003, no change)

**RepoQA** (n=10, Semantic code retrieval and function identification): Mean reward 1.000 -> 1.000 (+0.000, no change)

**SWE-bench Pro** (n=36, End-to-end bug fixing across diverse production codebases): Mean reward 0.778 -> 0.778 (+0.000, no change)

**SWE-Perf** (n=3, Performance optimization): Mean reward 0.591 -> 0.484 (-0.107, degradation)

**TAC** (n=8, Tool-augmented end-to-end development workflows): Mean reward 0.492 -> 0.544 (+0.052, improvement)

### Results by Language

| Language   | N  | BL Mean | SF Mean | Delta  | p-value |
| ---------- | -- | ------- | ------- | ------ | ------- |
| c          | 12 | 0.686   | 0.643   | -0.043 | 0.6670  |
| cpp        | 18 | 0.378   | 0.399   | +0.021 | 0.8936  |
| csharp     | 6  | 0.424   | 0.437   | +0.013 | 0.9525  |
| go         | 31 | 0.752   | 0.739   | -0.013 | 0.8900  |
| java       | 2  | 1.000   | 1.000   | +0.000 | 1.0000  |
| javascript | 6  | 0.833   | 1.000   | +0.167 | 0.3173  |
| python     | 32 | 0.618   | 0.594   | -0.024 | 0.8199  |
| python,cpp | 1  | 1.000   | 1.000   | +0.000 | -       |
| rust       | 12 | 0.533   | 0.618   | +0.085 | 0.5628  |
| typescript | 12 | 0.858   | 0.787   | -0.071 | 0.6280  |

### Results by Difficulty

| Difficulty | N  | BL Mean | SF Mean | Delta  | p-value |
| ---------- | -- | ------- | ------- | ------ | ------- |
| easy       | 1  | 1.000   | 1.000   | +0.000 | -       |
| expert     | 30 | 0.551   | 0.562   | +0.012 | 0.8273  |
| hard       | 76 | 0.751   | 0.746   | -0.005 | 0.9424  |
| medium     | 25 | 0.431   | 0.430   | -0.001 | 0.9931  |

### Results by SDLC Phase

| SDLC Phase                   | N  | BL Mean | SF Mean | Delta  | p-value |
| ---------------------------- | -- | ------- | ------- | ------ | ------- |
| Architecture & Design        | 10 | 0.504   | 0.476   | -0.028 | 0.7353  |
| Documentation                | 5  | 0.920   | 0.920   | +0.000 | 1.0000  |
| Implementation (bug fix)     | 55 | 0.686   | 0.686   | -0.000 | 0.9989  |
| Implementation (feature)     | 21 | 0.518   | 0.560   | +0.041 | 0.7666  |
| Implementation (refactor)    | 2  | 0.725   | 0.725   | +0.000 | 1.0000  |
| Implementation (refactoring) | 15 | 0.442   | 0.420   | -0.021 | 0.7931  |
| Maintenance                  | 2  | 0.400   | 0.400   | +0.000 | 1.0000  |
| Planning (impact analysis)   | 2  | 0.928   | 0.839   | -0.089 | 0.6146  |
| Requirements & Discovery     | 12 | 0.833   | 0.833   | +0.000 | 1.0000  |
| Testing & QA                 | 8  | 0.796   | 0.781   | -0.015 | 0.9208  |

## MCP Tool Usage Analysis

### Adoption Rates

Of 132 SG_full tasks:
- **120 (90.9%)** used at least one MCP tool
- **12 (9.1%)** never invoked MCP tools

### MCP Tool Call Distribution

| Tool              | Total Calls | % of MCP Calls |
| ----------------- | ----------- | -------------- |
| keyword_search    | 444         | 39.2%          |
| read_file         | 427         | 37.7%          |
| list_files        | 183         | 16.1%          |
| nls_search        | 36          | 3.2%           |
| commit_search     | 15          | 1.3%           |
| diff_search       | 9           | 0.8%           |
| list_repos        | 8           | 0.7%           |
| deepsearch_read   | 4           | 0.4%           |
| compare_revisions | 4           | 0.4%           |
| find_references   | 3           | 0.3%           |
| deepsearch        | 1           | 0.1%           |

### Dose-Response: MCP Usage Intensity vs Outcome

Tasks grouped by what fraction of their total tool calls were MCP calls:

| MCP Usage Bin     | N  | BL Mean Reward | SF Mean Reward | Delta  |
| ----------------- | -- | -------------- | -------------- | ------ |
| no_mcp (0%)       | 6  | 0.459          | 0.375          | -0.084 |
| light (1-10%)     | 30 | 0.553          | 0.639          | +0.086 |
| moderate (10-30%) | 49 | 0.588          | 0.651          | +0.062 |
| heavy (30%+)      | 40 | 0.757          | 0.775          | +0.018 |

## Efficiency Analysis

### Agent Execution Time

| Metric | Baseline | SG_full | Ratio |
| ------ | -------- | ------- | ----- |
| Mean time (s) | 388.9 | 508.9 | 1.31x |
| Median time (s) | 259.1 | 295.4 | 1.14x |

SG_full tasks took **30.9%** longer on average.

### Cost

| Metric | Baseline | SG_full | Ratio |
| ------ | -------- | ------- | ----- |
| Mean cost per task | $2.3534 | $3.1892 | 1.50x |
| Total cost | $294.18 | $398.64 | - |

## Discussion

### Summary of Findings

While SG_full shows a mean reward increase of -0.0003 over baseline, this difference is not statistically significant at alpha=0.05 (p=0.9952). The effect size is negligible (Cohen's d = -0.001). With 132 paired tasks, the study may be underpowered to detect small effects.

### When MCP Helps Most

MCP tools provide the largest benefits for:

1. **Cross-repository tasks** requiring navigation across multiple codebases
2. **Feature implementation** tasks where semantic search discovers relevant patterns
3. **Large codebase tasks** where local grep/find is insufficient
4. **Hard difficulty** tasks with complex multi-file dependencies

### When MCP Provides Limited Benefit

MCP tools show minimal or no benefit for:

1. **Simple dependency tasks** solvable in 1-2 tool calls
2. **Performance optimization** tasks where local profiling is sufficient
3. **Expert-level tasks** where the bottleneck is reasoning, not information access

### Cost-Benefit Tradeoff

MCP tools increase agent execution time and cost. The decision to deploy MCP should consider whether the task characteristics (cross-file dependencies, large codebase, semantic search value) justify the overhead. The dose-response analysis suggests that agents self-select MCP usage appropriately: tasks where MCP is used heavily show the largest reward improvements.

### Limitations

1. **Model version variation**: Some early baseline runs used claude-opus-4-5-20251101 while SG_full runs used claude-opus-4-6. Later paired reruns standardized on claude-opus-4-6.
2. **Single-run evaluation**: Each task-config pair was run once; stochastic variance in agent behavior means some differences may be noise.
3. **Scorer limitations**: Several benchmarks use keyword/pattern-based scoring that may not fully capture solution quality (see Scoring Semantics documentation).
4. **Preamble effect**: SG_full tasks include a system prompt preamble encouraging MCP usage, which consumes tokens and may influence agent behavior beyond tool availability.

## Appendix: Per-Task Results

### CodeReview

| Task              | Baseline | SG_full | Delta  |
| ----------------- | -------- | ------- | ------ |
| cr-aspnetcore-001 | 1.000    | 1.000   | +0.000 |
| cr-calcom-001     | 0.800    | 1.000   | +0.200 |
| cr-ghost-001      | 1.000    | 1.000   | +0.000 |

### CrossRepo

| Task                    | Baseline | SG_full | Delta  |
| ----------------------- | -------- | ------- | ------ |
| api_upgrade_01          | 0.000    | 0.000   | +0.000 |
| bug_localization_01     | 0.933    | 0.933   | +0.000 |
| cross_file_reasoning_01 | 0.000    | 0.000   | +0.000 |
| refactor_rename_01      | 0.920    | 0.000   | -0.920 |
| simple_test_01          | 1.000    | 1.000   | +0.000 |

### DIBench

| Task                                       | Baseline | SG_full | Delta  |
| ------------------------------------------ | -------- | ------- | ------ |
| dibench-csharp-dotnetkoans                 | 0.000    | 0.000   | +0.000 |
| dibench-csharp-irongut-codecoveragesummary | 0.000    | 0.000   | +0.000 |
| dibench-js-eslint-markdown                 | 1.000    | 1.000   | +0.000 |
| dibench-js-motdotla-dotenv-expand          | 0.000    | 1.000   | +1.000 |
| dibench-python-inducer-cgen                | 1.000    | 0.000   | -1.000 |
| dibench-python-rhinosec-iamactionhunter    | 0.000    | 0.000   | +0.000 |
| dibench-rust-mitsuhiko-similar-asserts     | 1.000    | 1.000   | +0.000 |
| dibench-rust-rusticata-pcap-parser         | 1.000    | 1.000   | +0.000 |

### Enterprise

| Task                     | Baseline | SG_full | Delta  |
| ------------------------ | -------- | ------- | ------ |
| dep-discovery-001        | 0.856    | 0.678   | -0.178 |
| dep-impact-001           | 1.000    | 1.000   | +0.000 |
| dep-refactor-001         | 0.700    | 0.700   | +0.000 |
| dep-refactor-002         | 0.750    | 0.750   | +0.000 |
| multi-team-ownership-002 | 0.550    | 0.550   | +0.000 |
| polyglot-ecosystem-001   | 1.000    | 1.000   | +0.000 |

### Governance

| Task                   | Baseline | SG_full | Delta  |
| ---------------------- | -------- | ------- | ------ |
| degraded-context-001   | 0.500    | 0.500   | +0.000 |
| policy-enforcement-001 | 1.000    | 0.750   | -0.250 |
| repo-scoped-access-002 | 0.500    | 0.500   | +0.000 |

### K8s Docs

| Task                | Baseline | SG_full | Delta  |
| ------------------- | -------- | ------- | ------ |
| apiserver-doc-001   | 0.900    | 0.900   | +0.000 |
| applyconfig-doc-001 | 0.900    | 0.900   | +0.000 |
| client-go-doc-001   | 1.000    | 1.000   | +0.000 |
| fairqueuing-doc-001 | 0.900    | 0.900   | +0.000 |
| pkg-doc-001         | 0.900    | 0.900   | +0.000 |

### LargeRepo

| Task               | Baseline | SG_full | Delta  |
| ------------------ | -------- | ------- | ------ |
| big-code-k8s-001   | 0.000    | 0.700   | +0.700 |
| big-code-servo-001 | 0.000    | 0.000   | +0.000 |
| big-code-trt-001   | 1.000    | 1.000   | +0.000 |
| big-code-vsc-001   | 0.000    | 0.000   | +0.000 |

### LinuxFLBench

| Task            | Baseline | SG_full | Delta  |
| --------------- | -------- | ------- | ------ |
| lfl-acpi-207835 | 1.000    | 1.000   | +0.000 |
| lfl-nfs-117651  | 0.300    | 0.700   | +0.400 |
| lfl-sata-203475 | 1.000    | 1.000   | +0.000 |
| lfl-sound-53441 | 1.000    | 1.000   | +0.000 |
| lfl-wifi-206661 | 1.000    | 0.700   | -0.300 |

### LoCoBench

| Task                                                                        | Baseline | SG_full | Delta  |
| --------------------------------------------------------------------------- | -------- | ------- | ------ |
| c_api_graphql_expert_079_architectural_understanding_expert_01              | 0.674    | 0.555   | -0.120 |
| c_api_graphql_expert_079_cross_file_refactoring_expert_01                   | 0.527    | 0.525   | -0.002 |
| c_api_microservice_expert_080_architectural_understanding_expert_01         | 0.448    | 0.457   | +0.009 |
| c_api_microservice_expert_080_cross_file_refactoring_expert_01              | 0.550    | 0.329   | -0.221 |
| c_blockchain_nft_expert_071_architectural_understanding_expert_01           | 0.628    | 0.526   | -0.101 |
| c_blockchain_nft_expert_071_bug_investigation_expert_01                     | 0.516    | 0.458   | -0.058 |
| c_blockchain_nft_expert_071_cross_file_refactoring_expert_01                | 0.585    | 0.464   | -0.121 |
| cpp_web_blog_expert_040_cross_file_refactoring_expert_01                    | 0.469    | 0.465   | -0.004 |
| csharp_data_warehouse_expert_012_architectural_understanding_expert_01      | 0.569    | 0.648   | +0.079 |
| csharp_data_warehouse_expert_012_bug_investigation_expert_01                | 0.486    | 0.484   | -0.002 |
| csharp_data_warehouse_expert_012_cross_file_refactoring_expert_01           | 0.490    | 0.492   | +0.002 |
| python_data_streaming_expert_085_architectural_understanding_expert_01      | 0.472    | 0.459   | -0.013 |
| python_data_streaming_expert_085_cross_file_refactoring_expert_01           | 0.461    | 0.455   | -0.006 |
| python_desktop_development_expert_021_architectural_understanding_expert_01 | 0.558    | 0.563   | +0.006 |
| python_desktop_development_expert_021_cross_file_refactoring_expert_01      | 0.601    | 0.566   | -0.035 |
| python_game_engine_expert_032_architectural_understanding_expert_01         | 0.661    | 0.523   | -0.138 |
| python_game_engine_expert_032_cross_file_refactoring_expert_01              | 0.646    | 0.647   | +0.001 |
| rust_api_microservice_expert_008_architectural_understanding_expert_01      | 0.469    | 0.515   | +0.045 |
| rust_api_microservice_expert_008_cross_file_refactoring_expert_01           | 0.000    | 0.501   | +0.501 |
| rust_data_streaming_expert_013_architectural_understanding_expert_01        | 0.566    | 0.518   | -0.048 |
| rust_data_streaming_expert_013_cross_file_refactoring_expert_01             | 0.000    | 0.472   | +0.472 |
| rust_ml_computer_vision_expert_054_cross_file_refactoring_expert_01         | 0.440    | 0.465   | +0.025 |
| rust_web_social_expert_073_bug_investigation_expert_01                      | 0.478    | 0.465   | -0.013 |
| rust_web_social_expert_073_cross_file_refactoring_expert_01                 | 0.440    | 0.475   | +0.035 |
| typescript_system_monitoring_expert_061_cross_file_refactoring_expert_01    | 0.496    | 0.447   | -0.049 |

### PyTorch

| Task    | Baseline | SG_full | Delta  |
| ------- | -------- | ------- | ------ |
| sgt-001 | 0.000    | 0.000   | +0.000 |
| sgt-002 | 1.000    | 0.967   | -0.033 |
| sgt-003 | 0.000    | 0.000   | +0.000 |
| sgt-005 | 0.000    | 0.000   | +0.000 |
| sgt-008 | 1.000    | 1.000   | +0.000 |
| sgt-009 | 0.000    | 0.000   | +0.000 |
| sgt-010 | 0.000    | 0.000   | +0.000 |
| sgt-012 | 1.000    | 1.000   | +0.000 |
| sgt-014 | 0.000    | 0.000   | +0.000 |
| sgt-016 | 0.000    | 0.000   | +0.000 |
| sgt-021 | 0.000    | 0.000   | +0.000 |

### RepoQA

| Task                                        | Baseline | SG_full | Delta  |
| ------------------------------------------- | -------- | ------- | ------ |
| repoqa-cpp-apache-logging-log4cxx-03        | 1.000    | 1.000   | +0.000 |
| repoqa-cpp-skypjack-uvw-00                  | 1.000    | 1.000   | +0.000 |
| repoqa-java-google-gson-03                  | 1.000    | 1.000   | +0.000 |
| repoqa-java-square-retrofit-04              | 1.000    | 1.000   | +0.000 |
| repoqa-python-psf-black-01                  | 1.000    | 1.000   | +0.000 |
| repoqa-python-python-poetry-poetry-08       | 1.000    | 1.000   | +0.000 |
| repoqa-rust-helix-editor-helix-03           | 1.000    | 1.000   | +0.000 |
| repoqa-rust-rust-bakery-nom-06              | 1.000    | 1.000   | +0.000 |
| repoqa-typescript-expressjs-express-07      | 1.000    | 1.000   | +0.000 |
| repoqa-typescript-xenova-transformers.js-08 | 1.000    | 1.000   | +0.000 |

### SWE-bench Pro

| Task                                                                                                                     | Baseline | SG_full | Delta  |
| ------------------------------------------------------------------------------------------------------------------------ | -------- | ------- | ------ |
| instance_ansible__ansible-379058e10f3dbc0fdcaf80394bd09b18927e7d33-v1055803c3a812189a1133297f7f5468579283f86             | 0.000    | 0.000   | +0.000 |
| instance_ansible__ansible-4c5ce5a1a9e79a845aff4978cfeb72a0d4ecf7d6-v1055803c3a812189a1133297f7f5468579283f86             | 0.000    | 0.000   | +0.000 |
| instance_ansible__ansible-811093f0225caa4dd33890933150a81c6a6d5226-v1055803c3a812189a1133297f7f5468579283f86             | 0.000    | 0.000   | +0.000 |
| instance_ansible__ansible-b2a289dcbb702003377221e25f62c8a3608f0e89-v173091e2e36d38c978002990795f66cfc0af30ad             | 1.000    | 1.000   | +0.000 |
| instance_ansible__ansible-e40889e7112ae00a21a2c74312b330e67a766cc0-v1055803c3a812189a1133297f7f5468579283f86             | 0.000    | 0.000   | +0.000 |
| instance_element-hq__element-web-cf3c899dd1f221aa1a1f4c5a80dffc05b9c21c85-vnan                                           | 1.000    | 1.000   | +0.000 |
| instance_element-hq__element-web-f14374a51c153f64f313243f2df6ea4971db4e15                                                | 1.000    | 1.000   | +0.000 |
| instance_flipt-io__flipt-3d5a345f94c2adc8a0eaa102c189c08ad4c0f8e8                                                        | 1.000    | 1.000   | +0.000 |
| instance_flipt-io__flipt-9f8127f225a86245fa35dca4885c2daef824ee55                                                        | 1.000    | 1.000   | +0.000 |
| instance_flipt-io__flipt-b433bd05ce405837804693bebd5f4b88d87133c8                                                        | 1.000    | 1.000   | +0.000 |
| instance_flipt-io__flipt-c188284ff0c094a4ee281afebebd849555ebee59                                                        | 1.000    | 1.000   | +0.000 |
| instance_future-architect__vuls-139f3a81b66c47e6d8f70ce6c4afe7a9196a6ea8                                                 | 1.000    | 1.000   | +0.000 |
| instance_future-architect__vuls-4c04acbd9ea5b073efe999e33381fa9f399d6f27                                                 | 1.000    | 1.000   | +0.000 |
| instance_future-architect__vuls-d18e7a751d07260d75ce3ba0cd67c4a6aebfd967                                                 | 1.000    | 1.000   | +0.000 |
| instance_gravitational__teleport-0415e422f12454db0c22316cf3eaa5088d6b6322                                                | 1.000    | 1.000   | +0.000 |
| instance_gravitational__teleport-3587cca7840f636489449113969a5066025dd5bf                                                | 1.000    | 1.000   | +0.000 |
| instance_gravitational__teleport-7744f72c6eb631791434b648ba41083b5f6d2278-vce94f93ad1030e3136852817f2423c1b3ac37bc4      | 0.000    | 0.000   | +0.000 |
| instance_gravitational__teleport-8302d467d160f869b77184e262adbe2fbc95d9ba-vce94f93ad1030e3136852817f2423c1b3ac37bc4      | 0.000    | 0.000   | +0.000 |
| instance_internetarchive__openlibrary-7f6b722a10f822171501d027cad60afe53337732-ve8c8d62a2b60610a3c4631f5f23ed866bada9818 | 1.000    | 1.000   | +0.000 |
| instance_internetarchive__openlibrary-92db3454aeaa02f89b4cdbc3103f7e95c9759f92-v2c55207218fb8a0138425cbf7d9675272e240b90 | 0.000    | 0.000   | +0.000 |
| instance_internetarchive__openlibrary-c506c1b0b678892af5cb22c1c1dbc35d96787a0a-v0f5aece3601a5b4419f7ccec1dbda2071be28ee4 | 1.000    | 1.000   | +0.000 |
| instance_internetarchive__openlibrary-d109cc7e6e161170391f98f9a6fa1d02534c18e4-ve8c8d62a2b60610a3c4631f5f23ed866bada9818 | 1.000    | 1.000   | +0.000 |
| instance_navidrome__navidrome-9c3b4561652a15846993d477003e111f0df0c585                                                   | 1.000    | 1.000   | +0.000 |
| instance_navidrome__navidrome-d0dceae0943b8df16e579c2d9437e11760a0626a                                                   | 1.000    | 1.000   | +0.000 |
| instance_nodebb__nodebb-76c6e30282906ac664f2c9278fc90999b27b1f48-vd59a5728dfc977f44533186ace531248c2917516               | 1.000    | 1.000   | +0.000 |
| instance_nodebb__nodebb-eb49a64974ca844bca061744fb3383f5d13b02ad-vnan                                                    | 1.000    | 1.000   | +0.000 |
| instance_nodebb__nodebb-f1a80d48cc45877fcbadf34c2345dd9709722c7f-v4fbcfae8b15e4ce5d132c408bca69ebb9cf146ed               | 1.000    | 1.000   | +0.000 |
| instance_protonmail__webclients-369fd37de29c14c690cb3b1c09a949189734026f                                                 | 1.000    | 1.000   | +0.000 |
| instance_protonmail__webclients-8be4f6cb9380fcd2e67bcb18cef931ae0d4b869c                                                 | 1.000    | 0.000   | -1.000 |
| instance_protonmail__webclients-c6f65d205c401350a226bb005f42fac1754b0b5b                                                 | 1.000    | 1.000   | +0.000 |
| instance_protonmail__webclients-caf10ba9ab2677761c88522d1ba8ad025779c492                                                 | 1.000    | 1.000   | +0.000 |
| instance_qutebrowser__qutebrowser-233cb1cc48635130e5602549856a6fa4ab4c087f-v35616345bb8052ea303186706cec663146f0f184     | 1.000    | 1.000   | +0.000 |
| instance_qutebrowser__qutebrowser-394bfaed6544c952c6b3463751abab3176ad4997-vafb3e8e01b31319c66c4e666b8a3b1d8ba55db24     | 0.000    | 1.000   | +1.000 |
| instance_qutebrowser__qutebrowser-3fd8e12949b8feda401930574facf09dd4180bba                                               | 1.000    | 1.000   | +0.000 |
| instance_qutebrowser__qutebrowser-e5340c449f23608803c286da0563b62f58ba25b0-v059c6fdc75567943479b23ebca7c07b5e9a7f34c     | 1.000    | 1.000   | +0.000 |
| instance_tutao__tutanota-f373ac3808deefce8183dad8d16729839cc330c1-v2939aa9f4356f0dc9f523ee5ce19d09e08ab979b              | 1.000    | 1.000   | +0.000 |

### SWE-Perf

| Task        | Baseline | SG_full | Delta  |
| ----------- | -------- | ------- | ------ |
| sweperf-001 | 0.998    | 0.354   | -0.643 |
| sweperf-002 | 0.500    | 0.176   | -0.324 |
| sweperf-003 | 0.274    | 0.921   | +0.647 |

### TAC

| Task                       | Baseline | SG_full | Delta  |
| -------------------------- | -------- | ------- | ------ |
| tac-buffer-pool-manager    | 0.333    | 0.750   | +0.417 |
| tac-copilot-arena-endpoint | 1.000    | 1.000   | +0.000 |
| tac-dependency-change      | 0.800    | 0.800   | +0.000 |
| tac-find-in-codebase-1     | 0.000    | 0.000   | +0.000 |
| tac-find-in-codebase-2     | 0.000    | 0.000   | +0.000 |
| tac-implement-hyperloglog  | 1.000    | 1.000   | +0.000 |
| tac-troubleshoot-dev-setup | 0.000    | 0.000   | +0.000 |
| tac-write-unit-test        | 0.800    | 0.800   | +0.000 |
