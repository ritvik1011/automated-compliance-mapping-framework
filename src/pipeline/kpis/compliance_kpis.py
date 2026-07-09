"""Compliance KPI Calculator.

This module calculates Key Performance Indicators (KPIs) from gap analysis
results. KPIs provide executive-level metrics for compliance monitoring.

Research Context:
    KPIs are essential for:
    1. Executive reporting (board-level compliance metrics)
    2. Trend analysis (is compliance improving?)
    3. DORA compliance (requires regular reporting to regulators)
    4. Benchmarking against industry standards

    The KPI calculation methodology is transparent and reproducible,
    supporting the research goal of Policy-as-Code automation.
"""

import logging
from typing import Dict, List

from src.models.gap_analysis import GapAnalysisReport

logger = logging.getLogger(__name__)


class ComplianceKPICalculator:
    """Calculates compliance KPIs from gap analysis reports.

    KPIs are categorized into:
    - Overall metrics (total compliance score)
    - Regulation-specific metrics (GDPR, DORA, NIS2)
    - Confidence metrics (reliability of assessments)
    - Friction metrics (socio-technical challenges)
    """

    def __init__(self, report: GapAnalysisReport):
        """Initialize the KPI calculator.

        Args:
            report: GapAnalysisReport from the gap analysis engine
        """
        self.report = report

    def calculate_all_kpis(self) -> Dict[str, float]:
        """Calculate all KPIs and return as a dictionary.

        Returns:
            Dictionary mapping KPI names to values
        """
        kpis: Dict[str, float] = {}

        # Overall metrics
        kpis.update(self._calculate_overall_kpis())

        # Regulation-specific metrics
        kpis.update(self._calculate_regulation_kpis())

        # Confidence metrics
        kpis.update(self._calculate_confidence_kpis())

        # Friction metrics
        kpis.update(self._calculate_friction_kpis())

        logger.info(f"✓ Calculated {len(kpis)} KPIs")
        return kpis

    def _calculate_overall_kpis(self) -> Dict[str, float]:
        """Calculate overall compliance KPIs."""
        summary = self.report.summary
        if hasattr(summary, "model_dump"):
            summary_dict = summary.model_dump()
        elif isinstance(summary, dict):
            summary_dict = summary
        else:
            summary_dict = {}

        compliance_breakdown = summary_dict.get("compliance_status_breakdown", {})
        if not compliance_breakdown and self.report.results:
            compliant_c = len([r for r in self.report.results if r.compliance_status == "compliant"])
            partial_c = len([r for r in self.report.results if r.compliance_status == "partial"])
            non_c = len(
                [
                    r
                    for r in self.report.results
                    if r.compliance_status in ["non-compliant", "non_compliant"]
                ]
            )
            unk_c = len([r for r in self.report.results if r.compliance_status == "unknown"])
            compliance_breakdown = {
                "compliant": compliant_c,
                "partial": partial_c,
                "non-compliant": non_c,
                "unknown": unk_c,
            }

        total = sum(compliance_breakdown.values())
        if total == 0:
            total = len(self.report.results)
        if total == 0:
            return {
                "overall_compliance_rate": 0.0,
                "total_controls_analyzed": 0.0,
                "compliant_controls_count": 0.0,
                "partial_controls_count": 0.0,
                "non_compliant_controls_count": 0.0,
                "unknown_controls_count": 0.0,
            }

        compliant = compliance_breakdown.get("compliant", 0)
        partial = compliance_breakdown.get("partial", 0)
        non_compliant = compliance_breakdown.get(
            "non-compliant", compliance_breakdown.get("non_compliant", 0)
        )
        unknown = compliance_breakdown.get("unknown", 0)

        # Overall compliance rate (weighted)
        compliance_rate = ((compliant * 1.0 + partial * 0.5) / total) * 100

        return {
            "overall_compliance_rate": round(compliance_rate, 2),
            "total_controls_analyzed": float(total),
            "compliant_controls_count": float(compliant),
            "partial_controls_count": float(partial),
            "non_compliant_controls_count": float(non_compliant),
            "unknown_controls_count": float(unknown),
        }

    def _calculate_regulation_kpis(self) -> Dict[str, float]:
        """Calculate regulation-specific KPIs."""
        kpis: Dict[str, float] = {}

        # Group results by regulation
        by_regulation: Dict[str, List] = {}
        for result in self.report.results:
            reg = result.regulation
            if reg not in by_regulation:
                by_regulation[reg] = []
            by_regulation[reg].append(result)

        # Calculate KPIs for each regulation
        for regulation, results in by_regulation.items():
            reg_lower = regulation.lower()
            total = len(results)
            compliant = len([r for r in results if r.compliance_status == "compliant"])
            partial = len([r for r in results if r.compliance_status == "partial"])

            if total > 0:
                compliance_rate = ((compliant * 1.0 + partial * 0.5) / total) * 100
            else:
                compliance_rate = 0.0

            kpis[f"{reg_lower}_compliance_rate"] = round(compliance_rate, 2)
            kpis[f"{reg_lower}_controls_count"] = float(total)
            kpis[f"{reg_lower}_compliant_count"] = float(compliant)

        return kpis

    def _calculate_confidence_kpis(self) -> Dict[str, float]:
        """Calculate confidence-related KPIs."""
        if not self.report.results:
            return {
                "average_confidence_score": 0.0,
                "high_confidence_percentage": 0.0,
            }

        # Average confidence score
        avg_confidence = sum(r.confidence_score for r in self.report.results) / len(
            self.report.results
        )

        # High confidence percentage
        high_confidence_count = len(
            [r for r in self.report.results if r.confidence_score >= 0.8]
        )
        high_confidence_pct = (high_confidence_count / len(self.report.results)) * 100

        return {
            "average_confidence_score": round(avg_confidence * 100, 2),
            "high_confidence_percentage": round(high_confidence_pct, 2),
        }

    def _calculate_friction_kpis(self) -> Dict[str, float]:
        """Calculate socio-technical friction KPIs."""
        if not self.report.results:
            return {
                "high_friction_controls_count": 0.0,
                "friction_rate": 0.0,
            }

        # Count controls with friction points
        high_friction_count = len(
            [r for r in self.report.results if len(r.friction_points) > 0]
        )

        friction_rate = (high_friction_count / len(self.report.results)) * 100

        return {
            "high_friction_controls_count": float(high_friction_count),
            "friction_rate": round(friction_rate, 2),
        }

    def generate_kpi_summary(self, kpis: Dict[str, float]) -> str:
        """Generate a human-readable summary of KPIs.

        Useful for executive reports and terminal output.
        """
        lines = [
            "═══════════════════════════════════════════════════════",
            "  Compliance KPI Summary",
            "═══════════════════════════════════════════════════════",
            "",
            f"  Overall Compliance Rate: {kpis.get('overall_compliance_rate', 0):.1f}%",
            f"  Total Controls Analyzed: {int(kpis.get('total_controls_analyzed', 0))}",
            f"  Average Confidence Score: {kpis.get('average_confidence_score', 0):.1f}%",
            f"  High Friction Controls: {int(kpis.get('high_friction_controls_count', 0))}",
            "",
        ]

        # Add regulation-specific KPIs
        for reg in ["gdpr", "dora", "nis2"]:
            rate = kpis.get(f"{reg}_compliance_rate")
            if rate is not None:
                lines.append(f"  {reg.upper()} Compliance Rate: {rate:.1f}%")

        lines.append("")
        lines.append("═══════════════════════════════════════════════════════")

        return "\n".join(lines)
