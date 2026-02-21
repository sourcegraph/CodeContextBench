# Incident Debugging: etcd DialTimeout Configuration Across Kubernetes Ecosystem

## Your Task

During an incident, your Kubernetes cluster's etcd connections are timing out. You need
to find every location where the etcd client `DialTimeout` parameter is configured across
the Kubernetes apiserver and etcd codebase. Include both the consumer side (k8s apiserver
configuring the etcd client) and the provider side (etcd defining and using DialTimeout).

**Specific question**: Find all Go source files in:
1. `kubernetes/kubernetes` under `staging/src/k8s.io/apiserver/` that configure `DialTimeout`
2. `etcd-io/etcd` (or `sg-benchmarks/etcd-io-etcd`) under `client/` and `server/` that define or use `DialTimeout`

**IMPORTANT**: Exclude vendored files under `vendor/` directories — these are copies,
not authoritative sources. Also exclude test files (`_test.go`) — focus on production
source code that affects runtime behavior.

## Context

The etcd DialTimeout controls how long the etcd client waits when establishing a
connection. This timeout propagates through several layers:
- **Kubernetes apiserver** (`staging/src/k8s.io/apiserver/`) configures DialTimeout when
  creating the etcd client for storage backend access
- **etcd client library** (`client/v3/`) defines the DialTimeout config field and uses it
  during connection establishment
- **etcd server** (`server/`) uses DialTimeout for peer transport, gRPC proxy, and
  internal server configuration

During incident debugging, you need the complete picture of where this timeout is set,
passed through, and applied.

## Available Resources

The local `/workspace/` directory contains all repositories:
- `kubernetes/kubernetes` at v1.32.0 → `/workspace/kubernetes`
- `kubernetes/client-go` at v0.32.0 → `/workspace/client-go`
- `kubernetes/api` at v0.32.0 → `/workspace/api`
- `etcd-io/etcd` at v3.5.17 → `/workspace/etcd`

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {"repo": "kubernetes/kubernetes", "path": "staging/src/k8s.io/apiserver/pkg/storage/..."},
    {"repo": "etcd-io/etcd", "path": "client/v3/config.go"}
  ],
  "text": "Narrative explanation of the DialTimeout configuration chain."
}
```

**Important**: Use canonical repo names (`kubernetes/kubernetes`, `etcd-io/etcd`).
For Sourcegraph searches, the etcd mirror is `sg-benchmarks/etcd-io-etcd` — both names
are accepted. Sourcegraph MCP tools return repo names with a `github.com/` prefix —
strip this prefix in your answer.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all files where DialTimeout is configured or used?
- **Keyword presence**: Does your narrative mention key terms like `DialTimeout`, `dialTimeout`, and `timeout`?
