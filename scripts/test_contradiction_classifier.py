import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.verification.contradiction_classifier import (
    ContextualContradictionClassifier,
    ContradictionLabel,
)


classifier = ContextualContradictionClassifier()


def test_genuine_contradiction():
    print("\n" + "-" * 80)
    print("TEST 1 — GENUINE CONTRADICTION")
    print("-" * 80)

    result = classifier.classify(
        evidence_a=(
            "The system achieved 94% accuracy."
        ),
        evidence_b=(
            "The system achieved 87% accuracy."
        ),
    )

    print(f"Label: {result.label}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Rationale: {result.rationale}")

    assert result.label == ContradictionLabel.CONTRADICTION

    print("[PASS] Same context + incompatible values -> CONTRADICTION")


def test_contextual_difference():
    print("\n" + "-" * 80)
    print("TEST 2 — CONTEXTUAL DIFFERENCE")
    print("-" * 80)

    result = classifier.classify(
        evidence_a=(
            "BM25 performs better for short queries."
        ),
        evidence_b=(
            "Dense retrieval performs better for long queries."
        ),
    )

    print(f"Label: {result.label}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Rationale: {result.rationale}")

    assert result.label == ContradictionLabel.CONTEXTUAL_DIFFERENCE

    print("[PASS] Different conditions -> CONTEXTUAL_DIFFERENCE")


def test_no_contradiction():
    print("\n" + "-" * 80)
    print("TEST 3 — NO CONTRADICTION")
    print("-" * 80)

    result = classifier.classify(
        evidence_a=(
            "The system uses BM25 for sparse retrieval."
        ),
        evidence_b=(
            "The system uses dense embeddings for semantic retrieval."
        ),
    )

    print(f"Label: {result.label}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Rationale: {result.rationale}")

    assert result.label == ContradictionLabel.NO_CONTRADICTION

    print("[PASS] Compatible statements -> NO_CONTRADICTION")


def test_uncertain():
    print("\n" + "-" * 80)
    print("TEST 4 — UNCERTAIN")
    print("-" * 80)

    result = classifier.classify(
        evidence_a=(
            "The model performed better in the evaluation."
        ),
        evidence_b=(
            "The model performed worse in the evaluation."
        ),
    )

    print(f"Label: {result.label}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Rationale: {result.rationale}")

    assert result.label == ContradictionLabel.UNCERTAIN

    print("[PASS] Missing comparison context -> UNCERTAIN")


def test_empty_evidence():
    print("\n" + "-" * 80)
    print("TEST 5 — EMPTY EVIDENCE")
    print("-" * 80)

    try:
        classifier.classify(
            evidence_a="",
            evidence_b="Some evidence",
        )

        raise AssertionError("Expected ValueError")

    except ValueError as exc:
        print(f"Expected error: {exc}")

    print("[PASS] Empty evidence rejected")


if __name__ == "__main__":

    print("=" * 80)
    print("STEP 15A — CONTEXTUAL CONTRADICTION CLASSIFICATION")
    print("=" * 80)

    test_genuine_contradiction()
    test_contextual_difference()
    test_no_contradiction()
    test_uncertain()
    test_empty_evidence()

    print("\n" + "=" * 80)
    print("STEP 15A TEST COMPLETE")
    print("=" * 80)
    print("[PASS] Genuine contradiction detection")
    print("[PASS] Contextual difference detection")
    print("[PASS] No-contradiction detection")
    print("[PASS] Uncertain classification")
    print("[PASS] Empty evidence validation")
    print("=" * 80)
