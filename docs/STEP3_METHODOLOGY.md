# Step 3: Automated Gap Analysis Engine — Methodology

> **Academic Research Context**: Policy-as-Code & Automated Compliance Mapping Framework  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Lifecycle Phase**: Step 3 — Automated Gap Analysis & Epistemic Confidence Scoring  

---

## 1. Research Context

This module addresses the core challenge of Policy-as-Code: **How do we automatically compare regulatory requirements against technical implementations when the mapping is rarely 1:1?**

Automated governance systems face a fundamental dilemma when evaluating compliance between statutory legal texts and empirical cloud systems:

$$\text{Legal Statute (Qualitative, Ambiguous)} \iff \text{Cloud Infrastructure (Deterministic, Binary)}$$

- **Step 1 Output**: NIST OSCAL Control Catalogs defining statutory obligations from **GDPR**, **DORA**, and **NIS2**, annotated with Socio-Technical Friction scores and Human-in-the-Loop (HITL) recommendations.
- **Step 2 Output**: NIST OSCAL Component-Definitions and Infrastructure Baselines capturing empirical cloud configurations across security categories (Identity & Access Management, Data Encryption, Network Security, Backup & Recovery, Logging & Monitoring).
- **The Core Dilemma**: How do we automatically compare qualitative legal expectations with binary technical telemetry without falling into the **"False Assurance" trap**—the erroneous belief that passing a binary technical check implies complete statutory immunity?

Step 3 introduces the **Automated Gap Analysis Engine**, delivering an evidence-driven, ambiguity-aware compliance evaluation system.

---

## 2. Design Decisions

### 2.1 Pure Python vs OPA (Open Policy Agent)
**Decision**: Pure Python as primary approach.

**Rationale**:
- **Resume & Project Focus**: Aligns with Python-based automation and data science pipelines.
- **Custom Mathematical Logic**: Greater flexibility for continuous mathematical logic (confidence scoring equations, socio-technical friction discounts, non-linear penalties).
- **Academic Transparency & Debuggability**: Easier to explain, inspect via debugger tracing, and review for academic evaluators without requiring external Rego runtimes.
- **Lower Barrier to Entry**: No requirement for end-users to learn declarative Rego syntax.

**Trade-offs**:
- May not scale as natively as OPA daemon sidecars for ultra-high-throughput sub-millisecond API admission control in large Kubernetes clusters.
- Less out-of-the-box integration with existing enterprise GRC platforms that standardize exclusively on OPA/Gatekeeper.
- *Future Roadmap (Step 4)*: Step 3's Python engine can serve as an upstream compiler that synthesizes OPA/Rego constraints for CI/CD runtime gates.

| Evaluation Dimension | Pure Python (Chosen Approach) | Open Policy Agent (OPA / Rego) |
| :--- | :--- | :--- |
| **Epistemic Confidence Scoring** | Direct implementation of multi-factor continuous mathematical scoring functions ($0.000 - 1.000$). | Difficult to represent continuous non-linear arithmetic in declarative Rego. |
| **Socio-Technical Friction Integration** | Seamless coupling with Step 1 friction heuristics and Step 2 Pydantic telemetry models. | Requires translating heuristic dictionary structures into flat OPA data payloads. |
| **Academic Transparency & Reproducibility** | Native Python AST allows step-by-step debugger tracing and transparent review for MPI-SP reviewers. | Black-box policy evaluation requiring specialized Rego runtime toolchains. |
| **Remediation Directives** | Generates tailored cloud CLI commands (Azure CLI, AWS CLI) and localized remediation advice dynamically. | Primarily limited to binary `allow` / `deny` decisions with static message strings. |
| **Future Enterprise Path** | Can serve as an upstream decision compiler that generates Rego rules for CI/CD gates (Step 4). | Best suited for sub-millisecond API admission control, not complex multi-framework gap reasoning. |

### 2.2 Confidence Scoring
**Decision**: Multi-factor epistemic confidence scoring algorithm.

**Factors & Mathematical Weights**:
- **Evidence Completeness (30%)**: Volume and coverage of mapped technical controls observed in the active baseline.
- **Control Coverage (30%)**: Proportion of required technical security categories validated against statutory obligations.
- **Friction Level (20%)**: Ambiguity discount derived from legal text analysis (penalizes open-textured phrases like "appropriate technical measures" or "state of the art").
- **Data Quality & Status Consistency (20%)**: Consistency among telemetry observations across multi-resource environments (penalizes mixed compliant/non-compliant statuses).

$$C_{\text{confidence}} = \max\Big(0.0, \, \min\big(1.0, \, E_{\text{coverage}} \times (1.0 - P_{\text{friction}}) \times K_{\text{consistency}} + Q_{\text{adjustment}}\big)\Big)$$

**Confidence Categorization**:
- **HIGH** ($\ge 80\%$): High evidence volume, consistent telemetry, low legal ambiguity.
- **MEDIUM** ($50\% - 79.9\%$): Sufficient evidence with minor status divergence or moderate legal friction.
- **LOW** ($< 50\%$): Zero or sparse technical controls, high legal ambiguity, or contradictory configurations requiring Human-in-the-Loop (HITL) review.

**Rationale**: Acknowledges uncertainty in automated assessment and quantifies reliability, preventing "False Assurance."

### 2.3 Control Mapping Strategy
**Decision**: Hybrid approach (pre-defined rules + wildcard heuristics + bidirectional reverse indexing).

**Rationale**:
- Balances automation with human expertise, recognizing that full automation of regulatory mapping is not yet feasible.
- Forward mapping supports wildcard prefix expansion (e.g. `azure-storage-encryption-*`).
- Reverse index ($O(1)$ lookup) enables instant querying from technical infrastructure components back to the originating statutory obligations.

---

## 3. Socio-Technical Friction Findings

During implementation and testing, we identified several fundamental friction points:

1. **Mapping Ambiguity**: Regulatory mandates (e.g., GDPR Art. 32 "appropriate technical and organizational measures") cannot be mapped 1:1 to discrete cloud settings. A single legal clause often fans out across identity, encryption, network isolation, and redundancy.
2. **Partial Compliance**: Infrastructure frequently satisfies some technical requirements while failing others (e.g., storage encryption enabled with Microsoft-managed keys instead of customer-managed keys). Binary pass/fail models fail to capture this state.
3. **Evidence Gaps**: Not all technical controls provide verifiable programmatic telemetry. Certain governance obligations (e.g., employee vetting, incident response tabletop testing) produce zero cloud API artifacts.
4. **Context Dependency**: Compliance often depends on organizational risk appetite, geographical data residency, and processing scale—nuances absent from raw cloud resource JSON payloads.

---

## 4. Limitations & Future Work

- **Mapping Coverage**: Current mapping rules in `data/control_mappings/gdpr_to_technical.json` cover primary security clauses across GDPR, DORA, and NIS2, but can be expanded to cover specialized sector-specific guidelines (e.g. EBA ICT guidelines).
- **Confidence Calibration**: Heuristic confidence scores should be continuously calibrated and benchmarked against expert legal auditor reviews.
- **Continuous Monitoring**: The current pipeline performs point-in-time snapshot assessments; future Step 4 extensions will stream event-driven cloud audit logs for real-time compliance alerting.

---

## 5. Testing Strategy

- **Mocked Data & Deterministic Baselines**: Comprehensive mock catalogs and cloud telemetry baselines isolate evaluation logic from live cloud infrastructure latency.
- **Edge Cases**: Systematically tested against unmapped regulatory controls, missing technical controls, empty baselines, contradictory compliance states, and extreme statutory friction scores.
- **Structural & Schema Validation**: Output reports validated against NIST OSCAL standards and strict Pydantic v2 schemas across JSON, Markdown, and Rich terminal output formats.

---

## 6. Execution & Verification

The Step 3 pipeline can be run via:
1. **Interactive CLI**: `python src/main_gap_analysis.py --catalog oscal_profiles/gdpr_catalog.json --baseline baselines/technical_baseline.json --output reports/gap_analysis.json --markdown reports/gap_analysis.md --verbose`
2. **Python Example Pipeline**: `python examples/run_gap_analysis.py`
3. **Automated Test Suite**: `pytest tests/test_gap_analysis.py tests/test_control_mapper.py -v` (135 tests passing)
