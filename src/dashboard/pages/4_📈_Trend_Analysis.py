"""Trend Analysis Page.

This page shows compliance trends over time, enabling continuous
monitoring and demonstrating DORA/NIS2 compliance.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path before any local imports
# Hierarchy: page.py -> pages -> dashboard -> src -> project_root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.dashboard.database import (
    get_all_assessments_summary,
    get_kpi_trend,
)
from src.dashboard.visualizations import create_trend_line_chart

st.set_page_config(page_title="Trend Analysis", page_icon="📈", layout="wide")

st.markdown("# 📈 Trend Analysis")
st.markdown("*Compliance trends over time for continuous monitoring*")

# Load data
assessments_summary = get_all_assessments_summary()

if assessments_summary.empty:
    st.warning("⚠️ No historical assessment data available.")
    st.info("Run the compliance pipeline multiple times to see trends.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# OVERALL COMPLIANCE TREND
# ─────────────────────────────────────────────────────────────
st.markdown("## 📊 Overall Compliance Trend")

trend_df = assessments_summary.copy()
if "overall_compliance_score" in trend_df.columns:
    trend_df["kpi_value"] = trend_df["overall_compliance_score"]

st.plotly_chart(
    create_trend_line_chart(trend_df, "Overall Compliance Score"),
    use_container_width=True,
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# KPI-SPECIFIC TRENDS
# ─────────────────────────────────────────────────────────────
st.markdown("## 🎯 KPI-Specific Trends")

selected_kpi = st.selectbox(
    "Select KPI to analyze",
    options=[
        "overall_compliance_rate",
        "gdpr_compliance_rate",
        "dora_compliance_rate",
        "nis2_compliance_rate",
        "average_confidence_score",
        "high_confidence_percentage",
        "friction_rate",
    ],
    index=0,
)

kpi_name = str(selected_kpi) if selected_kpi else "overall_compliance_rate"
kpi_trend = get_kpi_trend(kpi_name)

if not kpi_trend.empty:
    st.plotly_chart(
        create_trend_line_chart(kpi_trend, kpi_name),
        use_container_width=True,
    )
else:
    st.info(f"No trend data available for {kpi_name}")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# ASSESSMENT HISTORY TABLE
# ─────────────────────────────────────────────────────────────
st.markdown("## 📋 Assessment History")

st.dataframe(
    assessments_summary,
    use_container_width=True,
    height=400,
)
