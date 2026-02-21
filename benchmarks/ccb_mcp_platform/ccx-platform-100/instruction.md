# Platform Audit: Deprecated Struct Fields in Kubernetes API Types

## Your Task

Your platform team is inventorying deprecated API fields that are still defined in Kubernetes. Find all Go source files in `kubernetes/kubernetes` that define struct fields or constants with `Deprecated` in the identifier name (e.g., `DeprecatedServiceAccount`, `DeprecatedTopology`, `DeprecatedSource`).

## Scope

Search `staging/src/k8s.io/api/` and `pkg/apis/` directories. Include both the API types (staging) and internal types (pkg/apis). Also include the annotation constants file that defines deprecated annotation key constants.

**IMPORTANT**: Only include files that DEFINE the deprecated identifiers (struct field declarations or const declarations). Do not include files that merely reference or use these deprecated fields (e.g., conversion functions, deepcopy, tests).

## Context

You are performing a platform audit to inventory all deprecated but still-present API fields in Kubernetes. This is a prerequisite for planning deprecation removal timelines and assessing backward compatibility impact. The deprecated fields span core types (Pod, Container), discovery types (EndpointSlice), event types, and annotation constants.

## Available Resources

The local `/workspace/` directory contains:
- `kubernetes/kubernetes` at v1.32.0 → `/workspace/kubernetes`
- `etcd-io/etcd` at v3.5.17 → `/workspace/etcd`
- `grafana/grafana` at v11.4.0 → `/workspace/grafana`

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "kubernetes/kubernetes", "path": "relative/path/to/file.go"}
  ],
  "text": "Narrative explanation of deprecated fields found."
}
```

**Important**: Use `"kubernetes/kubernetes"` for the repo name. Strip `github.com/` prefix.
**Note**: Sourcegraph MCP tools return repo names with a `github.com/` prefix (e.g., `github.com/kubernetes/kubernetes`). Strip this prefix in your answer.

Include only the `files` field. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all files that define deprecated struct fields or constants?
- **Keyword presence**: Does your answer reference key deprecated identifiers (DeprecatedServiceAccount, DeprecatedTopology, DeprecatedSource, DeprecatedSeccompProfileDockerDefault)?
