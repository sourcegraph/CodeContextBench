# Argo CD Sync Reconciliation Pipeline

## Q1: Reconciliation Triggering and Git Fetch

### Triggers for Reconciliation

Reconciliation cycles are triggered through three mechanisms:

1. **Periodic Refresh**: The ApplicationController continuously monitors Application resources. Every `statusRefreshTimeout` seconds (default 3 minutes) or `statusHardRefreshTimeout` seconds (default 24 hours), the controller schedules a new comparison cycle.

2. **Resource Change Events**: When an Application resource is created, updated, or deleted, the informer event handler enqueues it into the work queue.

3. **Manual Sync**: Users can trigger manual syncs via the API, which queues the operation.

**File**: `controller/appcontroller.go:2399-2460`
- Event handler registration: `appInformer.AddEventHandler()` with AddFunc, UpdateFunc, DeleteFunc
- Refresh queue: `appRefreshQueue workqueue.TypedRateLimitingInterface[string]` (line 122)
- Comparison levels: `CompareWithLatest`, `CompareWithRecent`, `CompareWithLatestForceResolve` (lines 83-94)

### Controller-to-RepoServer Communication

The ApplicationController requests manifest generation via gRPC. The data structures for this communication are:

**Request**: `apiclient.ManifestRequest`
- **File**: `reposerver/apiclient/repository.pb.go:32-60+`
- Fields:
  - `Repo` (*v1alpha1.Repository) - repository credentials
  - `ApplicationSource` (*v1alpha1.ApplicationSource) - source definition
  - `Revision` (string) - Git target revision
  - `NoCache` (bool) - cache bypass flag
  - `NoRevisionCache` (bool) - revision cache bypass
  - `AppName` (string) - application instance name
  - `Namespace` (string) - target namespace
  - `VerifySignature` (bool) - GPG signature verification flag
  - Additional fields: HelmOptions, KustomizeOptions, TrackingMethod, RefSources, etc.

**Response**: `apiclient.ManifestResponse`
- **File**: `reposerver/apiclient/repository.pb.go:703-715+`
- Fields:
  - `Manifests` ([]string) - YAML manifests as strings
  - `Revision` (string) - resolved commit SHA
  - `SourceType` (string) - detected template tool (Helm, Kustomize, Plain, Plugin, Directory)
  - `VerifyResult` (string) - GPG verification result

### Git Repository Fetch and Caching

The RepoServer manages Git repository access:

**File**: `reposerver/repository/repository.go:518-586` (GenerateManifest method)

1. **Repository Locking**: `repoLock *repositoryLock` (line 91) ensures concurrent access safety
2. **Revision Resolution**:
   - `s.newClientResolveRevision()` resolves symbolic refs (master, HEAD, v1.2.3) to concrete commit SHAs
   - Caching uses `git.WithCache(s.cache, !q.NoRevisionCache && !q.NoCache)`
3. **Git Client Management**: `newGitClient` function (line 96) creates Go-git clients that fetch from remote repositories
4. **Repository Caching**:
   - **File**: `reposerver/cache/cache.go` - manifest caching layer
   - Cache key includes: repo URL, revision, app path, helm values, kustomize patches
   - Invalidation: changes to ApplicationSource, signature verification requirements, or explicit noCache flag

**Key interaction flow**:
```
ApplicationController.reconcile()
  → ctrl.appStateManager.CompareAppState()
    → m.GetRepoObjs() [controller/state.go:129]
      → repoClient.GenerateManifest() [gRPC call]
        → Service.GenerateManifest() [reposerver/repository/repository.go:518]
          → s.runRepoOperation() [with cache check]
            → s.runManifestGen() [async generation]
```

## Q2: Manifest Generation and Rendering

### Tool Detection and Selection

**File**: `reposerver/repository/repository.go:700+`

The RepoServer determines which config management tool to use through a discovery process:

1. **Explicit Configuration**:
   - `source.IsHelm()` checks for `applicationSource.Chart` field
   - `source.IsKustomize()` checks for `applicationSource.Kustomize` field
   - `source.IsPlugin()` checks for `applicationSource.Plugin` field

2. **Automatic Discovery** (if no explicit config):
   - **File**: `util/app/discovery/discovery.go:36` - `Discover()` function
   - Scans application path for: `kustomization.yaml`, `Chart.yaml`, `plugin.yaml`
   - Returns map of `SourceType → enabled` based on discovery

3. **Tool-Specific Flows**:
   - **Helm**: `s.newHelmClientResolveRevision()` - fetches Helm charts, resolves dependencies
   - **Kustomize**: Direct YAML generation using kustomize library
   - **Plain YAML**: Direct file reading
   - **CMP (Config Management Plugin)**: Stream via `generateManifestsCMP()` (line 2039)

### Manifest Generation Sequence

**File**: `reposerver/repository/repository.go:680-693` (runManifestGen)

```
runManifestGen()
  ├─ operationContextSrc() → operationContext{appPath, repoRoot}
  │
  ├─ s.runRepoOperation() [with cache checking]
  │   └─ cacheFn() checks manifest cache (lines 532-536)
  │       └─ s.getManifestCacheEntry() for cache hits
  │
  └─ s.runManifestGenAsync() [async execution]
      ├─ For Helm: render chart with values
      ├─ For Kustomize: execute kustomize build
      ├─ For CMP: send tgz to cmp-server via gRPC stream
      │   └─ File: cmpserver/plugin/plugin.proto:68-71
      │   └─ Stream: ManifestRequestWithFiles repeated bytes
      └─ Send ManifestResponse on responseCh or errCh
```

### Caching Strategy

**Files**:
- `reposerver/cache/cache.go` - Cache interface and implementations
- `reposerver/repository/repository.go:532-536` - Cache lookup logic

Cache key components (line 712):
- Repository URL
- Revision (commit SHA)
- Application path
- Application name
- Namespace
- Source type configuration
- Tracking method

Cache invalidation triggers:
1. Explicit `NoCache=true` parameter
2. Revision cache expiry if `NoRevisionCache=true`
3. Configuration changes (IgnoreDifferences, HelmOptions, etc.)

**Manifest Response Structure**:

```go
// controller/state.go:129-320
targetObjs, manifestInfos, revisionUpdated, err := m.GetRepoObjs(...)
// manifestInfos: []*apiclient.ManifestResponse
// targetObjs: []*unstructured.Unstructured (unmarshalled from Manifests)
```

Lines 269-303 show the manifest request construction and response unmarshalling via `unmarshalManifests()`.

## Q3: Diff Computation Between Desired and Live State

### Live State Fetching

**File**: `controller/state.go:611-620` (GetManagedLiveObjs)

```go
liveObjByKey, err := m.liveStateCache.GetManagedLiveObjs(app, targetObjs)
```

The `liveStateCache` (of type `statecache.LiveStateCache`) queries the Kubernetes cluster:

1. **Cluster Connection**: Established via REST client to destination cluster
2. **Resource Selection**: Fetches resources matching:
   - GVK (GroupVersionKind) of target resources
   - Destination namespace
   - Resource tracking labels (to identify managed resources)
3. **Filtering**: Removes resources not permitted by AppProject RBAC rules (lines 622-640)

**Data Structure**: `map[kubeutil.ResourceKey]*unstructured.Unstructured`
- Key: `{Group, Kind, Namespace, Name}`
- Value: unstructured Kubernetes resource object

### Diff Engine

**File**: `controller/state.go:695` (Core reconciliation)

```go
reconciliation := sync.Reconcile(targetObjs, liveObjByKey, app.Spec.Destination.Namespace, infoProvider)
```

This calls into **gitops-engine** (`github.com/argoproj/gitops-engine/pkg/sync`):

- **Input**: Target manifests and live cluster state
- **Output**: `sync.ReconciliationResult` containing:
  - `reconciliation.Target` - matched target resources
  - `reconciliation.Live` - matched live resources
  - Correlation between target and live for each resource

### Diff Strategies

**File**: `controller/state.go:709-760` (Diff configuration)

**1. Server-Side Diff (default in Argo CD 2.9+)**:

```go
serverSideDiff := m.serverSideDiff ||
    resourceutil.HasAnnotationOption(app, common.AnnotationCompareOptions, "ServerSideDiff=true")

if serverSideDiff {
    applier, cleanup, err := m.getServerSideDiffDryRunApplier(app.Spec.Destination.Server)
    defer cleanup()
    diffConfigBuilder.WithServerSideDryRunner(diff.NewK8sServerSideDryRunner(applier))
}
```

- Executes `kubectl apply --dry-run=server` on cluster
- Computes server-side merge patch
- More accurate for custom resource controllers

**2. Client-Side Apply Diff**:

- Legacy 3-way merge (kubectl merge-patch logic)
- Used when ServerSideDiff=false

**3. Structured Merge Diff**:

```go
if app.Spec.SyncPolicy != nil && app.Spec.SyncPolicy.SyncOptions.HasOption("ServerSideApply=true") {
    diffConfigBuilder.WithStructuredMergeDiff(true)
}
```

- Used with kubectl server-side apply
- Tracks field ownership via managed fields

### Diff Result

**File**: `controller/state.go:762-769`

```go
diffResults, err := argodiff.StateDiffs(reconciliation.Live, reconciliation.Target, diffConfig)
```

Returns `diff.DiffResultList` containing:

```go
type DiffResult struct {
    Modified        bool      // differs between desired and live
    NormalizedLive  []byte    // normalized live state
    PredictedLive   []byte    // predicted result of applying target
}
```

### Sync Status Determination

**File**: `controller/state.go:771-876` (Resource status aggregation)

For each resource pair (target, live):

1. **Diff Check** (line 823):
   ```go
   if !isManagedNs && (diffResult.Modified || targetObj == nil || liveObj == nil) {
       resState.Status = v1alpha1.SyncStatusCodeOutOfSync
   }
   ```

2. **Aggregated Sync Status** (line 832):
   ```go
   syncCode = v1alpha1.SyncStatusCodeOutOfSync  // if any resource differs
   ```

3. **Final SyncStatus** (lines 881-902):
   ```go
   syncStatus := v1alpha1.SyncStatus{
       ComparedTo: v1alpha1.ComparedTo{Destination, Source, IgnoreDifferences},
       Status:     syncCode,
       Revision:   revision,
   }
   ```

## Q4: Sync Operation Execution

### Sync Phases and Orchestration

**File**: `controller/sync.go:97-414` (SyncAppState method)

The sync process executes three phases orchestrated by gitops-engine:

1. **PreSync Phase**: Executes resource hooks marked with `argocd.argoproj.io/compare-result: prune`
2. **Sync Phase**: Applies target resources to cluster
3. **PostSync Phase**: Executes post-deployment hooks

**Phase Execution** (lines 390-414):

```go
syncCtx, cleanup, err := sync.NewSyncContext(
    compareResult.syncStatus.Revision,
    reconciliationResult,  // target vs live mapping
    restConfig,            // cluster access
    rawConfig,
    m.kubectl,
    app.Spec.Destination.Namespace,
    openAPISchema,
    opts...,  // sync options
)

if state.Phase == common.OperationTerminating {
    syncCtx.Terminate()  // abort if termination requested
} else {
    syncCtx.Sync()  // execute PreSync → Sync → PostSync
}

state.Phase, state.Message, resState = syncCtx.GetState()
```

### Apply Strategies: Client-Side vs Server-Side

**File**: `controller/sync.go:367, 381`

```go
sync.WithOperationSettings(syncOp.DryRun, syncOp.Prune, syncOp.SyncStrategy.Force(), ...),
sync.WithServerSideApply(syncOp.SyncOptions.HasOption(common.SyncOptionServerSideApply)),
```

**Client-Side Apply**:
- Executes `kubectl apply` on local workstation
- Uses three-way strategic merge patch (kubectl.kubernetes.io/last-applied-configuration)
- Default strategy

**Server-Side Apply**:
- Executes `kubectl apply --field-manager=argocd-application-controller --server-side`
- Tracks field ownership in Kubernetes server
- Recommended for controllers/operators that modify resources
- Enabled via: `SyncOptions: ["ServerSideApply=true"]`

### Resource Ordering and Sync Waves

**File**: `controller/sync.go:376`

```go
sync.WithSyncWaveHook(delayBetweenSyncWaves),
```

Resources are grouped into sync waves based on annotation:
```
metadata.annotations:
  argocd.argoproj.io/sync-wave: "0"  // executed first
                                "1"  // executed after wave 0 completes
```

Waves enable sequential deployment: databases → services → deployments → smoke tests

### Resource Filtering and Selective Sync

**File**: `controller/sync.go:369-374`

```go
sync.WithResourcesFilter(func(key kube.ResourceKey, target, live *unstructured.Unstructured) bool {
    return (len(syncOp.Resources) == 0 ||
            isPostDeleteHook(target) ||
            argo.ContainsSyncResource(...)) &&
           m.isSelfReferencedObj(...)  // only sync app-owned resources
})
```

Enables partial syncs targeting specific resources:
```yaml
sync:
  resources:
  - kind: Deployment
    name: web-server
    namespace: default
```

### Sync Options

**File**: `controller/sync.go:280-388`

Key options configured as sync operation parameters:

| Option | Effect |
|--------|--------|
| `Prune=true` | Delete extra resources in cluster not in Git |
| `DryRun=true` | Calculate changes without applying |
| `Force=true` | Force resource recreation |
| `ServerSideApply=true` | Use kubectl server-side apply |
| `CreateNamespace=true` | Create missing namespaces (line 386) |
| `PrunePropagationPolicy=foreground/background/orphan` | Delete cascade policy (lines 280-288) |
| `RespectIgnoreDifferences=true` | Apply ignored fields from live to target (line 302) |
| `ApplyOutOfSyncOnly=true` | Only sync drifted resources (line 378) |

### Sync Status Tracking

**File**: `controller/sync.go:415-453`

After sync completion, resource results are mapped from gitops-engine format to Application status:

```go
resState := syncCtx.GetState()  // []common.ResourceSyncResult

for _, res := range resState {
    state.SyncResult.Resources = append(..., &v1alpha1.ResourceResult{
        Group:     res.ResourceKey.Group,
        Kind:      res.ResourceKey.Kind,
        Namespace: res.ResourceKey.Namespace,
        Name:      res.ResourceKey.Name,
        Status:    res.Status,      // Succeeded/Failed/Unknown
        SyncPhase: res.SyncPhase,    // PreSync/Sync/PostSync
        HookType:  res.HookType,     // PreSync/PostSync/SyncFail
        Message:   res.Message,
    })
}
```

### Revision History Persistence

**File**: `controller/sync.go:457-463`

```go
if !syncOp.DryRun && len(syncOp.Resources) == 0 && state.Phase.Successful() {
    err := m.persistRevisionHistory(app, compareResult.syncStatus.Revision, source,
        compareResult.syncStatus.Revisions, compareResult.syncStatus.ComparedTo.Sources, ...)
}
```

Successful syncs record:
- Commit SHA (revision)
- Application source configuration used
- Timestamp of sync
- Tracking info for multi-source applications

## Data Flow Summary

### Complete Synchronization Pipeline

```
1. RECONCILIATION TRIGGER (every ~3min or on Application change)
   ├─ Source: Periodic refresh queue or informer event
   ├─ Input: Application resource from etcd
   └─ Data Structure: v1alpha1.Application

2. FETCH DESIRED STATE FROM GIT
   ├─ Component: ApplicationController → RepoServer (gRPC)
   ├─ Request: apiclient.ManifestRequest
   │   └─ Contains: Repo creds, ApplicationSource, Revision, sync flags
   ├─ Git Fetch: RepoServer.newGitClient() resolves revision → commit SHA
   ├─ Manifest Generation:
   │   ├─ Tool Detection: IsHelm() / IsKustomize() / Discover()
   │   ├─ Helm: Fetch chart, resolve dependencies, render templates
   │   ├─ Kustomize: Execute kustomize build
   │   ├─ CMP: Stream to cmp-server for custom plugin
   │   └─ Result: YAML manifests as strings
   ├─ Response: apiclient.ManifestResponse
   │   └─ Contains: Manifests[], Revision, SourceType
   └─ Output: []*unstructured.Unstructured (targetObjs)

3. FETCH LIVE STATE FROM CLUSTER
   ├─ Component: ApplicationController via liveStateCache
   ├─ Query: Kubernetes API for resources matching targetObjs GVK + labels
   ├─ Filtering: Remove unpermitted resources (project RBAC)
   └─ Output: map[kubeutil.ResourceKey]*unstructured.Unstructured (liveObjByKey)

4. COMPUTE DIFF (DESIRED vs LIVE)
   ├─ Component: gitops-engine sync.Reconcile()
   ├─ Correlation: Match target resources to live by Name/Namespace/GVK
   ├─ Normalization:
   │   ├─ Apply IgnoreDifferences rules
   │   ├─ Apply ResourceOverrides
   │   └─ Resolve conflicts (MutatingWebhooks, defaulting)
   ├─ Diff Strategy:
   │   ├─ Server-Side: `kubectl apply --dry-run=server` on cluster
   │   ├─ Client-Side: 3-way strategic merge patch locally
   │   └─ Structured Merge: Field ownership for SSA
   ├─ Per-Resource Status:
   │   ├─ Synced: No diff (diffResult.Modified == false)
   │   ├─ OutOfSync: Differences exist or resource missing
   │   └─ Unknown: Load/comparison errors
   └─ Output: v1alpha1.SyncStatus{Status, Revision, Resources[]}

5. PERSIST COMPARISON RESULT
   ├─ Update Application.Status:
   │   ├─ Status.Sync = syncStatus (Synced/OutOfSync/Unknown)
   │   ├─ Status.Revision = git commit SHA
   │   ├─ Status.Resources[] = per-resource status
   │   ├─ Status.ReconciledAt = timestamp
   │   └─ Status.Conditions = [ComparisonError, SyncError, ...]
   └─ Persist to etcd

6. AUTO-SYNC DECISION
   ├─ Check: SyncPolicy.Automated enabled?
   ├─ Check: SyncWindow allows sync?
   ├─ Check: Conditions allow operation?
   └─ Decision: Queue sync operation or skip

7. SYNC OPERATION EXECUTION
   ├─ Create SyncContext with reconciliationResult
   ├─ Phase 1 - PreSync Hooks: Execute resources with SyncWave < 0 or hook phase
   ├─ Phase 2 - Sync: Apply target resources in wave order using:
   │   ├─ Strategy: client-side apply OR server-side apply
   │   ├─ Pruning: Delete extra resources if Prune=true
   │   ├─ Ordering: Respect SyncWave annotations
   │   └─ Validation: Manifest validation before apply
   ├─ Phase 3 - PostSync Hooks: Execute resources with SyncWave >= max or hook phase
   ├─ Per-Resource Tracking:
   │   ├─ Status: Succeeded/Failed/Unknown
   │   ├─ Message: kubectl output or error
   │   ├─ SyncPhase: PreSync/Sync/PostSync
   │   └─ HookType: PreSync/PostSync/SyncFail
   └─ Output: OperationState{Phase, Message, Resources[]}

8. UPDATE OPERATION STATUS
   ├─ Update Application.Status.OperationState:
   │   ├─ Phase = Succeeded/Failed/Error
   │   ├─ Message = summary message
   │   ├─ SyncResult.Revision = final commit SHA
   │   ├─ SyncResult.Resources[] = per-resource results
   │   └─ SyncResult.ManagedNamespaceMetadata = namespace metadata applied
   ├─ Record revision history (successful syncs only)
   └─ Persist to etcd

9. LOOP (goto 1)
   └─ Next refresh cycle or event trigger
```

### Transformation Points and Data Structures

| Stage | Input | Component | Processing | Output |
|-------|-------|-----------|-----------|--------|
| Trigger | Event/Timer | ApplicationController | Check refresh needed | Application to reconcile |
| Git Fetch | Application.Spec.Source | RepoServer | Fetch repo, resolve revision | ManifestResponse (manifests[]) |
| Unmarshal | manifests[] | appStateManager | YAML → Unstructured | []*unstructured.Unstructured (targetObjs) |
| Live State | targetObjs metadata | liveStateCache | Query cluster API | map[ResourceKey]*Unstructured (liveObjByKey) |
| Reconcile | targetObjs, liveObjByKey | gitops-engine | Match resources | ReconciliationResult (Target[], Live[]) |
| Normalize | Target[], Live[] | argodiff | Apply rules/webhooks | NormalizedTarget[], NormalizedLive[] |
| Diff | NormalizedTarget[], NormalizedLive[] | diff engine | 3-way or server-side | DiffResultList (Modified[], PredictedLive[]) |
| Status | DiffResultList, hierarchy | statusAggregator | Compute per-resource status | ResourceStatus[] (Synced/OutOfSync) |
| Sync | ReconciliationResult, SyncOp | gitops-engine sync | Apply with waves/pruning | ResourceSyncResult[] (per-resource sync status) |

## Evidence

### Core Controller Files

**Application Controller Reconciliation**:
- `controller/appcontroller.go:113-150` - ApplicationController struct definition
- `controller/appcontroller.go:1620-1800` - reconcileApplications() main reconciliation loop
- `controller/appcontroller.go:1728-1730` - CompareAppState invocation

**Application State Comparison**:
- `controller/state.go:70-75` - AppStateManager interface definition
- `controller/state.go:104-123` - appStateManager struct
- `controller/state.go:129-320` - GetRepoObjs() manifest fetching
- `controller/state.go:476-954` - CompareAppState() complete diff computation

**Sync Operation Execution**:
- `controller/sync.go:97-414` - SyncAppState() sync orchestration
- `controller/sync.go:367-383` - Sync options and strategies
- `controller/sync.go:390-416` - SyncContext creation and execution

### RepoServer Manifest Generation

**Manifest Request/Response**:
- `reposerver/apiclient/repository.pb.go:30-60` - ManifestRequest proto
- `reposerver/apiclient/repository.pb.go:703-715` - ManifestResponse proto

**Manifest Generation Service**:
- `reposerver/repository/repository.go:84-100` - Service struct
- `reposerver/repository/repository.go:518-586` - GenerateManifest() method
- `reposerver/repository/repository.go:680-693` - runManifestGen() async execution

### Data Structure Definitions

**Application API Types**:
- `pkg/apis/application/v1alpha1/types.go:463-466` - RefreshType enum
- `pkg/apis/application/v1alpha1/types.go:3021-3037` - IsRefreshRequested() logic

**Sync Status Types**:
- `pkg/apis/application/v1alpha1/types.go` - SyncStatus, ResourceStatus, OperationState structs

**Cache Management**:
- `reposerver/cache/cache.go` - Manifest caching interface
- `util/cache/appstate/` - Application state cache

### Test References

Demonstrates actual usage patterns:
- `controller/appcontroller_test.go` - Controller reconciliation tests
- `controller/state_test.go` - State comparison tests
- `controller/sync_test.go` - Sync operation tests
- `test/e2e/app_management_test.go` - End-to-end sync scenarios
