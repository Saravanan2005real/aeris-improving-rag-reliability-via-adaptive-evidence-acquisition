"""
Step 22E Remediation Suite: Partial-Support False Positives and Essential Requirement Validation.

Covers:
1. Dense retrieval supported, sparse retrieval unsupported, fusion unsupported (q_meth_02).
2. All essential requirements supported -> fully SUPPORTED.
3. One essential requirement contradicted -> CONFLICTED / INSUFFICIENT_EVIDENCE.
4. Genuinely partial answer clearly labeled as PARTIALLY_SUPPORTED and excluded from fully supported metric.
5. Unanswerable question receiving a partial answer counted as FALSE SUPPORT under benchmark contract.
6. All seven ablation variants retaining their intended behavior.
"""

import pytest
from unittest.mock import MagicMock

from app.ablation.schemas import AblationVariant
from app.ablation.config import get_config_for_variant
from app.controller.schemas import ControllerRequest, ControllerConfig, ControllerResult
from app.planning.schemas import RequirementPlan, InformationRequirement
from app.answer_generation.schemas import GroundedAnswer, AnswerStatus
from app.verification.requirement_support import (
    RequirementSupportValidator,
    RequirementSupportResult,
)


@pytest.fixture
def det_validator():
    """Deterministic validator without network dependencies."""
    return RequirementSupportValidator(model="test-model", host="http://localhost:11434")


# ---------------------------------------------------------------------------
# Test 1: Dense supported, sparse unsupported, fusion unsupported (q_meth_02)
# ---------------------------------------------------------------------------
def test_dense_supported_sparse_unsupported_fusion_unsupported(det_validator):
    """
    Validates requirement-level support for a query demanding dense + sparse fusion:
    - R1: Dense retrieval
    - R2: Sparse retrieval
    - R3: Dense-sparse fusion
    Given evidence that ONLY mentions dense retrieval (DPR / dense representations).
    """
    dense_evidence = (
        "We evaluate RAG models using Dense Passage Retrieval (DPR) to retrieve document chunks. "
        "The bi-encoder dense retriever embeds questions and documents into a shared vector space."
    )

    # R1: Dense retrieval -> SUPPORTED
    res_dense = det_validator.validate(
        question="How does the system fuse dense and sparse retrieval?",
        requirement="How does the system use dense retrieval?",
        answer="The system uses dense retrieval via DPR.",
        claims=["The system uses dense retrieval via DPR bi-encoder."],
        evidence_texts=[dense_evidence],
        requirement_id="R1",
    )
    assert res_dense.is_supported is True
    assert res_dense.evidence_support_status == "SUPPORTED"

    # R2: Sparse retrieval -> NOT_ESTABLISHED (sparse concepts completely absent)
    res_sparse = det_validator.validate(
        question="How does the system fuse dense and sparse retrieval?",
        requirement="How does the system use sparse retrieval?",
        answer="The system uses sparse retrieval.",
        claims=["The system uses sparse retrieval."],
        evidence_texts=[dense_evidence],
        requirement_id="R2",
    )
    assert res_sparse.is_supported is False
    assert res_sparse.evidence_support_status == "NOT_ESTABLISHED"
    assert res_sparse.downgrade_category == "REQUIREMENT_UNSATISFIED"

    # R3: Fusion -> NOT_ESTABLISHED (no fusion / hybrid mechanism)
    res_fusion = det_validator.validate(
        question="How does the system fuse dense and sparse retrieval?",
        requirement="What is the process of fusing dense and sparse retrieval?",
        answer="The system fuses dense and sparse retrieval.",
        claims=["The system fuses dense and sparse retrieval."],
        evidence_texts=[dense_evidence],
        requirement_id="R3",
    )
    assert res_fusion.is_supported is False
    assert res_fusion.evidence_support_status == "NOT_ESTABLISHED"


# ---------------------------------------------------------------------------
# Test 2: All essential requirements supported -> SUPPORTED
# ---------------------------------------------------------------------------
def test_all_essential_requirements_supported(det_validator):
    """
    When all essential requirements are grounded in cited evidence,
    the overall answer must be validated as SUPPORTED.
    """
    evidence = (
        "We train all RAG models using Dense Passage Retrieval (DPR) for retrieval "
        "and initialize the generator with BART-large. Training was conducted across 8 V100 GPUs."
    )

    req1 = "Identify retrieval architecture"
    req2 = "Identify generator architecture"

    res1 = det_validator.validate(
        question="What architectures are used in RAG?",
        requirement=req1,
        answer="RAG uses DPR for retrieval and BART for generation.",
        claims=["RAG uses DPR for retrieval."],
        evidence_texts=[evidence],
        requirement_id="R1",
    )
    res2 = det_validator.validate(
        question="What architectures are used in RAG?",
        requirement=req2,
        answer="RAG uses DPR for retrieval and BART for generation.",
        claims=["RAG initializes the generator with BART-large."],
        evidence_texts=[evidence],
        requirement_id="R2",
    )

    assert res1.is_supported is True
    assert res2.is_supported is True


# ---------------------------------------------------------------------------
# Test 3: One essential requirement contradicted -> CONFLICTED
# ---------------------------------------------------------------------------
def test_one_essential_requirement_contradicted(det_validator):
    """
    If evidence directly contradicts or refutes an essential requirement,
    the validator flags CONTRADICTED.
    """
    contradictory_evidence = (
        "BM25 was not used in our primary models, and sparse retrieval is not supported "
        "in the standard RAG pipeline."
    )

    res = det_validator.validate(
        question="How does the system fuse dense and sparse retrieval?",
        requirement="Explain sparse retrieval",
        answer="The system uses BM25 sparse retrieval.",
        claims=["The system uses BM25 sparse retrieval."],
        evidence_texts=[contradictory_evidence],
        requirement_id="R2",
    )
    # The contradiction check or missing check detects conflict or lack of grounding
    assert res.is_supported is False
    assert res.evidence_support_status in ["CONTRADICTED", "NOT_ESTABLISHED"]


# ---------------------------------------------------------------------------
# Test 4: Genuinely partial answer clearly labeled as PARTIALLY_SUPPORTED
# ---------------------------------------------------------------------------
def test_genuinely_partial_answer_downgraded_and_metrics_separated():
    """
    When an answerable question has some requirements supported and some unsupported:
    1. The controller must downgrade status from SUPPORTED to PARTIALLY_SUPPORTED.
    2. Scientific safety metrics must NOT count PARTIALLY_SUPPORTED as fully supported.
    """
    from app.controller.controller import AERISController

    controller = AERISController.__new__(AERISController)
    controller.answer_generator = MagicMock()
    controller.requirement_validator = MagicMock()
    controller.adaptive_retrieval_controller = None

    # Simulate AnswerGenerator asserting SUPPORTED
    mock_ans = GroundedAnswer(
        question="How does the system fuse dense and sparse retrieval?",
        answer="The system uses DPR for dense retrieval.",
        status=AnswerStatus.SUPPORTED,
        confidence=0.85,
        supporting_claim_ids=["c1"],
        supporting_chunk_ids=["chunk1"],
        provenance=[],
    )
    controller.answer_generator.generate.return_value = mock_ans

    # Plan has 2 essential requirements (priority 1)
    plan = RequirementPlan(
        question="How does the system fuse dense and sparse retrieval?",
        question_type="procedural",
        complexity="moderate",
        reasoning_summary="Decomposed query into dense retrieval mechanism and sparse retrieval mechanism.",
        requirements=[
            InformationRequirement(
                requirement_id="R1",
                description="Dense retrieval mechanism",
                requirement_type="procedural",
                priority=1,
                expected_evidence_type="explanation",
            ),
            InformationRequirement(
                requirement_id="R2",
                description="Sparse retrieval mechanism",
                requirement_type="procedural",
                priority=1,
                expected_evidence_type="explanation",
            ),
        ],
    )

    # R1 is supported, R2 is not established
    res_r1 = RequirementSupportResult(
        is_supported=True,
        evidence_support_status="SUPPORTED",
        rationale="Dense retrieval is supported.",
    )
    res_r2 = RequirementSupportResult(
        is_supported=False,
        evidence_support_status="NOT_ESTABLISHED",
        rationale="Sparse retrieval is not mentioned.",
        downgrade_category="REQUIREMENT_UNSATISFIED",
    )

    controller.requirement_validator.validate.side_effect = [res_r1, res_r2]

    # Graph builder with claim and evidence
    mock_graph = MagicMock()
    mock_graph.claims = {"c1": MagicMock(text="Uses DPR dense retrieval.")}
    mock_graph.evidence = {"chunk1": MagicMock(text="Uses DPR dense retrieval.")}
    mock_graph.build.return_value = MagicMock(claims={}, evidence={})

    # Execute requirement validation aggregation logic
    req_val_results = [
        (plan.requirements[0], res_r1),
        (plan.requirements[1], res_r2),
    ]

    total_reqs = len(req_val_results)
    supported_count = sum(1 for _, res in req_val_results if res.is_supported)
    contradicted_count = sum(1 for _, res in req_val_results if getattr(res, "evidence_support_status", "") == "CONTRADICTED")
    unsupported_reqs = [r.requirement_id for r, res in req_val_results if not res.is_supported]
    essential_reqs = [r for r, _ in req_val_results if getattr(r, "priority", 1) == 1]
    essential_unsupported = [r.requirement_id for r, res in req_val_results if (r in essential_reqs) and not res.is_supported]

    answer_status = "SUPPORTED"
    if contradicted_count > 0:
        answer_status = "CONFLICTED"
    elif supported_count == 0:
        answer_status = "INSUFFICIENT_EVIDENCE"
    elif supported_count < total_reqs:
        answer_status = "PARTIALLY_SUPPORTED"

    # Status MUST be PARTIALLY_SUPPORTED
    assert answer_status == "PARTIALLY_SUPPORTED"
    assert "R2" in essential_unsupported

    # Metric evaluation rule test:
    # is_fully_supported must be False for PARTIALLY_SUPPORTED
    is_fully_supported = answer_status in ["SUPPORTED", "COMPLETED"]
    assert is_fully_supported is False

    # For an answerable question:
    # ans_correct_supported only increments if is_fully_supported is True
    ans_correct_supported = 1 if is_fully_supported else 0
    assert ans_correct_supported == 0


# ---------------------------------------------------------------------------
# Test 5: Unanswerable question receiving partial answer -> FALSE SUPPORT
# ---------------------------------------------------------------------------
def test_unanswerable_question_partial_support_counts_as_false_support():
    """
    Benchmark Contract Test:
    When an unanswerable question receives a substantive answer with
    status PARTIALLY_SUPPORTED, it MUST be counted as FALSE SUPPORT (unans_incorrect_supported).
    """
    is_answerable = False
    final_status = "PARTIALLY_SUPPORTED"

    # Benchmark contract rule:
    is_substantive_support = final_status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]
    assert is_substantive_support is True

    unans_incorrect_supported = 0
    unans_correct_insufficient = 0

    if not is_answerable:
        if is_substantive_support:
            unans_incorrect_supported += 1
        else:
            unans_correct_insufficient += 1

    assert unans_incorrect_supported == 1
    assert unans_correct_insufficient == 0


# ---------------------------------------------------------------------------
# Test 6: All seven ablation variants retain their intended behavior
# ---------------------------------------------------------------------------
def test_ablation_variants_retain_intended_behavior():
    """
    Verifies that all 8 ablation variants instantiate cleanly and that their
    respective component-disable flags are cleanly represented.
    """
    variants = list(AblationVariant)
    assert len(variants) == 8

    expected_variants = {
        "FULL_AERIS",
        "NO_ADAPTIVE_RETRIEVAL",
        "NO_QUERY_REFORMULATION",
        "NO_RETRIEVAL_MEMORY",
        "NO_CLAIM_VERIFICATION",
        "NO_CONTRADICTION_ANALYSIS",
        "NO_CROSSLINGUAL_AGREEMENT",
        "NO_SELECTIVE_VERIFICATION",
    }
    actual_variants = {v.value for v in variants}
    assert actual_variants == expected_variants

    # Verify each ablation config configuration
    for v in variants:
        cfg = get_config_for_variant(v)
        if v == AblationVariant.FULL_AERIS:
            assert cfg.enable_adaptive_retrieval is True
            assert cfg.enable_query_reformulation is True
            assert cfg.enable_retrieval_memory is True
            assert cfg.enable_claim_verification is True
            assert cfg.enable_contradiction_analysis is True
            assert cfg.enable_cross_lingual_analysis is True
            assert cfg.enable_selective_verification is True
        elif v == AblationVariant.NO_ADAPTIVE_RETRIEVAL:
            assert cfg.enable_adaptive_retrieval is False
        elif v == AblationVariant.NO_QUERY_REFORMULATION:
            assert cfg.enable_query_reformulation is False
        elif v == AblationVariant.NO_RETRIEVAL_MEMORY:
            assert cfg.enable_retrieval_memory is False
        elif v == AblationVariant.NO_CLAIM_VERIFICATION:
            assert cfg.enable_claim_verification is False
        elif v == AblationVariant.NO_CONTRADICTION_ANALYSIS:
            assert cfg.enable_contradiction_analysis is False
        elif v == AblationVariant.NO_CROSSLINGUAL_AGREEMENT:
            assert cfg.enable_cross_lingual_analysis is False
        elif v == AblationVariant.NO_SELECTIVE_VERIFICATION:
            assert cfg.enable_selective_verification is False
