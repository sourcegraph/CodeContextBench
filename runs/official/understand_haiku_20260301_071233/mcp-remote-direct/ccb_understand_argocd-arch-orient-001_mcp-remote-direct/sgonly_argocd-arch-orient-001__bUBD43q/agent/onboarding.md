# Argo CD Codebase Orientation

## 1. Main Entry Points

Argo CD is a multi-binary system where each component is a separate executable built from the same codebase. The main entry point is `cmd/main.go`, which determines which component to run based on the binary name.

### API Server (argocd-server)
- **Entry Point**: `cmd/argocd-server/commands/argocd_server.go:NewCommand()`
- **Primary Responsibility**: Exposes the gRPC/REST API consumed by the Web UI, CLI, and CI/CD systems. It handles authentication, authorization, application management, and provides streaming capabilities for real-time updates.
- **Key Features**:
  - Manages HTTP/gRPC endpoints for application, repository, cluster, and project management
  - Handles webhook integrations (GitHub, GitLab, Bitbucket, etc.)
  - Manages caching layers for repositories and application state
  - Supports Dex integration for OIDC/SSO authentication
  - Serves static web UI assets

### Application Controller (argocd-application-controller)
- **Entry Point**: `cmd/argocd-application-controller/commands/argocd_application_controller.go:NewCommand()`
- **Primary Responsibility**: Continuously monitors running applications and compares current live state against desired target state (GitOps reconciliation loop). This is the core component that implements the sync and health assessment logic.
- **Key Features**:
  - Watches Application resources in the cluster
  - Communicates with repo server to fetch manifests
  - Compares desired state (from Git) with live state (in cluster)
  - Executes sync operations to bring live state to desired state
  - Handles multi-cluster synchronization with sharding support
  - Tracks application health and status

### Repository Server (argocd-repo-server)
- **Entry Point**: `cmd/argocd-repo-server/commands/argocd_repo_server.go:NewCommand()`
- **Primary Responsibility**: Maintains a local cache of Git repositories and generates Kubernetes manifests from various sources (Helm, Kustomize, Jsonnet, plain YAML, plugins).
- **Key Features**:
  - Clones and caches Git repositories
  - Generates manifests using multiple tools (Helm, Kustomize, etc.)
  - Handles template substitution and parameterization
  - Supports custom config management plugins
  - Provides parallelized manifest generation
  - Manages GPG signature verification

### ApplicationSet Controller (argocd-applicationset-controller)
- **Entry Point**: `cmd/argocd-applicationset-controller/commands/applicationset_controller.go:NewCommand()`
- **Primary Responsibility**: Manages ApplicationSet resources which allow templating and generating multiple Applications from a single ApplicationSet definition using various generators (Git, Cluster, SCM, Pull Request, Matrix, etc.).
- **Key Features**:
  - Watches ApplicationSet resources
  - Generates Applications using multiple generator types
  - Implements progressive sync strategies (rolling sync, canary deployments)
  - Merges generated applications with template specifications
  - Handles webhook integration for PR-based generators

## 2. Core Packages

### pkg/apis/application/v1alpha1
**Location**: `pkg/apis/application/v1alpha1/`
**Responsibility**: Defines the Kubernetes Custom Resource Definitions (CRDs) for Argo CD including Application, ApplicationSet, AppProject, and related types. Contains the API types that represent the declarative state users specify.
**Key Types**:
- `Application`: The main resource defining a deployed application
- `ApplicationSet`: Template for generating multiple applications
- `ApplicationSpec`: Desired application state (source, destination, sync policy)
- `ApplicationStatus`: Current application state (sync status, health, resources)
- `SyncPolicy`: Controls automated sync behavior
- `SyncStrategy`: Defines how resources are applied (hook vs apply)

### controller
**Location**: `controller/`
**Responsibility**: Implements the core Kubernetes controller logic that reconciles Application resources. It's a custom Kubernetes controller using controller-runtime patterns.
**Key Components**:
- `appcontroller.go`: Main ApplicationController that watches applications and orchestrates reconciliation
- `sync.go`: Implements the sync operation execution logic
- `state.go`: Compares desired vs. live state and determines differences
- `health.go`: Assesses resource health status
- `cache/`: Application state caching to avoid repeated comparisons

### reposerver
**Location**: `reposerver/`
**Responsibility**: Implements the repository server gRPC service that generates Kubernetes manifests from various source types. Handles Git operations, manifest templating, and manifest caching.
**Key Components**:
- `repository/repository.go`: Core manifest generation logic supporting Helm, Kustomize, Helm OCI, plain YAML, Jsonnet, CMP plugins
- `apiclient/`: gRPC client and protobuf definitions for repo server API
- `cache/`: Caches generated manifests by Git commit SHA
- `metrics/`: Metrics collection for manifest generation operations

### server
**Location**: `server/`
**Responsibility**: Implements the API server gRPC and REST services. Contains handlers for application management, repository management, cluster management, and WebSocket streaming.
**Key Components**:
- `application/application.go`: Handles Application CRUD operations and streaming
- `repository/repository.go`: Repository credential and configuration management
- `cluster/cluster.go`: Cluster registration and management
- `cache/`: Server-side caching for frequently accessed data

### applicationset
**Location**: `applicationset/`
**Responsibility**: Implements ApplicationSet controller logic including generators and template rendering for creating multiple applications.
**Key Components**:
- `controllers/`: Contains the main ApplicationSet controller and template renderer
- `generators/`: Different generator implementations (Git, Cluster, SCM providers, Pull Requests, Matrix, etc.)
- `services/`: External service integrations (GitHub, GitLab, Bitbucket for PR generation)
- `utils/`: Utility functions for ApplicationSet processing

### util/argo
**Location**: `util/argo/`
**Responsibility**: Core Argo CD utilities including diff calculation, normalization, health assessment, and application state management.
**Key Components**:
- `diff/`: Resource difference calculation and normalization logic
- `normalizers/`: Normalizes resources before comparison to avoid false positives
- `argo.go`: Utility functions for application operations and manifest validation

## 3. Configuration Loading

Configuration in Argo CD is loaded through multiple mechanisms that combine CLI flags, environment variables, and ConfigMaps.

### Configuration Pipeline

1. **CLI Flags (Cobra)**
   - Each component's `NewCommand()` function uses `github.com/spf13/cobra` to define flags
   - Example: `cmd/argocd-server/commands/argocd_server.go` defines flags like `--listen-port`, `--repo-server-address`, etc.
   - Flags are bound to local variables in the command's Run/RunE function

2. **Environment Variables**
   - Components use `github.com/argoproj/argo-cd/v2/util/env` package for environment variable parsing
   - Provides functions like `env.StringFromEnv()`, `env.ParseNumFromEnv()`, `env.ParseBoolFromEnv()`
   - Examples: `ARGOCD_SERVER_INSECURE`, `ARGOCD_REPO_SERVER_PARALLELISM_LIMIT`, etc.

3. **Kubernetes ConfigMaps/Secrets**
   - Runtime settings stored in `argocd-cm` and `argocd-secret` ConfigMaps
   - Accessed through `util/settings/settings.go` package
   - `ArgoCDSettings` struct (lines 49+) contains all runtime configuration

### Configuration Loading Flow

```
CLI Flags → Environment Variables → ConfigMap/Secrets → Default Values
```

### Key Configuration Structs

1. **ArgoCDSettings** (`util/settings/settings.go:49`)
   - Holds runtime configuration for Argo CD
   - Fields include: URL, OIDC config, webhook secrets, server signature, TLS certificates
   - Loaded from `argocd-cm` and `argocd-secret` Kubernetes resources

2. **Application/Project Settings**
   - Application CRD: `pkg/apis/application/v1alpha1/types.go:55`
   - Contains spec and status fields controlling sync behavior

### Configuration Access Pattern

Each component:
1. Defines CLI flags in `NewCommand()` using Cobra
2. Reads environment variables using `util/env` package
3. Loads Kubernetes ConfigMap settings using `util/settings.SettingsManager`
4. Applies defaults if not specified elsewhere

Example flow in API Server:
```go
// cmd/argocd-server/commands/argocd_server.go
command.Flags().StringVar(&listenHost, "listen-host", "0.0.0.0", "...")
command.Flags().IntVar(&listenPort, "listen-port", common.DefaultPortAPIServer, "...")
// Then in Run():
settings, _ := settingsManager.GetSettings(ctx)  // Loads from ConfigMap
```

## 4. Test Structure

Argo CD has a comprehensive multi-layered testing strategy across unit, integration, and E2E tests.

### Unit Tests
- **Location**: Scattered throughout codebase with `*_test.go` suffix
- **Framework**: Go's standard `testing` package with `github.com/stretchr/testify` for assertions and mocks
- **Examples**:
  - `controller/appcontroller_test.go`: Tests application controller reconciliation
  - `controller/state_test.go`: Tests state comparison and health assessment
  - `reposerver/repository/repository_test.go`: Tests manifest generation
  - `util/argo/diff/normalize_test.go`: Tests resource normalization

**Key Testing Pattern**:
```go
func TestApplicationController(t *testing.T) {
    // Setup fake clients, mock repo server
    ctrl := newFakeController(&fakeData{...}, nil)
    // Execute test
    // Assert results
}
```

### Integration Tests
- **Location**: Primarily in `test/` directory and within component packages
- **Framework**: Uses fixture-based testing with Kubernetes test clients
- **Examples**:
  - `test/testutil.go`: Testing utilities and helpers
  - `controller/appcontroller_test.go`: Tests controller with mocked dependencies

### E2E Tests
- **Location**: `test/e2e/` directory
- **Framework**: Custom fixture framework in `test/e2e/fixture/`
- **Key Components**:
  - `test/e2e/fixture/fixture.go`: Test fixture setup and teardown
  - Individual test files: `app_management_test.go`, `sync_waves_test.go`, `helm_test.go`, etc.
  - TestData: `test/e2e/testdata/` and `test/e2e/testdata2/`

**E2E Test Pattern**:
```go
func TestLocalManifestSync(t *testing.T) {
    Given(t).  // Setup fixture
        When().CreateApp(...).  // Create application
        Then().Expect(...).   // Assert on live state
}
```

### Testing Frameworks Used
1. **Testify** (`github.com/stretchr/testify`): Assertions, mocks, and matchers
2. **Kubernetes Testing** (`k8s.io/client-go/testing`): Fake clientsets and reactor patterns
3. **gitops-engine Testing** (`github.com/argoproj/gitops-engine`): Mocked cluster cache
4. **Custom Fixtures** (`test/e2e/fixture/`): Domain-specific testing helpers

### Test Data
- Stored in `test/testdata/`, `test/e2e/testdata/`, `test/e2e/fixture/`
- Contains sample manifests, Helm charts, Kustomize bases, and application definitions

## 5. Application Sync Pipeline

The path of an Application resource from CRD definition to actual deployment in a Kubernetes cluster involves multiple stages with distinct responsibilities.

### Stage 1: Application Definition & Storage
**Files/Packages**: `pkg/apis/application/v1alpha1/types.go`

1. User creates Application CRD with:
   - `spec.source`: Git repo URL, path, branch/tag/commit, templating options
   - `spec.destination`: Target cluster and namespace
   - `spec.syncPolicy`: Auto-sync behavior, pruning, self-healing
   - `spec.project`: RBAC project constraints

2. Application stored in Kubernetes as `etcd` entry

### Stage 2: Application Monitoring & Queuing
**Files/Packages**: `controller/appcontroller.go`, `pkg/client/informers/`

1. Application Controller watches Application resources using Kubernetes informers
2. Changes trigger events:
   - Application creation/update → add to `appRefreshQueue`
   - Spec changes → trigger reconciliation
   - Operation requests → add to `appOperationQueue`
3. Controller processes queued applications with configurable parallelism

### Stage 3: Manifest Generation
**Files/Packages**: `reposerver/repository/repository.go`, `reposerver/server.go`

1. Controller calls Repo Server via gRPC: `GenerateManifest()`
2. Repo Server:
   - Clones/updates Git repository
   - Selects appropriate tool (Helm, Kustomize, plain YAML, plugins)
   - Applies templating and parameter substitution
   - Returns list of Kubernetes manifests
3. Result cached by Git commit SHA

**Tools Supported**: Helm, Kustomize, Jsonnet, plain YAML directories, Config Management Plugins (CMP)

### Stage 4: State Comparison
**Files/Packages**: `controller/state.go`, `util/argo/diff/`

1. Controller retrieves desired state from Repo Server
2. Retrieves live state from target cluster via `kubectl get` / API calls
3. Normalizes both states:
   - Removes system-added fields (metadata, status)
   - Applies `ignoreDifferences` rules from Application spec
   - Uses CRD-aware type normalizers
4. Calculates diffs for each resource
5. Determines overall sync status: `Synced`, `OutOfSync`, or error states

### Stage 5: Health Assessment
**Files/Packages**: `controller/health.go`, `util/argo/health/`

1. For each deployed resource, assess health status
2. Uses Argo CD's health assessment rules:
   - Built-in rules for standard Kubernetes resources
   - Custom resource health definitions
3. Aggregate health across all resources
4. Determine overall application health: `Healthy`, `Progressing`, `Degraded`, `Unknown`

### Stage 6: Sync Execution (when triggered)
**Files/Packages**: `controller/sync.go`, `reposerver/apiclient/`

1. User triggers sync or auto-sync activates (if configured)
2. Controller prepares SyncOperation:
   - Determines which resources to sync (all or specific)
   - Applies sync options (PrunePropagationPolicy, RespectIgnoreDifferences, etc.)
   - Selects sync strategy (Apply or Hook-based)

3. Controller executes sync:
   - **Apply Strategy**: Uses `kubectl apply` with strategic merge patches
   - **Hook Strategy**: Looks for sync hooks (PreSync, Sync, PostSync phases)
   - Handles hooks in order: PreSync → Sync → PostSync
   - Respects sync waves (sequential ordering of resources)

4. Sync execution details:
   - For each resource, generates JSON/strategic merge patch
   - Applies patch to cluster using kubectl
   - Waits for resource to become healthy (based on health rules)
   - Records results in `status.operationState.syncResult`

### Stage 7: Status Update
**Files/Packages**: `pkg/apis/application/v1alpha1/types.go`, `server/application/`

1. Controller updates Application status:
   - `status.sync.status`: Current sync status
   - `status.health.status`: Current health status
   - `status.operationState`: Details of last operation
   - `status.resources`: List of managed resources and their statuses
   - `status.conditions`: Array of conditions (errors, warnings)

2. Status persists to `etcd`

### Stage 8: User Visibility
**Files/Packages**: `server/application/application.go`, UI TypeScript

1. API Server exposes status via REST/gRPC
2. UI/CLI polls or streams updates
3. Webhooks trigger CI/CD on sync completion

### Key Data Flow Diagram
```
Application CRD
    ↓
ApplicationController watches
    ↓
Queue application for refresh
    ↓
Call Repo Server → Generate Manifests
    ↓
Compare desired (manifests) vs live (cluster)
    ↓
Assess resource health
    ↓
Determine sync status
    ↓
(If sync triggered) Execute sync → kubectl apply
    ↓
Update Application.status
    ↓
API Server broadcasts to UI/CLI/webhooks
```

## 6. Adding a New Sync Strategy

To add a new sync strategy (e.g., a custom hook behavior or wave strategy), changes are required across multiple packages following the existing pattern of `SyncStrategy` types.

### Current Sync Strategy Architecture

The current system supports two strategies:
- **Apply Strategy** (`SyncStrategyApply`): Uses `kubectl apply` with configurable force flag
- **Hook Strategy** (`SyncStrategyHook`): Runs resources with PreSync/Sync/PostSync hooks

### Steps to Add a New Sync Strategy (Example: Custom Rolling Update Strategy)

#### 1. Define CRD Types
**File**: `pkg/apis/application/v1alpha1/types.go`

Add new strategy type:
```go
// Around line 1340-1377 where SyncStrategy is defined
type SyncStrategy struct {
    Apply *SyncStrategyApply `json:"apply,omitempty"`
    Hook *SyncStrategyHook `json:"hook,omitempty"`
    RollingUpdate *SyncStrategyRollingUpdate `json:"rollingUpdate,omitempty"` // NEW
}

type SyncStrategyRollingUpdate struct {
    BatchSize int `json:"batchSize,omitempty"`
    Delay time.Duration `json:"delay,omitempty"`
}
```

#### 2. Generate Proto Definitions
**File**: `pkg/apis/application/v1alpha1/generated.proto`

Add protobuf message definitions for interoperability with repo server.

#### 3. Update Controller Sync Logic
**File**: `controller/sync.go`

In `SyncAppState()` function (~line 90):
- Add strategy type detection
- Implement custom sync execution logic
- Handle batching and delays specific to new strategy
- Record sync phase and wave information

Example pattern:
```go
if syncOp.SyncStrategy.RollingUpdate != nil {
    err = m.syncRollingUpdate(ctx, app, operationState)
}
```

#### 4. Implement Execution Logic
**File**: `controller/sync.go` or new file

Implement the execution function:
```go
func (m *appStateManager) syncRollingUpdate(ctx context.Context, app *v1alpha1.Application, state *v1alpha1.OperationState) error {
    // 1. Group resources into batches by BatchSize
    // 2. For each batch:
    //    - Apply batch resources
    //    - Wait for health
    //    - Record progress
    //    - Sleep for Delay duration
    // 3. Handle rollback on failure
    // 4. Update state.SyncResult.Resources
}
```

#### 5. Add Sync Options Support (Optional)
**File**: `pkg/apis/application/v1alpha1/types.go`

If the strategy needs additional options, add to `SyncOperation`:
```go
type SyncOperation struct {
    SyncStrategy *SyncStrategy `json:"syncStrategy,omitempty"`
    SyncOptions SyncOptions `json:"syncOptions,omitempty"`
    // ... existing fields
    RollingUpdateOptions map[string]string `json:"rollingUpdateOptions,omitempty"` // NEW
}
```

#### 6. Add API Server Support
**File**: `server/application/application.go`

Update `Sync()` handler to validate and handle the new strategy:
```go
func (s *Server) Sync(ctx context.Context, q *application.SyncRequest) (*application.SyncResponse, error) {
    // ... existing validation

    if q.Strategy.RollingUpdate != nil {
        // Validate BatchSize > 0, etc.
    }
    // ... proceed with sync
}
```

#### 7. Update CLI
**File**: `cmd/argocd/commands/app.go`

Add CLI flags for the new strategy:
```go
command.Flags().StringVar(&syncOpt, "strategy", "", "Sync strategy: apply|hook|rolling-update")
command.Flags().IntVar(&batchSize, "batch-size", 1, "Batch size for rolling update")
```

#### 8. Add Tests
**Files**: `controller/sync_test.go`, `test/e2e/sync_waves_test.go`

Add unit tests:
```go
func TestSyncRollingUpdate(t *testing.T) {
    // Setup application with rolling update strategy
    // Execute sync
    // Verify batching and delays
    // Verify resources applied in correct order
}
```

Add E2E tests:
```go
func TestRollingUpdateStrategy(t *testing.T) {
    Given(t).
        When().CreateApp(NewApp(WithSyncStrategy("rolling-update"))).
        Then().ExpectBatchedSync()
}
```

#### 9. Update Documentation
**Files**: `docs/user-guide/sync-options.md`, `docs/user-guide/sync-strategies.md`

Document the new strategy with examples.

### Key Integration Points

1. **CRD Definitions** (`pkg/apis/application/v1alpha1/types.go`): Define the strategy specification
2. **Controller Reconciliation** (`controller/sync.go`): Execute the strategy
3. **Health Assessment** (`controller/health.go`): May need strategy-specific health checks
4. **API Server** (`server/application/application.go`): Validate and expose strategy in API
5. **CLI** (`cmd/argocd/commands/app.go`): Allow users to specify strategy
6. **Proto Definitions** (`pkg/apis/application/v1alpha1/generated.proto`): For gRPC compatibility
7. **Tests**: Unit and E2E test coverage

### Design Considerations

- **Idempotency**: Ensure sync can be safely re-applied without duplicate operations
- **Rollback**: Consider rollback mechanism if sync fails mid-strategy
- **Status Tracking**: Record phase, batch number, and resource status details
- **Error Handling**: Define behavior on resource deployment failures
- **Wave Compatibility**: Consider interaction with existing sync waves feature
- **Hook Compatibility**: Consider if strategy supports PreSync/Sync/PostSync hooks
