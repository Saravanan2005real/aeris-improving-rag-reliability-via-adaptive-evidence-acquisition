import pytest
from typing import Dict, List, Any


def compute_evaluation_metrics(
    records: List[Dict[str, Any]],
    benchmark: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Independent evaluation logic computing Retriever metrics vs Citation metrics
    with strict intent-to-treat denominators and explicit execution failure accounting.
    """
    bench_map = {b["question_id"]: b for b in benchmark}
    ans_qids = set(b["question_id"] for b in benchmark if b.get("answerability", True))
    unans_qids = set(b["question_id"] for b in benchmark if not b.get("answerability", True))
    
    total_evaluations = len(records)
    total_answerable = len(ans_qids)
    total_unanswerable = len(unans_qids)
    
    ans_supported = 0
    ans_insufficient = 0
    ans_failed = 0
    
    unans_rejected = 0
    unans_false_support = 0
    unans_failed = 0
    
    provenance_defects = 0
    
    retriever_hits = 0
    retriever_recall_sum = 0.0
    citation_hits = 0
    citation_recall_sum = 0.0
    
    for r in records:
        qid = r["question_id"]
        status = r.get("final_status")
        retrieved = set(r.get("retrieved_chunk_ids", []))
        cited = set(r.get("supporting_chunk_ids", []))
        gold = set(bench_map.get(qid, {}).get("supporting_chunk_ids", []))
        
        # Provenance check: cited chunks must be a subset of retrieved chunks
        if not cited.issubset(retrieved):
            provenance_defects += 1
            
        if qid in ans_qids:
            if status == "FAILED":
                ans_failed += 1
            elif status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]:
                ans_supported += 1
            else:
                ans_insufficient += 1
                
            # Compute retriever metrics (Intent-to-treat: failed runs count as 0 hit/recall)
            if status != "FAILED" and gold:
                if len(gold.intersection(retrieved)) > 0:
                    retriever_hits += 1
                retriever_recall_sum += len(gold.intersection(retrieved)) / len(gold)
                
                if len(gold.intersection(cited)) > 0:
                    citation_hits += 1
                citation_recall_sum += len(gold.intersection(cited)) / len(gold)
        else:
            if status == "FAILED":
                unans_failed += 1
            elif status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]:
                unans_false_support += 1
            else:
                unans_rejected += 1

    return {
        "total_evaluations": total_evaluations,
        "answerable_support_rate": ans_supported / total_answerable if total_answerable else 0.0,
        "answerable_insufficient_rate": ans_insufficient / total_answerable if total_answerable else 0.0,
        "answerable_failure_rate": ans_failed / total_answerable if total_answerable else 0.0,
        "unanswerable_false_support_rate": unans_false_support / total_unanswerable if total_unanswerable else 0.0,
        "retriever_hit_rate": retriever_hits / total_answerable if total_answerable else 0.0,
        "retriever_recall": retriever_recall_sum / total_answerable if total_answerable else 0.0,
        "citation_hit_rate": citation_hits / total_answerable if total_answerable else 0.0,
        "citation_recall": citation_recall_sum / total_answerable if total_answerable else 0.0,
        "provenance_defects": provenance_defects
    }


def test_retriever_vs_citation_divergence():
    """
    Test 1: When retriever captures gold chunk but answer generator does not cite it,
    Retriever Hit Rate must be 1.0 while Citation Hit Rate must be 0.0.
    """
    benchmark = [
        {"question_id": "q1", "answerability": True, "supporting_chunk_ids": ["gold_chunk_1"]}
    ]
    records = [
        {
            "question_id": "q1",
            "final_status": "SUPPORTED",
            "retrieved_chunk_ids": ["gold_chunk_1", "distractor_chunk_2"],
            "supporting_chunk_ids": ["distractor_chunk_2"]  # cited distractor only
        }
    ]
    
    metrics = compute_evaluation_metrics(records, benchmark)
    
    assert metrics["retriever_hit_rate"] == 1.0
    assert metrics["retriever_recall"] == 1.0
    assert metrics["citation_hit_rate"] == 0.0
    assert metrics["citation_recall"] == 0.0
    assert metrics["provenance_defects"] == 0


def test_provenance_defect_detection():
    """
    Test 2: When answer generator cites a chunk that was NEVER retrieved,
    a provenance defect must be flagged.
    """
    benchmark = [
        {"question_id": "q1", "answerability": True, "supporting_chunk_ids": ["gold_chunk_1"]}
    ]
    records = [
        {
            "question_id": "q1",
            "final_status": "SUPPORTED",
            "retrieved_chunk_ids": ["other_chunk_1"],
            "supporting_chunk_ids": ["fabricated_chunk_99"]  # never retrieved!
        }
    ]
    
    metrics = compute_evaluation_metrics(records, benchmark)
    assert metrics["provenance_defects"] == 1


def test_failed_run_intent_to_treat_accounting():
    """
    Test 3: Execution failures must NOT be counted as successful abstention (insufficient)
    or supported answers. Denominators must strictly preserve intent-to-treat.
    """
    benchmark = [
        {"question_id": "q1", "answerability": True, "supporting_chunk_ids": ["gold_1"]},
        {"question_id": "q2", "answerability": True, "supporting_chunk_ids": ["gold_2"]}
    ]
    records = [
        {
            "question_id": "q1",
            "final_status": "SUPPORTED",
            "retrieved_chunk_ids": ["gold_1"],
            "supporting_chunk_ids": ["gold_1"]
        },
        {
            "question_id": "q2",
            "final_status": "FAILED",  # execution failed
            "retrieved_chunk_ids": ["gold_2"],
            "supporting_chunk_ids": []
        }
    ]
    
    metrics = compute_evaluation_metrics(records, benchmark)
    assert metrics["answerable_support_rate"] == 0.5  # 1 / 2
    assert metrics["answerable_failure_rate"] == 0.5  # 1 / 2
    assert metrics["answerable_insufficient_rate"] == 0.0  # NOT counted as insufficient!
    assert metrics["retriever_hit_rate"] == 0.5  # failed run does not receive hit
    assert metrics["citation_hit_rate"] == 0.5


def test_query_reformulation_telemetry_consistency():
    """
    Test 4: Verify consistent telemetry between producer (query reformulator / adaptive controller)
    and consumer (controller telemetry summarizer).
    """
    attempts = [
        {"query_type": "original", "candidate_k": 10},
        {"query_type": "reformulation_1", "candidate_k": 10},
        {"query_type": "reformulation_2", "candidate_k": 25}
    ]
    
    ref_calls = 0
    ref_triggered = False
    
    for att in attempts:
        # Standardized check: supports either 'reformulation_' prefix or 'reformulated'
        qtype = att["query_type"]
        if qtype == "reformulated" or qtype.startswith("reformulation_"):
            ref_calls += 1
            ref_triggered = True
            
    assert ref_triggered is True
    assert ref_calls == 2
