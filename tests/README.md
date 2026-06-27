# Testing & Quality Assurance Methodology

> Comprehensive testing documentation for the **Automated Compliance Mapping & Gap Analysis Framework**, detailing test architectures, verification strategies, NIST OSCAL schema validation, multi-cloud mock simulation, and empirical research reproducibility.

---

## 🎯 Testing Philosophy & Research Grounding

In cybersecurity compliance research and Policy-as-Code engineering, automated verification is not merely a software hygiene practice—it is the **empirical baseline** that validates whether legal mandates and technical infrastructure states can be reliably translated into machine-readable controls without semantic drift or false assurance.

This framework integrates automated testing across five orthogonal dimensions:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   NIST OSCAL Schema Validation                         │
│     (Official v1.1.1 Catalog & v1.1.2 Component-Definition schemas)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    End-to-End Integration Tests                        │
│     (CLI Pipelines: Ingest -> Analyze -> Collect -> Normalize)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                 Multi-Cloud Mock Response Verification                 │
│      (Zero-Credential ARM / SDK Mocking & Offline JSON Simulation)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                  Adversarial & Edge-Case Testing                       │
│    (Unicode/Emojis, Malformed JSON, Empty Files, 60k+ char payloads)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                         Core Unit Tests                                │
│       Parser | Friction Engine | Cloud Collectors | OSCAL Normalizer   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Test Suite Structure

```text
tests/
├── __init__.py                # Test package marker
├── conftest.py                # Shared pytest fixtures (session & function scoped)
├── test_parser.py             # Unit tests for regulatory ingestion & Pydantic validation
├── test_friction_analyzer.py  # Unit tests for heuristic socio-technical friction engine
├── test_oscal_generator.py    # Unit tests for NIST OSCAL catalog construction
├── test_oscal_validation.py   # Strict schema validation against official NIST schema
├── test_edge_cases.py         # Boundary fuzzing, Unicode, ReDoS resistance, malformed input
├── test_integration.py        # Multi-regulation end-to-end pipeline integration
├── test_technical_control.py  # Pydantic technical control & baseline model tests
├── test_base_collector.py     # BaseCollector interface, error isolation, & persistence
├── test_azure_collector.py    # AzureCollector live SDK client & mock response tests
├── test_collectors.py         # End-to-end cloud collector error handling & boundary tests
├── test_oscal_component_normalizer.py # NIST OSCAL Component-Definition generator tests
├── test_normalizers.py        # Normalizer suite alias for OSCAL component tests
├── test_main_baseline.py      # Baseline orchestrator CLI & Rich UI tests
├── test_control_mapper.py     # Step 3: Regulatory-to-technical control mapping & reverse index
└── test_gap_analysis.py       # Step 3: GapEvaluator, ConfidenceScorer, & ReportGenerator suite
```

---

## 🔬 Test Modules & Methodological Rationale

### 1. Regulatory Ingestion & Friction Analysis (Step 1)
- **`test_parser.py`**: Verifies multi-regulation JSON parsing, Pydantic schema validation, regulation name canonicalization (`"gdpr"` -> `"GDPR"`), and NCName ID sanitization.
- **`test_friction_analyzer.py`**: Validates the detection of open-textured legal terms ("state of the art", "appropriate technical measures"), scoring automation feasibility and generating HITL guidance.
- **`test_oscal_generator.py`**: Tests translation of regulatory articles into NIST OSCAL Catalog JSON models with friction properties.
- **`test_oscal_validation.py`**: Asserts strict compliance with the official NIST OSCAL Control Catalog JSON Schema (v1.1.1).
- **`test_edge_cases.py`**: Fuzzes parsers with adversarial inputs (Unicode, emojis, 60k ReDoS payloads, empty files).
- **`test_integration.py`**: Tests end-to-end Step 1 pipeline execution from raw JSON to catalog artifacts.

### 2. Technical Control Baseline Collection (Step 2)
- **`test_technical_control.py`**: Verifies Pydantic v2 runtime validation for `TechnicalControl` and `InfrastructureBaseline`, ensuring invalid control IDs are rejected and serialization preserves ISO 8601 timestamps.
- **`test_base_collector.py`**: Asserts that `BaseCollector` cannot be instantiated directly (abstract contract), verifies the fault-tolerant category execution loop, and confirms error isolation.
- **`test_azure_collector.py`**: Comprehensive verification of `AzureCollector` across all four control categories (IAM, Encryption, Network, Backup) using both mocked Azure SDK clients and local offline mock responses.
- **`test_collectors.py`**: High-level integration tests asserting baseline collection integrity, multi-cloud dispatching, and compliance status rollup.
- **`test_oscal_component_normalizer.py` / `test_normalizers.py`**: Validates transformation of infrastructure baselines into NIST OSCAL Component-Definitions (v1.1.2), asserting resource-level component deduplication and weakest-link compliance evaluation.
- **`test_main_baseline.py`**: Verifies the CLI baseline collection orchestrator, testing provider selection, subscription overrides, mock data flags, and Rich table rendering.

### 3. Automated Gap Analysis Engine (Step 3)
- **`test_control_mapper.py`**: Validates `ControlMapper` default heuristic rules, JSON configuration ingestion, wildcard pattern expansion (`azure-storage-encryption-*`), reverse indexing ($O(1)$ amortized lookups), unmapped control isolation, and dynamic rule additions.
- **`test_gap_analysis.py`**: Comprehensive suite validating:
  - Pydantic models (`GapType`, `ConfidenceLevel`, `GapAnalysisResult`, `GapAnalysisReport`).
  - Epistemic confidence scoring bounds $[0.0, 1.0]$, status consistency deductions, legal friction penalties, and evidence quality adjustments.
  - Gap evaluation pipeline verifying `MISSING`, `PARTIAL`, `NON_COMPLIANT`, and `COMPLIANT` outcomes.
  - Multi-target report generation (JSON, Markdown, and Windows `cp1252`-resilient Rich terminal output).

---

## 🧪 Zero-Credential Testing Strategy

To guarantee that academic peer reviewers and CI/CD pipelines can reproduce all tests without requiring live Azure subscriptions, testing employs a dual-layer mocking strategy:

1. **Local Response Simulation (`data/mock_cloud_responses/azure_mock_response.json`)**: Realistic JSON responses containing storage accounts, virtual machines, network security groups, and key vaults.
2. **SDK Object Mocking (`unittest.mock`)**: Mocking ARM SDK client methods (`virtual_machines.list_all`, `storage_accounts.list_by_resource_group`) to simulate transient network timeouts, `403 Forbidden` errors, and malformed API returns.

---

## 🚀 Test Execution Commands

### Quick Execution
```bash
# Run all 93 test cases
pytest -v
```

### Run Step 2 Collector & Normalizer Tests Specifically
```bash
pytest tests/test_collectors.py tests/test_normalizers.py -v
```

### Run with Coverage Telemetry
```bash
# Terminal output with missing line numbers
pytest -v --cov=src --cov-report=term-missing

# Generate visual HTML coverage report
pytest --cov=src --cov-report=html
```

---

## 📊 Coverage & Quality Standards

| Module | Statements | Missing Lines | Coverage | Status |
| :--- | :---: | :---: | :---: | :---: |
| `src/__init__.py` | 4 | 0 | **100%** | Passed |
| `src/models/technical_control.py` | 57 | 0 | **100%** | Passed |
| `src/models/__init__.py` | 2 | 0 | **100%** | Passed |
| `src/collectors/__init__.py` | 3 | 0 | **100%** | Passed |
| `src/collectors/base_collector.py` | 60 | 6 | **90%** | Passed |
| `src/collectors/azure_collector.py` | 282 | 26 | **91%** | Passed |
| `src/normalizers/__init__.py` | 2 | 0 | **100%** | Passed |
| `src/normalizers/oscal_component_normalizer.py` | 68 | 2 | **97%** | Passed |
| `src/main_baseline.py` | 105 | 6 | **94%** | Passed |
| `src/oscal_generator.py` | 85 | 2 | **98%** | Passed |
| `src/friction_analyzer.py` | 172 | 7 | **96%** | Passed |
| `src/main.py` | 124 | 6 | **95%** | Passed |
| `src/parser.py` | 133 | 29 | **78%** | Passed |
| `src/gap_analysis/control_mapper.py` | 118 | 4 | **96%** | Passed |
| `src/gap_analysis/confidence_scorer.py` | 52 | 2 | **96%** | Passed |
| `src/gap_analysis/gap_evaluator.py` | 98 | 6 | **94%** | Passed |
| `src/gap_analysis/report_generator.py` | 120 | 8 | **93%** | Passed |
| `src/models/gap_analysis.py` | 92 | 2 | **98%** | Passed |
| **Total Framework (135 Tests)** | **1,577** | **106** | **93%** | **Exceeds Target (>80%)** |

### Static Analysis & Quality Gates
```bash
# Code formatting check
black --check src/ tests/

# Style & PEP 8 validation
flake8 src/ tests/ --max-line-length=100

# Strict static type safety
mypy src/ tests/
```
All static analysis checks pass with **zero warnings and zero errors**.
