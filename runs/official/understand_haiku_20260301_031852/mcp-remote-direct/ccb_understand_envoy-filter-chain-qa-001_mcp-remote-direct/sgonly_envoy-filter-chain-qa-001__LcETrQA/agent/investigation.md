# Envoy HTTP Filter Chain Architecture

## Q1: Listener to Connection Manager

### Mechanism for Selecting Network Filter Chain

When a downstream TCP connection arrives, Envoy uses a hierarchical matching mechanism to select the appropriate network filter chain:

**FilterChainManager Selection** (`source/common/listener_manager/filter_chain_manager_impl.h:147-149`):
- `FilterChainManager::findFilterChain()` is called with:
  - `Network::ConnectionSocket& socket` - contains connection metadata (SNI, source IP, destination port, etc.)
  - `StreamInfo::StreamInfo& info` - contains dynamic filter state and metadata
- Returns the matched `Network::FilterChain` that contains the network-level filters

**Matching Hierarchy** (`source/common/listener_manager/filter_chain_manager_impl.h:205-216`):
The manager uses an ordered hierarchy of match criteria:
1. **Destination Port** (DestinationPortsMap): Network interface listening port
2. **Destination IP** (DestinationIPsTrie): Listener's bind address
3. **Server Name** (ServerNamesMap): SNI from TLS ClientHello
4. **Transport Protocol** (TransportProtocolsMap): TLS vs plaintext
5. **Application Protocol** (ApplicationProtocolsMap): ALPN (h2, http/1.1, etc.)
6. **Direct Source IPs** (DirectSourceIPsTrie): Direct client connection source IPs
7. **Source IPs/Ports** (SourceIPsTrie/SourcePortsMap): Firewalling rules
8. **Default Filter Chain** (fallback): If no match found

### Installation of HTTP Connection Manager as Network Filter

The HTTP Connection Manager (`ConnectionManagerImpl`) is installed as a **network-level filter**, not an HTTP filter:

**Class Hierarchy** (`source/common/http/conn_manager_impl.h:60-64`):
```cpp
class ConnectionManagerImpl : Logger::Loggable<Logger::Id::http>,
                            public Network::ReadFilter,        // ← Network-level filter
                            public ServerConnectionCallbacks,
                            public Network::ConnectionCallbacks,
                            public Http::ApiListener
```

**Network Filter Callbacks** (`source/common/http/conn_manager_impl.h:93-96`):
- `Network::FilterStatus onData(Buffer::Instance& data, bool end_stream)` - processes incoming TCP data
- `Network::FilterStatus onNewConnection()` - called when connection is established
- `void initializeReadFilterCallbacks(Network::ReadFilterCallbacks& callbacks)` - stores connection context

### What Happens in onData()

**Codec Lazy Initialization** (`source/common/http/conn_manager_impl.cc:498-505`):
When the first bytes arrive:
1. **Codec Creation** (if not already created):
   - The codec detects the HTTP protocol version from the first bytes
   - HTTP/1: identified by "GET", "POST", etc. or "HTTP/" in request line
   - HTTP/2: identified by PRI (connection preface)
   - HTTP/3: created early on connection open via `createCodec()`

2. **Dispatch Parsing** (`source/common/http/conn_manager_impl.cc:503`):
   ```cpp
   const Status status = codec_->dispatch(data);
   ```
   - Parses HTTP headers from the TCP data
   - When headers are complete, codec calls `ServerConnectionCallbacks::newStream()`

3. **Stream Creation and Filter Chain Invocation**:
   - Codec calls `newStream()` (implemented by ConnectionManager)
   - This triggers HTTP filter chain creation and processing
   - Request headers flow through decoder filters → router filter → upstream

**File References:**
- `source/common/http/conn_manager_impl.h:60-64` - ConnectionManagerImpl class declaration
- `source/common/http/conn_manager_impl.cc:148-199` - initializeReadFilterCallbacks()
- `source/common/http/conn_manager_impl.cc:498-505` - onData() codec dispatch

---

## Q2: HTTP Filter Chain Creation and Iteration

### When HTTP Filter Chain is Created

The HTTP filter chain is created lazily when the first HTTP request arrives:

**Creation Trigger** (`source/common/http/conn_manager_impl.cc:387-442`):
In `ConnectionManagerImpl::newStream()`, when the codec creates a new HTTP stream:

1. **ActiveStream Instantiation** (`source/common/http/conn_manager_impl.cc:407-408`):
   - Creates per-stream wrapper combining decoder/encoder callbacks
   - Contains embedded `DownstreamFilterManager filter_manager_` (`source/common/http/conn_manager_impl.h:457`)

2. **Filter Chain Factory Invocation** (implicit in filter_manager initialization):
   - `FilterManager::createFilterChain()` (`source/common/http/filter_manager.cc:1660-1665`)
   - Calls user-configured `FilterChainFactory::createFilterChain(FilterChainManager& manager)`
   - Factory applies filter factories via `manager.applyFilterFactoryCb()`

**File References:**
- `source/common/http/conn_manager_impl.cc:387-442` - newStream() method
- `source/common/http/filter_manager.cc:1660-1665` - createFilterChain()
- `source/common/http/filter_manager.h:34-35` - FilterManager forward declarations

### Decoder vs. Encoder Filter Invocation Order

**Decoder Filters (Request Processing)**:
1. **Headers Phase** (`source/common/http/filter_manager.cc:130-162`):
   - Called in order when `decodeHeaders()` is invoked
   - Can return: `Continue`, `StopIteration`, `StopAllIterationAndBuffer`, `StopAllIterationAndWatermark`

2. **Data Phase**:
   - Called in same order for request body chunks
   - Can buffer and stop iteration

3. **Trailers Phase**:
   - Called in order when trailers arrive

**Encoder Filters (Response Processing)**:
1. Invoked in **reverse order** of decoder filters
2. First encoder filter receives response from upstream
3. Response flows backward through filter chain

**Flow Example:**
```
Request:  Client → [Decoder1 → Decoder2 → Decoder3(Router)] → Upstream
Response: Client ← [Encoder3 ← Encoder2 ← Encoder1]         ← Upstream
```

### Return Values Control Iteration

**Filter Status Values** (`source/common/http/filter_manager.cc:130-162`):

- **`FilterHeadersStatus::Continue`**: Pass to next filter
- **`FilterHeadersStatus::StopIteration`**: Stop headers iteration, don't process body until `continueDecoding()` is called
- **`FilterHeadersStatus::StopAllIterationAndBuffer`**: Stop all iteration, buffer request body
- **`FilterHeadersStatus::StopAllIterationAndWatermark`**: Stop with watermark backpressure
- **`FilterHeadersStatus::ContinueAndDontEndStream`**: Continue but override end_stream flag

**Iteration State Machine** (`source/common/http/filter_manager.cc:50-111`):
```cpp
void ActiveStreamFilterBase::commonContinue() {
  // Resume iteration from current or next filter based on iteration_state_
  if (stoppedAll()) {
    iterate_from_current_filter_ = true;  // Resume from current filter
  }
  allowIteration();
  doHeaders(observedEndStream() && !bufferedData() && !hasTrailers());
  doData(observedEndStream() && !had_trailers_before_data);
  doTrailers();
}
```

**File References:**
- `source/common/http/filter_manager.cc:130-162` - commonHandleAfterHeadersCallback() status handling
- `source/common/http/filter_manager.cc:50-111` - commonContinue() iteration resume logic
- `source/common/http/filter_manager.h` - IterationState enum and filter status definitions

---

## Q3: Router and Upstream

### Router Cluster and Host Selection

**Route Lookup** (`source/common/router/router.cc:1-150`):
The router filter (`Router::Filter`) is the terminal HTTP decoder filter:

1. **Route Resolution**:
   - Calls `Route::routeEntry()` from the route configuration
   - Route contains cluster name, timeout, retry policy, etc.

2. **Cluster Selection** (`source/common/http/conn_manager_impl.h:296`):
   - `router_callbacks_->clusterInfo()` returns the `Upstream::ClusterInfo`
   - Provides cluster manager access

3. **Upstream Host Selection**:
   - `ClusterManager::httpConnPool()` obtains connection pool for cluster
   - Pool's load balancing algorithm selects specific host (round-robin, least request, etc.)
   - Pool returns a connection to upstream host

**File References:**
- `source/common/router/router.h:1-150` - Router filter interface
- `source/common/router/router.cc:1-150` - Router configuration

### UpstreamRequest and Upstream Filter Chain

**UpstreamRequest Creation** (`source/common/router/upstream_request.h:66-150`):
```cpp
class UpstreamRequest : public UpstreamToDownstream,
                        public GenericConnectionPoolCallbacks {
  // Manages upstream connection lifecycle
  std::unique_ptr<GenericUpstream> upstream_;
  std::unique_ptr<UpstreamFilterManager> upstream_filter_manager_;
};
```

**Upstream Filter Chain** (`source/common/router/upstream_request.h:41-65`):
- Request path: Router → `UpstreamFilterManager` → [upstream filters] → `UpstreamCodecFilter`
- `UpstreamCodecFilter` is terminal filter that sends to codec
- Response path: Codec → `UpstreamCodecFilter::CodecBridge` → upstream filters (reverse) → router

**UpstreamCodecFilter Role** (`source/common/router/upstream_codec_filter.cc:51-66`):
```cpp
Http::FilterHeadersStatus UpstreamCodecFilter::decodeHeaders(
    Http::RequestHeaderMap& headers, bool end_stream) {
  // Terminal filter: encodes headers directly to upstream codec
  const Http::Status status =
      callbacks_->upstreamCallbacks()->upstream()->encodeHeaders(headers, end_stream);
}
```

**Response Flow** (`source/common/router/upstream_codec_filter.cc:146-149`):
- Codec delivers response via `CodecBridge::decodeHeaders()`
- Flows through upstream filter manager to router
- Router passes to downstream via `RouterFilterInterface::onUpstream[X]()`

**File References:**
- `source/common/router/upstream_request.h:66-150` - UpstreamRequest class
- `source/common/router/upstream_codec_filter.cc` - Terminal upstream filter
- `source/common/http/filter_manager.h:221-263` - UpstreamStreamFilterCallbacks

### Response Flow to Downstream Client

**Encoding Phase**:
1. Router receives response via `onUpstreamHeaders()`
2. Calls `downstreamCallbacks()->encodeHeaders(response_headers, end_stream)`
3. Response flows through **encoder filters in reverse order**
4. Final encoder calls `ConnectionManager::encodeHeaders()`
5. ConnectionManager writes to response encoder → codec → client

**File References:**
- `source/common/http/conn_manager_impl.h:244-265` - FilterManagerCallbacks encode methods
- `source/common/http/filter_manager.h` - Upstream/downstream filter manager interface

---

## Q4: Architectural Boundaries

### Network Filter Chain vs HTTP Filter Chain

**Network-Level Filter Chain** (Managed by `FilterChainManager`):
- **Location**: `source/common/listener_manager/filter_chain_manager_impl.h:127-334`
- **Scope**: Per-connection, selected once at connection accept
- **Data Type**: Raw TCP bytes (`Buffer::Instance`)
- **Interface**: `Network::Filter` with `onData()`, `onNewConnection()`
- **Responsibility**:
  - Connection-level filtering (TLS, Proxy Protocol, etc.)
  - **Installs** the HTTP Connection Manager as a network filter
  - One filter chain per connection (selected at accept time)

**Example Network Filters**:
- TLS Transport Socket
- Proxy Protocol decode filter
- HTTP Connection Manager (bridge to HTTP layer)

**HTTP-Level Filter Chain** (Managed by `FilterManager`):
- **Location**: `source/common/http/filter_manager.h` and `.cc`
- **Scope**: Per-HTTP-stream (request/response pair)
- **Data Type**: HTTP headers, body, trailers, metadata
- **Interface**: `Http::StreamFilter`, `Http::StreamDecoderFilter`, `Http::StreamEncoderFilter`
- **Responsibility**:
  - Request/response filtering (routing, auth, compression, etc.)
  - Created per newStream() call by codec
  - Many filter chains per connection (one per HTTP stream)

**Example HTTP Filters**:
- Router filter (terminal decoder filter)
- Authentication filter
- Rate limit filter
- Compression filter
- Access log filter
- Upstream filters (in upstream filter chain)

### Why They Are Separate

**1. Temporal Separation**:
- Network chain: Selected at TCP connection accept (milliseconds)
- HTTP chain: Created for each HTTP stream (many per connection)
- Connection may have hundreds of streams on HTTP/2 or HTTP/3

**2. Protocol Separation**:
- Network chain: Handles transport (TLS, PROXY protocol)
- HTTP chain: Handles HTTP semantics (routing, headers, content)
- Encapsulation: Connection Manager (network filter) creates HTTP streams

**3. Data Format**:
- Network chain: Operates on raw TCP bytes
- HTTP chain: Operates on parsed HTTP objects (headers maps, body buffers)

**4. State Management**:
- Network chain: Per-connection state (ciphers, certificates, connection ID)
- HTTP chain: Per-stream state (request headers, response status, route selection)

### How They Relate

**Flow Architecture**:
```
TCP Accept → ListenerFilterChain
           → FilterChainManager::findFilterChain()
           ↓
         Network Filters (TLS, Proxy Protocol)
           ↓
         HTTP Connection Manager (Network::ReadFilter)
           ↓ (onData → codec.dispatch)
         Per-Stream Creation (newStream())
           ↓
         HTTP Filter Chain (per stream)
           ├→ Decoder Filters
           ├→ Router (terminal decoder)
           └→ Encoder Filters (reverse)
             ↓
         Upstream Connection
```

**Lifecycle Nesting**:
1. **Connection Level**: Network filter chain lifetime = TCP connection lifetime
2. **Stream Level**: HTTP filter chain lifetime = Single HTTP request/response
3. **Multiple Streams**: One network chain handles many HTTP chains

**File References**:
- Network: `source/common/listener_manager/filter_chain_manager_impl.h:127-334`
- HTTP: `source/common/http/filter_manager.h`
- Connection Manager: `source/common/http/conn_manager_impl.h:60-64`
- Bridge: `source/common/http/conn_manager_impl.cc:387-442` (newStream creates HTTP chain)

---

## Evidence

### Key Files and Locations

#### Listener and Network Filter Chain
- `source/common/listener_manager/listener_impl.h` - Listener interface
- `source/common/listener_manager/filter_chain_manager_impl.h:127-334` - Network filter chain manager
- `source/common/listener_manager/filter_chain_manager_impl.cc:513-516` - findFilterChain() implementation
- `source/common/listener_manager/active_tcp_listener.cc:80-91` - onAccept() connection handoff
- `source/common/listener_manager/active_tcp_socket.cc:1-100` - Socket handling

#### HTTP Connection Manager (Network Filter)
- `source/common/http/conn_manager_impl.h:60-64` - ConnectionManagerImpl class declaration
- `source/common/http/conn_manager_impl.h:93-96` - Network::ReadFilter interface
- `source/common/http/conn_manager_impl.cc:148-199` - initializeReadFilterCallbacks()
- `source/common/http/conn_manager_impl.cc:498-505` - onData() implementation

#### HTTP Stream Creation
- `source/common/http/conn_manager_impl.h:133-442` - ActiveStream struct definition
- `source/common/http/conn_manager_impl.cc:387-442` - newStream() creates HTTP stream + filter chain
- `source/common/http/conn_manager_impl.cc:407-408` - ActiveStream instantiation

#### HTTP Filter Chain Management
- `source/common/http/filter_manager.h` - FilterManager class (HTTP filter orchestration)
- `source/common/http/filter_manager.cc:1-200` - Filter iteration logic
- `source/common/http/filter_manager.cc:50-111` - commonContinue() iteration resume
- `source/common/http/filter_manager.cc:130-162` - commonHandleAfterHeadersCallback() status handling
- `source/common/http/filter_manager.cc:1660-1665` - createFilterChain()

#### Router Filter (Terminal Decoder Filter)
- `source/common/router/router.h:1-150` - Router filter interface
- `source/common/router/router.cc:1-150` - Router implementation
- `source/common/router/upstream_request.h:66-150` - UpstreamRequest class

#### Upstream Request and Filter Chain
- `source/common/router/upstream_request.h:41-150` - UpstreamRequest with upstream filter chain
- `source/common/router/upstream_codec_filter.cc:51-66` - UpstreamCodecFilter encodes to codec
- `source/common/router/upstream_codec_filter.cc:146-149` - CodecBridge response path
- `envoy/http/filter.h:221-263` - UpstreamStreamFilterCallbacks interface

### Critical Line References

| Concept | File | Lines | Purpose |
|---------|------|-------|---------|
| Network filter chain selection | `filter_chain_manager_impl.h` | 127-334 | FilterChainManagerImpl implementation |
| Finding correct filter chain | `filter_chain_manager_impl.cc` | 513-516 | findFilterChain() matching logic |
| ConnectionManager as network filter | `conn_manager_impl.h` | 60-64 | Class hierarchy |
| Network ReadFilter interface | `conn_manager_impl.h` | 93-96 | onData(), onNewConnection() |
| Codec dispatch on data arrival | `conn_manager_impl.cc` | 498-505 | onData() calls codec.dispatch() |
| HTTP stream creation trigger | `conn_manager_impl.cc` | 387-442 | newStream() creates ActiveStream |
| Filter chain factory invocation | `filter_manager.cc` | 1660-1665 | createFilterChain() |
| Filter iteration state machine | `filter_manager.cc` | 50-111 | commonContinue() resume logic |
| Status value handling | `filter_manager.cc` | 130-162 | commonHandleAfterHeadersCallback() |
| Router terminal filter | `router.h` | 1-150 | Router::Filter class |
| UpstreamRequest creation | `upstream_request.h` | 66-150 | Upstream request lifecycle |
| UpstreamCodecFilter terminal | `upstream_codec_filter.cc` | 51-66 | Encodes to upstream codec |
| Response codec bridge | `upstream_codec_filter.cc` | 146-149 | Response from upstream |
