import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.answer_generation.answer_generator import AnswerGenerator
from app.answer_generation.schemas import AnswerStatus
from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import EdgeType
from app.claim_extraction.schemas import ClaimType
from app.verification.graph_verifier import GraphVerificationResult
from app.verification.cross_claim_contradiction import CrossClaimContradictionReport, CrossClaimContradictionResult
from app.verification.contradiction_classifier import ContradictionLabel
from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus, ControllerStage
from app.controller.controller import AERISController

def test_a_supported():
    print("\n--- TEST A: SUPPORTED ---")
    question = "What datasets were used in the experiments?"
    
    graph = ClaimEvidenceGraphBuilder("test_doc")
    graph.add_evidence(
        chunk_id="test_document_p019_c041",
        text="The datasets used in the experiments include Natural Questions, TriviaQA, and MS-MARCO."
    )
    graph.add_claim(
        claim_id="claim_1",
        text="The datasets used in the experiments include Natural Questions, TriviaQA, and MS-MARCO.",
        claim_type=ClaimType.FACT,
        source_chunk_id="test_document_p019_c041"
    )
    graph.add_edge("claim_1", "test_document_p019_c041")
    
    ver_results = [
        GraphVerificationResult(
            claim_id="claim_1", 
            claim="The datasets used in the experiments include Natural Questions, TriviaQA, and MS-MARCO.",
            evidence_count=1,
            evidence_chunk_ids=["test_document_p019_c041"],
            label=EdgeType.SUPPORTS, 
            verification_confidence=0.95,
            rationale="Matches the text exactly."
        )
    ]
    
    gen = AnswerGenerator()
    ans = gen.generate(question, graph, ver_results)
    
    assert ans.status == AnswerStatus.SUPPORTED, f"Expected SUPPORTED, got {ans.status}"
    assert "Natural Questions" in ans.answer
    assert "test_document_p019_c041" in [p.chunk_id for p in ans.provenance]
    print("TEST A PASSED")

def test_b_insufficient():
    print("\n--- TEST B: INSUFFICIENT ---")
    question = "What is the capital of Japan?"
    
    graph = ClaimEvidenceGraphBuilder("test_doc")
    graph.add_evidence(
        chunk_id="test_document_p019_c041",
        text="The datasets used in the experiments include Natural Questions, TriviaQA, and MS-MARCO."
    )
    
    gen = AnswerGenerator()
    ans = gen.generate(question, graph, [])
    
    assert ans.status == AnswerStatus.INSUFFICIENT_EVIDENCE, f"Expected INSUFFICIENT_EVIDENCE, got {ans.status}"
    assert "Tokyo" not in ans.answer
    print("TEST B PASSED")

def test_c_complex():
    print("\n--- TEST C: COMPLEX ---")
    question = "How does the system fuse dense and sparse retrieval?"
    
    graph = ClaimEvidenceGraphBuilder("test_doc")
    graph.add_evidence(
        chunk_id="chunk_1",
        text="Dense and sparse retrieval are fused using Reciprocal Rank Fusion (RRF)."
    )
    graph.add_evidence(
        chunk_id="chunk_2",
        text="Dense and sparse retrieval are fused using a linear combination of scores."
    )
    graph.add_claim(
        claim_id="claim_1",
        text="Dense and sparse retrieval are fused using Reciprocal Rank Fusion (RRF).",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk_1"
    )
    graph.add_claim(
        claim_id="claim_2",
        text="Dense and sparse retrieval are fused using a linear combination of scores.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk_2"
    )
    graph.add_edge("claim_1", "chunk_1")
    graph.add_edge("claim_2", "chunk_2")
    
    ver_results = [
        GraphVerificationResult(
            claim_id="claim_1",
            claim="Dense and sparse retrieval are fused using Reciprocal Rank Fusion (RRF).",
            evidence_count=1,
            evidence_chunk_ids=["chunk_1"],
            label=EdgeType.SUPPORTS, 
            verification_confidence=0.9,
            rationale="Matches."
        ),
        GraphVerificationResult(
            claim_id="claim_2",
            claim="Dense and sparse retrieval are fused using a linear combination of scores.",
            evidence_count=1,
            evidence_chunk_ids=["chunk_2"],
            label=EdgeType.SUPPORTS, 
            verification_confidence=0.8,
            rationale="Matches."
        )
    ]
    
    contradictions = CrossClaimContradictionReport(
        document_id="test_doc",
        claim_count=2,
        evidence_pair_count=1,
        contradiction_count=1,
        contextual_difference_count=0,
        no_contradiction_count=0,
        uncertain_count=0,
        conflicts=[
            CrossClaimContradictionResult(
                claim_a_id="claim_1",
                claim_a="Dense and sparse retrieval are fused using Reciprocal Rank Fusion (RRF).",
                evidence_a_chunk_id="chunk_1",
                claim_b_id="claim_2",
                claim_b="Dense and sparse retrieval are fused using a linear combination of scores.",
                evidence_b_chunk_id="chunk_2",
                label=ContradictionLabel.CONTRADICTION,
                confidence=0.95,
                rationale="RRF vs Linear Combination"
            )
        ]
    )
    
    gen = AnswerGenerator()
    ans = gen.generate(question, graph, ver_results, contradictions)
    
    assert ans.status == AnswerStatus.CONFLICTED, f"Expected CONFLICTED, got {ans.status}"
    assert "RRF" in ans.answer or "Linear" in ans.answer
    assert ans.conflict_information is not None
    print("TEST C PASSED")

def test_d_disabled():
    print("\n--- TEST D: DISABLED ---")
    from unittest.mock import MagicMock
    class DummyGenerator:
        def generate(self, *args, **kwargs):
            raise Exception("Should not be called")
            
    dummy = MagicMock()
    dummy.plan.return_value = type('Result', (), {'requirements': []})
    dummy.retrieve_for_requirement.return_value = []
    
    controller = AERISController(
        planner=dummy, adaptive_retrieval_controller=dummy, claim_extractor=dummy,
        claim_normalizer=dummy, claim_typer=dummy, graph_builder_factory=lambda x: ClaimEvidenceGraphBuilder(x),
        graph_verifier=dummy, contradiction_analyzer=dummy, contradiction_integrator=dummy, 
        cross_lingual_analyzer=dummy, cross_lingual_integrator=dummy, calibrator=dummy, 
        selective_verification_executor=dummy, answer_generator=DummyGenerator()
    )
    
    req = ControllerRequest(document_id="test_doc", question="Test?", config=ControllerConfig(answer_generation_enabled=False))
    res = controller.run(req)
    
    assert res.final_answer is None
    assert any(s.stage == ControllerStage.ANSWER_GENERATION and s.status == StageStatus.SKIPPED for s in res.stages)
    assert res.status == StageStatus.COMPLETED
    print("TEST D PASSED")

def test_e_failure():
    print("\n--- TEST E: FAILURE ---")
    from unittest.mock import MagicMock
    class FailingGenerator:
        def generate(self, *args, **kwargs):
            raise Exception("Mocked LLM timeout")
            
    dummy = MagicMock()
    dummy.plan.return_value = type('Result', (), {'requirements': []})
    dummy.retrieve_for_requirement.return_value = []
            
    controller = AERISController(
        planner=dummy, adaptive_retrieval_controller=dummy, claim_extractor=dummy,
        claim_normalizer=dummy, claim_typer=dummy, graph_builder_factory=lambda x: ClaimEvidenceGraphBuilder(x),
        graph_verifier=dummy, contradiction_analyzer=dummy, contradiction_integrator=dummy, 
        cross_lingual_analyzer=dummy, cross_lingual_integrator=dummy, calibrator=dummy, 
        selective_verification_executor=dummy, answer_generator=FailingGenerator()
    )
    
    req = ControllerRequest(document_id="test_doc", question="Test?", config=ControllerConfig(answer_generation_enabled=True))
    res = controller.run(req)
    
    assert res.status == StageStatus.FAILED
    assert res.final_answer is None
    assert any("Mocked LLM timeout" in s.message for s in res.stages if s.status == StageStatus.FAILED)
    print("TEST E PASSED")

if __name__ == "__main__":
    test_a_supported()
    test_b_insufficient()
    test_c_complex()
    test_d_disabled()
    test_e_failure()
    print("\nALL TESTS PASSED")
