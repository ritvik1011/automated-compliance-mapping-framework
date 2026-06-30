"""Tests for the cloud infrastructure collectors.

These tests use mocked cloud responses to verify the collectors
work correctly without requiring real cloud credentials.
"""

import json
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch
import pytest

from src.collectors.azure_collector import AzureCollector
from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    InfrastructureBaseline,
    TechnicalControl,
)


@pytest.fixture
def mock_azure_credentials() -> Generator[MagicMock, None, None]:
    """Mock Azure credentials."""
    with patch("src.collectors.azure_collector.DefaultAzureCredential") as mock_cred:
        mock_instance = MagicMock()
        mock_cred.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_subscription_client() -> Generator[MagicMock, None, None]:
    """Mock Azure SubscriptionClient."""
    with patch("src.collectors.azure_collector.SubscriptionClient") as mock_client:
        mock_instance = MagicMock()
        mock_subscription = MagicMock()
        mock_subscription.subscription_id = "test-sub-id"
        mock_instance.subscriptions.list.return_value = [mock_subscription]
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def azure_collector(
    mock_azure_credentials: MagicMock, mock_subscription_client: MagicMock
) -> AzureCollector:
    """Create an AzureCollector with mocked credentials."""
    collector = AzureCollector(subscription_id="test-sub-id")
    collector.credential = mock_azure_credentials
    return collector


def test_azure_collector_cloud_provider(
    azure_collector: AzureCollector,
) -> None:
    """Test that AzureCollector reports correct cloud provider."""
    assert azure_collector.cloud_provider == CloudProvider.AZURE


def test_azure_collector_authenticate_success(
    azure_collector: AzureCollector, mock_subscription_client: MagicMock
) -> None:
    """Test successful authentication."""
    result = azure_collector.authenticate()
    assert result is True


def test_azure_collector_authentication_failure(
    mock_azure_credentials: MagicMock,
) -> None:
    """Test authentication failure handling."""
    from azure.core.exceptions import ClientAuthenticationError

    with patch("src.collectors.azure_collector.SubscriptionClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.subscriptions.list.side_effect = ClientAuthenticationError("Auth failed")
        mock_client.return_value = mock_instance

        collector = AzureCollector()
        collector.credential = mock_azure_credentials
        result = collector.authenticate()

        assert result is False


def test_collect_encryption_controls_compliant_storage(
    azure_collector: AzureCollector,
) -> None:
    """Test collection of encryption controls for compliant storage."""
    mock_storage_client = MagicMock()

    mock_account = MagicMock()
    mock_account.id = (
        "/subscriptions/test/resourceGroups/rg-test/providers/"
        "Microsoft.Storage/storageAccounts/test1"
    )
    mock_account.name = "test1"
    mock_account.location = "westeurope"
    mock_account.sku.name = "Standard_GRS"
    mock_account.kind = "StorageV2"
    mock_account.enable_https_traffic_only = True
    mock_account.encryption.services.blob.enabled = True
    mock_account.encryption.services.file.enabled = True
    mock_account.encryption.key_source = "Microsoft.Storage"
    mock_account.encryption.require_infrastructure_encryption = True

    mock_storage_client.storage_accounts.list_by_resource_group.return_value = [mock_account]

    with (
        patch.object(azure_collector, "_get_storage_client", return_value=mock_storage_client),
        patch.object(azure_collector, "_list_resource_groups", return_value=["rg-test"]),
        patch.object(
            azure_collector,
            "_collect_keyvault_encryption_controls",
            return_value=[],
        ),
    ):
        controls = azure_collector.collect_encryption_controls()

    assert len(controls) >= 1
    encryption_control = next(c for c in controls if "encryption" in c.control_id)
    assert encryption_control.compliance_status == ComplianceStatus.COMPLIANT


def test_collect_network_controls_detects_risky_rules(
    azure_collector: AzureCollector,
) -> None:
    """Test that network collection detects risky NSG rules."""
    mock_network_client = MagicMock()

    # Create a mock NSG with a risky rule (allows all inbound)
    mock_nsg = MagicMock()
    mock_nsg.id = (
        "/subscriptions/test/resourceGroups/rg-test/providers/"
        "Microsoft.Network/networkSecurityGroups/nsg-test"
    )
    mock_nsg.name = "nsg-test"
    mock_nsg.location = "westeurope"

    mock_rule = MagicMock()
    mock_rule.name = "AllowAll"
    mock_rule.access = "Allow"
    mock_rule.direction = "Inbound"
    mock_rule.source_address_prefix = "*"
    mock_rule.destination_port_range = "*"
    mock_rule.protocol = "*"

    mock_nsg.security_rules = [mock_rule]
    mock_network_client.network_security_groups.list.return_value = [mock_nsg]
    mock_network_client.public_ip_addresses.list.return_value = []

    with (
        patch.object(azure_collector, "_get_network_client", return_value=mock_network_client),
        patch.object(azure_collector, "_list_resource_groups", return_value=["rg-test"]),
    ):
        controls = azure_collector.collect_network_controls()

    assert len(controls) >= 1
    nsg_control = next(c for c in controls if "nsg" in c.control_id)
    assert nsg_control.compliance_status == ComplianceStatus.NON_COMPLIANT
    assert nsg_control.current_state["risky_rules_count"] > 0


def test_collect_backup_controls_geo_redundant(
    azure_collector: AzureCollector,
) -> None:
    """Test that geo-redundant storage is marked as compliant."""
    mock_storage_client = MagicMock()

    mock_account = MagicMock()
    mock_account.id = (
        "/subscriptions/test/resourceGroups/rg-test/providers/"
        "Microsoft.Storage/storageAccounts/backup1"
    )
    mock_account.name = "backup1"
    mock_account.location = "westeurope"
    mock_account.sku.name = "Standard_GRS"

    mock_storage_client.storage_accounts.list_by_resource_group.return_value = [mock_account]

    with (
        patch.object(azure_collector, "_get_storage_client", return_value=mock_storage_client),
        patch.object(azure_collector, "_list_resource_groups", return_value=["rg-test"]),
    ):
        controls = azure_collector.collect_backup_controls()

    assert len(controls) >= 1
    backup_control = controls[0]
    assert backup_control.compliance_status == ComplianceStatus.COMPLIANT
    assert backup_control.control_category == ControlCategory.BACKUP_RECOVERY


def test_baseline_save_and_load(azure_collector: AzureCollector, tmp_path: Path) -> None:
    """Test saving and loading a baseline."""
    control = TechnicalControl(
        control_id="test-control-1",
        control_category=ControlCategory.ENCRYPTION,
        cloud_provider=CloudProvider.AZURE,
        resource_type="StorageAccount",
        resource_id="/subscriptions/test/resource",
        resource_name="test-storage",
        control_description="Test control",
        current_state={"encryption": True},
        compliance_status=ComplianceStatus.COMPLIANT,
    )

    baseline = InfrastructureBaseline(
        baseline_id="test-baseline",
        cloud_provider=CloudProvider.AZURE,
        subscription_id="test-sub",
        total_resources_scanned=1,
        controls=[control],
    )

    output_path = tmp_path / "test_baseline.json"
    azure_collector.save_baseline(baseline, str(output_path))

    assert output_path.exists()

    with open(output_path, encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data["baseline_id"] == "test-baseline"
    assert len(loaded_data["controls"]) == 1
    assert loaded_data["controls"][0]["control_id"] == "test-control-1"
