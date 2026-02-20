# MCP-Never-Used Task Analysis (2026-02-20)

Analysis of SG_full tasks where the agent had 13 Sourcegraph MCP tools available
but chose not to use any of them.

## Summary

**7 confirmed mcp_never_used tasks** (1 originally flagged was misclassified):

| # | Task | Model | Reward | MCP Calls | MCP Useful? | Root Cause |
|---|------|-------|--------|-----------|-------------|------------|
| 1 | bustub-hyperloglog-impl-001 | Sonnet | **1.00** | 0 | No | Self-contained implementation |
| 2 | etcd-grpc-api-upgrade-001 (run 045219) | Sonnet | **0.77** | 0 | No | Exact pattern grep sufficient |
| 3 | etcd-grpc-api-upgrade-001 (run 045323) | Sonnet | **0.77** | 0 | No | Duplicate of #2 |
| 4 | pandas-groupby-perf-001 | Opus | **0.92** | 0 | No | Local profiling + optimization |
| 5 | numpy-array-sum-perf-001 | Sonnet | **0.95** | 0 | No | Pure algorithmic optimization |
| 6 | openhands-search-file-test-001 | Sonnet | **0.80** | 0 | No | Test generation with local code |
| 7 | sklearn-kmeans-perf-001 | Sonnet | **0.15** | 0 | **YES** | Compilation blocker solvable via MCP |

**1 misclassified (restored from archive):**

| Task | Model | Reward | MCP Calls | Notes |
|------|-------|--------|-----------|-------|
| pandas-groupby-perf-001 | Sonnet | 0.33 | **9** | Had MCP calls; all returned empty results |

**Key findings:**
- 6/7 tasks achieved good rewards (>0.77) without MCP — MCP genuinely unnecessary
- 1/7 (sklearn-kmeans-perf) critically needed MCP but never used it (reward 0.15)
- V4 preamble is fully ignored by agents when local approach seems sufficient
- No agent in any transcript explicitly considered and rejected MCP tools — they simply never thought about them

---

## Detailed Analysis by Task

### 1. bustub-hyperloglog-impl-001 (Sonnet, reward=1.00)

**Task type:** Build — implement HyperLogLog data structure in bustub database

**Tools used:** Bash(12), TodoWrite(9), Read(7), Edit(3), Write(2) — 33 total

**Why no MCP:**
- Pure algorithmic implementation task (HyperLogLog is well-specified)
- All code in single local repo, cloned at task start
- No cross-repo patterns needed — solution derived from test expectations
- Agent achieved perfect 1.0 score via local-only approach

**Agent reasoning about MCP:** Never mentioned. Went straight to cloning repo,
reading test expectations, implementing algorithm. Zero deliberation about
remote search.

**Verdict:** MCP correctly skipped. Would have been detrimental — searching
"HyperLogLog" remotely would surface different-language implementations
(Go, Python, Redis) that don't match bustub's C++ API. Classic case where
MCP anchoring bias could hurt.

---

### 2-3. etcd-grpc-api-upgrade-001 (Sonnet, reward=0.77, two runs)

**Task type:** Design — analyze gRPC API upgrade path across etcd/k8s/containerd

**Tools used:** Bash(63), Read(33), TodoWrite(3), Edit(1) — 100 total

**Why no MCP:**
- Task has exact, literal search patterns (`grpc.Dial`, `grpc.DialContext`)
- All 3 target repos present locally under `/ccb_crossrepo/src/`
- Local `grep -rn` found all 21 callsites instantly
- No semantic understanding needed — pure find-and-replace pattern

**Agent reasoning about MCP:** Zero mentions of Sourcegraph in 155 assistant
messages. Agent used Bash grep as primary discovery tool throughout.

**Verdict:** MCP correctly skipped. Local grep is faster and more precise for
exact string matching across known repos. MCP adds latency without benefit
when the search pattern is a literal function name.

---

### 4. pandas-groupby-perf-001 — Opus (reward=0.92)

**Task type:** Test/Performance — optimize pandas groupby aggregation

**Tools used:** Bash(90), Read(20), TodoWrite(7), Edit(3) — 120 total

**Why no MCP:**
- Full pandas codebase available locally in system site-packages
- Task is performance optimization requiring local profiling + benchmarking
- Agent found the bottleneck (`_aggregate_series_pure_python`) via local Read
- Solution requires editing local files — MCP tools are read-only
- Achieved 5.4x speedup and 0.92 reward

**Agent reasoning about MCP:** Called `ListMcpResourcesTool` once to verify
availability, then ignored MCP entirely. Pragmatic environment detection —
saw full code was accessible locally and proceeded.

**Verdict:** MCP correctly skipped. Performance optimization is inherently
local: profile, identify bottleneck, edit code, re-benchmark. Remote code
search adds nothing to this workflow.

**Contrast with Sonnet run (0.33, 9 MCP calls):** The Sonnet version of this
same task actually made 9 MCP calls (3 keyword_search, 2 commit_search,
1 diff_search, 3 read_file) — all returned empty results. The MCP calls
were wasted effort searching for internal Cython functions not indexed in
public repos. Opus achieved 2.83x better reward by skipping MCP entirely.

---

### 5. numpy-array-sum-perf-001 (Sonnet, reward=0.95)

**Task type:** Test/Performance — optimize numpy array_sum function

**Tools used:** **0 tool calls total** — pure LLM code generation

**Why no MCP:**
- Standard algorithmic optimization (numpy einsum vectorization)
- Instruction provided baseline runtime and optimization hints
- Solution derived from first principles, not code discovery
- Agent generated complete solution in 4 messages with zero tool calls
- Achieved 21.6x speedup

**Agent reasoning about MCP:** Never mentioned. Immediate implementation
from message 1 — no exploration phase at all.

**Verdict:** MCP not just unnecessary but irrelevant. Task is a closed
optimization problem solvable from domain knowledge alone. Agent correctly
identified no code discovery was needed.

---

### 6. openhands-search-file-test-001 (Sonnet, reward=0.80)

**Task type:** Test — write unit tests for OpenHands search_file function

**Tools used:** Bash(47), Read(7), TodoWrite(5), Write(1), Edit(1) — 61 total

**Why no MCP:**
- Instruction provided exact file paths for the target function
- Full repo cloned locally at task start
- Test writing is a local code generation task
- No exploration needed — function signature + behavior visible in local source

**Agent reasoning about MCP:** Zero mentions. Agent cloned repo, read the
target function, wrote comprehensive 6-scenario test suite, verified with
pytest. Completed in ~9 minutes.

**Verdict:** MCP correctly skipped. When exact file paths are provided in the
instruction, remote code discovery adds no value. The agent had everything
it needed locally.

---

### 7. sklearn-kmeans-perf-001 (Sonnet, reward=0.15) -- MCP WOULD HAVE HELPED

**Task type:** Test/Performance — optimize scikit-learn KMeans Elkan algorithm

**Tools used:** Bash(185), Read(16), TodoWrite(7), Edit(6), Write(4) — 218 total

**Why no MCP (despite needing it):**
- Agent never mentioned or considered Sourcegraph tools
- V4 preamble present but completely ignored
- Agent jumped straight to local implementation without any exploration phase

**What went wrong:**
1. Agent tried to optimize Cython code but environment lacked Cython compiler
2. Spent 150+ Bash commands trying compilation approaches (ctypes, meson, importlib)
3. All 50+ compilation attempts failed — classic exploration loop without exit criteria
4. Eventually attempted Python fallback but never produced valid `solution.patch`
5. Verifier had nothing to apply — reward 0.15 (near-zero)

**How MCP would have helped (4 critical uses):**

| Blocker | MCP Solution | Estimated Impact |
|---------|-------------|------------------|
| Cython not installed | `keyword_search: "dockerfile cython sklearn"` → find CI configs | **Unblock compilation** |
| Wrong module structure | `go_to_definition` on `_kmeans_single_elkan` → see actual imports | **Correct approach** |
| Unknown optimization patterns | `keyword_search: "bounds_tight distance_matrix"` → existing patterns | **Better strategy** |
| Wrong output format | `diff_search: "optimization patch sklearn"` → example format | **Correct deliverable** |

**Token waste:** ~3000-4000 tokens on failed approaches that 2-3 MCP searches
could have resolved. Agent spent 54% of runtime (25 min) on compilation
attempts.

**Verdict:** This is the strongest case for MCP value in the entire set.
The agent was stuck on a solvable blocker (missing Cython compiler) and
never escalated to external knowledge. MCP could have provided the build
system context that local exploration couldn't.

---

## Cross-Task Patterns

### Pattern 1: Preamble Invisibility
All 7 tasks had the V4 "# Searching Sourcegraph" preamble injected. In **zero
cases** did the agent reference, acknowledge, or act on it. The preamble
provides "soft guidance" that agents treat as informational background noise,
not actionable instructions.

### Pattern 2: No Explicit MCP Rejection
In no transcript did an agent say "I could use Sourcegraph here but I'll use
local tools instead." The decision to skip MCP was always implicit —
agents simply never considered it as an option. This suggests MCP tools
are not in the agent's "default tool consideration set" despite being listed
in the system prompt.

### Pattern 3: Task Type Determines MCP Value

| Task Type | MCP Value | Reason |
|-----------|-----------|--------|
| Pure implementation (bustub) | None | Self-contained, deterministic |
| Exact pattern search (etcd) | None | Local grep is faster |
| Performance optimization (pandas, numpy) | None | Requires local profiling |
| Test generation with explicit paths (openhands) | None | All context provided |
| Build system debugging (sklearn) | **High** | External knowledge needed |

### Pattern 4: High Reward Correlates with Correct MCP Skip
6 of 7 tasks that skipped MCP achieved rewards >= 0.77 (mean: 0.91).
The one task that needed MCP but didn't use it scored 0.15.
This suggests agents are generally good at recognizing when local tools
suffice — they just lack the metacognitive trigger to escalate to MCP
when stuck.

### Pattern 5: Struggling Doesn't Trigger MCP Consideration
sklearn-kmeans-perf spent 150+ failed commands without ever considering
MCP as an alternative. The V4 preamble says "Search before you build"
but the agent had already started building before the preamble's guidance
could activate. There's no "I'm stuck, maybe I should search" heuristic.

---

## Implications for Preamble Design

1. **V4 preamble is invisible** to agents on tasks with clear local approaches.
   This is actually desirable for 6/7 cases — forced MCP usage would add
   overhead without benefit.

2. **The missing trigger is escalation-on-failure.** The preamble should add:
   "If you've attempted the same category of approach 3+ times without
   success, use Sourcegraph to search for build configs, CI patterns,
   or similar implementations."

3. **Task type classification in preamble** could help: "For performance
   optimization tasks, MCP is optional. For build/compilation issues,
   search CI configs via MCP."

4. **The misclassification (Sonnet pandas-groupby)** shows that even when
   agents DO use MCP, ineffective searches (internal function names not
   in public indexes) waste tokens. Better query guidance needed.

---

## Archival Summary

**Archived to `__mcp_never_used` (7 task directories):**
- build_sonnet_20260219_220402/archive/bustub-hyperloglog-impl-001_SGfull__mcp_never_used
- design_sonnet_20260219_045219/archive/etcd-grpc-api-upgrade-001_SGfull__mcp_never_used
- design_sonnet_20260219_045323/archive/etcd-grpc-api-upgrade-001_SGfull__mcp_never_used
- test_opus_20260220_004116/archive/pandas-groupby-perf-001_SGfull__mcp_never_used
- test_sonnet_20260219_015458_to_20260219_213932/archive/numpy-array-sum-perf-001_SGfull__mcp_never_used
- test_sonnet_20260219_015458_to_20260219_213932/archive/openhands-search-file-test-001_SGfull__mcp_never_used
- test_sonnet_20260219_015458_to_20260219_213932/archive/sklearn-kmeans-perf-001_SGfull__mcp_never_used

**Restored from archive (misclassified — had 9 MCP calls):**
- test_sonnet_20260219_015458_to_20260219_213932/sourcegraph_full/ccb_test_pandas-groupby-perf-001_sourcegraph_full/sdlc_test_pandas-groupby-perf-00__UCpUi9B

**Archived to `__errored` (7 task directories):**
- build_sonnet_20260219_214508/archive/kafka-batch-accumulator-refac-001__errored_agent_timeout
- build_sonnet_20260219_133554_to_20260219_172247/archive/k8s-noschedule-taint-feat-001__errored_agent_timeout
- design_sonnet_20260219_220407/archive/k8s-typemeta-dep-chain-001_BL__errored_docker_rwlayer
- design_sonnet_20260219_220407/archive/k8s-typemeta-dep-chain-001_SGfull__errored_verifier_bug
- design_sonnet_20260219_220407/archive/envoy-routeconfig-dep-chain-001_SGfull__errored_verifier_bug
- secure_sonnet_20260219_220419/archive/django-repo-scoped-access-001_SGfull__errored_setup_timeout
- test_opus_20260220_004116/archive/ghost-code-review-001_SGfull__errored_agent_timeout
