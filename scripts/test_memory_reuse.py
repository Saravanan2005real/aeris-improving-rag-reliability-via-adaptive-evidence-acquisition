import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

from app.ingestion.pdf_loader import load_pdf
from app.planning.requirement_planner import RequirementPlanner
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.coverage.evidence_coverage import EvidenceCoverageEstimator
from app.adaptive_retrieval.controller import AdaptiveRetrievalController
from app.retrieval_memory.memory import RetrievalMemory

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_memory_reuse.py <pdf_path> \"<question>\"")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    question = sys.argv[2]
    document_id = pdf_path.stem

    print("=" * 80)
    print("STEP 11C-4 — MEMORY REUSE TEST")
    print("=" * 80)

    document = load_pdf(str(pdf_path))
    planner = RequirementPlanner()
    plan = planner.plan(question)

    hybrid = HybridRetriever()
    reranker = Reranker()
    coverage_estimator = EvidenceCoverageEstimator()

    memory = RetrievalMemory(document_id=document_id, question=question)

    controller = AdaptiveRetrievalController(
        hybrid_retriever=hybrid,
        reranker=reranker,
        coverage_estimator=coverage_estimator,
        candidate_k_schedule=[10, 25, 50],
        rerank_top_k=5,
        max_attempts_per_query=3,
        support_threshold=0.70,
        memory=memory,
    )

    print("\n--- RUN 1 ---")
    for req in plan.requirements:
        print(f"\nProcessing: {req.requirement_id} - {req.description}")
        res1 = controller.retrieve_for_requirement(document_id, question, req)
        print(f"Attempts executed: {len(res1.attempts)}")
        for a in res1.attempts:
            print(f"  [Run 1] {a.query_type} (k={a.candidate_k}) -> {a.coverage_status}")

    print("\n" + "-" * 80)
    print("--- RUN 2 (SAME MEMORY) ---")
    for req in plan.requirements:
        print(f"\nProcessing: {req.requirement_id} - {req.description}")
        res2 = controller.retrieve_for_requirement(document_id, question, req)
        print(f"Attempts executed: {len(res2.attempts)}")
        for a in res2.attempts:
            print(f"  [Run 2] {a.query_type} (k={a.candidate_k}) -> {a.coverage_status}")
            
    print("\n" + "=" * 80)
    print("MEMORY REUSE TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
