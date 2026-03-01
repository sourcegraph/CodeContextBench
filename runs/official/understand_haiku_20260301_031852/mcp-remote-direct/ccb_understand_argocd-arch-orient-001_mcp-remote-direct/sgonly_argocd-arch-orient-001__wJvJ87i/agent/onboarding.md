# Argo CD Codebase Orientation

## 1. Main Entry Points

Argo CD is a multi-binary system with distinct components, each with its own entry point in the `cmd/` directory:

### API Server (`argocd-server`)
- **Entry Point**: `cmd/argocd-server/commands/argocd_server.go:NewCommand()`
- **Primary Responsibility**: Provides the gRPC and REST API server for Argo CD. Handles user authentication, application management, cluster management, repository credentials, and all user-facing operations. Serves the Web UI and runs on port 8080 by default.
- **Key Function**: Listens for client requests and manages state through the Kubernetes API server.

### Application Controller (`argocd-application-controller`)
- **Entry Point**: `cmd/argocd-application-controller/commands/argocd_application_controller.go:NewCommand()`
- **Primary Responsibility**: The core reconciliation engine. Continuously monitors Application CRD resources and compares desired state (from git) against live state (in Kubernetes clusters). Executes sync operations to bring clusters into sync with desired state. Manages application status, health checks, and sync waves.
- **Key Function**: Implements the main control loop that performs GitOps reconciliation using informers and work queues.

### Repository Server (`argocd-repo-server`)
- **Entry Point**: `cmd/argocd-repo-server/commands/argocd_repo_server.go:NewCommand()`
- **Primary Responsibility**: Generates Kubernetes manifests from various sources (Helm, Kustomize, Jsonnet, plain YAML, etc.). Clones and maintains git repositories, performs manifest generation, and caches results. Communicates via gRPC with the API server and application controller.
- **Key Function**: Isolated service that handles all git operations and manifest generation to keep these resource-intensive operations separate from the main controller.

### ApplicationSet Controller (`argocd-applicationset-controller`)
- **Entry Point**: `cmd/argocd-applicationset-controller/commands/command.go:NewCommand()`
- **Primary Responsibility**: Manages ApplicationSet CRD resources which generate multiple Application resources dynamically using generators (cluster generator, git generator, matrix generator, etc.). Implements progressive syncs for rolling deployments and integrates with webhooks.
- **Key Function**: Provides templating and automation for managing applications across multiple clusters with different configurations.

### Main Router (`cmd/main.go`)
Routes to the appropriate component based on the binary name being executed, supporting a single multi-binary executable.

---

## 2. Core Packages

### `pkg/apis/application/v1alpha1/` - API Types and CRDs
- **Responsibility**: Defines all Argo CD CRD types and API structures
- **Key Files**:
  - `types.go`: Core Application, ApplicationSpec, ApplicationStatus, SyncOperation types
  - `applicationset_types.go`: ApplicationSet and ApplicationSetGenerator types
  - `app_project_types.go`: AppProject type for RBAC and multi-tenancy
  - `repository_types.go`: Repository and RepositoryCredentials types
- **Critical Structs**: `Application`, `ApplicationSpec`, `ApplicationStatus`, `SyncPolicy`, `SyncOperation`, `SyncStrategy`

### `controller/` - Application Reconciliation and Sync Logic
- **Responsibility**: Core reconciliation loop and state synchronization engine
- **Key Files**:
  - `appcontroller.go`: Main ApplicationController struct with reconciliation loop
  - `sync.go`: Sync operation execution and resource synchronization logic
  - `state.go`: Application state calculation (desired vs live)
  - `hook.go`: Pre/post-sync and post-delete hook execution
  - `health.go`: Resource health assessment
  - `cache/`: Live state cache for tracking cluster resources
- **Critical Methods**: `ApplicationController.syncAppState()`, `ApplicationController.processAppOperation()`, state calculation and health assessment

### `server/` - API Server and REST/gRPC Endpoints
- **Responsibility**: REST and gRPC API implementation, user interface backend
- **Key Subdirectories**:
  - `application/`: Application management endpoints
  - `cluster/`: Cluster management endpoints
  - `repository/`: Repository credential management
  - `session/`: Authentication and RBAC
  - `cache/`: Server-side caching for performance
  - `settings/`: Configuration management
- **Critical Methods**: Implement CRUD operations for Application, Cluster, Repository resources

### `reposerver/` - Git and Manifest Management
- **Responsibility**: Isolated service for git operations and manifest generation
- **Key Files**:
  - `server.go`: gRPC server setup and lifecycle
  - `repository/repository.go`: Manifest generation for different templating systems
  - `apiclient/`: Types for gRPC communication with application controller
  - `cache/`: Manifest caching to avoid redundant generations
- **Critical Methods**: GenerateManifests(), ListDirectory(), GetAppDetails()

### `applicationset/` - ApplicationSet Generation and Templating
- **Responsibility**: Dynamic Application generation from ApplicationSet resources
- **Key Subdirectories**:
  - `controllers/`: Main ApplicationSet reconciliation controller
  - `generators/`: Implementations of various generators (cluster, git, matrix, SCM, etc.)
  - `services/`: Template rendering and application generation
- **Critical Structs**: `ApplicationSetController`, various Generator interfaces

### `util/` - Utility Packages
Essential utility packages used across the codebase:
- **`util/argo/`**: Argo CD-specific utilities for application tracking, manifest comparison, diff calculation
- **`util/kube/`**: Kubernetes API interactions, kubectl wrapper
- **`util/cache/`**: Application state caching, Redis integration
- **`util/git/`**: Git operations (clone, fetch, commit operations)
- **`util/helm/`**: Helm chart rendering and caching
- **`util/settings/`**: Configuration loading from ConfigMaps and Secrets
- **`util/db/`**: Database (Kubernetes secret) abstraction for Argo CD configuration
- **`util/rbac/`**: RBAC policy enforcement
- **`util/dex/`**: OIDC/SSO integration with Dex

---

## 3. Configuration Loading

### Configuration Pipeline

Argo CD uses a multi-layered configuration approach:

#### 1. **CLI Flags and Environment Variables**
- **Library**: `github.com/spf13/cobra` for CLI framework
- **Usage**: Each component's NewCommand() function defines CLI flags in cobra.Command.Flags()
- **Examples**:
  - `--repo-server`: Address of repo server (default: `argocd-repo-server:8081`)
  - `--kubeconfig`: Kubernetes config file
  - `--loglevel`: Logging level

#### 2. **Settings Manager** (`util/settings/settings.go`)
- **Struct**: `ArgoCDSettings` holds in-memory configuration
- **Source**: Kubernetes ConfigMaps and Secrets
  - `argocd-cm`: Application ConfigMap with URLs, SSO, webhook secrets, etc.
  - `argocd-secret`: Secret with JWT signing keys, certificate data, etc.
- **Loading**: Informers watch ConfigMap/Secret changes for live reload
- **Key Configuration Fields**:
  - `URL`: External Argo CD server URL
  - `DexConfig`: OIDC provider configuration
  - `ServerSignature`: JWT signing key
  - `Certificate`: TLS certificate for API server

#### 3. **Database** (`util/db/db.go`)
- **Purpose**: Abstraction for storing cluster credentials and repository credentials
- **Storage**: Kubernetes Secrets with labels `argocd.argoproj.io/secret-type`
- **Types**: `cluster`, `repository`, `repo-creds`

#### 4. **Application Controller Configuration** (`cmd/argocd-application-controller/commands/argocd_application_controller.go`)
- **Key Parameters**:
  - `--app-resync-period`: How often to sync applications (default: 180s)
  - `--hard-resync-period`: Force full status refresh
  - `--status-processors`: Parallel status processing threads
  - `--operation-processors`: Parallel operation processing threads
  - `--repo-server-timeout-seconds`: gRPC timeout for repo server calls

#### 5. **Repository Server Configuration** (`cmd/argocd-repo-server/commands/argocd_repo_server.go`)
- **Key Parameters**:
  - `--parallelism-limit`: Max concurrent manifest generation requests
  - `--helm-index-cache-duration`: Helm repo index caching
  - `--max-combined-directory-manifests-size`: Validation for manifest size

#### 6. **Common Package Constants** (`common/common.go`)
- Defines ConfigMap/Secret names, port defaults, and environment variable constants
- Service addresses: `DefaultRepoServerAddr`, `DefaultDexServerAddr`, `DefaultRedisAddr`
- ConfigMap names: `argocd-cm`, `argocd-rbac-cm`, `argocd-ssh-known-hosts-cm`, etc.

---

## 4. Test Structure

### Unit Tests
- **Location**: Throughout codebase with `*_test.go` suffix
- **Framework**: Go's standard `testing` package with assertions
- **Examples**: `controller/appcontroller_test.go`, `util/argo/diff_test.go`
- **Scope**: Test individual functions and small components in isolation
- **Characteristics**: Fast, no cluster dependency

### Integration Tests
- **Location**: Scattered with unit tests, often in same `*_test.go` files
- **Focus**: Test interactions between multiple packages
- **Examples**: Testing Application CRD parsing + controller state updates
- **Characteristics**: May use mocks or local in-memory structures

### E2E Tests (End-to-End)
- **Location**: `test/e2e/` directory
- **Framework**: Go's `testing` package + custom fixtures in `test/e2e/fixture/`
- **Infrastructure**:
  - **Fixture**: `test/e2e/fixture/fixture.go` - Sets up real Kubernetes cluster, Argo CD components, git test repos
  - **Test Data**: `test/e2e/testdata/` - Sample applications, manifests, and configurations
  - **Execution**: Deploys actual Argo CD components in Docker/Kubernetes
- **Types of E2E Tests**:
  - **Application Management**: `app_management_test.go` - CRUD operations, basic syncing
  - **Sync Features**: `sync_waves_test.go`, `sync_options_test.go` - Sync strategies, waves, hooks
  - **Tool Integration**: `helm_test.go`, `kustomize_test.go`, `jsonnet_test.go` - Different manifest generators
  - **Special Features**: `applicationset_test.go`, `app_autosync_test.go`, `cluster_generator_test.go`
  - **Advanced**: `deployment_test.go`, `selective_sync_test.go`, `git_submodule_test.go`
- **Environment**: Requires Docker, Kubernetes cluster, and git test repositories
- **Characteristics**: Slow, comprehensive, tests real-world scenarios

### Test Utilities
- **`test/testutil.go`**: Common test utilities and helpers
- **`test/testdata.go`**: Test data generation
- **`util/test/`**: Shared testing utilities across packages

---

## 5. Application Sync Pipeline

The path of an Application resource from CRD definition to actual deployment in Kubernetes:

### Stage 1: Application CRD Admission and Storage
- **File**: `pkg/apis/application/v1alpha1/types.go` - Application struct definition
- **Process**: User creates Application CRD in Kubernetes cluster
- **Storage**: Kubernetes API server persists Application resource
- **Outcome**: Application resource available in cluster

### Stage 2: Application Discovery and Queuing
- **File**: `controller/appcontroller.go` - ApplicationController struct and reconciliation loop
- **Process**:
  - Kubernetes informer watches Application resources
  - Controller's work queue receives application name/namespace when created/modified
  - Events trigger from: Application change, referenced cluster change, or time-based resync
- **Components**:
  - `appRefreshQueue`: Primary queue for application refreshes
  - `appOperationQueue`: Queue for sync/rollback/delete operations
  - `projectRefreshQueue`: Queue for AppProject changes affecting apps
- **Outcome**: Application enters reconciliation pipeline

### Stage 3: State Calculation and Comparison
- **Files**:
  - `controller/state.go:GetRepoObjs()` - Gets desired state
  - `controller/appcontroller.go:refreshAppStatus()` - Compares states
  - `util/argo/diff/` - Diff calculation logic
- **Process**:
  - Desired State: Calls repo server to generate manifests from git sources
  - Live State: Queries live cluster for actual resources
  - Diff: Compares desired vs live and calculates differences
  - Health: Assesses resource health status
- **Key Data Flow**:
  1. `ApplicationController.syncAppState()` is called
  2. Calls `repoClient.GenerateManifests()` via gRPC (repo server)
  3. Calls `liveStateCache.GetClusterCache()` for live resources
  4. `appStateManager.GetRepoObjs()` processes manifests
  5. Diff engine compares manifests with live resources
- **Outcome**: Application.Status contains sync status (Synced/OutOfSync) and resource list

### Stage 4: Sync Policy Evaluation
- **File**: `pkg/apis/application/v1alpha1/types.go` - SyncPolicy struct
- **Process**:
  - Evaluates `Application.Spec.SyncPolicy`:
    - If `automated.enabled`: Auto-sync is enabled (can have `prune` and `selfHeal` options)
    - If sync needed: Automatic or manual operation is initiated
- **Options**:
  - `SyncOptions`: Controls sync behavior (e.g., `Validate=false`, `PrunePropagationPolicy=foreground`)
  - `Retry`: Retry policy for failed syncs
- **Outcome**: Sync operation is queued if needed

### Stage 5: Sync Strategy Application
- **File**: `controller/sync.go` and `pkg/apis/application/v1alpha1/types.go` - SyncStrategy
- **Process**:
  - Two strategies available:
    - **Hook Strategy**: Uses Argo CD hook annotations (`argocd.argoproj.io/hook`) or Helm hooks
    - **Apply Strategy**: Direct kubectl apply without hooks
  - Default: Hook strategy (falls back to apply if no hooks found)
- **Outcome**: Sync strategy determines how resources are applied

### Stage 6: Sync Wave Processing
- **Files**:
  - `controller/sync.go`: Wave execution logic
  - `pkg/apis/application/v1alpha1/types.go`: SyncWave annotation `argocd.argoproj.io/sync-wave`
  - External: `github.com/argoproj/gitops-engine/pkg/sync/syncwaves` - gitops-engine wave logic
- **Process**:
  1. Resources grouped by sync-wave annotation (default: 0)
  2. Pre-sync hooks executed (only hooks allowed in pre-sync phase)
  3. Sync phase: Waves executed sequentially (0, 1, 2, ...)
  4. Resources within same wave applied in parallel
  5. Controller waits for all resources in wave to become healthy before next wave
  6. Post-sync hooks executed after sync completes
- **Configuration**:
  - `--sync-wave-delay`: Delay between waves (from `ARGOCD_SYNC_WAVE_DELAY`)
  - Annotation value: Wave number (e.g., `argocd.argoproj.io/sync-wave: "5"`)
- **Outcome**: Ordered resource deployment with health checks between waves

### Stage 7: Resource Synchronization
- **Files**:
  - `controller/sync.go:syncResourcesUsingResourceOperations()` - Main sync execution
  - `util/kube/`: kubectl wrapper and resource operations
  - External: `github.com/argoproj/gitops-engine/pkg/sync` - gitops-engine sync engine
- **Process**:
  1. For each resource in current wave:
     - Get desired manifest from generated objects
     - Determine operation: Create, Update, Delete
     - Apply using kubectl (with sync options applied)
     - Record result in operation state
  2. Monitor resource health after application
  3. Handle sync options like `Force`, `DisableDeletion`, `ApplyOutOfSyncOnly`
- **Outcome**: Kubernetes resources created/updated/deleted in target cluster

### Stage 8: Status Update and Recording
- **Files**:
  - `controller/appcontroller.go:persistAppStatus()` - Updates Application.Status
  - `controller/sync.go:updateOperationState()` - Updates operation state
- **Process**:
  1. Application.Status.SyncResult updated with:
     - Resources synced and their individual statuses
     - Revision information
     - Sync time and phase
  2. Application.Status.OperationState records:
     - Sync operation result
     - Start/finish times
     - Error information
  3. Resource-level status: Each ResourceStatus includes:
     - Health status
     - Sync status
     - Kind, name, namespace, group
     - Sync wave information
- **Outcome**: Application.Status reflects current sync state

### Stage 9: Metrics and Auditing
- **Files**:
  - `controller/metrics/`: Prometheus metrics
  - `util/argo/audit.go`: Audit logging
- **Recording**:
  - Sync operation metrics (duration, success/failure)
  - Resource metrics (health, sync status)
  - Audit logs for compliance tracking
- **Outcome**: Monitoring data available for dashboards and alerting

---

## 6. Adding a New Sync Strategy

To add a new sync strategy (e.g., a custom hook behavior or wave strategy), follow this sequence:

### Step 1: Define the Strategy Type
- **File**: `pkg/apis/application/v1alpha1/types.go`
- **Changes**:
  - Add new struct for your strategy (e.g., `SyncStrategyCustom`)
  - Add field to `SyncStrategy` struct
  - Include kubebuilder validation markers
  - Add protobuf annotations for gRPC marshaling
- **Example**:
  ```go
  type SyncStrategyCustom struct {
      // Your options here
      Option1 string `json:"option1,omitempty" protobuf:"bytes,1,opt,name=option1"`
  }
  ```

### Step 2: Update Generated Code
- **Files**:
  - `pkg/apis/application/v1alpha1/generated.pb.go` - Protocol buffer generated code
  - `pkg/apis/application/v1alpha1/zz_generated.deepcopy.go` - DeepCopy implementations
  - `pkg/apis/application/v1alpha1/openapi_generated.go` - OpenAPI schema
- **Action**: Run code generators:
  ```bash
  make codegen
  ```
- **Purpose**: Generates protobuf, deepcopy, and OpenAPI code from types

### Step 3: Implement Strategy Logic
- **File**: `controller/sync.go`
- **Key Functions**:
  - `AppStateManager.SyncAppState()` - Entry point for sync
  - Add new function: `syncResourcesUsingCustomStrategy()` mirroring existing patterns
  - Call your strategy function based on `app.Spec.SyncPolicy.SyncStrategy` type
- **Logic Should**:
  - Access desired manifests from `targets`
  - Access live resources from cluster
  - Determine order of resource application (consider sync waves)
  - Apply resources using `resourceOperations` interface
  - Return results for status update

### Step 4: Integrate with Sync Execution Pipeline
- **File**: `controller/sync.go:SyncAppState()`
- **Changes**:
  - Add conditional logic to detect your strategy
  - Call your custom sync implementation
  - Ensure wave handling if applicable
  - Handle pre/post-sync hooks if needed
- **Considerations**:
  - Order of resource application (waves)
  - Health checks between operations
  - Error handling and recovery
  - Rollback behavior

### Step 5: Add Sync Options Support (Optional)
- **File**: `pkg/apis/application/v1alpha1/types.go` - SyncOptions
- **Changes**:
  - If your strategy needs options, define them in SyncOptions
  - Document in sync options documentation
- **Common Options**:
  - `Validate`: Run kubectl validation
  - `Force`: Use --force flag
  - `DisableDeletion`: Skip deletion of resources
  - `PrunePropagationPolicy`: How to prune resources

### Step 6: Update Repo Server Manifest Generation (if needed)
- **File**: `reposerver/repository/repository.go`
- **Changes**: Only if your strategy requires pre-processing manifests
  - E.g., adding strategy-specific metadata
  - Example: Wave annotation generation based on resource order

### Step 7: Add Hook Support (if applicable)
- **File**: `controller/hook.go`
- **Changes**: Only if your strategy uses hooks differently
  - Pre-sync hooks: Execute before sync phase
  - Post-sync hooks: Execute after sync phase
  - Post-delete hooks: Execute during application deletion

### Step 8: Write Tests
- **Files**:
  - `controller/sync_test.go` - Unit tests for sync logic
  - `test/e2e/sync_options_test.go` or create new E2E test file
- **Test Coverage**:
  - Unit tests: Sync strategy selection, resource ordering
  - E2E tests: Full sync workflow with your strategy
  - Edge cases: Partial failures, retries, rollback

### Step 9: Update API Clients
- **Files**:
  - `server/application/application.proto` - gRPC definitions
  - `pkg/apiclient/application/` - Generated Go client code
- **Changes**:
  - Add strategy type to SyncOperation proto
  - Regenerate client code:
    ```bash
    make codegen
    ```

### Step 10: Update Web UI (Optional)
- **File**: `ui/src/app/shared/models.ts` - TypeScript type definitions
- **Changes**:
  - Add SyncStrategy type for UI
  - Update sync panel component to accept new strategy
  - UI changes in `ui/src/app/applications/components/application-sync-panel/`

### Step 11: Update Documentation
- **Files**:
  - `docs/user-guide/sync-options.md` - Sync options documentation
  - Create new doc for your strategy if significant
- **Contents**: Usage examples, behavior description, limitations

### Step 12: Update CHANGELOG
- **File**: `CHANGELOG.md`
- **Entry**: Document the new feature with version and brief description

### Example Flow for Implementation
The addition would follow this execution path:
1. User creates/modifies Application with new SyncStrategy
2. ApplicationController informer detects change → queues refresh
3. `ApplicationController.processAppRefreshQueue()` → `refreshAppStatus()`
4. `SyncAppState()` evaluates strategy type
5. Your custom sync function executes based on strategy
6. Resources synced according to your strategy's logic
7. Status updated in Application.Status
8. UI reflects current sync state

### Key Architectural Principles to Follow
- **Separation of Concerns**: Keep strategy logic in sync.go, not controller
- **Reuse gitops-engine**: Use `github.com/argoproj/gitops-engine/pkg/sync` for core operations
- **Wave Support**: Respect sync-wave annotations even in custom strategies
- **Health Checks**: Implement proper health assessment before proceeding
- **Error Handling**: Graceful degradation and detailed error reporting
- **Testing**: Comprehensive test coverage before merge
- **Backward Compatibility**: Don't break existing sync strategies
