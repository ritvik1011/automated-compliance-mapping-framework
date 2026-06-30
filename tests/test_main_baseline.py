"""Unit Test Suite for Main Baseline CLI Orchestrator.

This module validates CLI argument handling, Rich table visualizations,
and end-to-end baseline collection execution workflows.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.main_baseline import main, print_baseline_summary
from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    InfrastructureBaseline,
    TechnicalControl,
)


@pytest.fixture
def mock_baseline() -> InfrastructureBaseline:
    """Fixture providing an infrastructure baseline with diverse statuses."""
    c1 = TechnicalControl(
        control_id="azure-storage-enc-01",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AZURE,
        resource_type="StorageAccount",
        resource_id="/sub/rg/storage1",
        resource_name="storage1",
        control_description="Storage encryption",
        compliance_status=ComplianceStatus.COMPLIANT,
    )
    c2 = TechnicalControl(
        control_id="azure-nsg-01",
        control_category=ControlCategory.NETWORK,
        cloud_provider=CloudProvider.AZURE,
        resource_type="NetworkSecurityGroup",
        resource_id="/sub/rg/nsg1",
        resource_name="nsg1",
        control_description="Port 22 closed",
        compliance_status=ComplianceStatus.NON_COMPLIANT,
    )
    c3 = TechnicalControl(
        control_id="azure-backup-01",
        control_category=ControlCategory.BACKUP_RECOVERY,
        cloud_provider=CloudProvider.AZURE,
        resource_type="BackupVault",
        resource_id="/sub/rg/vault1",
        resource_name="vault1",
        control_description="Daily backup",
        compliance_status=ComplianceStatus.PARTIAL,
    )

    return InfrastructureBaseline(
        baseline_id="baseline-azure-test",
        cloud_provider=CloudProvider.AZURE,
        subscription_id="sub-abc",
        total_resources_scanned=3,
        controls=[c1, c2, c3],
        collection_metadata={
            "errors_encountered": 1,
            "error_details": [{"category": "IAM", "error": "Access denied"}],
        },
    )


def test_print_baseline_summary_renders(
    mock_baseline: InfrastructureBaseline,
) -> None:
    """WHAT: Verifies that print_baseline_summary prints without error.

    WHY IT MATTERS:
    Ensures Rich tables, compliance percentages, and error reports render cleanly.
    """
    print_baseline_summary(mock_baseline)


def test_main_baseline_azure_happy_path(
    mock_baseline: InfrastructureBaseline, tmp_path: Path
) -> None:
    """WHAT: Tests main baseline CLI entry point with Azure provider and OSCAL output.

    WHY IT MATTERS:
    Ensures end-to-end execution coordinates collection, baseline serialization, and OSCAL export.
    """
    out_baseline = tmp_path / "baselines" / "azure_baseline.json"
    out_oscal = tmp_path / "baselines" / "oscal_component.json"

    with patch("src.main_baseline.AzureCollector") as mock_collector_cls:
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = mock_baseline
        mock_collector_cls.return_value = mock_collector

        argv = [
            "--provider",
            "azure",
            "--subscription",
            "sub-abc",
            "--output",
            str(out_baseline),
            "--oscal-output",
            str(out_oscal),
            "--verbose",
        ]

        exit_code = main(argv)
        assert exit_code == 0
        mock_collector.save_baseline.assert_called_once_with(mock_baseline, str(out_baseline))
        assert out_oscal.exists()


def test_main_baseline_unsupported_provider() -> None:
    """WHAT: Tests main baseline handling for AWS (unimplemented) provider.

    WHY IT MATTERS:
    Ensures graceful error reporting and non-zero exit code when provider is not ready.
    """
    exit_code = main(["--provider", "aws"])
    assert exit_code == 1


def test_main_baseline_collection_failure() -> None:
    """WHAT: Tests error handling when collector raises an exception.

    WHY IT MATTERS:
    Ensures crashes in collector are cleanly caught and exit with code 1.
    """
    with patch("src.main_baseline.AzureCollector") as mock_collector_cls:
        mock_collector = MagicMock()
        mock_collector.collect_all.side_effect = RuntimeError("Authentication failed")
        mock_collector_cls.return_value = mock_collector

        exit_code = main(["--provider", "azure"])
        assert exit_code == 1


def test_main_baseline_keyboard_interrupt() -> None:
    """WHAT: Tests handling of user Ctrl+C cancellation.

    WHY IT MATTERS:
    Ensures CLI halts cleanly on user interrupt.
    """
    with patch("src.main_baseline.AzureCollector") as mock_collector_cls:
        mock_collector = MagicMock()
        mock_collector.collect_all.side_effect = KeyboardInterrupt()
        mock_collector_cls.return_value = mock_collector

        exit_code = main(["--provider", "azure"])
        assert exit_code == 1
