"""Gap Analysis Data Models.

This module defines Pydantic v2 models representing the results of
automated gap analysis between regulatory requirements and technical
implementations.

Research Context (MPI-SP):
    These models capture not just binary compliance (pass/fail) but
    also multi-factor confidence scores, partial compliance, and
    socio-technical friction points - key elements for understanding
    the real-world challenges of regulatory compliance automation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.technical_control import ControlCategory


def _utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def _generate_report_id() -> str:
    """Generate a unique UUIDv4 string for gap analysis reports."""
    return str(uuid.uuid4())


# ============================================================================
# PIPELINE DATA MODELS (Step 3 Standard Architecture)
# ============================================================================


class GapType(str, Enum):
    """Types of compliance gaps."""

    MISSING = "missing"  # Control not implemented at all
    PARTIAL = "partial"  # Control partially implemented
    NON_COMPLIANT = "non_compliant"  # Control implemented but doesn't meet requirements
    UNKNOWN = "unknown"  # Cannot determine compliance status
    COMPLIANT = "compliant"  # Control fully compliant


class ConfidenceLevel(str, Enum):
    """Confidence levels for gap analysis results."""

    HIGH = "high"  # >80% confidence
    MEDIUM = "medium"  # 50-80% confidence
    LOW = "low"  # <50% confidence


class GapAnalysisResult(BaseModel):
    """Represents the result of analyzing a single control.

    This is the fundamental unit of gap analysis - each result represents
    one regulatory control and its compliance status in the technical baseline.
    """

    model_config = ConfigDict(extra="allow")

    regulatory_control_id: str = Field(
        ...,
        description="ID of the regulatory control (e.g., 'gdpr-art32')",
    )
    regulatory_control_title: str = Field(
        ...,
        description="Title of the regulatory control",
    )
    regulation: str = Field(
        ...,
        description="Regulation this control belongs to (GDPR, DORA, NIS2)",
    )
    mapped_technical_controls: List[str] = Field(
        default_factory=list,
        description="IDs of technical controls that map to this regulatory control",
    )
    gap_type: GapType = Field(
        ...,
        description="Type of gap identified",
    )
    compliance_status: str = Field(
        ...,
        description="Overall compliance status (compliant, partial, non-compliant)",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for this assessment",
    )
    confidence_level: ConfidenceLevel = Field(
        ...,
        description="Categorized confidence level",
    )
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence supporting this assessment",
    )
    friction_points: List[str] = Field(
        default_factory=list,
        description="Socio-technical friction points identified",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations for remediation",
    )
    analysis_timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When this analysis was performed",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context about the analysis",
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        """Ensure confidence score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class GapAnalysisSummary(BaseModel):
    """Aggregate statistics and health metrics for the gap analysis."""

    model_config = ConfigDict(extra="ignore")

    total_regulatory_controls: int = Field(default=0)
    compliant_controls: int = Field(default=0)
    partially_compliant_controls: int = Field(default=0)
    non_compliant_controls: int = Field(default=0)
    unmapped_controls: int = Field(default=0)
    overall_compliance_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    overall_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    total_gaps: int = Field(default=0)
    gaps_by_severity: Dict[str, int] = Field(default_factory=dict)
    hitl_reviews_required: int = Field(default=0)

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dict-style key access."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style subscription."""
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)


class GapAnalysisReport(BaseModel):
    """Represents a complete gap analysis report.

    This is the top-level container that holds all gap analysis results
    and provides summary statistics for the entire assessment.
    """

    model_config = ConfigDict(extra="allow")

    report_id: str = Field(
        default_factory=_generate_report_id,
        description="Unique identifier for this report",
    )
    catalog_id: str = Field(
        default="regulatory-catalog",
        description="ID of the OSCAL catalog analyzed",
    )
    baseline_id: str = Field(
        default="unknown-baseline",
        description="ID of the technical baseline analyzed",
    )
    analysis_timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When the analysis was performed",
    )
    total_regulatory_controls: int = Field(
        default=0,
        description="Total number of regulatory controls analyzed",
    )
    total_technical_controls: int = Field(
        default=0,
        description="Total number of technical controls in baseline",
    )
    results: List[GapAnalysisResult] = Field(
        default_factory=list,
        description="Individual gap analysis results",
    )
    summary: Any = Field(
        default_factory=dict,
        description="Summary statistics",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the analysis",
    )

    # Backward compatibility fields for advanced evaluation engine
    catalog_title: Optional[str] = Field(default=None)
    cloud_provider: str = Field(default="unknown")
    evaluations: List[Any] = Field(default_factory=list)
    all_gaps: List[Any] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utc_now)

    @field_validator("report_id")
    @classmethod
    def validate_report_id(cls, v: str) -> str:
        """Ensure report ID is non-empty."""
        if not v or not v.strip():
            raise ValueError("report_id cannot be blank")
        return v

    def get_results_by_gap_type(self, gap_type: GapType) -> List[GapAnalysisResult]:
        """Filter results by gap type."""
        return [r for r in self.results if r.gap_type == gap_type]

    def get_non_compliant_results(self) -> List[GapAnalysisResult]:
        """Get all non-compliant results."""
        return [
            r
            for r in self.results
            if r.gap_type in [GapType.MISSING, GapType.NON_COMPLIANT, GapType.PARTIAL]
        ]

    def get_compliance_summary(self) -> Dict[str, int]:
        """Generate a summary of compliance status counts."""
        summary = {gap_type.value: 0 for gap_type in GapType}
        for result in self.results:
            summary[result.gap_type.value] += 1
        return summary

    def get_confidence_summary(self) -> Dict[str, int]:
        """Generate a summary of confidence level counts."""
        summary = {level.value: 0 for level in ConfidenceLevel}
        for result in self.results:
            summary[result.confidence_level.value] += 1
        return summary


# ============================================================================
# EXTENDED SOCIO-TECHNICAL MODELS (MPI-SP Research Extensions)
# ============================================================================


class GapSeverity(str, Enum):
    """Categorical severity of a detected compliance gap."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class RegulationComplianceStatus(str, Enum):
    """Compliance assessment outcome for a regulatory article."""

    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNMAPPED = "unmapped"


class ComplianceGap(BaseModel):
    """Represents a concrete divergence between legal expectation and infrastructure state."""

    model_config = ConfigDict(extra="allow")

    gap_id: str = Field(
        ...,
        description="Deterministic or unique identifier for the gap (e.g., 'GAP-GDPR-32-001').",
    )
    regulatory_control_id: str = Field(
        ...,
        description="Associated regulatory article ID (e.g., 'gdpr-art-32').",
    )
    regulation: str = Field(
        ...,
        description="Source regulatory framework (e.g., 'GDPR', 'DORA', 'NIS2').",
    )
    sub_clause_id: Optional[str] = Field(
        default=None,
        description="Specific clause or item if applicable (e.g., '1(a)').",
    )
    technical_control_id: Optional[str] = Field(
        default=None,
        description="ID of the failing or deficient technical control instance.",
    )
    resource_id: Optional[str] = Field(
        default=None,
        description="Cloud provider resource identifier where the gap was observed.",
    )
    resource_name: Optional[str] = Field(
        default=None,
        description="Human-readable resource name.",
    )
    severity: GapSeverity = Field(
        ...,
        description="Risk/severity rating of the gap.",
    )
    title: str = Field(
        ...,
        description="Concise description of the compliance deficiency.",
    )
    description: str = Field(
        ...,
        description="Detailed contextual explanation of why the infrastructure failed the rule.",
    )
    observed_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Observed empirical configuration from cloud telemetry.",
    )
    expected_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected compliant baseline configuration.",
    )
    remediation_guidance: str = Field(
        ...,
        description="Step-by-step technical remediation instructions for engineering teams.",
    )
    hitl_action: Optional[str] = Field(
        default=None,
        description="Specific Human-in-the-Loop review action if legal ambiguity is involved.",
    )


class ConfidenceBreakdown(BaseModel):
    """Explains the mathematical factors composing a control's confidence score."""

    model_config = ConfigDict(extra="ignore")

    evidence_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Proportion of expected technical control categories with observed evidence.",
    )
    friction_penalty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Discount factor applied due to legal ambiguity in the statutory text.",
    )
    status_consistency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Uniformity of evidence status across evaluated resources.",
    )
    hitl_adjustment: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence boost applied if qualified human review was performed.",
    )
    final_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Synthesized confidence score between 0.0 and 1.0.",
    )


class ControlEvaluation(BaseModel):
    """Comprehensive compliance evaluation result for a single regulatory control."""

    model_config = ConfigDict(extra="allow")

    regulatory_control_id: str = Field(
        ...,
        description="Unique identifier for the regulatory control (e.g., 'gdpr-art-32').",
    )
    regulation: str = Field(
        ...,
        description="Regulatory framework name (GDPR, DORA, NIS2).",
    )
    title: str = Field(
        ...,
        description="Formal title of the regulatory requirement.",
    )
    legal_reference: str = Field(
        default="",
        description="Statutory legal reference citation.",
    )
    friction_level: str = Field(
        default="Low",
        description="Socio-technical friction rating ('Low', 'Medium', 'High').",
    )
    friction_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Numeric friction score (0.0 - 10.0) from Step 1 analysis.",
    )
    hitl_recommended: bool = Field(
        default=False,
        description="Whether human-in-the-loop review is required to confirm compliance.",
    )
    status: RegulationComplianceStatus = Field(
        ...,
        description=(
            "Evaluated compliance posture "
            "(COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT, UNMAPPED)."
        ),
    )
    compliance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Calculated compliance percentage (0.0% - 100.0%).",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Evidence and ambiguity weighted confidence score (0.0 - 1.0).",
    )
    confidence_breakdown: Optional[ConfidenceBreakdown] = Field(
        default=None,
        description="Mathematical component details explaining the confidence score.",
    )
    mapped_categories: List[ControlCategory] = Field(
        default_factory=list,
        description="Technical control categories mapped to this regulatory article.",
    )
    total_mapped_controls: int = Field(
        default=0,
        description="Count of empirical technical controls evaluated.",
    )
    passed_controls: int = Field(
        default=0,
        description="Count of evaluated technical controls with COMPLIANT status.",
    )
    failed_controls: int = Field(
        default=0,
        description="Count of evaluated technical controls with NON_COMPLIANT status.",
    )
    partial_controls: int = Field(
        default=0,
        description="Count of evaluated technical controls with PARTIAL status.",
    )
    gaps: List[ComplianceGap] = Field(
        default_factory=list,
        description="Specific compliance gaps identified during evaluation.",
    )
    remediation_steps: List[str] = Field(
        default_factory=list,
        description="Consolidated technical remediation tasks for engineers.",
    )
    hitl_guidance: List[str] = Field(
        default_factory=list,
        description="Actionable HITL governance review procedures.",
    )
