"""
Step 22D Regression Test: Workstream 3 - Retrieval-Memory Evaluation Meaningful

Verifies:
1. Valid cache hit under intended usage (scoped memory cross-request within session/doc).
2. Key dimension compatibility: candidate depth incompatibility prevents invalid cache hit.
3. Cross-document and cross-session isolation (no leakage between docs or users/sessions).
4. Invalidation mechanisms (per-document and global clear).
5. Telemetry correctness: lookups, hits, misses, skips.
"""

import pytest
from app.retrieval_memory.memory import RetrievalMemory, RetrievalMemoryRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    RetrievalMemoryRegistry.clear()
    yield
    RetrievalMemoryRegistry.clear()


def test_valid_cache_hit_under_intended_usage():
    """
    Demonstrates at least one valid cache hit under intended usage:
    - Same session, same document, same query, compatible candidate depth.
    """
    memory = RetrievalMemoryRegistry.get_scoped_memory(
        document_id="doc_audit_101",
        session_id="session_auditor_A",
        question="What is the baseline BLEU?",
    )

    # Initial query recording
    memory.record_query(
        query="baseline BLEU score transformer",
        query_type="original",
        requirement_id="req_bleu",
        candidate_k=10,
        rerank_top_k=5,
        retrieved_chunk_ids=["chunk_1", "chunk_2"],
        successful=True,
    )

    # Subsequent lookup for the exact same query and candidate_k
    has_attempt = memory.has_query_attempt(
        query="baseline BLEU score transformer",
        requirement_id="req_bleu",
        candidate_k=10,
        document_id="doc_audit_101",
    )

    assert has_attempt is True
    assert memory.lookup_count == 1
    assert memory.hit_count == 1
    assert memory.miss_count == 0


def test_candidate_depth_incompatibility_prevents_cache_hit():
    """
    When deeper search is requested (e.g. candidate_k=25),
    a cached shallow entry (candidate_k=10) cannot satisfy the depth requirement.
    """
    memory = RetrievalMemoryRegistry.get_scoped_memory(
        document_id="doc_audit_101",
        session_id="session_auditor_A",
    )

    memory.record_query(
        query="adaptive candidate depth",
        candidate_k=10,
        retrieved_chunk_ids=["chunk_1"],
    )

    # Request candidate_k=25 (deeper than cached 10)
    has_attempt = memory.has_query_attempt(
        query="adaptive candidate depth",
        candidate_k=25,
        document_id="doc_audit_101",
    )

    assert has_attempt is False
    assert memory.lookup_count == 1
    assert memory.hit_count == 0
    assert memory.miss_count == 1


def test_no_leakage_between_isolated_sessions_and_documents():
    """
    Verifies that cache entries never leak between:
    - Different documents within the same session.
    - Different sessions/users for the same document.
    """
    # Session A records query on docA
    mem_A = RetrievalMemoryRegistry.get_scoped_memory(
        document_id="docA",
        session_id="user_alice",
    )
    mem_A.record_query(
        query="confidential patent data",
        candidate_k=10,
        retrieved_chunk_ids=["chunk_secret_1"],
    )

    # 1. Different document in Session A: no leakage
    has_doc_b = mem_A.has_query_attempt(
        query="confidential patent data",
        candidate_k=10,
        document_id="docB",
    )
    assert has_doc_b is False

    # 2. Same document in Session B (Bob): isolated memory instance
    mem_B = RetrievalMemoryRegistry.get_scoped_memory(
        document_id="docA",
        session_id="user_bob",
    )
    has_bob = mem_B.has_query_attempt(
        query="confidential patent data",
        candidate_k=10,
        document_id="docA",
    )
    assert has_bob is False
    assert mem_B.hit_count == 0
    assert mem_B.miss_count == 1


def test_invalidation_lifecycle():
    """
    Verifies that invalidating a document or session clears memory safely.
    """
    memory = RetrievalMemoryRegistry.get_scoped_memory(
        document_id="doc_temp",
        session_id="sess_temp",
    )
    memory.record_query(
        query="temporary facts",
        candidate_k=10,
        retrieved_chunk_ids=["c1"],
    )

    assert memory.has_query_attempt("temporary facts", candidate_k=10, document_id="doc_temp") is True

    # Invalidate document entries
    memory.invalidate_for_document("doc_temp")

    # Now it must be a miss
    assert memory.has_query_attempt("temporary facts", candidate_k=10, document_id="doc_temp") is False


def test_telemetry_accounting_hits_misses_skips():
    """
    Validates complete telemetry counter tracking:
    - lookups = hits + misses
    - skips tracked explicitly
    """
    memory = RetrievalMemory(document_id="doc1", session_id="sess1")

    # Miss 1
    assert memory.has_query_attempt("query A", candidate_k=10, document_id="doc1") is False
    # Record query A
    memory.record_query("query A", candidate_k=10)

    # Hit 1
    assert memory.has_query_attempt("query A", candidate_k=10, document_id="doc1") is True
    # Hit 2
    assert memory.has_query_attempt("query A", candidate_k=5, document_id="doc1") is True
    # Miss 2 (depth 20 > 10)
    assert memory.has_query_attempt("query A", candidate_k=20, document_id="doc1") is False

    memory.record_skip("skip reason")

    assert memory.lookup_count == 4
    assert memory.hit_count == 2
    assert memory.miss_count == 2
    assert memory.skip_count == 1
