# CodeContextBench

Benchmark suite for evaluating how AI coding agents leverage external context tools on software engineering tasks across the SDLC. Developed as the reproducibility artifact for the paper *"CodeContextBench: A Systematic Evaluation Framework for Assessing the Impact of Enhanced Code Intelligence on AI Coding Agent Performance."*

This repository contains **benchmark task definitions**, **evaluation configs**, and a **metrics extraction pipeline**. Tasks are executed via the [Harbor](https://github.com/laude-institute/harbor/tree/main) runner with the Claude Code agent harness.

---

## Benchmark Suites

| Suite | Tasks | Languages | Evaluation Method | SDLC Phase |
|-------|------:|-----------|-------------------|------------|
| `ccb_swebenchpro` | 36 | Go, TypeScript, Python, JavaScript | LLM judge + test suite | Bug fixing |
| `ccb_largerepo` | 25 | Go, Rust, C/C++, Java, Python, TypeScript | LLM judge + test suite | Feature impl, Analysis, Debugging, Security |
| `ccb_docgen` | 13 | Go, C++, Java, TypeScript | LLM judge + keyword checks | Documentation |
| `ccb_crossrepo` | 12 | Go, C++ | LLM judge + test suite | Architecture, Bug fix, Refactoring, Discovery |
| `ccb_enterprise` | 12 | Go, Python | LLM judge + test suite | Impact analysis, Feature impl, Bug fix |
| `ccb_pytorch` | 11 | C++ | LLM judge + test suite | Bug fixing |
| `ccb_navprove` | 9 | Go, Python, TypeScript | LLM judge + test suite | Debugging |
| `ccb_codereview` | 8 | C, C++, C#, Go, Java, JavaScript, TypeScript | Hybrid detection + fix scoring | Testing & QA |
| `ccb_dibench` | 8 | Python, Rust, JavaScript, C# | LLM judge + syntax/dependency validation | Dependency inference |
| `ccb_governance` | 8 | Go, Python | LLM judge + test suite | Feature impl, Bug fix |
| `ccb_nlqa` | 8 | Go, C++, Java, TypeScript | LLM judge + test suite | Debugging, Discovery |
| `ccb_onboarding` | 8 | Go, C++, Java | LLM judge + test suite | Discovery |
| `ccb_security` | 8 | Go, C, C++, Java | LLM judge + test suite | Discovery |
| `ccb_tac` | 8 | C++, Python | LLM judge + deterministic checks | Mixed (4 phases) |
| `ccb_linuxflbench` | 5 | C | Test script verification | Kernel fault localization |
| `ccb_investigation` | 4 | Go, Python | LLM judge + test suite | Discovery |
| `ccb_sweperf` | 3 | Python | LLM judge + test suite | Testing & QA |
| **Total** | **186** | | | |

Archived suites (not included in official evaluation): `ccb_dependeval`, `ccb_locobench`, `ccb_repoqa`, and `ccb_k8sdocs` (superseded by `ccb_docgen`). Task files live under `benchmarks/archive/` or their original directories.

---

## 3-Config Evaluation Matrix

All benchmarks are evaluated across three agent configurations that vary the external context tools available via MCP:

| Paper Config Name | `BASELINE_MCP_TYPE` | MCP Tools Available |
|-------------------|---------------------|---------------------|
| Baseline | `none` | None (agent uses only built-in tools) |
| MCP-Base | `sourcegraph_base` | `sg_keyword_search`, `sg_read_file`, `sg_find_file`, `sg_nls_search`, `sg_search_suggestions`, `sg_get_context` (6 tools) |
| MCP-Full | `sourcegraph_full` | All MCP-Base tools + `sg_deepsearch`, `sg_deepsearch_read` (8 tools) |

See [docs/CONFIGS.md](docs/CONFIGS.md) for the full tool-by-tool breakdown.

---

## Repository Structure

```
benchmarks/              # Task definitions organized by benchmark suite
  archive/               #   Archived suites (ccb_dependeval, ccb_repoqa, ccb_k8sdocs, ccb_locobench)
  ccb_codereview/        #   AI code review: PR defect detection (8 tasks)
  ccb_crossrepo/         #   Cross-repository reasoning (12 tasks)
  ccb_dibench/           #   Dependency inference tasks (8 tasks)
  ccb_docgen/            #   Documentation generation (13 tasks)
  ccb_enterprise/        #   Enterprise codebase challenges (12 tasks)
  ccb_governance/        #   Access control and policy enforcement (8 tasks)
  ccb_investigation/     #   Deep debugging and investigation (4 tasks)
  ccb_largerepo/         #   Large-repo code navigation (25 tasks)
  ccb_linuxflbench/      #   Linux kernel fault localization (5 tasks)
  ccb_navprove/          #   Navigation and provenance reasoning (9 tasks)
  ccb_nlqa/              #   Natural-language code Q&A (8 tasks)
  ccb_onboarding/        #   Codebase onboarding and orientation (8 tasks)
  ccb_pytorch/           #   PyTorch PR-level tasks (11 tasks)
  ccb_security/          #   Security analysis and CVE reasoning (8 tasks)
  ccb_swebenchpro/       #   SWE-Bench Pro bug-fixing tasks (36 tasks)
  ccb_sweperf/           #   Performance testing (3 tasks)
  ccb_tac/               #   TheAgentCompany tasks (8 tasks)
configs/                 # 3-config comparison shell runners + task selection
  _common.sh             #   Shared infra: token refresh, parallel execution, multi-account
  codereview_2config.sh  #   Per-suite runner: CodeReview (8 tasks)
  crossrepo_2config.sh   #   Per-suite runner: CrossRepo (12 tasks)
  dibench_2config.sh     #   Per-suite runner: DIBench (8 tasks)
  docgen_2config.sh      #   Per-suite runner: DocGen (13 tasks)
  enterprise_2config.sh  #   Per-suite runner: Enterprise (12 tasks)
  governance_2config.sh  #   Per-suite runner: Governance (8 tasks)
  investigation_2config.sh # Per-suite runner: Investigation (4 tasks)
  largerepo_2config.sh   #   Per-suite runner: LargeRepo (25 tasks)
  linuxflbench_2config.sh #  Per-suite runner: LinuxFLBench (5 tasks)
  navprove_2config.sh    #   Per-suite runner: NavProve (9 tasks)
  nlqa_2config.sh        #   Per-suite runner: NLQA (8 tasks)
  onboarding_2config.sh  #   Per-suite runner: Onboarding (8 tasks)
  pytorch_2config.sh     #   Per-suite runner: PyTorch (11 tasks)
  security_2config.sh    #   Per-suite runner: Security (8 tasks)
  swebenchpro_2config.sh #   Per-suite runner: SWE-Bench Pro (36 tasks)
  sweperf_2config.sh     #   Per-suite runner: SWE-Perf (3 tasks)
  tac_2config.sh         #   Per-suite runner: TheAgentCompany (8 tasks)
  run_selected_tasks.sh  #   Unified runner for all tasks
  selected_benchmark_tasks.json  # Canonical task selection with metadata
scripts/                 # Metrics extraction, evaluation, and operational tooling
  ccb_metrics/           #   Python package: models, extractors, discovery, judge context
  generate_eval_report.py  # CLI: deterministic evaluation report generator
  aggregate_status.py    #   Core run scanner (status, errors, watch mode)
  status_fingerprints.py #   Error classification (12 regex patterns)
  validate_tasks_preflight.py # Pre-flight task validation
  validate_task_run.py   #   Post-run validation
  check_infra.py         #   Infrastructure readiness checker
  compare_configs.py     #   Cross-config divergence analysis
  cost_report.py         #   Token/cost aggregation
  sync_task_metadata.py  #   task.toml vs selection registry reconciliation
  generate_manifest.py   #   Rebuild MANIFEST from on-disk results
  archive_run.py         #   Archive old runs to save disk
  rerun_failed.py        #   Generate rerun commands for failed tasks
  abc_audit.py           #   ABC benchmark quality audit framework
  abc_score_task.py      #   Per-task quality scoring
  abc_criteria.py        #   ABC criteria data model (32 criteria)
  docs_consistency_check.py # Documentation drift guard
tests/                   # Unit tests for scripts/
  test_abc_audit.py      #   Tests for ABC audit framework
  test_abc_criteria.py   #   Tests for ABC criteria data model
  test_abc_score_task.py #   Tests for task quality scorer
  test_extract_task_metrics.py # Tests for metrics extraction
docs/                    # Operational documentation
  CONFIGS.md             #   3-config tool breakdown
  ERROR_CATALOG.md       #   Known error fingerprints, causes, fixes
  QA_PROCESS.md          #   Quality assurance and validation pipeline
  TASK_CATALOG.md        #   Detailed per-task reference
  TASK_SELECTION.md      #   Selection criteria, difficulty calibration, MCP scoring
  SCORING_SEMANTICS.md   #   Reward and pass interpretation per benchmark
  WORKFLOW_METRICS.md    #   Timing/cost metric definitions
  AGENT_INTERFACE.md     #   Runtime I/O contract for agents
  EXTENSIBILITY.md       #   Safe suite/task/config extension guide
  LEADERBOARD.md         #   Ranking policy
  SUBMISSION.md          #   Submission format specification
skills/                  # AI agent skill definitions (operational runbooks)
  ccb/                   #   CCB-specific: pre-run, monitoring, triage, analysis, maintenance
  general/               #   Reusable: workflow tools, agent delegation, dev practices
schemas/                 # JSON schemas for MANIFEST.json, task.toml, etc.
```

Each benchmark directory contains:
- `MANIFEST.json` -- metadata, task IDs, evaluation config
- Per-task subdirectories with `instruction.md`, `task.toml`, tests, and ground truth (or `solution/`)

---

## Metrics Extraction Pipeline

The `scripts/` directory contains a stdlib-only Python 3.10+ pipeline for extracting deterministic metrics from Harbor run output:

```bash
# Generate evaluation report from Harbor runs
python3 scripts/generate_eval_report.py \
  --runs-dir /path/to/runs/official/ \
  --output-dir ./eval_reports/

# Generate LLM judge context files
python3 -m scripts.ccb_metrics.judge_context \
  --runs-dir /path/to/runs/official/ \
  --benchmarks-dir ./benchmarks/ \
  --output-dir ./judge_contexts/
```

The report generator produces:
- `eval_report.json` -- full structured report
- `REPORT.md` -- markdown tables (performance, efficiency, tool utilization)
- `harness_configs.json` -- exact harness configuration per run
- CSV files per table for downstream analysis

See `python3 scripts/generate_eval_report.py --help` for all options.

---

## Running with Harbor

The unified runner executes all 186 tasks across the 3-config matrix:

```bash
# Run all 186 tasks across 3 configs
bash configs/run_selected_tasks.sh

# Run only the baseline config
bash configs/run_selected_tasks.sh --baseline-only

# Dry run to list tasks without executing
bash configs/run_selected_tasks.sh --dry-run
```

Per-suite runners are also available for individual benchmarks:

```bash
bash configs/swebenchpro_2config.sh      # 36 SWE-Bench Pro tasks
bash configs/largerepo_2config.sh        # 25 LargeRepo tasks
bash configs/docgen_2config.sh           # 13 DocGen tasks
bash configs/crossrepo_2config.sh        # 12 CrossRepo tasks
bash configs/enterprise_2config.sh       # 12 Enterprise tasks
bash configs/pytorch_2config.sh          # 11 PyTorch tasks
bash configs/navprove_2config.sh         # 9 NavProve tasks
bash configs/codereview_2config.sh       # 8 CodeReview tasks
bash configs/dibench_2config.sh          # 8 DIBench tasks
bash configs/governance_2config.sh       # 8 Governance tasks
bash configs/nlqa_2config.sh             # 8 NLQA tasks
bash configs/onboarding_2config.sh       # 8 Onboarding tasks
bash configs/security_2config.sh         # 8 Security tasks
bash configs/tac_2config.sh              # 8 TheAgentCompany tasks
bash configs/linuxflbench_2config.sh     # 5 LinuxFLBench tasks (see note below)
bash configs/investigation_2config.sh    # 4 Investigation tasks
bash configs/sweperf_2config.sh          # 3 SWE-Perf tasks
```

All runners support `--baseline-only` and `--full-only` flags.

**LinuxFLBench note:** Docker image build is slow (~10 min) due to Linux kernel partial clone (~2GB). Pre-build images before running to save time.

Requires [Harbor](https://github.com/laude-institute/harbor/tree/main) installed and configured with a Claude API key.

---

## Quality Assurance & Validation

CodeContextBench includes a multi-stage QA pipeline to ensure task integrity, reproducible runs, and accurate scoring.

| Phase | Script | Purpose |
|-------|--------|---------|
| **Pre-flight** | `scripts/validate_tasks_preflight.py` | Catches truncated instructions, template placeholders, language/difficulty mismatches, missing test.sh |
| **Infra check** | `scripts/check_infra.py` | Verifies OAuth tokens (all accounts), Docker, disk space, Harbor CLI |
| **Error fingerprinting** | `scripts/status_fingerprints.py` | Classifies failures with 12 regex patterns; auto-retry guidance per pattern |
| **Post-run** | `scripts/validate_task_run.py` | Flags crashes, MCP tool usage anomalies, suspicious scoring |
| **Metadata sync** | `scripts/sync_task_metadata.py` | Keeps task.toml in sync with `selected_benchmark_tasks.json`; `--fix` to auto-update |
| **Run analysis** | `scripts/aggregate_status.py` | Scans run dirs, classifies per-task status, writes status.json, supports `--watch` mode |

The QA methodology uses a 6-dimension audit framework: instruction contamination, reproducibility, verifier correctness, ghost/false-positive detection, error misclassification, and tool effectiveness analysis.

See [docs/QA_PROCESS.md](docs/QA_PROCESS.md) for the full pipeline documentation and [docs/ERROR_CATALOG.md](docs/ERROR_CATALOG.md) for the known error catalog.

---

## Operational Tooling

Key scripts organized by workflow phase:

| Phase | Script | Usage |
|-------|--------|-------|
| **Pre-run** | `validate_tasks_preflight.py` | `python3 scripts/validate_tasks_preflight.py [--suite ccb_pytorch] [--task sgt-001]` |
| **Pre-run** | `check_infra.py` | `python3 scripts/check_infra.py` |
| **During run** | `aggregate_status.py --since 2h` | `python3 scripts/aggregate_status.py --since 2h` |
| **Post-run** | `aggregate_status.py` | `python3 scripts/aggregate_status.py [--watch]` |
| **Post-run** | `validate_task_run.py` | `python3 scripts/validate_task_run.py <run_dir>` |
| **Analysis** | `compare_configs.py` | `python3 scripts/compare_configs.py` |
| **Analysis** | `cost_report.py` | `python3 scripts/cost_report.py` |
| **Analysis** | `generate_manifest.py` | `python3 scripts/generate_manifest.py` |
| **Maintenance** | `sync_task_metadata.py` | `python3 scripts/sync_task_metadata.py [--fix]` |
| **Maintenance** | `archive_run.py` | `python3 scripts/archive_run.py <run_dir> [--compress]` |
| **Maintenance** | `rerun_failed.py` | `python3 scripts/rerun_failed.py [--fingerprint timeout] [--suite ccb_pytorch]` |

---

## AI Agent Skills

The `skills/` directory contains structured runbooks for AI coding agents operating on this repository. These encode operational workflows — infrastructure checks, task validation, failure triage, report generation — so any agent (Claude Code, Cursor, Copilot, etc.) can follow them autonomously.

| Category | Skills | Description |
|----------|--------|-------------|
| **CCB Operations** | 20 skills in 6 files | Pre-run checks, monitoring, triage, analysis, maintenance, task authoring |
| **General Purpose** | 11 skills in 4 files | Session management, agent delegation, search patterns, dev practices |

Skills are plain markdown and tool-agnostic. See [`skills/README.md`](skills/README.md) for the full index and integration guides for Cursor, Claude Code, and other agents. See [`docs/SKILLS.md`](docs/SKILLS.md) for background on the skills system.

---

## License

See [LICENSE](LICENSE).
