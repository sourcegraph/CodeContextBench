# LLVM Legacy Pass Manager to New Pass Manager Migration Inventory

## Your Task

LLVM has been migrating from the legacy pass manager to the new pass manager. Find C++ source files in `llvm/llvm-project` under `llvm/lib/Transforms/Scalar/` and `llvm/lib/Transforms/IPO/` that still contain references to legacy pass manager infrastructure. Specifically, find files that: 1. Use `INITIALIZE_PASS` or `INITIALIZE_PASS_BEGIN`/`INITIALIZE_PASS_END` macros. 2. Inherit from `FunctionPass` or `ModulePass` (legacy base classes). 3. Define `create*Pass()` factory functions (legacy registration pattern). Report each file path and which legacy patterns it uses.

## Context

You are working on a codebase task involving repos from the migration domain.

## Available Resources

No local repositories are pre-checked out.

**Note:** Additional repositories may be relevant to this task:
- `github.com/llvm/llvm-project` (llvm/llvm-project)
- `github.com/gcc-mirror/gcc` (gcc-mirror/gcc)

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
