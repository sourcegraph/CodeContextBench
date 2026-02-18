# Task: Generate Operational Runbook for Prometheus TSDB Compaction

## Objective

Generate a comprehensive operational runbook for the Prometheus TSDB compaction process. The runbook should be written for SRE/operators managing Prometheus instances in production and must be grounded in the actual codebase.

## Repository

The Prometheus repository is cloned at `/workspace`. Focus your investigation on the `tsdb/` directory, particularly:

- `tsdb/compact.go` -- compaction logic and `LeveledCompactor`
- `tsdb/db.go` -- database lifecycle and compaction triggering
- `tsdb/block.go` -- block structure, metadata, and readers
- `tsdb/head.go` -- head block, WAL interaction, and truncation

You should also examine related files such as metric definitions, error handling, and CLI tooling to ensure accuracy.

## Requirements

The runbook must cover the following four areas in depth:

### 1. Monitoring Indicators
Document the Prometheus metrics that signal compaction health. Include specific metric names (e.g., `prometheus_tsdb_compactions_total`, `prometheus_tsdb_compaction_duration_seconds`) and explain what values or trends indicate problems. Cover metrics related to:
- Compaction counts and rates
- Compaction duration and latency
- Block counts (loaded, created)
- WAL health (size, truncations, corruptions)
- Head block state (series, chunks, samples)
- Storage size on disk

### 2. Failure Modes
Describe the concrete failure scenarios an operator may encounter during TSDB compaction, including:
- **Disk full during compaction**: symptoms, how compaction writes temporary data, ENOSPC behavior
- **Corrupted blocks**: causes, detection via checksums, impact on queries
- **OOM during compaction**: memory usage patterns, large block merges, mitigation
- **Overlapping blocks**: how they occur, impact on data integrity, detection
- **WAL corruption**: causes, symptoms, impact on head block recovery

### 3. Recovery Procedures
Provide step-by-step recovery instructions for each failure mode, including:
- Using `promtool tsdb` commands (analyze, clean-tombstones, list, dump)
- Manual block deletion (identifying and removing corrupted block directories)
- Snapshot-based restore (using the `/api/v1/admin/tsdb/snapshot` endpoint)
- WAL replay and truncation recovery (checkpoint behavior, manual WAL cleanup)

### 4. Code References
Ground the runbook in the actual codebase. Reference specific Go source files, structs, and functions that implement the behavior described. For example:
- The `LeveledCompactor` struct and its `Compact()` method in `compact.go`
- The `DB.Compact()` and `DB.reload()` methods in `db.go`
- Block metadata structures (`BlockMeta`) in `block.go`
- Head block truncation logic in `head.go`

## Output

Write the complete runbook to `/workspace/documentation.md`.

## Quality Bar

- Cite specific Prometheus metric names (e.g., `prometheus_tsdb_*` family)
- Reference specific Go functions and file paths from the codebase
- Include actual CLI commands (e.g., `promtool tsdb analyze`, `curl` for snapshot API)
- Provide actionable procedures, not just descriptions
- Target length: 1500+ words covering all four areas

## Anti-Requirements

- Do NOT explain PromQL syntax or how to write alerting rules
- Do NOT cover Prometheus scraping, service discovery, or remote write/read
- Focus exclusively on TSDB internals and compaction operations
