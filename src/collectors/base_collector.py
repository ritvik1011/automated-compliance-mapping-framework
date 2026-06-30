"""Base Collector - Abstract Interface for Cloud Infrastructure Collection.

This module defines the abstract base class that all cloud-specific
collectors (Azure, AWS, GCP) must implement. It ensures a consistent
interface regardless of the underlying cloud provider.

Research Context:
    By abstracting the collection layer, we can compare compliance
    postures across multi-cloud environments using the same framework.
    This is critical for enterprises operating under DORA, which
    requires consistent ICT risk management across all service providers.
"""

from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models.technical_control import (
    CloudProvider,
    InfrastructureBaseline,
    TechnicalControl,
)

# Configure module-level logger
logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for cloud infrastructure collectors.

    All cloud-specific collectors (Azure, AWS) must inherit from this
    class and implement the abstract methods. This ensures consistency
    in the data collection process across different cloud environments.

    Usage:
        class AzureCollector(BaseCollector):
            def collect_iam_controls(self) -> List[TechnicalControl]:
                # Azure-specific implementation
                ...
    """

    def __init__(self, subscription_id: Optional[str] = None, region: Optional[str] = None) -> None:
        """Initialize the collector.

        Args:
            subscription_id: Cloud subscription/account ID to scan
            region: Specific region to limit collection (optional)
        """
        self.subscription_id = subscription_id
        self.region = region
        self.collected_controls: List[TechnicalControl] = []
        self.errors: List[Dict[str, Any]] = []
        logger.info(f"Initialized {self.__class__.__name__} for subscription: {subscription_id}")

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            Exception: If authentication fails with details
        """
        pass

    @abstractmethod
    def collect_iam_controls(self) -> List[TechnicalControl]:
        """Collect Identity and Access Management controls.

        This includes:
        - User/service principal configurations
        - Role assignments and permissions
        - MFA enforcement status
        - Password policies
        - Conditional access policies

        Returns:
            List of TechnicalControl objects representing IAM state
        """
        pass

    @abstractmethod
    def collect_encryption_controls(self) -> List[TechnicalControl]:
        """Collect data encryption controls.

        This includes:
        - Storage account encryption status
        - Database encryption (at rest and in transit)
        - Key vault configurations
        - TLS/SSL certificate status
        - Disk encryption status

        Returns:
            List of TechnicalControl objects representing encryption state
        """
        pass

    @abstractmethod
    def collect_network_controls(self) -> List[TechnicalControl]:
        """Collect network security controls.

        This includes:
        - Network Security Groups (NSGs) / Security Groups
        - Virtual network configurations
        - Firewall rules
        - Public IP exposure
        - DDoS protection status

        Returns:
            List of TechnicalControl objects representing network state
        """
        pass

    @abstractmethod
    def collect_backup_controls(self) -> List[TechnicalControl]:
        """Collect backup and recovery controls.

        This is CRITICAL for DORA compliance, which mandates:
        - Backup frequency and retention
        - Recovery Time Objective (RTO) capabilities
        - Recovery Point Objective (RPO) configurations
        - Backup encryption
        - Off-site backup storage

        Returns:
            List of TechnicalControl objects representing backup state
        """
        pass

    def collect_all(self) -> InfrastructureBaseline:
        """Orchestrate the collection of all control categories.

        This is the main entry point for the collector. It calls each
        category-specific method and aggregates the results into a
        single InfrastructureBaseline object.

        Returns:
            InfrastructureBaseline containing all collected controls

        Raises:
            RuntimeError: If authentication fails or critical errors occur
        """
        logger.info("Starting full infrastructure baseline collection")

        # Authenticate first
        if not self.authenticate():
            raise RuntimeError("Authentication failed. Cannot proceed with collection.")

        # Collect each category
        collection_methods = [
            ("IAM", self.collect_iam_controls),
            ("Encryption", self.collect_encryption_controls),
            ("Network", self.collect_network_controls),
            ("Backup/Recovery", self.collect_backup_controls),
        ]

        all_controls: List[TechnicalControl] = []

        for category_name, method in collection_methods:
            try:
                logger.info(f"Collecting {category_name} controls...")
                controls = method()
                all_controls.extend(controls)
                logger.info(f"  + Collected {len(controls)} {category_name} controls")
            except Exception as e:
                error_msg = f"Failed to collect {category_name} controls: {str(e)}"
                logger.error(error_msg)
                self.errors.append({"category": category_name, "error": str(e)})

        # Build the baseline
        provider_name = (
            self.cloud_provider.value
            if isinstance(self.cloud_provider, CloudProvider)
            else str(self.cloud_provider)
        )
        baseline = InfrastructureBaseline(
            baseline_id=f"baseline-{provider_name}-{self.subscription_id or 'default'}",
            cloud_provider=self.cloud_provider,
            subscription_id=self.subscription_id,
            total_resources_scanned=len(all_controls),
            controls=all_controls,
            collection_metadata={
                "collector_version": "1.0.0",
                "region": self.region,
                "errors_encountered": len(self.errors),
                "error_details": self.errors,
            },
        )

        logger.info(
            f"Baseline collection complete. "
            f"Total controls: {len(all_controls)}, "
            f"Errors: {len(self.errors)}"
        )

        return baseline

    @property
    @abstractmethod
    def cloud_provider(self) -> CloudProvider:
        """Return the cloud provider this collector supports."""
        pass

    def save_baseline(self, baseline: InfrastructureBaseline, output_path: str) -> None:
        """Save the baseline to a JSON file.

        Args:
            baseline: The InfrastructureBaseline to save
            output_path: File path where the JSON will be written
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable dict
        baseline_dict = baseline.model_dump(mode="json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(baseline_dict, f, indent=2, default=str)

        logger.info(f"Baseline saved to {output_path}")
