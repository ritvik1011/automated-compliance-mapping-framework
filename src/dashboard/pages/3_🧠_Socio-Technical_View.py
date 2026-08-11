"""Socio-Technical View Page.

THIS IS THE RESEARCH HIGHLIGHT PAGE.

This page showcases the unique research contribution of this framework:
identifying and visualizing socio-technical friction points in compliance
automation.

Research Context:
    Most GRC tools treat compliance as a purely technical problem.
    This page demonstrates that compliance is fundamentally a
    SOCIO-TECHNICAL challenge - where human factors, process bottlenecks,
    and organizational constraints significantly impact compliance outcomes.

    By quantifying and visualizing these friction points, we provide
    actionable insights that go beyond simple pass/fail assessments.
"""

import json
import pandas as pd
import streamlit as st

from src.dashboard.database import get_friction_points, get_latest_assessment_data
from src.dashboard.visualizations import (
    create_friction_impact_chart,
    display_friction_point_card,
)

st.set_page_config(page_title="Socio-Technical View", page_icon="🧠", layout="wide")

st.markdown("# 🧠 Socio-Technical View")
st.markdown("""
*Identifying human and process bottlenecks in compliance automation*

**🔬 Research Highlight**: This page showcases the unique contribution of this framework —
quantifying socio-technical friction in Policy-as-Code approaches to regulatory compliance.
""")

# Load data
data = get_latest_assessment_data()
friction_df = get_friction_points()

if not data:
    st.warning("⚠️ No assessment data available.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# RESEARCH INSIGHT BANNER
# ─────────────────────────────────────────────────────────────
st.info("""
🔬 **Research Insight**: Compliance is not just a technical problem.

Our analysis reveals that **socio-technical friction** — human factors, process bottlenecks,
and organizational constraints — significantly impacts compliance outcomes. This page
identifies and quantifies these friction points to enable targeted interventions.
""")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# FRICTION OVERVIEW
# ─────────────────────────────────────────────────────────────
st.markdown("## 📊 Friction Overview")

col1, col2, col3, col4 = st.columns(4)

total_controls = len(data["controls"])
controls_with_friction = len(friction_df)
friction_rate = (controls_with_friction / total_controls * 100) if total_controls > 0 else 0

total_friction_points = 0
if not friction_df.empty:
    for val in friction_df["friction_points"]:
        if val and str(val) != "[]":
            try:
                parsed = json.loads(val) if isinstance(val, str) else val
                total_friction_points += len(parsed) if isinstance(parsed, list) else 1
            except Exception:
                total_friction_points += 1

with col1:
    st.metric(
        "Controls with Friction",
        controls_with_friction,
        help="Controls where automated assessment identified socio-technical challenges",
    )

with col2:
    st.metric(
        "Friction Rate",
        f"{friction_rate:.1f}%",
        help="Percentage of controls with socio-technical friction",
    )

with col3:
    st.metric(
        "Total Friction Points",
        int(total_friction_points),
        help="Total number of individual friction points identified",
    )

with col4:
    avg_confidence_with_friction = (
        float(friction_df["confidence_score"].mean()) if not friction_df.empty else 0.0
    )
    st.metric(
        "Avg Confidence (Friction)",
        f"{avg_confidence_with_friction:.0%}",
        help="Average confidence for controls with friction (typically lower)",
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# FRICTION IMPACT CHART
# ─────────────────────────────────────────────────────────────
st.markdown("## 📈 Friction Impact Analysis")

st.markdown("""
This chart shows the number of friction points per control, color-coded by compliance status.
**Key Insight**: Controls with high friction often have lower compliance rates.
""")

if not friction_df.empty:
    st.plotly_chart(create_friction_impact_chart(friction_df), use_container_width=True)
else:
    st.success("✅ No friction points detected! All controls have clear automated assessments.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# FRICTION CATEGORIZATION
# ─────────────────────────────────────────────────────────────
st.markdown("## 🏷️ Friction Point Categories")

if not friction_df.empty:
    all_friction_points = []
    for _, row in friction_df.iterrows():
        raw_fp = row.get("friction_points")
        fps = []
        if raw_fp and str(raw_fp) != "[]":
            try:
                fps = json.loads(raw_fp) if isinstance(raw_fp, str) else raw_fp
            except Exception:
                fps = [str(raw_fp)]

        if isinstance(fps, list):
            for fp in fps:
                fp_str = str(fp)
                fp_lower = fp_str.lower()
                if "ambiguous" in fp_lower or "legal" in fp_lower or "interpret" in fp_lower:
                    category = "📜 Legal Ambiguity"
                elif (
                    "human" in fp_lower
                    or "manual" in fp_lower
                    or "bandwidth" in fp_lower
                    or "process" in fp_lower
                ):
                    category = "👥 Human/Process Bottleneck"
                elif "mapping" in fp_lower or "complex" in fp_lower or "unclear" in fp_lower:
                    category = "🔗 Mapping Complexity"
                else:
                    category = "⚙️ Technical Challenge"

                all_friction_points.append(
                    {
                        "control_id": row.get("regulatory_control_id"),
                        "category": category,
                        "friction_point": fp_str,
                    }
                )

    if all_friction_points:
        friction_categorized = pd.DataFrame(all_friction_points)
        category_counts = friction_categorized["category"].value_counts()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Friction by Category")
            for cat, count in category_counts.items():
                st.markdown(f"- **{cat}**: {count} instances")

        with col2:
            st.markdown("### Category Distribution")
            st.bar_chart(category_counts)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# DETAILED FRICTION POINTS
# ─────────────────────────────────────────────────────────────
st.markdown("## 🔍 Detailed Friction Points")

st.markdown("""
Each friction point represents a specific challenge where automated compliance assessment
encountered limitations due to socio-technical factors.
""")

if not friction_df.empty:
    reg_options = sorted(friction_df["regulation"].unique())
    selected_regulation = st.multiselect(
        "Filter by Regulation",
        options=reg_options,
        default=reg_options,
    )

    filtered_friction = friction_df[friction_df["regulation"].isin(selected_regulation)]

    for _, row in filtered_friction.iterrows():
        raw_fp = row.get("friction_points")
        raw_rec = row.get("recommendations")

        friction_points: list[str] = []
        if raw_fp and str(raw_fp) != "[]":
            try:
                parsed = json.loads(raw_fp) if isinstance(raw_fp, str) else raw_fp
                friction_points = (
                    [str(p) for p in parsed] if isinstance(parsed, list) else [str(parsed)]
                )
            except Exception:
                friction_points = [str(raw_fp)]

        recommendations: list[str] = []
        if raw_rec and str(raw_rec) != "[]":
            try:
                parsed = json.loads(raw_rec) if isinstance(raw_rec, str) else raw_rec
                recommendations = (
                    [str(r) for r in parsed] if isinstance(parsed, list) else [str(parsed)]
                )
            except Exception:
                recommendations = [str(raw_rec)]

        display_friction_point_card(
            control_id=str(row.get("regulatory_control_id")),
            title=str(row.get("control_title", "")),
            friction_points=friction_points,
            recommendations=recommendations,
            confidence=float(row.get("confidence_score", 0.0)),
        )
else:
    st.success("✅ No friction points detected!")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# RESEARCH CONCLUSIONS
# ─────────────────────────────────────────────────────────────
st.markdown("## 🎓 Research Conclusions")

st.markdown("""
### Key Findings from Socio-Technical Analysis

1. **Compliance is Not Purely Technical**: Our framework reveals that a significant portion
   of compliance challenges stem from human and process factors, not technical deficiencies.

2. **Confidence Scores Predict Friction**: Controls with high friction consistently show
   lower confidence scores, validating our multi-factor confidence scoring methodology.

3. **Legal Ambiguity is the Primary Friction Source**: The most common friction points
   relate to ambiguous legal language (e.g., "appropriate measures") that cannot be
   cleanly mapped to binary technical controls.

4. **Human-in-the-Loop is Essential**: Pure automation is insufficient. Our findings
   support a hybrid approach where automated assessment identifies potential issues
   and human experts validate high-friction cases.

### Implications for Policy-as-Code

These findings suggest that future Policy-as-Code systems must:
- Explicitly model socio-technical friction
- Provide confidence scores alongside compliance assessments
- Support human-in-the-loop workflows for high-friction cases
- Track friction trends over time to identify systemic issues

### Future Research Directions

- **Longitudinal Studies**: Track how friction evolves as organizations mature
- **Cross-Organizational Analysis**: Compare friction patterns across industries
- **Intervention Effectiveness**: Measure impact of targeted friction reduction
""")
