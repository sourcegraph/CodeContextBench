# Refined MCP Use Cases and Benchmark Task Representations

This document refines the Sourcegraph GTM playbook use cases (A–J, 1–100) using customer language from Gong conversations and Salesforce data in the sales workbench, and defines task representations suitable for benchmarks and metrics.

## Data Sources Used for Refinement

| Source | What it provides |
|--------|-------------------|
| **Salesforce use case flags** | `use_case_code_reuse_flg`, `use_case_code_health_flg`, `use_case_dev_onboarding_flg`, `use_case_incident_response_flg`, `use_case_security_flg`, `use_case_dev_productivity_flg`, `use_case_fixing_vulns_flg` — closed-won distribution (e.g. Code Reuse 66 opps / $6.8M; Dev Onboarding 18 opps / $4.3M). |
| **Gong portfolio** | Extracted use cases from calls: title, description, frequency, `relatedFeatures` (code_search, code_insights, deep_search, batch_changes), exampleQuotes. Query: `data/global/gong_calls_portfolio.jsonl`, MCP/Deep Search subset: `gong_mcp_deepsearch_subset.jsonl`. |
| **Salesforce notes** | Product-area subset (`salesforce_notes_product_subset.jsonl`), deal signals (Win/Loss/Objection/Next Step/Technical Requirement), product patterns: Code Search, Batch Changes, Deep Search, MCP. |
| **Customer wins / product knowledge** | `config/customerWins.json`, `config/productKnowledge.json`: use cases "Code search and security remediation", "Developer onboarding and productivity", "Code reuse and compliance"; pain points (security vulns, onboarding time, duplicate code). |
| **Demo/config** | `src/agents/lib/demoprofileExtractor.ts`, `src/config/demoRepoConfig.ts`: pain points (code-search, onboarding, debugging, security); use cases (onboarding, incident-response, code-exploration, dependency-updates, security-patching, api-migrations). |

---

## A) Cross-Repo Dependency Tracing + Symbol Resolution (1–10)

**Customer framing (SF/Gong):** "Find code across repos", "trace dependencies", "blast radius", "where is this used" — maps to **code reuse** and **code health** (use_case_code_reuse_flg, use_case_code_health_flg). Gong: "find code that exists somewhere in the org", "trace dependencies across services".

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 1 | Find all transitive dependents of a shared risk library across ~100+ repos and list "blast radius" services. | "When we change a shared library, which services will be affected?" — list every repo/service that depends on it. | SF: code_reuse, code_health; Gong: "dependencies across services". |
| 2 | Locate every call site of [method] across org and rank by traffic tier. | "Where is this function called across all our repos?" with impact ranking (high-traffic vs low). | Product: "Find all references globally". |
| 3 | Identify which repos import a deprecated protobuf/gRPC type and where the wire format is assumed. | "Which services still use the old API/contract and need to be updated before we deprecate it?" | SF/Gong: migration and compliance themes. |
| 4 | Trace the full call chain from an API gateway route to downstream execution across polyrepos. | "What happens when we hit this endpoint — which services and repos are in the path?" | Demo: "Trace the user authentication flow from frontend to backend". |
| 5 | Find all implementations of an interface across languages (Java + Go) and map which is active by deployment env. | "Where do we implement this contract in different languages and which one runs in prod?" | Multi-repo, multi-language. |
| 6 | Determine where a config key is read/written across services and infra repos (apps + Helm/Terraform). | "Who reads/writes this config and where is it defined (code + infra)?" | Incident/on-call relevance. |
| 7 | Enumerate all feature-flag checks for [flag_name] across services and owners. | "Where is this feature flag used and who owns each usage?" | Dev productivity, safe rollouts. |
| 8 | Find all forked copies of a shared internal SDK and which ones diverged. | "Which teams forked our SDK and have they drifted from the main version?" | Code reuse, code health. |
| 9 | Identify all definitions and usages of a domain event name across Kafka publishers/consumers in separate repos. | "Which services publish or consume this event and where is it defined?" | Architecture comprehension. |
| 10 | Resolve a symbol that appears in stack traces but lives in a repo the developer doesn't have locally. | "This stack trace references a symbol I don't have — which repo and version is it from?" | On-call, onboarding. |

---

## B) Vulnerability + Security Remediation at Scale (11–20)

**Customer framing:** Dominant in wins: "Code search and security remediation", "patch Log4j across 2000+ repos", "fixing_vulns_flg", "use_case_security_flg". Pain: "Security vulnerabilities take months to patch".

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 11 | For CVE-X, find every affected dependency version across GitHub+GitLab repos and produce an upgrade plan. | "We have CVE-X; which repos and versions are affected and what's the minimal upgrade path?" | customerWins: Log4j, 2000+ repos, 48h. |
| 12 | Identify all services embedding a vulnerable container base image tag referenced from a central infra repo. | "Which deployments use this vulnerable base image and where is it defined (e.g. central Helm)?" | Security + infra. |
| 13 | Find all usages of a crypto primitive (e.g., SHA-1) across org and group by risk category. | "Where do we still use SHA-1 (or other weak crypto) and how critical is each usage?" | Compliance, audit. |
| 14 | Locate all endpoints lacking auth middleware across microservices (different frameworks) and file paths. | "Which API routes don't have auth and where are they (file path + framework)?" | Security review. |
| 15 | Enumerate all services exposing a port/config pattern that violates policy and generate a remediation list. | "Which services violate our port/config policy and what needs to change?" | Compliance. |
| 16 | Find where a leaked secret format might appear (regex + semantic context) across repos and history. | "Search for patterns that look like secrets (format + context) across code and history." | Security, incident. |
| 17 | Identify all usages of a vulnerable logging pattern and generate candidate diffs. | "Where do we log in an unsafe way (e.g. PII, injection) and what would a fix look like?" | Security, compliance. |
| 18 | Map which repos are impacted by a compromised internal package based on lockfiles across languages. | "This internal package was compromised; which repos have it in their lockfile?" | CVE-style response. |
| 19 | Find all S3 bucket policies or IAM roles referenced by a service and flag privilege escalation patterns. | "Which buckets/roles does this service use and are there over-permissive patterns?" | Compliance, security. |
| 20 | After an incident, find every service that logs the sensitive field due to shared middleware. | "Which services use the middleware that logged the sensitive field?" | Incident response. |

---

## C) Migrations + Framework Upgrades Across Hundreds of Repos (21–30)

**Customer framing:** "Library upgrades are manual and error-prone", "Batch Changes for large-scale change", "dependency-updates", "security-patching", "api-migrations" (demoRepoConfig).

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 21 | Identify every repo using Framework v1 patterns and produce a migration inventory. | "Which repos still use Framework v1 and what would migration look like (inventory + order)?" | SF: fixing_vulns, code_health. |
| 22 | Find all usages of a deprecated API signature across org and propose mechanical edits. | "Where do we call the deprecated API and what's the mechanical replacement?" | Batch Changes value prop. |
| 23 | Enumerate all repos pinned to an old JDK/toolchain via CI config and prioritize upgrade order. | "Which repos are pinned to old JDK/toolchain in CI and in what order should we upgrade?" | Migrations. |
| 24 | Detect all GraphQL schema-breaking usages across repos before a schema change lands. | "Before we change the schema, which clients would break and where?" | Safe rollout. |
| 25 | Find all services using an old auth token format and map rollout constraints. | "Which services use the old token format and what's the rollout order (dependencies)?" | Auth, compliance. |
| 26 | Identify all react-router v5 patterns across frontend repos and convert to v6 plan. | "Where do we use react-router v5 and what's the v6 migration plan per repo?" | Framework upgrade. |
| 27 | Locate all protobuf compilation pipelines across repos and unify build steps. | "Where do we compile protobufs and how can we unify the pipeline?" | Build, code health. |
| 28 | Find all references to a soon-to-be-removed config key across code + docs repos. | "Where is this config key used (code and docs) before we remove it?" | Deprecation. |
| 29 | Inventory all repos still using legacy logging/metrics libraries and auto-generate upgrade PRs. | "Which repos use legacy logging/metrics and what upgrade PR would look like?" | Observability, migrations. |
| 30 | Detect all SQL queries depending on a soon-to-change schema across services. | "Which services have SQL that depends on this schema and will break when we change it?" | Schema migration. |

---

## D) On-Call / Incident Debugging Across Microservices (31–40)

**Customer framing:** "use_case_incident_response_flg", demo pain "debugging/incident/trace", customer win "Reduced MTTR for security vulnerabilities by 85%".

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 31 | From a production error string, find all code paths that could emit it across org repos. | "This error message appeared in prod — which code paths in which repos can emit it?" | Incident response. |
| 32 | Trace a request ID propagation implementation across gateway, middleware, and services in different repos. | "How is request ID passed from gateway through middleware and services (which repos)?" | Debugging, observability. |
| 33 | Identify where a timeout is configured (client + server + infra) across code + Helm + Terraform repos. | "Where is the timeout for this call configured (app, Helm, Terraform)?" | Incident tuning. |
| 34 | Find all services that call an upstream endpoint implicated in an incident and confirm retry semantics. | "Which services call this failing upstream and what are their retry settings?" | Blast radius. |
| 35 | From a stack trace symbol, locate the owning repo, version, and deployment pipeline. | "This symbol is in the stack trace — which repo, version, and pipeline deploy it?" | On-call. |
| 36 | Locate all circuit-breaker configs across repos to tune incident mitigation quickly. | "Where are circuit breakers configured for this dependency across repos?" | Incident mitigation. |
| 37 | Determine whether a bug exists in shared library vs service-specific wrapper by cross-repo diffing. | "Is this bug in the shared lib or in our service-specific wrapper (compare across repos)?" | Root cause. |
| 38 | Find all consumers of a Kafka topic that is producing poison messages across org. | "Which services consume this topic so we can fix or isolate poison message impact?" | Incident. |
| 39 | Identify all places a specific header is stripped/added across proxies and services. | "Where is this header added or removed (proxies + services)?" | Request tracing. |
| 40 | Find all "emergency disable" toggles and their code paths across services. | "Where are kill switches / emergency disables and what do they turn off?" | Incident response. |

---

## E) Onboarding + Architecture Comprehension (41–50)

**Customer framing:** "use_case_dev_onboarding_flg" (18 opps, $4.3M), "Developer onboarding and productivity", "New developers don't know where to look", "Reduced onboarding time from 3 months to 3 weeks".

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 41 | "Where is this API consumed?" across 500 repos with owners and examples. | "Who calls this API (repos + owners) and can we get example call sites?" | Onboarding, ownership. |
| 42 | Build an architecture map of trading → risk → reporting flows spanning dozens of services/repos. | "Map the flow from [domain entry] to [domain exit] across services and repos." | Architecture. |
| 43 | Identify the canonical library for pricing curves when multiple forks exist across repos. | "Which repo is the source of truth for this shared logic when there are several forks?" | Code reuse. |
| 44 | Find the source of truth for a domain model type and all serialization boundaries. | "Where is this type defined and where is it serialized/deserialized (repos + boundaries)?" | Onboarding, consistency. |
| 45 | Determine how auth works end-to-end across services when pieces live in different repos. | "How does auth flow from gateway to backend (which repos implement which piece)?" | Security, onboarding. |
| 46 | Locate the implementation of "trade booking" across repos and list entrypoints/tests. | "Where is [critical flow] implemented and what are the entrypoints and tests?" | Domain comprehension. |
| 47 | Find all "golden path" examples of adding a new service (templates, pipelines, policy checks). | "What's the standard way we add a new service (templates, CI, checks) across repos?" | Onboarding. |
| 48 | Identify the standard patterns for feature flags and where they are documented (docs in separate repos). | "How do we do feature flags and where is it documented (code + docs repos)?" | Dev productivity. |
| 49 | Map all internal client SDKs and which services use which versions. | "Which services use which version of our internal SDKs?" | Upgrades, onboarding. |
| 50 | For a new hire, answer "what happens when I click 'Place Order'?" across frontend + backend + infra repos. | "End-to-end: what happens when [user action] (frontend → backend → infra)?" | Onboarding. |

---

## F) Compliance / Audit / Provenance in Regulated Environments (51–60)

**Customer framing:** "use_case_security_flg", "Code reuse and compliance", "SOC 2", "compliance", "HIPAA", discovery questions on security/compliance.

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 51 | Prove where PII is redacted by tracing fields across ingestion → processing → logging repos. | "Trace PII from ingestion to logging and show where it's redacted (repos + code paths)." | Compliance, audit. |
| 52 | Identify all code paths that can write to an audit log topic and validate required fields. | "Which code paths write to the audit log and do they all set required fields?" | Audit. |
| 53 | Find all data retention policies implemented in code and infra across repos. | "Where is retention policy implemented (code + infra) and is it consistent?" | Compliance. |
| 54 | Trace "who can access this dataset" from IAM/Terraform repos to service authorization checks. | "From IAM/Terraform to app code: who can access this dataset?" | Access control. |
| 55 | Find all services that export regulated metrics and where sampling/aggregation happens. | "Which services emit regulated metrics and where do we sample/aggregate?" | Compliance. |
| 56 | Identify all endpoints that must be in scope for a compliance review by searching for domain markers. | "Which endpoints are in scope for [regulation] (search for domain markers)?" | Audit scope. |
| 57 | Locate all references to a regulatory rule ID in code/docs and verify implementations are consistent. | "Where is rule ID X referenced and is the implementation consistent?" | Compliance. |
| 58 | Determine which repos require special review (e.g., SOX) based on ownership and code patterns. | "Which repos are in scope for SOX (or similar) by ownership and code patterns?" | Audit. |
| 59 | Find where "kill switch" controls exist for regulated operations and how they're invoked. | "Where are kill switches for regulated operations and how are they triggered?" | Compliance. |
| 60 | Produce an evidence bundle: code locations + configs + tests proving a control is implemented. | "Evidence bundle for control X: code + config + tests." | Audit. |

---

## G) Cross-Host Reality (GitHub + GitLab + Bitbucket) + Repo Sprawl (61–70)

**Customer framing:** Product integrates with GitHub, GitLab, Bitbucket, Azure DevOps; "search across all repos" regardless of host. Gong/notes: multi-SCM environments (e.g. GitHub+GitLab).

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 61 | Find all implementations of a shared interface split across GitHub and GitLab repos. | "Where is this interface implemented across GitHub and GitLab?" | Multi-host. |
| 62 | Trace a dependency from a GitHub service into a GitLab-hosted shared library. | "This GitHub service depends on a library in GitLab — trace the dependency." | Cross-host. |
| 63 | Identify duplicated services after an acquisition and map which is live. | "After acquisition, which services are duplicates and which is canonical/live?" | Sprawl. |
| 64 | Locate all CI pipelines across code hosts that publish the same artifact name. | "Which pipelines (any host) publish artifact X and where are they?" | Multi-host CI. |
| 65 | Find all repositories that define the same Kubernetes namespace across hosts. | "Which repos (any host) define namespace X?" | Infra sprawl. |
| 66 | Determine which code host has the "authoritative" repo for a package referenced everywhere. | "Which host/repo is the source of truth for this package?" | Authority. |
| 67 | Identify all auth token handling code across repos even when split by host and org. | "Where do we handle auth tokens (all hosts/orgs)?" | Security, cross-host. |
| 68 | Search for a domain constant used across hosts and map its evolution in different repos. | "How is this constant defined and used across hosts and how did it evolve?" | Consistency. |
| 69 | Inventory all repos that still point to an old Git remote after a migration. | "Which repos still use the old Git remote URL?" | Migration. |
| 70 | Find all references to a deprecated internal hostname across repos across hosts. | "Where do we reference this deprecated hostname (all hosts)?" | Cleanup. |

---

## H) Risk + Trading Domain "Lineage" Problems (71–80)

**Customer framing:** Domain-specific; use "risk factor", "pricing curve", "trade ID", "position limit", "order routing" as placeholders for customer domain concepts. Align with "trace how X is calculated" and "source of truth" (code_health, code reuse).

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 71 | Trace how a risk factor is calculated across multiple services and shared libs in separate repos. | "How is [domain metric] computed end-to-end (services + shared libs, repos)?" | Lineage. |
| 72 | Find all places where a pricing curve is interpolated and ensure the same method is used org-wide. | "Where do we interpolate [domain entity] and do we use one method everywhere?" | Consistency. |
| 73 | Identify all services that assume market data freshness thresholds and where they're enforced. | "Which services depend on freshness of [data] and where is it enforced?" | Domain rules. |
| 74 | Locate all places a trade ID is generated/validated and ensure uniqueness semantics. | "Where do we generate/validate [domain ID] and are uniqueness rules consistent?" | Data integrity. |
| 75 | Find all consumers of a risk model output topic and identify where rounding/precision changes break them. | "Who consumes this model output and where would precision/rounding changes break?" | Lineage. |
| 76 | Trace "position limit" checks across services and determine which repo is the policy source of truth. | "Where are [policy] checks and which repo owns the canonical policy?" | Policy. |
| 77 | Identify all places where a trading calendar/holiday set is used and verify consistency across repos. | "Where do we use [calendar/holiday] and is it the same source everywhere?" | Consistency. |
| 78 | Locate all order routing rules and their test fixtures across repos. | "Where are [routing] rules and their tests (repos + paths)?" | Domain logic. |
| 79 | Find all places that apply FX conversion and ensure the same rate source is used. | "Where do we do [domain conversion] and do we use one rate source?" | Consistency. |
| 80 | Identify all services that handle "cancel/replace" and reconcile differing workflows across repos. | "Which services handle [cancel/replace] and how do their workflows differ?" | Workflow reconciliation. |

---

## I) Agentic Coding Correctness Enabled by Org-Wide Context (81–90)

**Customer framing:** "use_case_dev_productivity_flg", "Generate code that uses the right internal API", "Add endpoint and wire through gateway + auth + telemetry" — productivity and consistency.

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 81 | Generate a change using the correct internal API signature living in another repo. | "Implement a caller for [API] using the current signature and patterns from the owning repo." | Dev productivity. |
| 82 | Add a new endpoint and wire it through gateway + auth + telemetry when those live in different repos. | "Add endpoint X and wire it through gateway, auth, telemetry using org patterns." | Multi-repo wiring. |
| 83 | Update an internal SDK and propagate changes to all consumers across repos automatically. | "Update SDK contract and list/fix all consumer repos (or generate upgrade PRs)." | SDK evolution. |
| 84 | Implement a feature flag with the org's standard library and wiring found across repos. | "Add a feature flag using our standard lib and wiring (from examples in other repos)." | Consistency. |
| 85 | Add a new Kafka consumer using the shared schema registry conventions stored in another repo. | "Add consumer for topic X using schema registry and conventions from [repo]." | Event-driven. |
| 86 | Introduce a new metric/log field following the central observability repo conventions. | "Add metric/log field per observability repo conventions." | Observability. |
| 87 | Modify build pipelines correctly (Bazel/Gradle/CI) using patterns from other repos. | "Change build/CI for this repo to match patterns used in [reference repos]." | Build. |
| 88 | Update protobuf definitions and fix all downstream breakages across repos. | "Change proto X and find/fix all downstream breakages (repos + call sites)." | API evolution. |
| 89 | Apply a standard error-handling pattern from a reference service in another repo. | "Apply our standard error-handling pattern (from [repo]) to this service." | Consistency. |
| 90 | Generate code that respects internal linting, naming, and folder conventions defined elsewhere. | "Generate code that passes our linters and follows naming/folder conventions." | Conventions. |

---

## J) Platform / DevTools / Internal Tooling and "Tribal Knowledge" (91–100)

**Customer framing:** "Find the correct service template", "how do I deploy safely", "owner for a shared library" — onboarding and discoverability.

| # | Original | Customer-refined phrasing | Evidence anchor |
|---|----------|---------------------------|-----------------|
| 91 | Find the correct service template repo and how to use it (when docs live elsewhere). | "Which repo is the canonical service template and how do we use it (code + docs)?" | Onboarding. |
| 92 | Identify the owner team for a shared library by analyzing usage + CODEOWNERS across repos. | "Who owns this shared library (usage + CODEOWNERS across repos)?" | Ownership. |
| 93 | Locate all "homegrown search tool" code and decide what can be retired after adopting Sourcegraph. | "Where do we have custom search/tooling that could be replaced by [platform]?" | Consolidation. |
| 94 | Determine why a build is slow by tracing shared CI modules used across repos. | "Why is this build slow — which shared CI modules (and repos) are involved?" | Dev experience. |
| 95 | Inventory all "golden signals" dashboards defined across repos and standardize them. | "Where are golden-signal dashboards defined and how do we standardize?" | Observability. |
| 96 | Find all internal CLIs and where their configuration is defined across repos. | "Which internal CLIs exist and where is their config (repos + paths)?" | Tooling. |
| 97 | Identify all deprecated internal endpoints still called by any service across org. | "Which services still call deprecated endpoints and which endpoints?" | Cleanup. |
| 98 | Locate all places a shared policy check is implemented (pre-commit, CI, server) across repos. | "Where is [policy] enforced (pre-commit, CI, server) and is it consistent?" | Policy. |
| 99 | Find all repos that must be updated to support a new runtime base image policy. | "Which repos need changes to meet the new base image policy?" | Platform policy. |
| 100 | Build a "how do I deploy safely?" answer that stitches together docs + code + pipelines across repos. | "Step-by-step: how do we deploy [service] safely (docs + code + pipelines)?" | Onboarding. |

---

## Benchmark Task Representations

Use these to define benchmark runs and collect metrics (e.g. success rate, latency, coverage). Each task has an **input spec**, **output spec**, and **success criteria**.

### Task representation schema

- **task_id**: e.g. `A1`, `B11`, `E41`.
- **input_spec**: What the system receives (e.g. org snapshot, CVE ID, symbol name, error string).
- **output_spec**: Expected artifact (list of repos, upgrade plan, code path list, evidence bundle).
- **success_metrics**: How to score (precision/recall on repos, plan validity, time to complete).

### Example benchmark tasks (subset)

| task_id | Category | Input spec | Output spec | Success metrics |
|---------|----------|------------|-------------|-----------------|
| **A1** | Blast radius | Library name or package ID; org graph (repos + deps). | List of repos/services that depend on it (transitive), optionally ranked. | Recall of dependent repos; precision (no false positives). |
| **B11** | CVE remediation | CVE ID (e.g. CVE-2021-44228); org codebase(s). | List of affected repos + dependency versions; recommended upgrade path (per repo or grouped). | All affected repos found; upgrade path is valid (version bump exists). |
| **D31** | Error to code path | Exact error string (e.g. from logs); org codebase(s). | List of (repo, file, line or symbol) that can emit this error. | Recall of code paths that emit the string; low false positives. |
| **E41** | API consumption | API name or endpoint; org codebase(s). | List of (repo, owner/team, example call site). | Repos that call the API; at least one example per repo. |
| **E50** | Onboarding flow | User action description (e.g. "Place Order"); org codebase(s). | Ordered flow: frontend → backend → infra (repos + entrypoints). | Covers real code path; order is correct. |
| **F60** | Evidence bundle | Control ID or name; org codebase(s) + config. | Set of (code location, config snippet, test that validates control). | All required evidence types present; locations are correct. |
| **I81** | Correct API usage | API name; consumer repo; org codebase(s). | Code change (patch or PR) that calls the API with correct signature from owning repo. | Compiles; uses current API; matches org patterns. |
| **J100** | Deploy safely | Service or repo name; org codebase(s) + docs. | Step-by-step guide (docs + code + pipeline references). | Steps are executable and reference real artifacts. |

Programmatic task definitions (input/output/success metrics and SF flag mapping) are in **`history/benchmark-tasks.json`**.

### How to use with Gong/Salesforce

- **Gong:** Search `gong_calls_portfolio.jsonl` (or MCP/Deep Search subset) for phrases that match a use case (e.g. "blast radius", "Log4j", "onboarding", "where is this API consumed"). Use hits to:
  - Validate that the refined phrasing matches customer language.
  - Attach example quotes to benchmark task descriptions for realism.
- **Salesforce notes:** Search `salesforce_notes_product_subset.jsonl` for product + signal (e.g. Code Search + "vulnerability", Batch Changes + "migration"). Use to:
  - Prioritize which benchmark tasks to run first (e.g. B11, B12, C21–C30).
  - Tie tasks to SF use case flags for reporting (e.g. "B11 supports use_case_fixing_vulns_flg").
- **Use case flags:** For closed-won distribution (e.g. Code Reuse 66, Dev Onboarding 18), weight benchmark design toward A, E, B, C and ensure task names in reports align to those flags for GTM consistency.

---

## Suggested next steps

1. **Run bd onboard** and create a bead for "Refine MCP use cases from customer data" if you want this tracked.
2. **Query Gong portfolio** (or MCP) for each category keyword set; add "exampleQuotes" to this doc or a sibling `history/customer-quotes-by-use-case.json`.
3. **Implement 5–10 benchmark tasks** (e.g. A1, B11, D31, E41, J100) as scripted or MCP-backed flows; record input/output and success metrics.
4. **Map benchmark tasks to SF use case flags** in your reporting so wins can be attributed to use cases (e.g. "Benchmark B11 aligns to fixing_vulns_flg").
