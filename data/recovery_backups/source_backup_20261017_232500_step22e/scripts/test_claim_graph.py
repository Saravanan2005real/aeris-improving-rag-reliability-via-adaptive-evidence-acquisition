import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import ClaimType
from app.claim_graph.validator import (
    ClaimEvidenceGraphValidator,
)


def build_valid_graph():

    builder = ClaimEvidenceGraphBuilder(
        document_id="test_document",
        embedding_model="all-MiniLM-L6-v2",
        similarity_threshold=0.70,
    )

    builder.add_evidence(
        chunk_id="chunk_1",
        text=(
            "AERIS uses dense retrieval using "
            "all-MiniLM-L6-v2."
        ),
    )

    builder.add_evidence(
        chunk_id="chunk_2",
        text=(
            "AERIS uses sparse retrieval using BM25."
        ),
    )

    builder.add_claim(
        claim_id="claim_1",
        text="AERIS uses dense retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk_1",
    )

    builder.add_claim(
        claim_id="claim_2",
        text="AERIS uses sparse retrieval using BM25.",
        claim_type=ClaimType.COMPONENT,
        source_chunk_id="chunk_2",
    )

    builder.add_edge(
        claim_id="claim_1",
        chunk_id="chunk_1",
        confidence=0.90,
    )

    builder.add_edge(
        claim_id="claim_2",
        chunk_id="chunk_2",
        confidence=0.95,
    )

    return builder.build()


def main():

    print("=" * 80)
    print("STEP 13D — CLAIM-EVIDENCE GRAPH VALIDATION TEST")
    print("=" * 80)

    validator = ClaimEvidenceGraphValidator()

    # ---------------------------------------------------------
    # VALID GRAPH
    # ---------------------------------------------------------

    print("\n" + "-" * 80)
    print("TEST 1 — VALID GRAPH")
    print("-" * 80)

    graph = build_valid_graph()

    errors = validator.validate(graph)

    assert len(errors) == 0

    print("[PASS] Valid graph contains no structural errors")
    print("[PASS] Claim provenance is valid")
    print("[PASS] Evidence provenance is valid")
    print("[PASS] Edge references are valid")
    print("[PASS] Confidence values are valid")
    print("[PASS] No orphan claims")
    print("[PASS] No orphan evidence")
    print("[PASS] No duplicate relationships")

    # ---------------------------------------------------------
    # ORPHAN CLAIM
    # ---------------------------------------------------------

    print("\n" + "-" * 80)
    print("TEST 2 — ORPHAN CLAIM")
    print("-" * 80)

    orphan_builder = ClaimEvidenceGraphBuilder(
        document_id="test_document",
        embedding_model="all-MiniLM-L6-v2",
    )

    orphan_builder.add_evidence(
        chunk_id="chunk_1",
        text="Some evidence text.",
    )

    orphan_builder.add_claim(
        claim_id="claim_1",
        text="An unsupported claim.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk_1",
    )

    orphan_graph = orphan_builder.build()

    errors = validator.validate(orphan_graph)

    assert any(
        error.code == "ORPHAN_CLAIM"
        for error in errors
    )

    print("[PASS] Orphan claim detected")

    # ---------------------------------------------------------
    # ORPHAN EVIDENCE
    # ---------------------------------------------------------

    print("\n" + "-" * 80)
    print("TEST 3 — ORPHAN EVIDENCE")
    print("-" * 80)

    orphan_evidence_builder = ClaimEvidenceGraphBuilder(
        document_id="test_document",
        embedding_model="all-MiniLM-L6-v2",
    )

    orphan_evidence_builder.add_evidence(
        chunk_id="chunk_1",
        text="Connected evidence.",
    )

    orphan_evidence_builder.add_evidence(
        chunk_id="chunk_2",
        text="Unused evidence.",
    )

    orphan_evidence_builder.add_claim(
        claim_id="claim_1",
        text="A claim.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk_1",
    )

    orphan_evidence_builder.add_edge(
        claim_id="claim_1",
        chunk_id="chunk_1",
        confidence=0.90,
    )

    orphan_evidence_graph = (
        orphan_evidence_builder.build()
    )

    errors = validator.validate(
        orphan_evidence_graph
    )

    assert any(
        error.code == "ORPHAN_EVIDENCE"
        for error in errors
    )

    print("[PASS] Orphan evidence detected")

    # ---------------------------------------------------------
    # INVALID EDGE REFERENCE
    # ---------------------------------------------------------

    print("\n" + "-" * 80)
    print("TEST 4 — INVALID EDGE REFERENCE")
    print("-" * 80)

    invalid_builder = ClaimEvidenceGraphBuilder(
        document_id="test_document",
        embedding_model="all-MiniLM-L6-v2",
    )

    invalid_builder.add_claim(
        claim_id="claim_1",
        text="A claim.",
        claim_type=ClaimType.FACT,
        source_chunk_id="chunk_1",
    )

    invalid_builder.add_evidence(
        chunk_id="chunk_1",
        text="Evidence.",
    )

    # Directly construct an invalid graph edge.
    from app.claim_graph.schemas import (
        ClaimEvidenceEdge,
        ClaimEvidenceGraph,
    )

    invalid_edge = ClaimEvidenceEdge(
        edge_id="invalid_edge",
        claim_id="claim_DOES_NOT_EXIST",
        chunk_id="chunk_1",
        confidence=0.80,
    )

    invalid_graph = ClaimEvidenceGraph(
        document_id="test_document",
        claims=list(invalid_builder.claims.values()),
        evidence=list(invalid_builder.evidence.values()),
        edges=[invalid_edge],
    )

    errors = validator.validate(invalid_graph)

    assert any(
        error.code == "INVALID_CLAIM_REFERENCE"
        for error in errors
    )

    print("[PASS] Invalid claim reference detected")

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("STEP 13D TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
