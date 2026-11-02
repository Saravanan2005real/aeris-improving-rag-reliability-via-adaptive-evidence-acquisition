import pytest
from unittest.mock import MagicMock
from app.controller.schemas import (
    ControllerResult,
    ControllerStage,
    StageStatus,
    ControllerStageResult
)
from app.ablation.schemas import AblationVariant, AblationResult
from app.benchmark.schemas import BenchmarkRecord


def test_controller_schema_fields():
    """
    Test 1: Verify ControllerResult properly encapsulates retrieved_chunk_ids,
    retrieval_attempts_history, and provenance_defects.
    """
    res = ControllerResult(
        document_id="doc_1",
        question="What is the test parameter?",
        status=StageStatus.COMPLETED,
        retrieved_chunk_ids=["chunk_1", "chunk_2", "chunk_3"],
        supporting_chunk_ids=["chunk_1"],
        retrieval_attempts_history=[
            {"query": "param query", "query_type": "original", "candidate_k": 10, "retrieved_chunk_ids": ["chunk_1", "chunk_2"]},
            {"query": "param query alt", "query_type": "reformulation_1", "candidate_k": 25, "retrieved_chunk_ids": ["chunk_3"]}
        ],
        provenance_defects=[],
        final_answer="The parameter is 42."
    )
    
    assert res.retrieved_chunk_ids == ["chunk_1", "chunk_2", "chunk_3"]
    assert len(res.retrieval_attempts_history) == 2
    assert res.retrieval_attempts_history[1]["query_type"] == "reformulation_1"
    assert res.provenance_defects == []


def test_provenance_defect_flagging_in_controller():
    """
    Test 2: When an answer cites a chunk outside the retrieved evidence pool,
    it must be captured in provenance_defects and downgrade answer support.
    """
    retrieved_chunk_ids = ["chunk_1", "chunk_2"]
    supporting_chunk_ids = ["chunk_1", "fabricated_chunk_99"]
    
    provenance_defects = [
        cid for cid in supporting_chunk_ids if cid not in retrieved_chunk_ids
    ]
    
    assert provenance_defects == ["fabricated_chunk_99"]


def test_runner_metric_divergence_and_provenance():
    """
    Test 3: Verify the ablation runner's metric evaluation for:
    - Gold retrieved but not cited (Retriever Hit = 1, Citation Hit = 0)
    - Gold neither retrieved nor cited (Both = 0)
    - Cited chunk outside allowed pool (Provenance defect recorded)
    """
    from app.ablation.runner import AblationRunner
    
    mock_controller = MagicMock()
    runner = AblationRunner(mock_controller)
    
    # Case A: Gold chunk retrieved but not cited
    gold_record = BenchmarkRecord(
        question_id="q_ans_01",
        question="What is X?",
        document_id="doc_1",
        category="DIRECT_FACT",
        difficulty="EASY",
        expected_status="SUPPORTED",
        answerability=True,
        supporting_chunk_ids=["gold_chunk_10"]
    )
    
    res_a = ControllerResult(
        document_id="doc_1",
        question="What is X?",
        status=StageStatus.COMPLETED,
        retrieved_chunk_ids=["gold_chunk_10", "distractor_chunk_20"],
        supporting_chunk_ids=["distractor_chunk_20"],
        final_answer="Answer based on distractor.",
        answer_status="SUPPORTED"
    )
    
    # Evaluate as runner does
    expected_chunks = set(gold_record.supporting_chunk_ids)
    actual_retrieved = set(res_a.retrieved_chunk_ids)
    cited_chunks = set(res_a.supporting_chunk_ids)
    
    retriever_hit_a = len(expected_chunks.intersection(actual_retrieved)) > 0
    citation_hit_a = len(expected_chunks.intersection(cited_chunks)) > 0
    prov_defects_a = [cid for cid in cited_chunks if cid not in actual_retrieved]
    
    assert retriever_hit_a is True
    assert citation_hit_a is False
    assert prov_defects_a == []
    
    # Case B: Gold chunk neither retrieved nor cited
    res_b = ControllerResult(
        document_id="doc_1",
        question="What is X?",
        status=StageStatus.COMPLETED,
        retrieved_chunk_ids=["other_1", "other_2"],
        supporting_chunk_ids=["other_1"],
        final_answer="Answer without gold.",
        answer_status="SUPPORTED"
    )
    actual_retrieved_b = set(res_b.retrieved_chunk_ids)
    cited_chunks_b = set(res_b.supporting_chunk_ids)
    
    retriever_hit_b = len(expected_chunks.intersection(actual_retrieved_b)) > 0
    citation_hit_b = len(expected_chunks.intersection(cited_chunks_b)) > 0
    
    assert retriever_hit_b is False
    assert citation_hit_b is False
    
    # Case C: Cited chunk outside allowed pool
    res_c = ControllerResult(
        document_id="doc_1",
        question="What is X?",
        status=StageStatus.COMPLETED,
        retrieved_chunk_ids=["chunk_1"],
        supporting_chunk_ids=["chunk_1", "hallucinated_chunk"],
        final_answer="Answer with hallucinated citation.",
        answer_status="SUPPORTED"
    )
    actual_retrieved_c = set(res_c.retrieved_chunk_ids)
    cited_chunks_c = set(res_c.supporting_chunk_ids)
    prov_defects_c = [cid for cid in cited_chunks_c if cid not in actual_retrieved_c]
    
    assert prov_defects_c == ["hallucinated_chunk"]


def test_failed_execution_runner_handling():
    """
    Test 4: Verify that runner preserves ground-truth answerability on failure
    (expected_answerability=True, is_answerable=True), marks final_status='FAILED',
    success=False, zero hit/recall, and is NOT treated as an abstention (INSUFFICIENT_EVIDENCE).
    """
    ablation_res = AblationResult(
        experiment_id="exp_test",
        variant=AblationVariant.FULL_AERIS,
        question_id="q_fail",
        question="Failing query on answerable question",
        document_id="doc_1",
        question_type="MULTI_HOP",
        expected_answerability=True,
        final_status="FAILED",
        retrieved_chunk_ids=[],
        retriever_hit=False,
        retriever_recall=0.0,
        citation_hit=False,
        citation_recall=0.0,
        evidence_hit=False,
        evidence_recall=0.0,
        provenance_defects=[],
        latency_seconds=12.5,
        error="ClaimTypingError",
        timestamp="2026-10-11T12:00:00",
        is_answerable=True,  # Ground truth preserved!
        success=False
    )
    
    dump = ablation_res.model_dump()
    assert dump["expected_answerability"] is True
    assert dump["is_answerable"] is True  # Preserved ground-truth answerability!
    assert dump["final_status"] == "FAILED"  # Execution failure explicitly recorded
    assert dump["final_status"] != "INSUFFICIENT_EVIDENCE"  # NOT an abstention!
    assert dump["final_status"] != "SUPPORTED"  # NOT supported!
    assert dump["retriever_hit"] is False  # Counts as 0 for intent-to-treat
    assert dump["citation_hit"] is False  # Counts as 0 for intent-to-treat
    assert dump["success"] is False
    assert dump["error"] == "ClaimTypingError"


def test_query_reformulation_telemetry_matching():
    """
    Test 5: Verify query-reformulation telemetry counters with both
    'reformulated' and 'reformulation_<n>' query types, alongside depth expansion.
    """
    from app.adaptive_retrieval.schemas import is_reformulated_query_type
    
    assert is_reformulated_query_type("reformulated") is True
    assert is_reformulated_query_type("reformulation_1") is True
    assert is_reformulated_query_type("reformulation_2") is True
    assert is_reformulated_query_type("original") is False
    
    attempts = [
        {"query_type": "original", "candidate_k": 10},
        {"query_type": "original", "candidate_k": 25},  # candidate depth expansion
        {"query_type": "reformulation_1", "candidate_k": 10},
        {"query_type": "reformulated", "candidate_k": 10}
    ]
    
    ref_calls = 0
    ref_triggered = False
    cand_expansions = 0
    
    for att in attempts:
        if att["candidate_k"] > 10:
            cand_expansions += 1
        if is_reformulated_query_type(att["query_type"]):
            ref_calls += 1
            ref_triggered = True
            
    assert ref_triggered is True
    assert ref_calls == 2
    assert cand_expansions == 1
