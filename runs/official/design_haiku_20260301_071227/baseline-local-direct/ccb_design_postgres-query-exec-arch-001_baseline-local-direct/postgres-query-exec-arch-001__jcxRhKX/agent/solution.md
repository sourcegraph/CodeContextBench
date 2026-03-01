# PostgreSQL Query Execution Pipeline: From Parse to Execute

## Files Examined

### Traffic Cop (Query Dispatcher)
- `src/backend/tcop/postgres.c` — Main backend interface; contains `exec_simple_query()` entry point, `pg_parse_query()`, `pg_analyze_and_rewrite_fixedparams()`, `pg_plan_queries()`, and `pg_plan_query()` functions that orchestrate the entire pipeline

### Parser (Lexical & Grammatical Analysis)
- `src/backend/parser/parser.c` — Main parser entry point; `raw_parser()` function initializes Flex scanner and Bison parser
- `src/backend/parser/scansup.c` — Lexical scanner support functions (part of Flex lexer)
- `src/backend/parser/grammar.y` — Bison grammar definition (compiled to `gramparse.c`)
- `src/backend/parser/keywords.c` — SQL keyword definitions used by lexer

### Semantic Analyzer (Parse Analysis)
- `src/backend/parser/analyze.c` — Main semantic analyzer; contains `parse_analyze_fixedparams()` and `parse_analyze_varparams()` which call `transformTopLevelStmt()` to analyze raw parse trees
- `src/backend/parser/parse_*.c` — Specialized analysis modules:
  - `parse_clause.c` — Analyzes SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY
  - `parse_expr.c` — Analyzes expressions and function calls
  - `parse_func.c` — Function resolution and overload selection
  - `parse_agg.c` — Aggregate function analysis
  - `parse_relation.c` — Range table entry processing
  - `parse_cte.c` — Common table expression (WITH clause) analysis
  - `parse_target.c` — Target list (SELECT list) analysis
  - `parse_coerce.c` — Type coercion rules
  - `parse_collate.c` — Collation inference
  - `parse_oper.c` — Operator resolution and overload selection
  - `parse_type.c` — Type name resolution
  - `parse_param.c` — Parameter placeholder analysis

### Query Rewriter (Rule Application)
- `src/backend/rewrite/rewriteHandler.c` — Main rewrite handler; contains `QueryRewrite()` function that applies view rules, stored rules, and row-level security
- `src/backend/rewrite/rewriteSupport.c` — Support functions for rule rewriting
- `src/backend/rewrite/rewriteDefine.c` — Rule creation and storage
- `src/backend/rewrite/rowsecurity.c` — Row-level security policy rewriting

### Planner & Optimizer
- `src/backend/optimizer/plan/planner.c` — Main planner entry point; `planner()` function and `standard_planner()` orchestrate the optimization process
- `src/backend/optimizer/plan/createplan.c` — Phase 2: Plan creation; `create_plan()` converts optimal Path nodes to executable Plan nodes
- `src/backend/optimizer/path/allpaths.c` — Phase 1: Path generation; `make_one_rel()` generates alternative execution paths for each relation and join
- `src/backend/optimizer/path/costsize.c` — Cost calculation for paths
- `src/backend/optimizer/path/indxpath.c` — Index access path generation
- `src/backend/optimizer/path/joinpath.c` — Join path generation (nested loop, merge join, hash join)
- `src/backend/optimizer/path/joinrels.c` — Join relation enumeration (dynamic programming)
- `src/backend/optimizer/path/pathkeys.c` — Pathkey management (sort order tracking)
- `src/backend/optimizer/plan/initsplan.c` — Initial planning setup
- `src/backend/optimizer/plan/analyzejoins.c` — Join clause analysis
- `src/backend/optimizer/util/clauses.c` — Clause extraction and analysis
- `src/backend/optimizer/util/relnode.c` — RelOptInfo creation and management
- `src/backend/optimizer/geqo/geqo_main.c` — Genetic query optimizer for large join problems

### Executor (Tuple-at-a-time Execution)
- `src/backend/executor/execMain.c` — Main executor entry point; `ExecutorStart()`, `ExecutorRun()`, `ExecutorFinish()` functions
- `src/backend/executor/execProcnode.c` — Volcano-style dispatch; `ExecInitNode()` initializes PlanState nodes and `ExecProcNode()` macro dispatches to node-specific execution functions
- `src/backend/executor/nodeSeqscan.c` — Sequential scan executor (full table scan)
- `src/backend/executor/nodeIndexscan.c` — Index scan executor
- `src/backend/executor/nodeNestloop.c` — Nested loop join executor
- `src/backend/executor/nodeHashjoin.c` — Hash join executor
- `src/backend/executor/nodeMergejoin.c` — Merge join executor
- `src/backend/executor/nodeAgg.c` — Aggregation executor (GROUP BY)
- `src/backend/executor/nodeSort.c` — Sort executor
- `src/backend/executor/execScan.c` — Common scan logic (qualification and projection)
- `src/backend/executor/execExpr.c` — Expression evaluation
- `src/backend/executor/execExprInterp.c` — Bytecode interpreter for expressions

### Node Type Definitions
- `src/include/nodes/parsenodes.h` — Raw parse tree and analyzed Query node definitions
- `src/include/nodes/plannodes.h` — PlannedStmt and Plan node definitions
- `src/include/nodes/pathnodes.h` — Path, RelOptInfo, and PlannerInfo definitions
- `src/include/executor/execnodes.h` — PlanState, ExprState, and ExprContext definitions
- `src/include/executor/tuptable.h` — TupleTableSlot definition

---

## Dependency Chain

### 1. **Entry Point: Traffic Cop**
- **Location:** `src/backend/tcop/postgres.c:1011` — `exec_simple_query()`
- **Purpose:** Main query dispatcher in the backend; called by libpq protocol handler when a simple Query message arrives

### 2. **Stage 1: Lexical & Grammatical Analysis (Parsing)**
- **Calls:** `pg_parse_query()` at line 1064
- **Delegates to:** `raw_parser()` in `src/backend/parser/parser.c:42`
  - **Scanner:** `scanner_init()` initializes Flex lexer from SQL string
  - **Parser:** `base_yyparse()` is Bison parser (generated from `grammar.y`)
  - **Output:** `List<RawStmt>` — List of raw (unanalyzed) statement nodes with SQL syntax tree structure

**Data Structure Transformation:** `const char* query_string` → `List<RawStmt>`

### 3. **Stage 2: Semantic Analysis**
- **Calls:** `pg_analyze_and_rewrite_fixedparams()` at line 1189 for each RawStmt
- **Delegates to:** `parse_analyze_fixedparams()` in `src/backend/parser/analyze.c:105`
  - **Calls:** `transformTopLevelStmt()` to recursively transform raw parse tree
  - **What happens:**
    - Validates column references against table schemas (via `transformFromClause()`)
    - Resolves function names and operator symbols (via `parse_func.c`, `parse_oper.c`)
    - Type-checks expressions and applies implicit type coercions (via `parse_coerce.c`)
    - Analyzes aggregate functions and window functions (via `parse_agg.c`)
    - Builds range table entries (RTEs) for all referenced relations
    - Analyzes GROUP BY, HAVING, ORDER BY, DISTINCT (via `parse_clause.c`)
    - Analyzes target list (SELECT list) (via `parse_target.c`)
    - Builds expression nodes with full type information
  - **Output:** `Query` — Single analyzed query tree with semantic information

**Data Structure Transformation:** `RawStmt` → `Query`

### 4. **Stage 3: Query Rewriting**
- **Calls:** `pg_rewrite_query()` in `src/backend/tcop/postgres.c:798`
- **Delegates to:** `QueryRewrite()` in `src/backend/rewrite/rewriteHandler.c`
  - **What happens:**
    - Applies view rules (rewrite rules defined on views)
    - Applies stored rules (user-defined rewrite rules created with CREATE RULE)
    - Applies row-level security (RLS) policies (via `rowsecurity.c`)
    - Converts INSERT/UPDATE/DELETE into underlying table operations if rules exist
    - May expand one query into multiple queries (e.g., UNION for updatable views)
  - **Output:** `List<Query>` — List of rewritten Query nodes (usually one, but can be multiple if rules expand the query)

**Data Structure Transformation:** `Query` → `List<Query>` (usually 1:1, sometimes 1:N)

### 5. **Stage 4: Planning & Optimization**
- **Calls:** `pg_plan_queries()` at line 1192 for the rewritten query list
  - **Dispatches:** For non-utility statements, calls `pg_plan_query()` in `src/backend/tcop/postgres.c:882`
    - **Delegates to:** `planner()` in `src/backend/optimizer/plan/planner.c:287`

#### **Phase 4A: Path Generation (Cost Estimation)**
- **Function:** `standard_planner()` → `subquery_planner()` → `query_planner()` → `make_one_rel()` in `src/backend/optimizer/path/allpaths.c:171`
- **What happens:**
  1. **Setup:** `setup_simple_rel_arrays()` creates RelOptInfo nodes for each base table
  2. **Base relation paths:** `set_base_rel_pathlists()` generates alternative access paths:
     - Sequential scan (via `create_seqscan_path()`)
     - Index scan paths (via `create_index_paths()` in `indxpath.c`)
  3. **Selectivity estimation:** `set_base_rel_sizes()` calculates expected rows and costs
  4. **Join enumeration:** `make_rel_from_joinlist()` → `standard_join_search()` uses dynamic programming:
     - For each level K (2 to N relations):
       - Generates all K-way join possibilities
       - Creates JoinPath nodes with different join methods:
         - Nested loop joins (via `create_nestloop_path()`)
         - Hash joins (via `create_hashjoin_path()`)
         - Merge joins (via `create_mergejoin_path()`)
     - Selects cheapest paths via `set_cheapest()`
  5. **Upper-level planning:** `grouping_planner()` generates additional paths for:
     - Aggregation and GROUP BY (via `UPPERREL_GROUP_AGG`)
     - DISTINCT (via `UPPERREL_DISTINCT`)
     - ORDER BY (via `UPPERREL_ORDERED`)
     - Set operations (via `UPPERREL_SETOP`)
     - Window functions (via `UPPERREL_WINDOW`)
  6. **Path selection:** `get_cheapest_fractional_path()` selects the best path based on tuple_fraction
- **Output:** `Path` — Best cost-annotated execution path for the entire query

**Data Structure Transformation:** `Query` → `Path` (with cost estimates: startup_cost, total_cost, rows)

#### **Phase 4B: Plan Creation (Executable Code Generation)**
- **Function:** `create_plan()` in `src/backend/optimizer/plan/createplan.c:337`
- **What happens:**
  1. **Recursive conversion:** `create_plan_recurse()` converts Path to Plan:
     - SeqScan Path → SeqScan Plan (via `create_seqscan_plan()`)
     - IndexScan Path → IndexScan Plan (via `create_indexscan_plan()`)
     - NestLoop Path → NestLoop Plan (via `create_nestloop_plan()`)
     - HashJoin Path → HashJoin Plan (via `create_hashjoin_plan()`)
     - MergeJoin Path → MergeJoin Plan (via `create_mergejoin_plan()`)
     - Agg Path → Agg Plan (via `create_agg_plan()`)
     - Sort Path → Sort Plan (via `create_sort_plan()`)
  2. **Target list construction:** Builds the SELECT list for each plan node
  3. **Qual attachment:** Adds WHERE clauses and join conditions to appropriate nodes
  4. **Sub-plan handling:** Recursively creates plans for subqueries (initPlan)
  5. **Parameterization info:** Sets up external parameters and dependencies
  6. **Label assignment:** Assigns node IDs and validates parameter flow
- **Output:** `PlannedStmt` — Executable plan tree ready for the executor

**Data Structure Transformation:** `Path` → `PlannedStmt` (with Plan tree containing executable instructions)

### 6. **Stage 5: Portal Creation & Execution**
- **Calls:** `PortalDefineQuery()` at line 1224 to bind the PlannedStmt to a Portal
- **Calls:** `PortalStart()` at line 1234 and `PortalRun()` to start execution

### 7. **Stage 6: Tuple Execution (Volcano Model)**
- **Entry:** `ExecutorStart()` in `src/backend/executor/execMain.c:121`
  - **Calls:** `standard_ExecutorStart()` → `InitPlan()`
  - **What happens:**
    - Creates EState (global execution context)
    - Recursively calls `ExecInitNode()` in `execProcnode.c:141` for each Plan node
    - `ExecInitNode()` creates a PlanState for each Plan node type:
      - SeqScan Plan → SeqScanState (via `ExecInitSeqScan()`)
      - IndexScan Plan → IndexScanState (via `ExecInitIndexScan()`)
      - NestLoop Plan → NestLoopState (via `ExecInitNestLoop()`)
      - HashJoin Plan → HashJoinState (via `ExecInitHashJoin()`)
    - Sets `ExecProcNode` function pointer to node-specific execution function
    - Allocates TupleTableSlots for passing tuples between operators

- **Execution:** `ExecutorRun()` in `src/backend/executor/execMain.c:296`
  - **Calls:** `ExecutePlan()` main tuple iteration loop
  - **Volcano-style dispatch:** Each iteration calls `ExecProcNode(root_planstate)`
    - **Dispatch mechanism:** `ExecProcNode()` is a macro that calls the function pointer
    - **Tuple pulling:** Each PlanState recursively calls `ExecProcNode()` on children
    - **Iterator protocol:** Returns TupleTableSlot; NULL slot signals end of stream
  - **Example flow for `SELECT a.x FROM a WHERE a.x > 10`:**
    1. `ExecProcNode(SeqScanState)`
    2. → `ExecSeqScan()` (function pointed to by ExecProcNode)
    3. → `SeqNext()` gets tuple from table via `table_scan_getnextslot()`
    4. → `ExecScanExtended()` applies WHERE qual
    5. → `ExecProject()` applies SELECT list
    6. → Returns slot with result tuple `[x=15]`
    7. `ExecutePlan()` sends to client
    8. Loop repeats until `ExecProcNode()` returns NULL slot

- **Finalization:** `ExecutorFinish()` in `src/backend/executor/execMain.c:414`
  - Finalizes any ModifyTable operations
  - Executes queued AFTER triggers

**Data Structure Transformation:** `PlannedStmt` → `TupleTableSlot` (tuples)

---

## Analysis

### Design Patterns Identified

#### 1. **Pipeline Architecture**
The query execution follows a classic multi-stage pipeline:
- **Parse stage:** Converts textual SQL to syntactic structure
- **Analyze stage:** Adds semantic information (types, table schemas)
- **Rewrite stage:** Applies rules and policies
- **Optimize stage:** Generates efficient execution plans
- **Execute stage:** Evaluates the plan to produce results

This separation allows:
- Caching of earlier stages (e.g., prepared statements skip parsing/analyzing)
- Plugin hooks at each stage for customization
- Clear responsibility boundaries

#### 2. **Two-Phase Optimization in the Planner**

**Phase 1 (Path Generation):** Explores the search space
- Generates multiple execution strategies (Paths)
- Each Path represents a different way to execute the query
- Paths include cost estimates (startup_cost, total_cost) and cardinality (rows)
- Examples: Sequential scan vs. index scan, nested loop vs. hash join
- Dynamic programming finds all reasonable join orders and methods

**Phase 2 (Plan Creation):** Commits to the best strategy
- Selects the single best Path based on cost minimization
- Converts Path to Plan (adds executor-specific details)
- Creates instruction sequence for the executor

**Key insight:** This separation allows sophisticated optimization without expensive plan creation. Dominated paths are discarded before plan conversion.

#### 3. **Volcano-Style Tuple Execution**

The executor implements the Volcano model (also called the iterator model):
- **Pull-based:** Each operator calls its children to fetch tuples
- **Function pointers:** Each PlanState has an ExecProcNode function pointer that points to node-specific code
- **Iterator protocol:** Operators return one tuple at a time via TupleTableSlot; NULL signals end
- **Lazy evaluation:** Tuples only fetched when needed (no buffering)
- **Memory efficiency:** Slots can share tuple data (virtual slots)

**Key advantage:** Allows each operator to implement its control flow naturally (e.g., nested loop joins can naturally rescan inner plan)

#### 4. **Node Type Polymorphism**

Rather than a giant switch statement, each Plan/PlanState has a function pointer:
- `PlanState->ExecProcNode` points to `ExecSeqScan`, `ExecHashJoin`, etc.
- This allows:
  - Dynamic dispatch without branching
  - Runtime optimization (swap function pointers on first call)
  - New node types without modifying core dispatch code
  - Instrumentation variants (with/without profiling)

#### 5. **Cost-Based Optimizer**

All planning decisions driven by cost estimates:
- `startup_cost` — Cost to generate first tuple
- `total_cost` — Cost to generate all tuples
- `rows` — Estimated number of result tuples
- Selection uses `tuple_fraction` to decide if startup or total cost matters

Example:
```
Path A: startup=100, total=1000, rows=100  (good for LIMIT)
Path B: startup=500, total=500, rows=100   (good for full scan)
```
If query uses `LIMIT 1`, choose Path A. Otherwise, choose Path B.

### Component Responsibilities

#### Traffic Cop (`postgres.c`)
- **Responsibility:** Query protocol dispatcher and pipeline orchestrator
- **Does:** Calls parse, analyze/rewrite, plan, and execute stages in sequence
- **Owns:** Connection state, transaction context
- **Hooks:** Provides hooks for extension modules at each pipeline stage

#### Parser (`parser.c`, `grammar.y`, lexer)
- **Responsibility:** Syntactic analysis only
- **Does:** Converts SQL text to raw parse tree respecting SQL grammar
- **Constraints:** No database access allowed (must work in aborted transactions)
- **Limitation:** Cannot resolve column names, function overloads, or types

#### Semantic Analyzer (`analyze.c`, `parse_*.c`)
- **Responsibility:** Convert raw parse tree to analyzable Query with semantic information
- **Does:**
  - Resolves all names to database objects
  - Validates column references
  - Resolves function and operator overloads
  - Infers and checks types
  - Builds range table for table references
  - Validates query structure (e.g., aggregates in correct place)
- **Output:** Query node with full semantic information

#### Query Rewriter (`rewriteHandler.c`)
- **Responsibility:** Apply view rules, stored rules, and RLS policies
- **Does:**
  - Expands views into underlying tables/queries
  - Applies user-defined INSTEAD OF rules
  - Applies row-level security policies
  - Converts INSERT/UPDATE/DELETE into rule-defined operations
- **Limitation:** Can expand one query into multiple (e.g., UNION)

#### Planner/Optimizer (`planner.c`, `allpaths.c`, `createplan.c`)
- **Responsibility:** Generate efficient execution strategy
- **Phase 1 (allpaths.c):** Generate alternative Paths
  - For each relation: sequential scan vs. index scans
  - For joins: all join orders × all join methods
  - For upper operations: all reasonable grouping/sorting strategies
- **Phase 2 (createplan.c):** Convert best Path to executable Plan
  - Recursive descent through Path tree
  - Calls type-specific plan builders
  - Attaches executor-specific info

#### Executor (`execMain.c`, `execProcnode.c`, `node*.c`)
- **Responsibility:** Execute Plan tree to produce result tuples
- **Initialization (ExecutorStart):**
  - Recursively initializes Plan nodes to PlanState
  - Allocates TupleTableSlots
  - Opens relations and indexes
- **Execution (ExecutorRun):**
  - Main loop calls `ExecProcNode()` to pull tuples
  - Passes tuples to result receiver (client)
  - Repeats until EOF or tuple limit
- **Finalization (ExecutorFinish):**
  - Runs final operations (AFTER triggers)
  - Closes resources

### Data Flow Description

#### RawStmt (Raw Parse Tree)
```c
typedef struct RawStmt {
    NodeTag type;
    Node *stmt;           // Syntactic parse tree (SelectStmt, InsertStmt, etc.)
    ParseLoc stmt_location;
    ParseLoc stmt_len;
}
```
- **Contains:** Raw syntactic structure with unresolved names
- **Example:** SelectStmt with "a" as a TableRef (not yet matched to actual table)
- **Generated by:** Lexer + Parser (raw_parser)

#### Query (Analyzed Query)
```c
typedef struct Query {
    NodeTag type;
    CmdType commandType;     // select|insert|update|delete|merge|utility
    List *rtable;            // Range table (list of RangeTableEntry)
    FromExpr *jointree;      // FROM and WHERE as joined tree
    List *targetList;        // SELECT list (list of TargetEntry)
    List *groupClause;       // GROUP BY
    Node *havingQual;        // HAVING
    List *sortClause;        // ORDER BY
    // ... many more semantic fields
}
```
- **Contains:** Fully analyzed query with resolved names and types
- **Examples in fields:**
  - `rtable` has RangeTableEntry nodes; each entry references a specific table
  - `targetList` has expressions with full type information
  - `groupClause` has references resolved
- **Generated by:** Semantic analyzer (analyze.c)

#### Path (Cost-Annotated Execution Strategy)
```c
typedef struct Path {
    NodeTag type;
    NodeTag pathtype;           // T_SeqScan, T_HashJoin, etc.
    RelOptInfo *parent;         // Relation this path builds

    Cardinality rows;           // Estimated # of tuples
    Cost startup_cost;          // Cost before returning first tuple
    Cost total_cost;            // Total cost for all tuples

    List *pathkeys;             // Sort order
}

// Subtype example:
typedef struct JoinPath {
    Path path;
    JoinType jointype;          // INNER, LEFT, SEMI, ANTI, FULL
    Path *outerjoinpath;        // Outer side
    Path *innerjoinpath;        // Inner side
    List *joinrestrictinfo;     // Join conditions
}
```
- **Contains:** One possible execution strategy with cost estimates
- **Multiple Paths:** Many exist for a single relation (all considered)
- **Generated by:** Path generation phase (allpaths.c)
- **Example:** For `SELECT a.x FROM a WHERE x > 10`
  - Path 1: SeqScan(rows=1000, startup=0, total=100)
  - Path 2: IndexScan(rows=100, startup=5, total=50) (if x > 10 is indexed)

#### PlannedStmt (Executable Plan)
```c
typedef struct PlannedStmt {
    NodeTag type;
    CmdType commandType;
    Plan *planTree;             // Root of plan tree
    List *rtable;               // Range table
    List *subplans;             // Plans for SubPlan nodes
    List *paramExecTypes;       // Types of PARAM_EXEC params
    // ... metadata
}

typedef struct Plan {
    NodeTag type;
    Cost startup_cost;          // Copied from best path
    Cost total_cost;            // Copied from best path
    Cardinality plan_rows;      // Expected rows

    List *targetlist;           // Output columns
    List *qual;                 // WHERE clauses to check
    struct Plan *lefttree;      // Outer input plan
    struct Plan *righttree;     // Inner input plan
}
```
- **Contains:** Single executable plan tree
- **Example plan nodes:**
  - SeqScan: scans one table
  - HashJoin: builds hash table from inner plan, probes with outer plan
  - Sort: sorts input tuples
  - Limit: returns first N tuples
- **Generated by:** Plan creation phase (createplan.c)

#### TupleTableSlot (Runtime Tuple Container)
```c
typedef struct TupleTableSlot {
    Datum *tts_values;         // Current attribute values
    bool *tts_isnull;          // Current NULL flags
    TupleDesc tts_tupleDescriptor;
    ItemPointerData tts_tid;   // For ctid and locking
}
```
- **Contains:** Single tuple being passed between operators
- **Multiple representations:**
  - Virtual: No tuple data, just Datum/isnull arrays
  - Heap: Palloc'd tuple
  - Minimal: Compact tuple without system columns
- **Generated/used by:** Executor nodes during execution
- **Passed via:** Function return values from `ExecProcNode()`

### Interface Contracts Between Components

**Parser ↔ Semantic Analyzer:**
- **Input:** RawStmt (raw parse tree)
- **Output:** Query (analyzed tree)
- **Contract:** Semantic analyzer promises to resolve all names and types

**Semantic Analyzer ↔ Rewriter:**
- **Input:** Query (analyzed)
- **Output:** List<Query> (rewritten)
- **Contract:** Rewriter may expand one query into many (views)

**Rewriter ↔ Planner:**
- **Input:** Query (rewritten)
- **Output:** PlannedStmt (executable plan)
- **Contract:** Planner must generate efficient executable plan

**Planner Phase 1 ↔ Planner Phase 2:**
- **Input:** List of Paths (all reasonable strategies)
- **Output:** Single best Path (optimal)
- **Intermediate:** RelOptInfo with multiple Paths for each relation
- **Contract:** Phase 1 generates candidates, Phase 2 converts winner

**Planner ↔ Executor:**
- **Input:** PlannedStmt (plan tree)
- **Output:** TupleTableSlot stream (result tuples)
- **Contract:** Plan is executable; executor drives through pull model

---

## Two-Phase Optimization Architecture

### Phase 1: Path Generation (`allpaths.c`, `costsize.c`)

**Goal:** Explore search space of reasonable execution strategies

**Process:**
1. **Relation setup:** For each base table, create a RelOptInfo
2. **Base relation paths:** Generate alternative access methods
   - Sequential scan
   - Index scans (for each usable index)
   - Bitmap index scans
3. **Join enumeration:** Build join relations using dynamic programming
   - **Level 1:** All base relations alone
   - **Level 2:** All 2-way joins (R1-R2, R1-R3, ..., R2-R3, ...)
   - **Level 3:** All 3-way joins (R1-R2-R3, R1-R2-R4, ...)
   - **...:** Up to N-way join
   - For each join, try all join methods: nested loop, hash, merge
4. **Upper-level operations:** Generate paths for GROUP BY, SORT, etc.
5. **Path selection:** Keep only non-dominated paths using `add_path()`
   - A path is dominated if another path has lower cost with same or better properties
   - Helps prune search space before expensive plan creation

**Output:** RelOptInfo for final relation has list of Paths; best path accessible via `cheapest_total_path` or `cheapest_startup_path`

### Phase 2: Plan Creation (`createplan.c`)

**Goal:** Convert best Path to executable Plan tree

**Process:**
1. **Path selection:** Choose best Path based on cost and `tuple_fraction`
   - If full result needed: minimize `total_cost`
   - If partial result (LIMIT): minimize `startup_cost`
2. **Recursive conversion:** `create_plan_recurse()` walks Path tree
   - **Base case:** Leaf paths (scans) → Scan plans (call `create_seqscan_plan()`, etc.)
   - **Recursive case:** Join paths → Join plans (call `create_nestloop_plan()`, etc.)
   - Each conversion includes:
     - Building target list (SELECT columns)
     - Attaching WHERE and JOIN quals
     - Recursively converting child paths to child plans
3. **Executor metadata:** Add execution information
   - Node IDs
   - External parameters
   - Subplan linkage

**Output:** PlannedStmt with Plan tree ready for executor

---

## Volcano-Style Executor Dispatch in `execProcnode.c`

### The Dispatch Mechanism

```c
// From executor.h:
static inline TupleTableSlot *
ExecProcNode(PlanState *node)
{
    if (node->chgParam != NULL)
        ExecReScan(node);

    return node->ExecProcNode(node);  // <-- Function pointer dispatch!
}
```

**Key insight:** Rather than a switch statement on node type, each PlanState has a function pointer (`ExecProcNode`) that points to the node-specific execution function. This allows:

1. **Dynamic dispatch:** No branching on node type at execution time
2. **Performance:** Better CPU cache behavior
3. **Extensibility:** New node types don't require modifying core dispatch code

### Initialization: `ExecInitNode()`

```c
PlanState *
ExecInitNode(Plan *node, EState *estate, int eflags)
{
    // switch on node type to create appropriate PlanState subtype
    switch (nodeTag(node)) {
        case T_SeqScan:
            result = (PlanState *) ExecInitSeqScan((SeqScan *)node, ...);
            break;
        case T_HashJoin:
            result = (PlanState *) ExecInitHashJoin((HashJoin *)node, ...);
            break;
        // ... more cases
    }

    // Set the function pointer to the execution function
    result->ExecProcNode = result->ExecProcNodeReal;
    return result;
}
```

**What happens:**
1. Dispatches on Plan node type (switch statement)
2. Creates appropriate PlanState subtype (e.g., SeqScanState, HashJoinState)
3. Sets `ExecProcNode` function pointer to node-specific function (e.g., `ExecSeqScan`)
4. Allocates TupleTableSlots for tuple passing
5. Opens relations, indexes, etc.

### Execution: Function Pointer Variants

Different variants are used depending on needs:

**First call:** `ExecProcNodeFirst()`
- Checks stack depth once
- Determines if instrumentation needed
- Sets function pointer to appropriate variant
- Calls actual function

**With instrumentation:** `ExecProcNodeInstr()`
- Measures execution time and tuple count
- Calls `ExecProcNodeReal` and records metrics

**Direct execution:** `ExecSeqScan()`, `ExecHashJoin()`, etc.
- Node-specific execution logic
- Returns next tuple via `TupleTableSlot`

This pattern allows cheap dynamic dispatch after the first call.

### Example: Nested Loop Join Execution

```c
// From nodeNestloop.c
static TupleTableSlot *
ExecNestLoop(PlanState *pstate)
{
    NestLoopState *node = (NestLoopState *) pstate;

    for (;;) {
        // If we need a new outer tuple
        if (node->nl_NeedNewOuter) {
            // PULL from outer plan
            outerTuple = ExecProcNode(outerPlanState(node));

            if (TupIsNull(outerTuple))
                return NULL;  // EOF

            // Store outer tuple in context for expressions
            econtext->ecxt_outertuple = outerTuple;

            // Rescan inner plan for new outer tuple
            ExecReScan(innerPlanState(node));
            node->nl_NeedNewOuter = false;
        }

        // Get next inner tuple
        innerTuple = ExecProcNode(innerPlanState(node));
        econtext->ecxt_innertuple = innerTuple;

        if (TupIsNull(innerTuple)) {
            // No more inner tuples for this outer
            node->nl_NeedNewOuter = true;
            continue;
        }

        // Check join condition
        if (ExecQual(joinqual, econtext)) {
            // Apply projection and return result
            return ExecProject(node->js.ps.ps_ProjInfo);
        }
    }
}
```

**Tuple flow:**
```
1. ExecutePlan() calls ExecProcNode(NestLoopState)
2. ExecNestLoop() calls ExecProcNode(outerPlanState) → gets outer tuple
3. ExecNestLoop() calls ExecProcNode(innerPlanState) → gets inner tuple
4. ExecNestLoop() checks join condition
5. ExecNestLoop() applies projection
6. ExecNestLoop() returns result tuple
7. ExecutePlan() sends to client
8. Loop repeats (back to step 2)
```

### Tuple Iteration Protocol

**Key contract:** Operators follow iterator protocol
- **Normal case:** Return TupleTableSlot with tuple data
- **End of stream:** Return NULL slot (checked by `TupIsNull()` macro)
- **No buffering:** Return tuples one at a time
- **Memory:** Slots can be reused (virtua slots avoid tuple copying)

### Scan Operators: `ExecScanExtended()`

Common pattern for scan-like operators (SeqScan, IndexScan, etc.):

```c
static TupleTableSlot *
ExecScanExtended(ScanState *node,
                 ExecScanAccessMtd accessMtd,  // e.g., SeqNext
                 ExecScanRecheckMtd recheckMtd,
                 EPQState *epqstate,
                 ExprState *qual,              // WHERE clause
                 ProjectionInfo *projInfo)      // SELECT list
{
    for (;;) {
        // Step 1: Fetch tuple from table/index
        slot = accessMtd(node);

        if (TupIsNull(slot))
            return NULL;  // EOF

        // Step 2: Place in context and check WHERE clause
        econtext->ecxt_scantuple = slot;

        if (qual == NULL || ExecQual(qual, econtext)) {
            // Tuple passes WHERE clause

            // Step 3: Apply SELECT list (projection)
            if (projInfo)
                return ExecProject(projInfo);
            else
                return slot;
        }

        // Tuple failed WHERE clause, loop for next
    }
}
```

**Variants based on qual and projection:**
- No qual, no projection: minimal overhead
- Qual only: check WHERE clause
- Projection only: build result tuple
- Both: check WHERE and build result

This allows the optimizer to choose the fastest path for each case.

---

## Summary

PostgreSQL's query execution pipeline elegantly separates concerns across six major stages:

1. **Parse:** Convert SQL text to raw syntactic tree (lexer + Bison grammar)
2. **Analyze:** Add semantic information by resolving names and types
3. **Rewrite:** Apply view rules and row-level security policies
4. **Optimize (Phase 1):** Generate alternative execution Paths with cost estimates
5. **Optimize (Phase 2):** Convert best Path to executable Plan tree
6. **Execute:** Drive Plan tree using Volcano pull-based tuple iteration with function pointer dispatch

The two-phase optimization approach allows sophisticated cost-based optimization without expensive plan creation for dominated strategies. The Volcano-style executor uses function pointers for dynamic dispatch, enabling efficient tuple-at-a-time execution while maintaining flexibility and extensibility. Data flows through clearly-defined node types (RawStmt → Query → Path → PlannedStmt → TupleTableSlot) with contract boundaries between components, making the system modular and amenable to extension via hooks and plugins.
