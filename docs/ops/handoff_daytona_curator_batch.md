# Handoff: Parallelize Curator Ground Truth Generation via Daytona

## Goal
Refactor `scripts/daytona_curator_runner.py` to support CodeScaleBench SDLC tasks (not just ContextBench), then run the 56 remaining missing ground truth tasks in parallel via Daytona sandboxes.

## Current State (as of 2026-03-03 16:00 UTC)

### What's done
- Phase1 curator prompt restored in `scripts/context_retrieval_agent.py` (commit 63c9ec401)
  - `PHASE1_CLI_PROMPTS` + `PHASE1_SUFFIX`: per-backend recall-focused prompts
  - `--prompt-version phase1` flag (default), scored F1=0.749 on ContextBench calibration
  - `get_phase1_system_prompt(backend)` and `get_phase1_allowed_tools(backend)` helper functions
- Sequential run completed 18/74 SDLC tasks before being killed (committed in 26f793e95)
- All 221 Org tasks already have oracle files (0 missing)
- `_resolve_repos()` enhanced with Strategy 3: parses `# Repo:` comments from SWEAP Dockerfiles
- `daytona_curator_runner.py` already has `--prompt-version` flag plumbed through

### What's left: 56 SDLC tasks missing ground_truth.json
- 39 tasks have `git clone` URLs in Dockerfile (sg-evals mirror repos)
- 6 tasks have `# Repo:` comment in Dockerfile (SWEAP images, e.g. element-hq/element-web)
- 9 tasks have `# Source: org/repo (commit)` in Dockerfile (SWEAP debug tasks)
- 2 tasks use TAC images (ghcr.io/theagentcompany/...) with no repo reference

Breakdown by suite:
```
15 csb_sdlc_test     (code reviews, coverage gaps, unit gen)
10 csb_sdlc_fix      (pytorch, teleport, terraform, webclients)
 9 csb_sdlc_debug    (ansible, flipt, qutebrowser, teleport, tutanota, vuls)
 8 csb_sdlc_secure   (django, flipt)
 4 csb_sdlc_feature  (bustub, postgres, servo, vscode)
 4 csb_sdlc_design   (django, etcd, flipt)
 3 csb_sdlc_understand (django, numpy)
 3 csb_sdlc_refactor (flipt, python-http)
```

## The Problem: daytona_curator_runner.py Doesn't Support SDLC Tasks

The current Daytona runner was built for ContextBench validation (loads tasks from HuggingFace parquet, writes trajectory files). To support SDLC ground truth generation, it needs these changes:

### 1. Task Discovery (currently: parquet → need: benchmarks/ directories)
- Replace `load_tasks()` (parquet) with `discover_tasks(sdlc_all=True)` from context_retrieval_agent.py
- Add `--sdlc-all`, `--mcp-all`, `--suite`, `--task-dir` flags (mirror context_retrieval_agent.py's CLI)
- Add `--missing-only` flag to skip tasks that already have ground_truth.json
- Each task is a `Path` to `benchmarks/csb_sdlc_*/{task_name}/`

### 2. Task Context Loading (currently: problem_statement field → need: parse_task_for_curator)
- Call `parse_task_for_curator(task_dir)` for each task to get:
  - `instruction` (from instruction.md), `seed_prompt` (from task_spec.json)
  - `suite_name` (for curator profile selection)
  - `test_sh_diff_targets` (expected edit files from test.sh git diff)
  - `repo_urls` (from Dockerfile git clone commands)
  - `task_type` (sdlc vs mcp_unique)

### 3. Repo Cloning in Sandbox (currently: single repo_url → need: multi-strategy)
- `_resolve_repos(ctx, cache_dir)` handles three strategies:
  1. Repo fixture (from task_spec.json repo_set_id → fixtures/repo_sets/*.json)
  2. Dockerfile git clone URLs (parsed via `_extract_clone_urls()`)
  3. `# Repo:` comment in Dockerfile (SWEAP images)
  4. `# Source: org/repo (commit)` in Dockerfile (SWEAP debug tasks — **needs adding**)
- In Daytona sandbox: clone each repo to /workspace/{repo_name}/
- For tasks with sg-evals mirrors: clone `https://github.com/sg-evals/{repo}--{commit}.git`

### 4. User Message (currently: hardcoded → need: build_user_message)
- Call `build_user_message(ctx, repo_paths)` which includes:
  - Task description from instruction.md or seed_prompt
  - Repo paths mapped to sandbox locations
  - Verifier targets from test.sh (helps agent find expected_edit_files)
  - Deep Search repo name hints

### 5. Output Writing (currently: trajectory JSON → need: write_curator_outputs)
- Call `write_curator_outputs(task_dir, oracle, metadata, ctx, overwrite=True)` after each task
- This writes to the task's own `tests/` directory:
  - `ground_truth.json` (IR pipeline format — files, symbols, expected_edit_files, chunks)
  - `ground_truth_meta.json` (confidence, cost, timing sidecar)
- **Important**: The Daytona sandbox writes files *inside the sandbox*. You need to either:
  - (A) Upload task context TO sandbox, run curator, download results back to host, then call `write_curator_outputs` locally
  - (B) Or have the sandbox write to a mounted volume / collect results via `sandbox.process.exec` output

### 6. Recommended Architecture

The simplest approach: **keep repo cloning and curator execution in Daytona, but collect results back to the host for writing**.

```python
def process_sdlc_task(task_dir, idx, total, daytona_client, creds, model, backend, prompt_version):
    # 1. Parse task locally
    ctx = parse_task_for_curator(task_dir)

    # 2. Determine repo URL(s) for sandbox cloning
    repo_info = _extract_repo_info_for_sandbox(ctx)  # NEW: extract URL+commit for sandbox cloning

    # 3. Create sandbox, clone repo(s), install tools
    sandbox = setup_curator_sandbox(daytona_client, creds, repo_info, model, backend)

    # 4. Build user message with sandbox repo paths
    sandbox_repo_paths = {name: Path(f"/workspace/{name}") for name in repo_info}
    user_msg = build_user_message(ctx, sandbox_repo_paths)

    # 5. Run curator in sandbox
    result = run_curator_in_sandbox(sandbox, user_msg, creds, model, backend, prompt_version, ctx)

    # 6. Write results locally (not in sandbox)
    if result["oracle"].get("files"):
        write_curator_outputs(task_dir, result["oracle"], result["metadata"], ctx, overwrite=True)

    # 7. Cleanup sandbox
    daytona_client.delete(sandbox)
    return result
```

## Key Files to Read

```
scripts/context_retrieval_agent.py   # The full curator — prompts, tools, CLI runner, output writing
  - PHASE1_CLI_PROMPTS (line ~870)   # The phase1 prompt constants
  - get_phase1_system_prompt()       # Helper to get prompt for backend
  - get_phase1_allowed_tools()       # Helper to get tools for backend
  - parse_task_for_curator()         # Phase 0 task parsing
  - build_user_message()             # User message construction
  - _resolve_repos()                 # Multi-strategy repo resolution
  - write_curator_outputs()          # Ground truth file writing
  - _convert_to_ir_schema()          # Oracle → ground_truth.json conversion
  - _extract_json_from_text()        # Parse oracle JSON from CLI output

scripts/daytona_curator_runner.py    # Current Daytona runner (ContextBench-only)
  - setup_curator_sandbox()          # Sandbox creation + tool installation
  - _build_python_runner()           # Python wrapper avoiding shell quoting
  - run_curator_in_sandbox()         # Prompt injection + CLI execution
  - process_task()                   # Per-task orchestration

docs/DAYTONA.md                      # Daytona environment reference
```

## Environment Setup

```bash
source .env.local   # Sets DAYTONA_API_KEY, SOURCEGRAPH_ACCESS_TOKEN, OAuth creds

# Required env vars:
# DAYTONA_API_KEY          — Daytona API key (Tier 3: 125 sandbox limit)
# SOURCEGRAPH_ACCESS_TOKEN — For SG keyword + NLS search in hybrid backend
# OAuth creds at ~/.claude-homes/account1/.claude/.credentials.json

# Verify:
python3 -c "import daytona_sdk; print('OK')"
```

## Execution Parameters

- **Parallelism**: 20 concurrent sandboxes (conservative for long-running curator tasks)
- **Model**: claude-opus-4-6 (subscription billing via OAuth, not API key)
- **Backend**: hybrid (local tools + SG keyword + SG NLS search)
- **Prompt**: phase1 (default, recall-focused)
- **Timeout**: 900s per task (15 min, same as sequential)
- **Expected cost**: ~$0.66/task × 56 = ~$37 (subscription, effectively $0)
- **Expected time**: ~30 min with 20 parallel (vs ~4 hours sequential)

## Verification After Run

```bash
# Check coverage
python3 scripts/context_retrieval_agent.py --sdlc-all --missing-only --dry-run
# Should show: Total: 0 tasks

# Spot-check a few outputs
cat benchmarks/csb_sdlc_debug/flipt-auth-cookie-regression-prove-001/tests/ground_truth.json | python3 -m json.tool | head -20

# Commit results
git add benchmarks/csb_sdlc_*/tests/ground_truth*.json
git commit -m "chore: commit ground truth from Daytona parallel curator run"
git push
```

## Edge Cases

1. **TAC image tasks** (bustub, openhands): No repo URL in Dockerfile. Need manual repo resolution or skip. The bustub task uses `ghcr.io/theagentcompany/sde-implement-hyperloglog-image:1.0.0` — the repo is likely `cmu-db/bustub`. The openhands task needs `All-Hands-AI/OpenHands`.

2. **SWEAP debug tasks with `# Source:` comment**: 9 tasks have `# Source: org/repo (commit)` but no `# Repo:` line. The `_resolve_repos()` Strategy 3 only parses `# Repo:`. You need to add a Strategy 4 that parses `# Source: org/repo (commit)` and clones `https://github.com/org/repo.git` at that commit.

3. **Large repos** (pytorch, ansible, teleport): These take 5-10 min to clone. Consider pre-warming the Daytona sandbox image with common repos, or cloning locally first and uploading.

4. **Rate limiting**: With 20 concurrent `claude -p` calls, monitor for rate limit errors. The sequential run had 0 errors in 18 tasks at ~$0.66/task avg.
