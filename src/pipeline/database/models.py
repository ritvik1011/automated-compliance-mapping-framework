"""Database Models for Compliance Pipeline.

This module defines SQLAlchemy models for storing compliance assessment
results over time, enabling trend analysis and historical reporting.

Research Context:
    Storing historical compliance data is essential for:
    1. Trend analysis (is compliance improving?)
    2. Audit trails (what was the compliance status on date X?)
    3. KPI calculation over time
    4. Demonstrating continuous monitoring (DORA requirement)
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()


def _utc_now() -> datetime:
    """Return timezone-naive UTC datetime for SQLAlchemy DateTime compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ComplianceAssessment(Base):
    """Represents a single compliance assessment run.

    Each time the pipeline runs, it creates one ComplianceAssessment
    record that contains the overall results and links to individual
    control assessments.
    """

    __tablename__ = "compliance_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_date = Column(DateTime, default=_utc_now, nullable=False)
    baseline_id = Column(String(100), nullable=False)
    catalog_id = Column(String(100), nullable=False)
    cloud_provider = Column(String(50), nullable=False)
    subscription_id = Column(String(100))

    # Overall metrics
    total_regulatory_controls = Column(Integer, default=0)
    total_technical_controls = Column(Integer, default=0)
    compliant_count = Column(Integer, default=0)
    partial_count = Column(Integer, default=0)
    non_compliant_count = Column(Integer, default=0)
    unknown_count = Column(Integer, default=0)
    overall_compliance_score = Column(Float, default=0.0)
    average_confidence_score = Column(Float, default=0.0)

    # Metadata
    assessment_metadata = Column(Text)  # JSON string
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    control_results = relationship(
        "ControlAssessmentResult",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ComplianceAssessment(id={self.id}, date={self.assessment_date})>"


class ControlAssessmentResult(Base):
    """Represents the assessment result for a single regulatory control.

    Each regulatory control gets its own record, allowing granular
    tracking of compliance status over time.
    """

    __tablename__ = "control_assessment_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(
        String(36),
        ForeignKey("compliance_assessments.id"),
        nullable=False,
    )
    regulatory_control_id = Column(String(100), nullable=False)
    regulation = Column(String(50), nullable=False)
    control_title = Column(String(500))

    # Assessment results
    gap_type = Column(String(50), nullable=False)
    compliance_status = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    confidence_level = Column(String(20))

    # Evidence and recommendations
    evidence = Column(Text)  # JSON string
    friction_points = Column(Text)  # JSON string
    recommendations = Column(Text)  # JSON string

    # Metadata
    created_at = Column(DateTime, default=_utc_now)

    # Relationships
    assessment = relationship("ComplianceAssessment", back_populates="control_results")

    def __repr__(self) -> str:
        return (
            f"<ControlAssessmentResult("
            f"control={self.regulatory_control_id}, "
            f"status={self.compliance_status})>"
        )


class ComplianceKPI(Base):
    """Stores calculated KPIs for each assessment.

    KPIs are stored separately to enable easy querying and
    visualization of compliance trends over time.
    """

    __tablename__ = "compliance_kpis"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), nullable=False)
    kpi_name = Column(String(100), nullable=False)
    kpi_value = Column(Float, nullable=False)
    kpi_unit = Column(String(50))  # e.g., "percentage", "count"
    kpi_category = Column(String(50))  # e.g., "overall", "gdpr", "dora"
    calculated_at = Column(DateTime, default=_utc_now)

    def __repr__(self) -> str:
        return f"<ComplianceKPI(name={self.kpi_name}, value={self.kpi_value})>"


def init_db(database_url: str = "sqlite:///compliance.db") -> None:
    """Initialize the database and create all tables.

    Args:
        database_url: SQLAlchemy database URL
            - SQLite: "sqlite:///compliance.db"
            - PostgreSQL: "postgresql://user:pass@localhost/dbname"
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    print(f"✓ Database initialized at {database_url}")


def get_engine(database_url: str = "sqlite:///compliance.db"):
    """Get a SQLAlchemy engine."""
    return create_engine(database_url, echo=False)


def get_session(database_url: str = "sqlite:///compliance.db") -> Session:
    """Get a SQLAlchemy session."""
    from sqlalchemy.orm import sessionmaker

    engine = get_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    return session_factory()
