# Envoy Request Routing Flow

This document traces the complete path of a single HTTP/1.1 request from TCP accept through filter chain processing, route resolution, upstream cluster selection, and upstream connection establishment.

## Q1: Listener Accept to Network Filter Chain

### TCP Socket Accept
1. **Component**: `TcpListenerImpl` (/workspace/source/common/network/tcp_listener_impl.cc)
   - Line 56-126: `onSocketEvent()` handles incoming TCP connection notifications
   - Line 71: `socket_->ioHandle().accept()` accepts the new connection
   - Line 117-119: `cb_.onAccept()` is called with the `AcceptedSocketImpl`

### Connection Routing to Network Filter Chain
2. **Component**: `ActiveTcpListener` (/workspace/source/common/listener_manager/active_tcp_listener.cc)
   - Line 80-91: `onAccept()` receives the accepted socket
   - Line 90: Calls `onAcceptWorker()` to process the socket
   - Line 118-123: Connection balancing may route to a different handler
   - Line 126-129: Creates `ActiveTcpSocket` and initiates listener filter processing

### Listener Filter Processing
3. **Component**: `ActiveTcpSocket` (/workspace/source/common/listener_manager/active_tcp_socket.cc)
   - Line 74: `startFilterChain()` initiates listener filter chain
   - Line 111-173: `continueFilterChain()` iterates through listener filters
   - Line 121: Each filter's `onAccept()` is called
   - Line 185-222: `newConnection()` creates the network connection when listener filters complete
   - Line 216: Sets default transport protocol if not already set
   - Line 220: Calls `listener_.newConnection()` to create the server connection

### Filter Chain Selection and Server Connection Creation
4. **Component**: `ActiveStreamListenerBase` (/workspace/source/common/listener_manager/active_stream_listener_base.cc)
   - Line 38-76: `newConnection()` creates the HTTP connection
   - Line 41: `config_->filterChainManager().findFilterChain()` selects the appropriate filter chain based on socket properties
   - Line 58: Creates transport socket from the filter chain's factory
   - Line 59-60: `dispatcher().createServerConnection()` creates the server connection
   - Line 68-69: `createNetworkFilterChain()` creates the network filter chain (HTTP connection manager is added here)

### HTTP Connection Manager Initialization
5. **Component**: `ConnectionManagerImpl` (/workspace/source/common/http/conn_manager_impl.h/cc)
   - Inherited from `Network::ReadFilter`
   - Registered as a network filter in the filter chain
   - Line 95: `onNewConnection()` called when connection is established
   - Prepares for HTTP decoding

## Q2: HTTP Parsing and Filter Chain Iteration

### Data Arrival and Codec Creation
1. **Component**: `ConnectionManagerImpl::onData()` (/workspace/source/common/http/conn_manager_impl.cc:486)
   - Line 488-496: Creates HTTP codec lazily if not already created
   - Line 503: `codec_->dispatch(data)` parses the byte stream into HTTP messages

### HTTP Stream Creation
2. **Component**: `ConnectionManagerImpl::newStream()` (/workspace/source/common/http/conn_manager_impl.cc:387)
   - Called by the HTTP codec when request headers are complete
   - Line 407-408: Creates `ActiveStream` structure
   - Line 440-441: Adds the stream to the `streams_` list
   - Line 441: Returns reference to the newly created stream for codec to use

### ActiveStream Structure and Filter Chain
3. **Component**: `ActiveStream` (nested in `/workspace/source/common/http/conn_manager_impl.h:141`)
   - Implements `RequestDecoder` interface for the codec
   - Line 1193-1447 in conn_manager_impl.cc: `decodeHeaders()` processes incoming HTTP headers
   - Line 1403: `filter_manager_.createDownstreamFilterChain()` creates HTTP decoder/encoder filter chains
   - Line 1439: `filter_manager_.decodeHeaders()` initiates filter chain processing

### Filter Chain Iteration
4. **Component**: `FilterManager` (/workspace/source/common/http/filter_manager.cc)
   - Line 1045-1088: `createDownstreamFilterChain()` instantiates all HTTP filters
   - Filters are created in order: decoder filters, then encoder filters
   - Each filter inherits from `Http::StreamDecoderFilter` and `Http::StreamEncoderFilter`

### Decoder Filter Execution
5. **Component**: `FilterManager::decodeHeaders()` (/workspace/source/common/http/filter_manager.cc:313-320)
   - Iterates through each decoder filter in sequence
   - Each filter's `decodeHeaders()` returns a `FilterHeadersStatus`:
     - `Continue`: filter completed, proceed to next filter
     - `StopIteration`: filter needs more data or async processing
     - `StopAllIteration`: critical condition, stop all processing
   - Router filter is typically the last decoder filter

## Q3: Route Resolution and Upstream Selection

### Route Resolution
1. **Component**: `Router::Filter::decodeHeaders()` (/workspace/source/common/router/router.cc:445)
   - Line 468: `callbacks_->route()` queries the route configuration provider
   - Route configuration is matched based on:
     - Request headers (method, path, authority)
     - Virtual hosts configured in the listener
     - Route match conditions (prefix, regex, headers, query params, etc.)

### Route Entry and Cluster Selection
2. **Component**: Route Configuration (/workspace/source/common/router/config_impl.h)
   - Line 506: Route entry is retrieved from the matched route
   - Line 519: `config_->cm_.getThreadLocalCluster()` gets the upstream cluster by name
   - Cluster must be configured in the Envoy bootstrap configuration

### Host Selection from Cluster
3. **Component**: Upstream Cluster Manager (/workspace/source/common/router/router.cc:664)
   - Line 664: `cluster->chooseHost(this)` selects a specific upstream host
   - Selection algorithm depends on load balancer policy:
     - Round-robin, least-request, ring-hash, random, maglev, etc.
     - Can be synchronous or asynchronous
   - Returns a `Upstream::HostConstSharedPtr` referencing the selected host

### Connection Pool Creation
4. **Component**: `Filter::createConnPool()` (/workspace/source/common/router/router.cc:905)
   - Line 724: `createConnPool()` creates a connection pool for the selected host
   - Line 905-944: Determines upstream protocol (HTTP, TCP, UDP)
   - Connection pool may reuse existing connections or create new ones

### Upstream Stream Request
5. **Component**: `UpstreamRequest::acceptHeadersFromRouter()` (/workspace/source/common/router/upstream_request.cc:380)
   - Line 404: `conn_pool_->newStream(this)` requests a new upstream stream
   - Connection pool:
     - Returns existing connection if available and suitable
     - Creates new upstream TCP connection if needed
     - Initiates TLS handshake if required

## Q4: Upstream Connection and Data Flow

### Connection Pool Provides Upstream Connection
1. **Component**: Connection Pool (HTTP/TCP)
   - Maintains a pool of connections to the upstream host
   - For HTTP: provides `Http::RequestEncoder` via `newStream()`
   - For TCP: provides raw socket connection
   - Handles connection reuse, timeouts, and health checks

### Upstream Connection Establishment
2. **Component**: `UpstreamRequest::onPoolReady()` (/workspace/source/common/router/upstream_request.cc:584)
   - Called when connection pool has a connection ready
   - Line 593: Stores the upstream connection/stream
   - Line 626-628: Records upstream connection information (addresses, protocol)
   - Line 693-695: Invokes callbacks to notify upstream is ready

### Request Encoding to Upstream
3. **Component**: Upstream Filter Chain Processing
   - Line 431-434: `filter_manager_->requestHeadersInitialized()` and `decodeHeaders()`
   - Request passes through upstream decoder filters
   - Last filter is `UpstreamCodecFilter` which:
     - Creates HTTP request encoder
     - Encodes headers: `encoder->encodeHeaders(headers, end_stream)`
     - Sends data: `encoder->encodeData(data, end_stream)`
     - Sends trailers: `encoder->encodeTrailers(trailers)`

### HTTP Request Writing to Socket
4. **Component**: HTTP Codec (HTTP/1.1, HTTP/2, HTTP/3)
   - Codec translates request headers/data/trailers to wire format
   - Writes to underlying `Network::Connection`
   - Connection buffers data and writes to socket via `write()`
   - `onData()` callback on connection signals data written

### Response Reception Path
5. **Component**: Codec callbacks on upstream connection
   - Codec receives response bytes from socket
   - Parses HTTP response format
   - Calls callback: `RequestDecoder::decodeHeaders()` → `UpstreamRequest::decodeHeaders()`
   - Line 306: `parent_.onUpstreamHeaders()` passes response to router filter

### Response Encoding and Return to Downstream
6. **Component**: `Router::Filter::onUpstreamHeaders()` (/workspace/source/common/router/router.cc - upstream response handling)
   - Response headers flow back to router filter
   - Router passes response through encoder filter chain
   - Each encoder filter's `encodeHeaders()` is called
   - Final `ResponseEncoder::encodeHeaders()` sends response to downstream HTTP connection
   - Response data flows similarly: `decodeData()` → encoder filters → `encodeData()`

### Decoder vs. Encoder Filter Chain
7. **Filter Chain Invocation Pattern**:
   - **Decoder Chain** (request path):
     - Invoked by: HTTP codec receiving request bytes
     - Order: First filter → ... → Router filter → Last filter
     - Headers/data/trailers flow: request → decoder filters → router

   - **Encoder Chain** (response path):
     - Invoked by: Router filter receiving upstream response
     - Order: Router filter → First filter → ... → Last filter
     - Headers/data/trailers flow: router → encoder filters → downstream codec

## Evidence

### Key File References and Line Numbers

#### TCP Accept and Listener Setup
- `/workspace/source/common/network/tcp_listener_impl.cc:56-126` - TcpListenerImpl::onSocketEvent()
- `/workspace/source/common/network/tcp_listener_impl.cc:71` - socket->ioHandle().accept()
- `/workspace/source/common/listener_manager/active_tcp_listener.cc:80-91` - ActiveTcpListener::onAccept()
- `/workspace/source/common/listener_manager/active_tcp_listener.cc:118-123` - Connection balancing

#### Listener Filters and Socket Processing
- `/workspace/source/common/listener_manager/active_tcp_socket.cc:74` - startFilterChain()
- `/workspace/source/common/listener_manager/active_tcp_socket.cc:111-173` - continueFilterChain()
- `/workspace/source/common/listener_manager/active_tcp_socket.cc:185-222` - newConnection()
- `/workspace/source/common/listener_manager/active_stream_listener_base.cc:38-76` - newConnection() and filter chain creation

#### Network Filter Chain Selection
- `/workspace/source/common/listener_manager/active_stream_listener_base.cc:41` - findFilterChain()
- `/workspace/source/common/listener_manager/active_stream_listener_base.cc:59-60` - createServerConnection()
- `/workspace/source/common/listener_manager/active_stream_listener_base.cc:68-69` - createNetworkFilterChain()

#### HTTP Connection Manager and Codec
- `/workspace/source/common/http/conn_manager_impl.cc:486-535` - ConnectionManagerImpl::onData()
- `/workspace/source/common/http/conn_manager_impl.cc:465-484` - createCodec()
- `/workspace/source/common/http/conn_manager_impl.cc:387-442` - ConnectionManagerImpl::newStream()

#### HTTP Filter Chain and Decoder Filter Processing
- `/workspace/source/common/http/conn_manager_impl.cc:1193-1447` - ActiveStream::decodeHeaders()
- `/workspace/source/common/http/conn_manager_impl.cc:1403` - createDownstreamFilterChain()
- `/workspace/source/common/http/conn_manager_impl.cc:1439` - filter_manager_.decodeHeaders()
- `/workspace/source/common/http/filter_manager.cc:1086-1088` - createDownstreamFilterChain()

#### Route Resolution and Upstream Selection
- `/workspace/source/common/router/router.cc:445-703` - Filter::decodeHeaders() and route selection
- `/workspace/source/common/router/router.cc:468` - callbacks_->route()
- `/workspace/source/common/router/router.cc:519` - getThreadLocalCluster()
- `/workspace/source/common/router/router.cc:664` - chooseHost()
- `/workspace/source/common/router/router.cc:724` - createConnPool()
- `/workspace/source/common/router/router.cc:714-903` - continueDecodeHeaders() - host selection and upstream creation
- `/workspace/source/common/router/router.cc:845-848` - UpstreamRequest creation

#### Upstream Connection and Request Encoding
- `/workspace/source/common/router/upstream_request.cc:380-434` - acceptHeadersFromRouter()
- `/workspace/source/common/router/upstream_request.cc:404` - conn_pool_->newStream()
- `/workspace/source/common/router/upstream_request.cc:584-696` - onPoolReady()
- `/workspace/source/common/router/upstream_request.cc:431-433` - filter_manager_->decodeHeaders() (upstream)
- `/workspace/source/common/router/upstream_request.h:66-123` - UpstreamRequest interface

#### Response Path and Upstream Data Flow
- `/workspace/source/common/router/upstream_request.cc:267-307` - decodeHeaders() receives upstream response
- `/workspace/source/common/router/upstream_request.cc:321-327` - decodeData() receives upstream response body
- `/workspace/source/common/router/upstream_request.cc:329-340` - decodeTrailers() receives upstream trailers
- `/workspace/source/common/router/upstream_request.cc:306` - parent_.onUpstreamHeaders() passes response to router

### Key Classes and Interfaces
- `TcpListenerImpl` - TCP socket accept and event loop integration
- `ActiveTcpListener` - Manages accepted TCP connections and delegates to listener filter processing
- `ActiveTcpSocket` - Wraps socket with listener filter manager
- `ActiveStreamListenerBase` - Creates network filter chain and server connection
- `ConnectionManagerImpl` - HTTP protocol handling, codec creation, stream management
- `FilterManager` - Manages HTTP filter chain iteration (decoder and encoder)
- `Router::Filter` - Route resolution and upstream selection
- `UpstreamRequest` - Manages upstream connection and request/response handling
- `GenericConnPool` / `Http::ConnectionPool` - Connection reuse and upstream stream creation

### Configuration and Policy Components
- `Network::FilterChain` - Defines network filters and transport socket factory for a connection
- `Router::RouteConfiguration` - Routes requests to clusters based on match conditions
- `Upstream::Cluster` - Upstream cluster definition with load balancer configuration
- `Http::FilterChainFactory` - Creates HTTP decoder and encoder filters
- `ConnectionPool::Instance` - Manages connections to upstream hosts
