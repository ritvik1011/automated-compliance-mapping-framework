"""Executive Summary Page.

This page provides high-level KPIs for CISOs, DPOs, and board members.
It focuses on what matters most: overall compliance, risk exposure,
and key trends.

Research Context:
    This page demonstrates the "translation layer" between technical
    compliance data and executive decision-making - a core research
    contribution of this framework.
"""

import streamlit as st
import pandas as pd

from src.dashboard.database import (
    get_latest_assessment_data,
    get_all_assessments_summary,
    get_compliance_by_regulation,
    get_compliance_by_category,
)
from src.dashboard.visualizations import (
    create_compliance_gauge,
    create_regulation_breakdown_chart,
    create_category_pie_chart,
)
from src.dashboard.export import export_assessment_to_excel, generate_executive_html_report

st.set_page_config(page_title="Executive Summary", page_icon="📊", layout="wide")

st.markdown("# 📊 Executive Summary")
st.markdown("*High-level compliance metrics for leadership and board reporting*")

# Load data
data = get_latest_assessment_data()
assessments_summary = get_all_assessments_summary()
regulation_data = get_compliance_by_regulation()
category_data = get_compliance_by_category()

if not data:
    st.warning("⚠️ No assessment data available. Please run the compliance pipeline first.")
    st.stop()

assessment = data["assessment"]
controls_df = data["controls"]
kpis_df = data["kpis"]

total_controls = assessment.get("total_regulatory_controls", len(controls_df))
compliant_count = assessment.get("compliant_count", 0)
partial_count = assessment.get("partial_count", 0)
non_compliant_count = assessment.get("non_compliant_count", 0)
score = assessment.get("overall_compliance_score", 0.0)
avg_confidence = assessment.get("average_confidence_score", 0.0)

# ─────────────────────────────────────────────────────────────
# TOP ROW: Key Metrics
# ─────────────────────────────────────────────────────────────
st.markdown("## 🎯 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.plotly_chart(
        create_compliance_gauge(score, "Overall Compliance"),
        use_container_width=True,
    )

with col2:
    st.metric(
        "Total Controls",
        total_controls,
        help="Number of regulatory controls analyzed",
    )

with col3:
    compliant_pct = (compliant_count / total_controls * 100) if total_controls > 0 else 0
    st.metric(
        "✅ Compliant",
        compliant_count,
        delta=f"{compliant_pct:.1f}%",
    )

with col4:
    st.metric(
        "⚠️ Partial",
        partial_count,
    )

with col5:
    st.metric(
        "❌ Non-Compliant",
        non_compliant_count,
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# MIDDLE ROW: Regulation Breakdown
# ─────────────────────────────────────────────────────────────
st.markdown("## 📋 Compliance by Regulation")

col1, col2 = st.columns(2)

with col1:
    if not regulation_data.empty:
        st.plotly_chart(
            create_regulation_breakdown_chart(regulation_data),
            use_container_width=True,
        )
    else:
        st.info("No regulation breakdown data available.")

with col2:
    if not category_data.empty:
        st.plotly_chart(
            create_category_pie_chart(category_data),
            use_container_width=True,
        )
    else:
        st.info("No category breakdown data available.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# BOTTOM ROW: Regulation-Specific KPIs
# ─────────────────────────────────────────────────────────────
st.markdown("## 🎯 Regulation-Specific Compliance Rates")

col1, col2, col3 = st.columns(3)

for reg_col, regulation in zip([col1, col2, col3], ["GDPR", "DORA", "NIS2"]):
    with reg_col:
        reg_kpi = pd.DataFrame()
        if not kpis_df.empty and "kpi_name" in kpis_df.columns:
            reg_kpi = kpis_df[kpis_df["kpi_name"] == f"{regulation.lower()}_compliance_rate"]

        if not reg_kpi.empty:
            rate = float(reg_kpi.iloc[0]["kpi_value"])
            st.plotly_chart(
                create_compliance_gauge(rate, f"{regulation} Compliance"),
                use_container_width=True,
            )
        else:
            # Fallback calculate from controls_df if available
            reg_controls = (
                controls_df[controls_df["regulation"].str.upper() == regulation.upper()]
                if not controls_df.empty and "regulation" in controls_df.columns
                else pd.DataFrame()
            )
            if not reg_controls.empty:
                comp = (reg_controls["compliance_status"] == "compliant").sum()
                rate = (comp / len(reg_controls)) * 100.0
                st.plotly_chart(
                    create_compliance_gauge(rate, f"{regulation} Compliance"),
                    use_container_width=True,
                )
            else:
                st.info(f"No {regulation} data available")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# EXECUTIVE SUMMARY TEXT & EXPORT
# ─────────────────────────────────────────────────────────────
st.markdown("## 📝 Executive Summary")

compliance_status = (
    "✅ **STRONG**" if score >= 80 else "⚠️ **MODERATE**" if score >= 60 else "❌ **AT RISK**"
)

confidence_desc = (
    "high" if avg_confidence >= 0.7 else "moderate" if avg_confidence >= 0.5 else "low"
)
rec_1 = "✅ Continue current compliance program" if score >= 80 else "⚠️ Focus on partial controls"
rec_2 = "✅ Maintain monitoring cadence" if score >= 80 else "🔴 Address non-compliant controls"

st.markdown(f"""
**Overall Compliance Status**: {compliance_status}

**Key Findings**:
- Your organization is currently at **{score:.1f}%** overall compliance
- **{compliant_count}** controls are fully compliant
- **{partial_count}** controls require attention (partial compliance)
- **{non_compliant_count}** controls are non-compliant and need immediate action

**Confidence Assessment**:
- Average confidence score: **{avg_confidence:.0%}**
- This indicates {confidence_desc} reliability in the automated assessments

**Recommendations**:
1. {rec_1}
2. {rec_2}
3. 📋 Review socio-technical friction points for process improvements
""")

st.markdown("---")
st.markdown("## 📥 Export Executive Report")
exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    excel_bytes = export_assessment_to_excel(data)
    st.download_button(
        label="📊 Download Board Excel Pack (.xlsx)",
        data=excel_bytes,
        file_name=f"board_compliance_pack_{assessment.get('id', 'latest')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with exp_col2:
    html_report = generate_executive_html_report(data)
    st.download_button(
        label="📄 Download Executive Summary (.html)",
        data=html_report,
        file_name=f"executive_summary_{assessment.get('id', 'latest')}.html",
        mime="text/html",
    )
