# Security Audit: Missing Authentication Middleware in HTTP Handlers

## Your Task

Your security team is conducting an audit of the Grafana observability stack.
The pattern in `grafana/grafana` (local) shows proper authentication middleware
usage: HTTP handlers are wrapped with `middleware.AuthenticateUser` to enforce
tenant authentication.

Your task is to **find Go source files in the MCP-only repositories** (Loki
and/or Mimir) that register HTTP handlers or routes **without applying
authentication middleware** such as `middleware.AuthenticateUser`.

For each file found, report:
- The repository (`org/repo-name`)
- The file path within the repository
- The specific endpoint path(s) registered without authentication

## Context

You are auditing a microservices observability stack. The local `grafana/grafana`
repo correctly wraps its compactor deletion endpoint with authentication:

```go
// Example from pkg/compactor/ui.go — middleware applied correctly
mw := middleware.Merge(
    middleware.AuthenticateUser,
    deletion.TenantMiddleware(c.limits),
)
```

In contrast, some files in the MCP-only repos may register endpoints directly
with `mux.HandleFunc(...)` without any auth middleware wrapping, or use
`RegisterRoute(...)` with `auth=false`. These are the files your audit needs
to surface.

## Available Resources

The local `/workspace/` directory contains: `grafana/grafana`.

**Note:** Additional repositories are accessible via Sourcegraph MCP tools:
- `sg-benchmarks/grafana-loki` (log-aggregation)
- `sg-benchmarks/grafana-mimir` (metrics-backend)

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {
      "repo": "org/repo-name",
      "path": "relative/path/to/file.go",
      "endpoints": ["/endpoint/path/1", "/endpoint/path/2"]
    }
  ],
  "text": "Narrative citing specific repos, file paths, and endpoint paths registered without authentication."
}
```

Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find the Go files that register handlers without authentication middleware?
- **Provenance**: Does your answer cite the specific repos and file paths?
