# Envoy HTTP Filter Chain Architecture

## Q1: Listener to Connection Manager

### Mechanism for Selecting Network Filter Chain

When a downstream client opens a TCP connection to Envoy, the connection is handled by the listener's filter chain selection mechanism:

**File: `source/common/listener_manager/active_stream_listener_base.h:85-94`**
```
void onSocketAccepted(std::unique_ptr<ActiveTcpSocket> active_socket) {
  // Create and run the filters
  if (config_->filterChainFactory().createListenerFilterChain(*active_socket)) {
    active_socket->startFilterChain();
  }
}
```

The listener first creates the **listener filter chain** using `createListenerFilterChain()`. Listener filters process the raw TCP data (e.g., TLS SNI, source IP), and based on their output, a matching mechanism determines which **network filter chain** to use.

**File: `source/common/listener_manager/filter_chain_manager_impl.h:86-100`**

The `FilterChainImpl` class holds:
- `transport_socket_factory_` - manages TLS/transport protocol
- `filters_factory_` - contains all network filters in this chain (including HTTP connection manager)

**File: `source/common/listener_manager/filter_chain_manager_impl.h:114-130`**

The `FilterChainManagerImpl` manages multiple filter chains and selects the appropriate one based on connection properties:
- SNI (Server Name Indication) from TLS handshake
- Source IP and port
- Destination IP and port
- Transport protocol

### Installation of HTTP Connection Manager

Once a network filter chain is selected, its network filters are instantiated in order. The HTTP connection manager is installed as a **network filter** in the selected filter chain.

**File: `source/common/http/conn_manager_impl.h:60-64`**
```
class ConnectionManagerImpl : Logger::Loggable<Logger::Id::http>,
                              public Network::ReadFilter,
                              public ServerConnectionCallbacks,
                              public Network::ConnectionCallbacks,
                              public Http::ApiListener {
```

The `ConnectionManagerImpl` implements `Network::ReadFilter`, making it a network-level filter that can be installed in the network filter chain.

### onData() Execution

When the first bytes arrive on the TCP connection, the network layer invokes `onData()` on each network filter in the chain.

**File: `source/common/http/conn_manager_impl.cc:486-542`**
```
Network::FilterStatus ConnectionManagerImpl::onData(Buffer::Instance& data, bool) {
  requests_during_dispatch_count_ = 0;
  if (!codec_) {
    createCodec(data);  // Line 496
  }
  const Status status = codec_->dispatch(data);  // Line 503
  // ... handle codec results ...
  return Network::FilterStatus::StopIteration;
}
```

**Key steps in `onData()`:**
1. **Line 488-496**: If no codec exists yet, create it based on protocol detection (HTTP/1.1, HTTP/2, HTTP/3)
2. **Line 503**: Call `codec_->dispatch(data)` to parse HTTP frames
3. The codec calls back to `ServerConnectionCallbacks` methods (e.g., `onNewStream()`, `onHeaders()`)
4. These callbacks trigger the HTTP stream creation and filter chain processing

**File: `source/common/http/conn_manager_impl.cc:465-484`** (createCodec implementation)

The codec is created from the configuration, and the protocol is detected from initial bytes.

---

## Q2: HTTP Filter Chain Creation and Iteration

### HTTP Filter Chain Creation Point

The HTTP filter chain is created **when request headers are fully parsed**, in the `decodeHeaders()` method of `ActiveStream`.

**File: `source/common/http/conn_manager_impl.cc:1193-1410`**

The `decodeHeaders()` function:
- **Line 1199-1202**: Records timing information
- **Line 1206**: `filter_manager_.requestHeadersInitialized()` - prepares filter manager
- **Line 1370-1402**: Mutates headers, refreshes route config, sets up tracing
- **Line 1402-1403**: Creates the HTTP filter chain:
```
const FilterManager::CreateChainResult create_chain_result =
    filter_manager_.createDownstreamFilterChain();
```

**File: `source/common/http/filter_manager.cc:1086-1087`**
```
FilterManager::CreateChainResult DownstreamFilterManager::createDownstreamFilterChain() {
  return createFilterChain(filter_chain_factory_);
}
```

**File: `source/common/http/filter_manager.cc:1661-1702`** (createFilterChain implementation)

The `createFilterChain()` method:
- **Line 1668-1675**: Sets up initialization cleanup to configure filter entries
- **Line 1689-1695**: Attempts upgrade filter chain (for WebSocket/CONNECT upgrades)
- **Line 1700-1701**: Creates the default HTTP filter chain via `filter_chain_factory.createFilterChain(*this, options)`

The filter chain factory instantiates all configured HTTP filters in order.

### Order of Decoder vs. Encoder Filters

**File: `source/common/http/filter_manager.h:66-99`**

```
// HTTP decoder filters - iterate in configured order
struct StreamDecoderFilters {
  using Iterator = std::vector<ActiveStreamDecoderFilterPtr>::iterator;
  Iterator begin() { return entries_.begin(); }    // First to last
  std::vector<ActiveStreamDecoderFilterPtr> entries_;
};

// HTTP encoder filters - iterate in REVERSE configured order
struct StreamEncoderFilters {
  using Iterator = std::vector<ActiveStreamEncoderFilterPtr>::reverse_iterator;
  Iterator begin() { return entries_.rbegin(); }   // Last to first
  std::vector<ActiveStreamEncoderFilterPtr> entries_;
};
```

**Decoder chain order (configured order):**
- Filter A → Filter B → Filter C (e.g., Router filter is last)

**Encoder chain order (reverse of configured order):**
- Filter C → Filter B → Filter A

This allows filters to wrap the response in reverse order (e.g., compression applied before stats logging).

### Filter Control Return Values

**File: `source/common/http/filter_manager.h:211-218`**

Each filter can control iteration using return status enums:

```
enum class IterationState : uint8_t {
  Continue,            // Iteration continues to next filter
  StopSingleIteration, // Stops for headers/data/trailers only
  StopAllBuffer,       // Stops all iteration, buffers following data
  StopAllWatermark,    // Stops all iteration, buffers until high watermark
};
```

**Return values from filter callbacks:**
- `FilterHeadersStatus::Continue` - pass headers to next filter
- `FilterHeadersStatus::StopIteration` - buffer and wait (filter must call `continue()`)
- `FilterHeadersStatus::StopAllIteration` - buffer all data types

**File: `source/common/http/filter_manager.cc:50-100`** (commonContinue implementation)

When a filter calls `continue()`, the `commonContinue()` method resumes iteration with proper state management.

---

## Q3: Router and Upstream

### Router's Cluster and Host Selection

The router filter is the **terminal HTTP decoder filter** that forwards requests to upstream servers.

**File: `source/common/router/router.h:308-348`**
```
class Filter : public Http::StreamDecoderFilter,
               public Upstream::LoadBalancerContextBase,
               public RouterFilterInterface {
public:
  Http::FilterHeadersStatus decodeHeaders(Http::RequestHeaderMap& headers,
                                          bool end_stream) override;
```

**Router filter decoding process:**
1. **Cluster lookup**: Uses the request headers and route configuration to find the target cluster
   - Route matching: GET /api/users → route rule → cluster name "backend"
2. **Host selection**: Load balancer selects a specific upstream host from the cluster
   - Considers: load balancing policy, health status, zone-aware routing

**File: `source/common/router/router.cc:845-849`** (UpstreamRequest creation)
```
UpstreamRequestPtr upstream_request = std::make_unique<UpstreamRequest>(
    *this, std::move(generic_conn_pool), can_send_early_data, can_use_http3,
    allow_multiplexed_upstream_half_close_);
LinkedList::moveIntoList(std::move(upstream_request), upstream_requests_);
upstream_requests_.front()->acceptHeadersFromRouter(end_stream);
```

### Role of UpstreamRequest and Upstream Filter Chain

**File: `source/common/router/upstream_request.h:41-65`**

The `UpstreamRequest` class manages the lifecycle of forwarding a request to a single upstream server:
- Manages the upstream TCP connection pool
- Creates an **upstream filter chain** (via `UpstreamFilterManager`)
- Buffers request data until the upstream connection is established

```
On the new request path:
- Data arrives via acceptHeadersFromRouter/acceptDataFromRouter
- Data is passed to UpstreamFilterManager
- UpstreamFilterManager iterates through upstream filters
- Last filter in chain is UpstreamCodecFilter (encodes to HTTP)
- If upstream not connected, UpstreamCodecFilter returns StopAllIteration
- FilterManager buffers data with watermark management

On the response path:
- Upstream data arrives via UpstreamCodecFilter's CodecBridge callback
- UpstreamFilterManager iterates filters in encode direction
- Data traverses filter chain
- UpstreamRequestFilterManagerCallbacks passes data back to router
- Router sends to downstream via HTTP encoder filters
```

**File: `source/common/router/upstream_request.h:80-97`**

Key methods for accepting data from router:
```
virtual void acceptHeadersFromRouter(bool end_stream);
virtual void acceptDataFromRouter(Buffer::Instance& data, bool end_stream);
void acceptTrailersFromRouter(Http::RequestTrailerMap& trailers);
void acceptMetadataFromRouter(Http::MetadataMapPtr&& metadata_map_ptr);

// Response decoding methods (called by upstream codec)
void decodeHeaders(Http::ResponseHeaderMapPtr&& headers, bool end_stream) override;
void decodeData(Buffer::Instance& data, bool end_stream) override;
void decodeTrailers(Http::ResponseTrailerMapPtr&& trailers) override;
```

### Response Flow Back Through Filter Chain

The response flows back through the **downstream encoder filter chain** in reverse order.

**File: `source/common/http/conn_manager_impl.h:457`**

The `ActiveStream` contains `DownstreamFilterManager filter_manager_` which manages both decoder and encoder filters.

**Response flow:**
1. UpstreamRequest receives response headers from upstream codec
2. UpstreamRequest calls router's `onUpstreamHeaders(response_headers)`
3. Router filter encodes response headers via `encodeHeaders(response_headers, end_stream)`
4. DownstreamFilterManager iterates **encoder filters in reverse order** (C → B → A)
5. Last encoder filter (first in reverse) sends response to downstream client via `response_encoder_`

**File: `source/common/http/filter_manager.h:92-98`**
```
struct StreamEncoderFilters {
  using Iterator = std::vector<ActiveStreamEncoderFilterPtr>::reverse_iterator;
  Iterator begin() { return entries_.rbegin(); }  // Reverse iteration
  std::vector<ActiveStreamEncoderFilterPtr> entries_;
};
```

---

## Q4: Architectural Boundaries

### Network-Level Filter Chain

**Managed by: `FilterChainManager` (in listener_manager)**

**File: `source/common/listener_manager/filter_chain_manager_impl.h:86-100`**

The network filter chain:
- **Scope**: TCP/connection level
- **Managed by**: `FilterChainManagerImpl` in the listener
- **Selection**: Based on SNI, source IP, destination IP, transport protocol
- **Filters**: Network filters (e.g., TLS filter, HTTP connection manager, TCP proxy)
- **Configuration**: Defined in listener config as `filter_chains[]`

Each network filter implements `Network::Filter` interface with `onData()` and `onNewConnection()`.

**File: `source/common/http/conn_manager_impl.h:60-64`**

The HTTP connection manager is itself a network filter, implementing `Network::ReadFilter`.

### HTTP-Level Filter Chain

**Managed by: `FilterManager` (in http)**

**File: `source/common/http/filter_manager.h:681-690`**

The HTTP filter chain:
- **Scope**: HTTP stream level
- **Managed by**: `DownstreamFilterManager` instance per HTTP stream (in `ActiveStream`)
- **Selection**: Based on HTTP request properties (headers, path, method)
- **Filters**: HTTP filters (decoder/encoder) like router, compression, rate limit, logging
- **Configuration**: Defined in HCM config as `http_filters[]`

Each HTTP filter implements `Http::StreamDecoderFilter` and/or `Http::StreamEncoderFilter`.

### Why They Are Separate

**1. Protocol Abstraction**
- Network filters don't understand HTTP; they operate on raw data
- HTTP filters assume HTTP parsing is complete
- Separation allows other network protocols (TCP, gRPC streaming) without HTTP

**2. Performance**
- Network filters can drop connections before expensive HTTP parsing
- Filter chain selection happens once per connection, not per request
- Encoder filters can be applied per-request after routing decisions

**3. Configuration Scope**
- Network filter chains configured per **listener**
- HTTP filter chains configured per **HTTP connection manager**
- Different listeners can have different network filters but same HCM

**4. Lifecycle**
- Network filters live for entire TCP connection
- HTTP filters created fresh for each HTTP stream
- Allows independent state management at each level

### Relationship Flow

```
TCP Connection arrives
  ↓
Listener filters (Network::Filter chain)
  ↓
Network filter chain selected (FilterChainManager matches on SNI/IP)
  ↓
Network filters instantiated (TLS, HTTP Connection Manager, etc.)
  ↓
ConnectionManagerImpl receives data via onData()
  ↓
Codec parses HTTP
  ↓
HTTP stream created (ActiveStream)
  ↓
HTTP filter chain created (DownstreamFilterManager creates filters)
  ↓
Decoder filters iterate (A → B → Router)
  ↓
Router creates UpstreamRequest with upstream filter chain
  ↓
Response flows back through encoder filters (Router → B → A)
  ↓
Response sent to client via response_encoder
```

---

## Evidence

### Key File Paths and Line References

**Listener and Network Filter Chain:**
- `source/common/listener_manager/active_stream_listener_base.h:85` - `onSocketAccepted()`
- `source/common/listener_manager/filter_chain_manager_impl.h:86` - `FilterChainImpl` class
- `source/common/listener_manager/filter_chain_manager_impl.h:114` - `FilterChainManagerImpl` class
- `source/common/listener_manager/active_tcp_listener.cc:149` - `newActiveConnection()`

**HTTP Connection Manager (Network Filter):**
- `source/common/http/conn_manager_impl.h:60` - `ConnectionManagerImpl` class
- `source/common/http/conn_manager_impl.cc:486` - `onData()` method
- `source/common/http/conn_manager_impl.cc:465` - `createCodec()` method
- `source/common/http/conn_manager_impl.cc:387` - `newStream()` method

**HTTP Stream and Filter Chain:**
- `source/common/http/conn_manager_impl.h:141` - `ActiveStream` class
- `source/common/http/conn_manager_impl.h:457` - `filter_manager_` member
- `source/common/http/conn_manager_impl.cc:1193` - `decodeHeaders()` method
- `source/common/http/conn_manager_impl.cc:1402` - `createDownstreamFilterChain()` call

**HTTP Filter Manager:**
- `source/common/http/filter_manager.h:681` - `FilterManager` class
- `source/common/http/filter_manager.h:745` - `decodeHeaders()` public method
- `source/common/http/filter_manager.h:73` - `StreamDecoderFilters` struct
- `source/common/http/filter_manager.h:92` - `StreamEncoderFilters` struct (reverse iteration)
- `source/common/http/filter_manager.cc:1661` - `createFilterChain()` method

**Router Filter:**
- `source/common/router/router.h:308` - `Filter` class
- `source/common/router/router.h:347` - `decodeHeaders()` method
- `source/common/router/router.cc:845` - `UpstreamRequest` creation

**Upstream Request:**
- `source/common/router/upstream_request.h:66` - `UpstreamRequest` class
- `source/common/router/upstream_request.h:80` - `acceptHeadersFromRouter()` method
- `source/common/router/upstream_request.h:94` - `decodeHeaders()` response method

**Filter Return Values and Iteration:**
- `source/common/http/filter_manager.h:211` - `IterationState` enum
- `source/common/http/filter_manager.cc:50` - `commonContinue()` method
