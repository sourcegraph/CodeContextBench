# Multi-Harness Contract

This document defines the required contract for each CodeContextBench harness in this rollout.
It applies to: Codex, Cursor, Gemini, Copilot, and OpenHands.

## Required Registry Fields

Each harness entry must define the following fields:

- `harness_name`: Stable identifier for the harness (`codex`, `cursor`, `gemini`, `copilot`, `openhands`).
- `agent_import_path`: Runtime import path or executable target used by launch scripts.
- `model_default`: Default model identifier for the harness.
- `transcript_artifact_path`: Path or filename pattern used to locate the transcript artifact.
- `result_metadata`: Required result metadata contract.
  - Must include harness identity, model, MCP mode, run timestamp, and task identifier.
  - Must be emitted in a machine-readable structure consumed by downstream reporting.

## MCP Policy For This Rollout

Allowed MCP modes are constrained to exactly:

- `none`
- `sourcegraph_full`

No additional MCP mode values are allowed for this rollout.

## Result Metadata Requirements

Every run output must include result metadata with:

- `harness_name`
- `model`
- `mcp_mode`
- `task_id`
- `run_id`
- `timestamp`
- `transcript_artifact_path`

If a harness cannot produce one of these fields directly, the launcher must populate it before result finalization.

## Transcript Contract

- Harnesses must produce a transcript artifact discoverable from `transcript_artifact_path`.
- Transcript paths must be stable enough for metrics extraction and post-run audits.
- If multiple transcript filenames are possible, the harness must document fallback ordering.

## Conformance Checklist

Use this checklist before promoting harness changes:

- [ ] Codex: defines `harness_name`, `agent_import_path`, `model_default`, `transcript_artifact_path`, and required result metadata.
- [ ] Cursor: defines `harness_name`, `agent_import_path`, `model_default`, `transcript_artifact_path`, and required result metadata.
- [ ] Gemini: defines `harness_name`, `agent_import_path`, `model_default`, `transcript_artifact_path`, and required result metadata.
- [ ] Copilot: defines `harness_name`, `agent_import_path`, `model_default`, `transcript_artifact_path`, and required result metadata.
- [ ] OpenHands: defines `harness_name`, `agent_import_path`, `model_default`, `transcript_artifact_path`, and required result metadata.
- [ ] Codex, Cursor, Gemini, Copilot, and OpenHands allow only `none` and `sourcegraph_full` MCP modes.

