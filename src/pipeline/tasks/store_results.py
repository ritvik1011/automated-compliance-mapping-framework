"""Task 4: Store Results to Database.

This Airflow task stores the compliance assessment results and KPIs
to the database for historical tracking and trend analysis.
"""

import json
import logging
from typing import Any, Dict

from src.models.gap_analysis import GapAnalysisReport
from src.pipeline.database.models import get_session, init_db
from src.pipeline.database.repository import ComplianceRepository

logger = logging.getLogger(__name__)


def store_results(
    database_url: str = "sqlite:///compliance.db",
    **context: Any,
) -> Dict[str, Any]:
    """Store compliance assessment results and KPIs to database.

    Args:
        database_url: SQLAlchemy database URL
        context: Airflow context

    Returns:
        Dictionary with storage metadata
    """
    logger.info("Starting results storage")

    # Initialize database
    init_db(database_url)

    # Get metadata from upstream tasks (via XCom or fallback context)
    ti = context.get("ti")
    baseline_metadata = None
    gap_analysis_metadata = None
    kpi_metadata = None

    if ti and hasattr(ti, "xcom_pull"):
        baseline_metadata = ti.xcom_pull(task_ids="pull_configs")
        gap_analysis_metadata = ti.xcom_pull(task_ids="run_gap_analysis")
        kpi_metadata = ti.xcom_pull(task_ids="calculate_kpis")

    if not baseline_metadata:
        baseline_metadata = context.get("baseline_metadata")
    if not gap_analysis_metadata:
        gap_analysis_metadata = context.get("gap_analysis_metadata")
    if not kpi_metadata:
        kpi_metadata = context.get("kpi_metadata")

    if baseline_metadata is None or gap_analysis_metadata is None or kpi_metadata is None:
        raise ValueError("Missing metadata from upstream tasks")

    session = None
    try:
        # Load gap analysis report
        json_report_path = str(gap_analysis_metadata["json_report_path"])
        with open(json_report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        report = GapAnalysisReport(**report_data)

        # Store to database
        session = get_session(database_url)
        repository = ComplianceRepository(session)

        # Store assessment
        assessment = repository.store_assessment(
            report=report,
            cloud_provider=str(baseline_metadata["cloud_provider"]),
            subscription_id=baseline_metadata.get("subscription_id"),
        )

        assessment_id = str(assessment.id)

        # Store KPIs
        kpis = kpi_metadata["kpis"]
        repository.store_kpis(assessment_id, kpis)

        logger.info(f"✓ Stored assessment {assessment_id} and {len(kpis)} KPIs to database")

        return {
            "assessment_id": assessment_id,
            "stored_kpis_count": len(kpis),
            "database_url": database_url,
        }

    except Exception as e:
        logger.error(f"✗ Failed to store results: {e}")
        raise
    finally:
        if session:
            session.close()
