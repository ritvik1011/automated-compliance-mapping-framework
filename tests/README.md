# Testing & Quality Assurance Methodology

> Comprehensive testing documentation for the **Automated Compliance Mapping & Gap Analysis Framework**, detailing test architectures, verification strategies, NIST OSCAL schema validation, and empirical research reproducibility.

---

## 🎯 Testing Philosophy & Research Grounding

In cybersecurity compliance research and Policy-as-Code engineering, automated verification is not merely a software hygiene practice—it is the **empirical baseline** that validates whether legal mandates can be reliably translated into machine-readable controls without semantic drift or false assurance.

This framework integrates automated testing across four orthogonal dimensions:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   NIST OSCAL Schema Validation                         │
│     (Official v1.1.1 JSON Schema compliance via jsonschema/regex)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    End-to-End Integration Tests                        │
│          (CLI Orchestrator: Ingest -> Analyze -> Generate)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                  Adversarial & Edge-Case Testing                       │
│    (Unicode/Emojis, Malformed JSON, Empty Files, 60k+ char payloads)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                         Core Unit Tests                                │
│       Parser (Pydantic) | Friction Engine | OSCAL Profile Generator    │
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
├── test_integration.py        # End-to-end CLI orchestrator and artifact generation
├── test_oscal_validation.py   # Strict schema validation against official NIST schema
└── test_edge_cases.py         # Boundary fuzzing, Unicode, ReDoS resistance, malformed input
```

---

## 🔬 Test Modules & Methodological Rationale

### 1. `tests/test_parser.py` (Regulatory Ingestion Engine)
- **What it tests**: Multi-regulation JSON ingestion, Pydantic schema validation, regulation name canonicalization (`"gdpr"` -> `"GDPR"`, `"nis 2"` -> `"NIS2"`), ID sanitization into OSCAL-compatible NCNames, and handling of malformed payloads.
- **Why it matters**: Incomplete or unnormalized legal metadata corrupts downstream semantic mapping and causes catalog validation failures.
- **Key Cases**:
  - `test_parser_reads_valid_gdpr_article`: Verifies clean parsing and sub-clause extraction.
  - `test_parser_handles_multiple_regulations`: Ingestion of heterogeneous GDPR, DORA, and NIS2 corpora.
  - `test_parser_sanitizes_article_ids`: Normalizes whitespace and invalid characters.
  - `test_parser_applicability_parsing`: Flexible parsing of lists, comma-separated strings, and null values.
  - `test_parser_rejects_missing_required_fields`: Fail-fast Pydantic validation on incomplete models.

### 2. `tests/test_friction_analyzer.py` (Socio-Technical Friction Engine)
- **What it tests**: Heuristic keyword scanner and scoring algorithm for open-textured legal terminology ("state of the art", "appropriate technical measures", "proportionate").
- **Why it matters**: Investigates the core research hypothesis: legal indeterminacy creates operational friction that resists binary (Pass/Fail) Policy-as-Code automation.
- **Key Cases**:
  - `test_detects_high_friction_with_multiple_ambiguous_words`: Flags compounding ambiguity.
  - `test_detects_state_of_the_art_phrase`: Isolates the primary trigger requiring dynamic telemetry.
  - `test_detects_low_friction_with_binary_language`: Verifies high automation readiness for strict deadlines (e.g., "within 72 hours").
  - `test_detects_medium_friction_with_mixed_language`: Validates hybrid evaluation requirements.
  - `test_friction_analyzer_hitl_guidance_generation`: Verifies generation of actionable Human-in-the-Loop recommendations.

### 3. `tests/test_oscal_generator.py` (NIST OSCAL Catalog Generator)
- **What it tests**: Construction of NIST OSCAL v1.1.1 Catalog data models, control properties, sub-clause nesting into OSCAL `parts` (`item` / `statement`), and custom friction namespace encoding.
- **Why it matters**: Generates standards-compliant artifacts that integrate directly with enterprise GRC platforms (FedRAMP, OpenShift Compliance Operator, Trestle).
- **Key Cases**:
  - `test_oscal_output_has_catalog_root`: Verifies mandatory root dictionary structure.
  - `test_oscal_control_includes_friction_level`: Asserts friction metadata is embedded in `props` under `https://automated-compliance.org/ns/friction`.
  - `test_oscal_sub_clauses_mapped_to_parts`: Validates hierarchical decomposition of clauses.

### 4. `tests/test_oscal_validation.py` (Official NIST Schema Validation)
- **What it tests**: Direct schema validation of all generated catalogs (`gdpr_catalog.json`, `dora_catalog.json`, `nis2_catalog.json`, `unified_catalog.json`) against the official NIST JSON Schema (`oscal_catalog_schema.json`).
- **Why it matters**: Guarantees zero schema divergence, ensuring academic and industrial portability.
- **Implementation Note**: Uses the `regex` engine monkey-patched into `jsonschema` to support ECMA-262 Unicode category properties (`\p{L}`, `\p{N}`) specified by NIST.

### 5. `tests/test_integration.py` (CLI Pipeline Orchestration)
- **What it tests**: End-to-end execution of `main.py` and `run_pipeline()`, checking artifact emission, regulation filtering, and Rich terminal visualization.
- **Why it matters**: Ensures all modules interact cleanly under realistic command-line invocation scenarios.

### 6. `tests/test_edge_cases.py` (Adversarial Robustness)
- **What it tests**: Multilingual text (German DSGVO, Chinese cybersecurity law), emojis (🛡️), empty JSON arrays, duplicate article IDs, 60,000+ character legal texts (ReDoS prevention), and malformed syntax.
- **Why it matters**: Protects the framework against denial-of-service vulnerabilities and edge-case ingestion crashes.

---

## 🚀 Running the Tests

### Quick Execution
```bash
# Run all 53 test cases
pytest -v
```

### Run with Coverage Telemetry
```bash
# Terminal output with line numbers of untested code
pytest -v --cov=src --cov-report=term-missing

# Generate visual HTML coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Modules
```bash
# Run only OSCAL schema validation
pytest tests/test_oscal_validation.py -v

# Run only friction heuristic tests
pytest tests/test_friction_analyzer.py -v
```

---

## 📊 Coverage & Quality Standards

| Module | Statements | Missing Lines | Coverage | Status |
| :--- | :---: | :---: | :---: | :---: |
| `src/__init__.py` | 4 | 0 | **100%** | Passed |
| `src/friction_analyzer.py` | 172 | 7 | **96%** | Passed |
| `src/main.py` | 124 | 6 | **95%** | Passed |
| `src/oscal_generator.py` | 85 | 2 | **98%** | Passed |
| `src/parser.py` | 133 | 29 | **78%** | Passed |
| **Total Project** | **518** | **44** | **92%** | **Exceeds Target (>80%)** |

### Static Analysis Checks
```bash
# Code formatting check
black --check src/ tests/

# Style & PEP 8 validation
flake8 src/ tests/ --max-line-length=100

# Strict static type safety
mypy src/ tests/
```
