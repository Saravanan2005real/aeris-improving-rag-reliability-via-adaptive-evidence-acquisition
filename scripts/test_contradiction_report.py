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
from app.verification.contradiction_report import (
    ClaimContradictionAnalyzer,
)


DOCUMENT_ID = "test_document"


def build_graph(evidence_texts):
    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    graph.add_claim(
        claim_id="c1",
        text="The proposed system achieves high accuracy.",
        claim_type=ClaimType.QUANTITATIVE,
        source_chunk_id="chunk1",
    )

    for index, text in enumerate(
        evidence_texts,
        start=1,
    ):
        graph.add_evidence(
            chunk_id=f"chunk{index}",
            text=text,
        )

        graph.add_edge(
            claim_id="c1",
            chunk_id=f"chunk{index}",
            edge_type=EdgeType.RELATED,
            confidence=0.80,
        )

    return graph


def test_pair_generation():
    print("\n" + "-" * 80)
    print("TEST 1 — PAIR GENERATION")
    print("-" * 80)

    graph = build_graph([
        "The system achieved 94% accuracy.",
        "The system achieved 87% accuracy.",
        "The system achieved 91% accuracy.",
    ])

    report = ClaimContradictionAnalyzer().analyze_claim(
        graph,
        "c1",
    )

    print(f"Evidence count: {report.evidence_count}")
    print(f"Pair count: {report.pair_count}")

    assert report.evidence_count == 3
    assert report.pair_count == 3

    print("[PASS] Three evidence chunks produced three pairs")


def test_contradiction_report():
    print("\n" + "-" * 80)
    print("TEST 2 — CONTRADICTION REPORT")
    print("-" * 80)

    graph = build_graph([
        "The system achieved 94% accuracy.",
        "The system achieved 87% accuracy.",
    ])

    report = ClaimContradictionAnalyzer().analyze_claim(
        graph,
        "c1",
    )

    print(f"Contradictions: {report.contradiction_count}")

    for pair in report.pairs:
        print(
            f"{pair.evidence_a_chunk_id} <-> "
            f"{pair.evidence_b_chunk_id}: "
            f"{pair.label}"
        )

    assert report.pair_count == 1
    assert report.contradiction_count == 1
    assert (
        report.pairs[0].label
        == ContradictionLabel.CONTRADICTION
    )

    print("[PASS] Genuine contradiction propagated to report")


def test_contextual_difference_report():
    print("\n" + "-" * 80)
    print("TEST 3 — CONTEXTUAL DIFFERENCE REPORT")
    print("-" * 80)

    graph = build_graph([
        "BM25 performs better for short queries.",
        "Dense retrieval performs better for long queries.",
    ])

    report = ClaimContradictionAnalyzer().analyze_claim(
        graph,
        "c1",
    )

    print(
        f"Contextual differences: "
        f"{report.contextual_difference_count}"
    )

    assert report.pair_count == 1
    assert report.contextual_difference_count == 1
    assert report.contradiction_count == 0

    print(
        "[PASS] Context-dependent evidence kept separate "
        "from contradiction"
    )


def test_no_contradiction_report():
    print("\n" + "-" * 80)
    print("TEST 4 — NO CONTRADICTION REPORT")
    print("-" * 80)

    graph = build_graph([
        "The system uses BM25.",
        "The system uses dense embeddings.",
    ])

    report = ClaimContradictionAnalyzer().analyze_claim(
        graph,
        "c1",
    )

    print(
        f"No contradiction: "
        f"{report.no_contradiction_count}"
    )

    assert report.pair_count == 1
    assert report.no_contradiction_count == 1
    assert report.contradiction_count == 0

    print("[PASS] Compatible evidence remains non-contradictory")


def test_unknown_claim():
    print("\n" + "-" * 80)
    print("TEST 5 — UNKNOWN CLAIM")
    print("-" * 80)

    graph = ClaimEvidenceGraphBuilder(
        document_id=DOCUMENT_ID
    )

    try:
        ClaimContradictionAnalyzer().analyze_claim(
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
    print("STEP 15B — CLAIM-LEVEL CONTRADICTION ANALYSIS")
    print("=" * 80)

    test_pair_generation()
    test_contradiction_report()
    test_contextual_difference_report()
    test_no_contradiction_report()
    test_unknown_claim()

    print("\n" + "=" * 80)
    print("STEP 15B TEST COMPLETE")
    print("=" * 80)
    print("[PASS] Pair generation")
    print("[PASS] Contradiction report")
    print("[PASS] Contextual difference report")
    print("[PASS] No-contradiction report")
    print("[PASS] Unknown claim validation")
    print("=" * 80)
