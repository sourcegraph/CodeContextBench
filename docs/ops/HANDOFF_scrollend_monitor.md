# Handoff: Monitor csb_sdlc_build rerun + scrollend=0 triage

## Goal
- Keep watching the active 5-task `csb_sdlc_build` baseline rerun.
- Confirm final rewards/artifacts for all 5 tasks.
- Triage why `servo-scrollend-event-feat-001` got verifier reward `0`.

## Current Status (2026-02-27)
- Active run root: `runs/staging/csb_sdlc_build_haiku_20260227_025524/baseline-local-direct`
- 4 tasks done, 1 still running (`flink-pricing-window-feat-001`).
- `servo-scrollend-event-feat-001` completed with verifier reward `0`.
- `servo-scrollend` artifacts exist (`trajectory.json` and `claude-code.txt` are present).
- Verifier output for `servo-scrollend` says:
  - `Change detection: unstaged=0 staged=0 untracked=0 commits=0`
  - `No code changes detected — agent did not execute successfully`

## Files Changed
- `scripts/handoff_monitor_scrollend.sh` (new monitor/investigation helper script)

## Commands Run
```bash
chmod +x scripts/handoff_monitor_scrollend.sh
scripts/handoff_monitor_scrollend.sh status
scripts/handoff_monitor_scrollend.sh investigate
```

## Monitoring Workflow
1. Live watch the active rerun:
```bash
scripts/handoff_monitor_scrollend.sh watch 30
```

2. One-shot status refresh:
```bash
scripts/handoff_monitor_scrollend.sh status
```

3. Check only running harbor processes:
```bash
ps -ef | rg "harbor run --path .*/benchmarks/csb_sdlc_build|run_selected_tasks.sh" | rg -v rg
```

## `scrollend` Zero-Score Investigation Workflow
1. Run the built-in triage command:
```bash
scripts/handoff_monitor_scrollend.sh investigate
```

2. Re-check verifier rationale directly:
```bash
trial=$(find runs/staging/csb_sdlc_build_haiku_20260227_025524/baseline-local-direct -type d -name 'servo-scrollend-event-feat-001__*' | head -n1)
tail -n 80 "$trial/verifier/test-stdout.txt"
jq '{status,reward,exception_info,verifier_reward:(.verifier_result.rewards.reward // null)}' "$trial/result.json"
```

3. Confirm agent command completion signals:
```bash
find "$trial/agent" -maxdepth 2 -name return_code.txt -print -exec cat {} \;
```

4. If verifier still reports "no changes", inspect whether agent reasoning got stuck without writing files:
```bash
tail -n 400 "$trial/agent/claude-code.txt"
```

## Findings / Decisions
- This is not a missing-artifact failure mode.
- It currently looks like a no-op run outcome (no repo diff produced), so verifier correctly scored `0`.
- Keep this rerun as authoritative evidence for `servo-scrollend` unless a follow-up rerun is explicitly requested.

## Open Risks / Unknowns
- `flink-pricing-window-feat-001` is still in-flight and may still timeout or fail.
- If `flink` fails, coverage for the 5-task recovery batch remains incomplete.

## Next Best Command
```bash
scripts/handoff_monitor_scrollend.sh watch 30
```
