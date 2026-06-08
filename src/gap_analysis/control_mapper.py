"""Control Mapper - Maps Regulatory Controls to Technical Controls.

This module handles the mapping between regulatory requirements (OSCAL Catalog)
and technical implementations (OSCAL Component-Definition). This is a critical
step because the mapping is rarely 1:1 - one regulatory control may map to
multiple technical controls, or vice versa.

Research Context:
    The mapping process itself reveals socio-technical friction points.
    When a regulatory control like "appropriate technical measures" (GDPR Art. 32)
    cannot be cleanly mapped to specific technical controls, this indicates
    a fundamental challenge in Policy-as-Code approaches.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _normalize_id(control_id: str) -> str:
    """Normalize control ID for flexible matching (e.g., 'gdpr-art-32' <-> 'gdpr-art32')."""
    return control_id.strip().lower().replace("-", "").replace("_", "")


class ControlMapper:
    """Maps regulatory controls to technical controls.

    The mapper uses a combination of:
    1. Pre-defined mapping rules (from JSON configuration)
    2. Heuristic matching based on control categories
    3. Manual overrides for edge cases

    This approach balances automation with human expertise, acknowledging
    that full automation of regulatory mapping is not yet feasible.
    """

    def __init__(self, mapping_config_path: Optional[str] = None):
        """Initialize the control mapper.

        Args:
            mapping_config_path: Path to JSON file containing mapping rules.
                                 If None, uses default heuristic mapping.
        """
        self.mapping_rules: Dict[str, Any] = {}
        self.reverse_mapping: Dict[str, List[str]] = {}

        if mapping_config_path:
            self._load_mapping_config(mapping_config_path)
        else:
            self._initialize_default_mappings()

    def _load_mapping_config(self, config_path: str) -> None:
        """Load mapping configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Mapping config not found: {config_path}. Using defaults.")
            self._initialize_default_mappings()
            return

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.mapping_rules = config.get("regulatory_to_technical", {})

        # Build reverse mapping
        self._rebuild_reverse_mapping()
        logger.info(f"Loaded {len(self.mapping_rules)} mapping rules from {config_path}")

    def _initialize_default_mappings(self) -> None:
        """Initialize default heuristic mappings.

        These mappings are based on common patterns in regulatory frameworks
        and technical implementations.
        """
        self.mapping_rules = {
            # GDPR Article 32: Security of Processing
            "gdpr-art32": [
                "azure-storage-encryption-*",
                "azure-keyvault-protection-*",
                "azure-vm-managed-identity-*",
                "azure-storage-redundancy-*",
                "azure-storage-https-*",
            ],
            "gdpr-art-32": [
                "azure-storage-encryption-*",
                "azure-keyvault-protection-*",
                "azure-vm-managed-identity-*",
                "azure-storage-redundancy-*",
                "azure-storage-https-*",
                "azure-nsg-*",
            ],
            "gdpr-art30": [
                "azure-storage-*",
            ],
            "gdpr-art33": [
                "azure-monitor-*",
            ],
            "gdpr-art-33": [
                "azure-monitor-*",
            ],
            # DORA Article 6: ICT Risk Management
            "dora-art-6": [
                "azure-nsg-*",
                "azure-storage-redundancy-*",
                "azure-keyvault-protection-*",
                "azure-storage-encryption-*",
                "azure-vm-managed-identity-*",
            ],
            "dora-art6": [
                "azure-nsg-*",
                "azure-storage-redundancy-*",
                "azure-keyvault-protection-*",
            ],
            # DORA Article 11: ICT Business Continuity
            "dora-art-11": [
                "azure-storage-redundancy-*",
                "azure-backup-*",
            ],
            "dora-art11": [
                "azure-storage-redundancy-*",
                "azure-backup-*",
            ],
            # NIS2 Article 21: Security of Network and Information Systems
            "nis2-art-21": [
                "azure-nsg-*",
                "azure-storage-encryption-*",
                "azure-keyvault-protection-*",
                "azure-storage-redundancy-*",
                "azure-vm-managed-identity-*",
            ],
            "nis2-art21": [
                "azure-nsg-*",
                "azure-storage-encryption-*",
                "azure-keyvault-protection-*",
            ],
        }

        self._rebuild_reverse_mapping()
        logger.info("Initialized default heuristic mappings")

    def _rebuild_reverse_mapping(self) -> None:
        """Rebuild reverse index mapping technical patterns to regulatory controls."""
        self.reverse_mapping = {}
        for reg_control, tech_patterns in self.mapping_rules.items():
            for pattern in tech_patterns:
                if isinstance(pattern, list):
                    pattern_str = pattern[0]
                else:
                    pattern_str = pattern
                base_pattern = pattern_str.replace("*", "")
                if base_pattern not in self.reverse_mapping:
                    self.reverse_mapping[base_pattern] = []
                if reg_control not in self.reverse_mapping[base_pattern]:
                    self.reverse_mapping[base_pattern].append(reg_control)

    def get_technical_controls_for_regulatory(
        self,
        regulatory_control_id: str,
        available_technical_controls: List[str],
    ) -> List[str]:
        """Get technical controls that map to a regulatory control.

        Args:
            regulatory_control_id: ID of the regulatory control
            available_technical_controls: List of available technical control IDs

        Returns:
            List of technical control IDs that map to the regulatory control
        """
        # Look up directly or by normalized ID
        patterns = self.mapping_rules.get(regulatory_control_id)
        if patterns is None:
            norm = _normalize_id(regulatory_control_id)
            for k, v in self.mapping_rules.items():
                if _normalize_id(k) == norm:
                    patterns = v
                    break

        if not patterns:
            logger.debug(
                f"No technical controls found for regulatory control: {regulatory_control_id}"
            )
            return []

        matched_controls = []
        for pattern in patterns:
            if isinstance(pattern, list):
                pattern = pattern[0]

            # Handle wildcard patterns
            if pattern.endswith("*"):
                base_pattern = pattern[:-1]
                matched = [tc for tc in available_technical_controls if tc.startswith(base_pattern)]
                matched_controls.extend(matched)
            else:
                # Exact match
                if pattern in available_technical_controls:
                    matched_controls.append(pattern)

        # Remove duplicates while preserving deterministic order
        seen = set()
        deduped = []
        for c in matched_controls:
            if c not in seen:
                seen.add(c)
                deduped.append(c)

        return deduped

    def get_regulatory_controls_for_technical(
        self,
        technical_control_id: str,
    ) -> List[str]:
        """Get regulatory controls that a technical control maps to.

        Args:
            technical_control_id: ID of the technical control

        Returns:
            List of regulatory control IDs
        """
        # Try exact match first
        if technical_control_id in self.reverse_mapping:
            return self.reverse_mapping[technical_control_id]

        # Try pattern matching
        results: List[str] = []
        for base_pattern, reg_controls in self.reverse_mapping.items():
            if technical_control_id.startswith(base_pattern):
                for rc in reg_controls:
                    if rc not in results:
                        results.append(rc)

        return results

    def get_unmapped_regulatory_controls(
        self,
        all_regulatory_controls: List[str],
    ) -> List[str]:
        """Get regulatory controls that have no mapping rules.

        This is a key research metric - it shows which regulatory
        requirements cannot be automatically mapped to technical controls.

        Args:
            all_regulatory_controls: List of all regulatory control IDs

        Returns:
            List of unmapped regulatory control IDs
        """
        unmapped = []
        for reg_id in all_regulatory_controls:
            norm = _normalize_id(reg_id)
            has_rule = any(_normalize_id(k) == norm for k in self.mapping_rules)
            if not has_rule:
                unmapped.append(reg_id)

        if unmapped:
            logger.warning(
                f"Found {len(unmapped)} unmapped regulatory controls. "
                "This indicates socio-technical friction in Policy-as-Code approaches."
            )

        return unmapped

    def add_mapping_rule(
        self,
        regulatory_control_id: str,
        technical_control_patterns: List[str],
    ) -> None:
        """Add a new mapping rule.

        Args:
            regulatory_control_id: Regulatory control ID
            technical_control_patterns: List of technical control patterns
        """
        self.mapping_rules[regulatory_control_id] = technical_control_patterns
        self._rebuild_reverse_mapping()
        logger.info(f"Added mapping rule: {regulatory_control_id} → {technical_control_patterns}")

    def save_mapping_config(self, output_path: str) -> None:
        """Save the current mapping configuration to a JSON file."""
        config = {
            "regulatory_to_technical": self.mapping_rules,
            "metadata": {
                "description": "Control mapping configuration for gap analysis",
                "version": "1.0.0",
            },
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Mapping configuration saved to {output_path}")
