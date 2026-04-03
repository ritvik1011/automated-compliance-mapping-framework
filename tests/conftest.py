"""Shared Pytest Fixtures for Automated Compliance Mapping Framework.

This module provides reusable test fixtures across unit, integration,
edge case, and schema validation test suites. Fixtures act as pre-configured
test objects and standard inputs to keep test cases clean, independent,
and DRY (Don't Repeat Yourself).
"""

from pathlib import Path
from typing import Any, Dict
import pytest

from src.parser import RegulatoryArticle, RegulatoryParser, SubClause
from src.friction_analyzer import FrictionAnalyzer
from src.oscal_generator import OSCALGenerator


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns the absolute Path to the project root directory.

    WHY THIS MATTERS:
    Ensures file path lookups (like data/ or schemas/) are always stable
    regardless of which directory pytest was launched from.
    """
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_data_path(project_root: Path) -> Path:
    """Returns the path to the canonical sample input file containing GDPR/DORA/NIS2 articles."""
    return project_root / "data" / "sample_input.json"


@pytest.fixture(scope="session")
def oscal_schema_path(project_root: Path) -> Path:
    """Returns the path to the official NIST OSCAL Control Catalog JSON Schema."""
    return project_root / "oscal_catalog_schema.json"


@pytest.fixture
def parser() -> RegulatoryParser:
    """Provides a fresh instance of the RegulatoryParser."""
    return RegulatoryParser(fail_on_error=True)


@pytest.fixture
def analyzer() -> FrictionAnalyzer:
    """Provides a fresh instance of the FrictionAnalyzer heuristic engine."""
    return FrictionAnalyzer()


@pytest.fixture
def generator() -> OSCALGenerator:
    """Provides a fresh instance of the OSCALGenerator catalog builder."""
    return OSCALGenerator()


@pytest.fixture
def sample_gdpr_article() -> Dict[str, Any]:
    """Provides raw dictionary data for GDPR Article 32."""
    return {
        "article_id": "gdpr-art32",
        "regulation": "GDPR",
        "title": "Security of processing",
        "legal_reference": "Regulation (EU) 2016/679, Article 32(1)",
        "legal_text": (
            "Taking into account the state of the art, the costs of implementation "
            "and the nature, scope, context and purposes of processing as well as the risk, "
            "the controller and the processor shall implement appropriate technical and "
            "organisational measures to ensure a level of security appropriate to the risk."
        ),
        "applicability": ["Data Controllers", "Data Processors"],
        "sub_clauses": [
            {
                "clause_id": "1(a)",
                "title": "Encryption",
                "text": "The pseudonymisation and encryption of personal data.",
            }
        ],
    }


@pytest.fixture
def sample_dora_article() -> Dict[str, Any]:
    """Provides raw dictionary data for DORA Article 6."""
    return {
        "article_id": "dora-art-6",
        "regulation": "DORA",
        "title": "ICT risk management framework",
        "legal_reference": "Regulation (EU) 2022/2554, Article 6(1)",
        "legal_text": (
            "Financial entities shall have in place a sound, comprehensive and well-documented "
            "ICT risk management framework as part of their overall risk management system."
        ),
        "applicability": ["Financial Entities"],
    }


@pytest.fixture
def sample_nis2_article() -> Dict[str, Any]:
    """Provides raw dictionary data for NIS2 Article 21."""
    return {
        "article_id": "nis2-art-21",
        "regulation": "NIS2",
        "title": "Cybersecurity risk-management measures",
        "legal_reference": "Directive (EU) 2022/2555, Article 21(1)",
        "legal_text": (
            "Essential and important entities shall take appropriate and proportionate "
            "technical, operational and organisational measures to manage the risks posed "
            "to the security of network and information systems."
        ),
        "applicability": ["Essential Entities", "Important Entities"],
    }


@pytest.fixture
def sample_article_model() -> RegulatoryArticle:
    """Provides a fully instantiated Pydantic RegulatoryArticle model."""
    return RegulatoryArticle(
        article_id="gdpr-art-32",
        regulation="GDPR",
        title="Security of processing",
        legal_reference="Regulation (EU) 2016/679, Article 32",
        legal_text=(
            "Taking into account the state of the art, the controller shall implement "
            "appropriate technical and organisational measures."
        ),
        applicability=["Data Controllers", "Data Processors"],
        sub_clauses=[
            SubClause(
                clause_id="1(a)",
                title="Encryption",
                text="The pseudonymisation and encryption of personal data.",
            )
        ],
    )
