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
from app.verification.selective_verification import (
    SelectiveVerificationPolicy,
    SelectiveVerificationSelector,
    VerificationPriority,
)


def build_graph():
    graph = ClaimEvidenceGraphBuilder(
        document_id="test_document"
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses hybrid retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    graph.add_claim(
        claim_id="c2",
        text="AERIS improves recall.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk2",
    )

    graph.add_claim(
        claim_id="c3",
        text="AERIS supports multilingual retrieval.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk3",
    )

    graph.add_claim(
        claim_id="c4",
        text="AERIS uses BM25.",
        claim_type=ClaimType.COMPONENT,
        source_chunk_id="chunk4",
    )

    graph.add_evidence(
        chunk_id="chunk1",
        text="AERIS uses dense and sparse retrieval.",
    )

    graph.add_evidence(
        chunk_id="chunk2",
        text="AERIS improves recall compared with baselines.",
    )

    graph.add_evidence(
        chunk_id="chunk3",
        text="AERIS supports multilingual retrieval.",
    )

    graph.add_evidence(
        chunk_id="chunk4",
        text="AERIS uses BM25.",
    )

    return graph


def test_supported_high_confidence_is_skipped():
    graph = build_graph()

    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk1",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.90,
        verification_confidence=0.95,
    )

    policy = SelectiveVerificationPolicy()

    result = policy.evaluate_claim(
        graph,
        "c1",
        raw_confidence=0.90,
        calibrated_confidence=0.95,
    )

    assert result.claim_status == ClaimVerificationStatus.SUPPORTED
    assert result.priority == VerificationPriority.SKIP
    assert result.requires_verification is False

    print("TEST 1 — Strong supported claim: PASS")


def test_low_confidence_is_high_priority():
    graph = build_graph()

    graph.add_edge(
        claim_id="c2",
        chunk_id="chunk2",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.70,
        verification_confidence=0.40,
    )

    policy = SelectiveVerificationPolicy()

    result = policy.evaluate_claim(
        graph,
        "c2",
        raw_confidence=0.40,
        calibrated_confidence=0.40,
    )

    assert result.priority == VerificationPriority.HIGH
    assert result.requires_verification is True

    print("TEST 2 — Low confidence claim: PASS")


def test_contradicted_claim_is_critical():
    graph = build_graph()

    graph.add_edge(
        claim_id="c3",
        chunk_id="chunk3",
        edge_type=EdgeType.CONTRADICTS,
        confidence=0.90,
        verification_confidence=0.90,
    )

    policy = SelectiveVerificationPolicy()

    result = policy.evaluate_claim(
        graph,
        "c3",
        raw_confidence=0.90,
        calibrated_confidence=0.90,
    )

    assert result.claim_status == ClaimVerificationStatus.CONTRADICTED
    assert result.priority == VerificationPriority.CRITICAL
    assert result.requires_verification is True

    print("TEST 3 — Contradicted claim: PASS")


def test_unverified_claim_is_high_priority():
    graph = build_graph()

    policy = SelectiveVerificationPolicy()

    result = policy.evaluate_claim(
        graph,
        "c4",
    )

    assert result.claim_status == ClaimVerificationStatus.UNVERIFIED
    assert result.priority == VerificationPriority.CRITICAL
    assert result.requires_verification is True

    print("TEST 4 — Unverified claim: PASS")


def test_unknown_claim_rejected():
    graph = build_graph()

    policy = SelectiveVerificationPolicy()

    try:
        policy.evaluate_claim(
            graph,
            "unknown_claim",
        )
    except ValueError:
        print("TEST 5 — Unknown claim rejection: PASS")
        return

    raise AssertionError("Unknown claim was not rejected")


def test_duplicate_claims_removed():
    graph = build_graph()

    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk1",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.90,
        verification_confidence=0.90,
    )

    selector = SelectiveVerificationSelector()

    results = selector.evaluate(
        graph,
        [
            {
                "claim_id": "c1",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
            {
                "claim_id": "c1",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
        ],
    )

    assert len(results) == 1

    print("TEST 6 — Duplicate claim protection: PASS")


def test_budget_is_respected():
    graph = build_graph()

    graph.add_edge(
        claim_id="c2",
        chunk_id="chunk2",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.40,
        verification_confidence=0.40,
    )

    graph.add_edge(
        claim_id="c3",
        chunk_id="chunk3",
        edge_type=EdgeType.CONTRADICTS,
        confidence=0.90,
        verification_confidence=0.90,
    )

    selector = SelectiveVerificationSelector()

    results = selector.evaluate(
        graph,
        [
            {
                "claim_id": "c2",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
            {
                "claim_id": "c3",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
        ],
    )

    selected = selector.select(
        results,
        budget=1,
    )

    assert len(selected) == 1
    assert selected[0].claim_id == "c3"

    print("TEST 7 — Verification budget: PASS")


if __name__ == "__main__":
    print("\n=== STEP 18A TEST ===")

    test_supported_high_confidence_is_skipped()
    test_low_confidence_is_high_priority()
    test_contradicted_claim_is_critical()
    test_unverified_claim_is_high_priority()
    test_unknown_claim_rejected()
    test_duplicate_claims_removed()
    test_budget_is_respected()

    print("\nSTEP 18A TEST COMPLETE")
