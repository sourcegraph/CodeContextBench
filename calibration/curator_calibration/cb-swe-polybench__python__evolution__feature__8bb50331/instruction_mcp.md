# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

- `github.com/sg-evals/transformers--408b2d2b` — use `repo:^github.com/sg-evals/transformers--408b2d2b$` filter

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

# Fix: SWE-PolyBench__python__evolution__feature__8bb50331

**Repository:** github.com/sg-evals/transformers--408b2d2b (mirror of huggingface/transformers)
**Language:** python
**Category:** contextbench_cross_validation

## Description

The new impl for CONFIG_MAPPING prevents users from adding any custom models
## Environment info
<!-- You can run the command `transformers-cli env` and copy-and-paste its output below.
     Don't forget to fill out the missing fields in that output! -->

- `transformers` version: 4.10+
- Platform: Ubuntu 18.04
- Python version: 3.7.11
- PyTorch version (GPU?): N/A
- Tensorflow version (GPU?): N/A
- Using GPU in script?: N/A
- Using distributed or parallel set-up in script?: No.

### Who can help
<!-- Your issue will be replied to more quickly if you can figure out the right person to tag with @
 If you know how to use git blame, that is the easiest way, otherwise, here is a rough guide of **who to tag**.
 Please tag fewer than 3 people.
 -->


## Information

Model I am using (Bert, XLNet ...): _Custom_ model

The problem arises when using:
* [ ] the official example scripts: (give details below)
* [x] my own modified scripts: (give details below)

The tasks I am working on is:
* [x] an official GLUE/SQUaD task: (give the name)
* [ ] my own task or dataset: (give details below)

## To reproduce

See: https://github.com/huggingface/transformers/blob/010965dcde8ce9526f6a7e6e2c3f36276c153708/src/transformers/models/auto/configuration_auto.py#L297

This was changed from the design in version `4.9` which used an `OrderedDict` instead of the new `_LazyConfigMapping`. The current design makes it so users cannot add their own custom models by assigning names and classes to the following registries (example: classification tasks):

- `CONFIG_MAPPING` in `transformers.models.auto.configuration_auto`, and
- `MODEL_FOR_SEQUENCE_CLASSIFICATION_MAPPING` in `transformers.models.auto.modeling_auto`.

<!-- If you have code snippets, error messages, stack traces please provide them here as well.
     Important! Use code tags to correctly format your code. See https://help.github.com/en/github/writing-on-github/creating-and-highlighting-code-blocks#syntax-highlighting
     Do not use screenshots, as they are hard to read and (more importantly) don't allow others to copy-and-paste your code.-->

## Expected behavior

Either a mechanism to add custom `Config`s (and the corresponding models) with documentation for it, or documentation for whatever other recommended method. Possibly that already exists, but I haven't found it yet.

<!-- A clear and concise description of what you would expect to happen. -->

@sgugger 


## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
