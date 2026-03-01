# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

When a user runs `terraform plan`, the execution flow from CLI to core planning logic proceeds as follows:

### PlanCommand.Run() - CLI Entry Point
**File**: `internal/command/plan.go:22`

The `PlanCommand.Run()` method orchestrates the plan command:
1. **Argument Parsing** (line 34): `arguments.ParsePlan(rawArgs)` parses CLI flags
2. **Backend Preparation** (line 68): `c.PrepareBackend()` initializes the backend
3. **Operation Request Building** (line 82): `c.OperationRequest()` constructs the operation with:
   - `opReq.PlanMode` (from `args.PlanMode`)
   - `opReq.PlanRefresh` (from `args.Refresh`)
   - `opReq.Targets` (from `args.Targets`)
   - `opReq.ForceReplace` (from `args.ForceReplace`)
4. **Variable Gathering** (line 90): `c.GatherVariables()` collects input values
5. **Backend Execution** (line 103): `c.RunOperation(be, opReq)` delegates to backend

### Backend Execution - Plan Operation
**File**: `internal/backend/local/backend_plan.go:108`

The local backend's `opPlan()` method executes the actual planning:
```go
plan, planDiags = lr.Core.Plan(lr.Config, lr.InputState, lr.PlanOpts)
```

This calls `terraform.Context.Plan()` with:
- `config`: The Terraform configuration (root module + children)
- `prevRunState`: The prior state from the last run
- `opts`: The planning options (contains Mode, SkipRefresh, Targets, ForceReplace, etc.)

### Context.Plan() - Core Planning Entry Point
**File**: `internal/terraform/context_plan.go:155`

The `Context.Plan()` method is the public API to the planning logic:
```go
func (c *Context) Plan(config *configs.Config, prevRunState *states.State, opts *PlanOpts)
  (*plans.Plan, tfdiags.Diagnostics)
```

This delegates to `Context.PlanAndEval()` (line 156), which:
1. Validates configurations and options (lines 188-247)
2. Routes based on plan mode (lines 206-229):
   - `plans.NormalMode` → `c.plan()`
   - `plans.RefreshOnlyMode` → `c.refreshOnlyPlan()`
   - `plans.DestroyMode` → `c.destroyPlan()`
3. For normal mode, calls `c.plan()` (line 412)

### Context.plan() and Context.planWalk() - Graph Building and Execution
**File**: `internal/terraform/context_plan.go:412 and 673`

The `c.plan()` method for normal mode delegates to `c.planWalk()`, which:
1. **Applies Moves** (line 678): `c.prePlanFindAndApplyMoves()` handles resource move statements
2. **Builds Graph** (line 694): `c.planGraph()` constructs the dependency graph using `PlanGraphBuilder`
3. **Walks Graph** (line 719): `c.walk()` executes the graph with `graphWalkOpts` containing changes, move results, and override data

### PlanOpts - Planning Configuration
**File**: `internal/terraform/context_plan.go:32-138`

The `PlanOpts` struct controls plan behavior with key fields:
- `Mode`: The plan mode (Normal, Destroy, RefreshOnly)
- `SkipRefresh`: Whether to skip refreshing remote state (default: false)
- `PreDestroyRefresh`: Special flag for refresh before destroy
- `SetVariables`: Input variable values
- `Targets`: Resource addresses to target (for `-target=...`)
- `ForceReplace`: Resource instances to force replacement (for `-replace=...`)
- `DeferralAllowed`: Whether to allow deferred changes
- `ExternalReferences`: References from external callers to preserve
- `Overrides`: Test mocking overrides
- `GenerateConfigPath`: Path for generated import configuration
- `ExternalProviders`: Pre-configured external provider clients

## Q2: Graph Construction Pipeline

### PlanGraphBuilder.Steps() - Transformer Sequence
**File**: `internal/terraform/graph_builder_plan.go:121`

The `PlanGraphBuilder.Steps()` method returns a sequence of `GraphTransformer` stages that build the dependency graph:

#### Stage 1: Node Creation (lines 135-202)
1. **ConfigTransformer** (line 137): Creates resource nodes from configuration
   - Adds all managed and data resources from the config tree
   - Marks whether this is a destroy operation
   - Handles import targets and configuration generation

2. **Variable and Output Transformers** (lines 149-176):
   - `RootVariableTransformer`: Adds root module variables with values
   - `ModuleVariableTransformer`: Adds module-level variables
   - `variableValidationTransformer`: Adds validation nodes
   - `LocalTransformer`: Adds local value nodes
   - `OutputTransformer`: Adds output value nodes

3. **Orphan and Deposed Resource Handling** (lines 185-202):
   - `OrphanResourceInstanceTransformer`: Adds nodes for resources in state but not config
   - `StateTransformer`: Adds nodes for deposed resource instances (from failed replacements)
   - `AttachStateTransformer` (line 205): **Attaches prior state to each resource instance node**

#### Stage 2: Configuration and Provider Setup (lines 214-225)
4. **AttachResourceConfigTransformer** (line 215): Attaches configuration blocks to resource nodes

5. **Provider Transformation** (line 218): `transformProviders()` adds provider nodes
   - Adds placeholder nodes for externally-configured providers
   - Adds provider configuration nodes from the configuration

6. **AttachSchemaTransformer** (line 225): **Must run before ReferenceTransformer**
   - Attaches provider schemas to nodes
   - Enables reference analysis based on schema information

#### Stage 3: Module and Reference Processing (lines 227-239)
7. **ModuleExpansionTransformer** (line 230): Creates expansion nodes for module calls

8. **ExternalReferenceTransformer** (line 233): Preserves externally referenced nodes

9. **ReferenceTransformer** (line 237): **Creates dependency edges from references**
   - Analyzes all node references to find what each node depends on
   - Connects edges from referencing nodes to their dependencies
   - Implementation covered in detail below

10. **AttachDependenciesTransformer** (line 239): Attaches explicit dependencies
    - Processes depends_on arguments in resource configuration

11. **attachDataResourceDependsOnTransformer** (line 243): Handles data resource depends_on

#### Stage 4: Lifecycle and Cleanup (lines 245-274)
12. **DestroyEdgeTransformer** (line 247): Creates edges for destroy operations
13. **pruneUnusedNodesTransformer** (line 251): Removes unused nodes
14. **TargetsTransformer** (line 256): Filters graph to only targeted resources (with dependencies)
15. **ForcedCBDTransformer** (line 260): Forces create-before-destroy where needed
16. **ephemeralResourceCloseTransformer** (line 263): Closes ephemeral resources
17. **CloseProviderTransformer** (line 266): **Adds edges to properly close providers**
18. **CloseRootModuleTransformer** (line 269): Closes the root module
19. **TransitiveReductionTransformer** (line 273): Removes redundant edges

### ReferenceTransformer - Dependency Edge Creation
**File**: `internal/terraform/transform_reference.go:108-156`

The `ReferenceTransformer` analyzes configuration references to build dependency edges:

```go
func (t *ReferenceTransformer) Transform(g *Graph) error
```

**Key Interface Requirements**:
- **GraphNodeReferenceable**: Implemented by nodes that can be referenced (resources, modules, variables, outputs)
  - `ReferenceableAddrs()`: Returns addresses through which this node can be referenced

- **GraphNodeReferencer**: Implemented by nodes that reference other terraform objects
  - `References()`: Returns a list of `addrs.Reference` objects being referenced

**Algorithm** (lines 112-156):
1. Builds a `ReferenceMap` from all graph vertices (line 115)
2. For each vertex that implements `GraphNodeReferencer`:
   - Calls `m.References(v)` to find parent dependencies (line 125)
   - For each parent that is NOT a destroy node (to avoid cycles):
     - Creates a `dag.BasicEdge` from the referencing node to the parent (line 144)
     - Registers the edge in the graph: `g.Connect(edge)`

**Example**: If a resource `aws_instance.web` references `aws_security_group.allow_http`, the ReferenceTransformer:
1. Identifies the reference in the instance's configuration
2. Finds the security group node in the graph
3. Creates an edge: `aws_instance.web` → `aws_security_group.allow_http`
4. This ensures the security group is created before the instance

### ConfigTransformer - Resource Node Creation
**File**: `internal/terraform/transform_config.go:17-30`

The `ConfigTransformer` adds nodes for all resources in the configuration:
- Iterates over `config.Module.ManagedResources` and `config.Module.DataResources`
- Creates concrete resource nodes using the provided `ConcreteResourceNodeFunc`
- Only adds resources; variables, outputs, and providers are added separately
- Handles import targets for `import` blocks

### AttachStateTransformer - State Attachment
**File**: `internal/terraform/transform_attach_state.go:35-63`

The `AttachStateTransformer` attaches prior run state to resource instance nodes:
```go
func (t *AttachStateTransformer) Transform(g *Graph) error
```

For each vertex implementing `GraphNodeAttachResourceState`:
1. Gets the resource address from the vertex
2. Looks up the corresponding resource in `t.State`
3. Calls `AttachResourceState()` on the vertex with the prior state
4. This state is used during planning to detect what changed

## Q3: Provider Resolution and Configuration

### Provider Initialization - EvalContext.InitProvider()
**File**: `internal/terraform/eval_context.go:49-55`

The `EvalContext` interface defines provider initialization:
```go
InitProvider(addr addrs.AbsProviderConfig, configs *configs.Provider)
  (providers.Interface, error)
```

**Implementation**: `internal/terraform/eval_context_builtin.go:138`

The `BuiltinEvalContext.InitProvider()` method:
1. Checks if the provider is already initialized (error if so)
2. Uses the configured provider factory to create a plugin process
3. Caches the provider instance in `ctx.Providers` map
4. Returns the provider implementation

**When Called**: During graph execution when a provider node is reached
- Provider nodes implement `GraphNodeExecutable`
- The graph walk reaches the provider node
- `Execute()` calls `InitProvider()` to instantiate the plugin

### Provider Configuration - NodeApplyableProvider.ConfigureProvider()
**File**: `internal/terraform/node_provider.go:99-110`

After a provider is initialized, it must be configured:
```go
func (n *NodeApplyableProvider) ConfigureProvider(ctx EvalContext,
  provider providers.Interface, verifyConfigIsKnown bool) tfdiags.Diagnostics
```

This method:
1. Builds the provider configuration from the configuration block and context evaluation
2. Calls `provider.GetProviderSchema()` to get schema for validation
3. Evaluates the provider configuration block
4. Calls `provider.ConfigureProvider()` (provider RPC) with the evaluated config
5. Returns diagnostics if configuration fails

**Graph Execution Timing**:
- Provider nodes are created by `ProviderConfigTransformer`
- Graph walk ensures providers execute before dependent resources
- `CloseProviderTransformer` creates edges from resources to provider close nodes

### CloseProviderTransformer - Provider Lifecycle
**File**: `internal/terraform/graph_builder_plan.go:266`

The `CloseProviderTransformer` adds provider cleanup to the graph:
- Creates edges to ensure providers are closed after all dependent resources complete
- Prevents resource leaks and ensures proper plugin shutdown
- Runs after all planning and refresh operations

**Provider Lifecycle Summary**:
1. **Instantiation**: `InitProvider()` creates plugin process
2. **Validation**: `ValidateProvider()` validates configuration (during validation walk)
3. **Configuration**: `ConfigureProvider()` configures the provider with credentials/settings
4. **Usage**: Resources use the configured provider during planning/refresh
5. **Cleanup**: `CloseProvider()` shuts down the plugin process

## Q4: Diff Computation per Resource

### Execution Entry Point - NodePlannableResourceInstance.Execute()
**File**: `internal/terraform/node_resource_plan_instance.go:70`

The `NodePlannableResourceInstance.Execute()` method is the entry point for planning a single resource instance:

```go
func (n *NodePlannableResourceInstance) Execute(ctx EvalContext, op walkOperation)
  tfdiags.Diagnostics
```

Routes to specific handler based on resource type:
- **Managed Resources** (line 75): Calls `n.managedResourceExecute()`
- **Data Resources** (line 77): Calls `n.dataResourceExecute()`
- **Ephemeral Resources** (line 79): Calls `n.ephemeralResourceExecute()`

### Managed Resource Execution - managedResourceExecute()
**File**: `internal/terraform/node_resource_plan_instance.go:179-536`

The complete execution flow for managed resources:

#### Step 1: Provider Setup (lines 190-194)
```go
provider, providerSchema, err := getProvider(ctx, n.ResolvedProvider)
```
- Retrieves the already-initialized and configured provider for this resource
- Gets the provider's schema for the resource type

#### Step 2: Import or Read State (lines 210-260)
**If importing**:
1. Calls `n.importState()` which invokes provider's `ImportResourceState()` RPC
2. Gets the imported resource state

**If not importing**:
1. Calls `n.readResourceInstanceState()` to load state from the prior state
2. Handles schema upgrades if needed

#### Step 3: State Snapshots (lines 268-278)
- Writes the loaded/imported state to `prevRunState` (preserves original)
- Writes the loaded/imported state to `refreshState` (will be updated)

#### Step 4: Refresh Phase (lines 296-323)
**Calls `n.refresh()`** (unless `skipRefresh` is true or importing):

```go
instanceRefreshState, refreshDeferred, refreshDiags =
  n.refresh(ctx, states.NotDeposed, instanceRefreshState,
    ctx.Deferrals().DeferralAllowed())
```

### Refresh Method - Synchronizing Remote State
**File**: `internal/terraform/node_resource_abstract_instance.go:580`

The `refresh()` method detects out-of-band changes to the remote resource:

```go
func (n *NodeAbstractResourceInstance) refresh(ctx EvalContext,
  deposedKey states.DeposedKey, state *states.ResourceInstanceObject,
  deferralAllowed bool) (*states.ResourceInstanceObject, *providers.Deferred,
  tfdiags.Diagnostics)
```

**Refresh Steps** (lines 580-741):
1. **Pre-refresh Hook** (line 613): Calls hook to notify UI before refresh
2. **Provider ReadResource RPC** (line 635):
   ```go
   resp = provider.ReadResource(providers.ReadResourceRequest{
     TypeName: n.Addr.Resource.Resource.Type,
     PriorState: priorVal,
     Private: state.Private,
     ProviderMeta: metaConfigVal,
     ClientCapabilities: {DeferralAllowed: deferralAllowed},
   })
   ```
3. **State Update**: Updates state with the remote object's current state
4. **Validation**: Ensures returned state conforms to schema
5. **Returns**: New state reflecting remote reality, potential deferral indicator

**Purpose**: The refresh detects:
- Resources deleted outside of Terraform
- Attribute changes made outside of Terraform (drift)
- Resource still exists and is accessible

#### Step 5: Plan Phase (lines 336-476)
**Calls `n.plan()`** (unless `skipPlanChanges` is true):

```go
change, instancePlanState, planDeferred, repeatData, planDiags :=
  n.plan(ctx, nil, instanceRefreshState, n.ForceCreateBeforeDestroy,
    n.forceReplace)
```

### Plan Method - Computing Desired Changes
**File**: `internal/terraform/node_resource_abstract_instance.go:744`

The `plan()` method computes what changes are needed to match configuration:

```go
func (n *NodeAbstractResourceInstance) plan(ctx EvalContext,
  plannedChange *plans.ResourceInstanceChange,
  currentState *states.ResourceInstanceObject,
  createBeforeDestroy bool,
  forceReplace []addrs.AbsResourceInstance,
) (*plans.ResourceInstanceChange, *states.ResourceInstanceObject,
  *providers.Deferred, instances.RepetitionData, tfdiags.Diagnostics)
```

**Plan Steps** (lines 744-1200+):

1. **Configuration Evaluation** (lines 796-825):
   - Evaluates the resource configuration block in context
   - Handles `for_each`, `count` expressions
   - Validates preconditions

2. **Prior Value Preparation** (lines 834-894):
   - Gets prior state value (from refresh)
   - Handles tainted state (forces replace)
   - Applies `ignore_changes` meta-argument

3. **Proposed New Value** (line 896):
   ```go
   proposedNewVal := objchange.ProposedNew(schema,
     unmarkedPriorVal, unmarkedConfigVal)
   ```
   - Combines prior state with desired configuration
   - Fills in provider-known computed values

4. **Provider ValidateResourceConfig** (line 866):
   - Calls provider to validate configuration is correct
   - Catches configuration errors early

5. **Provider PlanResourceChange RPC** (line 927):
   ```go
   resp = provider.PlanResourceChange(providers.PlanResourceChangeRequest{
     TypeName: n.Addr.Resource.Resource.Type,
     Config: unmarkedConfigVal,
     PriorState: unmarkedPriorVal,
     ProposedNewState: proposedNewVal,
     PriorPrivate: priorPrivate,
     ProviderMeta: metaConfigVal,
     ClientCapabilities: {DeferralAllowed: deferralAllowed},
   })
   ```
   - Core RPC call to provider plugin
   - Provider returns `PlannedState` and `RequiresReplace` paths
   - Provider may also return deferred status

6. **Action Determination** (line 1054):
   ```go
   action, actionReason := getAction(n.Addr, unmarkedPriorVal,
     unmarkedPlannedNewVal, createBeforeDestroy, forceReplace, reqRep)
   ```

### getAction() - Determining Resource Action
**File**: `internal/terraform/node_resource_abstract_instance.go:2736`

The `getAction()` function determines what action to take based on plan analysis:

```go
func getAction(addr addrs.AbsResourceInstance, priorVal, plannedNewVal cty.Value,
  createBeforeDestroy bool, forceReplace []addrs.AbsResourceInstance,
  reqRep cty.PathSet) (action plans.Action, actionReason plans.ResourceInstanceChangeActionReason)
```

**Action Determination Logic** (lines 2736-2774):

1. **Create** (line 2762):
   - When `priorVal.IsNull()` (no prior state)
   - Resource is brand new

2. **NoOp** (line 2764):
   - When `eq && !matchedForceReplace`
   - Prior and planned values are identical AND not force-replaced
   - No changes needed

3. **Replace** (lines 2765-2773):
   - When `matchedForceReplace` (user specified `-replace=...`)
   - OR `!reqRep.Empty()` (provider says certain paths require replacement)
   - Determines replace strategy:
     - `CreateThenDelete` if `createBeforeDestroy=true`
     - `DeleteThenCreate` otherwise

4. **Update** (implicit):
   - If prior exists and planned is different
   - And no paths require replacement
   - Resource is modified in-place

5. **Delete** (handled elsewhere):
   - When resource is in state but not in configuration
   - Handled by separate graph nodes (`OrphanResourceInstanceTransformer`)

**Special Cases**:
- **Tainted State** (lines 1143-1152): Tainted resources always force replace
- **Replace Triggered By** (lines 393-395): Resources can be replaced by changes in other resources
- **forceReplace Filtering** (line 1048): User `-replace=...` flags override provider logic

### Change Recording (lines 404-431)
- Writes the computed change to the plan: `n.writeChange(ctx, change, "")`
- Writes the resulting state to working state: `n.writeResourceInstanceState(ctx, instancePlanState, workingState)`
- Checks `prevent_destroy` meta-argument
- Evaluates postconditions

## Evidence

### Critical Files and Line References

**Command and Backend**:
- `internal/command/plan.go:22` - PlanCommand.Run() entry point
- `internal/command/plan.go:82` - OperationRequest building with PlanMode, Refresh, Targets, ForceReplace
- `internal/backend/local/backend_plan.go:108` - Backend invocation of Context.Plan()

**Context Planning**:
- `internal/terraform/context_plan.go:32-138` - PlanOpts type definition and fields
- `internal/terraform/context_plan.go:155` - Context.Plan() public API
- `internal/terraform/context_plan.go:169` - Context.PlanAndEval() router
- `internal/terraform/context_plan.go:412` - Context.plan() for normal mode
- `internal/terraform/context_plan.go:673` - Context.planWalk() graph builder and walker

**Graph Building**:
- `internal/terraform/graph_builder_plan.go:30-109` - PlanGraphBuilder struct
- `internal/terraform/graph_builder_plan.go:121` - PlanGraphBuilder.Steps() transformer sequence
- `internal/terraform/graph_builder_plan.go:135-274` - Complete transformer pipeline with line numbers

**Transformers**:
- `internal/terraform/transform_config.go:17-30` - ConfigTransformer
- `internal/terraform/transform_attach_state.go:35` - AttachStateTransformer.Transform()
- `internal/terraform/transform_reference.go:108-156` - ReferenceTransformer
- `internal/terraform/transform_provider.go:18-28` - transformProviders()

**Provider Operations**:
- `internal/terraform/eval_context.go:49-55` - EvalContext.InitProvider() interface
- `internal/terraform/eval_context_builtin.go:138` - BuiltinEvalContext.InitProvider() implementation
- `internal/terraform/node_provider.go:99-110` - NodeApplyableProvider.ConfigureProvider()

**Resource Planning**:
- `internal/terraform/node_resource_plan_instance.go:29-56` - NodePlannableResourceInstance struct
- `internal/terraform/node_resource_plan_instance.go:70` - Execute() router
- `internal/terraform/node_resource_plan_instance.go:179-536` - managedResourceExecute() main logic
- `internal/terraform/node_resource_plan_instance.go:354-356` - Call to n.plan()

**Refresh and Plan Methods**:
- `internal/terraform/node_resource_abstract_instance.go:580` - refresh() method
- `internal/terraform/node_resource_abstract_instance.go:635` - provider.ReadResource() RPC call
- `internal/terraform/node_resource_abstract_instance.go:744` - plan() method
- `internal/terraform/node_resource_abstract_instance.go:927` - provider.PlanResourceChange() RPC call (first)
- `internal/terraform/node_resource_abstract_instance.go:1089` - provider.PlanResourceChange() RPC call (for replace)
- `internal/terraform/node_resource_abstract_instance.go:2736` - getAction() function
- `internal/terraform/node_resource_abstract_instance.go:2761-2774` - Action determination logic
