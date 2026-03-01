# Terraform State Backend Subsystem - Onboarding Document

## 1. Purpose

The state backend subsystem is responsible for managing Terraform's state files, which contain the critical mapping between configured resources and real-world infrastructure. This subsystem solves several fundamental problems:

### Core Responsibilities

**State Persistence**: Backends provide pluggable storage mechanisms for state snapshots. Rather than hardcoding local filesystem storage, Terraform abstracts state storage through backends, enabling teams to store state in various systems (S3, Azure Blob Storage, Consul, Kubernetes, HTTP endpoints, etc.).

**Concurrency Management**: Multiple Terraform processes must safely access and modify state. Backends implement state locking mechanisms to prevent concurrent modifications from corrupting state. When one user runs `terraform apply`, the state lock prevents other users from modifying the same state simultaneously.

**Workspace Support**: Most backends support multiple named workspaces (e.g., "prod", "staging", "dev"), allowing a single configuration to manage multiple environments. Each workspace has its own independent state.

**Remote Operations**: Some backends (Remote, Local) can orchestrate Terraform operations (plan, apply, refresh) themselves, while others only provide state storage. This distinction separates concerns: storage backends vs. operational backends.

### Why Multiple Backend Types?

Different organizations have different requirements:
- **Local backend** (`/workspace/internal/backend/local`): Default, filesystem-based storage for single-user workflows
- **S3 backend** (`/workspace/internal/backend/remote-state/s3`): Team collaboration with state locking via DynamoDB
- **Remote/Cloud backend** (`/workspace/internal/backend/remote`, `/workspace/internal/cloud`): Managed operations platform with state storage
- **Consul, Azure, GCS, etc.**: Integrate with existing infrastructure and compliance requirements

The backend interface allows Terraform CLI to remain agnostic about where state is stored while supporting all these scenarios.

---

## 2. Dependencies

### Architecture Overview

The state backend subsystem sits at a critical junction in Terraform's architecture:

```
Command CLI Layer
    ↓
Backend Interface (backend.Backend)
    ↓
State Manager Layer (statemgr.Full)
    ↓
Persistent Storage (S3, local filesystem, etc.)
```

### Upstream Dependencies (What Calls Backends)

**Command Layer** (`/workspace/internal/command/meta_backend.go`):
- The Meta command handler initializes backends via `Backend()` method
- Commands (apply, plan, refresh, etc.) use backends to get state managers
- Backend selection/initialization happens in `/workspace/internal/command/meta_backend.go` (~400+ lines)

**Terraform Engine** (`/workspace/internal/terraform`):
- The terraform package performs actual infrastructure operations
- Requires state managers from backends to read/write state during operations
- Doesn't know about concrete backend implementations

**Backend Initialization System** (`/workspace/internal/backend/init/init.go`):
- Central registry of available backends
- Maps backend type names (e.g., "s3", "azurerm") to InitFn constructors
- Currently hardcoded; custom backends require recompilation

### Downstream Dependencies (What Backends Call)

**State Manager Interface** (`/workspace/internal/states/statemgr/statemgr.go`):
- `statemgr.Full` is the complete state management interface
- Composes `Storage`, `Locker`, and other interfaces
- Each backend must provide a `statemgr.Full` implementation via `StateMgr(workspace string)` method

**State Interfaces** (`/workspace/internal/states/`):
- Backends use `*states.State` to represent in-memory state snapshots
- State files are serialized via `statefile.File` and `statefile.Read/Write`

**Configuration Schema** (`/workspace/internal/configs/configschema`):
- Backends expose their configuration schema via `ConfigSchema()` method
- Uses the same schema model as providers

**Helpers & Utilities**:
- `/workspace/internal/backend/backendbase`: Base implementations of ConfigSchema/PrepareConfig
- `/workspace/internal/states/remote`: Abstract state manager for remote backends
- `/workspace/internal/states/statemgr`: Lock management and state persistence

### Integration Patterns

**Configuration Flow**:
1. HCL backend block is parsed (e.g., `terraform { backend "s3" { ... } }`)
2. Backend name is used to lookup InitFn in registry
3. Backend is instantiated, ConfigSchema() is called
4. PrepareConfig() validates and applies defaults
5. Configure() performs backend-specific setup
6. StateMgr() is called to get state manager for operations

**Operation Flow**:
1. Command gets backend from `meta.Backend()`
2. Calls `backend.StateMgr(workspace)` to get state manager
3. Calls `statemgr.Lock()` if implementing Locker
4. Reads state with `RefreshState()` and `State()`
5. Modifies state in-memory
6. Writes state with `WriteState()` and persists with `PersistState()`
7. Calls `statemgr.Unlock()` to release lock

---

## 3. Relevant Components

### Core Backend Interface

**File**: `/workspace/internal/backend/backend.go` (107 lines)

```go
type Backend interface {
    ConfigSchema() *configschema.Block      // Define expected config structure
    PrepareConfig(cty.Value) (cty.Value, tfdiags.Diagnostics)  // Validate & apply defaults
    Configure(cty.Value) tfdiags.Diagnostics  // Setup after validation
    StateMgr(workspace string) (statemgr.Full, error)  // Get state manager for workspace
    DeleteWorkspace(name string, force bool) error  // Remove a workspace
    Workspaces() ([]string, error)  // List all workspaces
}
```

Key constants:
- `DefaultStateName = "default"`: Every backend must have a default workspace
- `ErrWorkspacesNotSupported`: Returned when backend doesn't support multiple workspaces
- `ErrDefaultWorkspaceNotSupported`: Returned when default workspace is required but not available

### State Manager Interfaces

**File**: `/workspace/internal/states/statemgr/statemgr.go` (30 lines)

```go
type Full interface {
    Storage     // Combines Transient + Persistent
    Locker      // Lock/Unlock for concurrency control
}

type Storage interface {
    Transient
    Persistent
}

type Persistent interface {
    Refresher
    Persister
    OutputReader
}

type Refresher interface {
    RefreshState() error  // Read latest state from persistent storage
}

type Persister interface {
    PersistState(*schemarepo.Schemas) error  // Write state to persistent storage
}

type OutputReader interface {
    GetRootOutputValues(ctx context.Context) (map[string]*states.OutputValue, error)
}
```

**File**: `/workspace/internal/states/statemgr/locker.go` (228 lines)

```go
type Locker interface {
    Lock(info *LockInfo) (string, error)    // Acquire lock, returns lock ID
    Unlock(id string) error                 // Release lock
}

type LockInfo struct {
    ID        string    // Unique lock identifier
    Operation string    // e.g., "apply", "plan"
    Who       string    // user@hostname
    Version   string    // Terraform version
    Created   time.Time // Lock creation time
    Path      string    // State file path
}

// Helper: Retry lock acquisition with exponential backoff
func LockWithContext(ctx context.Context, s Locker, info *LockInfo) (string, error)

type LockError struct {
    Info *LockInfo
    Err  error
}
```

### Transient State Interfaces

**File**: `/workspace/internal/states/statemgr/transient.go` (referenced in statemgr.go)

```go
type Reader interface {
    State() *states.State  // Get current in-memory state snapshot
}

type Writer interface {
    WriteState(*states.State) error  // Update in-memory state snapshot
}

type Transient interface {
    Reader
    Writer
}
```

### Base Implementation Helper

**File**: `/workspace/internal/backend/backendbase/base.go` (117 lines)

Provides partial Backend implementation:
```go
type Base struct {
    Schema          *configschema.Block
    SDKLikeDefaults SDKLikeDefaults  // Optional: SDK-style defaults + env vars
}

// Implements ConfigSchema() and PrepareConfig()
// Embedders must implement: Configure(), StateMgr(), DeleteWorkspace(), Workspaces()
```

Used by most remote-state backends:
- `/workspace/internal/backend/remote-state/consul/backend.go` embeds `backendbase.Base`
- `/workspace/internal/backend/remote-state/azure/backend.go` uses different pattern (legacy SDK schema)
- `/workspace/internal/backend/remote-state/s3/backend.go` implements directly

### Remote State Manager

**File**: `/workspace/internal/states/remote/state.go` (400+ lines)

Generic state manager for remote backends. Combines:
- `remote.Client` interface for storage I/O
- Serialization/deserialization logic
- Lineage/serial tracking for conflict detection
- Optional locking support

Used by all remote-state backends:
```go
type State struct {
    Client Client  // Low-level storage (Get/Put/Delete)
    // State snapshots and metadata
    lineage, readLineage string
    serial, readSerial   uint64
    state, readState     *states.State
}
```

**File**: `/workspace/internal/states/remote/remote.go` (42 lines)

```go
type Client interface {
    Get() (*Payload, error)  // Read state
    Put([]byte) error        // Write state
    Delete() error           // Delete state
}

type ClientLocker interface {
    Client
    statemgr.Locker  // Optional: implement locking
}
```

### Local State Manager

**File**: `/workspace/internal/states/statemgr/filesystem.go` (300+ lines)

Filesystem-based state manager with full locking support:
```go
type Filesystem struct {
    path, readPath, backupPath string
    file, readFile, backupFile *statefile.File
    // OS-level locking (fcntl on Unix, LockFileEx on Windows)
}
```

Features:
- Read from one path, write to different path
- Optional backup of previous state
- OS-level file locks
- Implements `statemgr.Full`, `statemgr.PersistentMeta`, `statemgr.Migrator`

### Backend Implementations

Directory structure: `/workspace/internal/backend/remote-state/`

**Standard Backends**:

| Backend | File | Type | Locking |
|---------|------|------|---------|
| local | `/workspace/internal/backend/local/backend.go` | Operations | OS locks |
| remote | `/workspace/internal/backend/remote/backend.go` | Operations | HCP Terraform |
| s3 | `/workspace/internal/backend/remote-state/s3/backend.go` | State | DynamoDB |
| azurerm | `/workspace/internal/backend/remote-state/azure/backend.go` | State | Blob leases |
| gcs | `/workspace/internal/backend/remote-state/gcs/backend.go` | State | GCS object metadata |
| consul | `/workspace/internal/backend/remote-state/consul/backend.go` | State | Consul KV |
| http | `/workspace/internal/backend/remote-state/http/backend.go` | State | HTTP-based |
| kubernetes | `/workspace/internal/backend/remote-state/kubernetes/backend.go` | State | K8s ConfigMap |
| oss | `/workspace/internal/backend/remote-state/oss/backend.go` | State | Aliyun OSS |
| pg | `/workspace/internal/backend/remote-state/pg/backend.go` | State | PostgreSQL |
| cos | `/workspace/internal/backend/remote-state/cos/backend.go` | State | Tencent COS |
| inmem | `/workspace/internal/backend/remote-state/inmem/backend.go` | State | In-memory |

Each backend typically has:
- `backend.go`: Main Backend implementation (ConfigSchema, PrepareConfig, Configure, Workspaces, DeleteWorkspace)
- `backend_state.go`: StateMgr() implementation
- `client.go`: Client or RemoteClient implementation (storage I/O + locking)
- `client_test.go`: Client tests
- `backend_test.go`: Backend tests

### Backend Registration & Initialization

**File**: `/workspace/internal/backend/init/init.go` (148 lines)

```go
var backends map[string]backend.InitFn  // Global registry (thread-safe with mutex)
var RemovedBackends map[string]string   // Deprecated backends with error messages

func Init(services *disco.Disco)         // Initialize registry
func Backend(name string) backend.InitFn // Lookup backend
func Set(name string, f backend.InitFn)  // Register backend
```

Currently hardcoded backends (lines 55-74):
- `"local"`, `"remote"`, `"azurerm"`, `"consul"`, `"cos"`, `"gcs"`, `"http"`, `"inmem"`, `"kubernetes"`, `"oss"`, `"pg"`, `"s3"`, `"cloud"`

### Operations Backend Interface

**File**: `/workspace/internal/backend/backendrun/operation.go` (60+ lines)

```go
type OperationsBackend interface {
    backend.Backend
    Operation(context.Context, *Operation) (*RunningOperation, error)
    ServiceDiscoveryAliases() ([]HostAlias, error)
}
```

Only implemented by:
- `Local` backend: Runs operations locally
- `Remote` backend: Runs operations on HCP Terraform

### Command Integration

**File**: `/workspace/internal/command/meta_backend.go` (400+ lines)

Key functions:
- `Backend(opts *BackendOpts)`: Main entry point, initializes backend with config
- Handles backend migration (switching backends)
- Validates Terraform version compatibility
- Performs authentication/authorization

---

## 4. Failure Modes

### State Locking Failures

**Lock Contention**:
- When lock already held, `Lock()` returns `*statemgr.LockError` with existing lock info
- `LockWithContext()` implements exponential backoff retry (1s → 2s → 4s ... → 16s max)
- If context timeout/cancellation occurs during retry, returns last LockError

**Common Issues**:
```
Error: Error acquiring the state lock

Error: error in state lock info: "..."
```

Causes:
1. Another user running `terraform apply` (legitimate contention)
2. Stale lock from crashed process (lock not released due to ungraceful termination)
3. Network issues preventing lock service communication
4. Insufficient permissions to access lock storage

**Stale Lock Resolution**:
- S3: Manually delete DynamoDB lock table entry
- Consul: Manually delete lock key
- Filesystem: Remove `.terraform.lock.hcl` file
- Azure: Force-release blob lease
- Command: `terraform force-unlock <LOCK_ID>`

### Storage Unavailability

**Remote Service Down**:
- S3/Azure/GCS: Network errors during Get/Put/Delete
- HTTP backend: 5xx responses
- Consul/Kubernetes: Service discovery failure

Errors from `RefreshState()` and `PersistState()`:
- Propagate to terraform operations
- Commands fail gracefully with error messages
- No automatic fallback (safety-first: don't proceed with stale state)

### State Corruption Scenarios

**Conflict Detection via Lineage & Serial**:

```go
type SnapshotMeta struct {
    Lineage string      // Unique state ID (doesn't change unless force-push)
    Serial  uint64      // Version counter (incremented each persist)
}
```

**Scenarios**:

1. **Concurrent Writes** (should not happen with locking):
   - Client A reads state (serial=5, lineage=abc)
   - Client B reads state (serial=5, lineage=abc)
   - Client B writes (serial=6, lineage=abc)
   - Client A writes (serial=6, lineage=abc) → CONFLICT
   - Terraform detects serial/lineage mismatch, refuses to write
   - User must manually resolve (rerun plan, re-apply)

2. **Lineage Mismatch**:
   - Happens when states are from different runs
   - `terraform state pull | terraform state push` with wrong state
   - Causes: `serial` alone doesn't uniquely identify state sequence

3. **Migration Corruption**:
   - Moving state between backends
   - `/workspace/internal/command/meta_backend_migrate.go` handles migration
   - Reads from old backend, writes to new backend
   - Lockfiles managed carefully to prevent races

**File**: `/workspace/internal/states/statemgr/persistent.go` (193 lines)
- `Persister.PersistState()` must detect and avoid destroying concurrent changes
- Implementations use serial/lineage or storage-level atomicity

### Configuration Errors

**Invalid Configuration**:
- `PrepareConfig()` returns diagnostics with detailed attribute paths
- Errors prevent `Configure()` from being called
- Example S3 backend errors:
  - Missing `bucket` (required)
  - Invalid AWS region format
  - Insufficient IAM permissions

**Detection**:
- Schema validation via `configschema.CoerceValue()`
- Backend-specific validation in `Configure()`:
  - Connection tests (can we reach S3?)
  - Permission checks (can we read/write?)
  - Resource existence checks (does bucket exist?)

### Workspace Errors

**Unsupported Operations**:
```go
ErrWorkspacesNotSupported  // Backend doesn't support workspaces
ErrDefaultWorkspaceNotSupported  // Backend requires non-default workspace
```

**File Deletion Prevention**:
- `DeleteWorkspace()` cannot delete default workspace
- Cannot delete workspace if state manager holds lock on it (caller must release lock first)

### Type System Safety

**File**: `/workspace/internal/states/statemgr/statemgr.go` (compile-time check)

All state manager implementations must verify interface satisfaction:
```go
var _ statemgr.Full = (*YourType)(nil)
```

Found in implementations:
- `/workspace/internal/states/statemgr/filesystem.go:67`
- `/workspace/internal/states/remote/state.go:51-53`

Catch interface drift at compile time.

---

## 5. Testing

### Testing Infrastructure

**Main Testing Functions** (`/workspace/internal/backend/testing.go`, 400+ lines):

```go
// Configure and validate backend with HCL config
TestBackendConfig(t *testing.T, b Backend, c hcl.Body) Backend

// Wrap raw Go types into HCL bodies for testing
TestWrapConfig(raw map[string]interface{}) hcl.Body

// Test state operations (create, read, update workspaces)
TestBackendStates(t *testing.T, b Backend)

// Test state locking (two instances, lock contention, stale locks)
TestBackendStateLocks(t *testing.T, b1, b2 Backend)

// Test force-unlock capability
TestBackendStateForceUnlock(t *testing.T, b1, b2 Backend)
```

### Backend Test Pattern

**Example**: `/workspace/internal/backend/local/backend_test.go`

```go
func TestLocal_impl(t *testing.T) {
    var _ backendrun.OperationsBackend = New()
    var _ backendrun.Local = New()
    var _ backendrun.CLI = New()
}

func TestLocal_backend(t *testing.T) {
    testTmpDir(t)
    b := New()
    backend.TestBackendStates(t, b)        // Test state operations
    backend.TestBackendStateLocks(t, b, b) // Test locking
}
```

Pattern:
1. Create backend instance with `New()`
2. Configure if necessary with `TestBackendConfig()`
3. Call `TestBackendStates()` to verify workspace operations
4. Call `TestBackendStateLocks()` with two backend instances

### State Operations Tested

`TestBackendStates()` verifies:
- Create/read/update/delete workspaces
- Multiple workspaces stay isolated
- State persists across RefreshState calls
- Default workspace cannot be deleted
- Workspace listing is accurate

### Locking Tested

`TestBackendStateLocks()` verifies:
- Lock acquisition succeeds
- Second instance cannot acquire lock while held
- Lock release allows second instance to acquire
- Lock info contains correct metadata
- Optional: Force-unlock capability

### Remote-State Backend Test Pattern

**Example**: `/workspace/internal/backend/remote-state/inmem/backend_test.go`

```go
func TestBackend_impl(t *testing.T) {
    var _ backend.Backend = New()
}

func TestBackend(t *testing.T) {
    Reset()  // Clear in-memory state
    b := New()
    backend.TestBackendConfig(t, b, nil)
    backend.TestBackendStates(t, b)
}

func TestBackendLocked(t *testing.T) {
    Reset()
    b := New()
    backend.TestBackendConfig(t, b, nil)
    backend.TestBackendStateLocks(t, b, b)
}
```

Pattern is same, but with additional setup/teardown (Reset() for in-memory).

### Operations Backend Test Pattern

**Example**: `/workspace/internal/backend/local/backend_apply_test.go`

Tests use the `backendrun.Operation` struct:
```go
type Operation struct {
    Type       OperationType
    PlanFile   *planfile.File
    Plan       *plans.Plan
    StateLocker clistate.Locker
    // ... many more fields for terraform operations
}
```

Tests verify:
- Operations execute correctly (apply modifies state)
- State locks held during operation
- State changes reflected in state manager
- Errors propagated correctly

### Client Testing

**File**: `/workspace/internal/backend/remote-state/consul/client_test.go`

For remote backends, test the Client interface:
```go
func TestRemoteClient(t *testing.T) {
    client := &RemoteClient{...}

    data := []byte("test state")
    if err := client.Put(data); err != nil {
        t.Fatal(err)
    }

    payload, err := client.Get()
    if payload.Data != data {
        t.Fatal("data mismatch")
    }
}
```

### Testing State Locking Behavior

**File**: `/workspace/internal/backend/testing.go:302-400`

Detailed lock testing:
1. Create two backend instances pointing to same storage
2. First acquires lock with operation="test"
3. Second attempts lock → gets LockError
4. First releases lock
5. Second successfully acquires lock
6. First cannot acquire while second holds it
7. Verify lock metadata (Who, Version, Created, etc.)

Example flow:
```go
lockIDA, err := lockerA.Lock(infoA)  // Succeeds
lockIDB, err := lockerB.Lock(infoB)  // Fails with LockError
lockerA.Unlock(lockIDA)
lockIDB, err := lockerB.Lock(infoB)  // Succeeds
```

### Integration Tests

**File**: `/workspace/internal/command/meta_backend_test.go`

Test backend initialization through command layer:
- Backend selection from configuration
- Backend migration (switching backends)
- Configuration validation
- Workspace switching

**Example S3 Backend Tests**:
- `/workspace/internal/backend/remote-state/s3/backend_complete_test.go`: Full integration tests against real S3
- Uses acceptance testing pattern: `TestAccBackendS3Config*`

---

## 6. Debugging

### Enabling Logging

Set environment variable:
```bash
TF_LOG=DEBUG terraform apply
TF_LOG_PATH=/tmp/terraform.log terraform apply
```

Backend-specific logging:
- `log.Printf()` calls in backend implementations
- Use `internal/logging` package for structured logging

### Common Issues and Diagnostics

**Issue 1: Lock Contention**

```
Error: Error acquiring the state lock

Lock Info:
  ID:        12345-67890-abcde-fgh
  Path:      s3://my-bucket/terraform.tfstate
  Operation: apply
  Who:       alice@prod-server
  Version:   1.5.0
  Created:   2024-02-15T10:30:45Z
  Info:
```

**Debugging**:
1. Check who has the lock: `Who` field shows user/host
2. Check when: `Created` field
3. Check operation type: `Operation` field
4. Is the process still running? SSH to that host and check
5. If stale: Use `terraform force-unlock <ID>`

**Issue 2: State Lineage Mismatch**

```
Error: resource aws_instance.web: resource previously tracked as "module.vpc.aws_instance.web"
```

**Debugging**:
1. Compare current and previous state:
   ```bash
   terraform state show aws_instance.web
   terraform state pull | jq .
   ```
2. Check serial/lineage in state file:
   ```bash
   terraform state pull | jq '.serial, .lineage'
   ```
3. If moved between backends, verify move completed correctly

**Issue 3: Remote Service Unavailable**

```
Error: error reading state: RequestError: send request failed...
```

**Debugging**:
1. Verify backend is reachable:
   - S3: `aws s3 ls s3://bucket-name/`
   - Azure: `az storage blob show -c container -n file`
   - Consul: `consul members`
2. Check credentials/permissions
3. Check network connectivity (firewalls, proxies, VPN)

**Issue 4: Configuration Validation Failure**

```
Error: Invalid backend configuration
  on  line 1: attribute "bucket" is required
```

**Debugging**:
1. Check backend block in code:
   ```hcl
   terraform {
     backend "s3" {
       bucket = "..."  # Missing?
     }
   }
   ```
2. Check environment variables (some backends use EnvDefaults)
3. Run `terraform init` with `-reconfigure` to reset cached config

### Verifying State Consistency

**1. Check state file integrity**:
```bash
# Pull state and verify it parses
terraform state pull > state.json
jq . state.json

# Check serial/lineage match
jq '.serial, .lineage' state.json
```

**2. Verify state matches backend**:
```bash
# For S3 backend
aws s3api head-object --bucket my-bucket --key terraform.tfstate
aws s3api get-object --bucket my-bucket --key terraform.tfstate /tmp/s3-state.json

# For local backend
cat terraform.tfstate | jq '.serial, .lineage'
```

**3. Detect concurrent modifications**:
```bash
# Get latest state from backend
terraform state pull > /tmp/latest.json

# Compare serial numbers - if they don't match your local copy,
# someone else modified state
jq '.serial' /tmp/latest.json  # Compare with your state
```

### Investigating Lock Failures

**Issue: Lock timeout**

```bash
# Check if lock service is responding
# S3/DynamoDB
aws dynamodb get-item --table-name terraform-locks \
  --key "{\"LockID\": {\"S\": \"my-bucket/terraform.tfstate\"}}"

# Consul
consul kv get -detailed "terraform-lock/my-state"

# Remove stale lock (if confirmed crashed)
# WARNING: Only if you're absolutely sure process is dead!
aws dynamodb delete-item --table-name terraform-locks --key "{...}"
```

**Lock ID Format**:
- Each lock attempt creates unique ID
- ID used in error message helps identify specific lock
- Force-unlock requires this ID

### State File Inspection

**File Format**: `/workspace/internal/states/statefile/file.go`

```go
type File struct {
    TerraformVersion *version.Version
    Serial           uint64
    Lineage          string
    State            *states.State
}
```

**Inspect locally**:
```bash
# View as JSON
cat terraform.tfstate | jq '.'

# Check version that created state
jq '.terraform_version' terraform.tfstate

# Count resources
jq '.resources | length' terraform.tfstate

# Find specific resource
jq '.resources[] | select(.type == "aws_instance")' terraform.tfstate
```

### Diagnostic Tools

**Reading State Programmatically**:
```bash
# terraform state list
terraform state list

# terraform state show <address>
terraform state show aws_instance.example

# terraform state pull - get full state JSON
terraform state pull | jq '.'

# terraform state push - replace state (dangerous!)
```

**Backend Health Checks**:
```bash
# Implicit: terraform init (validates backend is working)
terraform init

# terraform validate (doesn't check backend connectivity)
terraform validate

# Force backend interaction:
terraform state list  # This refreshes state from backend
```

### Logs to Check

**When debugging, examine these files**:
1. `TF_LOG_PATH` output (if enabled)
2. Backend service logs:
   - S3: CloudTrail logs
   - Azure: Activity log or storage logs
   - Consul: Agent logs
   - Kubernetes: kubectl logs
3. Terraform state file itself for corruption signs
4. Lock service logs (DynamoDB streams, Consul logs, etc.)

### Tracing Backend Calls

Key code paths to trace:
1. **Backend initialization**: `meta.Backend()` → `init.Backend()` → backend constructor
2. **State manager creation**: `backend.StateMgr()` → returns `statemgr.Full`
3. **Lock acquisition**: `statemgr.Locker.Lock()` or `LockWithContext()`
4. **State read**: `RefreshState()` → `Client.Get()` → parse statefile
5. **State write**: `PersistState()` → `Client.Put()`

Add logging at these points to trace issues.

---

## 7. Adding a New Backend

### High-Level Process

1. **Create backend package** under `/workspace/internal/backend/remote-state/{backend-name}`
2. **Implement Backend interface** (ConfigSchema, PrepareConfig, Configure, StateMgr, DeleteWorkspace, Workspaces)
3. **Implement state manager** (use `remote.State` wrapper + custom Client)
4. **Implement Client interface** (Get, Put, Delete, optionally Lock/Unlock)
5. **Register backend** in `/workspace/internal/backend/init/init.go`
6. **Write tests** following established patterns
7. **Test integration** via command layer

### Step-by-Step Example: Adding a PostgreSQL Backend

#### Step 1: Create Package Structure

```bash
mkdir -p /workspace/internal/backend/remote-state/pg
touch /workspace/internal/backend/remote-state/pg/backend.go
touch /workspace/internal/backend/remote-state/pg/backend_state.go
touch /workspace/internal/backend/remote-state/pg/client.go
touch /workspace/internal/backend/remote-state/pg/client_test.go
touch /workspace/internal/backend/remote-state/pg/backend_test.go
```

#### Step 2: Implement Backend

**File**: `/workspace/internal/backend/remote-state/pg/backend.go`

```go
package pg

import (
    "database/sql"
    "fmt"
    "github.com/zclconf/go-cty/cty"
    "github.com/hashicorp/terraform/internal/backend"
    "github.com/hashicorp/terraform/internal/backend/backendbase"
    "github.com/hashicorp/terraform/internal/configs/configschema"
    "github.com/hashicorp/terraform/internal/tfdiags"
)

func New() backend.Backend {
    return &Backend{
        Base: backendbase.Base{
            Schema: &configschema.Block{
                Attributes: map[string]*configschema.Attribute{
                    "connstr": {
                        Type:        cty.String,
                        Required:    true,
                        Description: "PostgreSQL connection string",
                    },
                    "schema_name": {
                        Type:        cty.String,
                        Optional:    true,
                        Description: "Schema name for state table",
                    },
                    "table_name": {
                        Type:        cty.String,
                        Optional:    true,
                        Description: "Table name for state storage",
                    },
                    "skip_table_creation": {
                        Type:        cty.Bool,
                        Optional:    true,
                        Description: "Don't auto-create table",
                    },
                },
            },
        },
    }
}

type Backend struct {
    backendbase.Base

    connstr         string
    schemaName      string
    tableName       string
    skipTableCreate bool
    db              *sql.DB
}

func (b *Backend) Configure(configVal cty.Value) tfdiags.Diagnostics {
    var diags tfdiags.Diagnostics

    b.connstr = configVal.GetAttr("connstr").AsString()
    b.schemaName = backendbase.MustStringValue(
        backendbase.GetAttrDefault(configVal, "schema_name", cty.StringVal("terraform")),
    )
    b.tableName = backendbase.MustStringValue(
        backendbase.GetAttrDefault(configVal, "table_name", cty.StringVal("tfstate")),
    )
    b.skipTableCreate = backendbase.MustBoolValue(
        backendbase.GetAttrDefault(configVal, "skip_table_creation", cty.False),
    )

    // Connect to database
    db, err := sql.Open("postgres", b.connstr)
    if err != nil {
        return diags.Append(tfdiags.Sourceless(
            tfdiags.Error,
            "Failed to connect to PostgreSQL",
            err.Error(),
        ))
    }

    // Test connection
    if err := db.Ping(); err != nil {
        return diags.Append(tfdiags.Sourceless(
            tfdiags.Error,
            "Failed to ping PostgreSQL",
            err.Error(),
        ))
    }

    b.db = db

    // Create table if needed
    if !b.skipTableCreate {
        if err := b.ensureTable(); err != nil {
            return diags.Append(tfdiags.Sourceless(
                tfdiags.Error,
                "Failed to create state table",
                err.Error(),
            ))
        }
    }

    return diags
}

func (b *Backend) ensureTable() error {
    query := fmt.Sprintf(`
        CREATE TABLE IF NOT EXISTS %s.%s (
            name TEXT PRIMARY KEY,
            data BYTEA,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    `, b.schemaName, b.tableName)

    _, err := b.db.Exec(query)
    return err
}
```

#### Step 3: Implement Backend State Methods

**File**: `/workspace/internal/backend/remote-state/pg/backend_state.go`

```go
package pg

import (
    "fmt"
    "github.com/hashicorp/terraform/internal/backend"
    "github.com/hashicorp/terraform/internal/states/remote"
    "github.com/hashicorp/terraform/internal/states/statemgr"
)

func (b *Backend) StateMgr(name string) (statemgr.Full, error) {
    stateMgr := &remote.State{
        Client: &RemoteClient{
            db:         b.db,
            schemaName: b.schemaName,
            tableName:  b.tableName,
            name:       name,
        },
    }
    return stateMgr, nil
}

func (b *Backend) Workspaces() ([]string, error) {
    var workspaces []string

    query := fmt.Sprintf("SELECT DISTINCT name FROM %s.%s ORDER BY name",
        b.schemaName, b.tableName)

    rows, err := b.db.Query(query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    found := false
    for rows.Next() {
        var name string
        if err := rows.Scan(&name); err != nil {
            return nil, err
        }
        if name == backend.DefaultStateName {
            found = true
        }
        workspaces = append(workspaces, name)
    }

    // Ensure default always exists in list
    if !found {
        workspaces = append([]string{backend.DefaultStateName}, workspaces...)
    }

    return workspaces, rows.Err()
}

func (b *Backend) DeleteWorkspace(name string, force bool) error {
    if name == backend.DefaultStateName {
        return fmt.Errorf("cannot delete default workspace")
    }

    query := fmt.Sprintf("DELETE FROM %s.%s WHERE name = $1",
        b.schemaName, b.tableName)

    _, err := b.db.Exec(query, name)
    return err
}
```

#### Step 4: Implement Client

**File**: `/workspace/internal/backend/remote-state/pg/client.go`

```go
package pg

import (
    "database/sql"
    "fmt"
    "github.com/hashicorp/terraform/internal/states/remote"
)

type RemoteClient struct {
    db         *sql.DB
    schemaName string
    tableName  string
    name       string
}

func (c *RemoteClient) Get() (*remote.Payload, error) {
    query := fmt.Sprintf(
        "SELECT data FROM %s.%s WHERE name = $1",
        c.schemaName, c.tableName)

    var data []byte
    err := c.db.QueryRow(query, c.name).Scan(&data)
    if err == sql.ErrNoRows {
        return &remote.Payload{Data: []byte("")}, nil
    }
    if err != nil {
        return nil, err
    }

    return &remote.Payload{Data: data}, nil
}

func (c *RemoteClient) Put(data []byte) error {
    query := fmt.Sprintf(
        "INSERT INTO %s.%s (name, data) VALUES ($1, $2) ON CONFLICT (name) DO UPDATE SET data = $2, updated_at = NOW()",
        c.schemaName, c.tableName)

    _, err := c.db.Exec(query, c.name, data)
    return err
}

func (c *RemoteClient) Delete() error {
    query := fmt.Sprintf(
        "DELETE FROM %s.%s WHERE name = $1",
        c.schemaName, c.tableName)

    _, err := c.db.Exec(query, c.name)
    return err
}
```

#### Step 5: Write Tests

**File**: `/workspace/internal/backend/remote-state/pg/backend_test.go`

```go
package pg

import (
    "testing"
    "github.com/hashicorp/terraform/internal/backend"
)

func TestBackend_impl(t *testing.T) {
    var _ backend.Backend = New()
}

func TestBackendConfig(t *testing.T) {
    // Requires real PostgreSQL or skip test
    t.Skip("requires PostgreSQL setup")

    b := New()
    c := backend.TestWrapConfig(map[string]interface{}{
        "connstr": "postgres://localhost/terraform_test",
    })

    backend.TestBackendConfig(t, b, c)
}

func TestBackendStates(t *testing.T) {
    t.Skip("requires PostgreSQL setup")

    b := New()
    c := backend.TestWrapConfig(map[string]interface{}{
        "connstr": "postgres://localhost/terraform_test",
    })
    backend.TestBackendConfig(t, b, c)
    backend.TestBackendStates(t, b)
}
```

#### Step 6: Register Backend

**File**: `/workspace/internal/backend/init/init.go`

Add import:
```go
import (
    // ... existing imports
    backendPg "github.com/hashicorp/terraform/internal/backend/remote-state/pg"
)
```

Add to `Init()` function (around line 68):
```go
backends = map[string]backend.InitFn{
    "local":  func() backend.Backend { return backendLocal.New() },
    "remote": func() backend.Backend { return backendRemote.New(services) },
    // ... existing backends
    "pg":     func() backend.Backend { return backendPg.New() },  // Add this
}
```

#### Step 7: Test Integration

In terraform configuration:
```hcl
terraform {
    backend "pg" {
        connstr     = "postgres://user:password@localhost/terraform"
        schema_name = "terraform"
        table_name  = "state"
    }
}
```

Run:
```bash
terraform init  # Should initialize with PostgreSQL backend
terraform plan  # Should work with PostgreSQL-backed state
terraform apply # Should persist state to PostgreSQL
```

### Key Design Decisions

**1. State Manager Wrapper**:
- Most backends use `remote.State` wrapper
- Provides lineage/serial handling, conflict detection
- Only need to implement low-level Client interface

**2. Workspace Naming**:
- Store workspace name as key/ID in storage
- List all workspace names from storage
- Prevent default workspace deletion

**3. Locking Strategy**:
- Optional: implement `ClientLocker` for distributed locking
- If implemented, `remote.State` automatically handles Locker interface
- If not, falls back to in-memory (no concurrency protection)

**4. Configuration Validation**:
- Use `backendbase.Base` for schema handling
- Implement backend-specific validation in `Configure()`
- Test all config combinations

### Testing Patterns

**Minimal tests**:
1. `TestBackend_impl`: Verify interface satisfaction
2. `TestBackendConfig`: Verify configuration validation
3. `TestBackendStates`: Verify workspace operations
4. `TestBackendStateLocks`: Verify locking (if implemented)

**Acceptance tests** (optional but recommended):
- Use real backend service (not mocks)
- Test against staging/test environment
- Verify locks work correctly under concurrency

### Common Pitfalls

1. **Forgetting DefaultStateName**: Must always include "default" workspace
2. **Not handling workspace creation**: `StateMgr()` for new workspace should auto-create
3. **Race conditions in Workspaces()**: Multiple processes reading/writing simultaneously
4. **Lock cleanup**: Stale locks must be detectable and removable
5. **Serial/lineage handling**: Let `remote.State` handle this, don't reimplement
6. **State file format**: Must use standard `statefile.File` format, not custom JSON

---

## Summary

The state backend subsystem is a critical, well-architected component of Terraform that abstracts state storage while maintaining safety through locking and conflict detection. The modular design allows new backends to be added by implementing a simple interface, while the testing framework ensures consistency across all backends.

Key takeaways:
- **Backend interface** is simple (6 methods) but powerful
- **State managers** handle persistence, locking, and consistency
- **Remote.State** wrapper simplifies backend implementations
- **Tests** are comprehensive and must pass for acceptance
- **Configuration** uses standard schema model
- **Locking** is critical for team environments and uses exponential backoff
- **Adding backends** is straightforward with clear patterns to follow
