# Terraform State Backend Subsystem Handoff Documentation

## 1. Purpose

### What the Backend Subsystem Solves

The state backend subsystem is the abstraction layer that allows Terraform to persist and retrieve state files, which contain the critical mapping between Terraform configurations and real-world infrastructure resources. It solves several key problems:

- **State Persistence**: Provides a consistent interface to store state snapshots to various storage backends (local disk, S3, Azure, GCS, etc.)
- **Concurrent Access Control**: Implements state locking to prevent multiple Terraform processes from corrupting state through simultaneous modifications
- **Multi-workspace Support**: Allows teams to manage multiple independent state files (workspaces) within a single backend
- **Team Collaboration**: Enables remote state storage so teams can share infrastructure state without manual file copying

### Why Different Backend Types Are Needed

Different organizations have different infrastructure requirements:

- **Local Backend** (`internal/backend/local/`): Simple local development, no remote state
- **Remote State Backends**:
  - **S3** (`internal/backend/remote-state/s3/`): AWS-native state storage with DynamoDB locking
  - **Azure** (`internal/backend/remote-state/azure/`): Azure Blob Storage backend
  - **GCS** (`internal/backend/remote-state/gcs/`): Google Cloud Storage backend
  - **Consul** (`internal/backend/remote-state/consul/`): Distributed Consul clusters
  - **Postgres** (`internal/backend/remote-state/pg/`): SQL database backend
  - **HTTP** (`internal/backend/remote-state/http/`): Generic HTTP endpoints
  - **Kubernetes** (`internal/backend/remote-state/kubernetes/`): Kubernetes secrets/etcd
  - **OSS** (`internal/backend/remote-state/oss/`): Alibaba Cloud Object Storage Service
  - **COS** (`internal/backend/remote-state/cos/`): Tencent Cloud Object Storage
  - **Inmem** (`internal/backend/remote-state/inmem/`): In-memory for testing
- **Remote/Cloud Backends**: HCP Terraform and Terraform Enterprise for managed operations

### Key Responsibilities of a Backend

Every backend implementation must:

1. **Store State Snapshots**: Persist state to storage and retrieve it on demand
2. **Manage Workspaces**: Create, list, and delete named state workspaces
3. **Handle Configuration**: Accept and validate backend-specific configuration (credentials, endpoints, etc.)
4. **Lock State** (optional): Prevent concurrent modifications through exclusive locking
5. **Support Operations** (optional): Execute Terraform operations (plan, apply, etc.) if implementing `OperationsBackend`

---

## 2. Dependencies

### Upstream Dependencies (What Calls Into Backends)

The backend system is called by the CLI command layer:

- **`internal/command/`**: CLI commands like `init`, `plan`, `apply`, `destroy` all retrieve backends
  - `meta_backend.go`: Core backend initialization and configuration
  - `meta_backend_migrate.go`: State migration between backends
  - `init.go`: Backend initialization during `terraform init`
- **`internal/command/meta.go`**: The `Meta` struct holds the configured backend and orchestrates operations
- **`internal/builtin/providers/terraform/`**: The `terraform` provider's `terraform_remote_state` data source reads state from configured backends

### Downstream Dependencies (What Backends Call)

Backends depend on several core subsystems:

- **`internal/states/statemgr/`**: The state manager interfaces that all backends use
  - `Persistent`: Read/write operations on persistent storage
  - `Locker`: State locking interface for concurrent access control
  - `Full`: Union of all state manager functionality
  - `statemgr.Filesystem`: Default implementation for local state
- **`internal/states/`**: State data structures (`State`, `OutputValue`, etc.)
- **`internal/terraform/`**: Terraform Core for executing operations (plans, applies, refreshes)
- **`internal/configs/configschema/`**: Schema definitions for backend configuration validation
- **`internal/tfdiags/`**: Diagnostic collection for validation and configuration errors

### Backend Initialization Flow

```
CLI Command (e.g., terraform init)
    ↓
Meta.Backend() / backendInitFromConfig()
    ↓
backend/init.Backend() - lookup in registry
    ↓
Backend.New() - instantiate backend
    ↓
Backend.ConfigSchema() - get expected config structure
    ↓
Backend.PrepareConfig() - validate and set defaults
    ↓
Backend.Configure() - initialize with configuration values
    ↓
Backend.StateMgr(workspace) - get state manager for workspace
    ↓
statemgr.Full implementation (Filesystem, S3Client, etc.)
    ↓
Lock/Unlock → RefreshState → WriteState → PersistState
```

### Integration with Broader Architecture

- **Local Backend as Operations Container**: The local backend (`internal/backend/local/Local`) implements `backendrun.OperationsBackend` and is always present. It coordinates:
  - Configuration loading from HCL files
  - Terraform Core context initialization
  - Plan and apply execution
  - State locking and persistence

- **Remote Backends Wrap Local**: For remote state with local execution, the local backend wraps another backend via the `Backend` field, delegating state operations while retaining operation execution.

- **HCP Terraform / Cloud Backends**: The `internal/cloud/Cloud` backend provides remote operation execution, wrapping the local backend for hybrid execution modes.

---

## 3. Relevant Components

### Core Files and Directories

#### Backend Interface Definition
- **`internal/backend/backend.go`**: Defines the base `Backend` interface
  - `ConfigSchema()`: Returns configuration schema
  - `PrepareConfig()`: Validates configuration
  - `Configure()`: Initializes with configuration
  - `StateMgr(workspace)`: Gets state manager for workspace
  - `Workspaces()`: Lists available workspaces
  - `DeleteWorkspace()`: Removes a workspace

#### Backend Initialization Registry
- **`internal/backend/init/init.go`**: Backend registration system
  - `Init()`: Registers all built-in backends
  - `Backend(name)`: Retrieves a backend factory
  - `Set()`: Dynamically registers/unregisters backends
  - Handles deprecated backends with `deprecatedBackendShim`

#### State Manager Interfaces
- **`internal/states/statemgr/statemgr.go`**: Base state manager interfaces
  - `Full`: Complete union interface implemented by all state managers
  - `Storage`: Transient + Persistent combined
  - `Transient`: In-memory state operations (Reader, Writer)
  - `Persistent`: Disk/remote persistence operations

- **`internal/states/statemgr/persistent.go`**: Persistence contract
  - `Refresher`: Load state from persistent storage
  - `Persister`: Save state to persistent storage
  - `OutputReader`: Fetch output values
  - `IntermediateStateConditionalPersister`: Control intermediate snapshots

- **`internal/states/statemgr/locker.go`**: Locking interface and implementation
  - `Locker`: Lock/Unlock operations for state
  - `LockInfo`: Metadata about lock holder (who, when, operation, reason)
  - `LockError`: Returned when lock acquisition fails
  - `LockWithContext()`: Retry logic with exponential backoff

#### Filesystem State Manager
- **`internal/states/statemgr/filesystem.go`**: Default local state implementation
  - Manages `terraform.tfstate` files
  - `StateSnapshotMeta()`: Tracks lineage and serial for change detection
  - Platform-specific locking:
    - **Unix**: `internal/states/statemgr/filesystem_lock_unix.go` - fcntl locking
    - **Windows**: `internal/states/statemgr/filesystem_lock_windows.go` - file locking

#### Local Backend (Operations Backend)
- **`internal/backend/local/backend.go`**: Core local backend implementation
  - Manages local state via `statemgr.Filesystem`
  - Fields: `StatePath`, `StateOutPath`, `StateBackupPath`, `StateWorkspaceDir`
  - Can wrap another backend for remote state with local operations

- **`internal/backend/local/backend_local.go`**: Implements `backendrun.Local` interface
  - `Context()`: Creates Terraform context for operations
  - Handles configuration loading and variable processing

- **`internal/backend/local/backend_plan.go`**: Plan operation implementation
- **`internal/backend/local/backend_apply.go`**: Apply operation implementation
- **`internal/backend/local/backend_refresh.go`**: Refresh operation implementation
- **`internal/backend/local/hook_state.go`**: State persistence during operations

#### Remote State Backend Templates
All remote state backends follow the same pattern:

- **`internal/backend/remote-state/s3/`**: AWS S3 backend (most complex example)
  - `backend.go`: Backend configuration and initialization
  - `client.go`: RemoteClient implementation with state I/O
  - Lock support via DynamoDB
  - Checksum validation for state integrity

- **`internal/backend/remote-state/azure/`**: Azure Blob Storage
- **`internal/backend/remote-state/gcs/`**: Google Cloud Storage
- **`internal/backend/remote-state/consul/`**: Consul KV store
- **`internal/backend/remote-state/pg/`**: PostgreSQL database
- **`internal/backend/remote-state/http/`**: Generic HTTP endpoint
- **`internal/backend/remote-state/kubernetes/`**: Kubernetes secrets
- **`internal/backend/remote-state/oss/`**: Alibaba Cloud OSS
- **`internal/backend/remote-state/cos/`**: Tencent Cloud COS
- **`internal/backend/remote-state/inmem/`**: In-memory (testing)

Each implements:
- `New()`: Factory function
- `backend.Backend` interface
- State manager via `internal/states/remote/client.go` interfaces:
  - `Client`: Get/Put/Delete state
  - `ClientLocker`: Optional locking (extends Client + statemgr.Locker)

#### Remote/Cloud Backends (Operations Backends)
- **`internal/backend/remote/`**: Remote Terraform Backend
  - Full `backendrun.OperationsBackend` implementation
  - Delegates operations to HCP Terraform/Terraform Enterprise
  - Wraps local backend for local execution fallback

- **`internal/cloud/`**: HCP Terraform / Cloud backend
  - Modern version of remote backend
  - Full workspace management and run orchestration
  - Hybrid execution modes (remote or local)

#### Backend Operation Interfaces
- **`internal/backend/backendrun/operation.go`**: Operation definition
  - `OperationsBackend`: Extended backend for plan/apply
  - `Operation`: Request structure for plan/apply/refresh operations
  - `OperationType`: Enum (plan, apply, destroy, refresh, etc.)
  - `RunningOperation`: Async operation handle

- **`internal/backend/backendrun/local_run.go`**: Local operation context
  - `LocalRun`: Objects needed to execute local operations
  - `terraform.Context`: Core context for plan/apply
  - Configuration, state, hooks

- **`internal/backend/backendrun/cli.go`**: CLI integration
  - `CLI`: Optional interface for backends needing user interaction
  - `CLIOpts`: Options (streams, paths, context, validation flags)

- **`internal/backend/backendrun/local.go`**: Local execution interface
  - `Local`: Operations requiring direct config/variable access
  - `LocalRun()`: Prepares objects for console, import, graph commands

#### Testing Utilities
- **`internal/backend/testing.go`**: Testing helpers for all backends
  - `TestBackendConfig()`: Configure backend for tests
  - `TestWrapConfig()`: Create synthetic HCL for tests
  - `TestBackendStates()`: Test workspace functionality
  - `TestBackendStateLocks()`: Test locking behavior
  - `TestBackendStateForceUnlock()`: Test force-unlock scenarios

- **`internal/backend/local/testing.go`**: Local backend test utilities
  - `TestLocalSingleState`: Workspace-less test backend
  - `TestLocalNoDefaultState`: No default workspace
  - Provides mock providers and contexts

---

## 4. Failure Modes

### State Locking Failures

**Stale Locks**:
- Occur when a process holding a lock crashes/terminates unexpectedly
- Lock remains in storage indefinitely
- **Recovery**: `terraform force-unlock <LOCK_ID>` manually releases the lock
- Implementation: `statemgr.LockWithContext()` includes user/hostname/timestamp in lock metadata for debugging

**Lock Acquisition Timeouts**:
- Configured via `state_lock_timeout` (default varies by backend)
- `LockWithContext()` retries with exponential backoff (1s → 16s max delay)
- **Failure Mode**: Operation aborts if timeout exceeded while waiting for lock release
- **Error Type**: `statemgr.LockError` returned by `Lock()` contains info about existing lock holder

**Lock Contention**:
- Multiple processes attempting simultaneous operations
- S3 backend uses DynamoDB conditional writes for atomicity
- Consul uses distributed lock sessions
- Kubernetes uses lease objects with TTLs

### Storage Unavailability

**Remote Endpoint Unreachable**:
- Network failures, service outages
- Backend `Configure()` stage may not catch this (validation deferred)
- Caught at first `RefreshState()` or `PersistState()` call
- **Error Handling**: Network errors propagated as-is; backends log retry attempts

**Missing Credentials/Permissions**:
- S3: IAM policy missing `s3:GetObject`, `s3:PutObject`
- Azure: Authentication token expired or insufficient permissions
- GCS: Service account missing Storage permissions
- Caught during `Configure()` or first state operation
- **Recovery**: Update credentials/environment and retry `terraform init`

**Storage Corruption**:
- State file becomes unreadable/invalid JSON
- S3 backend has checksum validation (MD5 in DynamoDB)
- **Detection**: `RefreshState()` returns parse error
- **Handling**: Manual state file inspection/recovery required; can restore from backup

### Configuration Errors

**Invalid Backend Configuration**:
- Missing required fields (e.g., S3 bucket, Azure container)
- Invalid values (malformed URL, bad encryption key)
- **Caught By**: `backend.PrepareConfig()` validates per schema
- Validation happens during `terraform init` before actual configuration

**Backend Type Changed**:
- Configuration specifies different backend than what's initialized
- Detected in `meta_backend.go` during `Backend()` call
- Prompts user: migrate state with `-migrate-state` or reconfigure with `-reconfigure`

**Incompatible State**:
- State created by newer Terraform version
- Detected via `version.Version` in state file
- `meta_backend_migrate.go` checks version compatibility before migration
- **Error**: Refuses to use incompatible state without explicit flag

### Workspace Issues

**Workspace Doesn't Exist**:
- Backend returns error from `StateMgr()` if workspace missing and backend doesn't auto-create
- Local backend creates on-demand; remote backends may require pre-creation
- Most backends auto-create on first `PersistState()`

**Workspace Deletion While In Use**:
- Backend prevents deletion of currently-selected workspace (requires lock)
- If force-deleted externally, next operation gets state not found error
- State can be recovered from backup if available

---

## 5. Testing

### Test Patterns for Backend Implementations

#### Configuration Testing
```go
// in *_test.go files
func TestBackendConfig(t *testing.T) {
    backend := New() // Initialize backend
    config := backend.TestWrapConfig(map[string]interface{}{
        "bucket": "my-bucket",
        "key": "terraform.tfstate",
        "region": "us-east-1",
    })
    configured := backend.TestBackendConfig(t, backend, config)
    // Backend now ready for state operations
}
```

#### State Operations Testing
```go
func TestBackendStates(t *testing.T) {
    // Helper in internal/backend/testing.go
    // Tests: workspace creation, listing, state persistence/retrieval
    backend.TestBackendStates(t, configuredBackend)
}
```

#### Locking Testing
```go
func TestBackendLocking(t *testing.T) {
    // Create two backend instances pointing to same storage
    b1 := backend.New()
    b2 := backend.New()
    backend.TestBackendConfig(t, b1, config)
    backend.TestBackendConfig(t, b2, config)

    // Test locking behavior
    backend.TestBackendStateLocks(t, b1, b2)
}
```

#### Force-Unlock Testing
```go
func TestForceUnlock(t *testing.T) {
    backend.TestBackendStateForceUnlock(t, b1, b2)
    // Verifies lock ID from error can be used to force-unlock
}
```

### Test Locations

- **Backend unit tests**: Each backend has `backend_test.go` and `client_test.go`
  - S3: `internal/backend/remote-state/s3/backend_test.go` (extensive, ~3000 lines)
  - Local: `internal/backend/local/backend_test.go`
  - Others follow similar pattern

- **State manager tests**: `internal/states/statemgr/`
  - `filesystem_test.go`: Filesystem state manager tests
  - `lock_test.go`: Locking mechanism tests
  - `statemgr_test.go`: Interface compliance tests

- **Integration tests**: `internal/command/` tests exercise backends through CLI
  - `internal/command/meta_backend.go` tested via CLI command tests

### Testing Infrastructure

- **Testing Backend Factory**: `internal/backend/init/init_test.go` provides test helper
- **Fake State**: `internal/states/statemgr/statemgr_fake.go` - fake implementation for testing
- **Lock Testing Hooks**: `postLockHook` in `locker.go` for test synchronization

---

## 6. Debugging

### Troubleshooting State Lock Issues

**Identify Lock Holder**:
```bash
# State file contains lock metadata in json format
# For S3 backend, check DynamoDB table:
aws dynamodb get-item \
  --table-name terraform-lock \
  --key '{"LockID":{"S":"my-bucket/terraform.tfstate"}}'

# Lock info includes:
# - ID: Unique lock identifier
# - Who: user@hostname
# - Version: Terraform version that locked state
# - Operation: What operation locked (plan, apply)
# - Created: Lock timestamp
```

**Release Stale Lock**:
```bash
terraform force-unlock <LOCK_ID>
# This calls backend.DeleteWorkspace() with force=true
# Bypasses lock check to forcibly remove
```

**Debug Lock Contention**:
- Enable Terraform debug logging: `TF_LOG=DEBUG terraform plan`
- Look for lock retry attempts with timestamps
- Check logs from `LockWithContext()` retry loop

### Verifying State Consistency

**S3 Backend**:
```bash
# Check state file exists in S3
aws s3 ls s3://bucket/path/terraform.tfstate

# Verify DynamoDB checksum matches
aws dynamodb get-item --table-name terraform-lock \
  --key '{"LockID":{"S":"bucket/terraform.tfstate-md5"}}'
```

**Local Backend**:
```bash
# State is plain JSON file
cat terraform.tfstate | jq .

# Check backup
cat terraform.tfstate.backup
```

**Filesystem Lock Status** (Unix):
```bash
# Check if lock file exists (indicates held lock)
ls -la terraform.tfstate.lock
```

### Available Diagnostics

- **TF_LOG Levels**:
  - `TRACE`: Most verbose, shows lock attempts, state I/O
  - `DEBUG`: Backend configuration, state operations
  - `INFO`: High-level operation summaries
  - `WARN`: Configuration warnings, deprecated backends

- **State Metadata**:
  - `statemgr.SnapshotMeta`: Contains Lineage (unique ID) and Serial (version number)
  - Serial increments on each state change for conflict detection
  - Lineage tracks state history across migrations

### Debugging State Corruption

**Symptom**: State doesn't parse / contains invalid JSON

**Investigation**:
```bash
# For remote backends, download and inspect
aws s3 cp s3://bucket/terraform.tfstate - | jq . 2>&1

# Check for:
# - Incomplete writes (missing closing braces)
# - Binary data in JSON
# - Special characters not escaped
```

**Prevention**:
- S3 backend validates checksums on read
- All backends use atomic writes (write-to-temp + move)
- `PersistState()` implementations must prevent concurrent writes

---

## 7. Adding a New Backend

### Step-by-Step Process

#### 1. Create Backend Directory Structure
```
internal/backend/remote-state/mybackend/
├── backend.go          # Backend interface implementation
├── client.go           # State read/write logic
├── lock.go             # Optional: locking implementation
└── backend_test.go     # Tests
```

#### 2. Implement Backend Configuration Schema

In `backend.go`:
```go
package mybackend

import (
    "github.com/zclconf/go-cty/cty"
    "github.com/hashicorp/terraform/internal/backend"
    "github.com/hashicorp/terraform/internal/configs/configschema"
    "github.com/hashicorp/terraform/internal/tfdiags"
)

type Backend struct {
    // Configuration fields
    endpoint string
    apiKey   string
    // Client for state operations
    client *RemoteClient
}

func New() backend.Backend {
    return &Backend{}
}

func (b *Backend) ConfigSchema() *configschema.Block {
    return &configschema.Block{
        Attributes: map[string]*configschema.Attribute{
            "endpoint": {
                Type:        cty.String,
                Required:    true,
                Description: "API endpoint URL",
            },
            "api_key": {
                Type:        cty.String,
                Required:    true,
                Description: "API authentication key",
                Sensitive:   true,
            },
        },
    }
}

func (b *Backend) PrepareConfig(obj cty.Value) (cty.Value, tfdiags.Diagnostics) {
    // Validation without side effects (no external calls)
    // Return modified config and diagnostics
    return obj, nil
}

func (b *Backend) Configure(obj cty.Value) tfdiags.Diagnostics {
    // Extract configuration values
    endpoint := obj.GetAttr("endpoint").AsString()
    apiKey := obj.GetAttr("api_key").AsString()

    b.endpoint = endpoint
    b.apiKey = apiKey

    // Initialize client
    b.client = &RemoteClient{
        endpoint: endpoint,
        apiKey:   apiKey,
    }

    // Validate connectivity (optional at this stage)
    // Most backends defer to first StateMgr call

    return nil
}
```

#### 3. Implement State Manager Interface

In `client.go`:
```go
package mybackend

import (
    "github.com/hashicorp/terraform/internal/states/remote"
    "github.com/hashicorp/terraform/internal/states/statemgr"
)

type RemoteClient struct {
    endpoint string
    apiKey   string
}

// Implement remote.Client interface
func (c *RemoteClient) Get() (*remote.Payload, error) {
    // Fetch state from remote storage
    // Return Payload with State bytes and MD5 checksum
}

func (c *RemoteClient) Put(data []byte) error {
    // Write state to remote storage
    // Should be atomic if possible
}

func (c *RemoteClient) Delete() error {
    // Remove state from storage (for workspace deletion)
}

// Implement statemgr.Locker if backend supports locking
func (c *RemoteClient) Lock(info *statemgr.LockInfo) (string, error) {
    // Attempt to acquire lock
    // Return lock ID or LockError with existing lock info
}

func (c *RemoteClient) Unlock(id string) error {
    // Release lock by ID
}
```

#### 4. Create State Manager Wrapper

The backend must return a `statemgr.Full` from `StateMgr()`. Use the helper:

In `backend.go`:
```go
func (b *Backend) StateMgr(workspace string) (statemgr.Full, error) {
    // Create or retrieve state for workspace
    // Most backends wrap RemoteClient with statemgr adapter

    client := &RemoteClient{...}

    // Use internal/states/remote package to wrap
    return &remoteStateManager{
        client:    client,
        workspace: workspace,
    }, nil
}
```

#### 5. Implement Workspace Management

```go
func (b *Backend) Workspaces() ([]string, error) {
    // List available workspaces
    // Can query remote API or return ["default"] if single-state
}

func (b *Backend) DeleteWorkspace(name string, force bool) error {
    // Remove workspace
    // If force=true, ignore lock
    // Otherwise check that state is locked before deletion
}
```

#### 6. Register Backend in Init Registry

In `internal/backend/init/init.go`, add to `Init()` function:
```go
func Init(services *disco.Disco) {
    backendsLock.Lock()
    defer backendsLock.Unlock()

    backends = map[string]backend.InitFn{
        // ... existing backends ...
        "mybackend": func() backend.Backend {
            return mybackendpkg.New()
        },
    }
}
```

Also add import:
```go
import (
    // ...
    backendMyBackend "github.com/hashicorp/terraform/internal/backend/remote-state/mybackend"
)
```

#### 7. Write Tests

In `backend_test.go`:
```go
func TestBackendConfig(t *testing.T) {
    b := New()
    config := backend.TestWrapConfig(map[string]interface{}{
        "endpoint": "https://api.example.com",
        "api_key":  "test-key",
    })

    backend.TestBackendConfig(t, b, config)
}

func TestBackendStates(t *testing.T) {
    // Setup backend with real/mocked remote service
    b := New()
    // ... configure ...
    backend.TestBackendStates(t, b)
}

func TestBackendLocks(t *testing.T) {
    b1 := New()
    b2 := New()
    // ... configure both ...
    backend.TestBackendStateLocks(t, b1, b2)
}
```

### Key Design Decisions

**Single-State vs. Multi-State**:
- Return `ErrWorkspacesNotSupported` from `Workspaces()` if single-state only
- HTTP backend example: typically single-state (one endpoint = one state)
- S3 backend example: multi-state via object path prefixes

**Locking Strategy**:
- **Distributed Lock Service**: Consul, etcd, DynamoDB (recommended)
- **Database Rows**: PostgreSQL locks rows in table
- **File-based**: Local filesystem fcntl/file locking (not suitable for remote)
- **No Locking**: inmem, HTTP backends (user responsibility)

**Atomicity Guarantees**:
- Write to temporary location, then atomic rename/move
- Or use remote service's conditional write API (DynamoDB ConditionExpression, S3 if-match)
- Never overwrite without ensuring you have latest state

**Checksum Validation**:
- Store MD5 alongside state for consistency verification
- On read: retry if checksum mismatches (eventual consistency)
- On write: verify write succeeded before claiming success

### Template: Minimal HTTP Backend

A simple backend for debugging:

```go
// internal/backend/remote-state/http/backend.go
package http

import (
    "io"
    "net/http"
    "github.com/hashicorp/terraform/internal/backend"
    "github.com/hashicorp/terraform/internal/states/remote"
    "github.com/hashicorp/terraform/internal/states/statemgr"
)

type Backend struct {
    url string
}

func (b *Backend) StateMgr(workspace string) (statemgr.Full, error) {
    client := &HTTPClient{url: b.url}
    return &stateManager{client: client}, nil
}

type HTTPClient struct {
    url string
}

func (c *HTTPClient) Get() (*remote.Payload, error) {
    resp, err := http.Get(c.url)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    data, _ := io.ReadAll(resp.Body)
    return &remote.Payload{Data: data}, nil
}

func (c *HTTPClient) Put(data []byte) error {
    req, _ := http.NewRequest("PUT", c.url, bytes.NewReader(data))
    _, err := http.DefaultClient.Do(req)
    return err
}
```

---

## Summary of Critical File Paths

| Component | Path |
|-----------|------|
| Backend Interface | `internal/backend/backend.go` |
| Registry | `internal/backend/init/init.go` |
| State Manager | `internal/states/statemgr/statemgr.go` |
| Locking | `internal/states/statemgr/locker.go` |
| Filesystem (Local) | `internal/states/statemgr/filesystem.go` |
| Local Backend | `internal/backend/local/backend.go` |
| Local Operations | `internal/backend/local/backend_*.go` |
| S3 Backend | `internal/backend/remote-state/s3/backend.go` |
| Remote Backend | `internal/backend/remote/backend.go` |
| Cloud Backend | `internal/cloud/backend.go` |
| Backend Operations | `internal/backend/backendrun/operation.go` |
| Testing Helpers | `internal/backend/testing.go` |
| CLI Integration | `internal/command/meta_backend.go` |
| State Migration | `internal/command/meta_backend_migrate.go` |

---

## Quick Reference: Adding Support for New Backend

1. **Create directory**: `internal/backend/remote-state/myname/`
2. **Implement** `backend.Backend` interface (ConfigSchema, PrepareConfig, Configure)
3. **Implement** `statemgr.Full` or wrap RemoteClient
4. **Register** in `internal/backend/init/init.go`
5. **Test** with `TestBackendConfig`, `TestBackendStates`, optionally `TestBackendStateLocks`
6. **Document** in `website/docs/language/settings/backends/myname.mdx`

The backend system is designed to be extensible but currently requires recompilation (backends are hardcoded, not plugins).
