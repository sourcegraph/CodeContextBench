# Investigation Report: Duplicate Response Headers in Envoy Filter Pipeline

## Summary

Response headers configured via `response_headers_to_add` in route configuration are duplicated when the router filter generates a local reply (upstream timeout, connection failure, etc.), but appear only once for proxied upstream responses. The root cause is that `finalizeResponseHeaders()` is invoked twice during local reply processing: once directly in the filter manager's local reply path, and again via the router's `modify_headers_` callback, causing headers to be added multiple times.

## Root Cause

**File:** `/workspace/source/common/http/filter_manager.cc` (lines 1123-1129)
**Mechanism:** Double invocation of `route_entry_->finalizeResponseHeaders()` during local reply processing

In `DownstreamFilterManager::sendLocalReplyViaFilterChain()`, an `EncodeFunctions` lambda is created that:

1. **First call** (line 1125): Directly calls `route_entry_->finalizeResponseHeaders()`
2. **Second call** (line 1128): Calls `modify_headers()` callback, which is the router's `modify_headers_` lambda

The router's `modify_headers_` lambda (defined in `/workspace/source/common/router/router.cc` lines 444-453) itself calls `route_entry_->finalizeResponseHeaders()` again at line 453.

## Evidence

### Local Reply Code Path

**File:** `/workspace/source/common/http/filter_manager.cc:1123-1129`
```cpp
[this, modify_headers](ResponseHeaderMap& headers) -> void {
  if (streamInfo().route() && streamInfo().route()->routeEntry()) {
    streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());  // CALL #1
  }
  if (modify_headers) {
    modify_headers(headers);  // CALL #2 (router's modify_headers_ lambda)
  }
},
```

### Router's modify_headers_ Lambda

**File:** `/workspace/source/common/router/router.cc:444-453`
```cpp
modify_headers_ = [this](Http::ResponseHeaderMap& headers) {
  if (route_entry_ == nullptr) {
    return;
  }
  if (modify_headers_from_upstream_lb_) {
    modify_headers_from_upstream_lb_(headers);
  }
  route_entry_->finalizeResponseHeaders(headers, callbacks_->streamInfo());  // FINAL CALL

  if (attempt_count_ == 0 || !route_entry_->includeAttemptCountInResponse()) {
    return;
  }
  headers.setEnvoyAttemptCount(attempt_count_);
};
```

### Upstream Response Path (Correct Behavior)

**File:** `/workspace/source/common/router/router.cc:1794`
```cpp
modify_headers_(*headers);  // SINGLE CALL - finalizeResponseHeaders invoked once
```

For upstream responses, `modify_headers_` is called directly, and `finalizeResponseHeaders()` is invoked **only once**.

### Header Parser Implementation

**File:** `/workspace/source/common/router/header_parser.cc:173-212`

The `evaluateHeaders()` function processes `response_headers_to_add` entries:
- For `APPEND_IF_EXISTS_OR_ADD` (default when `append_action` not specified or proto defaults apply):
  - Uses `headers.addReferenceKey()` (line 211), which adds headers without removing existing ones
  - Multiple calls result in multiple header values

- For `OVERWRITE_IF_EXISTS_OR_ADD`:
  - Uses `headers.setReferenceKey()` (line 206), which removes then adds
  - But if header parser evaluation happens twice, the second invocation still produces a header value

### Local Reply Preparation

**File:** `/workspace/source/common/http/utility.cc:709-721`

```cpp
Utility::PreparedLocalReplyPtr Utility::prepareLocalReply(const EncodeFunctions& encode_functions,
                                                          const LocalReplyData& local_reply_data) {
  // ...
  ResponseHeaderMapPtr response_headers{createHeaderMap<ResponseHeaderMapImpl>(...)};

  if (encode_functions.modify_headers_) {
    encode_functions.modify_headers_(*response_headers);  // Lambda invoked with both calls
  }
  // ...
}
```

## Affected Components

1. **`source/common/router/router.cc`**
   - Router filter's `modify_headers_` lambda definition (lines 444-461)
   - `onUpstreamHeaders()` direct call to `modify_headers_` (line 1794)
   - Multiple `sendLocalReply()` calls with `modify_headers_` as callback (lines 522, 550, 739, 750, 931, 1002, 1058, 1338, 1405, 2235, 2254)

2. **`source/common/http/filter_manager.cc`**
   - `DownstreamFilterManager::sendLocalReplyViaFilterChain()` lambda with double `finalizeResponseHeaders()` calls (lines 1123-1129)
   - `DownstreamFilterManager::sendLocalReply()` orchestrator (lines 982-1053)
   - `Utility::sendLocalReply()` dispatcher (via utility.cc)

3. **`source/common/router/header_parser.cc`**
   - `HeaderParser::evaluateHeaders()` applies configured response headers (lines 145-213)
   - `HeadersToAddEntry` parsing of deprecated `append` vs newer `append_action` fields (lines 53-76)

4. **`source/common/http/utility.cc`**
   - `Utility::prepareLocalReply()` invokes the modify_headers callback (lines 709-781)
   - `Utility::encodeLocalReply()` executes the prepared response (lines 783-814)

5. **`api/envoy/config/core/v3/base.proto`**
   - `HeaderValueOption.append_action` enum with default `APPEND_IF_EXISTS_OR_ADD` (line ~18)
   - Deprecated `HeaderValueOption.append` BoolValue field (defaults true)

## Causal Chain

1. **Symptom**: Response headers in access logs show duplicate values for the same header key in local replies
   - Example: `x-custom-trace: abc123` appears twice

2. **Observation**: Headers duplicated only on local replies (timeout, no healthy upstream, etc.), not on proxied responses

3. **Filter Chain Invocation**: `DownstreamFilterManager::sendLocalReply()` is called by the router filter when generating a local response (line 982)

4. **Local Reply Path Selection**: `sendLocalReplyViaFilterChain()` is chosen when response hasn't started (line 1031)

5. **Lambda Creation with Double Finalization**: `sendLocalReplyViaFilterChain()` creates an `EncodeFunctions` lambda that calls:
   - `route_entry_->finalizeResponseHeaders()` directly (line 1125)
   - Then `modify_headers()` callback (line 1128)

6. **Router Filter's Callback**: The `modify_headers` callback is the router's `modify_headers_` lambda, which itself calls `route_entry_->finalizeResponseHeaders()` (router.cc:453)

7. **Header Parser Double Invocation**: `finalizeResponseHeaders()` (router/config_impl.cc:942-950) invokes `HeaderParser::evaluateHeaders()` for each response header parser

8. **Duplicate Header Addition**: For headers using `APPEND_IF_EXISTS_OR_ADD` or default `append_action`:
   - First invocation adds header via `addReferenceKey()`
   - Second invocation adds the same header again via `addReferenceKey()`
   - Result: Multiple header values for the same key

9. **Root Cause**: The filter manager's local reply path was designed to ensure route-specific headers are applied by explicitly calling `finalizeResponseHeaders()`, but this inadvertently bypasses the deduplication mechanism present in the upstream response path where `modify_headers_` is called exactly once.

## Recommendation

### Fix Strategy

The issue stems from the filter manager's attempt to apply route-level response headers in the local reply path. The correct fix is to remove the explicit `finalizeResponseHeaders()` call from the lambda in `sendLocalReplyViaFilterChain()` and rely solely on the `modify_headers` callback (the router's `modify_headers_` lambda) to handle header finalization.

**Proposed Change:**

In `/workspace/source/common/http/filter_manager.cc`, lines 1123-1129, modify the lambda:

```cpp
// BEFORE (problematic)
[this, modify_headers](ResponseHeaderMap& headers) -> void {
  if (streamInfo().route() && streamInfo().route()->routeEntry()) {
    streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());  // REMOVE THIS
  }
  if (modify_headers) {
    modify_headers(headers);  // This already calls finalizeResponseHeaders()
  }
},

// AFTER (fixed)
[this, modify_headers](ResponseHeaderMap& headers) -> void {
  if (modify_headers) {
    modify_headers(headers);  // Single call handles all header finalization
  }
},
```

Apply the same fix to `prepareLocalReplyViaFilterChain()` at lines 1072-1078.

### Diagnostic Steps

To verify the issue in a running Envoy instance:

1. Enable response logging with both headers and details:
   - Format string: `"%RESPONSE_CODE_DETAILS%"` and `"%RESP(header-name)%"`

2. Generate a local reply condition (upstream timeout, circuit breaker open, etc.)

3. Observe response headers in access logs:
   - Duplicates confirm the issue
   - Single values after fix confirms resolution

4. Compare behavior with proxied upstream responses (should show single headers in both cases)

### Impact Assessment

- **Breaking Changes**: None - this is a bug fix that normalizes local reply behavior to match upstream response behavior
- **Performance**: Slight improvement from fewer header parser invocations
- **Compatibility**: Fixes application-level duplicate header handling bugs
