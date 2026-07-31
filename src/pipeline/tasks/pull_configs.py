"""Task 1: Pull Infrastructure Configurations.

This Airflow task extracts the current state of cloud infrastructure
using the collectors from Step 2.

Research Context:
    This task implements continuous monitoring, a key requirement of
    DORA Article 11 and NIS2 Article 21. By automatically pulling
    infrastructure configurations on a schedule, we ensure that
    compliance assessments are always based on current data.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.collectors.azure_collector import AzureCollector

logger = logging.getLogger(__name__)


def pull_infrastructure_configs(
    cloud_provider: str = "azure",
    subscription_id: Optional[str] = None,
    output_dir: str = "baselines",
    mock_data_path: Optional[str] = None,
    **context: Any,  # Airflow context
) -> Dict[str, Any]:
    """Pull the latest infrastructure configurations from cloud provider.

    This function is called by Airflow as a PythonOperator task.

    Args:
        cloud_provider: Cloud provider to pull from (azure, aws)
        subscription_id: Cloud subscription ID (optional)
        output_dir: Directory to save baseline JSON
        mock_data_path: Optional path to mock data response for offline testing
        context: Airflow context (contains execution_date, ti, etc.)

    Returns:
        Dictionary with baseline metadata for downstream tasks
    """
    logger.info(f"Starting infrastructure config pull for {cloud_provider}")

    # Get execution date from Airflow context or default to current time
    execution_date = context.get("logical_date") or context.get(
        "execution_date", datetime.now(timezone.utc)
    )
    if isinstance(execution_date, str):
        try:
            execution_date = datetime.fromisoformat(execution_date)
        except Exception:
            execution_date = datetime.now(timezone.utc)

    try:
        # Initialize collector
        if cloud_provider.lower() == "azure":
            # Fall back to default mock if no mock path is given and file exists
            if not mock_data_path:
                default_mock = Path("data/mock_cloud_responses/azure_mock_response.json")
                if default_mock.exists():
                    mock_data_path = str(default_mock)

            collector = AzureCollector(
                subscription_id=subscription_id,
                mock_data_path=mock_data_path,
            )
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")

        # Collect baseline
        baseline = collector.collect_all()

        # Save to file
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = execution_date.strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_{cloud_provider}_{timestamp}.json"
        filepath = output_path / filename

        collector.save_baseline(baseline, str(filepath))

        logger.info(f"✓ Baseline saved to {filepath}")

        # Return metadata for downstream tasks (via XCom)
        return {
            "baseline_id": baseline.baseline_id,
            "baseline_path": str(filepath),
            "cloud_provider": cloud_provider,
            "subscription_id": baseline.subscription_id,
            "total_controls": len(baseline.controls),
            "collection_timestamp": baseline.collection_timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"✗ Failed to pull infrastructure configs: {e}")
        raise
