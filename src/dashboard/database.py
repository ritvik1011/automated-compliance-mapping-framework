"""Dashboard Database Connection Layer.

This module provides Streamlit-optimized database access with caching
for efficient dashboard performance.

Research Context:
    Efficient data access is crucial for dashboard responsiveness.
    By caching database queries, we ensure that the dashboard remains
    usable even with large historical datasets.
"""

import logging
from typing import Dict, Optional

import pandas as pd
import streamlit as st
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from src.pipeline.database.models import get_engine

logger = logging.getLogger(__name__)


@st.cache_resource
def get_db_engine(database_url: str = "sqlite:///compliance.db"):
    """Get a cached SQLAlchemy engine.

    Using @st.cache_resource ensures the engine is created once
    and reused across dashboard sessions.
    """
    return get_engine(database_url)


@st.cache_resource
def get_session_factory(database_url: str = "sqlite:///compliance.db"):
    """Get a cached session factory."""
    engine = get_db_engine(database_url)
    return sessionmaker(bind=engine)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_assessment_data(database_url: str = "sqlite:///compliance.db") -> Optional[Dict]:
    """Get the latest compliance assessment data.

    Returns:
        Dictionary with assessment summary and control results, or None if empty.
    """
    engine = get_db_engine(database_url)

    try:
        with engine.connect() as conn:
            # Get latest assessment
            assessment_query = text("""
                SELECT * FROM compliance_assessments
                ORDER BY assessment_date DESC
                LIMIT 1
            """)
            assessment_df = pd.read_sql(assessment_query, conn)

            if assessment_df.empty:
                return None

            assessment_id = assessment_df.iloc[0]["id"]

            # Get control results for this assessment
            controls_query = text("""
                SELECT * FROM control_assessment_results
                WHERE assessment_id = :assessment_id
            """)
            controls_df = pd.read_sql(controls_query, conn, params={"assessment_id": assessment_id})

            # Get KPIs for this assessment
            kpis_query = text("""
                SELECT * FROM compliance_kpis
                WHERE assessment_id = :assessment_id
            """)
            kpis_df = pd.read_sql(kpis_query, conn, params={"assessment_id": assessment_id})

        return {
            "assessment": assessment_df.iloc[0].to_dict(),
            "controls": controls_df,
            "kpis": kpis_df,
        }
    except Exception as exc:
        logger.warning(f"Error fetching latest assessment data: {exc}")
        return None


@st.cache_data(ttl=300)
def get_all_assessments_summary(database_url: str = "sqlite:///compliance.db") -> pd.DataFrame:
    """Get summary of all assessments for trend analysis.

    Returns:
        DataFrame with assessment dates and overall scores
    """
    engine = get_db_engine(database_url)

    query = text("""
        SELECT
            assessment_date,
            cloud_provider,
            total_regulatory_controls,
            compliant_count,
            partial_count,
            non_compliant_count,
            unknown_count,
            overall_compliance_score,
            average_confidence_score
        FROM compliance_assessments
        ORDER BY assessment_date DESC
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as exc:
        logger.warning(f"Error querying assessments summary: {exc}")
        return pd.DataFrame(
            columns=[
                "assessment_date",
                "cloud_provider",
                "total_regulatory_controls",
                "compliant_count",
                "partial_count",
                "non_compliant_count",
                "unknown_count",
                "overall_compliance_score",
                "average_confidence_score",
            ]
        )


@st.cache_data(ttl=300)
def get_kpi_trend(kpi_name: str, database_url: str = "sqlite:///compliance.db") -> pd.DataFrame:
    """Get historical trend for a specific KPI.

    Args:
        kpi_name: Name of the KPI (e.g., "overall_compliance_rate")
        database_url: SQLAlchemy database URL

    Returns:
        DataFrame with dates and KPI values
    """
    engine = get_db_engine(database_url)

    query = text("""
        SELECT
            k.calculated_at,
            k.kpi_value,
            k.kpi_category,
            a.assessment_date
        FROM compliance_kpis k
        JOIN compliance_assessments a ON k.assessment_id = a.id
        WHERE k.kpi_name = :kpi_name
        ORDER BY k.calculated_at ASC
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"kpi_name": kpi_name})
        return df
    except Exception as exc:
        logger.warning(f"Error fetching KPI trend for {kpi_name}: {exc}")
        return pd.DataFrame(
            columns=["calculated_at", "kpi_value", "kpi_category", "assessment_date"]
        )


@st.cache_data(ttl=300)
def get_friction_points(database_url: str = "sqlite:///compliance.db") -> pd.DataFrame:
    """Get all friction points from the latest assessment.

    This is a KEY research function - it extracts the socio-technical
    friction data that is the core contribution of this framework.

    Returns:
        DataFrame with friction points and their context
    """
    engine = get_db_engine(database_url)

    query = text("""
        SELECT
            regulatory_control_id,
            regulation,
            control_title,
            compliance_status,
            confidence_score,
            friction_points,
            recommendations,
            gap_type
        FROM control_assessment_results
        WHERE assessment_id = (
            SELECT id FROM compliance_assessments
            ORDER BY assessment_date DESC LIMIT 1
        )
        AND friction_points != '[]'
        AND friction_points IS NOT NULL
        ORDER BY confidence_score ASC
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as exc:
        logger.warning(f"Error querying friction points: {exc}")
        return pd.DataFrame(
            columns=[
                "regulatory_control_id",
                "regulation",
                "control_title",
                "compliance_status",
                "confidence_score",
                "friction_points",
                "recommendations",
                "gap_type",
            ]
        )


@st.cache_data(ttl=300)
def get_compliance_by_regulation(database_url: str = "sqlite:///compliance.db") -> pd.DataFrame:
    """Get compliance breakdown by regulation."""
    engine = get_db_engine(database_url)

    query = text("""
        SELECT
            regulation,
            COUNT(*) as total_controls,
            SUM(CASE WHEN compliance_status = 'compliant' THEN 1 ELSE 0 END) as compliant,
            SUM(CASE WHEN compliance_status = 'partial' THEN 1 ELSE 0 END) as partial,
            SUM(CASE WHEN compliance_status = 'non-compliant' THEN 1 ELSE 0 END) as non_compliant,
            AVG(confidence_score) as avg_confidence
        FROM control_assessment_results
        WHERE assessment_id = (
            SELECT id FROM compliance_assessments
            ORDER BY assessment_date DESC LIMIT 1
        )
        GROUP BY regulation
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as exc:
        logger.warning(f"Error querying compliance by regulation: {exc}")
        return pd.DataFrame(
            columns=[
                "regulation",
                "total_controls",
                "compliant",
                "partial",
                "non_compliant",
                "avg_confidence",
            ]
        )


@st.cache_data(ttl=300)
def get_compliance_by_category(database_url: str = "sqlite:///compliance.db") -> pd.DataFrame:
    """Get compliance breakdown by control category."""
    data = get_latest_assessment_data(database_url)
    if not data or data["controls"].empty:
        return pd.DataFrame(
            columns=["category", "total_controls", "compliant_count", "avg_confidence"]
        )

    controls_df = data["controls"].copy()

    # Extract category from control ID (heuristic)
    def extract_category(control_id: str) -> str:
        control_lower = str(control_id).lower()
        if "encryption" in control_lower or "keyvault" in control_lower:
            return "Encryption"
        elif "nsg" in control_lower or "network" in control_lower or "publicip" in control_lower:
            return "Network Security"
        elif (
            "identity" in control_lower
            or "managed-identity" in control_lower
            or "iam" in control_lower
        ):
            return "Identity & Access"
        elif "redundancy" in control_lower or "backup" in control_lower:
            return "Backup & Recovery"
        else:
            return "Other"

    controls_df["category"] = controls_df["regulatory_control_id"].apply(extract_category)

    summary = (
        controls_df.groupby("category")
        .agg(
            total_controls=("regulatory_control_id", "count"),
            compliant_count=("compliance_status", lambda x: (x == "compliant").sum()),
            avg_confidence=("confidence_score", "mean"),
        )
        .reset_index()
    )

    return summary
