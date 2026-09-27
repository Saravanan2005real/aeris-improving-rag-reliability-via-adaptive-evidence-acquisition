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
from app.verification.cross_lingual_agreement import (
    CrossLingualEvidenceClassifier,
)
from app.verification.cross_lingual_claim import (
    ClaimCrossLingualAnalyzer,
)
from app.verification.cross_lingual_graph import (
    CrossLingualGraphIntegrator,
)


def build_graph():

    graph = ClaimEvidenceGraphBuilder(
        document_id="step16c_test"
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses hybrid retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="chunk_en",
    )

    graph.add_evidence(
        chunk_id="chunk_en",
        text=(
            "AERIS uses hybrid retrieval combining "
            "dense retrieval and BM25."
        ),
    )

    graph.add_evidence(
        chunk_id="chunk_ta",
        text=(
            "AERIS அடர்த்தியான மீட்டெடுப்பு மற்றும் BM25 ஐ "
            "இணைத்து கலப்பு மீட்டெடுப்பைப் பயன்படுத்துகிறது."
        ),
    )

    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk_en",
    )

    graph.add_edge(
        claim_id="c1",
        chunk_id="chunk_ta",
    )

    return graph


def main():

    print("\n=== STEP 16C TEST ===\n")

    graph = build_graph()

    classifier = CrossLingualEvidenceClassifier()

    analyzer = ClaimCrossLingualAnalyzer(
        classifier=classifier
    )

    result = analyzer.analyze_claim(
        graph=graph,
        claim_id="c1",
        evidence_languages={
            "chunk_en": "English",
            "chunk_ta": "Tamil",
        },
    )

    print(
        "Analysis label:",
        result.overall_label.value,
    )

    print(
        "Pair count:",
        result.pair_count,
    )

    assert result.pair_count == 1
    assert len(result.pair_results) == 1

    pair = result.pair_results[0]

    print(
        "Pair:",
        pair.evidence_a_chunk_id,
        "<->",
        pair.evidence_b_chunk_id,
    )

    print(
        "Pair label:",
        pair.label.value,
    )

    print(
        "Pair confidence:",
        f"{pair.confidence:.3f}",
    )

    assert pair.label.value == "AGREEMENT"

    integrator = CrossLingualGraphIntegrator()

    evidence_pairs = [
        {
            "evidence_a_chunk_id":
                pair.evidence_a_chunk_id,

            "evidence_b_chunk_id":
                pair.evidence_b_chunk_id,

            "label":
                pair.label.value,

            "confidence":
                pair.confidence,

            "rationale":
                pair.rationale,
        }
    ]

    relations = integrator.integrate(
        graph=graph,
        result=result,
        evidence_pairs=evidence_pairs,
    )

    print(
        "\nPersisted relations:",
        len(relations),
    )

    assert len(relations) == 1
    assert graph.evidence_relation_count() == 1

    relation = relations[0]

    print(
        relation.evidence_a_chunk_id,
        "<->",
        relation.evidence_b_chunk_id,
        "|",
        relation.relation_type.value,
        "|",
        f"{relation.confidence:.3f}",
    )

    assert (
        relation.relation_type
        == EvidenceRelationType.AGREEMENT
    )

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
        == "c1"
    )

    assert (
        relation.source_claim_b_id
        == "c1"
    )

    assert relation.confidence == 0.90
    assert relation.rationale

    print("\nGraph persistence: PASS")
    print("Agreement relation: PASS")
    print("Evidence references: PASS")
    print("Claim provenance: PASS")
    print("Confidence preservation: PASS")
    print("Rationale preservation: PASS")

    # Duplicate integration
    integrator.integrate(
        graph=graph,
        result=result,
        evidence_pairs=evidence_pairs,
    )

    assert graph.evidence_relation_count() == 1

    print(
        "Duplicate integration protection: PASS"
    )

    built_graph = graph.build()

    assert len(
        built_graph.evidence_relations
    ) == 1

    print(
        "Graph serialization: PASS"
    )

    print("\nSTEP 16C TEST COMPLETE")


if __name__ == "__main__":
    main()
