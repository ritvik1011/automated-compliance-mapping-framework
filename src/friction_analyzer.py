"""Socio-Technical Friction Analysis Engine.

This module analyzes regulatory articles to detect "socio-technical friction
points"—areas where legal ambiguity (e.g., 'appropriate technical measures',
'proportionate', 'state of the art') prevents direct 1:1 mapping to deterministic,
binary (Pass/Fail) Policy-as-Code technical controls.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from src.parser import RegulatoryArticle

logger = logging.getLogger(__name__)


class AmbiguityTrigger(BaseModel):
    """Represents a specific legal phrase or term that triggers friction."""

    model_config = ConfigDict(extra="ignore")

    phrase: str = Field(..., description="Matched ambiguous legal phrase.")
    category: str = Field(
        ...,
        description=(
            "Category of ambiguity (e.g., 'Proportionality', 'Technological Indeterminacy')."
        ),
    )
    context_excerpt: str = Field(
        ...,
        description="Sentence or clause fragment containing the ambiguous phrase.",
    )
    weight: float = Field(
        ..., description="Heuristic weight contributing to friction score."
    )


class FrictionAssessment(BaseModel):
    """Detailed socio-technical friction evaluation for a regulatory control."""

    model_config = ConfigDict(extra="allow")

    article_id: str = Field(
        ..., description="Identifier of the assessed regulatory article."
    )
    regulation: str = Field(..., description="Regulation regime (GDPR, DORA, NIS2).")
    title: str = Field(..., description="Title of the article.")
    friction_level: Literal["Low", "Medium", "High"] = Field(
        ...,
        description="Categorical friction rating reflecting automation feasibility.",
    )
    friction_score: float = Field(
        ...,
        description="Normalized numeric friction score ranging from 0.0 to 10.0.",
    )
    automatable_status: str = Field(
        ...,
        description="Feasibility assessment for Policy-as-Code automation.",
    )
    detected_triggers: List[str] = Field(
        default_factory=list,
        description="Unique triggering terms identified in the legal text.",
    )
    ambiguity_details: List[AmbiguityTrigger] = Field(
        default_factory=list,
        description="Detailed list of matched triggers with context excerpts.",
    )
    reason: str = Field(
        ...,
        description="Research-backed rationale explaining why binary automation fails.",
    )
    recommendation: str = Field(
        ...,
        description="Strategic recommendation for engineering and GRC teams.",
    )
    hitl_validation_steps: List[str] = Field(
        default_factory=list,
        description="Actionable Human-in-the-Loop (HITL) verification procedures.",
    )


class FrictionReport(BaseModel):
    """Comprehensive analysis report across a batch of regulatory articles."""

    model_config = ConfigDict(extra="allow")

    total_articles: int
    friction_distribution: Dict[str, int]
    high_friction_count: int
    medium_friction_count: int
    low_friction_count: int
    assessments: List[FrictionAssessment]
    common_ambiguities: Dict[str, int]


class FrictionAnalyzer:
    """Heuristic engine evaluating legal indeterminacy and socio-technical friction."""

    # Heuristic Trigger Rulebase: (Regex Pattern, Canonical Phrase, Category, Weight)
    TRIGGER_DEFINITIONS: List[Tuple[str, str, str, float]] = [
        # Technological & Temporal Indeterminacy (High Weight)
        (
            r"\bstate of the art\b",
            "state of the art",
            "Technological Indeterminacy",
            3.0,
        ),
        (r"\bcutting edge\b", "cutting edge", "Technological Indeterminacy", 2.5),
        (
            r"\bwithout undue delay\b",
            "without undue delay",
            "Temporal Indeterminacy",
            2.0,
        ),
        (r"\bundue delay\b", "undue delay", "Temporal Indeterminacy", 2.0),
        (r"\btimely\b", "timely", "Temporal Indeterminacy", 1.5),
        (r"\bpromptly\b", "promptly", "Temporal Indeterminacy", 1.5),
        (
            r"\bas soon as possible\b",
            "as soon as possible",
            "Temporal Indeterminacy",
            1.5,
        ),
        (r"\bregularly\b", "regularly", "Temporal Indeterminacy", 1.2),
        # Subjective Discretion & Proportionality
        (
            r"\bappropriate and proportionate\b",
            "appropriate and proportionate",
            "Proportionality & Discretion",
            3.0,
        ),
        (r"\bappropriate\b", "appropriate", "Proportionality & Discretion", 1.8),
        (r"\bproportionate\b", "proportionate", "Proportionality & Discretion", 2.0),
        (r"\breasonable\b", "reasonable", "Proportionality & Discretion", 1.8),
        (r"\badequate\b", "adequate", "Proportionality & Discretion", 1.8),
        (r"\bsuitable\b", "suitable", "Proportionality & Discretion", 1.5),
        (r"\bsufficient\b", "sufficient", "Proportionality & Discretion", 1.5),
        (r"\bduly consider\b", "duly consider", "Proportionality & Discretion", 1.5),
        (r"\bcommensurate\b", "commensurate", "Proportionality & Discretion", 1.8),
        # Contextual & Economic Balancing
        (
            r"\bcosts of implementation\b",
            "costs of implementation",
            "Economic Balancing",
            2.5,
        ),
        (
            r"\bnature, scope, context and purposes\b",
            "nature, scope, context and purposes",
            "Contextual Balancing",
            2.5,
        ),
        (
            r"\btaking into account\b",
            "taking into account",
            "Contextual Balancing",
            1.5,
        ),
        (r"\bseverity of the risk\b", "severity of the risk", "Risk Balancing", 1.8),
        (r"\boverall risk profile\b", "overall risk profile", "Risk Balancing", 1.8),
        (r"\brisk-based approach\b", "risk-based approach", "Risk Balancing", 1.5),
        (r"\bwhere feasible\b", "where feasible", "Conditional Feasibility", 2.0),
        # Socio-Organisational & Governance Factors
        (
            r"\borganisational measures\b",
            "organisational measures",
            "Socio-Organisational",
            2.0,
        ),
        (
            r"\borganizational measures\b",
            "organizational measures",
            "Socio-Organisational",
            2.0,
        ),
        (r"\bsound governance\b", "sound governance", "Socio-Organisational", 1.5),
        (r"\bcompetent staff\b", "competent staff", "Human Factors", 1.8),
        (r"\bhuman intervention\b", "human intervention", "Human Factors", 2.0),
        (r"\bawareness\b", "awareness", "Human Factors", 1.2),
        (r"\bindependent audit\b", "independent audit", "Governance Verification", 1.5),
    ]

    # Explicit Quantitative Markers that moderate subjective ambiguity
    DETERMINISTIC_MARKERS: List[str] = [
        r"\b\d+\s*(?:hours|days|business days|months|years)\b",
        r"\bannually\b",
        r"\bquarterly\b",
        r"\bnot later than \d+\b",
        r"\bwithin \d+\b",
    ]

    def __init__(self) -> None:
        """Initializes the FrictionAnalyzer and compiles regex patterns."""
        self.compiled_triggers = [
            (re.compile(pattern, re.IGNORECASE), phrase, cat, weight)
            for pattern, phrase, cat, weight in self.TRIGGER_DEFINITIONS
        ]
        self.compiled_deterministic = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.DETERMINISTIC_MARKERS
        ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyzes a text fragment for ambiguous legal language and calculates friction level.

        Args:
            text: Normative or regulatory text to analyze.

        Returns:
            Dictionary with friction_level ("HIGH", "MEDIUM", "LOW"), ambiguous_phrases,
            and details.
        """
        detected_triggers: List[str] = []
        for regex, phrase, _, _ in self.compiled_triggers:
            if regex.search(text):
                detected_triggers.append(phrase)

        unique_triggers = sorted(list(set(detected_triggers)))
        has_deterministic = any(det.search(text) for det in self.compiled_deterministic)

        if len(unique_triggers) >= 2 or "state of the art" in unique_triggers:
            friction_level = "HIGH"
        elif len(unique_triggers) == 1:
            friction_level = "MEDIUM" if has_deterministic else "HIGH"
        else:
            friction_level = "LOW"

        return {
            "friction_level": friction_level,
            "ambiguous_phrases": unique_triggers,
            "has_deterministic_markers": has_deterministic,
        }

    def generate_report(self, text: str, control_id: str = "") -> Dict[str, Any]:
        """Generates a structured friction report for a single requirement or control.

        Args:
            text: Requirement or regulatory text.
            control_id: Identifier for the control or article.

        Returns:
            Dictionary containing control_id, friction_level, ambiguous_phrases, reason,
            and recommendation.
        """
        analysis = self.analyze(text)
        article = RegulatoryArticle(
            article_id=control_id or "control-item",
            regulation="REGULATION",
            title=control_id or "Regulatory Requirement",
            legal_text=text,
        )
        assessment = self.analyze_article(article)

        return {
            "control_id": control_id,
            "friction_level": analysis["friction_level"],
            "ambiguous_phrases": analysis["ambiguous_phrases"],
            "reason": assessment.reason,
            "recommendation": assessment.recommendation,
            "friction_score": assessment.friction_score,
        }

    def analyze_article(self, article: RegulatoryArticle) -> FrictionAssessment:
        """Evaluates a single regulatory article for socio-technical friction.

        Args:
            article: Parsed regulatory article.

        Returns:
            Structured FrictionAssessment instance.
        """
        full_text = self._aggregate_article_text(article)
        sentences = self._split_into_sentences(full_text)

        detected_triggers: List[str] = []
        ambiguity_details: List[AmbiguityTrigger] = []
        raw_score = 0.0
        categories_detected: set[str] = set()

        # Scan text against ambiguity rules
        for regex, phrase, category, weight in self.compiled_triggers:
            matches = list(regex.finditer(full_text))
            if matches:
                detected_triggers.append(phrase)
                categories_detected.add(category)
                # Incremental scoring with diminishing returns for repeated terms
                count = len(matches)
                term_score = weight * (1.0 + 0.3 * (count - 1))
                raw_score += term_score

                # Extract context sentences
                for match in matches[:2]:  # Limit to 2 context excerpts per trigger
                    match_pos = match.start()
                    excerpt = self._find_surrounding_sentence(
                        sentences, full_text, match_pos
                    )
                    ambiguity_details.append(
                        AmbiguityTrigger(
                            phrase=phrase,
                            category=category,
                            context_excerpt=excerpt,
                            weight=weight,
                        )
                    )

        # Check for deterministic anchors (e.g., explicit deadlines)
        has_deterministic_markers = any(
            det.search(full_text) for det in self.compiled_deterministic
        )
        if has_deterministic_markers and raw_score > 0:
            # Concrete deadlines mitigate temporal ambiguity slightly
            raw_score = max(0.5, raw_score * 0.85)

        # Normalize score to 0.0 - 10.0 scale
        friction_score = min(10.0, round(raw_score, 1))

        # Categorize level
        friction_level, automatable_status = self._determine_friction_level(
            friction_score=friction_score,
            detected_triggers=detected_triggers,
            categories=categories_detected,
        )

        # Synthesize research-backed reasons and recommendations
        reason, recommendation, hitl_steps = self._generate_guidance(
            article=article,
            friction_level=friction_level,
            detected_triggers=detected_triggers,
            categories=categories_detected,
        )

        return FrictionAssessment(
            article_id=article.article_id,
            regulation=article.regulation,
            title=article.title,
            friction_level=friction_level,
            friction_score=friction_score,
            automatable_status=automatable_status,
            detected_triggers=sorted(list(set(detected_triggers))),
            ambiguity_details=ambiguity_details,
            reason=reason,
            recommendation=recommendation,
            hitl_validation_steps=hitl_steps,
        )

    def analyze_articles(
        self,
        articles: List[RegulatoryArticle],
        attach_to_articles: bool = True,
    ) -> FrictionReport:
        """Analyzes a batch of regulatory articles and creates a friction report.

        Args:
            articles: List of RegulatoryArticle instances.
            attach_to_articles: If True, attaches friction metadata to each article model.

        Returns:
            FrictionReport with aggregate metrics and individual assessments.
        """
        assessments: List[FrictionAssessment] = []
        counts = {"High": 0, "Medium": 0, "Low": 0}
        ambiguity_freq: Dict[str, int] = {}

        for article in articles:
            assessment = self.analyze_article(article)
            assessments.append(assessment)
            counts[assessment.friction_level] += 1

            for trigger in assessment.detected_triggers:
                ambiguity_freq[trigger] = ambiguity_freq.get(trigger, 0) + 1

            if attach_to_articles:
                article.friction_metadata = assessment.model_dump()

        report = FrictionReport(
            total_articles=len(articles),
            friction_distribution=counts,
            high_friction_count=counts["High"],
            medium_friction_count=counts["Medium"],
            low_friction_count=counts["Low"],
            assessments=assessments,
            common_ambiguities=dict(
                sorted(ambiguity_freq.items(), key=lambda item: item[1], reverse=True)
            ),
        )

        logger.info(
            "Friction Analysis Complete: Total=%d | High=%d | Medium=%d | Low=%d",
            report.total_articles,
            report.high_friction_count,
            report.medium_friction_count,
            report.low_friction_count,
        )
        return report

    def export_report_to_json(
        self,
        report: FrictionReport,
        output_path: Union[str, Path],
    ) -> Path:
        """Saves the friction report as a formatted JSON document.

        Args:
            report: Generated FrictionReport.
            output_path: Target destination file path.

        Returns:
            Path object of the saved file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
        logger.info("Friction analysis report saved to %s", path)
        return path

    # --------------------------------------------------------------------------
    # Private Helper Methods
    # --------------------------------------------------------------------------

    def _aggregate_article_text(self, article: RegulatoryArticle) -> str:
        """Combines article legal text and sub-clauses into a consolidated corpus."""
        parts = [article.legal_text]
        for sub in article.sub_clauses:
            if sub.title:
                parts.append(sub.title)
            parts.append(sub.text)
        return " ".join(parts)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Splits narrative legal text into sentences for excerpt identification."""
        clean = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", clean)
        return [s.strip() for s in sentences if s.strip()]

    def _find_surrounding_sentence(
        self, sentences: List[str], full_text: str, match_pos: int
    ) -> str:
        """Extracts the sentence containing a specific character offset."""
        current_len = 0
        for sentence in sentences:
            current_len += len(sentence) + 1
            if current_len >= match_pos:
                return sentence
        start_pos = max(0, match_pos - 40)
        end_pos = min(len(full_text), match_pos + 60)
        return full_text[start_pos:end_pos].strip()

    def _determine_friction_level(
        self,
        friction_score: float,
        detected_triggers: List[str],
        categories: set[str],
    ) -> Tuple[Literal["Low", "Medium", "High"], str]:
        """Calculates categorical friction level and Policy-as-Code automation status."""
        has_state_of_the_art = "state of the art" in detected_triggers
        has_proportionality = "Proportionality & Discretion" in categories
        has_balancing = (
            "Economic Balancing" in categories or "Contextual Balancing" in categories
        )

        # Compounding ambiguity condition
        if (
            friction_score >= 5.0
            or (has_state_of_the_art and has_proportionality)
            or (has_proportionality and has_balancing)
        ):
            return "High", "Non-Binary / Qualitative Governance Review Required"
        elif friction_score >= 2.0 or len(detected_triggers) >= 2:
            return (
                "Medium",
                "Hybrid / HITL Attestation & Quantitative Baseline Required",
            )
        else:
            return "Low", "Deterministic / Direct Policy-as-Code Assertion Feasible"

    def _generate_guidance(
        self,
        article: RegulatoryArticle,
        friction_level: Literal["Low", "Medium", "High"],
        detected_triggers: List[str],
        categories: set[str],
    ) -> Tuple[str, str, List[str]]:
        """Synthesizes academic, research-backed reasoning and HITL recommendations."""
        reason_fragments: List[str] = []
        recommendation_fragments: List[str] = []
        hitl_steps: List[str] = []

        if "state of the art" in detected_triggers:
            reason_fragments.append(
                "Mandates 'state of the art' protections without prescribing static "
                "cryptographic or architectural baselines. Hardcoding fixed parameters "
                "(e.g., TLS 1.3 or specific AES modes) into static Policy-as-Code creates "
                "rapid obsolescence and false assurance as cryptographic standards evolve."
            )
            recommendation_fragments.append(
                "Establish an automated telemetry pipeline linked to NIST/ENISA vulnerability "
                "repositories to dynamically refresh baseline benchmarks."
            )
            hitl_steps.append(
                "Quarterly Cryptographic & Architecture Review by the Principal Security Architect."
            )

        if "Proportionality & Discretion" in categories:
            reason_fragments.append(
                "Contains subjective proportionality standards ('appropriate', 'proportionate', "
                "'reasonable'). A binary boolean evaluation (Pass/Fail) cannot weigh the entity's "
                "size, operational risk profile, or threat environment against the technical "
                "burden of implementation."
            )
            recommendation_fragments.append(
                "Implement a Tiered Control Matrix where automated CI/CD checks enforce minimal "
                "hygiene, while context-dependent risk waivers are reviewed by GRC leadership."
            )
            hitl_steps.append(
                "Documented Risk Acceptance & Proportionality Rationale signed off by the "
                "CISO/Data Protection Officer (DPO)."
            )

        if "Economic Balancing" in categories or "Contextual Balancing" in categories:
            reason_fragments.append(
                "Requires balancing security controls against the 'costs of implementation' and "
                "the 'nature, scope, context and purposes of processing'. Economic feasibility "
                "and contextual business necessity are fundamentally socio-organizational "
                "judgments inaccessible to static code scanners."
            )
            hitl_steps.append(
                "Annual Cost-Benefit & Impact Assessment attesting to control proportionality."
            )

        if "Temporal Indeterminacy" in categories:
            reason_fragments.append(
                "Relies on open-ended temporal thresholds ('without undue delay', 'timely', "
                "'promptly'). While log event timestamps can measure elapsed time, "
                "determining whether a delay was 'undue' depends on forensic complexity "
                "and containment velocity."
            )
            hitl_steps.append(
                "Post-Incident Triage Review validating incident timeline logs against "
                "operational complexity records."
            )

        if "Socio-Organisational" in categories or "Human Factors" in categories:
            reason_fragments.append(
                "Enforces organizational, governance, or human factor safeguards (e.g., "
                "'organisational measures', 'awareness', 'competent staff'). "
                "Cloud infrastructure assertions cannot ascertain human training retention, "
                "segregation of duties efficacy, or governance meeting integrity."
            )
            hitl_steps.append(
                "Human-in-the-Loop verification of training completion metrics and role-based "
                "access review attestations."
            )

        # Default fallbacks if low friction
        if not reason_fragments:
            if friction_level == "Low":
                reason = (
                    "Control provisions exhibit high linguistic determinism with concrete "
                    "obligations (e.g., specific reporting deadlines, formalized procedures). "
                    "This requirement can be reliably translated into deterministic "
                    "Policy-as-Code checks (e.g., Open Policy Agent/Rego rules or Cloud "
                    "Custodian filters)."
                )
                recommendation = (
                    "Directly codify into CI/CD deployment gates and real-time infrastructure "
                    "policy enforcement."
                )
                hitl_steps = [
                    "Automated integration test validation in deployment pipelines.",
                    "Audit log ingestion of policy evaluation telemetry.",
                ]
            else:
                reason = (
                    "Contains moderate linguistic ambiguity requiring localized configuration "
                    "verification."
                )
                recommendation = (
                    "Combine automated unit verification with human reviewer sign-off."
                )
                hitl_steps = [
                    "Peer review of infrastructure compliance configurations."
                ]
        else:
            reason = " ".join(reason_fragments)
            recommendation = " ".join(recommendation_fragments)
            if not hitl_steps:
                hitl_steps = [
                    "Documented risk assessment and compensating control validation."
                ]

        return reason, recommendation, hitl_steps
