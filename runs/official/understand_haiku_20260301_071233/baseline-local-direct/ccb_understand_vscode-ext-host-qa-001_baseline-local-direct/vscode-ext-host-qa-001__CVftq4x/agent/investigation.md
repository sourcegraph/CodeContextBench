# VS Code Extension Host Isolation

## Q1: Process Isolation Architecture

### How is the extension host process isolated from the main VS Code window process?

The extension host is spawned as a completely separate OS-level process using **Electron's utility process API**. The key isolation mechanisms are:

**Process Spawning Mechanism:**
- **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` (line 244)
- **Method:** `UtilityProcess.doStart()` uses `utilityProcess.fork(modulePath, args, {...})` to create a new Electron utility process
- The extension host runs the entry point `vs/workbench/api/node/extensionHostProcess` (set via `VSCODE_ESM_ENTRYPOINT` environment variable)

**Parent-Child Process Relationship:**
- **File:** `src/vs/platform/extensions/electron-main/extensionHostStarter.ts` (lines 70-101)
- **Class:** `ExtensionHostStarter` manages multiple `WindowUtilityProcess` instances (line 23)
- Each extension host is created with a unique ID and maintains separate state
- On **Windows** (line 219 in `localProcessExtensionHost.ts`): The process is spawned with `detached: true`, causing it to be detached from the parent renderer process. This prevents the OS from brutally terminating the extension host when the renderer exits
- On **Linux/macOS**: Processes are orphaned by default and continue running independently

**OS-Level Isolation:**
- Each extension host has its own **process ID (PID)** managed by the operating system
- The process has its own memory space, file descriptors, and environment variables
- The main VS Code window and extension host are completely separate executable instances at the OS level
- A crash in one process cannot directly access or corrupt the memory of the other

**Process Lifecycle Management:**
- **File:** `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts` (lines 284)
- The main window registers a listener on `extensionHostProcess.onExit()` to be notified when the extension host process terminates
- The event includes exit code and signal information, allowing detection of crashes, normal exits, and kills

---

## Q2: Communication Between Processes

### How do the extension host and main window communicate?

**IPC Mechanism - Message Ports:**
- **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` (lines 420-425)
- **Method:** `UtilityProcess.connect()` creates a **MessageChannelMain** with two ports: one for the main window, one for the utility process
- Uses Electron's `MessagePortMain` API, which provides a secure, isolated communication channel

**Message Protocol Handshake:**
- **File:** `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts` (lines 318-322)
- **Sequence:**
  1. Main window acquires a message port via `acquirePort()` (line 360)
  2. Extension host process starts and sends a `Ready` message (MessageType.Ready)
  3. Main window responds with initialization data (extension list, workspace info, environment)
  4. Extension host sends `Initialized` message
  5. Communication channel is now established

**RPC Protocol Layer:**
- **File:** `src/vs/workbench/services/extensions/common/rpcProtocol.ts`
- **Class:** `RPCProtocol` (line 117) wraps the underlying message port
- All method calls between main and extension host are serialized/deserialized as JSON with special handling for buffers
- Implements request-response semantics with unique message IDs to track which responses correspond to which requests

**Communication Channel Closure on Crash:**
- When the extension host crashes, the underlying OS-level process is terminated
- The message port connection is automatically closed by the OS (no graceful shutdown)
- **File:** `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts` (lines 369-371)
- The main window has a `toDisposable` handler that closes the message port when disposed

**Crash Detection via Communication:**
- **File:** `src/vs/workbench/services/extensions/common/rpcProtocol.ts` (lines 121, 208-221)
- **Timeout:** `UNRESPONSIVE_TIME = 3 * 1000` (3 seconds)
- The RPC protocol tracks unacknowledged requests via `_unacknowledgedCount`
- If a request is sent but no acknowledgment arrives within 3 seconds, the extension host is marked as **Unresponsive**
- Continuous unresponsiveness indicates a hang or crash (fires `onDidChangeResponsiveState` event with `ResponsiveState.Unresponsive`)

**Direct Crash Detection:**
- **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` (lines 316-325)
- The main process registers on the `exit` event of the native Electron UtilityProcess
- Also registers on the `app.on('child-process-gone')` event (lines 367-397) which provides crash details including reason: 'crashed', 'oom', 'abnormal-exit', etc.

---

## Q3: Crash Detection and Recovery

### What happens when the extension host crashes?

**Crash Detection Components:**

1. **OS-Level Event Monitoring:**
   - **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` (lines 316-325, 367-397)
   - The `exit` event fires when the process terminates normally or abnormally
   - The `app.on('child-process-gone')` event provides detailed crash information including reason and exit code

2. **Main Process Handler:**
   - **File:** `src/vs/platform/extensions/electron-main/extensionHostStarter.ts` (lines 77-99)
   - **Method:** `createExtensionHost()` registers disposal handlers for each extension host
   - When the process exits, logs the crash and removes the process from the tracked `_extHosts` map
   - Includes a force-kill mechanism (lines 90-98): if the process sends an exit event but doesn't actually terminate within 1 second, it's forcefully killed

3. **Extension Host Manager:**
   - **File:** `src/vs/workbench/services/extensions/common/extensionHostManager.ts` (lines 60, 108)
   - **Event:** `onDidExit` is exposed from the underlying `IExtensionHost` to notify about process termination
   - The manager exposes this event for higher-level handling

4. **Native Extension Service:**
   - **File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts` (lines 149-228)
   - **Method:** `_onExtensionHostCrashed()` is called when a crash is detected
   - Logs the crash and sends telemetry data

**Automatic Restart Decision Logic:**

1. **Crash Tracker:**
   - **File:** `src/vs/workbench/services/extensions/common/abstractExtensionService.ts` (lines 1469-1492)
   - **Class:** `ExtensionHostCrashTracker` limits crashes to prevent infinite restart loops
   - **Limits:** Maximum 3 crashes within a 5-minute window (`_TIME_LIMIT = 5 * 60 * 1000`, `_CRASH_LIMIT = 3`)

2. **Automatic Restart:**
   - **File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts` (lines 183-188)
   - If `shouldAutomaticallyRestart()` returns true (fewer than 3 crashes in 5 minutes):
     - Logs "Automatically restarting the extension host"
     - Shows notification: "The extension host terminated unexpectedly. Restarting..."
     - Calls `this.startExtensionHosts()` to spawn a new process

3. **Manual Restart Prompt:**
   - **File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts` (lines 189-226)
   - If crash threshold exceeded:
     - Shows error notification: "Extension host terminated unexpectedly 3 times within the last 5 minutes"
     - Offers user choices: "Start Extension Bisect", "Restart Extension Host", "Learn More"
     - On production builds, suggests extension bisect to help identify the problematic extension

**Infinite Restart Loop Prevention:**

- **File:** `src/vs/workbench/services/extensions/common/abstractExtensionService.ts` (lines 1488-1491)
- **Method:** `shouldAutomaticallyRestart()` checks if `_recentCrashes.length < ExtensionHostCrashTracker._CRASH_LIMIT`
- Crashes older than 5 minutes are removed from the tracking list (line 1476-1481)
- Once 3 crashes are detected, automatic restart is disabled
- User must explicitly choose to restart, giving them time to investigate or disable problematic extensions

**Exit Code Handling:**

- **File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts` (lines 162-177)
- **Special Case:** Exit code 55 (`ExtensionHostExitCode.VersionMismatch`) triggers a special path
- Shows: "Extension host cannot start: version mismatch"
- Offers: "Relaunch VS Code" (not automatic restart)
- All other exit codes follow the standard crash recovery flow

---

## Q4: Isolation Mechanisms

### What specific architectural features ensure the main window's lifecycle is independent of the extension host?

**1. Process-Level Memory Isolation:**
- Each process has its own JavaScript V8 heap, stack, and memory space
- **No shared memory:** The main window cannot directly access extension host memory
- A segfault or memory corruption in the extension host only affects that process
- **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` (line 244) - uses native `utilityProcess.fork()` which ensures complete memory isolation

**2. Exception and Error Containment:**
- Uncaught exceptions in the extension host process are caught by Node.js/Electron, not propagated to the main window
- **File:** `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts` (line 195)
- The environment variable `VSCODE_HANDLES_UNCAUGHT_ERRORS: true` tells the extension host to handle its own uncaught exceptions
- The extension host process can segfault, throw, or panic without affecting the main VS Code window

**3. Message Port-Based Communication Guarantees:**
- **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` (lines 420-425)
- Communication only happens through message ports, which is inherently safe
- No direct function calls between processes
- All data is serialized/deserialized, preventing pointer dereferences or memory access across boundaries

**4. RPC Protocol Isolation:**
- **File:** `src/vs/workbench/services/extensions/common/rpcProtocol.ts` (lines 117-282)
- Remote Procedure Calls are made through proxies (line 243-266)
- Proxies create isolated function contexts (line 251-265)
- If the extension host crashes during an RPC call, the promise is rejected, but the main window continues
- The main window is never blocked waiting for the extension host (timeouts prevent hangs)

**5. Event-Driven Lifecycle:**
- **File:** `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts` (lines 96-97)
- `onExit` event allows the main window to handle extension host termination asynchronously
- Main window registers handlers but is never dependent on extension host being alive
- Main window can continue handling user input even while extension host exits

**6. Graceful Degradation:**
- **File:** `src/vs/workbench/services/extensions/common/extensionHostManager.ts` (lines 201-203)
- `ready()` method waits for extension host initialization, but returns a promise
- Main window doesn't block on extension host readiness
- If extension host fails to start, UI remains responsive
- User can edit files, open tabs, etc. without extensions working

**7. OS-Specific Isolation Optimizations:**

**Windows-Specific (line 219 in localProcessExtensionHost.ts):**
- Extension host is spawned with `detached: true`
- This means the extension host is not part of the same process group as the renderer
- If the renderer crashes or closes, the OS doesn't automatically terminate the extension host
- Prevents cascading failures where the main window crashing takes down extensions

**Linux/macOS:**
- Processes are orphaned by default, naturally providing independence
- No special flags needed for isolation

**8. Notification Service Integration:**
- **File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts` (lines 187, 225)
- Crash notifications are shown in-UI but don't block the main window
- User is notified asynchronously about extension host problems
- Main window continues functioning while dialogs are shown

**9. Lifecycle Service Integration:**
- **File:** `src/vs/platform/extensions/electron-main/extensionHostStarter.ts` (lines 34-38)
- On main application shutdown, extension hosts are gracefully shut down (with timeout)
- Main window shutdown doesn't depend on extension host shutdown (uses timeout mechanism)
- `_waitForAllExit(maxWaitTimeMs)` (line 151) limits the wait time, ensuring app closure regardless of extension host state

**10. Independent Event Loop:**
- Main window and extension host run separate Node.js/V8 event loops
- One process blocking doesn't prevent the other from handling events
- This is guaranteed by the OS process isolation, not application code

---

## Evidence

### Process Spawning and Isolation
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:244` - `utilityProcess.fork()` spawns the process
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:305-314` - Spawn event registers process PID
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:316-325` - Exit event detection
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:367-397` - Crash event handling
- `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts:219` - Detached flag on Windows

### Communication and Handshake
- `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts:355-405` - Protocol establishment
- `src/vs/workbench/services/extensions/electron-sandbox/localProcessExtensionHost.ts:407-459` - Handshake protocol
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:420-425` - Message port connection
- `src/vs/workbench/services/extensions/common/extensionHostProtocol.ts:118-146` - Message types (Ready, Initialized, Terminate)

### Crash Detection
- `src/vs/platform/extensions/electron-main/extensionHostStarter.ts:77-99` - Crash tracking
- `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts:149-228` - Crash handler
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:90-98` - Force-kill mechanism

### Automatic Restart Logic
- `src/vs/workbench/services/extensions/common/abstractExtensionService.ts:1469-1492` - ExtensionHostCrashTracker
- `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts:183-226` - Restart decision logic

### Responsiveness Tracking
- `src/vs/workbench/services/extensions/common/rpcProtocol.ts:121` - UNRESPONSIVE_TIME constant (3 seconds)
- `src/vs/workbench/services/extensions/common/rpcProtocol.ts:184-206` - Request acknowledgment tracking
- `src/vs/workbench/services/extensions/common/rpcProtocol.ts:208-221` - Unresponsiveness detection
- `src/vs/workbench/services/extensions/common/rpcProtocol.ts:223-230` - Responsive state change notification

### Extension Host Lifecycle
- `src/vs/workbench/services/extensions/common/extensions.ts:115-133` - IExtensionHost interface
- `src/vs/workbench/services/extensions/common/extensionHostManager.ts:92-162` - Manager initialization and monitoring
- `src/vs/platform/extensions/common/extensionHostStarter.ts:13-36` - IExtensionHostStarter interface

### Graceful Degradation
- `src/vs/workbench/services/extensions/common/extensionHostManager.ts:164-166` - Disconnect support
- `src/vs/workbench/services/extensions/common/extensionHostManager.ts:201-203` - Ready promise (non-blocking)
- `src/vs/platform/extensions/electron-main/extensionHostStarter.ts:151-157` - Graceful shutdown with timeout
