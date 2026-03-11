# Handoff: Harness-Agnostic Verifier Hardening (continued)

## What was done (2026-03-11 session)

1. **Trace QA**: Validated 1,094 OH/CC Sonnet 4.6 traces. Found 62 OAuth-expired OH tasks (removed from `_raw`), 6 false-negative `no_changes_guard` tasks, and 1 MCP verifier bug (flipt Go version).

2. **Root cause analysis**: 3 agents investigated 16 tasks. All CC-vs-OH gaps were infrastructure artifacts (OAuth expiry, `no_changes_guard` false negatives, sg_only verifier bugs), not agent capability differences.

3. **5-agent audit** of all 275 benchmark tasks for harness-specific assumptions covering: verifier git state, sg_only Dockerfiles, instruction bias, Dockerfile portability, and answer format assumptions.

4. **Applied fixes (commit `24f69afb9`, pushed to main)**:
   - 76 files: Python `no_changes_guard` + origin ref check
   - 12 files: Shell `no_changes_guard` + `_nc_committed` origin check
   - 2 files: flipt `GOWORK=off`
   - 8 files: onboarding `/app` → `/workspace` default
   - 464 files: `answer_json_verifier_lib.sh` `/repo_full` → workspace fallback

5. **OH Sonnet 4.6 rerun**: 37 tasks x 2 configs completed. Results at `runs/staging/openhands_sonnet46_20260311_174751`. 1 missing baseline (`kafka-contributor-workflow-001`, Harbor timestamp collision). Needs promotion after merging with existing `_raw` data.

## Remaining work (priority order)

### P2 — HIGH ✓ DONE (2026-03-11)

- ~~**132 org `instruction.md` files**~~: Removed false "local `/workspace/` directory contains: sg-evals/REPO" claim from all 132 files.
- ~~**132 Dockerfiles with `USER claude`**~~: Added `chmod -R a+rwX /workspace` before ENTRYPOINT in all 132 Dockerfiles with `USER claude`. Ownership is now harness-agnostic (both root/OH and claude/CC can read/write).
- ~~**4 Linux kernel sg_only Dockerfiles**~~: Added `SOURCEGRAPH_REPOS="torvalds/linux"`, `safe.directory` config, and clone manifest JSON to all 4 tasks.

### P3 — MEDIUM

- **14 SWEAP images** still reference `jefzda/sweap-images` (personal Docker Hub) — migrate to `ghcr.io/sg-evals/`.
- **~30 test runners** missing `timeout` wrapper or `--forceExit` for Jest.
- **6 task.toml files** under-provisioned at 2GB default (qutebrowser x4, nodebb x2 need 4-8GB).

### Promotion

- Promote `runs/staging/openhands_sonnet46_20260311_174751` after rerunning `kafka-contributor-workflow-001` baseline (Harbor timestamp collision).
- The 62 OAuth-expired tasks were already removed from `runs/official/_raw/oh_*_sonnet46_merged/`.

### Key files

- `scripts/apply_verifier_fixes.py` — reusable batch fix script for verifier patterns
- `configs/oh_sonnet46_oauth_rerun.json` — subset config used for the 37-task rerun
