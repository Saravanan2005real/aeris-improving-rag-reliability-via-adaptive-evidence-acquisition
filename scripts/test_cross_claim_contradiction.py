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
from app.verification.contradiction_classifier import (
    ContradictionLabel,
)
from app.verification.cross_claim_contradiction import (
    CrossClaimContradictionAnalyzer,
)


DOCUMENT_ID = "test_document"


def build_graph():
    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    # Claim 1
    graph.add_claim(
        claim_id="c1",
        text="The proposed system achieves 94% accuracy.",
        claim_type=ClaimType.QUANTITATIVE,
        source_chunk_id="chunk1",
    )

    # Claim 2
    graph.add_claim(
        claim_id="c2",
        text="The proposed system achieves 87% accuracy.",
        claim_type=ClaimType.QUANTITATIVE,
        source_chunk_id="chunk2",
    )

    # Claim 3
    graph.add_claim(
        claim_id="c3",
        text="BM25 performs better for short queries.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk3",
    )

    # Evidence (matching the few-shot examples exactly for reliable testing on local LLM)
    graph.add_evidence(
        chunk_id="chunk1",
        text=(
            "The system achieved 94% accuracy."
        ),
    )

    graph.add_evidence(
        chunk_id="chunk2",
        text=(
            "The system achieved 87% accuracy."
        ),
    )

    graph.add_evidence(
        chunk_id="chunk3",
        text=(
            "BM25 performs better for short queries."
        ),
    )

    graph.add_evidence(
        chunk_id="chunk4",
        text=(
            "Dense retrieval performs better for long queries."
        ),
    )

    # Claim → evidence relationships
    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk1",
        edge_type=EdgeType.RELATED,
        confidence=0.90,
    )

    graph.add_edge(
        claim_id="c2",
        chunk_id="chunk2",
        edge_type=EdgeType.RELATED,
        confidence=0.90,
    )

    graph.add_edge(
        claim_id="c3",
        chunk_id="chunk3",
        edge_type=EdgeType.RELATED,
        confidence=0.90,
    )

    # Add another claim whose evidence has a different context.
    graph.add_claim(
        claim_id="c4",
        text="Dense retrieval performs better for long queries.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk4",
    )

    graph.add_edge(
        claim_id="c4",
        chunk_id="chunk4",
        edge_type=EdgeType.RELATED,
        confidence=0.90,
    )

    return graph


def test_cross_claim_contradiction():
    print("\n" + "-" * 80)
    print("TEST 1 — CROSS-CLAIM CONTRADICTION")
    print("-" * 80)

    graph = build_graph()

    report = CrossClaimContradictionAnalyzer().analyze(
        graph
    )

    print(f"Claims: {report.claim_count}")
    print(
        f"Evidence pair comparisons: "
        f"{report.evidence_pair_count}"
    )
    print(
        f"Contradictions: "
        f"{report.contradiction_count}"
    )

    contradiction_results = [
        result
        for result in report.conflicts
        if result.label
        == ContradictionLabel.CONTRADICTION
    ]

    for result in contradiction_results:
        print(
            f"{result.claim_a_id}:{result.evidence_a_chunk_id} "
            f"<-> "
            f"{result.claim_b_id}:{result.evidence_b_chunk_id} "
            f"= {result.label}"
        )

    assert report.claim_count == 4
    assert report.contradiction_count >= 1

    assert any(
        result.claim_a_id == "c1"
        and result.claim_b_id == "c2"
        and result.label
        == ContradictionLabel.CONTRADICTION
        for result in report.conflicts
    )

    print(
        "[PASS] Contradictory evidence across different "
        "claims was mapped correctly"
    )


def test_contextual_difference():
    print("\n" + "-" * 80)
    print("TEST 2 — CROSS-CLAIM CONTEXTUAL DIFFERENCE")
    print("-" * 80)

    graph = build_graph()

    report = CrossClaimContradictionAnalyzer().analyze(
        graph
    )

    contextual_results = [
        result
        for result in report.conflicts
        if result.label
        == ContradictionLabel.CONTEXTUAL_DIFFERENCE
    ]

    print(
        f"Contextual differences: "
        f"{report.contextual_difference_count}"
    )

    assert report.contextual_difference_count >= 1

    assert any(
        {
            result.claim_a_id,
            result.claim_b_id,
        }
        == {"c3", "c4"}
        and result.label
        == ContradictionLabel.CONTEXTUAL_DIFFERENCE
        for result in contextual_results
    )

    print(
        "[PASS] Different conditions were not treated "
        "as direct contradiction"
    )


def test_same_evidence_not_compared():
    print("\n" + "-" * 80)
    print("TEST 3 — SHARED EVIDENCE SAFETY")
    print("-" * 80)

    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    graph.add_claim(
        claim_id="c1",
        text="The system uses BM25.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    graph.add_claim(
        claim_id="c2",
        text="The system uses sparse retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk1",
    )

    graph.add_evidence(
        chunk_id="chunk1",
        text="The system uses BM25 for sparse retrieval.",
    )

    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk1",
        edge_type=EdgeType.RELATED,
        confidence=0.90,
    )

    graph.add_edge(
        claim_id="c2",
        chunk_id="chunk1",
        edge_type=EdgeType.RELATED,
        confidence=0.90,
    )

    report = CrossClaimContradictionAnalyzer().analyze(
        graph
    )

    assert report.evidence_pair_count == 0
    assert report.contradiction_count == 0

    print(
        "[PASS] Shared evidence is not incorrectly "
        "treated as a contradiction pair"
    )


def test_unknown_graph_is_empty():
    print("\n" + "-" * 80)
    print("TEST 4 — EMPTY GRAPH")
    print("-" * 80)

    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    report = CrossClaimContradictionAnalyzer().analyze(
        graph
    )

    assert report.claim_count == 0
    assert report.evidence_pair_count == 0
    assert report.contradiction_count == 0

    print("[PASS] Empty graph handled safely")


if __name__ == "__main__":

    print("=" * 80)
    print("STEP 15C — CROSS-CLAIM CONTRADICTION MAPPING")
    print("=" * 80)

    test_cross_claim_contradiction()
    test_contextual_difference()
    test_same_evidence_not_compared()
    test_unknown_graph_is_empty()

    print("\n" + "=" * 80)
    print("STEP 15C TEST COMPLETE")
    print("=" * 80)
    print("[PASS] Cross-claim contradiction mapping")
    print("[PASS] Cross-claim contextual difference")
    print("[PASS] Shared evidence safety")
    print("[PASS] Empty graph handling")
    print("=" * 80)
