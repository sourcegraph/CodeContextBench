# Find and Prove Benchmark Suite

This suite tests your ability to navigate a large codebase, locate a reported bug, and write a regression test that **proves** the bug exists. You must find the root cause through code search and write a test that fails on the current (buggy) code.

## Search Strategy

**This repository is large.** You MUST use Sourcegraph MCP tools to locate the bug:

- Use `keyword_search` to find symbols, error messages, config keys, or patterns mentioned in the bug report
- Use `find_references` to trace how a buggy function or variable is used across the codebase
- Use `go_to_definition` to understand type hierarchies, interfaces, and function contracts
- Use `commit_search` to find recent commits that may have introduced the regression
- Use `diff_search` to inspect what code was added or removed in suspicious commits
- Use `read_file` to read full implementations once you've located the relevant file

## Output Requirements

Write your regression test as a **single file** at `/workspace/regression_test.{ext}` (use the appropriate extension for the project language — `.py`, `.go`, or `.test.ts`). Do NOT create a directory — write a single file directly at that path.

Your regression test MUST:
1. **Import or invoke** the buggy component directly
2. **Reproduce the exact symptom** described in the bug report
3. **Fail** (non-zero exit / assertion error) when run against the current buggy code
4. **Pass** (zero exit / assertions succeed) once the underlying bug is fixed

## Constraints

- Do **NOT** fix the bug — your job is to write the test only
- Do **NOT** modify any existing source files in `/workspace/`
- Test timeout: **60 seconds** per run — keep tests focused and fast
- Use the project's existing test framework and conventions when possible
