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
)
from app.verification.graph_verifier import (
    GraphVerificationResult,
)
from app.verification.selective_executor import (
    SelectiveVerificationExecutor,
)
from app.verification.selective_verification import (
    SelectiveVerificationSelector,
)


class FakeGraphVerifier:
    """
    Deterministic verifier used only to test selective
    verification orchestration.
    """

    def __init__(self):
        self.calls = []

    def verify_claim(
        self,
        graph,
        claim_id,
    ):
        self.calls.append(claim_id)

        claim = graph.claims[claim_id]
        edges = graph.get_claim_evidence(claim_id)

        for edge in edges:
            edge.edge_type = EdgeType.SUPPORTS
            edge.verification_confidence = 0.90

        return GraphVerificationResult(
            claim_id=claim_id,
            claim=claim.text,
            evidence_count=len(edges),
            evidence_chunk_ids=[
                edge.chunk_id
                for edge in edges
            ],
            label=EdgeType.SUPPORTS,
            verification_confidence=0.90,
            rationale="Fake verifier result for orchestration testing.",
        )


def build_graph():

    graph = ClaimEvidenceGraphBuilder(
        document_id="test_document"
    )

    graph.add_claim(
        claim_id="critical_claim",
        text="The system has contradictory evidence.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk1",
    )

    graph.add_claim(
        claim_id="low_confidence_claim",
        text="The system improves recall.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk2",
    )

    graph.add_claim(
        claim_id="strong_claim",
        text="The system uses hybrid retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk3",
    )

    graph.add_evidence(
        chunk_id="chunk1",
        text="Evidence concerning the contradictory claim.",
    )

    graph.add_evidence(
        chunk_id="chunk2",
        text="Evidence concerning recall.",
    )

    graph.add_evidence(
        chunk_id="chunk3",
        text="Evidence concerning hybrid retrieval.",
    )

    graph.add_edge(
        claim_id="critical_claim",
        chunk_id="chunk1",
        edge_type=EdgeType.CONTRADICTS,
        confidence=0.90,
        verification_confidence=0.90,
    )

    graph.add_edge(
        claim_id="low_confidence_claim",
        chunk_id="chunk2",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.60,
        verification_confidence=0.40,
    )

    graph.add_edge(
        claim_id="strong_claim",
        chunk_id="chunk3",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.90,
        verification_confidence=0.95,
    )

    return graph


def test_budget_limits_verification():

    graph = build_graph()

    fake_verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=fake_verifier,
        selector=SelectiveVerificationSelector(),
    )

    report = executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "critical_claim",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
            {
                "claim_id": "low_confidence_claim",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
            {
                "claim_id": "strong_claim",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.95,
            },
        ],
        budget=1,
    )

    assert report.candidate_count == 3
    assert report.selected_count == 1
    assert report.verified_count == 1
    assert report.budget == 1

    assert fake_verifier.calls == [
        "critical_claim"
    ]

    assert report.selected_claim_ids == [
        "critical_claim"
    ]

    print("TEST 1 — Hard verification budget: PASS")


def test_strong_claim_is_not_verified():

    graph = build_graph()

    fake_verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=fake_verifier,
        selector=SelectiveVerificationSelector(),
    )

    report = executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "strong_claim",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.95,
            },
        ],
        budget=5,
    )

    assert report.candidate_count == 1
    assert report.selected_count == 0
    assert report.verified_count == 0

    assert fake_verifier.calls == []

    print("TEST 2 — Strong claim skipped: PASS")


def test_low_confidence_claim_is_verified():

    graph = build_graph()

    fake_verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=fake_verifier,
        selector=SelectiveVerificationSelector(),
    )

    report = executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "low_confidence_claim",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
        ],
        budget=1,
    )

    assert report.selected_count == 1
    assert report.verified_count == 1

    assert fake_verifier.calls == [
        "low_confidence_claim"
    ]

    print("TEST 3 — Low-confidence claim verified: PASS")


def test_graph_updated_by_verifier():

    graph = build_graph()

    fake_verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=fake_verifier,
    )

    executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "low_confidence_claim",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
        ],
        budget=1,
    )

    edge = graph.get_claim_evidence(
        "low_confidence_claim"
    )[0]

    assert edge.edge_type == EdgeType.SUPPORTS
    assert edge.verification_confidence == 0.90

    print("TEST 4 — Graph update after verification: PASS")


def test_zero_budget():

    graph = build_graph()

    fake_verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=fake_verifier,
    )

    report = executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "critical_claim",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
        ],
        budget=0,
    )

    assert report.selected_count == 0
    assert report.verified_count == 0
    assert fake_verifier.calls == []

    print("TEST 5 — Zero-budget execution: PASS")


def test_negative_budget_rejected():

    graph = build_graph()

    fake_verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=fake_verifier,
    )

    try:
        executor.execute(
            graph=graph,
            claims=[
                {
                    "claim_id": "critical_claim",
                }
            ],
            budget=-1,
        )
    except ValueError:
        print("TEST 6 — Negative budget rejection: PASS")
        return

    raise AssertionError(
        "Negative budget was not rejected"
    )


if __name__ == "__main__":

    print("\n=== STEP 18B TEST ===")

    test_budget_limits_verification()
    test_strong_claim_is_not_verified()
    test_low_confidence_claim_is_verified()
    test_graph_updated_by_verifier()
    test_zero_budget()
    test_negative_budget_rejected()

    print("\nSTEP 18B TEST COMPLETE")
