# Platform Engineering: CODEOWNERS Infrastructure Discovery

## Your Task

Your platform team needs to understand how code ownership works in Grafana — not just the CODEOWNERS file itself, but the entire infrastructure around it: manifest generation, CI validation, Go integration with feature management, and npm scripts.

**Specific question**: Find all files in `grafana/grafana` that form the CODEOWNERS infrastructure:

1. **The actual CODEOWNERS file** — the GitHub ownership definition
2. **CI workflows** that validate CODEOWNERS
3. **Manifest generation scripts** (JavaScript) that parse and index CODEOWNERS
4. **Go code** that defines the `codeowner` type for feature management
5. **npm scripts** that orchestrate manifest generation

This crosses YAML (CI), JavaScript (scripts), Go (backend), and file ownership conventions.

## Context

You are a platform engineer investigating how code ownership is implemented and enforced in a large monorepo. Understanding this infrastructure is critical for onboarding new teams, debugging CI failures related to CODEOWNERS validation, and extending the ownership system to new areas of the codebase.

## Available Resources

Your ecosystem includes the following repositories:
- `grafana/grafana` at v11.4.0

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "grafana/grafana", "path": "relative/path/to/file"}
  ],
  "text": "Narrative explanation of the CODEOWNERS infrastructure."
}
```

**Important**: Use `"grafana/grafana"` for the repo name. Strip `github.com/` prefix.
**Note**: Sourcegraph MCP tools return repo names with a `github.com/` prefix (e.g., `github.com/grafana/grafana`). Strip this prefix in your answer.

Include only the `files` field. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all files that form the CODEOWNERS infrastructure?
- **Keyword presence**: Does your answer reference key identifiers (CODEOWNERS, codeowners-manifest, codeowner)?
