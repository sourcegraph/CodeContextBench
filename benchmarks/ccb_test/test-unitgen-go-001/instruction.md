# Generate Unit Tests for Kubernetes Sets Utility Package

## Objective

Generate comprehensive unit tests for the Kubernetes `sets` utility package located at `staging/src/k8s.io/apimachinery/pkg/util/sets/`. The existing test files have been removed; you must write new tests from scratch.

## Target File

Write your test file to:

```
staging/src/k8s.io/apimachinery/pkg/util/sets/set_test.go
```

## Functions to Test

You must write tests covering the following core functions from the `sets` package:

- `New()` — create a new set from a list of items
- `Insert()` — add elements to a set
- `Delete()` — remove elements from a set
- `Has()` — check if a single element is in the set
- `HasAll()` — check if all specified elements are in the set
- `HasAny()` — check if any of the specified elements are in the set
- `Len()` — return the number of elements in the set
- `Union()` — return the union of two sets
- `Intersection()` — return the intersection of two sets
- `Difference()` — return elements in the first set but not in the second
- `SymmetricDifference()` — return elements in either set but not both
- `IsSuperset()` — check if the set is a superset of another
- `Equal()` — check if two sets are equal
- `List()` — return a sorted slice of elements
- `PopAny()` — remove and return an arbitrary element

## Edge Cases

Your tests must include edge cases such as:

- Empty sets (zero elements)
- Single-element sets
- Nil inputs or zero-value handling
- Large sets (e.g., 100+ elements)
- Sets with duplicate insertions (inserting the same element multiple times)

## Requirements

- Use **table-driven test patterns** (idiomatic Go style)
- Use the standard `testing` package with clear, descriptive test names
- Use **subtests** via `t.Run()` for each test case within table-driven tests
- Cover both **positive cases** (expected success) and **negative cases** (expected failure/absence)
- Tests must compile cleanly with `go vet`
- Do **not** use external test frameworks (e.g., testify, gomega). Use only the Go standard library.

## Quality Bar

- Every core function listed above should have at least one dedicated test
- Tests should be self-contained and not depend on test execution order
- Use clear variable names and test case descriptions
- The test file must declare the correct package (`package sets` or `package sets_test`)
- Import only the `testing` package and, if needed, `sort` or other standard library packages
