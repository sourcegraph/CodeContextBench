# Configs Directory Guide

Use this file when working in `configs/` launchers and run orchestration wrappers.

## Non-Negotiables
- Every `harbor run` invocation must be interactively confirmed.
- Do not reintroduce `--yes` for `configs/run_selected_tasks.sh`.
- Validate config naming and paired-run semantics via shared helpers in `configs/_common.sh`.

## Navigation Rules
- Start with `configs/_common.sh` for shared run policy and confirmation behavior.
- Use `configs/run_selected_tasks.sh` for selected-task execution flows.
- Use `configs/*_2config.sh` wrappers for paired baseline/MCP runs.
- For Daytona cloud execution, add `--environment-type daytona` to `harbor run` commands. See `docs/DAYTONA.md` for prerequisites and capacity planning.

## When Editing
- Preserve `confirm_launch()` gating behavior.
- Keep config name semantics aligned with `docs/CONFIGS.md`.
- Run at least `python3 scripts/docs_consistency_check.py` after changing command references.
