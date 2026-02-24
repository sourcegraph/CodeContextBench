# Security Compliance Audit: TLS Configuration Across Prometheus Stack

## Your Task

For a security audit, prove that TLS is enforced on all external interfaces of the Prometheus monitoring stack. Find all Go source files in `prometheus/prometheus` that define, load, validate, or apply TLS configuration for: scrape targets, remote write/read endpoints, the web server, tracing exporters, and service discovery plugins.

**NOTE**: The canonical TLS config struct is defined in the `prometheus-common` library (available in this task as `sourcegraph-testing/prometheus-common`). Include this definition file in your answer.

## Specific Files to Find

1. **TLS struct definition and factory function** (in prometheus-common)
2. **Config embedding** — where TLS is wired into scrape/remote/tracing configs
3. **Server-side TLS** — web server TLS setup
4. **Client-side TLS** — outbound connections: remote write, tracing, scrape, service discovery
5. **TLS validation** — promtool config validation

## Context

You are performing a compliance audit of the Prometheus monitoring stack. The goal is to verify that TLS is enforced on all external-facing interfaces. This requires tracing TLS configuration from its definition in the shared `prometheus-common` library through its embedding in Prometheus's own config, its application on the web server (server-side), its use in outbound connections (client-side), and its validation by the `promtool` CLI.

## Available Resources

Your ecosystem includes the following repositories:
- `prometheus/prometheus` at v3.2.1

## Output Format

Create a file at `/workspace/answer.json` with your findings in the following structure:

```json
{
  "files": [
    {"repo": "prometheus/prometheus", "path": "relative/path/to/file.go"},
    {"repo": "sourcegraph-testing/prometheus-common", "path": "relative/path/to/file.go"}
  ],
  "text": "Narrative explanation of the TLS architecture across the Prometheus stack."
}
```

**Important**: Use `"prometheus/prometheus"` or `"sourcegraph-testing/prometheus-common"` for repo names. Strip `github.com/` prefix.
**Note**: Tool output may return repo names with a `github.com/` prefix (e.g., `github.com/prometheus/prometheus`). Strip this prefix in your answer.

Include only the `files` field. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant TLS configuration files across both repos?
- **Keyword presence**: Does your answer reference key TLS identifiers (TLSConfig, NewTLSConfig, ServeMultiple)?
- **Provenance**: Does your answer cite the correct repos and key file paths?
