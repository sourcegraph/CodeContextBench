# Incident Investigation: Loki Client Retry and Timeout Configuration

## Incident Report

Your team is investigating a Loki ingestion incident. Grafana sends logs to Loki
via both HTTP and gRPC clients, each with their own retry and timeout
configuration. To scope the incident, you need to find every Go source file in
`grafana/grafana` that implements the Loki client retry/timeout logic.

## Your Task

Find all Go source files in `grafana/grafana` under `pkg/components/loki/` that
define or configure:

1. **HTTP client timeout and retry/backoff logic** — files containing `StopNow`,
   `Timeout`, and `backoff` configuration for the HTTP Loki client
2. **gRPC client retry configuration** — files containing `grpcretry.WithMax`,
   `Timeout` for the gRPC Loki client

Include both the client implementation files AND their configuration struct
definition files. Also include the HTTP fake/stub client used for testing.

## Available Resources

Your ecosystem includes the following repositories:
- `grafana/grafana` at v11.4.0
- `grafana/loki` at v3.3.4

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {"repo": "grafana/grafana", "path": "pkg/components/loki/lokihttp/client.go"},
    {"repo": "grafana/grafana", "path": "pkg/components/loki/lokihttp/config.go"}
  ],
  "text": "Narrative explanation of the retry/timeout logic found in each file."
}
```

**Important**: Use `grafana/grafana` as the exact `repo` identifier. Strip the
`github.com/` prefix that Sourcegraph MCP tools return.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all 5 files under `pkg/components/loki/` that implement retry/timeout logic?
- **Keyword coverage**: Does your answer mention the key symbols (`StopNow`, `grpcretry`, `Timeout`, `WithMax`, `BackoffConfig`)?
