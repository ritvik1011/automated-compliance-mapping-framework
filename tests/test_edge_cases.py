"""Edge Case and Adversarial Input Test Suite.

This module subjects the framework to boundary conditions, extreme inputs,
multilingual unicode payloads, empty datasets, duplicate records, and malformed structures
to ensure graceful handling and zero unhandled exceptions.
"""

from pathlib import Path
from typing import Any, Dict, List
import json
import pytest

from src.parser import RegulatoryParser
from src.friction_analyzer import FrictionAnalyzer


def test_parser_handles_multilingual_and_unicode_payloads(
    parser: RegulatoryParser,
    tmp_path: Path,
) -> None:
    """WHAT: Tests legal texts containing German umlauts, Chinese characters, and modern emojis.

    WHY IT MATTERS:
    Global compliance mandates originate across jurisdictions (EU, Asia, Americas)
    and contain localized terminology, diacritics, and varied Unicode code points.
    """
    payload: List[Dict[str, Any]] = [
        {
            "article_id": "test-multilingual",
            "regulation": "GDPR",
            "title": "Datenschutz & Sicherheit 🛡️ — Sicherheitsmaßnahmen",
            "legal_text": (
                "Verordnung (EU) 2016/679 (DSGVO): Die Verarbeitung personenbezogener "
                "Daten muss angemessen sein. 网络安全与数据保护法规 — 安全要求。"
            ),
            "applicability": ["Verantwortlicher", "Auftragsverarbeiter", "数据控制者"],
        }
    ]

    input_file = tmp_path / "unicode_input.json"
    input_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    articles = parser.parse(str(input_file))

    assert len(articles) == 1
    assert "Sicherheitsmaßnahmen" in articles[0].title
    assert "🛡️" in articles[0].title
    assert "数据保护" in articles[0].legal_text
    assert "数据控制者" in articles[0].applicability


def test_parser_handles_empty_json_array(
    parser: RegulatoryParser,
    tmp_path: Path,
) -> None:
    """WHAT: Ingesting an empty JSON array '[]' returns an empty list without crashing.

    WHY IT MATTERS:
    Feed queries or filters that return zero results should cleanly yield an empty
    collection rather than raising an unhandled IndexError or ValueError.
    """
    empty_file = tmp_path / "empty_array.json"
    empty_file.write_text("[]", encoding="utf-8")

    articles = parser.parse(str(empty_file))
    assert articles == []


def test_parser_handles_duplicate_article_identifiers(
    parser: RegulatoryParser,
    tmp_path: Path,
) -> None:
    """WHAT: Verifies that duplicate article IDs in input files are deduplicated cleanly.

    WHY IT MATTERS:
    Upstream legal corpora may mistakenly contain duplicated sections. Passing duplicate
    control IDs into OSCAL creates invalid catalogs with colliding keys.
    """
    duplicate_payload: List[Dict[str, Any]] = [
        {
            "article_id": "collision-id",
            "regulation": "GDPR",
            "title": "Primary Entry",
            "legal_text": "Primary legal requirement.",
        },
        {
            "article_id": "collision-id",
            "regulation": "GDPR",
            "title": "Duplicate Entry",
            "legal_text": "Duplicate legal requirement.",
        },
    ]

    input_file = tmp_path / "duplicates.json"
    input_file.write_text(json.dumps(duplicate_payload), encoding="utf-8")

    articles = parser.parse(str(input_file))
    ids = [a.article_id for a in articles]

    assert len(ids) == len(set(ids)), "Article IDs must be unique after parsing."
    assert len(articles) == 1


def test_friction_analyzer_handles_empty_string(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Tests analyzing an empty string ("") does not raise exceptions.

    WHY IT MATTERS:
    Regulatory articles with missing or whitespace-only legal text must default safely
    to LOW friction rather than throwing regex errors.
    """
    result = analyzer.analyze("")

    assert result["friction_level"] == "LOW"
    assert len(result["ambiguous_phrases"]) == 0


def test_friction_analyzer_handles_extremely_long_legal_text(
    analyzer: FrictionAnalyzer,
) -> None:
    """WHAT: Tests friction analysis over massive legal text blocks (60,000+ characters).

    WHY IT MATTERS:
    Certain comprehensive omnibus regulations (e.g., NIS2 Annexes or full DORA Chapters)
    contain tens of thousands of words. Analysis must complete rapidly without timeout or ReDoS.
    """
    # 5,000 repetitions of an ambiguous phrase (~60,000 characters)
    massive_text = "The entity shall implement appropriate security. " * 1200

    result = analyzer.analyze(massive_text)

    assert result["friction_level"] == "HIGH"
    assert "appropriate" in result["ambiguous_phrases"]


@pytest.mark.parametrize(
    "invalid_input",
    [
        "Not a JSON string at all",
        '{"unclosed": "brace"',
        "12345",
    ],
)
def test_parser_rejects_malformed_json_inputs(
    parser: RegulatoryParser,
    invalid_input: str,
    tmp_path: Path,
) -> None:
    """WHAT: Ensures malformed or non-dict/list JSON inputs raise ValueError.

    WHY IT MATTERS:
    Defends the pipeline against corrupted data transfers or non-JSON payloads.
    """
    bad_file = tmp_path / "malformed.txt"
    bad_file.write_text(invalid_input, encoding="utf-8")

    with pytest.raises(ValueError):
        parser.parse(str(bad_file))
