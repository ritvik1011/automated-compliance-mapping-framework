"""Unit Test Suite for Socio-Technical Friction Analyzer.

This module validates the core research heuristic engine that scans regulatory legal text
for open-textured terms (e.g. 'state of the art', 'appropriate technical measures')
that obstruct binary (Pass/Fail) Policy-as-Code automation and mandate Human-in-the-Loop
(HITL) oversight.
"""

from typing import Any, Dict

from src.friction_analyzer import FrictionAnalyzer
from src.parser import RegulatoryArticle


def test_detects_high_friction_with_multiple_ambiguous_words(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Text with multiple ambiguous terms must be classified as HIGH friction.

    WHY IT MATTERS:
    When a regulation combines multiple open-textured words (e.g., 'appropriate' +
    'organisational measures'), binary boolean automation produces false assurance.
    The framework must catch compounding ambiguity.
    """
    text = (
        "The controller shall implement appropriate technical and organisational "
        "measures to ensure security."
    )
    result = analyzer.analyze(text)

    assert result["friction_level"] == "HIGH"
    assert "appropriate" in result["ambiguous_phrases"]
    assert "organisational measures" in result["ambiguous_phrases"]


def test_detects_state_of_the_art_phrase(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Specifically flags 'state of the art' as a prime ambiguity trigger.

    WHY IT MATTERS:
    'State of the art' cannot be statically pinned to a fixed cryptographic cipher in code;
    it evolves continuously, necessitating continuous telemetry or human architectural review.
    """
    text = "Taking into account the state of the art and the costs of implementation..."
    result = analyzer.analyze(text)

    assert result["friction_level"] == "HIGH"
    assert "state of the art" in result["ambiguous_phrases"]


def test_detects_low_friction_with_binary_language(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Requirements with crisp, measurable deadlines must be classified as LOW friction.

    WHY IT MATTERS:
    Provisions like 'notify within 72 hours' can be directly automated via event triggers
    and alerting logic without requiring subjective human policy interpretation.
    """
    text = "The controller shall notify the supervisory authority within 72 hours."
    result = analyzer.analyze(text)

    assert result["friction_level"] == "LOW"
    assert len(result["ambiguous_phrases"]) == 0


def test_detects_low_friction_with_numeric_requirements(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Validates that numeric operational thresholds map cleanly to LOW friction.

    WHY IT MATTERS:
    Deterministic parameters (retention days, availability percentages) are directly
    expressible as Rego/OPA boolean assertions.
    """
    text = "Maintain backups for a minimum of 90 days with 99.9% availability."
    result = analyzer.analyze(text)

    assert result["friction_level"] == "LOW"


def test_detects_medium_friction_with_mixed_language(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Verifies that text with both ambiguity and concrete deadlines receives hybrid scoring.

    WHY IT MATTERS:
    Hybrid mandates can automate the timing component while triggering an approval workflow
    for the subjective adequacy assessment.
    """
    text = "Implement adequate security measures and notify within 72 hours."
    result = analyzer.analyze(text)

    assert result["friction_level"] in ["MEDIUM", "HIGH"]
    assert "adequate" in result["ambiguous_phrases"]
    assert result["has_deterministic_markers"] is True


def test_friction_report_contains_required_fields(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Verifies that generate_report() returns a complete diagnostic dictionary.

    WHY IT MATTERS:
    Downstream compliance dashboards and OSCAL guidance generators depend on these exact
    keys to display rationale and remediation guidance to engineers.
    """
    text = "implement appropriate technical measures"
    report: Dict[str, Any] = analyzer.generate_report(text, control_id="gdpr-art-32")

    assert report["control_id"] == "gdpr-art-32"
    assert "friction_level" in report
    assert "ambiguous_phrases" in report
    assert "reason" in report
    assert "recommendation" in report
    assert len(report["recommendation"]) > 0


def test_friction_analyzer_batch_analysis(
    analyzer: FrictionAnalyzer,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Tests analyze_articles() batch method across multiple articles.

    WHY IT MATTERS:
    The CLI and reporting pipelines process batches of articles and require aggregated
    friction distributions and metadata injection into each article model.
    """
    batch = [sample_article_model]
    report = analyzer.analyze_articles(batch, attach_to_articles=True)

    assert report.total_articles == 1
    assert report.high_friction_count == 1
    assert report.friction_distribution["High"] == 1
    assert sample_article_model.friction_metadata is not None
    assert "friction_level" in sample_article_model.friction_metadata


def test_friction_analyzer_hitl_guidance_generation(
    analyzer: FrictionAnalyzer,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Validates that High friction articles receive concrete HITL validation steps.

    WHY IT MATTERS:
    The core contribution of this framework is guiding engineering teams on what human
    validation to perform when binary automation is mathematically or legally impossible.
    """
    assessment = analyzer.analyze_article(sample_article_model)

    assert assessment.friction_level == "High"
    assert len(assessment.hitl_validation_steps) > 0
    assert any(
        "Cryptographic" in step or "Risk" in step
        for step in assessment.hitl_validation_steps
    )
