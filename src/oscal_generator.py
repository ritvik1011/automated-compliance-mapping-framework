"""NIST OSCAL (Open Security Controls Assessment Language) Catalog Generator.

This module maps standardized regulatory articles and their socio-technical friction
metadata into valid NIST OSCAL Catalog JSON structures (v1.1.1).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.parser import RegulatoryArticle

logger = logging.getLogger(__name__)

# Canonical Namespaces
OSCAL_VERSION = "1.1.1"
NS_FRAMEWORK = "https://compliance-framework.eu/ns/oscal"
NS_FRICTION = "https://compliance-framework.eu/ns/socio-technical-friction"
NS_EURLEX = "https://eur-lex.europa.eu"


class OSCALGenerator:
    """Transforms parsed regulatory articles into NIST OSCAL Catalog documents."""

    def __init__(self, oscal_version: str = OSCAL_VERSION) -> None:
        """Initializes the OSCALGenerator.

        Args:
            oscal_version: Supported OSCAL schema version string.
        """
        self.oscal_version = oscal_version
        self.logger = logging.getLogger(self.__class__.__name__)

    def article_to_control(self, article: RegulatoryArticle) -> Dict[str, Any]:
        """Converts a single RegulatoryArticle into an OSCAL control object.

        Args:
            article: Parsed regulatory article with optional friction metadata.

        Returns:
            Dictionary representing an OSCAL control.
        """
        control_id = article.article_id

        # Build OSCAL Properties
        props: List[Dict[str, str]] = [
            {"name": "regulation", "value": article.regulation, "ns": NS_EURLEX},
            {
                "name": "legal_reference",
                "value": article.legal_reference,
                "ns": NS_EURLEX,
            },
            {
                "name": "applicability",
                "value": (
                    ", ".join(article.applicability)
                    if article.applicability
                    else "All In-Scope Entities"
                ),
                "ns": NS_FRAMEWORK,
            },
        ]

        # Attach friction metadata properties if available
        friction = article.friction_metadata
        if not friction:
            try:
                from src.friction_analyzer import FrictionAnalyzer

                assessment = FrictionAnalyzer().analyze_article(article)
                friction = assessment.model_dump()
            except Exception:
                friction = {}
        friction_level = friction.get("friction_level", "Unassessed")
        friction_score = str(friction.get("friction_score", 0.0))
        automatable_status = friction.get(
            "automatable_status", "Standard Automation Assessment Required"
        )
        detected_triggers = friction.get("detected_triggers", [])

        props.extend(
            [
                {"name": "friction_level", "value": friction_level, "ns": NS_FRICTION},
                {"name": "friction_score", "value": friction_score, "ns": NS_FRICTION},
                {
                    "name": "automatable_status",
                    "value": automatable_status,
                    "ns": NS_FRICTION,
                },
            ]
        )

        if detected_triggers:
            props.append(
                {
                    "name": "ambiguity_triggers",
                    "value": "; ".join(detected_triggers),
                    "ns": NS_FRICTION,
                }
            )

        # Build OSCAL Parts
        parts: List[Dict[str, Any]] = []

        # 1. Primary Normative Statement Part
        statement_part: Dict[str, Any] = {
            "id": f"{control_id}-statement",
            "name": "statement",
            "prose": article.legal_text,
        }

        # Sub-clauses as sub-parts of the statement
        if article.sub_clauses:
            sub_parts: List[Dict[str, Any]] = []
            for sub in article.sub_clauses:
                sub_id_clean = (
                    sub.clause_id.replace("(", "")
                    .replace(")", "")
                    .replace(" ", "-")
                    .lower()
                )
                sub_part: Dict[str, Any] = {
                    "id": f"{control_id}-item-{sub_id_clean}",
                    "name": "item",
                    "props": [{"name": "clause_id", "value": sub.clause_id}],
                    "prose": f"{sub.title + ': ' if sub.title else ''}{sub.text}",
                }
                sub_parts.append(sub_part)
            statement_part["parts"] = sub_parts

        parts.append(statement_part)

        # 2. Socio-Technical Friction & HITL Guidance Part
        if friction:
            reason = friction.get("reason", "No friction rationale documented.")
            recommendation = friction.get(
                "recommendation", "No specific recommendation provided."
            )
            hitl_steps = friction.get("hitl_validation_steps", [])

            guidance_prose_lines = [
                f"### Socio-Technical Friction Analysis (Rating: {friction_level})",
                f"**Automation Feasibility:** {automatable_status}",
                f"**Indeterminacy Rationale:** {reason}",
                f"**Engineering Recommendation:** {recommendation}",
            ]
            if hitl_steps:
                guidance_prose_lines.append(
                    "**Human-in-the-Loop (HITL) Validation Procedures:**"
                )
                for step in hitl_steps:
                    guidance_prose_lines.append(f"- {step}")

            guidance_part = {
                "id": f"{control_id}-socio-technical-guidance",
                "name": "guidance",
                "prose": "\n\n".join(guidance_prose_lines),
            }
            parts.append(guidance_part)

        return {
            "id": control_id,
            "class": "regulatory-requirement",
            "title": article.title,
            "props": props,
            "parts": parts,
        }

    def generate(
        self,
        articles: List[RegulatoryArticle],
        title: Optional[str] = None,
        regulation_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates an OSCAL catalog from articles (convenience alias for generate_catalog).

        Args:
            articles: List of RegulatoryArticle instances to include.
            title: Optional catalog title.
            regulation_filter: Optional regulation name to filter by.

        Returns:
            Dictionary strictly following the OSCAL Catalog schema.
        """
        return self.generate_catalog(
            articles=articles, title=title, regulation_filter=regulation_filter
        )

    def generate_catalog(
        self,
        articles: List[RegulatoryArticle],
        title: Optional[str] = None,
        regulation_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates a complete NIST OSCAL Catalog JSON structure.

        Args:
            articles: List of RegulatoryArticle instances to include.
            title: Optional catalog title.
            regulation_filter: Optional regulation name to filter by.

        Returns:
            Dictionary strictly following the OSCAL Catalog schema.
        """
        filtered_articles = articles
        if regulation_filter:
            norm_filter = regulation_filter.strip().upper()
            filtered_articles = [
                a for a in articles if a.regulation.upper() == norm_filter
            ]

        catalog_title = title or (
            f"{regulation_filter.upper()} Regulatory Catalog"
            if regulation_filter
            else "Multi-Regulation Compliance Catalog (GDPR, DORA, NIS2)"
        )

        controls = [self.article_to_control(art) for art in filtered_articles]

        catalog_uuid = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        catalog_data = {
            "catalog": {
                "uuid": catalog_uuid,
                "metadata": {
                    "title": catalog_title,
                    "last-modified": timestamp,
                    "version": "1.0.0",
                    "oscal-version": self.oscal_version,
                    "remarks": (
                        "Generated by Automated Compliance Mapping Framework (Step 1: "
                        "Ingestion & Standardization with Socio-Technical Friction Analysis)."
                    ),
                },
                "controls": controls,
            },
            "metadata": {
                "title": catalog_title,
                "last-modified": timestamp,
                "version": "1.0.0",
                "oscal-version": self.oscal_version,
            },
        }

        self.logger.info(
            "Generated OSCAL Catalog '%s' with %d controls (UUID: %s)",
            catalog_title,
            len(controls),
            catalog_uuid,
        )
        return catalog_data

    def generate_regulation_catalogs(
        self,
        articles: List[RegulatoryArticle],
    ) -> Dict[str, Dict[str, Any]]:
        """Splits articles by regulation and creates a dedicated OSCAL catalog for each.

        Args:
            articles: Ingested articles.

        Returns:
            Dictionary mapping regulation names to their respective OSCAL catalogs.
        """
        regulations = sorted(list(set(art.regulation for art in articles)))
        catalogs: Dict[str, Dict[str, Any]] = {}

        for reg in regulations:
            catalogs[reg] = self.generate_catalog(
                articles=articles,
                title=f"{reg} Standardized Regulatory Control Catalog",
                regulation_filter=reg,
            )

        return catalogs

    def save_catalog_to_json(
        self,
        catalog_data: Dict[str, Any],
        output_path: Union[str, Path],
    ) -> Path:
        """Serializes and saves the OSCAL catalog to a JSON file.

        Args:
            catalog_data: OSCAL catalog data structure.
            output_path: Target destination path.

        Returns:
            Path object of the saved catalog file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        export_payload = (
            {"catalog": catalog_data["catalog"]}
            if "catalog" in catalog_data
            else catalog_data
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_payload, f, indent=2, ensure_ascii=False)
        self.logger.info("Saved OSCAL catalog to %s", path)
        return path
