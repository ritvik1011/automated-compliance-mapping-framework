# Empirical Testing & Verification Methodology

**Project:** Automated Compliance Mapping & Gap Analysis Framework  
**Author:** Ritvik Bahirwar  
**Affiliation:** Max Planck Institute for Security and Privacy (MPI-SP) Application Portfolio  
**Phase:** Phase 1 Milestone — Testing, Verification & Hardening (April 2026)

---

## 1. Executive Summary & Research Motivation

In regulatory technology and Policy-as-Code research, verifying automated systems poses a unique challenge: legal mandates are intentionally drafted with **open-textured standards** (e.g., GDPR Art. 32 *"state of the art"*, DORA Art. 6 *"sound and comprehensive"*, NIS2 Art. 21 *"proportionate measures"*). 

Traditional software engineering tests verify deterministic inputs against deterministic outputs. However, an academic compliance framework must verify two disparate phenomena:
1. **Syntactic Conformance**: Does the emitted data model strictly adhere to the formal specification (NIST OSCAL v1.1.1)?
2. **Semantic & Socio-Technical Fidelity**: Does the framework reliably detect and flag clauses that resist automated binary evaluation, providing appropriate Human-in-the-Loop (HITL) escalations?

This document outlines the testing architecture designed to guarantee both mathematical correctness and research reproducibility.

---

## 2. Test Architecture Overview

The framework employs a four-tiered verification pyramid:

```text
               ┌────────────────────────┐
               │  NIST OSCAL Validation │  (Schema conformance, 4 catalogs)
               ├────────────────────────┤
               │   Integration Suite    │  (End-to-end pipeline execution)
               ├────────────────────────┤
               │ Adversarial / Fuzzing  │  (Unicode, ReDoS, malformed JSON)
               ├────────────────────────┤
               │    Core Unit Tests     │  (Parser, Friction, Generator)
               └────────────────────────┘
```

### Architectural Guarantees:
- **Test Independence**: Every test function executes in complete isolation. Zero shared mutable state.
- **Idempotence**: Tests produce the exact same assertions regardless of execution order or frequency.
- **Filesystem Isolation**: All temporary files and test catalogs are generated in ephemeral `tmp_path` fixtures managed by pytest and cleaned up automatically.
- **Zero Network Flakiness**: All test dependencies (including regulatory inputs and NIST schema files) are local and pinned.

---

## 3. Socio-Technical Friction Verification Paradigm

A central contribution of this research is the **Socio-Technical Friction Analyzer**. The testing strategy evaluates the analyzer's heuristic classification against three distinct linguistic categories:

| Friction Tier | Linguistic Indicators | Test Case | Expected Framework Output |
| :--- | :--- | :--- | :--- |
| **HIGH** | "appropriate", "state of the art", "organisational measures" | `test_detects_high_friction_with_multiple_ambiguous_words` | Friction Level: `HIGH`, Automation Readiness: `LOW`, `hitl_recommended: true` |
| **MEDIUM** | "reasonable estimates", "proportionate taking into account size" | `test_detects_medium_friction_with_mixed_language` | Friction Level: `MEDIUM`, Automation Readiness: `MEDIUM`, Hybrid verification |
| **LOW** | "within 72 hours", "at least 12 months", "SHA-256" | `test_detects_low_friction_with_binary_language` | Friction Level: `LOW`, Automation Readiness: `HIGH`, Direct policy rule |

### ReDoS (Regular Expression Denial of Service) Resilience
Regulatory recitals often span several pages. To verify that regex heuristic engines do not exhibit catastrophic backtracking, `test_friction_analyzer_handles_extremely_long_legal_text` subjects the engine to ~65,000-character input payloads and validates linear $O(n)$ completion time.

---

## 4. NIST OSCAL Schema Conformance Strategy

To ensure research credibility and industry interoperability, our test suite integrates direct validation against the official **NIST OSCAL v1.1.1 Control Catalog JSON Schema**.

### Technical Challenges & Solutions:
- **ECMA-262 Unicode Character Properties**: The official NIST schema uses regex patterns like `^\p{L}[\p{L}\p{N}_.-]*$`. Standard Python `re` does not support `\p{L}` (Unicode letter) or `\p{N}` (Unicode number).
- **Engine Patching**: `tests/test_oscal_validation.py` introduces dynamic monkey-patching of `jsonschema._keywords.re` and `jsonschema._format.re` with Python's compiled `regex` engine, allowing full Draft-07 compliance validation without modifying upstream NIST schema files.

```python
# Schema validation pattern
import jsonschema
import regex
jsonschema._keywords.re = regex
jsonschema._format.re = regex

validator = jsonschema.Draft7Validator(nist_schema)
errors = list(validator.iter_errors(generated_catalog))
assert len(errors) == 0
```

---

## 5. Adversarial Input & Boundary Testing

Real-world regulatory feeds from the European Commission, ENISA, and national authorities present extreme variations in text encoding and structure.

1. **Multilingual Unicode Payloads (`test_parser_handles_multilingual_and_unicode_payloads`)**:
   - Ingests mixed German (DSGVO), Chinese (网络安全与数据保护法规), and emoji glyphs (🛡️) to ensure UTF-8 encoding stability across string slicing and serialization.
2. **Deduplication & Collision Defense (`test_parser_handles_duplicate_article_identifiers`)**:
   - Ingests multiple articles bearing identical `article_id` fields, asserting that deterministic deduplication preserves data consistency without runtime crashes.
3. **Empty Payloads & Malformed Syntaxes (`test_parser_rejects_malformed_json_inputs`)**:
   - Asserts that corrupt JSON, empty arrays (`[]`), and non-dictionary items raise typed exceptions (`ValueError`, `ValidationError`) rather than unhandled tracebacks.

---

## 6. Continuous Verification & Quality Gates

The framework enforces static analysis and test automation on every push and pull request via GitHub Actions:

```yaml
# .github/workflows/tests.yml Quality Pipeline
- Black Formatter (PEP 8 code formatting)
- Flake8 Linter (max-line-length=100, zero syntax warnings)
- Mypy Static Type Checker (strict typing on all signatures)
- Pytest Suite with Coverage (minimum gate: >80%, current: 92%)
```

---

## 7. Research Reproducibility Guide

To reproduce all experimental results reported in this framework:

```bash
# 1. Clone repository
git clone https://github.com/ritvik1011/automated-compliance-mapping-framework.git
cd automated-compliance-mapping-framework

# 2. Initialize clean environment
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# 3. Execute full verification suite with coverage telemetry
pytest -v --cov=src --cov-report=term-missing --cov-report=html

# 4. Validate official NIST OSCAL schema
pytest tests/test_oscal_validation.py -v -s
```

All 53 test cases execute in ~4.0 seconds on standard consumer hardware, providing rapid, deterministic feedback for compliance researchers and software engineers.
