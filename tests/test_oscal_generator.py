"""Unit Test Suite for NIST OSCAL Catalog Generator.

This module validates that ingested regulatory articles and their associated
socio-technical friction metadata are mapped into standard NIST OSCAL Control
Catalog data structures (v1.1.1).
"""

from pathlib import Path
from typing import Any, Dict, List
import json

from src.oscal_generator import OSCALGenerator
from src.parser import RegulatoryArticle, SubClause


def test_oscal_output_has_catalog_root(
    generator: OSCALGenerator,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Verifies that the generated OSCAL structure has 'catalog' as its root dictionary key.

    WHY IT MATTERS:
    NIST OSCAL JSON schema strictly specifies that a Control Catalog root document
    must be keyed under 'catalog'. Any deviation causes rejection by automated GRC tools.
    """
    catalog = generator.generate([sample_article_model])

    assert "catalog" in catalog, "OSCAL output must have 'catalog' as the root element."


def test_oscal_output_has_metadata(
    generator: OSCALGenerator,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Validates that catalog metadata includes title, version, and OSCAL schema version.

    WHY IT MATTERS:
    Traceability and auditability require catalog metadata to specify timestamps,
    versioning, and target OSCAL spec versions (1.1.1).
    """
    catalog = generator.generate([sample_article_model])

    meta = catalog["catalog"].get("metadata", {})
    assert "title" in meta
    assert meta.get("oscal-version") == "1.1.1"
    assert "version" in meta
    assert "last-modified" in meta


def test_oscal_control_has_required_fields(
    generator: OSCALGenerator,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Ensures each generated OSCAL control contains mandatory keys (id, title, props, parts).

    WHY IT MATTERS:
    In OSCAL, controls define the operational security requirements. Missing any of these
    structural components creates non-conforming controls that break policy compilers.
    """
    catalog = generator.generate([sample_article_model])

    controls: List[Dict[str, Any]] = catalog["catalog"].get("controls", [])
    assert len(controls) == 1, "Catalog should contain exactly 1 control."

    control = controls[0]
    assert control["id"] == "gdpr-art-32"
    assert control["title"] == "Security of processing"
    assert isinstance(control.get("props"), list)
    assert isinstance(control.get("parts"), list)


def test_oscal_control_includes_friction_level(
    generator: OSCALGenerator,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Verifies that socio-technical friction metadata is attached as OSCAL properties.

    WHY IT MATTERS:
    Our research framework extends standard OSCAL by embedding friction annotations
    directly into machine-readable control properties for automated GRC consumption.
    """
    catalog = generator.generate([sample_article_model])

    control = catalog["catalog"]["controls"][0]
    props = control.get("props", [])

    prop_names = {p["name"] for p in props}
    assert "friction_level" in prop_names
    assert "friction_score" in prop_names
    assert "automatable_status" in prop_names

    friction_prop = next(p for p in props if p["name"] == "friction_level")
    assert friction_prop["value"] in ["Low", "Medium", "High"]


def test_oscal_sub_clauses_mapped_to_parts(
    generator: OSCALGenerator,
) -> None:
    """WHAT: Tests that article sub-clauses are structured as hierarchical parts under 'statement'.

    WHY IT MATTERS:
    Legal provisions often have structured paragraphs (e.g., Article 32(1)(a)-(d)).
    OSCAL accommodates these granular requirements through nested 'item' sub-parts.
    """
    article = RegulatoryArticle(
        article_id="dora-multi-clause",
        regulation="DORA",
        title="Testing Nested Subclauses",
        legal_text="Main introductory statement.",
        sub_clauses=[
            SubClause(clause_id="1", title="Clause 1", text="Sub-clause one text."),
            SubClause(clause_id="2", title="Clause 2", text="Sub-clause two text."),
        ],
    )

    control = generator.article_to_control(article)
    parts = control.get("parts", [])

    # Locate the primary statement part
    statement_part = next((p for p in parts if p.get("name") == "statement"), None)
    assert statement_part is not None

    nested_parts = statement_part.get("parts", [])
    assert len(nested_parts) == 2
    assert nested_parts[0]["name"] == "item"
    assert nested_parts[0]["id"] == "dora-multi-clause-item-1"


def test_oscal_regulation_specific_catalogs(
    generator: OSCALGenerator,
    sample_article_model: RegulatoryArticle,
) -> None:
    """WHAT: Tests generate_regulation_catalogs() separates articles by regulatory regime.

    WHY IT MATTERS:
    GRC teams often require isolated regulation-specific catalogs (e.g. GDPR-only vs DORA-only)
    alongside unified cross-framework views.
    """
    dora_article = RegulatoryArticle(
        article_id="dora-art-10",
        regulation="DORA",
        title="DORA Provision",
        legal_text="Financial risk control text.",
    )
    catalogs = generator.generate_regulation_catalogs([sample_article_model, dora_article])

    assert "GDPR" in catalogs
    assert "DORA" in catalogs
    assert len(catalogs["GDPR"]["catalog"]["controls"]) == 1
    assert len(catalogs["DORA"]["catalog"]["controls"]) == 1


def test_oscal_save_catalog_to_disk(
    generator: OSCALGenerator,
    sample_article_model: RegulatoryArticle,
    tmp_path: Path,
) -> None:
    """WHAT: Verifies that save_catalog_to_json() writes a valid, formatted JSON file to disk.

    WHY IT MATTERS:
    Artifact generation is the terminal goal of the pipeline; the generated file must be
    valid UTF-8 JSON ready for distribution.
    """
    catalog = generator.generate([sample_article_model])
    target_file = tmp_path / "output_catalog.json"

    saved_path = generator.save_catalog_to_json(catalog, target_file)

    assert saved_path.exists()
    with open(saved_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "catalog" in loaded
    assert "controls" in loaded["catalog"]
