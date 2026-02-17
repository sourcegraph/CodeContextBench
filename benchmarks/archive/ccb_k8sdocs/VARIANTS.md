# ccb_k8sdocs Environment Variants

This suite keeps `environment/Dockerfile` as the canonical task definition.

## Variant Policy

- Never overwrite canonical `Dockerfile` for official task lineage.
- Variant environments must use separate filenames in the same directory.
- Any run using a variant Dockerfile should be tracked as a separate study.

## Current Files by Task

For each task under `benchmarks/ccb_k8sdocs/*/environment/`:

- `Dockerfile`
  - Canonical environment (full local checkout at pinned commit).
  - This is the default Harbor build target.
- `Dockerfile.isolated`
  - Sparse-checkout environment (target package only).
  - Intended for MCP-isolation experiments where local cross-package context is restricted.
- `Dockerfile.sg_only`
  - Sourcegraph-only local environment (no repo clone; target path scaffold only).
  - Intended for strict MCP-only ablations.

## Notes

- `Dockerfile.isolated` changes task conditions and should not be mixed into the
  canonical official baseline/full series without explicit variant labeling.
- `applyconfig-doc-001` has verifier checks that assume some sibling package
  paths exist; if running isolated/sg-only variants, verify rubric compatibility
  before interpreting score deltas.
