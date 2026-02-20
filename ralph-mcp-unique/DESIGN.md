# MCP-Unique Org-Scale Context Retrieval Benchmark — Design Document

## 1. Objective

Extend CodeContextBench to measure what local-only agents **cannot** do: cross-repo
discovery, cross-host symbol resolution, dependency tracing, and deep-search-driven
investigation in polyrepo environments with 5–20+ repos spanning multiple code hosts.

The extension:
1. Translates 100 GTM use cases into a structured task registry
2. Adds task templates + generators for rapid task authoring
3. Provides exit-code-first deterministic evaluation (SWE-Factory)
4. Supports optional rubric judging for narrative tasks (PRDBench)
5. Adds MCP retrieval metrics (coverage, latency, scope) from run logs
6. Includes a starter pack of 10 validated tasks across 5 categories

## 2. Methodology Alignment

### SWE-Factory Patterns Adopted
| Pattern | Adoption | CCB Implementation |
|---------|----------|-------------------|
| Exit-code-first grading | Full | eval.sh returns exit 0/1; reward.txt for Harbor |
| Fail2Pass validity gate | Full | validate_mcp_task_instance.py checks oracle=pass, empty=fail |
| Environment memory pool | Partial | Reuse base images per repo-set fixture family |
| Targeted iteration | Partial | Generator creates stubs; manual oracle curation |

### PRDBench Patterns Adopted
| Pattern | Adoption | CCB Implementation |
|---------|----------|-------------------|
| PRD-centered task spec | Full | task_spec.json per task with user_story + constraints |
| AAA criteria scheme | Full | tests/criteria.json with Arrange-Act-Assert entries |
| Agent-as-judge | Opt-in | run_judge.py --hybrid mode for E/F category tasks |
| Multi-format evaluation | Full | oracle_checks.py supports 6 check types |
| Human alignment | Deferred | Existing judge agreement module (agreement.py) |

## 3. Architecture

```
                   ┌──────────────────────┐
                   │  Use Case Registry   │   configs/use_case_registry.json
                   │  (100 entries)       │   100 GTM use cases, metadata,
                   │                      │   MCP capabilities, oracle types
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐
                   │  Repo-Set Fixtures   │   fixtures/repo_sets/*.json
                   │  (5+ fixtures)       │   local vs MCP-only repos
                   │                      │   per code host
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐
                   │  Task Generator      │   scripts/generate_mcp_unique_tasks.py
                   │  + Templates         │   templates/mcp_unique_task/*.j2
                   └──────────┬───────────┘
                              │ generates
                   ┌──────────▼───────────┐
                   │  Task Directories    │   benchmarks/ccb_*/mcp-*-NNN/
                   │  task.toml           │     task_spec.json
                   │  instruction.md      │     eval.sh + oracle_answer.json
                   │  Dockerfile[.sg_only]│     criteria.json (optional)
                   └──────────┬───────────┘
                              │ executed by
                   ┌──────────▼───────────┐
                   │  Harbor Runner       │   configs/run_selected_tasks.sh
                   │  (baseline + SG_full)│   configs/sdlc_suite_2config.sh
                   └──────────┬───────────┘
                              │ produces
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │  result.json  │  │ eval score    │  │ transcript    │
   │  (Harbor)     │  │ (exit code)   │  │ (claude-code) │
   └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │ extracted by
                   ┌──────────▼───────────┐
                   │  Metrics Extractors  │
                   │  retrieval.py        │  oracle coverage, time-to-hit
                   │  oracle_checks.py    │  file/symbol/chain precision
                   │  run_judge.py        │  hybrid judge (optional)
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐
                   │  Eval Report         │   generate_eval_report.py
                   │  (sliced by category │   MCP retrieval section
                   │   mcp_unique, host)  │   baseline vs MCP comparison
                   └──────────────────────┘
```

## 4. Key Schemas

### 4.1 Use Case Registry Entry

```json
{
  "use_case_id": 1,
  "category": "A",
  "title": "Cross-repo blast radius analysis",
  "customer_prompt": "When we change a shared library, which services will be affected?",
  "task_family": "cross-repo-dep-trace",
  "sdlc_suite": "ccb_design",
  "mcp_unique": true,
  "mcp_capabilities_required": ["keyword_search", "find_references", "read_file"],
  "oracle_type": "deterministic_json",
  "oracle_check_types": ["file_set_match", "provenance"],
  "repo_set_id": "kubernetes-ecosystem",
  "difficulty": "hard",
  "estimated_repos_needed": 5,
  "salesforce_flags": {
    "code_reuse": true,
    "code_health": true
  },
  "gong_evidence": {
    "keywords": ["blast radius", "dependencies across services"],
    "example_quotes": ["Find code that exists somewhere in the org"]
  }
}
```

### 4.2 Repo-Set Fixture

```json
{
  "repo_set_id": "kubernetes-ecosystem",
  "description": "Kubernetes core + client libraries for dependency tracing tasks",
  "repos": [
    {
      "host": "github.com",
      "org": "kubernetes",
      "repo_name": "kubernetes",
      "full_name": "github.com/kubernetes/kubernetes",
      "revision": "v1.29.0",
      "logical_name": "k8s-core",
      "access_mode": "local_checkout",
      "sourcegraph_indexed": true
    },
    {
      "host": "github.com",
      "org": "kubernetes",
      "repo_name": "client-go",
      "full_name": "github.com/kubernetes/client-go",
      "revision": "v0.29.0",
      "logical_name": "k8s-client-go",
      "access_mode": "mcp_only",
      "sourcegraph_indexed": true
    }
  ],
  "local_checkout_repos": ["github.com/kubernetes/kubernetes"],
  "mcp_only_repos": ["github.com/kubernetes/client-go", "github.com/kubernetes/api", "github.com/etcd-io/etcd"],
  "language_mix": ["go"],
  "primary_language": "go"
}
```

### 4.3 TaskSpec (per task instance)

```json
{
  "id": "CCX-dep-trace-001",
  "family": "cross-repo-dep-trace",
  "use_case_id": 1,
  "category": "A",
  "prd": {
    "user_story": "As a platform engineer, I need to know which services are affected when we change the shared scheduling library so I can notify teams and plan a safe rollout.",
    "constraints": [
      "Repos span 4+ repositories across the kubernetes ecosystem",
      "Only kubernetes/kubernetes is available locally",
      "Other repos must be discovered via Sourcegraph MCP"
    ],
    "success_definition": "A complete list of repos/files that import or transitively depend on the scheduling library, with file path evidence for each."
  },
  "artifacts": {
    "repo_set_id": "kubernetes-ecosystem",
    "seed_prompt": "Which repos and services depend on the scheduling library in pkg/scheduler? List all direct and transitive dependents with file paths.",
    "oracle": {
      "required_files": [
        {"repo": "github.com/kubernetes/kubernetes", "path": "pkg/scheduler/scheduler.go"},
        {"repo": "github.com/kubernetes/client-go", "path": "tools/cache/reflector.go"}
      ],
      "required_symbols": [
        {"name": "Scheduler", "repo": "github.com/kubernetes/kubernetes", "file": "pkg/scheduler/scheduler.go"}
      ],
      "required_references": [],
      "dependency_chains": [],
      "minimum_recall": 0.8,
      "minimum_precision": 0.6
    }
  },
  "evaluation": {
    "modes": ["retrieval_only"],
    "checks": [
      {"type": "file_set_match", "params": {"min_recall": 0.8, "min_precision": 0.6}},
      {"type": "provenance", "params": {"must_cite_paths": true, "must_cite_repos": true}}
    ],
    "eval_script": "eval.sh",
    "pass_exit_code": 0
  },
  "logging": {
    "required_metrics": [
      "wall_time_ms", "tool_calls", "unique_repos_touched",
      "unique_hosts_touched", "tokens_in", "tokens_out", "mcp_tool_breakdown"
    ]
  },
  "rubric_judge": {
    "enabled": false
  }
}
```

### 4.4 Oracle Answer Format (what the agent must produce)

```json
{
  "task_id": "CCX-dep-trace-001",
  "files": [
    {"repo": "github.com/kubernetes/kubernetes", "path": "pkg/scheduler/scheduler.go", "reason": "Defines the Scheduler type"},
    {"repo": "github.com/kubernetes/client-go", "path": "tools/cache/reflector.go", "reason": "Uses scheduler cache interface"}
  ],
  "symbols": [
    {"name": "Scheduler", "repo": "github.com/kubernetes/kubernetes", "file": "pkg/scheduler/scheduler.go", "line": 42}
  ],
  "dependency_chain": [],
  "summary": "The scheduling library is used by 3 repos with 12 direct import sites."
}
```

### 4.5 Criteria JSON (for rubric-judged tasks)

Following PRDBench AAA pattern:
```json
[
  {
    "metric": "Architecture Comprehension - End-to-end flow accuracy",
    "description": "Arrange: Load the agent's answer.json with flow steps. Act: Compare each step against the oracle dependency chain. Assert: At least 80% of oracle steps are present in correct order.",
    "max_score": 1.0
  },
  {
    "metric": "Evidence Quality - File path citations",
    "description": "Arrange: Extract all file path citations from the agent's answer. Act: Verify each cited file exists in the referenced repo at the specified revision. Assert: >90% of citations are valid.",
    "max_score": 1.0
  }
]
```

## 5. Evaluation Framework

### 5.1 Deterministic Checks (exit-code-first)

The oracle_checks.py library provides 6 composable check types:

| Check Type | What It Validates | Pass Condition |
|------------|------------------|----------------|
| `file_set_match` | Agent found the right files across repos | recall >= threshold AND precision >= threshold |
| `symbol_resolution` | Agent resolved symbols to correct repo/file | All required symbols matched |
| `dependency_chain` | Agent traced correct dependency order | Oracle chain is subsequence of answer chain |
| `provenance` | Agent cited actual file paths as evidence | All citations have repo + path |
| `keyword_presence` | Agent's output contains required terms | All required keywords present |
| `json_schema_match` | Agent's output conforms to expected schema | Zero validation errors |

### 5.2 Hybrid Judge (opt-in for E/F category tasks)

```
final_score = 0.6 * deterministic_eval_score + 0.4 * rubric_judge_score
```

Deterministic eval score comes from oracle_checks.py (verifier reward).
Rubric judge score comes from run_judge.py with criteria.json.

### 5.3 Validity Gate (SWE-Factory fail2pass)

Before any task is admitted to the benchmark:
1. Run eval.sh with oracle_answer.json → MUST pass (exit 0)
2. Run eval.sh with empty answer → MUST fail (exit != 0)
3. If either fails → task is DEGENERATE and rejected

## 6. Retrieval Metrics

Computed from agent transcripts, independent of task scoring:

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| `oracle_coverage` | fraction of oracle items found in MCP tool outputs | Did the agent discover the right code? |
| `time_to_first_oracle_hit_ms` | ms from task start to first relevant MCP result | How fast did search converge? |
| `unique_repos_touched` | distinct repos referenced in MCP outputs | Did the agent search broadly enough? |
| `unique_hosts_touched` | distinct code hosts in MCP outputs | Did the agent search across hosts? |
| `mcp_tool_breakdown` | {tool_name: call_count} | Which MCP tools drive discovery? |
| `retrieval_tokens` | tokens spent on MCP tool calls | Cost of context retrieval |

### Baseline Comparison

For MCP-unique tasks, baseline agents should have:
- `oracle_coverage` near 0 for mcp_only repos (they can't access them)
- `unique_hosts_touched` = 1 (only local host)
- Higher wall time (manual grep/exploration of limited local repos)

This provides an honest, tool-native measurement of MCP value.

## 7. Task Families (12 families from 100 use cases)

| Family | Categories | Use Cases | Oracle Type | MCP Tools Exercised |
|--------|-----------|-----------|-------------|---------------------|
| Cross-repo dep trace | A | 1-5 | deterministic | find_references, go_to_definition |
| Cross-repo config trace | A | 6-10 | deterministic | keyword_search, nls_search |
| Vuln remediation | B | 11-20 | hybrid | keyword_search, read_file |
| Migration inventory | C | 21-30 | deterministic | keyword_search, diff_search |
| Incident debug | D | 31-40 | deterministic | keyword_search, nls_search |
| Onboarding comprehension | E | 41-50 | hybrid | deepsearch, read_file |
| Compliance audit | F | 51-60 | hybrid | keyword_search, read_file |
| Cross-host discovery | G | 61-70 | deterministic | keyword_search (multi-host) |
| Domain lineage | H | 71-80 | deterministic | find_references, read_file |
| Agentic correctness | I | 81-90 | unit_tests | go_to_definition, read_file |
| Platform knowledge | J | 91-100 | hybrid | nls_search, deepsearch |

## 8. Starter Pack (10 tasks, Phase 1)

| Task ID | Use Case | Category | Family | Fixture |
|---------|----------|----------|--------|---------|
| CCX-dep-trace-001 | A1 | A | dep-trace | kubernetes-ecosystem |
| CCX-dep-trace-004 | A4 | A | dep-trace | microservices-polyrepo |
| CCX-dep-trace-010 | A10 | A | config-trace | kubernetes-ecosystem |
| CCX-vuln-remed-011 | B11 | B | vuln-remed | nodejs-web-stack |
| CCX-vuln-remed-014 | B14 | B | vuln-remed | microservices-polyrepo |
| CCX-incident-031 | D31 | D | incident-debug | microservices-polyrepo |
| CCX-onboard-041 | E41 | E | onboarding | kubernetes-ecosystem |
| CCX-onboard-050 | E50 | E | onboarding | nodejs-web-stack |
| CCX-crosshost-061 | G61 | G | cross-host | cross-host-go |
| CCX-crosshost-062 | G62 | G | cross-host | cross-host-go |

Selection rationale:
- **A** (3 tasks): Highest MCP differentiation — symbol resolution + find_references
- **B** (2 tasks): Highest revenue ICP pain point — security remediation
- **D** (1 task): MTTR reduction — incident response
- **E** (2 tasks): Second-highest revenue — developer onboarding
- **G** (2 tasks): Strongest MCP moat — cross-host discovery

## 9. Honest Baselining (Without Human Studies)

Since we cannot run granular human timing studies, we use:

### Tool-Native KPIs (measured directly)
- Oracle coverage: baseline vs MCP-Full
- Time-to-first-relevant-file: baseline vs MCP-Full
- Unique repos/hosts touched: baseline vs MCP-Full
- Recall/precision vs oracle file set

### Published Macro Anchors (cited, not measured)
- Developers spend ~58% of time on comprehension, ~24% on navigation (Xia et al.)
- Program comprehension cited at 35-70% of developer time (ACM surveys)
- IDC reports 16% of time on actual development
- 30-60+ minutes/day searching for solutions (2024 developer survey)

### Baseline Agent Comparison
- Baseline: local checkout + ripgrep in subset repos (1 host)
- MCP-Full: Sourcegraph cross-host retrieval (all hosts, all repos)

## 10. Non-Goals

- Do not rebuild the benchmark framework
- Do not require human-subject studies
- Do not assume baseline sees all repos locally
- Do not modify Harbor agent code
- Do not change existing task scoring
- Do not create tasks that are "literally impossible" for baseline — design for
  "predictably slow/low-recall" instead

## 11. File Inventory (new files this PRD creates)

```
schemas/
  use_case_registry.schema.json     # US-001
  repo_set_fixture.schema.json      # US-002
  mcp_task_spec.schema.json         # US-004

configs/
  use_case_registry.json            # US-003

fixtures/
  repo_sets/
    README.md                       # US-007
    kubernetes-ecosystem.json       # US-007
    nodejs-web-stack.json           # US-007
    python-ml-stack.json            # US-007
    cross-host-go.json              # US-007
    microservices-polyrepo.json     # US-007

templates/
  mcp_unique_task/
    README.md                       # US-008
    task.toml.j2                    # US-008
    instruction.md.j2               # US-008
    eval.sh.j2                      # US-008
    task_spec.json.j2               # US-008
    Dockerfile.j2                   # US-008
    Dockerfile.sg_only.j2           # US-008

scripts/
  generate_mcp_unique_tasks.py      # US-009
  validate_mcp_task_instance.py     # US-006
  ccb_metrics/
    oracle_checks.py                # US-005
    retrieval.py                    # US-015

benchmarks/ccb_design/
  mcp-blast-radius-001/             # US-010
  mcp-gateway-trace-004/            # US-010
  mcp-symbol-resolve-010/           # US-010
  mcp-crosshost-interface-061/      # US-014
  mcp-crosshost-dep-062/            # US-014

benchmarks/ccb_secure/
  mcp-cve-remediation-011/          # US-011
  mcp-auth-audit-014/               # US-011

benchmarks/ccb_debug/
  mcp-error-trace-031/              # US-012

benchmarks/ccb_understand/
  mcp-api-consumption-041/          # US-013
  mcp-e2e-flow-050/                 # US-013

docs/
  MCP_UNIQUE_TASKS.md               # US-020

ralph-mcp-unique/
  prd.json                          # This file
  CLAUDE.md                         # Agent instructions
  DESIGN.md                         # This document
  progress.txt                      # Created at runtime
```

## 12. Dependencies and Sequencing

```
US-001 (registry schema) ──┐
US-002 (fixture schema)  ──┼── US-003 (seed registry)
                           │
US-004 (TaskSpec schema) ──┘
        │
US-005 (oracle checks) ── US-006 (validity gate)
        │
US-007 (fixtures) ── US-008 (templates) ── US-009 (generator)
        │                                      │
        └──── US-010 through US-014 (starter tasks) ── US-016 (config wiring)
                                                           │
US-015 (retrieval metrics) ── US-017 (report integration) ─┘
                                                           │
US-018 (rubric judge) ─────────────────────────────────────┤
                                                           │
                                              US-019 (E2E validation)
                                                           │
                                              US-020 (documentation)
```

Critical path: US-001 → US-003 → US-005 → US-008 → US-010 → US-016 → US-019
