"""Technical View Page.

This page provides detailed compliance heatmaps and technical breakdowns
for security engineers and compliance officers.
"""

import streamlit as st

from src.dashboard.database import (
    get_compliance_by_category,
    get_compliance_by_regulation,
    get_latest_assessment_data,
)
from src.dashboard.visualizations import (
    create_compliance_heatmap,
    create_confidence_scatter,
)

st.set_page_config(page_title="Technical View", page_icon="🔍", layout="wide")

st.markdown("# 🔍 Technical View")
st.markdown("*Detailed compliance analysis for security engineers and compliance officers*")

# Load data
data = get_latest_assessment_data()
regulation_data = get_compliance_by_regulation()
category_data = get_compliance_by_category()

if not data:
    st.warning("⚠️ No assessment data available.")
    st.stop()

controls_df = data["controls"]

# ─────────────────────────────────────────────────────────────
# FILTERS
# ─────────────────────────────────────────────────────────────
st.markdown("## 🔎 Filters")

col1, col2, col3 = st.columns(3)

reg_options = sorted(controls_df["regulation"].unique()) if not controls_df.empty else []
status_options = sorted(controls_df["compliance_status"].unique()) if not controls_df.empty else []

with col1:
    selected_regulation = st.multiselect(
        "Filter by Regulation",
        options=reg_options,
        default=reg_options,
    )

with col2:
    selected_status = st.multiselect(
        "Filter by Status",
        options=status_options,
        default=status_options,
    )

with col3:
    min_confidence = st.slider(
        "Minimum Confidence Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
    )

# Apply filters
filtered_df = controls_df[
    (controls_df["regulation"].isin(selected_regulation))
    & (controls_df["compliance_status"].isin(selected_status))
    & (controls_df["confidence_score"] >= min_confidence)
]

st.markdown(f"*Showing {len(filtered_df)} of {len(controls_df)} controls*")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# HEATMAP
# ─────────────────────────────────────────────────────────────
st.markdown("## 🗺️ Compliance Heatmap")

heatmap_data = filtered_df.copy()
if not heatmap_data.empty:

    def extract_category(control_id: str) -> str:
        control_lower = str(control_id).lower()
        if "encryption" in control_lower or "keyvault" in control_lower:
            return "Encryption"
        elif "nsg" in control_lower or "network" in control_lower or "publicip" in control_lower:
            return "Network"
        elif (
            "identity" in control_lower
            or "managed-identity" in control_lower
            or "iam" in control_lower
        ):
            return "IAM"
        elif "redundancy" in control_lower or "backup" in control_lower:
            return "Backup"
        else:
            return "Other"

    heatmap_data["category"] = heatmap_data["regulatory_control_id"].apply(extract_category)

    heatmap_summary = (
        heatmap_data.groupby(["regulation", "category"])
        .agg(compliance_rate=("compliance_status", lambda s: (s == "compliant").mean() * 100))
        .reset_index()
    )

    if not heatmap_summary.empty:
        st.plotly_chart(create_compliance_heatmap(heatmap_summary), use_container_width=True)
    else:
        st.info("No data available for heatmap with current filters.")
else:
    st.info("No data available for heatmap with current filters.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# CONFIDENCE SCATTER
# ─────────────────────────────────────────────────────────────
st.markdown("## 🎯 Confidence Score Analysis")

st.markdown("""
This visualization shows the relationship between confidence scores and compliance status.
**Low confidence + non-compliant** controls require immediate human review.
""")

st.plotly_chart(create_confidence_scatter(filtered_df), use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# DETAILED TABLE
# ─────────────────────────────────────────────────────────────
st.markdown("## 📋 Detailed Control View")

display_columns = [
    c
    for c in [
        "regulatory_control_id",
        "regulation",
        "control_title",
        "compliance_status",
        "confidence_score",
        "gap_type",
    ]
    if c in filtered_df.columns
]

if not filtered_df.empty:
    st.dataframe(
        filtered_df[display_columns].sort_values("confidence_score"),
        use_container_width=True,
        height=400,
    )
else:
    st.info("No controls match the selected filters.")
