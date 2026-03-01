# PostgreSQL Query Execution Pipeline: Architecture Analysis

## Files Examined

### Traffic Cop (Entry Point)
- **src/backend/tcop/postgres.c** — `exec_simple_query()` entry point that orchestrates the entire pipeline; contains `pg_parse_query()`, `pg_analyze_and_rewrite_fixedparams()`, `pg_plan_queries()` wrapper functions

### Parser Subsystem
- **src/backend/parser/parser.c** — `raw_parser()` function that invokes lexer and grammar
- **src/backend/parser/scan.l** — Flex lexer for tokenization
- **src/backend/parser/gram.y** — Bison grammar rules for SQL syntax
- **src/backend/parser/analyze.c** — `parse_analyze_fixedparams()` semantic analyzer that converts RawStmt → Query

### Rewriter Subsystem
- **src/backend/rewrite/rewriteHandler.c** — `QueryRewrite()` entry point; applies view expansion, rule substitution via `RewriteQuery()` and `fireRIRrules()`
- **src/backend/rewrite/rewriteManip.c** — Query manipulation utilities

### Optimizer/Planner Subsystem
- **src/backend/optimizer/plan/planner.c** — `planner()` and `standard_planner()` orchestrate optimization; `subquery_planner()` recursively plans subqueries
- **src/backend/optimizer/plan/createplan.c** — `create_plan()` converts best Path to Plan tree
- **src/backend/optimizer/path/allpaths.c** — `make_rel_from_joinlist()`, path generation and cost computation
- **src/backend/optimizer/plan/planmain.c** — `query_planner()` main join planning logic
- **src/backend/optimizer/plan/joinpath.c**, **pathnode.c** — Path data structure creation and manipulation

### Executor Subsystem
- **src/backend/executor/execProcnode.c** — `ExecInitNode()`, `ExecProcNode()`, `ExecEndNode()` Volcano-style dispatch; switch statement mapping Plan types to executor functions
- **src/backend/executor/execMain.c** — `ExecutorStart()`, `ExecutorRun()`, `ExecutorEnd()` high-level executor control
- **src/backend/executor/node*.c** — Individual executor node implementations (nodeSeqscan.c, nodeNestloop.c, nodeAgg.c, etc.)

### Node Type Definitions
- **src/include/nodes/parsenodes.h** — `RawStmt`, `Query` structures
- **src/include/nodes/plannodes.h** — `PlannedStmt`, `Plan`, join/scan/aggregate node types
- **src/include/nodes/pathnodes.h** — `Path`, `RelOptInfo`, `PlannerInfo` optimizer structures
- **src/include/nodes/execnodes.h** — `PlanState`, `TupleTableSlot`, `EState` executor structures

---

## Dependency Chain

### 1. Entry Point: exec_simple_query() in src/backend/tcop/postgres.c:1011

**Flow:**
```
exec_simple_query(query_string)
  ├─ MessageContext memory context switched
  └─ parsetree_list = pg_parse_query(query_string)
```

### 2. Parser Stage: pg_parse_query() → raw_parser()

**File:** src/backend/tcop/postgres.c:602

**Code:**
```c
parsetree_list = raw_parser(query_string, RAW_PARSE_DEFAULT);
```

**Implementation:** src/backend/parser/parser.c:41
- Initializes Flex lexer via `scanner_init()`
- Invokes Bison grammar parser from gram.y
- Lexer (scan.l) tokenizes SQL string
- Grammar rules build AST with Node types (SelectStmt, InsertStmt, etc.)

**Output:** `List *parsetree_list` of `RawStmt` objects
```c
typedef struct RawStmt {
    Node *stmt;           // Unanalyzed parse tree (SelectStmt, etc.)
    ParseLoc stmt_location, stmt_len;  // Source location tracking
} RawStmt;
```

### 3. Semantic Analysis Stage: pg_analyze_and_rewrite_fixedparams()

**File:** src/backend/tcop/postgres.c:664

**Code:**
```c
querytree_list = pg_analyze_and_rewrite_fixedparams(
    parsetree,           // RawStmt
    query_string,
    NULL, 0, NULL        // param types
);
```

**Substage 3a: Parse Analysis → parse_analyze_fixedparams()**

**File:** src/backend/parser/analyze.c:104

**Transforms:** RawStmt → Query
- Validates SQL semantics (relation/column existence)
- Resolves names and types
- Builds range table (rtable)
- Constructs target list, join tree (FromExpr)
- Detects aggregates, window functions, sublinks

**Output:** Single `Query` object
```c
typedef struct Query {
    CmdType commandType;      // CMD_SELECT, CMD_INSERT, etc.
    List *rtable;             // Range table entries
    FromExpr *jointree;       // JOIN and WHERE clauses
    List *targetList;         // SELECT target expressions
    List *groupClause, *havingQual, *sortClause;
    Node *limitOffsetClause;
} Query;
```

**Substage 3b: Query Rewriting → QueryRewrite()**

**File:** src/backend/rewrite/rewriteHandler.c:4565

**Transforms:** Query → List of Query objects (0, 1, or many)

**Two-phase rewriting:**
1. **RewriteQuery()** — Applies non-SELECT rules (INSERT/UPDATE/DELETE rules)
2. **fireRIRrules()** — Applies RIR (view) rules (view expansion)

**Output:** `List *querytree_list` of rewritten Query objects

### 4. Planning Stage: pg_plan_queries()

**File:** src/backend/tcop/postgres.c:969

**Code:**
```c
plantree_list = pg_plan_queries(
    querytree_list,
    query_string,
    CURSOR_OPT_PARALLEL_OK,
    NULL
);
```

**For each Query:** calls pg_plan_query() if not utility command

### 5. Optimizer Stage: pg_plan_query() → planner()

**File:** src/backend/tcop/postgres.c:881

**Code:**
```c
plan = planner(querytree, query_string, cursorOptions, boundParams);
```

**Delegates to:** src/backend/optimizer/plan/planner.c:287 **standard_planner()**

#### Phase A: Path Generation (Cost Model)

**File:** src/backend/optimizer/plan/planner.c:435

**Code:**
```c
root = subquery_planner(glob, parse, NULL, false, tuple_fraction, NULL);
final_rel = fetch_upper_rel(root, UPPERREL_FINAL, NULL);
best_path = get_cheapest_fractional_path(final_rel, tuple_fraction);
```

**Key functions in src/backend/optimizer/path/allpaths.c:**
- `make_rel_from_joinlist()` — Builds all possible join orders
- `set_base_rel_pathlist()` — Generates scan paths (sequential, index, bitmap)
- `add_paths_to_joinrel()` — Joins relations with different algorithms (Nested Loop, Hash Join, Merge Join)
- `recurse_set_operations()` — Handles UNION/INTERSECT/EXCEPT

**Output:** `Path` objects organized in `RelOptInfo.pathlist`
```c
typedef struct Path {
    Cost startup_cost, total_cost;
    int rows;
    int pathkeys;
    // Specific path types: SeqScanPath, IndexPath, NestLoopPath, HashJoinPath, etc.
} Path;
```

#### Phase B: Plan Creation (Node Instantiation)

**File:** src/backend/optimizer/plan/planner.c:441

**Code:**
```c
top_plan = create_plan(root, best_path);
```

**Implementation:** src/backend/optimizer/plan/createplan.c:336

- Recursively converts best Path tree to executable Plan tree
- Allocates Plan node structures (SeqScan, NestLoop, Hash, Agg, Sort, etc.)
- Computes node estimates (rows, width)
- Attaches initialization plans (initPlans) for subqueries

**Output:** `Plan *planTree` (executable plan tree structure)
```c
typedef struct Plan {
    uint32 startup_cost, total_cost;
    Plan *lefttree, *righttree;     // Child plans
    List *targetlist;               // Expressions to compute
    List *qual;                     // WHERE/join predicates
} Plan;
```

#### Final Planner Output: PlannedStmt

**File:** src/backend/optimizer/plan/planner.c:556

```c
result = makeNode(PlannedStmt);
result->planTree = top_plan;
result->rtable = glob->finalrtable;
result->subplans = glob->subplans;
result->paramExecTypes = glob->paramExecTypes;
return result;
```

**Output:** `PlannedStmt` (complete execution specification)
```c
typedef struct PlannedStmt {
    Plan *planTree;              // Executable plan tree
    List *rtable;                // Relations referenced
    List *subplans;              // Subplan trees
    List *paramExecTypes;        // Parameter types
    int jitFlags;                // JIT compilation hints
} PlannedStmt;
```

### 6. Portal Creation and Execution

**File:** src/backend/tcop/postgres.c:1215–1278

**Code:**
```c
portal = CreatePortal("", true, true);
PortalDefineQuery(portal, NULL, query_string, commandTag,
                  plantree_list, NULL);
PortalStart(portal, NULL, 0, InvalidSnapshot);
(void) PortalRun(portal, FETCH_ALL, true, receiver, receiver, &qc);
```

**Portal** bundles PlannedStmt with execution state

### 7. Executor Stage: PortalRun() → ExecutorRun()

**File:** src/backend/executor/execMain.c

**High-level executor control:**
```c
ExecutorStart(queryDesc, eflags)    // Initialize plan tree
    → ExecInitNode(planTree, ...)   // Recursively init all nodes

ExecutorRun(queryDesc, ScanDirection, count)
    → ExecProcNode(planstate)       // Pull tuples in Volcano model

ExecutorEnd(queryDesc)              // Cleanup
    → ExecEndNode(planstate)
```

### 8. Volcano-Style Iterator Dispatch

**File:** src/backend/executor/execProcnode.c

#### Phase A: Initialization (ExecInitNode)

**Lines 141–430:** Switch statement dispatching on Plan node type:

```c
PlanState *ExecInitNode(Plan *node, EState *estate, int eflags) {
    switch (nodeTag(node)) {
        case T_SeqScan:
            result = ExecInitSeqScan((SeqScan *)node, estate, eflags);
            break;
        case T_NestLoop:
            result = ExecInitNestLoop((NestLoop *)node, estate, eflags);
            break;
        case T_Agg:
            result = ExecInitAgg((Agg *)node, estate, eflags);
            break;
        // ... 50+ node types
    }
    return result;
}
```

**Creates:** `PlanState` tree (execution state)
```c
typedef struct PlanState {
    Plan *plan;
    PlanState *lefttree, *righttree;
    TupleTableSlot *(*ExecProcNode)(PlanState *pstate);  // Function pointer!
} PlanState;
```

#### Phase B: Tuple Production (ExecProcNode)

**Lines 447–570:** Iterator pattern with method pointers:

Each PlanState has `ExecProcNode` function pointer set to node-specific handler:

```c
// For SeqScan nodes
seqscanstate->ps.ExecProcNode = ExecSeqScan;

// For NestLoop nodes
nestloopstate->ps.ExecProcNode = ExecNestLoop;
```

**Execution Loop (ExecutorRun):**
```c
slot = ExecProcNode(planstate);    // Calls appropriate handler
while (!TupIsNull(slot)) {
    // Process tuple (send to output, etc.)
    slot = ExecProcNode(planstate);  // Pull next tuple
}
```

**Node Implementations (pull tuples from children):**
- **SeqScan** (src/backend/executor/nodeSeqscan.c) — Scans heap sequentially
- **NestLoop** (nodeNestloop.c) — Nested loop join: `ExecProcNode(inner)` for each `ExecProcNode(outer)` tuple
- **HashJoin** (nodeHashjoin.c) — Hash table join
- **Agg** (nodeAgg.c) — Aggregation (groups tuples, computes aggregate functions)
- **Sort** (nodeSort.c) — Sorts all input tuples
- **Limit** (nodeLimit.c) — Stops after N tuples

#### Phase C: Cleanup (ExecEndNode)

**Recursively calls node-specific cleanup:**
```c
void ExecEndNode(PlanState *node) {
    if (!node) return;

    ExecEndNode(outerPlanState(node));
    ExecEndNode(innerPlanState(node));

    switch (nodeTag(node->plan)) {
        case T_SeqScan: ExecEndSeqScan(...); break;
        case T_NestLoop: ExecEndNestLoop(...); break;
        // ... release resources, close files, etc.
    }
}
```

---

## Analysis

### Design Patterns Identified

#### 1. **Layered Architecture**
- **Parsing Layer:** Lexer + Grammar → RawStmt
- **Analysis Layer:** Semantic validation → Query
- **Rewriting Layer:** Rule application → Query list
- **Optimization Layer:** Cost-based planning → Path selection → PlannedStmt
- **Execution Layer:** Iterator model → Tuples

#### 2. **Two-Phase Optimization**
PostgreSQL uses a sophisticated two-phase optimization strategy:

**Phase 1: Path Generation (allpaths.c)**
- Explores multiple execution strategies (sequential scan, index scan, different join orders)
- Computes cost estimates for each Path
- Selects lowest-cost Path for each RelOptInfo (relation)

**Phase 2: Plan Creation (createplan.c)**
- Converts best Path to executable Plan node tree
- Allocates node structures with precise execution parameters
- Instantiates subplan forests

**Rationale:** Separating path exploration from plan instantiation allows:
- Multiple optimization passes without reallocation
- Clear separation of costs (Path) from execution (Plan)
- Dynamic plan adjustment based on runtime parameters

#### 3. **Volcano Iterator Model (Pull-Based)**
Each executor node implements:
```
ExecInitNode() → Initialize state
ExecProcNode() → TupleTableSlot* (*iterator function)
ExecEndNode()  → Cleanup
```

**Pull-based execution:**
- Parent calls `ExecProcNode(child)` to get one tuple
- Child pulls from its children as needed
- Enables:
  - Pipeline parallelism (tuples flow immediately)
  - Early termination (LIMIT stops at N tuples)
  - Memory efficiency (no intermediate materialization for all operators)

#### 4. **Extensibility via Function Pointers**
```c
// In PlanState
TupleTableSlot *(*ExecProcNode)(struct PlanState *pstate);
```

Each node type can implement its own tuple production logic. Called via:
```c
slot = node->ps.ExecProcNode(&node->ps);
```

Enables custom nodes (ForeignScan, CustomScan) without modifying core executor.

#### 5. **Memory Context Management**
PostgreSQL uses hierarchical memory contexts:
- **MessageContext** — Per-query message parsing
- **PlanCacheContext** — Cached plan trees
- **ExecutorContext** — Per-execution tuple/state memory

Allows efficient bulk cleanup via `MemoryContextReset()`.

### Component Responsibilities

| Component | Input | Output | Key Responsibility |
|-----------|-------|--------|-------------------|
| **Traffic Cop (tcop/postgres.c)** | SQL string | Tuples | Orchestrate entire pipeline; manage transactions |
| **Lexer/Parser (parser/)** | SQL text | RawStmt list | Tokenize and parse SQL syntax |
| **Analyzer (analyze.c)** | RawStmt | Query | Validate semantics; resolve names; build range table |
| **Rewriter (rewriteHandler.c)** | Query | Query list | Apply view expansion, rules |
| **Optimizer (plan/, path/)** | Query | PlannedStmt | Cost-based planning; choose execution strategy |
| **Path Generation (allpaths.c)** | RelOptInfo | Path forest | Enumerate and cost execution alternatives |
| **Plan Creation (createplan.c)** | Path | Plan tree | Convert best path to executable plan |
| **Executor (executor/)** | Plan + Data | Tuples | Execute plan tree; return result tuples |

### Data Flow Description

```
SQL String (e.g., "SELECT * FROM t WHERE x > 5")
    ↓
[Parser] raw_parser(scan.l + gram.y)
    ↓
RawStmt {stmt: SelectStmt {relation: t, where: x>5}}
    ↓
[Analyzer] parse_analyze_fixedparams()
    ↓
Query {
    rtable: [RangeTblEntry(t)],
    targetList: [...],
    jointree: FromExpr{...}
}
    ↓
[Rewriter] QueryRewrite()
    ↓
Query (possibly transformed by rules/views)
    ↓
[Planner] standard_planner()
    ├─ Phase A: subquery_planner() + allpaths
    │   Path{SeqScanPath{cost:100}, IndexScanPath{cost:5}}
    │   → Best path chosen (IndexScanPath)
    │
    └─ Phase B: create_plan()
        Plan{IndexScan{index_name: t_x_idx}}
    ↓
PlannedStmt {
    planTree: IndexScan{...},
    rtable: [RangeTblEntry(t)],
    paramExecTypes: [...]
}
    ↓
[Executor] ExecutorStart() → ExecInitNode()
    ↓
PlanState Tree {
    ExecProcNode: ExecIndexScan,
    ...
}
    ↓
[Execution] ExecutorRun() → ExecProcNode() (Iterator)
    ↓
TupleTableSlot[] (result tuples)
    ↓
Output to client
```

### Interface Contracts Between Components

**Parser → Analyzer:**
- Input: `List *parsetree_list` of `RawStmt` objects
- Contract: RawStmt.stmt contains raw AST (SelectStmt, etc.); names unresolved
- Output: Single `Query` object with validated, resolved semantics

**Analyzer → Rewriter:**
- Input: `Query` from parse analysis
- Contract: Query has rtable, validated columns; can be transformed
- Output: `List *querytree_list` of `Query` objects (may be multiple for rules)

**Rewriter → Optimizer:**
- Input: `List *querytree_list` of fully rewritten `Query` objects
- Contract: Query is final, semantically valid, ready for optimization
- Output: `List *plantree_list` of `PlannedStmt` objects

**Optimizer → Executor:**
- Input: `PlannedStmt` containing `Plan *planTree`
- Contract: Plan tree is executable; costs are estimated; all nodes have execution parameters
- Output: Result tuples via `TupleTableSlot` structures

**Path Generation ↔ Plan Creation (within Planner):**
- Path objects are temporary cost-computation structures
- Once best path selected, converted to Plan (discarded after)
- Plan objects are the final executable specification stored in PlannedStmt

---

## Summary

PostgreSQL's query execution pipeline implements a **layered, extensible architecture** that separates parsing, analysis, rewriting, optimization, and execution into distinct phases. The **two-phase optimization** strategy (Path generation + Plan instantiation) enables sophisticated cost-based planning while maintaining clean separation of concerns. The **Volcano-style iterator model** with function-pointer dispatch provides an efficient, extensible execution engine that enables custom operators without core modifications. Data flows through a sequence of increasingly refined representations: SQL string → RawStmt → Query → PlannedStmt → PlanState → tuples, with each stage adding semantic information or execution constraints.

