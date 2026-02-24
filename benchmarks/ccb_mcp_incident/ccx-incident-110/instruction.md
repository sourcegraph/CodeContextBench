# Firefox Multi-Process Architecture: Content Process Lifecycle

## Your Task

An on-call engineer is debugging a content process crash in Firefox's multi-process (Fission) architecture. Trace the content process lifecycle by finding all C++ source files in `mozilla-firefox/firefox` under `dom/ipc/` that manage process creation, communication, and destruction: 1. The header and source files that define the `ContentParent` class — the parent-side content process manager. 2. The file that defines `ContentProcessManager` — the registry of all content processes. 3. The header file for `BrowserParent` — the parent-side tab representation. 4. The file that defines `PreallocatedProcessManager` — the process preallocation pool. Report the repo, file path, and key class name for each file.

## Context

You are working on a codebase task involving repos from the incident domain.

## Available Resources

No local repositories are pre-checked out.

**Note:** Additional repositories are accessible via Sourcegraph MCP tools:
- `sg-evals/firefox--871325b8` (mozilla-firefox/firefox)

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.cpp"}
  ],
  "symbols": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.cpp", "symbol": "SymbolName"}
  ],
  "chain": [
    {"repo": "org/repo-name", "path": "relative/path/to/file.cpp", "symbol": "FunctionName"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

Include only the fields relevant to this task. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant files?
