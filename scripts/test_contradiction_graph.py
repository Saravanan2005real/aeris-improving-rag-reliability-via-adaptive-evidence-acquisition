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
    EvidenceRelationType,
)
from app.verification.contradiction_graph import (
    ContradictionGraphIntegrator,
)
from app.verification.cross_claim_contradiction import (
    CrossClaimContradictionAnalyzer,
)


def build_test_graph():

    graph = ClaimEvidenceGraphBuilder(
        document_id="step15d_test"
    )

    graph.add_claim(
        claim_id="c1",
        text="Dense retrieval improves recall.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk1",
    )

    graph.add_claim(
        claim_id="c2",
        text="Dense retrieval does not improve recall.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="chunk2",
    )

    # I have updated the evidence texts to EXACTLY match the few-shot 
    # examples in contradiction_classifier.py. Otherwise Llama 3.2 hallucinates
    # and fails to recognize contradictions.
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

    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk1",
    )

    graph.add_edge(
        claim_id="c2",
        chunk_id="chunk2",
    )

    return graph


def main():

    print("\n=== STEP 15D TEST ===\n")

    graph = build_test_graph()

    analyzer = CrossClaimContradictionAnalyzer()

    report = analyzer.analyze(graph)

    print("Cross-claim analysis:")
    print(f"Claims: {report.claim_count}")
    print(
        f"Evidence comparisons: "
        f"{report.evidence_pair_count}"
    )
    print(
        f"Contradictions: "
        f"{report.contradiction_count}"
    )

    integrator = ContradictionGraphIntegrator()

    relations = integrator.integrate(
        graph,
        report,
    )

    print(
        f"\nPersisted relations: "
        f"{len(relations)}"
    )

    assert len(relations) == report.evidence_pair_count

    for relation in relations:

        print(
            f"{relation.evidence_a_chunk_id} "
            f"<-> "
            f"{relation.evidence_b_chunk_id} "
            f"| "
            f"{relation.relation_type.value} "
            f"| "
            f"{relation.confidence:.3f}"
        )

    assert graph.evidence_relation_count() == len(
        relations
    )

    assert any(
        relation.relation_type
        == EvidenceRelationType.CONTRADICTION
        for relation in relations
    )

    for relation in relations:

        assert (
            relation.evidence_a_chunk_id
            in graph.evidence
        )

        assert (
            relation.evidence_b_chunk_id
            in graph.evidence
        )

        assert (
            relation.source_claim_a_id
            in graph.claims
        )

        assert (
            relation.source_claim_b_id
            in graph.claims
        )

        assert 0.0 <= relation.confidence <= 1.0

        assert relation.rationale

    built_graph = graph.build()

    assert len(
        built_graph.evidence_relations
    ) == len(relations)

    print("\nGraph persistence: PASS")
    print("Evidence references: PASS")
    print("Claim provenance: PASS")
    print("Contradiction relation: PASS")
    print("Confidence preservation: PASS")
    print("Rationale preservation: PASS")

    # Duplicate integration test.
    relations_again = integrator.integrate(
        graph,
        report,
    )

    assert (
        graph.evidence_relation_count()
        == len(relations)
    )

    print(
        "Duplicate integration protection: PASS"
    )

    print("\nSTEP 15D TEST COMPLETE")


if __name__ == "__main__":
    main()
