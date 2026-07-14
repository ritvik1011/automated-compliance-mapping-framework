"""Task 2: Run Gap Analysis.

This Airflow task compares the technical baseline (from Task 1) against
the regulatory catalog (from Step 1) to identify compliance gaps.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict

from src.gap_analysis.gap_evaluator import GapEvaluator
from src.gap_analysis.report_generator import ReportGenerator
from src.models.technical_control import InfrastructureBaseline

logger = logging.getLogger(__name__)


def run_gap_analysis(
    catalog_path: str = "oscal_profiles/gdpr_catalog.json",
    output_dir: str = "reports",
    **context: Any,  # Airflow context
) -> Dict[str, Any]:
    """Run gap analysis between regulatory catalog and technical baseline.

    This task receives baseline metadata from Task 1 via XCom,
    loads the baseline, and performs gap analysis.

    Args:
        catalog_path: Path to OSCAL catalog JSON
        output_dir: Directory to save gap analysis reports
        context: Airflow context

    Returns:
        Dictionary with gap analysis metadata for downstream tasks
    """
    logger.info("Starting gap analysis")

    # Get baseline metadata from Task 1 (via XCom or fallback context)
    ti = context.get("ti")
    baseline_metadata = None
    if ti and hasattr(ti, "xcom_pull"):
        baseline_metadata = ti.xcom_pull(task_ids="pull_configs")
    if not baseline_metadata:
        baseline_metadata = context.get("baseline_metadata")

    if not baseline_metadata:
        raise ValueError("No baseline metadata found from Task 1")

    baseline_path = baseline_metadata["baseline_path"]

    try:
        # Load baseline
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

        baseline = InfrastructureBaseline(**baseline_data)

        # Load catalog
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        # Extract controls from catalog
        catalog_controls = []
        catalog = catalog_data.get("catalog", {})

        # Handle both grouped and flat control structures
        if "groups" in catalog:
            for group in catalog["groups"]:
                for control in group.get("controls", []):
                    catalog_controls.append(
                        {
                            "id": control["id"],
                            "title": control.get("title", "Unknown"),
                        }
                    )
        elif "controls" in catalog:
            for control in catalog["controls"]:
                catalog_controls.append(
                    {
                        "id": control["id"],
                        "title": control.get("title", "Unknown"),
                    }
                )

        # Run gap analysis
        evaluator = GapEvaluator()
        report = evaluator.evaluate_gaps(catalog_controls, baseline)

        # Save reports
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        execution_date = context.get("logical_date") or context.get(
            "execution_date", datetime.now(timezone.utc)
        )
        if isinstance(execution_date, str):
            try:
                execution_date = datetime.fromisoformat(execution_date)
            except Exception:
                execution_date = datetime.now(timezone.utc)

        timestamp = execution_date.strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_path = output_path / f"gap_analysis_{timestamp}.json"
        report_gen = ReportGenerator(report)
        report_gen.save_json(str(json_path))

        # Save Markdown report
        md_path = output_path / f"gap_analysis_{timestamp}.md"
        report_gen.save_markdown(str(md_path))

        logger.info(f"✓ Gap analysis complete. Reports saved to {output_path}")

        summary_dict = (
            report.summary.model_dump()
            if hasattr(report.summary, "model_dump")
            else report.summary
        )

        # Return metadata for downstream tasks
        return {
            "report_id": report.report_id,
            "json_report_path": str(json_path),
            "md_report_path": str(md_path),
            "total_regulatory_controls": report.total_regulatory_controls,
            "total_technical_controls": report.total_technical_controls,
            "summary": summary_dict,
        }

    except Exception as e:
        logger.error(f"✗ Failed to run gap analysis: {e}")
        raise
