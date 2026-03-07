# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

- `github.com/sg-evals/svelte--e4460e38` — use `repo:^github.com/sg-evals/svelte--e4460e38$` filter

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

# Fix: SWE-PolyBench__javascript__maintenance__bugfix__e647c8ce

**Repository:** github.com/sg-evals/svelte--e4460e38 (mirror of sveltejs/svelte)
**Language:** javascript
**Category:** contextbench_cross_validation

## Description

Hydrating element removes every other attribute
I'm new to Svelte so it's entirely possible i'm missing something basic.  I'm seeing some weird behavior around the hydration feature. Attributes on the element being hydrated are removed and I'm not sure why. 

For example, given this markup:
```html
<span id="rehydrateContainer">
  <button data-track-id="123" class="button button--small" id="button" role="button" disabled>content</button>
</span>
```
and this component:
```html
<button on:click="set({ count: count + 1 })">
  {text} {count}
</button>

<script>
  export default {
    oncreate() {
      this.set({ count: 0 });
    }
  };
</script>
```
the hydrated dom ends up being this:
```html
<span id="rehydrateContainer">
  <button class="button button--small" role="button">rehydrated 0</button>
</span>
```

At first glance it seems that it maybe only works with certain attributes like `class` or `role` but that's not the case. When I change the order it seems like the odd numbered attributes are being removed.

given this:
```html
<button class="button button--small" data-track-id="123" role="button" id="button" disabled>content</button>
```

we end up with this:
```html
<button data-track-id="123" id="button">rehydrated 0</button>
```

here's a small reproduction to play around with: https://github.com/sammynave/rehydrate-attrs


## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
