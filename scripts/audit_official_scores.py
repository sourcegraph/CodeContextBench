#!/usr/bin/env python3
"""Audit official run scores for infrastructure health, score legitimacy,
config fairness, and verifier consistency.

Reads:
  - runs/official/MANIFEST.json
  - runs/official/**/task_metrics.json
  - runs/official/**/retrieval_events/**/*.retrieval_metrics.json
  - configs/selected_benchmark_tasks.json
  - benchmarks/{suite}/{task_name}/task.toml
  - benchmarks/{suite}/{task_name}/instruction.md

Produces:
  - JSON report at runs/official/audit_report.json (configurable via --output)
  - Human-readable summary on stdout
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RUNS_DIR = PROJECT_ROOT / "runs" / "official"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
SELECTION_FILE = PROJECT_ROOT / "configs" / "selected_benchmark_tasks.json"

sys.path.insert(0, str(SCRIPT_DIR))
from config_utils import is_mcp_config, is_baseline_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MCP_SUITE_PREFIX = "ccb_mcp_"

# Cache for case-insensitive directory lookups within benchmark suite dirs.
# Maps (suite, task_name_lower) -> actual_dirname on disk.
_BENCHMARK_DIR_CACHE: dict[tuple[str, str], str] = {}
_BENCHMARK_DIR_CACHE_BUILT = False


def _build_benchmark_dir_cache() -> None:
    """Build a case-insensitive lookup cache for benchmark task directories."""
    global _BENCHMARK_DIR_CACHE, _BENCHMARK_DIR_CACHE_BUILT
    if _BENCHMARK_DIR_CACHE_BUILT:
        return
    for suite_dir in BENCHMARKS_DIR.iterdir():
        if not suite_dir.is_dir() or suite_dir.name.startswith("."):
            continue
        suite_name = suite_dir.name
        for task_dir in suite_dir.iterdir():
            if not task_dir.is_dir():
                continue
            _BENCHMARK_DIR_CACHE[(suite_name, task_dir.name.lower())] = task_dir.name
    _BENCHMARK_DIR_CACHE_BUILT = True


def _resolve_task_dir_name(suite: str, task_name: str) -> str:
    """Resolve the on-disk directory name for a task, handling case mismatches.

    MANIFEST may use 'CCX-compliance-124' while the directory is 'ccx-compliance-124'.
    """
    _build_benchmark_dir_cache()
    # Try exact match first
    path = BENCHMARKS_DIR / suite / task_name
    if path.is_dir():
        return task_name
    # Try case-insensitive lookup
    resolved = _BENCHMARK_DIR_CACHE.get((suite, task_name.lower()))
    if resolved:
        return resolved
    return task_name  # Fall back to original name


def _is_mcp_suite(suite: str) -> bool:
    """Check if a suite is an MCP-unique suite."""
    return suite.startswith(MCP_SUITE_PREFIX)


def _parse_toml_simple(path: Path) -> dict[str, Any]:
    """Minimal TOML parser for task.toml files (flat sections only).

    Handles [section] headers and key = "value" / key = number pairs.
    Does not support nested tables, arrays-of-tables, or multi-line strings
    beyond triple-quoted blocks (which are stored as raw strings).
    """
    result: dict[str, Any] = {}
    current_section: Optional[str] = None
    in_multiline: Optional[str] = None
    multiline_buf: list[str] = []

    if not path.is_file():
        return result

    for line in path.read_text(errors="replace").splitlines():
        # Handle multi-line triple-quoted strings
        if in_multiline is not None:
            if '"""' in line:
                multiline_buf.append(line.split('"""')[0])
                result[in_multiline] = "\n".join(multiline_buf)
                in_multiline = None
                multiline_buf = []
            else:
                multiline_buf.append(line)
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Section header
        m = re.match(r"^\[([^\]]+)\]$", stripped)
        if m:
            current_section = m.group(1).replace(".", "_")
            continue

        # Key = value
        m = re.match(r'^(\w+)\s*=\s*(.+)$', stripped)
        if m:
            key = m.group(1)
            val_raw = m.group(2).strip()

            if current_section:
                key = f"{current_section}.{key}"

            # Multi-line triple-quoted
            if val_raw.startswith('"""'):
                rest = val_raw[3:]
                if '"""' in rest:
                    result[key] = rest.split('"""')[0]
                else:
                    in_multiline = key
                    multiline_buf = [rest]
                continue

            # String
            if val_raw.startswith('"') and val_raw.endswith('"'):
                result[key] = val_raw[1:-1]
            elif val_raw in ("true", "false"):
                result[key] = val_raw == "true"
            elif val_raw == "null":
                result[key] = None
            else:
                # Number
                try:
                    result[key] = float(val_raw) if "." in val_raw else int(val_raw)
                except ValueError:
                    # Arrays or other complex types: store as raw string
                    result[key] = val_raw

    return result


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_manifest(path: Path) -> dict:
    """Load MANIFEST.json."""
    if not path.is_file():
        print(f"ERROR: MANIFEST not found at {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def load_selected_tasks(path: Path) -> dict[str, dict]:
    """Load selected_benchmark_tasks.json and return {task_id: task_entry}."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text())
    tasks_list = data.get("tasks", [])
    result = {}
    for t in tasks_list:
        tid = t.get("task_id", t.get("task_name", ""))
        if tid:
            result[tid] = t
    return result


def _normalize_metrics_task_id(raw_id: str) -> str:
    """Normalize a task_id from task_metrics.json to match MANIFEST keys.

    Handles:
    - mcp_ prefix stripping: mcp_CCX-compliance-124_SeYJ2K -> CCX-compliance-124_SeYJ2K
    - Random 6-char hash suffix: CCX-compliance-124_SeYJ2K -> CCX-compliance-124
    - bl_ prefix stripping: bl_CCX-vuln-remed-141_Hv3FTI -> CCX-vuln-remed-141
    """
    name = raw_id
    # Strip mcp_ or bl_ prefix
    if name.startswith("mcp_"):
        name = name[4:]
    elif name.startswith("bl_"):
        name = name[3:]
    # Strip random 6-char suffix (pattern: _[A-Za-z0-9]{6} at end)
    name = re.sub(r"_[A-Za-z0-9]{6}$", "", name)
    return name


def find_task_metrics(runs_dir: Path) -> dict[str, list[dict]]:
    """Find all task_metrics.json files and index them by task_id.

    Returns {task_id: [list of metric dicts]} since the same task may have
    metrics from multiple configs/runs.  Keys are stored under original,
    normalized, and lowered forms for flexible lookup.
    """
    index: dict[str, list[dict]] = defaultdict(list)
    try:
        result = subprocess.run(
            ["find", str(runs_dir), "-name", "task_metrics.json", "-type", "f"],
            capture_output=True, text=True, timeout=30,
        )
        paths = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        paths = []

    for p in paths:
        try:
            data = json.loads(Path(p).read_text())
            tid = data.get("task_id", "")
            if tid:
                data["_metrics_path"] = p
                # Index under original, normalized, and lowered keys
                keys_to_index = {tid}
                normalized = _normalize_metrics_task_id(tid)
                keys_to_index.add(normalized)
                keys_to_index.add(tid.lower())
                keys_to_index.add(normalized.lower())
                for key in keys_to_index:
                    if key:
                        index[key].append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return dict(index)


def find_retrieval_metrics(runs_dir: Path) -> dict[str, list[dict]]:
    """Find all *.retrieval_metrics.json files and index by task name.

    These are in retrieval_events/{config}/{task_name}.retrieval_metrics.json
    Returns {task_name: [list of metric dicts]}.
    """
    index: dict[str, list[dict]] = defaultdict(list)
    try:
        result = subprocess.run(
            ["find", str(runs_dir), "-name", "*.retrieval_metrics.json", "-type", "f"],
            capture_output=True, text=True, timeout=30,
        )
        paths = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        paths = []

    for p in paths:
        try:
            data = json.loads(Path(p).read_text())
            # Extract task name from filename: {task_name}.retrieval_metrics.json
            fname = Path(p).name
            task_name = fname.replace(".retrieval_metrics.json", "")
            data["_metrics_path"] = p
            data["_task_name"] = task_name
            index[task_name].append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return dict(index)


def load_task_toml(suite: str, task_name: str) -> dict:
    """Load and parse task.toml for a benchmark task."""
    resolved = _resolve_task_dir_name(suite, task_name)
    path = BENCHMARKS_DIR / suite / resolved / "task.toml"
    return _parse_toml_simple(path)


def load_instruction_md(suite: str, task_name: str) -> Optional[str]:
    """Load instruction.md content for a benchmark task."""
    resolved = _resolve_task_dir_name(suite, task_name)
    path = BENCHMARKS_DIR / suite / resolved / "instruction.md"
    if not path.is_file():
        return None
    try:
        return path.read_text(errors="replace")
    except OSError:
        return None


def load_task_spec(suite: str, task_name: str) -> Optional[dict]:
    """Load task_spec.json for MCP-unique tasks."""
    resolved = _resolve_task_dir_name(suite, task_name)
    path = BENCHMARKS_DIR / suite / resolved / "tests" / "task_spec.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Audit checks
# ---------------------------------------------------------------------------

def check_infrastructure_health(
    run_key: str,
    task_name: str,
    task_data: dict,
    task_metrics_index: dict[str, list[dict]],
) -> list[dict]:
    """Check A: Infrastructure health for a single task.

    Returns list of flag dicts (may be empty if clean).
    """
    flags = []
    suite = run_key.split("/")[0]
    config = run_key.split("/")[1] if "/" in run_key else "unknown"

    status = task_data.get("status", "unknown")
    has_trajectory = task_data.get("has_trajectory", False)
    has_cost = task_data.get("has_cost", False)

    # Errored with no trajectory = agent never ran (infra failure)
    if status == "errored" and not has_trajectory:
        flags.append({
            "type": "infra_failure",
            "run_key": run_key,
            "task": task_name,
            "config": config,
            "detail": "Status 'errored' with no trajectory — agent never ran (infra failure)",
        })

    # Check for task_metrics.json
    # Task metrics may be keyed by task_name or by a CCX-style ID.
    # The index stores entries under both original case and lowered key.
    metrics_found = False
    metrics_entries = task_metrics_index.get(task_name, [])
    if not metrics_entries:
        # Try case-insensitive and variant lookups
        ccx_variants = [
            task_name.lower(),
            task_name.upper(),
            task_name.replace("-", "_"),
            "CCX-" + task_name.split("-", 1)[-1] if task_name.lower().startswith("ccx-") else "",
            "ccx-" + task_name.split("-", 1)[-1] if task_name.upper().startswith("CCX-") else "",
        ]
        for variant in ccx_variants:
            if variant and variant in task_metrics_index:
                metrics_entries = task_metrics_index[variant]
                break

    if metrics_entries:
        metrics_found = True
        # Check if any matching metrics entry has nonzero tokens/tool_calls
        # for this specific config
        relevant_metrics = [
            m for m in metrics_entries
            if m.get("config_name", "") == config
            or config in m.get("_metrics_path", "")
        ]
        if not relevant_metrics:
            # Fall back to all metrics for this task
            relevant_metrics = metrics_entries

        for m in relevant_metrics:
            total_tokens = (
                (m.get("input_tokens") or 0)
                + (m.get("output_tokens") or 0)
                + (m.get("cache_creation_tokens") or 0)
                + (m.get("cache_read_tokens") or 0)
            )
            total_tool_calls = m.get("tool_calls_total") or 0

            if total_tokens == 0 and total_tool_calls == 0 and status != "errored":
                flags.append({
                    "type": "agent_did_nothing",
                    "run_key": run_key,
                    "task": task_name,
                    "config": config,
                    "detail": (
                        f"task_metrics.json exists but total_tokens=0 and "
                        f"total_tool_calls=0 — agent did nothing"
                    ),
                    "metrics_path": m.get("_metrics_path", ""),
                })
    else:
        # Only flag missing metrics for non-errored tasks (errored tasks
        # may never have produced metrics)
        if status != "errored":
            flags.append({
                "type": "missing_metrics",
                "run_key": run_key,
                "task": task_name,
                "config": config,
                "detail": "task_metrics.json not found for this task",
            })

    return flags


def check_score_legitimacy(
    run_key: str,
    task_name: str,
    task_data: dict,
    suite: str,
    task_spec: Optional[dict],
) -> list[dict]:
    """Check B: Score legitimacy for a single task.

    Returns list of flag dicts.
    """
    flags = []
    config = run_key.split("/")[1] if "/" in run_key else "unknown"
    status = task_data.get("status", "unknown")
    reward = task_data.get("reward", 0.0)

    # Passed but reward is 0.0 — contradictory
    if status == "passed" and reward == 0.0:
        flags.append({
            "type": "score_anomaly",
            "run_key": run_key,
            "task": task_name,
            "config": config,
            "detail": "Status is 'passed' but reward is 0.0 — contradictory",
        })

    # Errored but reward > 0 — suspicious
    if status == "errored" and reward > 0:
        flags.append({
            "type": "score_anomaly",
            "run_key": run_key,
            "task": task_name,
            "config": config,
            "detail": f"Status is 'errored' but reward is {reward} > 0 — suspicious",
        })

    # For MCP-unique tasks, check oracle alignment
    if _is_mcp_suite(suite) and task_spec is not None:
        oracle = (task_spec.get("artifacts") or {}).get("oracle", {})
        evaluation = task_spec.get("evaluation", {})
        checks = evaluation.get("checks", [])

        # Check if oracle has meaningful content
        required_files = oracle.get("required_files", [])
        required_symbols = oracle.get("required_symbols", [])
        dependency_chains = oracle.get("dependency_chains", [])
        required_references = oracle.get("required_references", [])

        oracle_populated = (
            bool(required_files)
            or bool(required_symbols)
            or bool(dependency_chains)
            or bool(required_references)
        )

        # If evaluation checks exist but oracle is empty, the oracle_checks
        # evaluator may produce vacuous passes
        if checks and not oracle_populated:
            flags.append({
                "type": "score_anomaly",
                "subtype": "empty_oracle",
                "run_key": run_key,
                "task": task_name,
                "config": config,
                "detail": (
                    "MCP-unique task has evaluation checks in task_spec.json "
                    "but oracle arrays are all empty — oracle_checks evaluator "
                    "may produce vacuous scores"
                ),
            })

    return flags


def check_config_fairness(
    manifest_runs: dict,
) -> tuple[list[dict], dict]:
    """Check C: Config fairness across paired tasks.

    Returns (list of flag dicts, paired_comparison summary dict).
    """
    flags = []

    # Group runs by suite + task to find pairs
    # Key: (suite, task_name) -> {config: task_data}
    task_configs: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)

    for run_key, run_data in manifest_runs.items():
        parts = run_key.split("/")
        suite = parts[0]
        config = parts[1] if len(parts) > 1 else "unknown"
        for task_name, task_data in run_data.get("tasks", {}).items():
            task_configs[(suite, task_name)][config] = task_data

    # Analyze pairs
    total_pairs = 0
    mcp_helps = 0
    mcp_hurts = 0
    mcp_neutral = 0
    both_errored = 0
    one_errored = 0

    for (suite, task_name), configs in task_configs.items():
        # Find baseline and MCP configs
        baseline_configs = {
            c: d for c, d in configs.items() if is_baseline_config(c)
        }
        mcp_configs = {
            c: d for c, d in configs.items() if is_mcp_config(c)
        }

        # Skip tasks with only one config type
        if not baseline_configs or not mcp_configs:
            continue

        # Compare each baseline-MCP pair
        for bl_name, bl_data in baseline_configs.items():
            for mcp_name, mcp_data in mcp_configs.items():
                total_pairs += 1
                bl_status = bl_data.get("status", "unknown")
                mcp_status = mcp_data.get("status", "unknown")
                bl_reward = bl_data.get("reward", 0.0)
                mcp_reward = mcp_data.get("reward", 0.0)
                bl_has_traj = bl_data.get("has_trajectory", False)
                mcp_has_traj = mcp_data.get("has_trajectory", False)

                # Both errored
                if bl_status == "errored" and mcp_status == "errored":
                    both_errored += 1
                    continue

                # One errored
                if bl_status == "errored" or mcp_status == "errored":
                    one_errored += 1
                    errored_side = bl_name if bl_status == "errored" else mcp_name
                    success_side = mcp_name if bl_status == "errored" else bl_name
                    flags.append({
                        "type": "config_fairness",
                        "subtype": "asymmetric_error",
                        "suite": suite,
                        "task": task_name,
                        "detail": (
                            f"Config '{errored_side}' errored but "
                            f"'{success_side}' succeeded — asymmetric infra failure"
                        ),
                        "errored_config": errored_side,
                        "success_config": success_side,
                    })
                    continue

                # Both completed — compare rewards
                if mcp_reward > bl_reward + 0.001:
                    mcp_helps += 1
                elif bl_reward > mcp_reward + 0.001:
                    mcp_hurts += 1
                else:
                    mcp_neutral += 1

                # Check trajectory presence asymmetry
                if bl_has_traj and not mcp_has_traj:
                    flags.append({
                        "type": "config_fairness",
                        "subtype": "missing_trajectory",
                        "suite": suite,
                        "task": task_name,
                        "detail": (
                            f"Baseline '{bl_name}' has trajectory but "
                            f"MCP '{mcp_name}' does not"
                        ),
                    })
                elif mcp_has_traj and not bl_has_traj:
                    flags.append({
                        "type": "config_fairness",
                        "subtype": "missing_trajectory",
                        "suite": suite,
                        "task": task_name,
                        "detail": (
                            f"MCP '{mcp_name}' has trajectory but "
                            f"baseline '{bl_name}' does not"
                        ),
                    })

    paired_comparison = {
        "total_pairs": total_pairs,
        "mcp_helps": mcp_helps,
        "mcp_hurts": mcp_hurts,
        "mcp_neutral": mcp_neutral,
        "both_errored": both_errored,
        "one_errored": one_errored,
    }

    return flags, paired_comparison


def check_verifier_consistency(
    run_key: str,
    task_name: str,
    suite: str,
) -> list[dict]:
    """Check D: Verifier consistency for a task.

    Returns list of flag dicts.
    """
    flags = []
    config = run_key.split("/")[1] if "/" in run_key else "unknown"

    # Load task.toml
    toml_data = load_task_toml(suite, task_name)

    # For MCP-unique tasks, check verification command path
    if _is_mcp_suite(suite):
        verify_cmd = toml_data.get("verification.command", "")
        if verify_cmd:
            # The correct path is /tests/test.sh (Harbor uploads tests/ to /tests/)
            if "/workspace/tests/" in verify_cmd:
                flags.append({
                    "type": "verifier_issue",
                    "subtype": "wrong_test_path",
                    "run_key": run_key,
                    "task": task_name,
                    "config": config,
                    "detail": (
                        f"verification_info.command uses '/workspace/tests/' "
                        f"but Harbor uploads tests to '/tests/' — command: {verify_cmd}"
                    ),
                })
        else:
            # No verification command at all
            if not toml_data:
                flags.append({
                    "type": "verifier_issue",
                    "subtype": "missing_task_toml",
                    "run_key": run_key,
                    "task": task_name,
                    "config": config,
                    "detail": "task.toml not found or empty for this task",
                })

    # Check instruction.md exists and has meaningful content
    instruction = load_instruction_md(suite, task_name)
    if instruction is None:
        flags.append({
            "type": "verifier_issue",
            "subtype": "missing_instruction",
            "run_key": run_key,
            "task": task_name,
            "config": config,
            "detail": "instruction.md not found",
        })
    elif len(instruction.strip()) < 50:
        flags.append({
            "type": "verifier_issue",
            "subtype": "stub_instruction",
            "run_key": run_key,
            "task": task_name,
            "config": config,
            "detail": (
                f"instruction.md exists but is very short "
                f"({len(instruction.strip())} chars) — may be a stub"
            ),
        })

    return flags


# ---------------------------------------------------------------------------
# Main audit orchestration
# ---------------------------------------------------------------------------

def run_audit(
    manifest_path: Path,
    output_path: Path,
    verbose: bool = False,
) -> dict:
    """Run the full audit and return the report dict."""

    print("=" * 72)
    print("  CodeContextBench Official Score Audit")
    print("=" * 72)
    print()

    # Load all data sources
    print("[1/6] Loading MANIFEST.json ...")
    manifest = load_manifest(manifest_path)
    manifest_runs = manifest.get("runs", {})
    print(f"       {len(manifest_runs)} run entries, "
          f"{manifest.get('total_tasks', 0)} total tasks")

    print("[2/6] Indexing task_metrics.json files ...")
    task_metrics_index = find_task_metrics(RUNS_DIR)
    total_metrics = sum(len(v) for v in task_metrics_index.values())
    print(f"       {total_metrics} metrics files across "
          f"{len(task_metrics_index)} unique task IDs")

    print("[3/6] Indexing retrieval_metrics.json files ...")
    retrieval_metrics_index = find_retrieval_metrics(RUNS_DIR)
    total_retrieval = sum(len(v) for v in retrieval_metrics_index.values())
    print(f"       {total_retrieval} retrieval metrics files across "
          f"{len(retrieval_metrics_index)} unique task names")

    print("[4/6] Loading selected_benchmark_tasks.json ...")
    selected_tasks = load_selected_tasks(SELECTION_FILE)
    print(f"       {len(selected_tasks)} selected tasks")

    print("[5/6] Running audit checks ...")
    print()

    # Collect all flags
    all_infra_flags: list[dict] = []
    all_metrics_flags: list[dict] = []
    all_score_flags: list[dict] = []
    all_fairness_flags: list[dict] = []
    all_verifier_flags: list[dict] = []

    total_tasks_audited = 0
    errored_tasks = 0
    clean_tasks = 0
    flagged_task_set: set[str] = set()
    by_category: dict[str, int] = defaultdict(int)
    tasks_by_suite: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "passed": 0, "failed": 0, "errored": 0}
    )

    # Deduplicate: track which (suite, task) combos we've checked for
    # verifier consistency to avoid repeated flags
    verified_tasks: set[tuple[str, str]] = set()

    for run_key, run_data in manifest_runs.items():
        suite = run_key.split("/")[0]
        config = run_key.split("/")[1] if "/" in run_key else "unknown"

        for task_name, task_data in run_data.get("tasks", {}).items():
            total_tasks_audited += 1
            status = task_data.get("status", "unknown")

            # Track suite stats
            tasks_by_suite[suite]["total"] += 1
            if status == "errored":
                tasks_by_suite[suite]["errored"] += 1
                errored_tasks += 1
            elif status == "passed":
                tasks_by_suite[suite]["passed"] += 1
            else:
                tasks_by_suite[suite]["failed"] += 1

            task_flagged = False

            # A. Infrastructure Health
            infra_flags = check_infrastructure_health(
                run_key, task_name, task_data, task_metrics_index
            )
            for f in infra_flags:
                ftype = f["type"]
                if ftype == "infra_failure":
                    all_infra_flags.append(f)
                elif ftype == "missing_metrics":
                    all_metrics_flags.append(f)
                elif ftype == "agent_did_nothing":
                    all_infra_flags.append(f)
                task_flagged = True

            # B. Score Legitimacy
            task_spec = None
            if _is_mcp_suite(suite):
                task_spec = load_task_spec(suite, task_name)
            score_flags = check_score_legitimacy(
                run_key, task_name, task_data, suite, task_spec
            )
            if score_flags:
                all_score_flags.extend(score_flags)
                task_flagged = True

            # D. Verifier Consistency (deduplicated per suite+task)
            if (suite, task_name) not in verified_tasks:
                verified_tasks.add((suite, task_name))
                verifier_flags = check_verifier_consistency(
                    run_key, task_name, suite
                )
                if verifier_flags:
                    all_verifier_flags.extend(verifier_flags)
                    task_flagged = True

            if task_flagged:
                flagged_task_set.add(f"{run_key}/{task_name}")
            else:
                clean_tasks += 1

    # C. Config Fairness (cross-run comparison)
    fairness_flags, paired_comparison = check_config_fairness(manifest_runs)
    all_fairness_flags.extend(fairness_flags)

    # Update flagged count for fairness issues
    for f in fairness_flags:
        suite = f.get("suite", "")
        task = f.get("task", "")
        flagged_task_set.add(f"{suite}/{task}")

    print("[6/6] Building report ...")
    print()

    # Build category breakdown
    for suite_name, stats in tasks_by_suite.items():
        by_category[suite_name] = stats

    # Build report
    report = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tasks_audited": total_tasks_audited,
        "flags": {
            "infra_failures": all_infra_flags,
            "missing_metrics": all_metrics_flags,
            "score_anomalies": all_score_flags,
            "config_fairness_issues": all_fairness_flags,
            "verifier_issues": all_verifier_flags,
        },
        "summary": {
            "clean_tasks": clean_tasks,
            "flagged_tasks": len(flagged_task_set),
            "errored_tasks": errored_tasks,
            "by_category": dict(by_category),
        },
        "paired_comparison": paired_comparison,
    }

    # Write JSON report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"JSON report written to: {output_path}")
    print()

    # Print human-readable summary
    _print_summary(report, verbose=verbose)

    return report


def _print_summary(report: dict, verbose: bool = False) -> None:
    """Print human-readable audit summary to stdout."""
    summary = report["summary"]
    flags = report["flags"]
    paired = report["paired_comparison"]

    print("=" * 72)
    print("  AUDIT SUMMARY")
    print("=" * 72)
    print()
    print(f"  Total tasks audited:   {report['total_tasks_audited']}")
    print(f"  Clean tasks:           {summary['clean_tasks']}")
    print(f"  Flagged tasks:         {summary['flagged_tasks']}")
    print(f"  Errored tasks:         {summary['errored_tasks']}")
    print()

    # Flag counts
    print("  Flag Counts:")
    print(f"    Infrastructure failures:   {len(flags['infra_failures'])}")
    print(f"    Missing metrics:           {len(flags['missing_metrics'])}")
    print(f"    Score anomalies:           {len(flags['score_anomalies'])}")
    print(f"    Config fairness issues:    {len(flags['config_fairness_issues'])}")
    print(f"    Verifier issues:           {len(flags['verifier_issues'])}")
    print()

    # Paired comparison
    if paired["total_pairs"] > 0:
        print("  Paired Comparison (Baseline vs MCP):")
        print(f"    Total pairs:     {paired['total_pairs']}")
        print(f"    MCP helps:       {paired['mcp_helps']}")
        print(f"    MCP hurts:       {paired['mcp_hurts']}")
        print(f"    MCP neutral:     {paired['mcp_neutral']}")
        print(f"    Both errored:    {paired['both_errored']}")
        print(f"    One errored:     {paired['one_errored']}")
        print()

    # Suite breakdown
    by_cat = summary.get("by_category", {})
    if by_cat:
        print("  Per-Suite Breakdown:")
        print(f"    {'Suite':<40s} {'Total':>6s} {'Pass':>6s} {'Fail':>6s} {'Error':>6s}")
        print(f"    {'-'*40} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")
        for suite_name in sorted(by_cat.keys()):
            stats = by_cat[suite_name]
            print(
                f"    {suite_name:<40s} "
                f"{stats['total']:>6d} "
                f"{stats['passed']:>6d} "
                f"{stats['failed']:>6d} "
                f"{stats['errored']:>6d}"
            )
        print()

    # Verbose: list all flags
    if verbose:
        for flag_category, flag_list in flags.items():
            if not flag_list:
                continue
            print(f"  --- {flag_category.upper()} ({len(flag_list)}) ---")
            for f in flag_list:
                task = f.get("task", "?")
                config = f.get("config", f.get("errored_config", "?"))
                detail = f.get("detail", "")
                run_key = f.get("run_key", f.get("suite", "?"))
                print(f"    [{run_key}] {task} ({config})")
                print(f"      {detail}")
            print()
    else:
        # Non-verbose: show only top issues per category
        for flag_category, flag_list in flags.items():
            if not flag_list:
                continue
            shown = min(3, len(flag_list))
            remaining = len(flag_list) - shown
            print(f"  --- {flag_category.replace('_', ' ').upper()} "
                  f"(showing {shown}/{len(flag_list)}) ---")
            for f in flag_list[:shown]:
                task = f.get("task", "?")
                config = f.get("config", f.get("errored_config", "?"))
                detail = f.get("detail", "")
                print(f"    {task} ({config}): {detail}")
            if remaining > 0:
                print(f"    ... and {remaining} more (use --verbose to see all)")
            print()

    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Audit official CodeContextBench scores for legitimacy, "
                    "fairness, and infrastructure health.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/audit_official_scores.py\n"
            "  python3 scripts/audit_official_scores.py --verbose\n"
            "  python3 scripts/audit_official_scores.py --output /tmp/audit.json\n"
            "  python3 scripts/audit_official_scores.py --manifest runs/official/MANIFEST.json\n"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=RUNS_DIR / "MANIFEST.json",
        help="Path to MANIFEST.json (default: runs/official/MANIFEST.json)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=RUNS_DIR / "audit_report.json",
        help="Output path for JSON report (default: runs/official/audit_report.json)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print all flags in detail (default: show top 3 per category)",
    )
    args = parser.parse_args()

    run_audit(
        manifest_path=args.manifest,
        output_path=args.output,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
