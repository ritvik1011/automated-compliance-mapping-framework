"""Airflow entrypoint pointing to compliance_monitoring_dag."""

from src.pipeline.dags.compliance_monitoring_dag import *  # noqa: F401, F403
