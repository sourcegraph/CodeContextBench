# Envoy Request Routing Flow

## Q1: Listener Accept to Network Filter Chain

When a downstream client establishes a TCP connection to Envoy, the following sequence occurs:

**Socket Accept:**
- The kernel accepts the incoming TCP connection and the worker thread's event loop detects it
- `Network::TcpListenerImpl::onAccept()` is invoked (source/common/network/tcp_listener_impl.cc)
- This callback invokes `Network::TcpListenerCallbacks::onAccept()` with the new socket

**Listener-Level Processing:**
- `ActiveTcpListener::onAccept()` is called (source/common/listener_manager/active_tcp_listener.cc:80)
- If connection limits are reached, the socket is closed; otherwise, `onAcceptWorker()` is called
- `onAcceptWorker()` (source/common/listener_manager/active_tcp_listener.cc:108) applies connection balancing via `connection_balancer_.pickTargetHandler()`
- An `ActiveTcpSocket` is created (source/common/listener_manager/active_tcp_socket.cc:10)
- `onSocketAccepted()` is called to promote the socket through the listener filter chain

**Listener Filter Chain:**
- `ActiveStreamListenerBase::onSocketAccepted()` (source/common/listener_manager/active_stream_listener_base.h:85) executes:
  - `config_->filterChainFactory().createListenerFilterChain()` to instantiate listener filters
  - `startFilterChain()` to begin listener filter iteration
  - Listener filters (e.g., TLS Inspector) examine connection properties and may modify filter state
  - Once listener filters complete and the appropriate filter chain is selected via `findFilterChain()`

**Network Filter Chain Selection:**
- After listener filters complete, `newConnection()` is called with the accepted socket and stream info
- `ActiveStreamListenerBase::newConnection()` (source/common/listener_manager/active_stream_listener_base.h:58) does:
  - Creates a new `Network::Connection` (server connection) from the socket
  - Calls `config_->filterChainFactory().createNetworkFilterChain()` with the server connection
  - This factory instantiates all configured network filters for the selected filter chain
  - The HTTP Connection Manager (HCM) network filter is instantiated as the primary decoder of downstream traffic

**First Data Arrival:**
- When the first bytes arrive from the downstream client, the listener's I/O event handler triggers
- The `Network::FilterManagerImpl` begins iterating through network filters
- Bytes flow to the HCM's `onData()` method (source/common/http/conn_manager_impl.cc:486)

## Q2: HTTP Parsing and Filter Chain Iteration

Once bytes arrive at the HTTP Connection Manager, the following flow occurs:

**Codec Creation and HTTP Parsing:**
- `ConnectionManagerImpl::onData()` (source/common/http/conn_manager_impl.cc:486) receives raw bytes
- If the codec doesn't exist, `createCodec()` is called, which instantiates the appropriate codec (HTTP/1.1, HTTP/2, or HTTP/3)
- The codec's `dispatch()` method is called with the buffer, parsing the byte stream into structured HTTP messages
- For HTTP/1.1: parser extracts headers from the first line and header fields
- For HTTP/2: parser deshames multiplexed streams and parses frame data
- The codec invokes callbacks on `ServerConnectionCallbacks` as it completes parsing

**ActiveStream Creation:**
- When HTTP headers are fully parsed, the codec invokes `onHeadersComplete()` on its connection callbacks
- This triggers `ConnectionManagerImpl::ActiveStream::onHeadersComplete()`
- A new `ActiveStream` is created (source/common/http/conn_manager_impl.h:ActiveStream) to manage this single HTTP request/response
- Stream info is initialized with connection properties, timing, and filter state

**HTTP Filter Chain Creation and Iteration:**
- `ActiveStream` creates a `DownstreamFilterManager` for this stream
- `FilterManager::createDownstreamFilterChain()` calls the HCM's filter chain factory
- The factory applies all configured HTTP filters to the filter manager, creating `ActiveStreamDecoderFilter` wrappers for each filter
- `FilterManager::decodeHeaders()` (source/common/http/filter_manager.cc:536) is called with parsed headers

**Decoder Filter Chain Iteration:**
- `FilterManager::decodeHeaders()` iterates through decoder_filters_ list:
  - For each filter, invokes `StreamDecoderFilter::decodeHeaders(headers, end_stream)`
  - Filter returns `FilterHeadersStatus`: `Continue` (proceed to next), `StopIteration` (pause and wait for resume), or local reply status
  - `CommonDecodePrefix()` handles state transitions based on return values
  - If a filter returns `StopIteration` and is not terminal, iteration pauses; the filter must call `continueDecoding()` to resume
  - The terminal filter (router) always processes headers and determines upstream behavior

**Data and Trailers Processing:**
- When data bytes arrive from the codec, `FilterManager::decodeData()` is called similarly
- Each decoder filter's `decodeData()` is invoked in sequence
- Filters can buffer data (returning `StopIterationAndBuffer`) or continue immediately
- When trailers are parsed, `FilterManager::decodeTrailers()` invokes each filter's `decodeTrailers()`

**Return Value Semantics:**
- `FilterHeadersStatus::Continue`: proceed to next filter
- `FilterHeadersStatus::StopIteration`: halt iteration; filter must call `continueDecoding()` to resume
- `FilterHeadersStatus::StopAllIterationAndWatermark`: halt and apply write buffer limits
- Local reply returns (e.g., from auth filters) short-circuit the chain and generate a response

## Q3: Route Resolution and Upstream Selection

The router decoder filter is the terminal filter in the decoder chain. It performs the following:

**Route Resolution:**
- Router filter's `decodeHeaders()` is invoked by the filter manager
- Router calls `route()` on the route configuration to find the matching route
- Route matching occurs against configured virtual hosts and their routes, based on:
  - Authority header (for host matching)
  - Path prefix/regex (for route matching)
  - HTTP method and other request properties
- The result is a `RouteEntry` which specifies the target cluster and route-level configuration

**Cluster and Host Selection:**
- `Router::Filter::decodeHeaders()` (source/common/router/router.cc) obtains the target cluster name from the route entry
- `cluster_manager_.getThreadLocalCluster(cluster_name)` retrieves the upstream cluster
- The cluster's load balancer is invoked via `loadBalancer().chooseHost(lb_context)` (envoy/upstream/load_balancer.h:58)
- Load balancing algorithms (round-robin, least request, ring hash, etc.) select a specific upstream host
- Returns `HostSelectionResponse` containing the selected `HostConstSharedPtr` and optional async handle

**Connection Pool Acquisition:**
- Router obtains the connection pool for the selected host:
  - For HTTP upstream: `thread_local_cluster.httpConnPool(host, priority, downstream_protocol, context)`
  - For TCP upstream: `thread_local_cluster.tcpConnPool(host, priority, context)`
- The connection pool is per-host, per-priority, and per-protocol
- Connection pool implementation is in source/common/http/ (HTTP/1.1, HTTP/2) or source/extensions/upstreams/http/tcp/ (TCP)

**UpstreamRequest Creation:**
- Router creates an `UpstreamRequest` (source/common/router/upstream_request.h:65) to manage this request-to-upstream mapping
- The `UpstreamRequest` contains:
  - Reference to the downstream request's filter callbacks
  - Connection pool instance for the selected cluster
  - Upstream request state (headers, trailers, data buffering)
- `GenericConnPool::newStream()` is called to request a connection from the pool

**Upstream Connection Establishment:**
- Connection pool checks for existing connections (`selectExistingConnection()`)
- If a connection exists and is available, `onPoolReady()` callback is invoked immediately
- If no connection is available, the pool initiates a new connection via the TCP client:
  - `Network::ClientConnectionFactory::createClientConnection()` creates the upstream socket
  - Connection establishment occurs asynchronously; the pool holds the request pending connection ready
  - When the TCP handshake completes or an existing connection becomes available, `onPoolReady()` is called

## Q4: Upstream Connection and Data Flow

**Upstream Pool Ready Callback:**
- When a connection from the pool is ready, `GenericConnectionPoolCallbacks::onPoolReady()` is invoked
- This callback passes the `RequestEncoder` (the codec's encoder interface for this stream)
- An `UpstreamRequest` instance receives the encoder and transitions to "upstream connected"

**Upstream Filter Chain and Encoding:**
- The `UpstreamRequest` has its own filter manager for encoding: `UpstreamRequestFilterManager`
- This filter manager contains the `UpstreamCodecFilter` (source/common/router/upstream_codec_filter.cc) as the terminal decoder
- When the connection is ready, `onUpstreamConnectionEstablished()` is called (source/common/router/upstream_codec_filter.cc:40)
- If headers were latched while waiting for connection, they are now sent via `decodeHeaders()`

**Request Encoding to Upstream:**
- `UpstreamCodecFilter::decodeHeaders()` (source/common/router/upstream_codec_filter.cc:52) receives downstream headers from the upstream filter manager
- It calls `callbacks_->upstreamCallbacks()->upstream()->encodeHeaders(headers, end_stream)`
- `upstream()` is the `RequestEncoder` from the connection pool
- The encoder serializes headers to the wire: HTTP/1.1 request line + headers, or HTTP/2 HEADERS frame
- Data is encoded similarly: `UpstreamCodecFilter::decodeData()` calls `upstream()->encodeData()`
- Trailers are encoded via `upstream()->encodeTrailers()`

**Upstream Response Reception:**
- The codec's receive path processes incoming data from the upstream server
- When response headers are fully received, the codec invokes its `decodeHeaders()` callbacks
- Response flows into the upstream filter manager's encoder filter chain (note: response is "decoded" from upstream perspective)
- The upstream codec filter's encoder filters receive response headers
- `UpstreamCodecFilter::encodeHeaders()` (source/common/router/upstream_codec_filter.cc) receives response headers

**Response Flow to Downstream:**
- The upstream request's filter manager passes response headers to the `UpstreamRequestFilterManagerCallbacks`
- Callbacks invoke `UpstreamRequest::decodeHeaders()` which represents receiving response from upstream
- This calls `RouterFilter::callbacks()->encodeHeaders()` on the downstream side
- `ActiveStreamEncoderFilter` wrappers in the downstream filter manager iterate through encoder filters
- Each encoder filter's `encodeHeaders()` is invoked: router filters, logging filters, compression filters, etc.
- Terminal encoder filter (if any) or connection manager itself calls `response_encoder_->encodeHeaders()`
- Response headers are serialized by the codec and sent to the downstream client

**Response Data and Trailers:**
- Response body data from upstream is similarly encoded through encoder filters
- `UpstreamRequest::decodeData()` triggers `ActiveStream::encodeData()` on decoder callbacks
- Encoder filters iterate and process response body with `encodeData()`
- Terminal encoder calls `response_encoder_->encodeData()` which sends to downstream
- When upstream sends trailers (HTTP/1.1 chunked encoding or HTTP/2 with trailers), same process applies
- Trailers are iterated through encoder filters and serialized to the downstream connection

**Connection Cleanup:**
- When response is complete (end_stream=true received from upstream), the upstream connection is returned to the pool
- If the connection is reusable (HTTP/1.1 keep-alive or HTTP/2 multiplexing), it remains in the pool for next request
- If not reusable, it is closed
- The `UpstreamRequest` is deleted, and the downstream stream continues until the downstream client closes

## Evidence

### File References

**Listener and TCP Accept Path:**
- source/common/listener_manager/active_tcp_listener.cc:80 - `onAccept()`
- source/common/listener_manager/active_tcp_listener.cc:108 - `onAcceptWorker()`
- source/common/listener_manager/active_tcp_listener.h:25 - `ActiveTcpListener` class definition
- source/common/listener_manager/active_tcp_socket.cc:10 - `ActiveTcpSocket` constructor
- source/common/listener_manager/active_stream_listener_base.h:85 - `onSocketAccepted()`
- source/common/listener_manager/active_stream_listener_base.h:58 - `newConnection()`

**Network Filter Chain:**
- source/common/listener_manager/listener_impl.cc:942 - `createNetworkFilterChain()`
- envoy/network/connection_handler.h:232 - `createListener()` interface
- source/common/network/tcp_listener_impl.cc:128 - `TcpListenerImpl` constructor

**HTTP Parsing:**
- source/common/http/conn_manager_impl.cc:486 - `ConnectionManagerImpl::onData()`
- source/common/http/conn_manager_impl.cc:496 - `createCodec()`
- source/common/http/conn_manager_impl.h:ActiveStream - Stream management

**HTTP Filter Chain Iteration:**
- source/common/http/filter_manager.cc:536 - `FilterManager::decodeHeaders()`
- source/common/http/filter_manager.h:237 - `ActiveStreamDecoderFilter` wrapper
- source/common/http/filter_manager.h:271 - Filter iteration state tracking
- envoy/http/filter.h:38 - `FilterHeadersStatus` enum definition

**Route Resolution:**
- source/common/router/router.cc:1 - Router filter implementation
- source/common/router/router.h - Router filter header
- source/common/router/config_impl.h - Route configuration

**Load Balancing and Host Selection:**
- envoy/upstream/load_balancer.h:58 - `LoadBalancer::chooseHost()` interface
- envoy/upstream/load_balancer.h:83 - `LoadBalancerContext` interface
- source/extensions/clusters/dynamic_forward_proxy/cluster.cc:204 - `chooseHost()` implementation

**Connection Pool:**
- source/common/http/conn_pool_base.cc - Base connection pool
- source/common/http/conn_pool_grid.cc - HTTP connection pool grid
- source/extensions/upstreams/http/http/upstream_request.h:20 - `HttpConnPool` implementation
- source/extensions/upstreams/http/tcp/upstream_request.h:21 - `TcpConnPool` implementation

**Upstream Request and Encoding:**
- source/common/router/upstream_request.h:65 - `UpstreamRequest` class
- source/common/router/upstream_codec_filter.cc:52 - `UpstreamCodecFilter::decodeHeaders()`
- source/common/router/upstream_codec_filter.cc:97 - `UpstreamCodecFilter::decodeData()`
- source/extensions/upstreams/http/http/upstream_request.h:55 - HTTP upstream encoding

**Response Flow:**
- source/common/http/conn_manager_impl.cc:1951 - `onDecoderFilterBelowWriteBufferLowWatermark()`
- source/common/http/filter_manager.h - `DownstreamFilterManager` class
- envoy/http/filter.h:42 - `FilterHeadersStatus` and `FilterDataStatus` enums
