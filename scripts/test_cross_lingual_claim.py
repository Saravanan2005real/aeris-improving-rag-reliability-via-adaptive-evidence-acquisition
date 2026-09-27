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
from app.verification.cross_lingual_agreement import (
    CrossLingualEvidenceClassifier,
    CrossLingualAgreementLabel,
)
from app.verification.cross_lingual_claim import (
    ClaimCrossLingualAnalyzer,
)


def build_graph():

    graph = ClaimEvidenceGraphBuilder(
        document_id="step16b_test"
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

    print("\n=== STEP 16B TEST ===\n")

    graph = build_graph()

    classifier = CrossLingualEvidenceClassifier()

    analyzer = ClaimCrossLingualAnalyzer(
        classifier=classifier
    )

    languages = {
        "chunk_en": "English",
        "chunk_ta": "Tamil",
    }

    result = analyzer.analyze_claim(
        graph=graph,
        claim_id="c1",
        evidence_languages=languages,
    )

    print("Claim:", result.claim)
    print("Evidence count:", result.evidence_count)
    print("Language count:", result.language_count)
    print("Pair count:", result.pair_count)

    print(
        "Agreement:",
        result.agreement_count,
    )

    print(
        "Contradiction:",
        result.contradiction_count,
    )

    print(
        "Contextual difference:",
        result.contextual_difference_count,
    )

    print(
        "Uncertain:",
        result.uncertain_count,
    )

    print(
        "Overall label:",
        result.overall_label.value,
    )

    print(
        "Confidence:",
        f"{result.confidence:.3f}",
    )

    print(
        "Rationale:",
        result.rationale,
    )

    assert result.evidence_count == 2
    assert result.language_count == 2
    assert result.pair_count == 1

    assert result.agreement_count == 1
    assert result.contradiction_count == 0
    assert result.contextual_difference_count == 0

    assert result.overall_label == (
        CrossLingualAgreementLabel.AGREEMENT
    )

    assert result.confidence == 0.90

    print("\nTEST 1 — Cross-lingual claim agreement: PASS")


    # ---------------------------------------------------------
    # TEST 2 — Contradictory multilingual evidence
    # ---------------------------------------------------------

    graph2 = ClaimEvidenceGraphBuilder(
        document_id="step16b_test_2"
    )

    graph2.add_claim(
        claim_id="c1",
        text="The system achieved 91 percent recall.",
        claim_type=ClaimType.QUANTITATIVE,
        source_chunk_id="chunk_en",
    )

    graph2.add_evidence(
        chunk_id="chunk_en",
        text=(
            "The experiment achieved 91 percent recall using hybrid retrieval."
        ),
    )

    graph2.add_evidence(
        chunk_id="chunk_ta",
        text=(
            "கலப்பு மீட்டெடுப்பைப் பயன்படுத்திய சோதனையில் மீட்டெடுப்பு விகிதம் 76 சதவீதமாக இருந்தது."
        ),
    )

    graph2.add_edge(
        claim_id="c1",
        chunk_id="chunk_en",
    )

    graph2.add_edge(
        claim_id="c1",
        chunk_id="chunk_ta",
    )

    result2 = analyzer.analyze_claim(
        graph=graph2,
        claim_id="c1",
        evidence_languages={
            "chunk_en": "English",
            "chunk_ta": "Tamil",
        },
    )

    print("\nTEST 2")
    print(
        "Overall label:",
        result2.overall_label.value,
    )
    print(
        "Confidence:",
        f"{result2.confidence:.3f}",
    )

    assert result2.pair_count == 1

    assert result2.contradiction_count == 1

    assert result2.overall_label == (
        CrossLingualAgreementLabel.CONTRADICTION
    )

    print(
        "TEST 2 — Cross-lingual contradiction: PASS"
    )


    # ---------------------------------------------------------
    # TEST 3 — No cross-lingual pair
    # ---------------------------------------------------------

    graph3 = ClaimEvidenceGraphBuilder(
        document_id="step16b_test_3"
    )

    graph3.add_claim(
        claim_id="c1",
        text="AERIS uses BM25.",
        claim_type=ClaimType.COMPONENT,
        source_chunk_id="chunk1",
    )

    graph3.add_evidence(
        chunk_id="chunk1",
        text="AERIS uses BM25.",
    )

    graph3.add_edge(
        claim_id="c1",
        chunk_id="chunk1",
    )

    result3 = analyzer.analyze_claim(
        graph=graph3,
        claim_id="c1",
        evidence_languages={
            "chunk1": "English",
        },
    )

    print("\nTEST 3")
    print(
        "Overall label:",
        result3.overall_label.value,
    )
    print(
        "Pair count:",
        result3.pair_count,
    )

    assert result3.pair_count == 0

    assert result3.overall_label == (
        CrossLingualAgreementLabel.UNCERTAIN
    )

    print(
        "TEST 3 — No cross-lingual pair: PASS"
    )


    # ---------------------------------------------------------
    # TEST 4 — Missing language validation
    # ---------------------------------------------------------

    try:

        analyzer.analyze_claim(
            graph=graph,
            claim_id="c1",
            evidence_languages={
                "chunk_en": "English",
            },
        )

        raise AssertionError(
            "Expected missing language error"
        )

    except ValueError:

        print(
            "\nTEST 4 — Missing language rejected: PASS"
        )


    # ---------------------------------------------------------
    # TEST 5 — Unknown claim
    # ---------------------------------------------------------

    try:

        analyzer.analyze_claim(
            graph=graph,
            claim_id="unknown",
            evidence_languages=languages,
        )

        raise AssertionError(
            "Expected unknown claim error"
        )

    except ValueError:

        print(
            "TEST 5 — Unknown claim rejected: PASS"
        )


    print("\nSTEP 16B TEST COMPLETE")


if __name__ == "__main__":
    main()
