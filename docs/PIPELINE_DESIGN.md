# Continuous Compliance Monitoring Pipeline — Architecture & Design

> **Academic Research Context**: Policy-as-Code & Automated Compliance Mapping Framework  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Lifecycle Phase**: Step 4 — Orchestration & Automation (The Pipeline)  

---

## 1. Executive Summary & Design Vision

Traditional cybersecurity governance is hindered by **temporal fragility**: compliance audits are conducted once a year or once a quarter, leaving vast temporal intervals where cloud configuration drift and silent compliance degradation occur undetected.

Under **DORA Article 11** (ICT business continuity) and **NIS2 Article 21** (continuous security monitoring), financial entities and critical infrastructure operators must maintain active, continuous supervision over their operational resilience.

Step 4 bridges this gap by engineering a production-grade, scheduled **Apache Airflow Orchestration Pipeline** supported by a relational persistence layer, a multi-factor Key Performance Indicator (KPI) calculator, and transactional audit tracking.

---

## 2. End-to-End Pipeline Architecture

The pipeline executes on a scheduled weekly cadence (`0 2 * * 1` — every Monday at 02:00 UTC) with automatic exponential backoff retries:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        COMPLIANCE MONITORING AIRFLOW DAG                               │
│                                                                                        │
│   ┌─────────────────────┐                   XCom                   ┌─────────────────┐ │
│   │       Task 1        │─────────────────────────────────────────►│     Task 2      │ │
│   │ pull_infrastructure │  Baseline Metadata:                      │ run_gap_analysis│ │
│   │       _configs      │  - baseline_id, filepath, total_controls │                 │ │
│   └─────────────────────┘                                          └────────┬────────┘ │
│              ▲                                                              │          │
│              │ [Cron: Weekly 02:00 UTC]                                     │ XCom     │
│              │ [Retries: 2x, 5m delay]                                      │ Report   │
│              │                                                              ▼ Metadata │
│              │                                                     ┌─────────────────┐ │
│              │                                                     │     Task 3      │ │
│              │                                                     │ calculate_kpis  │ │
│              │                                                     └────────┬────────┘ │
│              │                                                              │          │
│              │                                                              │ XCom     │
│              │                                                              ▼ KPIs Dict│
│              │                                                     ┌─────────────────┐ │
│              │                                                     │     Task 4      │ │
│              │                                                     │  store_results  │ │
│              │                                                     └────────┬────────┘ │
│              │                                                              │          │
│              │                                                              ▼          │
│              │                           ┌───────────────────────────────────────────┐ │
│              └───────────────────────────│   Relational Store (SQLite/PostgreSQL)    │ │
│                                          │  - compliance_assessments                 │ │
│                                          │  - control_assessment_results             │ │
│                                          │  - compliance_kpis                        │ │
│                                          └───────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Relational Schema & Persistence Layer

The database models are constructed using **SQLAlchemy 2.0 ORM** (`src/pipeline/database/models.py`), ensuring complete portability between lightweight local SQLite storage (for zero-friction evaluation and academic review) and enterprise PostgreSQL clusters.

### Schema Blueprint

```text
┌───────────────────────────────────┐         1 : N
│       ComplianceAssessment        │─────────────────────────┐
├───────────────────────────────────┤                         │
│ id: String(36) [PK]               │                         ▼
│ assessment_date: DateTime         │        ┌───────────────────────────────────┐
│ baseline_id: String(100)          │        │      ControlAssessmentResult      │
│ catalog_id: String(100)           │        ├───────────────────────────────────┤
│ cloud_provider: String(50)        │        │ id: String(36) [PK]               │
│ subscription_id: String(100)      │        │ assessment_id: String(36) [FK]    │
│ total_regulatory_controls: Integer│        │ regulatory_control_id: String     │
│ total_technical_controls: Integer │        │ regulation: String(50)            │
│ compliant_count: Integer          │        │ control_title: String(500)        │
│ partial_count: Integer            │        │ gap_type: String(50)              │
│ non_compliant_count: Integer      │        │ compliance_status: String(50)     │
│ unknown_count: Integer            │        │ confidence_score: Float           │
│ overall_compliance_score: Float   │        │ confidence_level: String(20)      │
│ average_confidence_score: Float   │        │ evidence: Text (JSON serialized)  │
│ assessment_metadata: Text (JSON)  │        │ friction_points: Text (JSON)      │
│ created_at: DateTime              │        │ recommendations: Text (JSON)      │
└───────────────────────────────────┘        │ created_at: DateTime              │
                  │                          └───────────────────────────────────┘
            1 : N │
                  ▼
┌───────────────────────────────────┐
│           ComplianceKPI           │
├───────────────────────────────────┤
│ id: String(36) [PK]               │
│ assessment_id: String(36)         │
│ kpi_name: String(100)             │
│ kpi_value: Float                  │
│ kpi_unit: String(50)              │
│ kpi_category: String(50)          │
│ calculated_at: DateTime           │
└───────────────────────────────────┘
```

---

## 4. Multi-Category KPI Engine Methodology

The KPI calculation engine (`src/pipeline/kpis/compliance_kpis.py`) aggregates micro-level control evaluation results into structured, macro-level governance indicators:

### 4.1 Weighted Compliance Scoring
Binary compliance models penalize partially implemented controls unfairly, while relaxed models risk false assurance. The framework utilizes a continuous, transparent weighting formula:

$$\text{Compliance Rate} = \frac{N_{\text{compliant}} \times 1.0 + N_{\text{partial}} \times 0.5}{N_{\text{total\_controls}}} \times 100$$

### 4.2 Multi-Regulation Segmentation
Compliance is calculated independently for each statutory framework:
- **`gdpr_compliance_rate`**: Personal data protection, encryption at rest/in transit, key rotation.
- **`dora_compliance_rate`**: ICT business continuity, backup retention, automated recovery telemetry.
- **`nis2_compliance_rate`**: Network security, vulnerability scanning, and incident monitoring.

### 4.3 Epistemic Confidence & Socio-Technical Friction Metrics
- **`high_confidence_percentage`**: Percentage of control evaluations supported by concrete evidence achieving confidence scores $\ge 0.80$.
- **`high_friction_controls_count` & `friction_rate`**: Quantifies the percentage of statutory rules impeded by legal-technical misalignment or organizational ambiguity.

---

## 5. Airflow Task Lifecycle & XCom Data Contract

| Task ID | Operator | Source Module | Inputs / XCom Pulled | Outputs / XCom Pushed |
| :--- | :--- | :--- | :--- | :--- |
| `pull_configs` | `PythonOperator` | `tasks/pull_configs.py` | `cloud_provider`, `subscription_id` | `baseline_id`, `baseline_path`, `total_controls`, `collection_timestamp` |
| `run_gap_analysis` | `PythonOperator` | `tasks/run_gap_analysis.py` | `baseline_path` (from Task 1), `catalog_path` | `report_id`, `json_report_path`, `md_report_path`, `summary` |
| `calculate_kpis` | `PythonOperator` | `tasks/calculate_kpis.py` | `json_report_path` (from Task 2) | `report_id`, `kpis` dictionary |
| `store_results` | `PythonOperator` | `tasks/store_results.py` | Metadata from Tasks 1, 2, and 3 | `assessment_id`, `stored_kpis_count`, `database_url` |

### Dual-Mode Execution Pattern
Each task function takes `**context` and supports Airflow's TaskInstance (`ti.xcom_pull()`). If executed outside Airflow (e.g. in standalone testing or CI scripts), the functions gracefully fall back to keyword arguments (`context.get('baseline_metadata')`), enabling full testability with zero external daemon dependencies.
