"""Unit Test Suite for RegulatoryParser and RegulatoryArticle Models.

This module validates that heterogeneous legal texts (GDPR, DORA, NIS2) are
reliably ingested, parsed, sanitized, and normalized into strongly-typed Pydantic
domain models required by Policy-as-Code pipelines.
"""

from pathlib import Path
from typing import Any, Dict, List
import json
import pytest
from pydantic import ValidationError

from src.parser import RegulatoryArticle, RegulatoryParser


def test_parser_reads_valid_gdpr_article(
    parser: RegulatoryParser,
    sample_gdpr_article: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """WHAT: Validates that a standard GDPR article dictionary is correctly parsed from JSON.

    WHY IT MATTERS:
    This is the fundamental happy-path entry point. If the parser cannot ingest a baseline
    valid regulatory provision, all downstream Policy-as-Code mappings fail immediately.
    """
    input_file = tmp_path / "gdpr_input.json"
    input_file.write_text(json.dumps([sample_gdpr_article]), encoding="utf-8")

    articles = parser.parse(str(input_file))

    assert len(articles) == 1, "Parser must return exactly one article."
    assert articles[0].article_id == "gdpr-art32"
    assert articles[0].regulation == "GDPR"
    assert "Data Controllers" in articles[0].applicability
    assert len(articles[0].sub_clauses) == 1
    assert articles[0].sub_clauses[0].clause_id == "1(a)"


def test_parser_handles_multiple_regulations(
    parser: RegulatoryParser,
    sample_gdpr_article: Dict[str, Any],
    sample_dora_article: Dict[str, Any],
    sample_nis2_article: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """WHAT: Ensures the parser can process a heterogeneous file containing GDPR, DORA, and NIS2.

    WHY IT MATTERS:
    Real-world enterprise compliance programs must map across multiple regulatory regimes
    simultaneously without regime-specific ingest crashes.
    """
    input_file = tmp_path / "multi_framework.json"
    input_file.write_text(
        json.dumps([sample_gdpr_article, sample_dora_article, sample_nis2_article]),
        encoding="utf-8",
    )

    articles = parser.parse(str(input_file))

    assert len(articles) == 3, "All three frameworks must be ingested."
    regulations = {a.regulation for a in articles}
    assert regulations == {"GDPR", "DORA", "NIS2"}


@pytest.mark.parametrize(
    "raw_name, expected_norm",
    [
        ("gdpr", "GDPR"),
        ("GDPR_REGULATION", "GDPR"),
        ("dora", "DORA"),
        ("dora_directive", "DORA"),
        ("nis 2", "NIS2"),
        ("NIS2_DIRECTIVE", "NIS2"),
    ],
)
def test_parser_normalizes_regulation_names(
    raw_name: str,
    expected_norm: str,
) -> None:
    """WHAT: Tests regex-based normalization of regulatory regime names to canonical acronyms.

    WHY IT MATTERS:
    Downstream OSCAL profile generators require canonical names to generate consistent
    namespaces and avoid fragmentation like 'gdpr' vs 'GDPR'.
    """
    article = RegulatoryArticle(
        article_id="art-test",
        regulation=raw_name,
        title="Testing Normalization",
        legal_text="Normative legal text placeholder.",
    )
    assert article.regulation == expected_norm


@pytest.mark.parametrize(
    "raw_id, expected_clean_id",
    [
        ("GDPR Art. 32", "gdpr-art-32"),
        ("DORA/Art-6(1)", "dora-art-6-1"),
        ("  NIS2__Art_21  ", "nis2__art_21"),
        ("Article #15 @ EU", "article-15-eu"),
    ],
)
def test_parser_sanitizes_article_ids(
    raw_id: str,
    expected_clean_id: str,
) -> None:
    """WHAT: Tests sanitization of article IDs into URL-safe, OSCAL NCName-compliant identifiers.

    WHY IT MATTERS:
    NIST OSCAL control identifiers must conform to strict schema regexes (alphanumeric with
    hyphens/underscores). Punctuation or whitespace will invalidate the OSCAL catalog.
    """
    article = RegulatoryArticle(
        article_id=raw_id,
        regulation="GDPR",
        title="Sanitization Test",
        legal_text="Sample normative text.",
    )
    assert article.article_id == expected_clean_id


@pytest.mark.parametrize(
    "raw_applicability, expected_list",
    [
        (["Banks", "Insurers"], ["Banks", "Insurers"]),
        (
            "Banks, Insurers, Payment Gateways",
            ["Banks", "Insurers", "Payment Gateways"],
        ),
        ("", []),
        (None, []),
    ],
)
def test_parser_applicability_parsing(
    raw_applicability: Any,
    expected_list: List[str],
) -> None:
    """WHAT: Validates that applicability can accept lists, comma-delimited strings, or empties.

    WHY IT MATTERS:
    External GRC feeds provide applicability entities in irregular formats. The parser
    must gracefully standardize them into a structured List[str].
    """
    article = RegulatoryArticle(
        article_id="art-applicability",
        regulation="DORA",
        title="Applicability Test",
        legal_text="Legal requirement placeholder.",
        applicability=raw_applicability,
    )
    assert article.applicability == expected_list


@pytest.mark.parametrize(
    "bad_payload",
    [
        [{"title": "Missing Article ID and text"}],
        [{"article_id": "test-id"}],  # Missing legal_text and regulation
        [{"article_id": "test-id", "regulation": "GDPR"}],  # Missing legal_text
    ],
)
def test_parser_rejects_missing_required_fields(
    parser: RegulatoryParser,
    bad_payload: List[Dict[str, Any]],
    tmp_path: Path,
) -> None:
    """WHAT: Ensures that articles missing mandatory fields raise pydantic.ValidationError.

    WHY IT MATTERS:
    Failing fast on malformed data prevents corrupted regulatory records from silently
    polluting the security policy repository.
    """
    bad_file = tmp_path / "bad_data.json"
    bad_file.write_text(json.dumps(bad_payload), encoding="utf-8")

    with pytest.raises(ValidationError):
        parser.parse(str(bad_file))


def test_parser_handles_nonexistent_file(parser: RegulatoryParser) -> None:
    """WHAT: Verifies that passing a missing file path raises FileNotFoundError.

    WHY IT MATTERS:
    Clean, predictable error types allow automated pipelines to report actionable diagnostic
    messages rather than unhandled Python exceptions.
    """
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent_regulatory_file.json")


def test_parser_rejects_invalid_json_content(
    parser: RegulatoryParser,
    tmp_path: Path,
) -> None:
    """WHAT: Verifies that passing non-JSON syntactical content raises ValueError.

    WHY IT MATTERS:
    Guards the parser against truncated or corrupted files received from upstream feeds.
    """
    corrupt_file = tmp_path / "corrupted.json"
    corrupt_file.write_text("{This is not valid json!}", encoding="utf-8")

    with pytest.raises(ValueError, match="Failed to parse JSON file"):
        parser.parse(str(corrupt_file))
