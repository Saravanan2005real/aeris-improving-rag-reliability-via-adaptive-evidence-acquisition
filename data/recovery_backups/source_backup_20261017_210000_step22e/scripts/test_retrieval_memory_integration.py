import os
import sys

# Add project root to sys.path
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
        print(
            "Usage:\n"
            "python scripts/test_retrieval_memory_integration.py "
            "<pdf_path> \"<question>\""
        )
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    question = sys.argv[2]

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    document_id = pdf_path.stem

    print("=" * 80)
    print("STEP 11B — RETRIEVAL MEMORY + ADAPTIVE CONTROLLER")
    print("=" * 80)

    document = load_pdf(str(pdf_path))

    planner = RequirementPlanner()
    plan = planner.plan(question)

    hybrid = HybridRetriever()
    reranker = Reranker()
    coverage_estimator = EvidenceCoverageEstimator()

    memory = RetrievalMemory(
        document_id=document_id,
        question=question,
    )

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

    print("\nRequirements:")

    for requirement in plan.requirements:
        print(
            f"  {requirement.requirement_id}: "
            f"{requirement.description}"
        )

    print("\n" + "=" * 80)
    print("ADAPTIVE RETRIEVAL")
    print("=" * 80)

    for requirement in plan.requirements:

        print("\n" + "-" * 80)
        print(
            f"{requirement.requirement_id}: "
            f"{requirement.description}"
        )
        print("-" * 80)

        result = controller.retrieve_for_requirement(
            document_id=document_id,
            question=question,
            requirement=requirement,
        )

        for attempt in result.attempts:

            print(
                f"\nAttempt {attempt.attempt_number}"
            )

            print(
                f"  query        : "
                f"[{attempt.query_type}] "
                f"{attempt.query}"
            )

            print(
                f"  candidate_k  : "
                f"{attempt.candidate_k}"
            )

            print(
                f"  coverage     : "
                f"{attempt.coverage_status}"
            )

            print(
                f"  score        : "
                f"{attempt.coverage_score:.4f}"
            )

    print("\n" + "=" * 80)
    print("MEMORY INTEGRATION SUMMARY")
    print("=" * 80)

    print(
        f"\nQueries remembered   : "
        f"{memory.query_count()}"
    )

    print(
        f"Evidence remembered : "
        f"{memory.evidence_count()}"
    )

    print("\nQuery history:")

    for item in memory.get_queries():

        print(
            f"\n  [{item.query_type}] "
            f"{item.query}"
        )

        print(
            f"    Requirement : "
            f"{item.requirement_id}"
        )

        print(
            f"    candidate_k : "
            f"{item.candidate_k}"
        )

        print(
            f"    status      : "
            f"{item.coverage_status}"
        )

        print(
            f"    score       : "
            f"{item.coverage_score}"
        )

    print("\nEvidence history:")

    for item in memory.state.evidence_history:

        print(
            f"\n  {item.chunk_id}"
        )

        print(
            f"    Requirements : "
            f"{item.requirement_ids}"
        )

        print(
            f"    Queries      : "
            f"{item.source_queries}"
        )

        print(
            f"    Depths       : "
            f"{item.retrieval_depths}"
        )

        print(
            f"    Best score   : "
            f"{item.best_coverage_score}"
        )

        print(
            f"    Status       : "
            f"{item.coverage_status}"
        )

    print("\n" + "=" * 80)
    print("STEP 11B TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
