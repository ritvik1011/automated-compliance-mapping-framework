"""Airflow tasks for the automated compliance monitoring pipeline."""

from src.pipeline.tasks.calculate_kpis import calculate_kpis
from src.pipeline.tasks.pull_configs import pull_infrastructure_configs
from src.pipeline.tasks.run_gap_analysis import run_gap_analysis
from src.pipeline.tasks.store_results import store_results

__all__ = [
    "pull_infrastructure_configs",
    "run_gap_analysis",
    "calculate_kpis",
    "store_results",
]
