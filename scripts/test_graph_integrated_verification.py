import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import ClaimType, EdgeType
from app.verification.claim_verifier import ClaimVerifier
from app.verification.graph_verifier import GraphClaimVerifier


DOCUMENT_ID = "test_document"


def build_supporting_graph():
    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID,
        similarity_threshold=0.60,
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses BM25 for sparse retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    graph.add_evidence(
        chunk_id="chunk1",
        text="AERIS combines dense and sparse retrieval methods.",
    )

    graph.add_evidence(
        chunk_id="chunk2",
        text="The sparse retrieval component uses BM25.",
    )

    graph.auto_link_claims_to_evidence()

    return graph


def build_contradictory_graph():
    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID,
        similarity_threshold=0.50,
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses BM25 for sparse retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    graph.add_evidence(
        chunk_id="chunk1",
        text="AERIS uses sparse retrieval.",
    )

    graph.add_evidence(
        chunk_id="chunk2",
        text=(
            "AERIS does not use BM25 for sparse retrieval. "
            "Its sparse retrieval component uses another ranking method."
        ),
    )

    graph.auto_link_claims_to_evidence()

    return graph


def test_supporting_graph():
    print("\n" + "-" * 80)
    print("TEST 1 — GRAPH-INTEGRATED SUPPORT")
    print("-" * 80)

    graph = build_supporting_graph()

    verifier = GraphClaimVerifier(
        ClaimVerifier()
    )

    result = verifier.verify_claim(
        graph=graph,
        claim_id="c1",
    )

    print(f"Label: {result.label}")
    print(
        f"Verification confidence: "
        f"{result.verification_confidence:.3f}"
    )
    print(
        f"Evidence count: "
        f"{result.evidence_count}"
    )
    print(
        f"Evidence chunks: "
        f"{result.evidence_chunk_ids}"
    )
    print(f"Rationale: {result.rationale}")

    assert result.label == EdgeType.SUPPORTS
    assert result.evidence_count == 2
    assert len(result.evidence_chunk_ids) == 2
    assert result.verification_confidence > 0

    edges = graph.get_claim_evidence("c1")

    assert len(edges) == 2

    for edge in edges:
        assert edge.edge_type == EdgeType.SUPPORTS
        assert edge.verification_confidence is not None
        assert edge.verification_confidence > 0
        assert edge.confidence is not None

    print("[PASS] Claim verified through graph-connected evidence")
    print("[PASS] All evidence edges updated to SUPPORTS")
    print("[PASS] Verification confidence stored separately")
    print("[PASS] Semantic similarity confidence preserved")


def test_contradictory_graph():
    print("\n" + "-" * 80)
    print("TEST 2 — GRAPH-INTEGRATED CONTRADICTION")
    print("-" * 80)

    graph = build_contradictory_graph()

    verifier = GraphClaimVerifier(
        ClaimVerifier()
    )

    result = verifier.verify_claim(
        graph=graph,
        claim_id="c1",
    )

    print(f"Label: {result.label}")
    print(
        f"Verification confidence: "
        f"{result.verification_confidence:.3f}"
    )
    print(
        f"Evidence count: "
        f"{result.evidence_count}"
    )
    print(f"Rationale: {result.rationale}")

    assert result.label == EdgeType.CONTRADICTS
    assert result.evidence_count == 2

    edges = graph.get_claim_evidence("c1")

    assert len(edges) == 2

    for edge in edges:
        assert edge.edge_type == EdgeType.CONTRADICTS
        assert edge.verification_confidence is not None
        assert edge.verification_confidence > 0

    print("[PASS] Graph-integrated contradiction detected")
    print("[PASS] All claim edges updated to CONTRADICTS")


def test_no_evidence():
    print("\n" + "-" * 80)
    print("TEST 3 — CLAIM WITHOUT EVIDENCE")
    print("-" * 80)

    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses BM25.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    verifier = GraphClaimVerifier(
        ClaimVerifier()
    )

    try:
        verifier.verify_claim(
            graph=graph,
            claim_id="c1",
        )

        raise AssertionError(
            "Expected ValueError for claim without evidence"
        )

    except ValueError as exc:
        print(f"Expected error: {exc}")

    print("[PASS] Claims without evidence are rejected")


def test_unknown_claim():
    print("\n" + "-" * 80)
    print("TEST 4 — UNKNOWN CLAIM")
    print("-" * 80)

    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    verifier = GraphClaimVerifier(
        ClaimVerifier()
    )

    try:
        verifier.verify_claim(
            graph=graph,
            claim_id="does_not_exist",
        )

        raise AssertionError(
            "Expected ValueError for unknown claim"
        )

    except ValueError as exc:
        print(f"Expected error: {exc}")

    print("[PASS] Unknown claim rejected")


if __name__ == "__main__":

    print("=" * 80)
    print("STEP 14C — GRAPH-INTEGRATED CLAIM VERIFICATION")
    print("=" * 80)

    test_supporting_graph()
    test_contradictory_graph()
    test_no_evidence()
    test_unknown_claim()

    print("\n" + "=" * 80)
    print("STEP 14C TEST COMPLETE")
    print("=" * 80)
    print("[PASS] Graph-to-verifier integration")
    print("[PASS] Multi-evidence SUPPORTS propagation")
    print("[PASS] Multi-evidence CONTRADICTS propagation")
    print("[PASS] Verification confidence separation")
    print("[PASS] Semantic similarity preservation")
    print("[PASS] Missing evidence validation")
    print("[PASS] Unknown claim validation")
    print("=" * 80)
