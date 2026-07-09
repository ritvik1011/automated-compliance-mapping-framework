"""Unit tests for compliance KPI calculations and trend analysis."""

from datetime import datetime, timedelta, timezone
import pytest

from src.models.gap_analysis import (
    ConfidenceLevel,
    GapAnalysisReport,
    GapAnalysisResult,
    GapType,
)
from src.pipeline.database.models import get_session, init_db
from src.pipeline.database.repository import ComplianceRepository
from src.pipeline.kpis.compliance_kpis import ComplianceKPICalculator


@pytest.fixture
def multi_reg_gap_report():
    """Create a comprehensive multi-regulation report for KPI testing."""
    results = [
        # GDPR Controls
        GapAnalysisResult(
            regulatory_control_id="gdpr-art-32",
            regulatory_control_title="Security of processing",
            regulation="GDPR",
            mapped_technical_controls=["tc-enc-1", "tc-enc-2"],
            gap_type=GapType.COMPLIANT,
            compliance_status="compliant",
            confidence_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            evidence=[{"item": "AES256 enabled"}],
            friction_points=[],
            recommendations=[],
        ),
        GapAnalysisResult(
            regulatory_control_id="gdpr-art-25",
            regulatory_control_title="Data protection by design",
            regulation="GDPR",
            mapped_technical_controls=["tc-iam-1"],
            gap_type=GapType.PARTIAL,
            compliance_status="partial",
            confidence_score=0.75,
            confidence_level=ConfidenceLevel.MEDIUM,
            evidence=[],
            friction_points=["Policy friction between Dev & Legal"],
            recommendations=["Document architecture requirements"],
        ),
        # DORA Controls
        GapAnalysisResult(
            regulatory_control_id="dora-art-11",
            regulatory_control_title="ICT business continuity",
            regulation="DORA",
            mapped_technical_controls=["tc-backup-1"],
            gap_type=GapType.COMPLIANT,
            compliance_status="compliant",
            confidence_score=0.90,
            confidence_level=ConfidenceLevel.HIGH,
            evidence=[{"backup": "Daily automated snapshot"}],
            friction_points=[],
            recommendations=[],
        ),
        GapAnalysisResult(
            regulatory_control_id="dora-art-6",
            regulatory_control_title="ICT risk management framework",
            regulation="DORA",
            mapped_technical_controls=[],
            gap_type=GapType.MISSING,
            compliance_status="non-compliant",
            confidence_score=0.30,
            confidence_level=ConfidenceLevel.LOW,
            evidence=[],
            friction_points=["No continuous monitoring pipeline configured"],
            recommendations=["Deploy automated scheduler"],
        ),
        # NIS2 Controls
        GapAnalysisResult(
            regulatory_control_id="nis2-art-21",
            regulatory_control_title="Cybersecurity risk-management measures",
            regulation="NIS2",
            mapped_technical_controls=["tc-net-1"],
            gap_type=GapType.UNKNOWN,
            compliance_status="unknown",
            confidence_score=0.40,
            confidence_level=ConfidenceLevel.LOW,
            evidence=[],
            friction_points=["Audit log retention duration unverified"],
            recommendations=["Verify SIEM logging policies"],
        ),
    ]

    return GapAnalysisReport(
        report_id="multi-reg-report-001",
        catalog_id="unified-catalog-v1",
        baseline_id="baseline-azure-prod",
        total_regulatory_controls=5,
        total_technical_controls=10,
        results=results,
        summary={
            "total_controls_analyzed": 5,
            "compliance_status_breakdown": {
                "compliant": 2,
                "partial": 1,
                "non-compliant": 1,
                "unknown": 1,
            },
            "avg_confidence_score": 0.66,
        },
    )


def test_kpi_calculator_confidence_and_friction(multi_reg_gap_report):
    """Test confidence percentages and socio-technical friction metrics."""
    calculator = ComplianceKPICalculator(multi_reg_gap_report)
    kpis = calculator.calculate_all_kpis()

    # Total controls = 5
    # High confidence (>=0.8): 2 controls (0.95, 0.90) -> 2/5 = 40.0%
    assert kpis["high_confidence_percentage"] == 40.0

    # Controls with friction: 3 controls (gdpr-art-25, dora-art-6, nis2-art-21) -> 3/5 = 60.0%
    assert kpis["high_friction_controls_count"] == 3.0
    assert kpis["friction_rate"] == 60.0


def test_kpi_calculator_weighted_compliance_score(multi_reg_gap_report):
    """Test that compliant gets 1.0 weight and partial gets 0.5 weight."""
    calculator = ComplianceKPICalculator(multi_reg_gap_report)
    kpis = calculator.calculate_all_kpis()

    # Compliant: 2, Partial: 1, Total: 5
    # (2 * 1.0 + 1 * 0.5) / 5 = 2.5 / 5 = 50.0%
    assert kpis["overall_compliance_rate"] == 50.0

    # GDPR: 1 compliant, 1 partial -> (1 + 0.5) / 2 = 75.0%
    assert kpis["gdpr_compliance_rate"] == 75.0

    # DORA: 1 compliant, 1 non-compliant -> 1 / 2 = 50.0%
    assert kpis["dora_compliance_rate"] == 50.0

    # NIS2: 1 unknown -> 0.0%
    assert kpis["nis2_compliance_rate"] == 0.0


def test_kpi_summary_generation(multi_reg_gap_report):
    """Test generation of formatted summary for reporting."""
    calculator = ComplianceKPICalculator(multi_reg_gap_report)
    kpis = calculator.calculate_all_kpis()
    summary_text = calculator.generate_kpi_summary(kpis)

    assert "Compliance KPI Summary" in summary_text
    assert "Overall Compliance Rate: 50.0%" in summary_text
    assert "GDPR Compliance Rate: 75.0%" in summary_text
    assert "DORA Compliance Rate: 50.0%" in summary_text


def test_empty_report_handling():
    """Test KPI calculator behaves gracefully on empty reports."""
    empty_report = GapAnalysisReport(
        report_id="empty-report",
        total_regulatory_controls=0,
        total_technical_controls=0,
        results=[],
        summary={},
    )
    calculator = ComplianceKPICalculator(empty_report)
    kpis = calculator.calculate_all_kpis()

    assert kpis["overall_compliance_rate"] == 0.0
    assert kpis["total_controls_analyzed"] == 0.0
    assert kpis["average_confidence_score"] == 0.0
    assert kpis["friction_rate"] == 0.0


def test_repository_historical_querying(multi_reg_gap_report, tmp_path):
    """Test date range querying and trend analysis in ComplianceRepository."""
    db_path = tmp_path / "trend.db"
    db_url = f"sqlite:///{db_path}"

    init_db(db_url)
    session = get_session(db_url)
    repository = ComplianceRepository(session)

    # Store assessment
    assessment = repository.store_assessment(
        report=multi_reg_gap_report,
        cloud_provider="azure",
        subscription_id="sub-test-999",
    )

    # Store multiple KPIs
    calculator = ComplianceKPICalculator(multi_reg_gap_report)
    kpis = calculator.calculate_all_kpis()
    repository.store_kpis(assessment.id, kpis)

    # Query latest assessment
    latest = repository.get_latest_assessment()
    assert latest is not None
    assert latest.id == multi_reg_gap_report.report_id

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = now - timedelta(days=1)
    end = now + timedelta(days=1)
    range_results = repository.get_assessments_by_date_range(start, end)
    assert len(range_results) == 1

    # Query KPI trend
    trend = repository.get_kpi_trend("overall_compliance_rate", limit=5)
    assert len(trend) == 1
    assert trend[0]["value"] == 50.0

    session.close()
