"""Report Generator - Generates Human-Readable Gap Analysis Reports.

This module converts GapAnalysisReport objects into various output formats
(JSON, Markdown, terminal) for consumption by technical and governance stakeholders.

Research Context:
    Effective reporting is crucial for bridging the gap between technical
    compliance assessment and organizational decision-making. The report
    generator ensures that complex gap analysis results are accessible
    to both technical engineers and legal auditors.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.models.gap_analysis import GapAnalysisReport, GapAnalysisResult

logger = logging.getLogger(__name__)
console = Console()


def _safe_print(*args: Any, **kwargs: Any) -> None:
    """Print using Rich console with fallback for legacy Windows cp1252 consoles."""
    try:
        console.print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.replace("✓", "[OK]").replace("⚠", "[!]").replace("•", "*"))
            else:
                safe_args.append(a)
        try:
            console.print(*safe_args, **kwargs)
        except Exception:
            pass


class ReportGenerator:
    """Generates reports from gap analysis results.

    Supports multiple output formats:
    - JSON (machine-readable)
    - Markdown (human-readable, version-controlled)
    - Terminal (Rich-powered console output)
    """

    def __init__(self, report: GapAnalysisReport):
        """Initialize the report generator.

        Args:
            report: GapAnalysisReport to generate reports from
        """
        self.report = report

    def save_json(self, output_path: str) -> None:
        """Save report as JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        report_dict = self.report.model_dump(mode="json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"Gap analysis report saved to {output_path}")
        _safe_print(f"[green]✓ JSON report saved to {output_path}[/]")

    def save_markdown(self, output_path: str) -> None:
        """Save report as Markdown file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        md_content = self._generate_markdown()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Markdown report saved to {output_path}")
        _safe_print(f"[green]✓ Markdown report saved to {output_path}[/]")

    def _generate_markdown(self) -> str:
        """Generate Markdown content for the report."""
        lines: List[str] = [
            "# Gap Analysis Report",
            "",
            f"**Report ID**: {self.report.report_id}",
            f"**Generated**: {self.report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Catalog**: {self.report.catalog_id}",
            f"**Baseline**: {self.report.baseline_id}",
            "",
            "## Executive Summary",
            "",
        ]

        summary = self.report.summary
        total_analyzed = summary.get("total_controls_analyzed", len(self.report.results))
        avg_conf = summary.get("avg_confidence_score", 0.0)

        total_tech = self.report.total_technical_controls
        lines.extend(
            [
                f"- **Total Regulatory Controls Analyzed**: {total_analyzed}",
                f"- **Total Technical Controls in Baseline**: {total_tech}",
                f"- **Average Confidence Score**: {avg_conf:.2%}",
                "",
                "## Compliance Overview",
                "",
                "| Status | Count | Percentage |",
                "|:-------|:------|:-----------|",
            ]
        )

        compliance_breakdown = summary.get("compliance_status_breakdown", {})
        total = sum(compliance_breakdown.values()) or 1
        for status, count in compliance_breakdown.items():
            percentage = (count / total) * 100
            lines.append(f"| {status.upper()} | {count} | {percentage:.1f}% |")

        lines.extend(
            [
                "",
                "## Detailed Results",
                "",
            ]
        )

        # Group by regulation
        by_regulation: Dict[str, List[GapAnalysisResult]] = {}
        for result in self.report.results:
            reg = result.regulation
            if reg not in by_regulation:
                by_regulation[reg] = []
            by_regulation[reg].append(result)

        for regulation, results in sorted(by_regulation.items()):
            lines.append(f"### {regulation}")
            lines.append("")

            for result in results:
                status_emoji = {
                    "compliant": "✅",
                    "partial": "⚠️",
                    "non-compliant": "❌",
                    "unknown": "❓",
                }.get(result.compliance_status, "❓")

                ctrl_header = (
                    f"#### {status_emoji} {result.regulatory_control_id}: "
                    f"{result.regulatory_control_title}"
                )
                lines.extend(
                    [
                        ctrl_header,
                        "",
                        f"**Compliance Status**: {result.compliance_status.upper()}",
                        (
                            f"**Confidence**: {result.confidence_score:.2%} "
                            f"({result.confidence_level.value})"
                        ),
                        f"**Mapped Technical Controls**: {len(result.mapped_technical_controls)}",
                        "",
                    ]
                )

                if result.friction_points:
                    lines.append("**Friction Points**:")
                    for fp in result.friction_points:
                        lines.append(f"- {fp}")
                    lines.append("")

                if result.recommendations:
                    lines.append("**Recommendations**:")
                    for rec in result.recommendations:
                        lines.append(f"- {rec}")
                    lines.append("")

                lines.extend(["---", ""])

        lines.extend(
            [
                "",
                "---",
                "*Report generated by Automated Compliance Mapping Framework v1.0.0*",
            ]
        )

        return "\n".join(lines)

    def print_terminal_report(self) -> None:
        """Print a beautiful terminal report using Rich."""
        _safe_print("\n")
        timestamp_str = self.report.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        _safe_print(
            Panel(
                f"[bold cyan]Gap Analysis Report[/]\n"
                f"Report ID: {self.report.report_id}\n"
                f"Generated: {timestamp_str}",
                title="Automated Compliance Mapping Framework",
                border_style="cyan",
            )
        )
        _safe_print("")

        summary = self.report.summary
        total_analyzed = summary.get("total_controls_analyzed", len(self.report.results))
        avg_conf = summary.get("avg_confidence_score", 0.0)

        # Summary table
        summary_table = Table(title="Summary Statistics")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Regulatory Controls", str(total_analyzed))
        summary_table.add_row("Total Technical Controls", str(self.report.total_technical_controls))
        summary_table.add_row("Average Confidence Score", f"{avg_conf:.2%}")

        _safe_print(summary_table)
        _safe_print("")

        # Compliance breakdown
        compliance_table = Table(title="Compliance Status Breakdown")
        compliance_table.add_column("Status", style="cyan")
        compliance_table.add_column("Count", style="green")
        compliance_table.add_column("Percentage", style="yellow")

        compliance_breakdown = summary.get("compliance_status_breakdown", {})
        total = sum(compliance_breakdown.values()) or 1

        for status, count in compliance_breakdown.items():
            percentage = f"{(count / total) * 100:.1f}%"
            status_style = {
                "compliant": "green",
                "partial": "yellow",
                "non-compliant": "red",
                "unknown": "dim",
            }.get(status, "white")

            compliance_table.add_row(
                f"[{status_style}]{status.upper()}[/{status_style}]",
                str(count),
                percentage,
            )

        _safe_print(compliance_table)
        _safe_print("")

        # Confidence breakdown
        confidence_table = Table(title="Confidence Level Breakdown")
        confidence_table.add_column("Level", style="cyan")
        confidence_table.add_column("Count", style="green")

        confidence_breakdown = summary.get("confidence_breakdown", {})
        for level, count in confidence_breakdown.items():
            confidence_table.add_row(level.upper(), str(count))

        _safe_print(confidence_table)
        _safe_print("")

        # Critical gaps
        non_compliant = self.report.get_non_compliant_results()
        if non_compliant:
            _safe_print(f"[bold red]⚠ Critical Gaps Identified: {len(non_compliant)}[/]")
            _safe_print("")

            for result in non_compliant[:5]:  # Show top 5
                _safe_print(
                    f"  • [yellow]{result.regulatory_control_id}[/]: "
                    f"{result.regulatory_control_title} "
                    f"(Confidence: {result.confidence_score:.2%})"
                )

            if len(non_compliant) > 5:
                _safe_print(f"  ... and {len(non_compliant) - 5} more")

        _safe_print("")
        _safe_print("[bold green]✓ Gap analysis complete[/]")
        _safe_print("")
