"""Main Baseline Collection Orchestrator.

This module provides the CLI interface for collecting technical baselines
from cloud environments. It orchestrates the collection, normalization,
and saving of infrastructure state data.

Usage:
    # Collect from Azure (using default credentials)
    python -m src.main_baseline --provider azure --output baselines/azure_baseline.json

    # Collect from Azure with specific subscription
    python -m src.main_baseline --provider azure --subscription xxx-xxx-xxx \
        --output baselines/azure.json

    # Collect and also generate OSCAL component-definition
    python -m src.main_baseline --provider azure --oscal-output baselines/oscal_component.json
"""

import argparse
import logging
import sys
from typing import List, Optional

# Ensure UTF-8 output on Windows consoles to prevent charmap encoding errors
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from src.collectors.azure_collector import AzureCollector
from src.models.technical_control import InfrastructureBaseline
from src.normalizers.oscal_component_normalizer import OSCALComponentNormalizer

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
console = Console()


def print_baseline_summary(baseline: InfrastructureBaseline) -> None:
    """Print a beautiful summary of the collected baseline."""
    console.print("\n[bold cyan]======================================================[/]")
    console.print("[bold cyan]  Infrastructure Baseline Collection Summary[/]")
    console.print("[bold cyan]======================================================[/]\n")

    # Summary table
    table = Table(title="Collection Overview")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cloud Provider", baseline.cloud_provider.value.upper())
    table.add_row("Subscription ID", baseline.subscription_id or "N/A")
    table.add_row("Total Controls", str(len(baseline.controls)))
    table.add_row(
        "Collection Time",
        baseline.collection_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    )

    console.print(table)

    # Compliance status table
    summary = baseline.get_compliance_summary()
    status_table = Table(title="Compliance Status Breakdown")
    status_table.add_column("Status", style="cyan")
    status_table.add_column("Count", style="green")
    status_table.add_column("Percentage", style="yellow")

    total = len(baseline.controls) or 1
    for status, count in summary.items():
        percentage = f"{(count / total) * 100:.1f}%"
        status_style = {
            "compliant": "green",
            "non_compliant": "red",
            "partial": "yellow",
            "unknown": "dim",
        }.get(status, "white")
        status_table.add_row(
            f"[{status_style}]{status.upper()}[/{status_style}]",
            str(count),
            percentage,
        )

    console.print("\n")
    console.print(status_table)

    # Category breakdown
    categories: dict[str, int] = {}
    for control in baseline.controls:
        cat = control.control_category.value
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    cat_table = Table(title="Controls by Category")
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", style="green")

    for cat, count in sorted(categories.items()):
        cat_table.add_row(cat, str(count))

    console.print("\n")
    console.print(cat_table)

    # Errors if any
    if baseline.collection_metadata.get("errors_encountered", 0) > 0:
        console.print("\n[bold red]⚠ Errors Encountered:[/]")
        for error in baseline.collection_metadata.get("error_details", []):
            console.print(f"  • {error['category']}: {error['error']}")


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for baseline collection."""
    parser = argparse.ArgumentParser(
        description="Collect technical baseline from cloud infrastructure"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["azure", "aws"],
        default="azure",
        help="Cloud provider to collect from (default: azure)",
    )
    parser.add_argument(
        "--subscription",
        type=str,
        help="Cloud subscription/account ID (optional)",
    )
    parser.add_argument(
        "--region",
        type=str,
        help="Specific region to limit collection (optional)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="baselines/technical_baseline.json",
        help="Output path for the baseline JSON (default: baselines/technical_baseline.json)",
    )
    parser.add_argument(
        "--oscal-output",
        type=str,
        help="If provided, also save OSCAL Component-Definition to this path",
    )
    parser.add_argument(
        "--mock",
        type=str,
        nargs="?",
        const="data/mock_cloud_responses/azure_mock_response.json",
        default=None,
        help="Path to mock cloud response JSON file (for offline execution without credentials)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console.print(f"\n[bold]Starting baseline collection for {args.provider.upper()}[/]\n")

    try:
        # Initialize the appropriate collector
        if args.provider == "azure":
            collector = AzureCollector(
                subscription_id=args.subscription,
                region=args.region,
                mock_data_path=args.mock,
            )
        elif args.provider == "aws":
            # AWS collector will be implemented similarly
            raise NotImplementedError("AWS collector not yet implemented. Coming in Step 2.5!")
        else:
            raise ValueError(f"Unsupported provider: {args.provider}")

        # Collect the baseline
        baseline = collector.collect_all()

        # Print summary
        print_baseline_summary(baseline)

        # Save baseline
        collector.save_baseline(baseline, args.output)
        console.print(f"\n[green]Baseline saved to {args.output}[/]")

        # Optionally generate OSCAL output
        if args.oscal_output:
            normalizer = OSCALComponentNormalizer(baseline)
            normalizer.save(args.oscal_output)
            console.print(f"[green]OSCAL Component-Definition saved to {args.oscal_output}[/]")

        console.print("\n[bold green]======================================================[/]")
        console.print("[bold green]  Baseline Collection Complete![/]")
        console.print("[bold green]======================================================[/]\n")
        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Collection interrupted by user[/]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/]")
        logger.exception("Baseline collection failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
