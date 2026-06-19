"""Main Gap Analysis CLI Orchestrator.

This module provides the command-line interface for executing the automated
gap analysis engine. It evaluates OSCAL regulatory catalogs against empirical
cloud infrastructure baselines, renders a rich terminal dashboard, and exports
actionable audit reports in both JSON and Markdown formats.

Usage:
    # Run full gap analysis against default catalog and baseline
    python -m src.main_gap_analysis

    # Run gap analysis with specific files
    python -m src.main_gap_analysis \
        --catalog oscal_profiles/unified_catalog.json \
        --baseline baselines/azure_baseline.json \
        --output reports/gap_analysis_report.json \
        --markdown reports/gap_analysis_report.md

    # Filter evaluation by specific regulation
    python -m src.main_gap_analysis --regulation GDPR --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

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
from rich.panel import Panel
from rich.table import Table

from src.gap_analysis_engine import GapAnalysisEngine
from src.models.gap_analysis import GapAnalysisReport, GapSeverity, RegulationComplianceStatus

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
console = Console()


def print_dashboard_banner() -> None:
    """Print the header banner for the Gap Analysis Engine."""
    sub_title = (
        "[dim]Bridges Qualitative EU Statutes (GDPR/DORA/NIS2) " "with Binary Cloud Telemetry[/dim]"
    )
    console.print(
        Panel.fit(
            "[bold white]Automated Compliance Mapping Framework[/bold white]\n"
            "[bold cyan]🔍 Step 3: Automated Gap Analysis Engine & Decision Brain[/bold cyan]\n"
            + sub_title,
            border_style="cyan",
        )
    )


def print_report_summary(report: GapAnalysisReport, verbose: bool = False) -> None:
    """Render a comprehensive Rich dashboard summarizing gap analysis results."""
    summary = report.summary

    # Overall Posture Card
    comp_color = (
        "green"
        if summary.overall_compliance_percentage >= 80
        else ("yellow" if summary.overall_compliance_percentage >= 50 else "red")
    )
    conf_color = (
        "green"
        if summary.overall_confidence_score >= 0.8
        else ("yellow" if summary.overall_confidence_score >= 0.6 else "red")
    )

    summary_table = Table(title="Compliance & Confidence Metrics", border_style="cyan")
    summary_table.add_column("Evaluation Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Score / Result", style="bold")
    summary_table.add_column("Benchmark Target", style="dim")
    summary_table.add_column("Assessment", style="bold")

    comp_assessment = (
        f"[{comp_color}]"
        f"{'COMPLIANT' if summary.overall_compliance_percentage >= 95 else 'ACTION REQUIRED'}"
        f"[/{comp_color}]"
    )
    summary_table.add_row(
        "Overall Compliance Score",
        f"[{comp_color}]{summary.overall_compliance_percentage:.1f}%[/{comp_color}]",
        "≥ 95.0%",
        comp_assessment,
    )

    conf_assessment = (
        f"[{conf_color}]"
        f"{'HIGH CERTAINTY' if summary.overall_confidence_score >= 0.85 else 'DISCOUNT APPLIED'}"
        f"[/{conf_color}]"
    )
    summary_table.add_row(
        "Automated Confidence Score",
        f"[{conf_color}]{summary.overall_confidence_score:.3f} / 1.000[/{conf_color}]",
        "≥ 0.850",
        conf_assessment,
    )

    ctrl_assessment = (
        f"[green]{summary.compliant_controls} Compliant[/green] | "
        f"[yellow]{summary.partially_compliant_controls} Partial[/yellow] | "
        f"[red]{summary.non_compliant_controls} Failed[/red]"
    )
    summary_table.add_row(
        "Evaluated Regulatory Controls",
        str(summary.total_regulatory_controls),
        "Full Catalog",
        ctrl_assessment,
    )

    crit_count = summary.gaps_by_severity.get("critical", 0)
    high_count = summary.gaps_by_severity.get("high", 0)
    gap_assessment = f"[red]{crit_count} Critical[/red], [yellow]{high_count} High[/yellow]"
    summary_table.add_row(
        "Total Infrastructure Gaps",
        f"[red]{summary.total_gaps}[/red]",
        "0 Gaps",
        gap_assessment,
    )

    summary_table.add_row(
        "Human-in-the-Loop Reviews",
        f"[magenta]{summary.hitl_reviews_required}[/magenta]",
        "High Friction Articles",
        "[magenta]Mandatory Governance Sign-Off[/magenta]",
    )

    console.print(summary_table)

    # Control Evaluation Breakdown Table
    ctrl_table = Table(title="Regulatory Control Evaluations", border_style="blue")
    ctrl_table.add_column("Control ID", style="cyan", no_wrap=True)
    ctrl_table.add_column("Reg.", style="magenta")
    ctrl_table.add_column("Title", style="white")
    ctrl_table.add_column("Status", style="bold")
    ctrl_table.add_column("Compliance", justify="right")
    ctrl_table.add_column("Confidence", justify="right")
    ctrl_table.add_column("Friction", style="yellow")
    ctrl_table.add_column("HITL?", justify="center")

    for ev in report.evaluations:
        status_styled = {
            RegulationComplianceStatus.COMPLIANT: "[green]COMPLIANT[/green]",
            RegulationComplianceStatus.PARTIALLY_COMPLIANT: "[yellow]PARTIAL[/yellow]",
            RegulationComplianceStatus.NON_COMPLIANT: "[red]NON-COMPLIANT[/red]",
            RegulationComplianceStatus.UNMAPPED: "[dim]UNMAPPED[/dim]",
        }.get(ev.status, str(ev.status))

        hitl_styled = (
            "[bold magenta]REQUIRED[/bold magenta]" if ev.hitl_recommended else "[dim]AUTO[/dim]"
        )
        comp_str = f"{ev.compliance_score:.1f}%"
        conf_str = f"{ev.confidence_score:.3f}"

        ctrl_table.add_row(
            ev.regulatory_control_id,
            ev.regulation,
            ev.title[:35] + ("..." if len(ev.title) > 35 else ""),
            status_styled,
            comp_str,
            conf_str,
            f"{ev.friction_level} ({ev.friction_score:.1f})",
            hitl_styled,
        )

    console.print(ctrl_table)

    # Gaps Table
    if report.all_gaps:
        gap_table = Table(title="Prioritized Infrastructure Compliance Gaps", border_style="red")
        gap_table.add_column("Gap ID", style="bold cyan", no_wrap=True)
        gap_table.add_column("Severity", style="bold")
        gap_table.add_column("Regulation", style="magenta")
        gap_table.add_column("Resource", style="white")
        gap_table.add_column("Issue Description", style="yellow")

        for gap in report.all_gaps:
            sev_styled = {
                GapSeverity.CRITICAL: "[bold red]CRITICAL[/bold red]",
                GapSeverity.HIGH: "[red]HIGH[/red]",
                GapSeverity.MEDIUM: "[yellow]MEDIUM[/yellow]",
                GapSeverity.LOW: "[blue]LOW[/blue]",
                GapSeverity.INFORMATIONAL: "[dim]INFO[/dim]",
            }.get(gap.severity, str(gap.severity))

            gap_table.add_row(
                gap.gap_id,
                sev_styled,
                f"{gap.regulation} ({gap.regulatory_control_id})",
                gap.resource_name or "N/A",
                gap.title,
            )

        console.print(gap_table)

        if verbose:
            console.print(
                "\n[bold cyan]── Detailed Technical Remediation Directives ──[/bold cyan]"
            )
            for gap in report.all_gaps:
                console.print(
                    f"\n[bold red][{gap.gap_id}][/bold red] [bold white]{gap.title}[/bold white]"
                )
                console.print(f"  [dim]Resource:[/dim] {gap.resource_id}")
                console.print(
                    f"  [dim]Remediation:[/dim] [green]{gap.remediation_guidance}[/green]"
                )
                if gap.hitl_action:
                    console.print(f"  [dim]HITL Action:[/dim] [magenta]{gap.hitl_action}[/magenta]")


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entrypoint for Step 3 Gap Analysis."""
    parser = argparse.ArgumentParser(
        description="Automated Compliance Gap Analysis Engine (Step 3)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--catalog",
        type=str,
        default="oscal_profiles/unified_catalog.json",
        help="Path to NIST OSCAL Catalog JSON or profile from Step 1",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="baselines/azure_baseline.json",
        help="Path to Infrastructure Baseline JSON or OSCAL Component-Definition from Step 2",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/gap_analysis_report.json",
        help="Path to export the structured JSON gap analysis report",
    )
    parser.add_argument(
        "--markdown",
        type=str,
        default="reports/gap_analysis_report.md",
        help="Path to export the human-readable Markdown audit report",
    )
    parser.add_argument(
        "--regulation",
        type=str,
        default=None,
        help="Filter evaluation by specific regulation regime (e.g., GDPR, DORA, NIS2)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.35,
        help="Friction penalty weighting parameter (0.0 to 1.0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display verbose remediation directives in the terminal",
    )

    args = parser.parse_args(argv)

    print_dashboard_banner()

    engine = GapAnalysisEngine(friction_weight_alpha=args.alpha)

    try:
        console.print(f"[cyan]Loading regulatory catalog:[/] [bold]{args.catalog}[/bold]")
        console.print(f"[cyan]Loading infrastructure baseline:[/] [bold]{args.baseline}[/bold]")
        if args.regulation:
            reg_name = args.regulation.upper()
            console.print(f"[cyan]Applying regulation filter:[/] [bold]{reg_name}[/bold]")

        report = engine.evaluate(
            catalog_source=args.catalog,
            baseline_source=args.baseline,
            regulation_filter=args.regulation,
        )

        print_report_summary(report, verbose=args.verbose)

        # Export outputs
        json_path = engine.export_json(report, args.output)
        md_path = engine.export_markdown(report, args.markdown)

        console.print("\n[bold green]✔ Gap Analysis Audit Successfully Completed![/bold green]")
        console.print(f"  • JSON Audit Report: [bold cyan]{json_path}[/bold cyan]")
        console.print(f"  • Markdown Report:   [bold cyan]{md_path}[/bold cyan]\n")

        return 0

    except Exception as e:
        logger.exception("Error executing gap analysis engine: %s", e)
        console.print(f"\n[bold red]✖ Error executing gap analysis:[/] {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
