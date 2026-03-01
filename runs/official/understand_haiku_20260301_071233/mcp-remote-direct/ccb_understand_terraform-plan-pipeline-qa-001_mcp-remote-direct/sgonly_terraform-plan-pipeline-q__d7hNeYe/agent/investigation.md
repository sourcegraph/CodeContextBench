# Terraform Plan/Apply Pipeline Architecture

## Q1: Command to Context

When a user runs `terraform plan`, the execution flow is:

1. **CLI Entry Point**: `PlanCommand.Run()` in `internal/command/plan.go:22` parses command-line arguments and validates flags using `arguments.ParsePlan()`.

2. **Backend Preparation**:
   - `PlanCommand.PrepareBackend()` (line 120) loads the backend configuration and initializes the backend via `c.Backend()`.
   - The backend is obtained from `c.Meta` which implements the `BackendWithRemoteTerraformVersion` interface for remote execution detection.

3. **Operation Request Construction**:
   - `PlanCommand.OperationRequest()` (line 145) constructs the operation request by calling `c.Operation(be, viewType)`.
   - Key fields set in the operation request:
     - `Type = backendrun.OperationTypePlan` (line 165)
     - `PlanMode = args.PlanMode` (line 158) - controls whether it's Normal, Destroy, or RefreshOnly mode
     - `Targets = args.Targets` (line 163) - specific resources to target
     - `ForceReplace = args.ForceReplace` (line 164) - resources to force replace
     - `PlanRefresh = args.Refresh` (line 160) - whether to refresh state first
     - `ConfigDir = "."` (line 157)

4. **Backend Execution**:
   - `PlanCommand.Run()` delegates to `c.RunOperation(be, opReq)` (line 103), which is the backend's operation handler.
   - The backend eventually calls `Context.Plan()` with the configuration and state.

5. **Context.Plan() in `internal/terraform/context_plan.go:155`**:
   - Accepts `config *configs.Config`, `prevRunState *states.State`, and `opts *PlanOpts`.
   - The `PlanOpts` structure (lines 30-138) defines the key control fields:
     - `Mode plans.Mode` - NormalMode, DestroyMode, or RefreshOnlyMode
     - `SkipRefresh bool` - whether to skip the refresh phase
     - `Targets []addrs.Targetable` - targeted resources
     - `ForceReplace []addrs.AbsResourceInstance` - resources to force replace
     - `SetVariables InputValues` - variable values
     - `DeferralAllowed bool` - whether deferred actions are allowed
     - `ExternalProviders map[addrs.RootProviderConfig]providers.Interface` - pre-configured providers

6. **Delegation to PlanAndEval()**:
   - `Context.Plan()` (line 155) calls `c.PlanAndEval(config, prevRunState, opts)` and returns the plan.
   - `PlanAndEval()` (line 169) performs additional setup and returns both a plan and an evaluation scope for the root module.

## Q2: Graph Construction Pipeline

The dependency graph for a plan is built via `PlanGraphBuilder` in `internal/terraform/graph_builder_plan.go`:

1. **Graph Builder Creation**:
   - `c.planGraph()` in `context_plan.go:887` creates a new `PlanGraphBuilder` with:
     - `Config` - the configuration tree
     - `State` - the current state
     - `RootVariableValues` - variable values from the plan options
     - `ExternalProviderConfigs` - pre-configured providers
     - `Plugins` - the plugin library
     - `Targets` - resource targets
     - `ForceReplace` - forced replacements
     - `Operation` - the walk operation type (walkPlan, walkPlanDestroy, etc.)

2. **Graph Builder.Build() (line 112)**:
   - Calls `BasicGraphBuilder` with `Steps: b.Steps()` and builds the graph.
   - The `Steps()` method (line 121) returns a sequence of `GraphTransformer` stages that progressively build the dependency graph.

3. **Transformer Pipeline (Steps)**:
   The sequence of transformers in normal plan mode (lines 135-274):

   a. **ConfigTransformer** (lines 137-146): Creates nodes for all resources in the configuration.

   b. **RootVariableTransformer** & **ModuleVariableTransformer** (lines 149-159): Adds variable nodes and their values.

   c. **LocalTransformer** (line 163): Adds local value nodes.

   d. **OutputTransformer** (lines 164-176): Adds output nodes.

   e. **CheckTransformer** (lines 180-183): Adds nodes for check block assertions.

   f. **OrphanResourceInstanceTransformer** (lines 186-191): Handles resources in state but not in config.

   g. **StateTransformer** (lines 198-202): Adds nodes for deposed instances that need cleanup.

   h. **AttachStateTransformer** (line 205): Attaches existing state to resource nodes.

   i. **OrphanOutputTransformer** (lines 208-212): Handles orphaned outputs.

   j. **AttachResourceConfigTransformer** (line 215): Attaches configuration to resource nodes.

   k. **Provider Transformers** (line 218): Adds provider nodes via `transformProviders()`.

   l. **RemovedModuleTransformer** (line 221): Removes modules no longer in config.

   m. **AttachSchemaTransformer** (line 225): Attaches provider schemas to nodes.

   n. **ModuleExpansionTransformer** (line 230): Adds nodes for module calls.

   o. **ExternalReferenceTransformer** (lines 233-235): Handles external references.

   p. **ReferenceTransformer** (line 237): **Adds dependency edges between nodes based on references**.

   q. **AttachDependenciesTransformer** (line 239): Attaches explicit dependencies.

   r. **attachDataResourceDependsOnTransformer** (line 243): Handles depends_on for data sources.

   s. **DestroyEdgeTransformer** (lines 247-249): Adds destroy dependencies.

   t. **TargetsTransformer** (line 256): Prunes nodes not matching targets.

   u. **ForcedCBDTransformer** (line 260): Handles create_before_destroy forced cases.

   v. **ephemeralResourceCloseTransformer** (line 263): Closes ephemeral resource instances.

   w. **CloseProviderTransformer** (line 266): Marks provider cleanup.

   x. **CloseRootModuleTransformer** (line 269): Marks root module cleanup.

   y. **TransitiveReductionTransformer** (line 273): Simplifies the graph by removing transitive edges.

4. **Reference Analysis (ReferenceTransformer)**:
   - Located in `internal/terraform/transform_reference.go:112`, this transformer analyzes node references.
   - It builds a `ReferenceMap` from all vertices (line 115).
   - For each vertex implementing `GraphNodeReferencer`, it:
     1. Calls `m.References(v)` to find parent nodes (line 125)
     2. Connects the vertex to each parent with a DAG edge via `g.Connect()` (line 144)
     3. This creates dependency edges so nodes depending on others execute after their dependencies.

## Q3: Provider Resolution and Configuration

Provider initialization and configuration happens at different points:

1. **Provider Plugin Loading**:
   - Providers are loaded via `c.plugins` which is a `contextPlugins` object.
   - External provider configurations can be passed via `opts.ExternalProviders` in `PlanOpts` (line 125 in context_plan.go).

2. **Provider Node Creation**:
   - `PlanGraphBuilder.initPlan()` (line 279) sets `ConcreteProvider` to create `NodeApplyableProvider` nodes.
   - These nodes are added to the graph via the provider transformers (line 218 in graph_builder_plan.go).

3. **Provider Initialization in Graph Walk**:
   - During graph execution in `c.walk()` (`context_walk.go:83`), nodes are executed.
   - When a provider node is executed, it calls `ConfigureProvider()` via node evaluation.
   - The provider is obtained and configured based on its configuration block in the Terraform configuration.

4. **EvalContext Provider Access**:
   - During node execution, providers are accessed via `EvalContext`:
     - `ctx.Provider(addr addrs.AbsProviderConfig)` returns the provider instance
     - `ctx.ProviderSchema(addr)` returns the provider's schema
   - This is used in `getProvider()` function in `eval_provider.go:46` which:
     1. Checks the provider is initialized (line 51)
     2. Retrieves the schema (line 57)
     3. Returns both the provider interface and schema

5. **Configuration Building**:
   - `buildProviderConfig()` in `eval_provider.go:17` constructs the final provider configuration by:
     1. Starting with the config from the configuration block
     2. Merging with input from `ctx.ProviderInput(addr)` if present
     3. Returning the merged HCL body for evaluation

6. **Provider Lifecycle**:
   - Providers remain open during the entire graph walk
   - `CloseProviderTransformer` (line 266 in graph_builder_plan.go) adds nodes to close provider connections
   - This ensures proper cleanup after the plan walk completes

## Q4: Diff Computation per Resource

For a single managed resource instance, the planning flow is:

1. **Node Execution Entry Point**:
   - `NodePlannableResourceInstance.Execute()` in `node_resource_plan_instance.go:70` is called for each resource instance.
   - It delegates to `n.managedResourceExecute(ctx)` for managed resources (line 76).

2. **State Read Phase** (lines 179-260):
   - `managedResourceExecute()` in `node_resource_plan_instance.go:179` starts.
   - Gets the provider via `getProvider(ctx, n.ResolvedProvider)` (line 190).
   - For non-import cases, calls `n.readResourceInstanceState(ctx, addr)` (line 255) to read the current state from the state file.

3. **Refresh Phase** (lines 296-323):
   - If not skipping refresh (`!n.skipRefresh`), calls `n.refresh(ctx, states.NotDeposed, instanceRefreshState, ...)` (line 298).
   - `NodeAbstractResourceInstance.refresh()` in `node_resource_abstract_instance.go:580`:
     1. Gets the current state value
     2. Calls `provider.ReadResource()` RPC to fetch the current remote state
     3. Returns the refreshed state
   - The refreshed state is written to the refresh state store (line 318).

4. **Plan Phase** (lines 336-450):
   - If not in refresh-only mode (`!n.skipPlanChanges`), proceeds to planning.
   - Evaluates the configuration for the resource instance (line 819 in node_resource_abstract_instance.go).
   - Calls `n.plan()` method (lines 354-356 in node_resource_plan_instance.go):
     - Signature: `n.plan(ctx, nil, instanceRefreshState, n.ForceCreateBeforeDestroy, n.forceReplace)`

5. **PlanResourceChange RPC Call** (node_resource_abstract_instance.go:744-1100):
   - The `plan()` method:
     1. Evaluates the configuration block (line 819)
     2. Validates the resource config via `provider.ValidateResourceConfig()` (line 866)
     3. Applies `ignore_changes` (line 884)
     4. Calls `objchange.ProposedNew()` to compute the proposed new state (line 896)
     5. **Calls `provider.PlanResourceChange()`** (lines 927-937):
        - `TypeName` - the resource type
        - `Config` - the evaluated configuration
        - `PriorState` - the current state from the refresh
        - `ProposedNewState` - the proposed new state based on config
        - `PriorPrivate` - private data from the prior state
        - `ProviderMeta` - provider metadata values
        - `ClientCapabilities` with `DeferralAllowed` flag

6. **Diff Analysis**:
   - The provider returns `PlanResourceChangeResponse` with:
     - `PlannedState` - the final planned state
     - `RequiresReplace` - list of attribute paths that trigger replacement
     - `PlannedPrivate` - updated private data
     - `Diagnostics` - any warnings or errors
   - Terraform validates the response conforms to the schema (line 971)

7. **Action Determination** (line 1054):
   - Calls `getAction()` to determine the action based on:
     - Prior state vs. planned state
     - Configuration vs. planned state
     - `RequiresReplace` attributes from the provider
     - `forceReplace` flag from the user
     - `createBeforeDestroy` setting
   - Returns the action (Create, Update, Delete, Replace, NoOp) and reason

8. **Replace Handling** (lines 1056-1100):
   - If the action is a Replace operation, a second plan call is made:
     1. Computes proposed new value with a null prior (line 1078)
     2. Calls `provider.PlanResourceChange()` again (lines 1089-1099)
     3. This shows which computed attributes change in the replacement

9. **Change Recording** (line 424 in node_resource_plan_instance.go):
   - Creates `plans.ResourceInstanceChange` with:
     - `Addr` - the resource instance address
     - `Change.Action` - Create, Update, Delete, Replace, or NoOp
     - `Change.Before` - the prior state value
     - `Change.After` - the planned new state value
     - `Private` - the private data
   - Writes the change via `n.writeChange(ctx, change, "")` (line 424)

10. **State Tracking** (line 428):
    - Writes the planned state to the working state via `n.writeResourceInstanceState()` (line 428)
    - This allows the UI to show what the resource will look like after apply
    - Allows subsequent resources to reference this resource's planned values

11. **Condition Checks** (lines 452-463):
    - Evaluates post-conditions against the planned change (line 458)
    - These checks can block the plan if they fail

## Evidence

Key file paths and line references:

**Command Layer**:
- `internal/command/plan.go:22` - PlanCommand.Run()
- `internal/command/plan.go:120` - PlanCommand.PrepareBackend()
- `internal/command/plan.go:145` - PlanCommand.OperationRequest()

**Context and Planning**:
- `internal/terraform/context_plan.go:155` - Context.Plan()
- `internal/terraform/context_plan.go:169` - Context.PlanAndEval()
- `internal/terraform/context_plan.go:412` - Context.plan()
- `internal/terraform/context_plan.go:673` - Context.planWalk()
- `internal/terraform/context_plan.go:887` - Context.planGraph()
- `internal/terraform/context_plan.go:30-138` - PlanOpts type definition

**Graph Building**:
- `internal/terraform/graph_builder_plan.go:18-109` - PlanGraphBuilder type
- `internal/terraform/graph_builder_plan.go:112` - Build() method
- `internal/terraform/graph_builder_plan.go:121` - Steps() method
- `internal/terraform/graph_builder_plan.go:279-374` - initPlan(), initDestroy(), initValidate(), initImport()

**Graph Transformers**:
- `internal/terraform/transform_reference.go:108-151` - ReferenceTransformer and reference edge creation
- `internal/terraform/transform_config.go` - ConfigTransformer
- `internal/terraform/transform_attach_state.go` - AttachStateTransformer

**Graph Walking**:
- `internal/terraform/context_walk.go:83` - Context.walk()
- `internal/terraform/context_walk.go:101` - Context.graphWalker()

**Node Execution**:
- `internal/terraform/node_resource_plan_instance.go:29-84` - NodePlannableResourceInstance and Execute()
- `internal/terraform/node_resource_plan_instance.go:179-536` - managedResourceExecute()
- `internal/terraform/node_resource_abstract_instance.go:744-1100` - plan() method with PlanResourceChange() call at line 927
- `internal/terraform/node_resource_abstract_instance.go:580-742` - refresh() method
- `internal/terraform/node_resource_abstract_instance.go:360-492` - planDestroy() method

**Provider Integration**:
- `internal/terraform/eval_provider.go:17-62` - Provider configuration and retrieval
- `internal/terraform/eval_context.go` - EvalContext interface for provider access
- `internal/providers/` - Provider interface definitions
