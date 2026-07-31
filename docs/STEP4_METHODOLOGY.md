# Step 4: Orchestration & Automation — Methodology

> **Academic Research Context**: Policy-as-Code & Automated Compliance Mapping Framework  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Lifecycle Phase**: Step 4 — Workflow Orchestration, Continuous Monitoring & KPI Persistence  

---

## 1. Research Context

This module addresses a foundational operational challenge in automated governance and Policy-as-Code: **How do we transition from discrete, static "point-in-time" assessments to robust, automated continuous monitoring?**

In enterprise environments, cloud infrastructure is dynamic: new storage buckets are provisioned, firewall rules are altered, and encryption policies drift. Simultaneously, regulatory landscapes are evolving under strict European Union directives:
- **DORA Article 11** mandates continuous ICT business continuity management and ongoing validation of recovery objectives (RTO/RPO).
- **DORA Article 6** requires financial entities to maintain an up-to-date ICT risk management framework with regular testing and continuous automated control evaluation.
- **NIS2 Article 21** requires essential and important entities to perform ongoing risk analysis, incident handling, and systematic monitoring of technical network and information system security.

Annual or quarterly manual audits create dangerous "blind spots" where infrastructure drift goes undetected for months. Step 4 transforms the framework from an on-demand analysis tool into an **automated, scheduled compliance monitoring pipeline**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APACHE AIRFLOW ORCHESTRATION DAG                      │
│                                                                             │
│  ┌─────────────────┐      XCom       ┌───────────────────┐                  │
│  │     Task 1      │────────────────►│      Task 2       │                  │
│  │  pull_configs   │ (Baseline Meta) │ run_gap_analysis  │                  │
│  └─────────────────┘                 └─────────┬─────────┘                  │
│           ▲                                    │ XCom (Report Meta)         │
│           │ [Weekly Cron: 0 2 * * 1]           ▼                            │
│           │                          ┌───────────────────┐                  │
│           │                          │      Task 3       │                  │
│           │                          │  calculate_kpis   │                  │
│           │                          └─────────┬─────────┘                  │
│           │                                    │ XCom (KPIs Dict)           │
│           │                                    ▼                            │
│           │                          ┌───────────────────┐                  │
│           │                          │      Task 4       │                  │
│           │                          │   store_results   │                  │
│           │                          └─────────┬─────────┘                  │
│           │                                    │                            │
│           │                                    ▼                            │
│           │                       ┌─────────────────────────┐               │
│           └───────────────────────│  Relational DB & Audit  │               │
│                                   │ (Historical Time-Series)│               │
│                                   └─────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Decisions

### 2.1 Apache Airflow for Workflow Orchestration
**Decision**: Standardize on Apache Airflow as the DAG-based workflow orchestration engine.

**Rationale**:
- **Industry Standard**: Airflow is the predominant orchestrator across enterprise data platforms and DevSecOps ecosystems.
- **Python-Native Architecture**: DAGs and tasks are defined as standard Python code, enabling direct integration with the framework's existing Step 1–3 models and engines without external protocol bridges.
- **Deterministic Task Scheduling & Retries**: Provides cron-based execution (`0 2 * * 1`), exponential backoff retries (2 attempts with 5-minute delays), and failure notification hooks.
- **Decoupled Task Modularity**: Each pipeline phase is isolated into an independent task operator, preventing memory leaks and enabling modular maintenance.

**Trade-offs & Mitigation**:
- *Trade-off*: Airflow introduces operational overhead (scheduler daemon, relational metadata store, webserver UI).
- *Mitigation*: The task design implements a **dual-mode execution pattern**: every task function is a decoupled, pure Python callable that can execute independently in lightweight CI/CD scripts without requiring a running Airflow scheduler, while fully supporting Airflow's runtime and XCom when deployed in orchestration environments.

### 2.2 Storage Layer: SQLite for Development, PostgreSQL for Production
**Decision**: Adopt SQLAlchemy 2.0 ORM with a Dual-Database strategy.

**Rationale**:
- **Zero-Friction Evaluation (SQLite)**: SQLite provides an embedded, file-based database requiring zero setup, making the framework immediately executable and verifiable for academic review at MPI-SP.
- **Enterprise Scalability (PostgreSQL)**: PostgreSQL provides native JSONB queries, connection pooling, and multi-tenant isolation required for production-scale compliance telemetry.
- **Repository Pattern Abstraction**: The `ComplianceRepository` decouples high-level pipeline tasks from SQL dialect specifics, allowing the backend to switch via a single database connection URI (`database_url`).

### 2.3 Task Communication via XCom & Explicit Artifact Paths
**Decision**: Pass lightweight metadata dictionaries via Airflow XCom while saving comprehensive data payloads (raw baselines, OSCAL reports) as versioned artifacts on disk.

**Rationale**:
- **Prevents XCom Bloat**: Passing massive infrastructure baselines or whole JSON reports directly through XCom strains database backends. Passing lightweight metadata (paths, run IDs, control totals) keeps XCom fast and reliable.
- **Preserves Full Audit Records**: Raw baseline JSONs and generated Markdown/JSON gap reports remain preserved in `baselines/` and `reports/` for legal accountability and reproducibility.

---

## 3. Data Model Architecture

The persistence layer (`src/pipeline/database/models.py`) establishes a relational schema designed for trend analysis:

```
┌────────────────────────────────┐         1 : N
│     ComplianceAssessment       │──────────────────────┐
├────────────────────────────────┤                      │
│ id: String(36) [PK]            │                      ▼
│ assessment_date: DateTime      │        ┌───────────────────────────────┐
│ baseline_id: String(100)       │        │    ControlAssessmentResult    │
│ catalog_id: String(100)        │        ├───────────────────────────────┤
│ cloud_provider: String(50)     │        │ id: String(36) [PK]           │
│ compliant_count: Integer       │        │ assessment_id: String(36) [FK]│
│ partial_count: Integer         │        │ regulatory_control_id: String │
│ non_compliant_count: Integer   │        │ regulation: String(50)        │
│ overall_compliance_score: Float│        │ gap_type: String(50)          │
│ average_confidence_score: Float│        │ compliance_status: String(50) │
│ assessment_metadata: Text      │        │ confidence_score: Float       │
└────────────────────────────────┘        │ evidence: Text (JSON)         │
               │                          │ friction_points: Text (JSON)  │
         1 : N │                          └───────────────────────────────┘
               ▼
┌────────────────────────────────┐
│         ComplianceKPI          │
├────────────────────────────────┤
│ id: String(36) [PK]            │
│ assessment_id: String(36)      │
│ kpi_name: String(100)          │
│ kpi_value: Float               │
│ kpi_unit: String(50)           │
│ kpi_category: String(50)       │
│ calculated_at: DateTime        │
└────────────────────────────────┘
```

### Key Relational Entities
1. **`ComplianceAssessment`**: Top-level record of a single pipeline run, storing macro metrics (overall score, confidence averages, resource counts).
2. **`ControlAssessmentResult`**: Granular per-control audit record storing compliance status, confidence levels, technical evidence, and socio-technical friction notes.
3. **`ComplianceKPI`**: Normalized time-series metric entry enabling historical trend queries across arbitrary monitoring intervals.

---

## 4. Multi-Factor KPI Engine Methodology

The KPI Calculation Engine (`src/pipeline/kpis/compliance_kpis.py`) converts complex gap analysis reports into transparent executive metrics:

### 4.1 Weighted Compliance Rate Calculation
Rather than treating compliance as a binary pass/fail, partial compliance is assigned a fractional weight ($0.5$):

$$\text{Compliance Rate} = \frac{N_{\text{compliant}} \times 1.0 + N_{\text{partial}} \times 0.5}{N_{\text{total\_analyzed}}} \times 100$$

### 4.2 Framework-Specific Breakdown
The engine segregates metrics by statutory source:
- `gdpr_compliance_rate`: Focused on personal data protection and Article 32 encryption.
- `dora_compliance_rate`: Focused on ICT business continuity, backup frequency, and risk management.
- `nis2_compliance_rate`: Focused on essential entity cybersecurity hygiene and network security.

### 4.3 Epistemic Confidence & Friction Tracking
- **High-Confidence Coverage**: Percentage of control evaluations achieving confidence scores $\ge 0.80$.
- **Socio-Technical Friction Rate**: Percentage of regulatory obligations impeded by organizational or legal ambiguity (e.g., developer/legal misalignment or unquantified legal terms).

---

## 5. Pipeline Tasks Breakdown

| Task | Module | Input | Output | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Task 1: Pull Configs** | `tasks/pull_configs.py` | Cloud Provider, Subscription ID | Baseline JSON file + metadata dict | Extracts current security state via Azure Collector (or offline mock). |
| **Task 2: Gap Analysis** | `tasks/run_gap_analysis.py` | Baseline path, OSCAL catalog | JSON report, Markdown report + metadata | Executes Gap Evaluator to map controls and calculate confidence. |
| **Task 3: Calculate KPIs** | `tasks/calculate_kpis.py` | JSON report path | KPI dictionary + summary string | Computes overall, regulation, confidence, and friction KPIs. |
| **Task 4: Store Results** | `tasks/store_results.py` | Upstream task outputs, DB URL | Stored Assessment ID, KPI count | Commits assessment, control results, and KPIs to relational database. |

---

## 6. Socio-Technical Friction Findings

During the implementation of automated compliance orchestration, several socio-technical friction points emerged:

1. **Scheduling vs. API Quota Friction**:
   - Continuous real-time polling of cloud APIs risks throttling and high cost. A weekly schedule (`0 2 * * 1`) balances freshness with provider quotas, but creates a temporal lag between infrastructure drift and compliance detection.
2. **Deterministic Retries vs. Actionable Alerting**:
   - Transient cloud network errors justify automated retries with exponential backoff. However, persistent compliance failures (e.g., deleted backups) require urgent organizational escalation rather than endless background retries.
3. **KPI Granularity vs. Executive Cognitive Overload**:
   - Technical engineers require granular control statuses (e.g., specific Key Vault soft-delete flags), whereas executive governance boards require normalized percentage trends. The multi-tiered data model resolves this by maintaining both granular and summary records.

---

## 7. Regulatory Compliance Mapping

| Regulation & Article | Statutory Obligation | How Step 4 Satisfies It |
| :--- | :--- | :--- |
| **DORA Article 11** | ICT business continuity policy and continuous validation of backup and recovery controls. | Task 1 automatically pulls backup controls weekly, while Task 2 assesses compliance against RTO/RPO requirements. |
| **DORA Article 6** | ICT risk management framework requiring ongoing testing and evaluation of digital operational resilience. | Automates the periodic re-evaluation of technical baselines, eliminating manual point-in-time assessment gaps. |
| **NIS2 Article 21** | Cybersecurity risk-management measures including ongoing monitoring of network and information systems. | Scheduled execution detects security misconfigurations and maintains historical audit trails in the database. |

---

## 8. Limitations & Future Work

- **Notification Webhooks**: Current implementation logs and persists results; integration with Slack/Teams alerts on compliance degradation is planned for Step 5.
- **Visual Analytics Dashboard**: KPIs are persisted in SQLite/PostgreSQL; Step 5 will introduce web-based visual dashboards and interactive trend charts.
- **Multi-Cloud Collectors**: Task 1 currently targets Azure; AWS and GCP collectors will be integrated into the DAG via branching operators.
- **Event-Driven Triggering**: Transitioning from scheduled batch cron execution to real-time event-driven triggers via cloud audit logs (e.g., Azure Event Grid / AWS EventBridge).
