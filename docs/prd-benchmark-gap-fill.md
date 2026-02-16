# PRD: Benchmark Gap-Fill — Six New/Expanded Task Workstreams

## Introduction

CodeContextBench's existing 13 benchmark suites have significant ceiling saturation and coverage gaps that limit our ability to measure MCP value. RepoQA scores 1.000/1.000 on both configs. K8s Docs plateaus at 0.920 with zero MCP delta. CodeReview has only 3 tasks (2 at ceiling). Investigation just ran at 0.960-0.985. LoCoBench is being dropped entirely.

This PRD covers 7 workstreams to fill identified gaps, adding 38-56 new tasks across new and expanded suites, targeting new enterprise-scale repositories to be forked into the sg-benchmarks GitHub org for Sourcegraph indexing.

## Goals

- Eliminate ceiling saturation by designing tasks where baseline agents score 0.3-0.7 (not 0.9+)
- Create measurable MCP delta by requiring capabilities that MCP tools directly enable (cross-repo search, symbol resolution, commit history)
- Cover 7 task types currently missing or under-covered: Enterprise NL Q&A, Cross-Repo Symbol Lookup, Code Review (expanded), Security Vulnerability Triage, Onboarding Exploration, Advanced Doc Generation, Harder Investigation
- Add 5-8 tasks per workstream for statistical power
- Formally archive saturated ccb_repoqa (replaced by ccb_nlqa)
- Target new enterprise-scale repos (Envoy, Istio, Terraform, VS Code, Cilium, etc.) for broader coverage
- All tasks Harbor-compatible with automated verifiers (no manual scoring)

## Suite Organization

| Workstream | Suite | Type | Why |
|------------|-------|------|-----|
| Enterprise NL Q&A | `ccb_nlqa` | **NEW** | Replaces saturated ccb_repoqa + dropped LoCoBench |
| Cross-Repo Symbol Lookup | `ccb_crossrepo` | **EXPAND** | Adds symbol-resolution tasks to existing cross-repo suite |
| Code Review Expansion | `ccb_codereview` | **EXPAND** | Adds 5 harder tasks to existing 3-task suite |
| Security Vuln Triage | `ccb_security` | **NEW** | Genuinely new task type, no existing coverage |
| Onboarding Exploration | `ccb_onboarding` | **NEW** | Genuinely new task type, distinct from investigation |
| Advanced Doc Generation | `ccb_docgen` | **NEW** | Supersedes ceiling-saturated ccb_k8sdocs |
| Harder Investigation | `ccb_investigation` | **EXPAND** | Existing 4 tasks at 0.96-0.985 ceiling, need harder variants |

### Archival

| Suite | Action | Reason |
|-------|--------|--------|
| `ccb_repoqa` | **ARCHIVE** | 10/10 perfect on both configs, zero signal. Replaced by `ccb_nlqa` |
| `ccb_locobench` | **DROP** | Not suitable for our needs (already decided) |

## New Repository Targets

Tasks should draw from enterprise-scale repos not currently in our benchmark pool. Priority targets for Sourcegraph indexing:

| Repository | Language | Size | Why |
|------------|----------|------|-----|
| `envoyproxy/envoy` | C++ | ~2M LOC | Complex proxy with filter chains, xDS protocol |
| `istio/istio` | Go | ~800K LOC | Service mesh spanning pilot/galley/citadel components |
| `hashicorp/terraform` | Go | ~1.2M LOC | Provider/plugin architecture, state management |
| `microsoft/vscode` | TypeScript | ~3M LOC | Extension API, renderer/main process split |
| `cilium/cilium` | Go/C | ~1.5M LOC | eBPF datapath, Kubernetes network policies |
| `argoproj/argo-cd` | Go | ~400K LOC | GitOps reconciliation, multi-cluster management |
| `apache/kafka` | Java | ~1.2M LOC | Distributed streaming, replication protocol |
| `curl/curl` | C | ~300K LOC | Security-critical HTTP client (many CVEs for security tasks) |

Existing indexed repos (Django, Kubernetes, Grafana, Prometheus) may also be reused where appropriate, but should NOT be the primary source for new tasks.

---

## User Stories

---

### Workstream 1: Enterprise NL Codebase Q&A (`ccb_nlqa`)

**Replaces:** Saturated ccb_repoqa (10/10 perfect) and dropped LoCoBench. Targets multi-hop reasoning questions about enterprise codebases that require cross-package understanding.

**Design principles:**
- Questions require tracing through 3+ packages/modules (not findable by single grep)
- Answers must include specific file:line evidence (verifiable)
- Partial credit scoring via weighted checklist (like investigation tasks)
- Questions aligned with what a senior engineer would ask when debugging or reviewing

#### US-001: Scaffold ccb_nlqa benchmark suite
**Description:** As a benchmark developer, I want to create the ccb_nlqa suite infrastructure so that NL Q&A tasks can be added.

**Acceptance Criteria:**
- [ ] `benchmarks/ccb_nlqa/` directory created with suite-level CLAUDE.md
- [ ] `configs/nlqa_2config.sh` created following `_common.sh` patterns (baseline + SG_full)
- [ ] Suite registered in `configs/selected_benchmark_tasks.json` schema
- [ ] Shared test harness (`tests/test.sh`) using weighted checklist scoring (reuse investigation pattern)
- [ ] Ground truth format documented: `ground_truth.json` with required_findings, file_references, causal_chain sections

#### US-002: Create 3 multi-hop architecture Q&A tasks
**Description:** As a benchmark evaluator, I want tasks that test multi-hop architectural reasoning so that I can measure whether MCP tools help agents trace complex code flows.

**Acceptance Criteria:**
- [ ] 3 tasks created, each targeting a different repo (e.g., Envoy filter chain, Istio control plane, Terraform provider lifecycle)
- [ ] Each question requires tracing through 3+ packages to answer correctly
- [ ] Ground truth includes 5-8 required findings with file path evidence
- [ ] Baseline agent expected score: 0.3-0.5 (verified via dry run)
- [ ] MCP expected advantage: `find_references` + `go_to_definition` for tracing call chains
- [ ] task.toml with difficulty=hard, time_limit_sec=1200, language and repo fields populated
- [ ] Dockerfile clones target repo at pinned commit SHA

#### US-003: Create 3 cross-package data flow Q&A tasks
**Description:** As a benchmark evaluator, I want tasks asking "how does data X flow from input to output" so that I can test whether MCP search enables tracing data through transformation layers.

**Acceptance Criteria:**
- [ ] 3 tasks created targeting data-heavy systems (e.g., Kafka message lifecycle, Envoy request routing, Argo CD sync reconciliation)
- [ ] Each answer requires identifying 4+ transformation points with file references
- [ ] Partial credit: each transformation point scored independently (not all-or-nothing)
- [ ] Questions phrased as "Trace the path of X from A to B, identifying every transformation"
- [ ] Ground truth includes ordered causal chain with file:function references
- [ ] Dockerfile and task.toml complete per suite conventions

#### US-004: Create 2 "why does this behave this way" debugging Q&A tasks
**Description:** As a benchmark evaluator, I want tasks that present surprising behavior and ask the agent to explain the root cause, testing deep code comprehension.

**Acceptance Criteria:**
- [ ] 2 tasks: agent given a specific behavior observation and must explain WHY it happens
- [ ] Answer requires understanding interaction between 2+ subsystems
- [ ] Ground truth includes required root cause mechanism + negative checks (must NOT blame wrong components)
- [ ] Repos: choose from new targets (VS Code, Cilium) for diversity
- [ ] Expected baseline score: 0.3-0.5

---

### Workstream 2: Cross-Repo Symbol Lookup (expand `ccb_crossrepo`)

**Expands:** Existing ccb_crossrepo (5 tasks focused on migration/reasoning). Adds tasks where the PRIMARY goal is locating symbol definitions, usages, and interfaces across repository boundaries.

**Design principles:**
- Agent must use `find_references`, `go_to_definition` across repos
- Output is structured: list of locations, callers, implementors
- Partial credit per correctly identified location
- Baseline agents must manually clone + grep multiple repos (slow, error-prone)

#### US-005: Create 3 "find all callers" cross-repo tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must find all callers of a specific function/interface across 2-3 repositories.

**Acceptance Criteria:**
- [ ] 3 tasks created, each involving 2-3 repos that share interfaces (e.g., gRPC service definitions consumed across repos, shared Go interfaces, npm packages)
- [ ] Agent must produce structured output: `callers.json` with `[{repo, file, line, function, context}]`
- [ ] Scoring: precision + recall F1 against ground truth caller list
- [ ] Ground truth has 8-15 callers per task (enough for meaningful F1)
- [ ] MCP advantage: `find_references` directly solves this; baseline must grep across repos
- [ ] Repos from new targets: e.g., Istio calling Envoy APIs, Terraform calling provider interfaces, Argo CD calling K8s client-go
- [ ] task.toml with category=symbol_resolution, Dockerfiles clone all required repos

#### US-006: Create 2 "trace interface implementors" cross-repo tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must find all implementations of a shared interface across repositories.

**Acceptance Criteria:**
- [ ] 2 tasks: given an interface definition (e.g., Go interface, TypeScript type, Java interface), find all concrete implementations across 2-3 repos
- [ ] Output: `implementors.json` with `[{repo, file, line, class_or_struct, methods_implemented}]`
- [ ] Scoring: F1 on implementor identification + bonus for correctly listing methods
- [ ] Ground truth has 5-10 implementors per task
- [ ] Dockerfiles clone multiple repos, task.toml references all repos

#### US-007: Create 2 "dependency chain resolution" cross-repo tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must trace a symbol's definition through a chain of package dependencies (A imports B imports C, where is the original definition?).

**Acceptance Criteria:**
- [ ] 2 tasks involving 3-level dependency chains across repos
- [ ] Agent must produce the full chain: `{usage_site, re_export, original_definition}` with file:line for each
- [ ] Scoring: points for each correctly identified link in the chain
- [ ] Choose dependency chains that cross repo boundaries (e.g., K8s → client-go → apimachinery)
- [ ] MCP advantage: `go_to_definition` with cross-repo jump is the killer feature here

---

### Workstream 3: Code Review Expansion (expand `ccb_codereview`)

**Expands:** Existing ccb_codereview (3 tasks, 2/3 at baseline ceiling). Adds harder reviews with subtler bugs, larger PRs, and multi-file defect chains where MCP's `find_references` reveals non-obvious impact.

**Design principles:**
- Larger PRs (4-8 files changed, not 2-3)
- Subtler defects: race conditions, security-adjacent logic, incorrect error propagation
- Multi-file defect chains: bug in file A only manifests because of assumption in file B
- Scoring: detection F1 + fix quality (existing hybrid scorer pattern)

#### US-008: Create 3 "subtle multi-file defect" code review tasks
**Description:** As a benchmark evaluator, I want code review tasks with defects that span multiple files, requiring cross-file reasoning to detect.

**Acceptance Criteria:**
- [ ] 3 tasks, each with 4-8 files in the review scope
- [ ] Each task has 5-7 injected defects, at least 2 requiring cross-file reasoning
- [ ] Cross-file defects: e.g., function A changes return type but caller B still expects old type; config value in file C not propagated to file D
- [ ] Repos: Envoy (C++), VS Code (TypeScript), Terraform (Go) — one per language
- [ ] Reuse existing scoring pattern: 50% detection F1 + 50% fix quality
- [ ] inject_defects.sh + expected_defects.json + expected_patches/ per task
- [ ] Expected baseline score: 0.4-0.6 (harder than current 0.93)
- [ ] MCP advantage: `find_references` reveals callers affected by the change

#### US-009: Create 2 "security-adjacent review" code review tasks
**Description:** As a benchmark evaluator, I want code review tasks with security-relevant defects (not full CVE triage, but security-flavored review bugs).

**Acceptance Criteria:**
- [ ] 2 tasks with defects including: missing input validation, incorrect auth checks, TOCTOU races, unsafe deserialization
- [ ] Repos: curl (C) or similar security-critical project, plus one web framework
- [ ] Each task has 4-6 defects, at least 2 security-relevant
- [ ] Scoring weights security defects higher (critical/high severity in expected_defects.json)
- [ ] Expected baseline score: 0.3-0.5 (security bugs are hard to spot)
- [ ] MCP advantage: `diff_search` for similar past security fixes, `find_references` for checking all callers of unsafe function

---

### Workstream 4: Security Vulnerability Triage (`ccb_security`)

**New suite.** Agent receives a CVE advisory or vulnerability report and must: locate affected code, assess exploitability, trace attack paths, and produce a structured triage report. Pure analysis (no code fixes).

**Design principles:**
- Real CVEs with known resolutions (ground truth exists)
- Agent must search code to find vulnerable paths (not told which file)
- Partial credit: finding the vulnerable function, tracing the call path, assessing severity
- MCP value: `commit_search` for when vuln was introduced, `find_references` for reachability analysis, `diff_search` for related patches

#### US-010: Scaffold ccb_security benchmark suite
**Description:** As a benchmark developer, I want to create the ccb_security suite infrastructure.

**Acceptance Criteria:**
- [ ] `benchmarks/ccb_security/` directory created with suite-level CLAUDE.md
- [ ] `configs/security_2config.sh` created following `_common.sh` patterns
- [ ] Suite registered in selected_benchmark_tasks.json
- [ ] Shared test harness using weighted checklist scoring
- [ ] Output format: `/logs/agent/triage.md` with Summary, Affected Code, Attack Path, Severity Assessment, Remediation sections
- [ ] Ground truth format: `ground_truth.json` with vulnerable_functions, call_paths, severity_classification, negative_checks

#### US-011: Create 3 "locate vulnerable code from CVE" tasks
**Description:** As a benchmark evaluator, I want tasks where the agent receives a CVE description and must locate the vulnerable code in a large codebase.

**Acceptance Criteria:**
- [ ] 3 tasks using real CVEs in large C/Go/Python codebases
- [ ] CVE description provided (from NVD advisory text), but NOT the affected file/function
- [ ] Agent must identify: vulnerable function(s), vulnerable code pattern, which versions affected
- [ ] Ground truth: specific file:line:function for each vulnerable point
- [ ] Repos pinned to pre-fix commit (so vulnerable code is present)
- [ ] Candidate CVEs: curl (many well-documented CVEs), Envoy (security-focused advisories), Terraform (provider-side vulns)
- [ ] Expected baseline score: 0.3-0.5 (finding the needle in a large codebase)
- [ ] MCP advantage: `keyword_search` for vulnerability patterns, `commit_search` for related fixes

#### US-012: Create 3 "trace attack path / assess exploitability" tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must trace whether a known vulnerability is actually reachable from external input.

**Acceptance Criteria:**
- [ ] 3 tasks: agent given the vulnerable function (known) and must determine reachability
- [ ] Must trace from external entry points (HTTP handlers, CLI args, file parsers) to vulnerable function
- [ ] Output includes: full call chain, input constraints, exploitability assessment (exploitable/mitigated/unreachable)
- [ ] Ground truth includes the complete attack path with intermediate functions
- [ ] At least 1 task where the vuln is NOT reachable (agent must correctly identify as mitigated)
- [ ] MCP advantage: `find_references` traces callers; `go_to_definition` resolves function implementations
- [ ] Repos: choose projects with clear entry points (HTTP servers, CLI tools)

#### US-013: Create 2 "transitive dependency vulnerability" tasks
**Description:** As a benchmark evaluator, I want tasks where a vulnerability exists in a transitive dependency and the agent must determine if the consuming project is affected.

**Acceptance Criteria:**
- [ ] 2 tasks: vulnerable code is in dependency X, consuming project Y uses X transitively
- [ ] Agent must: identify which functions from X are used by Y, determine if vulnerable code paths are actually called
- [ ] Output: reachability assessment with evidence chain
- [ ] Ground truth: specific import chain + whether the vulnerable function IS actually called
- [ ] One task should be "yes, affected" and one should be "no, not reachable"
- [ ] MCP advantage: cross-repo `find_references` is the killer feature for dependency chain tracing

---

### Workstream 5: Onboarding Exploration (`ccb_onboarding`)

**New suite.** Simulates a new engineer's first day exploring an unfamiliar codebase. Agent must answer structured onboarding questions by exploring the repository. Pure analysis (no code changes).

**Design principles:**
- Questions a new hire would ask: "what does this service do?", "how do I add a new endpoint?", "what's the testing strategy?"
- Requires broad exploration, not deep single-file reading
- Partial credit per question answered correctly
- Distinct from investigation (which provides specific symptoms) and NL Q&A (which asks specific technical questions)

#### US-014: Scaffold ccb_onboarding benchmark suite
**Description:** As a benchmark developer, I want to create the ccb_onboarding suite infrastructure.

**Acceptance Criteria:**
- [ ] `benchmarks/ccb_onboarding/` directory created with suite-level CLAUDE.md
- [ ] `configs/onboarding_2config.sh` created following `_common.sh` patterns
- [ ] Shared test harness using weighted checklist scoring
- [ ] Output format: `/logs/agent/onboarding.md` with structured answers to numbered questions
- [ ] Ground truth: per-question findings with regex patterns for key concepts

#### US-015: Create 3 "codebase orientation" onboarding tasks
**Description:** As a benchmark evaluator, I want tasks that test an agent's ability to quickly orient in a new codebase — understanding project structure, entry points, key abstractions.

**Acceptance Criteria:**
- [ ] 3 tasks, each targeting a different large repo (e.g., Cilium, Argo CD, Kafka)
- [ ] Each task poses 5-7 onboarding questions: "What is the main entry point?", "What are the core packages and their responsibilities?", "How is configuration loaded?", "What's the test structure?", "How would you add a new [feature type]?"
- [ ] Ground truth per question: required concepts/files that must appear in answer
- [ ] Scoring: weighted average across questions (not all-or-nothing)
- [ ] MCP advantage: `list_files` for structure discovery, `nls_search` for finding entry points, `read_file` for understanding patterns
- [ ] Expected baseline score: 0.4-0.6 (broad exploration is slow without search tools)

#### US-016: Create 3 "team handoff" onboarding tasks
**Description:** As a benchmark evaluator, I want tasks simulating receiving ownership of an unfamiliar service, requiring the agent to produce a handoff document.

**Acceptance Criteria:**
- [ ] 3 tasks: agent given a subsystem/service within a larger codebase and must produce a team handoff doc
- [ ] Handoff doc must cover: purpose, dependencies (upstream/downstream), key files, failure modes, how to deploy, how to debug
- [ ] Target subsystems that have clear boundaries but non-obvious dependencies
- [ ] Ground truth: required sections with key facts per section
- [ ] Repos from new targets: e.g., Envoy's ext_authz filter, Terraform's state backend, Cilium's eBPF datapath
- [ ] MCP advantage: `find_references` for discovering downstream consumers, `keyword_search` for deployment/config patterns

#### US-017: Create 2 "development workflow discovery" onboarding tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must figure out how to contribute to a project — build system, test commands, CI pipeline, PR process.

**Acceptance Criteria:**
- [ ] 2 tasks targeting projects with non-trivial build systems (e.g., Envoy's Bazel build, Kafka's Gradle build)
- [ ] Agent must produce a "contributor guide" covering: build prerequisites, how to build, how to run tests, how to run a subset of tests, CI pipeline overview
- [ ] Ground truth: specific build commands, test commands, CI file locations
- [ ] Scoring: per-item accuracy (correct build command = 1 point, wrong = 0)
- [ ] MCP advantage: `list_files` + `read_file` for finding Makefiles, CI configs, CONTRIBUTING.md

---

### Workstream 6: Advanced Doc Generation (`ccb_docgen`)

**New suite.** Supersedes ceiling-saturated ccb_k8sdocs (0.920 plateau, zero MCP delta). Tasks require generating documentation for complex, multi-package systems where understanding the code requires cross-referencing multiple components.

**Design principles:**
- Larger scope than K8s Docs: document a subsystem spanning 5-10 packages, not a single package
- Require understanding non-obvious interactions (not just listing public APIs)
- Output is a structured markdown document, scored on coverage of key concepts
- Harder baseline: large scope means agent can't read everything in time without search tools

#### US-018: Scaffold ccb_docgen benchmark suite
**Description:** As a benchmark developer, I want to create the ccb_docgen suite infrastructure.

**Acceptance Criteria:**
- [ ] `benchmarks/ccb_docgen/` directory created with suite-level CLAUDE.md
- [ ] `configs/docgen_2config.sh` created following `_common.sh` patterns
- [ ] Shared test harness using weighted checklist scoring (topic coverage + accuracy)
- [ ] Output format: markdown doc at `/workspace/documentation.md`
- [ ] Ground truth: required_topics (weighted), required_file_references, required_examples

#### US-019: Create 3 "subsystem architecture doc" tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must produce an architecture document for a complex subsystem, explaining how components interact.

**Acceptance Criteria:**
- [ ] 3 tasks targeting multi-package subsystems in large repos
- [ ] Candidate subsystems: Envoy's HTTP connection manager (filter chain + codec + router), Istio's Pilot discovery (xDS serving + config translation + service registry), Terraform's plan/apply pipeline (graph builder + provider interface + state management)
- [ ] Output: architecture doc with diagrams described in text, component responsibilities, data flow, extension points
- [ ] Ground truth: 10-15 required concepts with file references
- [ ] Scoring: weighted topic coverage (each concept is a fraction of total score)
- [ ] Expected baseline score: 0.3-0.5 (too much code to read without search tools)
- [ ] MCP advantage: `nls_search` for discovering components, `find_references` for tracing interactions

#### US-020: Create 3 "API reference with usage examples" tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must generate API reference documentation including non-obvious usage patterns found in tests and internal callers.

**Acceptance Criteria:**
- [ ] 3 tasks: document a public API surface including parameter semantics, error cases, and usage examples extracted from tests/internal callers
- [ ] Must go beyond just listing function signatures — include behavioral notes from implementation
- [ ] Ground truth: required API methods documented, required behavioral notes, required examples
- [ ] Repos: VS Code extension API, Cilium eBPF map API, Kafka consumer API
- [ ] MCP advantage: `find_references` to discover usage patterns, `read_file` for test examples
- [ ] Expected baseline score: 0.4-0.6

#### US-021: Create 2 "migration guide from code changes" tasks
**Description:** As a benchmark evaluator, I want tasks where the agent must produce a migration guide by analyzing breaking changes between two versions of a codebase.

**Acceptance Criteria:**
- [ ] 2 tasks: Dockerfile provides two commits (old version, new version), agent must produce migration guide
- [ ] Guide must cover: what changed, why, how to update consuming code, common pitfalls
- [ ] Ground truth: required breaking changes identified, correct migration steps per change
- [ ] MCP advantage: `compare_revisions` directly compares the two versions, `diff_search` finds related changes
- [ ] Repos: choose projects with well-documented breaking changes (Terraform provider SDK v1→v2, etc.)

---

### Workstream 7: Harder Investigation (expand `ccb_investigation`)

**Expands:** Existing ccb_investigation (4 tasks scoring 0.96-0.985 — near ceiling). Adds tasks with deeper causal chains, larger codebases, and more ambiguous symptoms where MCP search tools provide genuine differentiation.

**Design principles:**
- Longer causal chains: root cause is 4-5 hops from the symptom (not 2-3)
- Larger search space: spread across 8-15 packages (not 3-5)
- Red herrings: plausible-but-wrong explanations the agent must rule out (scored via negative checks)
- Ambiguous symptoms: multiple possible root causes, agent must identify the correct one with evidence
- Same output format as existing investigation tasks (`/logs/agent/investigation.md`)

#### US-022: Create 3 "deep causal chain" investigation tasks
**Description:** As a benchmark evaluator, I want investigation tasks with longer causal chains (4-5 hops) where the root cause is far from the symptom, requiring sustained cross-package tracing.

**Acceptance Criteria:**
- [ ] 3 tasks where the symptom appears in package A but root cause is in package D/E, with 3+ intermediate packages in the chain
- [ ] Repos from new targets: Envoy (filter chain → connection manager → codec → upstream), Istio (Pilot → xDS → Envoy config → runtime behavior), Terraform (CLI → backend → state → provider)
- [ ] Each task has 8-12 required findings (vs 5-8 in current tasks) with higher weight on full causal chain
- [ ] Negative checks: at least 2 plausible-but-wrong explanations per task (e.g., "must NOT blame the network layer")
- [ ] Expected baseline score: 0.3-0.5 (current tasks score 0.9+ — these must be significantly harder)
- [ ] MCP advantage: `find_references` to trace through intermediate packages, `commit_search` to find when the bug was introduced

#### US-023: Create 3 "multi-component interaction" investigation tasks
**Description:** As a benchmark evaluator, I want investigation tasks where the bug emerges from interaction between 3+ independent components, not from a single faulty function.

**Acceptance Criteria:**
- [ ] 3 tasks where the root cause is an emergent interaction (e.g., race condition between scheduler + controller + kubelet, or config drift between Envoy control plane + data plane + health check)
- [ ] Agent must identify ALL interacting components and explain the specific interaction that fails
- [ ] Scoring heavily weights the interaction mechanism (not just "which files are involved")
- [ ] Ground truth includes the timing/ordering/state conditions under which the bug manifests
- [ ] Repos: Kubernetes (multi-controller interaction), Cilium (eBPF + userspace + k8s watch), Kafka (producer + broker + consumer interaction failure)
- [ ] Expected baseline score: 0.2-0.4 (interaction bugs are among the hardest to diagnose)

#### US-024: Create 2 "historical regression hunt" investigation tasks
**Description:** As a benchmark evaluator, I want investigation tasks where the agent must use commit history to find when/why a regression was introduced, not just where the bug is now.

**Acceptance Criteria:**
- [ ] 2 tasks: Dockerfile provides the repo at a post-regression commit, agent must find the regressing commit and explain why it broke things
- [ ] Ground truth: specific commit SHA, author, changed function, and mechanism of regression
- [ ] Agent must produce evidence: "commit X changed function Y in way Z, which broke assumption W"
- [ ] MCP advantage: `commit_search` + `diff_search` + `compare_revisions` are the primary tools — this is the one task type where commit-based MCP tools are essential
- [ ] Repos: choose real regressions with clear bisection points (Grafana dashboard migrations, Prometheus recording rules)
- [ ] Expected baseline score: 0.2-0.4 (baseline agents lack commit search capability)

---

## Functional Requirements

### Infrastructure

- FR-1: Each new suite (`ccb_nlqa`, `ccb_security`, `ccb_onboarding`, `ccb_docgen`) must have a `configs/{suite}_2config.sh` script supporting `--parallel`, `--baseline-only`, `--full-only`, `--task TASK_ID` flags. Expanded suites (`ccb_crossrepo`, `ccb_codereview`, `ccb_investigation`) already have configs — just add new tasks.
- FR-2: All new tasks must be registered in `configs/selected_benchmark_tasks.json` with complete metadata (benchmark, task_id, repo, language, difficulty, mcp_benefit_score)
- FR-3: All Dockerfiles must pin repos to specific commit SHAs (no `--depth 1` to HEAD)
- FR-4: All test.sh scripts must produce machine-parseable scores (0.0-1.0 float to stdout)
- FR-5: New repos must be indexed in Sourcegraph (either public GitHub or sg-benchmarks mirrors) before SG_full runs
- FR-6: `scripts/generate_manifest.py` DIR_PREFIX_TO_SUITE mapping must include new suite prefixes
- FR-7: `scripts/aggregate_status.py` must recognize new suite directories

### Task Quality

- FR-8: Every task must have a ground truth that supports partial credit (no binary pass/fail)
- FR-9: Every task must target baseline agent scores of 0.3-0.6 (verified via at least 1 dry run before production runs)
- FR-10: Every task instruction.md must NOT contain MCP/Sourcegraph references (MCP guidance injected at runtime via preamble)
- FR-11: Every Dockerfile must build successfully in under 5 minutes
- FR-12: Every test.sh must complete scoring in under 60 seconds
- FR-13: Time limits: analysis-only tasks 900-1200s, code-change tasks 1200-1800s

### Scoring

- FR-14: Analysis tasks (nlqa, security, onboarding, docgen) use weighted checklist scoring: `ground_truth.json` with sections weighted by importance
- FR-15: Code review tasks use hybrid scoring: 50% detection F1 + 50% fix quality
- FR-16: Cross-repo symbol tasks use F1 scoring: precision and recall against ground truth location lists
- FR-17: All scorers must handle empty/missing output gracefully (score = 0.0, not crash)

## Non-Goals

- **No batch change generation tasks** — agentic batch solution is WIP, defer to future PRD
- **No replacement of existing passing tasks** — K8s Docs remains in suite for backward compatibility, new tasks carry the measurement signal. RepoQA formally archived (fully saturated).
- **No multi-container Dockerfiles** — multi-repo tasks clone all repos into a single container (decided)
- **No multi-turn conversational tasks** — all tasks are single-turn agent invocations
- **No tasks requiring internet access** — all repos cloned locally in Docker, no live API calls
- **No custom MCP server modifications** — tasks must work with standard Sourcegraph MCP tools
- **No tasks shorter than 5 minutes** — trivial tasks don't differentiate MCP value

## Technical Considerations

### Sourcegraph Indexing
- All 8 new repo targets fork into `sg-benchmarks` GitHub org → automatically indexed by Sourcegraph
- For repos >2GB, use orphan commit at pinned SHA (proven pattern from Linux kernel mirrors)
- Cross-repo symbol tasks require ALL referenced repos to be in sg-benchmarks for `find_references` to work cross-repo
- Index must be at the same commit SHA pinned in the Dockerfile
- This is straightforward: fork to sg-benchmarks = indexed. No special requests needed.

### Verifier Reuse
- Analysis tasks (nlqa, security, onboarding, docgen) can share a common weighted-checklist verifier (generalize investigation's `test.sh`)
- Code review expansion tasks reuse existing `ccb_codereview` scoring pattern (inject_defects.sh + hybrid F1 scorer)
- Cross-repo symbol tasks need a new F1 scorer for structured JSON output (`callers.json`, `implementors.json`)

### Difficulty Calibration
- Run each task once with haiku model (cheap, fast) to verify it's not trivially solvable
- Run once with opus baseline to estimate baseline score range
- Target: haiku < 0.2, opus baseline 0.3-0.6, opus SG_full 0.5-0.8
- If baseline scores > 0.7, add complexity (more packages to trace, more subtle findings required)

## Success Metrics

- **Coverage**: All 7 workstreams have 5-8 tasks each (38-56 total new tasks)
- **Discrimination**: Average baseline score per new suite is 0.3-0.6 (not ceiling-saturated)
- **MCP signal**: At least 5/7 workstreams show measurable SG_full delta > +0.05
- **Reliability**: All tasks produce consistent scores across 2+ runs (variance < 0.1)
- **Production**: All tasks pass `/validate-tasks` preflight checks
- **Integration**: MANIFEST correctly tracks all new tasks, `/generate-report` includes them

## Resolved Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Repo indexing | Fork to sg-benchmarks org = automatically indexed. No special timeline needed. |
| 2 | Cross-repo Dockerfiles | Single container with multiple `git clone` commands. |
| 3 | CVE selection | CVEs with public patches only — enables verifiable ground truth. |
| 4 | RepoQA | Formally archive. Fully saturated (1.000/1.000), zero signal. |
| 5 | Investigation ceiling | Add harder tasks (Workstream 7: US-022, US-023, US-024 — 8 new tasks). |
| 6 | Scoring normalization | Proportional to task count (not equal weight per suite). |
