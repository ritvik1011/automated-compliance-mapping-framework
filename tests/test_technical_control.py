"""Unit Test Suite for TechnicalControl and InfrastructureBaseline Models.

This module validates that technical controls and infrastructure baselines
accurately capture cloud asset security states, enforce naming conventions,
and provide filtering and summary analytics.
"""

from datetime import datetime
import pytest
from pydantic import ValidationError

from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    InfrastructureBaseline,
    TechnicalControl,
)


def test_technical_control_instantiation_valid() -> None:
    """WHAT: Validates creation of a compliant TechnicalControl model.

    WHY IT MATTERS:
    Serves as the atomic building block for cloud asset baseline data collection.
    """
    control = TechnicalControl(
        control_id="azure-storage-encryption-prod-01",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AZURE,
        resource_type="StorageAccount",
        resource_id=(
            "/subscriptions/sub-123/resourceGroups/rg-data/providers/"
            "Microsoft.Storage/storageAccounts/stprod01"
        ),
        resource_name="stprod01",
        control_description="Azure Storage Account has encryption at rest enabled",
        current_state={"encryption_enabled": True, "key_source": "Microsoft.Storage"},
        compliance_status=ComplianceStatus.COMPLIANT,
        metadata={"region": "westeurope", "environment": "production"},
    )

    assert control.control_id == "azure-storage-encryption-prod-01"
    assert control.control_category == ControlCategory.ENCRYPTION
    assert control.cloud_provider == CloudProvider.AZURE
    assert control.compliance_status == ComplianceStatus.COMPLIANT
    assert control.current_state["encryption_enabled"] is True
    assert isinstance(control.evidence_timestamp, datetime)


def test_technical_control_rejects_invalid_control_id() -> None:
    """WHAT: Ensures control_id validator rejects invalid characters.

    WHY IT MATTERS:
    Control IDs must be URI and identifier safe for OSCAL mapping without spaces or symbols.
    """
    with pytest.raises(ValidationError) as exc_info:
        TechnicalControl(
            control_id="invalid control id with spaces!",
            control_category=ControlCategory.NETWORK,
            cloud_provider=CloudProvider.AWS,
            resource_type="SecurityGroup",
            resource_id="sg-123456",
            resource_name="default-sg",
            control_description="Restricts SSH ingress",
        )
    assert "control_id must contain only alphanumeric, hyphens, underscores" in str(
        exc_info.value
    )


def test_infrastructure_baseline_operations() -> None:
    """WHAT: Tests InfrastructureBaseline container filtering and summaries.

    WHY IT MATTERS:
    Downstream gap analysis requires filtering controls by category and isolating
    non-compliant findings for remediation.
    """
    ctrl1 = TechnicalControl(
        control_id="ctrl-enc-01",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AZURE,
        resource_type="StorageAccount",
        resource_id="/sub/rg/storage1",
        resource_name="storage1",
        control_description="Encryption at rest",
        compliance_status=ComplianceStatus.COMPLIANT,
    )
    ctrl2 = TechnicalControl(
        control_id="ctrl-iam-01",
        control_category=ControlCategory.IDENTITY_ACCESS,
        cloud_provider=CloudProvider.AZURE,
        resource_type="RoleAssignment",
        resource_id="/sub/rg/iam1",
        resource_name="iam1",
        control_description="MFA enforced on admin role",
        compliance_status=ComplianceStatus.NON_COMPLIANT,
    )
    ctrl3 = TechnicalControl(
        control_id="ctrl-net-01",
        control_category=ControlCategory.NETWORK,
        cloud_provider=CloudProvider.AZURE,
        resource_type="NetworkSecurityGroup",
        resource_id="/sub/rg/nsg1",
        resource_name="nsg1",
        control_description="Port 22 closed to public internet",
        compliance_status=ComplianceStatus.PARTIAL,
    )

    baseline = InfrastructureBaseline(
        baseline_id="baseline-azure-prod-2026",
        cloud_provider=CloudProvider.AZURE,
        subscription_id="sub-12345",
        total_resources_scanned=3,
        controls=[ctrl1, ctrl2, ctrl3],
    )

    assert baseline.total_resources_scanned == 3
    assert len(baseline.get_controls_by_category(ControlCategory.ENCRYPTION)) == 1
    assert len(baseline.get_controls_by_category(ControlCategory.BACKUP_RECOVERY)) == 0

    non_compliant = baseline.get_non_compliant_controls()
    assert len(non_compliant) == 1
    assert non_compliant[0].control_id == "ctrl-iam-01"

    summary = baseline.get_compliance_summary()
    assert summary["compliant"] == 1
    assert summary["non_compliant"] == 1
    assert summary["partial"] == 1
    assert summary["unknown"] == 0


def test_baseline_json_serialization() -> None:
    """WHAT: Tests JSON serialization and deserialization of InfrastructureBaseline.

    WHY IT MATTERS:
    Ensures baselines can be stored as JSON artifacts and parsed by subsequent pipeline stages.
    """
    ctrl = TechnicalControl(
        control_id="aws-s3-encryption-01",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AWS,
        resource_type="S3Bucket",
        resource_id="arn:aws:s3:::my-bucket",
        resource_name="my-bucket",
        control_description="Default AES-256 encryption enabled",
        compliance_status=ComplianceStatus.COMPLIANT,
    )

    baseline = InfrastructureBaseline(
        baseline_id="baseline-aws-01",
        cloud_provider=CloudProvider.AWS,
        total_resources_scanned=1,
        controls=[ctrl],
    )

    json_str = baseline.model_dump_json()
    reconstructed = InfrastructureBaseline.model_validate_json(json_str)

    assert reconstructed.baseline_id == "baseline-aws-01"
    assert reconstructed.cloud_provider == CloudProvider.AWS
    assert len(reconstructed.controls) == 1
    assert reconstructed.controls[0].control_id == "aws-s3-encryption-01"
