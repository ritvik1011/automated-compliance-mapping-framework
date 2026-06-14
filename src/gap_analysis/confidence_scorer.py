"""Confidence Scoring Engine for Gap Analysis.

This module calculates multi-factor confidence scores representing the
epistemic certainty of automated compliance assessments. It combines
empirical evidence volume, status consistency, and legal ambiguity
(socio-technical friction) to prevent "False Assurance" in governance.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

from src.models.gap_analysis import ConfidenceLevel
from src.models.technical_control import ComplianceStatus, TechnicalControl

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculates multi-dimensional confidence scores for gap analysis evaluations.

    Confidence reflects three dimensions:
    1. Evidence completeness: Number and coverage of mapped technical controls.
    2. Status consistency: Agreement among technical controls for a given resource or category.
    3. Legal friction penalty: Discount applied when statutory text is open-textured.
    """

    def __init__(
        self,
        high_friction_penalty: float = 0.20,
        medium_friction_penalty: float = 0.10,
        low_friction_penalty: float = 0.0,
    ) -> None:
        """Initialize the confidence scorer with configurable friction penalties."""
        self.high_friction_penalty = high_friction_penalty
        self.medium_friction_penalty = medium_friction_penalty
        self.low_friction_penalty = low_friction_penalty

    def calculate_confidence(
        self,
        reg_control_id: Optional[str] = None,
        mapped_technical_controls: Optional[List[TechnicalControl]] = None,
        friction_level: str = "medium",
        evidence_quality: Optional[str] = None,
        regulatory_control_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[float, ConfidenceLevel]:
        """Calculate confidence score and categorical confidence level.

        Args:
            reg_control_id: ID of the evaluated regulatory control.
            mapped_technical_controls: List of matching TechnicalControl instances.
            friction_level: Friction level string ('high', 'medium', 'low').
            evidence_quality: Optional evidence quality string ('good', 'poor').
            regulatory_control_id: Optional alias for reg_control_id.
            **kwargs: Extra contextual arguments.

        Returns:
            Tuple of (confidence_score: float in [0.0, 1.0], confidence_level: ConfidenceLevel).
        """
        target_id = regulatory_control_id or reg_control_id or "unknown"
        controls = mapped_technical_controls if mapped_technical_controls is not None else []

        if not controls:
            logger.debug(f"Zero technical controls for '{target_id}'; confidence is 0.0")
            return 0.0, ConfidenceLevel.LOW

        # 1. Base Evidence Volume Score
        num_controls = len(controls)
        if num_controls == 1:
            base_score = 0.70
        elif num_controls == 2:
            base_score = 0.85
        elif num_controls >= 3:
            base_score = 0.95
        else:
            base_score = 0.50

        # 2. Status Consistency Assessment
        statuses = [tc.compliance_status for tc in controls]
        unique_statuses = set(statuses)

        consistency_penalty = 0.0
        if len(unique_statuses) > 1:
            # Mixed results (e.g. some compliant, some non-compliant)
            if (
                ComplianceStatus.COMPLIANT in unique_statuses
                and ComplianceStatus.NON_COMPLIANT in unique_statuses
            ):
                consistency_penalty = 0.10
            elif ComplianceStatus.PARTIAL in unique_statuses:
                consistency_penalty = 0.05

        # 3. Socio-Technical Friction Discount
        f_level = friction_level.strip().lower()
        if f_level == "high":
            friction_penalty = self.high_friction_penalty
        elif f_level == "medium":
            friction_penalty = self.medium_friction_penalty
        else:
            friction_penalty = self.low_friction_penalty

        # 4. Evidence Quality Adjustment
        quality_adjustment = 0.0
        if evidence_quality:
            eq = evidence_quality.strip().lower()
            if eq in ["good", "high"]:
                quality_adjustment = 0.05
            elif eq in ["poor", "low"]:
                quality_adjustment = -0.15

        # Compute raw confidence
        raw_score = base_score - consistency_penalty - friction_penalty + quality_adjustment
        final_score = round(max(0.0, min(1.0, raw_score)), 3)

        # Map to ConfidenceLevel
        if final_score >= 0.80:
            level = ConfidenceLevel.HIGH
        elif final_score >= 0.50:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return final_score, level
