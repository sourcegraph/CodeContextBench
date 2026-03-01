# Argo CD Codebase Orientation

## 1. Main Entry Points

Argo CD is a multi-binary system built on a single main entry point (`/workspace/cmd/main.go`) that dispatches to different components based on the binary name. Here are the 4 main components:

### API Server
- **Binary**: `argocd-server`
- **Entry Point**: `/workspace/cmd/argocd-server/commands/argocd_server.go` - `NewCommand()` function
- **Responsibility**: Exposes the gRPC/REST API consumed by the Web UI, CLI, and CI/CD systems. Handles:
  - gRPC server setup on configurable port (default 8080)
  - REST gateway for HTTP clients
  - Authentication and authorization via JWT tokens
  - Application resource management (CRUD operations)
  - Webhook handling for Git repository events
  - TLS configuration and security policies
- **Key File**: `/workspace/server/server.go` - contains `ArgoCDServerOpts` configuration struct and `NewServer()` function

### Application Controller
- **Binary**: `argocd-application-controller`
- **Entry Point**: `/workspace/cmd/argocd-application-controller/commands/argocd_application_controller.go` - `NewCommand()` function
- **Responsibility**: Core reconciliation loop that continuously monitors running applications and compares live state against desired state. Performs:
  - Application state management and health assessment
  - Synchronization of application manifests to target clusters
  - Resource diffing and comparison with desired state
  - Handling sync operations, rollbacks, and recovery actions
  - Metrics collection and status updates
  - Sharding support for horizontal scaling
- **Key File**: `/workspace/controller/appcontroller.go` - contains `ApplicationController` type (core reconciliation logic)

### Repository Server
- **Binary**: `argocd-repo-server`
- **Entry Point**: `/workspace/cmd/argocd-repo-server/commands/argocd_repo_server.go` - `NewCommand()` function
- **Responsibility**: Internal service that maintains a local cache of Git repositories and generates Kubernetes manifests. Handles:
  - Git repository caching and credential management
  - Manifest generation from various sources (Kustomize, Helm, raw manifests, plugins)
  - Rendering of ConfigMaps, Secrets, and Helm values
  - CMP (Config Management Plugin) support for custom tools
  - gRPC API for manifest generation requests
- **Key File**: `/workspace/reposerver/repository/repository.go` - contains manifest generation logic

### ApplicationSet Controller
- **Binary**: `argocd-applicationset-controller`
- **Entry Point**: `/workspace/cmd/argocd-applicationset-controller/commands/applicationset_controller.go` - `NewCommand()` function (note: package is `command`, not `commands`)
- **Responsibility**: Manages declarative ApplicationSet resources that generate multiple Applications from templates. Handles:
  - ApplicationSet template rendering
  - Generator execution (Git, Cluster, SCM providers, etc.)
  - Application generation from templates
  - Progressive sync strategies
  - Webhook support for SCM events
- **Key File**: `/workspace/applicationset/controllers/` - contains ApplicationSet reconciliation logic

---

## 2. Core Packages

### 1. **`/workspace/pkg/apis/application/v1alpha1`** - API Types & CRDs
- Defines all Custom Resource Definitions (CRDs) for Argo CD
- Contains core types: `Application`, `AppProject`, `ApplicationSet`, `Repository`, `Cluster`
- Includes validation, webhook markers, and Kubernetes codegen directives
- Key files: `types.go` (Application), `applicationset_types.go` (ApplicationSet), `types_test.go`
- Exports proto definitions for gRPC services

### 2. **`/workspace/controller`** - Application Reconciliation Engine
- Implements the core reconciliation loop for Applications
- Key components:
  - `appcontroller.go` - Main controller implementing `ApplicationController` interface with workqueue-based reconciliation
  - `sync.go` - Handles sync operation execution, wave synchronization, and sync result tracking
  - `state.go` - Manages application state calculation and status updates
  - `health.go` - Health assessment for resources
  - `hook.go` - Sync hook and PreDelete/PostDelete hook execution
  - `cache/` - In-memory caching of application state and live cluster state
  - `metrics/` - Prometheus metrics collection (sync count, resource count, etc.)
  - `sharding/` - Distributed application shard assignment for scaling

### 3. **`/workspace/reposerver`** - Manifest Generation & Repository Management
- Provides gRPC service for manifest generation and git operations
- Key components:
  - `repository/repository.go` - Service implementing manifest generation RPC
  - `apiclient/` - gRPC client for calling repo server from other components
  - `cache/` - Repository caching layer using Redis or in-memory storage
  - `metrics/` - Performance metrics (generation time, cache hits, etc.)
  - `askpass/` - Git credential handling via ssh-askpass socket

### 4. **`/workspace/server`** - API Server & REST/gRPC Gateway
- Implements gRPC and REST APIs exposed to clients
- Key components:
  - `server.go` - Main server with `ArgoCDServerOpts` and gRPC setup
  - `application/` - Application CRUD and sync operation services (implements gRPC ApplicationService)
  - `applicationset/` - ApplicationSet management services
  - `cluster/` - Cluster management and credential handling
  - `repository/` - Repository credential and configuration management
  - `project/` - AppProject RBAC and management
  - `account/` - User account and authentication management
  - `cache/` - Server-side caching (Redis-backed or in-memory)
  - `session/` - JWT session management for authentication
  - `metrics/` - HTTP metrics endpoint

### 5. **`/workspace/util`** - Utility Libraries
- Provides shared utilities across components:
  - `util/env/` - Environment variable parsing with type conversion and validation (ParseNumFromEnv, ParseBoolFromEnv, StringFromEnv)
  - `util/settings/` - Settings manager for ConfigMap-based configuration (RBAC policies, repository credentials, etc.)
  - `util/argo/` - Argo-specific utilities (diff normalization, manifest rendering, sync strategies)
  - `util/cli/` - Common CLI utilities and logging setup
  - `util/kube/` - Kubernetes client utilities
  - `util/cache/` - Generic caching utilities
  - `util/db/` - Database/Secret storage utilities
  - `util/errors/` - Error handling utilities

---

## 3. Configuration Loading

Each component loads configuration through a consistent pattern:

### Configuration Pipeline

1. **CLI Flags (Primary Source)**
   - Each component defines flags using `github.com/spf13/cobra` command framework
   - Flags use `command.Flags().StringVar()`, `BoolVar()`, `IntVar()`, etc.
   - Example: `/workspace/cmd/argocd-server/commands/argocd_server.go` lines 281-318

2. **Environment Variables (Override)**
   - Flags bind to environment variables with defaults
   - Parsing functions from `/workspace/util/env/env.go`:
     - `ParseNumFromEnv(envVar, defaultValue, min, max)` - Parse integers with bounds
     - `ParseBoolFromEnv(envVar, defaultValue)` - Parse booleans
     - `StringFromEnv(envVar, defaultValue)` - Parse strings
     - `ParseStringToStringFromEnv(envVar, defaultValue, separator)` - Parse maps
   - Priority: Command-line flag > Environment variable > Default value
   - Example: `listenPort` in API server uses `env.StringFromEnv("ARGOCD_SERVER_LISTEN_ADDRESS", common.DefaultAddressAPIServer)`

3. **ConfigMap/Settings (Runtime Configuration)**
   - `/workspace/util/settings/settings.go` - Settings manager that reads from ConfigMap `argocd-cm` in cluster
   - Manages:
     - RBAC policies (policy.default, policy.csv)
     - Repository credentials configuration
     - Repository SSL certificate configuration
     - UI theme and customization settings
   - Settings are loaded at startup and cached in memory

4. **Configuration Struct Definitions**
   - **API Server**: `ArgoCDServerOpts` in `/workspace/server/server.go`
   - **Application Controller**: Flags stored as local variables in `NewCommand()`, then passed to controller initialization
   - **Repo Server**: `RepoServerInitConstants` in `/workspace/reposerver/repository/repository.go`
   - **ApplicationSet Controller**: Flags in `NewCommand()` passed to controller manager setup

5. **Example: API Server Configuration Loading** (`/workspace/cmd/argocd-server/commands/argocd_server.go` lines 104-251)
   ```
   1. Parse kubectl flags for cluster access (cli.AddKubectlFlagsToCmd)
   2. Define flags for server-specific settings (port, address, TLS, repo-server address)
   3. Parse environment variables for each flag (e.g., ARGOCD_SERVER_LISTEN_ADDRESS)
   4. In Run() callback:
      - Get namespace and client config
      - Initialize Kubernetes clients (clientset, dynamic, etc.)
      - Setup TLS configuration
      - Setup Redis cache if configured
      - Create ArgoCDServerOpts struct with all parsed settings
      - Create server with NewServer() and call Init()
   ```

---

## 4. Test Structure

The project uses multiple testing approaches at different levels:

### 1. **Unit Tests** (`*_test.go` in source directories)
- **Location**: Alongside source code (e.g., `controller/appcontroller_test.go`, `server/server_test.go`)
- **Framework**: Go's standard `testing` package
- **Assertions**:
  - `github.com/stretchr/testify/assert` - Assertions that continue on failure
  - `github.com/stretchr/testify/require` - Assertions that fail fast
  - `github.com/stretchr/testify/mock` - Mock objects for interfaces
- **Fake Clients**: Uses `k8s.io/client-go/kubernetes/fake.Clientset` for mocking Kubernetes clients
- **Example**: `/workspace/controller/appcontroller_test.go` tests individual controller methods with mocked dependencies

### 2. **Integration Tests**
- **Location**: Alongside source files or in component test files
- **Approach**: Tests that use real Kubernetes clients or close integration between components
- **Example**: `/workspace/reposerver/repository/repository_test.go` tests manifest generation with actual Git operations
- **Key Packages**:
  - `github.com/argoproj/gitops-engine/pkg/utils/kube/kubetest` - GitOps Engine test utilities

### 3. **E2E Tests** (End-to-End / Acceptance Tests)
- **Location**: `/workspace/test/e2e/`
- **Pattern**: Tests run against a full Argo CD deployment in a Kubernetes cluster
- **Key Test Files**:
  - `app_management_test.go` - Application creation, sync, update, deletion
  - `applicationset_test.go` - ApplicationSet generation and templating
  - `app_autosync_test.go` - Automated sync behavior
  - `cluster_generator_test.go` - ApplicationSet cluster generator
  - Various feature-specific tests (hooks, multiple sources, notifications, etc.)
- **Fixture-based Testing**: Uses fixture pattern for setup/teardown
  - `test/e2e/fixture/app` - Application fixture builder
  - `test/e2e/fixture/account` - Account fixture builder
  - `test/e2e/fixture/project` - Project fixture builder
  - `test/e2e/fixture/repos` - Repository fixture builder
- **Example Test Pattern** (`/workspace/test/e2e/app_management_test.go` lines 58-80):
  ```go
  accountFixture.Given(t).
      Name("test").
      When().
      Create().
      Login().
      SetPermissions([...]).
      // ... more setup ...
      Then().
      Expect(...)
  ```

### 4. **Test Data & Fixtures**
- **Location**: `/workspace/test/fixture/` - Sample manifests and configurations
  - `guestbook/` - Simple multi-tier application
  - Various subdirectories for different manifest types
- **Location**: `/workspace/test/e2e/testdata/` - Test case data
- **Location**: `testdata/` directories in individual packages

### 5. **Testing Framework Commands**
- **Unit Tests**: `make test` or `make test-local` (runs in Docker or locally)
- **Race Detection**: `make test-race` - Detects data race conditions
- **E2E Tests**: `make test-e2e` - Full end-to-end testing against Kubernetes cluster

---

## 5. Application Sync Pipeline

The sync pipeline processes an Application resource from definition to actual deployment. Here's the detailed flow:

### Stage 1: **CRD Definition & Specification**
- **Files**: `/workspace/pkg/apis/application/v1alpha1/types.go`
- **Types**:
  - `Application` - Main CRD with metadata, spec, status
  - `ApplicationSpec` - Contains source, destination, sync policy
  - `ApplicationSource` - Git repo URL, path, revision, and tool-specific configs (Helm, Kustomize, Plugin)
  - `SyncPolicy` - Defines automated sync and sync options
- **Key Fields**:
  - `Spec.Source.RepoURL` - Git repository
  - `Spec.Source.Path` - Directory in repository
  - `Spec.Source.TargetRevision` - Git branch/tag/commit
  - `Spec.Destination.Server` - Target Kubernetes cluster
  - `Spec.Destination.Namespace` - Target namespace
  - `Spec.SyncPolicy` - Auto-sync, retry, sync options

### Stage 2: **Application Controller Reconciliation**
- **Files**: `/workspace/controller/appcontroller.go` (main reconciliation loop)
- **Process**:
  1. Controller watches Application CRDs via informer (line ~200)
  2. Workqueue processes applications based on resync period (default 180 seconds)
  3. `syncAppState()` method initiates reconciliation (sync.go line 90)
  4. Gets Application from apiserver
  5. Determines sync comparison mode (latest revision, recent revision, etc.)
  6. Calls `RefreshAppStatus()` to calculate desired and live states
  7. Calls `SyncAppState()` to execute sync operation if needed
- **Key Metrics**: Controller tracks pending operations, sync success/failure

### Stage 3: **Manifest Generation (Repo Server)**
- **Files**: `/workspace/reposerver/repository/repository.go`
- **RPC Method**: `GenerateManifest()` called by controller
- **Process**:
  1. Fetch Git repository and specified revision
  2. Render manifests based on source type:
     - **Raw YAML**: Direct file reading from specified path
     - **Kustomize**: `kustomize build` execution on path
     - **Helm**: `helm template` with values rendering
     - **Plugin/CMP**: Execute custom tool via Container Management Plugin
  3. Apply parameter overrides and variable substitution
  4. Return Kubernetes manifest list (unstructured resources)
  5. Cache result in Redis for performance
- **Key File**: `reposerver/repository/repository.go` lines 515-585

### Stage 4: **State Calculation & Diffing**
- **Files**: `/workspace/controller/state.go`, `/workspace/util/argo/diff/`
- **Process**:
  1. **Get Desired State**: Manifests from repo server (Stage 3)
  2. **Get Live State**: Query target Kubernetes cluster for actual resources
  3. **Normalization**: Apply normalizers to ignore insignificant differences:
     - Ignore timestamps, generation numbers
     - Apply custom ignore rules from `Application.Spec.IgnoreDifferences`
     - Normalize resource fields for comparison
  4. **Diff Calculation**: Compare desired vs. live using gitops-engine
  5. **Health Assessment**: Determine health status (Healthy, Progressing, Degraded)
  6. **Status Update**: Store results in `Application.Status.Resources`
- **Outputs**: Application status with resource health, sync status, resource tree

### Stage 5: **Sync Operation Execution**
- **Files**: `/workspace/controller/sync.go`
- **Process**:
  1. **SyncWave Ordering**: Resources are grouped by `argocd.argoproj.io/compare-result: "true"` annotation
  2. **Wave Synchronization**: Resources applied in order of `argocd.argoproj.io/sync-wave` (default 0)
  3. **Resource Application**:
     - For each resource in sync wave:
       - Call `kubectl apply` or create/update via Kubernetes API
       - Handle three-way merge (desired, live, last-applied)
       - Apply sync hooks if configured
  4. **Hook Execution** (`controller/hook.go`):
     - Pre-sync hooks: Execute before resource application
     - Sync hooks: Execute during resource application
     - Post-sync hooks: Execute after successful application
  5. **Progress Tracking**: Monitor resource health and application status
  6. **Retry Logic**: Configurable retry strategy on failures
- **Key Func**: `SyncAppState()` in sync.go orchestrates the sync process
- **SyncWave Delay**: Controlled by `ARGOCD_SYNC_WAVE_DELAY` environment variable (default per wave based on resource type)

### Stage 6: **Health Assessment & Status Update**
- **Files**: `/workspace/controller/health.go`
- **Process**:
  1. Determine health status for each resource type:
     - Deployment/StatefulSet: Check replica readiness
     - Pod: Check phase and conditions
     - Service: Check if ready
     - Job/CronJob: Check completion
  2. Aggregate to application-level health
  3. Update Application.Status with:
     - `OperationState` - Result of sync operation
     - `SyncResult` - Detailed sync results
     - `Health` - Overall health status
  4. Store revision information for rollback capability
- **Result**: Application status reflects current state and sync results

### Complete Flow Example
```
User creates Application CRD
        ↓
Application Controller detects via informer
        ↓
Repo Server generates manifests from Git
        ↓
Controller diffs desired vs. live state
        ↓
Controller executes sync in waves with hooks
        ↓
Resources applied to Kubernetes cluster
        ↓
Health assessment updates Application status
        ↓
User sees sync status and resource health in UI
```

---

## 6. Adding a New Sync Strategy

To implement a new sync strategy (e.g., custom hooks, wave behavior, or conditional sync), you would need to modify these components and files:

### Required Modifications:

1. **CRD Type Definition** (`/workspace/pkg/apis/application/v1alpha1/types.go`)
   - Add new field to `SyncStrategy` struct (around line 1342)
   - Add new field to `SyncOperation` struct for operation parameters
   - Update `.proto` file for gRPC serialization (`/workspace/pkg/apis/application/v1alpha1/generated.proto`)
   - Run code generation: `make codegen` to update generated files (zz_generated.deepcopy.go, generated.pb.go)

2. **Sync Execution Logic** (`/workspace/controller/sync.go`)
   - Modify `SyncAppState()` function to handle new strategy
   - Add helper functions for new sync behavior (similar to `delayBetweenSyncWaves()` at line 557)
   - If wave-based: Integrate with gitops-engine sync wave hook mechanism (line 357: `sync.WithSyncWaveHook`)
   - If conditional: Add pre-sync filtering logic
   - Update operation state tracking for the new strategy

3. **Resource Application Logic** (`/workspace/controller/sync.go`)
   - Modify resource filtering/ordering logic
   - Add pre-application/post-application checks
   - Handle retry logic specific to strategy
   - Update metrics collection for strategy-specific metrics

4. **API Server Updates** (`/workspace/server/application/application.go`)
   - Update `Sync()` RPC handler if strategy requires client input
   - Add new fields to SyncOptions struct if needed
   - Update validation logic for new strategy parameters

5. **Controller Initialization** (`/workspace/cmd/argocd-application-controller/commands/argocd_application_controller.go`)
   - Add CLI flags for strategy configuration if needed
   - Initialize strategy-specific components

6. **Tests**
   - Unit tests: `controller/sync_test.go` - Test sync logic with new strategy
   - Unit tests: `pkg/apis/application/v1alpha1/types_test.go` - Test type validation
   - E2E tests: `test/e2e/app_sync_options_test.go` - Test end-to-end sync behavior
   - Add test fixtures in `test/fixture/` for testing the new strategy

### Example: Adding a "Sequential Namespace Sync" Strategy

**Step 1**: Add to `SyncStrategy` in types.go
```go
type SyncStrategy struct {
    Apply *SyncStrategyApply `json:"apply,omitempty"`
    Hook *SyncStrategyHook `json:"hook,omitempty"`
    Sequential *SyncStrategySequential `json:"sequential,omitempty"` // NEW
}

type SyncStrategySequential struct {
    Namespace string `json:"namespace,omitempty"`
    MaxConcurrency int `json:"maxConcurrency,omitempty"`
}
```

**Step 2**: Modify `SyncAppState()` in sync.go to respect sequential namespace ordering

**Step 3**: Update `delayBetweenSyncWaves()` or add new hook function for namespace-aware wave delays

**Step 4**: Add tests covering the new strategy

**Step 5**: Update CLI documentation and examples

### Key Integration Points:

- **gitops-engine dependency**: Uses `github.com/argoproj/gitops-engine/pkg/sync` for core sync logic
  - `sync.PerformSync()` - Main sync execution function
  - `sync.WithSyncWaveHook()` - Wave-based execution hook
  - `sync.ResourceOperations` - Interface for resource apply/delete

- **Metrics**: Add metrics in `/workspace/controller/metrics/` for monitoring new strategy
  - Track strategy-specific counters (e.g., sequential syncs, conditional skips)
  - Track timing metrics

- **Backward Compatibility**: Ensure new strategy is optional; existing applications continue working with default strategy

