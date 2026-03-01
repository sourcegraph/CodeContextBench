# Investigation Report: Duplicate Response Headers in Envoy Filter Pipeline

## Summary

Response headers configured via `response_headers_to_add` in route configuration are being duplicated when the router filter generates local replies (e.g., upstream timeout, connection failure). The root cause is that `finalizeResponseHeaders()` is invoked twice during local reply processing: once from a header modification lambda in `DownstreamFilterManager::sendLocalReplyViaFilterChain()` and again from the router's `modify_headers_` callback that is passed to the same function.

## Root Cause

**Primary Issue**: Double invocation of `route_entry_->finalizeResponseHeaders()` during local reply header finalization.

**File**: `source/common/http/filter_manager.cc` lines 1123-1129
**Secondary Location**: `source/common/router/router.cc` line 453

When a local reply is sent via the filter chain, `DownstreamFilterManager::sendLocalReplyViaFilterChain()` creates a header modification lambda that calls `route_entry_->finalizeResponseHeaders()` AND invokes a second `modify_headers_` callback which itself calls `finalizeResponseHeaders()`. This causes header addition logic to execute twice on the same headers object.

## Evidence

### Code Path 1: Router Filter Sets Up modify_headers_ Callback
**File**: `source/common/router/router.cc` lines 444-461

```cpp
modify_headers_ = [this](Http::ResponseHeaderMap& headers) {
  if (route_entry_ == nullptr) {
    return;
  }

  if (modify_headers_from_upstream_lb_) {
    modify_headers_from_upstream_lb_(headers);
  }

  route_entry_->finalizeResponseHeaders(headers, callbacks_->streamInfo());  // LINE 453

  if (attempt_count_ == 0 || !route_entry_->includeAttemptCountInResponse()) {
    return;
  }
  headers.setEnvoyAttemptCount(attempt_count_);
};
```

The `modify_headers_` lambda is created during `decodeHeaders()` and is intended to finalize response headers. It's passed to `sendLocalReply()` when the router generates local replies (e.g., lines 522, 550, 750, 931 of router.cc).

### Code Path 2: Filter Manager Creates Additional Lambda Wrapping modify_headers_
**File**: `source/common/http/filter_manager.cc` lines 1109-1145

```cpp
void DownstreamFilterManager::sendLocalReplyViaFilterChain(
    bool is_grpc_request, Code code, absl::string_view body,
    const std::function<void(ResponseHeaderMap& headers)>& modify_headers,
    bool is_head_request,
    const absl::optional<Grpc::Status::GrpcStatus> grpc_status,
    absl::string_view details) {
  ENVOY_STREAM_LOG(debug, "Sending local reply with details {}", *this, details);
  ASSERT(!filter_manager_callbacks_.responseHeaders().has_value());

  createDownstreamFilterChain();

  Utility::sendLocalReply(
      state_.destroyed_,
      Utility::EncodeFunctions{
          [this, modify_headers](ResponseHeaderMap& headers) -> void {
            if (streamInfo().route() && streamInfo().route()->routeEntry()) {
              streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers,
                                                                          streamInfo());  // FIRST CALL
            }
            if (modify_headers) {
              modify_headers(headers);  // SECOND CALL (via router's modify_headers_ lambda)
            }
          },
          // ... other callbacks ...
      },
      Utility::LocalReplyData{is_grpc_request, code, body, grpc_status, is_head_request});
}
```

The lambda created at lines 1123-1129:
1. **Line 1125**: Calls `route_entry_->finalizeResponseHeaders()` directly (FIRST invocation)
2. **Line 1128**: Calls the `modify_headers` callback parameter, which is the router's `modify_headers_` lambda (SECOND invocation of `finalizeResponseHeaders()`)

### Code Path 3: Lambda is Applied to Headers
**File**: `source/common/http/utility.cc` lines 709-720

```cpp
Utility::PreparedLocalReplyPtr Utility::prepareLocalReply(
    const EncodeFunctions& encode_functions,
    const LocalReplyData& local_reply_data) {
  // ... header creation ...
  ResponseHeaderMapPtr response_headers{createHeaderMap<ResponseHeaderMapImpl>(
      {{Headers::get().Status, std::to_string(enumToInt(response_code))}})};

  if (encode_functions.modify_headers_) {
    encode_functions.modify_headers_(*response_headers);  // Lambda invoked HERE
  }
  // ... rest of preparation ...
}
```

The `modify_headers_` callback (which is the lambda from `sendLocalReplyViaFilterChain`) is invoked on the response headers at line 719, triggering BOTH calls to `finalizeResponseHeaders()` on the same headers object.

### Code Path 4: Header Parser Applies response_headers_to_add
**File**: `source/common/router/config_impl.cc` lines 942-950

```cpp
void RouteEntryImplBase::finalizeResponseHeaders(Http::ResponseHeaderMap& headers,
                                                 const StreamInfo::StreamInfo& stream_info) const {
  for (const HeaderParser* header_parser : getResponseHeaderParsers(
           /*specificity_ascend=*/vhost_->globalRouteConfig().mostSpecificHeaderMutationsWins())) {
    // Later evaluated header parser wins.
    header_parser->evaluateHeaders(headers, {stream_info.getRequestHeaders(), &headers},
                                   stream_info);
  }
}
```

`finalizeResponseHeaders()` iterates through all configured response header parsers (from route, virtual host, and global configuration) and calls `evaluateHeaders()` on each.

### Code Path 5: Header Addition Logic
**File**: `source/common/router/header_parser.cc` lines 173-212

When `header_parser->evaluateHeaders()` is called:

```cpp
for (const auto& [key, entry] : headers_to_add_) {
  absl::string_view value;
  // ... value formatting ...
  if (!value.empty() || entry->add_if_empty_) {
    switch (entry->append_action_) {
    case HeaderValueOption::APPEND_IF_EXISTS_OR_ADD:
      headers_to_add.emplace_back(key, value);
      break;
    case HeaderValueOption::ADD_IF_ABSENT:
      if (auto header_entry = headers.get(key); header_entry.empty()) {
        headers_to_add.emplace_back(key, value);
      }
      break;
    case HeaderValueOption::OVERWRITE_IF_EXISTS:
      if (headers.get(key).empty()) {
        break;
      }
      FALLTHRU;
    case HeaderValueOption::OVERWRITE_IF_EXISTS_OR_ADD:
      headers_to_overwrite.emplace_back(key, value);
      break;
    }
  }
}

// First overwrite all headers which need to be overwritten.
for (const auto& header : headers_to_overwrite) {
  headers.setReferenceKey(header.first, header.second);
}

// Now add headers which should be added.
for (const auto& header : headers_to_add) {
  headers.addReferenceKey(header.first, header.second);
}
```

Headers configured with `APPEND_IF_EXISTS_OR_ADD` (the default) are added via `headers.addReferenceKey()`, which appends to existing values. When `evaluateHeaders()` is called twice (due to double `finalizeResponseHeaders()` invocation), headers are appended twice.

## Affected Components

The issue affects the interaction of multiple packages:

1. **`source/common/router/router.cc`**: Creates `modify_headers_` lambda during request decoding
2. **`source/common/http/filter_manager.cc`**: Creates additional wrapper lambda in `sendLocalReplyViaFilterChain()` that calls both `finalizeResponseHeaders()` AND the passed `modify_headers_` callback
3. **`source/common/http/utility.cc`**: Invokes the combined lambda during local reply preparation
4. **`source/common/router/config_impl.cc`**: `finalizeResponseHeaders()` implementation
5. **`source/common/router/header_parser.cc`**: `HeaderParser::evaluateHeaders()` applies header additions
6. **`api/envoy/config/core/v3/base.proto`**: `HeaderValueOption` proto defines `append_action` enum with default `APPEND_IF_EXISTS_OR_ADD`

## Causal Chain

1. **Symptom**: Response headers appear duplicated in local reply responses (e.g., `x-custom-trace: abc123` appears twice)

2. **Access Log Evidence**: Response headers show duplicate entries for headers configured via `response_headers_to_add` when `response_code_details` indicates a local reply (e.g., `upstream_response_timeout`, `cluster_not_found`)

3. **Initial Hop**: Router filter calls `sendLocalReply()` with `modify_headers_` callback (router.cc:522, 550, 750, 931)

4. **Intermediate Hop 1**: Filter manager's `sendLocalReplyViaFilterChain()` is invoked

5. **Intermediate Hop 2**: A new lambda is created that:
   - Calls `route_entry_->finalizeResponseHeaders()` (first call)
   - Calls the `modify_headers_` callback parameter (second call, which calls `finalizeResponseHeaders()` again)

6. **Intermediate Hop 3**: This lambda is passed to `Utility::sendLocalReply()`

7. **Intermediate Hop 4**: `prepareLocalReply()` invokes the lambda on the response headers, triggering both calls to `finalizeResponseHeaders()`

8. **Intermediate Hop 5**: `finalizeResponseHeaders()` iterates through all response header parsers and calls `evaluateHeaders()` on each

9. **Root Cause**: `evaluateHeaders()` is called twice for each header parser on the same headers object. Headers configured with the default `append_action: APPEND_IF_EXISTS_OR_ADD` are appended via `addReferenceKey()`, resulting in duplicate entries. Even headers with `OVERWRITE_IF_EXISTS_OR_ADD` may be affected if there are multiple header parsers at different specificity levels (route vs. virtual host vs. global) that add the same header.

10. **Downstream Effect**: The duplicate headers are included in the HTTP response sent to the client and appear in access logs

## Role of Proto Configuration

**File**: `api/envoy/config/core/v3/base.proto`

The `HeaderValueOption` message defines:

```proto
message HeaderValueOption {
  enum HeaderAppendAction {
    APPEND_IF_EXISTS_OR_ADD = 0;  // DEFAULT
    ADD_IF_ABSENT = 1;
    OVERWRITE_IF_EXISTS_OR_ADD = 2;
    OVERWRITE_IF_EXISTS = 3;
  }

  HeaderValue header = 1;

  // DEPRECATED field:
  google.protobuf.BoolValue append = 2 [deprecated = true];

  // Current field:
  HeaderAppendAction append_action = 3;
}
```

When headers are processed in `header_parser.cc` lines 58-71:
- If the deprecated `append` field is set, it overrides `append_action`
- If only `append_action` is set, it is used directly
- **Proto default**: If neither is set, `append_action` defaults to `APPEND_IF_EXISTS_OR_ADD` (enum value 0)

This is critical because:
1. Headers with default `APPEND_IF_EXISTS_OR_ADD` get duplicated when `evaluateHeaders()` runs twice
2. Even explicitly-configured `OVERWRITE_IF_EXISTS_OR_ADD` headers can be duplicated if there are multiple header parsers at different specificity levels (each one adds its own copy, and calling `finalizeResponseHeaders()` twice means each parser runs twice)

## Filter Manager's Encode Path

**File**: `source/common/http/filter_manager.cc` lines 1244-1333

The `FilterManager::encodeHeaders()` function:
1. Iterates through the encoder filter chain in reverse order (line 1257)
2. Calls each filter's `encodeHeaders()` method (line 1265)
3. Invokes the downstream filter callback at line 1324

This is a separate concern from the duplicate `finalizeResponseHeaders()` issue, but important to understand the complete flow:
- During local reply processing, headers are already finalized with duplicates before `encodeHeaders()` is called
- Encoder filters see headers that have already been duplicated
- The header mutation filter (`source/extensions/filters/http/header_mutation/`) would see and process the already-duplicated headers

## Recommendation

**Fix Strategy**:

The issue requires removing one of the duplicate calls to `finalizeResponseHeaders()`. Two approaches are possible:

### Option A: Remove First Call (Preferred)
In `source/common/http/filter_manager.cc` lines 1123-1129, remove the direct call to `finalizeResponseHeaders()`:
```cpp
[this, modify_headers](ResponseHeaderMap& headers) -> void {
  // REMOVE: if (streamInfo().route() && streamInfo().route()->routeEntry()) {
  // REMOVE:   streamInfo().route()->routeEntry()->finalizeResponseHeaders(headers, streamInfo());
  // REMOVE: }
  if (modify_headers) {
    modify_headers(headers);  // This already calls finalizeResponseHeaders()
  }
},
```

This allows the router's `modify_headers_` callback to be the single point of finalization. However, ensure that `modify_headers` is always provided and that it always calls `finalizeResponseHeaders()`.

### Option B: Remove Second Call
In the router's `modify_headers_` lambda (router.cc lines 444-461), make the call to `finalizeResponseHeaders()` conditional or move it elsewhere. However, this would require ensuring `modify_headers_` is still called for upstream response paths.

**Diagnostic Steps**:

1. Add logging to `finalizeResponseHeaders()` in `source/common/router/config_impl.cc` to trace when it's called and from which code paths
2. In local reply scenarios, confirm that `finalizeResponseHeaders()` is being called twice on the same headers object
3. Verify the behavior difference between:
   - Local reply code path (where duplication occurs)
   - Upstream response code path (where it does not occur)
4. Test with various `append_action` configurations to confirm headers with `APPEND_IF_EXISTS_OR_ADD` (default) are affected most severely

**Related Files to Review**:
- `source/common/http/filter_manager.h`: Interface definitions
- `source/common/router/router.h`: Filter interface, `modify_headers_` member
- `source/common/http/codes.h`: HTTP status codes and response flag definitions
