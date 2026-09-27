import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.verification.cross_lingual_agreement import (
    CrossLingualEvidenceClassifier,
    CrossLingualAgreementLabel,
)


def main():

    print("\n=== STEP 16A TEST ===\n")

    classifier = CrossLingualEvidenceClassifier()

    # ---------------------------------------------------------
    # TEST 1 — Translation-equivalent evidence
    # ---------------------------------------------------------

    result = classifier.classify(
        evidence_a=(
            "AERIS uses hybrid retrieval combining dense "
            "retrieval and BM25."
        ),
        evidence_b=(
            "AERIS அடர்த்தியான மீட்டெடுப்பு மற்றும் BM25 ஐ "
            "இணைத்து கலப்பு மீட்டெடுப்பைப் பயன்படுத்துகிறது."
        ),
        language_a="English",
        language_b="Tamil",
    )

    print("TEST 1")
    print("Label:", result.label.value)
    print("Confidence:", f"{result.confidence:.3f}")
    print("Rationale:", result.rationale)

    assert result.label == (
        CrossLingualAgreementLabel.AGREEMENT
    )

    print("PASS\n")

    # ---------------------------------------------------------
    # TEST 2 — Cross-lingual contradiction
    # ---------------------------------------------------------

    result = classifier.classify(
        evidence_a=(
            "The experiment achieved 91 percent recall "
            "using hybrid retrieval."
        ),
        evidence_b=(
            "கலப்பு மீட்டெடுப்பைப் பயன்படுத்திய சோதனையில் "
            "மீட்டெடுப்பு விகிதம் 76 சதவீதமாக இருந்தது."
        ),
        language_a="English",
        language_b="Tamil",
    )

    print("TEST 2")
    print("Label:", result.label.value)
    print("Confidence:", f"{result.confidence:.3f}")
    print("Rationale:", result.rationale)

    assert result.label == (
        CrossLingualAgreementLabel.CONTRADICTION
    )

    print("PASS\n")

    # ---------------------------------------------------------
    # TEST 3 — Contextual difference
    # ---------------------------------------------------------

    result = classifier.classify(
        evidence_a=(
            "For short queries, the retrieval system achieved "
            "92 percent recall."
        ),
        evidence_b=(
            "நீண்ட வினவல்களுக்கு, மீட்டெடுப்பு அமைப்பு "
            "85 சதவீத மீட்டெடுப்பை அடைந்தது."
        ),
        language_a="English",
        language_b="Tamil",
    )

    print("TEST 3")
    print("Label:", result.label.value)
    print("Confidence:", f"{result.confidence:.3f}")
    print("Rationale:", result.rationale)

    assert result.label == (
        CrossLingualAgreementLabel.CONTEXTUAL_DIFFERENCE
    )

    print("PASS\n")

    # ---------------------------------------------------------
    # TEST 4 — Uncertain
    # ---------------------------------------------------------

    result = classifier.classify(
        evidence_a="The system performed well.",
        evidence_b="அமைப்பு நன்றாக இருந்தது.",
        language_a="English",
        language_b="Tamil",
    )

    print("TEST 4")
    print("Label:", result.label.value)
    print("Confidence:", f"{result.confidence:.3f}")
    print("Rationale:", result.rationale)

    assert result.label == (
        CrossLingualAgreementLabel.UNCERTAIN
    )

    print("PASS\n")

    # ---------------------------------------------------------
    # TEST 5 — Empty evidence validation
    # ---------------------------------------------------------

    try:
        classifier.classify(
            evidence_a="",
            evidence_b="AERIS uses BM25.",
            language_a="English",
            language_b="English",
        )

        raise AssertionError(
            "Expected empty evidence validation error"
        )

    except ValueError:
        print("TEST 5")
        print("Empty evidence rejected")
        print("PASS\n")

    print("STEP 16A TEST COMPLETE")


if __name__ == "__main__":
    main()
