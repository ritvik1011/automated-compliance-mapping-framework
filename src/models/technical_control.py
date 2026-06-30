"""Technical Control Data Models.

This module defines Pydantic models for representing the "As-Is" state
of enterprise infrastructure. These models ensure type safety and
validation when collecting cloud resource configurations.

Research Context:
    These models are designed to capture the technical reality of
    enterprise environments, which will later be compared against
    regulatory requirements (OSCAL catalogs from Step 1) to identify
    compliance gaps and socio-technical friction points.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


def _utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"


class ControlCategory(str, Enum):
    """Categories of technical controls based on regulatory frameworks."""

    IDENTITY_ACCESS = "identity_access_management"
    ENCRYPTION = "data_encryption"
    NETWORK = "network_security"
    BACKUP_RECOVERY = "backup_recovery"
    LOGGING_MONITORING = "logging_monitoring"
    APPLICATION_SECURITY = "application_security"


class ComplianceStatus(str, Enum):
    """Binary compliance status for a control."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class TechnicalControl(BaseModel):
    """Represents a single technical control in the enterprise environment.

    This is the fundamental unit of our baseline - each control represents
    one measurable aspect of the infrastructure's security posture.

    Example:
        - "Azure Storage Account X has encryption at rest enabled"
        - "AWS IAM User Y has MFA disabled"
    """

    control_id: str = Field(
        ...,
        description="Unique identifier for this control instance",
        examples=["azure-storage-encryption-abc123"],
    )
    control_category: ControlCategory = Field(
        ...,
        description="Category of the control (e.g., encryption, IAM)",
    )
    cloud_provider: CloudProvider = Field(
        ...,
        description="Cloud provider where this control exists",
    )
    resource_type: str = Field(
        ...,
        description="Type of cloud resource (e.g., 'StorageAccount', 'IAMUser')",
        examples=["StorageAccount", "IAMUser", "VirtualNetwork"],
    )
    resource_id: str = Field(
        ...,
        description="Cloud provider's unique resource identifier",
        examples=["/subscriptions/xxx/resourceGroups/rg1/providers/..."],
    )
    resource_name: str = Field(
        ...,
        description="Human-readable name of the resource",
    )
    control_description: str = Field(
        ...,
        description="What this control measures",
    )
    current_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="The actual configuration values observed",
    )
    compliance_status: ComplianceStatus = Field(
        default=ComplianceStatus.UNKNOWN,
        description="Whether this control meets baseline expectations",
    )
    evidence_timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When this data was collected",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (region, tags, owner, etc.)",
    )

    @field_validator("control_id")
    @classmethod
    def validate_control_id(cls, v: str) -> str:
        """Ensure control_id follows naming convention."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("control_id must contain only alphanumeric, hyphens, underscores")
        return v


class InfrastructureBaseline(BaseModel):
    """Represents the complete "As-Is" state of an enterprise environment.

    This is the top-level container that holds all technical controls
    collected from the infrastructure. It will be serialized to JSON
    and later compared against OSCAL catalogs for gap analysis.
    """

    baseline_id: str = Field(
        ...,
        description="Unique identifier for this baseline snapshot",
    )
    collection_timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When the baseline was collected",
    )
    cloud_provider: CloudProvider = Field(
        ...,
        description="Primary cloud provider for this baseline",
    )
    subscription_id: Optional[str] = Field(
        default=None,
        description="Cloud subscription/account ID",
    )
    total_resources_scanned: int = Field(
        default=0,
        description="Total number of resources examined",
    )
    controls: List[TechnicalControl] = Field(
        default_factory=list,
        description="All technical controls discovered",
    )
    collection_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the collection process",
    )

    def get_controls_by_category(self, category: ControlCategory) -> List[TechnicalControl]:
        """Filter controls by category."""
        return [c for c in self.controls if c.control_category == category]

    def get_non_compliant_controls(self) -> List[TechnicalControl]:
        """Get all controls that are non-compliant."""
        return [c for c in self.controls if c.compliance_status == ComplianceStatus.NON_COMPLIANT]

    def get_compliance_summary(self) -> Dict[str, int]:
        """Generate a summary of compliance status counts."""
        summary = {status.value: 0 for status in ComplianceStatus}
        for control in self.controls:
            summary[control.compliance_status.value] += 1
        return summary
