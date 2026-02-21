# Compliance Evidence Bundle: Audit Logging Feature in Grafana

## Scenario

For a SOC 2 audit, your security team needs a compliance evidence bundle proving
that Grafana's app platform audit logging control is implemented end-to-end. You
need to trace the `auditLoggingAppPlatform` feature flag from its definition
through the API server wiring to the audit backend infrastructure.

## Your Task

Find ALL files in `grafana/grafana` that form the audit logging control across
these 4 layers:

### 1. Feature Flag Definition
- The feature flag registry where `auditLoggingAppPlatform` is defined
- Generated constants files (Go, TypeScript, CSV, JSON) that reference this flag

### 2. Audit Infrastructure
- The `Logger` interface definition for audit logging
- The `Event` model/struct used for audit events
- The `Policy` evaluation logic for audit decisions
- The `Noop` implementation (no-op backend for when auditing is disabled)

### 3. API Server Wiring
- The `APIGroupAuditor` interface definition
- Policy aggregation logic that connects feature flags to audit backends
- Service dependency injection that wires auditing into the API server

### 4. Wire/DI Registration
- Wire sets and generated wire code that register audit components

## Available Resources

The local `/workspace/` directory contains all repositories:
- `grafana/grafana` at v11.4.0 → `/workspace/grafana`
- `grafana/loki` at v3.3.4 → `/workspace/loki`

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {"repo": "grafana/grafana", "path": "pkg/services/featuremgmt/registry.go"}
  ],
  "text": "Comprehensive explanation of how the 4 layers connect: feature flag definition → audit infrastructure → API server wiring → DI registration."
}
```

**Important**: Use `grafana/grafana` as the exact `repo` identifier. Strip the
`github.com/` prefix that Sourcegraph MCP tools return.

**Deep Search hint**: This task requires synthesizing across feature management,
API server infrastructure, and dependency injection layers. Deep Search is
particularly well-suited for tracing these cross-cutting concerns.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find the architecturally significant files across all 4 layers?
- **Keyword coverage**: Does your answer reference the key interfaces and types (`auditLoggingAppPlatform`, `APIGroupAuditor`, `audit.Backend`, `NoopBackend`, `Logger`)?
- **Provenance**: Does your answer cite the correct repos and directory paths?
- **Rubric judge**: An LLM judge will assess evidence completeness, cross-component tracing, auditor actionability, and technical accuracy.
