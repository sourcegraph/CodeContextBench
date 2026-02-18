# Task: Envoy Connection Pool Management Troubleshooting Runbook

## Objective

Generate a comprehensive troubleshooting runbook for Envoy's connection pool management system. The runbook should be written for platform engineers debugging Envoy connection issues in production environments.

## Repository

The Envoy repository is cloned at `/workspace`. Focus your investigation on the following key areas:

- `source/common/conn_pool/` -- core connection pool implementation
- `source/common/upstream/` -- upstream connection and cluster management
- `source/common/http/conn_pool_base.cc` -- HTTP connection pool base class
- `source/common/http/http1/conn_pool.cc` and `source/common/http/http2/conn_pool.cc` -- protocol-specific pools
- `source/common/upstream/cluster_manager_impl.cc` -- cluster manager implementation
- `source/common/upstream/resource_manager_impl.h` -- resource limiting (circuit breakers)

## Required Content

Your runbook must cover the following four areas:

### 1. Common Failure Scenarios (Critical)

Document the following failure scenarios with symptoms, root causes, and resolution steps:

- **Connection pool exhaustion**: What happens when `max_connections` is reached, how pending requests overflow, and how to identify this from stats
- **Circuit breaker trips**: How Envoy's circuit breakers interact with connection pools, the `cx_pool_overflow` and `upstream_rq_pending_overflow` counters, and threshold tuning
- **DNS resolution failures**: How `STRICT_DNS` and `LOGICAL_DNS` cluster types handle DNS failures and their impact on the connection pool
- **Upstream health check failures**: How outlier detection and health check failures lead to host ejection and reduced pool capacity
- **Connection timeout cascades**: How `connect_timeout` failures can cascade into retry storms and pool exhaustion
- **TLS handshake failures**: How SSL/TLS errors (certificate verification failures, handshake timeouts) affect upstream connections

### 2. Diagnostic Commands and Stats

Provide actionable diagnostic commands using Envoy's admin API:

- `/clusters` endpoint: how to read cluster membership, health status, and connection counts
- `/stats` endpoint: key stats to filter for, including `upstream_cx_active`, `upstream_cx_connect_fail`, `upstream_rq_pending_active`, `upstream_rq_pending_overflow`
- `/config_dump` endpoint: how to inspect runtime circuit breaker and connection pool configuration
- Specific stat paths and their meaning (e.g., `cluster.<name>.upstream_cx_active`, `cluster.<name>.circuit_breakers.<priority>.cx_pool_open`)
- Example curl commands or admin API queries

### 3. Configuration Fixes

For each failure scenario, provide specific Envoy configuration remediation:

- **Circuit breaker thresholds**: `circuit_breakers` settings including `max_connections`, `max_pending_requests`, `max_requests`, and `max_retries`
- **Connection timeout settings**: `connect_timeout`, `idle_timeout`, `max_connection_duration` tuning
- **Connection pool tuning**: `per_upstream_preconnect_ratio`, connection pool type selection, `max_connections_per_host` considerations
- **Retry and outlier detection**: `outlier_detection` settings (`consecutive_5xx`, `interval`, `base_ejection_time`), `retry_policy` interaction with pool pressure

### 4. Code-Level Debugging

Reference specific C++ classes and code structures for deeper debugging:

- `ConnPoolImplBase` / `conn_pool_base.cc`: connection lifecycle, `ActiveClient` management, drain mechanics
- `ClusterManagerImpl` / `cluster_manager_impl.cc`: how clusters own and manage connection pools
- `ResourceManager` / `resource_manager_impl.h`: how circuit breaker resource limits are enforced
- Connection pool hierarchy: `HttpConnPoolImplBase`, `Http1ConnPoolImpl`, `Http2ConnPoolImpl`, `TcpConnPoolImpl`
- Key data structures: `ConnectingStream`, pending request queues, ready client lists

## Deliverable

Write your runbook to `/workspace/documentation.md` in Markdown format.

## Quality Bar

- Cite specific Envoy stats paths (e.g., `cluster.<name>.upstream_cx_active`)
- Include example admin API responses or curl commands where relevant
- Reference actual C++ class names and source file paths from the repository
- Provide concrete configuration YAML snippets for each fix
- Organize content for quick lookups during an incident (use clear headings, tables where appropriate)

## Anti-Requirements

- Do NOT cover Envoy installation, deployment, or general architecture
- Do NOT document xDS or control plane configuration
- Stay focused on connection pool troubleshooting -- do not write a general Envoy operations guide

## Success Criteria

Your runbook will be evaluated on:
- Coverage of all common failure scenarios with actionable resolution steps
- Inclusion of specific diagnostic commands and stat paths
- Concrete configuration fixes with YAML examples
- Accurate code-level references to connection pool internals
- Overall usefulness as a production troubleshooting resource
