"""Unit and integration tests for the Step 5 Dashboard module."""

import json
import pytest
import pandas as pd
import plotly.graph_objects as go

from src.models.gap_analysis import GapAnalysisReport, GapAnalysisResult, GapType
from src.pipeline.database.models import init_db, get_session
from src.pipeline.database.repository import ComplianceRepository
from src.dashboard.database import (
    get_latest_assessment_data,
    get_all_assessments_summary,
    get_kpi_trend,
    get_friction_points,
    get_compliance_by_regulation,
    get_compliance_by_category,
)
from src.dashboard.visualizations import (
    create_compliance_gauge,
    _get_score_color,
    create_compliance_heatmap,
    create_regulation_breakdown_chart,
    create_confidence_scatter,
    create_trend_line_chart,
    create_friction_impact_chart,
    create_category_pie_chart,
)
from src.dashboard.export import (
    export_assessment_to_excel,
    generate_executive_html_report,
    export_executive_summary_to_pdf,
)


@pytest.fixture
def test_db_with_data(tmp_path):
    """Create a temporary SQLite database populated with test assessments and KPIs."""
    db_path = tmp_path / "compliance_test.db"
    db_url = f"sqlite:///{db_path}"

    init_db(db_url)
    session = get_session(db_url)
    repo = ComplianceRepository(session)

    # Assessment 1
    results_1 = [
        GapAnalysisResult(
            regulatory_control_id="gdpr-art32-encryption",
            regulatory_control_title="Security of processing (Encryption)",
            regulation="GDPR",
            mapped_technical_controls=["azure-storage-encryption-1"],
            gap_type=GapType.COMPLIANT,
            compliance_status="compliant",
            confidence_score=0.90,
            confidence_level="high",
            evidence=[{"type": "config", "detail": "blob encryption enabled"}],
            friction_points=[],
            recommendations=[],
        ),
        GapAnalysisResult(
            regulatory_control_id="dora-art6-network",
            regulatory_control_title="ICT risk management (Network)",
            regulation="DORA",
            mapped_technical_controls=[],
            gap_type=GapType.PARTIAL,
            compliance_status="partial",
            confidence_score=0.60,
            confidence_level="medium",
            evidence=[],
            friction_points=["Ambiguous boundary between cloud provider and tenant responsibility"],
            recommendations=["Clarify shared responsibility agreement with Azure"],
        ),
        GapAnalysisResult(
            regulatory_control_id="nis2-art21-backup",
            regulatory_control_title="Cybersecurity risk-management (Backup)",
            regulation="NIS2",
            mapped_technical_controls=[],
            gap_type=GapType.MISSING,
            compliance_status="non-compliant",
            confidence_score=0.40,
            confidence_level="low",
            evidence=[],
            friction_points=[
                "Manual human backup audit required",
                "Legal ambiguity around cross-border backup retention",
            ],
            recommendations=["Implement automated geo-redundant backups"],
        ),
    ]

    report_1 = GapAnalysisReport(
        report_id="assessment-2026-001",
        catalog_id="catalog-multi",
        baseline_id="baseline-azure-001",
        total_regulatory_controls=3,
        total_technical_controls=10,
        results=results_1,
        summary={
            "total_controls_analyzed": 3,
            "compliance_status_breakdown": {
                "compliant": 1,
                "partial": 1,
                "non-compliant": 1,
                "unknown": 0,
            },
            "avg_confidence_score": 0.633,
        },
    )

    assessment_1 = repo.store_assessment(report_1, cloud_provider="azure", subscription_id="sub-1")
    repo.store_kpis(
        assessment_1.id,
        {
            "overall_compliance_rate": 50.0,
            "gdpr_compliance_rate": 100.0,
            "dora_compliance_rate": 50.0,
            "nis2_compliance_rate": 0.0,
            "average_confidence_score": 63.3,
            "friction_rate": 66.7,
        },
    )

    session.close()
    return db_url


def test_database_empty_db(tmp_path):
    """Test database queries against an empty database."""
    db_path = tmp_path / "empty.db"
    db_url = f"sqlite:///{db_path}"
    init_db(db_url)

    latest = get_latest_assessment_data(db_url)
    assert latest is None

    summary_df = get_all_assessments_summary(db_url)
    assert summary_df.empty

    trend_df = get_kpi_trend("overall_compliance_rate", db_url)
    assert trend_df.empty

    friction_df = get_friction_points(db_url)
    assert friction_df.empty

    reg_df = get_compliance_by_regulation(db_url)
    assert reg_df.empty

    cat_df = get_compliance_by_category(db_url)
    assert cat_df.empty


def test_database_queries_with_data(test_db_with_data):
    """Test retrieving assessment, friction, regulation, and category data."""
    data = get_latest_assessment_data(test_db_with_data)
    assert data is not None
    assert "assessment" in data
    assert "controls" in data
    assert "kpis" in data

    assert data["assessment"]["cloud_provider"] == "azure"
    assert len(data["controls"]) == 3
    assert len(data["kpis"]) == 6

    # Summary
    summary_df = get_all_assessments_summary(test_db_with_data)
    assert len(summary_df) == 1
    assert summary_df.iloc[0]["total_regulatory_controls"] == 3

    # Trend
    trend_df = get_kpi_trend("overall_compliance_rate", test_db_with_data)
    assert len(trend_df) == 1
    assert trend_df.iloc[0]["kpi_value"] == 50.0

    # Friction points
    friction_df = get_friction_points(test_db_with_data)
    assert len(friction_df) == 2  # DORA and NIS2 have friction points

    # Compliance by regulation
    reg_df = get_compliance_by_regulation(test_db_with_data)
    assert len(reg_df) == 3
    assert "compliant" in reg_df.columns
    assert "partial" in reg_df.columns
    assert "non_compliant" in reg_df.columns

    # Compliance by category
    cat_df = get_compliance_by_category(test_db_with_data)
    assert not cat_df.empty
    assert "category" in cat_df.columns
    categories = set(cat_df["category"].unique())
    assert (
        "Encryption" in categories
        or "Backup & Recovery" in categories
        or "Network Security" in categories
    )


def test_visualization_gauges():
    """Test gauge chart creation and score coloring."""
    assert _get_score_color(90) == "#00cc44"
    assert _get_score_color(75) == "#88cc00"
    assert _get_score_color(60) == "#ffaa00"
    assert _get_score_color(30) == "#ff4444"

    fig = create_compliance_gauge(82.5, "Overall Compliance")
    assert isinstance(fig, go.Figure)
    assert fig.data[0].type == "indicator"
    assert fig.data[0].value == 82.5


def test_compliance_gauge_creation():
    """Test that compliance gauge chart is created successfully."""
    fig = create_compliance_gauge(75.5, "Test Compliance")
    assert fig is not None
    assert len(fig.data) > 0


def test_regulation_breakdown_chart():
    """Test regulation breakdown chart creation."""
    data = pd.DataFrame(
        {
            "regulation": ["GDPR", "DORA", "NIS2"],
            "compliant": [10, 8, 12],
            "partial": [3, 5, 2],
            "non_compliant": [2, 2, 1],
        }
    )

    fig = create_regulation_breakdown_chart(data)
    assert fig is not None
    assert len(fig.data) == 3  # Three traces (compliant, partial, non-compliant)


def test_trend_line_chart():
    """Test trend line chart creation."""
    data = pd.DataFrame(
        {
            "assessment_date": pd.date_range("2026-01-01", periods=5),
            "kpi_value": [70, 72, 75, 78, 80],
        }
    )

    fig = create_trend_line_chart(data, "Test KPI")
    assert fig is not None
    assert len(fig.data) > 0


def test_visualization_charts():
    """Test creation of heatmaps, breakdown charts, scatter, trend, and friction charts."""
    # Heatmap
    heatmap_df = pd.DataFrame(
        [
            {"regulation": "GDPR", "category": "Encryption", "compliance_rate": 100.0},
            {"regulation": "DORA", "category": "Network", "compliance_rate": 50.0},
        ]
    )
    fig_heatmap = create_compliance_heatmap(heatmap_df)
    assert isinstance(fig_heatmap, go.Figure)

    # Empty heatmap fallback
    fig_empty_heatmap = create_compliance_heatmap(pd.DataFrame())
    assert isinstance(fig_empty_heatmap, go.Figure)

    # Regulation breakdown
    reg_df = pd.DataFrame(
        [
            {"regulation": "GDPR", "compliant": 5, "partial": 1, "non_compliant": 0},
            {"regulation": "DORA", "compliant": 2, "partial": 3, "non_compliant": 2},
        ]
    )
    fig_reg = create_regulation_breakdown_chart(reg_df)
    assert isinstance(fig_reg, go.Figure)

    # Confidence scatter
    controls_df = pd.DataFrame(
        [
            {
                "regulatory_control_id": "ctrl-1",
                "control_title": "Title 1",
                "regulation": "GDPR",
                "confidence_score": 0.95,
                "compliance_status": "compliant",
                "friction_points": "[]",
            }
        ]
    )
    fig_scatter = create_confidence_scatter(controls_df)
    assert isinstance(fig_scatter, go.Figure)

    # Trend line chart
    trend_df = pd.DataFrame(
        [
            {"assessment_date": "2026-01-01", "kpi_value": 70.0},
            {"assessment_date": "2026-02-01", "kpi_value": 85.0},
        ]
    )
    fig_trend = create_trend_line_chart(trend_df, "overall_compliance_rate")
    assert isinstance(fig_trend, go.Figure)

    # Friction impact chart
    friction_df = pd.DataFrame(
        [
            {
                "regulatory_control_id": "ctrl-1",
                "compliance_status": "partial",
                "friction_points": json.dumps(["Ambiguity 1", "Human bottleneck"]),
            }
        ]
    )
    fig_friction = create_friction_impact_chart(friction_df)
    assert isinstance(fig_friction, go.Figure)

    # Category pie chart
    cat_df = pd.DataFrame(
        [
            {"category": "Encryption", "total_controls": 4},
            {"category": "Network", "total_controls": 6},
        ]
    )
    fig_pie = create_category_pie_chart(cat_df)
    assert isinstance(fig_pie, go.Figure)


def test_export_functionality(test_db_with_data, tmp_path):
    """Test Excel and HTML/PDF export capabilities."""
    data = get_latest_assessment_data(test_db_with_data)
    assert data is not None

    # Test Excel Export
    excel_path = tmp_path / "test_report.xlsx"
    excel_bytes = export_assessment_to_excel(data, output_path=excel_path)
    assert len(excel_bytes) > 0
    assert excel_path.exists()

    # Read back Excel sheets to verify content
    excel_file = pd.ExcelFile(excel_path)
    assert "Executive Summary" in excel_file.sheet_names
    assert "Control Assessment" in excel_file.sheet_names
    assert "KPIs" in excel_file.sheet_names
    assert "Socio-Technical Friction" in excel_file.sheet_names

    summary_sheet = pd.read_excel(excel_file, sheet_name="Executive Summary")
    assert not summary_sheet.empty

    # Test HTML Report Generation
    html_report = generate_executive_html_report(data)
    assert "<!DOCTYPE html>" in html_report
    assert "Compliance Assessment Executive Report" in html_report
    assert "50.0%" in html_report or "Overall Compliance" in html_report

    # Test PDF Export (or fallback to HTML)
    pdf_path = tmp_path / "executive_report"
    exported_bytes = export_executive_summary_to_pdf(data, output_path=pdf_path)
    assert len(exported_bytes) > 0
