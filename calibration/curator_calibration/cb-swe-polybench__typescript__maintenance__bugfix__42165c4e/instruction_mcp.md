# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

- `github.com/sg-evals/code-server--5d3c9edc` — use `repo:^github.com/sg-evals/code-server--5d3c9edc$` filter

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

# Fix: SWE-PolyBench__typescript__maintenance__bugfix__42165c4e

**Repository:** github.com/sg-evals/code-server--5d3c9edc (mirror of coder/code-server)
**Language:** typescript
**Category:** contextbench_cross_validation

## Description

[Bug]: Can't start 2 instances of code-server `4.14.0` for separate users
### Is there an existing issue for this?

- [X] I have searched the existing issues

### OS/Web Information

- Web Browser: Chrome
- Local OS: Ubuntu
- Remote OS: Windows
- Remote Architecture: amd64
- `code-server --version`: 4.14.0


### Steps to Reproduce

1. Run `/usr/bin/code-server` for user 1 - ok
2. Run `/usr/bin/code-server` for user 2 - fails with the following


### Expected

Both instances should start

### Actual

2nd instance fails to start

### Logs

2nd instance tries to open the same file

[2023-06-19T16:15:12.625Z] info  code-server 4.14.0 9955cd91a4ca17e47d205e5acaf4c342a917a5e9
[2023-06-19T16:15:12.626Z] info  Using user-data-dir ~/code-server/user
[2023-06-19T16:15:12.629Z] error EPERM: operation not permitted, unlink '/tmp/code-server-ipc.sock'


### Screenshot/Video

_No response_

### Does this issue happen in VS Code or GitHub Codespaces?

- [X] I cannot reproduce this in VS Code.
- [X] I cannot reproduce this in GitHub Codespaces.

### Are you accessing code-server over HTTPS?

- [X] I am using HTTPS.

### Notes

It seems that every instance is trying to write to `/tmp/code-server-ipc.sock`, this was not the case in `4.13.0`. Is there a way to specify an alternate socket file for each instance?


## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
