# Handoff: Scaffold 92 New Benchmark Tasks

## Context

Power analysis (2026-03-07) identified that CodeScaleBench needs +92 tasks to reach 80% power at δ=0.05 across all 5 analysis dimensions for the research paper. The paper evaluates:

1. **Single vs Multi-repo** — does codebase distribution affect agent/retrieval performance?
2. **Context-retrieval tools vs local search** — MCP (Sourcegraph) vs baseline (grep/glob/read)
3. **Codebase complexity** — does complexity moderate retrieval benefit?
4. **Codebase size** — does size moderate retrieval benefit?
5. **Task category** — Comprehension vs Implementation vs Quality

### Analytical Reclassification (reporting-layer only)

The paper uses 3 task categories that merge the 20 existing suites. No directory renames — this is a `SUITE_TO_CATEGORY` mapping in the analysis code:

```
Comprehension (167 tasks — NO expansion needed):
  csb_sdlc_understand, csb_sdlc_design, csb_sdlc_document,
  csb_org_crossrepo_tracing, csb_org_domain, csb_org_onboarding,
  csb_org_platform, csb_org_crossorg, csb_org_org

Implementation (117 → 153, +36 tasks):
  csb_sdlc_feature, csb_sdlc_fix, csb_sdlc_refactor,
  csb_org_crossrepo, csb_org_migration

Quality (120 → 176, +56 tasks):
  csb_sdlc_debug, csb_sdlc_test, csb_sdlc_secure,
  csb_org_incident, csb_org_security, csb_org_compliance
```

### Size Coverage Gaps Being Filled

The 92 tasks are deliberately allocated to underrepresented size tiers:

```
              Before  After   Change
<50MB:          24      48    +100%
50-200MB:       39      49     +26%
200-500MB:      93      93       0%
500MB-1GB:      18      34     +89%
1-3GB:          51      51       0%
3GB+:           12      54    +350%
```

---

## Task Allocation

### IMPLEMENTATION (+36 tasks)

#### csb_org_migration (+12)

Multi-repo migration inventory tasks. Pattern: find deprecated APIs, catalog breaking changes, audit version migration needs.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| <50MB | fastapi/fastapi (25MB, Python) | 2 | Pydantic v1→v2 migration inventory; deprecated endpoint pattern catalog |
| <50MB | gin-gonic/gin (20MB, Go) | 1 | Deprecated middleware API migration inventory |
| 500MB-1GB | elastic/elasticsearch (900MB, Java) | 2 | Deprecated transport client migration; index settings API audit |
| 500MB-1GB | apache/spark (600MB, Java) | 2 | RDD→DataFrame migration inventory; deprecated MLlib API catalog |
| 500MB-1GB | dotnet/runtime (800MB, C#) | 1 | Obsolete API migration inventory across System.* namespaces |
| 3GB+ | tensorflow/tensorflow (3GB, C++) | 2 | tf.compat.v1 usage inventory; deprecated estimator API catalog |
| 3GB+ | llvm/llvm-project (5GB, C++) | 2 | Legacy pass manager → new PM migration; deprecated intrinsic audit |

#### csb_org_crossrepo (+8)

Multi-repo cross-repo dependency tracing. Pattern: trace shared library upgrades, API boundary impacts.

| Size Tier | Repos | Count | Task Ideas |
|-----------|-------|:-----:|------------|
| <50MB | fastapi + psf/requests (25+15MB) | 2 | Trace HTTP client dependency; shared model schema impact |
| <50MB | gin-gonic/gin + stretchr/testify (20+5MB) | 2 | Trace test helper dependency; shared interface upgrade impact |
| 3GB+ | linux + gcc (4+3GB, C) | 2 | Kernel API change impact on compiler builtins |
| 3GB+ | chromium + v8 (15+2GB, C++) | 2 | Blink→V8 API boundary trace; shared memory model deps |

#### csb_sdlc_fix (+8)

Single-repo bug fixes sourced from actual GitHub issues with known patches.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| <50MB | fastapi/fastapi (25MB, Python) | 2 | Fix from GitHub issues (dependency injection, routing bugs) |
| <50MB | pallets/flask (15MB, Python) | 2 | Fix from GitHub issues (blueprint, context bugs) |
| 3GB+ | tensorflow/tensorflow (3GB, C++) | 2 | Fix from GitHub issues (op registration, graph bugs) |
| 3GB+ | linux (4GB, C) | 2 | Fix from actual commits (driver bugs, memory leaks) |

#### csb_sdlc_refactor (+4)

Single-repo refactoring tasks.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| 500MB-1GB | cockroachdb/cockroach (700MB, Go) | 2 | Extract SQL planning logic; reduce duplication in KV client |
| 3GB+ | llvm/llvm-project (5GB, C++) | 2 | Refactor pass pipeline; extract target-independent codegen |

#### csb_sdlc_feature (+4)

Single-repo feature implementations sourced from actual GitHub issues.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| <50MB | fastapi/fastapi (25MB, Python) | 2 | Feature from GitHub issues (middleware, response model) |
| <50MB | gin-gonic/gin (20MB, Go) | 2 | Feature from GitHub issues (route groups, binding) |

### QUALITY (+56 tasks)

#### csb_org_incident (+16)

Multi-repo incident debugging. Pattern: trace production error to authoritative source, diagnose failure root cause.

| Size Tier | Repos | Count | Task Ideas |
|-----------|-------|:-----:|------------|
| <50MB | fastapi + psf/requests | 2 | Trace 422 validation error to Pydantic model source |
| <50MB | gin-gonic/gin + stretchr/testify | 2 | Trace panic in middleware to handler chain setup |
| 50-200MB | hashicorp/consul (80MB, Go) | 3 | Service mesh timeout trace; anti-entropy sync failure; ACL deny |
| 50-200MB | hashicorp/vault (150MB, Go) | 3 | Secret lease expiry trace; auth method failure; seal/unseal error |
| 3GB+ | linux (4GB, C) | 3 | Kernel oops trace to driver source; OOM kill path; IRQ storm |
| 3GB+ | chromium (15GB, C++) | 3 | Renderer crash trace; IPC channel failure; GPU process abort |

#### csb_org_security (+16)

Multi-repo vulnerability audit/remediation. Pattern: CVE remediation, TLS/auth audit, security config review.

| Size Tier | Repos | Count | Task Ideas |
|-----------|-------|:-----:|------------|
| <50MB | fastapi/fastapi (25MB, Python) | 3 | CORS misconfiguration audit; JWT validation gaps; SQLi in deps |
| <50MB | pallets/flask (15MB, Python) | 2 | Session cookie hardening; CSRF token validation audit |
| 50-200MB | hashicorp/vault (150MB, Go) | 3 | TLS cert rotation audit; secret engine auth boundary check |
| 50-200MB | redis/redis (80MB, C) | 2 | AUTH command bypass audit; protected mode configuration check |
| 500MB-1GB | elastic/elasticsearch (900MB, Java) | 3 | Transport layer TLS audit; API key scope validation; RBAC config |
| 500MB-1GB | apache/spark (600MB, Java) | 3 | Spark UI auth audit; executor secrets exposure; network encryption |

#### csb_org_compliance (+10)

Multi-repo compliance audit. Pattern: policy enforcement check, config coverage, audit log review.

| Size Tier | Repos | Count | Task Ideas |
|-----------|-------|:-----:|------------|
| <50MB | fastapi + gin-gonic/gin | 3 | API input validation coverage; error response consistency audit |
| 500MB-1GB | dotnet/runtime (800MB, C#) | 3 | CAS policy enforcement; assembly signing audit; crypto usage |
| 500MB-1GB | cockroachdb/cockroach (700MB, Go) | 2 | Audit log coverage; privilege escalation boundary check |
| 3GB+ | tensorflow/tensorflow (3GB, C++) | 2 | Model serialization safety audit; op kernel input validation |

#### csb_sdlc_test (+7)

Single-repo test writing tasks.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| <50MB | fastapi/fastapi (25MB, Python) | 3 | Write tests for dependency injection, middleware, WebSocket |
| <50MB | gin-gonic/gin (20MB, Go) | 2 | Write tests for route matching, parameter binding |
| 50-200MB | hashicorp/consul (80MB, Go) | 2 | Write tests for service discovery, health check logic |

#### csb_sdlc_secure (+4)

Single-repo security hardening tasks.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| <50MB | pallets/flask (15MB, Python) | 2 | Harden session management, add HSTS headers |
| 3GB+ | linux (4GB, C) | 2 | Harden ioctl input validation in driver subsystem |

#### csb_sdlc_debug (+3)

Single-repo regression debugging tasks.

| Size Tier | Repo | Count | Task Ideas |
|-----------|------|:-----:|------------|
| <50MB | tokio-rs/tokio (30MB, Rust) | 1 | Debug async task starvation regression |
| 3GB+ | chromium (15GB, C++) | 2 | Debug renderer memory leak; debug compositor frame drop |

---

## New Repos Being Introduced (13)

| Repo | Language | Size | Tasks | Notes |
|------|----------|------|:-----:|-------|
| fastapi/fastapi | Python | ~25MB | 19 | Anchor for <50MB tier. Used across 7 suites. |
| pallets/flask | Python | ~15MB | 6 | Second <50MB Python repo. |
| gin-gonic/gin | Go | ~20MB | 7 | <50MB Go repo. |
| tokio-rs/tokio | Rust | ~30MB | 1 | Expands Rust coverage. |
| psf/requests | Python | ~15MB | 2 | Paired with fastapi for multi-repo tasks. |
| stretchr/testify | Go | ~5MB | 2 | Paired with gin for multi-repo tasks. |
| hashicorp/consul | Go | ~80MB | 5 | 50-200MB Go infra. |
| hashicorp/vault | Go | ~150MB | 6 | 50-200MB Go infra. |
| redis/redis | C | ~80MB | 2 | 50-200MB C. |
| dotnet/runtime | C# | ~800MB | 4 | **NEW language coverage.** 500MB-1GB tier. |
| apache/spark | Java | ~600MB | 5 | 500MB-1GB Java. |
| elastic/elasticsearch | Java | ~900MB | 3 | Already in use (csb_sdlc tasks). Expand to org suites. |
| chromium/chromium | C++ | ~15GB | 7 | 3GB+ anchor. |
| tensorflow/tensorflow | C++/Python | ~3GB | 6 | 3GB+ anchor. |

---

## Scaffolding Instructions

### Use `/mine-tasks` for each repo

The `/mine-tasks` skill analyzes a repo and proposes benchmark tasks. For each repo in the plan, run it with the target suite and count. Example:

```
/mine-tasks --repo fastapi/fastapi --suite csb_org_security --count 3
/mine-tasks --repo fastapi/fastapi --suite csb_sdlc_fix --count 2
```

### For csb_sdlc_fix tasks: use SWE-Bench Pro approach

Bug fix tasks should be sourced from actual GitHub issues with merged PRs. Use the `scripts/scaffold_swebench_pro_tasks.py` pattern:
1. Find closed issues with 1-3 file patches
2. Use the pre-patch commit as the base
3. The merged patch is the ground truth

### For csb_org_* tasks: use CCX task pattern

Org tasks follow the `ccx-*` naming convention and use multi-repo Dockerfiles that `git clone` multiple repos. Follow the pattern in existing tasks like `ccx-incident-031` or `ccx-vuln-remed-011`.

### Task ID naming conventions

- SDLC tasks: `{repo}-{description}-{suite_suffix}-{NNN}` (e.g., `fastapi-pydantic-migration-feat-001`)
- Org tasks: `ccx-{suite_short}-{NNN}` (e.g., `ccx-migration-040`, continuing from highest existing number)

### Dockerfile requirements

- Every task needs `environment/Dockerfile` (full source for baseline) and `environment/Dockerfile.sg_only` (truncated source for MCP config)
- Use `scripts/generate_sgonly_dockerfiles.py --force` to generate sg_only variants after creating the base Dockerfile
- For 3GB+ repos: consider using shallow clones (`git clone --depth 1`) in Dockerfiles to keep image sizes manageable
- For multi-repo tasks: clone all repos in the Dockerfile

### Ground truth curation

After scaffolding, run the curator to generate ground truth:
```bash
set -a
source .env.local
python3 scripts/daytona_curator_runner.py --sdlc-all --missing-only --prompt-version phase1
```

For org tasks that use `scripts/curate_oracle.py`, use the same exported-env pattern so
`SOURCEGRAPH_ACCESS_TOKEN` is available to subprocesses:
```bash
set -a
source .env.local
python3 scripts/curate_oracle.py --task-dir benchmarks/csb_org_incident/ccx-incident-297 --mode deep --verify
```

### Validation

After scaffolding all 92 tasks:
1. Add them to `configs/selected_benchmark_tasks.json` via `scripts/select_benchmark_tasks.py`
2. Run `python3 scripts/validate_tasks_preflight.py` to verify all tasks are well-formed
3. Run `python3 scripts/repo_health.py` before committing

---

## Execution Priority

Scaffold in this order (highest impact on power first):

1. **csb_org_incident +16** and **csb_org_security +16** (Quality category, biggest gap)
2. **csb_org_migration +12** and **csb_org_crossrepo +8** (Implementation category)
3. **csb_org_compliance +10** (Quality)
4. **csb_sdlc_fix +8** and **csb_sdlc_test +7** (fill <50MB and 3GB+ tiers)
5. **Remaining 15** (csb_sdlc_feature, refactor, secure, debug)

---

## Verification After Expansion

Run the power analysis to confirm all dimensions reach 80%:

```bash
python3 scripts/suite_power_analysis.py  # after updating for new SUITE_TO_CATEGORY mapping
```

Expected final state: 496 tasks, all 5 pairwise/main-effect tests at ≥80% power for δ=0.05.
