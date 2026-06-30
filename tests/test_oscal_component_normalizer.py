"""Unit Test Suite for OSCAL Component-Definition Normalizer.

This module validates that technical infrastructure baselines are faithfully transformed
into standard NIST OSCAL Component-Definition JSON structures.
"""

import json
from pathlib import Path
import pytest

from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    InfrastructureBaseline,
    TechnicalControl,
)
from src.normalizers.oscal_component_normalizer import OSCALComponentNormalizer


@pytest.fixture
def sample_baseline() -> InfrastructureBaseline:
    """Fixture providing a multi-resource infrastructure baseline."""
    res_id_storage = (
        "/subscriptions/sub-1/resourceGroups/rg-1/providers/"
        "Microsoft.Storage/storageAccounts/stprod"
    )
    res_id_nsg = (
        "/subscriptions/sub-1/resourceGroups/rg-1/providers/"
        "Microsoft.Network/networkSecurityGroups/nsg-web"
    )
    ctrl_enc = TechnicalControl(
        control_id="azure-storage-encryption-stprod",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AZURE,
        resource_type="StorageAccount",
        resource_id=res_id_storage,
        resource_name="stprod",
        control_description="Storage encryption at rest",
        current_state={"encryption_enabled": True},
        compliance_status=ComplianceStatus.COMPLIANT,
    )
    ctrl_https = TechnicalControl(
        control_id="azure-storage-https-stprod",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AZURE,
        resource_type="StorageAccount",
        resource_id=res_id_storage,
        resource_name="stprod",
        control_description="Enforces HTTPS traffic only",
        current_state={"https_only": False},
        compliance_status=ComplianceStatus.NON_COMPLIANT,
    )
    ctrl_nsg = TechnicalControl(
        control_id="azure-nsg-web",
        control_category=ControlCategory.NETWORK,
        cloud_provider=CloudProvider.AZURE,
        resource_type="NetworkSecurityGroup",
        resource_id=res_id_nsg,
        resource_name="nsg-web",
        control_description="Network security group inbound rules",
        current_state={"risky_rules_count": 0},
        compliance_status=ComplianceStatus.COMPLIANT,
    )

    return InfrastructureBaseline(
        baseline_id="baseline-azure-sub-1",
        cloud_provider=CloudProvider.AZURE,
        subscription_id="sub-1",
        total_resources_scanned=3,
        controls=[ctrl_enc, ctrl_https, ctrl_nsg],
    )


def test_oscal_component_normalizer_root_structure(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """WHAT: Tests top-level schema elements of OSCAL Component-Definition.

    WHY IT MATTERS:
    Guarantees structural compatibility with NIST OSCAL tooling and catalogs.
    """
    normalizer = OSCALComponentNormalizer(sample_baseline)
    doc = normalizer.normalize()

    assert "component-definition" in doc
    comp_def = doc["component-definition"]
    assert "uuid" in comp_def
    assert "metadata" in comp_def
    assert "components" in comp_def
    assert "capabilities" in comp_def
    assert "back-matter" in comp_def


def test_oscal_component_normalizer_metadata(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """WHAT: Validates metadata elements including roles, parties, and versioning.

    WHY IT MATTERS:
    Ensures baseline metadata adheres to OSCAL auditability expectations.
    """
    normalizer = OSCALComponentNormalizer(sample_baseline)
    doc = normalizer.normalize()
    metadata = doc["component-definition"]["metadata"]

    assert metadata["title"] == "Technical Baseline - AZURE"
    assert metadata["version"] == "1.0.0"
    assert metadata["oscal-version"] == "1.1.2"
    assert len(metadata["roles"]) == 2
    assert len(metadata["parties"]) == 1
    assert len(metadata["responsible-parties"]) == 1


def test_oscal_component_grouping_and_types(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """WHAT: Validates that multiple controls on the same resource are grouped into one component.

    WHY IT MATTERS:
    A physical/logical cloud asset has multiple security controls; it should not be duplicated.
    """
    normalizer = OSCALComponentNormalizer(sample_baseline)
    doc = normalizer.normalize()
    components = doc["component-definition"]["components"]

    # 3 controls across 2 unique resource_ids (stprod and nsg-web)
    assert len(components) == 2

    storage_comp = next(c for c in components if c["title"] == "stprod")
    assert storage_comp["type"] == "service"
    assert storage_comp["description"] == "StorageAccount resource in AZURE"

    # stprod had 1 compliant and 1 non-compliant control -> overall status is "non-compliant"
    status_prop = next(p for p in storage_comp["props"] if p["name"] == "compliance-status")
    assert status_prop["value"] == "non-compliant"

    # Check control-implementations for storage
    ctrl_impls = storage_comp["control-implementations"]
    assert len(ctrl_impls) == 1
    assert ctrl_impls[0]["source"] == "#data_encryption"
    assert len(ctrl_impls[0]["implemented-requirements"]) == 2

    nsg_comp = next(c for c in components if c["title"] == "nsg-web")
    assert nsg_comp["type"] == "network"
    nsg_status_prop = next(p for p in nsg_comp["props"] if p["name"] == "compliance-status")
    assert nsg_status_prop["value"] == "compliant"


def test_oscal_component_normalizer_overall_status_evaluation() -> None:
    """WHAT: Tests status resolution logic (compliant, non-compliant, partial, unknown).

    WHY IT MATTERS:
    Resource rollup must reflect weakest link security posture.
    """
    normalizer = OSCALComponentNormalizer(
        InfrastructureBaseline(
            baseline_id="b1",
            cloud_provider=CloudProvider.AWS,
            controls=[],
        )
    )

    c_comp = TechnicalControl(
        control_id="c1",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AWS,
        resource_type="S3Bucket",
        resource_id="arn:s3:::b1",
        resource_name="b1",
        control_description="enc",
        compliance_status=ComplianceStatus.COMPLIANT,
    )
    c_part = TechnicalControl(
        control_id="c2",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AWS,
        resource_type="S3Bucket",
        resource_id="arn:s3:::b1",
        resource_name="b1",
        control_description="enc",
        compliance_status=ComplianceStatus.PARTIAL,
    )
    c_non = TechnicalControl(
        control_id="c3",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AWS,
        resource_type="S3Bucket",
        resource_id="arn:s3:::b1",
        resource_name="b1",
        control_description="enc",
        compliance_status=ComplianceStatus.NON_COMPLIANT,
    )

    assert normalizer._get_overall_status([c_comp]) == "compliant"
    assert normalizer._get_overall_status([c_comp, c_part]) == "partial"
    assert normalizer._get_overall_status([c_comp, c_part, c_non]) == "non-compliant"


def test_oscal_component_normalizer_save(
    sample_baseline: InfrastructureBaseline, tmp_path: Path
) -> None:
    """WHAT: Tests serialization of OSCAL Component-Definition to disk.

    WHY IT MATTERS:
    Allows exporting normalized components for gap analysis.
    """
    normalizer = OSCALComponentNormalizer(sample_baseline)
    out_file = tmp_path / "oscal_profiles" / "azure_component_definition.json"
    normalizer.save(str(out_file))

    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "component-definition" in data
    assert data["component-definition"]["metadata"]["title"] == "Technical Baseline - AZURE"
    assert len(data["component-definition"]["components"]) == 2
