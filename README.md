# Automated Compliance Mapping & Gap Analysis Framework

> **A Policy-as-Code Research Initiative translating multi-jurisdictional regulatory frameworks (GDPR, DORA, NIS2) into standardized NIST OSCAL models, establishing automated enterprise infrastructure baselines, orchestrating continuous compliance monitoring via Apache Airflow, and quantifying socio-technical friction.**

[![Continuous Integration](https://github.com/ritvik1011/automated-compliance-mapping-framework/actions/workflows/tests.yml/badge.svg)](https://github.com/ritvik1011/automated-compliance-mapping-framework/actions/workflows/tests.yml)
[![Tests Passing](https://img.shields.io/badge/tests-145%20passed-brightgreen.svg)](tests/README.md)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)](tests/README.md)
[![NIST OSCAL](https://img.shields.io/badge/NIST%20OSCAL-v1.1.2%20Compliant-blue.svg)](https://pages.nist.gov/OSCAL/)
[![Orchestration: Apache Airflow](https://img.shields.io/badge/Airflow-2.8%2B-017CEE.svg)](https://airflow.apache.org/)
[![Database: SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00.svg)](https://www.sqlalchemy.org/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked: Mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](http://mypy-lang.org/)

---

## 🎯 Project Overview

Regulatory compliance in enterprise cloud computing is frequently treated as a superficial, post-hoc checkbox activity, leading to acute developer fatigue and brittle governance. This academic research project bridges the structural divide between legal jurisprudence and cloud infrastructure engineering. By operationalizing **Policy-as-Code**, this framework ingests European regulatory statutes (GDPR Art. 32, DORA Articles 6 & 11, NIS2 Art. 21), maps them into machine-readable **NIST OSCAL** structures, captures live and mock enterprise cloud baselines, and quantifies **socio-technical friction points** where legal ambiguity prevents binary automation. In Step 4, the framework transitions from a point-in-time analyzer into a production-ready, continuous compliance monitoring pipeline orchestrated by **Apache Airflow**.

---

## 🗺️ Framework Roadmap

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                FRAMEWORK RESEARCH LIFECYCLE                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
  Phase 1: Legal Ingestion & Socio-Technical Friction (March 2026)
  ┌──────────────────────────────────────────────────────────────────┐
  │ [x] Step 1: Ingestion & Standardisation (Policy-as-Code)         │ ──▶ Completed (March 2026)
  └──────────────────────────────────────────────────────────────────┘
  Phase 2: Quality Engineering & Infrastructure Baselines (April - May 2026)
  ┌──────────────────────────────────────────────────────────────────┐
  │ [x] QA Hardening: Testing Harness, NIST Schema, CI/CD Gates      │ ──▶ Completed (April 2026)
  │ [x] Step 2: Defining the Technical Control Baseline              │ ──▶ Completed (May 2026)
  └──────────────────────────────────────────────────────────────────┘
  Phase 3: Semantic Gap Reasoning & Confidence Scoring (June 2026)
  ┌──────────────────────────────────────────────────────────────────┐
  │ [x] Step 3: The Automated Gap Analysis Engine                    │ ──▶ Completed (June 2026)
  └──────────────────────────────────────────────────────────────────┘
  Phase 4: Continuous Pipeline Orchestration & Monitoring (July 2026)
  ┌──────────────────────────────────────────────────────────────────┐
  │ [x] Step 4: Orchestration & Automation (The Pipeline)            │ ──▶ Completed (July 2026)
  └──────────────────────────────────────────────────────────────────┘
  Phase 5: Executive Reporting & Visual Analytics (August 2026)
  ┌──────────────────────────────────────────────────────────────────┐
  │ [ ] Step 5: KPI Visualization & Socio-Technical Reporting        │ ──▶ In Progress (Target: August 2026)
  └──────────────────────────────────────────────────────────────────┘
```

---

## 📚 Step 1: Ingestion & Standardisation (The Policy-as-Code Foundation)

### What This Step Does
Step 1 establishes the legal ingestion foundation of the framework. It parses unstructured statutory articles from major cybersecurity and data privacy regulations into strongly typed models, generates standardized **NIST OSCAL Catalogs**, and evaluates text for open-textured legal terms to identify socio-technical friction points requiring human oversight.

### Sub-Steps
- **1.1 Regulatory Text Ingestion & Parsing**: Ingests multi-regulation JSON corpora (GDPR, DORA, NIS2) and validates clauses via Pydantic v2 schemas (`src/parser.py`).
- **1.2 OSCAL Catalog & Profile Generation**: Maps parsed regulatory mandates to standardized NIST OSCAL Control Catalogs v1.1.1 (`src/oscal_generator.py`).
- **1.3 Socio-Technical Friction Analysis Engine**: Scans legal provisions for ambiguous terms ("state of the art", "appropriate measures") and computes an Automation Feasibility Score (`src/friction_analyzer.py`).

### Key Deliverables
- Normalized legal schemas across GDPR, DORA, and NIS2 (`data/sample_input.json`).
- Standardized OSCAL Catalogs (`oscal_profiles/gdpr_catalog.json`, `dora_catalog.json`, `nis2_catalog.json`, `unified_catalog.json`).
- Empirical socio-technical friction report (`oscal_profiles/friction_report.json`).
- CLI orchestration pipeline with rich terminal visualization (`src/main.py`).

**Status**: ✅ **Completed (March 2026)**

---

## 🔍 Step 2: Defining the Technical Control Baseline

### What This Step Does
Step 2 extracts the empirical "As-Is" operational state of enterprise cloud infrastructure and translates it into standardized, machine-readable controls. Using the Gang of Four (GoF) Strategy Pattern, it abstracts multi-cloud SDK operations, inspects configurations across four core security categories, and serializes the baseline into official **NIST OSCAL Component-Definition** format for automated downstream gap analysis.

### Sub-Steps
- **2.1 Data Models & Architecture Design**: Engineered robust Pydantic v2 models (`TechnicalControl`, `InfrastructureBaseline`) and abstract base interfaces (`src/models/technical_control.py`, `src/collectors/base_collector.py`).
- **2.2 Azure Collector — IAM & Encryption Controls**: Implemented cloud collectors extracting Virtual Machine managed identities, Storage Account encryption at rest, HTTPS enforcement, and Key Vault protection (`src/collectors/azure_collector.py`).
- **2.3 Azure Collector — Network & Backup Controls**: Extended extraction to evaluate Network Security Group ingress rules (detecting overly permissive `*` wildcards) and Storage geo-redundancy (GRS/GZRS vs LRS) mapped directly to DORA Articles 6 and 11.
- **2.4 OSCAL Component-Definition Normalizer**: Engineered the normalizer transforming infrastructure snapshots into NIST OSCAL Component-Definitions with resource deduplication and weakest-link compliance rollup (`src/normalizers/oscal_component_normalizer.py`).
- **2.5 CLI Orchestrator & Integration**: Built the multi-cloud CLI baseline collector featuring Rich-powered reporting dashboards, dual JSON/OSCAL export, and air-gapped zero-credential mock support (`src/main_baseline.py`).

### Key Deliverables
- Multi-cloud collector architecture with fault-tolerant category execution (`src/collectors/`).
- Standardized Infrastructure Baseline JSON artifacts (`baselines/azure_baseline.json`, `baselines/technical_baseline.json`).
- Validated NIST OSCAL Component-Definition artifact (`baselines/oscal_component.json`).
- Air-gapped mock cloud response fixtures for zero-credential testing (`data/mock_cloud_responses/azure_mock_response.json`).
- Dedicated architecture and legal mapping documentation (`docs/ARCHITECTURE.md`, `docs/DORA_MAPPING.md`, `docs/STEP2_METHODOLOGY.md`).

**Status**: ✅ **Completed (May 2026)**

---

## 🧠 Step 3: The Automated Gap Analysis Engine

### What This Step Does
Step 3 is the semantic decision core of the compliance framework. It automatically compares what the law requires (Step 1 NIST OSCAL Catalogs) against what enterprise infrastructure actually implements (Step 2 NIST OSCAL Component-Definitions & Baselines). Rather than naive binary pass/fail assertions, it computes continuous **epistemic confidence scores** factoring in legal friction and evidence completeness, identifies infrastructure gaps with copy-pasteable Azure CLI remediation commands, and flags mandatory Human-in-the-Loop (HITL) review protocols.

### Sub-Steps
- **3.1 Gap Analysis Data Models**: Built Pydantic v2 schemas (`GapAnalysisResult`, `GapAnalysisReport`, `GapType`, `ConfidenceLevel`) modeling compliance status, gap categories, confidence levels, and summary statistics (`src/models/gap_analysis.py`).
- **3.2 Control Mapper (Regulatory → Technical)**: Maps regulatory controls to technical controls via pattern matching, heuristics, JSON configuration rules, and $O(1)$ amortized reverse indexing (`src/gap_analysis/control_mapper.py`, `data/control_mappings/gdpr_to_technical.json`).
- **3.3 Confidence Scoring Engine**: Multi-factor algorithm calculating epistemic certainty based on evidence completeness (30%), control coverage (30%), statutory friction discount (20%), and telemetry consistency (20%) (`src/gap_analysis/confidence_scorer.py`).
- **3.4 Gap Evaluator (Core Analysis Engine)**: Core pipeline engine evaluating regulatory requirements against cloud baseline telemetry, determining gap types (`MISSING`, `PARTIAL`, `NON_COMPLIANT`, `COMPLIANT`), and synthesizing technical remediations (`src/gap_analysis/gap_evaluator.py`).
- **3.5 Report Generator (JSON, Markdown, Terminal)**: Converts gap analysis results into structured machine-readable JSON (`reports/gap_analysis.json`), executive Markdown (`reports/gap_analysis.md`), and Rich-powered interactive terminal dashboards with Windows `cp1252` fallback resilience (`src/gap_analysis/report_generator.py`).

### Key Deliverables
- Complete Gap Analysis Pipeline Package (`src/gap_analysis/`).
- Strongly typed Pydantic gap analysis schemas (`src/models/gap_analysis.py`).
- Regulatory-to-technical mapping rules (`data/control_mappings/gdpr_to_technical.json`).
- Executable pipeline script (`examples/run_gap_analysis.py`) and CLI orchestrator (`src/main_gap_analysis.py`).
- Generated audit reports (`reports/gap_analysis.json`, `reports/gap_analysis.md`, `reports/gap_analysis_report.json`, `reports/gap_analysis_report.md`).
- Architectural specification (`docs/GAP_ANALYSIS_DESIGN.md`) and methodology document (`docs/STEP3_METHODOLOGY.md`).

**Status**: ✅ **Completed (June 2026)**

---

## 🔄 Step 4: Orchestration & Automation (The Pipeline)

### What This Step Does
Step 4 shifts compliance from isolated, point-in-time audits to **automated continuous monitoring**. Powered by Apache Airflow, it schedules automated cloud telemetry pulls, runs gap analysis against active statutory catalogs, calculates executive Key Performance Indicators (KPIs), and commits results to a relational database with time-series indexing. This directly implements the continuous monitoring obligations of **DORA Article 11** and **NIS2 Article 21**.

### Sub-Steps
- **4.1 Database Layer & Models**: Engineered relational schema with SQLAlchemy 2.0 ORM (`ComplianceAssessment`, `ControlAssessmentResult`, `ComplianceKPI`) supporting both local SQLite and enterprise PostgreSQL (`src/pipeline/database/models.py`).
- **4.2 Data Access Repository Layer**: Built decoupled data access layer (`ComplianceRepository`) supporting transaction-safe assessment storage, historical range queries, and KPI trend tracking (`src/pipeline/database/repository.py`).
- **4.3 Multi-Category KPI Engine**: Implemented mathematical calculation engine computing weighted compliance scores, regulation-specific metrics (GDPR, DORA, NIS2), high-confidence percentages ($\ge 80\%$), and socio-technical friction rates (`src/pipeline/kpis/compliance_kpis.py`).
- **4.4 Modular Airflow Tasks**: Built four decoupled pipeline tasks (`pull_configs`, `run_gap_analysis`, `calculate_kpis`, `store_results`) featuring XCom communication with graceful fallback for standalone execution (`src/pipeline/tasks/`).
- **4.5 Airflow DAG Orchestrator**: Authored the master DAG (`compliance_monitoring_dag.py`) scheduled weekly (`0 2 * * 1`), with automatic 2-attempt retries, 5-minute backoff, and full task dependency enforcement (`src/pipeline/dags/compliance_monitoring_dag.py`).

### Key Deliverables
- Complete Pipeline Orchestration Package (`src/pipeline/`).
- Database schema & repository layer (`src/pipeline/database/`).
- Multi-factor compliance KPI engine (`src/pipeline/kpis/`).
- Four production-grade Airflow task operators (`src/pipeline/tasks/`).
- Airflow configuration & master DAG (`airflow/airflow.cfg`, `src/pipeline/dags/compliance_monitoring_dag.py`).
- Architecture & methodology documentation (`docs/PIPELINE_DESIGN.md`, `docs/STEP4_METHODOLOGY.md`).
- Comprehensive pipeline test suite with 145 passing tests (`tests/test_pipeline.py`, `tests/test_kpis.py`).

**Status**: ✅ **Completed (July 2026)**

---

## 🚧 Upcoming Steps

### Step 5: KPI Visualization & Socio-Technical Reporting
*Status: 📋 In Progress (Target: August 2026)*  
Builds an interactive web dashboard (Streamlit / Modern UI) rendering historical compliance trajectories, regulation comparisons (GDPR vs DORA vs NIS2), interactive confidence distributions, and the Socio-Technical Friction Index. Generates board-ready executive PDF/HTML summaries with actionable Human-in-the-Loop guidance.

---

## 🛠️ Tech Stack

- **Workflow Orchestration**: Apache Airflow 2.8+ (DAG scheduling, XCom, task dependency trees)
- **Data Persistence**: SQLAlchemy 2.0+, SQLite (development/evaluation), PostgreSQL (production)
- **Data Science & Metrics**: Pandas 2.0+, NumPy 1.24+
- **Core Runtime**: Python 3.10+ (Tested against Python 3.10, 3.11, 3.12, 3.13)
- **Data Modeling & Validation**: Pydantic v2, JSON Schema (`jsonschema`)
- **Compliance Standard**: NIST OSCAL v1.1.1 (Catalogs) & v1.1.2 (Component-Definitions)
- **Cloud SDKs**: `azure-mgmt-resource`, `azure-mgmt-storage`, `azure-mgmt-network`, `azure-mgmt-compute`, `azure-mgmt-keyvault`, `azure-identity`, `boto3`
- **Testing & Mocking**: `pytest`, `pytest-cov`, `unittest.mock`, `moto` (AWS simulation)
- **Terminal UI & Visualization**: `rich`
- **Code Quality Gates**: `black`, `flake8` (`--max-line-length=120`), `mypy` (strict static typing)

---

## 📂 Project Structure

```text
automated-compliance-mapping-framework/
├── src/
│   ├── __init__.py                          # Package exports
│   ├── parser.py                            # Step 1: Regulatory text ingestion & Pydantic models
│   ├── oscal_generator.py                   # Step 1: NIST OSCAL Catalog generator
│   ├── friction_analyzer.py                 # Step 1: Socio-technical friction heuristic engine
│   ├── main.py                              # Step 1: Regulatory CLI pipeline orchestrator
│   ├── collectors/                          # Step 2: Multi-cloud infrastructure collectors
│   │   ├── __init__.py
│   │   ├── base_collector.py                # Abstract BaseCollector strategy interface
│   │   └── azure_collector.py               # Azure SDK collector & mock response handler
│   ├── normalizers/                         # Step 2: NIST OSCAL schema normalizers
│   │   ├── __init__.py
│   │   └── oscal_component_normalizer.py    # OSCAL Component-Definition generator
│   ├── main_baseline.py                     # Step 2: Multi-cloud baseline collection orchestrator
│   ├── gap_analysis/                        # Step 3: Automated Gap Analysis Pipeline
│   │   ├── __init__.py                      # Gap analysis package exports
│   │   ├── control_mapper.py                # Regulatory → technical control mapping
│   │   ├── confidence_scorer.py             # Multi-factor epistemic confidence scorer
│   │   ├── gap_evaluator.py                 # Core automated gap analysis engine
│   │   └── report_generator.py              # Multi-format report generator (JSON, MD, Terminal)
│   ├── pipeline/                            # Step 4: Orchestration & Automation Pipeline
│   │   ├── __init__.py                      # Pipeline package exports
│   │   ├── database/                        # Persistence layer
│   │   │   ├── __init__.py
│   │   │   ├── models.py                    # SQLAlchemy models (Assessment, Control, KPI)
│   │   │   └── repository.py                # Data Access Layer & historical trend queries
│   │   ├── kpis/                            # KPI calculation engine
│   │   │   ├── __init__.py
│   │   │   └── compliance_kpis.py           # Multi-category KPI calculator
│   │   ├── tasks/                           # Decoupled Airflow task callables
│   │   │   ├── __init__.py
│   │   │   ├── pull_configs.py              # Task 1: Infrastructure telemetry pull
│   │   │   ├── run_gap_analysis.py          # Task 2: Gap analysis execution
│   │   │   ├── calculate_kpis.py            # Task 3: KPI calculation
│   │   │   └── store_results.py             # Task 4: Relational persistence
│   │   └── dags/                            # Airflow DAG definitions
│   │       ├── __init__.py
│   │       └── compliance_monitoring_dag.py # Weekly master orchestration DAG
│   └── models/                              # Strongly typed Pydantic models
│       ├── __init__.py
│       ├── technical_control.py             # Step 2: TechnicalControl & Baseline models
│       └── gap_analysis.py                  # Step 3: Gap, Evaluation, & Report schemas
├── airflow/                                 # Step 4: Airflow Configuration
│   ├── airflow.cfg                          # Airflow local/production configuration
│   └── dags/                                # Airflow DAG entrypoint
│       └── compliance_monitoring_dag.py
├── data/
│   ├── sample_input.json                    # Step 1: Regulatory corpus (GDPR, DORA, NIS2)
│   ├── control_mappings/                    # Step 3: Mapping rules configuration
│   │   └── gdpr_to_technical.json           # GDPR → Technical control mappings
│   └── mock_cloud_responses/                # Step 2: Air-gapped cloud responses for testing
│       └── azure_mock_response.json
├── oscal_profiles/                          # Step 1 Generated Artifacts
│   ├── gdpr_catalog.json                    # NIST OSCAL Catalog for GDPR
│   ├── dora_catalog.json                    # NIST OSCAL Catalog for DORA
│   ├── nis2_catalog.json                    # NIST OSCAL Catalog for NIS2
│   ├── unified_catalog.json                 # Unified cross-regulation catalog
│   └── friction_report.json                 # Socio-technical friction analysis report
├── baselines/                               # Step 2 Generated Artifacts
│   ├── azure_baseline.json                  # Extracted infrastructure baseline JSON
│   ├── technical_baseline.json              # Standard technical baseline snapshot
│   └── oscal_component.json                 # Normalized NIST OSCAL Component-Definition
├── reports/                                 # Step 3 & 4 Generated Audit Artifacts
│   ├── gap_analysis.json                    # Step 3: Structured JSON gap report
│   ├── gap_analysis.md                      # Step 3: Executive Markdown report
│   ├── gap_analysis_report.json             # Extended engine JSON audit snapshot
│   └── gap_analysis_report.md               # Extended engine executive Markdown report
├── docs/                                    # Academic Research & Architecture Documentation
│   ├── ARCHITECTURE.md                      # System design, Strategy Pattern, & data pipeline
│   ├── DORA_MAPPING.md                      # Technical control alignment with DORA Articles 6 & 11
│   ├── STEP2_METHODOLOGY.md                 # Step 2 design trade-offs & friction analysis
│   ├── GAP_ANALYSIS_DESIGN.md               # Step 3 architectural design & pipeline pattern
│   ├── STEP3_METHODOLOGY.md                 # Step 3 gap analysis & epistemic confidence scoring
│   ├── PIPELINE_DESIGN.md                   # Step 4 architecture, schema, & DAG design
│   ├── STEP4_METHODOLOGY.md                 # Step 4 orchestration methodology & DORA alignment
│   ├── TESTING_METHODOLOGY.md               # Research verification pyramid & validation rigor
│   └── PROJECT_DEVELOPMENT_SUMMARY.md       # Chronological development history & milestone log
├── tests/                                   # Comprehensive Verification Suite (145 Tests)
│   ├── test_pipeline.py                     # Step 4: Tasks end-to-end & database persistence
│   ├── test_kpis.py                         # Step 4: Multi-factor KPI engine & trend queries
│   ├── test_gap_analysis.py                 # Step 3: GapEvaluator & ReportGenerator suite
│   ├── test_control_mapper.py               # Step 3: Control mapper & reverse index tests
│   ├── test_azure_collector.py              # Step 2: Azure live client & mock tests
│   ├── test_base_collector.py               # Step 2: Collector interface & error resilience tests
│   ├── test_collectors.py                   # Step 2: High-level collector tests
│   ├── test_oscal_component_normalizer.py   # Step 2: OSCAL component normalizer tests
│   ├── test_main_baseline.py                # Step 2: CLI orchestrator tests
│   ├── test_parser.py                       # Step 1: Ingestion & Pydantic validation tests
│   ├── test_friction_analyzer.py            # Step 1: Socio-technical friction heuristic tests
│   ├── test_oscal_generator.py              # Step 1: OSCAL catalog generator tests
│   ├── test_oscal_validation.py             # Step 1: Official NIST JSON Schema conformance tests
│   ├── test_edge_cases.py                   # Boundary, Unicode, and ReDoS fuzzing tests
│   ├── test_integration.py                  # Step 1: End-to-end CLI pipeline tests
│   └── README.md                            # Test documentation & coverage telemetry
├── requirements.txt                         # Production & research dependencies
└── README.md                                # Main framework documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites & Virtual Environment Setup
Ensure Python 3.10+ is installed:
```bash
# Clone the repository
git clone https://github.com/ritvik1011/automated-compliance-mapping-framework.git
cd automated-compliance-mapping-framework

# Create and activate virtual environment
python -m venv venv

# Linux / macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### 2. Dependency Installation
```bash
pip install -r requirements.txt
```

### 3. Step 1: Execute Legal Ingestion & Friction Pipeline
```bash
python -m src.main --input data/sample_input.json --output oscal_profiles/
```

### 4. Step 2: Execute Cloud Baseline Collection & OSCAL Normalization
```bash
# Zero-Credential Mock Mode (Offline evaluation)
python -m src.main_baseline \
  --provider azure \
  --mock data/mock_cloud_responses/azure_mock_response.json \
  --output baselines/azure_baseline.json \
  --oscal-output baselines/oscal_component.json
```

### 5. Step 3: Execute Automated Gap Analysis & Reporting
```bash
# Run the interactive CLI gap analysis orchestrator
python -m src.main_gap_analysis --regulation GDPR --verbose
```

### 6. Step 4: Execute Continuous Monitoring Pipeline

#### Option A: Standalone Python Execution (Zero Airflow Daemon Overhead)
Execute the complete 4-stage pipeline sequentially in Python:
```python
from src.pipeline.tasks import (
    pull_infrastructure_configs,
    run_gap_analysis,
    calculate_kpis,
    store_results,
)

# Task 1: Extract infrastructure state
t1 = pull_infrastructure_configs(cloud_provider="azure")

# Task 2: Evaluate gaps against regulatory catalog
t2 = run_gap_analysis(catalog_path="oscal_profiles/gdpr_catalog.json", baseline_metadata=t1)

# Task 3: Calculate multi-category KPIs
t3 = calculate_kpis(gap_analysis_metadata=t2)

# Task 4: Persist assessment & metrics into relational database
t4 = store_results(database_url="sqlite:///compliance.db", baseline_metadata=t1, gap_analysis_metadata=t2, kpi_metadata=t3)

print(f"✓ Pipeline run complete. Assessment ID: {t4['assessment_id']}")
```

#### Option B: Apache Airflow Orchestration (Docker / WSL / Linux)
```bash
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/src/pipeline/dags

# Initialize Airflow database
airflow db init

# Trigger the compliance monitoring DAG
airflow dags trigger compliance_monitoring_pipeline

# Check execution status
airflow dags state compliance_monitoring_pipeline
```

---

## 🧪 Testing & Empirical Verification

> For an in-depth breakdown of the verification pyramid and empirical reproducibility, see [`tests/README.md`](tests/README.md) and [`docs/TESTING_METHODOLOGY.md`](docs/TESTING_METHODOLOGY.md).

```bash
# Run all 145 automated tests
pytest -v

# Run Step 4 Pipeline & KPI tests specifically
pytest tests/test_pipeline.py tests/test_kpis.py -v

# Run with coverage telemetry (94% statement coverage across all 4 steps)
pytest --cov=src --cov-report=term-missing

# Execute static analysis quality gates
black --check src/ tests/
flake8 src/ tests/ --max-line-length=120
mypy src/ tests/
```

---

## 📊 Research Focus & Academic Alignment

Traditional GRC platforms assume that legal compliance is a binary decision problem reducible to simple Boolean rules. However, analysis of primary EU statutory legislation demonstrates that regulatory requirements rely extensively on **open-textured legal terms** ("appropriate technical measures", "state of the art", "proportionate").

This research project introduces:
1. **The Socio-Technical Friction Index**: A quantitative heuristic assessing the cognitive and operational friction imposed on engineering teams by ambiguous legal text.
2. **Standardized OSCAL Transformation**: Demonstration that both normative legal rules (Step 1) and empirical cloud infrastructure states (Step 2) can be unified under the NIST OSCAL specification.
3. **Epistemic Confidence Scoring**: Multi-factor mathematical scoring that quantifies uncertainty in automated compliance evaluation, actively preventing "False Assurance."
4. **Continuous Evidence Telemetry (Step 4)**: Shifting compliance from point-in-time annual audits to automated, verifiable Policy-as-Code pipelines, satisfying the continuous monitoring mandates of **DORA Article 11** and **NIS2 Article 21**.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ritvik Bahirwar**  
*Master's in Computer Engineering for IoT Systems*  
Research Focus: Policy-as-Code, Socio-Technical Cybersecurity, and Cloud Governance Automation  
Academic Portfolio Project for the Max Planck Institute for Security and Privacy (MPI-SP)
