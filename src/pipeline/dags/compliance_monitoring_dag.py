"""Compliance Monitoring DAG.

This Airflow DAG orchestrates the complete compliance monitoring pipeline:
1. Pull infrastructure configurations
2. Run gap analysis against regulatory catalog
3. Calculate compliance KPIs
4. Store results to database

Schedule: Every Monday at 2:00 AM UTC
Owner: Ritvik Bahirwar
Email: ritvikbahirwar11@outlook.com

Research Context:
    This DAG implements continuous compliance monitoring, a key requirement
    of DORA Article 11 and NIS2 Article 21. It demonstrates the viability
    of Policy-as-Code approaches for automated regulatory compliance.
"""

from datetime import datetime, timedelta
import logging

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.utils.dates import days_ago

    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False
    DAG = None  # type: ignore[assignment,misc]
    PythonOperator = None  # type: ignore[assignment,misc]
    days_ago = None  # type: ignore[assignment]

from src.pipeline.tasks.calculate_kpis import calculate_kpis
from src.pipeline.tasks.pull_configs import pull_infrastructure_configs
from src.pipeline.tasks.run_gap_analysis import run_gap_analysis
from src.pipeline.tasks.store_results import store_results

logger = logging.getLogger(__name__)

# Default arguments for all tasks
default_args = {
    "owner": "ritvik_bahirwar",
    "depends_on_past": False,
    "email": ["ritvikbahirwar11@outlook.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": days_ago(1) if days_ago else datetime(2026, 1, 1),
}

if AIRFLOW_AVAILABLE and DAG is not None and PythonOperator is not None:
    # Define the DAG
    with DAG(
        dag_id="compliance_monitoring_pipeline",
        default_args=default_args,
        description="Automated compliance monitoring pipeline for GDPR/DORA/NIS2",
        schedule_interval="0 2 * * 1",  # Every Monday at 2:00 AM UTC
        catchup=False,
        tags=["compliance", "gdpr", "dora", "nis2", "policy-as-code"],
        doc_md="""
        ## Compliance Monitoring Pipeline

        This DAG implements automated compliance monitoring for enterprise cloud infrastructure.

        ### Pipeline Steps:
        1. **Pull Configs**: Extract current infrastructure state from Azure
        2. **Gap Analysis**: Compare against GDPR/DORA/NIS2 regulatory catalog
        3. **Calculate KPIs**: Compute compliance metrics and confidence scores
        4. **Store Results**: Persist to database for trend analysis

        ### Schedule:
        Runs every Monday at 2:00 AM UTC

        ### Owner:
        Ritvik Bahirwar (ritvikbahirwar11@outlook.com)
        """,
    ) as dag:
        # Task 1: Pull infrastructure configurations
        pull_configs_task = PythonOperator(
            task_id="pull_configs",
            python_callable=pull_infrastructure_configs,
            op_kwargs={
                "cloud_provider": "azure",
                "subscription_id": None,  # Use default subscription
                "output_dir": "baselines",
            },
        )

        # Task 2: Run gap analysis
        run_gap_analysis_task = PythonOperator(
            task_id="run_gap_analysis",
            python_callable=run_gap_analysis,
            op_kwargs={
                "catalog_path": "oscal_profiles/gdpr_catalog.json",
                "output_dir": "reports",
            },
        )

        # Task 3: Calculate KPIs
        calculate_kpis_task = PythonOperator(
            task_id="calculate_kpis",
            python_callable=calculate_kpis,
        )

        # Task 4: Store results to database
        store_results_task = PythonOperator(
            task_id="store_results",
            python_callable=store_results,
            op_kwargs={
                "database_url": "sqlite:///compliance.db",
            },
        )

        # Define task dependencies
        pull_configs_task >> run_gap_analysis_task >> calculate_kpis_task >> store_results_task
else:
    dag = None
    logger.info(
        "Apache Airflow is not installed in the current environment; DAG definition is dormant."
    )
