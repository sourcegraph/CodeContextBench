# PostgreSQL Query Execution Pipeline: Complete Architectural Analysis

## Files Examined

### Traffic Cop (Query Entry Point)
- **src/backend/tcop/postgres.c** — Main backend interface; traffic cop containing exec_simple_query() entry point and pipeline coordination functions (pg_parse_query, pg_analyze_and_rewrite_fixedparams, pg_plan_queries, pg_rewrite_query)
- **src/include/tcop/tcopprot.h** — Traffic cop function declarations

### Parser Subsystem
- **src/backend/parser/parser.c** — Raw parser wrapper; calls raw_parser(RAW_PARSE_DEFAULT) which invokes flex/bison
- **src/backend/parser/gram.y** — Bison grammar specification; defines SQL syntax rules; produces RawStmt parse tree nodes without database access
- **src/backend/parser/scan.l** — Flex lexical scanner specification; tokenizes input stream; kept synchronized with src/fe_utils/psqlscan.l
- **src/include/parser/parser.h** — Parser API declarations; defines RawParseMode enum and raw_parser() signature

### Semantic Analysis Subsystem
- **src/backend/parser/analyze.c** — Semantic analyzer implementation; contains parse_analyze_fixedparams(), parse_analyze_varparams(), parse_analyze_withcb(), transformTopLevelStmt(), and statement-specific transformers
- **src/include/parser/analyze.h** — Semantic analyzer API declarations
- **src/backend/parser/parse_expr.h** — Expression analysis support
- **src/backend/parser/parse_clause.h** — SQL clause analysis (WHERE, GROUP BY, HAVING, etc.)
- **src/backend/parser/parse_func.h** — Function resolution and type coercion
- **src/backend/parser/parse_relation.h** — Table and relation name resolution
- **src/backend/parser/parse_target.h** — Target list analysis
- **src/backend/parser/parse_agg.h** — Aggregate function analysis

### Query Rewriter Subsystem
- **src/backend/rewrite/rewriteHandler.c** — Main rewriter containing QueryRewrite() function; applies ON SELECT/INSERT/UPDATE/DELETE rules and row-level security policies
- **src/backend/rewrite/rewriteDefine.c** — Rule definition handling
- **src/backend/rewrite/rewriteManip.c** — Rule manipulation utilities
- **src/backend/rewrite/rowsecurity.c** — Row-level security policy integration
- **src/include/rewrite/rewriteHandler.h** — Rewriter API declarations

### Optimizer/Planner Subsystem
- **src/backend/optimizer/plan/planner.c** — Main planner entry point; contains planner() and standard_planner(); orchestrates two-phase optimization
- **src/backend/optimizer/path/allpaths.c** — Phase 1: Path generation; generates alternative access paths with cost estimates; handles scan methods, index selection, join ordering
- **src/backend/optimizer/plan/createplan.c** — Phase 2: Plan conversion; contains create_plan() which converts best Path into executable Plan tree
- **src/backend/optimizer/plan/planmain.c** — Planning orchestration and coordination
- **src/backend/optimizer/plan/initsplan.c** — Initial plan construction
- **src/backend/optimizer/plan/subselect.c** — Subquery planning
- **src/backend/optimizer/plan/planagg.c** — Aggregate query planning
- **src/backend/optimizer/plan/analyzejoins.c** — Join analysis and optimization
- **src/include/optimizer/optimizer.h** — Optimizer API declarations; declares planner() function

### Executor Subsystem
- **src/backend/executor/execMain.c** — Main executor entry point; contains ExecutorStart(), ExecutorRun(), ExecutePlan(), ExecutorFinish(), ExecutorEnd(); implements execution loop
- **src/backend/executor/execProcnode.c** — Node dispatch controller; contains ExecInitNode() (initialization switch dispatch), ExecProcNode() (tuple generation dispatch via function pointers), ExecEndNode() (cleanup dispatch); implements Volcano-style iterator model with dynamic method dispatch
- **src/backend/executor/execExpr.c** — Expression evaluation setup
- **src/backend/executor/execExprInterp.c** — Expression interpreter
- **src/backend/executor/execTuples.c** — Tuple slot management and allocation
- **src/backend/executor/execUtils.c** — Executor utilities
- **src/backend/executor/execScan.c** — Base scan node utilities
- **src/backend/executor/execAmi.c** — Access method interface
- **src/backend/executor/nodeSeqscan.c** — Sequential scan node implementation
- **src/backend/executor/nodeIndexscan.c** — Index scan node implementation
- **src/backend/executor/nodeNestloop.c** — Nested loop join node implementation
- **src/backend/executor/nodeMergejoin.c** — Merge join node implementation
- **src/backend/executor/nodeHashjoin.c** — Hash join node implementation
- **src/backend/executor/nodeAgg.c** — Aggregate function implementation
- **src/backend/executor/nodeSort.c** — Sort node implementation
- **src/backend/executor/nodeHash.c** — Hash table construction
- **src/backend/executor/nodeAppend.c** — UNION/Append operations
- **src/backend/executor/nodeLimit.c** — LIMIT/OFFSET implementation
- **src/backend/executor/nodeModifyTable.c** — INSERT/UPDATE/DELETE implementation
- Plus 30+ additional node-specific implementation files

### Portal/Cursor Interface
- **src/backend/tcop/pquery.c** — Portal execution driver; contains PortalRun() which drives query execution through ExecutorStart/Run/Finish/End
- **src/include/tcop/pquery.h** — Portal API declarations

### Node Definitions
- **src/include/nodes/parsenodes.h** — Parse tree node definitions (RawStmt, Node hierarchy)
- **src/include/nodes/plannodes.h** — Plan tree node definitions (Plan, PlannedStmt)
- **src/include/nodes/execnodes.h** — Execution state node definitions (PlanState and its variants)
- **src/include/nodes/primnodes.h** — Primitive expression node definitions
- **src/include/nodes/pathnodes.h** — Path node definitions (RelOptInfo, Path hierarchy)

---

## Dependency Chain

### 1. Entry Point: Traffic Cop
**Location:** `src/backend/tcop/postgres.c:1011` (exec_simple_query)

```
exec_simple_query(const char *query_string)
  → Establishes transaction context
  → Manages memory contexts (MessageContext, per-parsetree context)
  → Coordinates all downstream pipeline stages
```

### 2. Parser Stage
**Calls:** `src/backend/tcop/postgres.c:603` (pg_parse_query)
```
pg_parse_query(const char *query_string)
  → raw_parser(query_string, RAW_PARSE_DEFAULT) [src/backend/parser/parser.c:42]
    → yyparse() [generated from gram.y]
      ├─ Lexer: scan.l tokenization
      └─ Parser: gram.y syntax rules
  ← Returns: List of RawStmt nodes
```

**Data Structure:** `RawStmt` containing:
- `stmt` — Pointer to statement union (SelectStmt, InsertStmt, UpdateStmt, DeleteStmt, etc.)
- `stmt_location` — Position in source string
- `stmt_len` — Length of statement in source

### 3. Semantic Analysis Stage
**Calls:** `src/backend/tcop/postgres.c:1189` (pg_analyze_and_rewrite_fixedparams)
  → `parse_analyze_fixedparams()` [src/backend/parser/analyze.c:105]
    → `transformTopLevelStmt()` [src/backend/parser/analyze.c:249]
      ├─ Switch on statement type (SelectStmt, InsertStmt, UpdateStmt, DeleteStmt, etc.)
      ├─ Calls statement-specific transformer:
      │  ├─ transformSelectStmt()
      │  ├─ transformInsertStmt()
      │  ├─ transformUpdateStmt()
      │  └─ transformDeleteStmt()
      └─ Calls helper modules:
         ├─ parse_expr.c — Expression analysis
         ├─ parse_clause.c — Clause analysis
         ├─ parse_func.c — Function resolution
         ├─ parse_relation.c — Relation name resolution
         └─ parse_target.c — Target list processing

**Data Structure:** `Query` containing:
- `commandType` — CMD_SELECT, CMD_INSERT, CMD_UPDATE, CMD_DELETE, CMD_UTILITY, etc.
- `rtable` — Range table (FROM clause relations)
- `targetList` — SELECT target list (fully type-checked expressions)
- `whereClause` — WHERE predicate (fully type-checked)
- `groupClause`, `havingClause` — GROUP BY specifications
- `sortClause` — ORDER BY specifications
- `limitOffset`, `limitCount` — LIMIT/OFFSET
- `canSetTag` — Can this command set completion tag?
- `queryId` — Query fingerprint for pg_stat_statements

### 4. Rewrite Stage
**Calls:** `pg_analyze_and_rewrite_fixedparams()` internally → `pg_rewrite_query()` [src/backend/tcop/postgres.c:798]
  → `QueryRewrite()` [src/backend/rewrite/rewriteHandler.c:4566]
    ├─ Lock tables referenced in query
    ├─ Process ON SELECT/INSERT/UPDATE/DELETE rules
    │  ├─ Rule definition acquisition
    │  ├─ Rule expansion (may expand one query to multiple)
    │  ├─ Cycle detection (prevent infinite recursion)
    │  └─ Recursively rewrite expanded queries
    └─ Apply row-level security policies [rowsecurity.c]
      ├─ SELECT policies → added to WHERE clause
      ├─ INSERT policies → added to WITH CHECK clause
      ├─ UPDATE policies → added to WHERE clause
      └─ DELETE policies → added to WHERE clause

**Data Structure:** `List<Query>` (may contain multiple Query nodes if rules expand query)

### 5. Planning Stage (Two-Phase Optimization)
**Calls:** `src/backend/tcop/postgres.c:1192` (pg_plan_queries)
  → `pg_plan_query()` [src/backend/tcop/postgres.c:882]
    → `planner()` [src/backend/optimizer/plan/planner.c:287]
      → `standard_planner()` [src/backend/optimizer/plan/planner.c:303]
        ├─ Initialize PlannerGlobal and PlannerInfo structures
        ├─ **PHASE 1: Path Generation** [allpaths.c]
        │  ├─ `planner_recurse_rel()` — Process each relation
        │  ├─ `add_paths_to_rel()` — Generate access paths for single relation
        │  │  ├─ Sequential scan path
        │  │  ├─ Index scan paths (for each available index)
        │  │  └─ Bitmap scan paths (combination of index scans)
        │  ├─ `make_join_rel()` — Generate paths for relation pairs
        │  │  ├─ Nested loop paths
        │  │  ├─ Hash join paths (with hash build)
        │  │  └─ Merge join paths (with sort if needed)
        │  ├─ `add_upper_paths_to_rel()` — Paths for aggregate/group by/window
        │  └─ `get_cheapest_path()` — Identify cheapest path per relation
        │
        ├─ **PHASE 2: Plan Creation** [createplan.c]
        │  ├─ `fetch_upper_rel()` — Get final relation with all paths
        │  ├─ `get_cheapest_fractional_path()` — Select best path for tuple_fraction
        │  └─ `create_plan()` [src/backend/optimizer/plan/createplan.c:337]
        │     ├─ Recursively converts Path tree to Plan tree
        │     ├─ `create_seqscan_plan()` → SeqScan node
        │     ├─ `create_indexscan_plan()` → IndexScan node
        │     ├─ `create_nestloop_plan()` → NestLoop node
        │     ├─ `create_mergejoin_plan()` → MergeJoin node
        │     ├─ `create_hashjoin_plan()` → HashJoin node
        │     ├─ `create_agg_plan()` → Agg node
        │     ├─ `create_sort_plan()` → Sort node
        │     └─ [Creates all other node types]
        │
        └─ Post-planning optimization
           ├─ `set_plan_references()` — Resolve Var nodes to plan column indices
           ├─ `SS_finalize_plan()` — Parameter handling
           └─ Generate PlannedStmt wrapper

**Data Structure:** `PlannedStmt` containing:
- `type` — T_PlannedStmt
- `plan` — Root Plan node (recursive tree structure)
- `rtable` — Final range table
- `resultRelations` — Indices of modifiable relations
- `planTree` — The executable plan tree
- `subplans` — Subplan list for initplans, CTEs
- `paramExecTypes` — Types of execution-time parameters
- `canSetTag`, `commandType` — Command metadata

**Key Path Nodes:** RelOptInfo, Path, AccessPath, JoinPath, UpperPath
**Key Plan Nodes:** SeqScan, IndexScan, NestLoop, MergeJoin, HashJoin, Agg, Sort, Gather, etc.

### 6. Execution Stage (Volcano-Style Iterator Model)
**Calls:** `src/backend/tcop/pquery.c:685` (PortalRun)
  → `ExecutorStart()` [src/backend/executor/execMain.c]
    → `InitPlan()` → `ExecInitNode()` [src/backend/executor/execProcnode.c:142]
      ```
      ExecInitNode(Plan *node) — Switch statement dispatch on nodeTag(node)
        case T_Result:     ExecInitResult()
        case T_SeqScan:    ExecInitSeqScan()
        case T_IndexScan:  ExecInitIndexScan()
        case T_NestLoop:   ExecInitNestLoop()
        case T_MergeJoin:  ExecInitMergeJoin()
        case T_HashJoin:   ExecInitHashJoin()
        case T_Agg:        ExecInitAgg()
        case T_Sort:       ExecInitSort()
        case T_Hash:       ExecInitHash()
        ... [48+ total node types]

      Each ExecInit<NodeType>() function:
        ├─ Allocates node-specific state structure (ResultState, SeqScanState, etc.)
        ├─ Sets up ExecProcNode function pointer via ExecSetExecProcNode()
        ├─ Initializes expression evaluation (JIT, JMH)
        └─ Recursively calls ExecInitNode() on child nodes (lefttree, righttree)

      Result: PlanState tree (mirrors Plan tree structure) with function pointers
      ```

  → `ExecutorRun()` [src/backend/executor/execMain.c:297]
    → `ExecutePlan()` [src/backend/executor/execMain.c:1660]
      ```
      Execution Loop: for each tuple needed {
        result = ExecProcNode(root_plan_state);
        ├─ Dynamic dispatch via PlanState.ExecProcNode function pointer
        ├─ First call triggers ExecProcNodeFirst() for stack depth check
        │  └─ Replaces wrapper with real function on first execution
        ├─ Optional instrumentation wrapper (ExecProcNodeInstr) for EXPLAIN ANALYZE
        └─ Calls actual node executor function:
           ├─ ExecSeqScan() — Retrieves next tuple from sequential scan
           │  └─ Calls heap_getnext() via table AM interface
           ├─ ExecIndexScan() — Retrieves tuple from index + heap
           ├─ ExecNestLoop() — Outer/inner tuple combination
           │  ├─ Calls ExecProcNode(outerPlan) for outer tuple
           │  ├─ For each outer tuple, calls ExecProcNode(innerPlan)
           │  └─ Evaluates join condition (qual)
           ├─ ExecMergeJoin() — Sorted stream merging
           ├─ ExecHashJoin() — Hash table lookup
           │  ├─ ExecHashTableCreate() — Build phase
           │  └─ Probe phase via hash table lookup
           ├─ ExecAgg() — Aggregate accumulation
           ├─ ExecSort() — Tuple materialization + sort
           └─ [40+ node executor functions]

        Process tuple:
          ├─ Apply expression evaluation (WHERE clauses, projections)
          ├─ Send to DestReceiver for output
          └─ Return to caller
      }
      ```

  → `ExecutorFinish()` [src/backend/executor/execMain.c]
    → `ExecEndNode()` [src/backend/executor/execProcnode.c:562]
      → Cleanup dispatch:
         ```
         Switch on nodeTag(state->plan):
           case T_Result:     ExecEndResult()
           case T_SeqScan:    ExecEndSeqScan()
           ... [all node types]

         Each ExecEnd<NodeType>() function:
           ├─ Releases scan descriptors
           ├─ Frees state-specific memory
           ├─ Recursively calls ExecEndNode() on children
           └─ Cleans up tuple slots
         ```

  → `ExecutorEnd()` [src/backend/executor/execMain.c]
    → Final cleanup and resource release

**Key Data Structures:**

**PlanState** (execnodes.h):
```c
typedef struct PlanState {
  NodeTag type;
  Plan *plan;                    /* Associated Plan node */
  EState *state;                 /* Execution state */
  ExecProcNodeMtd ExecProcNode;  /* Dispatch function pointer (may be wrapper) */
  ExecProcNodeMtd ExecProcNodeReal; /* Actual executor function */
  Instrumentation *instrument;   /* Performance monitoring */
  ExprState *qual;               /* WHERE clause evaluation state */
  struct PlanState *lefttree;    /* Child node state */
  struct PlanState *righttree;   /* Child node state */
} PlanState;
```

**TupleTableSlot** — Runtime tuple container with:
- `tts_values[]` — Datum values
- `tts_isnull[]` — NULL flags
- `tts_tuple` — Heap tuple pointer (if materialized)
- Methods for access and materialization

---

## Analysis

### Overall Design Philosophy

PostgreSQL implements a **classic five-stage query execution pipeline**:

1. **Parser**: Lexical + syntactic analysis (flex + bison) → RawStmt
2. **Semantic Analyzer**: Name/type resolution → Query
3. **Rewriter**: Rule expansion, RLS policies → Query list
4. **Optimizer**: Two-phase cost-based optimization → PlannedStmt
5. **Executor**: Volcano-style iterator model → result tuples

Each stage produces **immutable, reusable data structures** passed to the next stage, enabling modular upgrades and plugin hooks.

### Key Design Patterns

#### 1. **Separation of Concerns**
- **Parser** avoids database access (grammar is purely syntactic)
- **Analyzer** performs all semantic validation and type checking
- **Rewriter** handles rule and policy expansion
- **Optimizer** makes planning decisions independently
- **Executor** executes without planning concerns

This separation allows each phase to be tested and optimized independently.

#### 2. **Two-Phase Cost-Based Optimization**
```
Phase 1 (Pathfinding):
  - Generates ALL feasible access paths
  - Each path has:
    * startup_cost — cost before first tuple
    * total_cost — cost for all tuples
    * rows — estimated output rows
    * width — average tuple width
  - For each relation: selects cheapest path per ordering requirement
  - For joins: generates paths for all interesting join orders

Phase 2 (Plan Creation):
  - Selects single cheapest path from final relation
  - Converts Path tree → Plan tree
  - Path is cost-based abstract decision tree
  - Plan is executable instruction sequence
```

**Advantages of separation:**
- Paths are lightweight, don't contain execution details
- Planner can explore many paths without overhead
- Plan creation is straightforward conversion
- Easy to add new path types (e.g., for new index types)

#### 3. **Volcano-Style Iterators with Function Pointer Dispatch**

```c
/* Each executor node has function pointer dispatch */
struct PlanState {
  ExecProcNodeMtd ExecProcNode;      /* Points to real function after first call */
  ExecProcNodeMtd ExecProcNodeReal;  /* The actual node executor */
  // ...
};

/* Wrapper pattern for lazy initialization and instrumentation */
ExecProcNodeFirst()  /* First call: stack check, replace wrapper */
  → ExecProcNodeInstr() (if instrumentation) or ExecProcNodeReal()
    → Actual node function (ExecSeqScan, ExecNestLoop, etc.)
```

**Volcano Model Characteristics:**
- Each node executor implements pull-based interface
- `ExecProcNode(state)` returns next tuple on each call
- Recursively calls `ExecProcNode()` on children
- Enables pipelined execution (no full materialization)
- Clean separation of concerns

#### 4. **Node Type Dispatch Patterns**

**Initialization Dispatch** (ExecInitNode):
- Switch statement on `nodeTag(plan)` (48+ cases)
- Each case calls `ExecInit<NodeType>()` which:
  - Allocates state structure
  - Sets up function pointers
  - Initializes child nodes recursively

**Execution Dispatch** (ExecProcNode):
- Dynamic method dispatch via function pointer
- Each PlanState has `ExecProcNode` pointing to node-specific executor
- Indirect call enables:
  - Wrapper instrumentation without code duplication
  - Deferred stack depth checks
  - Easy optimization (JIT code replacement)

**Cleanup Dispatch** (ExecEndNode):
- Similar switch dispatch as initialization
- Each case calls `ExecEnd<NodeType>()` for cleanup

#### 5. **Expression Evaluation**

```
Expression nodes (Expr, OpExpr, FuncExpr, etc.)
  → compile-time: ExprState creation (execExpr.c)
  → runtime: Expression interpreter (execExprInterp.c)
  → OR JIT compilation to native code (jit/)
```

Expressions are pre-compiled to ExprState on node initialization, then rapidly evaluated at execution time.

#### 6. **Data Structure Transformations Along Pipeline**

```
SQL String (const char *)
  ↓ Parser
RawStmt { stmt: Node*, stmt_location, stmt_len }
  ↓ Analyzer
Query { commandType, rtable, targetList, whereClause, ... }
  ↓ Rewriter
List<Query> (may expand due to rules)
  ↓ Planner
PlannedStmt { plan: Plan*, rtable, subplans, ... }
  → Plan Tree { SeqScan/IndexScan/Join/Agg/... }
  ↓ Executor
PlanState Tree { ExecProcNode function pointers }
  → TupleTableSlot (repeated)
  ↓ Results
Client Protocol (RowDescription, DataRow, CommandComplete)
```

### Component Responsibilities

**Traffic Cop (postgres.c)**
- Entry point for all queries
- Manages transaction and memory contexts
- Coordinates pipeline stages
- Handles multiple queries in one message
- Implements error recovery

**Parser (gram.y, scan.l)**
- Tokenization and syntax analysis
- No database access
- Produces RawStmt minimally informative of semantics
- Recovers from syntax errors with error recovery

**Analyzer (analyze.c)**
- Name resolution (table, column, function names)
- Type inference and coercion
- Semantic validation
- Privilege checking
- Builds Query with all metadata resolved

**Rewriter (rewriteHandler.c)**
- Applies ON SELECT/INSERT/UPDATE/DELETE rules
- Applies row-level security policies
- Handles recursive rule expansion with cycle detection
- May expand single query to multiple

**Planner (planner.c, allpaths.c, createplan.c)**
- Cost-based optimization
- Estimates rows and costs
- Generates alternative access paths
- Selects cheapest execution plan
- Handles parallel execution planning

**Executor (execMain.c, execProcnode.c, node*.c)**
- Initializes plan state tree
- Drives tuple iteration
- Evaluates expressions
- Manages memory and resources
- Implements node-specific semantics

**Portal (pquery.c)**
- Manages named/unnamed statement cache
- Controls fetch direction and count
- Manages result format

### Interface Contracts Between Stages

| From | To | Data | Key Functions |
|------|----|----|---|
| Traffic Cop | Parser | SQL string | `pg_parse_query()` → RawStmt list |
| Parser | Analyzer | RawStmt | `parse_analyze_fixedparams()` → Query |
| Analyzer | Rewriter | Query | `pg_rewrite_query()` → Query list |
| Rewriter | Planner | Query list | `pg_plan_queries()` → PlannedStmt list |
| Planner | Executor | PlannedStmt | `PortalRun()` → tuples to DestReceiver |
| Executor | Output | TupleTableSlot | Client protocol (network) |

### Critical Design Insights

1. **Immutable Data Structures**: Each pipeline stage produces new structures without modifying inputs, enabling caching and replay.

2. **Lazy Evaluation**: Expression evaluation deferred until execution time, not during planning.

3. **Extensibility Points**:
   - `planner_hook` — Replace entire planner
   - `post_parse_analyze_hook` — Plugin into analyzer
   - Custom scan types (ForeignScan, CustomScan)
   - Per-node instrumentation hooks

4. **Cost Model**: All planning decisions based on:
   - Cost estimates (CPU, I/O)
   - Row count estimates
   - Memory constraints

5. **Memory Management**: Each pipeline stage and executor node allocates in isolated MemoryContext, enabling efficient cleanup on error or statement completion.

---

## Summary

PostgreSQL implements a **classic five-stage query execution architecture** with clear separation of concerns: syntactic parsing (gram.y + scan.l), semantic analysis (analyze.c), rule rewriting (rewriteHandler.c), cost-based optimization (planner.c + allpaths.c + createplan.c with two-phase path generation and plan creation), and **Volcano-style iterator execution** (execProcnode.c with dynamic function pointer dispatch). Data flows through immutable intermediate structures (RawStmt → Query → PlannedStmt) enabling modular testing, plugin hooks, and plan caching. The executor implements pull-based pipelined execution with recursive node dispatch, where each PlanState node contains a function pointer dynamically set to its node-specific executor (ExecSeqScan, ExecNestLoop, etc.), enabling transparent wrapper instrumentation and future JIT optimization.

---

## Detailed References

### Key Function Call Paths

**Simple Query Execution**:
```
exec_simple_query()
  → pg_parse_query()
    → raw_parser() [gram.y, scan.l]
    ← RawStmt list
  → pg_analyze_and_rewrite_fixedparams()
    → parse_analyze_fixedparams() [analyze.c:105]
      → transformTopLevelStmt() [analyze.c:249]
      ← Query
    → pg_rewrite_query()
      → QueryRewrite() [rewriteHandler.c:4566]
      ← Query list
  → pg_plan_queries()
    → pg_plan_query() for each query
      → planner() [planner.c:287]
        → standard_planner() [planner.c:303]
          → planner_recurse_rel() [allpaths.c] — Path generation Phase 1
          → create_plan() [createplan.c:337] — Plan creation Phase 2
        ← PlannedStmt
  → PortalRun()
    → ExecutorStart()
      → ExecInitNode() [execProcnode.c:142] — Switch dispatch initialization
    → ExecutorRun()
      → ExecutePlan() [execMain.c:1660] — Execution loop
        → ExecProcNode() [dynamic dispatch via function pointer]
    → ExecutorFinish()
    → ExecutorEnd()
      → ExecEndNode() [execProcnode.c:562] — Switch dispatch cleanup
```

### Node Type Categories in Executor

**Scan Nodes** (access tables/indexes):
- SeqScan, IndexScan, IndexOnlyScan, BitmapHeapScan, TidScan, FunctionScan, SubqueryScan, CteScan

**Join Nodes** (combine relation inputs):
- NestLoop, MergeJoin, HashJoin

**Aggregate Nodes** (reduce rows):
- Agg, Group, WindowAgg

**Materialization Nodes** (reorder or buffer):
- Sort, Material, Memoize

**Modification Nodes** (INSERT/UPDATE/DELETE):
- ModifyTable, LockRows

**Control Nodes** (control flow):
- Result, ProjectSet, Append, MergeAppend, RecursiveUnion

**Special Nodes** (optimization):
- Gather, GatherMerge, Hash, SetOp, Limit

### Optimizer Path Types

```
RelOptInfo.pathlist contains:
  - SeqScanPath — Sequential scan of all rows
  - IndexPath — Single index scan
  - BitmapHeapPath — Multiple indexes combined with bitmaps
  - NestPath — Nested loop join
  - MergePath — Merge join
  - HashPath — Hash join
  - AppendPath — UNION
  - MaterializePath — Force materialization
  - UniquePath — Remove duplicates
  - GroupPath — GROUP BY without aggregation
  - UpperUniquePath, GroupUpperPath, AggPath, WindowAggPath — Upper relations
```

Each path contains cost estimates and can be converted to corresponding Plan node.
