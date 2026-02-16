# Framework Audit (2026-02-16)

## Scope

- Core operational docs (`README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/CONFIGS.md`, `docs/QA_PROCESS.md`)
- Config/run script alignment
- Analysis/curation script maintainability
- Agent-skill alignment for Codex/Claude workflows

## Findings Fixed

1. Central docs referenced missing `*_3config.sh` scripts and a removed report-generator script.
2. `configs/run_selected_tasks.sh` still required `ANTHROPIC_API_KEY` despite subscription-only execution.
3. Config names were hardcoded in multiple scripts, making provider/config expansion fragile.
4. `*_2config.sh` headers still pointed to `*_3config.sh` invocations.
5. No automated guard existed to detect docs drifting away from real script paths.

## Changes Applied

- Added shared config matrix:
  - `configs/eval_matrix.json`
  - `scripts/eval_matrix.py`
- Refactored scripts to consume the shared matrix:
  - `scripts/generate_manifest.py`
  - `scripts/audit_traces.py`
  - `scripts/cost_report.py`
  - `scripts/validate_task_run.py`
- Added docs consistency linter:
  - `scripts/docs_consistency_check.py`
- Rewrote/updated core docs:
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/CONFIGS.md`
  - `docs/QA_PROCESS.md`
  - `docs/EXTENSIBILITY.md` (new)
- Updated config script usage headers in all `configs/*_2config.sh`.
- Updated `configs/_common.sh` comments to match current script naming.
- Updated `configs/run_selected_tasks.sh` to remove API-key hard requirement.

## Validation

- `python3 scripts/docs_consistency_check.py` -> OK
- `python3 -m py_compile` on modified scripts -> OK
- `python3 scripts/generate_manifest.py --require-triage --fail-on-unknown-prefix` -> OK
- `python3 scripts/validate_official_integrity.py --runs-dir runs/official --check-mcp-trace-health` -> OK (warnings only)
- `python3 scripts/audit_traces.py --json` -> 242 curated tasks
- `python3 scripts/cost_report.py --format json` -> 242 tasks (aligned with curated task count)

## Remaining Gaps / Follow-ups

1. Several specialized analysis scripts still assume `sourcegraph_base` in comments/help text even when not part of default official workflow.
2. Some global non-repo skills remain partially legacy; CCB-specific overrides were added, but a full skill refresh would reduce confusion further.
3. The official integrity gate reports setup/auth failures with no transcript (`mcp_init_missing_no_transcript`); these are warnings today and may be upgraded for stricter publication gates.
