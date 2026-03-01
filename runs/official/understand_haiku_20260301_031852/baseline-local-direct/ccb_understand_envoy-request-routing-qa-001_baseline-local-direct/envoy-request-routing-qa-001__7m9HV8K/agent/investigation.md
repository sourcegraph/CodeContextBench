# Envoy Request Routing Flow

This document traces the complete path of a single HTTP/1.1 request through Envoy's proxy architecture from TCP accept through upstream connection establishment and response forwarding.

## Q1: Listener Accept to Network Filter Chain

**Overview**: A downstream TCP connection is accepted at the OS level, wrapped by Envoy's listener infrastructure, run through listener filters for protocol detection/selection, and then handed to a network filter chain containing the HTTP Connection Manager.

### Component Hierarchy and Socket Acceptance

The **TcpListenerImpl** (source/common/network/tcp_listener_impl.h:17) implements the libevent-based TCP socket listener. When a new TCP connection arrives:

1. **Socket Accept Event** - The OS socket triggers a read event, invoking `TcpListenerImpl::onSocketEvent()` (source/common/network/tcp_listener_impl.h:39)

2. **Connection Socket Creation** - The accepted socket is wrapped in a `Network::ConnectionSocketPtr` and immediately passed to `TcpListenerCallbacks::onAccept()` (envoy/network/listener.h:318)

3. **Active Listener Callback** - The callback is implemented by `ActiveTcpListener::onAccept()` (source/common/listener_manager/active_tcp_listener.cc:80), which:
   - Checks if the listener has reached its connection limit (line 81-87)
   - Calls `onAcceptWorker()` to handle connection balancing (line 90)

4. **Connection Balancing** - `ActiveTcpListener::onAcceptWorker()` (source/common/listener_manager/active_tcp_listener.cc:108) determines which worker thread should handle the connection via the `ConnectionBalancer` (line 118-123). If the connection should be rebalanced, it's posted to another worker.

### Listener Filter Chain Selection and Execution

5. **Listener Filter Chain Creation** - An `ActiveTcpSocket` is created (source/common/listener_manager/active_tcp_listener.cc:126-127) and passed to `ActiveStreamListenerBase::onSocketAccepted()` (source/common/listener_manager/active_stream_listener_base.h:85)

6. **Filter Chain Factory** - The listener's filter chain factory is invoked (source/common/listener_manager/active_stream_listener_base.h:87):
   ```
   config_->filterChainFactory().createListenerFilterChain(*active_socket)
   ```
   This creates listener filters for tasks like:
   - TLS handshake
   - ALPN protocol detection
   - Transport protocol identification

7. **Filter Chain Execution** - `ActiveTcpSocket::startFilterChain()` initiates filter iteration (source/common/listener_manager/active_tcp_socket.h:74), calling `continueFilterChain(true)` (source/common/listener_manager/active_tcp_socket.cc:111)

8. **Filter Status Handling** - For each filter, `(*iter_)->onAccept(*this)` is called (source/common/listener_manager/active_tcp_socket.cc:121):
   - `Network::FilterStatus::Continue` → advances to next filter
   - `Network::FilterStatus::StopIteration` → filter needs more data; creates `ListenerFilterBuffer` to wait for socket data (source/common/listener_manager/active_tcp_socket.cc:134-155)

### Transition to Network Filter Chain

9. **Listener Filters Complete** - After all listener filters pass, `ActiveTcpSocket::newConnection()` is called (source/common/listener_manager/active_tcp_socket.cc:185)

10. **Filter Chain Selection** - `ActiveStreamListenerBase::newConnection()` (source/common/listener_manager/active_stream_listener_base.cc, implementation) selects the appropriate **network filter chain** based on connection properties:
    - Calls `config_->filterChainManager().findFilterChain(*socket, *stream_info)` to match against filter chain criteria (port, SNI, IP, etc.)

11. **Network Filter Chain Creation** - The matched filter chain's network filters are created via (source/common/listener_manager/active_stream_listener_base.cc):
    ```cpp
    config_->filterChainFactory().createNetworkFilterChain(
        *server_conn_ptr, filter_chain->networkFilterFactories());
    ```
    **This is where the HTTP Connection Manager (HCM) is instantiated** as the first network filter on the server connection.

12. **HCM Initialization** - The ConnectionManagerImpl (source/common/http/conn_manager_impl.h:60-64) implements `Network::ReadFilter` and receives initialization callbacks:
    - `onNewConnection()` is called (source/common/http/conn_manager_impl.h:95)
    - This prepares the HCM to receive data

### Data Reception Trigger

13. **Initial onData() Call** - When bytes arrive on the socket, the event dispatcher notifies the connection object, which triggers `Network::ReadFilter::onData()` calls for each filter in sequence. The HCM's `onData()` method is invoked with the raw bytes buffer.

---

## Q2: HTTP Parsing and Filter Chain Iteration

**Overview**: The HTTP Connection Manager parses the byte stream using a protocol-specific codec, creates ActiveStream objects for each HTTP request, and iterates through decoder filters in order, passing request data through the filter chain.

### HTTP Codec Creation and Parsing

1. **Lazy Codec Creation** - The HCM creates the codec on first `onData()` call (source/common/http/conn_manager_impl.h:84-91):
   ```
   ConnectionManagerImpl::onData(Buffer::Instance& data, bool end_stream)
   ```
   Creates appropriate codec (HTTP/1.1, HTTP/2, HTTP/3) based on the protocol detected by listener filters.

2. **Byte Stream Dispatch** - `codec_->dispatch(data)` is called (source/common/http/conn_manager_impl.cc) to parse the buffer. The codec:
   - Identifies HTTP message boundaries (headers/body/trailers)
   - Extracts HTTP headers into structured HeaderMaps
   - Returns parsing status

### ActiveStream Creation

3. **Stream Creation Callback** - When the codec parses a complete HTTP request header block, it invokes the `ServerConnectionCallbacks::newStream()` callback (source/common/http/conn_manager_impl.h:102):
   ```cpp
   RequestDecoder& newStream(ResponseEncoder& response_encoder, bool is_internally_created = false)
   ```

4. **ActiveStream Object** - An `ActiveStream` is constructed (source/common/http/conn_manager_impl.h:141-150, implemented in .cc) which:
   - Owns the `FilterManager` for this request
   - Receives decoded HTTP frames from the codec (headers, data, trailers)
   - Manages the lifecycle of the request/response

5. **FilterManager Creation** - Inside ActiveStream, a `FilterManager` is created to manage the filter chain. The filter manager holds:
   - Decoder filters (`StreamDecoderFilters`) in configured order (source/common/http/filter_manager.h:73-81)
   - Encoder filters in reverse order (source/common/http/filter_manager.h:92-100)

### Decoder Filter Iteration

6. **Header Decoding** - When the codec calls `stream_decoder->decodeHeaders()` on the ActiveStream with the parsed headers (source/common/http/conn_manager_impl.h:184), the ActiveStream:
   - Stores the headers in `request_headers_`
   - Calls `filter_manager_.decoderHeadersNext(headers, end_stream)` to start filter iteration

7. **Filter Chain Execution Order** - Decoder filters execute in configured order (source/common/http/filter_manager.h:66-72):
   - First filter → receives headers
   - If returns `Continue` → next filter receives same headers
   - If returns `StopIteration` → filter iteration pauses; filter is responsible for resuming later
   - If returns `StopAllIteration` → data is buffered; iteration resumes only after filter calls `continueDecoding()`

8. **Router Filter Invocation** - The router filter (typically last decoder filter) is one of these filters:
   - Receives the request headers via `Filter::decodeHeaders()` (source/common/router/router.h:347)
   - Determines which upstream cluster to use
   - Creates upstream request (detailed in Q3)

9. **Data and Trailer Processing** - After headers complete filter iteration:
   - Codec calls `stream_decoder->decodeData(data, end_stream)` for each body chunk
   - FilterManager iterates decoder filters again with data
   - Similar rules: filters can return `Continue`, `StopIteration`, or `StopAllIteration`
   - Codec calls `stream_decoder->decodeTrailers(trailers)` if present

### Return Values Control Flow

10. **Filter Return Values** (source/common/http/filter_manager.h:109-145):
    - `FilterHeadersStatus::Continue` → Continue to next filter
    - `FilterHeadersStatus::StopIteration` → Stop, wait for filter to call `continueDecoding()`
    - `FilterHeadersStatus::StopAllIteration` → Stop all filters; buffer incoming data
    - Similar statuses exist for `FilterDataStatus` and `FilterTrailersStatus`

11. **FilterManager State Tracking** - Each filter wrapper `ActiveStreamDecoderFilter` tracks (source/common/http/filter_manager.h:240-250):
    - `iteration_state_` (Continue, StopSingleIteration, StopAllBuffer, StopAllWatermark)
    - Whether the filter has called `continueDecoding()`
    - Whether headers/data/trailers have been processed

---

## Q3: Route Resolution and Upstream Selection

**Overview**: The router filter receives the request, uses the request path and method to match a route configuration, identifies the target upstream cluster, selects a specific host using load balancing, and initiates connection pool operations to acquire an upstream connection.

### Route Determination

1. **Route Resolution** - When `Filter::decodeHeaders()` is called (source/common/router/router.cc):
   ```cpp
   route_ = callbacks_->route();
   ```
   This queries the route manager (RDS) for the matching route entry. The route manager:
   - Compares request path against configured routes
   - Returns a `Route` object (or nullptr if no match)
   - Route includes virtual host info and route-specific settings

2. **No Route Handling** - If route is null (source/common/router/router.cc):
   - Sets response flag `NoRouteFound`
   - Sends local 404 reply via `callbacks_->sendLocalReply()`
   - Returns `StopIteration`

3. **Route Entry Extraction** - If route exists (source/common/router/router.cc):
   ```cpp
   route_entry_ = route_->routeEntry();
   ```
   The route entry contains:
   - Target cluster name
   - Retry policy
   - Timeout values
   - Weight for weighted routing
   - Shadow policies

### Cluster and Host Selection

4. **Cluster Lookup** - Get the upstream cluster by name (source/common/router/router.cc):
   ```cpp
   Upstream::ThreadLocalCluster* cluster =
       config_->cm_.getThreadLocalCluster(route_entry_->clusterName());
   ```
   This retrieves the **ThreadLocalCluster** for the current worker thread, which provides access to:
   - Cluster metadata and configuration
   - Load balancer for selecting individual hosts
   - Connection pool

5. **No Cluster Handling** - If cluster is null:
   - Sets response flag `NoClusterFound`
   - Sends local 503 reply
   - Returns `StopIteration`

6. **Host Selection** - The router calls the cluster's load balancer (source/common/router/router.cc):
   ```cpp
   auto host_selection_response = cluster->chooseHost(this);
   ```
   The load balancer (source/common/upstream/load_balancer_context_base.h and implementations):
   - Examines the request via the `LoadBalancerContext` (Filter implements this; see source/common/router/router.h:310)
   - Can use request headers (e.g., via hash policies) or connection properties
   - Returns a selected `Upstream::HostConstSharedPtr`
   - May support asynchronous host selection (returns a `Cancellable` handle)

7. **Async vs Sync Host Selection** - (source/common/router/router.cc):
   - **Synchronous** (common case): Host selection returns immediately; calls `continueDecodeHeaders()` directly
   - **Asynchronous**: Returns a `Cancellable` handle; router waits and continues when selection completes via callback

### Connection Pool Creation

8. **Generic Connection Pool** - `Filter::continueDecodeHeaders()` creates the connection pool (source/common/router/router.cc):
   ```cpp
   std::unique_ptr<GenericConnPool> generic_conn_pool =
       createConnPool(*cluster, selected_host);
   ```

   `createConnPool()` (source/common/router/router.cc):
   - Selects protocol (HTTP, TCP, UDP) based on route's CONNECT configuration
   - Gets protocol-specific factory (`GenericConnPoolFactory`) from config
   - Calls `factory->createGenericConnPool(host, cluster, ...)`
   - Returns pool bound to the selected host

9. **Connection Pool Type** - For HTTP, creates `HttpConnPoolImplBase` subclass (source/common/http/conn_pool_base.h:49-103):
   - Stores host, dispatcher, options
   - Maintains list of active connections and pending streams
   - Will lazily create upstream connections via `host->createConnection()`

### Upstream Request Creation

10. **UpstreamRequest Object** - After pool creation (source/common/router/router.cc):
    ```cpp
    UpstreamRequestPtr upstream_request = std::make_unique<UpstreamRequest>(
        *this, std::move(generic_conn_pool), can_send_early_data, can_use_http3, ...);
    LinkedList::moveIntoList(std::move(upstream_request), upstream_requests_);
    ```
    The `UpstreamRequest` (source/common/router/upstream_request.h:66-80) encapsulates:
    - Reference to the connection pool
    - Response decoder that receives upstream responses
    - Callbacks back to the router filter

11. **Headers Accepted** - The router immediately forwards headers to the upstream request (source/common/router/router.cc):
    ```cpp
    upstream_requests_.front()->acceptHeadersFromRouter(end_stream);
    ```
    This calls `UpstreamRequest::acceptHeadersFromRouter()` (source/common/router/upstream_request.cc:380) which:
    - Stores whether this is a CONNECT request
    - **Initiates upstream connection pool stream** via `conn_pool_->newStream(this)`

---

## Q4: Upstream Connection and Data Flow

**Overview**: The connection pool acquires or creates an upstream connection, the request is encoded to the upstream socket, the response is decoded via callbacks, and the response flows back through the encoder filter chain to the downstream socket.

### Connection Pool and Stream Acquisition

1. **newStream() Call** - When `UpstreamRequest` calls `conn_pool_->newStream(this)` (source/common/router/upstream_request.cc:405):
   - Connection pool enqueues this stream as `HttpPendingStream` if no connection is available
   - Connection pool checks if an existing connection can be reused (has available stream slots)
   - If reusable connection exists: calls `onPoolReady()` immediately
   - If no connection available: creates a new connection via `host->createConnection()`

2. **Upstream Connection Creation** - `host->createConnection()` (source/common/http/conn_pool_base.h:122) returns a `CreateConnectionData` struct containing:
   - New `Network::ClientConnection` created via dispatcher
   - Transport socket for TLS/TCP
   - Connection address provider

3. **Codec Client Wrapping** - The connection is wrapped in a codec-specific client:
   - `ActiveClient::initialize()` (source/common/http/conn_pool_base.h:127) creates the `CodecClient`:
   ```cpp
   codec_client_ = parent.createCodecClient(data);
   ```
   - For HTTP/1: `Http1CodecClient` wraps the connection
   - For HTTP/2: `Http2CodecClient` wraps the connection
   - CodecClient is responsible for encoding/decoding HTTP on the connection

4. **onPoolReady Callback** - Once connection is ready, pool calls (source/common/http/conn_pool_base.h:85):
   ```cpp
   void onPoolReady(Envoy::ConnectionPool::ActiveClient& client,
                    Envoy::ConnectionPool::AttachContext& context)
   ```
   This ultimately invokes `UpstreamRequest::onPoolReady()` (source/common/router/upstream_request.cc, large method around line 468+) which:
   - Stores reference to the `GenericUpstream` (the codec client wrapper)
   - Records upstream host information
   - Sets up upstream filter manager
   - **Signals pool that it's ready to send the request body**

### Request Encoding and Transmission

5. **Request Encoder Acquisition** - Within `onPoolReady()`, the `GenericUpstream` provides a `RequestEncoder`:
   - For HTTP/1: returned by `Http1CodecClient::newStream()`
   - For HTTP/2: returned by `Http2CodecClient::newStream()`
   - Encoder has methods: `encodeHeaders()`, `encodeData()`, `encodeTrailers()`

6. **Filter-Based Encoding** - The request is filtered before being sent upstream via `UpstreamFilterManager`:
   - Router calls `acceptDataFromRouter()` (source/common/router/upstream_request.cc:412) and `acceptTrailersFromRouter()`
   - Data passes through **upstream filters** (in normal order, same as downstream decoder filters)
   - Final filter is `UpstreamCodecFilter` which calls `encoder->encodeHeaders()`, `encoder->encodeData()`, `encoder->encodeTrailers()`
   - Encoded bytes are written to the upstream socket

7. **Socket Write** - The codec client's connection object performs the actual write:
   - Bytes are buffered in the connection's write buffer
   - When the buffer has data, it's flushed to the OS socket
   - Backpressure is managed via watermark callbacks

### Response Decoding and Transmission Downstream

8. **Response Reception** - When upstream sends response bytes:
   - Connection's read event triggers
   - Codec client's read filter (usually the codec itself) is invoked
   - Codec parses response frames and calls callbacks on the `ResponseDecoder`
   - `ResponseDecoder` is the `UpstreamRequest` object itself (source/common/router/upstream_request.h:94-98)

9. **Response Headers** - When codec parses response headers (source/common/router/upstream_request.cc):
   ```cpp
   void UpstreamRequest::decodeHeaders(Http::ResponseHeaderMapPtr&& headers, bool end_stream)
   ```
   This:
   - Receives response headers from upstream codec
   - Passes through **upstream encoder filters** (reverse order of decoder filters) via `UpstreamFilterManager`
   - Final filter calls back to router via `FilterInterface::onUpstreamHeaders()` (source/common/router/router.h:487)

10. **Router Handler** - `Filter::onUpstreamHeaders()` (source/common/router/router.cc):
    - Receives response code and headers from upstream
    - Handles redirects, retries, etc.
    - Eventually calls `ActiveStream::encodeHeaders()` (in HCM)

11. **Downstream Encoding** - The downstream `ActiveStream` encodes the response:
    - Receives headers via `Filter::onUpstreamHeaders()` callback
    - Calls `filter_manager_.encodeHeaders()` to iterate **downstream encoder filters**
    - **Encoder filters execute in REVERSE order** (source/common/http/filter_manager.h:89-100)
      - Last configured filter → first filter executed
      - This allows outer filters to modify inner responses
    - Final encoder call goes to `response_encoder_` which the codec provided at stream creation
    - Response headers are written to the downstream connection socket

12. **Response Data Flow** - Similar to headers:
    - `UpstreamRequest::decodeData()` receives body chunks (source/common/router/upstream_request.cc:490)
    - Passes through upstream encoder filters
    - `Filter::onUpstreamData()` handles and forwards to downstream
    - `ActiveStream::encodeData()` filters data through downstream encoder filters in reverse order
    - Bytes written to downstream socket via `response_encoder_`

13. **Response Trailers** - Same flow as headers/data:
    - `UpstreamRequest::decodeTrailers()` (source/common/router/upstream_request.cc:491)
    - Propagates through filter chain
    - `ActiveStream::encodeTrailers()`
    - Written to downstream socket

14. **Stream Cleanup** - When response is complete:
    - Upstream connection is returned to the connection pool (or closed if at limit)
    - Both upstream and downstream streams are marked complete
    - Access logs are written
    - Stream objects are deferred-deleted

---

## Evidence

### Key Files and Line References

**Listener Layer:**
- `/workspace/source/common/listener_manager/active_tcp_listener.h:25` - ActiveTcpListener class definition
- `/workspace/source/common/listener_manager/active_tcp_listener.cc:80` - onAccept() implementation
- `/workspace/source/common/listener_manager/active_tcp_listener.cc:108` - onAcceptWorker() implementation
- `/workspace/source/common/listener_manager/active_tcp_socket.h:28` - ActiveTcpSocket class definition
- `/workspace/source/common/listener_manager/active_tcp_socket.cc:111` - continueFilterChain() implementation
- `/workspace/source/common/listener_manager/active_tcp_socket.cc:185` - newConnection() implementation

**Network Filter Chain and HCM:**
- `/workspace/source/common/listener_manager/active_stream_listener_base.h:85` - onSocketAccepted() filter chain creation
- `/workspace/source/common/http/conn_manager_impl.h:60` - ConnectionManagerImpl class definition
- `/workspace/source/common/http/conn_manager_impl.h:94-95` - onData() and onNewConnection() methods

**Filter Manager:**
- `/workspace/source/common/http/filter_manager.h:73` - StreamDecoderFilters definition
- `/workspace/source/common/http/filter_manager.h:92` - StreamEncoderFilters definition (reverse order)
- `/workspace/source/common/http/filter_manager.h:240` - ActiveStreamDecoderFilter definition
- `/workspace/source/source/common/http/conn_manager_impl.h:141` - ActiveStream class definition
- `/workspace/source/common/http/conn_manager_impl.h:244-248` - Encoder callback methods

**Route Resolution:**
- `/workspace/source/common/router/router.h:308` - Filter class definition
- `/workspace/source/common/router/router.h:347` - decodeHeaders() declaration
- `/workspace/source/common/router/router.h:351` - continueDecodeHeaders() declaration

**Connection Pool:**
- `/workspace/source/common/http/conn_pool_base.h:49` - HttpConnPoolImplBase class
- `/workspace/source/common/http/conn_pool_base.h:106` - ActiveClient class
- `/workspace/source/common/http/conn_pool_base.h:127` - initialize() method

**Upstream Request:**
- `/workspace/source/common/router/upstream_request.h:66` - UpstreamRequest class definition
- `/workspace/source/common/router/upstream_request.cc:380` - acceptHeadersFromRouter() implementation
- `/workspace/source/common/router/upstream_request.cc:405` - conn_pool_->newStream() call
- `/workspace/source/common/router/upstream_request.cc:468+` - onPoolReady() implementation

**Network Listener Interface:**
- `/workspace/envoy/network/listener.h:310` - TcpListenerCallbacks interface
- `/workspace/envoy/network/listener.h:318` - onAccept() callback signature
