"""OSCAL Component-Definition Normalizer.

This module converts InfrastructureBaseline objects (collected from cloud
environments) into OSCAL Component-Definition format. This enables direct
comparison with OSCAL Catalogs (from Step 1) for automated gap analysis.

Research Context:
    By normalizing both regulatory requirements (Step 1) and technical
    baselines (Step 2) into OSCAL format, we create a common language
    for compliance analysis. This is the foundation of "Policy-as-Code"
    approaches to regulatory compliance.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import uuid

from src.models.technical_control import (
    ComplianceStatus,
    InfrastructureBaseline,
    TechnicalControl,
)

logger = logging.getLogger(__name__)


class OSCALComponentNormalizer:
    """Converts InfrastructureBaseline to OSCAL Component-Definition format.

    The OSCAL Component-Definition schema represents "what a component
    implements" in terms of security controls. This is the counterpart
    to the OSCAL Catalog (which represents "what controls exist").
    """

    def __init__(self, baseline: InfrastructureBaseline) -> None:
        """Initialize the normalizer with a baseline snapshot."""
        self.baseline = baseline
        self.component_uuid = str(uuid.uuid4())

    def normalize(self) -> Dict[str, Any]:
        """Convert the baseline to OSCAL Component-Definition format.

        Returns:
            Dict representing a valid OSCAL Component-Definition
        """
        return {
            "component-definition": {
                "uuid": str(uuid.uuid4()),
                "metadata": self._build_metadata(),
                "components": self._build_components(),
                "capabilities": [],
                "back-matter": self._build_back_matter(),
            }
        }

    def _build_metadata(self) -> Dict[str, Any]:
        """Build the OSCAL metadata section."""
        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            "title": (f"Technical Baseline - " f"{self.baseline.cloud_provider.value.upper()}"),
            "last-modified": now_iso,
            "version": "1.0.0",
            "oscal-version": "1.1.2",
            "roles": [
                {
                    "id": "asset-owner",
                    "title": "Asset Owner",
                },
                {
                    "id": "provider",
                    "title": "Cloud Service Provider",
                },
            ],
            "parties": [
                {
                    "uuid": str(uuid.uuid4()),
                    "type": "organization",
                    "name": (f"{self.baseline.cloud_provider.value.upper()} " f"Environment"),
                }
            ],
            "responsible-parties": [
                {
                    "role-id": "asset-owner",
                    "party-uuids": [str(uuid.uuid4())],
                }
            ],
        }

    def _build_components(self) -> List[Dict[str, Any]]:
        """Build OSCAL components from the baseline.

        Each cloud resource becomes an OSCAL "component" with its
        implemented requirements mapped to controls.
        """
        components: List[Dict[str, Any]] = []

        # Group controls by resource
        resources: Dict[str, List[TechnicalControl]] = {}
        for control in self.baseline.controls:
            key = control.resource_id
            if key not in resources:
                resources[key] = []
            resources[key].append(control)

        # Create a component for each resource
        for resource_id, controls in resources.items():
            if not controls:
                continue

            first_control = controls[0]
            component: Dict[str, Any] = {
                "uuid": str(uuid.uuid4()),
                "type": self._map_resource_type_to_oscal(first_control.resource_type),
                "title": first_control.resource_name,
                "description": (
                    f"{first_control.resource_type} resource in "
                    f"{self.baseline.cloud_provider.value.upper()}"
                ),
                "purpose": (
                    f"Technical component implementing security controls for "
                    f"{first_control.resource_type}"
                ),
                "props": [
                    {
                        "name": "resource-id",
                        "value": resource_id,
                    },
                    {
                        "name": "cloud-provider",
                        "value": self.baseline.cloud_provider.value,
                    },
                    {
                        "name": "resource-type",
                        "value": first_control.resource_type,
                    },
                    {
                        "name": "compliance-status",
                        "value": self._get_overall_status(controls),
                    },
                ],
                "control-implementations": self._build_control_implementations(controls),
            }
            components.append(component)

        return components

    def _map_resource_type_to_oscal(self, resource_type: str) -> str:
        """Map cloud resource types to OSCAL component types."""
        mapping = {
            "StorageAccount": "service",
            "VirtualMachine": "service",
            "VirtualNetwork": "network",
            "NetworkSecurityGroup": "network",
            "KeyVault": "service",
            "PublicIPAddress": "network",
            "IAMUser": "policy",
            "Database": "service",
        }
        return mapping.get(resource_type, "service")

    def _build_control_implementations(
        self, controls: List[TechnicalControl]
    ) -> List[Dict[str, Any]]:
        """Build OSCAL control-implementations from technical controls."""
        by_category: Dict[str, List[TechnicalControl]] = {}
        for control in controls:
            cat = control.control_category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(control)

        implementations: List[Dict[str, Any]] = []
        for category, category_controls in by_category.items():
            implementation = {
                "uuid": str(uuid.uuid4()),
                "source": f"#{category}",
                "description": f"Implementation of {category} controls",
                "implemented-requirements": [
                    self._build_implemented_requirement(c) for c in category_controls
                ],
            }
            implementations.append(implementation)

        return implementations

    def _build_implemented_requirement(self, control: TechnicalControl) -> Dict[str, Any]:
        """Build a single OSCAL implemented-requirement from a TechnicalControl."""
        return {
            "uuid": str(uuid.uuid4()),
            "control-id": control.control_id,
            "description": control.control_description,
            "props": [
                {
                    "name": "compliance-status",
                    "value": control.compliance_status.value,
                },
                {
                    "name": "evidence-timestamp",
                    "value": control.evidence_timestamp.isoformat(),
                },
            ],
            "statements": [
                {
                    "statement-id": f"{control.control_id}_statement",
                    "uuid": str(uuid.uuid4()),
                    "description": (
                        f"Current state: " f"{json.dumps(control.current_state, default=str)}"
                    ),
                }
            ],
        }

    def _get_overall_status(self, controls: List[TechnicalControl]) -> str:
        """Determine overall compliance status for a resource."""
        statuses = [c.compliance_status for c in controls]

        if all(s == ComplianceStatus.COMPLIANT for s in statuses):
            return "compliant"
        elif any(s == ComplianceStatus.NON_COMPLIANT for s in statuses):
            return "non-compliant"
        elif any(s == ComplianceStatus.PARTIAL for s in statuses):
            return "partial"
        else:
            return "unknown"

    def _build_back_matter(self) -> Dict[str, Any]:
        """Build the OSCAL back-matter section with resources."""
        return {
            "resources": [
                {
                    "uuid": str(uuid.uuid4()),
                    "title": "Collection Metadata",
                    "description": (
                        f"Baseline collected at "
                        f"{self.baseline.collection_timestamp.isoformat()}"
                    ),
                    "props": [
                        {
                            "name": "baseline-id",
                            "value": self.baseline.baseline_id,
                        },
                        {
                            "name": "total-controls",
                            "value": str(len(self.baseline.controls)),
                        },
                        {
                            "name": "subscription-id",
                            "value": self.baseline.subscription_id or "unknown",
                        },
                    ],
                }
            ]
        }

    def save(self, output_path: str) -> None:
        """Save the normalized OSCAL component-definition to a JSON file."""
        oscal_doc = self.normalize()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(oscal_doc, f, indent=2, default=str)

        logger.info(f"OSCAL Component-Definition saved to {output_path}")
        print(f"+ OSCAL Component-Definition saved to {output_path}")
