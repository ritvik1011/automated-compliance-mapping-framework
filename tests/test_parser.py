"""Unit tests for RegulatoryParser, FrictionAnalyzer, and OSCALGenerator."""

import json
from pathlib import Path
import pytest

from src.parser import RegulatoryArticle, RegulatoryParser
from src.friction_analyzer import FrictionAnalyzer
from src.oscal_generator import OSCALGenerator


@pytest.fixture
def sample_data_path() -> Path:
    """Returns the path to the sample input file."""
    return Path(__file__).resolve().parent.parent / "data" / "sample_input.json"


@pytest.fixture
def parser() -> RegulatoryParser:
    """Returns a default RegulatoryParser instance."""
    return RegulatoryParser()


@pytest.fixture
def analyzer() -> FrictionAnalyzer:
    """Returns a FrictionAnalyzer instance."""
    return FrictionAnalyzer()


@pytest.fixture
def oscal_generator() -> OSCALGenerator:
    """Returns an OSCALGenerator instance."""
    return OSCALGenerator()


def test_parser_load_sample_input(sample_data_path: Path, parser: RegulatoryParser):
    """Validates that the parser successfully ingests and validates the sample input."""
    assert sample_data_path.exists(), f"Sample data not found at {sample_data_path}"

    articles = parser.load_from_file(sample_data_path)
    assert len(articles) >= 4, f"Expected at least 4 articles, got {len(articles)}"

    # Check for presence of GDPR, DORA, and NIS2
    regulations = {a.regulation for a in articles}
    assert "GDPR" in regulations
    assert "DORA" in regulations
    assert "NIS2" in regulations

    # Validate model fields on GDPR Art 32
    gdpr_32 = next((a for a in articles if "art-32" in a.article_id), None)
    assert gdpr_32 is not None
    assert gdpr_32.title == "Security of processing"
    assert "state of the art" in gdpr_32.legal_text
    assert len(gdpr_32.sub_clauses) == 4
    assert "Data Controllers" in gdpr_32.applicability


def test_parser_edge_cases_and_normalization(parser: RegulatoryParser):
    """Validates ID sanitization, string applicability parsing, and malformed input handling."""
    # Test valid parsing with comma-separated string applicability
    raw_entry = {
        "article_id": "TEST Art. 12/A",
        "regulation": "dora_regulation",
        "title": "Test Title",
        "legal_reference": "Ref 123",
        "legal_text": "Sample text",
        "applicability": "Banks, Investment Firms",
    }
    article = parser.parse_article(raw_entry)
    assert article.article_id == "test-art-12-a"
    assert article.regulation == "DORA"
    assert article.applicability == ["Banks", "Investment Firms"]

    # Test error handling when non-fatal
    bad_data = [raw_entry, {"malformed": "missing required fields"}, "not-a-dict"]
    articles = parser.parse_raw_data(bad_data)
    assert len(articles) == 1
    assert articles[0].article_id == "test-art-12-a"


def test_friction_analyzer_high_friction_detection(analyzer: FrictionAnalyzer):
    """Validates that articles with high legal ambiguity are classified as High friction."""
    article = RegulatoryArticle(
        article_id="gdpr-art-32",
        regulation="GDPR",
        title="Security of processing",
        legal_reference="GDPR Art 32",
        legal_text=(
            "Taking into account the state of the art, the costs of implementation "
            "and the nature, scope, context and purposes of processing, the controller "
            "shall implement appropriate technical and organisational measures."
        ),
        applicability=["Data Controllers"],
    )

    assessment = analyzer.analyze_article(article)
    assert assessment.friction_level == "High"
    assert assessment.friction_score >= 5.0
    assert "state of the art" in assessment.detected_triggers
    assert "appropriate" in assessment.detected_triggers
    assert "costs of implementation" in assessment.detected_triggers
    assert len(assessment.hitl_validation_steps) > 0
    assert "Binary" in assessment.automatable_status or "Qualitative" in assessment.automatable_status


def test_friction_analyzer_low_friction_detection(analyzer: FrictionAnalyzer):
    """Validates that articles with explicit, deterministic deadlines score as Low friction."""
    article = RegulatoryArticle(
        article_id="dora-art-19",
        regulation="DORA",
        title="Incident Notification Deadlines",
        legal_reference="DORA Art 19",
        legal_text=(
            "Financial entities shall submit to the competent authority an initial notification "
            "no later than 4 hours from classification and not later than 24 hours, an intermediate "
            "report within 72 hours, and a final report within 1 month."
        ),
        applicability=["Financial Entities"],
    )

    assessment = analyzer.analyze_article(article)
    assert assessment.friction_level == "Low"
    assert assessment.friction_score < 2.0
    assert "Deterministic" in assessment.automatable_status


def test_oscal_catalog_generation(
    sample_data_path: Path,
    parser: RegulatoryParser,
    analyzer: FrictionAnalyzer,
    oscal_generator: OSCALGenerator,
):
    """Validates that generated OSCAL catalogs strictly conform to NIST OSCAL JSON schema rules."""
    articles = parser.load_from_file(sample_data_path)
    report = analyzer.analyze_articles(articles, attach_to_articles=True)

    catalog = oscal_generator.generate_catalog(articles)

    assert "catalog" in catalog
    cat_obj = catalog["catalog"]
    assert "uuid" in cat_obj
    assert "metadata" in cat_obj
    assert cat_obj["metadata"]["oscal-version"] == "1.1.1"
    assert "controls" in cat_obj
    assert len(cat_obj["controls"]) == len(articles)

    # Check structure of first control
    ctrl = cat_obj["controls"][0]
    assert "id" in ctrl
    assert "title" in ctrl
    assert "props" in ctrl
    assert "parts" in ctrl

    prop_names = {p["name"] for p in ctrl["props"]}
    assert "regulation" in prop_names
    assert "friction_level" in prop_names
    assert "friction_score" in prop_names

    part_names = {p["name"] for p in ctrl["parts"]}
    assert "statement" in part_names
    assert "guidance" in part_names
