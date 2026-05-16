# DORA Technical Control Mapping & Legal Alignment

> **Research Document**: Digital Operational Resilience Act (EU Regulation 2022/2554)  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Framework Module**: Step 2 — Technical Control Baseline Extraction

---

## 1. Regulatory Context & Research Motivation

The **Digital Operational Resilience Act (DORA - Regulation (EU) 2022/2554)** imposes a comprehensive, binding cybersecurity and operational resilience framework on financial entities operating within the European Union (banks, investment firms, insurance undertakings, crypto-asset service providers) and their **Critical ICT Third-Party Providers (CTPPs)**, including cloud hyperscalers (Microsoft Azure, AWS, Google Cloud).

A central friction point in DORA implementation is the operational translation of abstract legal obligations:
- **How do financial entities translate statutory ICT risk management mandates into deterministic, auditable technical controls?**
- **How do cloud configuration baselines demonstrate continuous compliance with DORA Articles 6 and 11?**

This document establishes the precise architectural mapping between the technical controls collected by our framework's `AzureCollector` and DORA's statutory mandates.

---

## 2. Comprehensive Regulatory Mapping Matrix

| DORA Article & Clause | Statutory Mandate Summary | Collected Technical Control | Resource Evaluated | Compliance Verification Logic |
| :--- | :--- | :--- | :--- | :--- |
| **Article 6(1)** | Continuous identification of ICT risk sources | `azure-vm-managed-identity-{vm}` | Azure Virtual Machine | Verifies `SystemAssigned` or `UserAssigned` managed identity to eliminate hardcoded long-lived credentials. |
| **Article 6(2)** | Robust protection of ICT systems & encryption | `azure-storage-encryption-{account}` | Azure Storage Account | Assesses infrastructure encryption-at-rest (`blob`, `file`) and Customer-Managed Key (`Microsoft.Keyvault`) enforcement. |
| **Article 6(2)** | Secure transmission of sensitive financial data | `azure-storage-https-{account}` | Azure Storage Account | Evaluates `enable_https_traffic_only == True` to mandate TLS in transit across all endpoints. |
| **Article 6(2)** | Key and secret management resilience | `azure-keyvault-protection-{vault}` | Azure Key Vault | Enforces `enable_soft_delete == True` and `enable_purge_protection == True` to prevent malicious deletion of encryption keys. |
| **Article 6(3)** | Network perimeter security & segmentation | `azure-nsg-rule-{nsg}-{rule}` | Network Security Group | Identifies wildcard inbound access rules (`source: *`, `port: *`, `action: Allow`) to detect unauthorized perimeter exposure. |
| **Article 11(1)** | Backup policies, redundancy, & business continuity | `azure-storage-backup-{account}` | Azure Storage Account | Verifies replication SKU (`Standard_GRS`, `Standard_GZRS`) providing geographic redundancy for RTO/RPO objectives. |
| **Article 11(2)** | Recovery capabilities & data availability | `azure-keyvault-protection-{vault}` | Azure Key Vault | Soft-delete retention (90 days) ensures cryptographic availability during operational disruptions. |

---

## 3. Deep Dive: DORA Article 6 — ICT Risk Management Framework

### 3.1 Statutory Text Analysis
> *"Financial entities shall use and maintain updated ICT systems, protocols and tools that are appropriate to the complexity of their operations... and ensure the continuous protection of data at rest and data in transit."* (DORA Art. 6(2))

### 3.2 Technical Implementation in AzureCollector
In [`src/collectors/azure_collector.py`](file:///c:/Users/barit/OneDrive/Desktop/automated-compliance-mapping-framework/src/collectors/azure_collector.py), the `collect_encryption_controls()` method validates data protection through dual-layer verification:
1. **At-Rest Cryptographic Isolation**:
   ```python
   # Verifies encryption across blob and file services
   encryption_status = {
       "blob_enabled": account.encryption.services.blob.enabled,
       "file_enabled": account.encryption.services.file.enabled,
       "key_source": account.encryption.key_source,
       "infrastructure_encryption": account.encryption.require_infrastructure_encryption
   }
   ```
2. **In-Transit Transmission Security**:
   Ensures that unencrypted HTTP endpoints are rejected at the ARM fabric level (`enable_https_traffic_only = True`).

### 3.3 Network Perimeter Defenses
Under DORA Article 6(3), financial entities must segment network architectures. The `collect_network_controls()` method iterates through all Network Security Groups (NSGs) and evaluates security rules against a least-privilege matrix:
- **Flagged Vulnerability**: Any inbound security rule allowing `*` or `Internet` as source prefix on management ports (22 SSH, 3389 RDP) is marked as `NON_COMPLIANT`.

---

## 4. Deep Dive: DORA Article 11 — Backup Policies & Recovery Methods

### 4.1 Statutory Text Analysis
> *"Financial entities shall develop and document backup policies and procedures... they shall maintain ICT systems that ensure redundancy and geographic separation of backup data to satisfy recovery time and recovery point objectives (RTO/RPO)."* (DORA Art. 11(1))

### 4.2 Technical Implementation in AzureCollector
In [`src/collectors/azure_collector.py`](file:///c:/Users/barit/OneDrive/Desktop/automated-compliance-mapping-framework/src/collectors/azure_collector.py), the `collect_backup_controls()` method evaluates storage redundancy configurations:

```python
# Evaluates storage redundancy SKU against DORA Article 11 geographic requirements
sku_name = account.sku.name  # e.g., 'Standard_GRS', 'Standard_LRS'
is_geo_redundant = "GRS" in sku_name or "GZRS" in sku_name

compliance_status = (
    ComplianceStatus.COMPLIANT if is_geo_redundant 
    else ComplianceStatus.NON_COMPLIANT
)
```

- **Compliant Redundancy**: Geo-Redundant Storage (`Standard_GRS`) and Geo-Zone-Redundant Storage (`Standard_GZRS`) replicate primary data to a paired secondary region located hundreds of kilometers away, satisfying DORA's geographic separation requirement.
- **Non-Compliant Redundancy**: Locally Redundant Storage (`Standard_LRS`) replicates data within a single physical data center, failing DORA's disaster resilience criteria.

---

## 5. Socio-Technical Friction in DORA Compliance

During the implementation of these mappings, several socio-technical friction points emerged:

1. **The "Proportionate" Ambiguity**: DORA requires measures to be *"proportionate to size, nature, scale and complexity"*. In code, determining whether a micro-entity requires expensive Geo-Zone Redundancy (`Standard_GZRS`) vs. standard `Standard_GRS` requires Human-in-the-Loop (HITL) architectural context.
2. **Key Custodianship Tensions**: DORA encourages Customer-Managed Keys (CMK) via Key Vault. However, misconfigured purge protection or expired key rotations can cause complete service outages, illustrating the trade-off between strict security compliance and operational availability.
3. **Multi-Tenant Hyperscaler Visibility**: Cloud providers operate under a shared responsibility model. While financial entities can audit their own resource configurations (ARM), they cannot directly audit the hyperscaler's physical data center failover mechanisms, necessitating OSCAL-based automated evidence exchange.
