"""Example: Running the complete gap analysis pipeline.

Demonstrates Step 3: Mapping regulatory requirements to technical baseline
telemetry, calculating confidence scores, and exporting JSON/Markdown/terminal reports.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.gap_analysis.gap_evaluator import GapEvaluator  # noqa: E402
from src.gap_analysis.report_generator import ReportGenerator  # noqa: E402
from src.models.technical_control import InfrastructureBaseline  # noqa: E402


def main() -> None:
    # 1. Load the technical baseline (from Step 2)
    baseline_path = Path("baselines/technical_baseline.json")
    if not baseline_path.exists():
        baseline_path = Path("baselines/azure_baseline.json")

    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    baseline = InfrastructureBaseline(**baseline_data)

    # 2. Load the regulatory catalog (from Step 1)
    catalog_path = Path("oscal_profiles/gdpr_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    # 3. Extract controls from catalog
    catalog_controls = []
    # Check top-level controls
    for control in catalog_data.get("catalog", {}).get("controls", []):
        catalog_controls.append(
            {
                "id": control["id"],
                "title": control.get("title", "Unknown"),
            }
        )
    # Check group controls if present
    for group in catalog_data.get("catalog", {}).get("groups", []):
        for control in group.get("controls", []):
            catalog_controls.append(
                {
                    "id": control["id"],
                    "title": control.get("title", "Unknown"),
                }
            )

    # 4. Run gap analysis
    evaluator = GapEvaluator()
    report = evaluator.evaluate_gaps(catalog_controls, baseline)

    # 5. Generate reports
    report_gen = ReportGenerator(report)
    report_gen.save_json("reports/gap_analysis.json")
    report_gen.save_markdown("reports/gap_analysis.md")
    report_gen.print_terminal_report()


if __name__ == "__main__":
    main()
