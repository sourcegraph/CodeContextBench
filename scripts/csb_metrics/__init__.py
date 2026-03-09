"""CSB Metrics — data models and extractors for CodeScaleBench evaluation."""

from .models import TaskMetrics, RunMetrics, EvalReport
from .discovery import discover_runs, collect_retrieval_data
from .extractors import extract_run_config
from .task_selection import (
    load_selected_tasks,
    load_canonical_evaluation_audit,
    build_task_index,
    build_task_contract_index,
    enrich_runs,
    enrich_run_contracts,
    filter_runs_to_selected,
)

__all__ = [
    "TaskMetrics",
    "RunMetrics",
    "EvalReport",
    "discover_runs",
    "collect_retrieval_data",
    "extract_run_config",
    "load_selected_tasks",
    "load_canonical_evaluation_audit",
    "build_task_index",
    "build_task_contract_index",
    "enrich_runs",
    "enrich_run_contracts",
    "filter_runs_to_selected",
]
