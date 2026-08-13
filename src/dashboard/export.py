"""Export Module for Compliance Dashboard.

Provides multi-format report export functionality (Excel, HTML, PDF)
for executive leadership, board members, and regulatory audit submissions.

Research Context:
    Translating compliance data into stakeholder-ready artifacts is the
    critical bridge between technical assessment and organizational governance.
    This module generates board-level summaries and detailed audit spreadsheets.
"""

from datetime import datetime, timezone
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


def export_assessment_to_excel(
    assessment_data: Dict[str, Any],
    output_path: Optional[Union[str, Path]] = None,
) -> bytes:
    """Export compliance assessment data to a multi-sheet Excel spreadsheet.

    Sheets:
        1. Executive Summary: High-level metrics and assessment metadata.
        2. Control Results: Granular status, confidence, and gap analysis per control.
        3. KPIs: Key performance indicators breakdown.
        4. Socio-Technical Friction: Research insights on human and process friction.

    Args:
        assessment_data: Dictionary containing 'assessment', 'controls', and 'kpis'.
        output_path: Optional path to save the .xlsx file on disk.

    Returns:
        bytes: Raw Excel file bytes.
    """
    buffer = io.BytesIO()

    assessment = assessment_data.get("assessment", {})
    controls_df: pd.DataFrame = assessment_data.get("controls", pd.DataFrame()).copy()
    kpis_df: pd.DataFrame = assessment_data.get("kpis", pd.DataFrame()).copy()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Sheet 1: Executive Summary
        summary_rows = [
            {"Metric": "Assessment ID", "Value": str(assessment.get("id", "N/A"))},
            {"Metric": "Assessment Date", "Value": str(assessment.get("assessment_date", "N/A"))},
            {
                "Metric": "Cloud Provider",
                "Value": str(assessment.get("cloud_provider", "N/A")).upper(),
            },
            {
                "Metric": "Overall Compliance Score",
                "Value": f"{assessment.get('overall_compliance_score', 0.0):.1f}%",
            },
            {
                "Metric": "Average Confidence Score",
                "Value": f"{assessment.get('average_confidence_score', 0.0):.1%}",
            },
            {
                "Metric": "Total Controls",
                "Value": assessment.get("total_regulatory_controls", len(controls_df)),
            },
            {"Metric": "Compliant Controls", "Value": assessment.get("compliant_count", 0)},
            {"Metric": "Partial Compliance Controls", "Value": assessment.get("partial_count", 0)},
            {"Metric": "Non-Compliant Controls", "Value": assessment.get("non_compliant_count", 0)},
            {"Metric": "Unknown Status Controls", "Value": assessment.get("unknown_count", 0)},
        ]
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)

        # Sheet 2: Control Results
        if not controls_df.empty:
            export_controls = controls_df.copy()
            # Clean string columns for clean Excel presentation
            for col in ["evidence", "friction_points", "recommendations"]:
                if col in export_controls.columns:
                    export_controls[col] = export_controls[col].astype(str)
            export_controls.to_excel(writer, sheet_name="Control Assessment", index=False)
        else:
            pd.DataFrame({"Message": ["No control results recorded"]}).to_excel(
                writer, sheet_name="Control Assessment", index=False
            )

        # Sheet 3: KPIs
        if not kpis_df.empty:
            kpis_df.to_excel(writer, sheet_name="KPIs", index=False)
        else:
            pd.DataFrame({"Message": ["No KPI records recorded"]}).to_excel(
                writer, sheet_name="KPIs", index=False
            )

        # Sheet 4: Socio-Technical Friction Points
        if not controls_df.empty and "friction_points" in controls_df.columns:
            friction_rows = []
            for _, row in controls_df.iterrows():
                fps_raw = row.get("friction_points")
                recs_raw = row.get("recommendations")

                fps = []
                if fps_raw and str(fps_raw) != "[]":
                    try:
                        fps = json.loads(fps_raw) if isinstance(fps_raw, str) else fps_raw
                    except Exception:
                        fps = [str(fps_raw)]

                recs = []
                if recs_raw and str(recs_raw) != "[]":
                    try:
                        recs = json.loads(recs_raw) if isinstance(recs_raw, str) else recs_raw
                    except Exception:
                        recs = [str(recs_raw)]

                if fps:
                    for fp in fps:
                        friction_rows.append(
                            {
                                "Control ID": row.get("regulatory_control_id"),
                                "Regulation": row.get("regulation"),
                                "Title": row.get("control_title"),
                                "Status": row.get("compliance_status"),
                                "Confidence": f"{float(row.get('confidence_score', 0)):.1%}",
                                "Friction Point": fp,
                                "Recommendations": "; ".join(recs) if recs else "N/A",
                            }
                        )

            if friction_rows:
                pd.DataFrame(friction_rows).to_excel(
                    writer, sheet_name="Socio-Technical Friction", index=False
                )
            else:
                pd.DataFrame({"Message": ["No friction points identified"]}).to_excel(
                    writer, sheet_name="Socio-Technical Friction", index=False
                )

    excel_data = buffer.getvalue()

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(excel_data)
        logger.info(f"Excel report saved to {path}")

    return excel_data


def generate_executive_html_report(assessment_data: Dict[str, Any]) -> str:
    """Generate a self-contained styled HTML report suitable for print or PDF.

    Args:
        assessment_data: Dictionary containing 'assessment', 'controls', and 'kpis'.

    Returns:
        str: HTML document content.
    """
    assessment = assessment_data.get("assessment", {})
    controls_df: pd.DataFrame = assessment_data.get("controls", pd.DataFrame())

    score = assessment.get("overall_compliance_score", 0.0)
    score_color = (
        "#00cc44"
        if score >= 85
        else "#88cc00" if score >= 70 else "#ffaa00" if score >= 50 else "#ff4444"
    )
    status_label = "STRONG" if score >= 80 else "MODERATE" if score >= 60 else "AT RISK"

    # Count friction points
    total_fps = 0
    if not controls_df.empty and "friction_points" in controls_df.columns:
        for val in controls_df["friction_points"]:
            if val and str(val) != "[]":
                try:
                    parsed = json.loads(val) if isinstance(val, str) else val
                    total_fps += len(parsed) if isinstance(parsed, list) else 1
                except Exception:
                    total_fps += 1

    # Format control table rows
    control_rows_html = ""
    if not controls_df.empty:
        for _, row in controls_df.head(25).iterrows():
            status_class = (
                "status-compliant"
                if row.get("compliance_status") == "compliant"
                else (
                    "status-partial"
                    if row.get("compliance_status") == "partial"
                    else "status-noncompliant"
                )
            )
            ctrl_id = row.get("regulatory_control_id", "")
            reg_name = row.get("regulation", "")
            ctrl_title = row.get("control_title", "")
            status_upper = row.get("compliance_status", "").upper()
            conf_pct = float(row.get("confidence_score", 0))
            control_rows_html += f"""
            <tr>
                <td><strong>{ctrl_id}</strong></td>
                <td>{reg_name}</td>
                <td>{ctrl_title}</td>
                <td><span class="badge {status_class}">{status_upper}</span></td>
                <td>{conf_pct:.0%}</td>
            </tr>
            """

    gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance Assessment Executive Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1a202c;
            line-height: 1.5;
            margin: 0;
            padding: 32px;
            background-color: #ffffff;
        }}
        .header {{
            border-bottom: 3px solid #2b6cb0;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 26px;
            font-weight: 700;
            color: #2b6cb0;
            margin: 0 0 6px 0;
        }}
        .subtitle {{
            font-size: 14px;
            color: #718096;
            margin: 0;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .kpi-card .value {{
            font-size: 24px;
            font-weight: 700;
            margin: 8px 0;
        }}
        .kpi-card .label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #4a5568;
        }}
        .score-pill {{
            color: {score_color};
            font-size: 32px;
            font-weight: 800;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }}
        .status-compliant {{ background-color: #c6f6d5; color: #22543d; }}
        .status-partial {{ background-color: #feebc8; color: #744210; }}
        .status-noncompliant {{ background-color: #fed7d7; color: #742a2a; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #edf2f7;
            font-weight: 600;
            color: #2d3748;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
            margin-top: 32px;
            margin-bottom: 12px;
            border-left: 4px solid #2b6cb0;
            padding-left: 8px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            font-size: 11px;
            color: #a0aec0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">🛡️ Compliance Assessment Executive Report</h1>
        <p class="subtitle">Generated: {gen_time} | Framework: Policy-as-Code Compliance Engine</p>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="label">Overall Compliance</div>
            <div class="value score-pill">{score:.1f}%</div>
            <div>Status: <strong>{status_label}</strong></div>
        </div>
        <div class="kpi-card">
            <div class="label">Total Controls</div>
            <div class="value">{assessment.get('total_regulatory_controls', len(controls_df))}</div>
            <div>Analyzed</div>
        </div>
        <div class="kpi-card">
            <div class="label">Confidence Score</div>
            <div class="value">{assessment.get('average_confidence_score', 0.0):.0%}</div>
            <div>Automated Assessment</div>
        </div>
        <div class="kpi-card">
            <div class="label">Socio-Technical Friction</div>
            <div class="value">{total_fps}</div>
            <div>Friction Points Identified</div>
        </div>
    </div>

    <div class="section-title">📊 Executive Summary & Recommendations</div>
    <p>
        The automated compliance assessment evaluated your infrastructure against GDPR,
        DORA, and NIS2 regulatory controls.
        Overall compliance is currently rated at <strong>{score:.1f}%</strong> ({status_label}).
        Key areas of attention include resolving {assessment.get('non_compliant_count', 0)}
        non-compliant controls and mitigating identified socio-technical friction.
    </p>

    <div class="section-title">📋 Regulatory Control Assessment (Top Findings)</div>
    <table>
        <thead>
            <tr>
                <th>Control ID</th>
                <th>Regulation</th>
                <th>Title</th>
                <th>Compliance Status</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>
            {control_rows_html}
        </tbody>
    </table>

    <div class="footer">
        Automated Compliance Mapping Framework | Confidential Board & Regulatory Report
    </div>
</body>
</html>
"""
    return html


def export_executive_summary_to_pdf(
    assessment_data: Dict[str, Any],
    output_path: Optional[Union[str, Path]] = None,
) -> bytes:
    """Export executive report to PDF.

    Uses WeasyPrint if available; otherwise falls back to generating
    the styled HTML report and saving it with .html extension.

    Args:
        assessment_data: Assessment dictionary.
        output_path: Optional output path.

    Returns:
        bytes: PDF bytes or HTML bytes.
    """
    html_content = generate_executive_html_report(assessment_data)

    try:
        from weasyprint import HTML  # type: ignore

        pdf_bytes = bytes(HTML(string=html_content).write_pdf())
        if output_path:
            path = Path(output_path).with_suffix(".pdf")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pdf_bytes)
            logger.info(f"PDF report saved to {path}")
        return pdf_bytes
    except (ImportError, Exception) as exc:
        logger.warning(
            f"WeasyPrint PDF generation not available ({exc}). Falling back to HTML report."
        )
        html_bytes = html_content.encode("utf-8")
        if output_path:
            path = Path(output_path).with_suffix(".html")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(html_bytes)
            logger.info(f"HTML fallback report saved to {path}")
        return html_bytes
