"""Tests for the compliance monitoring pipeline."""

from pathlib import Path
import pytest

from src.models.gap_analysis import GapAnalysisReport, GapAnalysisResult, GapType
from src.pipeline.database.models import get_session, init_db
from src.pipeline.database.repository import ComplianceRepository
from src.pipeline.kpis.compliance_kpis import ComplianceKPICalculator
from src.pipeline.tasks.calculate_kpis import calculate_kpis
from src.pipeline.tasks.pull_configs import pull_infrastructure_configs
from src.pipeline.tasks.run_gap_analysis import run_gap_analysis
from src.pipeline.tasks.store_results import store_results


@pytest.fixture
def sample_gap_report():
    """Create a sample gap analysis report for testing."""
    results = [
        GapAnalysisResult(
            regulatory_control_id="gdpr-art32",
            regulatory_control_title="Security of processing",
            regulation="GDPR",
            mapped_technical_controls=["azure-storage-encryption-1"],
            gap_type=GapType.COMPLIANT,
            compliance_status="compliant",
            confidence_score=0.85,
            confidence_level="high",
            evidence=[],
            friction_points=[],
            recommendations=[],
        ),
        GapAnalysisResult(
            regulatory_control_id="dora-art-6",
            regulatory_control_title="ICT risk management",
            regulation="DORA",
            mapped_technical_controls=[],
            gap_type=GapType.MISSING,
            compliance_status="non-compliant",
            confidence_score=0.3,
            confidence_level="low",
            evidence=[],
            friction_points=["No technical controls found"],
            recommendations=["Implement controls"],
        ),
    ]

    return GapAnalysisReport(
        report_id="test-report",
        catalog_id="test-catalog",
        baseline_id="test-baseline",
        total_regulatory_controls=2,
        total_technical_controls=5,
        results=results,
        summary={
            "total_controls_analyzed": 2,
            "compliance_status_breakdown": {
                "compliant": 1,
                "partial": 0,
                "non-compliant": 1,
                "unknown": 0,
            },
            "avg_confidence_score": 0.575,
        },
    )


def test_kpi_calculator_overall_metrics(sample_gap_report):
    """Test overall KPI calculation."""
    calculator = ComplianceKPICalculator(sample_gap_report)
    kpis = calculator.calculate_all_kpis()

    assert "overall_compliance_rate" in kpis
    assert "total_controls_analyzed" in kpis
    assert kpis["total_controls_analyzed"] == 2


def test_kpi_calculator_regulation_metrics(sample_gap_report):
    """Test regulation-specific KPI calculation."""
    calculator = ComplianceKPICalculator(sample_gap_report)
    kpis = calculator.calculate_all_kpis()

    assert "gdpr_compliance_rate" in kpis
    assert "dora_compliance_rate" in kpis


def test_database_repository_store_assessment(sample_gap_report, tmp_path):
    """Test storing assessment to database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    init_db(db_url)
    session = get_session(db_url)
    repository = ComplianceRepository(session)

    # Store assessment
    assessment = repository.store_assessment(
        report=sample_gap_report,
        cloud_provider="azure",
        subscription_id="test-sub",
    )

    assert assessment is not None
    assert assessment.id == "test-report"
    assert assessment.cloud_provider == "azure"

    # Verify control results were stored
    assert len(assessment.control_results) == 2

    session.close()


def test_database_repository_store_kpis(sample_gap_report, tmp_path):
    """Test storing KPIs to database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    init_db(db_url)
    session = get_session(db_url)
    repository = ComplianceRepository(session)

    # Store assessment first
    assessment = repository.store_assessment(
        report=sample_gap_report,
        cloud_provider="azure",
    )

    # Store KPIs
    kpis = {
        "overall_compliance_rate": 50.0,
        "gdpr_compliance_rate": 100.0,
        "dora_compliance_rate": 0.0,
    }

    stored_kpis = repository.store_kpis(assessment.id, kpis)

    assert len(stored_kpis) == 3

    session.close()


def test_pipeline_tasks_end_to_end(tmp_path):
    """Test full sequential pipeline execution across Tasks 1 -> 4."""
    baselines_dir = tmp_path / "baselines"
    reports_dir = tmp_path / "reports"
    db_path = tmp_path / "pipeline.db"
    db_url = f"sqlite:///{db_path}"

    # Task 1: pull_configs
    task1_result = pull_infrastructure_configs(
        cloud_provider="azure",
        subscription_id="sub-test-123",
        output_dir=str(baselines_dir),
        mock_data_path="data/mock_cloud_responses/azure_mock_response.json",
    )
    assert Path(task1_result["baseline_path"]).exists()
    assert task1_result["total_controls"] > 0

    # Task 2: run_gap_analysis
    task2_result = run_gap_analysis(
        catalog_path="oscal_profiles/gdpr_catalog.json",
        output_dir=str(reports_dir),
        baseline_metadata=task1_result,
    )
    assert Path(task2_result["json_report_path"]).exists()
    assert Path(task2_result["md_report_path"]).exists()
    assert task2_result["total_regulatory_controls"] > 0

    # Task 3: calculate_kpis
    task3_result = calculate_kpis(
        gap_analysis_metadata=task2_result,
    )
    assert "kpis" in task3_result
    assert "overall_compliance_rate" in task3_result["kpis"]

    # Task 4: store_results
    task4_result = store_results(
        database_url=db_url,
        baseline_metadata=task1_result,
        gap_analysis_metadata=task2_result,
        kpi_metadata=task3_result,
    )
    assert task4_result["assessment_id"] == task2_result["report_id"]
    assert task4_result["stored_kpis_count"] > 0
