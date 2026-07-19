"""Task 3: Calculate Compliance KPIs.

This Airflow task calculates Key Performance Indicators from the
gap analysis report.
"""

import json
import logging
from typing import Any, Dict

from src.models.gap_analysis import GapAnalysisReport
from src.pipeline.kpis.compliance_kpis import ComplianceKPICalculator

logger = logging.getLogger(__name__)


def calculate_kpis(**context: Any) -> Dict[str, Any]:
    """Calculate compliance KPIs from gap analysis report.

    Args:
        context: Airflow context

    Returns:
        Dictionary with calculated KPIs
    """
    logger.info("Starting KPI calculation")

    # Get gap analysis metadata from Task 2 (via XCom or fallback context)
    ti = context.get("ti")
    gap_analysis_metadata = None
    if ti and hasattr(ti, "xcom_pull"):
        gap_analysis_metadata = ti.xcom_pull(task_ids="run_gap_analysis")
    if not gap_analysis_metadata:
        gap_analysis_metadata = context.get("gap_analysis_metadata")

    if not gap_analysis_metadata:
        raise ValueError("No gap analysis metadata found from Task 2")

    json_report_path = gap_analysis_metadata["json_report_path"]

    try:
        # Load gap analysis report
        with open(json_report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        report = GapAnalysisReport(**report_data)

        # Calculate KPIs
        calculator = ComplianceKPICalculator(report)
        kpis = calculator.calculate_all_kpis()

        # Print summary
        summary = calculator.generate_kpi_summary(kpis)
        logger.info(f"\n{summary}")

        logger.info(f"✓ Calculated {len(kpis)} KPIs")

        # Return KPIs for downstream tasks
        return {
            "kpis": kpis,
            "report_id": report.report_id,
        }

    except Exception as e:
        logger.error(f"✗ Failed to calculate KPIs: {e}")
        raise
