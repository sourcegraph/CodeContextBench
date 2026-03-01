# ext_authz Filter Handoff Document

## 1. Purpose

The `ext_authz` (external authorization) filter is one of Envoy's core security components that delegates authorization decisions to an external service. It intercepts inbound requests or connections and sends them to an external authorization service before allowing them to proceed to the upstream server.

### Use Cases
- **Authentication/Authorization**: Verify user credentials and permissions before allowing requests
- **Policy Enforcement**: Check compliance policies, rate limits, or service-level agreements
- **Multi-tenant Authorization**: Enforce tenant-level access control
- **Centralized Authorization**: Maintain a single source of truth for authorization logic across multiple Envoy instances

### Supported Protocols
- **gRPC Authorization Service**: Uses Envoy's gRPC async client to communicate with a gRPC authorization server (recommended for performance)
- **HTTP Authorization Service**: Uses HTTP for authorization, useful for simpler deployments or legacy systems

### Request Flow
1. HTTP/network request arrives at Envoy
2. ext_authz filter intercepts the request
3. Filter builds a `CheckRequest` containing request attributes (headers, method, path, peer info, etc.)
4. Filter sends request to external authorization service
5. Based on response:
   - **OK**: Request continues to next filter and upstream
   - **Denied**: Local response sent to client with configured status code
   - **Error**: Either deny (fail-closed) or allow (fail-open) based on `failure_mode_allow` configuration

---

## 2. Dependencies

### Upstream Dependencies

**Core Envoy Components:**
- **Async Client Framework** (`envoy/grpc/async_client.h`, `envoy/http/async_client.h`)
  - gRPC async client for communicating with authorization services
  - HTTP async client for HTTP-based authorization services

- **Cluster Manager** (`envoy/upstream/cluster_manager.h`)
  - Manages upstream clusters for authorization service connections
  - Handles load balancing and failover to authorization service endpoints

- **HTTP Filter Interface** (`envoy/http/filter.h`)
  - Provides the base interface for HTTP stream filters
  - Filter lifecycle hooks: `decodeHeaders`, `decodeData`, `decodeTrailers`, `encode*`

- **Network Filter Interface** (`envoy/network/filter.h`)
  - Provides the base interface for network (L4) filters
  - Filter lifecycle hooks: `onNewConnection`, `onData`

- **Router** (`source/common/router/`)
  - Per-route configuration support via `FilterConfigPerRoute`
  - Route-specific authorization settings

- **gRPC Descriptor Pool** (`envoy/service/auth/v3/external_auth.pb.h`)
  - Protobuf definitions for gRPC authorization service
  - Defines `CheckRequest` and `CheckResponse` messages

- **Tracing** (`envoy/tracing/tracer.h`)
  - Trace span creation for observability of authorization calls

- **Stats** (`envoy/stats/stats_macros.h`)
  - Counters and gauges for monitoring filter behavior

**Key External Service Protocol:**
- **Envoy AuthZ Service** (`envoy/service/auth/v3/external_auth.proto`)
  - Defines the contract for external authorization services
  - `CheckRequest`: Attributes from the request being authorized
  - `CheckResponse`: Authorization decision and optional mutations

### Downstream Consumers

**HTTP Filter Chain:**
- `source/extensions/filters/http/ext_authz/ext_authz.h` implements `Http::StreamFilter`
- Integrated into HTTP filter chain by factory: `ExtAuthzFilterConfig`
- Can be configured per-route via `ExtAuthzPerRoute`
- Interacts with downstream HTTP clients sending authorization requests

**Network Filter Chain:**
- `source/extensions/filters/network/ext_authz/ext_authz.h` implements `Network::ReadFilter`
- Integrated into L4 network filter chain
- Intercepts TCP connections before protocol detection

**Other Filters:**
- Upstream filters can use dynamic metadata set by ext_authz for downstream decisions
- ext_authz can mutate request headers/body before passing to next filter

---

## 3. Relevant Components

### HTTP Filter Implementation

**File: `source/extensions/filters/http/ext_authz/ext_authz.h`**
- **Role**: Primary HTTP filter interface and state machine
- **Key Classes**:
  - `Filter`: Implements `Http::StreamFilter` and `RequestCallbacks`
    - State management: `State::NotStarted`, `State::Calling`, `State::Complete`
    - Filter decision logic: `FilterReturn::ContinueDecoding`, `FilterReturn::StopDecoding`
    - Header/data handling for request buffering
  - `FilterConfig`: Configuration parsing and initialization
    - Parses `ExtAuthz` protobuf configuration
    - Manages stats, runtime features, and feature flags
    - Per-route config merging support
  - `FilterConfigPerRoute`: Per-route authorization settings
    - Context extensions for auth request
    - Disable/enable per-route
    - Check settings override (body buffering, etc.)
- **Key Methods**:
  - `decodeHeaders()`: Entry point for HTTP requests
  - `initiateCall()`: Initiates authorization check
  - `onComplete()`: Callback when authorization check completes
  - `onData()`, `decodeTrailers()`: Request body buffering

**File: `source/extensions/filters/http/ext_authz/ext_authz.cc`**
- **Role**: Implementation of HTTP filter logic
- **Key Functions**:
  - `FilterConfig::FilterConfig()`: Parse configuration, initialize matcher patterns, setup stats
  - `Filter::decodeHeaders()`: Check if disabled at runtime, handle buffering, initiate auth call
  - `Filter::initiateCall()`: Build CheckRequest, create filter state logging info, call client
  - `Filter::onComplete()`: Handle auth response (OK/Denied/Error), apply mutations, send local reply if denied
  - `Filter::continueDecoding()`: Resume filter chain after async completion
  - `Filter::getPerRouteFlags()`: Resolve per-route configuration from route config

**File: `source/extensions/filters/http/ext_authz/config.h` and `config.cc`**
- **Role**: Filter factory and registration
- **Key Classes**:
  - `ExtAuthzFilterConfig`: Factory for creating filter instances
    - Creates either gRPC or HTTP client based on config
    - Default timeout: 200ms
- **Key Functions**:
  - `createFilterFactoryFromProtoWithServerContextTyped()`: Creates filter factory callback
  - `createRouteSpecificFilterConfigTyped()`: Creates per-route config

### Network Filter Implementation

**File: `source/extensions/filters/network/ext_authz/ext_authz.h`**
- **Role**: TCP/L4 authorization filter
- **Key Classes**:
  - `Filter`: Implements `Network::ReadFilter` and `ConnectionCallbacks`
    - State: `Status::NotStarted`, `Status::Calling`, `Status::Complete`
    - Return: `FilterReturn::Stop`, `FilterReturn::Continue`
  - `Config`: Network filter configuration
- **Design Notes**:
  - Performs check on new connection (no connection data)
  - Buffers data until authorization completes
  - Closes connection on denial or error

### Common Authorization Library

**File: `source/extensions/filters/common/ext_authz/ext_authz.h`**
- **Role**: Abstract interface for authorization clients
- **Key Classes**:
  - `Client`: Abstract interface for authorization clients
    - Methods: `check()`, `cancel()`, `streamInfo()`
  - `RequestCallbacks`: Callback interface for check completion
    - Method: `onComplete(ResponsePtr&& response)`
  - `Response`: Authorization response structure
    - Status: `OK`, `Denied`, `Error`
    - Header mutations: `headers_to_append`, `headers_to_set`, `headers_to_add`, `headers_to_remove`
    - Response headers: `response_headers_to_add`, `response_headers_to_set`, etc.
    - Query parameters: `query_parameters_to_set`, `query_parameters_to_remove`
    - Denied response: `body`, `status_code`
    - Dynamic metadata for downstream filters

**File: `source/extensions/filters/common/ext_authz/ext_authz_grpc_impl.h` and `.cc`**
- **Role**: gRPC client implementation
- **Key Classes**:
  - `GrpcClientImpl`: Implements gRPC-based authorization
    - Uses Envoy's typed async gRPC client
    - Handles response parsing from protobuf
    - Supports request cancellation
- **Key Methods**:
  - `check()`: Send CheckRequest to authorization service via gRPC
  - `onSuccess()`: Handle successful authorization response
  - `onFailure()`: Handle gRPC errors (UNAVAILABLE, UNKNOWN, etc.)
- **Important Details**:
  - One client created per filter stack (not per thread)
  - Timeout configurable (default 200ms)
  - Uses service method: `envoy.service.auth.v3.Authorization.Check`

**File: `source/extensions/filters/common/ext_authz/ext_authz_http_impl.h` and `.cc`**
- **Role**: HTTP client implementation
- **Key Classes**:
  - `RawHttpClientImpl`: HTTP-based authorization
    - Uses Envoy's async HTTP client
    - Transforms HTTP response into common Response format
  - `ClientConfig`: HTTP client configuration
    - Cluster name for authorization service
    - Path prefix for authorization endpoint
    - Header matchers for selecting which headers to include in response
- **Key Methods**:
  - `check()`: Send CheckRequest as HTTP request to authorization service
  - `onSuccess()`: Parse HTTP response and convert to Response
  - `onFailure()`: Handle HTTP client failures
- **Supported Features**:
  - Path prefix override per route
  - Header selection matchers (which headers to include)
  - Raw header encoding (bytes vs. string)

**File: `source/extensions/filters/common/ext_authz/check_request_utils.h` and `.cc`**
- **Role**: Build CheckRequest protobuf from HTTP/network context
- **Key Functions**:
  - `createHttpCheck()`: Extract HTTP request attributes and build CheckRequest
    - Headers (with allow/disallow list matching)
    - Request body (optional, with max size limit)
    - Peer information (address, certificate, TLS session)
    - Stream information (request ID, timestamp)
    - Dynamic metadata and route metadata
  - `createTcpCheck()`: Extract network connection attributes
    - Local and remote peer information
    - TLS certificate and session info
- **Matcher System**:
  - `HeaderKeyMatcher`: Match headers against list of matchers
  - `NotHeaderKeyMatcher`: Inverse matcher for disallowing headers
  - Used for fine-grained control over which request headers are sent to auth service

---

## 4. Failure Modes

### Authorization Service Failures

#### Scenario 1: Service Unavailable (Connection Error)
- **Cause**: Authorization service is down, unreachable, or network connectivity lost
- **CheckStatus**: `Error`
- **Handling**:
  - If `failure_mode_allow = true`: Allow request through with `failure_mode_allowed` stat incremented
    - If `failure_mode_allow_header_add = true`: Add header `x-envoy-auth-failure-mode-allowed: true`
  - If `failure_mode_allow = false`: Deny request with status code from `status_on_error` (default: 403 Forbidden)
- **Observability**: `ext_authz.error` counter incremented

#### Scenario 2: gRPC Service Returns Error
- **Cause**: gRPC status code (e.g., `UNAVAILABLE`, `UNKNOWN`, `INTERNAL`)
- **CheckStatus**: `Error`
- **Handling**: Same as Scenario 1

#### Scenario 3: Authorization Decision is Denied
- **Cause**: Authorization service returns `CheckResponse` with `denied_response`
- **CheckStatus**: `Denied`
- **Handling**:
  - Local response sent to client with:
    - Status code from `denied_response.status`
    - Body from `denied_response.body`
    - Headers from `denied_response.headers`
  - Response flag set: `UnauthorizedExternalService`
  - Response code details: `ext_authz_denied`
- **Observability**: `ext_authz.denied` counter incremented

#### Scenario 4: Request Body Buffer Overflow
- **Cause**: Request body exceeds `max_request_bytes` configured in `with_request_body`
- **Handling**:
  - If `allow_partial_message = true`: Initiate auth check with partial body
  - If `allow_partial_message = false`: Send HTTP 413 Payload Too Large, don't initiate auth
- **Observability**: Logged at debug level

#### Scenario 5: Invalid Authorization Response
- **Cause**: Authorization service returns headers/query parameters that fail validation
- **CheckStatus**: `OK` (accepted) but validation fails
- **Handling** (if `validate_mutations = true`):
  - Check header names and values for validity using `Http::HeaderUtility`
  - If invalid: Send local response with status 500 Internal Server Error
  - Response code details: `ext_authz_invalid`
- **Observability**: `ext_authz.invalid` counter incremented

#### Scenario 6: Filter Disabled at Runtime
- **Cause**: `filter_enabled` runtime feature flag disabled
- **Handling**:
  - If `deny_at_disable = true`: Send local response with `status_on_error`
  - If `deny_at_disable = false`: Allow request through without auth check
- **Observability**: `ext_authz.disabled` counter incremented

### Timeout Handling
- **Timeout**: Configured per client (default 200ms)
- **Behavior**: If timeout expires, treated as gRPC `DEADLINE_EXCEEDED` → handled as `Error`

### Request Cancellation
- **When**: If downstream client disconnects or request is cancelled
- **Mechanism**: `client_->cancel()` called to cancel inflight check request
- **State**: Filter transitions to `State::Complete` without processing response

### Network Filter Specific
- **Connection Closure**: If connection closed during check, filter cleans up state
- **Buffering**: Network filter buffers data until authorization completes
- **Default**: Fails closed (denies connection) on error unless `failure_mode_allow = true`

---

## 5. Testing

### Test Files Location

**HTTP Filter Tests:**
- `test/extensions/filters/http/ext_authz/ext_authz_test.cc` - Main unit tests
  - Tests: authorization OK, denied, errors, failure modes, buffering, per-route config
  - Uses mock client: `MockClient` for simulating auth service responses
  - ~3000+ lines covering comprehensive scenarios

- `test/extensions/filters/http/ext_authz/ext_authz_integration_test.cc` - End-to-end tests
  - Full Envoy instance with real HTTP server and fake auth service
  - Tests: gRPC auth, HTTP auth, various config scenarios, timeout behavior
  - Multiple test classes for different configurations

- `test/extensions/filters/http/ext_authz/config_test.cc` - Configuration tests
  - Proto config parsing validation
  - Invalid configuration detection

- `test/extensions/filters/http/ext_authz/ext_authz_*_fuzz_test.cc` - Fuzzing
  - `ext_authz_grpc_fuzz_test.cc`: Fuzzing gRPC client path
  - `ext_authz_http_fuzz_test.cc`: Fuzzing HTTP client path

**Network Filter Tests:**
- `test/extensions/filters/network/ext_authz/ext_authz_test.cc` - Network filter unit tests
  - TCP connection authorization scenarios

- `test/extensions/filters/network/ext_authz/ext_authz_fuzz_test.cc` - Network fuzzing

**Common Library Tests:**
- `test/extensions/filters/common/ext_authz/ext_authz_grpc_impl_test.cc` - gRPC client tests
  - Mock gRPC service responses
  - Error handling

- `test/extensions/filters/common/ext_authz/ext_authz_http_impl_test.cc` - HTTP client tests
  - Mock HTTP server responses
  - Response conversion

- `test/extensions/filters/common/ext_authz/check_request_utils_test.cc` - Request building tests
  - CheckRequest construction from various input scenarios

### Test Patterns

**Unit Test Setup:**
```cpp
template <class T> class HttpFilterTestBase : public T {
  void initialize(const ExtAuthz& proto_config);
  // Creates FilterConfig, mocks client, sets up callbacks
};
```

**Mock Client Usage:**
```cpp
client_ = new NiceMock<Filters::Common::ExtAuthz::MockClient>();
// Override expectations:
EXPECT_CALL(*client_, check(_, _, _, _))
  .WillOnce(WithArg<0>(Invoke([](auto& callback) {
    // Simulate response
    auto response = std::make_unique<Response>();
    callback.onComplete(std::move(response));
  })));
```

**Test Scenarios:**
- Authorization allowed (OK response)
- Authorization denied (Denied response)
- Error scenarios (network failure, timeout, gRPC errors)
- Failure mode allow
- Request body buffering
- Header mutations and validation
- Per-route configuration
- Disabled filter behavior
- Dynamic metadata handling
- Logging and observability

### Running Tests

**HTTP Filter:**
```bash
bazel test //test/extensions/filters/http/ext_authz:ext_authz_test
bazel test //test/extensions/filters/http/ext_authz:ext_authz_integration_test
```

**Network Filter:**
```bash
bazel test //test/extensions/filters/network/ext_authz:ext_authz_test
```

**Common Library:**
```bash
bazel test //test/extensions/filters/common/ext_authz:ext_authz_grpc_impl_test
bazel test //test/extensions/filters/common/ext_authz:ext_authz_http_impl_test
```

---

## 6. Debugging

### Observability Mechanisms

#### 1. Metrics (Counters and Gauges)

**HTTP Filter Stats:**
- `ext_authz.ok` - Authorization allowed
- `ext_authz.denied` - Authorization denied
- `ext_authz.error` - Authorization service error
- `ext_authz.invalid` - Invalid auth response (validation failure)
- `ext_authz.disabled` - Request bypassed (filter disabled)
- `ext_authz.failure_mode_allowed` - Error allowed through (failure mode)
- `ext_authz.ignored_dynamic_metadata` - Dynamic metadata dropped
- `ext_authz.filter_state_name_collision` - Filter state name conflict

Also emitted to cluster stats if `charge_cluster_response_stats = true`.

**Network Filter Stats:**
- `ext_authz.ok`, `ext_authz.denied`, `ext_authz.error`
- `ext_authz.failure_mode_allowed`
- `ext_authz.disabled`
- `ext_authz.active` - Active authorization checks (gauge)
- `ext_authz.cx_closed` - Connections closed due to auth

**Admin Interface:**
```
curl localhost:9901/stats | grep ext_authz
```

#### 2. Logs

**Filter Logging:**
- Component ID: `ext_authz` (for filter logs)
- Log level: Controlled by `--log-level` flag
- Default log level: varies by logger

**Key Log Messages:**

| Scenario | Log Level | Message |
|----------|-----------|---------|
| Filter calling auth service | `trace` | "ext_authz filter calling authorization server" |
| Request allowed | `trace` | "ext_authz filter allowed the request" |
| Request denied | `trace` | "ext_authz filter rejected the request" |
| Error with failure mode | `trace` | "ext_authz filter allowed the request with error" |
| Filter disabled, deny | `trace` | "ext_authz filter is disabled. Deny the request." |
| Buffering request | `debug` | "ext_authz filter is buffering the request" |
| Buffer finished | `debug` | "ext_authz filter finished buffering the request since {reason}" |
| Invalid header rejected | `trace` | "Rejected invalid header '{}':'{}'" |
| Filter state collision | `debug` | "Could not find logging info at {} !" |

**Example: Enable debug logging**
```
admin.log_level: "debug"  # In configuration
```

#### 3. Tracing

**Span Creation:**
- Parent span: Stream's active span (passed from filter chain)
- Child span: Created for gRPC call to authorization service

**Span Attributes (Tracing Constants):**
- `ext_authz_status` - Authorization status (allowed/denied/error)
- `ext_authz_unauthorized` - Custom label for denied responses
- `ext_authz_ok` - Custom label for allowed responses
- `ext_authz_http_status` - HTTP status code

**Enable Tracing:**
```yaml
tracing:
  provider:
    name: "envoy.tracers.zipkin"  # or other tracer
```

#### 4. Filter State / Logging Info

**Dynamic Metadata:**
- Key: `decoder_callbacks_->filterConfigName()` (typically "ext_authz_filter")
- Type: `ExtAuthzLoggingInfo`
- Contains:
  - Filter metadata from config
  - Latency (for gRPC)
  - Bytes sent/received (for gRPC)
  - Cluster info and upstream host info

**Retrieve in Custom Filters:**
```cpp
auto logging_info = filter_state->getDataReadOnly<ExtAuthzLoggingInfo>(name);
auto latency = logging_info->latency();
```

### Debugging Production Issues

#### Issue 1: Authorization Requests Timing Out
**Diagnosis:**
1. Check `ext_authz.error` metric spike
2. Look for trace logs: "ext_authz filter allowed the request with error"
3. Check authorization service metrics (response time, availability)
4. Verify network connectivity to auth service

**Investigation:**
```bash
# Check current timeout
curl localhost:9001/config_dump | grep -A5 "ext_authz" | grep "timeout"

# Increase timeout in config
grpc_service:
  timeout: 1s  # Default is 200ms
```

#### Issue 2: Requests Being Denied
**Diagnosis:**
1. Check `ext_authz.denied` counter
2. Look for trace logs: "ext_authz filter rejected the request"
3. Check denied response body and headers

**Investigation:**
- Review authorization service logs
- Verify request headers being sent: check `CheckRequest` in trace
- Check if context extensions are correct
- Verify allowed/disallowed headers configuration

#### Issue 3: Failure Mode Allowing Too Much Traffic
**Diagnosis:**
1. High `ext_authz.failure_mode_allowed` counter
2. Indicates auth service is frequently unavailable or slow

**Investigation:**
```bash
# Check auth service cluster health
curl localhost:9001/clusters | grep auth

# Monitor specific error types in gRPC call logs
TRACE level logs for "onFailure" messages
```

#### Issue 4: Invalid Response Rejection (500 errors)
**Diagnosis:**
1. Check `ext_authz.invalid` counter increasing
2. Look for: "Rejected invalid header"
3. Users get HTTP 500 errors

**Solution:**
- Fix authorization service to return valid headers
- Disable validation: `validate_mutations: false` (if acceptable)
- Check header naming conventions (lowercase, RFC 7230 compliant)

#### Issue 5: Filter State Collision
**Diagnosis:**
1. Check `ext_authz.filter_state_name_collision` counter
2. Debug log: "Could not find logging info at ..."

**Cause:**
- Another filter is using the same filter state name
- Solution: Use unique filter name in config, or resolve name conflict with other filters

### Performance Debugging

#### Latency Analysis
1. **gRPC client latency** (from `ExtAuthzLoggingInfo`):
   - `logging_info->latency()` - time from request to response
   - Check against configured timeout

2. **Request buffering overhead**:
   - If `with_request_body` configured, buffer size impacts latency
   - Monitor decoding buffer size

3. **Authorization service performance**:
   - Monitor authorization service response time
   - Check for downstream service issues (if auth service calls other systems)

#### Resource Usage
- **Memory**: Depends on request body buffering (`max_request_bytes`)
- **Threads**: Uses event dispatcher's thread (non-blocking)
- **Connections**: One async request per check

### Common Configuration Issues

**Issue: Auth service cluster not found**
```
Error: "ext_authz cluster not registered"
Solution: Ensure cluster name matches in config and cluster config
```

**Issue: Timeout always occurring**
```
Configuration mismatch between filter timeout and actual service latency
Solution: Increase timeout or optimize auth service
```

**Issue: Headers not being forwarded**
```
Allowed/disallowed header matchers blocking expected headers
Solution: Review header matcher configuration, adjust allow/disallow lists
```

### Log Location Examples

**Envoy Admin Interface:**
```
GET /logging: View current log level
GET /logging?level=trace: Set to trace level
```

**File-based Logging:**
```bash
tail -f /var/log/envoy/access.log
tail -f /var/log/envoy/error.log
```

**Kubernetes:**
```bash
kubectl logs <pod-name> -c envoy -f
kubectl logs <pod-name> -c envoy | grep ext_authz
```

---

## Summary

The ext_authz filter is a critical security component that:
- **Delegates authorization** to external services (gRPC or HTTP)
- **Supports multiple failure modes** (fail-open, fail-closed, deny-on-disable)
- **Provides rich observability** through stats, logs, and tracing
- **Integrates deeply** with Envoy's routing and request processing pipeline
- **Handles complex scenarios** like request buffering, header mutations, and dynamic metadata

Key files to master:
1. `source/extensions/filters/http/ext_authz/ext_authz.h` - HTTP filter interface
2. `source/extensions/filters/http/ext_authz/ext_authz.cc` - HTTP filter logic
3. `source/extensions/filters/common/ext_authz/ext_authz.h` - Abstract interface
4. `source/extensions/filters/common/ext_authz/ext_authz_grpc_impl.cc` - gRPC client
5. `test/extensions/filters/http/ext_authz/ext_authz_test.cc` - Comprehensive tests

For issues: Monitor ext_authz.* metrics, enable trace logging, and verify authorization service connectivity and response times.
