# Stack Protection Mechanisms in LLVM

## Your Task

Find all C++ source files in `llvm/llvm-project` that implement stack protection mechanisms against buffer overflow attacks. Specifically identify: 1. The LLVM pass that inserts stack protector checks (look for `StackProtector` in `llvm/lib/CodeGen/`). 2. The file that defines the `SafeStack` pass that separates safe and unsafe stack allocations (under `llvm/lib/CodeGen/`). 3. The header file that declares the stack protection pass interface. 4. The compiler-rt runtime file that provides the `__stack_chk_fail` implementation (look under `compiler-rt/lib/builtins/`). 5. Any file in `llvm/lib/Transforms/Instrumentation/` that implements memory safety instrumentation related to stack frame protection. Report the repo, file path, and the primary function or class handling stack protection for each.

## Context

You are working on a codebase task involving repos from the security domain.

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
