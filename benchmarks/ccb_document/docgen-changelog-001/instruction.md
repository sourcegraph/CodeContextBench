# Task: Generate Changelog for Terraform v1.9.0 to v1.10.0

## Objective

Generate a developer-facing changelog entry summarizing the changes between Terraform v1.9.0 and v1.10.0. The changelog should categorize changes clearly and reference specific commits, PR numbers, or issue numbers where identifiable.

## Environment

Your workspace contains two worktrees for direct comparison:

- `/workspace/v1.9.0/` -- Terraform source at the v1.9.0 release tag
- `/workspace/v1.10.0/` -- Terraform source at the v1.10.0 release tag
- `/workspace/commit_log.txt` -- git log (oneline) of all commits between the two versions

## Requirements

### Categories

Organize changes into the following sections:

1. **Features** -- New capabilities and enhancements
2. **Bug Fixes** -- Corrections to existing behavior
3. **Breaking Changes** -- Changes that may require user action or are backward-incompatible
4. **Deprecations** -- Features or behaviors being phased out
5. **Internal/Refactoring** -- Code improvements not directly visible to users (keep this section brief)

### Content Quality

- **Summarize user-visible behavior changes**, not just file diffs. Each entry should describe what changed from a user's perspective.
- **Reference specific commit hashes, PR numbers, or issue numbers** where they are identifiable from commit messages or code comments.
- **Identify the major changes** in this release. Key changes between v1.9.0 and v1.10.0 include (but are not limited to):
  - S3 backend native state locking (replacing the DynamoDB requirement)
  - Provider installation and caching improvements
  - Ephemeral resources and write-only attributes
  - Terraform test command enhancements
  - HCP Terraform integration changes
  - Moved block enhancements for refactoring
- **Focus on user-facing changes.** Do not list every single commit. Group related commits where appropriate and highlight the changes that matter to Terraform users and operators.

### Format

Use standard CHANGELOG.md format:

```
## [v1.10.0]

### Features
- Description of feature (PR #NNNN or commit hash)

### Bug Fixes
- Description of fix (PR #NNNN or commit hash)

### Breaking Changes
- Description of breaking change

### Deprecations
- Description of deprecation

### Internal/Refactoring
- Brief summary of internal changes
```

## Deliverable

Write your changelog to `/workspace/documentation.md`.

## Anti-Requirements

- Do NOT produce a raw list of every commit message -- curate and summarize.
- Do NOT focus on internal code structure changes at the expense of user-facing behavior.
- Do NOT omit version references or commit/PR identifiers where they are available.

## Success Criteria

Your changelog will be evaluated on:
- **Change categorization** (40%): Are changes correctly classified into the right sections? Are key features like S3 native locking and ephemeral resources properly categorized?
- **Completeness** (30%): Does the changelog cover the major changes in the release?
- **Issue/commit references** (30%): Does the changelog include commit hashes, PR numbers, version tags, and relevant file paths?
