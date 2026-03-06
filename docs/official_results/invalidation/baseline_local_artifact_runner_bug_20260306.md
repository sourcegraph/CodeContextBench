# Baseline Local Artifact Runner Bug

Date: 2026-03-06

## Summary

- `baseline-local-artifact` must use `environment/Dockerfile.artifact_baseline`.
- Using `environment/Dockerfile.artifact_only` for baseline is semantically wrong:
  it converts a local-code baseline into an empty-workspace artifact run.
- `runs/analysis/csb_org/...` was checked separately and was sourced from
  `baseline-local-direct`, so it is not part of this runner-bug invalidation set.

## Invalidate

These raw official trials were produced before the missing
`Dockerfile.artifact_baseline` files were backfilled for the affected tasks, so
their historical `baseline-local-artifact` results should be treated as invalid
under the old fallback behavior:

- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-14/bl_ccx-vuln-remed-161_nwcdij__kMhYaaB`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-18/bl_ccx-vuln-remed-162_zvuzze__jrLHQAa`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-22/bl_ccx-vuln-remed-163_ndblbk__MA97hbz`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-26/bl_ccx-vuln-remed-164_p2zsy7__CPGUKRB`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-31/bl_ccx-vuln-remed-165_p0ttqa__fP8KAKT`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-34/bl_ccx-vuln-remed-166_vjelxg__QVvraQ2`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-38/bl_ccx-vuln-remed-167_6vt6iw__MDRGFuW`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-43/bl_ccx-vuln-remed-168_xp7vik__mDPfLZn`
- `runs/official/_raw/csb_org_security_haiku_20260301_201904/baseline-local-artifact/2026-03-01__20-32-47/bl_ccx-vuln-remed-169_ausscm__u4uJ48Y`

Archived location:

- `runs/official/archive/qa_needed/runner_bug_20260306/`

## Checked And Not Invalidated

- `runs/analysis/csb_org/...`: sourced from `baseline-local-direct`, not
  `baseline-local-artifact`
- Raw official artifact trials that map to tasks with
  `Dockerfile.artifact_baseline`
