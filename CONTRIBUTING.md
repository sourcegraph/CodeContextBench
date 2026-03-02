# Contributing

Thanks for contributing to CodeScaleBench.

## Scope

This repository contains benchmark tasks, evaluation configs, and analysis tooling. Changes should preserve reproducibility and avoid breaking existing task definitions unless the change is intentional and documented.

## Before Opening a PR

Run the repo health gate from the repository root:

```bash
python3 scripts/repo_health.py
```

For docs/config-only changes, `--quick` is usually sufficient during iteration:

```bash
python3 scripts/repo_health.py --quick
```

## Change Guidelines

- Keep changes scoped and easy to review.
- Update documentation when behavior, workflows, or file locations change.
- Avoid committing local run artifacts (`runs/`, `results/`, `eval_reports/`, logs).
- Do not commit credentials, tokens, or private keys.

## Benchmark / Task Changes

- Validate tasks before launching runs: `python3 scripts/validate_tasks_preflight.py --all`
- Reconcile task metadata when needed: `python3 scripts/sync_task_metadata.py --help`
- Follow task-oriented docs in `docs/START_HERE_BY_TASK.md`

## Pull Requests

- Explain what changed and why.
- Call out any benchmark-impacting behavior changes.
- Include validation commands run (health gate, tests, or scripts) in the PR description.
