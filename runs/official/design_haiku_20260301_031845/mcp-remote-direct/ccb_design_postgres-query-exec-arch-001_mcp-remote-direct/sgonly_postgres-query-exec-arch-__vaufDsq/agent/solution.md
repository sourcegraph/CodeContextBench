# PostgreSQL Query Execution Pipeline: From Parse to Execute

## Files Examined

### Traffic Cop / Entry Point
- `src/backend/tcop/postgres.c` — Traffic cop main loop; entry point `exec_simple_query()` coordinates all stages of query execution

### Parsing Stage
- `src/backend/parser/scan.l` — Lexical analyzer (automatically generated into scan.c)
- `src/backend/parser/gram.y` — Yacc grammar (automatically generated into gram.c)
- `src/backend/parser/parser.h` — Parser interface defining RawStmt and parsing modes
- `src/backend/parser/analyze.c` — Semantic analyzer: transforms RawStmt → Query

### Rewriting Stage
- `src/backend/rewrite/rewriteMain.c` — Query rewriter: applies view expansions and rule transformations
- `src/include/rewrite/rewriteManip.h` — Rewrite utility functions

### Planning Stage - Phase 1 (Path Generation)
- `src/backend/optimizer/plan/planner.c` — Main planner entry point; orchestrates path generation
- `src/backend/optimizer/plan/planmain.c` — `query_planner()` function that drives path generation
- `src/backend/optimizer/path/allpaths.c` — Path generation for base relations and joins; generates multiple alternative paths with cost estimates
- `src/include/optimizer/paths.h` — Path type definitions and path node creation
- `src/include/nodes/plannodes.h` — PlannedStmt and Plan node structure definitions

### Planning Stage - Phase 2 (Plan Creation)
- `src/backend/optimizer/plan/createplan.c` — Converts best Path to Plan tree recursively
- `src/backend/optimizer/plan/setrefs.c` — Sets up column references in plan nodes
- `src/include/optimizer/planmain.h` — Plan creation interface

### Execution Stage - Initialization & Dispatch
- `src/backend/executor/execProcnode.c` — Node initialization (ExecInitNode) and Volcano-style dispatcher (ExecProcNode function pointers)
- `src/backend/executor/execMain.c` — Main executor loop; calls ExecInitNode, ExecutorRun, ExecEndNode
- `src/include/executor/executor.h` — Executor public interface including ExecProcNode macro

### Node Implementations
- `src/backend/executor/node*.c` — 30+ node type implementations (ExecSeqScan, ExecNestLoop, ExecAgg, etc.)
- Each provides ExecInit{Type}, Exec{Type}, ExecEnd{Type} functions

### Supporting Structures
- `src/include/nodes/execnodes.h` — PlanState and per-node state structures
- `src/include/utils/plancache.h` — CachedPlanSource structure for plan caching
- `src/include/utils/portal.h` — Portal structure for result delivery

---

## Dependency Chain

### 1. Entry Point: exec_simple_query()
**File**: `src/backend/tcop/postgres.c:1010`

```c
static void exec_simple_query(const char *query_string)
```

High-level flow:
1. Calls `pg_parse_query(query_string)` → returns List of RawStmt
2. For each RawStmt:
   - Calls `pg_analyze_and_rewrite_fixedparams(parsetree, ...)` → returns List of Query
   - Calls `pg_plan_queries(querytree_list, ...)` → returns List of PlannedStmt
   - Creates Portal and calls PortalStart, PortalRun to execute

### 2. Stage 1: Raw Parsing
**Function**: `pg_parse_query()`
**File**: `src/backend/tcop/postgres.c:602`

```c
List *pg_parse_query(const char *query_string)
```

- Calls `raw_parser(query_string, RAW_PARSE_DEFAULT)`
- Raw parser uses lexer (scan.l) → tokens; grammar (gram.y) → AST
- Returns: **List of RawStmt nodes** (one per SQL statement in query string)

**Key Data Structure - RawStmt**:
```c
typedef struct RawStmt {
    Node stmt;           // The actual statement node
    int stmt_location;   // Character offset in query string
    int stmt_len;        // Length in query string
}
```

### 3. Stage 2: Semantic Analysis
**Function**: `pg_analyze_and_rewrite_fixedparams()`
**File**: `src/backend/tcop/postgres.c:664`

```c
List *pg_analyze_and_rewrite_fixedparams(RawStmt *parsetree,
    const char *query_string,
    const Oid *paramTypes, int numParams,
    QueryEnvironment *queryEnv)
```

Flow:
1. Calls `parse_analyze_fixedparams(parsetree, ...)` → returns Query
   - **File**: `src/backend/parser/analyze.c:105`
   - Transforms RawStmt → Query with:
     - Table resolution and qualification
     - Type checking and inference
     - Aggregate and window function identification
     - Subquery analysis
   - Acquires table access locks

2. Calls `pg_rewrite_query(query)` → returns List of Query
   - **File**: `src/backend/tcop/postgres.c:797`
   - Applies view rewrites and rule transformations
   - May expand single Query into multiple Query nodes

Returns: **List of Query nodes** (may be 1 or more depending on rewrites)

**Key Data Structure - Query**:
Contains all semantic information: resolved tables, type-checked expressions, constraints, CTEs, etc.

### 4. Stage 3: Path Generation (Phase 1 of Optimization)
**Function**: `pg_plan_queries()` → `pg_plan_query()` → `planner()` → `standard_planner()`
**Files**: `src/backend/tcop/postgres.c` and `src/backend/optimizer/plan/planner.c`

**High-level planner flow** (in standard_planner):
1. Initialize PlannerGlobal (line 322 in planner.c)
   - Bounds parameter types
   - Sets up parallel safety checking

2. Call `subquery_planner(glob, parse, ...)` (line 435)
   - **File**: `src/backend/optimizer/plan/planner.c:650`
   - Creates PlannerInfo structure
   - Preprocessing: pulls up subqueries, removes unnecessary joins
   - Expression preprocessing (constant folding, type coercion)
   - Calls `grouping_planner()` for main query planning

3. In `grouping_planner()` (line 1433):
   - Call `query_planner()` (line 1654)
   - **File**: `src/backend/optimizer/plan/planmain.c:53`
   - **This is where path generation happens**

**Path Generation Details** (query_planner):
- Analyzes query FROM/WHERE/JOIN clauses
- For each table/relation in FROM:
  - Calls functions in `allpaths.c` to generate scan paths:
    - `create_seqscan_path()` — sequential scan
    - `create_index_paths()` — index scans
    - `create_bitmap_scan_path()` — bitmap index scans
    - FDW-specific paths via hooks
  - Each path has cost estimates (startup_cost, total_cost)
- For joins:
  - Enumerates join orderings (using genetic algorithm if > 12 tables)
  - For each ordering, generates join paths:
    - `create_nestloop_path()`
    - `create_hashjoin_path()`
    - `create_mergejoin_path()`
- Generates aggregate/sort/grouping paths if needed
- Returns: **RelOptInfo** containing `pathlist` — multiple Path objects

**Key Data Structures**:
- **Path**: Abstract node representing a physical plan choice with cost
- **RelOptInfo**: Represents a relation in the query; contains list of Paths
- **PlannerInfo**: Context for entire planning process
- **PathTarget**: Description of target columns for a path

All paths for a relation are stored in `RelOptInfo.pathlist` and sorted by cost.

### 5. Stage 4: Plan Creation (Phase 2 of Optimization)
**Function**: `create_plan()`
**File**: `src/backend/optimizer/plan/createplan.c:336`

```c
Plan *create_plan(PlannerInfo *root, Path *best_path)
```

Flow:
1. Selects cheapest/best path from RelOptInfo
2. Recursively converts Path tree to Plan tree:
   - `create_plan_recurse()` dispatches on path type
   - `create_scan_plan()` for scan paths → Scan nodes (SeqScan, IndexScan, etc.)
   - `create_join_plan()` for join paths → Join nodes (NestLoop, HashJoin, etc.)
   - `create_group_plan()`, `create_sort_plan()`, etc. for upper paths
3. Sets up node-specific structures:
   - Qualification expressions (qual)
   - Target list (targetlist)
   - Parameter information
   - Join conditions

Returns: **Plan tree** — tree of Plan nodes ready for execution

**Key Data Structure - Plan**:
```c
typedef struct Plan {
    NodeTag type;           // T_SeqScan, T_NestLoop, etc.
    List *targetlist;       // Columns to output
    List *qual;             // WHERE-like conditions
    Plan *lefttree;         // Left child in tree
    Plan *righttree;        // Right child in tree
    Cost startup_cost;      // Cost before first tuple
    Cost total_cost;        // Total cost
    double plan_rows;       // Estimated result rows
    int plan_width;         // Average row width
    // ... node-specific fields
}
```

### 6. Stage 5: Wrapping in PlannedStmt
**Function**: After plan creation in standard_planner

```c
PlannedStmt *stmt = makeNode(PlannedStmt);
stmt->planTree = top_plan;
stmt->commandType = CMD_SELECT;
// ... set other metadata
```

**Key Data Structure - PlannedStmt**:
```c
typedef struct PlannedStmt {
    NodeTag type;           // Always T_PlannedStmt
    CmdType commandType;    // SELECT, INSERT, UPDATE, DELETE, etc.
    bool canSetTag;         // Can this be assigned to tags?
    Plan *planTree;         // The plan itself
    List *rtable;           // Range table
    List *paramTypes;       // Parameter types for prepared statements
    // ... other metadata for executor
}
```

### 7. Execution Stage 1: Initialization
**Function**: `ExecInitNode()`
**File**: `src/backend/executor/execProcnode.c:141`

```c
PlanState *ExecInitNode(Plan *node, EState *estate, int eflags)
```

Dispatch by node type (big switch statement, line 161):

```c
switch (nodeTag(node)) {
    case T_SeqScan:
        result = (PlanState *) ExecInitSeqScan(...);
        break;
    case T_NestLoop:
        result = (PlanState *) ExecInitNestLoop(...);
        break;
    // ... 30+ node types
}
```

Each node's ExecInit{Type} function:
1. Allocates PlanState structure
2. Initializes node-specific state
3. Recursively initializes child nodes
4. Sets up ExecProcNode function pointer

**Key Data Structure - PlanState**:
```c
typedef struct PlanState {
    NodeTag type;
    Plan *plan;
    EState *state;
    TupleDesc ps_ResultTupleDesc;
    ExecProcNodeMtd ExecProcNode;  // Function pointer
    // ... node-specific state
}
```

### 8. Execution Stage 2: Volcano-Style Tuple Pull
**Macro/Function**: `ExecProcNode()`
**File**: `src/include/executor/executor.h:309`

```c
static inline TupleTableSlot *ExecProcNode(PlanState *node)
{
    if (node->chgParam != NULL)
        ExecReScan(node);
    return node->ExecProcNode(node);  // Call function pointer
}
```

Dispatch via function pointers:
- Each node type has `Exec{Type}()` function
- Example: `ExecSeqScan()` in `nodeSeqscan.c`
- Example: `ExecNestLoop()` in `nodeNestloop.c`

**Volcano Model Details**:
- **Pull Architecture**: Parent nodes pull tuples from children
- **Streaming**: One tuple at a time via TupleTableSlot
- **Stateful**: Node maintains state across multiple ExecProcNode calls
- **Recursive**: Parent calls ExecProcNode(child) to get next tuple

Example nested loop execution:
```c
// In ExecNestLoop():
while ((outerTuple = ExecProcNode(outerPlan)) != NULL) {  // Pull from outer
    ExecReScan(innerPlan);
    while ((innerTuple = ExecProcNode(innerPlan)) != NULL) {  // Pull from inner
        // Evaluate join condition and output
    }
}
```

### 9. Execution Stage 3: Cleanup
**Function**: `ExecEndNode()`
**File**: `src/backend/executor/execProcnode.c`

Similar dispatch structure to ExecInitNode:
- Each node type has ExecEnd{Type}() to free resources
- Recursively calls ExecEndNode on children
- Closes cursors, deallocates memory

---

## Analysis

### Design Patterns Identified

#### 1. Volcano Iterator Model
The executor implements the classic Volcano streaming architecture:
- **Open-Next-Close** interface (implemented via ExecInit/ExecProcNode/ExecEnd)
- **Pull Model**: Parent operators pull tuples on demand from children
- **Tuple-at-a-time**: Flow of single TupleTableSlots up the tree
- **State Preservation**: Node state persists across calls for stateful operators (Sort, HashJoin, Agg)

This enables:
- Efficient memory usage (don't materialize entire intermediate results)
- Natural pipeline parallelism between operators
- Easy integration of new node types

#### 2. Two-Phase Query Optimization

**Phase 1 - Path Generation (allpaths.c)**:
- Multiple alternative physical plans for each relation
- Generate all reasonable combinations of:
  - Scan methods (SeqScan, IndexScan, BitmapScan)
  - Join methods (NestedLoop, HashJoin, MergeJoin)
  - Join orderings
- Each path annotated with cost estimates
- Pruned to keep only promising paths

**Phase 2 - Plan Creation (createplan.c)**:
- Selects cheapest path (sometimes relaxing for robustness)
- Converts Path abstraction to concrete Plan tree
- Optimizes expression evaluation
- Adds projection/filtering nodes
- Parameterization for prepared statements

Benefits:
- Cost-based decision-making deferred until paths fully explored
- Can adjust costs as more information becomes available
- Path costs don't depend on parent's requirements (composable)
- Plan creation handles practical details (column mapping, parameterization)

#### 3. Type-Based Dispatch
Throughout the pipeline, dispatch via NodeTag (typeof system):
- ExecInitNode: switch on Plan node type
- ExecProcNode: function pointers set by ExecInitNode
- Path generation: specialized functions for each path type

This avoids:
- Virtual method tables (not available in C)
- Conditional checks everywhere
- Tight coupling between node types

#### 4. Metadata Threading
Context structures thread through recursion:
- **PlannerGlobal**: Shared state across entire planning
- **PlannerInfo**: Per-query/subquery planning context
- **RelOptInfo**: Per-relation during planning
- **EState**: Per-query execution context

### Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|-----------------|-------|--------|
| **raw_parser (gram.y + scan.l)** | Lexical analysis and syntax parsing | SQL string | RawStmt list |
| **analyze.c** | Semantic analysis and type checking | RawStmt | Query |
| **rewrite/rewriteMain.c** | View expansion and rule application | Query | Query list |
| **allpaths.c** | Generate alternative physical plans with costs | RelOptInfo, Query | Path list (in RelOptInfo) |
| **createplan.c** | Convert best Path to executable Plan | Path + PlannerInfo | Plan tree |
| **execProcnode.c** | Initialize executor and dispatch execution | Plan tree | PlanState tree |
| **node*.c** | Execute individual plan nodes | TupleTableSlot from children | TupleTableSlot results |

### Data Flow: Transformation Chain

```
SQL String
    ↓
pg_parse_query()
    ↓
RawStmt List (syntactically correct)
    ↓
pg_analyze_and_rewrite_fixedparams()
    ├─ parse_analyze_fixedparams() → semantic analysis
    └─ pg_rewrite_query() → apply rules/views
    ↓
Query List (semantically analyzed)
    ↓
pg_plan_queries()
    ├─ query_planner() → generate Paths (allpaths.c)
    │   ↓
    │   RelOptInfo { pathlist: [SeqScan@100, IndexScan@50, ...] }
    │
    └─ create_plan() → select cheapest Path
        ↓
        Plan Tree (e.g., NestLoop(IndexScan, SeqScan))
    ↓
PlannedStmt (wrapped Plan + metadata)
    ↓
ExecInitNode() → recursively initialize PlanState tree
    ↓
ExecutorRun() → repeatedly call ExecProcNode() on root
    ├─ Volcano pull: ExecNestLoop() → ExecProcNode(child) → TupleTableSlot
    │   ↓
    │   Filter/Project/Aggregate (stateful operators)
    │   ↓
    │   Return slot to parent
    └─ Repeat until EOF
    ↓
ExecEndNode() → cleanup
    ↓
Result Tuples (to client)
```

### Interface Contracts Between Components

#### Parser ↔ Analyzer
- **Parser produces**: RawStmt with statement node + location info
- **Analyzer expects**: Syntactically valid RawStmt
- **Analyzer produces**: Semantically complete Query with resolved references
- **Rewriter expects**: Query with all table/column references resolved

#### Analyzer ↔ Rewriter ↔ Planner
- **Rewriter produces**: Query list (same Query structure, possibly expanded)
- **Planner expects**: Query where all semantic validation complete
- **Planner produces**: PlannedStmt with concrete Plan tree
- **Executor expects**: PlannedStmt with all parameters resolved or marked

#### Planner Components (allpaths ↔ createplan)
- **allpaths produces**: RelOptInfo with pathlist containing cost-annotated Paths
- **createplan expects**: RelOptInfo with at least one valid Path
- **createplan produces**: Plan tree ready for executor setup
- **Executor expects**: Plan tree with all plan nodes properly initialized

#### Executor: Initialize ↔ Execute ↔ Cleanup
- **ExecInitNode produces**: PlanState tree with ExecProcNode function pointers set
- **ExecProcNode expects**: Properly initialized PlanState (by ExecInitNode)
- **ExecProcNode produces**: TupleTableSlot (or NULL for EOF)
- **ExecEndNode expects**: Initialized PlanState tree (from ExecInitNode)

---

## Summary

PostgreSQL's query execution pipeline implements a classic **layered compiler architecture** with three main phases:

1. **Analysis**: Parse SQL string → semantic Query tree (parsing, analysis, rewriting)
2. **Optimization**: Generate alternative Paths with costs, select best, convert to executable Plan
3. **Execution**: Initialize stateful node tree, then stream tuples up tree using Volcano pull model

The **two-phase optimization** (Path generation + Plan creation) enables cost-based decisions while deferring expression-level optimizations until the cheapest path is selected. The **Volcano executor** provides an elegant streaming model that minimizes memory usage while maintaining state for complex operators (joins, aggregates, sorting).

The entire system uses **type-based dispatch (NodeTag)** to avoid tight coupling between node types, and **metadata threading** through context structures to pass information through recursive functions, resulting in clean, extensible code that's been proven in production for decades.
