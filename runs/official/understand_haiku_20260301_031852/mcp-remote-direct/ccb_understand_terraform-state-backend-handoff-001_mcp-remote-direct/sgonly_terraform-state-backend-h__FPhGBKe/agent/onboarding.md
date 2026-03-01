# Terraform State Backend Subsystem - Handoff Document

## Overview

This document provides a comprehensive guide to the Terraform state backend subsystem. The state backend is the core abstraction that allows Terraform to support multiple storage mechanisms while maintaining a unified CLI interface. This handoff covers architecture, key components, failure scenarios, testing patterns, debugging techniques, and the process for adding new backends.

---

## 1. Purpose

### Problem Statement
The state backend subsystem solves the fundamental problem of **how Terraform stores and retrieves state files** across diverse operational models and storage systems.

Terraform must support:
- **Local state**: Single-user development on a local machine
- **Remote state**: Team-based operations with centralized storage (S3, Azure, GCS, etc.)
- **Remote operations**: Fully remote execution (Terraform Cloud/Enterprise)
- **Mixed configurations**: Local execution with remote state storage

### Why Different Backend Types?

Different operational models require different semantics:

1. **Local Backend** (`internal/backend/local/backend.go:35-45`)
   - Executes operations locally on the user's machine
   - Manages workspaces as directories on the filesystem
   - Handles state locking using filesystem locks
   - Provides the baseline behavior for Terraform operations (plan, apply, refresh)

2. **Remote State Backends** (e.g., S3 at `internal/backend/remote-state/s3/`)
   - Store state in remote systems without executing operations remotely
   - Examples: S3, Azure Blob, GCS, PostgreSQL, HTTP, Consul, DynamoDB
   - Operations execute locally but state persists remotely
   - Often include state locking mechanisms (e.g., DynamoDB for S3)

3. **Operations Backends** (`internal/backend/remote/backend.go`, `internal/cloud/backend.go`)
   - Execute operations remotely (plan, apply runs)
   - Terraform Cloud/Enterprise is the primary example
   - Return streaming output from remote operations
   - Manage remote workspaces and run history

### Key Responsibilities of a Backend

A backend implementation must:

1. **Configuration Management** (ConfigSchema → PrepareConfig → Configure)
   - Define schema for backend configuration
   - Validate configuration values
   - Apply defaults

2. **State Management**
   - Provide state managers for named workspaces
   - Handle workspace creation, listing, and deletion
   - Coordinate transient (in-memory) and persistent (remote) state snapshots

3. **State Locking** (if supported)
   - Prevent concurrent modifications across multiple Terraform processes
   - Implement Lock/Unlock methods on state managers
   - Handle lock conflicts and timeouts

4. **Operations Support** (for enhanced backends)
   - Implement Plan, Apply, Refresh operations
   - Manage operation context and configuration loading
   - Handle state locking during operations
   - Stream operation output to the user

---

## 2. Dependencies

### Upstream Dependencies (What Calls Backends)

**Command Layer** (`internal/command/`)
- `meta_backend.go`: Backend initialization and configuration
- `meta_backend_migrate.go`: State migration between backends
- `init.go`: Backend initialization during `terraform init`
- Command implementations (apply, plan, refresh) that request operations

**Initialization System** (`internal/command/init.go`)
```go
// Key function: InitCommand.initBackend()
// Responsible for:
// 1. Loading backend config from terraform files
// 2. Discovering backend implementation
// 3. Configuring the backend
// 4. Performing state migration if needed
```

**Backend Registry** (`internal/backend/init/init.go:51-84`)
- Central registry of all available backends (hardcoded at compile time)
- Backends list (v1.9.0):
  - Local, Remote (Terraform Cloud/Enterprise)
  - Remote state: S3, Azure, GCS, HTTP, Consul, PostgreSQL, OSS, Kubernetes, COS, In-Memory

### Downstream Dependencies (What Backends Call)

**State Management System** (`internal/states/statemgr/`)
- Interfaces: `Full`, `Storage`, `Transient`, `Persistent`, `Locker`
- Implementations: `Filesystem`, `TransientInMemory`
- Key concept: State managers implement both transient (in-memory) and persistent (remote) storage

**Configuration System** (`internal/configs/configschema/`)
- Schema definition for backend configuration blocks
- Attribute type definitions (string, number, bool, list, object, etc.)

**State Locking** (`internal/states/statemgr/locker.go`)
- Lock/Unlock operations with `LockInfo` metadata
- `LockWithContext()` helper for retry logic
- Lock timeout and conflict handling

**Terraform Context** (`internal/terraform/context.go`)
- Used by local backend to create evaluation contexts
- Applies configuration, computes changes, executes resource operations

### Architecture Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                       CLI Commands                           │
│              (apply, plan, refresh, init, etc.)              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌────────────────────────────────┐
        │  Backend Interface (abstract)   │
        │  - ConfigSchema()               │
        │  - PrepareConfig()              │
        │  - Configure()                  │
        │  - StateMgr()                   │
        │  - Workspaces()                 │
        │  - DeleteWorkspace()            │
        └────┬──────────────────────┬─────┘
             │                      │
    ┌────────▼─────────┐   ┌────────▼────────────┐
    │ Local Backend     │   │ Remote State Backends│
    │ (Operations)      │   │ (S3, Azure, etc.)    │
    │                   │   │ (State only)         │
    │ Remote Ops Backend│   │                      │
    │ (Cloud/Terraform) │   │ Operations Backend   │
    └────────┬─────────┘   │ (Cloud/TFE)          │
             │             └────────┬──────────────┘
             │                      │
             └──────────┬───────────┘
                        │
            ┌───────────▼────────────┐
            │  State Manager (Full)   │
            │  - Transient (Reader)   │
            │  - Persistent (Refresher/Persister)
            │  - Locker               │
            └────────┬────────────────┘
                     │
        ┌────────────▼──────────────┐
        │  Persistent Storage        │
        │  (Filesystem, S3, GCS,     │
        │   Database, etc.)          │
        └───────────────────────────┘
```

---

## 3. Relevant Components

### Core Backend Interface

**File**: `internal/backend/backend.go`

```go
type Backend interface {
    ConfigSchema() *configschema.Block           // Return config schema
    PrepareConfig(cty.Value) (cty.Value, tfdiags.Diagnostics)  // Validate & default
    Configure(cty.Value) tfdiags.Diagnostics    // Apply configuration
    StateMgr(workspace string) (statemgr.Full, error)  // Get state manager
    DeleteWorkspace(name string, force bool) error     // Remove workspace
    Workspaces() ([]string, error)                     // List workspaces
}
```

**Key Constants**:
- `DefaultStateName = "default"`: All backends must have a "default" workspace
- `ErrDefaultWorkspaceNotSupported`: Returned when operation requires named workspace
- `ErrWorkspacesNotSupported`: Returned when backend doesn't support multiple workspaces

### Backend Operations Interface

**File**: `internal/backend/backendrun/operation.go`

```go
type OperationsBackend interface {
    backend.Backend
    Operation(context.Context, *Operation) (*RunningOperation, error)
    ServiceDiscoveryAliases() ([]HostAlias, error)
}
```

**Supporting Types**:
- `Operation`: Describes a plan/apply/refresh operation with configuration, hooks, UI, state locker
- `RunningOperation`: Contains context, stop/cancel channels, result status, final state
- `OperationType`: Enum (Refresh, Plan, Apply, Invalid)

### Local Backend

**Files**: `internal/backend/local/`

**Core Files**:
- `backend.go`: Main backend implementation
- `backend_plan.go`: Plan operation implementation
- `backend_apply.go`: Apply operation implementation
- `backend_refresh.go`: Refresh operation implementation
- `backend_local.go`: LocalRun interface for local operation context

**Key Structures**:
```go
type Local struct {
    StatePath string              // Path to state file
    StateOutPath string            // Path for output state
    StateBackupPath string         // Path for backup
    StateWorkspaceDir string       // Directory for workspace states

    OverrideStatePath string       // CLI override for state path
    OverrideStateOutPath string    // CLI override for output path
    OverrideStateBackupPath string // CLI override for backup path

    states map[string]statemgr.Full // Cached state managers

    ContextOpts *terraform.ContextOpts
    Backend backend.Backend  // Wrapped remote-state backend (optional)

    opLock sync.Mutex  // Synchronize operations
}
```

**Workspace Storage**:
- Default workspace: State file at root (`terraform.tfstate`)
- Named workspaces: State directories at `terraform.tfstate.d/{workspace-name}/`
- Backup files: `.backup` extension (disabled with `-`)

**Operation Flow**:
1. `Operation()` method spawns goroutine for async execution
2. Creates terraform.Context with configuration and state
3. Executes plan/apply/refresh via context methods
4. Returns RunningOperation with context to block on completion

### State Manager System

**Files**: `internal/states/statemgr/`

**Core Interfaces**:

1. **Full** (composite interface)
   ```go
   type Full interface {
       Storage    // Transient + Persistent
       Locker     // Lock/Unlock
   }
   ```

2. **Storage** (composite interface)
   ```go
   type Storage interface {
       Transient   // Reader + Writer (in-memory)
       Persistent  // Refresher + Persister + OutputReader (remote)
   }
   ```

3. **Transient** (in-memory snapshots)
   ```go
   type Reader interface {
       State() *states.State  // Get current transient state
   }
   type Writer interface {
       WriteState(*states.State) error  // Update transient state
   }
   ```

4. **Persistent** (remote storage)
   ```go
   type Refresher interface {
       RefreshState() error  // Load from remote storage
   }
   type Persister interface {
       PersistState(*schemarepo.Schemas) error  // Save to remote storage
   }
   type OutputReader interface {
       GetRootOutputValues(ctx context.Context) (map[string]*states.OutputValue, error)
   }
   ```

5. **Locker** (mutual exclusion)
   ```go
   type Locker interface {
       Lock(info *LockInfo) (string, error)  // Acquire lock, returns lock ID
       Unlock(id string) error                // Release lock
   }
   ```

**LockInfo Structure**:
```go
type LockInfo struct {
    ID        string    // Unique lock ID (UUID)
    Operation string    // Operation type (plan, apply, refresh)
    Info      string    // Extra information
    Who       string    // user@hostname
    Version   string    // Terraform version
    Created   time.Time // Lock creation time
    Path      string    // State file path (set by implementation)
}
```

**Lock Error Handling**:
- `LockError` struct wraps conflict info
- `LockWithContext()` implements retry logic with exponential backoff (1s → 16s max)
- Respects context timeout and cancellation

**Key Implementations**:

1. **Filesystem** (`filesystem.go`)
   - Reads from `readPath`, writes to `path`
   - Supports backup files (optional)
   - Platform-specific locking (Unix: fcntl, Windows: LockFileEx)
   - Atomic writes via temp file + rename

2. **TransientInMemory** (`transient_inmem.go`)
   - In-memory state snapshots only
   - Used as transient storage by most backends

### Remote State Backends

**Location**: `internal/backend/remote-state/{backend-type}/`

**Examples**:
- **S3** (`s3/`): AWS S3 bucket + DynamoDB table for locking
- **Azure** (`azure/`): Azure Blob Storage + Blob leasing for locking
- **GCS** (`gcs/`): Google Cloud Storage + state versioning
- **HTTP** (`http/`): Generic HTTP/REST endpoint
- **PostgreSQL** (`pg/`): Database table storage
- **Consul** (`consul/`): Consul KV store
- **Kubernetes** (`kubernetes/`): Kubernetes Secrets

**Common Pattern** (using S3 as example):

1. **Configuration Schema** (`backend.go:ConfigSchema()`)
   - Define required and optional attributes
   - Include descriptions and deprecation warnings

2. **Configuration Preparation** (`backend.go:PrepareConfig()`)
   - Validate syntax
   - Insert defaults
   - No external API calls

3. **Configuration Application** (`backend.go:Configure()`)
   - Initialize clients (AWS SDK, HTTP client, etc.)
   - Connect to remote system
   - Validate connectivity and permissions

4. **StateMgr Implementation** (`backend.go:StateMgr()`)
   - Return a `Full` state manager for the workspace
   - Create workspace/state object if needed
   - Handle workspace-specific configuration

### Backend Initialization System

**File**: `internal/backend/init/init.go`

**Registry Mechanism**:
```go
var backends map[string]backend.InitFn  // Global registry
var backendsLock sync.Mutex

func Init(services *disco.Disco) {
    backends = map[string]backend.InitFn{
        "local": func() backend.Backend { return backendLocal.New() },
        "remote": func() backend.Backend { return backendRemote.New(services) },
        "s3": func() backend.Backend { return backendS3.New() },
        // ... 10 more backends
    }

    RemovedBackends = map[string]string{
        "artifactory": "...",
        "etcd": "...",
        // ... removed backends with deprecation messages
    }
}

func Backend(name string) backend.InitFn {
    backendsLock.Lock()
    defer backendsLock.Unlock()
    return backends[name]
}
```

**Deprecation Pattern**:
```go
type deprecatedBackendShim struct {
    backend.Backend
    Message string
}

func (b deprecatedBackendShim) PrepareConfig(obj cty.Value) (cty.Value, tfdiags.Diagnostics) {
    newObj, diags := b.Backend.PrepareConfig(obj)
    return newObj, diags.Append(tfdiags.SimpleWarning(b.Message))
}
```

### Backend Configuration Loading

**Files**: `internal/command/meta_backend.go`, `internal/command/init.go`

**BackendOpts Structure**:
```go
type BackendOpts struct {
    Config *configs.Backend         // From terraform block
    ConfigOverride hcl.Body         // From -backend-config flags
    Init bool                        // Allow initialization?
    ForceLocal bool                 // Ignore config, use local?
    ViewType arguments.ViewType     // Output format (JSON/text)
}
```

**Key Functions**:
- `Meta.Backend(opts)`: Main entry point for backend initialization
- `initBackend()`: Loads backend configuration, discovers backend type
- `backendFromConfig()`: Instantiates and configures backend
- `savedBackend()`: Loads previously saved backend configuration

**Configuration Migration**:
- Old backend config stored in `.terraform/terraform.tfstate`
- On `terraform init`, detects changes and prompts for migration
- `backendMigrateState()` handles state copying between backends

---

## 4. Failure Modes

### Configuration Errors

**Invalid Backend Type**:
```
Error: Invalid backend type
Reason: There is no backend type named "invalid".

Available backends:
  - local
  - remote
  - s3
  - azurerm
  ...
```
**File**: `internal/command/init.go:441-446`
**Code**: Check against `backendInit.Backend()` return, look up `backendInit.RemovedBackends`

**Invalid Configuration**:
```
Error: Invalid backend configuration
Reason: The "bucket" attribute is required.
```
**File**: `internal/backend/backend.go:52-70`
**Code**: `PrepareConfig()` validates schema, returns diagnostics

**Configure Failures**:
- AWS credentials not available/invalid
- Network connectivity issues
- Permissions denied to remote storage
- **Handling**: Return diagnostics from `Configure()`, which blocks backend initialization

### State Locking Failures

**Lock Acquisition Timeout**:
```
Error: Error acquiring the state lock
Lock Info:
  ID:        abc123-def456-...
  Path:      terraform.tfstate
  Operation: apply
  Who:       user@hostname
  Version:   1.9.0
  Created:   2024-01-15T14:30:00Z
  Info:      Another Terraform process is running
```
**File**: `internal/states/statemgr/locker.go:75-111`
**Mechanism**:
- `LockWithContext()` retries with exponential backoff (1s, 2s, 4s, 8s, 16s)
- Returns `LockError` with conflicting lock info
- Respects context timeout

**Stale Locks**:
- Occurs when Terraform process dies without releasing lock
- Lock file contains metadata: Who, When, Version, Operation
- **Solution**: Manual `terraform force-unlock <lock-id>`
- **Prevention**: Proper error handling ensures unlock on exit

**Lock Conflicts**:
```
Another operation is already in progress on this state.
Trying to acquire the lock will block until it's released.

Current Lock:
  ID:        xxx
  Operation: apply
  Who:       user@host
  Created:   2 hours ago

Waiting for lock...
```
**Code**: `internal/command/clistate/locker.go` - CLI lock wrapper with output

### State Storage Failures

**Network Connectivity**:
- S3 bucket unreachable
- Database server down
- HTTP endpoint timeout
- **Handling**: Returned as errors from `RefreshState()` or `PersistState()`
- **Impact**: Operations fail early, state not modified

**Concurrent Modifications**:
**Mechanism** (S3 example):
```go
// S3 detects concurrent writes via:
// 1. ETag comparison (MD5 of object)
// 2. Serial number in state file
// 3. Lineage matching
```
**File**: `internal/states/statefile/` - State version tracking
**Behavior**: `PersistState()` detects mismatch, returns error
**CLI Behavior**: User must resolve conflict (merge/retry)

**Permissions Issues**:
- Write denied to state file
- DynamoDB table unreadable
- KMS key unavailable (for encrypted state)
- **Impact**: Operations fail, user needs to fix permissions

### State Corruption

**Corrupted State File**:
- Invalid JSON
- Missing required fields
- **Detection**: Happens during `RefreshState()` unmarshaling
- **Prevention**: Backup files created before writes
- **Recovery**: Use `.backup` file or restore from version control

**Inconsistent Lineage**:
- State has different lineage than expected
- Indicates state was modified outside Terraform
- **Detection**: Lineage mismatch during refresh
- **User Action**: Investigate, possibly use `-refresh=false` to preserve state

### Workspace Errors

**Default Workspace Missing**:
```
Error: Cannot find default state
The "default" workspace must exist and is required.
```
**Code**: `internal/backend/backend.go:28-29` - ErrDefaultWorkspaceNotSupported
**When**: Backend doesn't support default workspace (rare)

**Workspace Not Supported**:
```
Error: Workspace operations not supported
The configured backend does not support multiple workspaces.
Use the "local" backend or a backend that supports workspaces.
```
**Code**: `internal/backend/backend.go:34-37` - ErrWorkspacesNotSupported
**Backends Affected**: Some HTTP backends, in-memory backend
**Workaround**: Use local backend or switch backend type

**Workspace Deletion Conflicts**:
```
Error: Cannot delete workspace with active lock
The workspace is currently locked by another process.
```
**Code**: `internal/backend/backend.go:96-101` - DeleteWorkspace contract requires lock held by caller
**Prevention**: Always ensure workspace isn't in use before deletion

### Backend-Specific Failures

**S3 Backend** (`internal/backend/remote-state/s3/`):
- S3 bucket doesn't exist
- DynamoDB table doesn't exist (for state locking)
- Insufficient IAM permissions
- Region mismatch
- KMS key errors (if using encryption)

**Azure Backend** (`internal/backend/remote-state/azure/`):
- Storage account not found
- Container doesn't exist
- Authentication failure (MSI, SAS token, storage key)
- Blob lease expiration (lock timeout)

**GCS Backend** (`internal/backend/remote-state/gcs/`):
- Bucket not found
- Service account permissions
- GCS API not enabled
- Bucket versioning misconfiguration

---

## 5. Testing

### Test Patterns and Locations

**Backend Interface Tests**:
- **File**: `internal/backend/testing.go`
- **Purpose**: Provides generic test suite for backend implementations
- **Key Function**: `TestBackendType(name string, be backend.Backend, opts *BackendTests)`

**Local Backend Tests**:
- **Files**: `internal/backend/local/backend_test.go`, `backend_plan_test.go`, `backend_apply_test.go`, etc.
- **Pattern**: Unit tests for specific operations
- **Key Tests**:
  - Plan/apply/refresh operations
  - State persistence
  - Error handling
  - Workspace operations

**State Manager Tests**:
- **Files**: `internal/states/statemgr/filesystem_test.go`, `lock_test.go`, `statemgr_test.go`
- **Coverage**:
  - State read/write
  - Locking mechanics
  - Backup file creation
  - Concurrent access
  - Platform-specific locking (Unix/Windows)

**Remote State Backend Tests**:
- **Pattern**: Each backend has `backend_test.go` and `client_test.go`
- **Example**: `internal/backend/remote-state/s3/backend_test.go`
- **Approach**:
  - Unit tests with mocked cloud SDK
  - Integration tests against real services (optional, behind build tags)
  - Config validation tests

**Mocking Patterns**:
```go
// Example: Mock HTTP backend response
type mockHTTPBackend struct {
    responses map[string][]byte
    mu        sync.RWMutex
}

func (m *mockHTTPBackend) Handle(r *http.Request) (*http.Response, error) {
    m.mu.RLock()
    defer m.mu.RUnlock()

    if body, ok := m.responses[r.URL.String()]; ok {
        return &http.Response{
            StatusCode: 200,
            Body:       io.NopCloser(bytes.NewReader(body)),
        }, nil
    }
    return nil, errors.New("not found")
}
```

**State Locking Tests**:
- **File**: `internal/states/statemgr/lock_test.go`
- **Tests**:
  - Lock acquisition and release
  - Concurrent lock attempts
  - Lock timeout handling
  - Stale lock detection
  - Force unlock behavior

**Testing Utilities**:

**File**: `internal/backend/testing.go`
```go
// TestBackend() helper runs standard backend tests
func TestBackend(t testing.TB, be backend.Backend, opts *BackendTests) {
    // Tests: ConfigSchema, PrepareConfig, Configure, StateMgr,
    // Workspaces, DeleteWorkspace, etc.
}
```

**File**: `internal/states/statemgr/testing.go`
```go
// Tests for state manager implementations
// Validates Full interface compliance
```

**File**: `internal/backend/local/testing.go`
```go
// Helpers for testing local backend operations
// Setup/teardown for operations, state cleanup
```

### Test Execution Examples

**Run all backend tests**:
```bash
go test ./internal/backend/...
```

**Run specific backend tests**:
```bash
go test ./internal/backend/local -run TestLocalBackend
go test ./internal/backend/remote-state/s3 -run TestBackend
```

**Run state manager tests**:
```bash
go test ./internal/states/statemgr -run TestFilesystem
go test ./internal/states/statemgr -run TestLocking
```

**With coverage**:
```bash
go test -cover ./internal/backend/...
```

### Integration Test Locations

**E2E Tests**:
- **Files**: `internal/command/e2etest/`, `internal/cloud/e2e/`
- **Pattern**: Full Terraform workflow tests
- **Coverage**: init → plan → apply → state verification

**Backend Migration Tests**:
- **File**: `internal/command/meta_backend_migrate_test.go`
- **Tests**: State migration between backend types

---

## 6. Debugging

### Troubleshooting State Lock Issues

**Enable Debug Logging**:
```bash
TF_LOG=DEBUG terraform apply
# or
TF_LOG=TRACE terraform apply

# Save to file:
TF_LOG=TRACE TF_LOG_PATH=./terraform.log terraform apply
```

**Log File Analysis**:
- Search for `[TRACE] backend/local` messages
- Look for `Lock()`/`Unlock()` calls
- Check lock acquisition timeline

**Example Trace**:
```
[TRACE] backend/local: requesting state manager for workspace "default"
[TRACE] backend/local: requesting state lock for workspace "default"
[TRACE] statemgr: lock acquired, ID: abc123-def456
[TRACE] backend/local: reading remote state for workspace "default"
```

**Inspecting Lock Files**:

**Filesystem Lock** (Local backend):
```bash
# Lock file location: {state-file}.lock

cat terraform.tfstate.lock

# Contains: JSON with lock metadata
{
  "ID": "abc123-def456-789ghi",
  "Operation": "apply",
  "Info": "Manual lock for debugging",
  "Who": "user@hostname",
  "Version": "1.9.0",
  "Created": "2024-01-15T14:30:00Z",
  "Path": "terraform.tfstate"
}
```

**DynamoDB Lock** (S3 backend):
```bash
# Check DynamoDB table for locks
aws dynamodb scan \
  --table-name terraform-locks \
  --region us-east-1

# Item example:
{
  "LockID": {"S": "bucket-name/path/to/state.tfstate"},
  "Info": {"S": "Operation=apply, Who=user@host, ..."},
  "Digest": {"S": "hashofstate"}
}
```

**Detecting Stale Locks**:

```bash
# Check lock creation time
# If it's hours/days old, it's likely stale

# Local backend:
stat terraform.tfstate.lock

# For remote backends, check their mechanism:
# - S3/DynamoDB: Check lock table timestamps
# - Azure: Check blob lease
# - Consul: Check key TTL
```

**Forcing Lock Release**:
```bash
# Built-in command
terraform force-unlock <lock-id>

# Manual removal (local filesystem):
rm terraform.tfstate.lock

# Manual removal (remote):
# S3: aws dynamodb delete-item --table-name terraform-locks ...
# Azure: az storage blob release-lease --container-name ...
```

### Verifying State Consistency

**Check State File Directly**:
```bash
# View state file JSON
terraform state list              # Show all resources
terraform state show 'resource.type.name'

# Pull state from remote backend
terraform state pull > state.backup

# Export as JSON for analysis
terraform show -json
```

**Verify Lineage and Serial**:
```bash
# In terraform.tfstate:
{
  "version": 4,
  "terraform_version": "1.9.0",
  "serial": 15,
  "lineage": "abc123-def456-789ghi",
  "outputs": { ... },
  "resources": [ ... ]
}

# Serial: incremented on each apply (should be monotonic)
# Lineage: should match if states were migrated from same origin
```

**Detect Concurrent Modifications**:
```bash
# On conflict:
Error: Error writing state file
Failed to persist state: the state has been modified by another process

# Solution: Pull latest, merge, push manually
terraform state pull
# ... inspect and edit if needed ...
terraform state push terraform.tfstate
```

### Debugging Backend Configuration

**Test Backend Configuration**:
```bash
# Validate terraform config (no provider calls)
terraform validate

# Try to load backend (no state operations)
terraform init -upgrade

# Check what backend is loaded:
grep -A 10 "terraform" .terraform/terraform.tfstate
```

**Backend Configuration File**:
```bash
# Location: .terraform/terraform.tfstate
# Contains: Serialized backend configuration after last init

cat .terraform/terraform.tfstate | jq '.backend'
```

**Trace Backend Initialization**:
```bash
TF_LOG=DEBUG terraform init -backend=true

# Look for:
# [DEBUG] command/init: loaded backend config
# [TRACE] Meta.Backend: instantiated backend of type
# [TRACE] Meta.Backend: backend %T supports operations
```

### Common Issues and Diagnostics

**Issue: "Error loading state" during operations**

```
Steps to diagnose:
1. Check backend connectivity
   terraform state pull

2. Check state file permissions
   ls -la terraform.tfstate

3. Check authentication credentials
   AWS: aws sts get-caller-identity
   Azure: az account show

4. Enable debug logging
   TF_LOG=TRACE terraform plan
```

**Issue: Lock timeout on operations**

```
Steps to diagnose:
1. Check for concurrent operations
   ps aux | grep terraform

2. Inspect lock age
   stat .terraform.lock.hcl  # local
   aws dynamodb scan --table-name terraform-locks  # S3

3. Check network/API latency
   time terraform state pull

4. Force unlock if needed
   terraform force-unlock <lock-id>
```

**Issue: State migration failures**

```
Steps to diagnose:
1. Check old backend still accessible
   terraform state pull -backup=/tmp/old.tfstate

2. Verify new backend connectivity
   terraform init -reconfigure -backend=false

3. Try migration with copy
   terraform init -migrate-state -reconfigure

4. Manual migration as fallback
   terraform state pull > state.backup
   # Switch backend config
   terraform init
   terraform state push state.backup
```

### Logging and Observability

**Terraform Logging Levels**:
- `TRACE`: Most verbose, all operations logged
- `DEBUG`: Operation and resource events
- `INFO`: Important messages only
- `WARN`: Warnings and errors
- `ERROR`: Errors only

**Log Output Locations**:
```bash
# Console output
terraform apply -input=false

# File logging
TF_LOG_PATH=/var/log/terraform.log TF_LOG=DEBUG terraform apply

# Separate logs by component
TF_LOG_EXCLUDE=core,provisioner TF_LOG=DEBUG terraform apply
```

**Key Components to Log**:
- `backend`: Backend initialization and operations
- `statemgr`: State manager read/write/lock
- `configs`: Configuration loading
- `states`: State parsing

---

## 7. Adding a New Backend

### Step-by-Step Process

#### Step 1: Create Backend Directory

```bash
mkdir -p internal/backend/remote-state/newservice
cd internal/backend/remote-state/newservice
```

#### Step 2: Implement Configuration Schema

**File**: `internal/backend/remote-state/newservice/backend.go`

```go
package newservice

import (
    "github.com/zclconf/go-cty/cty"
    "github.com/hashicorp/terraform/internal/backend"
    "github.com/hashicorp/terraform/internal/configs/configschema"
    "github.com/hashicorp/terraform/internal/tfdiags"
)

func New() backend.Backend {
    return &Backend{}
}

type Backend struct {
    // Configuration fields
    bucketName string
    keyPrefix  string
    region     string

    // Client fields
    client *NewServiceClient
}

// ConfigSchema returns the schema for backend configuration
func (b *Backend) ConfigSchema() *configschema.Block {
    return &configschema.Block{
        Attributes: map[string]*configschema.Attribute{
            "bucket": {
                Type:        cty.String,
                Required:    true,
                Description: "The bucket name",
            },
            "key_prefix": {
                Type:        cty.String,
                Optional:    true,
                Description: "Prefix for state keys",
            },
            "region": {
                Type:        cty.String,
                Optional:    true,
                Description: "Service region",
            },
        },
    }
}

// PrepareConfig validates and defaults configuration
func (b *Backend) PrepareConfig(obj cty.Value) (cty.Value, tfdiags.Diagnostics) {
    var diags tfdiags.Diagnostics

    // Validate bucket is not empty
    if val := obj.GetAttr("bucket"); !val.IsNull() {
        bucket := val.AsString()
        if bucket == "" {
            diags = diags.Append(tfdiags.AttributeValue(
                tfdiags.Error,
                "Invalid bucket name",
                `The "bucket" attribute must not be empty`,
                cty.Path{cty.GetAttrStep{Name: "bucket"}},
            ))
        }
    }

    return obj, diags
}

// Configure applies configuration to backend
func (b *Backend) Configure(obj cty.Value) tfdiags.Diagnostics {
    var diags tfdiags.Diagnostics

    // Extract configuration
    b.bucketName = obj.GetAttr("bucket").AsString()
    if val := obj.GetAttr("key_prefix"); !val.IsNull() {
        b.keyPrefix = val.AsString()
    } else {
        b.keyPrefix = "terraform/"
    }
    if val := obj.GetAttr("region"); !val.IsNull() {
        b.region = val.AsString()
    } else {
        b.region = "default"
    }

    // Initialize client
    var err error
    b.client, err = NewClient(b.bucketName, b.region)
    if err != nil {
        diags = diags.Append(fmt.Errorf("failed to initialize client: %w", err))
        return diags
    }

    return diags
}

// Workspaces lists available workspaces
func (b *Backend) Workspaces() ([]string, error) {
    workspaces := []string{backend.DefaultStateName}

    named, err := b.client.ListWorkspaces(b.keyPrefix)
    if err != nil {
        return nil, err
    }

    workspaces = append(workspaces, named...)
    return workspaces, nil
}

// DeleteWorkspace removes a workspace
func (b *Backend) DeleteWorkspace(name string, force bool) error {
    if name == backend.DefaultStateName {
        return errors.New("cannot delete default workspace")
    }

    return b.client.DeleteWorkspace(b.keyPrefix + name)
}

// StateMgr returns state manager for workspace
func (b *Backend) StateMgr(workspace string) (statemgr.Full, error) {
    // Validate workspace name
    if workspace == "" {
        workspace = backend.DefaultStateName
    }

    // Create state key path
    stateKey := b.keyPrefix + workspace

    // Return state manager for this workspace
    return NewStateManager(b.client, stateKey), nil
}
```

#### Step 3: Implement State Manager

**File**: `internal/backend/remote-state/newservice/state_manager.go`

```go
package newservice

import (
    "context"
    "github.com/hashicorp/terraform/internal/states"
    "github.com/hashicorp/terraform/internal/states/statemgr"
    "github.com/hashicorp/terraform/internal/schemarepo"
)

type StateManager struct {
    client *NewServiceClient
    key    string

    // Transient in-memory state
    transient *statemgr.TransientInMemory
}

func NewStateManager(client *NewServiceClient, key string) *StateManager {
    return &StateManager{
        client:    client,
        key:       key,
        transient: statemgr.NewTransientInMemory(),
    }
}

// Implement Full interface
var _ statemgr.Full = (*StateManager)(nil)

// Reader implementation
func (s *StateManager) State() *states.State {
    return s.transient.State()
}

// Writer implementation
func (s *StateManager) WriteState(state *states.State) error {
    return s.transient.WriteState(state)
}

// Refresher implementation
func (s *StateManager) RefreshState() error {
    data, err := s.client.GetState(s.key)
    if err != nil {
        return err
    }

    // Unmarshal state
    state, err := statemgr.UnmarshalState(data)
    if err != nil {
        return err
    }

    return s.transient.WriteState(state)
}

// Persister implementation
func (s *StateManager) PersistState(schemas *schemarepo.Schemas) error {
    state := s.transient.State()

    // Marshal state
    data, err := statemgr.MarshalState(state, schemas)
    if err != nil {
        return err
    }

    // Upload to service
    return s.client.PutState(s.key, data)
}

// OutputReader implementation
func (s *StateManager) GetRootOutputValues(ctx context.Context) (map[string]*states.OutputValue, error) {
    state := s.State()
    if state == nil {
        return nil, nil
    }
    return state.RootModule().OutputValues, nil
}

// Locker implementation (optional, return errors if not supported)
func (s *StateManager) Lock(info *statemgr.LockInfo) (string, error) {
    lockID, err := s.client.Lock(s.key, info)
    if err != nil {
        return "", &statemgr.LockError{
            Info: info,
            Err:  err,
        }
    }
    return lockID, nil
}

func (s *StateManager) Unlock(id string) error {
    return s.client.Unlock(s.key, id)
}
```

#### Step 4: Implement Client

**File**: `internal/backend/remote-state/newservice/client.go`

```go
package newservice

import (
    "fmt"
    "net/http"
)

type NewServiceClient struct {
    baseURL    string
    httpClient *http.Client
}

func NewClient(bucket, region string) (*NewServiceClient, error) {
    // Initialize HTTP client with auth, TLS, etc.
    httpClient := &http.Client{}

    baseURL := fmt.Sprintf("https://api.newservice.com/%s/%s", region, bucket)

    return &NewServiceClient{
        baseURL:    baseURL,
        httpClient: httpClient,
    }, nil
}

func (c *NewServiceClient) GetState(key string) ([]byte, error) {
    // Fetch state from remote service
    resp, err := c.httpClient.Get(c.baseURL + "/" + key)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    // Handle errors
    if resp.StatusCode == 404 {
        return nil, nil  // No state yet
    }
    if resp.StatusCode != 200 {
        return nil, fmt.Errorf("failed to get state: %s", resp.Status)
    }

    // Read response body
    var buf bytes.Buffer
    _, err = io.Copy(&buf, resp.Body)
    return buf.Bytes(), err
}

func (c *NewServiceClient) PutState(key string, data []byte) error {
    // Upload state to remote service
    req, err := http.NewRequest("PUT", c.baseURL+"/"+key, bytes.NewReader(data))
    if err != nil {
        return err
    }

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode != 200 && resp.StatusCode != 204 {
        return fmt.Errorf("failed to put state: %s", resp.Status)
    }

    return nil
}

func (c *NewServiceClient) Lock(key string, info *statemgr.LockInfo) (string, error) {
    // Implement locking mechanism
    // Return lock ID or error
    lockID := generateLockID()  // Use UUID

    // Store lock in service
    req, _ := http.NewRequest("POST", c.baseURL+"/"+key+"/lock",
        bytes.NewReader(info.Marshal()))

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    if resp.StatusCode == 409 {
        // Lock already exists, parse and return error
        // ... return *LockError
    }

    return lockID, nil
}

func (c *NewServiceClient) Unlock(key string, id string) error {
    // Release lock
    req, _ := http.NewRequest("DELETE", c.baseURL+"/"+key+"/lock/"+id, nil)

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    return nil
}

// Other helper methods
func (c *NewServiceClient) ListWorkspaces(prefix string) ([]string, error) { /* ... */ }
func (c *NewServiceClient) DeleteWorkspace(key string) error { /* ... */ }
```

#### Step 5: Add Tests

**File**: `internal/backend/remote-state/newservice/backend_test.go`

```go
package newservice

import (
    "testing"
    "github.com/hashicorp/terraform/internal/backend"
)

func TestBackend(t *testing.T) {
    b := New()

    // Test ConfigSchema
    schema := b.ConfigSchema()
    if schema == nil {
        t.Fatal("schema is nil")
    }

    if _, ok := schema.Attributes["bucket"]; !ok {
        t.Error("bucket attribute missing")
    }
}

func TestStateMgr(t *testing.T) {
    // Create mock client
    client := &mockNewServiceClient{}

    // Create state manager
    sm := NewStateManager(client, "test-state")

    // Test state operations
    // ... test Read/Write/Refresh/Persist
}
```

#### Step 6: Register Backend

**File**: `internal/backend/init/init.go` - Update the `Init()` function

```go
func Init(services *disco.Disco) {
    backendsLock.Lock()
    defer backendsLock.Unlock()

    backends = map[string]backend.InitFn{
        "local": func() backend.Backend { return backendLocal.New() },
        // ... existing backends ...

        // Add new backend:
        "newservice": func() backend.Backend { return backendNewService.New() },
    }
}
```

Add import:
```go
import (
    // ... existing imports ...
    backendNewService "github.com/hashicorp/terraform/internal/backend/remote-state/newservice"
)
```

#### Step 7: Documentation

**File**: `website/docs/language/settings/backends/newservice.md`

```markdown
# New Service Backend

The New Service backend stores state in New Service.

## Configuration

```hcl
terraform {
  backend "newservice" {
    bucket     = "my-bucket"
    key_prefix = "terraform/"
    region     = "us-east-1"
  }
}
```

### Arguments

- `bucket` - (Required) The bucket name
- `key_prefix` - (Optional) Prefix for state keys (default: `terraform/`)
- `region` - (Optional) Service region (default: `default`)

### State Locking

The New Service backend supports state locking via...
```

### Testing Your Backend

```bash
# Unit tests
go test ./internal/backend/remote-state/newservice -v

# Integration test (if you have TestBackend helpers)
go test ./internal/backend/... -run NewService

# E2E test
cd internal/command/e2etest
go test -run ".*newservice.*" -v
```

### Key Design Decisions

1. **State Manager Pattern**: Return a `Full` implementation that wraps `TransientInMemory` for in-memory state and delegates to client for persistent storage

2. **Locking Strategy**:
   - Implement `Lock()`/`Unlock()` if your service supports atomic operations
   - Return `&statemgr.LockError{}` for conflicts to enable retry logic
   - Store lock metadata (Who, When, Operation) for debugging

3. **Workspace Support**:
   - Use key prefix to segregate workspace states
   - Always support "default" workspace
   - Return all workspaces from `Workspaces()`

4. **Error Handling**:
   - Network errors: Return errors that client retries or CLI shows to user
   - Auth errors: Return specific error messages
   - Configuration errors: Return from `Configure()`, not later

5. **Backup/Versioning**:
   - Let the `Filesystem` state manager handle backups if using it
   - Or implement backup in your state manager if needed
   - Document how to recover from state corruption

### Common Pitfalls

- **Forgetting to validate workspace names** → Can cause state collisions
- **Not implementing lock conflict detection** → No way to detect concurrent operations
- **Returning nil for empty state** → Use empty state struct instead
- **Not handling auth failures early** → Should fail in Configure(), not on first operation
- **Mutex contention in clients** → Use connection pooling/reuse

---

## Appendix: Key File Locations Reference

### Core Backend System
- `internal/backend/backend.go` - Backend interface
- `internal/backend/init/init.go` - Backend registry and initialization
- `internal/backend/backendrun/operation.go` - Operations backend interface

### Local Backend
- `internal/backend/local/backend.go` - Local backend struct and interface
- `internal/backend/local/backend_plan.go` - Plan operation
- `internal/backend/local/backend_apply.go` - Apply operation
- `internal/backend/local/backend_refresh.go` - Refresh operation
- `internal/backend/local/backend_local.go` - LocalRun interface

### State Management
- `internal/states/statemgr/statemgr.go` - Full interface (composite)
- `internal/states/statemgr/transient.go` - Reader/Writer interfaces
- `internal/states/statemgr/persistent.go` - Refresher/Persister interfaces
- `internal/states/statemgr/locker.go` - Lock interface and lock retry logic
- `internal/states/statemgr/filesystem.go` - Filesystem state manager
- `internal/states/statemgr/lock.go` - LockDisabled wrapper

### Remote State Backends (Examples)
- `internal/backend/remote-state/s3/backend.go` - S3 backend config and init
- `internal/backend/remote-state/s3/client.go` - S3 client implementation
- `internal/backend/remote-state/azure/` - Azure Blob backend
- `internal/backend/remote-state/gcs/` - Google Cloud Storage backend
- `internal/backend/remote-state/http/` - Generic HTTP backend
- `internal/backend/remote-state/pg/` - PostgreSQL backend

### Operations Backends
- `internal/backend/remote/backend.go` - Terraform Cloud/Enterprise remote ops
- `internal/cloud/backend.go` - HCP Terraform (formerly Terraform Cloud)

### Command Integration
- `internal/command/meta_backend.go` - Backend initialization from CLI
- `internal/command/init.go` - `terraform init` command implementation
- `internal/command/meta_backend_migrate.go` - State migration between backends
- `internal/command/meta_backend_migrate_test.go` - Migration tests

### Testing
- `internal/backend/testing.go` - Generic backend test suite
- `internal/states/statemgr/testing.go` - State manager test utilities
- `internal/backend/local/testing.go` - Local backend test utilities

---

## Conclusion

The Terraform state backend subsystem is a well-architected abstraction that enables flexible state storage and operations while maintaining a consistent CLI interface. Key principles:

1. **Separation of Concerns**: Backend handles storage; Local backend handles operations
2. **Interface-Based Design**: Backends implement well-defined interfaces, not concrete types
3. **Workspace Abstraction**: Multiple isolated state environments per backend
4. **Locking Semantics**: Distributed locking prevents concurrent modifications
5. **Configuration Validation**: Three-phase process (schema → prepare → configure)

When maintaining or extending this system, follow existing patterns, add comprehensive tests, and document behavior thoroughly. The code is well-organized and readable, making it relatively straightforward to understand and modify.

For questions about specific backends or operations, consult the implementation files and tests listed above. Each remote-state backend follows a consistent pattern that can be used as a template for new backends.
