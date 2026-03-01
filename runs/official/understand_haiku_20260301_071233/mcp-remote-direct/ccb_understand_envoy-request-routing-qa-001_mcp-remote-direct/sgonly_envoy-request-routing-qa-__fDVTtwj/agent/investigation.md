# Envoy Request Routing Flow

## Q1: Listener Accept to Network Filter Chain

### Socket Accept
- **Component**: `TcpListenerImpl::onAccept()` (source/common/network/tcp_listener_impl.cc:76-83)
  - The Linux socket accept syscall is performed, returning a new file descriptor
  - This triggers the libevent callback which calls the TcpListenerImpl's onAccept method
  - The accepted socket is wrapped in a `Network::ConnectionSocket` object

### Connection Balancing
- **Component**: `ActiveTcpListener::onAccept()` (source/common/listener_manager/active_tcp_listener.cc:80-91)
  - The listener receives the accepted socket from TcpListenerImpl
  - It checks if per-listener connection limits have been reached
  - Calls `onAcceptWorker()` which may rebalance the connection to another worker thread/dispatcher using the connection balancer

### Listener Filter Chain Processing
- **Component**: `ActiveTcpSocket` (source/common/listener_manager/active_tcp_socket.h:28-107)
  - An `ActiveTcpSocket` wrapper is created for the socket with the accepted socket and any listener filters
  - `startFilterChain()` triggers `continueFilterChain(true)` to begin listener filter iteration
  - Each listener filter's `onAccept()` method is called (source/common/listener_manager/active_tcp_socket.cc:111-125)
  - If a filter returns `StopIteration`, a listener filter buffer is created to await more data or an async callback
  - When all listener filters complete (or don't require more data), `continueFilterChain(true)` is called

### Filter Chain Matching and Network Filter Instantiation
- **Component**: `ActiveStreamListenerBase::newConnection()` (source/common/listener_manager/active_stream_listener_base.cc:38-76)
  - Called after listener filters complete
  - `findFilterChain(*socket, *stream_info)` is called via config's FilterChainManager to match the filter chain based on connection properties (SNI, source IP, destination IP, etc.)
  - If no matching filter chain is found, connection is closed and logs are emitted
  - For the matching filter chain:
    - Transport socket factory creates a downstream transport socket
    - `dispatcher().createServerConnection()` is called to create a `ServerConnection` with the socket and transport socket
    - **HTTP Connection Manager (HCM) is instantiated here**: `createNetworkFilterChain()` is called with the filter chain's network filter factories
    - HCM is the first (usually only) network filter in the chain
    - Each filter's initialization happens during this call

### HCM Installation and onData Trigger
- **Component**: `ServerConnection` (source/common/network/connection_impl.h and connection_impl.cc)
  - The ServerConnection registers read callbacks on the socket via libevent
  - When data arrives on the socket, the read event fires
  - The ServerConnection calls `onData()` on its read filters (the HCM network filter)

### Summary
1. **Accept**: TcpListenerImpl accepts socket from kernel
2. **Listeners**: ActiveTcpListener → ActiveTcpSocket processes listener filters (e.g., TLS SNI inspection)
3. **Match**: ActiveStreamListenerBase finds matching FilterChain based on connection properties
4. **HCM Install**: Network filter chain is instantiated, HCM is created and registered
5. **Data Reception**: onData() is triggered when bytes arrive on socket

---

## Q2: HTTP Parsing and Filter Chain Iteration

### Codec Creation and HTTP Parsing
- **Component**: `ConnectionManagerImpl::onData()` (source/common/http/conn_manager_impl.cc)
  - Called by ServerConnection when bytes arrive on the socket
  - On first call, `codec_->onData(buffer, end_stream)` is invoked
  - The codec (HTTP/1.1, HTTP/2, or HTTP/3) parses the byte stream
  - As headers are parsed, codec calls back to ServerConnectionCallbacks::newStream()

### ActiveStream Creation
- **Component**: `ConnectionManagerImpl::newStream()` (source/common/http/conn_manager_impl.cc:387-442)
  - Called by codec when HTTP headers are decoded
  - Creates a new `ActiveStream` object with a FilterManager
  - Registers the ActiveStream as a RequestDecoder with the codec
  - Returns a ResponseEncoder for the codec to use for encoding responses
  - The RequestDecoder callback interface will receive decoded headers/body from codec

### Filter Chain Iteration - Decoder Path
- **Component**: `FilterManager` (source/common/http/filter_manager.h and filter_manager.cc)
  - When codec calls `decodeHeaders()` on the RequestDecoder, it delegates to FilterManager::decodeHeaders()
  - FilterManager maintains a list of ActiveStreamDecoderFilters
  - FilterManager iterates through decoder filters in order:
    - For each filter, calls `decodeHeaders(headers, end_stream)`
    - Filter can return `Continue`, `StopIteration`, or `StopAllIteration`
    - `Continue`: Move to next filter
    - `StopIteration`: Stop iterating, resume later when filter calls continueDecoding()
    - `StopAllIteration`: Stop and don't resume (usually means filter will send local response)
  - Router filter is the last filter in the chain

### Filter Return Values and Control Flow
- **Component**: Each filter's decode methods return `FilterHeadersStatus`, `FilterDataStatus`, etc.
  - `Continue`: FilterManager continues to next filter
  - `StopIteration`: FilterManager stops, buffer data, wait for filter to call continueDecoding()
  - `StopAllIteration`: FilterManager stops completely, filter handles response
  - Multiple data chunks may arrive; for each, `decodeData()` is called on all active decoder filters

### Summary
1. **Parse**: Codec parses bytes into HTTP protocol messages
2. **Create Stream**: ActiveStream created with FilterManager
3. **Iterate Decoders**: FilterManager calls each decoder filter in order
4. **Control Flow**: Filters control iteration via return status
5. **Buffer**: If filter stops, data is buffered and watermarks apply

---

## Q3: Route Resolution and Upstream Selection

### Route Lookup
- **Component**: `Router::Filter::decodeHeaders()` (source/common/router/router.h:347-348, source/common/router/router.cc)
  - Called by FilterManager as the last decoder filter
  - Calls `decoder_callbacks_->route()` to resolve the route
  - This queries the route table configuration to find matching route entry
  - Route table is obtained from RouteConfigProvider via the listener configuration

### Route Entry Resolution
- **Component**: `Router::RouteConstSharedPtr` (envoy/router/router.h)
  - Router calls `route->routeEntry()` to get the specific route entry
  - RouteEntry contains cluster name and routing configuration
  - Calls `route_entry_->clusterName()` to extract cluster name

### Upstream Host Selection
- **Component**: `Upstream::ClusterManager::getThreadLocalCluster()` (source/common/upstream/cluster_manager_impl.h)
  - Router obtains cluster from cluster manager by name
  - Gets the thread-local cluster object
  - `LoadBalancer::chooseHost()` is called to select a specific upstream host from the cluster
  - Load balancer uses:
    - Health information from cluster's HostSet
    - Load balancing policy (round-robin, least request, etc.)
    - Hash policy for session affinity (if configured)
    - Metadata matching criteria
    - Priority set selection

### Upstream Connection Creation Trigger
- **Component**: `Router::Filter::continueDecodeHeaders()` or `UpstreamRequest::onPoolReady()`
  - After route and host are selected, router creates an UpstreamRequest
  - UpstreamRequest calls `GenericConnPoolFactory::createGenericConnPool()`
  - Connection pool is requested with the selected host
  - Pool either returns existing connection or creates new one
  - When connection is ready, `onPoolReady()` callback is invoked

### Summary
1. **Route Lookup**: RouteConfigProvider resolves route from request headers
2. **Get Entry**: Extract RouteEntry from Route
3. **Get Cluster**: Get cluster name from RouteEntry
4. **Select Host**: LoadBalancer chooses specific host from cluster's HostSet
5. **Pool Ready**: Connection pool either reuses or creates upstream connection

---

## Q4: Upstream Connection and Data Flow

### Connection Pool and Upstream Connection
- **Component**: `GenericConnPool` / `HttpConnPool` (source/extensions/upstreams/http/http/conn_pool.h)
  - Created by GenericConnPoolFactory with selected host
  - Maintains connection pool for the specific host
  - If no available connection, creates new upstream TCP connection via Network::Dispatcher::createClientConnection()
  - Registers pool callbacks with the connection

### Upstream Request Setup
- **Component**: `UpstreamRequest` (source/common/router/upstream_request.h:66-150)
  - Created by Router::Filter when connection pool is ready
  - Wraps the upstream stream and handles request/response exchange
  - When `onPoolReady()` is called:
    - Creates `UpstreamFilterManager` for the upstream stream
    - Registers `UpstreamCodecFilter` as the last upstream filter
    - Creates upstream codec for the protocol

### Request Encoding to Upstream
- **Component**: `UpstreamRequest::acceptHeadersFromRouter()` and encoder filters
  - Router filter calls `upstream_request_->acceptHeadersFromRouter(end_stream)`
  - Request data flows through UpstreamFilterManager:
    - Each upstream decoder filter processes the data (if configured)
    - UpstreamCodecFilter receives the data
    - UpstreamCodecFilter encodes headers/body using upstream codec
    - Encoded bytes are written to upstream socket via the codec

### Response Flow Back
- **Component**: `UpstreamCodecFilter::CodecBridge` (source/common/router/upstream_codec_filter.h:54-77)
  - When upstream codec receives response, it calls response callbacks
  - CodecBridge forwards response to UpstreamFilterManager
  - UpstreamFilterManager passes response through encoder filters (in reverse order)
  - Final encoded response is passed back to Router via callbacks

### Encoder Filter Chain Invocation
- **Component**: `FilterManager::encodeHeaders()` and encoder filters (source/common/http/filter_manager.cc)
  - Called when response is ready from upstream
  - FilterManager iterates through encoder filters in reverse order of decoder execution
  - Each encoder filter can modify headers before sending downstream
  - Last encoder filter writes to response encoder (connected to downstream codec)
  - Response is encoded downstream via ResponseEncoder::encodeHeaders()

### Decoder vs Encoder Filter Chain Timing
- **Decoder Filters**: Called when request travels from downstream → upstream
  - Called in the order filters are configured
  - Example: auth filter → router filter
- **Encoder Filters**: Called when response travels from upstream → downstream
  - Called in REVERSE order of decoder filters
  - Example: router filter's response handling → auth filter → compression
  - This allows filters to unwrap/undo transformations made during decoding

### Summary
1. **Pool Ready**: Connection pool provides or creates upstream socket
2. **Encode Request**: UpstreamCodecFilter encodes request headers/body to upstream protocol
3. **Write Socket**: Encoded bytes written to upstream socket
4. **Response Arrive**: Upstream codec decodes response
5. **Encoder Chain**: Response flows through encoder filters (reverse order)
6. **Write Downstream**: Response written to downstream client via ResponseEncoder

---

## Evidence

### Q1: Listener Accept References
- `source/common/network/tcp_listener_impl.cc`: TcpListenerImpl::onAccept() - socket accept
- `source/common/listener_manager/active_tcp_listener.cc:80-91`: onAccept() handling and rebalancing
- `source/common/listener_manager/active_tcp_listener.cc:108-130`: onAcceptWorker() - listener creation
- `source/common/listener_manager/active_tcp_socket.h:28-110`: ActiveTcpSocket definition
- `source/common/listener_manager/active_tcp_socket.cc:111-160`: continueFilterChain() - listener filter iteration
- `source/common/listener_manager/active_stream_listener_base.cc:38-76`: newConnection() - filter chain matching and network filter creation
- `source/common/listener_manager/active_stream_listener_base.cc:59-69`: createServerConnection() and createNetworkFilterChain()

### Q2: HTTP Parsing and Filter Chain References
- `source/common/http/conn_manager_impl.h:56-64`: ConnectionManagerImpl definition
- `source/common/http/conn_manager_impl.cc:387-442`: newStream() - ActiveStream creation with FilterManager
- `source/common/http/filter_manager.h:332-345`: ActiveStreamEncoderFilter and decoder/encoder filter management
- `source/common/http/filter_manager.h:334-339`: DecoderFilters iteration structure
- `source/common/http/filter_manager.cc`: FilterManager::decodeHeaders() and encodeHeaders() implementations
- Test references showing decoder/encoder iteration: `test/common/http/conn_manager_impl_test.cc:381-406`

### Q3: Route Resolution and Upstream Selection References
- `source/common/router/router.h:308-320`: Router::Filter class definition
- `source/common/router/router.h:347-348`: Filter::decodeHeaders() method
- Test references: `test/common/router/router_test_base.cc:196-198`
- `source/common/router/router.h:379-403`: metadataMatchCriteria() and load balancer context methods
- `source/common/upstream/upstream_impl.h:570-602`: HostSet and host selection structures

### Q4: Upstream Connection and Data Flow References
- `source/common/router/upstream_request.h:30-150`: UpstreamRequest class - onPoolReady() and request handling
- `source/common/router/upstream_request.h:41-60`: Comments on request/response flow through filter chains
- `source/extensions/upstreams/http/http/config.h:17-26`: GenericConnPoolFactory and connection pool creation
- `source/common/router/upstream_codec_filter.h:21-31`: UpstreamCodecFilter - last filter in upstream chain
- `source/common/router/upstream_codec_filter.h:54-77`: CodecBridge - response callback handling
- `source/common/http/filter_manager.h:191-200`: ActiveStreamEncoderFilter wrapper
- `source/common/http/filter_manager.cc:1315-1318`: FilterManager::encodeMetadata() - encoder side
- Test references: `test/common/http/conn_manager_impl_test.cc:381-406` - encoder filter order

### Key Files Summary
- **Connection Accept**: `source/common/listener_manager/active_tcp_listener.cc`, `source/common/listener_manager/active_tcp_socket.cc`
- **Filter Chain Matching**: `source/common/listener_manager/active_stream_listener_base.cc`
- **HTTP Parsing**: `source/common/http/conn_manager_impl.cc`, `source/common/network/connection_impl.cc`
- **Filter Iteration**: `source/common/http/filter_manager.cc`, `source/common/http/filter_manager.h`
- **Router**: `source/common/router/router.cc`, `source/common/router/router.h`
- **Upstream**: `source/common/router/upstream_request.h`, `source/common/router/upstream_codec_filter.h`
- **Connection Pool**: `source/extensions/upstreams/http/http/conn_pool.h`
