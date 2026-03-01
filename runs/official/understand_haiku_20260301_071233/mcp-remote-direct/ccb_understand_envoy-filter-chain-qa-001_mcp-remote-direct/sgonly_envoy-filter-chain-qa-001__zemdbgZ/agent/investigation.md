# Envoy HTTP Filter Chain Architecture

## Q1: Listener to Connection Manager

When a downstream client opens a TCP connection to Envoy, the listener hands off the connection to the HTTP connection manager through a well-defined network filter chain mechanism:

### Connection Acceptance and Filter Chain Selection

1. **Connection Socket Creation**: The listener accepts a new TCP connection, creating a `Network::ConnectionSocket`.

2. **Filter Chain Selection**: The listener's `FilterChainManager` (specifically `FilterChainManagerImpl::findFilterChain()` at `source/common/listener_manager/filter_chain_manager_impl.h:148-149`) examines connection attributes (destination IP, destination port, server name, transport protocol, source IP, source port, etc.) to select the appropriate `FilterChain`.

3. **Network Filter Instantiation**: The selected `FilterChain` contains a list of `Network::FilterFactory` instances. The listener calls `ListenerImpl::createNetworkFilterChain()` (at `source/common/listener_manager/listener_impl.cc:942-945`) which delegates to `Configuration::FilterChainUtility::buildFilterChain()` to instantiate each network filter in order.

4. **HTTP Connection Manager Installation**: The HTTP connection manager filter (`ConnectionManagerImpl`) is instantiated as a `Network::ReadFilter` and added to the connection via the filter chain. The `ConnectionManagerImpl` class inherits from `Network::ReadFilter` (see `source/common/http/conn_manager_impl.h:60-64`).

### Data Flow in onData()

When the first bytes of HTTP data arrive on the connection:

1. **Network Layer Routing**: The network's read event dispatcher calls `ConnectionManagerImpl::onData()` (at `source/common/http/conn_manager_impl.cc:486-542`).

2. **Codec Creation**: If the codec hasn't been created yet (`!codec_`), `ConnectionManagerImpl` creates the appropriate HTTP codec (HTTP/1.x, HTTP/2, or HTTP/3) by calling `createCodec(data)` (line 496).

3. **Dispatch to Codec**: The `ConnectionManagerImpl::onData()` method calls `codec_->dispatch(data)` (line 503), which parses HTTP protocol-level data and invokes callbacks (i.e., `ServerConnectionCallbacks`) when complete messages arrive.

4. **Stream Creation**: When HTTP headers are fully parsed, the codec invokes `ServerConnectionCallbacks::newStream()`, which is implemented by `ConnectionManagerImpl::newStream()` (at `source/common/http/conn_manager_impl.cc:387-442`). This creates an `ActiveStream` object representing a single HTTP request/response.

**Key Files and Line References**:
- `source/common/http/conn_manager_impl.h:60-64` - ConnectionManagerImpl class definition as Network::ReadFilter
- `source/common/http/conn_manager_impl.cc:486-542` - ConnectionManagerImpl::onData() implementation
- `source/common/http/conn_manager_impl.cc:387-442` - ConnectionManagerImpl::newStream() creates ActiveStream
- `source/common/listener_manager/filter_chain_manager_impl.h:127-149` - FilterChainManagerImpl for network-level filter chain selection
- `source/common/listener_manager/listener_impl.cc:942-945` - ListenerImpl::createNetworkFilterChain()


## Q2: HTTP Filter Chain Creation and Iteration

The HTTP filter chain is built and iterated at the request-processing level, distinct from the network filter chain:

### Filter Chain Creation Point

The HTTP filter chain is created **when request headers are received and fully decoded**. The flow is:

1. **Codec Parses Headers**: The codec's `dispatch()` method detects complete HTTP headers and calls `ServerConnectionCallbacks::newStream()`.

2. **ActiveStream Created**: `ConnectionManagerImpl::newStream()` creates an `ActiveStream` object (line 407-408 in `source/common/http/conn_manager_impl.cc`). An `ActiveStream` wraps both a `RequestDecoder` and associated filter management.

3. **Headers Decoded**: When headers are available, `ActiveStream::decodeHeaders()` is called (from codec callbacks). This method:
   - Sets up request tracing and routing information
   - Calls `filter_manager_.createDownstreamFilterChain()` (at `source/common/http/conn_manager_impl.cc:1402-1403`)
   - This instantiates all HTTP decoder filters via the filter factory

4. **Filter Chain Structure**:
   - **Decoder Filters**: Configured filters are instantiated in order and stored in `StreamDecoderFilters::entries_` (a vector, see `source/common/http/filter_manager.h:73-81`). When iterating, decoder filters are called A → B → C (forward order).
   - **Encoder Filters**: The same filter instances are also registered as encoder filters, but stored in reverse (using `reverse_iterator` in `StreamEncoderFilters`, lines 92-100). When iterating, encoder filters are called C → B → A (reverse order).

### Filter Iteration and Control Flow

**Decoder Filter Chain Iteration** (request path):

1. `FilterManager::decodeHeaders()` is called after HTTP filter chain is created (line 1439 in `source/common/http/conn_manager_impl.cc`)

2. The filter manager iterates through decoder filters in order:
   - Calls `ActiveStreamDecoderFilter::decodeHeaders()` on each filter
   - Each filter processes headers and returns a `FilterHeadersStatus`

**Return Values Control Iteration**:

- `FilterHeadersStatus::Continue` - Continue to next filter
- `FilterHeadersStatus::StopIteration` - Halt iteration, wait for continued processing via `continueDecoding()`
- `FilterHeadersStatus::StopAllIteration` - Stop all filter processing until filter explicitly calls continue

**Encoder Filter Chain Iteration** (response path):

1. When upstream response headers arrive, they're passed to `FilterManager::encodeHeaders()`
2. Encoder filters are iterated in **reverse order** (C → B → A)
3. The router filter forwards the response back through encoders before reaching the downstream client

**Key Files and Line References**:
- `source/common/http/conn_manager_impl.cc:1402-1403` - createDownstreamFilterChain() call point
- `source/common/http/conn_manager_impl.cc:1439` - filter_manager_.decodeHeaders() call
- `source/common/http/filter_manager.h:73-100` - StreamDecoderFilters and StreamEncoderFilters structures
- `source/common/http/filter_manager.h:109-150` - ActiveStreamFilterBase with filter control logic
- `envoy/http/filter.h:902-904` - StreamDecoderFilter interface definition


## Q3: Router and Upstream

The router filter (the terminal HTTP decoder filter) forwards requests to upstream servers through a multi-stage process:

### Route Selection and Upstream Host Resolution

1. **Route Lookup**: The router filter (`Router::Filter`, which inherits from `Http::StreamDecoderFilter` at `source/common/router/router.h:308-311`) receives decoded request headers.

2. **Cluster Selection**: The route (obtained from the routing table) specifies a target cluster. The router filter uses `Upstream::ClusterManager` to obtain a reference to the cluster.

3. **Upstream Host Selection**: The router invokes cluster's load balancer to select a specific upstream host from available healthy hosts.

4. **Connection Pool Acquisition**: The router requests a connection pool from the cluster manager for the selected cluster. This returns a `GenericConnPool` (either HTTP connection pool or TCP connection pool depending on the route's cluster configuration).

### UpstreamRequest Creation and Request Forwarding

1. **UpstreamRequest Instantiation**: When the connection pool is ready (or immediately if already available), the router creates an `UpstreamRequest` object (at `source/common/router/router.cc:845-847`):
   ```cpp
   UpstreamRequestPtr upstream_request = std::make_unique<UpstreamRequest>(
       *this, std::move(generic_conn_pool), can_send_early_data, can_use_http3,
       allow_multiplexed_upstream_half_close_);
   ```

2. **Header Forwarding**: The `UpstreamRequest` is added to the router's list of upstream requests, and `UpstreamRequest::acceptHeadersFromRouter(end_stream)` is called (line 849), which forwards the request headers to the upstream connection.

3. **Upstream Filter Chain**: The `UpstreamRequest` manages its own filter chain via `UpstreamFilterManager` (referenced in the UpstreamRequest comments at `source/common/router/upstream_request.h:41-65`). Request data flows through this filter chain before being encoded to the upstream wire format by the `UpstreamCodecFilter`.

### Response Flow Back Through Filter Chain

1. **Upstream Response Reception**: When the upstream server responds, the `UpstreamCodecFilter` receives the response headers/data and passes them to the `UpstreamFilterManager`.

2. **Upstream to Downstream Bridge**: The upstream filter chain processes response data (via `UpstreamCodecFilter` at `source/common/router/upstream_codec_filter.h:28-30`) and passes it back to the router through `UpstreamRequest`'s response decoder interface.

3. **Router Encodes Response**: The router filter receives the upstream response and encodes it back through the **downstream** HTTP encoder filter chain (in reverse order) so other encoder filters can modify the response before it reaches the downstream client.

4. **ResponseEncoder Forwarding**: Finally, the response is sent to the `ResponseEncoder` which forwards it to the downstream client codec.

**Key Files and Line References**:
- `source/common/router/router.h:308-311` - Router::Filter class definition as StreamDecoderFilter
- `source/common/router/router.cc:845-847` - UpstreamRequest creation with connection pool
- `source/common/router/router.cc:849` - acceptHeadersFromRouter() call
- `source/common/router/upstream_request.h:66-124` - UpstreamRequest class definition
- `source/common/router/upstream_request.h:80-83` - acceptHeadersFromRouter, acceptDataFromRouter methods
- `source/common/router/upstream_codec_filter.h:28-30` - UpstreamCodecFilter for codec interaction
- `source/common/router/upstream_request.h:41-65` - Documentation of upstream request flow


## Q4: Architectural Boundaries

Envoy maintains two distinct but interconnected filter chain concepts at different layers:

### Network-Level Filter Chain (Network Layer)

**Purpose**: Process raw bytes at the TCP/UDP connection level before HTTP parsing.

**Management**:
- Managed by `FilterChainManager` interface and implemented by `FilterChainManagerImpl` (at `source/common/listener_manager/filter_chain_manager_impl.h:127-149`)
- Created and selected by the listener via `ListenerImpl::createNetworkFilterChain()` (at `source/common/listener_manager/listener_impl.cc:942-945`)
- Filters implement `Network::ReadFilter` and `Network::WriteFilter` interfaces

**Filters in This Chain**:
- TLS termination filters
- Proxy Protocol filters
- Rate limiting filters
- Any protocol-agnostic network filters
- **HTTP Connection Manager** - acts as the bridge between network and HTTP layers

**Selection Mechanism**:
- Connection attributes (destination IP/port, server name, source IP/port, etc.) are matched against filter chain match criteria in `FilterChainManagerImpl::findFilterChain()` (line 148-149)
- The matching process uses a complex trie structure (DestinationPortsMap, ServerNamesMap, etc. at lines 205-216)

### HTTP-Level Filter Chain (HTTP Application Layer)

**Purpose**: Process HTTP requests/responses after headers have been parsed.

**Management**:
- Managed by `FilterManager` and `DownstreamFilterManager` (in `source/common/http/filter_manager.h`)
- Created per-stream in `FilterManager::createDownstreamFilterChain()` (at `source/common/http/filter_manager.cc:1086-1087`)
- Filters implement `Http::StreamDecoderFilter` and `Http::StreamEncoderFilter` interfaces

**Filters in This Chain**:
- Router filter (forwards to upstream)
- Authentication/Authorization filters
- Request transformation filters (headers, body mutation)
- Custom application-specific filters

**Iteration**:
- **Decoder chain**: Processes requests in configured order (A → B → C)
- **Encoder chain**: Processes responses in **reverse** order (C → B → A)
- Both implemented using the same filter objects with different iteration directives

### Architectural Separation and Relationship

**Why They're Separate**:

1. **Protocol Independence**: Network filters don't know about HTTP; they work with any TCP/UDP protocol. The HTTP Connection Manager is the only network filter that understands HTTP.

2. **Filter Type Boundaries**: Network filters operate at Connection level; HTTP filters operate at Stream level. A single connection may have multiple streams (HTTP/2, HTTP/3), each with its own HTTP filter chain.

3. **Selection Criteria**: Network filter chains are selected based on connection socket properties before any data is read; HTTP filter chains are created per-request based on HTTP-level properties (route, headers, etc.).

4. **Multiple Instantiation**: The network filter chain exists once per connection. The HTTP filter chain is instantiated once per HTTP request/stream. A single connection may go through the HTTP filter chain multiple times for different requests.

**How They Relate**:

1. **Sequential Handoff**: Data flows:
   - Client → Network (TCP)
   - Network Filter Chain (TLS, etc.)
   - **HTTP Connection Manager** (network filter that bridges layers)
   - HTTP Codec parses bytes
   - HTTP Filter Chain (Router, Auth, etc.)
   - Upstream HTTP Codec
   - Upstream Network

2. **Callbacks**: The HTTP Connection Manager implements `Network::ReadFilter::onData()` (at `source/common/http/conn_manager_impl.cc:486`) and `ServerConnectionCallbacks` interface. When the codec detects complete HTTP messages, it calls back to the HTTP Connection Manager, which then creates HTTP filter chains for each stream.

3. **Watermarking**: Network-level flow control (connection high/low watermarks) is communicated to the HTTP stream filters via the HTTP Connection Manager, which updates per-stream watermarks.

**Key Files and Line References**:
- `source/common/listener_manager/filter_chain_manager_impl.h:127-149` - Network FilterChainManagerImpl
- `source/common/listener_manager/listener_impl.h:200-203` - ListenerImpl as both ListenerConfig and FilterChainFactory
- `source/common/listener_manager/listener_impl.cc:942-945` - Network filter chain creation
- `source/common/http/filter_manager.h:34-40` - HTTP FilterManager and DownstreamFilterManager declarations
- `source/common/http/filter_manager.h:73-100` - HTTP decoder/encoder filter chain structures
- `source/common/http/conn_manager_impl.h:60-64` - ConnectionManagerImpl as Network::ReadFilter
- `source/common/http/conn_manager_impl.cc:486-542` - onData() bridges network and HTTP
- `source/common/http/conn_manager_impl.cc:387-442` - newStream() creates HTTP filter chains


## Evidence

**Network-Level Components**:
- `envoy/network/filter.h` - FilterChainManager and FilterChainFactory interfaces
- `source/common/listener_manager/filter_chain_manager_impl.h` - FilterChainManagerImpl implementation
- `source/common/listener_manager/listener_impl.h:200-203, 280-281, 342-347` - ListenerImpl as network layer manager
- `source/common/listener_manager/listener_impl.cc:942-945` - createNetworkFilterChain() implementation

**HTTP Connection Manager (Bridge)**:
- `source/common/http/conn_manager_impl.h:60-64` - ConnectionManagerImpl as Network::ReadFilter
- `source/common/http/conn_manager_impl.cc:102-107` - ConnectionManagerImpl constructor
- `source/common/http/conn_manager_impl.cc:486-542` - onData() implementation
- `source/common/http/conn_manager_impl.cc:387-442` - newStream() and ActiveStream creation

**HTTP-Level Components**:
- `envoy/http/filter.h:902-904` - StreamDecoderFilter interface
- `source/common/http/filter_manager.h:34-40` - FilterManager and DownstreamFilterManager
- `source/common/http/filter_manager.h:73-100` - StreamDecoderFilters and StreamEncoderFilters
- `source/common/http/filter_manager.cc:1086-1087` - createDownstreamFilterChain() implementation
- `source/common/http/conn_manager_impl.cc:1402-1403` - createDownstreamFilterChain() call in decodeHeaders

**Router and Upstream**:
- `source/common/router/router.h:200-311` - FilterConfig and Router::Filter classes
- `source/common/router/router.cc:845-847` - UpstreamRequest creation
- `source/common/router/upstream_request.h:66-124` - UpstreamRequest implementation
- `source/common/router/upstream_codec_filter.h:28-30` - UpstreamCodecFilter
