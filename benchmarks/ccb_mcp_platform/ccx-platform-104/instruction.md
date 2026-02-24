# LLVM Loop Vectorization Infrastructure

## Your Task

Identify all C++ source and header files in `llvm/llvm-project` that form the LLVM loop vectorization infrastructure. Find: 1. The main implementation file for the `LoopVectorizePass` (under `llvm/lib/Transforms/Vectorize/`). 2. The header that defines `LoopVectorizeOptions` and the pass interface (under `llvm/include/llvm/Transforms/Vectorize/`). 3. The file that defines `LoopVectorizationLegality` — the legality checker that decides if a loop can be vectorized. 4. The file that defines `LoopVectorizationCostModel` — determines profitable vectorization factors. 5. The file that implements `VPlan` (the Vectorization Plan) data structure representing the vectorized loop body. Report the repo, file path, and key class name for each file.

## Context

You are working on a codebase task involving repos from the platform domain.

## Available Resources

No local repositories are pre-checked out.

**Note:** Additional repositories are accessible via Sourcegraph MCP tools:
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
