"""Regulatory-to-Technical Mapping Matrix.

This module provides the semantic cross-walk and rules engine that maps
normative legal requirements (GDPR, DORA, NIS2) to empirical technical
control categories (IAM, Data Encryption, Network Security, Backup & Recovery).

Research Context (MPI-SP):
    Bridges the semantic gap between high-level statutory obligations
    ("state of the art", "appropriate technical measures") and
    deterministic infrastructure configuration parameters.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from src.models.technical_control import ControlCategory

logger = logging.getLogger(__name__)


class CategoryMapping(BaseModel):
    """Specification of how a regulatory clause maps to a technical control category."""

    model_config = ConfigDict(extra="ignore")

    category: ControlCategory = Field(
        ...,
        description="Target technical control category.",
    )
    weight: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description=(
            "Relative importance/weight of this technical category for the legal requirement."
        ),
    )
    is_mandatory: bool = Field(
        default=True,
        description="If True, failure in this category triggers NON_COMPLIANT status.",
    )
    rationale: str = Field(
        default="",
        description="Legal-technical justification for why this category is required.",
    )


class MappingRule(BaseModel):
    """Rule defining mapping relationships for a regulatory article or sub-clause."""

    model_config = ConfigDict(extra="ignore")

    regulatory_control_id: str = Field(
        ...,
        description="Regulatory article or control ID (e.g., 'gdpr-art-32', 'dora-art-6').",
    )
    regulation: str = Field(
        ...,
        description="Source regulation regime (e.g., 'GDPR', 'DORA', 'NIS2').",
    )
    target_categories: List[CategoryMapping] = Field(
        default_factory=list,
        description="Set of technical categories mapped to this regulatory control.",
    )
    sub_clause_mappings: Dict[str, List[CategoryMapping]] = Field(
        default_factory=dict,
        description="Specific mappings per sub-clause or item ID (e.g., '1(a)' -> Encryption).",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Domain keywords used for heuristic semantic cross-referencing.",
    )


class RegulatoryMappingMatrix:
    """Central repository and resolver for regulatory-to-technical control mappings."""

    def __init__(self, custom_rules: Optional[List[MappingRule]] = None) -> None:
        """Initialize the mapping matrix with canonical rules and optional custom overrides."""
        self._rules: Dict[str, MappingRule] = {}
        self._keyword_category_map: Dict[str, ControlCategory] = {
            # Encryption & Cryptography
            "encrypt": ControlCategory.ENCRYPTION,
            "encryption": ControlCategory.ENCRYPTION,
            "cryptograph": ControlCategory.ENCRYPTION,
            "cipher": ControlCategory.ENCRYPTION,
            "pseudonym": ControlCategory.ENCRYPTION,
            "tls": ControlCategory.ENCRYPTION,
            "https": ControlCategory.ENCRYPTION,
            "at-rest": ControlCategory.ENCRYPTION,
            "in-transit": ControlCategory.ENCRYPTION,
            "key vault": ControlCategory.ENCRYPTION,
            # Identity & Access Management
            "access control": ControlCategory.IDENTITY_ACCESS,
            "authentication": ControlCategory.IDENTITY_ACCESS,
            "authorization": ControlCategory.IDENTITY_ACCESS,
            "identity": ControlCategory.IDENTITY_ACCESS,
            "mfa": ControlCategory.IDENTITY_ACCESS,
            "multi-factor": ControlCategory.IDENTITY_ACCESS,
            "credential": ControlCategory.IDENTITY_ACCESS,
            "least privilege": ControlCategory.IDENTITY_ACCESS,
            "managed identity": ControlCategory.IDENTITY_ACCESS,
            "rbac": ControlCategory.IDENTITY_ACCESS,
            # Network Security & Perimeter
            "network": ControlCategory.NETWORK,
            "firewall": ControlCategory.NETWORK,
            "nsg": ControlCategory.NETWORK,
            "security group": ControlCategory.NETWORK,
            "perimeter": ControlCategory.NETWORK,
            "segmentation": ControlCategory.NETWORK,
            "ingress": ControlCategory.NETWORK,
            "egress": ControlCategory.NETWORK,
            "port": ControlCategory.NETWORK,
            # Backup & Disaster Recovery
            "backup": ControlCategory.BACKUP_RECOVERY,
            "recovery": ControlCategory.BACKUP_RECOVERY,
            "restore": ControlCategory.BACKUP_RECOVERY,
            "redundancy": ControlCategory.BACKUP_RECOVERY,
            "resilience": ControlCategory.BACKUP_RECOVERY,
            "business continuity": ControlCategory.BACKUP_RECOVERY,
            "disaster": ControlCategory.BACKUP_RECOVERY,
            "replication": ControlCategory.BACKUP_RECOVERY,
            # Logging & Monitoring
            "logging": ControlCategory.LOGGING_MONITORING,
            "monitoring": ControlCategory.LOGGING_MONITORING,
            "audit": ControlCategory.LOGGING_MONITORING,
            "incident": ControlCategory.LOGGING_MONITORING,
            "detection": ControlCategory.LOGGING_MONITORING,
            "telemetry": ControlCategory.LOGGING_MONITORING,
        }

        # Populate baseline statutory rules
        self._load_canonical_rules()

        # Apply custom rules
        if custom_rules:
            for rule in custom_rules:
                self.register_rule(rule)

    def _load_canonical_rules(self) -> None:
        """Register canonical statutory mappings for GDPR, DORA, and NIS2."""
        # 1. GDPR Article 32: Security of processing
        self.register_rule(
            MappingRule(
                regulatory_control_id="gdpr-art-32",
                regulation="GDPR",
                target_categories=[
                    CategoryMapping(
                        category=ControlCategory.ENCRYPTION,
                        weight=1.5,
                        is_mandatory=True,
                        rationale=(
                            "GDPR Art. 32(1)(a) mandates pseudonymisation and "
                            "encryption of personal data."
                        ),
                    ),
                    CategoryMapping(
                        category=ControlCategory.IDENTITY_ACCESS,
                        weight=1.2,
                        is_mandatory=True,
                        rationale="GDPR Art. 32(1)(b) requires ongoing confidentiality.",
                    ),
                    CategoryMapping(
                        category=ControlCategory.NETWORK,
                        weight=1.0,
                        is_mandatory=False,
                        rationale="Network boundary protection ensures ongoing system security.",
                    ),
                    CategoryMapping(
                        category=ControlCategory.BACKUP_RECOVERY,
                        weight=1.2,
                        is_mandatory=True,
                        rationale=(
                            "GDPR Art. 32(1)(c) mandates ability to restore "
                            "availability and access."
                        ),
                    ),
                ],
                sub_clause_mappings={
                    "1(a)": [
                        CategoryMapping(
                            category=ControlCategory.ENCRYPTION,
                            weight=2.0,
                            is_mandatory=True,
                            rationale="Encryption at rest and in transit for personal data.",
                        )
                    ],
                    "1(b)": [
                        CategoryMapping(
                            category=ControlCategory.IDENTITY_ACCESS,
                            weight=1.5,
                            is_mandatory=True,
                            rationale="Confidentiality and integrity through identity governance.",
                        ),
                        CategoryMapping(
                            category=ControlCategory.NETWORK,
                            weight=1.0,
                            is_mandatory=False,
                            rationale="Network security controls to prevent unauthorized access.",
                        ),
                    ],
                    "1(c)": [
                        CategoryMapping(
                            category=ControlCategory.BACKUP_RECOVERY,
                            weight=2.0,
                            is_mandatory=True,
                            rationale="Timely availability and disaster recovery guarantees.",
                        )
                    ],
                    "1(d)": [
                        CategoryMapping(
                            category=ControlCategory.LOGGING_MONITORING,
                            weight=1.0,
                            is_mandatory=False,
                            rationale="Regular testing and evaluation through telemetry.",
                        )
                    ],
                },
                keywords=[
                    "encryption",
                    "confidentiality",
                    "integrity",
                    "restore",
                    "timely",
                    "resilience",
                ],
            )
        )

        # 2. GDPR Article 33: Notification of a personal data breach
        self.register_rule(
            MappingRule(
                regulatory_control_id="gdpr-art-33",
                regulation="GDPR",
                target_categories=[
                    CategoryMapping(
                        category=ControlCategory.LOGGING_MONITORING,
                        weight=1.5,
                        is_mandatory=True,
                        rationale="Audit logging and breach detection needed to alert in 72h.",
                    ),
                    CategoryMapping(
                        category=ControlCategory.IDENTITY_ACCESS,
                        weight=1.0,
                        is_mandatory=False,
                        rationale="Authentication logging to verify unauthorized breach vector.",
                    ),
                ],
                keywords=["breach", "notify", "72 hours", "supervisory authority", "incident"],
            )
        )

        # 3. DORA Article 6: ICT Risk Management Framework
        self.register_rule(
            MappingRule(
                regulatory_control_id="dora-art-6",
                regulation="DORA",
                target_categories=[
                    CategoryMapping(
                        category=ControlCategory.IDENTITY_ACCESS,
                        weight=1.3,
                        is_mandatory=True,
                        rationale="DORA Art. 6 requires sound access control systems.",
                    ),
                    CategoryMapping(
                        category=ControlCategory.ENCRYPTION,
                        weight=1.2,
                        is_mandatory=True,
                        rationale="Cryptographic protection across all financial data assets.",
                    ),
                    CategoryMapping(
                        category=ControlCategory.NETWORK,
                        weight=1.4,
                        is_mandatory=True,
                        rationale=(
                            "Network segmentation to minimize impact of ICT risks "
                            "per DORA Art. 6(2)."
                        ),
                    ),
                ],
                sub_clause_mappings={
                    "6(1)": [
                        CategoryMapping(
                            category=ControlCategory.IDENTITY_ACCESS,
                            weight=1.2,
                            is_mandatory=True,
                            rationale="Sound ICT management policies and role definitions.",
                        ),
                        CategoryMapping(
                            category=ControlCategory.ENCRYPTION,
                            weight=1.2,
                            is_mandatory=True,
                            rationale="Cryptographic protection of financial tools.",
                        ),
                    ],
                    "6(2)": [
                        CategoryMapping(
                            category=ControlCategory.NETWORK,
                            weight=1.5,
                            is_mandatory=True,
                            rationale=(
                                "Minimizing ICT risk via perimeter and segmentation controls."
                            ),
                        )
                    ],
                },
                keywords=[
                    "ict risk",
                    "framework",
                    "strategies",
                    "minimize impact",
                    "segmentation",
                ],
            )
        )

        # 4. DORA Article 11 / 12: ICT Systems Backup & Recovery
        self.register_rule(
            MappingRule(
                regulatory_control_id="dora-art-11",
                regulation="DORA",
                target_categories=[
                    CategoryMapping(
                        category=ControlCategory.BACKUP_RECOVERY,
                        weight=2.0,
                        is_mandatory=True,
                        rationale="Continuous backup, geographic redundancy, and rapid recovery.",
                    )
                ],
                keywords=["backup", "recovery", "redundancy", "continuity", "restoration"],
            )
        )

        # 5. DORA Article 19: Reporting of major ICT-related incidents
        self.register_rule(
            MappingRule(
                regulatory_control_id="dora-art-19",
                regulation="DORA",
                target_categories=[
                    CategoryMapping(
                        category=ControlCategory.LOGGING_MONITORING,
                        weight=1.5,
                        is_mandatory=True,
                        rationale="Continuous telemetry and log aggregation for incident alerts.",
                    ),
                    CategoryMapping(
                        category=ControlCategory.NETWORK,
                        weight=1.0,
                        is_mandatory=False,
                        rationale="Network telemetry for detecting anomalous data exfiltration.",
                    ),
                ],
                keywords=["incident", "classification", "reporting", "competent authority"],
            )
        )

        # 6. NIS2 Article 21: Cybersecurity risk-management measures
        self.register_rule(
            MappingRule(
                regulatory_control_id="nis2-art-21",
                regulation="NIS2",
                target_categories=[
                    CategoryMapping(
                        category=ControlCategory.NETWORK,
                        weight=1.4,
                        is_mandatory=True,
                        rationale=(
                            "NIS2 Art. 21(2)(e) requires basic cyber hygiene and "
                            "network security."
                        ),
                    ),
                    CategoryMapping(
                        category=ControlCategory.ENCRYPTION,
                        weight=1.3,
                        is_mandatory=True,
                        rationale=(
                            "NIS2 Art. 21(2)(g) mandates policies on cryptography "
                            "and encryption."
                        ),
                    ),
                    CategoryMapping(
                        category=ControlCategory.BACKUP_RECOVERY,
                        weight=1.4,
                        is_mandatory=True,
                        rationale=(
                            "NIS2 Art. 21(2)(c) mandates business continuity and "
                            "backup management."
                        ),
                    ),
                    CategoryMapping(
                        category=ControlCategory.IDENTITY_ACCESS,
                        weight=1.5,
                        is_mandatory=True,
                        rationale="NIS2 Art. 21(2)(i) mandates multi-factor authentication.",
                    ),
                ],
                sub_clause_mappings={
                    "21(2)(c)": [
                        CategoryMapping(
                            category=ControlCategory.BACKUP_RECOVERY,
                            weight=2.0,
                            is_mandatory=True,
                            rationale="Backup management and crisis recovery procedures.",
                        )
                    ],
                    "21(2)(e)": [
                        CategoryMapping(
                            category=ControlCategory.NETWORK,
                            weight=1.5,
                            is_mandatory=True,
                            rationale="Network security and basic cyber hygiene.",
                        ),
                        CategoryMapping(
                            category=ControlCategory.IDENTITY_ACCESS,
                            weight=1.2,
                            is_mandatory=True,
                            rationale="Access control and hygiene.",
                        ),
                    ],
                    "21(2)(g)": [
                        CategoryMapping(
                            category=ControlCategory.ENCRYPTION,
                            weight=2.0,
                            is_mandatory=True,
                            rationale="Policies and procedures on cryptography and encryption.",
                        )
                    ],
                    "21(2)(i)": [
                        CategoryMapping(
                            category=ControlCategory.IDENTITY_ACCESS,
                            weight=2.0,
                            is_mandatory=True,
                            rationale="Multi-factor authentication or secured voice communication.",
                        )
                    ],
                },
                keywords=["risk-management", "continuity", "cryptography", "mfa", "hygiene"],
            )
        )

    def register_rule(self, rule: MappingRule) -> None:
        """Register or overwrite a mapping rule in the matrix."""
        normalized_id = rule.regulatory_control_id.strip().lower()
        self._rules[normalized_id] = rule

    def get_rule(self, regulatory_control_id: str) -> Optional[MappingRule]:
        """Retrieve a direct mapping rule by article ID."""
        normalized_id = regulatory_control_id.strip().lower()
        return self._rules.get(normalized_id)

    def resolve_categories(
        self,
        regulatory_control_id: str,
        text_context: str = "",
    ) -> List[CategoryMapping]:
        """Resolve the technical categories mapped to a regulatory control.

        If a direct mapping exists in the matrix, it is returned.
        Otherwise, a semantic keyword heuristic is applied to infer
        relevant control categories from the statutory text.

        Args:
            regulatory_control_id: Identifier of the regulatory control.
            text_context: Supporting normative text (title, prose, clauses).

        Returns:
            List of CategoryMapping instances.
        """
        rule = self.get_rule(regulatory_control_id)
        if rule and rule.target_categories:
            return rule.target_categories

        # Fallback: Semantic heuristic keyword matching
        inferred_categories: Set[ControlCategory] = set()
        combined_text = f"{regulatory_control_id} {text_context}".lower()

        for phrase, category in self._keyword_category_map.items():
            if re.search(r"\b" + re.escape(phrase) + r"\b", combined_text):
                inferred_categories.add(category)

        if inferred_categories:
            logger.info(
                "Inferred categories for '%s' via heuristic keywords: %s",
                regulatory_control_id,
                [c.value for c in inferred_categories],
            )
            return [
                CategoryMapping(
                    category=cat,
                    weight=1.0,
                    is_mandatory=False,
                    rationale=f"Inferred via semantic keyword match in '{regulatory_control_id}'.",
                )
                for cat in inferred_categories
            ]

        return []
