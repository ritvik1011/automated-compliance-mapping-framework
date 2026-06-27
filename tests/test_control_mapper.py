"""Unit and Integration Tests for ControlMapper (Step 3).

Validates loading configuration, wildcard matching, reverse indexing,
unmapped regulatory control detection, dynamic rule registration,
and configuration serialization.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.gap_analysis.control_mapper import ControlMapper


def test_control_mapper_default_initialization() -> None:
    """Verify that ControlMapper initializes with default heuristic mappings."""
    mapper = ControlMapper()
    assert len(mapper.mapping_rules) > 0
    assert "gdpr-art32" in mapper.mapping_rules or "gdpr-art-32" in mapper.mapping_rules
    assert len(mapper.reverse_mapping) > 0


def test_control_mapper_wildcard_matching() -> None:
    """Verify wildcard pattern expansion against available technical controls."""
    mapper = ControlMapper()
    available_tech_controls = [
        "azure-storage-encryption-blob-001",
        "azure-storage-encryption-files-002",
        "azure-storage-redundancy-geo-001",
        "azure-keyvault-protection-kv1",
        "azure-vm-managed-identity-vm1",
        "unrelated-control-xyz",
    ]

    matched = mapper.get_technical_controls_for_regulatory("gdpr-art32", available_tech_controls)

    assert "azure-storage-encryption-blob-001" in matched
    assert "azure-storage-encryption-files-002" in matched
    assert "azure-storage-redundancy-geo-001" in matched
    assert "azure-keyvault-protection-kv1" in matched
    assert "azure-vm-managed-identity-vm1" in matched
    assert "unrelated-control-xyz" not in matched


def test_control_mapper_id_normalization() -> None:
    """Verify ID normalization allows 'gdpr-art-32' and 'gdpr-art32' lookups."""
    mapper = ControlMapper()
    available = ["azure-storage-encryption-blob-001"]

    matched_dash = mapper.get_technical_controls_for_regulatory("gdpr-art-32", available)
    matched_no_dash = mapper.get_technical_controls_for_regulatory("gdpr-art32", available)

    assert "azure-storage-encryption-blob-001" in matched_dash
    assert "azure-storage-encryption-blob-001" in matched_no_dash


def test_control_mapper_reverse_mapping() -> None:
    """Verify reverse mapping from technical control ID to regulatory controls."""
    mapper = ControlMapper()

    reg_controls = mapper.get_regulatory_controls_for_technical("azure-storage-encryption-storage1")
    assert len(reg_controls) > 0
    # Must include GDPR Art 32 or similar
    assert any("gdpr-art" in rc for rc in reg_controls)


def test_control_mapper_reverse_mapping_unmapped() -> None:
    """Verify reverse mapping returns empty list for unknown technical controls."""
    mapper = ControlMapper()
    reg_controls = mapper.get_regulatory_controls_for_technical("non-existent-system-999")
    assert reg_controls == []


def test_control_mapper_unmapped_regulatory_controls() -> None:
    """Verify identification of unmapped regulatory controls."""
    mapper = ControlMapper()
    all_regs = ["gdpr-art32", "dora-art-6", "unknown-tax-rule-99"]

    unmapped = mapper.get_unmapped_regulatory_controls(all_regs)
    assert "unknown-tax-rule-99" in unmapped
    assert "gdpr-art32" not in unmapped


def test_control_mapper_add_mapping_rule() -> None:
    """Verify dynamic addition of mapping rules and reverse index updates."""
    mapper = ControlMapper()
    custom_reg_id = "custom-soc2-cc6.1"
    tech_patterns = ["azure-nsg-rule-*", "custom-firewall-*"]

    mapper.add_mapping_rule(custom_reg_id, tech_patterns)

    available = ["azure-nsg-rule-inbound-01", "other-control"]
    matched = mapper.get_technical_controls_for_regulatory(custom_reg_id, available)
    assert "azure-nsg-rule-inbound-01" in matched

    reg_matches = mapper.get_regulatory_controls_for_technical("custom-firewall-fw1")
    assert custom_reg_id in reg_matches


def test_control_mapper_load_and_save_json(tmp_path: Path) -> None:
    """Verify loading from JSON file and saving configuration."""
    config_data = {
        "regulatory_to_technical": {
            "iso27001-a10": ["azure-crypto-*", "azure-keyvault-*"],
            "iso27001-a12": ["azure-backup-*"],
        },
        "metadata": {"version": "2.0.0"},
    }

    config_file = tmp_path / "test_mappings.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    mapper = ControlMapper(mapping_config_path=str(config_file))
    assert "iso27001-a10" in mapper.mapping_rules
    assert len(mapper.mapping_rules) == 2

    available = ["azure-crypto-tls-1.3", "azure-backup-vault-1"]
    matched = mapper.get_technical_controls_for_regulatory("iso27001-a10", available)
    assert "azure-crypto-tls-1.3" in matched

    # Save to a new file
    output_file = tmp_path / "saved_mappings.json"
    mapper.save_mapping_config(str(output_file))
    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert "regulatory_to_technical" in saved_data
    assert "iso27001-a10" in saved_data["regulatory_to_technical"]


def test_control_mapper_load_nonexistent_file(tmp_path: Path) -> None:
    """Verify that a non-existent file logs a warning and falls back to defaults."""
    non_existent = str(tmp_path / "does_not_exist.json")
    mapper = ControlMapper(mapping_config_path=non_existent)
    assert len(mapper.mapping_rules) > 0  # Fallback to default heuristic mappings
