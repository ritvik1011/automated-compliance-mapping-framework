"""Database Repository - Data Access Layer.

This module provides a clean interface for storing and retrieving
compliance assessment data from the database.

Research Context:
    A clean data access layer ensures that the pipeline logic is
    decoupled from database implementation details, making it easy
    to switch databases (SQLite → PostgreSQL) without changing
    pipeline code.
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.gap_analysis import GapAnalysisReport
from src.pipeline.database.models import (
    ComplianceAssessment,
    ComplianceKPI,
    ControlAssessmentResult,
)

logger = logging.getLogger(__name__)


class ComplianceRepository:
    """Repository for compliance assessment data.

    Provides methods to store assessment results, query historical data,
    and calculate trends.
    """

    def __init__(self, session: Session):
        """Initialize the repository with a SQLAlchemy session."""
        self.session = session

    def store_assessment(
        self,
        report: GapAnalysisReport,
        cloud_provider: str,
        subscription_id: Optional[str] = None,
    ) -> ComplianceAssessment:
        """Store a complete gap analysis report in the database.

        Args:
            report: GapAnalysisReport from the gap analysis engine
            cloud_provider: Cloud provider (azure, aws, etc.)
            subscription_id: Cloud subscription ID

        Returns:
            The created ComplianceAssessment record
        """
        # Calculate summary counts safely
        summary = report.summary
        if hasattr(summary, "model_dump"):
            summary_dict = summary.model_dump()
        elif isinstance(summary, dict):
            summary_dict = summary
        else:
            summary_dict = {}

        compliance_breakdown = summary_dict.get("compliance_status_breakdown", {})
        if not compliance_breakdown and report.results:
            compliance_breakdown = {
                "compliant": len([r for r in report.results if r.compliance_status == "compliant"]),
                "partial": len([r for r in report.results if r.compliance_status == "partial"]),
                "non-compliant": len(
                    [
                        r
                        for r in report.results
                        if r.compliance_status in ["non-compliant", "non_compliant"]
                    ]
                ),
                "unknown": len([r for r in report.results if r.compliance_status == "unknown"]),
            }

        avg_confidence = summary_dict.get("avg_confidence_score")
        if avg_confidence is None and report.results:
            avg_confidence = sum(r.confidence_score for r in report.results) / len(report.results)
        elif avg_confidence is None:
            avg_confidence = 0.0

        # Normalise timestamp for sqlite/sqlalchemy datetime compatibility
        assessment_date = report.analysis_timestamp
        if assessment_date and getattr(assessment_date, "tzinfo", None) is not None:
            assessment_date = assessment_date.replace(tzinfo=None)

        # Create assessment record
        assessment = ComplianceAssessment(
            id=report.report_id,
            assessment_date=assessment_date or datetime.utcnow(),
            baseline_id=report.baseline_id,
            catalog_id=report.catalog_id,
            cloud_provider=cloud_provider,
            subscription_id=subscription_id,
            total_regulatory_controls=report.total_regulatory_controls,
            total_technical_controls=report.total_technical_controls,
            compliant_count=compliance_breakdown.get("compliant", 0),
            partial_count=compliance_breakdown.get("partial", 0),
            non_compliant_count=compliance_breakdown.get(
                "non-compliant", compliance_breakdown.get("non_compliant", 0)
            ),
            unknown_count=compliance_breakdown.get("unknown", 0),
            overall_compliance_score=self._calculate_overall_score(compliance_breakdown),
            average_confidence_score=float(avg_confidence),
            assessment_metadata=json.dumps(report.metadata, default=str),
        )

        self.session.add(assessment)

        # Store individual control results
        for result in report.results:
            gap_type_str = (
                result.gap_type.value if hasattr(result.gap_type, "value") else str(result.gap_type)
            )
            confidence_level_str = (
                result.confidence_level.value
                if hasattr(result.confidence_level, "value")
                else str(result.confidence_level)
            )

            control_result = ControlAssessmentResult(
                assessment_id=assessment.id,
                regulatory_control_id=result.regulatory_control_id,
                regulation=result.regulation,
                control_title=result.regulatory_control_title,
                gap_type=gap_type_str,
                compliance_status=result.compliance_status,
                confidence_score=result.confidence_score,
                confidence_level=confidence_level_str,
                evidence=json.dumps(result.evidence, default=str),
                friction_points=json.dumps(result.friction_points, default=str),
                recommendations=json.dumps(result.recommendations, default=str),
            )
            self.session.add(control_result)

        self.session.commit()
        logger.info(
            f"✓ Stored assessment {assessment.id} with {len(report.results)} control results"
        )

        return assessment

    def store_kpis(self, assessment_id: str, kpis: Dict[str, float]) -> List[ComplianceKPI]:
        """Store calculated KPIs for an assessment.

        Args:
            assessment_id: ID of the assessment
            kpis: Dictionary of KPI name → value

        Returns:
            List of created ComplianceKPI records
        """
        kpi_records = []

        for kpi_name, kpi_value in kpis.items():
            category = self._determine_kpi_category(kpi_name)
            unit = "percentage" if "rate" in kpi_name or "percentage" in kpi_name else "count"

            kpi = ComplianceKPI(
                assessment_id=assessment_id,
                kpi_name=kpi_name,
                kpi_value=float(kpi_value),
                kpi_unit=unit,
                kpi_category=category,
            )
            self.session.add(kpi)
            kpi_records.append(kpi)

        self.session.commit()
        logger.info(f"✓ Stored {len(kpi_records)} KPIs for assessment {assessment_id}")

        return kpi_records

    def get_latest_assessment(self) -> Optional[ComplianceAssessment]:
        """Get the most recent compliance assessment."""
        return (
            self.session.query(ComplianceAssessment)
            .order_by(ComplianceAssessment.assessment_date.desc())
            .first()
        )

    def get_assessments_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[ComplianceAssessment]:
        """Get assessments within a date range."""
        return (
            self.session.query(ComplianceAssessment)
            .filter(
                ComplianceAssessment.assessment_date >= start_date,  # type: ignore[arg-type]
                ComplianceAssessment.assessment_date <= end_date,  # type: ignore[arg-type]
            )
            .order_by(ComplianceAssessment.assessment_date.desc())
            .all()
        )

    def get_kpi_trend(self, kpi_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical trend for a specific KPI.

        Useful for visualizing compliance improvement over time.
        """
        results = (
            self.session.query(ComplianceKPI)
            .filter(ComplianceKPI.kpi_name == kpi_name)
            .order_by(ComplianceKPI.calculated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "date": kpi.calculated_at.isoformat(),
                "value": kpi.kpi_value,
                "assessment_id": kpi.assessment_id,
            }
            for kpi in results
        ]

    def _calculate_overall_score(self, compliance_breakdown: Dict[str, int]) -> float:
        """Calculate overall compliance score as percentage."""
        total = sum(compliance_breakdown.values())
        if total == 0:
            return 0.0

        compliant = compliance_breakdown.get("compliant", 0)
        partial = compliance_breakdown.get("partial", 0)

        # Weighted score: compliant = 1.0, partial = 0.5, others = 0.0
        score = (compliant * 1.0 + partial * 0.5) / total
        return round(score * 100, 2)

    def _determine_kpi_category(self, kpi_name: str) -> str:
        """Determine the category of a KPI based on its name."""
        kpi_lower = kpi_name.lower()

        if "gdpr" in kpi_lower:
            return "gdpr"
        elif "dora" in kpi_lower:
            return "dora"
        elif "nis2" in kpi_lower:
            return "nis2"
        else:
            return "overall"
