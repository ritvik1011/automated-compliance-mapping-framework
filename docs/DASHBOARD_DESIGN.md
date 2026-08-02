# Step 5: Dashboard Architecture & Visualization Design

> **Module**: Interactive Decision-Support Dashboard & Socio-Technical Reporting  
> **Author**: Ritvik Bahirwar (*Master's in Computer Engineering for IoT Systems*)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Sprint Window**: August 1–15, 2026  
> **Lifecycle Phase**: Step 5 — Decision Support, Stakeholder Visualization & Audit Reporting  

---

## 1. System Objective & Research Rationale

The primary barrier preventing automated governance and Policy-as-Code from achieving real-world adoption in enterprise organizations is the **epistemic gap between technical evidence and executive decision-making**:
- **Raw Telemetry vs. Executive Actionability**: Steps 1–4 produce rich data—OSCAL profiles, cloud baselines, multi-factor confidence scores, and raw JSON gap analysis results. However, non-technical leadership (CISOs, DPOs, board members) cannot consume raw JSON or query relational database tables directly.
- **The Binary Fallacy of Traditional GRC**: Legacy compliance tools present boolean green/red checkboxes that conceal the socio-technical reality of compliance. Compliance challenges frequently stem not from missing technical configurations, but from **open-textured statutory language** ("appropriate safeguards", "state of the art"), **process bottlenecks**, and **organizational friction**.

Step 5 provides the interactive **decision-support layer** that bridges this divide.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STEP 5 DECISION-SUPPORT ARCHITECTURE                  │
│                                                                             │
│  [Step 1: Policy] ──► [Step 2: Baseline] ──► [Step 3: Gap Engine]          │
│                                                     │                       │
│                                                     ▼                       │
│                                          [Step 4: Airflow & DB]             │
│                                                     │                       │
│                                                     ▼                       │
│                        ┌──────────────────────────────────────────┐         │
│                        │       STEP 5: STREAMLIT DASHBOARD        │         │
│                        │       (Model-View-Controller MVC)        │         │
│                        └────────────────────┬─────────────────────┘         │
│                                             │                               │
│           ┌──────────────────┬──────────────┼──────────────┬─────────────┐  │
│           ▼                  ▼              ▼              ▼             ▼  │
│    📊 Exec Summary    🔍 Tech View   🧠 Friction View  📈 Trends   📋 Controls
│    (Gauges & KPIs)   (Heatmaps/Risk) (Human Factors)   (DORA/NIS2) (Drill-Down)
│           │                  │              │              │             │  │
│           └──────────────────┴──────────────┴──────────────┴─────────────┘  │
│                                             │                               │
│                                             ▼                               │
│                        ┌──────────────────────────────────────────┐         │
│                        │           EXECUTIVE EXPORT LAYER         │         │
│                        │  • Multi-Sheet Excel Board Pack (.xlsx)  │         │
│                        │  • Styled Print-Ready Executive (.html)  │         │
│                        │  • Regulatory Audit PDF (.pdf)           │         │
│                        └──────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Page Architecture (Model-View-Controller)

To ensure code maintainability, query performance, and clean separation of concerns, Step 5 is implemented using the **Model-View-Controller (MVC)** architectural pattern:

### 2.1 Model: Database Connection Layer (`src/dashboard/database.py`)
- Provides an optimized data access layer over SQLAlchemy historical tables (`compliance_assessments`, `control_assessment_results`, `compliance_kpis`).
- Implements Streamlit resource and query caching:
  - `@st.cache_resource` for SQLAlchemy connection engines and session factories, ensuring single-instance connection reuse.
  - `@st.cache_data(ttl=300)` with a 5-minute time-to-live to ensure near-instantaneous page transitions while reflecting recent pipeline runs.
- Extracts specialized slices:
  - `get_latest_assessment_data()`: Full snapshot of the most recent evaluation.
  - `get_friction_points()`: Key research query filtering controls with socio-technical challenges.
  - `get_compliance_by_regulation()`: Cross-regulatory breakdown (GDPR, DORA, NIS2).
  - `get_compliance_by_category()`: Categorization by infrastructure domain (Encryption, Network Security, IAM, Backup & Recovery).
  - `get_kpi_trend()`: Longitudinal time-series for continuous monitoring.

### 2.2 View: Visualization Engine (`src/dashboard/visualizations.py`)
- Standardizes on interactive **Plotly** (`plotly>=5.18.0`) components with custom color palettes aligned to compliance thresholds:
  - Green (`#00cc44`) for $\ge 85\%$ compliance.
  - Yellow-Green (`#88cc00`) for $70-85\%$ compliance.
  - Amber (`#ffaa00`) for $50-70\%$ compliance.
  - Red (`#ff4444`) for $< 50\%$ compliance.
- Visual components include:
  - `create_compliance_gauge()`: Dial indicator with delta reference against an $80\%$ target.
  - `create_compliance_heatmap()`: Cross-tabulation of regulation vs. technical control category.
  - `create_confidence_scatter()`: Scatter visualization highlighting high-risk, low-confidence controls requiring human review.
  - `create_friction_impact_chart()`: Quantifying friction points per regulatory control.
  - `create_trend_line_chart()`: Time-series tracking overall and regulation-specific scores.
  - `display_friction_point_card()`: Expandable UI component detailing human bottlenecks and actionable remediation.

### 2.3 Controller: Multi-Page Navigation Structure (`src/dashboard/pages/`)
Organized using Streamlit's native multi-page hierarchy:
1. `1_📊_Executive_Summary.py`: CISO/Board-level high-level posture overview, overall compliance gauge, and automated status narrative.
2. `2_🔍_Technical_View.py`: Security engineer view with interactive multi-select filters, domain heatmaps, and confidence scatter analysis.
3. `3_🧠_Socio-Technical_View.py`: **The Primary Research Showcase** — categorizes friction into *Legal Ambiguity*, *Human/Process Bottlenecks*, *Mapping Complexity*, and *Technical Challenges*.
4. `4_📈_Trend_Analysis.py`: Continuous monitoring evidence tracking over time to satisfy **DORA Article 11** and **NIS2 Article 21**.
5. `5_📋_Detailed_Controls.py`: Deep-dive inspector with keyword search, raw evidence JSON inspect, and status filters.

---

## 3. Visualization Strategy & Chart Selection Rationale

| Visualization | Target Audience | Research & Operational Objective |
|---|---|---|
| **Compliance Dial Gauge** | CISO, DPO, Board | At-a-glance executive posture metric with delta comparison against an 80% organizational compliance target. |
| **Domain Heatmap** | Cloud Architects, SecOps | Identifies systematic gaps across regulatory regimes (GDPR, DORA, NIS2) and infrastructure domains (Encryption, IAM, Network, Backup). |
| **Confidence Scatter Plot** | Compliance Officers, Auditors | Correlates epistemic confidence against compliance status to immediately isolate false-assurance candidates (low confidence, non-compliant). |
| **Friction Impact Bar Chart** | Researchers, Process Engineers | Quantifies the volume of socio-technical friction points per control, demonstrating that legal ambiguity directly drives compliance delays. |
| **Longitudinal Trend Chart** | Risk Committees, Regulators | Tracks compliance scores and confidence trajectories over time to satisfy DORA Article 11 continuous monitoring mandates. |

---

## 4. Export Architecture (`src/dashboard/export.py`)

Step 5 incorporates dual-mode export capabilities designed for formal enterprise governance workflows:
1. **Multi-Sheet Excel Audit Pack (`.xlsx`)**:
   - Sheet 1: *Executive Summary* with metadata and high-level KPIs.
   - Sheet 2: *Control Assessment* with granular evidence strings, status, and gap classifications.
   - Sheet 3: *KPIs* with calculated mathematical metrics.
   - Sheet 4: *Socio-Technical Friction* documenting friction points and mitigation recommendations.
2. **Executive HTML / PDF Board Reports (`.html` / `.pdf`)**:
   - Self-contained, responsive HTML styled with modern typography, KPI metric cards, status badges, and finding tables.
   - Headless PDF generation via `weasyprint` with graceful fallback to self-contained HTML when native OS GTK/Cairo libraries are absent.
