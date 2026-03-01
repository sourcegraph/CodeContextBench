# Investigation Report: Duplicate Response Headers in Envoy Filter Pipeline

## Summary

Response headers configured via `response_headers_to_add` are being duplicated on local replies (timeout, connection failure, etc.) due to `RouteEntry::finalizeResponseHeaders()` being called twice: once through the router's callback passed to `sendLocalReply()` and again through the filter manager's EncodeFunctions wrapper lambda.

## Root Cause

The root cause is a **double invocation of `RouteEntry::finalizeResponseHeaders()`** that occurs specifically for local replies via the following mechanism:

1. **Router Layer (source/common/router/router.cc:486-503, 520)**:
   - When the router detects a direct response or needs to send a local reply, it calls `callbacks_->sendLocalReply()`
   - For direct responses (lines 486-503), it passes a lambda containing `direct_response->finalizeResponseHeaders()` (line 501)
   - This lambda becomes the `modify_headers` parameter to the filter manager

2. **Filter Manager Layer (source/common/http/filter_manager.cc:1123-1129, 1070-1079)**:
   - `DownstreamFilterManager::sendLocalReplyViaFilterChain()` receives the router's `modify_headers` callback
   - It wraps this in an `EncodeFunctions` lambda (lines 1123-1129) that:
     - Calls `streamInfo().route()->routeEntry()->finalizeResponseHeaders()` at line 1125
     - Then calls the passed-in `modify_headers` callback at line 1127-1128
   - The same pattern exists in `prepareLocalReply()` (lines 1070-1079)

3. **Utility Layer (source/common/http/utility.cc:718-720)**:
   - `Utility::prepareLocalReply()` calls `encode_functions.modify_headers_()` (line 718-719)
   - This executes BOTH:
     - The filter manager's call to `finalizeResponseHeaders()` (first invocation)
     - The router's passed-in lambda that also calls `finalizeResponseHeaders()` (second invocation)

## Evidence

### Direct Response Path
**source/common/router/router.cc:486-503** - Router passes callback with `finalizeResponseHeaders()`:
```cpp
callbacks_->sendLocalReply(
    direct_response->responseCode(), direct_response->responseBody(),
    [this, direct_response, &request_headers = headers](Http::ResponseHeaderMap& response_headers) -> void {
      // ... location header logic ...
      direct_response->finalizeResponseHeaders(response_headers, callbacks_->streamInfo());  // FIRST CALL
    },
    absl::nullopt, StreamInfo::ResponseCodeDetails::get().DirectResponse);
```

**source/common/http/filter_manager.cc:1123-1129** - Filter manager wraps in another `finalizeResponseHeaders()`:
```cpp
Utility::EncodeFunctions{
    [this, modify_headers](ResponseHeaderMap& headers) -> void {
      if (streamInfo().route() && streamInfo().route()->routeEntry()) {
        streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());  // SECOND CALL
      }
      if (modify_headers) {
        modify_headers(headers);  // Executes router's lambda containing FIRST CALL
      }
    },
    // ... other functions ...
};
```

**source/common/http/utility.cc:709-720** - Execution order:
```cpp
Utility::PreparedLocalReplyPtr Utility::prepareLocalReply(const EncodeFunctions& encode_functions, ...) {
  // ... create response_headers ...
  if (encode_functions.modify_headers_) {
    encode_functions.modify_headers_(*response_headers);  // Executes filter_manager's lambda
  }
  // ... finalizes response ...
}
```

### Header Processing Logic
**source/common/router/config_impl.cc:942-950** - `finalizeResponseHeaders()` applies all response header parsers:
```cpp
void RouteEntryImplBase::finalizeResponseHeaders(Http::ResponseHeaderMap& headers,
                                                 const StreamInfo::StreamInfo& stream_info) const {
  for (const HeaderParser* header_parser : getResponseHeaderParsers(...)) {
    header_parser->evaluateHeaders(headers, {stream_info.getRequestHeaders(), &headers}, stream_info);
  }
}
```

**source/common/router/header_parser.cc:58-71** - Proto field handling (append vs append_action):
```cpp
if (header_value_option.has_append()) {
  if (header_value_option.append_action() != HeaderValueOption::APPEND_IF_EXISTS_OR_ADD) {
    // Error if both fields set
  }
  append_action_ = header_value_option.append().value()
                       ? HeaderValueOption::APPEND_IF_EXISTS_OR_ADD
                       : HeaderValueOption::OVERWRITE_IF_EXISTS_OR_ADD;
} else {
  append_action_ = header_value_option.append_action();  // Use new enum field
}
```

### Why Upstream Responses DON'T Duplicate
**source/common/router/router.cc:1792-1793** - Upstream path calls `finalizeResponseHeaders()` directly ONCE:
```cpp
route_entry_->finalizeResponseHeaders(*headers, callbacks_->streamInfo());
modify_headers_(*headers);
callbacks_->encodeHeaders(std::move(headers), end_stream, ...);
```

The upstream response flows through `encodeHeaders()` directly without the filter manager's double-wrapping for local replies.

## Affected Components

1. **source/common/router/** (router.cc, config_impl.cc, config_impl.h)
   - `Filter::decodeHeaders()` - sends local replies with `finalizeResponseHeaders()` callbacks
   - `RouteEntryImplBase::finalizeResponseHeaders()` - applies response header transformations

2. **source/common/http/** (filter_manager.cc, filter_manager.h, utility.cc, utility.h)
   - `DownstreamFilterManager::sendLocalReplyViaFilterChain()` - wraps router callback
   - `DownstreamFilterManager::prepareLocalReply()` - prepares local reply response
   - `Utility::prepareLocalReply()` - executes the double-wrapped callbacks
   - `Utility::encodeLocalReply()` - encodes prepared reply

3. **api/envoy/config/core/v3/** (base.proto)
   - `HeaderValueOption.append_action` - enum defining append behaviors (APPEND_IF_EXISTS_OR_ADD, ADD_IF_ABSENT, OVERWRITE_IF_EXISTS_OR_ADD, OVERWRITE_IF_EXISTS)
   - `HeaderValueOption.append` - deprecated BoolValue field

4. **source/extensions/filters/http/header_mutation/** (header_mutation.cc)
   - `HeaderMutation::encodeHeaders()` - applies additional header mutations on encode path, but only once

## Causal Chain

1. **Symptom**: Response headers appear duplicated in local reply access logs (e.g., `x-custom-trace: abc123` appears twice)

2. **Intermediate**: Access log shows `response_code_details=upstream_response_timeout` indicating a local reply was generated by the router

3. **Direct Cause**: `RouteEntry::finalizeResponseHeaders()` is invoked twice for the same response headers
   - First time: Through router's direct response lambda (line 501 of router.cc)
   - Second time: Through filter manager's EncodeFunctions wrapper (line 1125 of filter_manager.cc)

4. **Root Mechanism**:
   - Router constructs a callback that includes `finalizeResponseHeaders()` and passes it to `sendLocalReply()`
   - Filter manager wraps this callback in ANOTHER lambda that ALSO calls `finalizeResponseHeaders()`
   - When `prepareLocalReply()` executes the callbacks, both calls execute in sequence

5. **Why Headers Duplicate**:
   - First `finalizeResponseHeaders()` call processes response_headers_to_add config and adds headers according to their `append_action` (defaults to APPEND_IF_EXISTS_OR_ADD)
   - Second `finalizeResponseHeaders()` call processes the SAME config again
   - With `APPEND_IF_EXISTS_OR_ADD` action, the header is appended rather than overwritten
   - Result: header appears twice in the response

## Recommendation

**Fix Strategy**: Eliminate the duplicate wrapping by removing the `finalizeResponseHeaders()` call from the filter manager's EncodeFunctions lambda for local replies, since the router's callback already invokes it.

**Diagnostic Steps**:
1. Enable debug logging at filter_manager.cc and router.cc to trace `finalizeResponseHeaders()` call count
2. Add metrics to count how many times `finalizeResponseHeaders()` is called per request
3. Compare call counts between:
   - Upstream response path (should be 1)
   - Local reply path (currently 2, should be 1)

**Files Requiring Changes**:
- `source/common/http/filter_manager.cc` - Remove duplicate `finalizeResponseHeaders()` call from EncodeFunctions lambda in `sendLocalReplyViaFilterChain()` and `prepareLocalReply()` methods

**Why This Fix is Safe**:
- Router filter already guarantees `finalizeResponseHeaders()` is called via the passed callback
- Direct responses already include their own `finalizeResponseHeaders()` call in the lambda
- Non-direct local replies can be updated to include `finalizeResponseHeaders()` in their callbacks
- Filter manager should not redundantly invoke route-level header mutations

**Verification**:
- Run existing tests with the fix to ensure no regressions
- Add new test case specifically for local replies with response_headers_to_add to verify headers appear exactly once
- Use integration tests with access logging to verify duplicate header issue is resolved
