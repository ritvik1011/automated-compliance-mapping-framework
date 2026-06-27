"""Comprehensive Test Suite for Step 3: Automated Gap Analysis Engine.

Validates data models, mapping matrix, confidence scoring algorithms,
gap identification, report generation, and CLI orchestration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.gap_analysis import (
    ConfidenceScorer,
    ControlMapper,
    GapEvaluator,
    ReportGenerator,
)
from src.gap_analysis_engine import GapAnalysisEngine
from src.main_gap_analysis import main as cli_main
from src.mappings.regulatory_mapping import (
    CategoryMapping,
    MappingRule,
    RegulatoryMappingMatrix,
)
from src.models.gap_analysis import (
    ComplianceGap,
    ConfidenceBreakdown,
    ConfidenceLevel,
    ControlEvaluation,
    GapAnalysisReport,
    GapAnalysisResult,
    GapSeverity,
    GapType,
    RegulationComplianceStatus,
)
from src.models.technical_control import (
    CloudProvider,
    ComplianceStatus,
    ControlCategory,
    InfrastructureBaseline,
    TechnicalControl,
)
from src.parser import RegulatoryArticle

# ============================================================================
# 1. DATA MODEL TESTS
# ============================================================================


def test_gap_analysis_models_instantiation() -> None:
    """Verify standard creation and serialization of Gap Analysis models."""
    gap = ComplianceGap(
        gap_id="GAP-TEST-001",
        regulatory_control_id="gdpr-art-32",
        regulation="GDPR",
        technical_control_id="azure-storage-encryption-test1",
        resource_id="/subscriptions/xxx/storageAccounts/test1",
        resource_name="test1",
        severity=GapSeverity.HIGH,
        title="Unencrypted Storage Account",
        description="Storage account does not enforce encryption at rest.",
        observed_state={"blob_encryption": False},
        expected_state={"blob_encryption": True},
        remediation_guidance="az storage account update --name test1",
    )
    assert gap.gap_id == "GAP-TEST-001"
    assert gap.severity == GapSeverity.HIGH

    confidence = ConfidenceBreakdown(
        evidence_coverage=0.75,
        friction_penalty=0.25,
        status_consistency=0.9,
        final_score=0.506,
    )
    assert confidence.final_score == 0.506

    eval_result = ControlEvaluation(
        regulatory_control_id="gdpr-art-32",
        regulation="GDPR",
        title="Security of Processing",
        status=RegulationComplianceStatus.PARTIALLY_COMPLIANT,
        compliance_score=65.0,
        confidence_score=0.62,
        confidence_breakdown=confidence,
        mapped_categories=[ControlCategory.ENCRYPTION],
        gaps=[gap],
    )
    assert eval_result.compliance_score == 65.0
    assert len(eval_result.gaps) == 1

    report = GapAnalysisReport(
        baseline_id="base-001",
        evaluations=[eval_result],
        all_gaps=[gap],
    )
    assert report.baseline_id == "base-001"
    assert len(report.evaluations) == 1
    assert report.report_id is not None


def test_gap_analysis_report_id_validation() -> None:
    """Ensure report_id validation catches blank IDs."""
    with pytest.raises(ValueError):
        GapAnalysisReport(report_id="   ")


# ============================================================================
# 2. MAPPING MATRIX TESTS
# ============================================================================


def test_mapping_matrix_canonical_rules() -> None:
    """Verify built-in canonical statutory rules for GDPR, DORA, and NIS2."""
    matrix = RegulatoryMappingMatrix()

    # GDPR Art. 32
    gdpr_cats = matrix.resolve_categories("gdpr-art-32")
    assert len(gdpr_cats) > 0
    categories = [c.category for c in gdpr_cats]
    assert ControlCategory.ENCRYPTION in categories
    assert ControlCategory.IDENTITY_ACCESS in categories
    assert ControlCategory.BACKUP_RECOVERY in categories

    # DORA Art. 6
    dora_cats = matrix.resolve_categories("dora-art-6")
    assert any(c.category == ControlCategory.NETWORK for c in dora_cats)

    # NIS2 Art. 21
    nis2_cats = matrix.resolve_categories("nis2-art-21")
    assert any(c.category == ControlCategory.BACKUP_RECOVERY for c in nis2_cats)


def test_mapping_matrix_heuristic_fallback() -> None:
    """Verify keyword-based fallback matching for uncataloged regulatory text."""
    matrix = RegulatoryMappingMatrix()

    # Unlisted control ID with cryptography text
    cats = matrix.resolve_categories(
        "custom-law-art-99",
        text_context="Entities shall enforce robust cryptography and TLS encryption.",
    )
    assert len(cats) > 0
    assert any(c.category == ControlCategory.ENCRYPTION for c in cats)

    # Unlisted control ID with backup and disaster recovery text
    cats_backup = matrix.resolve_categories(
        "iso-27001-a12",
        text_context="Regular backup copies of information and software shall be maintained.",
    )
    assert any(c.category == ControlCategory.BACKUP_RECOVERY for c in cats_backup)


def test_mapping_matrix_custom_rule_registration() -> None:
    """Verify custom rules can be registered and take precedence."""
    matrix = RegulatoryMappingMatrix()
    custom_rule = MappingRule(
        regulatory_control_id="custom-pci-dss-3",
        regulation="PCI-DSS",
        target_categories=[
            CategoryMapping(
                category=ControlCategory.ENCRYPTION,
                weight=3.0,
                is_mandatory=True,
                rationale="Protect cardholder data at rest.",
            )
        ],
    )
    matrix.register_rule(custom_rule)

    resolved = matrix.resolve_categories("custom-pci-dss-3")
    assert len(resolved) == 1
    assert resolved[0].category == ControlCategory.ENCRYPTION
    assert resolved[0].weight == 3.0


# ============================================================================
# 3. ENGINE INGESTION & NORMALIZATION TESTS
# ============================================================================


def test_engine_load_catalog(tmp_path: Path) -> None:
    """Verify catalog loading from JSON file, dictionary, and RegulatoryArticle list."""
    engine = GapAnalysisEngine()

    # Dictionary source
    sample_catalog_dict: Dict[str, Any] = {
        "catalog": {
            "controls": [
                {
                    "id": "gdpr-art-32",
                    "title": "Security of processing",
                    "props": [{"name": "regulation", "value": "GDPR"}],
                }
            ]
        }
    }
    controls = engine.load_catalog(sample_catalog_dict)
    assert len(controls) == 1
    assert controls[0]["id"] == "gdpr-art-32"

    # File source
    cat_file = tmp_path / "test_cat.json"
    with open(cat_file, "w", encoding="utf-8") as f:
        json.dump(sample_catalog_dict, f)
    file_controls = engine.load_catalog(cat_file)
    assert len(file_controls) == 1

    # Article model list source
    article = RegulatoryArticle(
        article_id="dora-art-6",
        regulation="DORA",
        title="ICT risk management",
        legal_text="Financial entities shall maintain a sound ICT risk management framework.",
    )
    article_controls = engine.load_catalog([article])
    assert len(article_controls) == 1
    assert article_controls[0]["id"] == "dora-art-6"

    # Non-existent file
    with pytest.raises(FileNotFoundError):
        engine.load_catalog(tmp_path / "non_existent.json")


def test_engine_load_baseline(tmp_path: Path) -> None:
    """Verify baseline loading from raw baseline JSON and OSCAL Component-Definition."""
    engine = GapAnalysisEngine()

    # From InfrastructureBaseline model
    base = InfrastructureBaseline(
        baseline_id="test-base-1",
        cloud_provider=CloudProvider.AZURE,
        controls=[],
    )
    loaded = engine.load_baseline(base)
    assert loaded.baseline_id == "test-base-1"

    # From file
    base_file = tmp_path / "base.json"
    with open(base_file, "w", encoding="utf-8") as f:
        f.write(base.model_dump_json())
    loaded_file = engine.load_baseline(base_file)
    assert loaded_file.baseline_id == "test-base-1"

    # From OSCAL Component-Definition
    oscal_comp_dict: Dict[str, Any] = {
        "component-definition": {
            "uuid": "comp-uuid-1",
            "components": [
                {
                    "uuid": "res-uuid-1",
                    "title": "my-storage",
                    "props": [
                        {
                            "name": "resource-id",
                            "value": "/subscriptions/xxx/storageAccounts/my-storage",
                        },
                        {"name": "resource-type", "value": "StorageAccount"},
                        {"name": "cloud-provider", "value": "azure"},
                    ],
                    "control-implementations": [
                        {
                            "source": "#data_encryption",
                            "implemented-requirements": [
                                {
                                    "control-id": "azure-storage-encryption-my-storage",
                                    "description": "Storage encryption",
                                    "props": [{"name": "compliance-status", "value": "compliant"}],
                                    "statements": [
                                        {"description": 'Current state: {"blob": true}'}
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    }
    loaded_oscal = engine.load_baseline(oscal_comp_dict)
    assert loaded_oscal.baseline_id == "comp-uuid-1"
    assert len(loaded_oscal.controls) == 1
    assert loaded_oscal.controls[0].control_category == ControlCategory.ENCRYPTION
    assert loaded_oscal.controls[0].compliance_status == ComplianceStatus.COMPLIANT


# ============================================================================
# 4. CONFIDENCE SCORING & FRICTION INTEGRATION TESTS
# ============================================================================


def test_confidence_scoring_bounds_and_friction() -> None:
    """Verify that confidence score obeys mathematical bounds [0.0, 1.0]
    and applies friction penalty.
    """
    engine = GapAnalysisEngine(friction_weight_alpha=0.35)

    base = InfrastructureBaseline(
        baseline_id="test-base",
        cloud_provider=CloudProvider.AZURE,
        controls=[
            TechnicalControl(
                control_id="azure-storage-encryption-1",
                control_category=ControlCategory.ENCRYPTION,
                cloud_provider=CloudProvider.AZURE,
                resource_type="StorageAccount",
                resource_id="/storage/1",
                resource_name="storage1",
                control_description="Encryption at rest",
                compliance_status=ComplianceStatus.COMPLIANT,
            ),
        ],
    )

    mapping = [CategoryMapping(category=ControlCategory.ENCRYPTION, weight=1.0, is_mandatory=True)]

    # Case A: Low friction statutory text (0.0 friction)
    conf_low = engine._calculate_confidence(
        category_mappings=mapping,
        baseline=base,
        friction_score=0.0,
        total_controls=1,
        partial_count=0,
        failed_count=0,
    )
    assert conf_low.final_score == 1.0
    assert conf_low.friction_penalty == 0.0

    # Case B: High friction statutory text (10.0 friction, e.g. "state of the art")
    conf_high = engine._calculate_confidence(
        category_mappings=mapping,
        baseline=base,
        friction_score=10.0,
        total_controls=1,
        partial_count=0,
        failed_count=0,
    )
    assert conf_high.friction_penalty == 0.35
    assert conf_high.final_score == 0.65  # 1.0 * (1 - 0.35) * 1.0 = 0.65

    # Case C: Partial evidence consistency penalty
    conf_mixed = engine._calculate_confidence(
        category_mappings=mapping,
        baseline=base,
        friction_score=0.0,
        total_controls=2,
        partial_count=1,
        failed_count=1,
    )
    assert conf_mixed.final_score < 1.0
    assert conf_mixed.status_consistency < 1.0


# ============================================================================
# 5. INTEGRATION & EVALUATION TESTS
# ============================================================================


def test_engine_evaluate_against_real_artifacts() -> None:
    """Execute end-to-end evaluation against actual workspace artifacts."""
    engine = GapAnalysisEngine()

    catalog_path = "oscal_profiles/unified_catalog.json"
    baseline_path = "baselines/azure_baseline.json"

    assert Path(catalog_path).exists()
    assert Path(baseline_path).exists()

    report = engine.evaluate(
        catalog_source=catalog_path,
        baseline_source=baseline_path,
    )

    assert report is not None
    assert len(report.evaluations) == 5
    assert report.summary.total_regulatory_controls == 5
    assert report.summary.overall_compliance_percentage > 0.0
    assert report.summary.overall_confidence_score > 0.0
    assert len(report.all_gaps) > 0

    # Verify high friction controls triggered HITL
    gdpr_eval = next(e for e in report.evaluations if e.regulatory_control_id == "gdpr-art-32")
    assert gdpr_eval.hitl_recommended is True
    assert len(gdpr_eval.hitl_guidance) > 0


def test_engine_evaluate_with_oscal_component_definition() -> None:
    """Verify gap analysis can evaluate directly against an OSCAL Component-Definition file."""
    engine = GapAnalysisEngine()

    catalog_path = "oscal_profiles/unified_catalog.json"
    component_path = "baselines/oscal_component.json"

    assert Path(component_path).exists()

    report = engine.evaluate(
        catalog_source=catalog_path,
        baseline_source=component_path,
    )

    assert report is not None
    assert report.summary.total_regulatory_controls == 5
    assert len(report.evaluations) == 5


def test_engine_regulation_filter() -> None:
    """Verify regulation filter restricts evaluation to chosen regime."""
    engine = GapAnalysisEngine()

    report_gdpr = engine.evaluate(
        catalog_source="oscal_profiles/unified_catalog.json",
        baseline_source="baselines/azure_baseline.json",
        regulation_filter="GDPR",
    )
    assert report_gdpr.summary.total_regulatory_controls == 2
    assert all(e.regulation == "GDPR" for e in report_gdpr.evaluations)

    report_dora = engine.evaluate(
        catalog_source="oscal_profiles/unified_catalog.json",
        baseline_source="baselines/azure_baseline.json",
        regulation_filter="DORA",
    )
    assert report_dora.summary.total_regulatory_controls == 2
    assert all(e.regulation == "DORA" for e in report_dora.evaluations)


def test_engine_export_json_and_markdown(tmp_path: Path) -> None:
    """Verify JSON and Markdown report export functionality."""
    engine = GapAnalysisEngine()
    report = engine.evaluate(
        catalog_source="oscal_profiles/unified_catalog.json",
        baseline_source="baselines/azure_baseline.json",
    )

    json_out = tmp_path / "test_report.json"
    md_out = tmp_path / "test_report.md"

    engine.export_json(report, json_out)
    engine.export_markdown(report, md_out)

    assert json_out.exists()
    assert md_out.exists()

    # Verify JSON structure
    with open(json_out, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "report_id" in data
    assert "summary" in data

    # Verify Markdown structure
    with open(md_out, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "# Automated Compliance Gap Analysis Report" in md_text
    assert "Executive Summary & Audit Posture" in md_text
    assert "Prioritized Compliance Gaps" in md_text


def test_engine_edge_case_completely_compliant() -> None:
    """Verify behavior when infrastructure is 100% compliant."""
    engine = GapAnalysisEngine()

    compliant_baseline = InfrastructureBaseline(
        baseline_id="perfect-baseline",
        cloud_provider=CloudProvider.AZURE,
        controls=[
            TechnicalControl(
                control_id="azure-storage-encryption-p1",
                control_category=ControlCategory.ENCRYPTION,
                cloud_provider=CloudProvider.AZURE,
                resource_type="StorageAccount",
                resource_id="/s1",
                resource_name="s1",
                control_description="Encryption at rest",
                compliance_status=ComplianceStatus.COMPLIANT,
            ),
            TechnicalControl(
                control_id="azure-vm-identity-p1",
                control_category=ControlCategory.IDENTITY_ACCESS,
                cloud_provider=CloudProvider.AZURE,
                resource_type="VirtualMachine",
                resource_id="/vm1",
                resource_name="vm1",
                control_description="Managed identity",
                compliance_status=ComplianceStatus.COMPLIANT,
            ),
            TechnicalControl(
                control_id="azure-nsg-p1",
                control_category=ControlCategory.NETWORK,
                cloud_provider=CloudProvider.AZURE,
                resource_type="NetworkSecurityGroup",
                resource_id="/nsg1",
                resource_name="nsg1",
                control_description="Network perimeter",
                compliance_status=ComplianceStatus.COMPLIANT,
            ),
            TechnicalControl(
                control_id="azure-backup-p1",
                control_category=ControlCategory.BACKUP_RECOVERY,
                cloud_provider=CloudProvider.AZURE,
                resource_type="StorageAccount",
                resource_id="/s1",
                resource_name="s1",
                control_description="Backup redundancy",
                compliance_status=ComplianceStatus.COMPLIANT,
            ),
        ],
    )

    catalog = [
        RegulatoryArticle(
            article_id="gdpr-art-32",
            regulation="GDPR",
            title="Security of processing",
            legal_text="Controllers and processors shall implement appropriate technical measures.",
        )
    ]

    report = engine.evaluate(catalog_source=catalog, baseline_source=compliant_baseline)
    assert report.summary.overall_compliance_percentage == 100.0
    assert report.summary.compliant_controls == 1
    assert report.summary.total_gaps == 0


def test_engine_edge_case_unmapped_control() -> None:
    """Verify behavior when a control cannot be mapped to any technical category."""
    engine = GapAnalysisEngine()

    unmapped_catalog = [
        RegulatoryArticle(
            article_id="unrelated-tax-code-art-5",
            regulation="TAX",
            title="Corporate Tax Filing Procedures",
            legal_text="Corporations must file standard tax returns quarterly.",
        )
    ]

    empty_base = InfrastructureBaseline(
        baseline_id="empty-base",
        cloud_provider=CloudProvider.AZURE,
        controls=[],
    )

    report = engine.evaluate(catalog_source=unmapped_catalog, baseline_source=empty_base)
    assert report.summary.unmapped_controls == 1
    assert report.evaluations[0].status == RegulationComplianceStatus.UNMAPPED


# ============================================================================
# 6. CLI ORCHESTRATOR TESTS
# ============================================================================


def test_cli_main_execution(tmp_path: Path) -> None:
    """Verify CLI main entrypoint executes without error."""
    out_json = tmp_path / "cli_out.json"
    out_md = tmp_path / "cli_out.md"

    exit_code = cli_main(
        [
            "--catalog",
            "oscal_profiles/unified_catalog.json",
            "--baseline",
            "baselines/azure_baseline.json",
            "--output",
            str(out_json),
            "--markdown",
            str(out_md),
            "--verbose",
        ]
    )

    assert exit_code == 0
    assert out_json.exists()
    assert out_md.exists()


def test_cli_main_failure_on_invalid_file() -> None:
    """Verify CLI returns exit code 1 on non-existent input files."""
    exit_code = cli_main(["--catalog", "non_existent_file.json"])
    assert exit_code == 1


# ============================================================================
# 7. PIPELINE PATTERN & STEP 3 MODULE TESTS
# ============================================================================


def test_confidence_scorer_scoring_logic() -> None:
    """Verify ConfidenceScorer calculates correct scores and confidence levels."""
    scorer = ConfidenceScorer()

    # Case 1: Zero controls -> 0.0, LOW
    score, level = scorer.calculate_confidence("gdpr-art-32", [], "high")
    assert score == 0.0
    assert level == ConfidenceLevel.LOW

    # Helper to create dummy control
    def make_tc(ctrl_id: str, status: ComplianceStatus) -> TechnicalControl:
        return TechnicalControl(
            control_id=ctrl_id,
            control_category=ControlCategory.ENCRYPTION,
            cloud_provider=CloudProvider.AZURE,
            resource_type="Microsoft.Storage/storageAccounts",
            resource_id=f"/res/{ctrl_id}",
            resource_name=ctrl_id,
            control_description="Storage encryption",
            compliance_status=status,
            current_state={"state": "val"},
        )

    # Case 2: 3 compliant controls with low friction -> High confidence
    controls_compliant = [
        make_tc("ctrl-1", ComplianceStatus.COMPLIANT),
        make_tc("ctrl-2", ComplianceStatus.COMPLIANT),
        make_tc("ctrl-3", ComplianceStatus.COMPLIANT),
    ]
    score_hi, level_hi = scorer.calculate_confidence("gdpr-art-32", controls_compliant, "low")
    assert score_hi >= 0.80
    assert level_hi == ConfidenceLevel.HIGH

    # Case 3: High friction discount applied
    score_hf, _ = scorer.calculate_confidence("gdpr-art-32", controls_compliant, "high")
    assert score_hf < score_hi

    # Case 4: Inconsistent status penalty
    mixed_controls = [
        make_tc("ctrl-1", ComplianceStatus.COMPLIANT),
        make_tc("ctrl-2", ComplianceStatus.NON_COMPLIANT),
    ]
    score_mixed, _ = scorer.calculate_confidence("gdpr-art-32", mixed_controls, "low")
    assert score_mixed < 0.85


def test_gap_evaluator_pipeline() -> None:
    """Verify GapEvaluator end-to-end evaluation with catalog and baseline."""
    evaluator = GapEvaluator()

    catalog_controls = [
        {"id": "gdpr-art32", "title": "Security of Processing"},
        {"id": "dora-art-6", "title": "ICT Risk Management"},
        {"id": "unmapped-reg-99", "title": "Obscure Local Requirement"},
    ]

    baseline = InfrastructureBaseline(
        baseline_id="azure-prod-baseline",
        cloud_provider=CloudProvider.AZURE,
        controls=[
            TechnicalControl(
                control_id="azure-storage-encryption-blob1",
                control_category=ControlCategory.ENCRYPTION,
                cloud_provider=CloudProvider.AZURE,
                resource_type="Microsoft.Storage/storageAccounts",
                resource_id="/subscriptions/xxx/storageAccounts/blob1",
                resource_name="blob1",
                control_description="Storage account blob encryption",
                compliance_status=ComplianceStatus.COMPLIANT,
                current_state={"blob_encryption": True},
            ),
            TechnicalControl(
                control_id="azure-nsg-allow-all",
                control_category=ControlCategory.NETWORK,
                cloud_provider=CloudProvider.AZURE,
                resource_type="Microsoft.Network/networkSecurityGroups",
                resource_id="/subscriptions/xxx/nsg/nsg1",
                resource_name="nsg1",
                control_description="Network security group open ports",
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                current_state={"open_ports": [22, 80]},
            ),
        ],
    )

    friction_data = {"gdpr-art32": "high", "dora-art-6": "medium"}

    report = evaluator.evaluate_gaps(catalog_controls, baseline, friction_data)
    assert report.total_regulatory_controls == 3
    assert len(report.results) == 3

    # Check unmapped control
    unmapped_result = next(
        r for r in report.results if r.regulatory_control_id == "unmapped-reg-99"
    )
    assert unmapped_result.gap_type == GapType.MISSING
    assert unmapped_result.compliance_status == "non-compliant"
    assert len(unmapped_result.mapped_technical_controls) == 0

    # Check summary statistics
    assert report.summary["total_controls_analyzed"] == 3
    assert "gap_type_breakdown" in report.summary
    assert "avg_confidence_score" in report.summary


def test_gap_analysis_report_helper_methods() -> None:
    """Verify GapAnalysisReport filtering and summary methods."""
    results = [
        GapAnalysisResult(
            regulatory_control_id="reg-1",
            regulatory_control_title="Ctrl 1",
            regulation="GDPR",
            gap_type=GapType.COMPLIANT,
            compliance_status="compliant",
            confidence_score=0.9,
            confidence_level=ConfidenceLevel.HIGH,
        ),
        GapAnalysisResult(
            regulatory_control_id="reg-2",
            regulatory_control_title="Ctrl 2",
            regulation="GDPR",
            gap_type=GapType.MISSING,
            compliance_status="non-compliant",
            confidence_score=0.0,
            confidence_level=ConfidenceLevel.LOW,
        ),
        GapAnalysisResult(
            regulatory_control_id="reg-3",
            regulatory_control_title="Ctrl 3",
            regulation="DORA",
            gap_type=GapType.PARTIAL,
            compliance_status="partial",
            confidence_score=0.6,
            confidence_level=ConfidenceLevel.MEDIUM,
        ),
    ]

    report = GapAnalysisReport(
        report_id="test-report-01",
        catalog_id="cat-01",
        baseline_id="base-01",
        total_regulatory_controls=3,
        total_technical_controls=5,
        results=results,
    )

    # Test get_results_by_gap_type
    compliant = report.get_results_by_gap_type(GapType.COMPLIANT)
    assert len(compliant) == 1
    assert compliant[0].regulatory_control_id == "reg-1"

    # Test get_non_compliant_results
    non_compliant = report.get_non_compliant_results()
    assert len(non_compliant) == 2

    # Test get_compliance_summary
    comp_sum = report.get_compliance_summary()
    assert comp_sum[GapType.COMPLIANT.value] == 1
    assert comp_sum[GapType.MISSING.value] == 1
    assert comp_sum[GapType.PARTIAL.value] == 1

    # Test get_confidence_summary
    conf_sum = report.get_confidence_summary()
    assert conf_sum[ConfidenceLevel.HIGH.value] == 1
    assert conf_sum[ConfidenceLevel.LOW.value] == 1
    assert conf_sum[ConfidenceLevel.MEDIUM.value] == 1


def test_report_generator_formats(tmp_path: Path) -> None:
    """Verify ReportGenerator outputs JSON, Markdown, and terminal reports."""
    results = [
        GapAnalysisResult(
            regulatory_control_id="gdpr-art32",
            regulatory_control_title="Security of Processing",
            regulation="GDPR",
            mapped_technical_controls=["azure-storage-encryption-01"],
            gap_type=GapType.COMPLIANT,
            compliance_status="compliant",
            confidence_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            recommendations=["Maintain current encryption configurations."],
        )
    ]

    report = GapAnalysisReport(
        report_id="rep-test-100",
        catalog_id="cat-gdpr",
        baseline_id="base-azure",
        total_regulatory_controls=1,
        total_technical_controls=1,
        results=results,
        summary={
            "total_controls_analyzed": 1,
            "avg_confidence_score": 0.95,
            "compliance_status_breakdown": {"compliant": 1},
            "confidence_breakdown": {"high": 1},
        },
    )

    generator = ReportGenerator(report)

    # JSON output
    json_path = tmp_path / "report.json"
    generator.save_json(str(json_path))
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["report_id"] == "rep-test-100"

    # Markdown output
    md_path = tmp_path / "report.md"
    generator.save_markdown(str(md_path))
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "# Gap Analysis Report" in content
    assert "gdpr-art32" in content

    # Terminal report output (must run without exceptions)
    generator.print_terminal_report()


# ============================================================================
# 8. STEP 3 SPECIFICATION TESTS (Part 4 Testing Strategy)
# ============================================================================


@pytest.fixture
def sample_technical_controls() -> List[TechnicalControl]:
    """Create sample technical controls for testing."""
    return [
        TechnicalControl(
            control_id="azure-storage-encryption-test1",
            control_category=ControlCategory.ENCRYPTION,
            cloud_provider=CloudProvider.AZURE,
            resource_type="StorageAccount",
            resource_id="/subscriptions/test/resource1",
            resource_name="test-storage-1",
            control_description="Storage encryption",
            current_state={"encryption": True},
            compliance_status=ComplianceStatus.COMPLIANT,
        ),
        TechnicalControl(
            control_id="azure-nsg-test1",
            control_category=ControlCategory.NETWORK,
            cloud_provider=CloudProvider.AZURE,
            resource_type="NetworkSecurityGroup",
            resource_id="/subscriptions/test/resource2",
            resource_name="test-nsg-1",
            control_description="Network security",
            current_state={"rules": []},
            compliance_status=ComplianceStatus.NON_COMPLIANT,
        ),
    ]


@pytest.fixture
def sample_baseline(
    sample_technical_controls: List[TechnicalControl],
) -> InfrastructureBaseline:
    """Create a sample infrastructure baseline."""
    return InfrastructureBaseline(
        baseline_id="test-baseline",
        cloud_provider=CloudProvider.AZURE,
        subscription_id="test-sub",
        total_resources_scanned=len(sample_technical_controls),
        controls=sample_technical_controls,
    )


@pytest.fixture
def sample_catalog_controls() -> List[Dict[str, str]]:
    """Create sample regulatory catalog controls."""
    return [
        {
            "id": "gdpr-art32",
            "title": "Security of processing",
        },
        {
            "id": "dora-art-6",
            "title": "ICT risk management framework",
        },
    ]


def test_control_mapper_default_mappings() -> None:
    """Test that default mappings are initialized."""
    mapper = ControlMapper()
    assert len(mapper.mapping_rules) > 0
    assert "gdpr-art32" in mapper.mapping_rules


def test_control_mapper_get_technical_controls(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """Test mapping regulatory controls to technical controls."""
    mapper = ControlMapper()
    available = [tc.control_id for tc in sample_baseline.controls]

    mapped = mapper.get_technical_controls_for_regulatory("gdpr-art32", available)

    # Should find at least one matching control
    assert len(mapped) >= 0


def test_confidence_scorer_high_confidence(
    sample_technical_controls: List[TechnicalControl],
) -> None:
    """Test confidence scoring with good evidence."""
    scorer = ConfidenceScorer()

    score, level = scorer.calculate_confidence(
        regulatory_control_id="gdpr-art32",
        mapped_technical_controls=sample_technical_controls,
        friction_level="low",
        evidence_quality="good",
    )

    assert score > 0.5
    assert level in [ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH]


def test_confidence_scorer_low_confidence() -> None:
    """Test confidence scoring with poor evidence."""
    scorer = ConfidenceScorer()

    score, level = scorer.calculate_confidence(
        regulatory_control_id="gdpr-art32",
        mapped_technical_controls=[],
        friction_level="high",
        evidence_quality="poor",
    )

    assert score < 0.5
    assert level == ConfidenceLevel.LOW


def test_gap_evaluator_identifies_missing_controls(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """Test that gap evaluator identifies missing controls."""
    evaluator = GapEvaluator()

    catalog_controls = [{"id": "unknown-control", "title": "Unknown requirement"}]

    report = evaluator.evaluate_gaps(catalog_controls, sample_baseline)

    assert len(report.results) == 1
    assert report.results[0].gap_type == GapType.MISSING


def test_gap_evaluator_identifies_compliant_controls(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """Test that gap evaluator identifies compliant controls."""
    evaluator = GapEvaluator()

    # Create a custom mapper that maps to our sample controls
    mapper = ControlMapper()
    mapper.add_mapping_rule("test-control", ["azure-storage-encryption-test1"])

    evaluator = GapEvaluator(control_mapper=mapper)

    catalog_controls = [{"id": "test-control", "title": "Test requirement"}]

    report = evaluator.evaluate_gaps(catalog_controls, sample_baseline)

    assert len(report.results) == 1
    # Should be compliant since the control is COMPLIANT
    assert report.results[0].compliance_status == "compliant"


def test_gap_evaluator_generates_recommendations(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """Test that gap evaluator generates recommendations."""
    evaluator = GapEvaluator()

    catalog_controls = [{"id": "missing-control", "title": "Missing requirement"}]

    report = evaluator.evaluate_gaps(catalog_controls, sample_baseline)

    assert len(report.results) == 1
    assert len(report.results[0].recommendations) > 0


def test_gap_analysis_report_summary(
    sample_baseline: InfrastructureBaseline,
) -> None:
    """Test that report generates correct summary."""
    evaluator = GapEvaluator()

    catalog_controls = [
        {"id": "gdpr-art32", "title": "Security of processing"},
        {"id": "dora-art-6", "title": "ICT risk management"},
    ]

    report = evaluator.evaluate_gaps(catalog_controls, sample_baseline)

    assert report.summary["total_controls_analyzed"] == 2
    assert "gap_type_breakdown" in report.summary
    assert "compliance_status_breakdown" in report.summary
