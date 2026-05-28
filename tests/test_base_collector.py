"""Unit Test Suite for BaseCollector Abstract Interface and Collection Orchestration.

This module validates that BaseCollector enforces interface contracts across cloud providers,
resiliently handles category-level collection errors, and serializes baselines to disk.
"""

import json
from pathlib import Path
from typing import List
import pytest

from src.collectors.base_collector import BaseCollector
from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    TechnicalControl,
)


class MockWorkingCollector(BaseCollector):
    """Concrete mock collector simulating a fully operational provider."""

    @property
    def cloud_provider(self) -> CloudProvider:
        return CloudProvider.AZURE

    def authenticate(self) -> bool:
        return True

    def collect_iam_controls(self) -> List[TechnicalControl]:
        return [
            TechnicalControl(
                control_id="azure-iam-01",
                control_category=ControlCategory.IDENTITY_ACCESS,
                cloud_provider=CloudProvider.AZURE,
                resource_type="RoleAssignment",
                resource_id="/sub/rg/role1",
                resource_name="role1",
                control_description="MFA enabled",
                compliance_status=ComplianceStatus.COMPLIANT,
            )
        ]

    def collect_encryption_controls(self) -> List[TechnicalControl]:
        return [
            TechnicalControl(
                control_id="azure-enc-01",
                control_category=ControlCategory.ENCRYPTION,
                cloud_provider=CloudProvider.AZURE,
                resource_type="StorageAccount",
                resource_id="/sub/rg/st1",
                resource_name="st1",
                control_description="Storage encrypted",
                compliance_status=ComplianceStatus.COMPLIANT,
            )
        ]

    def collect_network_controls(self) -> List[TechnicalControl]:
        return [
            TechnicalControl(
                control_id="azure-net-01",
                control_category=ControlCategory.NETWORK,
                cloud_provider=CloudProvider.AZURE,
                resource_type="NSG",
                resource_id="/sub/rg/nsg1",
                resource_name="nsg1",
                control_description="Inbound SSH blocked",
                compliance_status=ComplianceStatus.COMPLIANT,
            )
        ]

    def collect_backup_controls(self) -> List[TechnicalControl]:
        return [
            TechnicalControl(
                control_id="azure-backup-01",
                control_category=ControlCategory.BACKUP_RECOVERY,
                cloud_provider=CloudProvider.AZURE,
                resource_type="BackupVault",
                resource_id="/sub/rg/vault1",
                resource_name="vault1",
                control_description="Daily backup retention configured",
                compliance_status=ComplianceStatus.COMPLIANT,
            )
        ]


class MockFailingAuthCollector(MockWorkingCollector):
    """Mock collector simulating authentication failure."""

    def authenticate(self) -> bool:
        return False


class MockPartialErrorCollector(MockWorkingCollector):
    """Mock collector simulating a network failure on one category."""

    def collect_network_controls(self) -> List[TechnicalControl]:
        raise ConnectionResetError("Remote API timed out")


def test_base_collector_cannot_be_instantiated_directly() -> None:
    """WHAT: Verifies that BaseCollector cannot be instantiated without abstract methods.

    WHY IT MATTERS:
    Ensures interface contracts cannot be bypassed by incomplete implementations.
    """
    with pytest.raises(TypeError):
        BaseCollector()  # type: ignore[abstract]


def test_base_collector_successful_orchestration() -> None:
    """WHAT: Tests collect_all across all four control categories.

    WHY IT MATTERS:
    Validates happy-path aggregation of IAM, encryption, network, and backup controls.
    """
    collector = MockWorkingCollector(subscription_id="sub-abc-123", region="westeurope")
    baseline = collector.collect_all()

    assert baseline.baseline_id == "baseline-azure-sub-abc-123"
    assert baseline.cloud_provider == CloudProvider.AZURE
    assert baseline.subscription_id == "sub-abc-123"
    assert baseline.total_resources_scanned == 4
    assert len(baseline.controls) == 4
    assert baseline.collection_metadata["errors_encountered"] == 0
    assert baseline.collection_metadata["region"] == "westeurope"


def test_base_collector_authentication_failure_raises() -> None:
    """WHAT: Ensures collect_all raises RuntimeError if authentication fails.

    WHY IT MATTERS:
    Prevents empty or silent partial baselines from being generated if credentials fail.
    """
    collector = MockFailingAuthCollector(subscription_id="sub-invalid")
    with pytest.raises(RuntimeError) as exc_info:
        collector.collect_all()
    assert "Authentication failed" in str(exc_info.value)


def test_base_collector_error_resilience() -> None:
    """WHAT: Verifies that failure in one category does not prevent other categories from running.

    WHY IT MATTERS:
    Cloud API transient rate limits or permission drops should not wipe out the entire scan.
    """
    collector = MockPartialErrorCollector(subscription_id="sub-part")
    baseline = collector.collect_all()

    # Network failed, but IAM, Encryption, and Backup should still succeed (3 controls total)
    assert len(baseline.controls) == 3
    assert baseline.collection_metadata["errors_encountered"] == 1
    assert len(baseline.collection_metadata["error_details"]) == 1
    assert baseline.collection_metadata["error_details"][0]["category"] == "Network"
    assert (
        "Remote API timed out"
        in baseline.collection_metadata["error_details"][0]["error"]
    )


def test_base_collector_save_baseline(tmp_path: Path) -> None:
    """WHAT: Verifies that save_baseline serializes output to JSON on disk.

    WHY IT MATTERS:
    Baseline persistence is needed for downstream gap analysis and artifact archiving.
    """
    collector = MockWorkingCollector(subscription_id="sub-disk")
    baseline = collector.collect_all()

    dest_file = tmp_path / "artifacts" / "baseline.json"
    collector.save_baseline(baseline, str(dest_file))

    assert dest_file.exists()
    data = json.loads(dest_file.read_text(encoding="utf-8"))
    assert data["baseline_id"] == "baseline-azure-sub-disk"
    assert data["cloud_provider"] == "azure"
    assert len(data["controls"]) == 4
