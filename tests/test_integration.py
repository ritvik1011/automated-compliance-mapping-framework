"""Integration Test Suite for Automated Compliance Mapping Pipeline.

This module validates the complete Policy-as-Code pipeline end-to-end:
ingesting regulatory articles, executing heuristic friction analysis, generating
NIST OSCAL catalogs, rendering Rich terminal telemetry, and serializing JSON artifacts.
"""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from src.main import main, run_pipeline


def test_full_pipeline_multi_regulation_execution(
    sample_data_path: Path,
    tmp_path: Path,
) -> None:
    """WHAT: Executes run_pipeline() end-to-end with sample multi-regulation input.

    WHY IT MATTERS:
    Validates that the orchestrator wires together parser -> analyzer -> OSCAL generator
    without contract mismatch, creating all individual and unified catalogs.
    """
    exit_code = run_pipeline(
        input_file=sample_data_path,
        output_dir=tmp_path,
        regulation_filter=None,
        verbose=False,
    )

    assert exit_code == 0, "Pipeline must exit cleanly with code 0 on valid inputs."

    # Verify all expected artifacts exist on disk
    expected_files = [
        "gdpr_catalog.json",
        "dora_catalog.json",
        "nis2_catalog.json",
        "unified_catalog.json",
        "friction_report.json",
    ]
    for filename in expected_files:
        file_path = tmp_path / filename
        assert file_path.exists(), f"Expected pipeline artifact missing: {filename}"
        assert file_path.stat().st_size > 0, f"Artifact {filename} must not be empty."

        # Verify artifact is syntactically valid JSON
        with open(file_path, "r", encoding="utf-8") as f:
            content: Dict[str, Any] = json.load(f)
            assert isinstance(content, dict)


def test_pipeline_filtering_by_regulation(
    sample_data_path: Path,
    tmp_path: Path,
) -> None:
    """WHAT: Tests running the pipeline with a regulation filter (e.g. --regulation GDPR).

    WHY IT MATTERS:
    In targeted audits, compliance teams need to isolate specific regulatory domains
    (e.g., privacy/GDPR) without generating noise from irrelevant mandates.
    """
    exit_code = run_pipeline(
        input_file=sample_data_path,
        output_dir=tmp_path,
        regulation_filter="GDPR",
        verbose=False,
    )

    assert exit_code == 0
    gdpr_catalog_path = tmp_path / "gdpr_catalog.json"
    assert gdpr_catalog_path.exists()

    with open(gdpr_catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    controls = catalog_data["catalog"]["controls"]
    assert len(controls) > 0

    # Ensure all controls belong strictly to GDPR
    for ctrl in controls:
        reg_prop = next(p for p in ctrl["props"] if p["name"] == "regulation")
        assert reg_prop["value"] == "GDPR"


def test_pipeline_error_on_empty_input(tmp_path: Path) -> None:
    """WHAT: Verifies that running the pipeline on an empty input returns exit code 1.

    WHY IT MATTERS:
    A robust CLI pipeline must detect empty/unactionable inputs, notify the user,
    and return an error exit code suitable for CI/CD pipeline halting.
    """
    empty_file = tmp_path / "empty_input.json"
    empty_file.write_text("[]", encoding="utf-8")

    exit_code = run_pipeline(
        input_file=empty_file,
        output_dir=tmp_path,
        regulation_filter=None,
        verbose=False,
    )

    assert exit_code == 1, "Pipeline should exit with code 1 when no articles are found."


def test_pipeline_main_cli_entrypoint(
    sample_data_path: Path,
    tmp_path: Path,
) -> None:
    """WHAT: Tests CLI main() entrypoint by simulating sys.argv arguments.

    WHY IT MATTERS:
    Validates argparse configuration, flag parsing (--input, --output-dir, -v),
    and terminal invocation as executed by users in bash/PowerShell.
    """
    test_args = [
        "main.py",
        "--input",
        str(sample_data_path),
        "--output-dir",
        str(tmp_path),
        "--verbose",
    ]
    with patch("sys.argv", test_args):
        # main() concludes with sys.exit(exit_code)
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    assert (tmp_path / "unified_catalog.json").exists()


def test_pipeline_generated_friction_report_integrity(
    sample_data_path: Path,
    tmp_path: Path,
) -> None:
    """WHAT: Verifies the structural integrity of the generated friction_report.json.

    WHY IT MATTERS:
    The socio-technical friction report is the core academic deliverable; it must
    include total counts, distributions, and actionable HITL validation steps.
    """
    run_pipeline(
        input_file=sample_data_path,
        output_dir=tmp_path,
        regulation_filter=None,
        verbose=False,
    )

    report_path = tmp_path / "friction_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert "total_articles" in report
    assert "friction_distribution" in report
    assert "assessments" in report
    assert report["total_articles"] >= 4
    assert report["friction_distribution"]["High"] > 0

    first_assessment = report["assessments"][0]
    assert "friction_level" in first_assessment
    assert "reason" in first_assessment
    assert "recommendation" in first_assessment
