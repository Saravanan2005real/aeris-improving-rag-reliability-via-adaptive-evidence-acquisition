import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pdf_loader import load_pdf
from app.planning.requirement_planner import RequirementPlanner
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.coverage.evidence_coverage import EvidenceCoverageEstimator
from app.adaptive_retrieval.controller import AdaptiveRetrievalController


def main():
    if len(sys.argv) < 3:
        print(
            "Usage:\n"
            "python scripts/test_adaptive_retrieval.py "
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
    print("STEP 10 — ADAPTIVE MISSING-EVIDENCE RETRIEVAL TEST")
    print("=" * 80)

    print(f"\nDocument : {document_id}")
    print(f"Question : {question}")

    # ------------------------------------------------------------------
    # 1. Load document
    # ------------------------------------------------------------------

    document = load_pdf(str(pdf_path))

    print(f"Pages    : {len(document.pages)}")

    # ------------------------------------------------------------------
    # 2. Requirement planning
    # ------------------------------------------------------------------

    planner = RequirementPlanner()

    plan = planner.plan(question)

    print("\n" + "-" * 80)
    print("INFORMATION REQUIREMENTS")
    print("-" * 80)

    for requirement in plan.requirements:
        print(
            f"\n{requirement.requirement_id}: "
            f"{requirement.description}"
        )

        print(
            f"Type              : "
            f"{requirement.requirement_type}"
        )

        print(
            f"Expected evidence : "
            f"{requirement.expected_evidence_type}"
        )

        print("Retrieval queries:")

        for query in requirement.retrieval_queries:
            print(f"  - {query}")

    # ------------------------------------------------------------------
    # 3. Retrieval components
    # ------------------------------------------------------------------

    hybrid = HybridRetriever()

    reranker = Reranker()

    coverage_estimator = EvidenceCoverageEstimator()

    # ------------------------------------------------------------------
    # 4. Adaptive controller
    # ------------------------------------------------------------------

    controller = AdaptiveRetrievalController(
        hybrid_retriever=hybrid,
        reranker=reranker,
        coverage_estimator=coverage_estimator,

        # Research baseline:
        # progressively expand the candidate pool.
        candidate_k_schedule=[10, 25, 50],

        # Keep Step 7 behavior unchanged.
        rerank_top_k=5,

        # One attempt per candidate-k level.
        max_attempts_per_query=3,

        # Same supported threshold used by Step 9.
        support_threshold=0.70,
    )

    # ------------------------------------------------------------------
    # 5. Run adaptive retrieval for every requirement
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("ADAPTIVE RETRIEVAL")
    print("=" * 80)

    results = []

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

        results.append(result)

        # --------------------------------------------------------------
        # Print every adaptive attempt
        # --------------------------------------------------------------

        for attempt in result.attempts:

            print(
                f"\nAttempt {attempt.attempt_number}"
            )

            print(
                f"  query            : "
                f"[{attempt.query_type}] {attempt.query}"
            )

            print(
                f"  candidate_k      : "
                f"{attempt.candidate_k}"
            )

            print(
                f"  rerank_top_k     : "
                f"{attempt.rerank_top_k}"
            )

            print(
                f"  retrieved chunks : "
                f"{len(attempt.retrieved_chunk_ids)}"
            )

            print(
                f"  new chunks       : "
                f"{len(attempt.new_chunk_ids)}"
            )

            print(
                f"  coverage status   : "
                f"{attempt.coverage_status}"
            )

            print(
                f"  coverage score    : "
                f"{attempt.coverage_score:.4f}"
            )

            if attempt.stopped:
                print(
                    f"  STOP              : "
                    f"{attempt.stop_reason}"
                )
            else:
                print(
                    "  ACTION            : "
                    "Expand retrieval"
                )

        # --------------------------------------------------------------
        # Final result
        # --------------------------------------------------------------

        print("\nFINAL RESULT")

        print(
            f"  Final candidate_k : "
            f"{result.final_candidate_k}"
        )

        print(
            f"  Unique chunks     : "
            f"{result.total_unique_chunks}"
        )

        print(
            f"  Final status      : "
            f"{result.final_coverage_status}"
        )

        print(
            f"  Final score       : "
            f"{result.final_coverage_score:.4f}"
        )

        print(
            f"  Success           : "
            f"{result.success}"
        )

        print(
            f"  Stop reason       : "
            f"{result.stop_reason}"
        )

        print("\nAll acquired chunks:")

        for chunk_id in result.all_chunk_ids:
            print(f"  - {chunk_id}")

    # ------------------------------------------------------------------
    # 6. Overall experiment summary
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("STEP 10 EXPERIMENT SUMMARY")
    print("=" * 80)

    successful = sum(
        1 for result in results
        if result.success
    )

    print(
        f"\nRequirements          : "
        f"{len(results)}"
    )

    print(
        f"Successfully supported: "
        f"{successful}/{len(results)}"
    )

    print("\nRequirement outcomes:")

    for result in results:

        print(
            f"  {result.requirement_id} | "
            f"status={result.final_coverage_status} | "
            f"score={result.final_coverage_score:.4f} | "
            f"final_k={result.final_candidate_k} | "
            f"chunks={result.total_unique_chunks}"
        )

    print("\n" + "=" * 80)
    print("STEP 10 TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
