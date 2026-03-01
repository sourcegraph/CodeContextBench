# ext_authz Filter Handoff Document

## 1. Purpose

The ext_authz (external authorization) filter is Envoy's extensibility mechanism for implementing authorization policies by delegating authorization decisions to an external service. Instead of hardcoding authorization logic into the proxy, organizations can centralize authorization policy in a dedicated service that the proxy consults for each request.

### What problems does it solve?
- **Decoupled authorization**: Move authorization logic out of the proxy configuration into a dedicated service
- **Unified policy engine**: Implement complex authorization policies (RBAC, attribute-based access control, etc.) in one place
- **Dynamic policy updates**: Change authorization rules without redeploying Envoy
- **Cross-cutting concerns**: Apply consistent authorization across multiple services without modifying each upstream

### When would someone use it?
- Enterprise deployments requiring sophisticated access control (e.g., JWT validation, OIDC integration, policy-based access control)
- Multi-tenant systems where authorization rules change frequently
- Organizations wanting to implement a "zero-trust" architecture
- Systems requiring audit trails of authorization decisions

## 2. Dependencies

### Upstream Dependencies

**Core Envoy interfaces:**
- `envoy/http/filter.h` - HTTP filter interface (HTTP version only)
- `envoy/network/filter.h` - Network (L4) filter interface (network version only)
- `envoy/upstream/cluster_manager.h` - Cluster management for routing authorization requests
- `envoy/runtime/runtime.h` - Runtime configuration for feature flags (e.g., `envoy.reloadable_features.ext_authz_measure_timeout_on_check_created`)
- `envoy/tracing/tracer.h` - Distributed tracing support for authorization calls
- `envoy/stats/stats.h` - Metrics collection

**Authorization service contract:**
- `envoy/service/auth/v3/external_auth.pb.h` - gRPC `CheckRequest`/`CheckResponse` protobuf definitions
- `envoy/service/auth/v3/attribute_context.pb.h` - Request/response attributes sent to auth service

**Common ext_authz library:**
- `source/extensions/filters/common/ext_authz/ext_authz.h` - Abstract `Client` interface
- `source/extensions/filters/common/ext_authz/ext_authz_grpc_impl.h` - gRPC client implementation
- `source/extensions/filters/common/ext_authz/ext_authz_http_impl.h` - Raw HTTP client implementation
- `source/extensions/filters/common/ext_authz/check_request_utils.h` - Utilities for building `CheckRequest` from HTTP/network requests

**Configuration parsing:**
- `envoy/config/common/mutation_rules/v3/mutation_rules.proto` - Header mutation validation rules
- `envoy/type/matcher/v3/string.proto` - Header matcher definitions

### Downstream Consumers

**Router/filter chain integration:**
- HTTP filters can have per-route overrides via `ExtAuthzPerRoute` configuration
- Filter state is added to `StreamInfo` for access logging (namespace: `envoy.filters.http.ext_authz` or `envoy.filters.network.ext_authz`)
- Dynamic metadata from the authorization service is consumed by downstream filters

**Produced metrics:**
- `ext_authz.ok` - Authorized requests
- `ext_authz.denied` - Denied requests
- `ext_authz.error` - Authorization service failures
- `ext_authz.failure_mode_allowed` - Requests allowed due to service failure in fail-open mode
- `ext_authz.disabled` - Requests skipped due to runtime disable
- `ext_authz.invalid` - Invalid authorization responses (when validation enabled)
- `ext_authz.timeout` - Authorization request timeouts

## 3. Relevant Components

### HTTP Filter Implementation
- **`source/extensions/filters/http/ext_authz/ext_authz.h`** (417 lines)
  - `Filter` class: Main HTTP filter implementing `Http::StreamFilter` and `RequestCallbacks`
  - `FilterConfig` class: Parses and holds configuration; manages stats and runtime features
  - `FilterConfigPerRoute` class: Per-route/virtualhost/weighted-cluster overrides
  - `ExtAuthzLoggingInfo` class: Filter state object holding latency, bytes transferred, cluster/host info
  - Core methods: `decodeHeaders()`, `decodeData()`, `decodeTrailers()` (request processing)
  - State management: `State::NotStarted`, `State::Calling`, `State::Complete`

- **`source/extensions/filters/http/ext_authz/ext_authz.cc`**
  - Implements filter logic: request buffering, metadata context filling, header mutation validation
  - Request path: Initiates auth call → waits for response → applies header/query mutations on OK
  - Denial path: Returns 403 (or configured `status_on_error`) to downstream
  - Failure handling: Applies `failure_mode_allow` logic (fail-open vs fail-closed)

- **`source/extensions/filters/http/ext_authz/config.h`** & **`config.cc`**
  - `ExtAuthzFilterConfig` factory class (Envoy plugin system)
  - Dynamically instantiates gRPC or HTTP client based on configuration
  - Creates filter instance per connection

### Network (L4) Filter Implementation
- **`source/extensions/filters/network/ext_authz/ext_authz.h`** (145 lines)
  - `Filter` class: Implements `Network::ReadFilter` and `RequestCallbacks`
  - Works at L4 (before application protocol parsing)
  - Buffers first data chunk, calls auth service, closes connection if denied
  - Stats: `cx_closed`, `denied`, `error`, `failure_mode_allowed`, `ok`, `total`, `disabled`, `active`

- **`source/extensions/filters/network/ext_authz/config.cc`**
  - Network filter factory; only supports gRPC clients (no HTTP)
  - Default timeout: 200ms

### Shared Library (Both HTTP & Network)
- **`source/extensions/filters/common/ext_authz/ext_authz.h`** (182 lines)
  - Abstract `Client` interface with `check()` method
  - `Response` struct: Contains `CheckStatus`, headers to add/set/remove, query params, body, dynamic metadata
  - `RequestCallbacks` interface: `onComplete()` callback invoked when authorization check finishes

- **`source/extensions/filters/common/ext_authz/ext_authz_grpc_impl.h`** & **`.cc`**
  - `GrpcClientImpl` class: gRPC client using Envoy's typed async client
  - Uses protocol buffer definitions from `envoy/service/auth/v3/`
  - Handles gRPC status codes, failures; creates child span for tracing
  - Supports timeout configuration (default 200ms)

- **`source/extensions/filters/common/ext_authz/ext_authz_http_impl.h`** & **`.cc`**
  - `RawHttpClientImpl` class: Raw HTTP/1.1 client using `Http::AsyncClient`
  - Parses HTTP response (headers, status code, body) into `Response` struct
  - Failure modes: Connection reset, exceed response buffer limit
  - Less flexible than gRPC (response format is HTTP headers, not protobuf)

- **`source/extensions/filters/common/ext_authz/check_request_utils.h`** & **`.cc`**
  - Utilities for constructing `CheckRequest` from HTTP/network request attributes
  - Handles metadata context extraction (filter metadata, typed metadata, route metadata)
  - Header selection: respects `allowed_headers` and `disallowed_headers` matchers

### Configuration Schemas (Protobuf)
- **`api/envoy/extensions/filters/http/ext_authz/v3/ext_authz.proto`**
  - Message `ExtAuthz`: Core filter configuration
  - Message `ExtAuthzPerRoute`: Per-route overrides
  - Message `CheckSettings`: Per-route auth check settings (context extensions, request body config)
  - Message `BufferSettings`: Request body buffering options
  - Message `HttpService`: HTTP authorization service configuration
  - Fields of interest:
    - `failure_mode_allow` (bool): Fail open vs fail closed
    - `failure_mode_allow_header_add` (bool): Add `x-envoy-auth-failure-mode-allowed` on error
    - `with_request_body` (BufferSettings): Enable request body buffering
    - `clear_route_cache` (bool): Clear route cache on auth response
    - `status_on_error` (HttpStatus): Status code on auth service error
    - `validate_mutations` (bool): Validate response headers/query params
    - `metadata_context_namespaces`: Metadata to pass to gRPC auth service
    - `filter_enabled`: Runtime fractional percent to disable filter
    - `allowed_headers` / `disallowed_headers`: Header matchers for auth request
    - `encode_raw_headers` (bool): Send raw headers (no sanitization)
    - `decoder_header_mutation_rules`: Validate header mutations against rules
    - `emit_filter_state_stats` (bool): Emit latency/bytes/cluster info to filter state
    - `enable_dynamic_metadata_ingestion` (bool): Accept dynamic metadata from auth service

- **`api/envoy/extensions/filters/network/ext_authz/v3/ext_authz.proto`**
  - Simpler than HTTP version (no HttpService, no per-route config)
  - Only gRPC service supported
  - Default timeout: 200ms

## 4. Failure Modes

### Authorization Service Unavailable / Timeout
**Symptom**: Auth service cluster not ready, network unreachable, or request timeout (default 200ms)

**Behavior**:
- **`failure_mode_allow: false`** (default, fail-closed): Request is denied; Envoy responds with 403 (Forbidden) or configured `status_on_error` code
- **`failure_mode_allow: true`** (fail-open): Request is allowed to proceed to upstream; `failure_mode_allowed` stat incremented
- **`failure_mode_allow_header_add: true`** + **`failure_mode_allow: true`**: Adds `x-envoy-auth-failure-mode-allowed: true` header to request

**Mitigation**:
- Configure appropriate timeout (default 200ms; increase for slow auth services)
- Monitor `ext_authz.error` and `ext_authz.timeout` stats
- Use `failure_mode_allow: true` only for graceful degradation (not recommended for security-critical deployments)

### Authorization Service Returns Denied (HTTP 401/403 or gRPC UNAUTHENTICATED/PERMISSION_DENIED)
**Symptom**: Auth service explicitly denies the request

**Behavior**:
- Request is terminated locally (not sent to upstream)
- Envoy responds with the status code from auth service (or 403 if unspecified)
- Optional response body from auth service is sent to downstream
- `ext_authz.denied` stat incremented
- Response code detail: `ext_authz_denied`

**Mitigation**: Log auth denial reasons; consider allowing auth service to return custom response bodies for diagnostic info

### Request Body Too Large
**Symptom**: Request exceeds `with_request_body.max_request_bytes` (HTTP only)

**Behavior**:
- Envoy responds with 413 (Payload Too Large)
- Auth service is **not** called
- Request does not reach upstream
- Precedence: This setting overrides `failure_mode_allow`

**Mitigation**: Set `max_request_bytes` high enough for expected payloads; consider `allow_partial_message: true` to send partial body instead

### Invalid Authorization Response
**Symptom**: Auth service returns headers/query params with invalid characters/encoding (when `validate_mutations: true`)

**Behavior**:
- Envoy responds with 500 (Internal Server Error)
- `ext_authz.invalid` stat incremented
- Response code detail: `ext_authz_invalid`
- Request does not reach upstream

**Mitigation**: Set `validate_mutations: true` to catch issues; debug auth service response format

### Non-UTF-8 Request Headers (gRPC Service)
**Symptom**: Downstream client sends headers with non-UTF-8 bytes; default sanitization is enabled

**Behavior**:
- By default, Envoy sanitizes header values to UTF-8 (invalid bytes replaced with `!`)
- Behavior is controlled by `encode_raw_headers` field:
  - `false` (default): Sanitize; multi-header values concatenated with commas; sent in `headers` field of CheckRequest
  - `true`: Send raw bytes; multi-header values preserved; sent in `header_map` field of CheckRequest

**Mitigation**: Set `encode_raw_headers: true` if auth service expects raw bytes

### Header Mutation Violations (Decoder Mutation Rules)
**Symptom**: Auth service returns headers that violate `decoder_header_mutation_rules` config

**Behavior**:
- Header is rejected (not applied to request)
- `filter_state_name_collision` stat may increment if internal header conflict

**Mitigation**: Configure appropriate `decoder_header_mutation_rules` or disable if not needed

### Dynamic Metadata Ingestion
**Symptom**: Auth service returns dynamic metadata but filter configured with `enable_dynamic_metadata_ingestion: false`

**Behavior**:
- Dynamic metadata is ignored
- `ignored_dynamic_metadata` stat incremented
- Request continues normally

**Mitigation**: Set `enable_dynamic_metadata_ingestion: true` (default) to accept metadata

### Filter Disabled at Runtime
**Symptom**: `filter_enabled` runtime key evaluates to disabled, or filter disabled via per-route config

**Behavior**:
- Request skips auth check
- `ext_authz.disabled` stat incremented
- If `deny_at_disable: true`, request is denied (with `status_on_error` code)

**Mitigation**: Use `filter_enabled` with fractional percent for gradual rollout; `deny_at_disable` for forced authz when disabled

## 5. Testing

### Test Directory Structure
```
test/extensions/filters/http/ext_authz/
  - ext_authz_test.cc              # Unit tests (1000+ lines)
  - ext_authz_integration_test.cc   # Integration tests (1600+ lines)
  - ext_authz_grpc_fuzz_test.cc     # Fuzzing (gRPC)
  - ext_authz_http_fuzz_test.cc     # Fuzzing (HTTP)
  - config_test.cc                  # Configuration parsing
  - ext_authz_fuzz_lib.{h,cc}       # Fuzzing library
  - ext_authz.yaml                  # Test configuration
  - logging_test_filter.{proto,cc}  # Test filter for logging

test/extensions/filters/common/ext_authz/
  - ext_authz_grpc_impl_test.cc     # gRPC client tests
  - ext_authz_http_impl_test.cc     # HTTP client tests
  - check_request_utils_test.cc     # CheckRequest building utilities
  - mocks.{h,cc}                    # MockClient for testing
  - test_common.{h,cc}              # Shared test utilities

test/extensions/filters/network/ext_authz/
  - ext_authz_test.cc               # Network filter unit tests
```

### Test Categories

**Unit Tests** (`ext_authz_test.cc`, 1000+ lines):
- Request/response header handling (add, set, remove)
- Query parameter mutations
- Metadata context extraction
- Per-route configuration merging
- Failure mode behavior (allow vs deny)
- Timeout handling
- Filter enable/disable logic
- Body buffering limits
- Dynamic metadata handling
- Stats validation

Key test patterns:
```cpp
// Typical test structure:
EXPECT_CALL(*client_, check(_, _, _, _))
    .WillOnce(Invoke([&](Filters::Common::ExtAuthz::RequestCallbacks& callbacks, ...) {
        callbacks.onComplete(std::move(response_ptr));
    }));
EXPECT_EQ(Http::FilterHeadersStatus::Continue, filter_->decodeHeaders(headers, false));
```

**Integration Tests** (`ext_authz_integration_test.cc`, 1600+ lines):
- End-to-end HTTP flow with fake upstream auth service
- gRPC authorization server scenarios
- HTTP authorization server scenarios
- Failure modes (timeout, connection error)
- Header mutation validation
- Buffer limit scenarios
- Route-specific configuration

Key test patterns:
- Use `FakeUpstream` to simulate auth service
- Test with `HttpIntegrationTest` framework
- Parameterized tests for gRPC vs HTTP clients

**Fuzzing Tests**:
- `ext_authz_grpc_fuzz_test.cc` / `ext_authz_http_fuzz_test.cc`
- Uses libFuzzer with protobuf corpus
- Fuzzes configuration and request handling

**Mocks** (`mocks.h`):
- `MockClient`: Mock ext_authz service for unit tests
- Allows testing filter logic in isolation

### Running Tests

```bash
# Run HTTP filter unit tests
bazel test //test/extensions/filters/http/ext_authz:ext_authz_test

# Run integration tests
bazel test //test/extensions/filters/http/ext_authz:ext_authz_integration_test

# Run gRPC client tests
bazel test //test/extensions/filters/common/ext_authz:ext_authz_grpc_impl_test

# Run HTTP client tests
bazel test //test/extensions/filters/common/ext_authz:ext_authz_http_impl_test

# Run network filter tests
bazel test //test/extensions/filters/network/ext_authz:ext_authz_test

# Run all ext_authz tests
bazel test //source/extensions/filters/http/ext_authz/... \
           //source/extensions/filters/network/ext_authz/... \
           //test/extensions/filters/http/ext_authz/... \
           //test/extensions/filters/network/ext_authz/...
```

## 6. Debugging

### Key Logs and Trace Points

**Enable DEBUG logging**:
```yaml
admin:
  access_log_path: /tmp/admin_access.log
  address:
    socket_address:
      protocol: TCP
      address: 127.0.0.1
      port_value: 9901

# In Envoy config:
logging:
  level: debug
  # Filter-specific logging
  loggers:
  - name: envoy.extensions.filters.http.ext_authz
    level: debug
```

**Important log lines to look for** (Logger ID: `ext_authz`):
- "Calling external authorization service" → Authorization request initiated
- "External authorization service response received" → Response from auth service
- "External authorization service error" → Service failure, gRPC error code logged
- "Injecting header" / "Removing header" → Header mutations applied
- "Request denied by external authorization service" → Request denied
- "Authorization failed with code" → Service returned error status

### Metrics to Monitor

**Counters**:
- `ext_authz.ok` ↑ on successful authorization
- `ext_authz.denied` ↑ on denied requests (watch for attacks/misconfiguration)
- `ext_authz.error` ↑ on auth service failures (circuit breaker, timeout, connection reset)
- `ext_authz.failure_mode_allowed` ↑ on service failures in fail-open mode
- `ext_authz.disabled` ↑ on filter disable via runtime
- `ext_authz.timeout` ↑ on request timeout to auth service
- `ext_authz.invalid` ↑ on invalid response (validate_mutations enabled)

**Gauges** (network filter only):
- `ext_authz.active` — Currently-pending auth checks

**Cluster-level stats** (if using gRPC):
- `cluster.ext_authz.upstream_rq_time_bucket_*` — Authorization latency histogram
- `cluster.ext_authz.upstream_rq_pending_*` — Buffered requests waiting for auth
- `cluster.ext_authz.circuit_breakers.default.remaining_requests` — Circuit breaker status

### Filter State for Access Logging

When `emit_filter_state_stats: true`, the filter emits `ExtAuthzLoggingInfo` to filter state:
- Latency (`ext_authz_duration` in dynamic metadata, or `latency()` method)
- Bytes sent/received (gRPC only)
- Upstream cluster and host info (gRPC only)

Access log format to include auth latency:
```yaml
access_log:
  - name: envoy.access_loggers.file
    typed_config:
      "@type": type.googleapis.com/envoy.data.accesslog.v3.FileAccessLog
      path: /var/log/envoy/access.log
      # Use ext_authz_duration from dynamic metadata if available
```

### Tracing

The filter creates a child span under the request's parent span:
- Span name: "ext_authz"
- Tags:
  - `ext_authz_status`: "ext_authz_ok" | "ext_authz_unauthorized" | "ext_authz_error"
  - `ext_authz_http_status`: HTTP status code from auth service (if applicable)

Example trace viewing:
```bash
# Using Jaeger or Zipkin, filter by span name "ext_authz"
# Look for timing and error tags
```

### Common Issues and Debugging Strategies

**Issue**: `ext_authz.denied` spike
- **Check**: Auth service logic; look for pattern in denied request headers
- **Debug**: Enable auth service logs to see why requests are being denied
- **Metric**: Compare with `ext_authz.ok` to assess deny rate

**Issue**: `ext_authz.error` spike
- **Check**: Auth service availability; network connectivity; cluster health
- **Debug**: Look for "External authorization service error" logs with gRPC error codes
- **Metric**: Check cluster stats for connection errors, timeouts, circuit breaker trips
- **Action**: Increase timeout if service is slow; check upstream cluster configuration

**Issue**: `ext_authz.timeout` increasing
- **Check**: Auth service latency; network latency
- **Debug**: Look for "timed out waiting for external authorization response" logs
- **Metric**: Check `cluster.ext_authz.upstream_rq_time_bucket_*` histograms
- **Action**: Increase timeout; check auth service performance; scale auth service

**Issue**: Headers missing in upstream request after auth
- **Check**: Header mutation rules; allowed_headers matcher; filter-enabled status
- **Debug**: Enable header logging; check CheckResponse headers_to_add/headers_to_set fields
- **Metric**: Check filter_state_name_collision counter
- **Action**: Adjust decoder_header_mutation_rules or allowed_headers config

**Issue**: "High latency" on requests
- **Metric**: `ext_authz_duration` in filter state; `cluster.ext_authz.upstream_rq_time`
- **Debug**: Determine if latency is in auth service response or network
- **Action**: Analyze auth service performance; consider caching or request batching

**Issue**: Requests denied due to invalid response
- **Check**: `validate_mutations: true` is set
- **Metric**: `ext_authz.invalid` counter
- **Debug**: Log auth service response; look for invalid character encoding or header syntax
- **Action**: Fix auth service response format

### Enabling Trace-level Debugging

For development, compile with debug symbols and use gdb/lldb to inspect filter state:

```cpp
// Useful breakpoints in ext_authz.cc:
// Filter::decodeHeaders() — Request entry point
// Filter::onComplete() — Response from auth service
// Filter::continueDecoding() — Request allowed, proceeding to upstream
```

### Performance Profiling

To understand auth latency impact:
1. Record baseline request latency without ext_authz
2. Enable ext_authz with `emit_filter_state_stats: true`
3. Compare `ext_authz_duration` from filter state with total request latency
4. If auth service adds >X ms overhead, investigate auth service perf or connection pooling

---

## Summary

The ext_authz filter is a critical component for delegating authorization decisions to external services. It's architected to support both L4 (network) and L7 (HTTP) filtering, with pluggable clients (gRPC and HTTP). The filter handles complex scenarios including request buffering, header mutations, failure modes, dynamic metadata, and per-route configuration. Debugging requires understanding the filter state machine, monitoring stats closely, and coordinating with the auth service implementation.
