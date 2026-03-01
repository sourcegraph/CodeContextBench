# Django ORM Query Compilation Pipeline Analysis

## Files Examined

### Core ORM Layer (High-Level API)
- **django/db/models/manager.py** — Entry point providing `Manager` class with `get_queryset()` that creates QuerySet instances
- **django/db/models/query.py** — Main `QuerySet` class implementing lazy query building via `filter()`, `exclude()`, `values()`, and execution via `__iter__()` and `iterator()`

### SQL Construction Layer (Query Representation)
- **django/db/models/sql/query.py** — `Query` class representing the SQL query structure, holds WHERE clauses, JOIN info, SELECT fields, annotations; includes `get_compiler()` for vendor dispatch
- **django/db/models/sql/where.py** — `WhereNode` tree structure representing WHERE clauses composed of Lookup expressions connected via AND/OR/XOR
- **django/db/models/sql/compiler.py** — `SQLCompiler` class converting `Query` objects to SQL via `as_sql()` method and executing via `execute_sql()`

### Expression and Lookup System
- **django/db/models/expressions.py** — `BaseExpression` and `Expression` base classes providing the `as_sql()` protocol for all SQL-generatable objects
- **django/db/models/lookups.py** — `Lookup` base class and specific lookups (`Exact`, `In`, `GreaterThan`, etc.) implementing field comparisons with `as_sql()` methods

### Database Backend Layer (Vendor-Specific)
- **django/db/backends/base/base.py** — `BaseDatabaseWrapper` managing database connections
- **django/db/backends/base/operations.py** — `BaseDatabaseOperations` with `compiler()` method for vendor-agnostic compiler lookup
- **django/db/backends/postgresql/operations.py** — PostgreSQL `DatabaseOperations` overriding `compiler_module` to point to vendor-specific compilers
- **django/db/backends/postgresql/compiler.py** — PostgreSQL-specific compiler subclasses (extends base SQLCompiler)
- Similar files exist for MySQL, SQLite, Oracle backends

## Dependency Chain

### 1. Entry Point: QuerySet Creation
```
User Code: Book.objects.filter(title="Django")
    ↓
Manager.get_queryset() [manager.py:150]
    ↓
QuerySet.__init__() with model and initial Query object [query.py]
```

### 2. Lazy Query Building Phase
```
QuerySet.filter(*args, **kwargs) [query.py:1475]
    ↓
QuerySet._filter_or_exclude(negate, args, kwargs) [query.py:1491]
    ↓
QuerySet._chain() creates new QuerySet clone [query.py]
    ↓
QuerySet._filter_or_exclude_inplace() [query.py:1502]
    ↓
Query.add_q(Q object) [sql/query.py:1625]
    ↓
Query._add_q() processes Q children [sql/query.py:1654]
    ↓
Query.build_filter() creates Lookup instances [sql/query.py]
    ↓
Query.where.add(clause, AND) [sql/where.py:21]
    (WhereNode accumulates filter conditions as Lookup objects)
```

### 3. Query Execution Trigger
```
User: for book in queryset (iteration) OR queryset.count() OR queryset.get()
    ↓
QuerySet.__iter__() [query.py:369]
    ↓
QuerySet._fetch_all() [query.py]
    ↓
ModelIterable.__iter__() [query.py:85]
    ↓
QuerySet.query.get_compiler(using=db) [sql/query.py:358]
```

### 4. Vendor Dispatch Mechanism
```
Query.get_compiler(using=db) [sql/query.py:358]
    ↓
connection.ops.compiler("SQLCompiler") [backends/base/operations.py:385]
    ↓
(Import from connection.ops.compiler_module)
For PostgreSQL: imports from django.db.backends.postgresql.compiler
For MySQL: imports from django.db.backends.mysql.compiler
For SQLite: imports from django.db.backends.sqlite3.compiler
    ↓
Returns vendor-specific SQLCompiler subclass
    ↓
SQLCompiler.__init__(query, connection, using) [sql/compiler.py:47]
```

### 5. SQL Generation Phase
```
compiler.execute_sql() [sql/compiler.py:1592]
    ↓
compiler.as_sql() [sql/compiler.py:754]
    ↓
compiler.pre_sql_setup() [sql/compiler.py:79]
    ↓
compiler.setup_query() [sql/compiler.py:71]
    ↓
compiler.get_select() — processes selected fields
    ↓
compiler.get_from_clause() — processes JOINs
    ↓
compiler.compile(self.where) where is WhereNode [sql/compiler.py:793]
    ↓
WhereNode.as_sql() [sql/where.py:116]
    ↓
(For each child in WhereNode.children)
    compiler.compile(child) — child is usually a Lookup
```

### 6. Expression Compilation (Lookup Rendering)
```
compiler.compile(lookup_object) [sql/compiler.py:571]
    ↓
Check for vendor-specific method: getattr(lookup, "as_" + connection.vendor)
    ↓
If found: call vendor-specific method (e.g., as_postgresql, as_sqlite)
If not found: call lookup.as_sql(compiler, connection)
    ↓
BuiltinLookup.as_sql() [lookups.py:256]
    ↓
lookup.process_lhs(compiler, connection) — compiles left-hand side (field)
lookup.process_rhs(compiler, connection) — compiles right-hand side (value)
    ↓
lookup.get_rhs_op(connection, rhs) — gets operator (=, >, IN, LIKE, etc.)
    ↓
Returns SQL string and parameters tuple
    (e.g., ("title" = %s, ["Django"]))
```

### 7. SQL Execution
```
compiler.as_sql() — generates complete SQL string and parameters
    ↓
cursor = connection.cursor() or connection.chunked_cursor() [sql/compiler.py:1618-1620]
    ↓
cursor.execute(sql, params) [sql/compiler.py:1622]
    ↓
Database backend executes query and returns cursor
    ↓
compiler.results_iter(cursor) — yields raw database rows
    ↓
ModelIterable._iterator yields model instances [query.py:85]
```

## Analysis

### Design Patterns

#### 1. **Lazy Evaluation Pattern**
QuerySet builds queries without execution. Each method (`filter()`, `exclude()`, `values()`) returns a new QuerySet clone with modified `Query` object. The actual SQL is only generated and executed when the QuerySet is iterated, cached, or counted.

**Implementation:**
- QuerySet maintains an internal `Query` object (initially empty)
- Methods like `filter()` call `_chain()` to clone and then modify the clone's query
- Execution only triggers via `__iter__()`, `__len__()`, `count()`, `get()`, etc.

#### 2. **Tree-Structured Query Representation**
The `Query` object doesn't directly build SQL. Instead:
- It maintains structural information (selected fields, joins, where conditions, ordering)
- WHERE clauses are stored as a `WhereNode` tree where:
  - Leaf nodes are `Lookup` instances (e.g., `Exact(field, value)`)
  - Internal nodes are `WhereNode` objects with connectors (AND/OR/XOR)
  - Tree structure preserves logical precedence and allows optimization

**Benefits:**
- Separates query structure from SQL rendering
- Enables query manipulation before compilation (e.g., join promotion, splitting)
- Supports multiple backends from same structure

#### 3. **Double-Dispatch Compilation via as_sql() Protocol**
All compilable objects (Expressions, Lookups, WhereNode) implement `as_sql(compiler, connection)`:
```python
def as_sql(self, compiler, connection):
    return sql_string, params_list
```

**Flow:**
- `compiler.compile(node)` attempts vendor-specific dispatch first
- Checks for `as_{vendor}()` method on the node
- Falls back to generic `as_sql()` if vendor-specific not found
- Recursively compiles child expressions

**Example Vendor Dispatch:**
```python
# In sql/compiler.py:571
def compile(self, node):
    vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
    if vendor_impl:
        sql, params = vendor_impl(self, self.connection)  # PostgreSQL-specific
    else:
        sql, params = node.as_sql(self, self.connection)   # Generic fallback
    return sql, params
```

#### 4. **Vendor Dispatch via Backend Operations**
Each database backend (PostgreSQL, MySQL, SQLite, Oracle) overrides the `compiler_module` attribute in its Operations class:

```python
# PostgreSQL
class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django.db.backends.postgresql.compiler"

# MySQL
class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django.db.backends.mysql.compiler"
```

When `Query.get_compiler()` is called, it uses:
```python
connection.ops.compiler("SQLCompiler")
    # Imports from connection.ops.compiler_module
    # Returns appropriate SQLCompiler subclass
```

#### 5. **Expression Protocol for Composability**
All SQL-generatable objects inherit from `BaseExpression` and implement:
- `as_sql(compiler, connection)` → `(sql_string, params)`
- `resolve_expression(query, ...)` → resolved expression (late binding)
- `get_source_expressions()` → child expressions
- `set_source_expressions(new_exprs)` → mutate child expressions

This enables:
- Nesting expressions: `F('field1') + F('field2')`
- Operator overloading: `Q(a=1) & Q(b=2)`
- Database-agnostic representation

### Component Responsibilities

#### Manager
- Entry point for query construction
- Creates initial QuerySet via `get_queryset()`
- Proxies QuerySet methods (via `from_queryset()`) like `filter()`, `get()`, `create()`

#### QuerySet
- Maintains mutable `Query` object and execution state
- Provides chainable filtering API: `filter()`, `exclude()`, `values()`, `annotate()`
- Implements iteration protocol: `__iter__()`, `__len__()`, `__getitem__()`
- Delegates SQL compilation to `Query.get_compiler()`
- Delegates execution to `Iterable` classes (ModelIterable, ValuesIterable, etc.)

#### Query (sql/query.py)
- Represents SQL query structure (not SQL string)
- Holds: selected fields, WHERE clause (as WhereNode), JOINs (alias_map), ORDER BY, GROUP BY, annotations
- Methods: `add_q()` (adds filter), `add_fields()`, `get_compiler()` (vendor dispatch)
- `get_compiler()` returns backend-specific SQLCompiler for current database

#### SQLCompiler
- Converts `Query` object to SQL string via `as_sql()`
- Orchestrates compilation: `pre_sql_setup()` → `get_select()` → `get_from_clause()` → compile WHERE/HAVING
- Executes compiled SQL via `execute_sql()`
- Subclassed per backend (PostgreSQLCompiler, MySQLCompiler, etc.) for dialect-specific SQL

#### WhereNode (sql/where.py)
- Tree of filter conditions
- Children are Lookup instances or other WhereNodes
- `as_sql()` recursively compiles children via `compiler.compile()`
- Handles AND/OR/XOR connectors and negation
- Supports optimization: splitting aggregate/window functions into HAVING/QUALIFY clauses

#### Lookup (lookups.py)
- Represents a single comparison operation (e.g., `field = value`)
- Has `lhs` (left-hand side, usually a field reference) and `rhs` (right-hand side, value)
- `as_sql()` compiles to comparison SQL: `process_lhs()` + operator + `process_rhs()`
- Subclasses: `Exact`, `In`, `GreaterThan`, `Contains`, `Range`, etc.
- Database preparations via `get_db_prep_value()` on fields

#### Expression (expressions.py)
- Base for all SQL expressions: values, field references, functions, operations
- Implements `as_sql()` for rendering to SQL
- Can be composed: `F('field1') + Value(5)` → `CombinedExpression`
- Supports vendor-specific implementations via `as_{vendor}()` methods

### Data Flow: Concrete Example

**Code:**
```python
books = Book.objects.filter(
    title__startswith="Django",
    author__name="Alice"
)
for book in books:
    print(book.title)
```

**Execution Flow:**

1. **QuerySet Creation:**
   - `Book.objects` → Manager returns QuerySet with empty Query

2. **Filter 1: title__startswith**
   - `filter(title__startswith="Django")`
   - Creates `Lookup` subclass via `Field.get_lookup("startswith")`
   - Adds to Query.where via `add_q()`
   - WhereNode now contains: `StartsWith(Col("title"), Value("Django"))`

3. **Filter 2: author__name="Alice"** (relational)
   - `filter(author__name="Alice")`
   - Resolves relationship: creates JOIN to author table
   - Adds to Query.where: `Exact(Col("author"."name"), Value("Alice"))`
   - Query.alias_map now tracks the JOIN

4. **Iteration (execution trigger):**
   - `for book in books` calls `QuerySet.__iter__()`
   - Calls `QuerySet._fetch_all()`
   - Creates compiler: `query.get_compiler(using="default")`

5. **Compiler Selection:**
   - `get_compiler()` calls `connection.ops.compiler("SQLCompiler")`
   - For PostgreSQL: imports from `django.db.backends.postgresql.compiler`
   - Instantiates PostgreSQL-specific `SQLCompiler(query, connection, using)`

6. **SQL Generation:**
   - `compiler.execute_sql()` calls `compiler.as_sql()`
   - `as_sql()` does:
     - `pre_sql_setup()`: processes select, from, group by
     - `compile(self.where)` → WhereNode.as_sql()
     - WhereNode iterates children, calls `compiler.compile()` on each

7. **Lookup Compilation:**
   - For `StartsWith(Col("title"), Value("Django"))`:
     - `compiler.compile(lookup)` tries `lookup.as_postgresql()`
     - Not found, falls back to `lookup.as_sql()`
     - BuiltinLookup.as_sql() calls:
       - `process_lhs()` → compiles to `"book"."title"`
       - `process_rhs()` → compiles to `%s` with params `["Django%"]`
       - `get_rhs_op()` → `"ILIKE"` (for PostgreSQL startswith)
     - Returns: `("book"."title" ILIKE %s, ["Django%"])`

   - For `Exact(Col("author"."name"), Value("Alice"))`:
     - Similar process returns: `("author"."name" = %s, ["Alice"])`

8. **Final SQL:**
   ```sql
   SELECT "book"."id", "book"."title", "book"."author_id"
   FROM "book"
   INNER JOIN "author" ON ("book"."author_id" = "author"."id")
   WHERE "book"."title" ILIKE %s AND "author"."name" = %s
   -- params: ["Django%", "Alice"]
   ```

9. **Execution & Results:**
   - `cursor.execute(sql, params)` executes on database
   - Results returned as rows
   - `ModelIterable` converts rows to Book instances
   - Yields instances one-by-one

### Interface Contracts

#### as_sql() Protocol
All compilable nodes must implement:
```python
def as_sql(self, compiler, connection) -> tuple[str, list]:
    """Return (SQL string with %s placeholders, parameters list)."""
```

#### resolve_expression() Protocol
Expressions can be late-bound to a Query:
```python
def resolve_expression(self, query, ...) -> Expression:
    """Return expression with query references resolved."""
```

#### get_lookup()/get_transform() Protocol
Fields provide lookup/transform factories:
```python
@Field.register_lookup
class MyLookup(Lookup):
    lookup_name = "my_lookup"
```

#### Backend Operations Interface
Each backend operations class provides:
- `compiler(compiler_name)` → compiler class
- `compiler_module` → module path to vendor compilers
- `operators` → dict mapping lookup names to SQL operators
- `pattern_ops` → dict for LIKE pattern formatting
- `quote_name()` → escape identifiers
- `distinct_sql()` → DISTINCT clause rendering

### Query Optimization Integration

The pipeline supports optimization without recompilation:
1. **Join Promotion:** `add_q()` can promote outer joins to inner based on filter semantics
2. **WHERE vs HAVING:** `WhereNode.split_having_qualify()` separates aggregate/window functions into HAVING/QUALIFY clauses
3. **Deferred Fields:** `defer()/only()` modify select list before compilation
4. **Select Related:** `select_related()` adds extra SELECT columns and JOINs before compilation

## Summary

Django's ORM query compilation follows a **three-phase pipeline**: (1) **Lazy Construction** via QuerySet building a tree-structured Query object with WhereNode leaf nodes as Lookups, (2) **Compilation** via double-dispatch where `SQLCompiler.compile()` first attempts vendor-specific `as_{vendor}()` methods before falling back to generic `as_sql()`, with backend selection via `operations.compiler_module` override, and (3) **Execution** where the compiled SQL is executed against the database and results materialized into model instances. This architecture cleanly separates concerns (query structure, vendor dialects, execution) and enables complex query optimization while maintaining database-agnostic code.
