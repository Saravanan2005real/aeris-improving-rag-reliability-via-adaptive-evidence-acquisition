import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.coverage.evidence_coverage import (
    EvidenceCoverageEstimator,
    EvidenceItem,
)
from app.planning.requirement_planner import (
    RequirementPlanner,
)
from app.retrieval.hybrid_retriever import (
    HybridRetriever,
)
from app.retrieval.reranker import (
    Reranker,
)


def main():

    if len(sys.argv) < 3:
        print(
            "Usage: "
            "python scripts/test_evidence_coverage.py "
            "<pdf_path> "
            "\"question\""
        )
        sys.exit(1)

    pdf_path = sys.argv[1]
    document_id = Path(pdf_path).stem

    question = " ".join(
        sys.argv[2:]
    ).strip()

    print("=" * 80)
    print("AERIS-RAG STEP 9 — EVIDENCE COVERAGE")
    print("=" * 80)

    # ---------------------------------------------------------
    # STEP 8
    # ---------------------------------------------------------

    print("\n[1] Planning requirements...")

    planner = RequirementPlanner()

    plan = planner.plan(
        question
    )

    print(
        f"Requirements generated: "
        f"{len(plan.requirements)}"
    )

    for requirement in plan.requirements:
        print(
            f"  {requirement.requirement_id}: "
            f"{requirement.description}"
        )

    # ---------------------------------------------------------
    # STEPS 6-7
    # ---------------------------------------------------------

    print("\n[2] Retrieving evidence...")

    hybrid = HybridRetriever()

    reranker = Reranker()

    requirement_evidence = {}
    total_unique_chunks = set()

    for requirement in plan.requirements:

        req_candidates = []

        for query in requirement.retrieval_queries[:2]:

            candidates = hybrid.retrieve(
                document_id=document_id,
                query=query,
                top_k=5,
                candidate_k=10,
            )

            reranked = reranker.rerank(
                query,
                candidates,
                top_k=3,
            )

            req_candidates.extend(
                reranked
            )

        unique = {}
        for item in req_candidates:
            if item.chunk_id not in unique:
                unique[item.chunk_id] = item
                total_unique_chunks.add(item.chunk_id)

        evidence_items = []
        for item in unique.values():
            evidence_items.append(
                EvidenceItem(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    text=item.text,
                    language=item.language,
                    pages=item.pages,
                    start_page=item.start_page,
                    end_page=item.end_page,
                    retrieval_score=item.retrieval_score,
                    rerank_score=item.rerank_score,
                )
            )

        requirement_evidence[requirement.requirement_id] = evidence_items

    print(
        f"Total unique evidence chunks retrieved: "
        f"{len(total_unique_chunks)}"
    )

    # ---------------------------------------------------------
    # STEP 9
    # ---------------------------------------------------------

    print("\n[3] Estimating evidence coverage...")

    estimator = EvidenceCoverageEstimator()

    result = estimator.estimate(
        question=question,
        requirements=plan.requirements,
        requirement_evidence=requirement_evidence,
    )

    # ---------------------------------------------------------
    # RESULTS
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("COVERAGE RESULTS")
    print("=" * 80)

    for coverage in result.requirement_coverages:

        print("\n" + "-" * 80)

        print(
            f"Requirement: "
            f"{coverage.requirement_id}"
        )

        print(
            f"Status: "
            f"{coverage.coverage_status}"
        )

        print(
            f"Coverage Score: "
            f"{coverage.coverage_score:.3f}"
        )

        print(
            f"Evidence Count: "
            f"{coverage.evidence_count}"
        )

        print(
            "Supporting Chunks:"
        )

        if coverage.supporting_chunk_ids:

            for chunk_id in (
                coverage.supporting_chunk_ids
            ):
                print(
                    f"  - {chunk_id}"
                )

        else:
            print("  None")

        print(
            f"Explanation: "
            f"{coverage.explanation}"
        )

    print("\n" + "=" * 80)

    print(
        f"Overall Coverage: "
        f"{result.overall_coverage:.3f}"
    )

    print(
        "Covered Requirements:",
        ", ".join(
            result.covered_requirements
        ) or "None",
    )

    print(
        "Partial Requirements:",
        ", ".join(
            result.partial_requirements
        ) or "None",
    )

    print(
        "Missing Requirements:",
        ", ".join(
            result.missing_requirements
        ) or "None",
    )

    print("=" * 80)

    print("\nSTATUS: SUCCESS")


if __name__ == "__main__":
    main()
