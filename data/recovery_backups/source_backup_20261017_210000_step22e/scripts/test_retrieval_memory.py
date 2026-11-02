import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.retrieval_memory import RetrievalMemory


def main():

    print("=" * 80)
    print("STEP 11A — RETRIEVAL MEMORY TEST")
    print("=" * 80)

    document_id = "test_document"
    question = "How does the retriever work?"

    memory = RetrievalMemory(
        document_id=document_id,
        question=question,
    )

    print("\nMemory initialized.")
    print(f"Document : {document_id}")
    print(f"Question : {question}")

    # --------------------------------------------------------------
    # RECORD QUERY 1
    # --------------------------------------------------------------

    memory.record_query(
        query="What retrieval mechanism is used by the retriever?",
        query_type="original",
        requirement_id="R1",
        candidate_k=10,
        rerank_top_k=5,
        retrieved_chunk_ids=[
            "test_document_p007_c017",
            "test_document_p001_c001",
        ],
        coverage_status="UNSUPPORTED",
        coverage_score=0.0,
        successful=False,
    )

    # --------------------------------------------------------------
    # RECORD QUERY 2
    # --------------------------------------------------------------

    memory.record_query(
        query="What retrieval mechanism is used by the retriever?",
        query_type="original",
        requirement_id="R1",
        candidate_k=25,
        rerank_top_k=5,
        retrieved_chunk_ids=[
            "test_document_p002_c004",
            "test_document_p007_c017",
        ],
        coverage_status="SUPPORTED",
        coverage_score=1.0,
        successful=True,
    )

    # --------------------------------------------------------------
    # RECORD EVIDENCE
    # --------------------------------------------------------------

    memory.record_evidence(
        chunk_id="test_document_p002_c004",
        document_id=document_id,
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=25,
        coverage_score=1.0,
        coverage_status="SUPPORTED",
    )

    memory.record_evidence(
        chunk_id="test_document_p007_c017",
        document_id=document_id,
        requirement_id="R1",
        source_query="What retrieval mechanism is used by the retriever?",
        retrieval_depth=10,
        coverage_score=0.2,
        coverage_status="UNSUPPORTED",
    )

    # --------------------------------------------------------------
    # TEST QUERY LOOKUP
    # --------------------------------------------------------------

    print("\n" + "-" * 80)
    print("QUERY LOOKUP")
    print("-" * 80)

    query = "What retrieval mechanism is used by the retriever?"

    print(f"\nHas query?")
    print(
        memory.has_query(
            query=query,
            requirement_id="R1",
        )
    )

    # --------------------------------------------------------------
    # TEST EVIDENCE LOOKUP
    # --------------------------------------------------------------

    print("\n" + "-" * 80)
    print("EVIDENCE LOOKUP")
    print("-" * 80)

    chunk_id = "test_document_p002_c004"

    evidence = memory.get_evidence(chunk_id)

    print(f"\nChunk: {chunk_id}")

    if evidence:
        print(f"Requirements     : {evidence.requirement_ids}")
        print(f"Source queries   : {evidence.source_queries}")
        print(f"Retrieval depths : {evidence.retrieval_depths}")
        print(f"Best score       : {evidence.best_coverage_score}")
        print(f"Status           : {evidence.coverage_status}")

    # --------------------------------------------------------------
    # TEST DUPLICATE EVIDENCE MERGING
    # --------------------------------------------------------------

    print("\n" + "-" * 80)
    print("DUPLICATE EVIDENCE MERGING")
    print("-" * 80)

    memory.record_evidence(
        chunk_id="test_document_p002_c004",
        document_id=document_id,
        requirement_id="R2",
        source_query="How does the retriever rank relevant evidence?",
        retrieval_depth=25,
        coverage_score=0.8,
        coverage_status="PARTIAL",
    )

    evidence = memory.get_evidence(
        "test_document_p002_c004"
    )

    print("\nAfter second evidence observation:")

    print(f"Requirements     : {evidence.requirement_ids}")
    print(f"Source queries   : {evidence.source_queries}")
    print(f"Retrieval depths : {evidence.retrieval_depths}")
    print(f"Best score       : {evidence.best_coverage_score}")
    print(f"Status           : {evidence.coverage_status}")

    # --------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------

    print("\n" + "=" * 80)
    print("MEMORY SUMMARY")
    print("=" * 80)

    print(f"\nQuery count    : {memory.query_count()}")
    print(f"Evidence count : {memory.evidence_count()}")

    print("\nAll known chunks:")

    for chunk_id in memory.get_all_chunk_ids():
        print(f"  - {chunk_id}")

    # --------------------------------------------------------------
    # FINAL STATE
    # --------------------------------------------------------------

    print("\n" + "=" * 80)
    print("FINAL MEMORY STATE")
    print("=" * 80)

    state = memory.get_state()

    print(
        state.model_dump_json(
            indent=2
        )
    )

    print("\n" + "=" * 80)
    print("STEP 11A TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
