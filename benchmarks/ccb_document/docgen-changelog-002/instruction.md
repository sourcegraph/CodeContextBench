# Task: Generate Release Notes for Flipt v2.6.0 to v2.7.0 API Changes

## Objective

Generate release notes summarizing the API changes between Flipt v2.6.0 and v2.7.0. The release notes should be written for consumers of Flipt's public API (gRPC and REST) and highlight what changed, what was deprecated, and what is new.

## Environment

The workspace contains two worktrees for side-by-side comparison:

- `/workspace/v2.6.0/` -- the Flipt source tree at the v2.6.0 release tag
- `/workspace/v2.7.0/` -- the Flipt source tree at the v2.7.0 release tag
- `/workspace/commit_log.txt` -- the commit log between the two versions

## Scope

Focus on the **gRPC and REST API surface**. This includes:

1. **Proto definitions** (`.proto` files) -- service definitions, message types, field changes
2. **HTTP handlers and REST routes** -- new endpoints, changed endpoints, removed endpoints
3. **SDK and client-facing changes** -- request/response type modifications, new client methods
4. **Configuration and admin API** -- management endpoints, feature flag administration
5. **Authentication and authorization** -- token changes, RBAC modifications, access control updates
6. **Evaluation engine** -- flag evaluation endpoints, boolean/variant evaluation changes

## Requirements

Your release notes must cover the following areas:

1. **Breaking Changes**: Identify any backward-incompatible API changes between v2.6.0 and v2.7.0. Note changes to proto/gRPC interfaces, REST endpoint modifications, and any SDK or client impact.

2. **Deprecations**: Document deprecated endpoints, fields, feature flags, or configuration options. Include deprecation timelines or sunset information if evident from the code. Provide migration paths or replacement recommendations.

3. **New Features**: Document newly added API endpoints, evaluation engine changes, configuration or admin API additions, and authentication/authorization enhancements.

4. **Migration Notes**: Where applicable, provide guidance on how users should update their integrations when moving from v2.6.0 to v2.7.0.

## Quality Bar

- Reference specific proto definitions, endpoint paths, or struct fields that changed
- Provide enough detail that API consumers can assess the impact on their integrations
- Organize content in standard release-notes style with clear section headers

## Anti-Requirements

- Do NOT include internal refactoring that does not affect the public API surface
- Do NOT document changes to build tooling, CI/CD, or internal test infrastructure
- Do NOT include cosmetic code style changes that have no functional API impact

## Deliverable

Write your release notes to `/workspace/documentation.md` in Markdown format.
