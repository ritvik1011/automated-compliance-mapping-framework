"""Gap Evaluator - Core Gap Analysis Engine.

This module implements the core logic for comparing regulatory requirements
against technical implementations to identify compliance gaps.

Research Context:
    The gap evaluator is where the "Policy-as-Code" promise meets reality.
    By analyzing gaps systematically, we can identify patterns in compliance
    challenges and quantify the socio-technical friction inherent in
    translating legal requirements into technical specifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from src.gap_analysis.confidence_scorer import ConfidenceScorer
from src.gap_analysis.control_mapper import ControlMapper
from src.models.gap_analysis import (
    GapAnalysisReport,
    GapAnalysisResult,
    GapType,
)
from src.models.technical_control import (
    ComplianceStatus,
    InfrastructureBaseline,
    TechnicalControl,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class GapEvaluator:
    """Core engine for automated gap analysis.

    The evaluator:
    1. Maps regulatory controls to technical controls
    2. Evaluates compliance status for each mapping
    3. Calculates confidence scores
    4. Identifies friction points
    5. Generates actionable recommendations
    """

    def __init__(self, control_mapper: Optional[ControlMapper] = None):
        """Initialize the gap evaluator.

        Args:
            control_mapper: ControlMapper instance. If None, creates default mapper.
        """
        self.control_mapper = control_mapper or ControlMapper()
        self.confidence_scorer = ConfidenceScorer()

    def evaluate_gaps(
        self,
        catalog_controls: List[Dict[str, Any]],
        baseline: InfrastructureBaseline,
        friction_data: Optional[Dict[str, str]] = None,
    ) -> GapAnalysisReport:
        """Perform gap analysis between regulatory catalog and technical baseline.

        Args:
            catalog_controls: List of regulatory controls from OSCAL catalog
            baseline: Technical baseline from cloud infrastructure
            friction_data: Optional dict mapping control IDs to friction levels

        Returns:
            GapAnalysisReport containing all analysis results
        """
        logger.info("Starting gap analysis")

        friction_data = friction_data or {}
        results: List[GapAnalysisResult] = []

        # Get all available technical control IDs
        available_tech_controls = [tc.control_id for tc in baseline.controls]

        # Analyze each regulatory control
        for catalog_control in catalog_controls:
            reg_control_id = str(catalog_control.get("id") or "")
            reg_control_title = str(catalog_control.get("title") or "Unknown")
            regulation = self._extract_regulation_from_id(reg_control_id)

            # Map to technical controls
            mapped_tech_ids = self.control_mapper.get_technical_controls_for_regulatory(
                reg_control_id, available_tech_controls
            )

            # Get the actual technical control objects
            mapped_tech_controls = [
                tc for tc in baseline.controls if tc.control_id in mapped_tech_ids
            ]

            # Evaluate gap
            gap_result = self._evaluate_single_control(
                reg_control_id=reg_control_id,
                reg_control_title=reg_control_title,
                regulation=regulation,
                mapped_tech_controls=mapped_tech_controls,
                friction_level=friction_data.get(reg_control_id, "medium"),
            )

            results.append(gap_result)

        # Build report
        report = GapAnalysisReport(
            report_id=f"gap-report-{uuid.uuid4()}",
            catalog_id="regulatory-catalog",
            baseline_id=baseline.baseline_id,
            total_regulatory_controls=len(catalog_controls),
            total_technical_controls=len(baseline.controls),
            results=results,
            summary=self._generate_summary(results),
            metadata={
                "evaluator_version": "1.0.0",
                "analysis_timestamp": _utc_now().isoformat(),
            },
        )

        logger.info(
            f"Gap analysis complete. Analyzed {len(catalog_controls)} regulatory controls, "
            f"found {len(results)} results"
        )

        return report

    def _evaluate_single_control(
        self,
        reg_control_id: str,
        reg_control_title: str,
        regulation: str,
        mapped_tech_controls: List[TechnicalControl],
        friction_level: str,
    ) -> GapAnalysisResult:
        """Evaluate a single regulatory control against mapped technical controls.

        This is the core logic for determining compliance status.
        """
        # Determine gap type
        gap_type = self._determine_gap_type(mapped_tech_controls)

        # Determine compliance status
        compliance_status = self._determine_compliance_status(mapped_tech_controls)

        # Calculate confidence score
        confidence_score, confidence_level = self.confidence_scorer.calculate_confidence(
            reg_control_id=reg_control_id,
            mapped_technical_controls=mapped_tech_controls,
            friction_level=friction_level,
        )

        # Gather evidence
        evidence = self._gather_evidence(mapped_tech_controls)

        # Identify friction points
        friction_points = self._identify_friction_points(
            reg_control_id, mapped_tech_controls, friction_level
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            gap_type, mapped_tech_controls, friction_points
        )

        return GapAnalysisResult(
            regulatory_control_id=reg_control_id,
            regulatory_control_title=reg_control_title,
            regulation=regulation,
            mapped_technical_controls=[tc.control_id for tc in mapped_tech_controls],
            gap_type=gap_type,
            compliance_status=compliance_status,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            evidence=evidence,
            friction_points=friction_points,
            recommendations=recommendations,
            metadata={
                "friction_level": friction_level,
                "num_mapped_controls": len(mapped_tech_controls),
            },
        )

    def _determine_gap_type(self, tech_controls: List[TechnicalControl]) -> GapType:
        """Determine the type of gap based on technical controls."""
        if not tech_controls:
            return GapType.MISSING

        statuses = [tc.compliance_status for tc in tech_controls]

        if all(s == ComplianceStatus.COMPLIANT for s in statuses):
            return GapType.COMPLIANT
        elif all(s == ComplianceStatus.NON_COMPLIANT for s in statuses):
            return GapType.NON_COMPLIANT
        elif any(s == ComplianceStatus.NON_COMPLIANT for s in statuses):
            return GapType.PARTIAL
        elif any(s == ComplianceStatus.PARTIAL for s in statuses):
            return GapType.PARTIAL
        else:
            return GapType.UNKNOWN

    def _determine_compliance_status(self, tech_controls: List[TechnicalControl]) -> str:
        """Determine overall compliance status."""
        if not tech_controls:
            return "non-compliant"

        statuses = [tc.compliance_status for tc in tech_controls]

        if all(s == ComplianceStatus.COMPLIANT for s in statuses):
            return "compliant"
        elif all(s == ComplianceStatus.NON_COMPLIANT for s in statuses):
            return "non-compliant"
        elif any(s == ComplianceStatus.NON_COMPLIANT for s in statuses):
            return "partial"
        elif any(s == ComplianceStatus.PARTIAL for s in statuses):
            return "partial"
        else:
            return "unknown"

    def _gather_evidence(self, tech_controls: List[TechnicalControl]) -> List[Dict[str, Any]]:
        """Gather evidence from technical controls."""
        evidence: List[Dict[str, Any]] = []
        for tc in tech_controls:
            evidence.append(
                {
                    "control_id": tc.control_id,
                    "resource_name": tc.resource_name,
                    "compliance_status": tc.compliance_status.value,
                    "current_state": tc.current_state,
                    "timestamp": tc.evidence_timestamp.isoformat(),
                }
            )
        return evidence

    def _identify_friction_points(
        self,
        reg_control_id: str,
        tech_controls: List[TechnicalControl],
        friction_level: str,
    ) -> List[str]:
        """Identify socio-technical friction points."""
        friction_points: List[str] = []

        if friction_level.lower() == "high":
            friction_points.append(
                f"Regulatory control '{reg_control_id}' contains ambiguous language "
                "that cannot be fully automated"
            )

        if not tech_controls:
            friction_points.append("No technical controls found - manual mapping required")

        if len(tech_controls) > 5:
            friction_points.append(
                f"Complex mapping ({len(tech_controls)} technical controls) - "
                "requires careful coordination"
            )

        return friction_points

    def _generate_recommendations(
        self,
        gap_type: GapType,
        tech_controls: List[TechnicalControl],
        friction_points: List[str],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations: List[str] = []

        if gap_type == GapType.MISSING:
            recommendations.append("Implement technical controls for this regulatory requirement")
            recommendations.append(
                "Review regulatory text to identify specific technical measures needed"
            )
        elif gap_type == GapType.NON_COMPLIANT:
            recommendations.append("Remediate non-compliant technical controls")
            recommendations.append("Review current implementation against regulatory requirements")
        elif gap_type == GapType.PARTIAL:
            recommendations.append("Complete partial implementation of technical controls")
            recommendations.append("Identify missing components and implement them")

        if friction_points:
            recommendations.append("Conduct manual review due to socio-technical friction")
            recommendations.append("Engage legal and technical teams to clarify requirements")

        return recommendations

    def _extract_regulation_from_id(self, control_id: str) -> str:
        """Extract regulation name from control ID."""
        cid = control_id.lower()
        if cid.startswith("gdpr"):
            return "GDPR"
        elif cid.startswith("dora"):
            return "DORA"
        elif cid.startswith("nis2"):
            return "NIS2"
        else:
            return "Unknown"

    def _generate_summary(self, results: List[GapAnalysisResult]) -> Dict[str, Any]:
        """Generate summary statistics for the report."""
        summary: Dict[str, Any] = {
            "total_controls_analyzed": len(results),
            "gap_type_breakdown": {},
            "compliance_status_breakdown": {},
            "confidence_breakdown": {},
            "avg_confidence_score": 0.0,
        }

        # Gap type breakdown
        for gap_type in GapType:
            count = len([r for r in results if r.gap_type == gap_type])
            summary["gap_type_breakdown"][gap_type.value] = count

        # Compliance status breakdown
        compliance_statuses = ["compliant", "partial", "non-compliant", "unknown"]
        for status in compliance_statuses:
            count = len([r for r in results if r.compliance_status == status])
            summary["compliance_status_breakdown"][status] = count

        # Confidence breakdown
        from src.models.gap_analysis import ConfidenceLevel

        for level in ConfidenceLevel:
            count = len([r for r in results if r.confidence_level == level])
            summary["confidence_breakdown"][level.value] = count

        # Average confidence score
        if results:
            avg_confidence = sum(r.confidence_score for r in results) / len(results)
            summary["avg_confidence_score"] = round(avg_confidence, 3)

        return summary
