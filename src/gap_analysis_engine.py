"""Automated Gap Analysis Engine.

This module evaluates the gap between normative regulatory requirements
(NIST OSCAL Catalogs from Step 1) and empirical cloud infrastructure states
(NIST OSCAL Component-Definitions and Technical Baselines from Step 2).

Research Innovations (MPI-SP):
    1. Multi-Dimensional Confidence Scoring: Discloses the epistemic certainty
       of automated evaluations by penalizing legal ambiguity and missing evidence.
    2. Socio-Technical Friction Integration: Automatically flags requirements
       where binary Policy-as-Code checks are insufficient, triggering
       Human-in-the-Loop (HITL) review protocols.
    3. Actionable Engineering Remediation: Translates legal non-compliance
       into concrete, copy-pasteable cloud configuration directives.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.mappings.regulatory_mapping import CategoryMapping, RegulatoryMappingMatrix
from src.models.gap_analysis import (
    ComplianceGap,
    ConfidenceBreakdown,
    ControlEvaluation,
    GapAnalysisReport,
    GapAnalysisSummary,
    GapSeverity,
    RegulationComplianceStatus,
)
from src.models.technical_control import (
    ComplianceStatus,
    ControlCategory,
    InfrastructureBaseline,
    TechnicalControl,
)
from src.parser import RegulatoryArticle

logger = logging.getLogger(__name__)


class GapAnalysisEngine:
    """Core evaluation engine performing automated regulatory-to-technical gap analysis."""

    def __init__(
        self,
        mapping_matrix: Optional[RegulatoryMappingMatrix] = None,
        friction_weight_alpha: float = 0.35,
    ) -> None:
        """Initialize the Gap Analysis Engine.

        Args:
            mapping_matrix: RegulatoryMappingMatrix instance or None for default.
            friction_weight_alpha: Weight (0.0 to 1.0) controlling the penalty that
                legal ambiguity applies to automated confidence scores.
        """
        self.mapping_matrix = mapping_matrix or RegulatoryMappingMatrix()
        self.friction_weight_alpha = max(0.0, min(1.0, friction_weight_alpha))
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_catalog(
        self,
        source: Union[str, Path, Dict[str, Any], List[RegulatoryArticle]],
    ) -> List[Dict[str, Any]]:
        """Load and normalize regulatory controls from an OSCAL catalog or article list.

        Args:
            source: Path to OSCAL catalog JSON, dictionary, or list of RegulatoryArticles.

        Returns:
            List of normalized regulatory control dictionaries.
        """
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Regulatory catalog file not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._extract_controls_from_dict(data)

        if isinstance(source, dict):
            return self._extract_controls_from_dict(source)

        if isinstance(source, list):
            controls: List[Dict[str, Any]] = []
            for item in source:
                if isinstance(item, RegulatoryArticle):
                    controls.append(self._article_to_control_dict(item))
                elif isinstance(item, dict):
                    controls.append(item)
            return controls

        raise TypeError(f"Unsupported catalog source type: {type(source)}")

    def _extract_controls_from_dict(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract controls from raw OSCAL catalog dictionary."""
        if "catalog" in data and "controls" in data["catalog"]:
            return list(data["catalog"]["controls"])
        if "controls" in data and isinstance(data["controls"], list):
            return list(data["controls"])
        return []

    def _article_to_control_dict(self, article: RegulatoryArticle) -> Dict[str, Any]:
        """Convert a RegulatoryArticle model to an OSCAL-compatible control dictionary."""
        props = [
            {"name": "regulation", "value": article.regulation},
            {"name": "legal_reference", "value": article.legal_reference},
        ]
        if hasattr(article, "friction_level") and article.friction_level:
            props.append({"name": "friction_level", "value": str(article.friction_level)})
        if hasattr(article, "friction_score") and article.friction_score is not None:
            props.append({"name": "friction_score", "value": str(article.friction_score)})
        if hasattr(article, "hitl_recommended") and article.hitl_recommended is not None:
            props.append(
                {"name": "hitl_recommended", "value": str(article.hitl_recommended).lower()}
            )

        parts = []
        if article.sub_clauses:
            parts = [
                {
                    "name": "item",
                    "props": [{"name": "clause_id", "value": sc.clause_id}],
                    "prose": f"{sc.title or ''}: {sc.text}".strip(),
                }
                for sc in article.sub_clauses
            ]

        return {
            "id": article.article_id,
            "title": article.title,
            "props": props,
            "parts": [
                {
                    "name": "statement",
                    "prose": f"{article.title}. {article.legal_reference}",
                    "parts": parts,
                }
            ],
        }

    def load_baseline(
        self,
        source: Union[str, Path, Dict[str, Any], InfrastructureBaseline],
    ) -> InfrastructureBaseline:
        """Load and normalize technical infrastructure baseline.

        Supports raw baseline JSON, InfrastructureBaseline objects,
        or OSCAL Component-Definition documents.

        Args:
            source: File path, dictionary, or InfrastructureBaseline instance.

        Returns:
            Validated InfrastructureBaseline object.
        """
        if isinstance(source, InfrastructureBaseline):
            return source

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Infrastructure baseline file not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._parse_baseline_data(data)

        if isinstance(source, dict):
            return self._parse_baseline_data(source)

        raise TypeError(f"Unsupported baseline source type: {type(source)}")

    def _parse_baseline_data(self, data: Dict[str, Any]) -> InfrastructureBaseline:
        """Parse dictionary into InfrastructureBaseline, supporting OSCAL Component-Definitions."""
        # Case 1: Direct InfrastructureBaseline schema
        if "baseline_id" in data and "controls" in data:
            return InfrastructureBaseline.model_validate(data)

        # Case 2: NIST OSCAL Component-Definition
        if "component-definition" in data:
            comp_def = data["component-definition"]
            controls: List[TechnicalControl] = []
            components = comp_def.get("components", [])

            for comp in components:
                resource_name = comp.get("title", "unknown-resource")
                resource_type = "Resource"
                cloud_provider = "azure"
                resource_id = comp.get("uuid", "")

                for prop in comp.get("props", []):
                    if prop.get("name") == "resource-id":
                        resource_id = prop.get("value", resource_id)
                    elif prop.get("name") == "resource-type":
                        resource_type = prop.get("value", resource_type)
                    elif prop.get("name") == "cloud-provider":
                        cloud_provider = prop.get("value", cloud_provider).lower()

                # Extract implemented requirements
                for impl in comp.get("control-implementations", []):
                    source_category = impl.get("source", "").lstrip("#")
                    try:
                        cat_enum = ControlCategory(source_category)
                    except ValueError:
                        cat_enum = ControlCategory.APPLICATION_SECURITY

                    for req in impl.get("implemented-requirements", []):
                        ctrl_id = req.get("control-id", f"ctrl-{comp.get('uuid')}")
                        desc = req.get("description", "")
                        status = ComplianceStatus.UNKNOWN

                        for p in req.get("props", []):
                            if p.get("name") == "compliance-status":
                                val = p.get("value", "").lower()
                                if val == "compliant":
                                    status = ComplianceStatus.COMPLIANT
                                elif val == "partial":
                                    status = ComplianceStatus.PARTIAL
                                elif val == "non_compliant":
                                    status = ComplianceStatus.NON_COMPLIANT

                        current_state: Dict[str, Any] = {}
                        for stmt in req.get("statements", []):
                            stmt_desc = stmt.get("description", "")
                            if stmt_desc.startswith("Current state:"):
                                raw_json = stmt_desc.replace("Current state:", "").strip()
                                try:
                                    current_state = json.loads(raw_json)
                                except Exception:
                                    current_state = {"raw_description": stmt_desc}

                        controls.append(
                            TechnicalControl(
                                control_id=ctrl_id,
                                control_category=cat_enum,
                                cloud_provider=cloud_provider,  # type: ignore[arg-type]
                                resource_type=resource_type,
                                resource_id=resource_id,
                                resource_name=resource_name,
                                control_description=desc,
                                current_state=current_state,
                                compliance_status=status,
                            )
                        )

            return InfrastructureBaseline(
                baseline_id=comp_def.get("uuid", "oscal-component-baseline"),
                cloud_provider="azure",  # type: ignore[arg-type]
                total_resources_scanned=len(components),
                controls=controls,
                collection_metadata={"source": "oscal_component_definition"},
            )

        raise ValueError(
            "Provided data is neither a valid InfrastructureBaseline "
            "nor an OSCAL Component-Definition."
        )

    def evaluate(
        self,
        catalog_source: Union[str, Path, Dict[str, Any], List[RegulatoryArticle]],
        baseline_source: Union[str, Path, Dict[str, Any], InfrastructureBaseline],
        regulation_filter: Optional[str] = None,
    ) -> GapAnalysisReport:
        """Execute automated gap analysis between regulatory catalog and baseline.

        Args:
            catalog_source: Catalog path, dictionary, or article models.
            baseline_source: Baseline path, dictionary, or InfrastructureBaseline.
            regulation_filter: Optional filter to restrict evaluation (e.g. 'GDPR').

        Returns:
            Comprehensive GapAnalysisReport.
        """
        raw_controls = self.load_catalog(catalog_source)
        baseline = self.load_baseline(baseline_source)

        evaluations: List[ControlEvaluation] = []
        all_gaps: List[ComplianceGap] = []
        gap_counter = 1

        for raw_ctrl in raw_controls:
            ctrl_id = raw_ctrl.get("id", "")
            title = raw_ctrl.get("title", ctrl_id)

            # Extract properties
            props = {
                str(p.get("name")): p.get("value")
                for p in raw_ctrl.get("props", [])
                if isinstance(p, dict)
            }
            regulation = str(props.get("regulation") or "REGULATION")
            legal_ref = str(props.get("legal_reference") or "")
            friction_level = str(props.get("friction_level") or "Low")
            raw_friction_score = props.get("friction_score")
            try:
                friction_score = (
                    float(raw_friction_score) if raw_friction_score is not None else 0.0
                )
            except (ValueError, TypeError):
                friction_score = 0.0

            hitl_recommended = (
                str(props.get("hitl_recommended", "")).lower() == "true"
                or friction_level.lower() == "high"
                or friction_score >= 7.0
            )

            # Apply regulation filter if requested
            if regulation_filter and regulation.upper() != regulation_filter.upper():
                continue

            # Extract full text context for semantic fallback matching
            text_context = self._extract_prose_context(raw_ctrl)

            # Resolve mapped technical categories
            category_mappings = self.mapping_matrix.resolve_categories(ctrl_id, text_context)

            # If no categories are mapped, mark as UNMAPPED
            if not category_mappings:
                evaluations.append(
                    ControlEvaluation(
                        regulatory_control_id=ctrl_id,
                        regulation=regulation,
                        title=title,
                        legal_reference=legal_ref,
                        friction_level=friction_level,
                        friction_score=friction_score,
                        hitl_recommended=hitl_recommended,
                        status=RegulationComplianceStatus.UNMAPPED,
                        compliance_score=0.0,
                        confidence_score=0.0,
                        mapped_categories=[],
                        remediation_steps=[
                            "Define technical mapping rules in mapping matrix for "
                            f"regulatory control '{ctrl_id}'."
                        ],
                        hitl_guidance=(
                            ["Perform qualitative audit assessment; no technical telemetry mapped."]
                            if hitl_recommended
                            else []
                        ),
                    )
                )
                continue

            # Perform technical control evaluation across mapped categories
            ctrl_eval, new_gaps = self._evaluate_single_control(
                raw_ctrl=raw_ctrl,
                category_mappings=category_mappings,
                baseline=baseline,
                gap_counter_start=gap_counter,
                friction_score=friction_score,
                friction_level=friction_level,
                hitl_recommended=hitl_recommended,
            )

            gap_counter += len(new_gaps)
            evaluations.append(ctrl_eval)
            all_gaps.extend(new_gaps)

        # Synthesize top-level summary metrics
        summary = self._synthesize_summary(evaluations, all_gaps)

        return GapAnalysisReport(
            catalog_title="Regulatory Compliance Catalog",
            baseline_id=baseline.baseline_id,
            cloud_provider=baseline.cloud_provider.value,
            summary=summary,
            evaluations=evaluations,
            all_gaps=all_gaps,
            metadata={
                "total_technical_controls_available": len(baseline.controls),
                "friction_weight_alpha": self.friction_weight_alpha,
            },
        )

    def _extract_prose_context(self, raw_ctrl: Dict[str, Any]) -> str:
        """Extract all prose text from control statement and parts."""
        parts_text: List[str] = [raw_ctrl.get("title", "")]
        for part in raw_ctrl.get("parts", []):
            if "prose" in part:
                parts_text.append(part["prose"])
            for subpart in part.get("parts", []):
                if "prose" in subpart:
                    parts_text.append(subpart["prose"])
        return " ".join(parts_text)

    def _evaluate_single_control(
        self,
        raw_ctrl: Dict[str, Any],
        category_mappings: List[CategoryMapping],
        baseline: InfrastructureBaseline,
        gap_counter_start: int,
        friction_score: float,
        friction_level: str,
        hitl_recommended: bool,
    ) -> Tuple[ControlEvaluation, List[ComplianceGap]]:
        """Evaluate a single regulatory control against matching baseline technical controls."""
        ctrl_id = raw_ctrl.get("id", "")
        title = raw_ctrl.get("title", ctrl_id)
        props = {
            str(p.get("name")): p.get("value")
            for p in raw_ctrl.get("props", [])
            if isinstance(p, dict)
        }
        regulation = str(props.get("regulation") or "REGULATION")
        legal_ref = str(props.get("legal_reference") or "")

        mapped_categories = [m.category for m in category_mappings]
        total_mapped_tech_controls = 0
        passed_count = 0
        failed_count = 0
        partial_count = 0

        category_scores: List[float] = []
        category_weights: List[float] = []
        gaps: List[ComplianceGap] = []
        remediation_steps: List[str] = []
        hitl_guidance: List[str] = []

        gap_idx = gap_counter_start

        # Iterate over each mapped technical category
        for cat_map in category_mappings:
            matching_controls = baseline.get_controls_by_category(cat_map.category)
            category_weights.append(cat_map.weight)

            if not matching_controls:
                # Evidence gap: Category is required by regulation, but not observed
                category_scores.append(0.0)
                if cat_map.is_mandatory:
                    gap_id = f"GAP-{regulation}-{gap_idx:03d}"
                    gap_idx += 1
                    cat_name = cat_map.category.value.replace("_", " ").title()
                    gaps.append(
                        ComplianceGap(
                            gap_id=gap_id,
                            regulatory_control_id=ctrl_id,
                            regulation=regulation,
                            severity=GapSeverity.HIGH,
                            title=f"Missing Evidence for {cat_name}",
                            description=(
                                f"Regulatory control requires {cat_map.category.value}, but no "
                                f"telemetry was collected. {cat_map.rationale}"
                            ),
                            remediation_guidance=(
                                f"Deploy and configure resources in '{cat_map.category.value}', "
                                "or extend cloud collectors to ingest this telemetry."
                            ),
                            hitl_action=(
                                "Verify with security engineering if this control category "
                                "is managed outside cloud automation."
                            ),
                        )
                    )
                continue

            total_mapped_tech_controls += len(matching_controls)
            cat_points = 0.0

            for tc in matching_controls:
                if tc.compliance_status == ComplianceStatus.COMPLIANT:
                    passed_count += 1
                    cat_points += 1.0
                elif tc.compliance_status == ComplianceStatus.PARTIAL:
                    partial_count += 1
                    cat_points += 0.5
                    gap, remedy = self._create_gap_from_control(
                        tc, ctrl_id, regulation, gap_idx, is_partial=True
                    )
                    gap_idx += 1
                    gaps.append(gap)
                    if remedy and remedy not in remediation_steps:
                        remediation_steps.append(remedy)
                elif tc.compliance_status in (
                    ComplianceStatus.NON_COMPLIANT,
                    ComplianceStatus.UNKNOWN,
                ):
                    failed_count += 1
                    gap, remedy = self._create_gap_from_control(
                        tc, ctrl_id, regulation, gap_idx, is_partial=False
                    )
                    gap_idx += 1
                    gaps.append(gap)
                    if remedy and remedy not in remediation_steps:
                        remediation_steps.append(remedy)

            # Category score normalized between 0.0 and 1.0
            category_scores.append(cat_points / max(1, len(matching_controls)))

        # Weighted compliance score (0.0 to 100.0)
        total_weight = sum(category_weights) if category_weights else 1.0
        weighted_sum = sum(s * w for s, w in zip(category_scores, category_weights))
        compliance_score = round((weighted_sum / total_weight) * 100.0, 2)

        # Confidence Score Formulation
        confidence_breakdown = self._calculate_confidence(
            category_mappings=category_mappings,
            baseline=baseline,
            friction_score=friction_score,
            total_controls=total_mapped_tech_controls,
            partial_count=partial_count,
            failed_count=failed_count,
        )

        # Status Assessment
        if compliance_score >= 99.9 and failed_count == 0 and partial_count == 0:
            status = RegulationComplianceStatus.COMPLIANT
        elif compliance_score >= 50.0 and failed_count == 0:
            status = RegulationComplianceStatus.PARTIALLY_COMPLIANT
        elif compliance_score > 0.0:
            status = (
                RegulationComplianceStatus.PARTIALLY_COMPLIANT
                if failed_count <= 1
                else RegulationComplianceStatus.NON_COMPLIANT
            )
        else:
            status = RegulationComplianceStatus.NON_COMPLIANT

        # Build Human-in-the-Loop guidance if legally ambiguous
        if hitl_recommended:
            f_score_str = f"{friction_score:.1f}/10.0"
            hitl_guidance.append(
                f"Statutory text for '{ctrl_id}' contains legal friction "
                f"(Score: {f_score_str}, Level: {friction_level})."
            )
            hitl_guidance.append(
                "Automated check verifies technical baseline, but qualitative 'state of the art' "
                "review must be signed off by a qualified Data Protection Officer (DPO) "
                "or Lead Architect."
            )
            hitl_guidance.append(
                "Document technical safeguards within the formal enterprise Information "
                "Security Management System (ISMS) risk register."
            )

        evaluation = ControlEvaluation(
            regulatory_control_id=ctrl_id,
            regulation=regulation,
            title=title,
            legal_reference=legal_ref,
            friction_level=friction_level,
            friction_score=friction_score,
            hitl_recommended=hitl_recommended,
            status=status,
            compliance_score=compliance_score,
            confidence_score=confidence_breakdown.final_score,
            confidence_breakdown=confidence_breakdown,
            mapped_categories=mapped_categories,
            total_mapped_controls=total_mapped_tech_controls,
            passed_controls=passed_count,
            failed_controls=failed_count,
            partial_controls=partial_count,
            gaps=gaps,
            remediation_steps=remediation_steps,
            hitl_guidance=hitl_guidance,
        )

        return evaluation, gaps

    def _calculate_confidence(
        self,
        category_mappings: List[CategoryMapping],
        baseline: InfrastructureBaseline,
        friction_score: float,
        total_controls: int,
        partial_count: int,
        failed_count: int,
    ) -> ConfidenceBreakdown:
        """Calculate multi-dimensional confidence score.

        Formula:
            Evidence_Coverage = (Observed_Categories / Expected_Categories)
            Friction_Penalty = (Friction_Score / 10.0) * alpha
            Consistency = 1.0 - (0.2 * Partial_Ratio + 0.1 * Failed_Ratio)
            Final_Confidence = Evidence_Coverage * (1.0 - Friction_Penalty) * Consistency
        """
        expected_cats = len(category_mappings)
        observed_cats = 0
        for m in category_mappings:
            if len(baseline.get_controls_by_category(m.category)) > 0:
                observed_cats += 1

        evidence_coverage = round(observed_cats / max(1, expected_cats), 3)

        # Legal friction discount
        normalized_friction = min(10.0, max(0.0, friction_score)) / 10.0
        friction_penalty = round(normalized_friction * self.friction_weight_alpha, 3)

        # Status consistency factor
        if total_controls > 0:
            partial_ratio = partial_count / total_controls
            failed_ratio = failed_count / total_controls
            consistency = max(0.5, 1.0 - (0.25 * partial_ratio + 0.15 * failed_ratio))
        else:
            consistency = 0.5
        consistency = round(consistency, 3)

        raw_final = evidence_coverage * (1.0 - friction_penalty) * consistency
        final_score = round(max(0.0, min(1.0, raw_final)), 3)

        return ConfidenceBreakdown(
            evidence_coverage=evidence_coverage,
            friction_penalty=friction_penalty,
            status_consistency=consistency,
            hitl_adjustment=0.0,
            final_score=final_score,
        )

    def _create_gap_from_control(
        self,
        tc: TechnicalControl,
        regulatory_control_id: str,
        regulation: str,
        gap_idx: int,
        is_partial: bool,
    ) -> Tuple[ComplianceGap, str]:
        """Synthesize a concrete ComplianceGap and remediation advice from a control."""
        gap_id = f"GAP-{regulation}-{gap_idx:03d}"
        res_name = tc.resource_name or tc.resource_id.split("/")[-1]

        # Determine severity based on category and observed state
        if tc.control_category == ControlCategory.NETWORK:
            severity = (
                GapSeverity.CRITICAL if "0.0.0.0/0" in str(tc.current_state) else GapSeverity.HIGH
            )
            title = f"Insecure Network Security Rule on '{res_name}'"
            description = (
                f"Network security group '{res_name}' permits overly permissive ingress/egress "
                f"rules, violating network boundary isolation requirements under {regulation}."
            )
            remediation = (
                f"az network nsg rule update --resource-group <rg> --nsg-name {res_name} "
                "--name <rule-name> --access Deny --source-address-prefixes '0.0.0.0/0'"
            )
        elif tc.control_category == ControlCategory.ENCRYPTION:
            severity = GapSeverity.HIGH if not is_partial else GapSeverity.MEDIUM
            title = f"Encryption Deficiency on '{res_name}'"
            description = (
                f"Resource '{res_name}' ({tc.resource_type}) does not enforce required "
                "cryptographic protections (HTTPS-only or customer-managed key encryption at rest)."
            )
            remediation = (
                f"az storage account update --name {res_name} --https-only true "
                "--min-tls-version TLS1_2"
            )
        elif tc.control_category == ControlCategory.BACKUP_RECOVERY:
            severity = GapSeverity.HIGH if not is_partial else GapSeverity.MEDIUM
            title = f"Redundancy / Disaster Recovery Gap on '{res_name}'"
            description = (
                f"Resource '{res_name}' uses local-only redundancy (LRS), failing cross-regional "
                f"disaster resilience under {regulation} (e.g. DORA Art. 11, NIS2 Art. 21)."
            )
            remediation = f"az storage account update --name {res_name} --sku Standard_GRS"
        elif tc.control_category == ControlCategory.IDENTITY_ACCESS:
            severity = GapSeverity.HIGH
            title = f"Managed Identity / Access Control Missing on '{res_name}'"
            description = (
                f"Compute asset '{res_name}' lacks a system-assigned managed identity, "
                "risking static credential leakage."
            )
            remediation = f"az vm identity assign --name {res_name} --resource-group <rg>"
        else:
            severity = GapSeverity.MEDIUM if is_partial else GapSeverity.HIGH
            title = f"Technical Baseline Deviation on '{res_name}'"
            description = (
                f"Observed state diverges from compliant baseline: {tc.control_description}"
            )
            remediation = (
                f"Inspect resource '{res_name}' and align configuration with baseline policy."
            )

        expected_state: Dict[str, Any] = {"compliance_status": "compliant"}
        if "https_only" in tc.current_state:
            expected_state["https_only"] = True
        if "blob_encryption_enabled" in tc.current_state:
            expected_state["blob_encryption_enabled"] = True
        if "sku_name" in tc.current_state:
            expected_state["sku_name"] = "Standard_GRS"

        gap = ComplianceGap(
            gap_id=gap_id,
            regulatory_control_id=regulatory_control_id,
            regulation=regulation,
            technical_control_id=tc.control_id,
            resource_id=tc.resource_id,
            resource_name=res_name,
            severity=severity,
            title=title,
            description=description,
            observed_state=tc.current_state,
            expected_state=expected_state,
            remediation_guidance=remediation,
            hitl_action=(
                "Verify operational impact before applying infrastructure configuration changes."
            ),
        )

        return gap, remediation

    def _synthesize_summary(
        self,
        evaluations: List[ControlEvaluation],
        all_gaps: List[ComplianceGap],
    ) -> GapAnalysisSummary:
        """Calculate aggregate metrics for the gap analysis report."""
        total = len(evaluations)
        compliant = sum(1 for e in evaluations if e.status == RegulationComplianceStatus.COMPLIANT)
        partial = sum(
            1 for e in evaluations if e.status == RegulationComplianceStatus.PARTIALLY_COMPLIANT
        )
        non_compliant = sum(
            1 for e in evaluations if e.status == RegulationComplianceStatus.NON_COMPLIANT
        )
        unmapped = sum(1 for e in evaluations if e.status == RegulationComplianceStatus.UNMAPPED)

        overall_compliance = (
            round(sum(e.compliance_score for e in evaluations) / total, 2) if total > 0 else 0.0
        )
        overall_confidence = (
            round(sum(e.confidence_score for e in evaluations) / total, 3) if total > 0 else 0.0
        )

        gaps_by_sev: Dict[str, int] = {sev.value: 0 for sev in GapSeverity}
        for gap in all_gaps:
            gaps_by_sev[gap.severity.value] += 1

        hitl_count = sum(1 for e in evaluations if e.hitl_recommended)

        return GapAnalysisSummary(
            total_regulatory_controls=total,
            compliant_controls=compliant,
            partially_compliant_controls=partial,
            non_compliant_controls=non_compliant,
            unmapped_controls=unmapped,
            overall_compliance_percentage=overall_compliance,
            overall_confidence_score=overall_confidence,
            total_gaps=len(all_gaps),
            gaps_by_severity=gaps_by_sev,
            hitl_reviews_required=hitl_count,
        )

    def export_json(self, report: GapAnalysisReport, output_path: Union[str, Path]) -> Path:
        """Export GapAnalysisReport to a formatted JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        self.logger.info("Exported Gap Analysis Report JSON to: %s", path)
        return path

    def export_markdown(self, report: GapAnalysisReport, output_path: Union[str, Path]) -> Path:
        """Generate a rich, human-readable Markdown gap analysis report."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = [
            "# Automated Compliance Gap Analysis Report",
            "",
            "> **Generated by**: Automated Compliance Mapping Framework (Step 3 Engine)  ",
            f"> **Execution Date**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"> **Report ID**: `{report.report_id}`  ",
            f"> **Cloud Provider**: `{report.cloud_provider.upper()}`  ",
            f"> **Baseline Snapshot ID**: `{report.baseline_id}`  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Audit Posture",
            "",
            "| Metric | Result | Target Benchmark | Status |",
            "| :--- | :--- | :--- | :--- |",
        ]

        s_comp = report.summary.overall_compliance_percentage
        s_conf = report.summary.overall_confidence_score
        comp_status = "✅ COMPLIANT" if s_comp >= 95 else "⚠️ ACTION REQUIRED"
        conf_status = "✅ HIGH CONFIDENCE" if s_conf >= 0.85 else "🔍 HITL REVIEW NEEDED"
        tot_ctrls = report.summary.total_regulatory_controls
        ctrl_status = "✅" if report.summary.compliant_controls == tot_ctrls else "⚠️"
        non_comp_status = "❌ CRITICAL" if report.summary.non_compliant_controls > 0 else "✅"
        part_status = "⚠️" if report.summary.partially_compliant_controls > 0 else "✅"
        summ = report.summary

        lines.extend(
            [
                f"| **Overall Compliance Score** | **{s_comp:.1f}%** | ≥ 95.0% | {comp_status} |",
                (
                    f"| **Automated Confidence Score** | **{s_conf:.3f} / 1.000** | "
                    f"≥ 0.850 | {conf_status} |"
                ),
                f"| **Total Regulatory Controls** | {tot_ctrls} | All Active Regulations | — |",
                f"| **Compliant Controls** | {summ.compliant_controls} | 100% | {ctrl_status} |",
                (
                    "| **Partially Compliant Controls** | "
                    f"{summ.partially_compliant_controls} | 0 | {part_status} |"
                ),
                (
                    f"| **Non-Compliant Controls** | {summ.non_compliant_controls} | "
                    f"0 | {non_comp_status} |"
                ),
                f"| **Unmapped Controls** | {summ.unmapped_controls} | 0 | — |",
                f"| **Total Identified Gaps** | **{summ.total_gaps}** | 0 | — |",
                (
                    "| **Human-in-the-Loop Reviews** | "
                    f"**{summ.hitl_reviews_required}** | Mandatory | 👤 Required |"
                ),
                "",
                "### Gap Severity Breakdown",
                "",
                "| Severity Rating | Count | Remediation SLA |",
                "| :--- | :--- | :--- |",
                f"| 🔴 **Critical** | {summ.gaps_by_severity.get('critical', 0)} | 24 hours |",
                f"| 🟠 **High** | {summ.gaps_by_severity.get('high', 0)} | 7 days |",
                f"| 🟡 **Medium** | {summ.gaps_by_severity.get('medium', 0)} | 30 days |",
                f"| 🔵 **Low** | {summ.gaps_by_severity.get('low', 0)} | Next Sprint |",
                "",
                "---",
                "",
                "## 2. Regulatory Control Evaluations",
                "",
                (
                    "| Control ID | Regulation | Title | Status | "
                    "Compliance | Confidence | Friction | HITL? |"
                ),
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            ]
        )

        for ev in report.evaluations:
            status_badge = {
                RegulationComplianceStatus.COMPLIANT: "✅ Compliant",
                RegulationComplianceStatus.PARTIALLY_COMPLIANT: "⚠️ Partial",
                RegulationComplianceStatus.NON_COMPLIANT: "❌ Non-Compliant",
                RegulationComplianceStatus.UNMAPPED: "⚪ Unmapped",
            }.get(ev.status, str(ev.status))

            hitl_badge = "👤 YES" if ev.hitl_recommended else "🤖 Auto"
            f_str = f"{ev.friction_level} ({ev.friction_score:.1f})"
            lines.append(
                f"| `{ev.regulatory_control_id}` | {ev.regulation} | {ev.title} | "
                f"{status_badge} | {ev.compliance_score:.1f}% | {ev.confidence_score:.3f} | "
                f"{f_str} | {hitl_badge} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 3. Prioritized Compliance Gaps & Remediation Directives",
                "",
            ]
        )

        if not report.all_gaps:
            lines.append(
                "🎉 **No compliance gaps detected!** Infrastructure satisfies all baselines."
            )
        else:
            for gap in report.all_gaps:
                severity_icon = {
                    GapSeverity.CRITICAL: "🔴 CRITICAL",
                    GapSeverity.HIGH: "🟠 HIGH",
                    GapSeverity.MEDIUM: "🟡 MEDIUM",
                    GapSeverity.LOW: "🔵 LOW",
                    GapSeverity.INFORMATIONAL: "ℹ️ INFO",
                }.get(gap.severity, str(gap.severity))

                lines.extend(
                    [
                        f"### [{gap.gap_id}] {gap.title} ({severity_icon})",
                        "",
                        (
                            f"- **Regulatory Requirement**: `{gap.regulatory_control_id}` "
                            f"({gap.regulation})"
                        ),
                        f"- **Target Asset**: `{gap.resource_name or gap.resource_id}`",
                        f"- **Technical Control ID**: `{gap.technical_control_id or 'N/A'}`",
                        f"- **Description**: {gap.description}",
                        "",
                        "**Observed State Telemetry:**",
                        "```json",
                        json.dumps(gap.observed_state, indent=2),
                        "```",
                        "",
                        "**Technical Remediation Command:**",
                        "```bash",
                        gap.remediation_guidance,
                        "```",
                        "",
                    ]
                )
                if gap.hitl_action:
                    lines.extend(
                        [
                            f"> **Human-in-the-Loop Action**: {gap.hitl_action}",
                            "",
                        ]
                    )

        lines.extend(
            [
                "---",
                "",
                "## 4. Socio-Technical Friction & HITL Governance Review",
                "",
                "The following regulatory articles contain high socio-technical friction "
                "(e.g., 'appropriate technical measures', 'state of the art'). "
                "Automated scripts cannot provide 100% legal immunity without certified "
                "human sign-off:",
                "",
            ]
        )

        for ev in report.evaluations:
            if ev.hitl_recommended and ev.hitl_guidance:
                lines.extend(
                    [
                        f"### `{ev.regulatory_control_id}`: {ev.title}",
                        (
                            f"- **Friction Rating**: Level: `{ev.friction_level}`, "
                            f"Score: `{ev.friction_score:.1f}/10.0`"
                        ),
                        "- **Auditor Checklist**:",
                    ]
                )
                for guide in ev.hitl_guidance:
                    lines.append(f"  - [ ] {guide}")
                lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        self.logger.info("Exported Markdown Report to: %s", path)
        return path
