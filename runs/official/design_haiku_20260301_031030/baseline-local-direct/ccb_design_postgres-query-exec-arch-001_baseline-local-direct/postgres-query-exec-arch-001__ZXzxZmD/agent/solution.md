# PostgreSQL Query Execution Pipeline: Trace Analysis

## Files Examined

### Traffic Cop (Query Entry Point)
- `src/backend/tcop/postgres.c` — Main traffic cop module; entry point `exec_simple_query()`, contains `pg_parse_query()`, `pg_analyze_and_rewrite_fixedparams()`, `pg_plan_queries()`, and `pg_rewrite_query()` functions

### Parser (Lexer + Grammar)
- `src/backend/parser/parser.c` — Raw parser entry point; calls `scanner_init()` (Flex lexer), `parser_init()`, and `base_yyparse()` (Bison grammar parser); returns list of RawStmt
- `src/backend/parser/gram.y` — Bison grammar file (generates gram.c during build) that defines SQL grammar rules
- `src/backend/parser/scan.l` — Flex lexer file (generates scan.c) that tokenizes SQL input

### Semantic Analyzer
- `src/backend/parser/analyze.c` — Semantic analysis entry point; contains `parse_analyze_fixedparams()`, `parse_analyze_varparams()`, and `parse_analyze_withcb()` functions that call `transformTopLevelStmt()` to transform RawStmt → Query

### Query Rewriter
- `src/backend/rewrite/rewriteHandler.c` — Query rewrite logic; contains `QueryRewrite()` function that applies rules (views, INSTEAD rules) to Query nodes, produces multiple Query nodes if rule-expanded

### Optimizer / Planner
- `src/backend/optimizer/plan/planner.c` — Main planner module; `planner()` dispatches to `standard_planner()` which calls:
  - `subquery_planner()` — generates RelOptInfo and Paths (two-phase optimization begins)
  - `get_cheapest_fractional_path()` — selects best Path based on cost
  - `create_plan()` — converts best Path → Plan tree (second phase)
- `src/backend/optimizer/plan/planmain.c` — Planning main routines
- `src/backend/optimizer/path/allpaths.c` — Path generation logic; generates alternative Path trees for each RelOptInfo
- `src/backend/optimizer/plan/createplan.c` — Creates Plan nodes from Path nodes; does second-phase optimization
- `src/backend/optimizer/plan/setrefs.c` — `set_plan_references()` cleans up plan tree references and handles subplan linking
- `src/backend/optimizer/util/clauses.c` — Clause optimization and manipulation utilities
- `src/backend/optimizer/geqo/geqo_main.c` — Genetic optimizer for large join problems

### Executor
- `src/backend/tcop/pquery.c` — Portal execution; contains `PortalRun()`, `PortalRunSelect()`, `PortalRunMulti()`, and `PortalStart()`; calls `ExecutorRun()` to execute plans
- `src/backend/executor/execMain.c` — Executor main; contains `ExecutorStart()`, `ExecutorRun()`, `ExecutorEnd()`; initializes EState and manages execution lifecycle
- `src/backend/executor/execProcnode.c` — Executor dispatch; contains `ExecInitNode()` (initializes PlanState tree), `ExecProcNode()` (function pointer dispatch), `ExecEndNode()` (cleanup); implements Volcano-style pull model
- `src/backend/executor/execUtils.c` — Executor utilities for memory and slot management
- `src/backend/executor/execExpr.c` — Expression evaluation
- `src/backend/executor/execScan.c` — Base scan node execution
- `src/backend/executor/nodeSeqscan.c` — Sequential scan execution
- `src/backend/executor/nodeNestloop.c` — Nested loop join execution
- `src/backend/executor/nodeHashjoin.c` — Hash join execution
- `src/backend/executor/nodeMergejoin.c` — Merge join execution
- `src/backend/executor/nodeAgg.c` — Aggregation execution
- `src/backend/executor/nodeSort.c` — Sort execution
- `src/backend/executor/nodeHash.c` — Hash table building for hash joins

### Node Type Definitions
- `src/include/nodes/parsenodes.h` — RawStmt, SelectStmt, Query definitions (parser output)
- `src/include/nodes/plannodes.h` — Plan, PlannedStmt, and all plan node types (Scan, Join, Agg, Sort, etc.)
- `src/include/nodes/execnodes.h` — PlanState and all plan state types; defines ExecProcNode function pointers
- `src/include/nodes/nodes.h` — Node type tag definitions
- `src/include/executor/executor.h` — Executor function prototypes

---

## Dependency Chain

### 1. **Entry Point: Traffic Cop**
   - **File**: `src/backend/tcop/postgres.c:1011` — `exec_simple_query(const char *query_string)`
   - **Purpose**: Main query execution entry point in the traffic cop; coordinates the entire pipeline

### 2. **Parsing Stage: Lexer → Parser → RawStmt**
   - **File**: `src/backend/tcop/postgres.c:603` → `pg_parse_query(const char *query_string)`
   - **Calls**: `src/backend/parser/parser.c:42` → `raw_parser(const char *str, RawParseMode mode)`
   - **Dispatch**:
     1. Initializes Flex scanner via `scanner_init()` (from `src/backend/parser/scan.l`)
     2. Calls `parser_init()` to initialize Bison parser state
     3. Calls `base_yyparse(yyscanner)` which uses grammar from `src/backend/parser/gram.y`
     4. Lexer tokenizes input; Bison parser applies grammar rules
   - **Output**: List of `RawStmt` nodes containing parsed SELECT/INSERT/UPDATE/DELETE/etc.
   - **Data Type**: `RawStmt` (from `parsenodes.h`) — minimal parse tree with statement tag and statement node

### 3. **Semantic Analysis Stage: RawStmt → Query**
   - **File**: `src/backend/tcop/postgres.c:665` → `pg_analyze_and_rewrite_fixedparams(RawStmt *parsetree, ...)`
   - **Calls**: `src/backend/parser/analyze.c:105` → `parse_analyze_fixedparams(RawStmt *parseTree, ...)`
   - **Dispatch**:
     1. Creates `ParseState` via `make_parsestate()`
     2. Calls `transformTopLevelStmt(pstate, parseTree)` — semantic analysis occurs here
     3. Validates types, resolves column references, builds scope chains, performs type coercion
     4. Optional: `JumbleQuery(query)` for query ID generation if enabled
   - **Output**: Single `Query` node with resolved types, validated expressions, and metadata
   - **Data Type**: `Query` (from `parsenodes.h`) — fully analyzed query tree with commandType, targetList, fromClause, whereClause, etc.

### 4. **Query Rewriting Stage: Query → Query (possibly multiple)**
   - **File**: `src/backend/tcop/postgres.c:798` → `pg_rewrite_query(Query *query)`
   - **Calls**: `src/backend/rewrite/rewriteHandler.c:4566` → `QueryRewrite(Query *parsetree)` (for non-utility queries)
   - **Dispatch**:
     1. Checks if query is utility command (no rewriting needed)
     2. For regular queries, applies rules (views, INSTEAD rules)
     3. May expand one Query into multiple (e.g., view with INSTEAD rules)
   - **Output**: List of `Query` nodes (may be 1 or more depending on rule expansion)
   - **Data Type**: List of `Query` — rewritten queries ready for planning

### 5. **Planning Stage: Query → PlannedStmt (Two-Phase Optimization)**

#### **Phase 1: Path Generation**
   - **File**: `src/backend/tcop/postgres.c:970` → `pg_plan_queries(List *querytrees, ...)`
   - **Calls**: `src/backend/tcop/postgres.c:882` → `pg_plan_query(Query *querytree, ...)` (per query)
   - **Calls**: `src/backend/optimizer/plan/planner.c:287` → `planner(Query *parse, ...)` → `standard_planner()`
   - **Dispatch**:
     1. `standard_planner()` initializes `PlannerGlobal` struct with bounds parameters, parallel settings
     2. Calls `subquery_planner(glob, parse, ...)` — this is where path generation happens
     3. Within `subquery_planner()`:
        - Validates parallel safety
        - Calls `src/backend/optimizer/path/allpaths.c` functions to generate alternative `Path` trees
        - Each RelOptInfo (relation) has multiple Path options (SeqScan, IndexScan, BitmapScan, etc.)
        - Calculates costs for each path using `src/backend/optimizer/path/costsize.c`
   - **Output**: RelOptInfo tree with Paths; `PlannerInfo` root structure

#### **Phase 2: Plan Creation**
   - **Within**: `src/backend/optimizer/plan/planner.c:303` → `standard_planner()` (lines 437-441)
   - **Calls**:
     1. `get_cheapest_fractional_path(final_rel, tuple_fraction)` — selects best Path
     2. `src/backend/optimizer/plan/createplan.c` → `create_plan(root, best_path)` — converts Path to Plan
   - **Dispatch**:
     - `create_plan()` recursively converts Path tree to Plan tree
     - Allocates Plan nodes matching Path structure (SeqScanPath → SeqScan, HashJoinPath → HashJoin, etc.)
     - Handles subplans, initPlans, parameter passing
   - **Cleanup & Finalization**:
     1. `SS_finalize_plan()` — computes parameter dependencies
     2. `set_plan_references()` — renumbers nodes, resolves varattno references
     3. Constructs final `PlannedStmt` with rtable, subplans, paramExecTypes, etc.
   - **Output**: `PlannedStmt` containing Plan tree, relation table, subplans, and execution metadata
   - **Data Type**: `PlannedStmt` (from `plannodes.h`) — final executable plan with Plan tree root

### 6. **Portal Creation & Execution Setup**
   - **File**: `src/backend/tcop/postgres.c:1215` → `CreatePortal("", true, true)` — creates unnamed portal
   - **Calls**: `src/backend/tcop/postgres.c:1224` → `PortalDefineQuery(portal, ..., plantree_list, ...)`
   - **Purpose**: Associates PlannedStmt list with portal for execution

### 7. **Executor Initialization & Execution**
   - **File**: `src/backend/tcop/postgres.c:1234` → `PortalStart(portal, NULL, 0, InvalidSnapshot)`
   - **File**: `src/backend/tcop/postgres.c:1273` → `PortalRun(portal, FETCH_ALL, true, receiver, receiver, &qc)`
   - **Calls**: `src/backend/tcop/pquery.c:685` → `PortalRun(Portal portal, long count, ...)`
   - **Dispatch**:
     1. Routes based on `portal->strategy` (PORTAL_ONE_SELECT, PORTAL_MULTI_QUERY, etc.)
     2. For SELECT: calls `PortalRunSelect(portal, true, count, dest)` at line 765
     3. `PortalRunSelect()` calls `ExecutorRun(queryDesc, direction, count)` at line 921
   - **Calls**: `src/backend/executor/execMain.c:297` → `ExecutorRun(QueryDesc *queryDesc, ScanDirection direction, uint64 count)`
   - **Dispatch**:
     1. Calls `ExecutorStart()` if not already initialized (initializes EState, calls ExecInitNode)
     2. Calls `ExecutePlan()` which repeatedly calls `ExecProcNode()` to pull tuples
     3. Tuples sent to `DestReceiver` for output formatting
   - **Output**: Result tuples sent to client

---

## Analysis

### **Design Patterns Identified**

1. **Volcano-Style Pull-Based Iterator Model (Executor)**
   - Each plan node implements a `ExecProcNode()` function pointer (set in `execProcnode.c:ExecInitNode()`)
   - Call stack flows top-down through plan tree: Each node calls `ExecProcNode()` on children to pull tuples
   - Example flow: `ExecNestLoop()` → `ExecProcNode(inner child)` → `ExecSeqScan()` → returns tuple
   - Enables pipelined execution with lazy evaluation; tuples flow bottom-up through pull requests
   - Contrast: Typical push-based systems process all tuples at each stage before moving to next

2. **Two-Phase Optimization Architecture**
   - **Phase 1 (allpaths.c)**: Generates multiple alternative paths per relation; explores join orders, scan methods, aggregation strategies
   - **Phase 2 (createplan.c)**: Commits to single best path; creates actual Plan tree with operator selections
   - Decouples optimization exploration from code generation; allows cost analysis without allocation overhead
   - Cost calculations guide path pruning (keeps only potentially-best paths)

3. **Function Dispatch via Polymorphism (Type-Based Dispatch)**
   - `ExecInitNode()` uses switch on `nodeTag(node)` to call type-specific initializers (ExecInitSeqScan, ExecInitNestLoop, etc.)
   - Each returns `PlanState` base type; contains function pointer `ExecProcNode` pointing to node-specific executor
   - Achieves C-level polymorphism without virtual method tables; enables custom executors via hooks

4. **Recursive Tree Traversal Pattern**
   - Parser: `base_yyparse()` recursively builds parse tree via grammar productions
   - Analyzer: `transformTopLevelStmt()` recursively validates and transforms statement tree
   - Planner: `subquery_planner()` recursively plans subqueries and upper relations
   - Executor: `ExecInitNode()` and `ExecProcNode()` recursively initialize and execute plan tree

5. **Memory Context Hierarchy**
   - Different memory contexts for different lifetimes (MessageContext, TransactionContext, per-parsetree context)
   - Allows efficient cleanup of large structures (e.g., per-parsetree context deleted after statement completes)

### **Component Responsibilities**

1. **Traffic Cop (postgres.c)**
   - Orchestrates entire pipeline: parsing → analysis → rewriting → planning → execution
   - Manages transaction boundaries; handles multiple statements in single query string
   - Manages memory contexts and cleanup

2. **Parser (parser.c, gram.y, scan.l)**
   - Lexical analysis (tokenization) by Flex lexer
   - Syntax analysis by Bison parser; validates SQL grammar
   - Produces minimally-processed RawStmt (just parsed structure, no semantic info)

3. **Semantic Analyzer (analyze.c, parse_node.c, parse_*.c)**
   - Type resolution and coercion
   - Name resolution (columns, tables, functions)
   - Scope and namespace handling
   - Validation of statement structure
   - Produces fully-analyzed Query node

4. **Query Rewriter (rewriteHandler.c)**
   - Applies database rules (views with rules, INSTEAD rules)
   - Expands one query into multiple if rules match
   - Conditional on rule configuration

5. **Planner/Optimizer (planner.c, allpaths.c, createplan.c)**
   - Generates and costs alternative execution paths
   - Selects cheapest path
   - Creates actual executable Plan tree
   - Handles subquery planning, join order optimization, aggregation strategies

6. **Executor (execMain.c, execProcnode.c, node*.c)**
   - Initializes execution state (EState) and plan state tree (PlanState)
   - Executes plan via pull-based iteration
   - Handles tuple flow, filtering, grouping, joining, sorting
   - Manages resources and cleanup

### **Data Flow Description**

```
SQL String
    ↓
[Parser: Lexer + Grammar] → raw_parser()
    ↓
RawStmt (list)
    ↓
[Semantic Analyzer] → parse_analyze_fixedparams()
    ↓
Query (one per input RawStmt)
    ↓
[Query Rewriter] → QueryRewrite()
    ↓
Query (one or more, depending on rule expansion)
    ↓
[Planner/Optimizer] → planner()
  ├─ subquery_planner(): Generate Paths (allpaths.c)
  └─ create_plan(): Convert Path → Plan (createplan.c)
    ↓
PlannedStmt (Plan tree + metadata)
    ↓
[Executor]
  ├─ ExecutorStart(): ExecInitNode() → PlanState tree
  ├─ ExecutorRun(): ExecProcNode() repeatedly → tuples
  └─ ExecutorEnd(): ExecEndNode() → cleanup
    ↓
Result Tuples → DestReceiver → Network/Client
```

### **Interface Contracts Between Components**

1. **Parser → Analyzer**
   - Input: `RawStmt` — minimal parse tree
   - Output: `Query` — fully analyzed, type-checked
   - Contract: RawStmt.stmt is a union of statement types (SelectStmt, InsertStmt, etc.); analyzer validates types match query semantics

2. **Analyzer → Rewriter**
   - Input: `Query` — analyzed query
   - Output: `List<Query>` — possibly multiple queries after rule expansion
   - Contract: Input Query is valid and type-checked; output Queries may have different content if rules expanded

3. **Rewriter → Planner**
   - Input: `List<Query>` — rewritten queries
   - Output: `List<PlannedStmt>` — one PlannedStmt per Query
   - Contract: Each Query is planned independently; PlannedStmt contains complete Plan tree

4. **Planner Components**
   - **Paths (allpaths.c)** → **Plan (createplan.c)**
   - Input: RelOptInfo with alternative Paths, cost estimates
   - Output: Plan tree matching best Path
   - Contract: create_plan recursively converts each Path node to corresponding Plan node

5. **Planner → Executor**
   - Input: `PlannedStmt` — plan tree + metadata (rtable, subplans, paramExecTypes)
   - Output: `TupleTableSlot` stream (tuples)
   - Contract: PlannedStmt.planTree is executable; contains all information needed for execution

6. **Executor Internal (execProcnode.c)**
   - `ExecInitNode()` → `ExecProcNode()` → `ExecEndNode()`
   - Input: Plan tree, EState
   - Output: PlanState tree with function pointers set
   - Contract: Each PlanState.ExecProcNode points to node-specific executor (e.g., ExecSeqScan)

---

## Summary

PostgreSQL's query execution follows a **five-stage pipeline** from SQL string to result tuples:

1. **Parsing** (lexer + Bison grammar) produces RawStmt with minimal structure
2. **Semantic Analysis** (transformTopLevelStmt) validates types, resolves names → Query
3. **Query Rewriting** (rules) expands views and applies INSTEAD rules → Query(s)
4. **Planning/Optimization** uses a two-phase approach: Path generation explores alternatives (allpaths.c), then Plan creation commits to best path (createplan.c) → PlannedStmt
5. **Execution** uses a **Volcano-style pull model** where ExecProcNode() is a function pointer dispatched by node type, enabling each plan node to pull tuples from children recursively, providing pipelined streaming execution without materializing intermediate results.

The architecture cleanly separates concerns: parsing handles syntax, analysis handles semantics, rewriting handles rule application, planning handles optimization, and execution handles runtime. The two-phase planner design (Paths then Plans) enables sophisticated cost-based optimization without allocation overhead. The Volcano iterator model enables efficient pipelined execution suitable for both OLAP and OLTP workloads.
