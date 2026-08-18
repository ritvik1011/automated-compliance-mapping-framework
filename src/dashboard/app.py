"""Compliance Dashboard - Main Application.

This is the entry point for the Streamlit dashboard. It sets up the
page configuration and provides navigation to the multi-page app.

Research Context:
    This dashboard represents the culmination of the research framework,
    translating complex compliance data into actionable insights for
    non-technical stakeholders. It demonstrates the viability of
    Policy-as-Code approaches for regulatory compliance.

Usage:
    streamlit run src/dashboard/app.py
"""

import sys
from pathlib import Path

# Add project root directory to sys.path before any local imports
# Hierarchy: app.py -> src/dashboard -> src -> project_root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.dashboard.database import get_latest_assessment_data
from src.dashboard.export import export_assessment_to_excel, generate_executive_html_report

# Configure page
st.set_page_config(
    page_title="Compliance Monitoring Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main entry point for the dashboard."""
    st.title("🛡️ Automated Compliance Monitoring Dashboard")

    st.markdown("""
    Welcome to the **Automated Compliance Mapping & Gap Analysis Framework** dashboard.

    This dashboard provides real-time visibility into your organization's compliance posture
    across **GDPR, DORA, and NIS2** regulations.

    ### 📚 Navigation

    Use the sidebar to navigate between different views:

    - **📊 Executive Summary**: High-level KPIs for leadership
    - **🔍 Technical View**: Detailed compliance heatmaps
    - **🧠 Socio-Technical View**: Friction points analysis *(Research Highlight)*
    - **📈 Trend Analysis**: Compliance over time
    - **📋 Detailed Controls**: Drill-down into specific controls

    ### 🎯 Key Features

    - ✅ Real-time compliance monitoring
    - ✅ Confidence scoring for automated assessments
    - ✅ Socio-technical friction identification
    - ✅ Trend analysis and historical tracking
    - ✅ Export to PDF/Excel for board reporting

    ---

    *Built with Python, Streamlit, and Policy-as-Code principles.*
    """)

    # Quick stats from latest assessment
    st.markdown("### 📊 Latest Assessment Snapshot")

    data = get_latest_assessment_data()

    if data:
        assessment = data["assessment"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Overall Compliance",
                f"{assessment['overall_compliance_score']:.1f}%",
            )

        with col2:
            st.metric(
                "Controls Analyzed",
                assessment["total_regulatory_controls"],
            )

        with col3:
            st.metric(
                "Avg Confidence",
                f"{assessment['average_confidence_score']:.0%}",
            )

        with col4:
            st.metric(
                "Cloud Provider",
                str(assessment["cloud_provider"]).upper(),
            )

        st.markdown("---")
        st.markdown("### 📥 Quick Export")
        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            excel_bytes = export_assessment_to_excel(data)
            st.download_button(
                label="📊 Download Excel Report (.xlsx)",
                data=excel_bytes,
                file_name=f"compliance_report_{assessment.get('id', 'latest')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with exp_col2:
            html_report = generate_executive_html_report(data)
            st.download_button(
                label="📄 Download Executive Report (.html)",
                data=html_report,
                file_name=f"executive_summary_{assessment.get('id', 'latest')}.html",
                mime="text/html",
            )
    else:
        st.warning("⚠️ No assessment data found. Please run the pipeline first.")

    st.markdown("---")
    st.markdown("*Select a page from the sidebar to explore detailed views.*")


if __name__ == "__main__":
    main()
