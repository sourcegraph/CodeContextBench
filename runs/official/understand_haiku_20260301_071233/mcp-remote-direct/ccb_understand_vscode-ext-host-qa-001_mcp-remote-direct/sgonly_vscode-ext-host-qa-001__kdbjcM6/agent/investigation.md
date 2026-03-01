# VS Code Extension Host Isolation

## Q1: Process Isolation Architecture

VS Code uses **Electron's utility process API** to isolate the extension host as a completely separate process. Here's how it works:

### Process Spawning Mechanism

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:244-251`

The extension host is spawned using Electron's `utilityProcess.fork()`:

```typescript
this.process = utilityProcess.fork(modulePath, args, {
    serviceName,
    env,
    execArgv,
    allowLoadingUnsignedLibraries,
    respondToAuthRequestsFromMainProcess,
    stdio
});
```

**Key spawning files:**
- `src/vs/platform/extensions/electron-main/extensionHostStarter.ts:103-119` - Manages extension host lifecycle
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:225-257` - Low-level process spawning using Electron's `utilityProcess.fork()`

### Process Relationship

**Parent/Child Relationship at OS Level:**
- The main VS Code process (renderer/main window) is the **parent**
- The extension host is a **child utility process** spawned via `utilityProcess.fork()`
- The child process is **detached in terms of memory and execution context**, but can communicate via IPC
- On shutdown, the parent gracefully terminates children with a timeout (`src/vs/platform/extensions/electron-main/extensionHostStarter.ts:35-38`)

### Crash Isolation Mechanism

**Entry point:** `src/vs/workbench/api/node/extensionHostProcess.ts:351-429`

The architecture ensures isolation through:

1. **Separate Event Loops**: Each process (main and extension host) has its own Node.js/Electron event loop
2. **No Shared Memory**: Extensions run in a completely separate V8 isolate with no direct access to main process memory
3. **Exception Handling**: Uncaught exceptions in the extension host (lines 83-96 in extensionHostProcess.ts) are caught by the process wrapper before they can affect the main process
4. **Process-Level Boundaries**: The OS-level process boundary prevents:
   - Stack overflows in one process from affecting another
   - Segmentation faults in native modules from crashing the main process
   - Memory exhaustion in one process from consuming main process memory

---

## Q2: Communication Between Processes

VS Code uses a **multi-layered IPC system** with MessagePort-based communication as the primary mechanism.

### IPC Mechanisms

**File:** `src/vs/workbench/services/extensions/common/extensionHostEnv.ts:8-94`

Three IPC connection types are supported:

1. **MessagePort (Primary):** `ExtHostConnectionType.MessagePort = 3`
   - Uses Electron's native `MessagePortMain` and `MessagePort` APIs
   - Established via `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:420-425`
   - Higher performance, modern async communication

2. **Socket Connection:** `ExtHostConnectionType.Socket = 2`
   - WebSocket or standard socket fallback
   - Uses `src/vs/base/parts/ipc/node/ipc.net.ts`

3. **Named Pipe IPC:** `ExtHostConnectionType.IPC = 1`
   - Legacy named pipe/domain socket communication
   - Used when other methods unavailable

### Communication Establishment

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:516-522`

```typescript
// Establish & exchange message ports
const windowPort = this.connect(configuration.payload);
responseWindow.win.webContents.postMessage(configuration.responseChannel,
    configuration.responseNonce, [windowPort]);
```

The main window sends a MessagePort to the extension host via `postMessage()`, enabling bidirectional messaging.

### Communication Protocol

**File:** `src/vs/workbench/services/extensions/common/extensionHostProtocol.ts`

The RPC protocol wraps IPC communication:
- `src/vs/workbench/services/extensions/common/extensionHostManager.ts:254` - Creates `RPCProtocol` instance
- Handles serialization/deserialization of method calls between processes
- Maintains request-response mappings across the IPC boundary

### Channel Closure on Crash

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:287-397`

When the extension host crashes, the IPC communication channel is automatically severed through several mechanisms:

1. **Process Exit Event Handler** (lines 317-325):
   ```typescript
   this._register(Event.fromNodeEventEmitter<number>(process, 'exit')(code => {
       this._onExit.fire({ pid: this.processPid!, code, signal: 'unknown' });
       this.onDidExitOrCrashOrKill();
   }));
   ```
   - Fires exit event with code
   - Cleans up IPC channels automatically

2. **Crash Detection via Electron's `child-process-gone` Event** (lines 368-397):
   ```typescript
   app.on('child-process-gone', (event, details) => {
       if (details.type === 'Utility' && details.name === serviceName) {
           this._onCrash.fire({ ... });
           this.onDidExitOrCrashOrKill();
       }
   });
   ```
   - Electron notifies parent when child utility process terminates
   - Provides exit code and crash reason
   - Reasons include: 'clean-exit', 'abnormal-exit', 'killed', 'crashed', 'oom', 'launch-failed', 'integrity-failure'

### Main Process Detection of Crash

**File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts:149-228`

The main process detects crashes through the `onDidExit` event subscription:

```typescript
protected override _onExtensionHostCrashed(extensionHost: IExtensionHostManager,
    code: number, signal: string | null): void {
    // Crash handling logic
}
```

The connection status is monitored continuously, and timeouts can be detected via the RPCProtocol's responsiveness checks.

---

## Q3: Crash Detection and Recovery

### Crash Detection

**Detection Points:**

1. **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:305-325`
   - `onSpawn` event: Process successfully started, captures PID
   - `onExit` event: Process exited normally
   - `onCrash` event: Electron app notifies of abnormal termination

2. **File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:368-397`
   - Electron's `app.on('child-process-gone')` listener
   - Provides crash reason and exit code
   - Distinguishes between clean exit and crash scenarios

3. **File:** `src/vs/workbench/services/extensions/common/extensionHostManager.ts:108`
   - Extension host manager subscribes to `onDidExit` event
   - Propagates crash information up to extension service

### Automatic vs. Manual Restart Decision

**File:** `src/vs/workbench/services/extensions/common/abstractExtensionService.ts:1469-1492`

**ExtensionHostCrashTracker Class:**
```typescript
export class ExtensionHostCrashTracker {
    private static _TIME_LIMIT = 5 * 60 * 1000;  // 5 minutes
    private static _CRASH_LIMIT = 3;             // Max 3 crashes

    public shouldAutomaticallyRestart(): boolean {
        this._removeOldCrashes();
        return (this._recentCrashes.length < ExtensionHostCrashTracker._CRASH_LIMIT);
    }
}
```

**Decision Logic** (`src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts:183-226`):

- **Automatic Restart:** If fewer than 3 crashes occurred within the last 5 minutes
  - Shows non-intrusive status bar message: "The extension host terminated unexpectedly. Restarting..."
  - Calls `this.startExtensionHosts()` automatically
  - Line 185-188: `if (this._localCrashTracker.shouldAutomaticallyRestart()) { ... }`

- **Manual Restart:** If 3+ crashes in 5 minutes
  - Shows error notification with choices
  - User must click "Restart Extension Host" button (line 209-210)
  - Also offers "Start Extension Bisect" or "Open Developer Tools" (lines 193-205)
  - Line 225: Shows final error message with full details

### Prevention of Infinite Restart Loops

**File:** `src/vs/workbench/services/extensions/common/abstractExtensionService.ts:1476-1481`

The `ExtensionHostCrashTracker` prevents infinite loops through:

1. **Time-Window Tracking**: Crashes older than 5 minutes are automatically discarded
2. **Crash Count Limit**: Maximum 3 automatic restarts within 5-minute window
3. **Manual Intervention**: 4th crash within 5 minutes requires user to click restart button
4. **Crash Information Storage**: Each crash is timestamped for age-based removal

**Reset Mechanism:**
```typescript
private _removeOldCrashes(): void {
    const limit = Date.now() - ExtensionHostCrashTracker._TIME_LIMIT;
    while (this._recentCrashes.length > 0 &&
           this._recentCrashes[0].timestamp < limit) {
        this._recentCrashes.shift();
    }
}
```

If crash frequency drops (more than 5 minutes between crashes), the counter resets and automatic restart is allowed again.

---

## Q4: Isolation Mechanisms

### OS-Level Process Isolation

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:225-285`

1. **Separate Process Created via Fork**: `utilityProcess.fork()` creates a new process with:
   - Separate process ID (PID)
   - Separate V8 JavaScript engine instance
   - Separate memory heap
   - Separate event loop

2. **Environment Variables Isolation** (lines 259-285):
   - Custom environment created per process
   - Parent process environment is cloned, not shared
   - Dangerous variables are stripped (`removeDangerousEnvVariables`)
   - Prevents pollution of parent environment

### Error Boundary Mechanisms

**File:** `src/vs/workbench/api/node/extensionHostProcess.ts:79-96`

Process-level error handling in extension host prevents errors from propagating to main process:

```typescript
function patchProcess(allowExit: boolean) {
    process.exit = function (code?: number) {
        if (allowExit) {
            nativeExit(code);
        } else {
            const err = new Error('An extension called process.exit() and this was prevented.');
            console.warn(err.stack);
        }
    };

    process.crash = function () {
        const err = new Error('An extension called process.crash() and this was prevented.');
        console.warn(err.stack);
    };
}
```

Extension code cannot directly terminate the process or call `process.crash()`.

### Native Module Isolation

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:244-250`

Native modules (`.node` files) can crash the process, but isolation mechanisms prevent this from affecting the main process:

1. **Separate V8 Isolate**: Native modules run in the extension host's isolate, not main process
2. **Crash Reporting** (lines 328-365):
   - V8 crashes are caught via `process.on('error')` handler
   - Error reports are parsed to identify problematic native addons
   - Telemetry sent to understand which addons cause crashes

3. **Forceful Cleanup** (`src/vs/platform/extensions/electron-main/extensionHostStarter.ts:85-98`):
   ```typescript
   setTimeout(() => {
       try {
           process.kill(pid, 0); // Check if process still exists
           if (process.kill(pid)) {  // Force kill if stuck
               this._logService.error(`Extension host with pid ${pid} still exists, forcefully killing it...`);
               process.kill(pid);
           }
       } catch (er) { /* already gone */ }
   }, 1000);
   ```
   - If extension host doesn't exit cleanly within 1 second, it's forcefully terminated
   - Prevents stuck processes from consuming resources

### Platform-Specific Isolation

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:268-274`

Windows-specific UNC path restrictions:
```typescript
if (isWindows) {
    if (isUNCAccessRestrictionsDisabled()) {
        env['NODE_DISABLE_UNC_ACCESS_CHECKS'] = '1';
    } else {
        env['NODE_UNC_HOST_ALLOWLIST'] = getUNCHostAllowlist().join('\\');
    }
}
```
- Restricts network access from extension host on Windows
- Prevents extensions from accessing unauthorized UNC paths

### Lifecycle Binding

**File:** `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts:523-532`

Window lifecycle binding ensures extension host cleanup:

```typescript
if (configuration.windowLifecycleBound) {
    this._register(Event.filter(this.lifecycleMainService.onWillLoadWindow,
        e => e.window.win === window)(() => this.kill()));
    this._register(Event.fromNodeEventEmitter(window, 'closed')
        (() => this.kill()));
}
```

When the renderer window closes or reloads, the bound extension host is killed.

### Main Window Independence

**File:** `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts:149-228`

Even when extension host crashes:
1. Main window's UI event handlers continue functioning (in browser process)
2. Editor operations remain responsive (DOM events still processed)
3. File system operations (via main process IPC) continue working
4. Only extension functionality is blocked until host restarts

The RPC channel disconnect is gracefully handled, and operations that depend on extensions show appropriate error messages rather than freezing the UI.

---

## Evidence

### Key Files and Line References:

**Process Management:**
- `src/vs/platform/extensions/electron-main/extensionHostStarter.ts` - Extension host lifecycle (create, start, kill, exit handling)
- `src/vs/platform/utilityProcess/electron-main/utilityProcess.ts` - Low-level process spawning and management
- Lines 244-251: `utilityProcess.fork()` spawning
- Lines 305-397: Event listeners for spawn, exit, crash, errors

**IPC Communication:**
- `src/vs/workbench/services/extensions/common/extensionHostEnv.ts` - IPC connection types (MessagePort, Socket, IPC)
- `src/vs/base/parts/ipc/electron-main/ipc.mp.ts` - MessagePort server implementation
- `src/vs/base/parts/ipc/node/ipc.mp.ts` - MessagePort client implementation

**Crash Detection & Recovery:**
- `src/vs/workbench/services/extensions/electron-sandbox/nativeExtensionService.ts:149-228` - Crash handler with recovery logic
- `src/vs/workbench/services/extensions/common/abstractExtensionService.ts:1469-1492` - ExtensionHostCrashTracker implementation
- Lines 1471-1472: 5-minute window and 3-crash limit

**Extension Host Entry Point:**
- `src/vs/workbench/api/node/extensionHostProcess.ts:79-96` - Process patching to prevent extension from terminating host
- Line 351-429: Extension host startup and initialization

**Isolation Enforcement:**
- `src/vs/workbench/services/extensions/common/extensionHostManager.ts:58-200` - ExtensionHostManager with onDidExit subscription
- `src/vs/workbench/services/extensions/common/lazyCreateExtensionHostManager.ts` - Lazy initialization to minimize impact

