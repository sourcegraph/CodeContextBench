# CodeScaleBench

Benchmark suite for evaluating how AI coding agents leverage external context retrieval tools on realistic developer tasks in large, enterprise-scale codebases.

This repository contains:
- **275 benchmark tasks** across 9 developer work types (debug, fix, feature, refactor, security, understand, crossrepo, test, document)
- **Metrics extraction and reporting pipelines** for score/cost/retrieval analysis
- **Run artifacts and agent traces** (in `runs/analysis/`)
- **AI agent skills** for operational workflows (`skills/`)

Tasks are executed via the [Harbor](https://github.com/laude-institute/harbor/tree/main) runner with the Claude Code agent harness.

---

## Quickstart

### Who this repo is for

- Researchers evaluating coding agents on realistic software engineering tasks
- Practitioners comparing baseline vs MCP-enabled agent configurations

### What you can do without Harbor

You can inspect task definitions, run validation and analysis scripts, and use the metrics/report pipeline on existing Harbor run outputs.

```bash
git clone https://github.com/sourcegraph/CodeScaleBench.git
cd CodeScaleBench

# Explore benchmark suites
ls benchmarks

# Browse trace results from analysis runs
python3 scripts/browse_results.py runs/analysis/csb_sdlc --serve

# Generate evaluation report from analysis runs
python3 scripts/generate_eval_report.py \
  --runs-dir runs/analysis/ \
  --output-dir ./eval_reports/
```

### What requires Harbor (benchmark execution)

Running benchmark tasks requires:

- [Harbor](https://github.com/laude-institute/harbor/tree/main) installed and configured
- Docker or a Daytona account for sandbox execution
- Agent/runtime credentials as needed by your Harbor harness

Recommended pre-run checks:

```bash
python3 scripts/check_infra.py
python3 scripts/validate_tasks_preflight.py --all
```

---

## Task Taxonomy

All tasks represent realistic developer work in large, often multi-repo, enterprise codebases. Tasks are organized by **developer work type** — what the developer is doing.

| Work Type | Tasks | Description | Repo Scope |
|-----------|------:|-------------|------------|
| **crossrepo** | 47 | Cross-repo navigation, dependency tracing, org-wide discovery | 18 single, 9 dual, 20 multi |
| **understand** | 44 | Codebase comprehension, architecture, onboarding, domain knowledge | 36 single, 4 dual, 4 multi |
| **refactor** | 43 | Code transformation, migration, dependency updates | 26 single, 2 dual, 15 multi |
| **security** | 39 | Security review, vulnerability remediation, compliance audit | 26 single, 2 dual, 11 multi |
| **feature** | 34 | Feature implementation, org-wide feature work | 24 single, 2 dual, 8 multi |
| **debug** | 26 | Debugging, root cause analysis, incident triage | 15 single, 8 dual, 3 multi |
| **fix** | 19 | Bug repair from issue reports | 19 single |
| **test** | 12 | Test generation, code review, QA | 12 single |
| **document** | 11 | API docs, architecture docs, migration guides | 10 single, 1 dual |
| **Total** | **275** | | 186 single, 28 dual, 61 multi |

**Structural complexity** varies within each work type. Tasks range from single-repo (186) through dual-repo (28) to multi-repo (61), enabling analysis of whether context retrieval tools help more as repo scope widens.

Both baseline and MCP-Full agents have access to **all repos** in each task's fixture. The only difference is the method: baseline reads code locally, MCP-Full uses Sourcegraph MCP tools (local code is truncated). This ensures we measure whether MCP tools help agents work better — not whether MCP can access repos the baseline can't.

---

## 2-Config Evaluation Matrix

All 275 tasks are evaluated across two primary configurations (Baseline vs MCP):

| Config Name | Internal MCP mode | MCP Tools Available |
|-------------------|---------------------|---------------------|
| Baseline | `none` | None (agent uses only built-in tools) |
| MCP | `sourcegraph` / `artifact` (task-dependent) | All 13 Sourcegraph MCP tools including `sg_deepsearch`, `sg_deepsearch_read` |

---

## Repository Structure

```
benchmarks/              # 275 tasks across 20 source directories (9 work types)
  csb_sdlc_feature/      #   feature: Feature Implementation (23 tasks)
  csb_sdlc_fix/          #   fix: Bug Repair (19 tasks)
  csb_sdlc_refactor/     #   refactor: Cross-File Refactoring (18 tasks)
  csb_sdlc_debug/        #   debug: Debugging & Investigation (13 tasks)
  csb_sdlc_secure/       #   security: CVE analysis, governance (13 tasks)
  csb_sdlc_test/         #   test: Testing & QA (12 tasks)
  csb_sdlc_design/       #   understand: Architecture analysis (11 tasks)
  csb_sdlc_document/     #   document: API references, guides (11 tasks)
  csb_sdlc_understand/   #   understand: Comprehension, onboarding (11 tasks)
  csb_org_migration/     #   refactor: Framework migration (25 tasks)
  csb_org_compliance/    #   security: Compliance & audit (13 tasks)
  csb_org_incident/      #   debug: Incident debugging (13 tasks)
  csb_org_platform/      #   crossrepo: Platform knowledge (13 tasks)
  csb_org_security/      #   security: Vulnerability remediation (13 tasks)
  csb_org_crossorg/      #   crossrepo: Cross-org discovery (12 tasks)
  csb_org_crossrepo/     #   crossrepo: Cross-repo discovery (11 tasks)
  csb_org_crossrepo_tracing/  #   crossrepo: Dependency tracing (11 tasks)
  csb_org_domain/        #   understand: Domain lineage (11 tasks)
  csb_org_onboarding/    #   understand: Onboarding (11 tasks)
  csb_org_org/           #   feature: Org-wide feature work (11 tasks)
scripts/                 # Metrics extraction, evaluation, and operational tooling
  csb_metrics/           #   Python package: models, extractors, discovery, judge context
  browse_results.py      #   Local trace results browser (stdlib-only, generates HTML)
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
skills/                  # AI agent skill definitions (operational runbooks)
  csb/                   #   CSB-specific: pre-run, monitoring, triage, analysis, maintenance
runs/
  analysis/              #   Trace results for browsing and analysis
schemas/                 # JSON schemas for MANIFEST.json, task.toml, etc.
tests/                   # Unit tests for scripts/
docs/
  technical_reports/     #   Published technical reports
```

Each suite directory contains per-task subdirectories with `instruction.md`, `task.toml`, `tests/`, and ground truth (or `solution/`). Org tasks additionally include `task_spec.json`, `oracle_answer.json`, and Dockerfile variants for baseline/MCP-only execution.

---

## Metrics Extraction Pipeline

The `scripts/` directory contains a stdlib-only Python 3.10+ pipeline for extracting deterministic metrics from Harbor run output.

```bash
# Generate evaluation report from analysis runs
python3 scripts/generate_eval_report.py \
  --runs-dir runs/analysis/ \
  --output-dir ./eval_reports/

# Generate LLM judge context files
python3 -m scripts.csb_metrics.judge_context \
  --runs-dir runs/analysis/ \
  --benchmarks-dir ./benchmarks/ \
  --output-dir ./judge_contexts/
```

The report generator produces:
- `eval_report.json` -- full structured report
- `REPORT.md` -- markdown tables (performance, efficiency, tool utilization)
- `harness_configs.json` -- exact harness configuration per run
- CSV files per table for downstream analysis

See `python3 scripts/generate_eval_report.py --help` for all options.

### Trace Results Browser

Browse agent traces locally with the built-in results browser:

```bash
# Generate HTML pages for a run directory
python3 scripts/browse_results.py runs/analysis/csb_sdlc

# Generate and serve locally
python3 scripts/browse_results.py runs/analysis/csb_sdlc --serve
```

No external dependencies required (stdlib-only).

---

## Quality Assurance & Validation

CodeScaleBench includes a multi-stage QA pipeline to ensure task integrity, reproducible runs, and accurate scoring.

| Phase | Script | Purpose |
|-------|--------|---------|
| **Pre-flight** | `scripts/validate_tasks_preflight.py` | Catches truncated instructions, template placeholders, language/difficulty mismatches, missing test.sh |
| **Infra check** | `scripts/check_infra.py` | Verifies OAuth tokens (all accounts), Docker, disk space, Harbor CLI |
| **Error fingerprinting** | `scripts/status_fingerprints.py` | Classifies failures with 12 regex patterns; auto-retry guidance per pattern |
| **Post-run** | `scripts/validate_task_run.py` | Flags crashes, MCP tool usage anomalies, suspicious scoring |
| **Metadata sync** | `scripts/sync_task_metadata.py` | Keeps task.toml in sync with selection registry; `--fix` to auto-update |
| **Run analysis** | `scripts/aggregate_status.py` | Scans run dirs, classifies per-task status, writes status.json, supports `--watch` mode |

---

## Operational Tooling

Key scripts organized by workflow phase:

| Phase | Script | Usage |
|-------|--------|-------|
| **Pre-run** | `validate_tasks_preflight.py` | `python3 scripts/validate_tasks_preflight.py [--suite csb_sdlc_fix] [--task sgt-001]` |
| **Pre-run** | `check_infra.py` | `python3 scripts/check_infra.py` |
| **During run** | `aggregate_status.py --since 2h` | `python3 scripts/aggregate_status.py --since 2h` |
| **Post-run** | `aggregate_status.py` | `python3 scripts/aggregate_status.py [--watch]` |
| **Post-run** | `validate_task_run.py` | `python3 scripts/validate_task_run.py <run_dir>` |
| **Analysis** | `compare_configs.py` | `python3 scripts/compare_configs.py` |
| **Analysis** | `cost_report.py` | `python3 scripts/cost_report.py` |
| **Analysis** | `generate_manifest.py` | `python3 scripts/generate_manifest.py` |
| **Maintenance** | `sync_task_metadata.py` | `python3 scripts/sync_task_metadata.py [--fix]` |
| **Maintenance** | `archive_run.py` | `python3 scripts/archive_run.py <run_dir> [--compress]` |
| **Maintenance** | `rerun_failed.py` | `python3 scripts/rerun_failed.py [--fingerprint timeout] [--suite csb_sdlc_fix]` |

---

## AI Agent Skills

The `skills/` directory contains structured runbooks for AI coding agents operating on this repository. These encode operational workflows — infrastructure checks, task validation, failure triage, report generation — so any agent (Claude Code, Cursor, Copilot, etc.) can follow them autonomously.

Skills are plain markdown and tool-agnostic. See [`skills/README.md`](skills/README.md) for the full index and integration guides.

---

## License

See [LICENSE](LICENSE).
