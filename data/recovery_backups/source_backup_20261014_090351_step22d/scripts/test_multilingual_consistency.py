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
    EvidenceRelationType,
)
from app.verification.cross_lingual_agreement import (
    CrossLingualEvidenceClassifier,
    CrossLingualAgreementLabel,
)
from app.verification.cross_lingual_claim import (
    ClaimCrossLingualAnalyzer,
)
from app.verification.cross_lingual_graph import (
    CrossLingualGraphIntegrator,
)


def build_agreement_graph():

    graph = ClaimEvidenceGraphBuilder(
        document_id="step16d_agreement"
    )

    graph.add_claim(
        claim_id="c1",
        text="AERIS uses hybrid retrieval.",
        claim_type=ClaimType.METHOD,
        source_chunk_id="en",
    )

    graph.add_evidence(
        chunk_id="en",
        text=(
            "AERIS uses hybrid retrieval combining "
            "dense retrieval and BM25."
        ),
    )

    graph.add_evidence(
        chunk_id="ta",
        text=(
            "AERIS அடர்த்தியான மீட்டெடுப்பு மற்றும் BM25 ஐ "
            "இணைத்து கலப்பு மீட்டெடுப்பைப் பயன்படுத்துகிறது."
        ),
    )

    graph.add_evidence(
        chunk_id="hi",
        text=(
            "AERIS डेंस रिट्रीवल और BM25 को मिलाकर "
            "हाइब्रिड रिट्रीवल का उपयोग करता है।"
        ),
    )

    graph.add_edge(
        claim_id="c1",
        chunk_id="en",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.90,
    )

    graph.add_edge(
        claim_id="c1",
        chunk_id="ta",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.90,
    )

    graph.add_edge(
        claim_id="c1",
        chunk_id="hi",
        edge_type=EdgeType.SUPPORTS,
        confidence=0.90,
    )

    return graph


def analyze(
    graph,
    classifier,
    claim_id,
    languages,
):

    analyzer = ClaimCrossLingualAnalyzer(
        classifier=classifier
    )

    return analyzer.analyze_claim(
        graph=graph,
        claim_id=claim_id,
        evidence_languages=languages,
    )


def main():

    print("\n=== STEP 16D TEST ===\n")

    classifier = CrossLingualEvidenceClassifier()

    integrator = CrossLingualGraphIntegrator()

    # =========================================================
    # TEST 1 — English/Tamil agreement
    # =========================================================

    graph = build_agreement_graph()

    result = analyze(
        graph,
        classifier,
        "c1",
        {
            "en": "English",
            "ta": "Tamil",
            "hi": "Hindi",
        },
    )

    print("TEST 1")
    print("Languages:", result.language_count)
    print("Pairs:", result.pair_count)
    print("Agreement:", result.agreement_count)
    print("Contradiction:", result.contradiction_count)

    assert result.language_count == 3

    # 3 languages => 3 cross-language pairs
    assert result.pair_count == 3

    assert result.agreement_count == 3
    assert result.contradiction_count == 0
    assert result.contextual_difference_count == 0
    assert result.uncertain_count == 0

    assert result.overall_label == (
        CrossLingualAgreementLabel.AGREEMENT
    )

    print(
        "Multilingual agreement: PASS"
    )


    # =========================================================
    # TEST 2 — Persist multilingual agreement
    # =========================================================

    evidence_pairs = []

    for pair in result.pair_results:

        evidence_pairs.append(
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
        )

    relations = integrator.integrate(
        graph=graph,
        result=result,
        evidence_pairs=evidence_pairs,
    )

    assert len(relations) == 3
    assert graph.evidence_relation_count() == 3

    assert all(
        relation.relation_type
        == EvidenceRelationType.AGREEMENT
        for relation in relations
    )

    print(
        "Multilingual graph integration: PASS"
    )


    # =========================================================
    # TEST 3 — Contradictory multilingual evidence
    # =========================================================

    graph2 = ClaimEvidenceGraphBuilder(
        document_id="step16d_contradiction"
    )

    graph2.add_claim(
        claim_id="c1",
        text="The system achieved 91 percent recall.",
        claim_type=ClaimType.QUANTITATIVE,
        source_chunk_id="en",
    )

    graph2.add_evidence(
        chunk_id="en",
        text=(
            "The experiment achieved 91 percent recall using hybrid retrieval."
        ),
    )

    graph2.add_evidence(
        chunk_id="ta",
        text=(
            "கலப்பு மீட்டெடுப்பைப் பயன்படுத்திய சோதனையில் மீட்டெடுப்பு விகிதம் 76 சதவீதமாக இருந்தது."
        ),
    )

    graph2.add_edge(
        claim_id="c1",
        chunk_id="en",
    )

    graph2.add_edge(
        claim_id="c1",
        chunk_id="ta",
    )

    result2 = analyze(
        graph2,
        classifier,
        "c1",
        {
            "en": "English",
            "ta": "Tamil",
        },
    )

    print("\nTEST 3")
    print(
        "Overall:",
        result2.overall_label.value,
    )

    assert result2.pair_count == 1

    assert result2.contradiction_count == 1

    assert result2.overall_label == (
        CrossLingualAgreementLabel.CONTRADICTION
    )

    print(
        "Cross-lingual contradiction: PASS"
    )

    relations2 = integrator.integrate(
        graph=graph2,
        result=result2,
        evidence_pairs=[
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
            for pair in result2.pair_results
        ],
    )

    assert len(relations2) == 1

    assert (
        relations2[0].relation_type
        == EvidenceRelationType.CONTRADICTION
    )

    print(
        "Contradiction graph persistence: PASS"
    )


    # =========================================================
    # TEST 4 — Contextual difference
    # =========================================================

    graph3 = ClaimEvidenceGraphBuilder(
        document_id="step16d_context"
    )

    graph3.add_claim(
        claim_id="c1",
        text="Retrieval recall varies by query condition.",
        claim_type=ClaimType.COMPARATIVE,
        source_chunk_id="en",
    )

    graph3.add_evidence(
        chunk_id="en",
        text=(
            "For short queries, the retrieval system achieved "
            "92 percent recall."
        ),
    )

    graph3.add_evidence(
        chunk_id="ta",
        text=(
            "நீண்ட வினவல்களுக்கு, மீட்டெடுப்பு அமைப்பு "
            "85 சதவீத மீட்டெடுப்பை அடைந்தது."
        ),
    )

    graph3.add_edge(
        claim_id="c1",
        chunk_id="en",
    )

    graph3.add_edge(
        claim_id="c1",
        chunk_id="ta",
    )

    result3 = analyze(
        graph3,
        classifier,
        "c1",
        {
            "en": "English",
            "ta": "Tamil",
        },
    )

    print("\nTEST 4")
    print(
        "Overall:",
        result3.overall_label.value,
    )

    assert result3.contextual_difference_count == 1

    assert result3.overall_label == (
        CrossLingualAgreementLabel.CONTEXTUAL_DIFFERENCE
    )

    print(
        "Contextual difference: PASS"
    )


    # =========================================================
    # TEST 5 — Same-language evidence excluded
    # =========================================================

    graph4 = ClaimEvidenceGraphBuilder(
        document_id="step16d_same_language"
    )

    graph4.add_claim(
        claim_id="c1",
        text="AERIS uses BM25.",
        claim_type=ClaimType.COMPONENT,
        source_chunk_id="a",
    )

    graph4.add_evidence(
        chunk_id="a",
        text="AERIS uses BM25.",
    )

    graph4.add_evidence(
        chunk_id="b",
        text="BM25 is used by AERIS.",
    )

    graph4.add_edge(
        claim_id="c1",
        chunk_id="a",
    )

    graph4.add_edge(
        claim_id="c1",
        chunk_id="b",
    )

    result4 = analyze(
        graph4,
        classifier,
        "c1",
        {
            "a": "English",
            "b": "English",
        },
    )

    print("\nTEST 5")
    print(
        "Cross-lingual pair count:",
        result4.pair_count,
    )

    assert result4.pair_count == 0

    assert result4.overall_label == (
        CrossLingualAgreementLabel.UNCERTAIN
    )

    print(
        "Same-language exclusion: PASS"
    )


    # =========================================================
    # TEST 6 — Existing contradiction relation preserved
    # =========================================================

    graph5 = build_agreement_graph()

    # Existing Step 15 relation
    existing_relation = graph5.add_evidence_relation(
        evidence_a_chunk_id="en",
        evidence_b_chunk_id="ta",
        relation_type=EvidenceRelationType.CONTRADICTION,
        confidence=0.90,
        rationale="Existing contradiction relation.",
        source_claim_a_id="c1",
        source_claim_b_id="c1",
    )

    existing_id = existing_relation.relation_id

    print("\nTEST 6")
    print(
        "Existing relation:",
        existing_relation.relation_type.value,
    )

    assert (
        graph5.evidence_relation_count() == 1
    )

    assert (
        graph5.evidence_relations[existing_id]
        .relation_type
        == EvidenceRelationType.CONTRADICTION
    )

    print(
        "Existing relation preservation: PASS"
    )


    # =========================================================
    # TEST 7 — Graph serialization
    # =========================================================

    built = graph.build()

    assert len(built.claims) == 1
    assert len(built.evidence) == 3
    assert len(built.edges) == 3
    assert len(built.evidence_relations) == 3

    print(
        "\nTEST 7"
    )
    print(
        "Claims:",
        len(built.claims),
    )
    print(
        "Evidence:",
        len(built.evidence),
    )
    print(
        "Claim-evidence edges:",
        len(built.edges),
    )
    print(
        "Evidence relations:",
        len(built.evidence_relations),
    )

    print(
        "Graph serialization: PASS"
    )


    # =========================================================
    # TEST 8 — Duplicate protection
    # =========================================================

    count_before = graph.evidence_relation_count()

    integrator.integrate(
        graph=graph,
        result=result,
        evidence_pairs=evidence_pairs,
    )

    count_after = graph.evidence_relation_count()

    assert count_before == count_after

    print(
        "\nTEST 8"
    )
    print(
        "Before:",
        count_before,
    )
    print(
        "After:",
        count_after,
    )
    print(
        "Duplicate protection: PASS"
    )


    print(
        "\nSTEP 16D TEST COMPLETE"
    )


if __name__ == "__main__":
    main()
