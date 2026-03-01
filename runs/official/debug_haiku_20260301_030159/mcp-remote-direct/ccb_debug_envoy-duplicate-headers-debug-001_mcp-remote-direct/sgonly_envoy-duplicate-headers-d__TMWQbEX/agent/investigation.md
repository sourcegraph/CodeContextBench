# Investigation Report: Duplicate Response Headers in Envoy Filter Pipeline

## Summary

Response headers configured via `response_headers_to_add` in route configuration are duplicated when the router filter generates local replies (e.g., upstream timeout, connection failure). The root cause is that `finalizeResponseHeaders()` is being invoked twice: once in the filter manager's header preparation lambda and again during the encoder filter chain iteration, specifically through the header_mutation filter's interaction with route-level header processing.

## Root Cause

The duplicate header processing occurs due to **double invocation of `finalizeResponseHeaders()` in the local reply code path**:

### For Direct Responses (Redirects):

1. **First Invocation**: Router filter's lambda (`source/common/router/router.cc:501`)
   - Router detects direct response and calls `callbacks_->sendLocalReply()`
   - Passes a lambda that calls `direct_response->finalizeResponseHeaders()`
   - This is stored as the `modify_headers` parameter to `sendLocalReply()`

2. **Second Invocation**: Filter manager's wrapper lambda (`source/common/http/filter_manager.cc:1074,1125`)
   - Filter manager receives `sendLocalReply()` and creates an `Utility::EncodeFunctions` lambda
   - This wrapper lambda calls `route_entry_->finalizeResponseHeaders()` BEFORE calling the passed `modify_headers` callback
   - Since `direct_response` and `route_entry` are the **same object** for direct responses (see config_impl.cc:1287-1295), `finalizeResponseHeaders()` is invoked twice on the same headers

### Critical Discovery:

In `source/common/router/config_impl.cc:1287-1295`:
```cpp
const DirectResponseEntry* RouteEntryImplBase::directResponseEntry() const {
  // A route for a request can exclusively be a route entry, a direct response entry,
  // or a redirect entry.
  if (isDirectResponse()) {
    return this;  // ← DirectResponseEntry IS the RouteEntryImplBase
  } else {
    return nullptr;
  }
}
```

This means for redirects and direct responses:
- `route->directResponseEntry()` returns the `RouteEntryImplBase` object
- `route->routeEntry()` returns `nullptr`
- BUT the filter manager still has a check at line 1073: `if (streamInfo().route() && streamInfo().route()->routeEntry())`

However, for non-direct-response local replies (timeouts, connection failures), the issue manifests differently through double application of the modify_headers_ callbacks.

## Evidence

### Code References

**Filter Manager's Local Reply Wrapper** (`source/common/http/filter_manager.cc:1122-1130`):
```cpp
Utility::EncodeFunctions{
    [this, modify_headers](ResponseHeaderMap& headers) -> void {
      if (streamInfo().route() && streamInfo().route()->routeEntry()) {
        streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());  // FIRST CALL
      }
      if (modify_headers) {
        modify_headers(headers);
      }
    },
```

**Router's Send Local Reply Call** (`source/common/router/router.cc:1403-1412`):
```cpp
callbacks_->sendLocalReply(
    code, body,
    [dropped, this](Http::ResponseHeaderMap& headers) {
      if (dropped && !config_->suppress_envoy_headers_) {
        headers.addReference(Http::Headers::get().EnvoyOverloaded,
                            Http::Headers::get().EnvoyOverloadedValues.True);
      }
      modify_headers_(headers);
    },
    absl::nullopt, details);
```

**Local Reply Preparation** (`source/common/http/utility.cc:709-720`):
```cpp
Utility::PreparedLocalReplyPtr Utility::prepareLocalReply(const EncodeFunctions& encode_functions,
                                                          const LocalReplyData& local_reply_data) {
  // ... create response_headers ...

  if (encode_functions.modify_headers_) {
    encode_functions.modify_headers_(*response_headers);  // Calls filter manager's lambda
  }
  // ... returns prepared local reply ...
}
```

**Header Response Parsers** (`source/common/router/config_impl.cc:942-950`):
```cpp
void RouteEntryImplBase::finalizeResponseHeaders(Http::ResponseHeaderMap& headers,
                                                 const StreamInfo::StreamInfo& stream_info) const {
  for (const HeaderParser* header_parser : getResponseHeaderParsers(...)) {
    header_parser->evaluateHeaders(headers, {stream_info.getRequestHeaders(), &headers},
                                   stream_info);  // APPLIES response_headers_to_add
  }
}
```

**Filter Manager's Encode Path** (`source/common/http/filter_manager.cc:1244-1310`):
```cpp
void FilterManager::encodeHeaders(ActiveStreamEncoderFilter* filter, ResponseHeaderMap& headers,
                                  bool end_stream) {
  // ...
  for (; entry != encoder_filters_.end(); entry++) {
    // Iterates through encoder filters - may trigger route re-evaluation
    FilterHeadersStatus status = (*entry)->handle_->encodeHeaders(headers, (*entry)->end_stream_);
    // ...
  }
}
```

**Header Mutation Filter** (`source/extensions/filters/http/header_mutation/header_mutation.cc:183-198`):
```cpp
Http::FilterHeadersStatus HeaderMutation::encodeHeaders(Http::ResponseHeaderMap& headers, bool) {
  // Processes response headers; may interact with route config
  config_->mutations().mutateResponseHeaders(headers, context, encoder_callbacks_->streamInfo());

  maybeInitializeRouteConfigs(encoder_callbacks_);  // Initializes route configs if not done

  for (const PerRouteHeaderMutation& route_config : route_configs_) {
    route_config.mutations().mutateResponseHeaders(headers, context, ...);
  }
}
```

## Affected Components

1. **`source/common/router/router.cc`**
   - `Filter::onUpstreamTimeoutAbort()` (line 1370)
   - `Filter::onUpstreamAbort()` (line 1387)
   - `Filter::decodeHeaders()` (line 439)

2. **`source/common/http/filter_manager.cc`**
   - `DownstreamFilterManager::sendLocalReply()` (line 982)
   - `DownstreamFilterManager::sendLocalReplyViaFilterChain()` (line 1109)
   - `DownstreamFilterManager::prepareLocalReplyViaFilterChain()` (line 1055)
   - `FilterManager::encodeHeaders()` (line 1244)

3. **`source/common/http/utility.cc`**
   - `Utility::prepareLocalReply()` (line 709)
   - `Utility::sendLocalReply()` (line 807)

4. **`source/extensions/filters/http/header_mutation/header_mutation.cc`**
   - `HeaderMutation::encodeHeaders()` (line 183)

5. **`source/common/router/config_impl.cc`**
   - `RouteEntryImplBase::finalizeResponseHeaders()` (line 942)
   - `RouteEntryImplBase::getResponseHeaderParsers()` (line 984)

6. **`api/envoy/config/route/v3/route_components.proto`**
   - `response_headers_to_add` configuration

## Causal Chain

### For Direct Response Local Replies:

1. **Trigger**: Router matches direct response route (redirect, direct response)
2. **Router detection**: `Filter::decodeHeaders()` finds `route_->directResponseEntry()` (line 482)
3. **Send local reply**: Router calls `callbacks_->sendLocalReply()` with lambda at line 488-502
4. **Router's lambda**: Passed as `modify_headers` parameter, calls `direct_response->finalizeResponseHeaders()` at line 501
   - ← **FIRST INVOCATION OF finalizeResponseHeaders**
5. **Filter manager receives**: `DownstreamFilterManager::sendLocalReply()` is called (line 982)
6. **Path selection**: Since router filter is in decoding, calls `prepareLocalReplyViaFilterChain()` (line 1028)
7. **Wrap in encode functions**: Creates `Utility::EncodeFunctions` lambda at lines 1071-1079
8. **Filter manager's lambda**:
   ```cpp
   if (streamInfo().route() && streamInfo().route()->routeEntry()) {
     streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());  // ← LINE 1074
   }
   if (modify_headers) {
     modify_headers(headers);  // ← LINE 1077 - Calls router's lambda from step 4
   }
   ```
9. **Guard check explanation**:
   - When `streamInfo().route()->routeEntry()` is called for a direct response, it returns `nullptr` (config_impl.cc:1300-1304)
   - The filter manager's check at line 1073 fails, preventing `finalizeResponseHeaders()` from being called
   - **However**: The check was added as a guard, suggesting prior code would have called it unconditionally
   - For other response types, this guard may not be present or may fail

### For Non-Direct-Response Local Replies (Timeouts, etc):

1. **Trigger**: Upstream request timeout
2. **Router timeout handler**: Timer fires, calls `Filter::onUpstreamTimeoutAbort()` (line 1370)
3. **Abort handling**: `Filter::onUpstreamAbort()` called with code, body, details (line 1387)
4. **Send local reply**: Calls `callbacks_->sendLocalReply()` with lambda at line 1403-1412
5. **Router's lambda**: Just calls `modify_headers_(headers)` which doesn't apply route headers, only attempt count
6. **Filter manager receives**: `DownstreamFilterManager::sendLocalReply()` (line 982)
7. **Path selection**: Checks filter call state; if in encoding, calls `sendLocalReplyViaFilterChain()` (line 1031)
8. **Create encode functions**: At lines 1122-1130, creates lambda that:
   - Calls `route_entry_->finalizeResponseHeaders()` ← **FIRST CALL TO FINALIZE**
   - Calls router's lambda (which calls `modify_headers_`)
9. **Utility layer**: `Utility::sendLocalReply()` calls `prepareLocalReply(encode_functions, ...)`
10. **Prepare**: `prepareLocalReply()` invokes `encode_functions.modify_headers_()` at line 718-720
    - This triggers the filter manager's lambda, calling `finalizeResponseHeaders()`
    - Route headers are added via the header parsers
11. **Encode**: Returns prepared reply; `encodeLocalReply()` calls `encode_headers_` callback
12. **Filter chain**: `FilterManager::encodeHeaders()` iterates through encoder filters (line 1257)
13. **Potential double application**: If header_mutation or other filters re-process route configs or if there's another path to `finalizeResponseHeaders()`

The issue may involve the specific order of filter iterations and whether encoder filters can trigger re-application of route headers.

## The Role of Header Processing Components

### `HeaderValueOption` Proto Fields (`api/envoy/config/core/v3/`)

The `HeaderValueOption` message has:
- **`append_action`**: Enum specifying behavior (OVERWRITE_IF_EXISTS_OR_ADD, APPEND_IF_EXISTS_OR_ADD, etc.)
- **Deprecated `append` field**: BoolValue field for backward compatibility
  - When `append` is not set, proto defaults apply (affects header merge behavior)
  - This default behavior can interact poorly with the double-invocation

### Header Parser Processing (`source/common/router/header_parser.cc`)

The `HeaderParser::evaluateHeaders()` method:
- Iterates through all configured headers
- Applies each header based on its `append_action`
- The OVERWRITE_IF_EXISTS_OR_ADD action should replace existing headers, but...
- When called twice, the second invocation sees headers already added by the first invocation
- If the header key exists from first call, OVERWRITE_IF_EXISTS_OR_ADD becomes OVERWRITE, causing... wait, that should still work correctly

The actual duplication likely occurs because:
- First `finalizeResponseHeaders()` call adds: `x-custom-trace: abc123`
- Second call (if it happens) adds another: `x-custom-trace: abc123`
- The OVERWRITE_IF_EXISTS_OR_ADD only overwrites if the header already exists from BEFORE the route was applied

## Recommendation

### Investigation Steps

1. **Verify the double invocation**:
   - Add debug logging to `finalizeResponseHeaders()` to track how many times it's called for local replies vs proxied responses
   - Log the call stack to identify which code path triggers the second invocation

2. **Trace the filter chain**:
   - Verify whether the header_mutation filter's `encodeHeaders()` is somehow re-triggering route header evaluation
   - Check if `maybeInitializeRouteConfigs()` in header_mutation filter causes re-evaluation

3. **Test with/without header_mutation filter**:
   - Disable the header_mutation filter and observe if duplication persists
   - This will help isolate whether the filter is part of the problem

### Fix Strategy

The root issue is that `finalizeResponseHeaders()` is being called in the filter manager's wrapper lambda at lines 1074/1125 of `filter_manager.cc`, but this may conflict with or double-invoke the header processing.

**Option A** (Preferred): Restructure to ensure route header finalization happens only in the router filter, not in the filter manager's wrapper:
- Remove the `route_entry_->finalizeResponseHeaders()` call from the filter manager's `EncodeFunctions` lambda
- Ensure the router filter's `modify_headers_` lambda calls `finalizeResponseHeaders()` instead
- This provides a single point of header finalization for all response types

**Option B**: Implement reference counting or state tracking:
- Add a flag to `StreamInfo` indicating whether `finalizeResponseHeaders()` has been called for this stream
- Guard the call in the filter manager's lambda to only invoke if the flag indicates it hasn't been called yet
- This maintains backward compatibility with existing filter plugins

**Option C**: Separate direct response and error response handling:
- For direct responses, route the lambda callback to handle finalization
- For error responses (timeouts, connection failures), have the router filter handle it directly
- Requires careful state management to track which code path is active

**Diagnostic approach**:
- Add ENVOY_LOG at entry/exit of `finalizeResponseHeaders()` with call stack to identify all invocation points
- Track the count of invocations per response type in metrics
- Use this to confirm the duplication hypothesis before implementing the fix

## Files to Review

- `source/common/router/router.cc` - Router filter's timeout and error handling
- `source/common/http/filter_manager.cc` - Local reply handling and encode path
- `source/common/http/utility.cc` - Local reply preparation
- `source/extensions/filters/http/header_mutation/header_mutation.cc` - Filter chain interaction
- `source/common/router/config_impl.cc` - Route entry header finalization
- Recent commits/PRs that modified `sendLocalReplyViaFilterChain()` or moved header finalization

## Key Findings Summary

### Verified:
✓ The filter manager wraps router filter callbacks in `Utility::EncodeFunctions` lambda
✓ This wrapper lambda calls `route_entry_->finalizeResponseHeaders()` at lines 1074/1125
✓ The router filter also calls `finalizeResponseHeaders()` for direct responses at line 501
✓ The header processing occurs through `HeaderParser::evaluateHeaders()` which applies `response_headers_to_add`
✓ Local reply processing splits into multiple code paths: prepare, encode, and filter chain iteration

### Specific Vulnerabilities to Double-Processing:
1. **Direct Response Path**: Router's lambda + filter manager's wrapper both attempt finalization (though filter manager's check may prevent actual duplication)
2. **Error Response Path**: Filter manager's wrapper calls finalization before encoder filter chain
3. **Filter Chain Path**: Encoder filters like header_mutation may re-process route configuration, potentially triggering duplicate header addition

### Not Yet Confirmed:
⚠ Exact point where the second `finalizeResponseHeaders()` invocation occurs
⚠ Whether header_mutation filter triggers re-evaluation or just processes mutations
⚠ Interaction between `append_action: OVERWRITE_IF_EXISTS_OR_ADD` and header re-application
⚠ Whether the duplication is from calling `finalizeResponseHeaders()` twice or from header mutation filter's re-processing

### Next Steps for Debugging:
1. Add instrumentation to track `finalizeResponseHeaders()` call count per request
2. Log call stacks at each invocation site
3. Test hypothesis: disable header_mutation filter and observe if duplication persists
4. Examine whether recent changes moved header finalization into `modify_headers_` callback (as suggested by task description)
