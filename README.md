# Automated Compliance Mapping & Gap Analysis Framework

> A Policy-as-Code research project translating complex regulatory mandates (GDPR, DORA, NIS2) into machine-readable OSCAL formats, with a specialized focus on identifying socio-technical friction points in enterprise environments.

## 🎯 Project Objective
Regulatory compliance is often treated as a purely technical checkbox, leading to "security fatigue" and operational friction. This framework bridges the gap between legal text and technical implementation by:
1. Parsing regulatory articles into structured, machine-readable formats.
2. Generating standardized **OSCAL (Open Security Controls Assessment Language)** catalogs.
3. Analyzing and documenting **socio-technical friction points** where legal ambiguity (e.g., "appropriate technical measures") prevents 1:1 binary automation, requiring human-in-the-loop validation.

## 🔬 Research Focus Areas
- **Policy-as-Code**: Translating GDPR Article 32 and DORA ICT risk mandates into executable logic.
- **Socio-Technical Security**: Evaluating the cognitive load and process bottlenecks faced by engineering teams when implementing abstract compliance mandates.
- **Automation**: Reducing manual GRC data synthesis time through Python-based orchestration.

## 📅 Project Timeline & Development History

This research initiative follows an agile, sprint-based engineering lifecycle designed to model and evaluate Policy-as-Code automation across complex socio-technical environments.

| Phase | Milestone / Milestone Focus | Timeframe | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1: Ingestion & Standardization** | Foundation: Pydantic parsing, NIST OSCAL generation, and socio-technical friction heuristic analysis engine | **March 1 – March 31, 2026** | **Completed** |
| **Phase 2: Semantic Mapping & Gap Analysis** | Cross-framework vector embeddings, semantic clustering, and regulatory divergence quantification | **April 2026** | *In Progress* |
| **Phase 3: Automated Enforcement & OPA Engine** | Rego/OPA policy generation, CI/CD compliance gates, and continuous evidence telemetry | **May 2026** | *Planned* |

### Phase 1 Sprint Milestones (March 2026)
- **March 1, 2026**: **Project Inception & Architecture Scaffolding** — Initialized repository structure, environment specifications (`requirements.txt`), licensing, and NIST OSCAL alignment baseline.
- **March 8, 2026**: **Regulatory Text Ingestion Engine** — Implemented `RegulatoryParser` with Pydantic v2 schemas and mock multi-regime legal corpus (`data/sample_input.json`).
- **March 15, 2026**: **NIST OSCAL Catalog Generator** — Engineered `OSCALGenerator` mapping regulatory provisions into standardized OSCAL Catalog JSON models (v1.1.1).
- **March 22, 2026**: **Socio-Technical Friction Analysis Engine** — Built `FrictionAnalyzer` to detect legal indeterminacy and open-textured terms, scoring automation feasibility and generating HITL recommendations.
- **March 27, 2026**: **Pipeline Orchestration & Rich CLI** — Developed `main.py` orchestrator with multi-regulation filtering, rich terminal visualizations, and artifact persistence.
- **March 31, 2026**: **Verification, Hardening & Phase 1 Release** — Delivered unit test suite (`tests/test_parser.py`), edge-case normalization, comprehensive documentation, and final Phase 1 catalog artifacts.

## 🛠️ Tech Stack
- **Core Language**: Python 3.10+
- **Data Modeling**: OSCAL (JSON/YAML), Pydantic
- **Policy Evaluation**: Open Policy Agent (OPA) / Custom Python Assertions
- **Visualization**: Streamlit / Rich (Terminal)
- **Version Control**: Git, GitHub

## 📂 Project Structure
```text
├── src/
│   ├── __init__.py            # Package initialization and exports
│   ├── parser.py              # Ingests, validates, and structures regulatory text
│   ├── oscal_generator.py     # Maps parsed data to NIST OSCAL catalog schema
│   ├── friction_analyzer.py   # Heuristic engine for socio-technical friction detection
│   └── main.py                # CLI pipeline orchestrator with Rich reporting
├── data/
│   └── sample_input.json      # Mock GDPR, DORA, and NIS2 articles for testing
├── oscal_profiles/            # Generated NIST OSCAL catalogs and friction reports
│   ├── gdpr_catalog.json      # OSCAL Catalog for GDPR
│   ├── dora_catalog.json      # OSCAL Catalog for DORA
│   ├── nis2_catalog.json      # OSCAL Catalog for NIS2
│   ├── unified_catalog.json   # Multi-regulation OSCAL catalog
│   └── friction_report.json   # Detailed socio-technical friction analysis report
├── tests/
│   ├── __init__.py            # Test package marker
│   ├── test_parser.py         # Regulatory parser test suite
│   ├── test_friction_analyzer.py # Socio-technical friction analysis tests
│   ├── test_oscal_generator.py # OSCAL generation and control mapping tests
│   ├── test_oscal_validation.py # Official NIST schema validation tests
│   ├── test_edge_cases.py     # Extreme inputs, Unicode, and empty file tests
│   └── test_integration.py    # Multi-regulation end-to-end pipeline tests
├── oscal_catalog_schema.json  # Official NIST OSCAL v1.1.1 JSON schema
├── requirements.txt           # Python dependencies and development tools
└── README.md
```

## 🚀 Quickstart & Pipeline Execution

### 1. Setup Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS / Linux:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
venv\Scripts\activate.bat
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download the NIST OSCAL Catalog Schema
Download the official NIST OSCAL schema (v1.1.1) for control catalog validation:
```bash
# macOS / Linux / Windows:
curl -L -o oscal_catalog_schema.json https://github.com/usnistgov/OSCAL/releases/download/v1.1.1/oscal_catalog_schema.json
```

### 4. Run the Full Ingestion & Friction Analysis Pipeline
Execute the pipeline orchestrator:
```bash
python -m src.main --input data/sample_input.json --output oscal_profiles/
# or
python src/main.py
```

Optional CLI parameters:
```bash
# Filter for a specific regulation (GDPR, DORA, or NIS2)
python -m src.main --regulation GDPR

# Specify custom input and output paths
python -m src.main --input data/sample_input.json --output-dir oscal_profiles/

# Enable verbose debug logging
python -m src.main --verbose
```

## 🧪 Testing Suite & Validation

### Run Full Test Suite
```bash
pytest -v
```

### Run NIST OSCAL Schema Validation
Validates that generated catalogs strictly conform to the official NIST OSCAL Control Catalog standard:
```bash
pytest tests/test_oscal_validation.py -v -s
```

### Run Code Coverage Analysis
```bash
# Generate terminal and HTML reports
pytest --cov=src --cov-report=term-missing --cov-report=html

# View HTML coverage report in browser:
# Windows:
start htmlcov/index.html
# macOS:
open htmlcov/index.html
# Linux:
xdg-open htmlcov/index.html
```

## 🧹 Code Quality & Static Analysis

```bash
# 1. Black: Auto-format code
black src/ tests/

# 2. Flake8: Style & PEP 8 validation
flake8 src/ tests/ --max-line-length=100

# 3. Mypy: Strict static type checking
mypy src/
```

## 🧠 Socio-Technical Friction Research Alignment
Traditional Policy-as-Code frameworks assume that compliance obligations map directly to deterministic, binary (Pass/Fail) infrastructure assertions. However, regulatory frameworks (GDPR Art. 32, DORA Art. 6, NIS2 Art. 21) are deliberately drafted with **open-textured legal terms** ("state of the art", "proportionate", "appropriate measures").

This framework systematically extracts these friction points, scores their automation feasibility, and generates structured **Human-in-the-Loop (HITL)** engineering recommendations to prevent false assurance and developer compliance fatigue.
