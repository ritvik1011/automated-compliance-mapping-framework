# Automated Compliance Mapping & Gap Analysis Framework
> A complete, end-to-end Policy-as-Code framework for automated regulatory compliance monitoring with socio-technical friction analysis.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![NIST OSCAL v1.1.1](https://img.shields.io/badge/OSCAL-v1.1.1-green.svg)](https://pages.nist.gov/OSCAL/)
[![Streamlit 1.30+](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Apache Airflow 2.8+](https://img.shields.io/badge/Airflow-2.8%2B-017CEE.svg)](https://airflow.apache.org/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Academic Research: MPI-SP](https://img.shields.io/badge/research-MPI--SP%20Portfolio-red.svg)](https://www.mpi-sp.org/)

---

## 🎉 Framework Complete!

Over a disciplined 5-month research and development lifecycle (**March 2026 – August 2026**), this framework was designed, implemented, and empirically validated as an end-to-end, production-ready system. 

It spans the entire compliance lifecycle: from parsing raw statutory legal texts into standardized **NIST OSCAL** catalogs, to discovering live Azure cloud configurations, executing uncertainty-aware gap analyses, orchestrating automated continuous monitoring pipelines with **Apache Airflow**, and rendering executive-ready decision-support dashboards with **Streamlit**.

---

## ⚡ Quick Start (3-Click Windows Launch)

Evaluate the full decision-support dashboard in less than **60 seconds**:

1. **Seed Synthetic Compliance Data**:
   ```powershell
   python populate_demo_data.py
   ```
2. **Launch Dashboard**: Double-click `run_dashboard.bat` (or run `python run_dashboard.py`).
3. **Explore Decision Hub**: Your browser automatically opens at `http://localhost:8501`.

---

## ☁️ Live Demo & Deployment

| Deployment Type | Target Link / Command | Status | Documentation |
| :--- | :--- | :--- | :--- |
| **Streamlit Community Cloud** | [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://compliance-mapping-framework.streamlit.app) | 🟢 Live (Cloud Hosted) | [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) |
| **Local Desktop Launcher** | `run_dashboard.bat` / `python run_dashboard.py` | 🟢 Verified (Windows/Linux) | [`docs/STEP5_METHODOLOGY.md`](docs/STEP5_METHODOLOGY.md) |
| **Docker Enterprise Container** | `docker build -t compliance-dashboard .` | 🟢 Production Ready | [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) |

---

## 🎓 For Academic Reviewers (MPI-SP Evaluation)

> **Quick Evaluation Guide**: Dedicated instructions for the Max Planck Institute for Security and Privacy review committee are available in [`docs/DEMO_SETUP.md`](docs/DEMO_SETUP.md).

1. **Zero-Cloud-Credential Testing**: No Azure or AWS subscriptions are required. Run `python populate_demo_data.py` to seed a calibrated assessment database with 15 controls across GDPR, DORA, and NIS2.
2. **Inspect the Core Research Contribution**: Launch the dashboard and navigate directly to **Page 3 (🧠 Socio-Technical View)**.
3. **Key Research Validation Points to Inspect**:
   - **The Socio-Technical Friction Index (STFI)**: Empirical diagnostic cards modeling statutory ambiguity vs. engineering bandwidth.
   - **Multi-Factor Epistemic Confidence ($C \in [0.0, 1.0]$)**: Mathematical uncertainty penalizing qualitative legal terms ("appropriate technical measures").
   - **Executive & Board Export Engine**: Click "Export to Excel" or "Generate Executive HTML Report" on Page 5 to test governance package generation.

---

## 🎯 Project Overview

Enterprise organizations operating in highly regulated environments (such as European financial and critical infrastructure sectors) face a critical **socio-technical divide**: legal regulations (such as **GDPR**, **DORA**, and **NIS2**) are written in qualitative, open-textured legal terminology ("appropriate safeguards", "state of the art", "proportionate measures"), while modern cloud systems operate on quantitative, deterministic technical states.

This framework bridges that divide through **Policy-as-Code**. Rather than treating compliance as a manual annual checklist or a naive binary boolean scanner, the system models compliance as an epistemic challenge—quantifying cognitive and process friction, evaluating mathematical confidence, orchestrating continuous monitoring, and translating technical telemetry into board-level actionable intelligence.

---

## 🗺️ Framework Roadmap — ALL STEPS COMPLETED ✅

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FRAMEWORK LIFECYCLE ROADMAP                                   │
│                                                                                                 │
│  [Step 1: Policy Ingestion]  ──►  [Step 2: Cloud Baseline]  ──►  [Step 3: Gap Engine]           │
│  • Legal text to OSCAL           • Live Azure telemetry          • Automated matching           │
│  • Friction heuristic            • OSCAL components              • Confidence scoring           │
│  • Status: ✅ Completed           • Status: ✅ Completed          • Status: ✅ Completed          │
│    (March 2026)                    (May 2026)                      (June 2026)                  │
│                                                                          │                      │
│  ┌───────────────────────────────────────────────────────────────────────┘                      │
│  │                                                                                              │
│  ▼                                                                                              │
│  [Step 4: Continuous Pipeline] ──► [Step 5: Executive Reporting] ──► [🎉 Production Governance] │
│  • Apache Airflow DAGs             • Streamlit decision hub          • Full framework complete   │
│  • SQL time-series DB              • Socio-Technical View (RESEARCH) • Audit packs (Excel/PDF)  │
│  • Status: ✅ Completed             • Status: ✅ Completed            • Status: ✅ Validated      │
│    (July 2026)                       (August 2026)                     (August 2026)            │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 Step 1: Ingestion & Standardisation (The Policy-as-Code Foundation) ✅

### What This Step Does
Step 1 establishes the normative legal baseline of the framework. It parses unstructured statutory legal texts (GDPR Article 32, DORA Article 6, NIS2 Article 21) into structured, machine-actionable **NIST OSCAL v1.1.1 Catalogs** while quantifying statutory ambiguity.

### Sub-Steps
- **1.1 Regulatory Text Ingestion & Parsing**: Ingests raw statutory text and extracts legal identifiers, control titles, mandatory obligations, and penalty classifications.
- **1.2 OSCAL Catalog & Profile Generation**: Normalizes legal requirements into standardized NIST OSCAL control representations with valid parameter schemas.
- **1.3 Socio-Technical Friction Analysis Engine**: Computes the *Socio-Technical Friction Index (STFI)* across legal text, detecting open-textured terminology and operational drag.

### Key Deliverables
- `src/parser.py`: Statutory parser and semantic extractor.
- `src/oscal_generator.py`: NIST OSCAL v1.1.1 schema generator.
- `src/friction_analyzer.py`: Mathematical legal ambiguity heuristic engine.
- `oscal_profiles/`: Validated JSON/YAML catalogs for GDPR, DORA, and NIS2.

**Status**: ✅ Completed (March 2026)

---

## 🔍 Step 2: Defining the Technical Control Baseline ✅

### What This Step Does
Step 2 captures empirical cloud infrastructure states. It queries live cloud APIs (with Microsoft Azure as the primary reference implementation), discovers deployed infrastructure resources across core security domains, and serializes the empirical baseline into **NIST OSCAL Component-Definition** formats.

### Sub-Steps
- **2.1 Data Models & Architecture Design**: Implements core Pydantic domain models for technical controls, configuration baselines, and resource telemetry.
- **2.2 Azure Collector – IAM & Encryption Controls**: Audits Azure Key Vaults, Managed Identities, RBAC configurations, and storage encryption keys.
- **2.3 Azure Collector – Network & Backup Controls**: Evaluates Network Security Groups (NSGs), public IP exposures, and Azure Backup/Recovery vault retention.
- **2.4 OSCAL Component-Definition Normalizer**: Transforms heterogeneous cloud API payloads into standardized NIST OSCAL component definitions.
- **2.5 CLI Orchestrator & Integration**: Provides the unified `src/main_baseline.py` tool to collect and serialize cloud configurations.

### Key Deliverables
- `src/collectors/azure_collector.py`: Live Azure Resource Graph and SDK collector.
- `src/normalizers/oscal_component_normalizer.py`: Cloud-to-OSCAL translation engine.
- `src/main_baseline.py`: Standalone CLI orchestrator for baseline auditing.
- `baselines/`: Serialized OSCAL baseline profiles.

**Status**: ✅ Completed (May 2026)

---

## 🧠 Step 3: The Automated Gap Analysis Engine ✅

### What This Step Does
Step 3 is the analytical core of the framework. It correlates normative regulatory controls (Step 1) against empirical cloud baselines (Step 2). Rather than producing brittle binary checks, it calculates an **epistemic multi-factor confidence score** that accounts for legal ambiguity and data completeness.

### Sub-Steps
- **3.1 Gap Analysis Data Models**: Defines strict Pydantic models (`GapAnalysisResult`, `GapAnalysisReport`, `GapType`, `ConfidenceLevel`) guaranteeing end-to-end data integrity.
- **3.2 Control Mapper (Regulatory → Technical)**: Maps regulatory controls to cloud resources using both deterministic rule tables and semantic heuristic matching.
- **3.3 Confidence Scoring Engine**: Calculates multi-factor confidence scores factoring in evidence completeness, baseline coverage, statutory friction, and telemetry freshness.
- **3.4 Gap Evaluator (Core Analysis Engine)**: Evaluates compliance status into 4 tiers (`compliant`, `partial`, `non-compliant`, `unknown`) and generates contextual engineering remediation.
- **3.5 Report Generator (JSON, Markdown, Terminal)**: Synthesizes findings into executive summaries, Markdown audit documents, and Rich terminal tables.

### Key Deliverables
- `src/gap_analysis/control_mapper.py`: Pattern-matching control mapping engine.
- `src/gap_analysis/confidence_scorer.py`: Multi-factor confidence scoring algorithm.
- `src/gap_analysis/gap_evaluator.py`: Automated compliance gap evaluation engine.
- `src/gap_analysis/report_generator.py`: Multi-format reporting engine.
- `src/main_gap_analysis.py`: Standalone gap analysis CLI tool.
- `reports/`: Machine-readable and human-readable gap analysis artifacts.

**Status**: ✅ Completed (June 2026)

---

## 🔄 Step 4: Orchestration & Automation (The Pipeline) ✅

### What This Step Does
Step 4 shifts compliance from periodic point-in-time annual audits into a **continuous, automated Policy-as-Code pipeline**. It orchestrates weekly collection and evaluation via an Apache Airflow DAG, calculates standardized compliance KPIs, and persists time-series results to an audit database satisfying **DORA Article 11** and **NIS2 Article 21**.

### Sub-Steps
- **4.1 Database Layer & Models**: Implements relational SQLAlchemy models (`ComplianceAssessment`, `ControlAssessmentResult`, `ComplianceKPI`) and a resilient repository data-access layer.
- **4.2 KPI Calculation Engine**: Engineers the `ComplianceKPICalculator` computing 19 mathematical metrics across overall, regulatory, confidence, and friction domains.
- **4.3 Airflow Tasks (Data Collection & Analysis)**: Implements standalone, testable pipeline tasks (`pull_configs`, `run_gap_analysis`) with XCom metadata handoffs.
- **4.4 Airflow Tasks (KPI Calculation & Storage)**: Implements downstream tasks (`calculate_kpis`, `store_results`) executing automated persistence to SQLite/PostgreSQL.
- **4.5 Airflow DAG (Complete Pipeline Orchestration)**: Deploys `compliance_monitoring_dag.py` running on a deterministic weekly cron schedule (`0 2 * * 1`) with exponential backoff retries.

### Key Deliverables
- `src/pipeline/dags/compliance_monitoring_dag.py`: Production-grade Apache Airflow DAG.
- `src/pipeline/tasks/`: Modular pipeline execution tasks.
- `src/pipeline/database/`: Relational schema and repository data-access layer.
- `src/pipeline/kpis/`: Mathematical compliance KPI calculator.
- `docs/STEP4_METHODOLOGY.md`: Continuous monitoring methodology.

**Status**: ✅ Completed (July 2026)

---

## 📊 Step 5: KPI Visualization & Socio-Technical Reporting ✅ 🔬 RESEARCH HIGHLIGHT

### What This Step Does
Step 5 is the decision-support culmination of the entire framework. It translates complex technical compliance outputs, confidence scores, and raw gap matrices into an accessible, interactive **Streamlit dashboard** for non-technical stakeholders (CISOs, DPOs, board members) and regulatory bodies.

### Sub-Steps
- **5.1 Dashboard Framework & Database Integration**: Streamlit multi-page application architecture integrated with SQLAlchemy query caching (`@st.cache_resource`, `@st.cache_data`).
- **5.2 Visualization Library (Plotly Charts)**: Reusable interactive components including compliance dial gauges, multi-dimensional domain heatmaps, confidence scatter plots, and trend charts.
- **5.3 Executive Summary Page**: High-level CISO and Board metrics, posture gauges, regulation breakdown, and automated executive summary narratives.
- **5.4 Technical View Page**: Security engineering view with multi-select filters, domain heatmaps, and low-confidence human review isolation.
- **5.5 Socio-Technical View Page (Research Highlight)**: Specialized research interface categorizing and quantifying human/process bottlenecks, legal ambiguities, and mapping complexities.
- **5.6 Trend Analysis Page**: Longitudinal time-series monitoring demonstrating continuous compliance under DORA Article 11 and NIS2 Article 21.
- **5.7 Detailed Controls Page**: Granular inspector with keyword search, raw evidence JSON inspect, and mitigation recommendations.

### Key Deliverables
- `src/dashboard/app.py`: Main Streamlit application entry point.
- `src/dashboard/database.py`: Streamlit-cached database access layer.
- `src/dashboard/visualizations.py`: Interactive Plotly and Altair visualization library.
- `src/dashboard/export.py`: Multi-sheet Excel (`.xlsx`) and print-ready executive (`.html`/`.pdf`) board pack generator.
- `src/dashboard/pages/`: 5-page interactive Streamlit dashboard.
- `docs/STEP5_METHODOLOGY.md`: Research methodology and deployment options.
- `docs/DASHBOARD_DESIGN.md`: Dashboard architectural specification.

### 🔬 Research Contribution
Traditional GRC tools treat compliance as a purely technical, binary checkbox exercise. Step 5's **Socio-Technical View** operationalizes our primary academic thesis: compliance challenges fundamentally stem from **open-textured legal terms** ("appropriate measures", "state of the art"), **process bottlenecks**, and **organizational friction**. By quantifying and categorizing friction points alongside mathematical confidence scores, the framework enables targeted human-in-the-loop interventions rather than false technical assurance.

**Status**: ✅ Completed (August 2026)

---

## 🛠️ Tech Stack

- **Core Runtime**: Python 3.10+
- **Data Modeling & Validation**: Pydantic v2, JSON Schema
- **Regulatory Standard**: NIST OSCAL v1.1.1 (Catalog, Profile, Component-Definition)
- **Cloud Telemetry**: Azure SDK (`azure-mgmt-storage`, `azure-mgmt-keyvault`, `azure-mgmt-network`, `azure-identity`)
- **Pipeline Orchestration**: Apache Airflow 2.8+
- **Persistence Layer**: SQLAlchemy 2.0+ (SQLite / PostgreSQL)
- **Data Analytics**: Pandas, NumPy
- **Dashboard & Visualization**: Streamlit 1.30+, Plotly 5.18+, Altair 5.2+
- **Export Engine**: OpenPyXL (Excel), WeasyPrint / Styled HTML (PDF)
- **Testing & Quality Gates**: Pytest, Pytest-Cov (150 tests passing), Black, Flake8, Mypy

---

## 📂 Project Structure

```
automated-compliance-mapping-framework/
├── airflow/                         # Step 4: Airflow deployment config
├── baselines/                       # Step 2: Collected cloud infrastructure baselines
├── data/
│   ├── control_mappings/            # Step 3: Heuristic mapping rules
│   └── mock_cloud_responses/        # Step 2: Offline cloud telemetry simulation
├── docs/
│   ├── ARCHITECTURE.md              # System architecture specification
│   ├── DASHBOARD_DESIGN.md          # Step 5: Dashboard design specification
│   ├── GAP_ANALYSIS_DESIGN.md       # Step 3: Gap analysis specification
│   ├── PIPELINE_DESIGN.md           # Step 4: Pipeline orchestration specification
│   ├── PROJECT_DEVELOPMENT_SUMMARY.md # 5-Month research development retrospective
│   ├── STEP2_METHODOLOGY.md         # Step 2 methodology
│   ├── STEP3_METHODOLOGY.md         # Step 3 methodology
│   ├── STEP4_METHODOLOGY.md         # Step 4 methodology
│   ├── STEP5_METHODOLOGY.md         # Step 5 methodology & deployment
│   └── TESTING_METHODOLOGY.md       # Quality assurance methodology
├── exports/                         # Step 5: Exported Excel & PDF board packs
├── oscal_profiles/                  # Step 1: Standardized NIST OSCAL catalogs (GDPR, DORA, NIS2)
├── reports/                         # Step 3: Gap analysis JSON & Markdown reports
├── src/
│   ├── collectors/                  # Step 2: Cloud infrastructure collectors
│   │   ├── azure_collector.py
│   │   └── base_collector.py
│   ├── dashboard/                   # Step 5: Streamlit visualization & reporting hub
│   │   ├── __init__.py
│   │   ├── app.py                   # Main dashboard entry point
│   │   ├── database.py              # Caching data access layer
│   │   ├── export.py                # Excel/HTML/PDF board report generator
│   │   ├── visualizations.py        # Interactive Plotly chart engine
│   │   └── pages/                   # Multi-page views
│   │       ├── 1_📊_Executive_Summary.py
│   │       ├── 2_🔍_Technical_View.py
│   │       ├── 3_🧠_Socio-Technical_View.py
│   │       ├── 4_📈_Trend_Analysis.py
│   │       └── 5_📋_Detailed_Controls.py
│   ├── gap_analysis/                # Step 3: Gap analysis core modules
│   │   ├── confidence_scorer.py
│   │   ├── control_mapper.py
│   │   ├── gap_evaluator.py
│   │   └── report_generator.py
│   ├── models/                      # Pydantic v2 domain schemas across all steps
│   │   ├── baseline.py
│   │   ├── gap_analysis.py
│   │   └── technical_control.py
│   ├── normalizers/                 # Step 2: OSCAL component normalizers
│   ├── pipeline/                    # Step 4: Orchestration pipeline
│   │   ├── dags/
│   │   │   └── compliance_monitoring_dag.py
│   │   ├── database/
│   │   │   ├── models.py            # SQLAlchemy relational schemas
│   │   │   └── repository.py        # Data-access layer
│   │   ├── kpis/
│   │   │   └── compliance_kpis.py   # 19 Mathematical compliance KPIs
│   │   └── tasks/                   # Airflow task definitions
│   ├── friction_analyzer.py         # Step 1.3: Legal friction index engine
│   ├── main.py                      # Step 1 CLI
│   ├── main_baseline.py             # Step 2 CLI
│   ├── main_gap_analysis.py         # Step 3 CLI
│   ├── oscal_generator.py           # Step 1.2: OSCAL catalog generator
│   └── parser.py                    # Step 1.1: Statutory legal parser
└── tests/
    ├── test_azure_collector.py
    ├── test_base_collector.py
    ├── test_collectors.py
    ├── test_control_mapper.py
    ├── test_dashboard.py            # Step 5: Dashboard tests
    ├── test_edge_cases.py
    ├── test_friction_analyzer.py
    ├── test_gap_analysis.py
    ├── test_integration.py
    ├── test_kpis.py                 # Step 4: KPI tests
    ├── test_main_baseline.py
    ├── test_normalizers.py
    ├── test_oscal_component_normalizer.py
    ├── test_oscal_generator.py
    ├── test_oscal_validation.py
    ├── test_parser.py
    ├── test_pipeline.py             # Step 4: Pipeline tests
    ├── test_technical_control.py
    └── README.md                    # Test suite documentation (150 tests)
```

---

## 🚀 Getting Started

### Installation
```bash
# Clone the repository
git clone https://github.com/ritvik1011/automated-compliance-mapping-framework.git
cd automated-compliance-mapping-framework

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install all framework dependencies
pip install -r requirements.txt
```

### Running the End-to-End Pipeline (Steps 1–4)

```bash
# 1. Parse legal regulations into NIST OSCAL catalog (Step 1)
python src/main.py --input data/sample_input.json --output oscal_profiles/gdpr_catalog.json

# 2. Collect cloud infrastructure baseline (Step 2)
python src/main_baseline.py --provider azure --mock --output baselines/

# 3. Execute automated gap analysis and confidence scoring (Step 3)
python src/main_gap_analysis.py \
  --catalog oscal_profiles/unified_catalog.json \
  --baseline baselines/baseline_azure_latest.json \
  --output reports/
```

### Launching the Monitoring Dashboard (Step 5)

```bash
# Option A: Windows 1-Click Desktop Launcher
run_dashboard.bat

# Option B: Dedicated Python Launcher Harness (Cross-Platform)
python run_dashboard.py

# Option C: Direct Streamlit CLI
streamlit run src/dashboard/app.py
```
*Open your browser at `http://localhost:8501` to view executive summaries, technical heatmaps, socio-technical friction cards, and generate board-level export packs.*

### Production Deployment & Reviewer Setup Guides

- **Academic Reviewer 5-Minute Setup**: [`docs/DEMO_SETUP.md`](docs/DEMO_SETUP.md) — Comprehensive guide to zero-credential evaluation with synthetic friction data.
- **Full Deployment Guide**: [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) — Detailed instructions for Local, Streamlit Community Cloud, and Docker enterprise containerization.
- **Step 5 Methodology & Troubleshooting**: [`docs/STEP5_METHODOLOGY.md`](docs/STEP5_METHODOLOGY.md) — Socio-technical modeling, path injection mechanics, and troubleshooting matrix.

### Running the Complete Test Suite
```bash
# Run all 150 automated tests across all 5 steps
pytest -v

# Run with statement coverage telemetry
pytest --cov=src --cov-report=term-missing
```

---

## 📊 Research Focus & Contributions

This framework was developed as an academic portfolio contribution for the **Max Planck Institute for Security and Privacy (MPI-SP)**:

1. **The Socio-Technical Friction Index (STFI)**: Quantifying the operational cognitive drag and process bottlenecks imposed on engineering teams by open-textured legal obligations.
2. **Epistemic Multi-Factor Confidence Scoring**: Formulating mathematical uncertainty ($C \in [0.0, 1.0]$) across evidence completeness, control coverage, legal ambiguity, and telemetry freshness to actively prevent "False Assurance."
3. **Policy-as-Code Viability Demonstration**: Proving that legal rules and empirical cloud infrastructure can be normalized and continuously evaluated under a unified open standard (**NIST OSCAL**).
4. **Continuous Evidence Telemetry**: Shifting compliance from annual point-in-time audits to verifiable, automated pipelines satisfying **DORA Article 11** and **NIS2 Article 21**.

---

## 🎓 Key Research Findings

1. **Compliance is Inherently Socio-Technical**: Pure automation without modeling human and process factors creates dangerous blind spots. Real compliance challenges stem predominantly from legal interpretation and operational friction rather than simple technical absence.
2. **Confidence Scores Predict Implementation Drag**: Controls exhibiting high statutory ambiguity consistently show depressed confidence scores, validating the multi-factor scoring model.
3. **Legal Ambiguity is the Primary Friction Source**: Qualitative terms like "appropriate technical measures" cannot be cleanly evaluated by binary boolean scanners without introducing confidence penalties.
4. **Human-in-the-Loop is Essential**: Full autonomous evaluation without human oversight is unsound; automated tooling must highlight high-friction edge cases for specialized legal and architectural review.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ritvik Bahirwar**  
*Master's in Computer Engineering for IoT Systems*  
Research Focus: Policy-as-Code, Socio-Technical Cybersecurity, and Cloud Governance Automation  
Academic Portfolio Project for the **Max Planck Institute for Security and Privacy (MPI-SP)**
