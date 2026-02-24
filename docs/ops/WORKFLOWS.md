# Operations Workflows

## When To Read This
- You need the standard operational sequence for runs, triage, or reporting.

## Do Not Read First If
- You only need a single script: use `docs/ops/SCRIPT_INDEX.md`.
- You need policy definitions/spec semantics: use `docs/reference/README.md`.

## Run Batch Workflow
1. Run infra checks (`scripts/check_infra.py`).
2. Validate tasks (`scripts/validate_tasks_preflight.py`).
3. Launch benchmark via `configs/*` runner (interactive confirmation required).
4. Monitor with `scripts/aggregate_status.py` and classify errors.
5. Validate outputs (`scripts/validate_task_run.py`).
6. Triage before reruns.
7. Regenerate manifest/report after completion.
8. Run `scripts/repo_health.py` before commit/push.

## Triage Workflow
1. Confirm error class via `docs/ERROR_CATALOG.md` and status fingerprints.
2. Check run outputs and trajectories.
3. Isolate task-level fix or rerun scope.
4. Avoid blind reruns; document root cause or limitation.

## Docs / Agent Navigation Maintenance Workflow
1. Edit canonical sources under `docs/ops/`.
2. Regenerate guides and indexes:
```bash
python3 scripts/refresh_agent_navigation.py
```
3. Verify freshness in CI/local (`python3 scripts/refresh_agent_navigation.py --check`).
4. Run `python3 scripts/docs_consistency_check.py`.
5. Run `python3 scripts/repo_health.py --quick` before commit.
