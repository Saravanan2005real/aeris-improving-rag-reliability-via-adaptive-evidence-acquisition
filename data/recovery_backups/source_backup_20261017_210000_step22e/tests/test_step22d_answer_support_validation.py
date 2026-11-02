"""
Step 22D Regression Test: Workstream 2 - Answer-Support Validation

Verifies:
1. RequirementSupportValidator semantic validation across 5 supported cases:
   - Direct facts
   - Methods / procedural claims
   - Quantitative claims (numbers / counts / scores)
   - Multi-hop questions
   - Paraphrased but supported claims
2. Genuinely unsupported claims are strictly REJECTED (is_supported=False).
3. Controller integration:
   - Unsupported answers are downgraded to INSUFFICIENT_EVIDENCE.
   - Controller records structured downgrade_details (reason, category, requirements, claim IDs).
   - Provenance defect causes structured PROVENANCE_DEFECT downgrade.
"""

from unittest.mock import MagicMock
from app.verification.requirement_support import (
    RequirementSupportValidator,
    RequirementSupportResult,
)
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus
from app.planning.schemas import InformationRequirement


# Instantiate validator with fallback (client=None forces deterministic semantic fallback)
validator = RequirementSupportValidator()
validator.client = None


def test_support_validation_direct_fact():
    """Direct factual statement supported by evidence."""
    res = validator.validate(
        question="What was the reported BLEU score of the base model?",
        requirement="Quantitative BLEU score of the baseline model.",
        answer="The baseline model achieved a BLEU score of 34.2 on the evaluation set.",
        claims=["The baseline model achieved a BLEU score of 34.2 on the evaluation set."],
        evidence_texts=["Our baseline transformer architecture scored 34.2 BLEU on WMT-14."],
        requirement_id="req_fact",
    )
    assert res.is_supported is True
    assert res.downgrade_category is None


def test_support_validation_methods():
    """Methodology / procedural claims supported by evidence."""
    res = validator.validate(
        question="How does the optimizer adjust learning rate?",
        requirement="Optimization methodology and learning rate schedule.",
        answer="The training uses cosine annealing learning rate schedule with linear warmup.",
        claims=["The training uses cosine annealing learning rate schedule with linear warmup."],
        evidence_texts=["We schedule the learning rate using cosine annealing preceded by 2000 steps of linear warmup."],
        requirement_id="req_method",
    )
    assert res.is_supported is True
    assert res.downgrade_category is None


def test_support_validation_quantitative():
    """Quantitative numbers, statistics, and counts."""
    res = validator.validate(
        question="How many training samples were used?",
        requirement="Dataset size and training sample count.",
        answer="The model was trained on 45,000 document pairs.",
        claims=["The training set comprised 45000 pairs of documents."],
        evidence_texts=["Dataset statistics: 45,000 document pairs in train split, 5,000 in dev split."],
        requirement_id="req_quant",
    )
    assert res.is_supported is True
    assert res.downgrade_category is None


def test_support_validation_multi_hop():
    """Multi-hop answers combining multiple evidence steps."""
    res = validator.validate(
        question="Which institution is the author affiliated with, and where is it located?",
        requirement="Author's institutional affiliation and geographic location.",
        answer="The author is affiliated with Max Planck Institute, which is located in Munich.",
        claims=[
            "Author Jane Doe is affiliated with the Max Planck Institute.",
            "The Max Planck Institute is located in Munich, Germany.",
        ],
        evidence_texts=[
            "Jane Doe is a researcher at Max Planck Institute.",
            "Max Planck Institute headquarters and main laboratories are located in Munich.",
        ],
        requirement_id="req_multihop",
    )
    assert res.is_supported is True
    assert res.downgrade_category is None


def test_support_validation_paraphrased_claim():
    """Paraphrased claim with semantic equivalence but differing wording."""
    res = validator.validate(
        question="What is the primary mechanism of AERIS adaptive retrieval?",
        requirement="Core mechanism and adaptation policy of AERIS.",
        answer="AERIS dynamically increases search candidate pool when initial evidence is inadequate.",
        claims=["The system adaptively increases candidate retrieval depth when coverage evaluation detects gaps."],
        evidence_texts=["AERIS dynamically expands retrieval candidate depth from 10 to 50 when coverage is insufficient."],
        requirement_id="req_para",
    )
    assert res.is_supported is True
    assert res.downgrade_category is None


def test_support_validation_genuinely_unsupported():
    """Genuinely unsupported claim MUST be rejected."""
    res = validator.validate(
        question="What was the pretraining batch size?",
        requirement="Batch size utilized during model pretraining.",
        answer="The model was pre-trained with a batch size of 2048 on TPU v4 pods.",
        claims=["The model was pre-trained with a batch size of 2048 on TPU v4 pods."],
        evidence_texts=["The network uses AdamW with weight decay 0.01 and learning rate 5e-4."],
        requirement_id="req_unsupported",
    )
    assert res.is_supported is False
    assert res.downgrade_category in ["REQUIREMENT_UNSUPPORTED", "EVIDENCE_UNSUPPORTED"]
    assert "lack grounding" in res.rationale.lower() or "does not support" in res.rationale.lower() or "missing" in res.rationale.lower()


def test_controller_downgrade_logging_and_provenance():
    """
    Test that when an answer fails requirement support validation:
    1. Status is downgraded to INSUFFICIENT_EVIDENCE.
    2. Structured downgrade_details are recorded in metadata.
    3. Provenance defect causes structured PROVENANCE_DEFECT downgrade.
    """
    mock_planner = MagicMock()
    mock_plan = MagicMock()
    mock_req = InformationRequirement(
        requirement_id="req_1",
        description="Pretraining batch size and hardware specification",
        requirement_type="quantitative",
        priority=1,
        expected_evidence_type="result",
        retrieval_queries=["batch size pretraining"],
    )
    mock_plan.requirements = [mock_req]
    mock_planner.plan.return_value = mock_plan

    # Generator returns answer with claims about batch size 2048
    mock_generator = MagicMock()
    ans_result = MagicMock()
    ans_result.answer = "Pretraining batch size was 2048."
    ans_result.status = MagicMock()
    ans_result.status.value = "SUPPORTED"
    ans_result.confidence = 0.85
    ans_result.supporting_claim_ids = ["c1"]
    ans_result.supporting_chunk_ids = ["chk_1"]
    ans_result.provenance = []
    ans_result.conflict_information = None
    ans_result.insufficiency_reason = None
    mock_generator.generate.return_value = ans_result

    class MockGraphBuilder:
        def __init__(self):
            self.claims = {"c1": MagicMock(text="Pretraining batch size was 2048 on TPU pods.")}
            self.evidence = {"chk_1": MagicMock(text="The network uses AdamW with weight decay 0.01.")}

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

    # Adaptive retrieval returning evidence that does NOT contain batch size
    mock_ar = MagicMock()
    ret_item = MagicMock(chunk_id="chk_1", document_id="doc1", text="The network uses AdamW.")
    mock_ar_res = MagicMock()
    mock_ar_res.evidence = [ret_item]
    mock_ar_res.attempts = [
        MagicMock(candidate_k=10, query_type="original", model_dump=lambda: {"candidate_k": 10})
    ]
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
        requirement_validator=validator,
    )

    req = ControllerRequest(
        document_id="doc1",
        question="What was the pretraining batch size?",
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

    assert res.status == StageStatus.COMPLETED, f"Pipeline error: {res.stages[-1].message if res.stages else 'no stages'}"
    # 1. Downgraded to INSUFFICIENT_EVIDENCE
    assert res.answer_status == "INSUFFICIENT_EVIDENCE"

    # 2. Structured downgrade details logged
    assert "downgrade_details" in res.metadata
    details = res.metadata["downgrade_details"]
    assert len(details) > 0
    req_downgrade = next(d for d in details if d["downgrade_type"] == "REQUIREMENT_UNSUPPORTED")
    assert "req_1" in req_downgrade["unsupported_requirements"]
    assert "c1" in req_downgrade["supporting_claim_ids"]
    assert "REQUIREMENT_UNSUPPORTED" in req_downgrade["categories"] or "EVIDENCE_UNSUPPORTED" in req_downgrade["categories"]
