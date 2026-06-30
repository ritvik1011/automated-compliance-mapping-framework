"""Azure Infrastructure Collector.

This module implements the BaseCollector for Microsoft Azure environments.
It uses the Azure SDK for Python to extract security-relevant configurations
from Azure resources, with support for offline mock data execution.

Research Context:
    This collector focuses on controls relevant to GDPR Article 32
    (security of processing), DORA (ICT risk management), and NIS2
    (essential entity requirements). The collected data forms the
    "As-Is" baseline for automated compliance gap analysis.

Prerequisites:
    - Azure subscription with appropriate read permissions
    - Authentication via one of:
      * Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
      * Azure CLI (az login)
      * Managed Identity (when running in Azure)
      * Mock response JSON (for local offline development and CI)
"""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from azure.core.exceptions import AzureError, ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.network import NetworkManagementClient

try:
    from azure.mgmt.subscription import SubscriptionClient  # type: ignore[import-untyped]
except ImportError:
    try:
        from azure.mgmt.resource.subscriptions import (  # type: ignore[import-untyped,no-redef]
            SubscriptionClient,
        )
    except ImportError:
        try:
            from azure.mgmt.resource import (  # type: ignore[import-untyped,no-redef]
                SubscriptionClient,
            )
        except ImportError:
            SubscriptionClient = None  # type: ignore[assignment,misc]

from azure.mgmt.storage import StorageManagementClient

from src.collectors.base_collector import BaseCollector
from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    TechnicalControl,
)

logger = logging.getLogger(__name__)


def _dict_to_obj(d: Any) -> Any:
    """Recursively convert nested dicts into SimpleNamespace objects."""
    if isinstance(d, dict):
        return SimpleNamespace(**{k: _dict_to_obj(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [_dict_to_obj(i) for i in d]
    return d


class AzureCollector(BaseCollector):
    """Collector for Microsoft Azure infrastructure.

    Extracts security-relevant configurations from Azure resources
    and converts them into TechnicalControl objects.

    Example:
        collector = AzureCollector(subscription_id="xxx-xxx-xxx")
        baseline = collector.collect_all()
        collector.save_baseline(baseline, "baselines/azure_baseline.json")
    """

    def __init__(
        self,
        subscription_id: Optional[str] = None,
        region: Optional[str] = None,
        credential: Optional[Any] = None,
        mock_data_path: Optional[str] = None,
    ) -> None:
        """Initialize the Azure collector.

        Args:
            subscription_id: Azure subscription ID to scan
            region: Optional region filter (e.g., "westeurope")
            credential: Optional pre-configured credential object
            mock_data_path: Optional path to mock JSON response file for offline operation
        """
        super().__init__(subscription_id=subscription_id, region=region)
        self.credential = credential
        self._clients_initialized = False
        self.mock_data: Optional[Any] = None
        if mock_data_path:
            p = Path(mock_data_path)
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    self.mock_data = _dict_to_obj(json.load(f))
                logger.info(f"Loaded mock cloud response from {mock_data_path}")

    @property
    def cloud_provider(self) -> CloudProvider:
        """Return Azure as cloud provider."""
        return CloudProvider.AZURE

    def authenticate(self) -> bool:
        """Authenticate with Azure using DefaultAzureCredential or mock data.

        Returns:
            True if authentication successful
        """
        if self.mock_data is not None:
            if self.subscription_id is None:
                self.subscription_id = "test-sub"
            self._clients_initialized = True
            logger.info(f"Using mock data for subscription: {self.subscription_id}")
            return True

        try:
            if self.credential is None:
                self.credential = DefaultAzureCredential()

            if SubscriptionClient is None:
                logger.error("SubscriptionClient is not available in environment")
                return False

            # Test the credential by listing subscriptions
            subscription_client = SubscriptionClient(self.credential)
            subscriptions = list(subscription_client.subscriptions.list())

            if not subscriptions:
                logger.error("No Azure subscriptions found for the authenticated identity")
                return False

            # If no subscription specified, use the first one
            if self.subscription_id is None and subscriptions:
                self.subscription_id = subscriptions[0].subscription_id
                logger.info(f"Using default subscription: {self.subscription_id}")

            self._clients_initialized = True
            logger.info(
                f"Successfully authenticated to Azure. Subscription: {self.subscription_id}"
            )
            return True

        except ClientAuthenticationError as e:
            logger.error(f"Azure authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Azure authentication: {e}")
            return False

    def _ensure_authenticated(self) -> tuple[Any, str]:
        """Ensure credential and subscription_id are available."""
        if self.credential is None or self.subscription_id is None:
            raise RuntimeError("AzureCollector must be authenticated before accessing clients.")
        return self.credential, self.subscription_id

    def _get_storage_client(self) -> StorageManagementClient:
        """Get an authenticated Storage Management client."""
        cred, sub_id = self._ensure_authenticated()
        return StorageManagementClient(cred, sub_id)

    def _get_network_client(self) -> NetworkManagementClient:
        """Get an authenticated Network Management client."""
        cred, sub_id = self._ensure_authenticated()
        return NetworkManagementClient(cred, sub_id)

    def _get_compute_client(self) -> ComputeManagementClient:
        """Get an authenticated Compute Management client."""
        cred, sub_id = self._ensure_authenticated()
        return ComputeManagementClient(cred, sub_id)

    def _get_keyvault_client(self) -> KeyVaultManagementClient:
        """Get an authenticated Key Vault Management client."""
        cred, sub_id = self._ensure_authenticated()
        return KeyVaultManagementClient(cred, sub_id)

    def _fallback_id(self, resource_type: str, resource_group: str, resource_name: str) -> str:
        """Construct fallback ARM resource ID if not provided by SDK object."""
        return (
            f"/subscriptions/{self.subscription_id}/resourceGroups/"
            f"{resource_group}/providers/{resource_type}/{resource_name}"
        )

    # =========================================================================
    # IAM CONTROLS
    # =========================================================================

    def collect_iam_controls(self) -> List[TechnicalControl]:
        """Collect IAM controls from Azure."""
        controls: List[TechnicalControl] = []

        try:
            if self.mock_data and hasattr(self.mock_data, "virtual_machines"):
                vms = self.mock_data.virtual_machines
            else:
                compute_client = self._get_compute_client()
                vms = list(compute_client.virtual_machines.list_all())

            for vm in vms:
                identity = getattr(vm, "identity", None)
                id_type = getattr(identity, "type", "None") if identity else "None"
                if identity and id_type != "None":
                    vm_name = getattr(vm, "name", "unknown-vm") or "unknown-vm"
                    vm_id = getattr(vm, "id", None) or self._fallback_id(
                        "Microsoft.Compute/virtualMachines", "unknown", vm_name
                    )
                    rg_name = vm_id.split("/")[4] if len(vm_id.split("/")) > 4 else "unknown-rg"

                    control = TechnicalControl(
                        control_id=f"azure-vm-managed-identity-{vm_name}",
                        control_category=ControlCategory.IDENTITY_ACCESS,
                        cloud_provider=CloudProvider.AZURE,
                        resource_type="VirtualMachine",
                        resource_id=vm_id,
                        resource_name=vm_name,
                        control_description="VM has managed identity configured",
                        current_state={
                            "identity_type": id_type,
                            "principal_id": getattr(identity, "principal_id", "None"),
                        },
                        compliance_status=ComplianceStatus.COMPLIANT,
                        metadata={
                            "location": getattr(vm, "location", "westeurope"),
                            "resource_group": rg_name,
                        },
                    )
                    controls.append(control)

            logger.info(f"Collected {len(controls)} IAM controls from Azure")

        except AzureError as e:
            logger.error(f"Azure error during IAM collection: {e}")
            self.errors.append({"category": "IAM", "error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error during IAM collection: {e}")
            self.errors.append({"category": "IAM", "error": str(e)})

        return controls

    # =========================================================================
    # ENCRYPTION CONTROLS
    # =========================================================================

    def collect_encryption_controls(self) -> List[TechnicalControl]:
        """Collect encryption controls from Azure."""
        controls: List[TechnicalControl] = []

        try:
            if self.mock_data and hasattr(self.mock_data, "storage_accounts"):
                for account in self.mock_data.storage_accounts:
                    rg = (
                        account.id.split("/")[4]
                        if hasattr(account, "id") and len(account.id.split("/")) > 4
                        else "rg-test"
                    )
                    encryption_status = self._check_storage_encryption(account)
                    acc_name = getattr(account, "name", "unknown-storage") or "unknown-storage"
                    acc_id = getattr(account, "id", None) or self._fallback_id(
                        "Microsoft.Storage/storageAccounts", rg, acc_name
                    )

                    control = TechnicalControl(
                        control_id=f"azure-storage-encryption-{acc_name}",
                        control_category=ControlCategory.ENCRYPTION,
                        cloud_provider=CloudProvider.AZURE,
                        resource_type="StorageAccount",
                        resource_id=acc_id,
                        resource_name=acc_name,
                        control_description="Storage account encryption at rest status",
                        current_state=encryption_status,
                        compliance_status=self._evaluate_encryption_compliance(encryption_status),
                        metadata={
                            "location": getattr(account, "location", "westeurope"),
                            "resource_group": rg,
                            "sku": (
                                account.sku.name
                                if hasattr(account, "sku") and account.sku
                                else "unknown"
                            ),
                            "kind": getattr(account, "kind", "StorageV2"),
                        },
                    )
                    controls.append(control)

                    https_control = self._create_https_control(account, rg)
                    if https_control:
                        controls.append(https_control)
            else:
                storage_client = self._get_storage_client()
                for rg in self._list_resource_groups():
                    for account in storage_client.storage_accounts.list_by_resource_group(rg):
                        encryption_status = self._check_storage_encryption(account)
                        acc_name = account.name or "unknown-storage"
                        acc_id = account.id or self._fallback_id(
                            "Microsoft.Storage/storageAccounts", rg, acc_name
                        )

                        control = TechnicalControl(
                            control_id=f"azure-storage-encryption-{acc_name}",
                            control_category=ControlCategory.ENCRYPTION,
                            cloud_provider=CloudProvider.AZURE,
                            resource_type="StorageAccount",
                            resource_id=acc_id,
                            resource_name=acc_name,
                            control_description="Storage account encryption at rest status",
                            current_state=encryption_status,
                            compliance_status=self._evaluate_encryption_compliance(
                                encryption_status
                            ),
                            metadata={
                                "location": account.location,
                                "resource_group": rg,
                                "sku": (account.sku.name if account.sku else "unknown"),
                                "kind": account.kind,
                            },
                        )
                        controls.append(control)

                        https_control = self._create_https_control(account, rg)
                        if https_control:
                            controls.append(https_control)

            keyvault_controls = self._collect_keyvault_encryption_controls()
            controls.extend(keyvault_controls)

            logger.info(f"Collected {len(controls)} encryption controls from Azure")

        except AzureError as e:
            logger.error(f"Azure error during encryption collection: {e}")
            self.errors.append({"category": "Encryption", "error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error during encryption collection: {e}")
            self.errors.append({"category": "Encryption", "error": str(e)})

        return controls

    def _list_resource_groups(self) -> List[str]:
        """List all resource groups in the subscription."""
        from azure.mgmt.resource import (  # type: ignore[import-untyped]
            ResourceManagementClient,
        )

        cred, sub_id = self._ensure_authenticated()
        resource_client = ResourceManagementClient(cred, sub_id)
        return [rg.name for rg in resource_client.resource_groups.list()]

    def _check_storage_encryption(self, account: Any) -> Dict[str, Any]:
        """Check encryption status of a storage account."""
        encryption = getattr(account, "encryption", None)
        services = getattr(encryption, "services", None) if encryption else None
        blob = getattr(services, "blob", None) if services else None
        file_srv = getattr(services, "file", None) if services else None

        has_blob = getattr(blob, "enabled", False) if blob else False
        has_file = getattr(file_srv, "enabled", False) if file_srv else False

        return {
            "encryption_services": {
                "blob": has_blob,
                "file": has_file,
            },
            "encryption_key_source": (
                getattr(encryption, "key_source", "unknown") if encryption else "unknown"
            ),
            "require_infrastructure_encryption": (
                getattr(encryption, "require_infrastructure_encryption", False)
                if encryption
                else False
            ),
        }

    def _evaluate_encryption_compliance(
        self, encryption_status: Dict[str, Any]
    ) -> ComplianceStatus:
        """Evaluate whether encryption status meets baseline expectations."""
        services = encryption_status.get("encryption_services", {})

        if all(services.values()):
            return ComplianceStatus.COMPLIANT
        elif any(services.values()):
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _create_https_control(
        self, account: Any, resource_group: str
    ) -> Optional[TechnicalControl]:
        """Create a control for HTTPS enforcement on a storage account."""
        https_enabled = getattr(account, "enable_https_traffic_only", False)
        acc_name = getattr(account, "name", "unknown-storage") or "unknown-storage"
        acc_id = getattr(account, "id", None) or self._fallback_id(
            "Microsoft.Storage/storageAccounts", resource_group, acc_name
        )

        return TechnicalControl(
            control_id=f"azure-storage-https-{acc_name}",
            control_category=ControlCategory.ENCRYPTION,
            cloud_provider=CloudProvider.AZURE,
            resource_type="StorageAccount",
            resource_id=acc_id,
            resource_name=acc_name,
            control_description="Storage account enforces HTTPS-only traffic",
            current_state={
                "https_only": https_enabled,
            },
            compliance_status=(
                ComplianceStatus.COMPLIANT if https_enabled else ComplianceStatus.NON_COMPLIANT
            ),
            metadata={
                "location": getattr(account, "location", "westeurope"),
                "resource_group": resource_group,
            },
        )

    def _collect_keyvault_encryption_controls(self) -> List[TechnicalControl]:
        """Collect encryption controls from Azure Key Vault."""
        controls: List[TechnicalControl] = []

        try:
            if self.mock_data and hasattr(self.mock_data, "key_vaults"):
                for vault in self.mock_data.key_vaults:
                    rg = (
                        vault.id.split("/")[4]
                        if hasattr(vault, "id") and len(vault.id.split("/")) > 4
                        else "rg-test"
                    )
                    properties = getattr(vault, "properties", None)
                    soft_delete = (
                        getattr(properties, "enable_soft_delete", True) if properties else True
                    )
                    purge_protection = (
                        getattr(properties, "enable_purge_protection", False)
                        if properties
                        else False
                    )

                    compliance = (
                        ComplianceStatus.COMPLIANT
                        if soft_delete and purge_protection
                        else (
                            ComplianceStatus.PARTIAL
                            if soft_delete
                            else ComplianceStatus.NON_COMPLIANT
                        )
                    )

                    vault_name = getattr(vault, "name", "unknown-vault") or "unknown-vault"
                    vault_id = getattr(vault, "id", None) or self._fallback_id(
                        "Microsoft.KeyVault/vaults", rg, vault_name
                    )

                    sku_name = "unknown"
                    if properties and hasattr(properties, "sku") and properties.sku:
                        sku_name = getattr(properties.sku, "name", "unknown")

                    control = TechnicalControl(
                        control_id=f"azure-keyvault-protection-{vault_name}",
                        control_category=ControlCategory.ENCRYPTION,
                        cloud_provider=CloudProvider.AZURE,
                        resource_type="KeyVault",
                        resource_id=vault_id,
                        resource_name=vault_name,
                        control_description=(
                            "Key Vault protection settings (soft-delete, purge protection)"
                        ),
                        current_state={
                            "soft_delete_enabled": soft_delete,
                            "purge_protection_enabled": purge_protection,
                            "sku": sku_name,
                        },
                        compliance_status=compliance,
                        metadata={
                            "location": getattr(vault, "location", "westeurope"),
                            "resource_group": rg,
                        },
                    )
                    controls.append(control)
            else:
                kv_client = self._get_keyvault_client()
                for rg in self._list_resource_groups():
                    for vault in kv_client.vaults.list_by_resource_group(rg):
                        properties = vault.properties
                        soft_delete = properties.enable_soft_delete if properties else True
                        purge_protection = (
                            properties.enable_purge_protection if properties else False
                        )

                        compliance = (
                            ComplianceStatus.COMPLIANT
                            if soft_delete and purge_protection
                            else (
                                ComplianceStatus.PARTIAL
                                if soft_delete
                                else ComplianceStatus.NON_COMPLIANT
                            )
                        )

                        vault_name = vault.name or "unknown-vault"
                        vault_id = vault.id or self._fallback_id(
                            "Microsoft.KeyVault/vaults", rg, vault_name
                        )

                        control = TechnicalControl(
                            control_id=f"azure-keyvault-protection-{vault_name}",
                            control_category=ControlCategory.ENCRYPTION,
                            cloud_provider=CloudProvider.AZURE,
                            resource_type="KeyVault",
                            resource_id=vault_id,
                            resource_name=vault_name,
                            control_description=(
                                "Key Vault protection settings (soft-delete, purge protection)"
                            ),
                            current_state={
                                "soft_delete_enabled": soft_delete,
                                "purge_protection_enabled": purge_protection,
                                "sku": (
                                    properties.sku.name
                                    if properties and properties.sku
                                    else "unknown"
                                ),
                            },
                            compliance_status=compliance,
                            metadata={
                                "location": vault.location,
                                "resource_group": rg,
                            },
                        )
                        controls.append(control)

        except Exception as e:
            logger.error(f"Error collecting Key Vault controls: {e}")
            self.errors.append({"category": "KeyVault", "error": str(e)})

        return controls

    # =========================================================================
    # NETWORK CONTROLS
    # =========================================================================

    def collect_network_controls(self) -> List[TechnicalControl]:
        """Collect network security controls from Azure."""
        controls: List[TechnicalControl] = []

        try:
            if self.mock_data and hasattr(self.mock_data, "network_security_groups"):
                for nsg in self.mock_data.network_security_groups:
                    rg = (
                        nsg.id.split("/")[4]
                        if hasattr(nsg, "id") and len(nsg.id.split("/")) > 4
                        else "rg-test"
                    )
                    controls.append(self._analyze_nsg(nsg, rg))
            else:
                network_client = self._get_network_client()
                for rg in self._list_resource_groups():
                    for nsg in network_client.network_security_groups.list(rg):
                        nsg_control = self._analyze_nsg(nsg, rg)
                        controls.append(nsg_control)

                    for public_ip in network_client.public_ip_addresses.list(rg):
                        pip_control = self._analyze_public_ip(public_ip, rg)
                        controls.append(pip_control)

            logger.info(f"Collected {len(controls)} network controls from Azure")

        except AzureError as e:
            logger.error(f"Azure error during network collection: {e}")
            self.errors.append({"category": "Network", "error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error during network collection: {e}")
            self.errors.append({"category": "Network", "error": str(e)})

        return controls

    def _analyze_nsg(self, nsg: Any, resource_group: str) -> TechnicalControl:
        """Analyze a Network Security Group for risky rules."""
        risky_rules: List[Dict[str, Any]] = []
        total_rules = 0

        rules = getattr(nsg, "security_rules", []) or []
        for rule in rules:
            total_rules += 1
            access = getattr(rule, "access", "")
            direction = getattr(rule, "direction", "")
            src_prefix = getattr(rule, "source_address_prefix", "")

            if (
                access == "Allow"
                and direction == "Inbound"
                and src_prefix in ["*", "Internet", "0.0.0.0/0"]
            ):
                risky_rules.append(
                    {
                        "rule_name": getattr(rule, "name", "rule"),
                        "destination_port": getattr(rule, "destination_port_range", "*"),
                        "protocol": getattr(rule, "protocol", "*"),
                    }
                )

        nsg_name = getattr(nsg, "name", "unknown-nsg") or "unknown-nsg"
        nsg_id = getattr(nsg, "id", None) or self._fallback_id(
            "Microsoft.Network/networkSecurityGroups", resource_group, nsg_name
        )

        return TechnicalControl(
            control_id=f"azure-nsg-{nsg_name}",
            control_category=ControlCategory.NETWORK,
            cloud_provider=CloudProvider.AZURE,
            resource_type="NetworkSecurityGroup",
            resource_id=nsg_id,
            resource_name=nsg_name,
            control_description="Network Security Group rule analysis",
            current_state={
                "total_rules": total_rules,
                "risky_rules_count": len(risky_rules),
                "risky_rules": risky_rules,
                "location": getattr(nsg, "location", "westeurope"),
            },
            compliance_status=(
                ComplianceStatus.COMPLIANT
                if len(risky_rules) == 0
                else ComplianceStatus.NON_COMPLIANT
            ),
            metadata={
                "resource_group": resource_group,
                "location": getattr(nsg, "location", "westeurope"),
            },
        )

    def _analyze_public_ip(self, public_ip: Any, resource_group: str) -> TechnicalControl:
        """Analyze a Public IP address for exposure risks."""
        is_associated = getattr(public_ip, "ip_configuration", None) is not None
        pip_name = getattr(public_ip, "name", "unknown-pip") or "unknown-pip"
        pip_id = getattr(public_ip, "id", None) or self._fallback_id(
            "Microsoft.Network/publicIPAddresses", resource_group, pip_name
        )

        sku = getattr(public_ip, "sku", None)
        sku_name = getattr(sku, "name", "Basic") if sku else "Basic"

        return TechnicalControl(
            control_id=f"azure-publicip-{pip_name}",
            control_category=ControlCategory.NETWORK,
            cloud_provider=CloudProvider.AZURE,
            resource_type="PublicIPAddress",
            resource_id=pip_id,
            resource_name=pip_name,
            control_description="Public IP address exposure analysis",
            current_state={
                "ip_address": getattr(public_ip, "ip_address", "unknown"),
                "is_associated": is_associated,
                "allocation_method": getattr(public_ip, "public_ip_allocation_method", "Dynamic"),
                "sku": sku_name,
            },
            compliance_status=ComplianceStatus.UNKNOWN,
            metadata={
                "resource_group": resource_group,
                "location": getattr(public_ip, "location", "westeurope"),
            },
        )

    # =========================================================================
    # BACKUP CONTROLS
    # =========================================================================

    def collect_backup_controls(self) -> List[TechnicalControl]:
        """Collect backup and recovery controls from Azure."""
        controls: List[TechnicalControl] = []

        try:
            if self.mock_data and hasattr(self.mock_data, "storage_accounts"):
                for account in self.mock_data.storage_accounts:
                    rg = (
                        account.id.split("/")[4]
                        if hasattr(account, "id") and len(account.id.split("/")) > 4
                        else "rg-test"
                    )
                    controls.append(self._analyze_storage_redundancy(account, rg))
            else:
                storage_client = self._get_storage_client()
                for rg in self._list_resource_groups():
                    for account in storage_client.storage_accounts.list_by_resource_group(rg):
                        redundancy_control = self._analyze_storage_redundancy(account, rg)
                        controls.append(redundancy_control)

            logger.info(f"Collected {len(controls)} backup controls from Azure")

        except AzureError as e:
            logger.error(f"Azure error during backup collection: {e}")
            self.errors.append({"category": "Backup", "error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error during backup collection: {e}")
            self.errors.append({"category": "Backup", "error": str(e)})

        return controls

    def _analyze_storage_redundancy(self, account: Any, resource_group: str) -> TechnicalControl:
        """Analyze storage account redundancy (backup) settings."""
        sku = getattr(account, "sku", None)
        sku_name = getattr(sku, "name", "unknown") if sku else "unknown"

        redundancy_map = {
            "Standard_LRS": "Locally Redundant (lowest resilience)",
            "Standard_GRS": "Geo-Redundant (cross-region backup)",
            "Standard_RAGRS": "Read-Access Geo-Redundant",
            "Standard_ZRS": "Zone-Redundant (cross-datacenter)",
            "Standard_GZRS": "Geo-Zone-Redundant (highest resilience)",
        }

        redundancy_level = redundancy_map.get(sku_name, sku_name)

        compliant_skus = [
            "Standard_GRS",
            "Standard_RAGRS",
            "Standard_GZRS",
            "Standard_ZRS",
            "Premium_ZRS",
        ]

        acc_name = getattr(account, "name", "unknown-storage") or "unknown-storage"
        acc_id = getattr(account, "id", None) or self._fallback_id(
            "Microsoft.Storage/storageAccounts", resource_group, acc_name
        )

        return TechnicalControl(
            control_id=f"azure-storage-redundancy-{acc_name}",
            control_category=ControlCategory.BACKUP_RECOVERY,
            cloud_provider=CloudProvider.AZURE,
            resource_type="StorageAccount",
            resource_id=acc_id,
            resource_name=acc_name,
            control_description="Storage account redundancy/backup configuration",
            current_state={
                "sku": sku_name,
                "redundancy_level": redundancy_level,
                "is_geo_redundant": sku_name in ["Standard_GRS", "Standard_RAGRS", "Standard_GZRS"],
            },
            compliance_status=(
                ComplianceStatus.COMPLIANT
                if sku_name in compliant_skus
                else ComplianceStatus.NON_COMPLIANT
            ),
            metadata={
                "resource_group": resource_group,
                "location": getattr(account, "location", "westeurope"),
                "dora_relevance": ("High - Maps to DORA Article 6 backup requirements"),
            },
        )
