"""Regulatory Text Ingestion and Standardization Module.

This module provides data models and parser implementations to ingest,
validate, and standardize regulatory texts (such as GDPR, DORA, and NIS2)
into structured representations for Policy-as-Code pipelines.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


class SubClause(BaseModel):
    """Represents an individual sub-clause, paragraph, or enumerated item within an article."""

    model_config = ConfigDict(extra="ignore")

    clause_id: str = Field(
        ...,
        description="Identifier of the sub-clause (e.g., '1', '1(a)', '2')",
    )
    text: str = Field(
        ...,
        description="The normative text of the sub-clause or item.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional title or subheading for the sub-clause.",
    )


class RegulatoryArticle(BaseModel):
    """Structured data model representing an ingested regulatory article.

    Adheres to strict schema validation for cross-framework standardization
    across GDPR, DORA, and NIS2.
    """

    model_config = ConfigDict(extra="allow")

    article_id: str = Field(
        ...,
        description="Unique identifier for the regulatory control (e.g., 'gdpr-art-32', 'dora-art-6').",
    )
    regulation: str = Field(
        ...,
        description="Source regulatory regime (e.g., 'GDPR', 'DORA', 'NIS2').",
    )
    title: str = Field(
        ...,
        description="Formal title of the regulatory article or section.",
    )
    legal_reference: str = Field(
        ...,
        description="Formal legal citation (e.g., 'Regulation (EU) 2016/679, Article 32').",
    )
    legal_text: str = Field(
        ...,
        description="Primary normative legal text of the article.",
    )
    applicability: List[str] = Field(
        default_factory=list,
        description="Target regulated entities (e.g., ['Data Controllers', 'Financial Entities']).",
    )
    sub_clauses: List[SubClause] = Field(
        default_factory=list,
        description="Optional granular sub-clauses or paragraphs.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary domain-specific metadata, jurisdiction details, or tags.",
    )
    friction_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Attached socio-technical friction analysis results.",
    )

    @field_validator("article_id")
    @classmethod
    def sanitize_article_id(cls, v: str) -> str:
        """Sanitizes article_id to ensure it conforms to OSCAL NCName-compatible format."""
        if not v or not v.strip():
            raise ValueError("article_id cannot be empty.")
        clean_id = re.sub(r"[^\w\-]", "-", v.strip().lower())
        clean_id = re.sub(r"-+", "-", clean_id).strip("-")
        return clean_id

    @field_validator("regulation")
    @classmethod
    def normalize_regulation(cls, v: str) -> str:
        """Normalizes regulation name to canonical uppercase acronym."""
        if not v or not v.strip():
            raise ValueError("regulation cannot be empty.")
        norm = v.strip().upper()
        # Canonical mappings
        if "GDPR" in norm:
            return "GDPR"
        if "DORA" in norm:
            return "DORA"
        if "NIS2" in norm or "NIS 2" in norm:
            return "NIS2"
        return norm

    @field_validator("applicability", mode="before")
    @classmethod
    def parse_applicability(cls, v: Any) -> List[str]:
        """Ensures applicability is always parsed into a list of strings."""
        if isinstance(v, str):
            # Split comma-delimited strings
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(item).strip() for item in v if str(item).strip()]
        return []


class RegulatoryParser:
    """Ingests and standardizes heterogeneous regulatory legal texts into Pydantic models."""

    def __init__(self, fail_on_error: bool = False):
        """Initializes the RegulatoryParser.

        Args:
            fail_on_error: If True, raises exceptions on invalid articles.
                           If False, logs error and skips invalid articles.
        """
        self.fail_on_error = fail_on_error
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_from_file(self, file_path: Union[str, Path]) -> List[RegulatoryArticle]:
        """Loads and parses regulatory articles from a JSON file.

        Args:
            file_path: Path to the JSON input file.

        Returns:
            List of validated RegulatoryArticle instances.

        Raises:
            FileNotFoundError: If the target file does not exist.
            ValueError: If file content is not valid JSON.
        """
        path = Path(file_path)
        if not path.is_file():
            self.logger.error("Input file not found: %s", path)
            raise FileNotFoundError(f"Regulatory input file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_content = json.load(f)
        except json.JSONDecodeError as err:
            self.logger.error("Malformed JSON in %s: %s", path, err)
            raise ValueError(f"Failed to parse JSON file {path}: {err}") from err

        return self.parse_raw_data(raw_content)

    def parse_raw_data(self, raw_data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[RegulatoryArticle]:
        """Parses in-memory raw JSON data into RegulatoryArticle models.

        Supports both a top-level list of articles and a top-level dict
        with an 'articles' or 'controls' key.

        Args:
            raw_data: Raw JSON structure.

        Returns:
            List of successfully validated RegulatoryArticle objects.
        """
        articles_data: List[Any] = []
        if isinstance(raw_data, list):
            articles_data = raw_data
        elif isinstance(raw_data, dict):
            # Accommodate wrapper formats
            if "articles" in raw_data and isinstance(raw_data["articles"], list):
                articles_data = raw_data["articles"]
            elif "controls" in raw_data and isinstance(raw_data["controls"], list):
                articles_data = raw_data["controls"]
            else:
                articles_data = [raw_data]
        else:
            self.logger.error("Invalid data format: expected list or dict, got %s", type(raw_data))
            if self.fail_on_error:
                raise ValueError("Expected raw data to be a list or dict.")
            return []

        parsed_articles: List[RegulatoryArticle] = []
        for idx, item in enumerate(articles_data):
            if not isinstance(item, dict):
                self.logger.warning("Skipping non-dictionary item at index %d: %s", idx, item)
                continue

            try:
                article = self.parse_article(item)
                parsed_articles.append(article)
            except Exception as err:
                self.logger.error("Failed to parse article at index %d: %s", idx, err)
                if self.fail_on_error:
                    raise

        self.logger.info("Successfully parsed and standardized %d regulatory articles.", len(parsed_articles))
        return parsed_articles

    def parse_article(self, article_data: Dict[str, Any]) -> RegulatoryArticle:
        """Parses and validates a single regulatory article dictionary.

        Args:
            article_data: Dictionary representing an article.

        Returns:
            Validated RegulatoryArticle.

        Raises:
            pydantic.ValidationError: If validation fails.
        """
        return RegulatoryArticle(**article_data)
