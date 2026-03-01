# Argo CD Sync Reconciliation Pipeline

## Q1: Reconciliation Triggering and Git Fetch

### Reconciliation Triggers
Reconciliation cycles are triggered by three mechanisms:

1. **Periodic Refresh**: The Application Controller continuously monitors applications via Kubernetes informers and processes periodic refresh requests based on configured intervals (`statusRefreshTimeout`, `statusHardRefreshTimeout`).

2. **Resource Change Events**: When an Application resource is added, updated, or deleted, the informer handler automatically triggers reconciliation:
   - **AddFunc** (controller/appcontroller.go:2401-2408): Newly added applications are added to `appRefreshQueue`
   - **UpdateFunc** (controller/appcontroller.go:2414-2448): Application changes trigger refresh based on changes to spec or automation settings
   - **DeleteFunc** (controller/appcontroller.go:2450-2465): Application deletion is queued for finalization

3. **Manual Sync**: Users can explicitly request synchronization via the API, which creates an `Operation` in the Application status.

### Communication with RepoServer

**Trigger Point**: `controller/appcontroller.go:processAppRefreshQueueItem()` (line 1598)
- The `ApplicationController` detects drift by calling `ctrl.appStateManager.CompareAppState()`
- This internally calls `m.GetRepoObjs()` to request manifest generation

**Request Path**:
```
ApplicationController (controller/appcontroller.go)
  └─> appStateManager.GetRepoObjs() (controller/state.go:129)
       └─> repoClientset.NewRepoServerClient() (controller/state.go:180)
            └─> repoClient.GenerateManifest() (controller/state.go:269)
                 └─> RepoServerService.GenerateManifest() (reposerver/repository/repository.go:518)
```

**Request Data Structure** (`ManifestRequest`):
- **File**: reposerver/repository/repository.proto (lines 9-45)
- **Type**: `apiclient.ManifestRequest`
- **Key Fields**:
  - `repo`: Repository credentials and URL
  - `revision`: Git revision (branch, tag, or commit SHA) to fetch
  - `applicationSource`: Source configuration (path, Helm values, Kustomize options)
  - `appLabelKey`: Label key for Argo CD resource tracking
  - `appName`: Application instance name
  - `namespace`: Target namespace for rendering
  - `noCache`: Force bypass of manifest cache
  - `noRevisionCache`: Force bypass of revision resolution cache
  - `verifySignature`: GPG signature verification flag
  - `enabledSourceTypes`: Map indicating which source types (Helm, Kustomize, CMP, Directory) are enabled
  - `kustomizeOptions`: Kustomize configuration
  - `helmOptions`: Helm configuration
  - `helmRepoCreds`: Helm repository credentials
  - `kubeVersion`: Kubernetes version for template rendering
  - `apiVersions`: Available API versions from destination cluster
  - `trackingMethod`: Resource tracking method (label or annotation)

### Git Fetch and Caching Mechanism

**RepoServer Git Fetch**:
1. **Entry Point**: `reposerver/repository/repository.go:GenerateManifest()` (line 518)
2. **Revision Resolution**: `s.newClientResolveRevision()` (reposerver/repository/repository.go:2419)
   - Creates a git client with configured credentials
   - Resolves ambiguous revisions (e.g., "HEAD", "main") to concrete commit SHAs
   - Uses git client options: `git.WithCache()` for enabling manifest caching based on revision
3. **Repository Download**: `s.runRepoOperation()` (reposerver/repository/repository.go:289)
   - Downloads the entire Git repository to a temporary directory at the specified revision
   - For CMP (Config Management Plugin), creates a tar.gz of the repo for sending to sidecar
   - Caches the downloaded repository based on:
     - Commit SHA
     - Whether caching is enabled (`!q.NoCache` and `!q.NoRevisionCache`)
     - Manifest generation paths annotation (if present)

**Cache Invalidation**:
- Cache is invalidated when:
  - Explicit `noCache=true` flag in request
  - Explicit `noRevisionCache=true` flag (forces revision resolution)
  - Application's manifest-generate-paths annotation changes (indicates only specific paths affect manifests)
  - Repository credentials are updated

**Response Data Structure** (`ManifestResponse`):
- **File**: reposerver/repository/repository.proto (lines 92-103)
- **Type**: `apiclient.ManifestResponse`
- **Key Fields**:
  - `manifests`: Array of JSON-serialized Kubernetes resource manifests
  - `revision`: Resolved commit SHA
  - `sourceType`: Detected source type (Helm, Kustomize, CMP, Directory)
  - `commands`: Array of commands executed to generate manifests (for audit)
  - `verifyResult`: GPG verification output (if requested)

---

## Q2: Manifest Generation and Rendering

### Source Type Detection

**Function**: `GetAppSourceType()` (reposerver/repository/repository.go:1615)
- Analyzes the application source configuration and repository structure
- Detection Logic:
  1. If `source.Helm` is configured → `ApplicationSourceTypeHelm`
  2. If `source.Kustomize` is configured → `ApplicationSourceTypeKustomize`
  3. If `source.Plugin` is configured → `ApplicationSourceTypePlugin`
  4. If directory mode is enabled and path exists → `ApplicationSourceTypeDirectory`
  5. Otherwise → Returns error

### Manifest Rendering Sequence

**Core Function**: `GenerateManifests()` (reposerver/repository/repository.go:1421)

The rendering sequence depends on the detected source type:

#### 1. Helm Sources
- **Function**: `helmTemplate()` (reposerver/repository/repository.go)
- **Process**:
  - Uses `helm template` to render charts
  - Applies parameter overrides from:
    - `.argocd-source.yaml` (global overrides)
    - `.argocd-source-<appName>.yaml` (application-specific overrides)
  - Injects environment variables (ARGOCD_APP_NAME, ARGOCD_APP_REVISION, etc.)
  - Merges Helm values from multiple sources (values.yaml, inline params, external repos)

#### 2. Kustomize Sources
- **Function**: `kustomize.NewKustomizeApp().Build()` (reposerver/repository/repository.go:1450-1454)
- **Process**:
  - Invokes kustomize CLI with configured kustomization.yaml
  - Applies Kubernetes version and API version constraints
  - Renders overlays based on environment

#### 3. Config Management Plugins (CMP)
- **Function**: `runConfigManagementPluginSidecars()` (reposerver/repository/repository.go:1461)
- **Process**:
  - Compresses repository as tar.gz (with exclusions from `.argocd-cmp-generate.ignore`)
  - Streams compressed repo to CMP sidecar container
  - CMP sidecar executes custom generation commands
  - Returns manifests from stdout

#### 4. Directory (Plain YAML)
- **Function**: `findManifests()` (reposerver/repository/repository.go:1471)
- **Process**:
  - Recursively searches directory for .yaml/.yml files
  - Excludes specified patterns (via configuration)
  - Parses and validates YAML structure

### Resource Tracking Injection

After manifest generation (reposerver/repository/repository.go:1502-1514):
- Each manifest is annotated with Argo CD resource tracking information:
  - **Tracking Labels/Annotations**: Identifies which Application manages each resource
  - **Key**: Configured via `appLabelKey` (default: `app.kubernetes.io/instance`)
  - **Value**: `appName` (format: `<namespace>_<appName>`)
  - **Tracking Method**: Label-based or annotation-based (configurable per Application)
  - **Installation ID**: Unique identifier for multi-tenant Argo CD instances

### Manifest Response Generation

**Final Output Structure** (reposerver/repository/repository.go:1517-1522):
```go
&apiclient.ManifestResponse{
  Manifests:  []string{...},  // JSON-serialized resources
  SourceType: string(appSourceType),
  Commands:   commands,       // For audit trail
}
```

### Caching Mechanisms

**Manifest Cache**:
- **Location**: In-memory cache in RepoServer (`s.cache`)
- **Cache Key**: Hash of (revision, appPath, source configuration)
- **TTL**: Configurable, typically tied to application refresh interval
- **Invalidation Triggers** (reposerver/repository/repository.go:useDiffCache logic):
  1. Explicit `noCache=true` request
  2. Application spec changes that affect rendering (source config, parameters)
  3. Git revision changes
  4. Manifest generation paths annotation modifications
  5. Timeout of cached entry

**Controller-Side Cache**:
- **Location**: `controller/cache` package (`appstate.Cache`)
- **Purpose**: Caches comparison results to avoid redundant diffing
- **Cache Key**: Application instance name + manifest revisions
- **Invalidation**: When manifests or live state changes

---

## Q3: Diff Computation Between Desired and Live State

### Live State Fetching

**Entry Point**: `appStateManager.CompareAppState()` (controller/state.go:476)

**Live State Source** (controller/state.go:611):
```
liveObjByKey := m.liveStateCache.GetManagedLiveObjs(app, targetObjs)
```

**Components**:
1. **Live State Cache** (`controller/cache/LiveStateCache`)
   - Continuously watches Kubernetes cluster for resource changes
   - Maintains an in-memory cache of live resource state
   - Uses Kubernetes informers for real-time updates
   - Filters resources to only those managed by the Application (via resource tracking labels/annotations)

2. **Cluster Cache** (`clustercache.ClusterCache` from gitops-engine)
   - Watches all resources in configured cluster namespaces
   - Maintains OpenAPI schema for the cluster
   - Provides resource info for diff computation

### Diff Normalization

**Entry Point**: `DeduplicateTargetObjects()` (controller/state.go:584)

Before diffing, manifests are normalized to ensure consistent comparison:
1. **Deduplication**: Removes duplicate resources with same GroupVersionKind and name
2. **Exclusion Filtering**: Removes resources excluded in Argo CD settings
3. **Managed Namespace Handling**: Creates synthetic namespace resources for managed metadata

### Reconciliation Result Computation

**Entry Point**: `sync.Reconcile()` (controller/state.go:695)
- **Source**: gitops-engine package
- **Purpose**: Matches desired (target) and live resources
- **Output**: `sync.ReconciliationResult`
  ```go
  type ReconciliationResult struct {
    Target []*unstructured.Unstructured  // Desired state
    Live   []*unstructured.Unstructured  // Current state
    // Parallel arrays where Live[i] and Target[i] are compared
  }
  ```
- **Matching Logic**: By GroupVersionKind, namespace, and name

### Diff Strategy Selection

**Configuration** (controller/state.go:709-756):

1. **Server-Side Diff (SSD)**
   - **Trigger**:
     - Application annotation: `argocd.argoproj.io/compare-options=ServerSideDiff=true`
     - Controller-level flag: `serverSideDiff`
   - **Implementation**: `diff.NewK8sServerSideDryRunner()`
   - **Process**: Uses `kubectl apply --dry-run=server` to simulate application
   - **Benefit**: Accounts for mutating webhooks and server-side validation

2. **Structured Merge Diff**
   - **Trigger**: Sync strategy includes `ServerSideApply=true`
   - **Purpose**: Respects Kubernetes field ownership and merge strategies
   - **Configuration**: `diffConfigBuilder.WithStructuredMergeDiff(true)`

3. **3-Way Diff (Default)**
   - **Method**: Client-side patch computation
   - **Source**: gitops-engine's `diff` package
   - **Compares**: Last-applied-configuration, desired, live

### Diff Configuration

**Builder Pattern** (controller/state.go:720-760):
```
DiffConfig := argodiff.NewDiffConfigBuilder()
  .WithDiffSettings(app.Spec.IgnoreDifferences, resourceOverrides, ...)
  .WithTracking(appLabelKey, trackingMethod)
  .WithCache(cache, appInstanceName)  // Optional
  .WithServerSideDiff(serverSideDiff)
  .WithStructuredMergeDiff(useStructuredMerge)
  .WithGVKParser(gvkParser)
  .WithManager(ArgoCDSSAManager)
  .Build()
```

**IgnoreDifferences Configuration**:
- **Source**: Application spec (`app.Spec.IgnoreDifferences`)
- **Application**: Normalizes fields before comparison (ignores specified paths/fields)
- **Normalizers**: Custom normalizers from settings and resource overrides

### Actual Diff Computation

**Entry Point**: `argodiff.StateDiffs()` (controller/state.go:762)
- **Source**: `util/argo/diff` package
- **Input**:
  - `reconciliation.Live[]`: Current cluster state
  - `reconciliation.Target[]`: Desired state from Git
  - `DiffConfig`: Normalization and comparison rules
- **Output**: `diff.DiffResultList`
  ```go
  type DiffResultList struct {
    Diffs []DiffResult
  }

  type DiffResult struct {
    Modified      bool
    NormalizedLive []byte  // Normalized current state
    PredictedLive []byte   // Predicted state after apply
    JsonPatch     []byte   // JSON patch representation
  }
  ```

### Diff Result Interpretation

**Out-of-Sync Detection** (controller/state.go:823):
Resource is marked OutOfSync if:
- `diffResult.Modified == true` (differs from desired), OR
- `targetObj == nil && liveObj != nil` (resource should be deleted), OR
- `targetObj != nil && liveObj == nil` (resource should be created)

**Status Computation** (controller/state.go:771-830):
```go
// For each target resource:
if resState.Hook || ignore.Ignore(obj) || !isSelfReferencedObj {
  // Skip tracking
} else if !isManagedNs && (diffResult.Modified || targetObj==nil || liveObj==nil) {
  // Set status = OutOfSync
} else {
  // Set status = Synced
}
```

### Sync Status Result

**Data Structure**: `v1alpha1.SyncStatus`
```go
type SyncStatus struct {
  Status     SyncStatusCode  // Synced, OutOfSync, Unknown
  ComparedTo ComparedTo      // Sources compared
  Revision   string          // Resolved revision
  Revisions  []string        // For multi-source apps
}
```

---

## Q4: Sync Operation Execution

### Sync Operation Phases

**Three-Phase Architecture** (gitops-engine):

1. **PreSync Phase** (`PreSync` hook type)
   - Executes before main sync
   - Typically for cleanup, migrations, or validation hooks
   - Ordered by sync wave

2. **Sync Phase** (Main resource application)
   - Applies desired resources to cluster
   - Creates/updates/deletes resources based on diff
   - Respects sync waves and dependencies

3. **PostSync Phase** (`PostSync` hook type)
   - Executes after main sync
   - Typically for notifications, cleanup, or health checks
   - Ordered by sync wave

### Sync Wave Ordering

**Implementation**: `syncwaves.Wave()` (controller/state.go:799)
- **Default Wave**: 0
- **Configuration**: `metadata.argocd.argoproj.io/compare-result: Wave` annotation or field
- **Execution**: Resources with lower wave numbers execute first
- **Wave Delay**: Configurable via `ARGOCD_SYNC_WAVE_DELAY` environment variable (default behavior in gitops-engine)

### Apply Strategies

**Client-Side Apply** (Default):
- **Method**: `kubectl apply -f <manifest>`
- **JSON Merge**: Merges desired state with live state
- **Tracking**: Uses `kubectl.kubernetes.io/last-applied-configuration` annotation
- **Triggers**: When no server-side apply option is specified

**Server-Side Apply**:
- **Trigger**: `app.Spec.SyncPolicy.SyncOptions` contains `ServerSideApply=true`
- **Implementation** (controller/sync.go:381):
  ```go
  sync.WithServerSideApply(syncOp.SyncOptions.HasOption(common.SyncOptionServerSideApply))
  ```
- **Process**: Uses `kubectl apply --server-side --force-conflicts`
- **Benefit**: Respects field ownership, handles concurrent modifications
- **Manager Identity**: Set via `sync.WithServerSideApplyManager(ArgoCDSSAManager)`

### Resource Application Order

**Sorting Algorithm** (controller/sort_delete.go):
1. **Dependency Resolution**: Topological sort based on resource dependencies
   - Namespaces before other resources
   - Webhooks before API resources
   - CRDs before custom resources
2. **Sync Wave**: Lower waves execute first
3. **Sync Weight**: Within same wave, ordered by specified weight

**Deletion Order** (controller/sort_delete.go):
- Reverse dependency order
- Respects `PrunePropagationPolicy` setting:
  - `foreground`: Wait for dependents (default)
  - `background`: Delete immediately
  - `orphan`: Keep dependents

### Sync Operation Execution

**Entry Point**: `appStateManager.SyncAppState()` (controller/sync.go:97)

**Step 1: Operation Initialization** (controller/sync.go:110-168):
- Validate operation parameters
- Resolve revision to concrete commit SHA
- Setup initial operation state

**Step 2: Pre-Sync State** (controller/sync.go:195):
- Call `CompareAppState()` again to get current diff
- Validates no comparison errors prevent sync

**Step 3: Sync Context Creation** (controller/sync.go:390-404):
```go
syncCtx, cleanup, err := sync.NewSyncContext(
  compareResult.syncStatus.Revision,
  reconciliationResult,  // Target and live resources
  restConfig,            // REST client config for cluster
  rawConfig,             // Raw config for impersonation
  m.kubectl,             // Kubectl implementation
  app.Spec.Destination.Namespace,
  openAPISchema,         // For validation
  opts...                // Sync options
)
```

**Step 4: Configure Sync Options** (controller/sync.go:346-388):
```go
opts := []sync.SyncOpt{
  sync.WithOperationSettings(dryRun, prune, force, selective),
  sync.WithResourcesFilter(filterFunc),      // Which resources to sync
  sync.WithManifestValidation(validate),
  sync.WithSyncWaveHook(delayBetweenSyncWaves),
  sync.WithPruneLast(pruneLast),
  sync.WithPrunePropagationPolicy(policy),
  sync.WithServerSideApply(useServerSideApply),
  sync.WithReplace(useReplace),
  // ... more options
}
```

**Step 5: Execute Sync** (controller/sync.go:410-414):
```go
if state.Phase == common.OperationTerminating {
  syncCtx.Terminate()  // Cancel in-progress sync
} else {
  syncCtx.Sync()       // Execute sync operation
}
```

**Step 6: Collect Results** (controller/sync.go:415-453):
```go
state.Phase, state.Message, resState = syncCtx.GetState()
// Convert to v1alpha1.ResourceResult
for _, res := range resState {
  state.SyncResult.Resources = append(
    state.SyncResult.Resources,
    &v1alpha1.ResourceResult{...}
  )
}
```

### Sync Status Tracking

**Detailed Tracking** (controller/sync.go:266-278):
Each synchronized resource has:
- `ResourceKey`: Group, Kind, Namespace, Name
- `SyncPhase`: PreSync, Sync, PostSync
- `HookPhase`: Pre, Sync, Post
- `Status`: Synced, Failed, Unknown
- `Message`: Human-readable status
- `Version`: API version at time of operation

**Operation State Propagation** (controller/sync.go:416-453):
```go
state.Phase        // Succeeded, Failed, Error, Terminating
state.Message      // Human-readable message
state.SyncResult   // Detailed sync result with all resource statuses
state.FinishedAt   // Completion timestamp
```

**Application Status Update** (controller/appcontroller.go:1777-1787):
```go
app.Status.Sync = *compareResult.syncStatus      // Sync status
app.Status.Health = *compareResult.healthStatus  // Health status
app.Status.Resources = compareResult.resources   // Resource details
app.Status.ReconciledAt = &now                   // Last reconciliation time
```

### Sync Completion and Refresh Trigger

**Operation Completion** (controller/appcontroller.go:1488-1493):
After successful sync:
1. Persist sync revision history (for rollback capability)
2. Force refresh with `CompareWithLatestForceResolve`
3. This re-triggers reconciliation to verify cluster matches desired state

**Failure Handling** (controller/appcontroller.go:1470-1484):
- Automatic retry with exponential backoff
- Respects retry policy (`operation.Retry.Limit`)
- Updates operation state with retry count and next retry time

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION CHANGE EVENT                        │
│  (Add/Update/Delete via Kubernetes API or Manual Sync Request)       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  1. RECONCILIATION TRIGGERING           │
        │  ApplicationController.Run()             │
        │  -> appInformer EventHandler             │
        │  -> appRefreshQueue.Add(appKey)          │
        │  -> processAppRefreshQueueItem()         │
        └─────────────────────┬───────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  2. GIT FETCH & MANIFEST GENERATION     │
        │  appStateManager.GetRepoObjs()           │
        │  -> repoClient.GenerateManifest()        │
        │  -> RepoServer.GenerateManifest()        │
        │     a) Resolve revision -> commit SHA    │
        │     b) Download repo to temp dir         │
        │     c) Detect source type                │
        │     d) Render manifests (Helm/Kustomize)│
        │     e) Inject resource tracking          │
        │  <- ManifestResponse[]                   │
        └─────────────────────┬───────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  3. DIFF COMPUTATION                    │
        │  appStateManager.CompareAppState()       │
        │  -> Fetch live state from cluster        │
        │  -> Reconcile(target, live) mapping      │
        │  -> StateDiffs(target, live, config)     │
        │  <- comparisonResult                     │
        │     - syncStatus (Synced/OutOfSync)      │
        │     - resources[] with ResourceStatus    │
        │     - diffResultList with patches        │
        └─────────────────────┬───────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  4a. STATUS UPDATE (NO SYNC)             │
        │  app.Status.Sync = syncStatus            │
        │  app.Status.Health = healthStatus        │
        │  app.Status.Resources = resources        │
        │  persistAppStatus(app)                   │
        └─────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │ (If Operation      │ (If OutOfSync &
                    │  Requested)        │  AutoSync Enabled)
                    │                    │
                    ▼                    ▼
        ┌──────────────────┐ ┌──────────────────┐
        │ 4b. MANUAL SYNC  │ │ 4c. AUTO SYNC    │
        │ Operation set    │ │ Trigger sync op  │
        │ -> appOperation  │ │ -> appOperation  │
        │    Queue.Add()   │ │    Queue.Add()   │
        └────────┬─────────┘ └────────┬─────────┘
                 │                    │
                 └────────┬───────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │  5. SYNC EXECUTION                      │
        │  processAppOperationQueueItem()          │
        │  -> processRequestedAppOperation()       │
        │  -> appStateManager.SyncAppState()       │
        │     a) Initialize OperationState         │
        │     b) Validate destination & perms      │
        │     c) CompareAppState() (get current)   │
        │     d) Create SyncContext                │
        │     e) sortResources() for apply order   │
        │     f) Execute PreSync hooks             │
        │     g) Apply resources (by sync wave)    │
        │        - Client-side apply or            │
        │        - Server-side apply               │
        │     h) Execute PostSync hooks            │
        │     i) Collect ResourceSyncResult[]      │
        │  <- state.Phase, state.SyncResult        │
        └─────────────────────┬───────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  6. SYNC COMPLETION                     │
        │  setOperationState(app, state)           │
        │  -> Update app.Status.OperationState     │
        │  -> Persist sync to revision history     │
        │  -> requestAppRefresh(CompareWithLatest) │
        │     (Re-trigger comparison to verify)    │
        └─────────────────────────────────────────┘
```

### Key Data Structures at Each Transformation Point

| Transformation | Input Type | Output Type | Location |
|---|---|---|---|
| Git Fetch | ManifestRequest | Git repo at commit SHA | RepoServer cache |
| Manifest Rendering | Source config + repo | ManifestResponse (manifests[]) | RepoServer memory |
| Manifest Parse | YAML strings | []*unstructured.Unstructured | controller/state.go:356 |
| Live State Query | Application object | map[ResourceKey]Object | controller/cache/ |
| Reconciliation | target[], live[] | ReconciliationResult | gitops-engine/sync |
| Diff Computation | ReconciliationResult | DiffResultList | argodiff.StateDiffs |
| Sync Status | DiffResultList | SyncStatus, ResourceStatus[] | controller/state.go:771-830 |
| Sync Execution | ReconciliationResult + config | ResourceSyncResult[] | sync.SyncContext |
| Status Persistence | OperationState | Application.Status patch | controller/appcontroller.go |

---

## Evidence

### Key Files and References

#### ApplicationController
- **controller/appcontroller.go** (96KB)
  - `Run()` line 859: Main controller loop startup
  - `processAppRefreshQueueItem()` line 1598: Reconciliation entry point
  - `processAppOperationQueueItem()` line 972: Sync operation processing
  - `processRequestedAppOperation()` line 1365: Operation execution coordinator
  - Event handlers and informer setup line 2399-2471

#### State Management & Comparison
- **controller/state.go** (1159 lines)
  - `CompareAppState()` line 476: Main comparison orchestrator
  - `GetRepoObjs()` line 129: Manifest generation request
  - `comparisonResult struct` line 78: Comparison result container
  - Diff computation line 762: `argodiff.StateDiffs()`

#### Sync Operations
- **controller/sync.go** (540 lines)
  - `SyncAppState()` line 97: Sync operation executor
  - Sync context setup line 390
  - Resource sorting line 346-388
  - Result collection line 415-453

#### RepoServer
- **reposerver/repository/repository.go** (2800+ lines)
  - `GenerateManifest()` line 518: Manifest generation entry point
  - `GenerateManifests()` line 1421: Manifest rendering logic
  - `GetAppSourceType()` line 1615: Source type detection
  - `newClientResolveRevision()` line 2419: Git revision resolution
  - `runRepoOperation()` line 289: Repository operation wrapper

#### API Contracts
- **reposerver/repository/repository.proto** (200+ lines)
  - `ManifestRequest` message lines 10-45
  - `ManifestResponse` message lines 92-103

#### Data Types
- **pkg/apis/application/v1alpha1/types.go** (1700+ lines)
  - `Application` struct line 60
  - `ApplicationStatus` struct line 1137
  - `SyncStatus` struct (referenced via import)
  - `OperationState` struct line 1369
  - `SyncOperationResult` struct line 1584
  - `ResourceStatus` struct (referenced via import)

#### External Dependencies
- **gitops-engine** (imported package)
  - `sync.Reconcile()`: Resource reconciliation mapping
  - `diff.DiffResultList`: Diff results
  - `sync.SyncContext`: Sync orchestration

#### Resource Tracking
- **util/argo/**: Resource tracking and labeling logic
- **controller/cache/**: Live state caching mechanism
- **util/argo/diff/**: Diff normalization and configuration

#### Caching
- **controller/cache/**: Live state cache implementation
- **util/cache/appstate/**: Application state cache
- **reposerver/cache/**: Repository cache

This data flow represents the core sync reconciliation pipeline of Argo CD without special sync options, hooks, or error-handling paths.
