# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

### Command Execution Flow

The `terraform plan` command is implemented in `internal/command/plan.go` and follows this execution path:

**1. PlanCommand.Run() Entry Point** (`internal/command/plan.go:22`)
- Parses CLI arguments using `arguments.ParsePlan(rawArgs)` (line 34)
- Prepares the backend via `c.PrepareBackend()` (line 68)
- Builds operation request via `c.OperationRequest()` (line 82)
  - Sets `opReq.Type = backendrun.OperationTypePlan` (line 165)
  - Configures key fields from `arguments.Operation`:
    - `opReq.PlanMode = args.PlanMode` (line 158)
    - `opReq.Targets = args.Targets` (line 163)
    - `opReq.ForceReplace = args.ForceReplace` (line 164)
- Invokes `c.RunOperation(be, opReq)` (line 103) which delegates to the backend

**2. Backend Delegation**
- The backend (typically local backend in `internal/backend/local`) receives the `Operation` request
- Backend calls `terraform.NewContext()` to instantiate the planning context
- Backend invokes `context.Plan(config, prevRunState, opts)` where opts is a `*PlanOpts` struct

**3. PlanOpts Structure** (`internal/terraform/context_plan.go:32-138`)
Key fields controlling plan behavior:
- `Mode plans.Mode` (line 36) - Specifies plan type: NormalMode, DestroyMode, or RefreshOnlyMode
- `SkipRefresh bool` (line 42) - Whether to skip refreshing managed resource instances
- `Targets []addrs.Targetable` (line 68) - Resource instances to limit planning to
- `ForceReplace []addrs.AbsResourceInstance` (line 79) - Resource instances to force replacement for
- `DeferralAllowed bool` (line 90) - Whether plan can defer some actions
- `ExternalProviders map[addrs.RootProviderConfig]providers.Interface` (line 125) - Pre-configured providers passed from caller
- `Overrides *mocking.Overrides` (line 106) - Testing overrides for provider computed values

**4. Context.Plan() Method** (`internal/terraform/context_plan.go:155-158`)
```go
func (c *Context) Plan(config *configs.Config, prevRunState *states.State, opts *PlanOpts) (*plans.Plan, tfdiags.Diagnostics)
```
- Delegates immediately to `c.PlanAndEval()` which:
  - Validates configuration and state dependencies (lines 188-204)
  - Routes based on opts.Mode to appropriate planner:
    - `c.plan()` for NormalMode (line 274)
    - `c.destroyPlan()` for DestroyMode (line 276)
    - `c.refreshOnlyPlan()` for RefreshOnlyMode (line 278)

Each of these calls `c.planWalk(config, prevRunState, opts)` which is the core planning logic.

## Q2: Graph Construction Pipeline

### PlanGraphBuilder and the Steps() Method

**PlanGraphBuilder Structure** (`internal/terraform/graph_builder_plan.go:30-109`)
- Constructed with configuration, state, provider plugins, and planning options
- `Build(path addrs.ModuleInstance)` method (line 112) creates a dependency graph
- Calls `BasicGraphBuilder.Build()` with the result of `Steps()` method (line 115)

**Steps() Method Sequence** (`internal/terraform/graph_builder_plan.go:121-277`)

The sequence of GraphTransformers applied:

1. **ConfigTransformer** (line 137)
   - **File**: `internal/terraform/transform_config.go`
   - **Role**: Creates all resource nodes from configuration
   - Recursively walks the configuration tree adding nodes for:
     - Managed resources (line 97-99 in transform_config.go)
     - Data resources (line 100-102)
   - Implements `type ConfigTransformer struct` (line 28)
   - Each resource becomes a node with concrete type set via `ConcreteResource` callback

2. **RootVariableTransformer, ModuleVariableTransformer** (lines 149-159)
   - Evaluates and adds nodes for input variables
   - Sets `Planning: true` to distinguish from apply/destroy walks

3. **LocalTransformer, OutputTransformer** (lines 163-176)
   - Adds local value and output nodes
   - OutputTransformer respects planning mode flags

4. **AttachSchemaTransformer** (line 225)
   - Attaches provider schemas to nodes before reference analysis
   - Critical pre-requisite for ReferenceTransformer

5. **ReferenceTransformer** (line 237)
   - **File**: `internal/terraform/transform_reference.go:108-156`
   - **Type**: `type ReferenceTransformer struct{}` (line 110)
   - **Role**: Analyzes node references and adds dependency edges
   - **Implementation**:
     - Builds `ReferenceMap(vs)` from all graph vertices (line 115)
     - For each vertex, calls `m.References(v)` to find referenced nodes (line 125)
     - Connects nodes with `g.Connect(dag.BasicEdge(v, parent))` (line 144)
   - Creates dependency edges by examining:
     - Configuration expressions that reference other resources
     - Data attributes used in interpolations
     - Module variable references

6. **AttachStateTransformer** (line 205)
   - **File**: `internal/terraform/transform_attach_state.go:29-71`
   - **Type**: `type AttachStateTransformer struct` (line 31)
   - **Role**: Attaches state objects to resource instance nodes
   - **Implementation**:
     - Iterates graph vertices implementing `GraphNodeAttachResourceState` (line 44)
     - For each node, retrieves corresponding resource from state via `t.State.Resource()` (line 50)
     - Calls `an.AttachResourceState(rs.DeepCopy())` to attach (line 67)
     - Enables nodes to access prior state during planning

7. **Provider Configuration** (line 218)
   - `transformProviders()` adds provider nodes to graph
   - Providers are later initialized and configured during walk

8. **Additional Transformers** (lines 220-273)
   - OrphanResourceInstanceTransformer - adds nodes for state-only resources
   - StateTransformer - adds deposed instance nodes
   - AttachResourceConfigTransformer - attaches configuration to resource nodes
   - ModuleExpansionTransformer - creates module instance expansion nodes
   - ReferenceTransformer - adds reference edges (line 237)
   - AttachDependenciesTransformer - records transitive dependencies for destroy ordering
   - DestroyEdgeTransformer - adds edges for destroy plan dependencies
   - TargetsTransformer - filters graph based on `-target` option
   - CloseProviderTransformer (line 266) - adds provider close nodes

**Critical Dependency Relationships**:
- ConfigTransformer must run before ReferenceTransformer (to create nodes)
- AttachSchemaTransformer must run before ReferenceTransformer (schemas needed for reference analysis)
- AttachStateTransformer makes state available to resource nodes for comparison during planning

## Q3: Provider Resolution and Configuration

### Provider Initialization and Configuration Sequence

**Provider Resolution in Graph Walk**

During `c.walk(graph, walkOp, &graphWalkOpts{...})` (context_plan.go:719), the graph is walked and provider nodes are executed first.

**NodeApplyableProvider.Execute()** (`internal/terraform/node_provider.go:28-52`)

For planning walks (`walkPlan`, `walkPlanDestroy`):

1. **InitProvider()** (line 29)
   ```go
   _, err := ctx.InitProvider(n.Addr, n.Config)
   ```
   - **File**: `internal/terraform/eval_context_builtin.go:138-186`
   - **Method**: `func (ctx *BuiltinEvalContext) InitProvider(addr addrs.AbsProviderConfig, config *configs.Provider) (providers.Interface, error)`
   - **Implementation**:
     - Checks if provider already initialized (line 140)
     - For root module providers, checks for external providers in `ctx.ExternalProviderConfigs` (line 156)
     - External providers are wrapped and cached without further configuration (line 160-162)
     - For normal providers, calls `ctx.Plugins.NewProviderInstance(addr.Provider)` (line 166)
     - Wraps provider with Mock provider if provider config specifies `Mock: true` (line 177-180)
     - Stores provider in `ctx.ProviderCache[key]` (line 183)
     - Returns initialized provider interface

2. **ConfigureProvider()** (line 46)
   ```go
   return diags.Append(n.ConfigureProvider(ctx, provider, false))
   ```
   - **File**: `internal/terraform/eval_context_builtin.go:213-237`
   - **Method**: `func (ctx *BuiltinEvalContext) ConfigureProvider(addr addrs.AbsProviderConfig, cfg cty.Value) tfdiags.Diagnostics`
   - **Timing**: Called after InitProvider, before resource planning begins
   - **Implementation**:
     - Validates provider is initialized: `p := ctx.Provider(addr)` (line 221)
     - Builds `ConfigureProviderRequest` with:
       - `Config: cfg` - evaluated provider configuration values (line 229)
       - `TerraformVersion: version.String()` (line 228)
       - `ClientCapabilities.DeferralAllowed` from deferrals (line 231)
     - Calls provider's `ConfigureProvider(req)` RPC method (line 235)
     - Returns diagnostics from provider response (line 236)

**Important Provider Lifecycle Notes**:
- External providers (passed via `ExternalProviders` in PlanOpts) are NOT configured by Terraform Core
  - Comment in PlanOpts (line 121-124): "Terraform Core will NOT call ValidateProviderConfig or ConfigureProvider on any providers in this map"
- Normal providers are configured once during the walk before resource instances use them
- Provider schema is retrieved via `ctx.ProviderSchema(addr)` (eval_context_builtin.go:195-197) which calls `ctx.Plugins.ProviderSchema()`

**CloseProviderTransformer** (`internal/terraform/transform_provider.go:255-310`)

- **Type**: `type CloseProviderTransformer struct{}`
- **Role**: Creates provider close nodes to clean up connections at end of graph walk
- **Implementation**:
  - Creates `graphNodeCloseProvider` nodes for each provider (line 273)
  - Adds edge from closer to provider node (line 281)
  - Connects provider consumers to appropriate closer (line 302-303)
  - Run during transitive reduction ensures unnecessary close edges are removed
- **Execution**: CloseProvider nodes execute during graph walk cleanup, calling provider.Close()

## Q4: Diff Computation per Resource

### Managed Resource Instance Planning Flow

**NodePlannableResourceInstance.Execute()** (`internal/terraform/node_resource_plan_instance.go:70-84`)

Entry point for single resource instance planning:
```go
func (n *NodePlannableResourceInstance) Execute(ctx EvalContext, op walkOperation) tfdiags.Diagnostics
```

Routes to appropriate method based on resource mode:
- `case addrs.ManagedResourceMode: return n.managedResourceExecute(ctx)` (line 76)

**managedResourceExecute() Method** (`internal/terraform/node_resource_plan_instance.go:179-510`)

Complete execution path for managed resource planning:

1. **Pre-Planning Setup** (lines 179-288)
   - Gets provider and schema via `getProvider(ctx, n.ResolvedProvider)` (line 190)
   - Initializes `instanceRefreshState` from prior state if not importing (line 255)
   - Writes prior state to prevRunState for state history (line 268)

2. **Refresh Phase** (lines 296-323)
   - Called unless `n.skipRefresh` is true
   - Invokes `n.refresh(ctx, states.NotDeposed, instanceRefreshState, ...)` (line 298)
   - **File**: `internal/terraform/node_resource_abstract_instance.go:580`
   - **Refresh Steps**:
     - Calls provider's `ReadResource` RPC to get current remote state
     - Detects out-of-band changes (drift)
     - Returns updated state object reflecting remote reality
   - State is merged with configured dependencies (line 310)
   - Updated state written to refreshState (line 318)

3. **Plan Change Computation** (lines 336-356)
   ```go
   change, instancePlanState, planDeferred, repeatData, planDiags := n.plan(
       ctx, nil, instanceRefreshState, n.ForceCreateBeforeDestroy, n.forceReplace,
   )
   ```

**plan() Method** (`internal/terraform/node_resource_abstract_instance.go:744-1150`)

Core diff computation logic for managed resources:

1. **Configuration Evaluation** (lines 819-826)
   ```go
   origConfigVal, _, configDiags := ctx.EvaluateBlock(config.Config, schema, nil, keyData)
   ```
   - Evaluates HCL configuration expressions to get proposed configuration values

2. **ProposedNew Calculation** (line 896)
   ```go
   proposedNewVal := objchange.ProposedNew(schema, unmarkedPriorVal, unmarkedConfigVal)
   ```
   - Merges prior state and configuration per schema rules
   - Unmarked values prevent sensitive data disclosure in logs

3. **Provider Validation** (lines 866-875)
   ```go
   validateResp := provider.ValidateResourceConfig(
       providers.ValidateResourceConfigRequest{
           TypeName: n.Addr.Resource.Resource.Type,
           Config:   unmarkedConfigVal,
       },
   )
   ```
   - Allows provider to reject invalid config before planning

4. **ignore_changes Processing** (lines 884-888)
   - Applies `ignore_changes` attribute to preserve certain fields
   - Must occur before PlanResourceChange for consistency

5. **PlanResourceChange RPC Call** (lines 927-937)
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
   - **File**: `internal/providers/provider.go`
   - **Request Fields**:
     - `TypeName`: Resource type (e.g., "aws_instance")
     - `Config`: HCL-evaluated configuration (marked values preserved)
     - `PriorState`: Current state before change (null for creates)
     - `ProposedNewState`: Theoretical new state from config
     - `PriorPrivate`: Provider-managed sensitive data from prior state
     - `ProviderMeta`: terraform_data values if present
     - `ClientCapabilities.DeferralAllowed`: If deferrals permitted
   - **Response Processing**:
     - `resp.PlannedState`: Provider's computed new state (line 954)
     - `resp.PlannedPrivate`: Provider's sensitive data for new state (line 955)
     - `resp.Deferred`: Optional deferral directive (line 951)
     - `resp.Diagnostics`: Provider warnings/errors

6. **Action Determination** (lines 1042-1150, not shown in excerpt but referenced)
   - Provider's response implicitly determines action:
     - **Create** (`plans.Create`): `PriorState` is null, `PlannedState` is non-null
     - **Update** (`plans.Update`): Both prior and planned differ with same values for unchanged attributes
     - **Replace** (`plans.Replace`): Fields marked with `RequiresReplace` in schema are changed
     - **Delete** (`plans.Delete`): Only computed during destroy plans (not here)
     - **NoOp** (`plans.NoOp`): Prior and planned states are identical

7. **Force-Replace Override** (lines 388-395 in managedResourceExecute)
   - If resource addr in `n.forceReplace`:
     - Planned action is upgraded to Replace if it was NoOp or Update
     - Change.ActionReason set to `plans.ResourceInstanceReplaceByTriggers` (line 394)

8. **Deferred Actions** (lines 397-476 in managedResourceExecute)
   - If provider returned `resp.Deferred`:
     - Change stored in deferrals tracker (line 402)
     - Not added to plan yet; will be revisited after dependencies resolve
   - If dependent resource was deferred:
     - This resource also deferred (line 475)

9. **Change Persistence** (lines 424-431 in managedResourceExecute)
   - Write computed change to plan via `n.writeChange(ctx, change, "")` (line 424)
   - Write resulting state via `n.writeResourceInstanceState(ctx, instancePlanState, workingState)` (line 428)

### Refresh vs Plan Comparison

**Refresh** (`n.refresh()` - line 298):
- Calls provider's `ReadResource` RPC with current state ID
- Returns actual remote resource attributes
- Detects out-of-band changes and deletions
- State is updated to reflect upstream reality

**Plan** (`n.plan()` - lines 354-356):
- Compares refreshed state (prior) with desired configuration
- Calls provider's `PlanResourceChange` RPC
- Provider determines if attributes require replacement or can be updated in-place
- Produces ResourceInstanceChange with proposed action and new value

### Summary: Action Determination Logic

The provider's `PlanResourceChange` determines the action by:
1. Analyzing which configuration attributes changed from prior state
2. For changed attributes, checking schema's `RequiresReplace` directive
3. Returning PlannedState with sensitive fields computed
4. Terraform Core calculates action based on schema-governed requirements

The complete resource change is captured in `plans.ResourceInstanceChange`:
- `Addr`: Resource address
- `ProviderAddr`: Provider configuration used
- `Change.Action`: Create/Update/Replace/Delete/NoOp
- `Change.Before`: Prior state value
- `Change.After`: Planned new value
- `Change.Importing`: If this is an import operation
- `ActionReason`: Why action was chosen (e.g., RequiresReplace, ForcedReplace, TriggeredBy)

## Evidence

### Key File Paths and Line References

**Command Layer**:
- `internal/command/plan.go:22-118` - PlanCommand.Run() implementation
- `internal/command/plan.go:145-190` - OperationRequest building

**Planning Context**:
- `internal/terraform/context_plan.go:30-138` - PlanOpts structure
- `internal/terraform/context_plan.go:155-158` - Context.Plan() entry
- `internal/terraform/context_plan.go:169-287` - Context.PlanAndEval() mode routing
- `internal/terraform/context_plan.go:673-848` - planWalk() core logic
- `internal/terraform/context_plan.go:887-952` - planGraph() graph builder setup

**Graph Construction**:
- `internal/terraform/graph_builder_plan.go:30-109` - PlanGraphBuilder structure
- `internal/terraform/graph_builder_plan.go:112-118` - Build() method
- `internal/terraform/graph_builder_plan.go:121-277` - Steps() transformer sequence
- `internal/terraform/graph_builder_plan.go:279-317` - initPlan() concrete node setup
- `internal/terraform/transform_config.go:17-53` - ConfigTransformer type
- `internal/terraform/transform_config.go:55-88` - ConfigTransformer.Transform()
- `internal/terraform/transform_reference.go:108-156` - ReferenceTransformer type and implementation
- `internal/terraform/transform_attach_state.go:29-71` - AttachStateTransformer type and implementation
- `internal/terraform/transform_provider.go:255-310` - CloseProviderTransformer type

**Provider Initialization**:
- `internal/terraform/node_provider.go:18-52` - NodeApplyableProvider type and Execute()
- `internal/terraform/eval_provider.go:45-62` - getProvider() helper
- `internal/terraform/eval_context_builtin.go:138-186` - InitProvider() implementation
- `internal/terraform/eval_context_builtin.go:188-211` - Provider() and ProviderSchema() helpers
- `internal/terraform/eval_context_builtin.go:213-237` - ConfigureProvider() implementation
- `internal/terraform/eval_context_builtin.go:199-211` - CloseProvider() implementation
- `internal/terraform/node_provider_eval.go:8-22` - NodeEvalableProvider for schema-only init

**Resource Planning**:
- `internal/terraform/node_resource_plan_instance.go:29-84` - NodePlannableResourceInstance type
- `internal/terraform/node_resource_plan_instance.go:70-84` - Execute() router
- `internal/terraform/node_resource_plan_instance.go:179-510` - managedResourceExecute() main logic
- `internal/terraform/node_resource_abstract_instance.go:580-650` - refresh() method signature and state update
- `internal/terraform/node_resource_abstract_instance.go:744-1150` - plan() method with PlanResourceChange call
- `internal/terraform/node_resource_abstract_instance.go:927-943` - PlanResourceChange RPC invocation

**Graph Walk**:
- `internal/terraform/context_plan.go:719-731` - walk() invocation with graph walk options
- `internal/terraform/graph_walk.go` - Graph walking and concurrent node execution
