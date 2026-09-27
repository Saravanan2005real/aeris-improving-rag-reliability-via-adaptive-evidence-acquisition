import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import (
    ClaimType,
    EdgeType,
    ClaimVerificationStatus,
)
from app.verification.claim_status import ClaimStatusResolver


DOCUMENT_ID = "test_document"


def make_graph(edge_types):
    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses BM25 for sparse retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    for index, edge_type in enumerate(
        edge_types,
        start=1,
    ):
        chunk_id = f"chunk{index}"

        graph.add_evidence(
            chunk_id=chunk_id,
            text=f"Evidence {index}",
        )

        graph.add_edge(
            claim_id="c1",
            chunk_id=chunk_id,
            edge_type=edge_type,
            confidence=0.80,
            verification_confidence=0.90,
        )

    return graph


def test_supported():
    print("\n" + "-" * 80)
    print("TEST 1 — SUPPORTED")
    print("-" * 80)

    graph = make_graph([
        EdgeType.SUPPORTS,
        EdgeType.SUPPORTS,
    ])

    status = ClaimStatusResolver().resolve(
        graph,
        "c1",
    )

    print(f"Status: {status}")

    assert status == ClaimVerificationStatus.SUPPORTED

    print("[PASS] Multiple supporting edges -> SUPPORTED")


def test_contradicted():
    print("\n" + "-" * 80)
    print("TEST 2 — CONTRADICTED")
    print("-" * 80)

    graph = make_graph([
        EdgeType.CONTRADICTS,
        EdgeType.CONTRADICTS,
    ])

    status = ClaimStatusResolver().resolve(
        graph,
        "c1",
    )

    print(f"Status: {status}")

    assert status == ClaimVerificationStatus.CONTRADICTED

    print("[PASS] Contradictory edges -> CONTRADICTED")


def test_insufficient():
    print("\n" + "-" * 80)
    print("TEST 3 — INSUFFICIENT")
    print("-" * 80)

    graph = make_graph([
        EdgeType.RELATED,
        EdgeType.RELATED,
    ])

    status = ClaimStatusResolver().resolve(
        graph,
        "c1",
    )

    print(f"Status: {status}")

    assert status == ClaimVerificationStatus.INSUFFICIENT

    print("[PASS] Related-only evidence -> INSUFFICIENT")


def test_conflicted():
    print("\n" + "-" * 80)
    print("TEST 4 — CONFLICTED")
    print("-" * 80)

    graph = make_graph([
        EdgeType.SUPPORTS,
        EdgeType.CONTRADICTS,
    ])

    status = ClaimStatusResolver().resolve(
        graph,
        "c1",
    )

    print(f"Status: {status}")

    assert status == ClaimVerificationStatus.CONFLICTED

    print("[PASS] Support + contradiction -> CONFLICTED")


def test_unverified():
    print("\n" + "-" * 80)
    print("TEST 5 — UNVERIFIED")
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

    status = ClaimStatusResolver().resolve(
        graph,
        "c1",
    )

    print(f"Status: {status}")

    assert status == ClaimVerificationStatus.UNVERIFIED

    print("[PASS] No evidence -> UNVERIFIED")


def test_unknown_claim():
    print("\n" + "-" * 80)
    print("TEST 6 — UNKNOWN CLAIM")
    print("-" * 80)

    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    try:
        ClaimStatusResolver().resolve(
            graph,
            "does_not_exist",
        )

        raise AssertionError(
            "Expected ValueError"
        )

    except ValueError as exc:
        print(f"Expected error: {exc}")

    print("[PASS] Unknown claim rejected")


if __name__ == "__main__":

    print("=" * 80)
    print("STEP 14D — VERIFICATION-AWARE CLAIM STATUS")
    print("=" * 80)

    test_supported()
    test_contradicted()
    test_insufficient()
    test_conflicted()
    test_unverified()
    test_unknown_claim()

    print("\n" + "=" * 80)
    print("STEP 14D TEST COMPLETE")
    print("=" * 80)
    print("[PASS] SUPPORTED status")
    print("[PASS] CONTRADICTED status")
    print("[PASS] INSUFFICIENT status")
    print("[PASS] CONFLICTED status")
    print("[PASS] UNVERIFIED status")
    print("[PASS] Unknown claim validation")
    print("=" * 80)
