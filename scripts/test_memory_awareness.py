import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.retrieval_memory.memory import RetrievalMemory


def main():
    print("=" * 80)
    print("STEP 11C — MEMORY AWARENESS TEST")
    print("=" * 80)

    memory = RetrievalMemory(
        document_id="test_document",
        question="How does the retriever work?",
    )

    # ------------------------------------------------------------------
    # 1. Record retrieval attempts
    # ------------------------------------------------------------------

    memory.record_query(
        query="What retrieval mechanism is used by the retriever?",
        query_type="original",
        requirement_id="R1",
        candidate_k=10,
        rerank_top_k=5,
        retrieved_chunk_ids=[
            "test_document_p001_c001",
            "test_document_p002_c004",
        ],
        coverage_status="UNSUPPORTED",
        coverage_score=0.0,
        successful=False,
    )

    memory.record_query(
        query="What retrieval mechanism is used by the retriever?",
        query_type="original",
        requirement_id="R1",
        candidate_k=25,
        rerank_top_k=5,
        retrieved_chunk_ids=[
            "test_document_p001_c001",
            "test_document_p002_c004",
            "test_document_p003_c006",
        ],
        coverage_status="SUPPORTED",
        coverage_score=1.0,
        successful=True,
    )

    # ------------------------------------------------------------------
    # 2. Record evidence
    # ------------------------------------------------------------------

    memory.record_evidence(
        chunk_id="test_document_p001_c001",
        document_id="test_document",
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=10,
        coverage_score=0.0,
        coverage_status="UNSUPPORTED",
    )

    memory.record_evidence(
        chunk_id="test_document_p002_c004",
        document_id="test_document",
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=10,
        coverage_score=0.0,
        coverage_status="UNSUPPORTED",
    )

    memory.record_evidence(
        chunk_id="test_document_p001_c001",
        document_id="test_document",
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=25,
        coverage_score=1.0,
        coverage_status="SUPPORTED",
    )

    memory.record_evidence(
        chunk_id="test_document_p002_c004",
        document_id="test_document",
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=25,
        coverage_score=1.0,
        coverage_status="SUPPORTED",
    )

    memory.record_evidence(
        chunk_id="test_document_p003_c006",
        document_id="test_document",
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=25,
        coverage_score=1.0,
        coverage_status="SUPPORTED",
    )

    # ------------------------------------------------------------------
    # 3. Query awareness
    # ------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("QUERY AWARENESS")
    print("-" * 80)

    query = "What retrieval mechanism is used by the retriever?"

    print(
        "Has query R1?",
        memory.has_query(query, requirement_id="R1"),
    )

    print(
        "Has query R2?",
        memory.has_query(query, requirement_id="R2"),
    )

    print(
        "Total query records:",
        memory.query_count(),
    )

    print(
        "R1 query records:",
        len(memory.get_queries(requirement_id="R1")),
    )

    print("\n" + "-" * 80)
    print("RETRIEVAL ATTEMPT AWARENESS")
    print("-" * 80)

    print(
        "R1 / k=10 already attempted?",
        memory.has_query_attempt(
            query=query,
            requirement_id="R1",
            candidate_k=10,
        ),
    )

    print(
        "R1 / k=25 already attempted?",
        memory.has_query_attempt(
            query=query,
            requirement_id="R1",
            candidate_k=25,
        ),
    )

    print(
        "R1 / k=50 already attempted?",
        memory.has_query_attempt(
            query=query,
            requirement_id="R1",
            candidate_k=50,
        ),
    )

    print(
        "R2 / k=10 already attempted?",
        memory.has_query_attempt(
            query=query,
            requirement_id="R2",
            candidate_k=10,
        ),
    )

    # ------------------------------------------------------------------
    # 4. Evidence awareness
    # ------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("EVIDENCE AWARENESS")
    print("-" * 80)

    known_chunk = "test_document_p002_c004"
    unknown_chunk = "test_document_p999_c999"

    print(
        "Known evidence?",
        memory.has_evidence(known_chunk),
    )

    print(
        "Unknown evidence?",
        memory.has_evidence(unknown_chunk),
    )

    print(
        "All known chunk IDs:",
        memory.get_all_chunk_ids(),
    )

    print(
        "Evidence count:",
        memory.evidence_count(),
    )

    # ------------------------------------------------------------------
    # 5. Duplicate evidence awareness
    # ------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("DUPLICATE EVIDENCE MERGING")
    print("-" * 80)

    evidence = memory.get_evidence(
        "test_document_p002_c004"
    )

    print(
        "Chunk:",
        evidence.chunk_id,
    )

    print(
        "Requirements:",
        evidence.requirement_ids,
    )

    print(
        "Source queries:",
        evidence.source_queries,
    )

    print(
        "Retrieval depths:",
        evidence.retrieval_depths,
    )

    print(
        "Best coverage score:",
        evidence.best_coverage_score,
    )

    print(
        "Coverage status:",
        evidence.coverage_status,
    )

    # ------------------------------------------------------------------
    # 6. Final state
    # ------------------------------------------------------------------

    print("\n" + "-" * 80)
    print("FINAL MEMORY STATE")
    print("-" * 80)

    print(
        memory.get_state().model_dump_json(
            indent=2
        )
    )

    print("\n" + "=" * 80)
    print("STEP 11C TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
