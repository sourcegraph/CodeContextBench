# ext_authz Filter Handoff Document

## 1. Purpose

The **ext_authz filter** is Envoy's external authorization extension that delegates authorization decisions to an external service. It intercepts incoming HTTP or TCP requests and makes a decision about whether to allow or deny them before further processing.

### What it does:
- **Calls an external authorization service** (either gRPC or HTTP) for each request/connection
- **Blocks or allows traffic** based on the authorization service's response
- **Supports request/response mutation**: The authorization service can add, remove, or modify HTTP headers and query parameters
- **Operates at two levels**:
  - **Network filter**: Operates at the connection level, can deny connections outright
  - **HTTP filter**: Operates at the request level, returns HTTP 403 Forbidden for unauthorized requests
- **Failure handling**: Can be configured to fail-open (permit requests if auth service is unavailable) or fail-closed (deny requests)

### When to use it:
- You need to enforce authorization policies from a centralized service
- You want to delegate authz decisions to a custom authorization engine (e.g., OPA, Opa, custom service)
- You need to enrich requests with information from an authorization service (headers, metadata)
- You require per-route authorization logic with virtual host/route-level customization

### Key Features:
- **Two transport options**: gRPC (preferred for performance) or HTTP
- **Request body buffering**: Can include request body in authorization checks
- **Dynamic metadata**: Authorization service can return metadata for other filters
- **Header/query parameter mutations**: Authorization response can modify upstream requests
- **Response header injection**: Can add headers to responses sent to clients
- **Tracing integration**: Maintains trace context and records authorization check outcomes
- **Per-route configuration**: Can disable filter or customize behavior per route


## 2. Dependencies

### Upstream Dependencies

**External Libraries & Interfaces:**
- `envoy/service/auth/v3/external_auth.proto`: gRPC service definition for authorization checks
  - Defines `CheckRequest` proto sent to the authorization service
  - Defines `CheckResponse` proto received from the authorization service

**Core Envoy Components:**
- **gRPC Async Client** (`envoy/grpc/async_client.h`, `envoy/grpc/async_client_manager.h`): For communicating with gRPC authorization services
- **HTTP Async Client** (`envoy/http/async_client.h`): For communicating with HTTP authorization services
- **Cluster Manager** (`envoy/upstream/cluster_manager.h`): For managing clusters and connections to authorization services
- **Stream Info** (`envoy/stream_info/stream_info.h`): For accessing request metadata (headers, connection info, etc.)
- **Network Connection** (`envoy/network/connection.h`, `envoy/network/filter.h`): For network-level authorization
- **HTTP Filter Base** (`envoy/http/filter.h`): For implementing HTTP-level filtering
- **Stats** (`envoy/stats/stats_macros.h`, `envoy/stats/scope.h`): For emitting metrics
- **Tracing** (`envoy/tracing/tracer.h`): For distributed tracing
- **Router** (`envoy/router/router.h`): For per-route configuration
- **Runtime** (`envoy/runtime/runtime.h`): For feature flags and runtime configuration

**Internal Envoy Helpers:**
- `source/common/http/utility_lib`: HTTP utilities (header validation, query parameter parsing, etc.)
- `source/common/common/matchers_lib`: Pattern matching for header selection
- `source/extensions/filters/common/mutation_rules`: For validating header/query parameter mutations

### Downstream Consumers

**What uses ext_authz:**
1. **Envoy Filter Chain**:
   - HTTP filter chain (via `Http::FilterChain`)
   - Network filter chain (via `Network::FilterChain`)

2. **Filter Configuration**:
   - `envoy::extensions::filters::http::ext_authz::v3::ExtAuthz` proto
   - `envoy::extensions::filters::http::ext_authz::v3::ExtAuthzPerRoute` proto for per-route overrides
   - `envoy::extensions::filters/network::ext_authz::v3::ExtAuthz` proto for network filter variant

3. **Authorization Service**:
   - Receives `CheckRequest` with HTTP/TCP attributes
   - Returns `CheckResponse` with authorization decision and optional mutations

4. **Other Filters**:
   - Downstream filters in the chain receive modified headers/query parameters
   - Can read dynamic metadata emitted by ext_authz


## 3. Relevant Components

### HTTP Filter (Primary Implementation)

- **`source/extensions/filters/http/ext_authz/ext_authz.h`**: Core HTTP filter class definition
  - `Filter` class: Implements `Http::StreamFilter` and `Filters::Common::ExtAuthz::RequestCallbacks`
  - `FilterConfig`: Holds filter configuration parsed from proto
  - `FilterConfigPerRoute`: Per-route configuration overrides
  - `ExtAuthzLoggingInfo`: Filter state object for observability

- **`source/extensions/filters/http/ext_authz/ext_authz.cc`**: HTTP filter implementation (~900 lines)
  - `decodeHeaders()`: Initiates authorization check for incoming requests
  - `decodeData()`: Buffers request body if configured
  - `encodeHeaders()/encodeData()`: Adds response headers if request was authorized
  - `onComplete()`: Callback when authorization check completes (~400 lines, handles all three outcomes: OK/Denied/Error)
  - `initiateCall()`: Sets up the authorization request
  - `continueDecoding()`: Resumes filter chain after auth check
  - **Key state machine**: `State::NotStarted → State::Calling → State::Complete`

- **`source/extensions/filters/http/ext_authz/config.cc` & `config.h`**: Filter factory and configuration
  - Creates filter instances for HTTP filter chain
  - Parses proto configuration and creates appropriate client (gRPC or HTTP)
  - Registers filter as named factory: `"envoy.ext_authz"`

### Network Filter (TCP-level Authorization)

- **`source/extensions/filters/network/ext_authz/ext_authz.h` & `ext_authz.cc`**: Network filter implementation
  - Similar to HTTP filter but operates at connection level
  - Closes connections (vs returning 403) for unauthorized traffic
  - Uses same authorization service and response handling

### Common/Shared Implementation

- **`source/extensions/filters/common/ext_authz/ext_authz.h`**: Base abstractions (~150 lines)
  - `Client` interface: Abstract base for both gRPC and HTTP clients
  - `RequestCallbacks` interface: Callback for async authorization checks
  - `Response` struct: Authorization response with status, headers, body, metadata
  - `CheckStatus` enum: OK, Denied, Error
  - Shared constants for headers, trace tags, response code details

- **`source/extensions/filters/common/ext_authz/ext_authz_grpc_impl.h` & `.cc`**: gRPC authorization client (~160 lines)
  - `GrpcClientImpl` class: Implements `Client` interface using Envoy's gRPC async client
  - `check()`: Sends CheckRequest via gRPC (unary RPC, not bidirectional streaming)
  - `onSuccess()`: Handles successful CheckResponse, extracts headers/body/metadata
  - `onFailure()`: Handles gRPC errors (timeouts, connection failures, etc.)
  - Returns `CheckStatus::Error` on any gRPC failure (timeout, network error, etc.)

- **`source/extensions/filters/common/ext_authz/ext_authz_http_impl.h` & `.cc`**: HTTP authorization client (~450 lines)
  - `RawHttpClientImpl` class: Implements `Client` interface using Envoy's HTTP async client
  - `check()`: Sends CheckRequest as HTTP POST to configured server URI
  - `onSuccess()`: Handles HTTP response, filters headers by configured matchers
  - `onFailure()`: Handles HTTP client errors or response buffer limits
  - `ClientConfig`: Holds HTTP-specific config (cluster name, timeout, path prefix, header matchers)
  - Returns `CheckStatus::Error` for 5xx responses or transport failures
  - Treats 403 as Denied (via response header matchers), 200 as OK

- **`source/extensions/filters/common/ext_authz/check_request_utils.h` & `.cc`**: Request building (~400 lines)
  - `CheckRequestUtils::createHttpCheck()`: Builds CheckRequest from HTTP headers, stream info, metadata
  - `CheckRequestUtils::createTcpCheck()`: Builds CheckRequest from network connection info
  - Extracts: method, path, headers, query params, client IP, peer certificate, TLS session, custom metadata
  - Handles: request body buffering, raw header encoding, header filtering (allowed/disallowed lists)

### Proto/Configuration

- **`api/envoy/extensions/filters/http/ext_authz/v3/ext_authz.proto`**: HTTP filter configuration
  - `ExtAuthz` message: Filter-level config (service definition, timeouts, failure mode, metadata options)
  - `ExtAuthzPerRoute` message: Per-route overrides (disabled flag, context extensions, body settings)
  - `BufferSettings` message: Request body buffering options
  - `HttpService` message: HTTP service configuration (URI, path prefix, header matchers)
  - `CheckSettings` message: Per-route check customization (context extensions, body settings)

- **`api/envoy/extensions/filters/network/ext_authz/v3/ext_authz.proto`**: Network filter configuration


## 4. Failure Modes

### Authorization Service Errors

**Timeout:**
- gRPC: Configurable timeout (default 200ms), handled by `GrpcClientImpl::onFailure()`
- HTTP: Timeout handled by HTTP async client, triggers `RawHttpClientImpl::onFailure()`
- **Result**: `CheckStatus::Error` response

**Connection Failure:**
- Network unreachable, DNS resolution failure, connection refused
- Both gRPC and HTTP clients catch these via their async client callbacks
- **Result**: `CheckStatus::Error` response

**Service Returns Error:**
- gRPC: Non-Ok status code in CheckResponse
- HTTP: 5xx response status code
- **Result**: `CheckStatus::Error` response

**Invalid Response:**
- CheckResponse contains invalid header names/values (caught during validation)
- Filter can be configured to reject invalid mutations (`validate_mutations=true`)
- **Result**: Local reply with 500 Internal Server Error if `validate_mutations=true`

### Error Handling Modes

**Failure Mode: fail-closed (default)** (`failure_mode_allow=false`):
- If auth service is unavailable or returns error: **deny request**
- HTTP filter returns 403 Forbidden with `status_on_error` code (default 403, configurable)
- Network filter closes the connection
- Sets `UnauthorizedExternalService` response flag
- Response code detail: `ext_authz_error`

**Failure Mode: fail-open** (`failure_mode_allow=true`):
- If auth service is unavailable or returns error: **permit request**
- Increments `failure_mode_allowed` counter
- Optionally adds `x-envoy-auth-failure-mode-allowed: true` header if `failure_mode_allow_header_add=true`
- Useful for graceful degradation when auth service is temporarily down

### Authorization Decision Outcomes

**OK** (`CheckStatus::OK`):
- Apply header/query parameter mutations from `OkHttpResponse`
- Continue to next filter in chain
- Increments `ok` counter

**Denied** (`CheckStatus::Denied`):
- Return to client with status code from response (default 403 Forbidden)
- Apply `headers_to_set` to response sent to client
- Stops filter chain execution
- Increments `denied` counter
- Sets `UnauthorizedExternalService` response flag

**Error** (`CheckStatus::Error`):
- Handled based on `failure_mode_allow` setting (see above)

### Header Validation Errors

**If `validate_mutations=true`:**
- Validates header names and values per HTTP RFC (check `HeaderUtility::headerNameIsValid`)
- Validates query parameters are properly URL-encoded
- Invalid mutations trigger local reply with 500 Internal Server Error
- Increments `invalid` counter

### Buffer Management

**If `with_request_body` is configured:**
- Filter buffers request body up to `max_request_bytes` (default 8KB)
- If body exceeds size and `allow_partial_message=false`: fails the check
- If `allow_partial_message=true`: sends partial body and sets `x-envoy-auth-partial-body: true` header
- Buffer exceeded: Blocks request with 413 Payload Too Large

### Filter State Collisions

**If `emit_filter_state_stats=true` and another filter uses same state name:**
- Filter logs warning and increments `filter_state_name_collision` counter
- Continues processing but observability data not available

### Per-Request Cancellation

**On client connection close or stream reset:**
- `onDestroy()` is called on filter
- Cancels in-flight authorization request via `client_->cancel()`
- `GrpcClientImpl::cancel()`: Calls `request_->cancel()` on gRPC request
- `RawHttpClientImpl` deletes `request_` on destruction


## 5. Testing

### Test Structure

**Unit Tests** (`test/extensions/filters/http/ext_authz/ext_authz_test.cc` - ~4000 lines):

1. **`HttpFilterTestBase<T>`**: Template base class with common setup
   - Sets up mock objects, factory context, cluster manager, HTTP context
   - Configures default authorization service cluster
   - Provides helper methods for creating requests/responses

2. **`HttpFilterTest`**: Main test class covering core functionality
   - `StatsWithPrefix`: Verify stat names with custom prefix
   - `ErrorFailClose`: Error handling with fail-closed mode
   - `ErrorFailOpen`: Error handling with fail-open mode
   - Authorization decision outcomes (OK, Denied, Error)
   - Header/query parameter mutations
   - Request body buffering
   - Per-route configuration merging
   - Dynamic metadata ingestion
   - Tracing integration

3. **`InvalidMutationTest`**: Header/query parameter validation
   - Tests for invalid header names/values (test `HeadersToSetKey`, `QueryParametersToSetValue`, etc.)
   - Only runs with `validate_mutations=true`

4. **`DecoderHeaderMutationRulesTest`**: Request header mutation rules
   - Tests header mutation rule enforcement
   - Blocked headers (pseudo-headers, etc.)
   - Allow/disallow expressions

5. **`EmitFilterStateTest`**: Filter state observability
   - Tests logging info emission for observability
   - Tests latency tracking
   - Tests bytes sent/received metrics for gRPC

6. **`HttpFilterTestParam`**: Parameterized tests
   - Tests multiple configurations (gRPC vs HTTP, with/without body, etc.)

### Test Infrastructure

**Mocks:**
- `MockAsyncClient`: Mocks gRPC async client for testing without real gRPC
- `MockHttpAsyncClientManager`: Mocks HTTP cluster manager
- `TestRequestCallbacks`: Captures authorization responses for assertions

**Test Configuration:**
- `config_builder()`: Builds proto config from YAML/code
- `createFilter()`: Factory for creating filter instances with config
- `callCheck()`: Triggers authorization check with mocked response

**Corpus Files (Fuzzing):**
- `test/extensions/filters/http/ext_authz/ext_authz_grpc_corpus/`: Fuzzing test cases for gRPC client
- `test/extensions/filters/http/ext_authz/ext_authz_http_corpus/`: Fuzzing test cases for HTTP client
- `ext_authz_grpc_fuzz_test.cc`, `ext_authz_http_fuzz_test.cc`: Fuzzing test drivers

### Integration Tests

**File**: `test/extensions/filters/http/ext_authz/ext_authz_integration_test.cc` (~1800 lines):

- `ExtAuthzGrpcIntegrationTest`: Full integration with real gRPC auth service
  - Sets up a mock authorization gRPC server
  - Tests end-to-end request flow with header mutations
  - Tests failure scenarios (service returning errors, timeouts)
  - Tests with real HTTP filter chain

**Test Scenarios:**
- Authorized request flows through filter chain
- Denied requests return 403 with response headers
- Authorization service timeouts handled correctly
- Header mutations applied correctly
- Request body buffering and partial body handling
- Per-route configuration overrides
- Multiple authorization headers merged correctly

### Configuration Tests

**File**: `test/extensions/filters/http/ext_authz/config_test.cc` (~400 lines):

- Proto config parsing and validation
- Cluster configuration validation
- Timeout configuration handling
- Request header matcher configuration


## 6. Debugging

### Logging

The filter uses Envoy's logging system with various levels:

**Trace Level** (most verbose):
- Every significant operation logged via `ENVOY_STREAM_LOG(trace, ...)`
- Examples:
  - "ext_authz filter calling authorization server"
  - "ext_authz filter is buffering the request"
  - "ext_authz filter added header(s) to the request" (with actual header key/values)
  - "ext_authz filter rejected the request. Response status code: '403'"

**Debug Level**:
- Major state transitions and decisions
- "ext_authz filter finished buffering the request"
- "ext_authz filter is disabled. Deny the request."

**Info Level**:
- Filter initialization, configuration errors

**To enable trace logging:**
```yaml
admin:
  access_log_path: /tmp/admin_access.log
  address:
    socket_address:
      address: 127.0.0.1
      port_value: 9000
logger_manager:
  loggers:
  - name: filter_ext_authz
    level: trace
```

### Metrics / Statistics

**Counters** (all in namespace `ext_authz.` or `ext_authz.<stat_prefix>.` if configured):

| Metric | Description | When Incremented |
|--------|-------------|------------------|
| `ok` | Successful authorization check | Request authorized (CheckStatus::OK) |
| `denied` | Request explicitly denied by auth service | CheckStatus::Denied response |
| `error` | Authorization service unavailable/error | Auth service unreachable, timeout, 5xx |
| `disabled` | Request allowed without calling auth service | Filter disabled (per-route or runtime) |
| `failure_mode_allowed` | Request allowed due to auth service error | CheckStatus::Error + failure_mode_allow=true |
| `invalid` | Invalid authorization response (bad headers/query) | validate_mutations=true and invalid mutation |
| `ignored_dynamic_metadata` | Dynamic metadata not ingested | Dynamic metadata in response but disabled |
| `filter_state_name_collision` | Filter state name collision detected | Another filter used same state name |

**Gauge** (network filter only, not HTTP):
| Metric | Description |
|--------|-------------|
| `active` | Active authorization checks in flight | Network filter only |

**To view stats:**
```bash
# All ext_authz stats
curl http://localhost:9000/stats | grep ext_authz

# Specific filter instance stats
curl http://localhost:9000/stats | grep "ext_authz.my_authz_filter"

# JSON format
curl http://localhost:9000/stats?format=json | jq '.stats[] | select(.name | contains("ext_authz"))'
```

### Request/Response Tracing

**Distributed Tracing Integration:**
- Filter creates a child span under the request's parent trace span
- Span name: "ext_authz" (for gRPC) or configured tracing name (for HTTP)
- Tags set on span:
  - `ext_authz_status`: "ext_authz_ok" or "ext_authz_unauthorized"
  - `ext_authz_http_status`: HTTP status code from HTTP auth service
  - Service name: Set in HTTP client config

**Example Trace Flow:**
```
Request Span
  ├─ ext_authz Check Span
  │    └─ Authorization Service Call
  │         └─ Duration in milliseconds
  └─ Upstream Request Span (if authorized)
```

**Tracing Configuration Example:**
```yaml
http_filters:
- name: envoy.filters.http.ext_authz
  typed_config:
    "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
    grpc_service:
      envoy_grpc:
        cluster_name: ext-authz
      timeout: 200ms
```

### Dynamic Metadata

**If `emit_filter_state_stats=true`:**
- Filter stores `ExtAuthzLoggingInfo` object in stream's filter state
- Can be accessed by other filters or access logs
- Contains:
  - `latency`: Authorization check duration (microseconds)
  - `bytes_sent`: Bytes sent to gRPC auth service (gRPC only)
  - `bytes_received`: Bytes received from gRPC auth service (gRPC only)
  - `cluster_info`: Cluster used for gRPC call
  - `upstream_host`: Specific host/endpoint used for gRPC call
  - `filter_metadata`: Custom metadata from proto config

**Access in Access Logs:**
```yaml
access_log_path: /tmp/access.log
access_log:
  name: envoy.access_loggers.file
  typed_config:
    "@type": type.googleapis.com/envoy.extensions.accesslog.v3.FileAccessLog
    path: /tmp/access.log
    format: '[%START_TIME%] ext_authz_duration=%FILTER_STATE(ext_authz:filter_metadata)%'
```

### Production Debugging Checklist

**When requests are being denied unexpectedly:**

1. **Check filter enabled state:**
   - Is the filter enabled for this route? Check `filter_enabled` config or per-route `disabled` flag
   - Is there a runtime override? Check `/runtime_keys` admin endpoint

2. **Check authorization service connectivity:**
   - Can Envoy reach the auth service? Check cluster health: `/clusters?format=json`
   - Are there connection errors? Look for error counter increments: `/stats/ext_authz.error`
   - Check logs for "failed with status" messages at debug level

3. **Check authorization service response:**
   - Enable trace logging to see actual CheckRequest and CheckResponse (with `DebugString()`)
   - Verify auth service returns correct status code (0=OK, non-0=Denied)
   - Check if response includes required mutations

4. **Check header mutations:**
   - Enable trace logging to see "headers_to_set" and "headers_to_add"
   - If `validate_mutations=true`, check for "Rejected invalid header" messages
   - Verify header values are valid HTTP (no nulls, etc.)

5. **Check failure mode:**
   - If auth service is down, is `failure_mode_allow` configured?
   - Look for `failure_mode_allowed` counter increments

6. **Useful admin endpoints:**
   ```bash
   # View config
   curl http://localhost:9000/config_dump | jq '.configs[] | select(.name | contains("ext_authz"))'

   # View stats
   curl http://localhost:9000/stats | grep ext_authz

   # View runtime values
   curl http://localhost:9000/runtime

   # View cluster health
   curl http://localhost:9000/clusters | grep -A 10 "ext-authz"
   ```

7. **gRPC-specific debugging:**
   - Use `grpcurl` to test auth service directly
   - Check if service is properly implementing `envoy.service.auth.v3.Authorization.Check` method

8. **Request body buffering issues:**
   - If using `with_request_body`, check if body exceeds `max_request_bytes`
   - Enable trace logging to see "finished buffering" messages
   - Look for buffer size warnings

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| All requests denied with 403 | Auth service returning non-OK status | Check auth service logic, add trace logging |
| Timeouts on every request | Auth service slow or unreachable | Increase timeout, check network/cluster config |
| Headers not being added | Mutations disabled or not in response | Check response from auth service, validate matchers |
| Filter overhead high | Header/body buffering or slow auth service | Profile auth service, consider fail-open mode |
| Stats not appearing | Filter not being called | Check per-route disable, runtime flags, cluster routing |
| Trace spans missing | Tracing not configured | Configure tracing provider, check trace sampling |

