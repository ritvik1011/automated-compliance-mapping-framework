"""
Demo Data Population Script
This script generates realistic mock data for the compliance dashboard,
including socio-technical friction points for the research highlight.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Configure UTF-8 encoding for Windows console to handle emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

# 1. Fix Python Path (Same fix we used for the dashboard)
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 2. Import Database Models and Setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.pipeline.database.models import (
    Base, 
    ComplianceAssessment, 
    ControlAssessmentResult, 
    ComplianceKPI
)

# Database URL (Must match the dashboard's database.py)
DATABASE_URL = "sqlite:///compliance.db"

def populate_data():
    print("🚀 Starting demo data population...")
    
    # Create engine and tables
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Clear existing data (optional, keeps things clean)
    session.query(ComplianceKPI).delete()
    session.query(ControlAssessmentResult).delete()
    session.query(ComplianceAssessment).delete()
    session.commit()
    
    # --- 1. Create a Mock Assessment ---
    assessment_id = str(uuid.uuid4())
    assessment = ComplianceAssessment(
        id=assessment_id,
        assessment_date=datetime.utcnow() - timedelta(days=2),
        baseline_id="mock-azure-baseline-001",
        catalog_id="gdpr-dora-nis2-catalog-v1",
        cloud_provider="azure",
        subscription_id="mock-sub-12345",
        total_regulatory_controls=15,
        total_technical_controls=45,
        compliant_count=9,
        partial_count=3,
        non_compliant_count=2,
        unknown_count=1,
        overall_compliance_score=68.5,
        average_confidence_score=0.74
    )
    session.add(assessment)
    
    # --- 2. Create Mock Control Results (Including Friction Points) ---
    controls_data = [
        {
            "id": "gdpr-art32", "title": "Security of processing", "reg": "GDPR",
            "status": "partial", "gap": "partial", "conf": 0.65, "level": "medium",
            "friction": '["Legal ambiguity: \'appropriate technical measures\' lacks binary definition", "Engineering team lacks bandwidth to implement metadata tagging for all databases"]',
            "recs": '["Conduct manual risk assessment for untagged databases", "Allocate sprint capacity for data classification"]'
        },
        {
            "id": "dora-art-6", "title": "ICT risk management framework", "reg": "DORA",
            "status": "compliant", "gap": "compliant", "conf": 0.92, "level": "high",
            "friction": '[]',
            "recs": '["Maintain current monitoring cadence"]'
        },
        {
            "id": "dora-art-11", "title": "ICT business continuity policy", "reg": "DORA",
            "status": "non-compliant", "gap": "missing", "conf": 0.85, "level": "high",
            "friction": '["Backup retention policy exists in OSCAL, but actual Azure Recovery Vault is not configured for geo-redundancy"]',
            "recs": '["Enable Geo-Redundant Storage (GRS) for critical backups immediately"]'
        },
        {
            "id": "nis2-art-21", "title": "Security of network and information systems", "reg": "NIS2",
            "status": "compliant", "gap": "compliant", "conf": 0.88, "level": "high",
            "friction": '[]',
            "recs": '["Continue regular NSG rule audits"]'
        },
        {
            "id": "gdpr-art33", "title": "Notification of a personal data breach", "reg": "GDPR",
            "status": "partial", "gap": "partial", "conf": 0.55, "level": "medium",
            "friction": '["Automated alerting is in place, but the 72-hour notification workflow relies on manual email chains"]',
            "recs": '["Automate DPO notification workflow via ServiceNow integration"]'
        }
    ]
    
    for c in controls_data:
        control = ControlAssessmentResult(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            regulatory_control_id=c["id"],
            regulation=c["reg"],
            control_title=c["title"],
            gap_type=c["gap"],
            compliance_status=c["status"],
            confidence_score=c["conf"],
            confidence_level=c["level"],
            evidence='[{"source": "Azure API", "timestamp": "2026-08-10T10:00:00"}]',
            friction_points=c["friction"],
            recommendations=c["recs"]
        )
        session.add(control)
        
    # --- 3. Create Mock KPIs ---
    kpis = {
        "overall_compliance_rate": 68.5,
        "gdpr_compliance_rate": 72.0,
        "dora_compliance_rate": 65.0,
        "nis2_compliance_rate": 88.0,
        "average_confidence_score": 74.0,
        "high_friction_controls_count": 3,
        "friction_rate": 20.0
    }
    
    for kpi_name, kpi_value in kpis.items():
        kpi = ComplianceKPI(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            kpi_name=kpi_name,
            kpi_value=kpi_value,
            kpi_unit="percentage" if "rate" in kpi_name else "count",
            kpi_category="overall"
        )
        session.add(kpi)
        
    # Save to database
    session.commit()
    session.close()
    
    print("✅ Demo data populated successfully!")
    print(f"📂 Database created/updated at: {project_root / 'compliance.db'}")
    print("🔄 Refresh your Streamlit dashboard to see the data!")

if __name__ == "__main__":
    populate_data()
