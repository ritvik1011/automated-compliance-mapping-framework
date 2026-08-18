"""Detailed Controls Page.

This page provides drill-down into specific controls for deep analysis.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path before any local imports
# Hierarchy: page.py -> pages -> dashboard -> src -> project_root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import streamlit as st

from src.dashboard.database import get_latest_assessment_data

st.set_page_config(page_title="Detailed Controls", page_icon="📋", layout="wide")

st.markdown("# 📋 Detailed Controls")
st.markdown("*Drill-down into specific regulatory controls*")

# Load data
data = get_latest_assessment_data()

if not data:
    st.warning("⚠️ No assessment data available.")
    st.stop()

controls_df = data["controls"]

# ─────────────────────────────────────────────────────────────
# SEARCH AND FILTER
# ─────────────────────────────────────────────────────────────
st.markdown("## 🔎 Search & Filter")

col1, col2 = st.columns(2)

with col1:
    search_term = st.text_input("Search by Control ID or Title", "")

with col2:
    status_options = (
        sorted(controls_df["compliance_status"].unique()) if not controls_df.empty else []
    )
    status_filter = st.multiselect(
        "Filter by Status",
        options=status_options,
        default=status_options,
    )

# Apply filters
filtered_df = controls_df.copy()

if search_term:
    filtered_df = filtered_df[
        filtered_df["regulatory_control_id"].str.contains(search_term, case=False, na=False)
        | filtered_df["control_title"].str.contains(search_term, case=False, na=False)
    ]

filtered_df = filtered_df[filtered_df["compliance_status"].isin(status_filter)]

st.markdown(f"*Showing {len(filtered_df)} controls*")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# CONTROL DETAILS
# ─────────────────────────────────────────────────────────────
st.markdown("## 📊 Control Details")

for _, row in filtered_df.iterrows():
    status_emoji = {
        "compliant": "✅",
        "partial": "⚠️",
        "non-compliant": "❌",
        "unknown": "❓",
    }.get(str(row["compliance_status"]).lower(), "❓")

    title_text = row.get("control_title") or "Untitled Control"
    control_id = row.get("regulatory_control_id")

    with st.expander(f"{status_emoji} {control_id}: {title_text}"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Regulation**: {row.get('regulation')}")
            st.markdown(f"**Gap Type**: {row.get('gap_type')}")

        with col2:
            st.markdown(f"**Status**: {str(row.get('compliance_status')).upper()}")
            st.markdown(f"**Confidence**: {float(row.get('confidence_score', 0)):.0%}")

        with col3:
            st.markdown(f"**Confidence Level**: {row.get('confidence_level')}")

        # Evidence
        raw_ev = row.get("evidence")
        if raw_ev and str(raw_ev) != "[]":
            st.markdown("**Evidence**:")
            try:
                evidence = json.loads(raw_ev) if isinstance(raw_ev, str) else raw_ev
                if isinstance(evidence, list):
                    for ev in evidence:
                        st.json(ev)
                else:
                    st.json(evidence)
            except Exception:
                st.write(str(raw_ev))

        # Friction points
        raw_fp = row.get("friction_points")
        if raw_fp and str(raw_fp) != "[]":
            st.markdown("**Socio-Technical Friction Points**:")
            try:
                friction = json.loads(raw_fp) if isinstance(raw_fp, str) else raw_fp
                if isinstance(friction, list):
                    for fp in friction:
                        st.markdown(f"- ⚠️ {fp}")
                else:
                    st.markdown(f"- ⚠️ {friction}")
            except Exception:
                st.markdown(f"- ⚠️ {raw_fp}")

        # Recommendations
        raw_rec = row.get("recommendations")
        if raw_rec and str(raw_rec) != "[]":
            st.markdown("**Recommendations**:")
            try:
                recs = json.loads(raw_rec) if isinstance(raw_rec, str) else raw_rec
                if isinstance(recs, list):
                    for rec in recs:
                        st.markdown(f"- 💡 {rec}")
                else:
                    st.markdown(f"- 💡 {recs}")
            except Exception:
                st.markdown(f"- 💡 {raw_rec}")
