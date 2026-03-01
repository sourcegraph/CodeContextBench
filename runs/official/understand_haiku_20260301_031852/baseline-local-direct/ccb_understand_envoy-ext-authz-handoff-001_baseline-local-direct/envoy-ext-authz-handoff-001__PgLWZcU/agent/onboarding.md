# ext_authz Filter Handoff Document

## 1. Purpose

The **ext_authz filter** is Envoy's external authorization extension that delegates authorization decisions to an external service. It acts as a policy enforcement point in the request/connection flow, allowing you to implement centralized authorization logic outside of Envoy.

### Key Responsibilities:
- **Intercepts requests** at either the HTTP or TCP level before they reach upstream services
- **Calls an external authorization service** (either gRPC or raw HTTP) to make permit/deny decisions
- **Applies mutations** returned by the authorization service (headers, query parameters) to requests/responses
- **Handles authorization failures** gracefully based on configuration (fail-open or fail-closed)
- **Emits observability data** (metrics, logs, traces, dynamic metadata) for monitoring

### When to Use:
- Implementing centralized access control policies
- Integrating with external authorization systems (OPA, AuthZ services)
- Adding header-based or context-based authorization logic
- Performing cross-cutting authentication/authorization checks before routing
- Enforcing fine-grained access policies at the proxy level

### Configuration Variants:
- **HTTP Filter**: Operates on HTTP requests, returns 403 Forbidden on denial
- **Network Filter**: Operates on TCP connections, closes connection on denial
- Can be configured as first filter in the chain for early authorization checks

---

## 2. Dependencies

### Upstream Dependencies

#### External Services:
- **Authorization Service Cluster**: A gRPC or HTTP endpoint configured via cluster manager
  - gRPC: Uses `envoy::service::auth::v3::Authorization::Check` RPC method
  - HTTP: Custom HTTP endpoint accepting `CheckRequest` and returning `CheckResponse`
  - Both must implement the protocol defined in `envoy::service::auth::v3` API

#### Envoy Core Components:
- **Cluster Manager** (`envoy/upstream/cluster_manager.h`): Manages connections to auth service
- **gRPC Async Client Manager** (`envoy/grpc/async_client_manager.h`): Creates gRPC clients for auth service
- **HTTP Async Client** (`envoy/http/async_client.h`): Creates HTTP clients for raw HTTP auth service
- **Routing** (`source/common/router/*`): Route matching and per-route configuration
- **Runtime** (`envoy/runtime/runtime.h`): Runtime feature flags for filter enablement
- **Tracing** (`envoy/tracing/tracer.h`): Distributed tracing integration for auth requests
- **Stream Info** (`envoy/stream_info/stream_info.h`): Access to request metadata and connection info
- **Stats** (`envoy/stats/*`): Metrics reporting (counters, gauges)

#### Supporting Libraries:
- **Protobuf** (`google/protobuf/*`): Protocol buffer definitions for CheckRequest/CheckResponse
- **gRPC Core** (`source/common/grpc/*`): gRPC transport layer
- **HTTP Utility** (`source/common/http/utility.h`): Header/query parameter manipulation
- **Mutation Rules** (`source/extensions/filters/common/mutation_rules/*`): Header mutation validation

### Downstream Consumers

#### HTTP Filter Chain:
- **Decoder Filters**: Other HTTP filters in the request path (encryption, routing, etc.)
- **Encoder Filters**: Response-phase filters that apply response headers from authz service
- **Router Filter**: Uses request mutations (headers, query params) for routing decisions

#### Network Filter Chain:
- **Read Filters**: Subsequent TCP-level filters in the connection pipeline
- **Connection Callbacks**: Integration with connection lifecycle events

#### Logging & Observability:
- **Filter State**: Can register dynamic metadata for downstream filters
- **Access Logs**: Provides logging info via `ExtAuthzLoggingInfo` in filter state
- **Trace Context**: Participates in distributed tracing with parent span context

---

## 3. Relevant Components

### HTTP Filter Implementation

#### **source/extensions/filters/http/ext_authz/ext_authz.h**
- **Role**: HTTP-specific filter interface and state machine
- **Key Classes**:
  - `Filter`: Main HTTP filter implementing `Http::StreamFilter` and `RequestCallbacks`
    - Manages request/response lifecycle (decode/encode headers, data, trailers)
    - Maintains authorization state (NotStarted, Calling, Complete)
    - Handles per-route configuration and filter enablement
  - `FilterConfig`: Global HTTP filter configuration
    - Parsed from `ExtAuthz` protobuf config
    - Manages global settings (timeouts, failure modes, mutation rules)
    - Provides statistics scope and runtime features
  - `FilterConfigPerRoute`: Per-route authorization overrides
    - Allows disabling authz for specific routes
    - Per-route context extensions and buffer settings
  - `ExtAuthzLoggingInfo`: Filter state object for logging information
    - Records auth request latency, bytes sent/received
    - Stores cluster and upstream host information

#### **source/extensions/filters/http/ext_authz/ext_authz.cc**
- **Role**: HTTP filter implementation (~850 lines)
- **Key Methods**:
  - `decodeHeaders()`: Initiates auth check on request headers
  - `decodeData()`: Buffers request body if needed for auth
  - `decodeTrailers()`: Completes request buffering
  - `encodeHeaders()`/`encodeData()`/`encodeTrailers()`: Applies response mutations
  - `onComplete()`: Callback when auth service responds
  - `initiateCall()`: Creates CheckRequest and sends to auth service
  - `continueDecoding()`: Resumes filter chain after auth completes
- **State Management**:
  - Tracks authorization state and filter return codes
  - Manages async callback handling (synchronous vs asynchronous)
  - Buffers request data if `with_request_body` configured

#### **source/extensions/filters/http/ext_authz/config.cc**
- **Role**: Filter factory and registration
- **Key Functions**:
  - `createFilterFactoryFromProtoWithServerContextTyped()`: Creates filter factory callback
    - Determines whether to use gRPC or HTTP client
    - Configures client timeouts and cluster connections
    - Registers filter with HTTP filter chain
  - `createRouteSpecificFilterConfigTyped()`: Creates per-route config
  - `LEGACY_REGISTER_FACTORY()`: Registers filter with Envoy's extension registry

#### **api/envoy/extensions/filters/http/ext_authz/v3/ext_authz.proto**
- **Role**: Configuration schema for HTTP ext_authz filter
- **Key Fields**:
  - `grpc_service`: gRPC auth service configuration
  - `http_service`: Raw HTTP auth service configuration
  - `failure_mode_allow`: Fail-open on service unavailability
  - `with_request_body`: Buffer and send request body to auth service
  - `clear_route_cache`: Clear routing cache after auth modifications
  - `status_on_error`: HTTP status code for authorization failures
  - `validate_mutations`: Validate header mutations returned by auth service
  - `encode_raw_headers`: Encode headers as bytes in CheckRequest

### Network Filter Implementation

#### **source/extensions/filters/network/ext_authz/ext_authz.h**
- **Role**: Network-level authorization before TCP data is processed
- **Key Classes**:
  - `Filter`: TCP filter implementing `Network::ReadFilter` and `RequestCallbacks`
    - Intercepts new connections and routes to auth service
    - Closes connection on denial or error
  - `Config`: Network filter configuration
    - Similar to HTTP but for TCP-level settings
    - Manages per-connection authorization state

### Common Components (Shared by HTTP and Network)

#### **source/extensions/filters/common/ext_authz/ext_authz.h**
- **Role**: Base interfaces and data structures
- **Key Classes**:
  - `Client`: Abstract interface for authorization clients
    - `check()`: Sends check request to auth service
    - `cancel()`: Cancels in-flight auth requests
    - `streamInfo()`: Returns stream info from auth request
  - `RequestCallbacks`: Async callback interface
    - `onComplete()`: Called when auth service responds
  - `Response`: Authorization response object
    - Status (OK, Denied, Error)
    - Headers/query parameters to mutate
    - Dynamic metadata to emit
    - Body and status code for denied responses
  - `CheckStatus`: Enum (OK, Error, Denied)

#### **source/extensions/filters/common/ext_authz/ext_authz_grpc_impl.h**
- **Role**: gRPC protocol client implementation (~230 lines)
- **Key Classes**:
  - `GrpcClientImpl`: Implements async gRPC client
    - Sends `CheckRequest` via gRPC unary RPC
    - Parses `CheckResponse` and builds Response object
    - Handles gRPC status codes and failures
    - Supports custom timeouts via async client options
- **Key Methods**:
  - `check()`: Initiates gRPC call
  - `onSuccess()`: Handles OK/Denied responses from auth service
  - `onFailure()`: Handles gRPC errors (timeouts, unavailable, etc.)
  - `cancel()`: Cancels in-flight gRPC request

#### **source/extensions/filters/common/ext_authz/ext_authz_http_impl.h**
- **Role**: Raw HTTP protocol client implementation (~280 lines)
- **Key Classes**:
  - `RawHttpClientImpl`: Implements HTTP async client
    - Sends `CheckRequest` as HTTP POST request
    - Parses HTTP response headers/body as Response
    - Matches response headers against configured patterns
  - `ClientConfig`: HTTP-specific configuration
    - Cluster name and path prefix
    - Header matchers for selecting which response headers to forward
    - Request/response header parsing rules
- **Key Methods**:
  - `check()`: Initiates HTTP POST to auth service
  - `onSuccess()`: Parses HTTP response into Response object
  - `onFailure()`: Handles HTTP request failures
  - `toResponse()`: Converts HTTP response to internal Response format

#### **source/extensions/filters/common/ext_authz/check_request_utils.h**
- **Role**: Utility for constructing CheckRequest from request context (~380 lines)
- **Key Functions**:
  - `createHttpCheck()`: Extracts HTTP request attributes and fills CheckRequest
    - Copies headers (with filtering), query params, path, method, scheme
    - Includes peer/destination information, TLS details
    - Buffers request body if configured
    - Handles raw header encoding
  - `createTcpCheck()`: Extracts TCP connection attributes
    - Source/destination addresses and ports
    - TLS certificate information
  - `toRequestMatchers()`: Builds header matchers from protobuf config

---

## 4. Failure Modes

### Common Failure Scenarios

#### **Authorization Service Unavailable**
- **Trigger**: Cluster has no healthy endpoints or connection fails
- **Behavior**:
  - If `failure_mode_allow=true`: Request passes through (fail-open)
    - Header `x-envoy-auth-failure-mode-allowed: true` added (if `failure_mode_allow_header_add=true`)
    - Metric: `ext_authz.failure_mode_allowed` counter incremented
  - If `failure_mode_allow=false`: Request denied with configured status code (default 403)
    - Metric: `ext_authz.error` counter incremented
    - Response code details: `ext_authz_error`

#### **Authorization Service Timeout**
- **Trigger**: No response within configured timeout (default 200ms, configurable per service)
- **Behavior**: Same as service unavailable
  - gRPC: Deadline exceeded error
  - HTTP: Request timeout
- **Example**: Auth service backlogged or network latency

#### **Authorization Service Returns Denied**
- **Trigger**: Auth service explicitly denies with non-OK gRPC status or HTTP error status
- **Behavior**:
  - HTTP filter: Returns 403 Forbidden (or custom status if provided in response)
  - Network filter: Closes connection
  - Metric: `ext_authz.denied` counter incremented
  - Response code details: `ext_authz_denied`
  - Optional body from auth service included in response

#### **Invalid CheckResponse/Response Headers**
- **Trigger**: Auth service returns malformed response or invalid header mutations
- **Behavior**:
  - If `validate_mutations=true`:
    - Invalid header names/values detected
    - Request rejected with 500 Internal Server Error
    - Metric: `ext_authz.invalid` counter incremented
    - Response code details: `ext_authz_invalid`
  - If `validate_mutations=false`: Mutations applied as-is (potential for request/response corruption)

#### **Request Body Buffering Full**
- **Trigger**: Request body exceeds `max_request_bytes` configured in `with_request_body`
- **Behavior**:
  - If `allow_partial_message=true`: Partial body sent to auth service
    - Header `x-envoy-auth-partial-body: true` added to CheckRequest
  - If `allow_partial_message=false`: Request rejected or truncated
- **Example**: Large file upload with small max_request_bytes limit

#### **Filter Disabled**
- **Trigger**: `filter_enabled` runtime flag set to false or `deny_at_disable=true`
- **Behavior**:
  - If disabled with `deny_at_disable=false`: Request bypasses auth (continue)
    - Metric: `ext_authz.disabled` counter incremented
  - If disabled with `deny_at_disable=true`: Request denied
- **Use case**: Gradual rollout or emergency disable

#### **Header Mutation Errors**
- **Trigger**: Auth service returns headers that violate mutation rules
- **Behavior**:
  - Pseudo-headers (`:authority`, `:path`, etc.) cannot be modified
  - Certain headers may be protected by `decoder_header_mutation_rules`
  - If validation enabled: Response rejected
  - Metric: `ext_authz.filter_state_name_collision` if filter state name conflicts

#### **Response Header Conflicts**
- **Trigger**: Auth service response headers conflict with existing headers
- **Behavior**: Depends on header mutation type
  - `headers_to_add`: Appends header (multiple values allowed)
  - `headers_to_set`: Overwrites existing header
  - `headers_to_add_if_absent`: Only adds if not already present
  - `headers_to_overwrite_if_exists`: Only overwrites if already present

### Error Handling Strategies

#### **Fail-Open Pattern** (failure_mode_allow=true)
- Best for authorization as an enhancement (not critical path)
- Allows service to degrade gracefully
- Risk: Requests bypass authorization if service is down
- Mitigated by: Monitoring `ext_authz.failure_mode_allowed` metric

#### **Fail-Closed Pattern** (failure_mode_allow=false)
- Best for critical authorization decisions
- Requires auth service availability
- Risk: Service outage causes all requests to be denied (DoS impact)
- Mitigated by: High availability setup for auth service, proper SLOs

#### **Custom Error Responses**
- `status_on_error`: Configure HTTP status returned on auth failure (default 403)
- Can be set to 500, 401, or other codes depending on failure semantics
- Affects how clients interpret authorization failures

---

## 5. Testing

### Test Locations

#### **Unit Tests**
- **HTTP Filter Tests**: `test/extensions/filters/http/ext_authz/ext_authz_test.cc` (~173KB)
  - Tests for HTTP filter behavior, header mutations, request buffering
  - Per-route configuration testing
  - Failure mode testing (timeout, error, denied)
  - Statistics and metadata validation

- **gRPC Client Tests**: `test/extensions/filters/common/ext_authz/ext_authz_grpc_impl_test.cc`
  - gRPC protocol handling, response parsing
  - Timeout and failure handling

- **HTTP Client Tests**: `test/extensions/filters/common/ext_authz/ext_authz_http_impl_test.cc`
  - Raw HTTP protocol handling, response parsing
  - Header matching and filtering

- **Config Tests**: `test/extensions/filters/http/ext_authz/config_test.cc`
  - Configuration parsing and validation

#### **Integration Tests**
- **HTTP Integration**: `test/extensions/filters/http/ext_authz/ext_authz_integration_test.cc` (~77KB)
  - End-to-end testing with real gRPC/HTTP auth services
  - Request/response mutation validation
  - Timeout and failure scenarios
  - Parameterized tests for gRPC/HTTP, IPv4/IPv6, raw headers
  - Statistics and dynamic metadata emission

#### **Fuzz Tests**
- **gRPC Fuzz**: `test/extensions/filters/http/ext_authz/ext_authz_grpc_fuzz_test.cc`
  - Fuzzing with random CheckRequest/CheckResponse data

- **HTTP Fuzz**: `test/extensions/filters/http/ext_authz/ext_authz_http_fuzz_test.cc`
  - Fuzzing with random HTTP request/response data

- **Network Fuzz**: `test/extensions/filters/network/ext_authz/ext_authz_fuzz_test.cc`
  - TCP-level fuzzing

### How to Run Tests

```bash
# Run HTTP filter unit tests
bazel test //test/extensions/filters/http/ext_authz:ext_authz_test

# Run integration tests
bazel test //test/extensions/filters/http/ext_authz:ext_authz_integration_test

# Run all ext_authz tests
bazel test //test/extensions/filters/http/ext_authz/...

# Run with verbose output
bazel test //test/extensions/filters/http/ext_authz:ext_authz_test --test_arg=--v=2
```

### Test Coverage Focus Areas

1. **Happy Path**: Request → Auth Service → OK → Continue
2. **Denied Path**: Request → Auth Service → Denied → 403 Response
3. **Error Path**: Request → Auth Service → Error/Timeout → Fail-open or Fail-closed
4. **Header Mutations**: Verify headers/query params modified correctly
5. **Request Buffering**: Test max_request_bytes, partial message handling
6. **Per-Route Config**: Test route-specific overrides and disabling
7. **Statistics**: Verify all counters incremented correctly
8. **Dynamic Metadata**: Test metadata emission from auth response
9. **Tracing**: Verify span creation and tags set correctly

---

## 6. Debugging

### Observability Tools

#### **Metrics/Statistics**
Key counters to monitor (namespace: `ext_authz.*`):

```
ext_authz.ok                    # Successful authorizations
ext_authz.denied                # Denied by auth service
ext_authz.error                 # Auth service errors/timeouts
ext_authz.failure_mode_allowed  # Errors but allowed via fail-open
ext_authz.disabled              # Bypassed due to filter being disabled
ext_authz.invalid               # Invalid response from auth service
```

View metrics via admin endpoint:
```bash
curl http://envoy-admin:9901/stats/prometheus | grep ext_authz
```

#### **Logging**
Enable debug logging for ext_authz:

```bash
# Set log level in bootstrap config
admin:
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 9901

# Or via admin API
curl -X POST http://envoy-admin:9901/logging?ext_authz=trace
```

Log output includes:
- CheckRequest contents (trace level): `ENVOY_LOG(trace, "Sending CheckRequest: {}", request.DebugString())`
- CheckResponse contents (trace level): `ENVOY_LOG(trace, "Received CheckResponse: {}", response->DebugString())`
- Filter state changes
- Authorization decisions (debug level)

#### **Tracing**
The ext_authz filter creates a child span in the request's distributed trace:

```
Parent Span (request)
└── ext_authz Span
    ├── Tag: ext_authz_status = "ext_authz_ok" | "ext_authz_unauthorized"
    ├── Tag: ext_authz_http_status = "<http_status_code>"
    └── Duration = auth service latency
```

Enable in config:
```yaml
tracing:
  provider:
    name: envoy.tracers.zipkin  # or jaeger, etc.
```

#### **Filter State & Dynamic Metadata**
Auth service can emit dynamic metadata that downstream filters access:

```c++
// In downstream filter:
const auto* ext_authz_info = stream_info.filterState().getDataReadOnly<
    Extensions::HttpFilters::ExtAuthz::ExtAuthzLoggingInfo>(
    "ext_authz_logging_info");
if (ext_authz_info) {
  auto latency = ext_authz_info->latency();  // microseconds
  auto metadata = ext_authz_info->filterMetadata();
}
```

### Common Debugging Scenarios

#### **"All requests being denied" (when they shouldn't be)**

1. **Check auth service connectivity**:
   ```bash
   curl -v http://<auth-service>:<port>/check
   # Should return 200/403/etc, not timeout/connection refused
   ```

2. **Verify filter configuration**:
   ```bash
   curl http://envoy-admin:9901/config_dump | grep -A 50 "ext_authz"
   ```
   - Ensure `grpc_service` or `http_service` is configured
   - Check `failure_mode_allow` setting

3. **Monitor statistics**:
   ```bash
   curl http://envoy-admin:9901/stats | grep "ext_authz" | head -20
   ```
   - If `ext_authz.denied` is high, auth service is explicitly denying
   - If `ext_authz.error` is high, check auth service logs

4. **Enable debug logging**:
   ```bash
   curl -X POST http://envoy-admin:9901/logging?ext_authz=debug
   ```
   - Look for "ext_authz denied" or error messages

5. **Check auth service logs**:
   - Verify it's receiving CheckRequests
   - Check for processing errors
   - Confirm policy rules are correct

#### **"Requests timeout at authorization service"**

1. **Increase timeout if auth is slow**:
   ```yaml
   grpc_service:
     envoy_grpc:
       cluster_name: ext_authz
     timeout: 1s  # Increase from default 200ms
   ```

2. **Check auth service health**:
   ```bash
   curl http://envoy-admin:9901/stats | grep "cluster.*ext_authz" | grep -i "health\|active"
   ```

3. **Monitor latency**:
   - Check `ext_authz_duration` dynamic metadata field
   - Look at trace spans for auth service latency
   - Monitor auth service backend metrics

4. **Check for slow queries**:
   - Enable auth service debug logging
   - Profile policy evaluation time
   - Check database query performance if applicable

#### **"Authorization service down, requests failing"**

1. **Enable fail-open**:
   ```yaml
   failure_mode_allow: true
   failure_mode_allow_header_add: true  # Mark bypassed requests
   ```
   - Allows service to keep operating
   - Add alert on `ext_authz.failure_mode_allowed` metric

2. **Increase auth service availability**:
   - Configure multiple endpoints in cluster
   - Set up failover/redundancy
   - Use health checks to detect failures quickly

3. **Implement circuit breaker**:
   ```yaml
   circuit_breakers:
     thresholds:
     - priority: HIGH
       max_connections: 100
       max_pending_requests: 100
       max_requests: 1000
   ```
   - Prevents cascading failures

#### **"Headers/query params not being modified correctly"**

1. **Verify auth service response format**:
   - gRPC: Check OkHttpResponse.headers, headers_to_remove, query_parameters
   - HTTP: Check response headers match allowed patterns

2. **Check header matchers configuration**:
   ```yaml
   http_service:
     authorization_response:
       allowed_upstream_headers:
         patterns:
         - prefix: "x-"  # Only forward headers starting with x-
   ```

3. **Enable mutation validation**:
   ```yaml
   validate_mutations: true  # Catch invalid header mutations
   ```

4. **Check for pseudo-header violations**:
   - `:authority`, `:path`, `:method`, `:scheme` cannot be modified
   - If auth service tries to modify these, they'll be rejected

#### **"Authorization not happening for certain requests"**

1. **Check if routes are disabled**:
   ```yaml
   typed_per_filter_config:
     envoy.filters.http.ext_authz:
       disabled: true
   ```
   - Verify per-route config isn't accidentally disabling filter

2. **Check filter_enabled runtime flag**:
   ```bash
   curl -X POST http://envoy-admin:9901/logging?runtime=debug
   ```
   - Check if `filter_enabled` runtime key is set to false

3. **Verify filter placement**:
   - ext_authz should be first in filter chain
   - Check filter ordering in config

4. **Check connection/stream state**:
   - Some requests may be completed before auth filter runs
   - Verify request is making it to ext_authz decode phase

### Health Check Configuration

For gRPC auth service:
```yaml
clusters:
- name: ext_authz
  type: static
  health_checks:
  - timeout: 1s
    interval: 10s
    grpc_health_check:
      service_name: envoy.service.auth.v3.Authorization
  load_assignment:
    cluster_name: ext_authz
    endpoints:
    - lb_endpoints:
      - endpoint:
          address:
            socket_address:
              address: 127.0.0.1
              port_value: 9000
```

### Key Files to Review When Debugging

1. **Auth service integration**: Check `ext_authz_grpc_impl.cc:onFailure()` and `ext_authz_http_impl.cc:onFailure()`
2. **Request creation**: Check `check_request_utils.cc` for what data is sent
3. **Response handling**: Check `ext_authz.cc:onComplete()` for how responses are processed
4. **Filter state**: Check `ext_authz.h:ExtAuthzLoggingInfo` for what's stored for logging

### Relevant Admin Endpoints

```bash
# View current config
curl http://envoy-admin:9901/config_dump

# View statistics
curl http://envoy-admin:9901/stats | grep ext_authz

# Change log level
curl -X POST http://envoy-admin:9901/logging?ext_authz=debug

# View cluster health
curl http://envoy-admin:9901/clusters | grep -A 10 ext_authz
```

---

## Key Takeaways for Maintainers

1. **Two Implementations**: HTTP and network variants using same client interface
2. **Two Protocols**: gRPC (structured) and HTTP (raw headers) for auth services
3. **Async Design**: Non-blocking client calls with callback-based completion
4. **Flexible Configuration**: Per-route overrides, runtime control, multiple failure modes
5. **Observable**: Rich metrics, tracing support, dynamic metadata, logging
6. **Error Handling**: Carefully distinguish between service errors and authorization denials
7. **Testing**: Comprehensive unit/integration/fuzz test coverage
8. **Production Ready**: Mature feature with real-world deployments and good observability

---

## Useful References

- Architecture: `docs/root/intro/arch_overview/security/ext_authz_filter.rst`
- HTTP Filter Config: `docs/root/configuration/http/http_filters/ext_authz_filter.rst`
- Network Filter Config: `docs/root/configuration/listeners/network_filters/ext_authz_filter.rst`
- API Protos: `api/envoy/extensions/filters/http/ext_authz/v3/ext_authz.proto`
- Service Proto: `envoy/service/auth/v3/external_auth.proto`
