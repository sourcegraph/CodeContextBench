# Envoy HTTP Filter Chain Architecture

## Q1: Listener to Connection Manager

### Connection Handoff Mechanism

When a downstream client opens a TCP connection to Envoy, the listener accepts the connection and hands it off to the HTTP connection manager through the **network filter chain selection and installation process**:

**1. Filter Chain Selection (Network-Level)**

The incoming connection's network properties (destination port, destination IP, source IP, source port, SNI, transport protocol, etc.) are matched against configured filter chains:

- **File**: `source/common/listener_manager/filter_chain_manager_impl.h` (lines 127-149)
- **Key Method**: `FilterChainManagerImpl::findFilterChain(const Network::ConnectionSocket& socket, const StreamInfo::StreamInfo& info)` (line 148-149)
- This method uses hierarchical tries and matcher logic to select the appropriate `Network::FilterChain` based on connection socket properties
- The filter chain match is performed before protocol negotiation

**2. Connection Manager Installation**

The HTTP connection manager (`ConnectionManagerImpl`) is installed as a `Network::ReadFilter` (the first network filter) in the selected filter chain:

- **File**: `source/common/http/conn_manager_impl.h` (lines 60-64)
- `ConnectionManagerImpl` implements `Network::ReadFilter`, `ServerConnectionCallbacks`, and `Network::ConnectionCallbacks`
- It's configured in the network filter factories list during listener initialization
- The connection manager operates as a network filter that intercepts all data from the downstream connection

**3. onData() Handler - Initial Request Processing**

When the first bytes arrive on the connection, `onData()` is invoked:

- **File**: `source/common/http/conn_manager_impl.cc` (lines 486-542)
- **Key Logic**:
  - Line 488: Lazily creates the HTTP codec if not already created: `if (!codec_) createCodec(data);`
  - Line 503: Dispatches data through the codec: `codec_->dispatch(data)`
  - The codec's dispatch method parses the HTTP protocol and invokes callbacks on `ServerConnectionCallbacks` (which the connection manager implements)
  - These callbacks trigger `newStream()` for each HTTP request

### newStream() Callback - Stream Creation

When the HTTP codec decodes the first request headers, it invokes the `ServerConnectionCallbacks::onNewHeaders()`:

- **File**: `source/common/http/conn_manager_impl.cc` (lines 387-442)
- **Method**: `ConnectionManagerImpl::newStream(ResponseEncoder& response_encoder, bool is_internally_created)`
- Creates a new `ActiveStream` object that wraps the HTTP stream lifecycle
- The `ActiveStream` contains a `FilterManager` (line 821-828) that will manage the HTTP filter chain
- The stream is added to the connection manager's stream list and returned to the codec as a request decoder

---

## Q2: HTTP Filter Chain Creation and Iteration

### Filter Chain Creation Timing

The HTTP filter chain is created **lazily** when headers are first decoded:

- **Trigger**: `ActiveStream::decodeHeaders()` in `source/common/http/conn_manager_impl.cc` (line 1193)
- **Creation Point**: `filter_manager_.requestHeadersInitialized()` (line 1206)
- **Lazy Creation Rationale**: Filters are only instantiated when the stream processing actually begins, allowing for overload shedding and early error handling without filter overhead

### Filter Chain Instantiation

The actual filter chain is created in `FilterManager::createFilterChain()`:

- **File**: `source/common/http/filter_manager.cc` (lines 1660-1703)
- **Key Step** (line 1701): `filter_chain_factory.createFilterChain(*this, options)`
  - The `FilterChainFactory` is provided by the connection manager's config: `connection_manager_.config_->filterFactory()` (line 824 in conn_manager_impl.cc)
  - It instantiates all configured HTTP filters from the `http_filters` configuration
  - Each filter becomes either an `ActiveStreamDecoderFilter` or `ActiveStreamEncoderFilter` (or both)

**Filter Lists**:
- **Decoder Filters**: `std::vector<ActiveStreamDecoderFilterPtr> entries_` in `StreamDecoderFilters` (line 80)
- **Encoder Filters**: `std::vector<ActiveStreamEncoderFilterPtr> entries_` in `StreamEncoderFilters` (line 99)

### Decoder Filter Chain Iteration

Decoder filters are invoked in **forward order** (A → B → C):

- **File**: `source/common/http/filter_manager.cc` (lines 537-623 for `decodeHeaders`)
- **Key Logic**:
  - Line 555: `FilterHeadersStatus status = (*entry)->decodeHeaders(headers, (*entry)->end_stream_);`
  - Loop iterates forward through `decoder_filters_.begin()` to `decoder_filters_.end()`
  - Each filter's `decodeHeaders()` is called in sequence

### Encoder Filter Chain Iteration

Encoder filters are invoked in **reverse order** (C → B → A):

- **File**: `source/common/http/filter_manager.h` (lines 92-100)
- **Design**: Uses reverse iterators: `Iterator begin() { return entries_.rbegin(); }` and `end() { return entries_.rend(); }`
- **Rationale**: Response data flows backward through the filter stack, so the last filter to see the request headers is the first to process the response
- **File**: `source/common/http/filter_manager.cc` (lines 1225-1305 for `encodeHeaders`)

### Filter Return Values and Control

Filters control chain iteration through return status values:

- **File**: `envoy/http/filter.h` (filter interface definitions)
- **Common Return Values**:

  | Status | Behavior |
  |--------|----------|
  | `FilterHeadersStatus::Continue` | Iteration continues to next filter (lines 150-153) |
  | `FilterHeadersStatus::StopIteration` | Stop current iteration; continue on next frame (lines 136-138) |
  | `FilterHeadersStatus::StopAllIterationAndBuffer` | Stop all iteration and buffer data (lines 139-141) |
  | `FilterHeadersStatus::StopAllIterationAndWatermark` | Stop and apply backpressure watermarks (lines 142-143) |

- **Data Frame Returns**:
  - `FilterDataStatus::Continue`
  - `FilterDataStatus::StopIterationAndBuffer`
  - `FilterDataStatus::StopIterationAndWatermark`

- **Handling**: After each filter callback, `ActiveStreamFilterBase::commonHandleAfterHeadersCallback()` updates the iteration state (lines 130-156)

---

## Q3: Router and Upstream

### Route Matching

The router filter (the terminal HTTP filter in the chain) matches the request to a route entry:

- **File**: `source/common/router/router.cc` (lines 445-506)
- **Mechanism**: `route_ = callbacks_->route();` (line 468)
  - `callbacks_->route()` is implemented by the HTTP connection manager's stream callbacks
  - It queries the configured route provider (static, RDS, scoped routes) to find a matching route
  - Route matching is based on path, method, headers, and other properties

### Cluster and Upstream Host Selection

After matching the route entry, the router selects an upstream host:

- **File**: `source/common/router/router.cc` (line 664)
- **Code**: `auto host_selection_response = cluster->chooseHost(this);`
  - `cluster` is obtained from `config_->cm_.getThreadLocalCluster(route_entry_->clusterName())` (line 519)
  - `chooseHost()` delegates to the **load balancer** for the selected cluster
  - The router implements `Upstream::LoadBalancerContextBase` to provide context for load balancing decisions (hash keys, metadata match criteria, retry policies, etc.)
  - Load balancing algorithm (round-robin, least request, random, maglev, ring hash, etc.) selects the specific host

### UpstreamRequest Role

The `UpstreamRequest` class manages the upstream HTTP stream lifecycle:

- **File**: `source/common/router/upstream_request.h` (lines 41-100)
- **Responsibilities**:
  - Manages the upstream connection pool
  - Forwards request headers, body, trailers, and metadata to upstream via `UpstreamFilterManager`
  - Handles response decoding from upstream
  - Manages retries, timeouts, and stream resets
  - Notifies the router filter of response events via `RouterFilterInterface` callbacks

**Upstream Filter Chain**:
- **New Architecture**: Upstream requests have their own filter chain (similar to downstream)
  - Request data flows through `UpstreamFilterManager` before being sent to upstream
  - Last filter is `UpstreamCodecFilter` which handles HTTP codec operations
  - Responses flow back through the filter chain via `CodecBridge`

### Response Flow Back Through Filter Chain

When the upstream response arrives, it flows backward through the encoder filters:

1. **Upstream Receives Response**: `UpstreamCodecFilter` receives data from upstream codec
2. **Upstream Filter Manager**: Response flows through upstream filter chain
3. **Router Callbacks**: Response reaches router filter via `RouterFilterInterface::onUpstreamHeaders()` (line 487 in router.h)
   - **File**: `source/common/router/router.cc` (line 1652)
   - Method: `Filter::onUpstreamHeaders()`
   - Sets response headers in stream info and calls `filter_manager_callbacks_.setResponseHeaders()`
4. **Downstream Encoder Filters**: Router then starts encoder filter iteration
   - **File**: `source/common/router/router.cc` (line 1793)
   - Code: `callbacks_->encodeHeaders(response_headers, end_stream);`
   - This initiates encoder filter chain (in reverse order: C → B → A)
5. **Final Encoding**: Last encoder filter calls `filter_manager_callbacks_.encodeHeaders()` which sends headers to downstream client

**Data Flow**:
- Headers: `onUpstreamHeaders()` → `encodeHeaders()` → downstream
- Body: `onUpstreamData()` → `encodeData()` → downstream
- Trailers: `onUpstreamTrailers()` → `encodeTrailers()` → downstream

---

## Q4: Architectural Boundaries

### Network Filter Chain (Layer 1: Transport)

**Managed by**: `FilterChainManager` and `ListenerImpl`

**Selection Mechanism**: `FilterChainManagerImpl::findFilterChain()`
- **File**: `source/common/listener_manager/filter_chain_manager_impl.h` (lines 148-250)
- Matches based on:
  - Destination port (line 216)
  - Destination IP (with trie lookup for performance) (lines 212-214)
  - Server name / SNI (from TLS) (line 210)
  - Transport protocol (line 206)
  - Application protocol (ALPN for TLS) (line 205)
  - Source IP (direct/indirect) (line 223)
  - Source port (line 226)

**Responsibilities**:
- Select transport socket factory (TLS vs plaintext)
- Install network-level filters (L4 filters)
- Apply drain decisions at connection level
- Network filter factories are created once per listener configuration change

**Network Filter Examples**:
- HTTP Connection Manager (HTTP)
- TCP Proxy (raw TCP forwarding)
- SNI/mTLS matching filters
- Listener filters (applied before connection filter chains)

### HTTP Filter Chain (Layer 2: Application)

**Managed by**: `FilterManager` (specifically `DownstreamFilterManager` for downstream)

**Creation Trigger**: First HTTP request headers decoded
- **File**: `source/common/http/filter_manager.cc` (line 1701)
- `filter_chain_factory.createFilterChain(*this, options)`

**Responsibilities**:
- Process HTTP semantic-level operations
- Headers, body, trailers, and metadata transformation
- Routing decisions (router filter)
- Load balancing and upstream connection management
- Local reply generation
- Authentication and authorization
- Rate limiting
- Request/response modification

**HTTP Filter Examples**:
- Router filter
- Local rate limit filter
- Authentication filters (JWT, OAuth)
- Transformation filters (buffer, decompression)
- Observability filters (tracing, metrics)

### Separation Rationale

1. **Protocol Layers**: Network filters work at Layer 4 (transport), HTTP filters at Layer 7 (application)
   - Network filters don't need HTTP semantics
   - HTTP filters assume valid HTTP protocol

2. **Lifecycle Differences**:
   - Network filters: One per connection, created once at listener setup
   - HTTP filters: One per request, created lazily when headers arrive

3. **Matching Scope**:
   - Network filters: Selected based on connection properties before protocol negotiation
   - HTTP filters: Applied uniformly to all HTTP requests on a connection, optionally with HTTP-level matching

4. **Performance**:
   - Network filter chain selection is optimized with tries and early termination
   - HTTP filter instantiation is deferred until actually needed

### Interaction Between Layers

1. **Connection Arrives**: Listener accepts → `FindFilterChain()` selects network filters
2. **HTTP Connection Manager Installed**: As first network filter in the chain
3. **TCP Connection Established**: `onNewConnection()` called on connection manager (line 544)
4. **First Data Arrives**: `onData()` creates codec and dispatches (line 486)
5. **HTTP Stream Created**: Codec triggers `newStream()` → creates `ActiveStream`
6. **Headers Decoded**: First `decodeHeaders()` → creates HTTP filter chain → starts decoder filter iteration
7. **Request Forwarding**: Router filter creates upstream connection (back through network filter system for upstream)
8. **Response Handling**: Upstream response → encoder filter iteration (reverse order)
9. **Response Sent**: Final filter sends to downstream connection

---

## Evidence

### Key Files and Line References

**Network Layer (FilterChainManager)**:
- `source/common/listener_manager/filter_chain_manager_impl.h`: 127-250 (FilterChainManagerImpl class definition and findFilterChain)
- `source/common/listener_manager/listener_impl.h`: 129-200 (ListenerImpl and filter chain integration)

**Connection Manager (Network Filter)**:
- `source/common/http/conn_manager_impl.h`: 55-100 (ConnectionManagerImpl header)
- `source/common/http/conn_manager_impl.cc`: 102-199 (Constructor), 381-442 (newStream method), 486-542 (onData method)

**HTTP Filter Chain Creation**:
- `source/common/http/filter_manager.h`: 34-100 (StreamDecoderFilters, StreamEncoderFilters), 1169-1210 (DownstreamFilterManager)
- `source/common/http/filter_manager.cc`: 1660-1703 (createFilterChain method)
- `source/common/http/conn_manager_impl.cc`: 820-829 (FilterManager instantiation in ActiveStream)

**Decoder Filter Iteration**:
- `source/common/http/filter_manager.cc`: 537-623 (decodeHeaders method), 638-750 (decodeData method), 796-841 (decodeTrailers method)
- `source/common/http/filter_manager.h`: 73-81 (StreamDecoderFilters definition with forward iteration)

**Encoder Filter Iteration**:
- `source/common/http/filter_manager.h`: 92-100 (StreamEncoderFilters with reverse iteration)
- `source/common/http/filter_manager.cc`: 1225-1305 (encodeHeaders method), 1401-1470 (encodeData method)

**Filter Return Values**:
- `source/common/http/filter_manager.h`: 109-151 (ActiveStreamFilterBase::commonHandleAfterHeadersCallback)
- `source/common/http/filter_manager.cc`: 113-175 (Status handling for decoder filters)

**Router Filter**:
- `source/common/router/router.h`: 308-350 (Filter class definition)
- `source/common/router/router.cc`: 445-506 (decodeHeaders), 664 (host selection), 1652-1800 (onUpstreamHeaders)

**Upstream Request**:
- `source/common/router/upstream_request.h`: 41-150 (UpstreamRequest class definition)
- `source/common/router/router.cc`: 724 (createConnPool), 905-946 (Filter::createConnPool)

**Filter Status Values**:
- `envoy/http/filter.h`: Filter interface with status enums
- `source/common/http/filter_manager.h`: 118-145 (commonHandleAfterHeadersCallback status handling)

