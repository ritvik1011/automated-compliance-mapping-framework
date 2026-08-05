"""Dashboard Visualization Functions.

This module provides reusable visualization functions for the compliance
dashboard. All charts are built with Plotly for interactivity.

Research Context:
    Effective visualization is crucial for communicating complex compliance
    data to non-technical stakeholders. The visualizations in this module
    are designed to:
    1. Present information at a glance (executive view)
    2. Enable drill-down for technical teams
    3. Highlight socio-technical friction points (research contribution)
    4. Show trends over time for continuous monitoring
"""

import json
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Re-export get_compliance_by_category for convenience across pages
from src.dashboard.database import get_compliance_by_category  # noqa: F401


def _get_score_color(score: float) -> str:
    """Get color based on compliance score."""
    if score >= 85:
        return "#00cc44"
    elif score >= 70:
        return "#88cc00"
    elif score >= 50:
        return "#ffaa00"
    else:
        return "#ff4444"


def create_compliance_gauge(score: float, title: str = "Overall Compliance") -> go.Figure:
    """Create a gauge chart showing compliance percentage.

    Args:
        score: Compliance score (0-100)
        title: Chart title

    Returns:
        Plotly Figure object
    """
    safe_score = max(0.0, min(100.0, float(score)))

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=safe_score,
            title={"text": title, "font": {"size": 22}},
            delta={
                "reference": 80,
                "increasing": {"color": "green"},
                "decreasing": {"color": "red"},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": _get_score_color(safe_score)},
                "steps": [
                    {"range": [0, 50], "color": "#ffe5e5"},
                    {"range": [50, 70], "color": "#fff3cd"},
                    {"range": [70, 85], "color": "#e8f5e9"},
                    {"range": [85, 100], "color": "#c8e6c9"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": 80,
                },
            },
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_compliance_heatmap(data: pd.DataFrame) -> go.Figure:
    """Create a heatmap showing compliance status by regulation and category.

    Args:
        data: DataFrame with regulation, category, and compliance data

    Returns:
        Plotly Figure object
    """
    if data.empty or "regulation" not in data.columns or "category" not in data.columns:
        fig = go.Figure()
        fig.update_layout(
            title="Compliance Heatmap (No Data Available)",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    pivot_data = data.pivot_table(
        index="regulation",
        columns="category",
        values="compliance_rate",
        aggfunc="mean",
        fill_value=0,
    )

    fig = px.imshow(
        pivot_data,
        text_auto=".0f",
        color_continuous_scale=["#ff4444", "#ffaa00", "#88cc00", "#00cc44"],
        labels={"color": "Compliance %"},
        title="Compliance Heatmap by Regulation and Category",
        aspect="auto",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_regulation_breakdown_chart(data: pd.DataFrame) -> go.Figure:
    """Create a stacked bar chart showing compliance breakdown by regulation.

    Args:
        data: DataFrame with regulation and compliance counts

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    if data.empty:
        fig.update_layout(
            title="Compliance Status by Regulation (No Data)",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    fig.add_trace(
        go.Bar(
            name="Compliant",
            x=data["regulation"],
            y=data.get("compliant", 0),
            marker_color="#00cc44",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Partial",
            x=data["regulation"],
            y=data.get("partial", 0),
            marker_color="#ffaa00",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Non-Compliant",
            x=data["regulation"],
            y=data.get("non_compliant", 0),
            marker_color="#ff4444",
        )
    )

    fig.update_layout(
        barmode="stack",
        title="Compliance Status by Regulation",
        xaxis_title="Regulation",
        yaxis_title="Number of Controls",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_confidence_scatter(data: pd.DataFrame) -> go.Figure:
    """Create a scatter plot showing confidence scores vs compliance status.

    This visualization helps identify controls where low confidence
    correlates with compliance issues - a key research insight.

    Args:
        data: DataFrame with control data

    Returns:
        Plotly Figure object
    """
    if data.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Confidence Score vs Compliance Status (No Data)",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    color_map = {
        "compliant": "#00cc44",
        "partial": "#ffaa00",
        "non-compliant": "#ff4444",
        "unknown": "#888888",
    }

    hover_cols = [
        c for c in ["control_title", "regulation", "friction_points"] if c in data.columns
    ]

    fig = px.scatter(
        data,
        x="regulatory_control_id",
        y="confidence_score",
        color="compliance_status",
        color_discrete_map=color_map,
        hover_data=hover_cols,
        title="Confidence Score vs Compliance Status",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_tickangle=-45,
    )

    return fig


def create_trend_line_chart(data: pd.DataFrame, kpi_name: str) -> go.Figure:
    """Create a line chart showing KPI trend over time.

    Args:
        data: DataFrame with dates and KPI values
        kpi_name: Name of the KPI being plotted

    Returns:
        Plotly Figure object
    """
    if data.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"{kpi_name.replace('_', ' ').title()} Trend (No Data)",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    # Determine x column
    date_col = "assessment_date"
    if date_col not in data.columns:
        if "date" in data.columns:
            date_col = "date"
        elif "calculated_at" in data.columns:
            date_col = "calculated_at"
        else:
            date_col = data.columns[0]

    val_col = "kpi_value" if "kpi_value" in data.columns else data.columns[1]

    fig = px.line(
        data,
        x=date_col,
        y=val_col,
        markers=True,
        title=f"{kpi_name.replace('_', ' ').title()} Trend",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Value",
    )

    # Add reference line at 80% if scale looks percentage-based
    max_val = data[val_col].max() if not data.empty else 0
    if max_val <= 100:
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="gray",
            annotation_text="Target: 80%",
        )

    return fig


def create_friction_impact_chart(data: pd.DataFrame) -> go.Figure:
    """Create a chart showing the impact of friction points on compliance.

    This is a KEY research visualization - it shows the correlation
    between socio-technical friction and compliance outcomes.

    Args:
        data: DataFrame with friction data

    Returns:
        Plotly Figure object
    """
    if data.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Friction Points per Control (No Data)",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    data = data.copy()

    def parse_count(val):
        if not val or val == "[]":
            return 0
        if isinstance(val, list):
            return len(val)
        try:
            parsed = json.loads(val)
            return len(parsed) if isinstance(parsed, list) else 0
        except Exception:
            return 1

    data["friction_count"] = data["friction_points"].apply(parse_count)

    color_map = {
        "compliant": "#00cc44",
        "partial": "#ffaa00",
        "non-compliant": "#ff4444",
        "unknown": "#888888",
    }

    fig = px.bar(
        data,
        x="regulatory_control_id",
        y="friction_count",
        color="compliance_status",
        color_discrete_map=color_map,
        title="Friction Points per Control (Research Insight)",
        labels={"friction_count": "Number of Friction Points"},
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_tickangle=-45,
    )

    return fig


def create_category_pie_chart(data: pd.DataFrame) -> go.Figure:
    """Create a pie chart showing controls by category."""
    if data.empty or "total_controls" not in data.columns or data["total_controls"].sum() == 0:
        fig = go.Figure()
        fig.update_layout(
            title="Controls by Category (No Data)",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    fig = px.pie(
        data,
        values="total_controls",
        names="category",
        title="Controls by Category",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def display_kpi_card(title: str, value: float, unit: str = "%", delta: Optional[float] = None):
    """Display a KPI metric card in the dashboard.

    Args:
        title: KPI title
        value: KPI value
        unit: Unit of measurement
        delta: Change from previous period (optional)
    """
    col = st.container()
    with col:
        st.metric(
            label=title,
            value=f"{value:.1f}{unit}",
            delta=f"{delta:+.1f}{unit}" if delta is not None else None,
        )


def display_friction_point_card(
    control_id: str,
    title: str,
    friction_points: List[str],
    recommendations: List[str],
    confidence: float,
):
    """Display a friction point card with context and recommendations.

    This is a KEY research component - it presents socio-technical
    friction in a way that non-technical stakeholders can understand.
    """
    with st.expander(f"🔴 {control_id}: {title} (Confidence: {confidence:.0%})", expanded=False):
        st.markdown("**Socio-Technical Friction Points:**")
        if friction_points:
            for fp in friction_points:
                st.markdown(f"- ⚠️ {fp}")
        else:
            st.markdown("_No specific friction points documented._")

        st.markdown("**Recommendations:**")
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- 💡 {rec}")
        else:
            st.markdown("_No specific recommendations documented._")

        # Visual indicator of friction severity
        friction_severity = (
            "High" if len(friction_points) > 2 else "Medium" if len(friction_points) > 0 else "Low"
        )
        st.markdown(f"**Friction Severity**: {friction_severity}")
