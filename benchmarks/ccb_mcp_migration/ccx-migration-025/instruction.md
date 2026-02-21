# Deprecated API Migration Inventory: numpy.distutils

## Your Task

Your team is planning a cleanup of the deprecated `numpy.distutils` module, which was
deprecated in NumPy 1.23 and removed in NumPy 2.0. Before completing the migration,
you need to identify every Python source file across the Python ML ecosystem that still
references `numpy.distutils` — either importing it, vendoring code from it, or
referencing it in help text.

**Specific question**: Which Python source files (`.py`) across the `numpy/numpy` and
`scipy/scipy` repositories still contain references to `numpy.distutils`?

Include files that:
- Import `numpy.distutils` or any of its submodules
- Contain vendored code originally from `numpy.distutils` (marked by comments)
- Reference `numpy.distutils` in help strings or docstrings

Do NOT include:
- Documentation files (`.rst`, `.md`, `.txt`)
- Release notes or changelogs
- Files inside the now-removed `numpy/distutils/` package directory itself (the definition, not consumers)

## Context

The `numpy.distutils` module provided enhanced distutils support for building C/Fortran
extensions. It was deprecated in favor of Meson build system. While `scikit-learn` and
`pandas` have fully migrated (zero references remain), `numpy` itself and `scipy` still
have residual references in vendored code and help strings.

## Available Resources

The local `/workspace/` directory contains all repositories:
- `numpy/numpy` at v2.2.2 → `/workspace/numpy`
- `scipy/scipy` at v1.15.1 → `/workspace/scipy`
- `scikit-learn/scikit-learn` at 1.6.1 → `/workspace/scikit-learn`
- `pandas-dev/pandas` at v2.2.3 → `/workspace/pandas`

## Output Format

Create a file at `/workspace/answer.json` with your findings:

```json
{
  "files": [
    {"repo": "numpy/numpy", "path": "relative/path/to/file.py"}
  ],
  "text": "Narrative explanation of your findings, citing repos and file paths."
}
```

**Important**: Use canonical repo names (e.g., `numpy/numpy`, `scipy/scipy`).
**Note**: Sourcegraph MCP tools return repo names with a `github.com/` prefix. Strip this prefix in your answer.

Include only the `files` field with `.py` source files. Your answer is evaluated against a closed-world oracle — completeness matters.

## Evaluation

Your answer will be scored on:
- **File recall and precision**: Did you find all relevant `.py` files that reference `numpy.distutils`?
- **Keyword presence**: Does your narrative mention key terms like `numpy.distutils`, `deprecated`, and `vendored`?
