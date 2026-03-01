# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

### CLI Command to Backend Delegation

When a user runs `terraform plan`, the execution flow is as follows:

**PlanCommand.Run()** (`internal/command/plan.go:22-118`)
- Parses and validates command-line arguments via `arguments.ParsePlan()`
- Prepares the backend by calling `c.PrepareBackend()` which loads backend configuration
- Builds the operation request via `c.OperationRequest()` which constructs a `*backendrun.Operation`
- Delegates actual planning to the backend via `c.RunOperation(be, opReq)` (line 103)

**Backend Operation Request** (`internal/command/plan.go:145-190`)
The `OperationRequest()` method creates `*backendrun.Operation` with key fields:
- `Type`: set to `backendrun.OperationTypePlan`
- `PlanMode`: controls planning behavior (Normal, Destroy, RefreshOnly modes)
- `PlanRefresh`: boolean for `PlanOpts.SkipRefresh`
- `Targets`: array of targetable resources
- `ForceReplace`: array of resource instances to force replace
- `DeferralAllowed`: experimental deferred actions support

**Local Backend Plan Execution** (`internal/backend/local/backend_plan.go:23-118`)
The local backend's `opPlan()` method:
1. Validates operation preconditions (lines 33-73)
2. Creates evaluation context via `b.localRun(op)` which returns `*LocalRun` containing:
   - `Core`: `*terraform.Context` instance
   - `Config`: parsed configuration
   - `InputState`: current state from storage
   - `PlanOpts`: constructed planning options
3. Invokes planning via `lr.Core.Plan(lr.Config, lr.InputState, lr.PlanOpts)` (line 108)
4. Handles plan serialization and output

### Context.Plan() Method

**Entry Point** (`internal/terraform/context_plan.go:155-158`)
```go
func (c *Context) Plan(config *configs.Config, prevRunState *states.State, opts *PlanOpts) (*plans.Plan, tfdiags.Diagnostics)
```
This is a simple wrapper that calls `Context.PlanAndEval()`.

**Core Planning Logic** (`internal/terraform/context_plan.go:169-372`)
`PlanAndEval()` is the actual implementation:
1. Validates config and state dependencies (lines 188-198)
2. Routes to mode-specific planner based on `opts.Mode`:
   - `plans.NormalMode`: calls `c.plan()` (line 274)
   - `plans.DestroyMode`: calls `c.destroyPlan()` (line 276)
   - `plans.RefreshOnlyMode`: calls `c.refreshOnlyPlan()` (line 278)
3. Constructs final plan object with metadata
4. Performs post-plan validation and apply graph checks

### PlanOpts Key Fields

**Type** (`internal/terraform/context_plan.go:32-138`)
```go
type PlanOpts struct {
    Mode                      plans.Mode                                    // Normal, Destroy, RefreshOnly
    SkipRefresh               bool                                          // Skip resource refresh
    Targets                   []addrs.Targetable                            // Resource targeting
    ForceReplace              []addrs.AbsResourceInstance                   // Force replacement
    SetVariables              InputValues                                   // Input variable values
    DeferralAllowed           bool                                          // Allow deferred actions
    ExternalProviderConfigs   map[addrs.RootProviderConfig]providers.Interface  // Pre-configured providers
    GenerateConfigPath        string                                        // Config generation output path
    Overrides                 *mocking.Overrides                            // Testing framework overrides
    // ... other fields
}
```

---

## Q2: Graph Construction Pipeline

### PlanGraphBuilder Overview

**Type** (`internal/terraform/graph_builder_plan.go:18-109`)
`PlanGraphBuilder` constructs the dependency graph for planning. Key characteristics:
- Makes decisions based on configuration (desired state)
- Ignores certain lifecycle concerns like `create_before_destroy` (only relevant post-planning)
- Supports multiple operation types: plan, destroy plan, validate, import

**Build Method** (`internal/terraform/graph_builder_plan.go:112-118`)
```go
func (b *PlanGraphBuilder) Build(path addrs.ModuleInstance) (*Graph, tfdiags.Diagnostics) {
    return (&BasicGraphBuilder{
        Steps: b.Steps(),
        Name:  "PlanGraphBuilder",
    }).Build(path)
}
```
The `Steps()` method returns the sequence of `GraphTransformer` stages.

### Graph Construction Pipeline: Steps()

**Complete Transformer Sequence** (`internal/terraform/graph_builder_plan.go:121-277`)

The `Steps()` method returns an ordered list of `GraphTransformer` instances:

1. **ConfigTransformer** (line 137-146)
   - Creates nodes for all resources from configuration
   - Handles import targets and config generation
   - Processes both managed and data sources

2. **Variable Transformers** (lines 149-162)
   - `RootVariableTransformer`: Evaluates root module input variables
   - `ModuleVariableTransformer`: Evaluates module input variables
   - `variableValidationTransformer`: Validates variable values

3. **LocalTransformer** (line 163)
   - Adds nodes for local values

4. **OutputTransformer** (lines 164-176)
   - Adds output value nodes
   - Respects `RefreshOnly` and `Destroying` flags

5. **checkTransformer** (lines 180-183)
   - Adds nodes and edges for check block assertions

6. **Orphan & Deposed Transformers** (lines 186-202)
   - `OrphanResourceInstanceTransformer`: Adds nodes for orphaned resources (not in config)
   - `StateTransformer`: Adds nodes for deposed instance objects

7. **AttachStateTransformer** (line 205)
   - Attaches prior state to resource nodes
   - Maps state objects to graph nodes by instance address

8. **AttachResourceConfigTransformer** (line 215)
   - Attaches configuration blocks to resource nodes
   - Enables nodes to access their config during execution

9. **Provider Transformers** (line 218)
   - `transformProviders()`: Creates provider configuration nodes
   - Links providers to resources that use them

10. **RemovedModuleTransformer** (line 221)
    - Removes module nodes that no longer exist in config

11. **AttachSchemaTransformer** (line 225)
    - Retrieves and attaches provider schemas to nodes
    - Required for configuration analysis

12. **ModuleExpansionTransformer** (line 230)
    - Creates expansion nodes for module calls
    - Must come after nodes are created

13. **ExternalReferenceTransformer** (lines 233-235)
    - Plugs in external references that shouldn't be pruned

14. **ReferenceTransformer** (line 237)
    - Analyzes node references and adds dependency edges
    - Connects nodes based on variable/resource references

15. **AttachDependenciesTransformer** (line 239)
    - Attaches explicit dependencies from configuration

16. **attachDataResourceDependsOnTransformer** (line 243)
    - Records dependencies from `depends_on` in data resources

17. **DestroyEdgeTransformer** (lines 247-249)
    - Creates destroy edges for plan operations
    - Used by TargetsTransformer to determine graph scope

18. **pruneUnusedNodesTransformer** (lines 251-253)
    - Removes unreachable nodes from graph

19. **TargetsTransformer** (line 256)
    - Implements resource targeting (`-target=...`)
    - Filters graph to target resources and dependencies

20. **ForcedCBDTransformer** (line 260)
    - Forces `create_before_destroy` when needed for dependency cycles

21. **ephemeralResourceCloseTransformer** (line 263)
    - Closes ephemeral resource instances

22. **CloseProviderTransformer** (line 266)
    - Closes provider plugin connections

23. **CloseRootModuleTransformer** (line 269)
    - Closes root module scope

24. **TransitiveReductionTransformer** (line 273)
    - Removes redundant edges for graph clarity

### ConfigTransformer: Resource Addition

**Type and Purpose** (`internal/terraform/transform_config.go:17-52`)
- Adds all resources from configuration to graph
- Works recursively through module tree
- Filters resources by mode (managed, data, ephemeral)
- Handles import target matching

**Transform Process** (`internal/terraform/transform_config.go:55-88`)
- Recursively processes module tree starting from root
- Calls `transformSingle()` for each module
- Collects managed, data, and ephemeral resources
- Skips resources during destroy operations (except ephemeral)

### ReferenceTransformer: Dependency Analysis

**Type and Purpose** (`internal/terraform/transform_reference.go:108-150`)
- Connects nodes that reference each other
- Builds proper execution ordering
- Analyzes both implicit references and explicit `depends_on`

**Reference Resolution** (`internal/terraform/transform_reference.go:112-148`)
```go
func (t *ReferenceTransformer) Transform(g *Graph) error {
    vs := g.Vertices()
    m := NewReferenceMap(vs)  // Build efficient reference lookup

    for _, v := range vs {
        // Skip destroy nodes to avoid cycles
        if _, ok := v.(GraphNodeDestroyer); ok {
            continue
        }

        parents := m.References(v)  // Find all referenced nodes
        for _, parent := range parents {
            if !graphNodesAreResourceInstancesInDifferentInstancesOfSameModule(v, parent) {
                g.Connect(dag.BasicEdge(v, parent))  // Add dependency edge
            }
        }
    }
}
```

**How References Are Analyzed**
- Nodes implementing `GraphNodeReferencer` report references via `References()` method
- Returns `[]*addrs.Reference` with addresses and source locations
- ReferenceMap resolves references to actual referenceable nodes
- Nodes implementing `GraphNodeReferenceable` provide `ReferenceableAddrs()`
- Edges are added from referencing node to referenced (parent) node

### AttachStateTransformer: State Attachment

**Type and Purpose** (`internal/terraform/transform_attach_state.go:29-71`)
- Attaches prior state from stored state to resource nodes
- Maps state objects to graph nodes by instance address
- Required for refresh and change detection

**State Attachment Process**
```go
func (t *AttachStateTransformer) Transform(g *Graph) error {
    for _, v := range g.Vertices() {
        if an, ok := v.(GraphNodeAttachResourceState); ok {
            addr := an.ResourceInstanceAddr()
            rs := t.State.Resource(addr.ContainingResource())
            if rs != nil {
                an.AttachResourceState(rs.DeepCopy())
            }
        }
    }
}
```

---

## Q3: Provider Resolution and Configuration

### EvalContext Interface

**Type and Methods** (`internal/terraform/eval_context.go:33-150`)

`EvalContext` is the interface given to graph nodes during execution. Key provider-related methods:

```go
type EvalContext interface {
    // InitProvider initializes and returns a provider plugin instance
    InitProvider(addr addrs.AbsProviderConfig, config *configs.Provider)
        (providers.Interface, error)

    // Provider retrieves an already-initialized provider
    Provider(addrs.AbsProviderConfig) providers.Interface

    // ProviderSchema retrieves the schema for a provider
    ProviderSchema(addrs.AbsProviderConfig)
        (providers.ProviderSchema, error)

    // ConfigureProvider sends configuration to provider
    ConfigureProvider(addrs.AbsProviderConfig, cty.Value) tfdiags.Diagnostics

    // CloseProvider closes provider connections
    CloseProvider(addrs.AbsProviderConfig) error

    // ... other methods
}
```

### BuiltinEvalContext: Concrete Implementation

**Type** (`internal/terraform/eval_context_builtin.go:36-94`)

`BuiltinEvalContext` is the primary implementation used during graph walks:

Key fields:
- `ProviderCache`: map of initialized provider instances
- `ProviderLock`: mutex for thread-safe provider access
- `ExternalProviderConfigs`: pre-configured providers from caller
- `Plugins`: library of available providers and provisioners

### InitProvider: Provider Instantiation

**Implementation** (`internal/terraform/eval_context_builtin.go:138-186`)

```go
func (ctx *BuiltinEvalContext) InitProvider(
    addr addrs.AbsProviderConfig,
    config *configs.Provider,
) (providers.Interface, error) {
    // Check for duplicate initialization
    if p := ctx.Provider(addr); p != nil {
        return nil, fmt.Errorf("%s is already initialized", addr)
    }

    // Handle external providers (pre-configured by caller)
    if addr.Module.IsRoot() {
        if external, isExternal := ctx.ExternalProviderConfigs[rootAddr]; isExternal {
            wrapped := externalProviderWrapper{external}
            ctx.ProviderCache[key] = wrapped
            return wrapped, nil
        }
    }

    // Instantiate provider plugin
    p, err := ctx.Plugins.NewProviderInstance(addr.Provider)
    if err != nil {
        return nil, err
    }

    // Apply mock override if specified
    if config != nil && config.Mock {
        p = &providers.Mock{Provider: p, Data: config.MockData}
    }

    ctx.ProviderCache[key] = p
    return p, nil
}
```

**Provider Lifecycle**
1. Check if provider already initialized (error if so)
2. Check for external pre-configured providers
3. Load provider plugin via plugin system
4. Apply test mocking if configured
5. Cache in `ProviderCache` for later retrieval

### ConfigureProvider: Provider Configuration

**Implementation** (`internal/terraform/eval_context_builtin.go:213-237`)

```go
func (ctx *BuiltinEvalContext) ConfigureProvider(
    addr addrs.AbsProviderConfig,
    cfg cty.Value,
) tfdiags.Diagnostics {
    p := ctx.Provider(addr)
    if p == nil {
        return diags.Append(fmt.Errorf("%s not initialized", addr))
    }

    req := providers.ConfigureProviderRequest{
        TerraformVersion: version.String(),
        Config:           cfg,
        ClientCapabilities: providers.ClientCapabilities{
            DeferralAllowed: ctx.Deferrals().DeferralAllowed(),
        },
    }

    resp := p.ConfigureProvider(req)
    return resp.Diagnostics
}
```

**Configuration Steps**
1. Verify provider has been initialized
2. Create `ConfigureProviderRequest` with:
   - Terraform version
   - Configuration values (evaluated from HCL)
   - Client capabilities (e.g., deferral support)
3. Call provider's `ConfigureProvider()` RPC method
4. Return diagnostics from provider

### Graph Execution Context: When Provider Methods Are Called

**Provider Initialization Timing**
- Occurs during graph walk when provider nodes are executed
- Executed via `NodeApplyableProvider.Execute()`
- Happens before any resource that depends on the provider is executed

**Provider Configuration Timing**
- Occurs after provider initialization in the execution order
- Executed in `NodeApplyableProvider.Execute()`
- Configuration values are evaluated from HCL using `EvaluateBlock()`
- Uses provider schema to shape the configuration value

**Graph Ordering Ensures**
1. Provider nodes execute before dependent resource nodes
2. Provider initialization completes before `ConfigureProvider()` is called
3. All dependencies are satisfied before resource planning

### CloseProviderTransformer: Resource Cleanup

**Type and Purpose** (`internal/terraform/graph_builder_plan.go:266`)
- Final transformer in pipeline
- Creates nodes that close provider connections after resource operations complete
- Ensures clean shutdown of provider plugins

**Execution Model**
- Provider close operations depend on all resource operations
- Prevents provider shutdown while resources still being processed
- Implemented via `CloseProviderTransformer` in graph construction

---

## Q4: Diff Computation per Resource

### NodePlannableResourceInstance: Resource Instance Planning

**Type** (`internal/terraform/node_resource_plan_instance.go:29-56`)

`NodePlannableResourceInstance` represents a single resource instance that can be planned.

Key fields:
- `NodeAbstractResourceInstance`: Base resource instance information
- `skipRefresh`: Skip remote state sync
- `skipPlanChanges`: Skip change planning (refresh-only mode)
- `forceReplace`: Force resource replacement
- `importTarget`: Import configuration

### Execute Method: Planning Entry Point

**Dispatch** (`internal/terraform/node_resource_plan_instance.go:70-84`)

```go
func (n *NodePlannableResourceInstance) Execute(
    ctx EvalContext,
    op walkOperation,
) tfdiags.Diagnostics {
    addr := n.ResourceInstanceAddr()

    switch addr.Resource.Resource.Mode {
    case addrs.ManagedResourceMode:
        return n.managedResourceExecute(ctx)  // Resource planning
    case addrs.DataResourceMode:
        return n.dataResourceExecute(ctx)     // Data source read
    case addrs.EphemeralResourceMode:
        return n.ephemeralResourceExecute(ctx) // Ephemeral resources
    }
}
```

### managedResourceExecute: Managed Resource Planning Flow

**Overview** (`internal/terraform/node_resource_plan_instance.go:179-450`)

Complete planning sequence for managed resources:

**1. Provider and Schema Resolution** (lines 190-201)
```go
provider, providerSchema, err := getProvider(ctx, n.ResolvedProvider)
// Validate self-references in configuration
```

**2. Import Handling** (lines 203-260)
- If importing: calls `n.importState()` which:
  - Calls provider's `ImportResourceState()` RPC
  - Performs refresh on imported state
  - Handles deferred imports
- Otherwise: reads current state from storage via `n.readResourceInstanceState()`

**3. Refresh Phase** (lines 294-323)
```go
if !n.skipRefresh && !importing {
    instanceRefreshState, refreshDeferred, refreshDiags = n.refresh(
        ctx,
        states.NotDeposed,
        instanceRefreshState,
        ctx.Deferrals().DeferralAllowed(),
    )
}
```

**4. Change Planning** (lines 336-450)
```go
if !n.skipPlanChanges {
    change, instancePlanState, planDeferred, repeatData, planDiags := n.plan(
        ctx,
        nil,
        instanceRefreshState,
        n.ForceCreateBeforeDestroy,
        n.forceReplace,
    )
}
```

### Refresh Phase: State Synchronization

**Implementation** (`internal/terraform/node_resource_abstract_instance.go:580-729`)

```go
func (n *NodeAbstractResourceInstance) refresh(
    ctx EvalContext,
    deposedKey states.DeposedKey,
    state *states.ResourceInstanceObject,
    deferralAllowed bool,
) (*states.ResourceInstanceObject, *providers.Deferred, tfdiags.Diagnostics)
```

**Refresh Execution**
1. **Pre-refresh Hook** (line 613-618)
   - Calls registered hooks to notify UI of refresh start

2. **Provider ReadResource RPC** (lines 635-643)
   ```go
   resp = provider.ReadResource(providers.ReadResourceRequest{
       TypeName:     n.Addr.Resource.Resource.Type,
       PriorState:   unmarkedPriorVal,
       Private:      state.Private,
       ProviderMeta: metaConfigVal,
       ClientCapabilities: providers.ClientCapabilities{
           DeferralAllowed: deferralAllowed,
       },
   })
   ```

3. **State Normalization** (lines 698-721)
   - Normalizes object from legacy SDKs
   - Validates returned state conforms to schema
   - Handles deferral responses

4. **Post-refresh Hook** (lines 724-729)
   - Notifies UI that refresh completed

**Purpose**: Synchronize stored state with actual remote resource state before planning changes

### Plan Phase: Change Computation

**Method Signature** (`internal/terraform/node_resource_abstract_instance.go:744-750`)

```go
func (n *NodeAbstractResourceInstance) plan(
    ctx EvalContext,
    plannedChange *plans.ResourceInstanceChange,
    currentState *states.ResourceInstanceObject,
    createBeforeDestroy bool,
    forceReplace []addrs.AbsResourceInstance,
) (*plans.ResourceInstanceChange, *states.ResourceInstanceObject, *providers.Deferred,
    instances.RepetitionData, tfdiags.Diagnostics)
```

**Plan Execution Steps**

**1. Configuration Evaluation** (lines 819-832)
```go
origConfigVal, _, configDiags := ctx.EvaluateBlock(
    config.Config,
    schema,
    nil,
    keyData,
)
```
- Evaluates HCL configuration to cty values
- Applies variable substitution and expression evaluation

**2. Prior State Setup** (lines 834-852)
- Retrieves prior value from current state
- Handles tainted resource state specially
- Extracts private data from state

**3. Proposed Value Creation** (lines 854-896)
```go
unmarkedConfigVal, unmarkedPaths := configValIgnored.UnmarkDeepWithPaths()
unmarkedPriorVal, _ := priorVal.UnmarkDeepWithPaths()
proposedNewVal := objchange.ProposedNew(schema, unmarkedPriorVal, unmarkedConfigVal)
```
- Starts with prior state value
- Merges in configuration-specified values
- Computes proposed changes based on attribute types

**4. Pre-diff Hook** (lines 899-904)
- Calls registered UI hooks before planning

**5. Provider PlanResourceChange RPC** (lines 906-937)
```go
resp = provider.PlanResourceChange(providers.PlanResourceChangeRequest{
    TypeName:         n.Addr.Resource.Resource.Type,
    Config:           unmarkedConfigVal,
    PriorState:       unmarkedPriorVal,
    ProposedNewState: proposedNewVal,
    PriorPrivate:     priorPrivate,
    ProviderMeta:     metaConfigVal,
    ClientCapabilities: providers.ClientCapabilities{
        DeferralAllowed: deferralAllowed,
    },
})
```

**Provider Response Processing**
- Provider examines prior state, configuration, and proposed new state
- Identifies which attributes require replacement vs update
- Returns planned new state with `RequiredReplace` path set
- Can return deferred actions if unknown values prevent planning

### Action Determination

**getAction Function** (`internal/terraform/node_resource_abstract_instance.go:2736`)

The planned change action (Create/Update/Delete/Replace) is determined by:

1. **Prior State Analysis**
   - `null`: Create action
   - Non-null: Update or Replace action

2. **Required Replacements**
   - Provider sets `RequiredReplace` path set in response
   - Any attribute change in required paths triggers Replace action

3. **Force Replace**
   - User-specified `-replace=address` overrides Update to Replace
   - Skips Create and Delete actions

4. **Create Before Destroy**
   - Replace actions become CreateThenDelete when configured
   - Ensures old resource destroyed after new one created

### Change Recording and State Writing

**Writing Changes** (line 424)
```go
diags = diags.Append(n.writeChange(ctx, change, ""))
```
- Records planned change in `ChangesSync` object
- Part of final plan that will be output to user

**Writing State** (line 428)
```go
diags = diags.Append(n.writeResourceInstanceState(ctx, instancePlanState, workingState))
```
- Updates state to reflect planning results
- `workingState` used during apply to track resource states

---

## Evidence

### Q1 Supporting Files
- `internal/command/plan.go`: Lines 22-190 (PlanCommand implementation)
- `internal/backend/local/backend_plan.go`: Lines 23-150 (backend operation dispatch)
- `internal/terraform/context_plan.go`: Lines 155-372 (Context.Plan methods)
- `internal/terraform/context_plan.go`: Lines 32-138 (PlanOpts definition)

### Q2 Supporting Files
- `internal/terraform/graph_builder_plan.go`: Lines 18-375 (PlanGraphBuilder)
- `internal/terraform/graph_builder_plan.go`: Lines 121-277 (Steps method)
- `internal/terraform/transform_config.go`: Lines 17-250 (ConfigTransformer)
- `internal/terraform/transform_reference.go`: Lines 108-150 (ReferenceTransformer)
- `internal/terraform/transform_attach_state.go`: Lines 29-71 (AttachStateTransformer)

### Q3 Supporting Files
- `internal/terraform/eval_context.go`: Lines 33-150 (EvalContext interface)
- `internal/terraform/eval_context_builtin.go`: Lines 36-300 (BuiltinEvalContext)
- `internal/terraform/eval_context_builtin.go`: Lines 138-186 (InitProvider)
- `internal/terraform/eval_context_builtin.go`: Lines 213-237 (ConfigureProvider)

### Q4 Supporting Files
- `internal/terraform/node_resource_plan_instance.go`: Lines 29-450 (NodePlannableResourceInstance.managedResourceExecute)
- `internal/terraform/node_resource_abstract_instance.go`: Lines 580-729 (refresh method)
- `internal/terraform/node_resource_abstract_instance.go`: Lines 744-1100 (plan method)
- `internal/terraform/node_resource_abstract_instance.go`: Lines 2736+ (getAction function)

### Key Type References
- `PlanCommand`: `internal/command/plan.go:18-20`
- `PlanGraphBuilder`: `internal/terraform/graph_builder_plan.go:30-109`
- `Context`: `internal/terraform/context.go`
- `Plan`: `internal/plans/plan.go`
- `PlanOpts`: `internal/terraform/context_plan.go:32-138`
- `EvalContext`: `internal/terraform/eval_context.go:34-300`
- `BuiltinEvalContext`: `internal/terraform/eval_context_builtin.go:36-94`
- `NodePlannableResourceInstance`: `internal/terraform/node_resource_plan_instance.go:29-56`
- `ReferenceTransformer`: `internal/terraform/transform_reference.go:108-150`
- `ConfigTransformer`: `internal/terraform/transform_config.go:28-53`
