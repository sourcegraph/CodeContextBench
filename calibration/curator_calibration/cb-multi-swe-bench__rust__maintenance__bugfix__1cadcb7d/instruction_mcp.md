# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

- `github.com/sg-evals/tracing--4609f22a` — use `repo:^github.com/sg-evals/tracing--4609f22a$` filter

Scope ALL keyword_search/nls_search queries to these repos.
Use the repo name as the `repo` parameter for read_file/go_to_definition/find_references.


## Required Workflow

1. **Search first** — Use MCP tools to find relevant files and understand existing patterns
2. **Read remotely** — Use `sg_read_file` to read full file contents from Sourcegraph
3. **Edit locally** — Use Edit, Write, and Bash to create or modify files in your working directory
4. **Verify locally** — Run tests with Bash to check your changes

## Tool Selection

| Goal | Tool |
|------|------|
| Exact symbol/string | `sg_keyword_search` |
| Concepts/semantic search | `sg_nls_search` |
| Trace usage/callers | `sg_find_references` |
| See implementation | `sg_go_to_definition` |
| Read full file | `sg_read_file` |
| Browse structure | `sg_list_files` |
| Find repos | `sg_list_repos` |
| Search commits | `sg_commit_search` |
| Track changes | `sg_diff_search` |
| Compare versions | `sg_compare_revisions` |

**Decision logic:**
1. Know the exact symbol? → `sg_keyword_search`
2. Know the concept, not the name? → `sg_nls_search`
3. Need definition of a symbol? → `sg_go_to_definition`
4. Need all callers/references? → `sg_find_references`
5. Need full file content? → `sg_read_file`

## Scoping (Always Do This)

```
repo:^github.com/ORG/REPO$           # Exact repo (preferred)
repo:github.com/ORG/                 # All repos in org
file:.*\.ts$                         # TypeScript only
file:src/api/                        # Specific directory
```

Start narrow. Expand only if results are empty.

## Efficiency Rules

- Chain searches logically: search → read → references → definition
- Don't re-search for the same pattern; use results from prior calls
- Prefer `sg_keyword_search` over `sg_nls_search` when you have exact terms
- Read 2-3 related files before synthesising, rather than one at a time
- Don't read 20+ remote files without writing code — once you understand the pattern, start implementing

## If Stuck

If MCP search returns no results:
1. Broaden the search query (synonyms, partial identifiers)
2. Try `sg_nls_search` for semantic matching
3. Use `sg_list_files` to browse the directory structure
4. Use `sg_list_repos` to verify the repository name

---

# Fix: Multi-SWE-Bench__rust__maintenance__bugfix__1cadcb7d

**Repository:** github.com/sg-evals/tracing--4609f22a (mirror of tokio-rs/tracing)
**Language:** rust
**Category:** contextbench_cross_validation

## Description

attributes: fix `#[instrument(err)]` with `impl Trait` return types

This backports PR #1233 to v0.1.x. This isn't *just* a simple cherry-pick
because the new tests in that branch use the v0.2.x module names, so
that had to be fixed. Otherwise, though, it's the same change, and I'll go
ahead and merge it when CI passes, since it was approved on `master`.

## Motivation

Currently, using `#[instrument(err)]` on a function returning a `Result`
with an `impl Trait` in it results in a compiler error. This is because
we generate a type annotation on the closure in the function body that
contains the user function's actual body, and `impl Trait` isn't allowed
on types in local bindings, only on function parameters and return
types.

## Solution

This branch fixes the issue by simply removing the return type
annotation from the closure. I've also added tests that break on master
for functions returning `impl Trait`, both with and without the `err`
argument.

Fixes #1227

Signed-off-by: Eliza Weisman <eliza@buoyant.io>

## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
