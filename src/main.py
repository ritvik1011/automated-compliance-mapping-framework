"""Pipeline Orchestration for Ingestion, Socio-Technical Friction Analysis, and OSCAL Generation.

This module provides the command-line interface and orchestrator executing
the full Step 1 Policy-as-Code pipeline: ingesting regulatory text, assessing
socio-technical friction, mapping to NIST OSCAL catalogs, and generating reports.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Ensure project root is present in sys.path for direct execution (e.g. `python src/main.py`)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

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

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402
from rich.text import Text  # noqa: E402

from src.friction_analyzer import FrictionAnalyzer, FrictionReport  # noqa: E402
from src.oscal_generator import OSCALGenerator  # noqa: E402
from src.parser import RegulatoryArticle, RegulatoryParser  # noqa: E402

logger = logging.getLogger("compliance_pipeline")


def setup_logging(verbose: bool = False) -> None:
    """Configures application logging level and formatting."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def print_rich_summary(
    console: Console, report: FrictionReport, articles: List[RegulatoryArticle]
) -> None:
    """Renders an executive terminal report using the Rich library.

    Args:
        console: Rich Console instance.
        report: Aggregated friction report.
        articles: Processed regulatory articles with attached metadata.
    """
    console.print()
    banner = Text(
        "Automated Compliance Mapping Framework | Policy-as-Code Foundation\n"
        "Step 1: Regulatory Ingestion, Standardization & Socio-Technical Friction Analysis",
        style="bold cyan",
        justify="center",
    )
    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))

    # Metrics Summary Table
    metrics_table = Table(
        title="Pipeline Ingestion & Friction Metrics", border_style="blue"
    )
    metrics_table.add_column(
        "Total Ingested Articles", justify="center", style="bold white"
    )
    metrics_table.add_column(
        "High Friction (Non-Binary)", justify="center", style="bold red"
    )
    metrics_table.add_column(
        "Medium Friction (Hybrid HITL)", justify="center", style="bold yellow"
    )
    metrics_table.add_column(
        "Low Friction (Fully Automatable)", justify="center", style="bold green"
    )

    metrics_table.add_row(
        str(report.total_articles),
        str(report.high_friction_count),
        str(report.medium_friction_count),
        str(report.low_friction_count),
    )
    console.print(metrics_table)
    console.print()

    # Detailed Controls Table
    controls_table = Table(
        title="Standardized Regulatory Controls & Friction Assessment",
        border_style="dim white",
        show_lines=True,
    )
    controls_table.add_column("Control ID", style="bold cyan", no_wrap=True)
    controls_table.add_column("Reg", justify="center", style="magenta", no_wrap=True)
    controls_table.add_column("Title", style="white")
    controls_table.add_column("Score", justify="right")
    controls_table.add_column("Friction Level", justify="center")
    controls_table.add_column("Detected Ambiguity Triggers", style="italic yellow")
    controls_table.add_column("Automation Feasibility", style="dim")

    for assessment in report.assessments:
        if assessment.friction_level == "High":
            level_badge = "[bold red]HIGH[/bold red]"
            score_str = f"[bold red]{assessment.friction_score:.1f}[/bold red]"
        elif assessment.friction_level == "Medium":
            level_badge = "[bold yellow]MEDIUM[/bold yellow]"
            score_str = f"[bold yellow]{assessment.friction_score:.1f}[/bold yellow]"
        else:
            level_badge = "[bold green]LOW[/bold green]"
            score_str = f"[bold green]{assessment.friction_score:.1f}[/bold green]"

        triggers_str = (
            ", ".join(assessment.detected_triggers)
            if assessment.detected_triggers
            else "None (Deterministic)"
        )

        controls_table.add_row(
            assessment.article_id,
            assessment.regulation,
            assessment.title,
            score_str,
            level_badge,
            triggers_str,
            assessment.automatable_status,
        )

    console.print(controls_table)
    console.print()

    # Callout panels for High Friction controls
    high_friction_items = [a for a in report.assessments if a.friction_level == "High"]
    if high_friction_items:
        console.print(
            "[bold red][!] Critical Socio-Technical Friction Points "
            "Detected (Deep Dive):[/bold red]"
        )
        for item in high_friction_items:
            triggers_str = ", ".join(item.detected_triggers)
            panel_content = (
                f"[bold cyan]Legal Reference:[/bold cyan] {item.article_id.upper()} "
                f"({item.regulation})\n"
                f"[bold yellow]Ambiguous Legal Triggers:[/bold yellow] {triggers_str}\n\n"
                "[bold underline]Why Binary Automation Fails (Research Rationale):"
                f"[/bold underline]\n{item.reason}\n\n"
                "[bold underline]Human-in-the-Loop (HITL) Engineering "
                f"Recommendation:[/bold underline]\n{item.recommendation}\n\n"
                f"[bold]Recommended Verification Procedures:[/bold]\n"
                + "\n".join(f"  * {step}" for step in item.hitl_validation_steps)
            )
            console.print(
                Panel(
                    panel_content,
                    title=f"[red]HIGH FRICTION CONTROL: {item.title}[/red]",
                    border_style="red",
                    padding=(1, 2),
                )
            )
            console.print()


def run_pipeline(
    input_file: Path,
    output_dir: Path,
    regulation_filter: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Executes the full Policy-as-Code ingestion and standardization pipeline.

    Args:
        input_file: Path to input JSON containing regulatory articles.
        output_dir: Directory where OSCAL catalogs and reports will be saved.
        regulation_filter: Optional regulation name to filter by.
        verbose: Verbose logging flag.

    Returns:
        Integer exit code (0 for success).
    """
    console = Console()
    setup_logging(verbose)

    console.print(
        f"[bold cyan][>] Ingesting regulatory articles from:[/bold cyan] {input_file}"
    )
    parser = RegulatoryParser(fail_on_error=False)
    articles = parser.load_from_file(input_file)

    if regulation_filter:
        norm_filter = regulation_filter.strip().upper()
        articles = [a for a in articles if a.regulation.upper() == norm_filter]
        console.print(
            f"[yellow]Filtered for regulation:[/yellow] {norm_filter} "
            f"({len(articles)} articles remaining)"
        )

    if not articles:
        console.print("[bold red]Error:[/bold red] No valid articles found to process.")
        return 1

    # Step 2: Socio-Technical Friction Analysis
    console.print(
        "[bold cyan][>] Analyzing socio-technical friction points and "
        "legal ambiguity...[/bold cyan]"
    )
    analyzer = FrictionAnalyzer()
    friction_report = analyzer.analyze_articles(articles, attach_to_articles=True)

    # Step 3: OSCAL Catalog Generation
    console.print("[bold cyan][>] Generating NIST OSCAL Catalogs...[/bold cyan]")
    oscal_gen = OSCALGenerator()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate regulation-specific catalogs
    catalogs = oscal_gen.generate_regulation_catalogs(articles)
    saved_catalogs: List[Path] = []
    for reg, catalog_data in catalogs.items():
        cat_file = output_dir / f"{reg.lower()}_catalog.json"
        oscal_gen.save_catalog_to_json(catalog_data, cat_file)
        saved_catalogs.append(cat_file)

    # Also generate unified multi-regulation catalog
    unified_catalog = oscal_gen.generate_catalog(articles)
    unified_file = output_dir / "unified_catalog.json"
    oscal_gen.save_catalog_to_json(unified_catalog, unified_file)
    saved_catalogs.append(unified_file)

    # Step 4: Export Friction Report JSON
    friction_report_path = output_dir / "friction_report.json"
    analyzer.export_report_to_json(friction_report, friction_report_path)

    # Step 5: Render Rich Terminal Output
    print_rich_summary(console, friction_report, articles)

    # Output Artifact Summary
    console.print("[bold green][OK] Pipeline executed successfully![/bold green]")
    console.print(f"[bold white]Generated Artifacts in '{output_dir}':[/bold white]")
    for cat_path in saved_catalogs:
        console.print(f"  * OSCAL Catalog: [green]{cat_path}[/green]")
    console.print(
        f"  * Socio-Technical Friction Report: [green]{friction_report_path}[/green]\n"
    )

    return 0


def main() -> None:
    """CLI entry point parsing command line arguments."""
    project_root = Path(__file__).resolve().parent.parent
    default_input = project_root / "data" / "sample_input.json"
    default_output = project_root / "oscal_profiles"

    arg_parser = argparse.ArgumentParser(
        description="Automated Compliance Mapping Framework - Step 1: Ingestion & Standardization",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=default_input,
        help="Path to JSON file containing raw regulatory articles.",
    )
    arg_parser.add_argument(
        "--output-dir",
        "--output",
        "-o",
        type=Path,
        default=default_output,
        help="Directory to store generated OSCAL catalogs and friction reports.",
    )
    arg_parser.add_argument(
        "--regulation",
        "-r",
        type=str,
        default=None,
        help="Optional filter to process only a specific regulation (e.g. GDPR, DORA, NIS2).",
    )
    arg_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug logging.",
    )

    args = arg_parser.parse_args()
    exit_code = run_pipeline(
        input_file=args.input,
        output_dir=args.output_dir,
        regulation_filter=args.regulation,
        verbose=args.verbose,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
