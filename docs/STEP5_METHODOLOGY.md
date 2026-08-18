# Step 5: KPI Visualization & Socio-Technical Reporting — Methodology

> **Academic Research Context**: Policy-as-Code & Automated Compliance Mapping Framework  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Lifecycle Phase**: Step 5 — Decision-Support Dashboards, Socio-Technical Visualization & Board Reporting  

---

## Research Context

This module addresses the final challenge in compliance automation: **How do we make complex compliance data accessible and actionable for non-technical stakeholders?**

The dashboard represents the culmination of the research framework, translating Policy-as-Code outputs into executive-level insights.

In enterprise environments, Steps 1–4 produce rich operational telemetry—OSCAL component definitions, technical cloud configurations, gap matrices, epistemic confidence metrics, and friction points. However, non-technical leadership (CISOs, DPOs, board members) cannot consume raw JSON files or database records. They need visual, intuitive, and actionable insights to guide organizational risk allocation and satisfy legal audit mandates.

```
┌─────────────────────────────────────────────────────────────┐
│                  COMPLETE FRAMEWORK                         │
│                                                             │
│  [Step 1] ──► [Step 2] ──► [Step 3] ──► [Step 4]          │
│  Policy        Baseline     Gap Analysis  Automation        │
│  Parsing       Collection   Engine        Pipeline          │
│                                              │              │
│                                              ▼              │
│                                    ┌──────────────────┐     │
│                                    │   STEP 5         │     │
│                                    │   Dashboard      │     │
│                                    │   (Decision Hub) │     │
│                                    └────────┬─────────┘     │
│                                             │               │
│                                             ▼               │
│                              ┌──────────────────────────┐   │
│                              │  Non-Technical Leaders   │   │
│                              │  • CISO / DPO / Board    │   │
│                              │  • Regulators            │   │
│                              │  • Engineering Teams     │   │
│                              └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

### 1. Streamlit for Dashboard Framework
**Decision**: Use Streamlit as the core dashboard framework (`streamlit>=1.30.0`).

**Rationale**:
- **Pure Python**: Integrates natively with the framework's existing Python data models (Pydantic, SQLAlchemy, Pandas) without requiring JavaScript/TypeScript compilation toolchains.
- **Rapid Development**: Accelerates feature velocity and layout experimentation.
- **Interactive by Default**: Built-in reactive widgets, session state management, and real-time filtering.
- **Streamlit Caching**: Efficient caching via `@st.cache_resource` (SQLAlchemy engines) and `@st.cache_data(ttl=300)` ensures instantaneous page transitions while tracking continuous monitoring runs.
- **Academic-Friendly**: Widely used in computer science research and reproducible scientific demonstrations.

### 2. Multi-Page Architecture
**Decision**: Separate the dashboard into 5 focused pages under the Model-View-Controller (MVC) pattern.

**Rationale**:
- **📊 Executive Summary (`1_📊_Executive_Summary.py`)**: For leadership (high-level KPIs, overall compliance score dial, regulation-specific gauges, and automated executive narrative).
- **🔍 Technical View (`2_🔍_Technical_View.py`)**: For security engineers and compliance officers (cross-domain heatmaps, multi-factor confidence scatter plot, granular filtering).
- **🧠 Socio-Technical View (`3_🧠_Socio-Technical_View.py`)**: For researchers and compliance architects (quantification, impact analysis, and categorization of socio-technical friction).
- **📈 Trend Analysis (`4_📈_Trend_Analysis.py`)**: For compliance officers and risk committees (historical trajectories, continuous monitoring validation under DORA/NIS2).
- **📋 Detailed Controls (`5_📋_Detailed_Controls.py`)**: For internal and external auditors (drill-down into specific controls, raw evidence inspect, and actionable recommendations).

### 3. Plotly for Visualizations
**Decision**: Use Plotly (`plotly>=5.18.0`) as the primary visualization engine, supplemented by Altair.

**Rationale**:
- **Interactive**: Native hover inspection, dynamic zooming, click-to-filter, and trace toggling.
- **Publication-Quality**: Vector-crisp rendering suitable for both dashboard screens and academic research publications.
- **Wide Range of Chart Types**: Supports gauges, stacked regulation bars, multi-category heatmaps, and epistemic confidence scatters.
- **Good Documentation**: Consistent API with seamless integration into Streamlit containers.

---

## Socio-Technical View: The Research Highlight

The Socio-Technical View page is the **unique research contribution** of this framework. Traditional Governance, Risk, and Compliance (GRC) tools treat compliance as a purely technical problem reducible to simple Boolean rules. However, primary EU statutory legislation (GDPR, DORA, NIS2) relies heavily on **open-textured legal terms** ("appropriate technical and organizational measures", "state of the art", "proportionate").

Our analysis demonstrates that compliance is fundamentally a **socio-technical challenge**:

1. **Quantifies Friction**: Identifies, counts, and categorizes friction points into:
   - 📜 *Legal Ambiguity* (unclear statutory terminology)
   - 👥 *Human/Process Bottlenecks* (manual workflows, cognitive overload, staff bandwidth)
   - 🔗 *Mapping Complexity* (multi-cloud abstraction mismatches)
   - ⚙️ *Technical Challenges* (tooling limitations)
2. **Visualizes Impact**: Demonstrates empirical correlation between high friction points and lower compliance rates.
3. **Provides Context**: Explains why automated checks encounter limitations when statutory requirements cannot be cleanly reduced to binary infrastructure checks.
4. **Suggests Interventions**: Delivers actionable remediation steps to resolve process gaps, bridging human governance and cloud automation.

---

## DORA/NIS2 Alignment

The dashboard directly operationalizes regulatory transparency mandates:
- **DORA Article 11**: Mandates regular continuous reporting of ICT continuity, operational resilience, and recovery readiness to management bodies.
- **DORA Article 6**: Demands ongoing visibility and periodic review of the organization's ICT risk management framework.
- **NIS2 Article 21**: Requires essential and important entities to demonstrate continuous monitoring of cyber risk-management measures and supply chain security.

---

## Export Functionality

To support formal governance workflows, Step 5 incorporates a comprehensive export engine (`src/dashboard/export.py`):
- **Multi-Sheet Excel Audit Pack (`.xlsx`)**: Generates an audit-ready workbook containing *Executive Summary*, *Control Assessment*, *KPIs*, and *Socio-Technical Friction* sheets.
- **Print-Ready Executive Report (`.html` / `.pdf`)**: Generates self-contained, responsive board-level reports styled with modern typography, KPI cards, and finding tables.

---

## Deployment Options

### 1. Local Development & Desktop Launchers
For zero-friction local execution on Windows and cross-platform environments:
- **Windows Desktop Launcher**: Double-click `run_dashboard.bat` in the project root. It auto-detects the virtual environment (`venv`), sets UTF-8 console encoding, and launches the dashboard.
- **Python Launcher Script**: Run `python run_dashboard.py` from the project root.
- **Direct Streamlit CLI**:
  ```bash
  streamlit run src/dashboard/app.py
  ```
Access via browser at `http://localhost:8501`.

---

## Local Execution Architecture & Troubleshooting

### 1. The `sys.path` Module Resolution Challenge
When Streamlit executes an entry point file (e.g., `streamlit run src/dashboard/app.py`), Python assigns `sys.path[0]` to the directory of the target script (`src/dashboard/`), rather than the project root directory (`automated-compliance-mapping-framework/`). 

As a result, relative absolute imports adhering to standard package layouts (e.g., `from src.dashboard.database import ...`) fail with:
```text
ModuleNotFoundError: No module named 'src'
```

### 2. Architectural Solution: Defense-in-Depth Path Resolution
To ensure foolproof execution across all environments (local development, terminal CLI, batch launchers, and Streamlit Community Cloud), the framework implements a two-tier resolution strategy:

1. **Dynamic Path Injection in App & Multi-Page Scripts**:
   At the very top of `src/dashboard/app.py` and all files in `src/dashboard/pages/`, the project root is dynamically computed and injected into `sys.path` before any package imports:
   ```python
   # In src/dashboard/app.py (3 levels up: app.py -> dashboard -> src -> root)
   import sys
   from pathlib import Path
   PROJECT_ROOT = Path(__file__).resolve().parents[2]
   if str(PROJECT_ROOT) not in sys.path:
       sys.path.insert(0, str(PROJECT_ROOT))
   ```
   For multi-page files in `src/dashboard/pages/`, the calculation traverses 4 levels up (`.parents[3]`), guaranteeing that each page is self-contained and independently navigable.

2. **Dedicated Launcher Harness (`run_dashboard.py` & `run_dashboard.bat`)**:
   - `run_dashboard.py`: Resolves the project root, mutates `sys.path`, injects `PYTHONPATH` into child process environments, sets `PYTHONIOENCODING=utf-8`, and delegates execution to `sys.executable -m streamlit run src/dashboard/app.py`.
   - `run_dashboard.bat`: Automates virtual environment activation (`venv` or `.venv`), configures Windows terminal codepage to UTF-8 (`chcp 65001`), forwards CLI parameters, and keeps the terminal open on errors via `pause`.

### 3. Troubleshooting Matrix

| Issue / Symptom | Root Cause | Resolution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'src'` | Execution context lacks project root in `sys.path` | Use `run_dashboard.bat` / `python run_dashboard.py` or verify dynamic path injection at top of `app.py`. |
| `UnicodeEncodeError: 'charmap' codec can't encode...` | Windows terminal defaults to legacy code page (CP1252) | Set `PYTHONIOENCODING=utf-8` or use `run_dashboard.bat` which executes `chcp 65001`. |
| `Port 8501 is already in use` | Another Streamlit or local web instance occupies default port | Pass custom port flag: `python run_dashboard.py --server.port 8502`. |
| `sqlite3.OperationalError: no such table` | Database has not been seeded with assessment data | Run `python populate_demo_data.py` to generate the mock SQLite database (`compliance.db`). |
| Streamlit page reload loses package context | Sub-page executed in isolated thread without parent state | Reusable `.parents[3]` path injection at top of each page file in `src/dashboard/pages/`. |

---

## Deployment Options

### 1. Local Development
Run `run_dashboard.bat` or `python run_dashboard.py`.

### 2. Streamlit Cloud (Production)
1. Push code repository to GitHub.
2. Connect repository to [Streamlit Community Cloud](https://streamlit.io/cloud).
3. Set main file path: `src/dashboard/app.py`.
4. Deploy with one click. Detailed deployment guide available in [`docs/DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).

### 3. Docker (Enterprise Container)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Limitations & Future Work

1. **Real-time Updates**: The current dashboard reads historical snapshots from SQLite/PostgreSQL; future work will incorporate streaming WebSockets for real-time cloud drift notifications.
2. **Role-Based Access Control (RBAC)**: Currently runs in an open single-tenant mode; enterprise production deployments will integrate OAuth2/OIDC (Azure AD, Okta) to partition views between CISOs, technical engineers, and external auditors.
3. **Custom Report Templating**: Future iterations will offer a drag-and-drop report builder allowing compliance officers to select custom control subsets for targeted audit submissions.
4. **Mobile Optimization**: The dashboard is optimized for desktop and tablet screens; dedicated mobile-responsive views will enhance accessibility for leadership on mobile devices.
