"""Unit Test Suite for Azure Infrastructure Collector.

This module validates that AzureCollector interfaces with Azure Resource Manager APIs,
evaluates infrastructure security compliance, and handles API errors resiliently.
"""

from unittest.mock import MagicMock, patch
from azure.core.exceptions import AzureError, ClientAuthenticationError
import pytest

from src.collectors.azure_collector import AzureCollector
from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
)


@pytest.fixture
def mock_credential() -> MagicMock:
    """Fixture providing a mock Azure token credential."""
    cred = MagicMock()
    return cred


def test_azure_collector_cloud_provider(mock_credential: MagicMock) -> None:
    """WHAT: Verifies that cloud_provider property returns CloudProvider.AZURE.

    WHY IT MATTERS:
    Ensures multi-cloud dispatching correctly routes Azure workloads.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)
    assert collector.cloud_provider == CloudProvider.AZURE


def test_azure_collector_authentication_success(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Tests successful authentication and auto-discovery of subscription ID.

    WHY IT MATTERS:
    Enables zero-touch discovery of default subscription when none is explicitly provided.
    """
    with patch("src.collectors.azure_collector.SubscriptionClient") as mock_sub_cls:
        mock_sub_client = MagicMock()
        mock_sub = MagicMock()
        mock_sub.subscription_id = "auto-discovered-sub-456"
        mock_sub_client.subscriptions.list.return_value = [mock_sub]
        mock_sub_cls.return_value = mock_sub_client

        collector = AzureCollector(credential=mock_credential)
        assert collector.authenticate() is True
        assert collector.subscription_id == "auto-discovered-sub-456"


def test_azure_collector_authentication_empty_subscriptions(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Tests authentication failure when no active subscriptions are found.

    WHY IT MATTERS:
    Prevents empty baseline scans when credentials have no RBAC scope.
    """
    with patch("src.collectors.azure_collector.SubscriptionClient") as mock_sub_cls:
        mock_sub_client = MagicMock()
        mock_sub_client.subscriptions.list.return_value = []
        mock_sub_cls.return_value = mock_sub_client

        collector = AzureCollector(credential=mock_credential)
        assert collector.authenticate() is False


def test_azure_collector_authentication_client_auth_error(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Tests handling of ClientAuthenticationError.

    WHY IT MATTERS:
    Authentication failures should return False cleanly rather than bubbling uncaught exceptions.
    """
    with patch("src.collectors.azure_collector.SubscriptionClient") as mock_sub_cls:
        mock_sub_client = MagicMock()
        mock_sub_client.subscriptions.list.side_effect = ClientAuthenticationError("Invalid secret")
        mock_sub_cls.return_value = mock_sub_client

        collector = AzureCollector(credential=mock_credential)
        assert collector.authenticate() is False


def test_collect_iam_controls(mock_credential: MagicMock) -> None:
    """WHAT: Tests collection of managed identities from virtual machines.

    WHY IT MATTERS:
    Verifies that cloud workloads use managed identities instead of long-lived secrets.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    vm_compliant = MagicMock()
    vm_compliant.name = "vm-prod-web"
    vm_compliant.id = (
        "/subscriptions/sub-123/resourceGroups/rg-app/providers/"
        "Microsoft.Compute/virtualMachines/vm-prod-web"
    )
    vm_compliant.location = "westeurope"
    vm_compliant.identity = MagicMock()
    vm_compliant.identity.type = "SystemAssigned"
    vm_compliant.identity.principal_id = "principal-guid-111"

    vm_ignored = MagicMock()
    vm_ignored.name = "vm-legacy"
    vm_ignored.identity = None

    with patch.object(collector, "_get_compute_client") as mock_get_compute_client:
        mock_compute = MagicMock()
        mock_compute.virtual_machines.list_all.return_value = [
            vm_compliant,
            vm_ignored,
        ]
        mock_get_compute_client.return_value = mock_compute

        controls = collector.collect_iam_controls()
        assert len(controls) == 1
        assert controls[0].control_id == "azure-vm-managed-identity-vm-prod-web"
        assert controls[0].control_category == ControlCategory.IDENTITY_ACCESS
        assert controls[0].compliance_status == ComplianceStatus.COMPLIANT
        assert controls[0].current_state["identity_type"] == "SystemAssigned"


def test_collect_encryption_controls_storage_and_keyvault(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Tests storage account encryption, HTTPS enforcement, and Key Vault protection.

    WHY IT MATTERS:
    Directly satisfies GDPR Art. 32 and DORA ICT encryption verification.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    account = MagicMock()
    account.name = "stsecprod"
    account.id = (
        "/subscriptions/sub-123/resourceGroups/rg-sec/providers/"
        "Microsoft.Storage/storageAccounts/stsecprod"
    )
    account.location = "westeurope"
    account.sku.name = "Standard_GRS"
    account.kind = "StorageV2"
    account.enable_https_traffic_only = True

    account.encryption = MagicMock()
    account.encryption.services.blob.enabled = True
    account.encryption.services.file.enabled = True
    account.encryption.key_source = "Microsoft.Keyvault"
    account.encryption.require_infrastructure_encryption = True

    vault = MagicMock()
    vault.name = "kv-sec-prod"
    vault.id = (
        "/subscriptions/sub-123/resourceGroups/rg-sec/providers/"
        "Microsoft.KeyVault/vaults/kv-sec-prod"
    )
    vault.location = "westeurope"
    vault.properties.enable_soft_delete = True
    vault.properties.enable_purge_protection = True
    vault.properties.sku.name = "standard"

    with patch.object(collector, "_list_resource_groups", return_value=["rg-sec"]), patch.object(
        collector, "_get_storage_client"
    ) as mock_get_storage, patch.object(collector, "_get_keyvault_client") as mock_get_kv:
        mock_storage = MagicMock()
        mock_storage.storage_accounts.list_by_resource_group.return_value = [account]
        mock_get_storage.return_value = mock_storage

        mock_kv = MagicMock()
        mock_kv.vaults.list_by_resource_group.return_value = [vault]
        mock_get_kv.return_value = mock_kv

        controls = collector.collect_encryption_controls()
        assert len(controls) == 3

        storage_enc = next(c for c in controls if "encryption-stsecprod" in c.control_id)
        assert storage_enc.compliance_status == ComplianceStatus.COMPLIANT
        assert storage_enc.current_state["encryption_services"]["blob"] is True

        storage_https = next(c for c in controls if "https-stsecprod" in c.control_id)
        assert storage_https.compliance_status == ComplianceStatus.COMPLIANT

        kv_control = next(c for c in controls if "keyvault-protection" in c.control_id)
        assert kv_control.compliance_status == ComplianceStatus.COMPLIANT


def test_collect_network_controls_nsg_and_public_ip(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Tests NSG rule inspection and public IP exposure.

    WHY IT MATTERS:
    Maps to NIS2 Article 21 network perimeter defense.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    # Permissive NSG rule (non-compliant)
    nsg_rule = MagicMock()
    nsg_rule.name = "Allow-All-Inbound"
    nsg_rule.access = "Allow"
    nsg_rule.direction = "Inbound"
    nsg_rule.source_address_prefix = "*"
    nsg_rule.destination_port_range = "22"
    nsg_rule.protocol = "TCP"

    nsg = MagicMock()
    nsg.name = "nsg-prod"
    nsg.id = (
        "/subscriptions/sub-123/resourceGroups/rg-net/providers/"
        "Microsoft.Network/networkSecurityGroups/nsg-prod"
    )
    nsg.location = "westeurope"
    nsg.security_rules = [nsg_rule]

    public_ip = MagicMock()
    public_ip.name = "pip-gateway"
    public_ip.id = (
        "/subscriptions/sub-123/resourceGroups/rg-net/providers/"
        "Microsoft.Network/publicIPAddresses/pip-gateway"
    )
    public_ip.location = "westeurope"
    public_ip.ip_address = "20.50.100.200"
    public_ip.ip_configuration = MagicMock()
    public_ip.public_ip_allocation_method = "Static"
    public_ip.sku.name = "Standard"

    with patch.object(collector, "_list_resource_groups", return_value=["rg-net"]), patch.object(
        collector, "_get_network_client"
    ) as mock_get_network:
        mock_net = MagicMock()
        mock_net.network_security_groups.list.return_value = [nsg]
        mock_net.public_ip_addresses.list.return_value = [public_ip]
        mock_get_network.return_value = mock_net

        controls = collector.collect_network_controls()
        assert len(controls) == 2

        nsg_control = next(c for c in controls if "nsg-prod" in c.control_id)
        assert nsg_control.compliance_status == ComplianceStatus.NON_COMPLIANT
        assert nsg_control.current_state["risky_rules_count"] == 1

        pip_control = next(c for c in controls if "pip-gateway" in c.control_id)
        assert pip_control.current_state["is_associated"] is True


def test_collect_backup_controls_storage_redundancy(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Tests backup resilience verification through GRS storage accounts.

    WHY IT MATTERS:
    DORA Article 6 mandates geo-redundant backups for critical financial services.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    acc_grs = MagicMock()
    acc_grs.name = "stbackupgrs"
    acc_grs.id = (
        "/subscriptions/sub-123/resourceGroups/rg-bk/providers/"
        "Microsoft.Storage/storageAccounts/stbackupgrs"
    )
    acc_grs.location = "westeurope"
    acc_grs.sku.name = "Standard_GRS"

    acc_lrs = MagicMock()
    acc_lrs.name = "stlocallrs"
    acc_lrs.id = (
        "/subscriptions/sub-123/resourceGroups/rg-bk/providers/"
        "Microsoft.Storage/storageAccounts/stlocallrs"
    )
    acc_lrs.location = "westeurope"
    acc_lrs.sku.name = "Standard_LRS"

    with patch.object(collector, "_list_resource_groups", return_value=["rg-bk"]), patch.object(
        collector, "_get_storage_client"
    ) as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.storage_accounts.list_by_resource_group.return_value = [
            acc_grs,
            acc_lrs,
        ]
        mock_get_storage.return_value = mock_storage

        controls = collector.collect_backup_controls()
        assert len(controls) == 2

        grs_control = next(c for c in controls if "stbackupgrs" in c.control_id)
        assert grs_control.compliance_status == ComplianceStatus.COMPLIANT
        assert grs_control.current_state["is_geo_redundant"] is True

        lrs_control = next(c for c in controls if "stlocallrs" in c.control_id)
        assert lrs_control.compliance_status == ComplianceStatus.NON_COMPLIANT
        assert lrs_control.current_state["is_geo_redundant"] is False


def test_azure_collector_handles_azure_errors_gracefully(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Verifies that AzureError during API calls is logged without crashing.

    WHY IT MATTERS:
    Ensures network glitches or unauthorized resource groups do not crash the collection run.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    with patch.object(collector, "_get_compute_client") as mock_compute_client:
        mock_compute = MagicMock()
        mock_compute.virtual_machines.list_all.side_effect = AzureError("Access denied to compute")
        mock_compute_client.return_value = mock_compute

        controls = collector.collect_iam_controls()
        assert len(controls) == 0
        assert len(collector.errors) == 1
        assert collector.errors[0]["category"] == "IAM"
        assert "Access denied" in collector.errors[0]["error"]


def test_azure_collector_with_mock_data_file() -> None:
    """WHAT: Verifies full collection pipeline when using local mock JSON dataset.

    WHY IT MATTERS:
    Ensures zero-credential offline mode exercises all 4 control categories accurately.
    """
    mock_path = "data/mock_cloud_responses/azure_mock_response.json"
    collector = AzureCollector(mock_data_path=mock_path)

    baseline = collector.collect_all()
    assert len(baseline.controls) > 0

    categories = {c.control_category for c in baseline.controls}
    assert ControlCategory.IDENTITY_ACCESS in categories
    assert ControlCategory.ENCRYPTION in categories
    assert ControlCategory.NETWORK in categories
    assert ControlCategory.BACKUP_RECOVERY in categories


def test_azure_collector_ensure_authenticated_raises() -> None:
    """WHAT: Verifies _ensure_authenticated raises RuntimeError when unauthenticated.

    WHY IT MATTERS:
    Prevents unauthenticated calls to cloud SDK clients.
    """
    collector = AzureCollector()
    collector.credential = None
    collector.subscription_id = None

    with pytest.raises(RuntimeError, match="must be authenticated"):
        collector._ensure_authenticated()


def test_azure_collector_client_factories(mock_credential: MagicMock) -> None:
    """WHAT: Verifies client getter methods construct ARM management clients.

    WHY IT MATTERS:
    Validates lazy SDK client initialization with valid credentials.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    with patch("src.collectors.azure_collector.StorageManagementClient") as mock_st, patch(
        "src.collectors.azure_collector.NetworkManagementClient"
    ) as mock_net, patch(
        "src.collectors.azure_collector.ComputeManagementClient"
    ) as mock_comp, patch(
        "src.collectors.azure_collector.KeyVaultManagementClient"
    ) as mock_kv:
        collector._get_storage_client()
        mock_st.assert_called_once_with(mock_credential, "sub-123")

        collector._get_network_client()
        mock_net.assert_called_once_with(mock_credential, "sub-123")

        collector._get_compute_client()
        mock_comp.assert_called_once_with(mock_credential, "sub-123")

        collector._get_keyvault_client()
        mock_kv.assert_called_once_with(mock_credential, "sub-123")


def test_azure_collector_unexpected_auth_exception(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Verifies unexpected exceptions during authentication return False.

    WHY IT MATTERS:
    Ensures network/OS-level aborts do not crash the orchestrator.
    """
    with patch("src.collectors.azure_collector.SubscriptionClient") as mock_sub_cls:
        mock_sub_cls.side_effect = RuntimeError("OS socket failure")

        collector = AzureCollector(credential=mock_credential)
        assert collector.authenticate() is False


def test_azure_collector_catches_generic_exceptions_in_categories(
    mock_credential: MagicMock,
) -> None:
    """WHAT: Verifies that generic Exception in collection categories is logged without crashing.

    WHY IT MATTERS:
    Ensures transient Python exceptions in one category do not abort the baseline run.
    """
    collector = AzureCollector(subscription_id="sub-123", credential=mock_credential)

    with patch.object(collector, "_get_compute_client") as mock_comp:
        mock_comp.side_effect = TypeError("Unexpected data structure")
        iam_controls = collector.collect_iam_controls()
        assert iam_controls == []
        assert any(e["category"] == "IAM" for e in collector.errors)

    with patch.object(collector, "_get_storage_client") as mock_st:
        mock_st.side_effect = TypeError("Storage error")
        enc_controls = collector.collect_encryption_controls()
        assert enc_controls == []
        assert any(e["category"] == "Encryption" for e in collector.errors)

    with patch.object(collector, "_get_network_client") as mock_net:
        mock_net.side_effect = TypeError("Network error")
        net_controls = collector.collect_network_controls()
        assert net_controls == []
        assert any(e["category"] == "Network" for e in collector.errors)

    with patch.object(collector, "_get_storage_client") as mock_bk:
        mock_bk.side_effect = TypeError("Backup error")
        bk_controls = collector.collect_backup_controls()
        assert bk_controls == []
        assert any(e["category"] == "Backup" for e in collector.errors)
