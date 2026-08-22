# Quick Demo Setup & Reviewer Guide

> **Academic Research Context**: Policy-as-Code & Automated Compliance Mapping Framework  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP) Evaluation Committee  
> **Evaluation Time**: ~5 minutes  
> **Zero-Credential Guarantee**: No cloud credentials, API tokens, or external databases required.

---

## 🎯 Executive Summary for Reviewers

In academic peer review and technical portfolio evaluations, evaluating a complex Policy-as-Code and cloud compliance pipeline often requires external cloud subscriptions (Azure RM, AWS IAM), live API credentials, and running daemon containers. 

To eliminate all friction for MPI-SP reviewers, this framework incorporates a **deterministic mock data generator** (`populate_demo_data.py`). It seeds a self-contained SQLite database (`compliance.db`) with realistic compliance assessments, multi-factor confidence evaluations, and empirical socio-technical friction points in less than **5 seconds**.

Reviewers can immediately evaluate the framework's core research contribution—**the Socio-Technical Friction Index and Decision Hub (Step 5)**—with zero configuration.

---

## ⚡ 5-Minute Quick Start

### Step 1: Environment Preparation
Ensure you are in the project root directory with your virtual environment activated:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

*(If you have not created a virtual environment yet, run `python -m venv venv` followed by `pip install -r requirements.txt`).*

### Step 2: Seed the Demo Database
Run the deterministic data generator:

```bash
python populate_demo_data.py
```

**Expected Console Output**:
```text
🚀 Starting demo data population...
✅ Demo data populated successfully!
📂 Database created/updated at: .../compliance.db
🔄 Refresh your Streamlit dashboard to see the data!
```

### Step 3: Launch the Compliance Dashboard
Launch the dashboard via the dedicated launcher or direct Streamlit CLI:

- **Windows (Double-Click)**: Double-click `run_dashboard.bat` in the project root.
- **Cross-Platform CLI**:
  ```bash
  python run_dashboard.py
  ```
- **Direct Streamlit CLI**:
  ```bash
  streamlit run src/dashboard/app.py
  ```

Your browser will automatically open at `http://localhost:8501`.

---

## 🧠 What the Demo Data Represents: The Research Highlight

The generated dataset does not contain generic random numbers. It reflects realistic compliance tensions modeled directly from European statutory mandates (**GDPR**, **DORA**, **NIS2**) and contemporary enterprise cloud architectures.

### 1. Overall Posture
- **Total Evaluated Controls**: 15 regulatory controls mapped to 45 technical cloud settings.
- **Compliance Score**: **68.5%** (9 Compliant, 3 Partial, 2 Non-Compliant, 1 Unknown).
- **Average Epistemic Confidence**: **74.0%** ($C = 0.74$).

### 2. Multi-Factor Confidence Distribution ($C \in [0.0, 1.0]$)
The framework rejects binary compliance scoring (where a control is naively marked $1$ or $0$). Instead, it computes confidence scores based on evidence completeness, telemetry freshness, and statutory ambiguity:
- **DORA Article 6 (ICT Risk Management)**: **0.92 Confidence (High)**  
  *Deterministic technical baseline*: Azure RBAC rules, NSG flow logs, and identity federation match the technical specification directly.
- **GDPR Article 32 (Security of Processing)**: **0.65 Confidence (Medium)**  
  *Ambiguity penalty applied*: The legal phrase *"appropriate technical and organisational measures"* cannot be resolved deterministically without human classification.
- **GDPR Article 33 (Breach Notification)**: **0.55 Confidence (Medium/Low)**  
  *Process penalty applied*: While cloud alerting triggers in real time, the subsequent 72-hour regulatory notification workflow depends on human email escalation.

---

## 🔍 Specific Socio-Technical Friction Points Modeled

When navigating to **Page 3 (🧠 Socio-Technical View)**, reviewers will inspect empirical friction points categorized by root cause:

| Regulatory Control | Regulation | Friction Type | Real-World Empirical Scenario | Suggested Remediation |
| :--- | :--- | :--- | :--- | :--- |
| **GDPR Art. 32** | GDPR | Legal Ambiguity & Capacity Bottleneck | Legal requirement for "appropriate measures" lacks binary criteria; DevOps team lacks sprint capacity to tag legacy databases with classification metadata. | Allocate sprint capacity for automated data classification; conduct manual risk assessment for untagged databases. |
| **DORA Art. 11** | DORA | Policy-Implementation Gap | Formal disaster recovery policy is declared in OSCAL, but the actual Azure Recovery Services Vault is configured for Local Redundancy (LRS) instead of Geo-Redundancy (GRS). | Immediately enable Geo-Redundant Storage (GRS) on critical recovery vaults to satisfy cross-border operational resilience. |
| **GDPR Art. 33** | GDPR | Process Bottleneck & Human Delay | SIEM security alerting triggers automatically in sub-seconds, but the statutory 72-hour incident notification workflow relies on manual email chains between security and the DPO. | Automate DPO escalation and incident logging via bidirectional ServiceNow / Jira integration. |

---

## 📋 Guided Reviewer Walkthrough

Reviewers are encouraged to follow this structured 5-page walkthrough:

1. **📊 Executive Summary (`pages/1_📊_Executive_Summary.py`)**:
   - Inspect the **Compliance Gauge** showing the aggregate score of 68.5%.
   - Examine the **Regulation Breakdown** chart contrasting high NIS2 compliance (88%) against lower DORA compliance (65%).
   - Review high-level KPIs designed specifically for non-technical board members and CISOs.

2. **🔍 Technical View (`pages/2_🔍_Technical_View.py`)**:
   - Explore the **Compliance Heatmap** showing compliance states across operational domains.
   - Inspect the **Confidence vs. Compliance Scatter Plot** to observe controls that appear compliant but suffer from low assurance confidence.

3. **🧠 Socio-Technical View (`pages/3_🧠_Socio-Technical_View.py`) — CORE RESEARCH HIGHLIGHT**:
   - Observe the **Friction Points Analysis** identifying cognitive and organizational bottlenecks.
   - Inspect the expandable friction cards containing detailed diagnostic narratives and concrete engineering recommendations.

4. **📈 Trend Analysis (`pages/4_📈_Trend_Analysis.py`)**:
   - Review longitudinal compliance tracking showing posture evolution across successive assessment intervals to demonstrate continuous compliance under DORA Article 6 and NIS2 Article 21.

5. **📋 Detailed Controls & Export (`pages/5_📋_Detailed_Controls.py`)**:
   - Search and filter specific regulatory controls.
   - Inspect raw evidence JSON blocks.
   - Test generating audit packages: click **Export to Excel** or **Generate Executive HTML Report** to test the audit export engine.

---

## 🔄 Resetting or Re-running the Data

The data generator is completely idempotent. You can re-run it at any time to reset the database to its clean demo baseline:

```bash
python populate_demo_data.py
```

If you modify controls or KPIs in `populate_demo_data.py`, simply save the file, re-run the command, and press **R** in your browser window to reload the Streamlit dashboard with updated metrics.
