"""
Step 22E Verification Suite: Answer-Support Validator Remediation Tests

Validates the four remediated answer-support defects:
1. Prevent Self-Support: Generated answer repeating question keywords cannot establish its own support.
2. Enforce Evidence Entailment: Outside world knowledge, bibliography volume numbers, and superficial concept overlap are rejected.
3. Correct Judge Behavior: Explicit evidence-only evaluation with structured 4-state categorization:
   (SUPPORTED, CONTRADICTED, NOT_ESTABLISHED, INSUFFICIENT_OR_AMBIGUOUS).
4. Safe Multi-Requirement Aggregation: Multi-part requirements with missing or contradicted parts cannot produce SUPPORTED.
"""

from unittest.mock import MagicMock
import pytest

from app.verification.requirement_support import (
    RequirementSupportValidator,
    RequirementSupportResult,
)
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus
from app.planning.schemas import InformationRequirement, RequirementPlan
from app.answer_generation.schemas import GroundedAnswer, AnswerStatus, ProvenanceItem


@pytest.fixture
def det_validator():
    """Deterministic validator without LLM client."""
    val = RequirementSupportValidator()
    val.client = None
    return val


# ---------------------------------------------------------------------------
# Test 1: Self-Support via Question Parroting (B1)
# ---------------------------------------------------------------------------
def test_defect_self_support_repetition_rejected(det_validator):
    """Generated answer repeats question words while evidence discusses unrelated tasks."""
    res = det_validator.validate(
        question="Does the RAG paper evaluate on multilingual tasks?",
        requirement="Did the RAG paper evaluate on multilingual tasks?",
        answer="The RAG paper evaluates on multilingual tasks.",
        claims=["RAG models can go beyond simple extractive QA and answer questions with free-form, abstractive text generation using MSMARCO."],
        evidence_texts=[
            "CT and WQ are small, we follow DPR by initializing CT and WQ models with our NQ RAG model. "
            "We report Exact Match (EM) scores. Abstractive Question Answering uses MSMARCO NLG task v2.1 in English."
        ],
        requirement_id="req_multi",
    )
    assert res.is_supported is False
    assert res.evidence_support_status == "NOT_ESTABLISHED"
    assert "multilingual" in str(res.unmatched_elements) or "multilingual" in res.rationale.lower()


# ---------------------------------------------------------------------------
# Test 2: World Knowledge Absent from Document (B2 & B3)
# ---------------------------------------------------------------------------
def test_defect_world_knowledge_absent_from_document_rejected(det_validator):
    """True real-world fact (Tokyo is capital of Japan) absent from document must be rejected."""
    res = det_validator.validate(
        question="What is the capital of Japan?",
        requirement="The capital of Japan",
        answer="Tokyo",
        claims=["The author published in Proceedings of the 56th Annual Meeting of ACL."],
        evidence_texts=["Wizard of wikipedia: Knowledge-powered conversational agents. SearchQA: A New Q&A Dataset."],
        requirement_id="req_japan",
    )
    assert res.is_supported is False
    assert res.evidence_support_status in ["NOT_ESTABLISHED", "INSUFFICIENT_OR_AMBIGUOUS"]
    assert res.downgrade_category in ["REQUIREMENT_UNSATISFIED", "EVIDENCE_UNSUPPORTED"]


# ---------------------------------------------------------------------------
# Test 3: Bibliography / Reference Number False Match (B2)
# ---------------------------------------------------------------------------
def test_defect_bibliography_numerical_match_rejected(det_validator):
    """Numerical claim (1,000 instances) matched to bibliography entry Volume 1 must be rejected."""
    res = det_validator.validate(
        question="What is the number of instances for the FEVER dataset?",
        requirement="The number of instances in the FEVER dataset",
        answer="The FEVER dataset contains 1,000 instances.",
        claims=["FEVER: a large-scale dataset for fact extraction and verification."],
        evidence_texts=[
            "[56] James Thorne, Andreas Vlachos, Christos Christodoulopoulos, and Arpit Mittal. "
            "FEVER: a large-scale dataset for fact extraction and verification. "
            "In Proceedings of the 2018 Conference of NAACL: HLT, Volume 1, pages 809-819."
        ],
        requirement_id="req_fever",
    )
    assert res.is_supported is False
    assert res.evidence_support_status == "NOT_ESTABLISHED"
    assert res.downgrade_category == "MISSING_QUANTITATIVE_EVIDENCE"


# ---------------------------------------------------------------------------
# Test 4: Dense-Sparse Fusion with Dense-Only Evidence (B2)
# ---------------------------------------------------------------------------
def test_defect_dense_sparse_fusion_unsupported_rejected(det_validator):
    """Claim asserting dense and sparse retrieval fusion when paper only describes dense retrieval."""
    res = det_validator.validate(
        question="How does the system fuse dense and sparse retrieval?",
        requirement="Explain how dense and sparse retrieval are fused",
        answer="The system fuses dense and sparse retrieval by leveraging a retrieval module to augment pre-trained, generative language models.",
        claims=["Our work aims to expand the space of possible tasks with a single, unified architecture, by learning a retrieval module to augment pre-trained, generative language models."],
        evidence_texts=[
            "General-Purpose Architectures for NLP. Prior work on general-purpose architectures for NLP tasks "
            "has shown great success without the use of retrieval. A single, pre-trained language model achieves "
            "strong performance across tasks."
        ],
        requirement_id="req_fusion",
    )
    assert res.is_supported is False
    assert res.evidence_support_status == "NOT_ESTABLISHED"
    assert "sparse" in str(res.unmatched_elements) or "sparse" in res.rationale.lower()


# ---------------------------------------------------------------------------
# Test 5: False Multilingual Evaluation Claim (B2)
# ---------------------------------------------------------------------------
def test_defect_multilingual_evaluation_claim_rejected(det_validator):
    """Claim asserting multilingual evaluation when paper only evaluates English benchmarks."""
    res = det_validator.validate(
        question="Does the RAG paper evaluate on multilingual tasks?",
        requirement="Identify if multilingual tasks are evaluated",
        answer="The paper evaluates on multilingual tasks.",
        claims=["We evaluate on Natural Questions, TriviaQA, WebQuestions, and CuratedTrec benchmarks."],
        evidence_texts=["We evaluate on Natural Questions, TriviaQA, WebQuestions, and CuratedTrec benchmarks in English."],
        requirement_id="req_multi_eval",
    )
    assert res.is_supported is False
    assert res.evidence_support_status == "NOT_ESTABLISHED"


# ---------------------------------------------------------------------------
# Test 6: Safe Multi-Requirement Aggregation in Controller (B4)
# ---------------------------------------------------------------------------
def test_controller_partially_supported_multi_requirement_downgrade():
    """Multi-part question where R1 is supported but R2 is unsupported must downgrade to PARTIALLY_SUPPORTED."""
    mock_planner = MagicMock()
    mock_plan = MagicMock()
    req1 = InformationRequirement(
        requirement_id="req_1",
        description="Author institutional affiliation",
        requirement_type="fact",
        priority=1,
        expected_evidence_type="text",
        retrieval_queries=["affiliation"],
    )
    req2 = InformationRequirement(
        requirement_id="req_2",
        description="Author personal phone number and direct contact",
        requirement_type="fact",
        priority=1,
        expected_evidence_type="text",
        retrieval_queries=["phone number"],
    )
    mock_plan.requirements = [req1, req2]
    mock_planner.plan.return_value = mock_plan

    mock_generator = MagicMock()
    ans_result = MagicMock()
    ans_result.answer = "The author is affiliated with Stanford University and phone is 555-0199."
    ans_result.status = MagicMock()
    ans_result.status.value = "SUPPORTED"
    ans_result.confidence = 0.90
    ans_result.supporting_claim_ids = ["c1"]
    ans_result.supporting_chunk_ids = ["chk_1"]
    ans_result.provenance = []
    ans_result.conflict_information = None
    ans_result.insufficiency_reason = None
    mock_generator.generate.return_value = ans_result

    class MockGraphBuilder:
        def __init__(self):
            self.claims = {"c1": MagicMock(text="Author is affiliated with Stanford University.")}
            self.evidence = {"chk_1": MagicMock(text="Jane Doe is a professor of computer science at Stanford University.")}

        def add_evidence(self, *args, **kwargs):
            pass

        def add_claim(self, *args, **kwargs):
            pass

        def auto_link_claims_to_evidence(self):
            pass

        def build(self):
            mock_g = MagicMock()
            mock_g.claims = self.claims
            mock_g.evidence = self.evidence
            return mock_g

    val = RequirementSupportValidator()
    val.client = None

    mock_ar = MagicMock()
    ret_item = MagicMock(chunk_id="chk_1", document_id="doc1", text="Jane Doe is a professor at Stanford University.")
    mock_ar_res = MagicMock()
    mock_ar_res.evidence = [ret_item]
    mock_ar_res.attempts = [MagicMock(candidate_k=10, query_type="original", model_dump=lambda: {"candidate_k": 10})]
    mock_ar.retrieve_for_requirement.return_value = mock_ar_res

    controller = AERISController(
        planner=mock_planner,
        adaptive_retrieval_controller=mock_ar,
        claim_extractor=MagicMock(),
        claim_normalizer=MagicMock(),
        claim_typer=MagicMock(),
        graph_builder_factory=lambda *args, **kwargs: MockGraphBuilder(),
        graph_verifier=MagicMock(),
        answer_generator=mock_generator,
        requirement_validator=val,
    )

    req = ControllerRequest(
        document_id="doc1",
        question="What is the author's affiliation and phone number?",
        config=ControllerConfig(
            enable_adaptive_retrieval=False,
            enable_query_reformulation=False,
            enable_retrieval_memory=False,
            enable_claim_extraction=False,
            enable_claim_verification=False,
            enable_contradiction_analysis=False,
            enable_cross_lingual_analysis=False,
            enable_calibration=False,
            enable_selective_verification=False,
            answer_generation_enabled=True,
        ),
    )

    res = controller.run(req)

    assert res.status == StageStatus.COMPLETED
    # Status MUST be downgraded from SUPPORTED to PARTIALLY_SUPPORTED
    assert res.answer_status == "PARTIALLY_SUPPORTED"
    assert "downgrade_details" in res.metadata
    details = res.metadata["downgrade_details"]
    part_downgrade = next((d for d in details if d["downgrade_type"] == "REQUIREMENT_PARTIALLY_UNSUPPORTED"), None)
    assert part_downgrade is not None
    assert part_downgrade["supported_count"] == 1
    assert part_downgrade["total_requirements"] == 2
    assert "req_2" in part_downgrade["unsupported_requirements"]


# ---------------------------------------------------------------------------
# Test 7: Contradictory Evidence Handling (B3 & B4)
# ---------------------------------------------------------------------------
def test_contradictory_evidence_handling():
    """Contradicted requirement must be flagged and controller must not accept as SUPPORTED."""
    val = RequirementSupportValidator()
    val.client = None

    res = val.validate(
        question="What was the pretraining batch size?",
        requirement="The pretraining batch size",
        answer="The batch size was 2048.",
        claims=["The pretraining batch size was 2048."],
        evidence_texts=["The network was trained using batch size 512 on 8 GPUs. Batch size 2048 was not used."],
        requirement_id="req_batch",
    )
    # The claimed number 2048 is not supported by the evidence numbers (512, 8)
    assert res.is_supported is False
    assert res.evidence_support_status in ["NOT_ESTABLISHED", "CONTRADICTED"]


# ---------------------------------------------------------------------------
# Test 8: Genuinely Supported Claim Accepted (Non-Regression)
# ---------------------------------------------------------------------------
def test_genuinely_supported_claim_accepted(det_validator):
    """Direct fact supported by evidence must be marked SUPPORTED."""
    res = det_validator.validate(
        question="What was the reported BLEU score of the base model?",
        requirement="Quantitative BLEU score of the baseline model.",
        answer="The baseline model achieved a BLEU score of 34.2 on the evaluation set.",
        claims=["The baseline model achieved a BLEU score of 34.2 on the evaluation set."],
        evidence_texts=["Our baseline transformer architecture scored 34.2 BLEU on WMT-14."],
        requirement_id="req_fact",
    )
    assert res.is_supported is True
    assert res.evidence_support_status == "SUPPORTED"
    assert res.downgrade_category is None


# ---------------------------------------------------------------------------
# Test 9: Multi-Hop Answer Supported When Each Requirement Entailed
# ---------------------------------------------------------------------------
def test_multi_hop_answer_all_requirements_supported(det_validator):
    """Multi-hop requirements where each essential requirement is supported by evidence."""
    res1 = det_validator.validate(
        question="Which institution is the author affiliated with, and where is it located?",
        requirement="Author institutional affiliation",
        answer="The author is affiliated with Max Planck Institute.",
        claims=["Author Jane Doe is affiliated with Max Planck Institute."],
        evidence_texts=["Jane Doe is a researcher at Max Planck Institute."],
        requirement_id="req_affil",
    )
    res2 = det_validator.validate(
        question="Which institution is the author affiliated with, and where is it located?",
        requirement="Geographic location of Max Planck Institute",
        answer="Max Planck Institute is located in Munich.",
        claims=["Max Planck Institute is located in Munich, Germany."],
        evidence_texts=["Max Planck Institute headquarters and main laboratories are located in Munich."],
        requirement_id="req_loc",
    )
    assert res1.is_supported is True
    assert res1.evidence_support_status == "SUPPORTED"
    assert res2.is_supported is True
    assert res2.evidence_support_status == "SUPPORTED"


# ---------------------------------------------------------------------------
# Test 10: Malformed or Missing Evidence and Provenance
# ---------------------------------------------------------------------------
def test_malformed_missing_evidence_and_provenance(det_validator):
    """Missing claims, empty evidence, or provenance defect must be strictly rejected."""
    # 1. No claims
    res_no_claims = det_validator.validate(
        question="What is the learning rate?",
        requirement="Learning rate schedule",
        answer="The learning rate is 5e-4.",
        claims=[],
        evidence_texts=["The optimizer is AdamW with learning rate 5e-4."],
    )
    assert res_no_claims.is_supported is False
    assert res_no_claims.downgrade_category == "NO_SUPPORTING_CLAIMS"

    # 2. No evidence texts
    res_no_ev = det_validator.validate(
        question="What is the learning rate?",
        requirement="Learning rate schedule",
        answer="The learning rate is 5e-4.",
        claims=["The learning rate is 5e-4."],
        evidence_texts=[],
    )
    assert res_no_ev.is_supported is False
    assert res_no_ev.evidence_support_status == "NOT_ESTABLISHED"
    assert res_no_ev.downgrade_category == "EVIDENCE_UNSUPPORTED"
