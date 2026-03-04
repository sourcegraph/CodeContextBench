#!/usr/bin/env python3
"""Paired MCP-vs-baseline cost analysis from runs/official/_raw.

Pairing rules produced:
  1) latest_task: canonical headline method
     - key by (model, normalized_task_id)
     - keep latest valid run per side
     - require both sides; one pair per task
  2) count_matched: sensitivity method
     - key by (model, normalized_task_id)
     - pair count = min(n_baseline, n_mcp)
     - newest-first matching on started_at within each side bucket

This script writes:
  - docs/analysis/mcp_cost_pairs_official_raw_YYYYMMDD.json
  - docs/assets/blog/codescalebench_mcp/figure_7_cost_pairing_by_model_and_size.{png,svg}
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "runs" / "official" / "_raw"
TASK_META_PATH = ROOT / "configs" / "selected_benchmark_tasks.json"
ANALYSIS_DIR = ROOT / "docs" / "analysis"
ASSET_DIR = ROOT / "docs" / "assets" / "blog" / "codescalebench_mcp"

PALETTE = {
    "bg": "#020202",
    "text": "#ededed",
    "text_secondary": "#a9a9a9",
    "grid": "#343434",
    "pos": "#8552f2",   # MCP better/cheaper
    "neg": "#ff7867",   # MCP worse/more expensive
    "base": "#6b7280",
}


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PALETTE["bg"],
            "axes.facecolor": PALETTE["bg"],
            "axes.edgecolor": PALETTE["grid"],
            "axes.labelcolor": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "text.color": PALETTE["text"],
            "grid.color": PALETTE["grid"],
            "font.family": "sans-serif",
            "font.sans-serif": ["Poly Sans", "Arial", "DejaVu Sans", "sans-serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
        }
    )


def _normalize_task_id(raw: str) -> str:
    task = (raw or "").strip().lower()
    task = re.sub(r"^(mcp_|bl_|sgonly_)", "", task)
    task = re.sub(r"^sdlc_[a-z]+_", "", task)
    task = re.sub(r"_[a-z0-9]{6,8}$", "", task)
    return task


def _normalize_task_from_dirname(dirname: str) -> str:
    task = dirname
    if "__" in task:
        task = task.split("__", 1)[0]
    return _normalize_task_id(task)


def _infer_model(run_name: str) -> str | None:
    m = re.search(r"(haiku|sonnet|opus)", run_name, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _classify_side(config_name: str) -> str | None:
    name = config_name.lower()
    if "baseline" in name:
        return "baseline"
    if "mcp" in name or "sourcegraph" in name:
        return "mcp"
    return None


def _is_valid(metrics: dict) -> bool:
    out = metrics.get("output_tokens")
    if out is not None and out == 0:
        return False
    agent_sec = metrics.get("agent_execution_seconds")
    if agent_sec is not None and agent_sec < 10:
        return False
    return True


def _context_bin(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value < 100_000:
        return "<100k"
    if value < 1_000_000:
        return "100k-1m"
    return ">=1m"


def _files_bin(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value < 10:
        return "<10"
    if value <= 100:
        return "10-100"
    return ">100"


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _collect_task_meta() -> dict[str, dict]:
    try:
        doc = json.loads(TASK_META_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    out = {}
    for t in doc.get("tasks", []):
        task_id = _normalize_task_id(str(t.get("task_id", "")))
        if task_id:
            out[task_id] = t
    return out


def _collect_records() -> list[dict]:
    records = []
    for tm_path in RAW_DIR.rglob("task_metrics.json"):
        rel = tm_path.relative_to(RAW_DIR)
        run_name = rel.parts[0]
        model = _infer_model(run_name)
        if model not in {"haiku", "sonnet", "opus"}:
            continue

        config_name = None
        for part in rel.parts[1:]:
            side = _classify_side(part)
            if side is not None:
                config_name = part
                break
        if not config_name:
            continue
        side = _classify_side(config_name)
        if side is None:
            continue

        try:
            metrics = json.loads(tm_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue

        raw_task = metrics.get("task_id")
        task_id = _normalize_task_id(raw_task) if isinstance(raw_task, str) and raw_task else None
        if not task_id:
            task_id = _normalize_task_from_dirname(tm_path.parent.name)
        if not task_id:
            continue

        started_at = ""
        result_path = tm_path.parent / "result.json"
        if result_path.is_file():
            try:
                started_at = (json.loads(result_path.read_text()).get("started_at") or "")
            except (OSError, json.JSONDecodeError):
                pass

        records.append(
            {
                "model": model,
                "task_id": task_id,
                "side": side,
                "cost_usd": float(metrics.get("cost_usd") or 0.0),
                "input_tokens": int(metrics.get("input_tokens") or 0),
                "output_tokens": int(metrics.get("output_tokens") or 0),
                "valid": _is_valid(metrics),
                "started_at": started_at,
            }
        )
    return records


def _pair_records_count_matched(records: list[dict], valid_only: bool) -> list[dict]:
    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in records:
        if valid_only and not r["valid"]:
            continue
        buckets[(r["model"], r["task_id"], r["side"])].append(r)

    for key in buckets:
        buckets[key].sort(key=lambda x: x["started_at"], reverse=True)

    pairs = []
    task_keys = {(m, t) for (m, t, _s) in buckets.keys()}
    for model, task in task_keys:
        bl = buckets.get((model, task, "baseline"), [])
        mc = buckets.get((model, task, "mcp"), [])
        n = min(len(bl), len(mc))
        if n == 0:
            continue
        for i in range(n):
            pairs.append(
                {
                    "model": model,
                    "task_id": task,
                    "baseline_cost_usd": bl[i]["cost_usd"],
                    "mcp_cost_usd": mc[i]["cost_usd"],
                    "baseline_input_tokens": bl[i]["input_tokens"],
                    "mcp_input_tokens": mc[i]["input_tokens"],
                    "baseline_output_tokens": bl[i]["output_tokens"],
                    "mcp_output_tokens": mc[i]["output_tokens"],
                }
            )
    return pairs


def _pair_records_latest_task(records: list[dict], valid_only: bool) -> list[dict]:
    """One pair per (model, task_id), using latest record per side."""
    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in records:
        if valid_only and not r["valid"]:
            continue
        buckets[(r["model"], r["task_id"], r["side"])].append(r)

    for key in buckets:
        buckets[key].sort(key=lambda x: x["started_at"], reverse=True)

    pairs = []
    task_keys = {(m, t) for (m, t, _s) in buckets.keys()}
    for model, task in task_keys:
        bl = buckets.get((model, task, "baseline"), [])
        mc = buckets.get((model, task, "mcp"), [])
        if not bl or not mc:
            continue
        b0 = bl[0]
        m0 = mc[0]
        pairs.append(
            {
                "model": model,
                "task_id": task,
                "baseline_cost_usd": b0["cost_usd"],
                "mcp_cost_usd": m0["cost_usd"],
                "baseline_input_tokens": b0["input_tokens"],
                "mcp_input_tokens": m0["input_tokens"],
                "baseline_output_tokens": b0["output_tokens"],
                "mcp_output_tokens": m0["output_tokens"],
            }
        )
    return pairs


def _summarize_model(pairs: list[dict]) -> dict[str, dict]:
    out = {}
    for model in ("haiku", "sonnet", "opus"):
        rows = [p for p in pairs if p["model"] == model]
        bl = sum(r["baseline_cost_usd"] for r in rows)
        mc = sum(r["mcp_cost_usd"] for r in rows)
        n = len(rows)
        out[model] = {
            "pairs": n,
            "baseline_total_cost_usd": bl,
            "mcp_total_cost_usd": mc,
            "baseline_avg_cost_usd": (bl / n) if n else 0.0,
            "mcp_avg_cost_usd": (mc / n) if n else 0.0,
            "delta_cost_usd": mc - bl,
            "pct_delta_cost_of_means": ((mc / bl - 1) * 100) if bl else None,
            "input_ratio_mcp_over_baseline": (
                (sum(r["mcp_input_tokens"] for r in rows) / sum(r["baseline_input_tokens"] for r in rows))
                if rows and sum(r["baseline_input_tokens"] for r in rows) > 0
                else None
            ),
        }
    return out


def _summarize_size(pairs: list[dict], task_meta: dict[str, dict]) -> dict[str, dict]:
    rows = [p for p in pairs if p["model"] == "haiku"]

    by_ctx: dict[str, list[dict]] = defaultdict(list)
    by_files: dict[str, list[dict]] = defaultdict(list)
    for p in rows:
        meta = task_meta.get(p["task_id"], {})
        cbin = _context_bin(meta.get("context_length"))
        fbin = _files_bin(meta.get("files_count"))
        by_ctx[cbin].append(p)
        by_files[fbin].append(p)

    def summarize(groups: dict[str, list[dict]]) -> dict[str, dict]:
        out = {}
        for band, vals in sorted(groups.items()):
            n = len(vals)
            bl = sum(v["baseline_cost_usd"] for v in vals)
            mc = sum(v["mcp_cost_usd"] for v in vals)
            out[band] = {
                "pairs": n,
                "baseline_avg_cost_usd": (bl / n) if n else 0.0,
                "mcp_avg_cost_usd": (mc / n) if n else 0.0,
                "delta_avg_cost_usd": ((mc - bl) / n) if n else 0.0,
                "pct_delta_cost_of_means": ((mc / bl - 1) * 100) if bl else None,
            }
        return out

    return {
        "haiku_by_context_length": summarize(by_ctx),
        "haiku_by_files_count": summarize(by_files),
    }


def _plot_figure(report: dict) -> None:
    _setup_style()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    canonical = report["latest_task"]["valid_only"]
    model = canonical["model_summary"]
    ctx = canonical["size_summary"]["haiku_by_context_length"]

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8))
    ax1, ax2 = axes

    # Panel A: model-level % cost delta.
    labels = ["haiku", "opus"]
    vals = [
        model["haiku"]["pct_delta_cost_of_means"] or 0.0,
        model["opus"]["pct_delta_cost_of_means"] or 0.0,
    ]
    colors = [PALETTE["pos"] if v < 0 else PALETTE["neg"] for v in vals]
    x = np.arange(len(labels))
    bars = ax1.bar(x, vals, color=colors, width=0.62)
    ax1.axhline(0, color=PALETTE["grid"], linewidth=1)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("% cost delta (MCP vs baseline)", color=PALETTE["text_secondary"])
    ax1.set_title("Valid Paired Cost Delta by Model")
    ax1.grid(axis="y", alpha=0.3)
    for b, v in zip(bars, vals):
        y = v + 1.8 if v >= 0 else v - 2.6
        va = "bottom" if v >= 0 else "top"
        ax1.text(b.get_x() + b.get_width() / 2, y, f"{v:+.1f}%", ha="center", va=va, fontsize=9)
    ax1.text(0.03, 0.05, "sonnet: no valid pairs", transform=ax1.transAxes, fontsize=8, color=PALETTE["text_secondary"])

    # Panel B: haiku by context-length proxy.
    ctx_order = ["<100k", "100k-1m", ">=1m", "unknown"]
    bands = [b for b in ctx_order if b in ctx]
    ctx_vals = [ctx[b]["pct_delta_cost_of_means"] or 0.0 for b in bands]
    c2 = [PALETTE["pos"] if v < 0 else PALETTE["neg"] for v in ctx_vals]
    x2 = np.arange(len(bands))
    bars2 = ax2.bar(x2, ctx_vals, color=c2, width=0.62)
    ax2.axhline(0, color=PALETTE["grid"], linewidth=1)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(bands, rotation=15, ha="right")
    ax2.set_ylabel("% cost delta (MCP vs baseline)", color=PALETTE["text_secondary"])
    ax2.set_title("Haiku Cost Delta by Context-Length Proxy")
    ax2.grid(axis="y", alpha=0.3)
    for b, v in zip(bars2, ctx_vals):
        y = v + 1.8 if v >= 0 else v - 2.6
        va = "bottom" if v >= 0 else "top"
        ax2.text(b.get_x() + b.get_width() / 2, y, f"{v:+.1f}%", ha="center", va=va, fontsize=8)

    fig.suptitle("MCP vs Baseline Cost (Latest-Task Valid Pairing, runs/official/_raw)", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(ASSET_DIR / "figure_7_cost_pairing_by_model_and_size.png", dpi=220, bbox_inches="tight")
    fig.savefig(ASSET_DIR / "figure_7_cost_pairing_by_model_and_size.svg", bbox_inches="tight")
    plt.close(fig)


def build_report() -> dict:
    records = _collect_records()
    task_meta = _collect_task_meta()

    latest_all = _pair_records_latest_task(records, valid_only=False)
    latest_valid = _pair_records_latest_task(records, valid_only=True)
    count_all = _pair_records_count_matched(records, valid_only=False)
    count_valid = _pair_records_count_matched(records, valid_only=True)

    now = datetime.now(timezone.utc).isoformat()
    report = {
        "generated_at": now,
        "source": "runs/official/_raw",
        "canonical_pairing_rule": "latest valid per side per (model, task_id); one pair per task",
        "sensitivity_pairing_rule": "count-matched per (model, task_id), newest-first within side",
        "valid_filter": "output_tokens > 0 and agent_execution_seconds >= 10",
        "records_scanned": len(records),
        "latest_task": {
            "all_pairs": {
                "pair_count": len(latest_all),
                "model_summary": _summarize_model(latest_all),
                "size_summary": _summarize_size(latest_all, task_meta),
            },
            "valid_only": {
                "pair_count": len(latest_valid),
                "model_summary": _summarize_model(latest_valid),
                "size_summary": _summarize_size(latest_valid, task_meta),
            },
        },
        "count_matched": {
            "all_pairs": {
                "pair_count": len(count_all),
                "model_summary": _summarize_model(count_all),
                "size_summary": _summarize_size(count_all, task_meta),
            },
            "valid_only": {
                "pair_count": len(count_valid),
                "model_summary": _summarize_model(count_valid),
                "size_summary": _summarize_size(count_valid, task_meta),
            },
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze paired MCP-vs-baseline costs from runs/official/_raw.")
    parser.add_argument("--date-tag", default=datetime.now(timezone.utc).strftime("%Y%m%d"))
    args = parser.parse_args()

    report = build_report()
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = ANALYSIS_DIR / f"mcp_cost_pairs_official_raw_{args.date_tag}.json"
    out_json.write_text(json.dumps(report, indent=2))

    _plot_figure(report)

    print(f"Wrote: {out_json}")
    print(f"Wrote: {ASSET_DIR / 'figure_7_cost_pairing_by_model_and_size.png'}")
    print(f"Wrote: {ASSET_DIR / 'figure_7_cost_pairing_by_model_and_size.svg'}")


if __name__ == "__main__":
    main()
