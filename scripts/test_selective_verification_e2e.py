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
from app.verification.graph_verifier import GraphVerificationResult
from app.verification.selective_executor import (
    SelectiveVerificationExecutor,
)
from app.verification.selective_verification import (
    SelectiveVerificationSelector,
)
from app.verification.verification_efficiency import (
    VerificationEfficiencyCalculator,
)


class FakeGraphVerifier:
    """
    Deterministic verifier for end-to-end orchestration testing.
    """

    def __init__(self):
        self.calls = []

    def verify_claim(self, graph, claim_id):

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
            rationale="E2E deterministic verification result.",
        )


def build_graph():

    graph = ClaimEvidenceGraphBuilder(
        document_id="e2e_test_document"
    )

    graph.add_claim(
        claim_id="critical",
        text="The evidence contains a contradiction.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk1",
    )

    graph.add_claim(
        claim_id="uncertain",
        text="The system improves recall.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk2",
    )

    graph.add_claim(
        claim_id="strong",
        text="The system uses hybrid retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk3",
    )

    graph.add_evidence(
        chunk_id="chunk1",
        text="Contradictory evidence.",
    )

    graph.add_evidence(
        chunk_id="chunk2",
        text="Evidence about recall.",
    )

    graph.add_evidence(
        chunk_id="chunk3",
        text="Evidence about hybrid retrieval.",
    )

    graph.add_edge(
        claim_id="critical",
        chunk_id="chunk1",
        edge_type=EdgeType.CONTRADICTS,
        confidence=0.90,
        verification_confidence=0.90,
    )

    graph.add_edge(
        claim_id="uncertain",
        chunk_id="chunk2",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.60,
        verification_confidence=0.40,
    )

    graph.add_edge(
        claim_id="strong",
        chunk_id="chunk3",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.95,
        verification_confidence=0.95,
    )

    return graph


def test_end_to_end_selection():

    graph = build_graph()

    verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=verifier,
        selector=SelectiveVerificationSelector(),
    )

    claims = [
        {
            "claim_id": "critical",
            "raw_confidence": 0.90,
            "calibrated_confidence": 0.90,
        },
        {
            "claim_id": "uncertain",
            "raw_confidence": 0.40,
            "calibrated_confidence": 0.40,
        },
        {
            "claim_id": "strong",
            "raw_confidence": 0.90,
            "calibrated_confidence": 0.95,
        },
    ]

    report = executor.execute(
        graph=graph,
        claims=claims,
        budget=2,
    )

    assert report.candidate_count == 3
    assert report.selected_count == 2
    assert report.verified_count == 2

    assert report.selected_claim_ids == [
        "critical",
        "uncertain",
    ]

    assert verifier.calls == [
        "critical",
        "uncertain",
    ]

    print(
        "TEST 1 — End-to-end selection and execution: PASS"
    )


def test_strong_claim_remains_unverified():

    graph = build_graph()

    verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=verifier,
    )

    executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "strong",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.95,
            }
        ],
        budget=2,
    )

    assert verifier.calls == []

    edge = graph.get_claim_evidence("strong")[0]

    assert edge.verification_confidence == 0.95

    print(
        "TEST 2 — Strong claim preserved without re-verification: PASS"
    )


def test_efficiency_accounting():

    graph = build_graph()

    verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=verifier,
    )

    report = executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "critical",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
            {
                "claim_id": "uncertain",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
            {
                "claim_id": "strong",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.95,
            },
        ],
        budget=2,
    )

    calculator = VerificationEfficiencyCalculator()

    efficiency = calculator.calculate(
        candidate_count=report.candidate_count,
        selected_count=report.selected_count,
        verified_count=report.verified_count,
        budget=report.budget,
    )

    assert efficiency.candidate_count == 3
    assert efficiency.verified_count == 2
    assert efficiency.skipped_count == 1
    assert efficiency.verification_rate == 2 / 3
    assert efficiency.skip_rate == 1 / 3
    assert efficiency.budget_utilization == 1.0
    assert efficiency.estimated_verification_calls_saved == 1

    print(
        "TEST 3 — End-to-end efficiency accounting: PASS"
    )


def test_verified_graph_state():

    graph = build_graph()

    verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=verifier,
    )

    executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "critical",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
            {
                "claim_id": "uncertain",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
        ],
        budget=2,
    )

    critical_edge = graph.get_claim_evidence(
        "critical"
    )[0]

    uncertain_edge = graph.get_claim_evidence(
        "uncertain"
    )[0]

    assert critical_edge.edge_type == EdgeType.SUPPORTS
    assert uncertain_edge.edge_type == EdgeType.SUPPORTS

    assert (
        critical_edge.verification_confidence
        == 0.90
    )

    assert (
        uncertain_edge.verification_confidence
        == 0.90
    )

    print(
        "TEST 4 — Verified graph state: PASS"
    )


def test_budget_zero_end_to_end():

    graph = build_graph()

    verifier = FakeGraphVerifier()

    executor = SelectiveVerificationExecutor(
        verifier=verifier,
    )

    report = executor.execute(
        graph=graph,
        claims=[
            {
                "claim_id": "critical",
                "raw_confidence": 0.90,
                "calibrated_confidence": 0.90,
            },
            {
                "claim_id": "uncertain",
                "raw_confidence": 0.40,
                "calibrated_confidence": 0.40,
            },
        ],
        budget=0,
    )

    assert report.selected_count == 0
    assert report.verified_count == 0
    assert verifier.calls == []

    print(
        "TEST 5 — Zero-budget end-to-end behavior: PASS"
    )


if __name__ == "__main__":

    print("\n=== STEP 18D TEST ===")

    test_end_to_end_selection()
    test_strong_claim_remains_unverified()
    test_efficiency_accounting()
    test_verified_graph_state()
    test_budget_zero_end_to_end()

    print("\nSTEP 18D TEST COMPLETE")
