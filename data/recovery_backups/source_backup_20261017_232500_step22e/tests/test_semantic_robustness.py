import pytest
import time
from unittest.mock import MagicMock

from app.claim_extraction.typer import ClaimTyper
from app.claim_extraction.schemas import ExtractedClaim
from app.planning.requirement_planner import RequirementPlanner
from app.answer_generation.answer_generator import AnswerGenerator
from app.answer_generation.schemas import AnswerStatus
from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest, ControllerConfig


def test_claim_typing_complete_index_classification():
    typer = ClaimTyper()
    typer.client.chat = MagicMock()
    # Correct response for two claims
    typer.client.chat.side_effect = [
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 1, "claim_type": "METHOD"}]'}}
    ]
    claims = [
        ExtractedClaim(claim_id="c1", text="text1", source_chunk_id="ch1", document_id="doc1"),
        ExtractedClaim(claim_id="c2", text="text2", source_chunk_id="ch1", document_id="doc1"),
    ]
    result = typer.type_claims(claims)
    assert len(result) == 2
    assert result[0].claim_id == "c1"
    assert result[0].claim_type == "FACT"
    assert result[1].claim_id == "c2"
    assert result[1].claim_type == "METHOD"
    # test 7 and 8: preservation of identity and provenance
    assert result[0].source_chunk_id == "ch1"
    assert result[0].document_id == "doc1"
    assert result[1].source_chunk_id == "ch1"
    assert result[1].document_id == "doc1"


def test_claim_typing_missing_index():
    typer = ClaimTyper()
    typer.client.chat = MagicMock()
    # First attempt: misses index 1. Second attempt: returns all.
    typer.client.chat.side_effect = [
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}]'}},
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 1, "claim_type": "METHOD"}]'}}
    ]
    claims = [
        ExtractedClaim(claim_id="c1", text="text1", source_chunk_id="ch1", document_id="doc1"),
        ExtractedClaim(claim_id="c2", text="text2", source_chunk_id="ch1", document_id="doc1"),
    ]
    result = typer.type_claims(claims)
    assert len(result) == 2
    # Verify retry prompt included missing ID error
    call_args = typer.client.chat.call_args_list[1][1]["messages"]
    assert "Missing required indexes" in call_args[-1]["content"]


def test_claim_typing_unknown_index():
    typer = ClaimTyper()
    typer.client.chat = MagicMock()
    # First attempt: unknown index 99. Second attempt: correct.
    typer.client.chat.side_effect = [
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 99, "claim_type": "METHOD"}]'}},
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 1, "claim_type": "METHOD"}]'}}
    ]
    claims = [
        ExtractedClaim(claim_id="c1", text="text1", source_chunk_id="ch1", document_id="doc1"),
        ExtractedClaim(claim_id="c2", text="text2", source_chunk_id="ch1", document_id="doc1"),
    ]
    result = typer.type_claims(claims)
    assert len(result) == 2
    call_args = typer.client.chat.call_args_list[1][1]["messages"]
    assert "Unknown indexes returned" in call_args[-1]["content"]


def test_claim_typing_duplicate_index():
    typer = ClaimTyper()
    typer.client.chat = MagicMock()
    # First attempt: duplicate index 0. Second attempt: correct.
    typer.client.chat.side_effect = [
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 0, "claim_type": "METHOD"}]'}},
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 1, "claim_type": "METHOD"}]'}}
    ]
    claims = [
        ExtractedClaim(claim_id="c1", text="text1", source_chunk_id="ch1", document_id="doc1"),
        ExtractedClaim(claim_id="c2", text="text2", source_chunk_id="ch1", document_id="doc1"),
    ]
    result = typer.type_claims(claims)
    assert len(result) == 2
    call_args = typer.client.chat.call_args_list[1][1]["messages"]
    assert "Duplicate indexes found" in call_args[-1]["content"]


def test_claim_typing_invalid_claim_type():
    typer = ClaimTyper()
    typer.client.chat = MagicMock()
    # First attempt: invalid claim type "MAGIC". Second attempt: correct.
    typer.client.chat.side_effect = [
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 1, "claim_type": "MAGIC"}]'}},
        {"message": {"content": '[{"index": 0, "claim_type": "FACT"}, {"index": 1, "claim_type": "METHOD"}]'}}
    ]
    claims = [
        ExtractedClaim(claim_id="c1", text="text1", source_chunk_id="ch1", document_id="doc1"),
        ExtractedClaim(claim_id="c2", text="text2", source_chunk_id="ch1", document_id="doc1"),
    ]
    result = typer.type_claims(claims)
    assert len(result) == 2
    call_args = typer.client.chat.call_args_list[1][1]["messages"]
    assert "Invalid claim type 'MAGIC'" in call_args[-1]["content"]


def test_claim_typing_large_batch_split():
    typer = ClaimTyper()
    typer.client.chat = MagicMock()
    
    # 15 claims total -> batched into 10 and 5
    claims = [
        ExtractedClaim(claim_id=f"c{i}", text=f"text{i}", source_chunk_id="ch1", document_id="doc1")
        for i in range(15)
    ]
    
    # Batch 1 (10 items, index 0 to 9)
    resp1 = [{"index": i, "claim_type": "FACT"} for i in range(10)]
    # Batch 2 (5 items, index 0 to 4)
    resp2 = [{"index": i, "claim_type": "METHOD"} for i in range(5)]
    
    import json
    typer.client.chat.side_effect = [
        {"message": {"content": json.dumps(resp1)}},
        {"message": {"content": json.dumps(resp2)}}
    ]
    
    result = typer.type_claims(claims)
    assert len(result) == 15
    assert typer.client.chat.call_count == 2
    
    # verify mapping preserved correctly
    assert result[0].claim_id == "c0"
    assert result[0].claim_type == "FACT"
    assert result[9].claim_id == "c9"
    assert result[9].claim_type == "FACT"
    assert result[10].claim_id == "c10"
    assert result[10].claim_type == "METHOD"
    assert result[14].claim_id == "c14"
    assert result[14].claim_type == "METHOD"


def test_planning_missing_required_field():
    from app.performance_cache import aeris_cache
    orig_enabled = aeris_cache.enabled
    aeris_cache.enabled = False
    try:
        planner = RequirementPlanner()
        planner.client.chat = MagicMock()
        
        # Missing 'question' and 'requirements'
        bad_json = '{"question_type": "factual", "complexity": "simple", "reasoning_summary": "why"}'
        good_json = '{"question": "Q?", "question_type": "factual", "complexity": "simple", "requirements": [], "reasoning_summary": "why"}'
        
        planner.client.chat.side_effect = [
            {"message": {"content": bad_json}},
            {"message": {"content": good_json}}
        ]
        
        result = planner.plan("Q_unique_planning_test?")
        assert result.question == "Q_unique_planning_test?"
        call_args = planner.client.chat.call_args_list[1][1]["messages"]
        assert "Your previous response omitted required fields:" in call_args[-1]["content"]
    finally:
        aeris_cache.enabled = orig_enabled


def test_answer_gen_empty_evidence():
    ag = AnswerGenerator()
    ag.client.chat = MagicMock(return_value={"message": {"content": '{"answer": "A", "status": "SUPPORTED", "confidence": 0.9}'}})
    
    graph = ClaimEvidenceGraphBuilder("doc")
    ans = ag.generate("Q?", graph, [], None)
    
    assert ans.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert ans.confidence == 0.0
    assert not ans.is_answerable_from_evidence


def test_answer_gen_invalid_evidence_ids():
    ag = AnswerGenerator()
    ag.client.chat = MagicMock(return_value={"message": {"content": '{"answer": "A", "status": "SUPPORTED", "confidence": 0.9, "supporting_chunk_ids": ["ch1"]}'}})
    
    graph = ClaimEvidenceGraphBuilder("doc")
    # ch1 is not in graph
    ans = ag.generate("Q?", graph, [], None)
    
    assert ans.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert ans.confidence == 0.0
    assert not ans.supporting_chunk_ids


def test_controller_latency_instrumentation():
    planner_mock = MagicMock()
    planner_mock.plan.side_effect = lambda x: time.sleep(0.01) or MagicMock(requirements=[])
    
    controller = AERISController(
        planner=planner_mock,
        adaptive_retrieval_controller=MagicMock(),
        claim_extractor=MagicMock(),
        claim_normalizer=MagicMock(),
        claim_typer=MagicMock(),
        graph_builder_factory=lambda x: MagicMock(),
        graph_verifier=MagicMock(),
        contradiction_analyzer=MagicMock(),
        contradiction_integrator=MagicMock(),
        cross_lingual_analyzer=MagicMock(),
        cross_lingual_integrator=MagicMock(),
        calibrator=MagicMock(),
        selective_verification_executor=MagicMock(),
        answer_generator=MagicMock(),
    )
    
    req = ControllerRequest(document_id="doc1", question="Q1", config=ControllerConfig(
        enable_claim_verification=False,
        enable_contradiction_analysis=False,
        enable_cross_lingual_analysis=False,
        enable_calibration=False,
        enable_selective_verification=False,
        answer_generation_enabled=False
    ))
    
    res = controller.run(req)
    for stage in res.stages:
        if stage.status == "SKIPPED":
            assert stage.latency_seconds >= 0.0
        elif stage.status == "COMPLETED" and stage.stage != "COMPLETED":
            assert stage.latency_seconds > 0.0, f"Stage {stage.stage} has 0.0 latency"
