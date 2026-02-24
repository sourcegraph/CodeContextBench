# Troubleshooting

## When To Read This
- You hit infra failures, verifier anomalies, missing outputs, or MCP regressions.

## Do Not Read First If
- You only need the standard run flow: use `docs/ops/WORKFLOWS.md`.

## Escalation Routing
- Repeated infra failures: stop reruns, fix root cause first (`scripts/check_infra.py`).
- Suspected verifier bug: quarantine task, collect evidence, open follow-up.
- Missing trajectories: use transcript/JSONL fallback and document limitation.
- Widespread MCP regressions: run `scripts/mcp_audit.py` before changing prompts/configs.

## Useful References
- `docs/ERROR_CATALOG.md`
- `docs/QA_PROCESS.md`
- `docs/REPO_HEALTH.md`
- `docs/ops/SCRIPT_INDEX.md`

## Minimal Triage Checklist
1. Confirm exact run/task path and error signature.
2. Validate task output files.
3. Check whether failure matches known fingerprint.
4. Classify as infra / verifier / task / agent behavior.
5. Choose isolated rerun or fix path.
