# Django ORM Query Compilation Pipeline: Architecture Analysis

## Files Examined

### Entry Point & Manager
- **django/db/models/manager.py** — `BaseManager` and `Manager` classes provide the entry point via `get_queryset()`. Delegates all QuerySet methods via `_get_queryset_methods()`. Returns a `QuerySet` instance bound to the model.

### QuerySet: Lazy Query Building
- **django/db/models/query.py** — `QuerySet` class encapsulates the public API for the ORM. Key methods include:
  - `filter()`/`exclude()` — Creates new QuerySet copies with filter conditions added
  - `_filter_or_exclude()` — Chains QuerySets and defers actual query building
  - `_filter_or_exclude_inplace()` — Calls `Query.add_q()` to accumulate WHERE conditions
  - `iterator()` — Triggers query execution via `_iterator()` which calls `ModelIterable`
  - `__iter__()` — Lazy evaluation starts here; calls `_fetch_all()` which calls `iterator()`

### Query: SQL Representation
- **django/db/models/sql/query.py** — `Query` class represents a single SQL SELECT/INSERT/UPDATE/DELETE statement:
  - `__init__()` — Initializes `self.where = WhereNode()` and `self.alias_map` for join tracking
  - `add_q()` — Entry point for adding filter conditions; calls `_add_q()` to build WHERE tree
  - `_add_q()` — Recursively processes Q objects and calls `build_filter()` for each child condition
  - `build_filter()` — Processes field lookups and resolves them to join paths and Lookup expressions
  - `get_compiler()` — **Key method**: Retrieves the backend-specific SQL compiler by calling `connection.ops.compiler(self.compiler)` which returns `SQLCompiler` class

### SQL Compilation: Vendor Dispatch
- **django/db/models/sql/compiler.py** — `SQLCompiler` class generates SQL from Query:
  - `compile(node)` — **Central dispatch mechanism** (line 571):
    ```python
    vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
    if vendor_impl:
        sql, params = vendor_impl(self, self.connection)
    else:
        sql, params = node.as_sql(self, self.connection)
    ```
    This implements the **as_{vendor}() pattern** for backend-specific compilation.

  - `as_sql()` — Main method to generate SELECT SQL (line 754):
    - Calls `pre_sql_setup()` to prepare WHERE/HAVING/GROUP BY clauses
    - Gets distinct fields, FROM clause, and processes WHERE/HAVING conditions
    - Builds SELECT clause with field expressions
    - Handles GROUP BY, ORDER BY, LIMIT/OFFSET
    - Returns final SQL string and parameter list

  - `execute_sql()` — Runs query execution (line 1592):
    - Calls `as_sql()` to compile the query to SQL
    - Gets database cursor from connection
    - Executes SQL with `cursor.execute(sql, params)`
    - Processes results based on `result_type` (MULTI, SINGLE, ROW_COUNT, CURSOR)

- **django/db/backends/base/operations.py** — `BaseDatabaseOperations.compiler()` (line 385):
  - Returns compiler class from `compiler_module` (default: `django.db.models.sql.compiler`)
  - Backends can override to provide vendor-specific compilers

### WHERE Clause Tree Structure
- **django/db/models/sql/where.py** — `WhereNode` class implements tree-based WHERE clause:
  - Inherits from `django.utils.tree.Node`
  - `children` — List of child nodes (Lookup expressions or nested WhereNodes)
  - `connector` — AND, OR, or XOR connecting children
  - `negated` — Whether to negate the entire clause
  - `as_sql()` — Recursively compiles all children via `compiler.compile(child)` and joins with connector
  - `split_having_qualify()` — Separates aggregates/window functions for HAVING/QUALIFY clauses

### Expression & Lookup System
- **django/db/models/expressions.py** — `BaseExpression` and subclasses represent SQL expressions:
  - `Combinable` — Implements `__add__()`, `__sub__()`, etc. for operator overloading
  - `BaseExpression.as_sql()` — Returns SQL string and parameter list
  - `Col` — Represents a table column with alias
  - `Value` — Represents a literal value
  - `F` — Represents a field reference across model lookups
  - Expressions can nest and be resolved via `resolve_expression()`

- **django/db/models/lookups.py** — `Lookup` class (inherits from Expression):
  - `__init__()` — Takes `lhs` (left-hand side expression) and `rhs` (right-hand side value)
  - `as_sql()` — Generates SQL for the comparison (e.g., "field > %s")
  - `process_lhs()` — Compiles the left expression (field reference)
  - `process_rhs()` — Compiles the right value with transforms applied
  - `resolve_expression()` — Resolves field references and nested expressions
  - Lookup subclasses: `Exact`, `IContains`, `GreaterThan`, etc.

### Backend Integration
- **django/db/backends/base/base.py** — `DatabaseWrapper` class:
  - Holds connection to the database
  - Provides `ops` attribute (`BaseDatabaseOperations` instance)
  - Provides `features` attribute describing backend capabilities
  - Provides `cursor()` to get database cursor for execution

## Dependency Chain

### 1. Entry Point: Manager.get_queryset()
```
Model.objects.filter(...)
  → Manager.filter() [delegated via _get_queryset_methods()]
    → QuerySet.filter(self, *args, **kwargs)
```

### 2. Lazy QuerySet Building Phase
```
QuerySet.filter()
  → _filter_or_exclude(False, args, kwargs)
    → _chain() [creates copy of QuerySet]
      → _filter_or_exclude_inplace(False, args, kwargs)
        → self._query.add_q(Q(*args, **kwargs))
```

### 3. Query Representation Phase
```
Query.add_q(q_object)
  → _add_q(q_object, used_aliases)
    → for child in q_object.children:
      → build_filter(child, can_reuse=used_aliases, ...)
        → names_to_path(lookup_parts, opts)  [resolve field path]
        → get_lookup(lookup_name)  [get Lookup class from field]
        → Lookup(lhs, rhs)  [instantiate lookup]
      → target_clause.add(child_clause, connector)
      → WhereNode.add(clause, AND)  [accumulate to tree]
```

### 4. Query Iteration Phase (Evaluation)
```
for obj in queryset:
  → QuerySet.__iter__()
    → _fetch_all()
      → iterator()  [get iterator]
        → _iterator(use_chunked_fetch, chunk_size)
          → ModelIterable(self, ...)
            → ModelIterable.__iter__()
```

### 5. SQL Compilation Phase
```
ModelIterable.__iter__()
  → queryset.query.get_compiler(using=db)
    → connection.ops.compiler("SQLCompiler")  [get compiler class]
      → SQLCompiler(query, connection, using)
  → compiler.execute_sql(chunked_fetch=True, chunk_size=...)
    → as_sql()  [compile query to SQL]
      → pre_sql_setup(with_col_aliases=False)
        → setup_query()
          → get_select(with_col_aliases=False)  [SELECT columns]
          → self.select = [(col, (sql, params), alias), ...]
        → self.where, self.having = query.where.split_having_qualify()
        → get_group_by(self.select + extra_select, order_by)
        → get_order_by()

      → self.compile(self.where)  [compile WHERE tree]
        → WhereNode.as_sql(compiler, connection)
          → for child in self.children:
            → compiler.compile(child)  [recursively compile all conditions]
              → getattr(child, "as_" + vendor, None)  [VENDOR DISPATCH]
              → if not found: child.as_sql(compiler, connection)
            → result.append(sql)
            → result_params.extend(params)
          → " AND ".join(result)  [connect children]

      → Build SELECT clause: "SELECT ... FROM ... WHERE ... GROUP BY ..."
      → return sql_string, tuple(params)

    → cursor.execute(sql, params)  [execute against database]
```

### 6. Result Processing Phase
```
cursor.execute() → cursor.fetchmany() → results iterator
  → for row in compiler.results_iter(results):
    → model_cls.from_db(db, init_list, row_data)  [hydrate model]
      → obj = model_cls.__new__(model_cls)
      → obj.__dict__.update({field_name: value, ...})
    → yield obj
```

## Analysis

### Design Patterns Identified

#### 1. **Lazy Evaluation Pattern**
The ORM defers SQL compilation until iteration. QuerySets don't execute SQL when created; they accumulate filter conditions in a Query object. Execution only happens when:
- Iterating: `for obj in queryset`
- Calling terminal operations: `.get()`, `.count()`, `.exists()`
- Explicit evaluation: `list(queryset)`

#### 2. **Vendor Dispatch Pattern** (as_{vendor}() mechanism)
Located in `SQLCompiler.compile()` (line 571-577), this is the key mechanism for backend-specific SQL generation:
- Expressions/Lookups can implement `as_postgresql()`, `as_sqlite()`, `as_mysql()`, etc.
- Falls back to generic `as_sql()` if no vendor-specific method exists
- Allows PostgreSQL-specific features (e.g., RETURNING clause) while maintaining compatibility

Example in expressions.py:
```python
class SQLiteNumericMixin:
    def as_sqlite(self, compiler, connection, **extra_context):
        sql, params = self.as_sql(compiler, connection, **extra_context)
        if self.output_field.get_internal_type() == "DecimalField":
            sql = "(CAST(%s AS NUMERIC))" % sql
        return sql, params
```

#### 3. **Tree-Based WHERE Clause Construction**
`WhereNode` builds an expression tree:
- Leaves are `Lookup` instances (e.g., `Exact`, `GreaterThan`)
- Internal nodes are `WhereNode` instances with connector (AND/OR/XOR)
- Negation is tracked per node
- Recursive `as_sql()` traversal generates SQL: `"(cond1 AND cond2) OR cond3"`

#### 4. **Expression Protocol**
All SQL-representable objects implement:
- `as_sql(compiler, connection)` → `(sql_string, params_list)`
- `resolve_expression(query, ...)` → resolves field references and nesting
- `get_source_expressions()` / `set_source_expressions()` → for traversal
- Optional: `as_{vendor}()` for backend-specific implementations

#### 5. **Join Management via Alias Map**
Query tracks:
- `alias_map` — Maps table alias (e.g., "T0", "T1") to Join objects
- `used_aliases` — Set of currently active aliases
- `join_type` — INNER vs LEFT OUTER join
- Join promotion during filter application: if a condition requires joining on a nullable relation with a non-null constraint, joins are demoted to INNER

### Component Responsibilities

#### Manager
- Entry point to QuerySet creation
- Holds model reference and database routing hints
- Delegates all query methods to QuerySet

#### QuerySet
- Public API for building queries
- Maintains immutability via chaining (each operation returns new instance)
- Holds reference to Query object for lazy building
- Implements iteration protocol via `__iter__()` → `iterator()` → `ModelIterable`

#### Query
- Internal representation of SQL statement
- Accumulates filter conditions in WhereNode tree
- Tracks joins via alias_map
- Bridges to compiler via `get_compiler()`

#### SQLCompiler
- Converts Query to SQL string
- Handles expression/lookup compilation via `compile(node)` with vendor dispatch
- Manages SELECT, FROM, WHERE, GROUP BY, ORDER BY, LIMIT/OFFSET clauses
- Executes query and returns cursor

#### Lookup
- Binary expression: `field OPERATOR value`
- Left-hand side: Field reference (Col) or expression
- Right-hand side: Literal value or expression
- `as_sql()` generates comparison SQL: `"col_name = %s"`

#### Expression
- Generic SQL expression abstraction
- Can be nested: `F('field1') + F('field2') * 2`
- Resolves to SQL via `as_sql()` and parameters via `resolve_expression()`

#### WhereNode
- Tree node representing boolean conditions
- Children can be Lookups or nested WhereNodes
- Connector specifies AND/OR/XOR logic
- Negation flips entire subtree logic

### Data Flow Description

#### Phase 1: Query Building (Lazy)
```python
qs = User.objects.filter(age__gte=18).filter(email__icontains='example')
```
- Each `.filter()` returns new QuerySet with accumulated conditions
- Actual WHERE tree is NOT built yet; conditions are stored as Q objects
- No database access

#### Phase 2: Query Compilation (On Iteration)
```python
for user in qs:  # <-- Triggers compilation
```
- QuerySet.__iter__() calls iterator()
- ModelIterable.__iter__() calls compiler.execute_sql()
- compiler.as_sql() converts Query to SQL:
  1. Resolves field names to table columns (age → users.age)
  2. Resolves lookups to database operators (gte → >=)
  3. Builds WHERE tree from accumulated Q objects
  4. Compiles WHERE tree to SQL via recursive traversal
  5. Handles joins for related lookups
  6. Returns: `"SELECT ... FROM users WHERE age >= %s AND email ILIKE %s", (18, '%example%')`

#### Phase 3: Execution
- SQLCompiler calls `cursor.execute(sql, params)`
- Database returns rows
- ModelIterable hydrates rows to model instances
- Iterator yields instances to for loop

### Interface Contracts Between Components

#### Query ↔ SQLCompiler
- Query provides: WHERE tree, joins info, model metadata, annotations
- SQLCompiler provides: `compile(expr) → (sql, params)`, `get_from_clause()`, `get_select()`

#### SQLCompiler ↔ Expressions/Lookups
- Compiler calls: `expr.as_sql(compiler, connection) → (sql, params)`
- Expressions call: `compiler.compile(child_expr)` for nested compilation

#### Lookup ↔ Field
- Lookup queries: `field.output_field` for type information
- Field provides: `get_prep_value()` for parameter preparation

#### Backend ↔ Compiler
- Backend provides: `ops.compiler("SQLCompiler")` to instantiate compiler
- Backend provides: `connection.vendor` ("postgresql", "sqlite", "mysql") for vendor dispatch
- Backend provides: `features` object describing capability flags

## Summary

The Django ORM query compilation pipeline implements **lazy evaluation** with a **tree-based WHERE clause** representation and **vendor-agnostic SQL generation** through the **as_{vendor}() dispatch pattern**. A QuerySet accumulates filter conditions as a Query object without executing SQL. On iteration, a backend-specific SQLCompiler traverses the WHERE tree, compiling each Lookup expression recursively via the `compile(node)` method, which tries vendor-specific implementations (e.g., `as_postgresql()`) before falling back to generic `as_sql()`. This architecture decouples high-level query building from database-specific SQL generation, allowing the same QuerySet API to work across PostgreSQL, MySQL, SQLite, Oracle, and other backends.
