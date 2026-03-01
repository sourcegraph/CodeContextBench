# PostgreSQL Query Execution Pipeline Analysis

## Files Examined

### Traffic Cop (Entry Point)
- `src/backend/tcop/postgres.c` — Main entry point via `exec_simple_query()`, coordinates the entire query execution pipeline
- `src/backend/tcop/pquery.c` — Portal execution logic via `PortalRun()`, bridges planning and execution phases

### Parser Subsystem
- `src/backend/parser/parser.c` — `raw_parser()` orchestrates lexical/grammatical analysis using flex/bison
- `src/backend/parser/gram.y` — Bison grammar specification (generated as gram.c)
- `src/backend/parser/scan.l` — Flex lexer specification (generated as scan.c)

### Semantic Analyzer Subsystem
- `src/backend/parser/analyze.c` — `parse_analyze_fixedparams()` transforms RawStmt → Query via `transformTopLevelStmt()`
- `src/backend/parser/parse_type.c` — Type resolution during semantic analysis
- `src/backend/rewrite/rewriteHandler.c` — `QueryRewrite()` applies view/rule transformations

### Query Rewriter
- `src/backend/rewrite/rewriteDefine.c` — Rule definition and application
- `src/include/rewrite/rewriteHandler.h` — Rewriter interface definitions

### Optimizer/Planner Subsystem
- `src/backend/optimizer/plan/planner.c` — Entry point `planner()` and `standard_planner()`, orchestrates optimization phases
- `src/backend/optimizer/plan/planmain.c` — `query_planner()` handles basic join planning
- `src/backend/optimizer/path/allpaths.c` — Path generation phase (Paths for baserels, joins, upper operations)
- `src/backend/optimizer/plan/createplan.c` — Plan creation phase (converts best Path to Plan tree)
- `src/backend/optimizer/util/pathnode.c` — Path structure creation and management

### Executor Subsystem
- `src/backend/executor/execMain.c` — `ExecutorStart()`, `ExecutorRun()`, `ExecutorEnd()` main executor lifecycle
- `src/backend/executor/execProcnode.c` — `ExecInitNode()`, `ExecProcNode()`, `ExecEndNode()` dispatch routines (Volcano-style)
- `src/backend/executor/nodeSeqscan.c` — Sequential scan node example
- `src/backend/executor/nodeNestloop.c` — Nested loop join example
- `src/backend/executor/nodeSort.c` — Sort node example

### Data Structure Definitions
- `src/include/nodes/parsenodes.h` — Parse tree node definitions (SelectStmt, InsertStmt, Query, etc.)
- `src/include/nodes/plannodes.h` — Plan node definitions (SeqScan, NestLoop, Sort, etc.)
- `src/include/nodes/pathnodes.h` — Optimizer structures (Path, RelOptInfo, PlannerInfo, etc.)
- `src/include/nodes/execnodes.h` — Executor state structures (PlanState, EState, ScanState, etc.)
- `src/include/nodes/primnodes.h` — Primitive expression nodes (Var, Const, OpExpr, etc.)

### Node Base Infrastructure
- `src/backend/nodes/outfuncs.c` — Serialization of node trees
- `src/backend/nodes/readfuncs.c` — Deserialization of node trees
- `src/backend/nodes/copyfuncs.c` — Deep copying of node trees
- `src/backend/nodes/equalfuncs.c` — Equality comparison of node trees

---

## Dependency Chain

### 1. Entry Point: Traffic Cop Layer

**Function**: `exec_simple_query(const char *query_string)` in `postgres.c:1010`

**Purpose**: Main query processing loop that dispatches a SQL string through the entire pipeline.

**Key Actions**:
- Calls `pg_parse_query(query_string)` to parse the query string
- Processes each RawStmt through subsequent pipeline stages
- Creates Portal and coordinates execution

---

### 2. Parser Stage: Lexical + Grammatical Analysis

**Functions**:
- `pg_parse_query()` in `postgres.c:602`
- `raw_parser(str, RAW_PARSE_DEFAULT)` in `parser.c:41`

**Data Flow**: `const char* query_string` → `List<RawStmt>`

**Process**:
```
1. scanner_init(query, &yyextra.core_yy_extra, &ScanKeywords, ScanKeywordTokens)
   - Initializes flex scanner with the input string
   - Creates YYSCAN_T scanner state

2. parser_init(&yyextra)
   - Initializes bison parser state

3. base_yyparse(yyscanner)
   - Runs bison parser which consumes tokens from flex scanner
   - Uses flex (lexer) to tokenize the input string character-by-character
   - Matches tokens against grammar rules defined in gram.y
   - Reduces grammar rules to build AST nodes

4. scanner_finish(yyscanner)
   - Cleans up lexer resources
```

**Output Structures**:
- `RawStmt`: Minimal parse tree node containing:
  - `Node *stmt`: The actual statement (SelectStmt, InsertStmt, UpdateStmt, DeleteStmt, etc.)
  - `int stmt_location`: Character offset in query string
  - `int stmt_len`: Length of statement text

**Design Pattern**: Separation of concerns between lexical analysis (flex) and grammatical analysis (bison). Both handle a single raw parse tree without semantic meaning.

---

### 3. Semantic Analyzer Stage

**Functions**:
- `pg_analyze_and_rewrite_fixedparams(RawStmt, query_string, paramTypes, numParams, queryEnv)` in `postgres.c:664`
- `parse_analyze_fixedparams(RawStmt, sourceText, paramTypes, numParams, queryEnv)` in `analyze.c:104`
- `transformTopLevelStmt(ParseState, RawStmt)` in `analyze.c:248`

**Data Flow**: `RawStmt` → `Query`

**Process**:
```
1. Create ParseState via make_parsestate()
   - Initializes parsing context with source text
   - Sets up parameter types if provided
   - Creates memory context for intermediate structures

2. Call transformTopLevelStmt(pstate, RawStmt->stmt)
   - Dispatches to specific transform function based on statement type:
     * transformSelectStmt() for SELECT
     * transformInsertStmt() for INSERT
     * transformUpdateStmt() for UPDATE
     * transformDeleteStmt() for DELETE
     * etc.

   - Each transform function:
     * Validates semantic constraints (e.g., column references exist)
     * Resolves column names to Vars (variable references)
     * Resolves function names to FuncExprs
     * Type-checks expressions
     * Handles subqueries recursively
     * Builds targetlist (output columns)
     * Analyzes WHERE/JOIN/GROUP BY/HAVING clauses
     * Builds final Query structure

3. Return Query object
   - Represents semantically valid, analyzed query
   - Contains resolved references, type information, optimizable operators
```

**Output Structures**:
- `Query`: Complete query representation with:
  - `CmdType commandType`: SELECT, INSERT, UPDATE, DELETE, UTILITY
  - `List *rtable`: Range table (FROM clause relations)
  - `List *targetList`: Target list (output columns)
  - `Node *whereClause`: WHERE clause expression tree
  - `List *groupClause`: GROUP BY clause
  - `Node *havingClause`: HAVING clause
  - `List *sortClause`: ORDER BY clause
  - `List *windowClause`: WINDOW definitions
  - Subquery list, CTE list, and other clause information

**Design Pattern**: Recursive descent parser for semantic analysis. Each transform function validates and builds portions of the Query tree. Subqueries are recursively analyzed.

---

### 4. Query Rewriter Stage

**Functions**:
- `pg_rewrite_query(Query)` in `postgres.c:797`
- `QueryRewrite(Query)` in `rewriteHandler.c:4566`

**Data Flow**: `Query` → `List<Query>`

**Process**:
```
1. Check if query is a utility command (CREATE TABLE, DROP, etc.)
   - If yes: Return query unchanged in a list (utilities skip rewriting)

2. For non-utility queries, call QueryRewrite(query)
   - Acquires locks on relations referenced in query
   - Finds applicable rules (views, INSTEAD rules, etc.)
   - For each rule:
     * Substitutes rule action into query
     * Creates new Query node with substituted components
     * Handles multiple rules by creating multiple Query nodes

   - Can generate 0+ Query nodes from a single input Query
     * 0: Query failed rule check
     * 1: Normal case, possibly with substituted view definitions
     * N>1: Multiple unconditional INSTEAD rules applied
```

**Output Structures**:
- `List<Query>`: List of (possibly rewritten) Query nodes
- Each Query has:
  - Substituted subqueries for views
  - Applied INSTEAD rule transformations
  - Still pre-optimization state (not yet a Plan)

**Design Pattern**: Rule system that transforms queries by substitution. Maintains semantic equivalence while allowing custom query transformations through rules.

---

### 5. Optimizer/Planner Stage: Path Generation Phase

**Functions**:
- `pg_plan_queries(List<Query>, query_string, cursorOptions, boundParams)` in `postgres.c:969`
- `pg_plan_query(Query, query_string, cursorOptions, boundParams)` in `postgres.c:881`
- `planner(Query, query_string, cursorOptions, boundParams)` in `planner.c:286`
- `standard_planner(Query, query_string, cursorOptions, boundParams)` in `planner.c:302`
- `subquery_planner(PlannerGlobal, Query, PlannerInfo*, ...)` in `planner.c:650`

**Data Flow**: `Query` → **Phase 1** → `RelOptInfo + List<Path>` → **Phase 2** → `Plan`

**Process - Phase 1 (Path Generation via allpaths.c)**:
```
1. standard_planner() initializes:
   - PlannerGlobal: Global state for entire plan
     * boundParams: External parameters
     * subplans: List of subplans for subqueries
     * relationOids: Relations used in query
     * etc.

2. Call subquery_planner(glob, query, ...)
   - Handles subquery and CTE recursion
   - Pre-processes query tree:
     * Simplifies expressions
     * Removes unnecessary subqueries
     * Handles CTEs (Common Table Expressions)
     * Validates query structure

   - Builds RelOptInfo tree for baserels (base relations):
     * For each table in FROM clause:
       - Creates RelOptInfo with:
         * Relation metadata
         * Estimated row count
         * Width estimate
         * List of usable indexes

   - Generates Paths for baserels via allpaths.c:
     * SeqScanPath: Sequential scan
     * IndexPath: Index scan using various index types
     * BitmapPath: Bitmap index scan
     * CustomPath: Extension-provided paths
     * For each Path:
       - Estimated startup_cost
       - Estimated total_cost
       - Estimated rows

   - Handles join operations:
     * Enumerates join orders (using dynamic programming or brute force)
     * For each join combination:
       - Generates NestLoopPath
       - Generates HashJoinPath (if allowed)
       - Generates MergejoinPath (if allowed)
     * Each path alternative with different cost estimates

   - Handles upper-level operations:
     * GROUP BY aggregation
     * Sorting (ORDER BY)
     * Windowing functions
     * Set operations (UNION, INTERSECT)
     * Limit clauses
     * Each creates upper RelOptInfo with multiple Paths

3. Returns PlannerInfo with:
   - Complete RelOptInfo tree
   - All candidate Paths at each level
   - Cost estimates for all alternatives
```

**Output Structures**:
- `Path` (abstract base):
  - `RelOptInfo *parent`: The RelOptInfo this path belongs to
  - `PathType type`: T_SeqScan, T_IndexScan, T_NestLoop, T_HashJoin, etc.
  - `Cost startup_cost`: Cost before first tuple
  - `Cost total_cost`: Cost for all tuples
  - `List *pathkeys`: Sort order of output tuples
  - `int rows`: Estimated number of output rows

- `RelOptInfo`: Represents a relation or relation join
  - `Relids relids`: Set of baserel indexes in this relation
  - `List *pathlist`: List of Path candidates
  - `List *join_pathlist`: Join paths (for join relations)
  - `double rows`: Estimated row count
  - `double width`: Estimated average row width

- `PlannerInfo`: Per-query planner context
  - `Query *parse`: Input Query
  - `PlannerGlobal *glob`: Global state
  - `RelOptInfo **simple_rel_array`: Array of baserels
  - `List *join_rel_list`: All join relations found
  - `RelOptInfo *root_rel`: Final result relation

**Design Pattern**: Generate-and-test approach. Creates all feasible execution paths with cost estimates, allowing optimizer to select best path based on costs.

---

### 5b. Optimizer/Planner Stage: Plan Creation Phase

**Functions**:
- `create_plan(PlannerInfo, Path)` in `createplan.c`
- `create_seqscan_plan()`, `create_indexscan_plan()`, etc.

**Data Flow**: `Path` → `Plan`

**Process - Phase 2 (Plan Conversion via createplan.c)**:
```
1. Select best Path via get_cheapest_fractional_path()
   - From final RelOptInfo (UPPERREL_FINAL)
   - Chooses Path with lowest total_cost
   - May optimize for partial result if cursor fetch

2. Recursively convert best Path to Plan:
   - For SeqScanPath:
     * Creates SeqScan Plan node
     * Sets targetlist, qual conditions

   - For IndexPath:
     * Creates IndexScan or IndexOnlyScan Plan
     * Determines which index clauses to use
     * Stores index oid and scan direction

   - For NestLoopPath:
     * Creates NestLoop Plan node
     * Recursively converts outer and inner Paths to Plans
     * Adds join conditions and filter conditions

   - For HashJoinPath/MergejoinPath:
     * Similar recursive conversion
     * Adds hash/merge-specific operators

   - For upper-level Paths:
     * Converts aggregation Paths to Agg Plans
     * Converts sort Paths to Sort Plans
     * Converts limit Paths to Limit Plans
     * etc.

3. Post-processing:
   - Assigns unique node IDs to each Plan node
   - Handles parameter assignments (ParamExec)
   - Applies subplan initialization
```

**Output Structures**:
- `Plan` (abstract base):
  - `NodeType type`: T_SeqScan, T_IndexScan, T_NestLoop, etc.
  - `Plan *lefttree, *righttree`: Child plans (for joins)
  - `List *initPlan`: Init plans (subqueries)
  - `List *targetlist`: Output columns
  - `List *qual`: Filter conditions
  - `int plan_node_id`: Unique ID within plan tree
  - `int total_cost, startup_cost`: Cost estimates
  - `int plan_rows`: Expected output rows
  - `int plan_width`: Expected average row width

- `SeqScan(Plan)`: Sequential scan plan
  - `Oid scanrelid`: OID of table to scan

- `IndexScan(Plan)`: Index scan plan
  - `Oid indexid`: OID of index
  - `List *indexquals`: Conditions on index keys
  - `ScanDirection direction`: Forward/backward

- `NestLoop(Plan)`: Nested loop join plan
  - `List *nestLoopPlan`: Join conditions
  - Left/right plans for outer/inner relations

- `Sort(Plan)`: Sort operation
  - `int numCols`: Number of sort keys
  - `AttrNumber *sortColIdx`: Column positions
  - `Oid *sortOperators`: Sort operators (ascending/descending)

- `PlannedStmt`: Top-level container
  - `Plan *planTree`: Root of plan tree
  - `List *rtable`: Range table (table references)
  - `List *commandType`: Type of command
  - `Oid queryId`: Query ID for tracking

**Design Pattern**: Tree-structured plan mirroring the Path structure. Each Plan node contains child Plans and execution instructions. Represents explicit decision tree for query execution.

---

### 6. Executor Stage: Initialization

**Functions**:
- `PortalRun(Portal, count, isTopLevel, dest, altdest, qc)` in `pquery.c:684`
- `ExecutorStart(QueryDesc, eflags)` in `execMain.c:121`
- `standard_ExecutorStart(QueryDesc, eflags)` in `execMain.c:140`
- `ExecInitNode(Plan, EState, eflags)` in `execProcnode.c:141`

**Data Flow**: `PlannedStmt` → `EState + PlanState tree` → Tuple processing

**Process**:
```
1. PortalRun() receives PlannedStmt wrapped in Portal
   - Portal encapsulates query execution context
   - Contains prepared PlannedStmt and parameters

2. ExecutorStart(QueryDesc) called:
   - QueryDesc wraps PlannedStmt + snapshot + destination

3. standard_ExecutorStart() initializes:
   - Creates EState (Executor State)
     * es_query_cxt: Memory context for query execution
     * es_param_list_info: External parameters
     * es_param_exec_vals: Internal parameters
     * es_snapshot: Current snapshot (MVCC)
     * es_instrument: Instrumentation flags

   - Calls ExecInitNode() on Plan tree root
     * Recursively initializes entire Plan tree
     * Creates corresponding PlanState tree
     * Each PlanState node corresponds to one Plan node
     * Each PlanState contains:
       - PlanState *lefttree, *righttree
       - ExecProcNodeMtd ExecProcNode: Function pointer to node-specific executor
       - TupleTableSlot *ps_ResultTupleSlot: Output slot for this node
       - State for node-specific processing (e.g., Sort state, Hash table)

   - Example ExecInitNode() dispatch:
     * Plan is T_SeqScan → calls ExecInitSeqScan()
     * Plan is T_IndexScan → calls ExecInitIndexScan()
     * Plan is T_NestLoop → calls ExecInitNestLoop()
       - Recursively calls ExecInitNode() on left and right child Plans
       - Sets up join state and hash table (if applicable)
     * Plan is T_Sort → calls ExecInitSort()
     * etc.
```

**Output Structures**:
- `EState`: Executor state for entire query
  - `PlanState *es_plannedstmt`: Root PlanState node
  - `Snapshot es_snapshot`: Snapshot for tuple visibility
  - `long es_tuples_returned`: Count of output tuples
  - Memory context and resource information

- `PlanState` (abstract base): Initialized from Plan node
  - `Plan *plan`: Corresponding Plan node
  - `EState *state`: Reference to EState
  - `PlanState *lefttree, *righttree`: Child states
  - `ExecProcNodeMtd ExecProcNode`: Function pointer for tuple generation
  - `TupleTableSlot *ps_ResultTupleSlot`: Output tuple slot
  - Node-specific state (varies by node type)

- `ScanState(PlanState)`: Base for all scan operations
  - `TableScanDesc ss_currentScanDesc`: Heap scan descriptor
  - `IndexScanDesc ss_index_scan_desc`: Index scan descriptor

- `JoinState(PlanState)`: Base for all joins
  - `ExprState *joinqual`: Join condition expression state
  - Join-specific state (e.g., HashJoinTable for hash joins)

**Design Pattern**: One-to-one correspondence between Plan nodes and PlanState nodes. PlanState encapsulates runtime state and function pointers for tuple generation.

---

### 7. Executor Stage: Tuple Processing (Volcano-Style Dispatch)

**Functions**:
- `ExecutorRun(QueryDesc, direction, count, dest)` in `execMain.c`
- `ExecutePlan(EState, PlanState, direction, count, dest)` in `execMain.c`
- `ExecProcNode(PlanState)` in `execProcnode.c` (macro that calls `ps->ExecProcNode(ps)`)

**Data Flow**: Call `ExecProcNode()` repeatedly → Tuple-at-a-time execution

**Process**:
```
1. ExecutorRun() calls ExecutePlan()

2. ExecutePlan() repeatedly calls:
   slot = ExecProcNode(planstate)

   This calls the function pointer stored in planstate->ExecProcNode

   Examples of Volcano-style dispatch:

   - If ps is SeqScanState:
     * ps->ExecProcNode points to ExecSeqScan()
     * ExecSeqScan() reads next tuple from heap
     * Evaluates WHERE clauses
     * Applies projection (targetlist)
     * Returns TupleTableSlot with result tuple

   - If ps is IndexScanState:
     * ps->ExecProcNode points to ExecIndexScan()
     * ExecIndexScan() uses index to fetch next matching tuple
     * Evaluates WHERE clauses not covered by index
     * Returns TupleTableSlot

   - If ps is NestLoopState:
     * ps->ExecProcNode points to ExecNestLoop()
     * ExecNestLoop() implements nested loop algorithm:
       1. Call ExecProcNode(outer_plan_state) to get outer tuple
       2. Inner loop: repeatedly call ExecProcNode(inner_plan_state)
          for each outer tuple
       3. For each inner tuple, evaluate join condition
       4. If matches, evaluate join targetlist
       5. Return combined tuples

   - If ps is SortState:
     * ps->ExecProcNode points to ExecSort()
     * First call accumulates all tuples in memory from child node
     * Sorts them using quicksort/merge-sort
     * Subsequent calls return tuples in sorted order

   - If ps is AggState:
     * ps->ExecProcNode points to ExecAgg()
     * Accumulates groups and aggregates over child node tuples
     * Returns one tuple per group

   - If ps is LimitState:
     * ps->ExecProcNode points to ExecLimit()
     * Returns at most N tuples from child node

3. Each node's ExecProcNode function:
   - Calls ExecProcNode() on child/children nodes recursively
   - Processes tuples from children
   - Applies node-specific operations
   - Returns one tuple per call (or NULL at end)
   - Maintains state between calls (e.g., sort buffer, hash table)

4. When ExecProcNode() returns NULL:
   - Indicates no more tuples available
   - Caller stops and calls ExecEndNode() for cleanup

5. Execution continues until:
   - Reached 'count' tuples, or
   - Child node returns NULL (end of stream)
```

**Output Structures**:
- `TupleTableSlot`: Represents single output tuple
  - `HeapTuple heapTuple`: Actual tuple data
  - `TupleDesc tupleDesc`: Column metadata
  - Various state flags (NULL if empty)

- Each node type's state has additional fields:
  - `SortState`: Sort buffer, state machine for sort
  - `HashJoinState`: Hash table, join state machine
  - `AggState`: Aggregate state per group
  - `WindowAggState`: Window partition buffers
  - etc.

**Design Pattern**: Volcano model (also called Iterator model)
- Pull-based execution
- Each node requests tuples from children via ExecProcNode()
- Enables pipelining and early termination
- No intermediate materialization except where required (Sort, Hash, Window)
- Function pointer dispatch in each PlanState node

---

### 8. Executor Stage: Result Delivery

**Functions**:
- `SendTupleToDestReceiver()` in `destReceiver.c`
- Various DestReceiver implementations

**Data Flow**: `TupleTableSlot` → Network/Output

**Process**:
```
1. ExecutePlan() receives TupleTableSlot from ExecProcNode()

2. For each non-NULL slot:
   - Calls receiver->receiveSlot(slot, receiver)
   - DestReceiver converts tuple to appropriate format:
     * DestRemote: PostgreSQL wire protocol
     * DestFile: COPY TO output
     * DestSPI: Store in SPI result buffer
     * etc.
   - Sends to client/output

3. Loop until end of tuples or limit reached

4. Calls receiver->rShutdown(receiver) for cleanup
```

**Design Pattern**: Strategy pattern for result delivery. Pluggable DestReceiver implementations allow same plan to output to different destinations without change to executor code.

---

### 9. Executor Cleanup

**Functions**:
- `ExecutorEnd(QueryDesc)` in `execMain.c`
- `ExecEndNode(PlanState)` in `execProcnode.c`

**Process**:
```
1. ExecutorEnd() calls ExecEndNode() on root PlanState

2. ExecEndNode() recursively cleans up entire tree:
   - For each node type:
     * Calls node-specific cleanup function (ExecEndSeqScan, ExecEndSort, etc.)
     * Recursively calls ExecEndNode() on child states
     * Releases node-specific resources:
       - Sort buffers
       - Hash tables
       - Index scan descriptors
       - Subplan results

3. Returns memory to context for reuse
```

---

## Analysis

### Design Patterns Identified

#### 1. **Separation of Concerns**
The query pipeline strictly separates concerns across subsystems:
- **Parser**: Only lexical/grammatical structure (no semantics)
- **Analyzer**: Semantic resolution (no optimization)
- **Rewriter**: Query transformation (no cost-based decisions)
- **Planner**: Cost-based decision making (no execution)
- **Executor**: Tuple processing (no planning decisions)

This separation allows each component to be independently tested, maintained, and improved.

#### 2. **Visitor/Dispatch Pattern**
Used throughout:
- **Parser**: Grammar rules dispatch to reduction functions
- **Analyzer**: transformTopLevelStmt() dispatches to statement-specific analyzers
- **Executor**: ExecProcNode function pointers dispatch to node-specific execution functions

#### 3. **Tree Traversal**
Each stage produces a tree structure:
- Parser: RawStmt tree
- Analyzer: Query expression trees
- Planner: RelOptInfo and Path trees
- Executor: PlanState tree

Each tree is recursively traversed by its corresponding stage.

#### 4. **Pull-Based Execution (Volcano Model)**
The executor uses pull-based execution:
- Each node asks its children for tuples via ExecProcNode()
- Tuples flow "up" the plan tree
- Enables pipelining without intermediate materialization
- Some nodes (Sort, HashJoin) still buffer internally but don't expose it

#### 5. **Generate-and-Test Optimization**
The planner generates multiple candidate execution paths, estimates costs for each, and selects the cheapest:
- Path generation (allpaths.c) creates all feasible paths
- Cost estimation assigns cost to each path
- Selection phase (createplan.c) chooses best path
- Extensible through hooks for custom paths

### Component Responsibilities

| Component | Input | Output | Responsibility |
|-----------|-------|--------|-----------------|
| Parser | SQL string | RawStmt list | Lexical/grammatical analysis |
| Analyzer | RawStmt | Query | Semantic validation, type resolution, name resolution |
| Rewriter | Query | Query list | Apply view/rule transformations |
| Planner | Query | PlannedStmt | Cost-based optimization, path generation, plan creation |
| Executor | PlannedStmt | Tuples | Tuple generation and filtering |

### Data Flow Summary

```
exec_simple_query(query_string)
    ↓
pg_parse_query(query_string)
    ↓ [raw_parser → flex scanner + bison parser]
    ↓
List<RawStmt>
    ↓
pg_analyze_and_rewrite_fixedparams(RawStmt)
    ├─ parse_analyze_fixedparams → transformTopLevelStmt
    │  ↓ [semantic analysis]
    │  Query
    │  ↓
    └─ pg_rewrite_query → QueryRewrite
       ↓ [view/rule substitution]
       List<Query>
           ↓
pg_plan_queries(List<Query>)
    ↓
    For each Query:
        pg_plan_query(Query)
        ├─ planner → standard_planner
        │  ├─ subquery_planner → [Path generation via allpaths.c]
        │  │  ↓
        │  │  RelOptInfo tree + Path candidates
        │  │
        │  └─ create_plan → [Path → Plan conversion via createplan.c]
        │     ↓
        │     Plan tree
        │
        └─ Wrap in PlannedStmt
           ↓
List<PlannedStmt>
    ↓
PortalRun(Portal with PlannedStmt)
    ├─ ExecutorStart(QueryDesc)
    │  ├─ standard_ExecutorStart → CreateExecutorState
    │  └─ ExecInitNode(Plan tree root)
    │     ↓ [Recursive initialization]
    │     PlanState tree
    │
    ├─ ExecutorRun
    │  └─ Loop: slot = ExecProcNode(PlanState)
    │     ↓ [Recursive tuple generation via Volcano dispatch]
    │     TupleTableSlot
    │     └─ Send to DestReceiver
    │
    └─ ExecutorEnd
       └─ ExecEndNode(PlanState tree)
          ↓ [Recursive cleanup]
          Resources released
```

### Two-Phase Optimization

The planner implements a sophisticated two-phase optimization process:

**Phase 1: Path Generation (allpaths.c)**
- Explores the space of feasible execution strategies
- For each base relation: SeqScan, IndexScan, BitmapScan paths
- For each join combination: NestLoop, HashJoin, MergeJoin paths
- For each upper operation: Aggregate, Sort, Limit, Window paths
- Assigns cost estimates to each path
- Maintains list of candidate paths at each level of the RelOptInfo tree

**Phase 2: Plan Creation (createplan.c)**
- Starting from the best path at the top level (UPPERREL_FINAL)
- Recursively converts each best Path to a corresponding Plan node
- Resolves execution details:
  - Which index to use and in what order
  - Hash function for hash joins
  - Sort key ordering
  - Projection and filtering details
- Assigns unique node IDs for plan identification
- Handles special cases like subplans and parameters

This two-phase approach allows the planner to:
1. Efficiently explore large solution spaces (Phase 1)
2. Make detailed execution decisions only for the selected plan (Phase 2)
3. Be extended with new path types without disrupting the overall algorithm

### Volcano-Style Executor Dispatch

The executor implements the Volcano model through function pointers in PlanState nodes:

**Dispatch Mechanism**:
```c
// In execProcnode.c:
// ExecProcNode is a macro:
#define ExecProcNode(ps) ((ps)->ExecProcNode(ps))

// Each PlanState has:
struct PlanState {
    ...
    ExecProcNodeMtd ExecProcNode;  // Function pointer
    ...
};

// ExecProcNodeMtd is defined as:
typedef TupleTableSlot *(*ExecProcNodeMtd)(struct PlanState *pstate);
```

**Dispatch Flow**:
1. Each node type (SeqScan, IndexScan, Sort, etc.) has an Exec* function (ExecSeqScan, ExecIndexScan, ExecSort)
2. During ExecInitNode(), the appropriate Exec* function pointer is stored in PlanState->ExecProcNode
3. During tuple processing, ExecProcNode(ps) macro calls the appropriate function
4. The function:
   - Calls ExecProcNode() on child nodes to get input tuples
   - Processes tuples according to node semantics
   - Returns one output tuple per call
   - Returns NULL when no more tuples available

**Advantages**:
- **Pipelining**: Tuples flow through the tree without intermediate materialization (except where necessary)
- **Early Termination**: Can stop processing when limit reached or client closes connection
- **Memory Efficiency**: Only tuples in transit through the pipeline need to be in memory
- **Flexibility**: Different node implementations can coexist (e.g., different sort algorithms)

**Example Nested Loop Join**:
```
ExecNestLoop(joinstate):
  outer_slot = ExecProcNode(outer_planstate)     // Get next outer tuple
  while outer_slot is not NULL:
    Reset inner_planstate
    inner_slot = ExecProcNode(inner_planstate)    // Get first inner tuple
    while inner_slot is not NULL:
      if join_condition(outer_slot, inner_slot):
        return combined_slot                      // Return joined tuple
      inner_slot = ExecProcNode(inner_planstate)  // Get next inner tuple
    outer_slot = ExecProcNode(outer_planstate)    // Get next outer tuple
  return NULL                                     // No more tuples
```

Each call to ExecNestLoop returns one tuple (or NULL). The caller continues calling until NULL is returned. This allows the caller to control tuple flow and implement LIMIT, early termination, or pipelined processing.

---

## Summary

PostgreSQL's query execution pipeline is a carefully layered architecture that transforms a SQL string through multiple stages of increasing specificity and detail. The parser produces a minimal parse tree, the analyzer adds semantic meaning, the rewriter applies transformations, the planner generates multiple candidate execution strategies and selects the best based on cost estimates, and the executor implements a pull-based pipeline that generates result tuples on demand.

The key architectural insight is the strict separation of concerns: each stage accepts input from the previous stage in a standardized format, performs its specific transformations, and produces output in a standardized format for the next stage. This separation enables independent optimization, testing, and extension of each component. The two-phase planner (path generation then plan creation) enables efficient exploration of large optimization spaces while still making detailed execution decisions. The Volcano-style executor dispatch enables pipelined execution without intermediate materialization, allowing efficient processing of large result sets and early query termination.

