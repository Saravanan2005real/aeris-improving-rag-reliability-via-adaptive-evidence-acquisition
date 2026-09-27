import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.verification.claim_verifier import (
    ClaimVerifier,
    VerificationLabel,
)


def print_result(result):

    print(f"\nLabel:      {result.label.value}")
    print(f"Strength:   {result.strength.value}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Evidence count: {result.evidence_count}")
    print(f"Rationale:  {result.rationale}")


def main():

    print("=" * 80)
    print("STEP 14B — MULTI-EVIDENCE CLAIM VERIFICATION")
    print("=" * 80)

    verifier = ClaimVerifier()

    # =========================================================
    # TEST 1 — COMPLEMENTARY EVIDENCE
    # =========================================================

    print("\n" + "-" * 80)
    print("TEST 1 — COMPLEMENTARY EVIDENCE")
    print("-" * 80)

    claim = (
        "AERIS uses a hybrid retrieval strategy "
        "combining dense and sparse retrieval."
    )

    evidence = [
        (
            "AERIS uses dense retrieval with "
            "all-MiniLM-L6-v2."
        ),
        (
            "AERIS uses BM25 for sparse retrieval."
        ),
    ]

    result = verifier.verify_multiple(
        claim=claim,
        evidence=evidence,
    )

    print_result(result)

    assert result.label == VerificationLabel.SUPPORTS
    assert result.evidence_count == 2
    assert 0.0 < result.confidence <= 1.0

    print(
        "[PASS] Complementary evidence jointly supports claim"
    )

    # =========================================================
    # TEST 2 — RELATED + SUPPORTING EVIDENCE
    # =========================================================

    print("\n" + "-" * 80)
    print("TEST 2 — RELATED + SUPPORTING EVIDENCE")
    print("-" * 80)

    claim = (
        "AERIS uses BM25 for sparse retrieval."
    )

    evidence = [
        (
            "AERIS combines dense and sparse retrieval "
            "methods."
        ),
        (
            "The sparse retrieval component uses BM25."
        ),
    ]

    result = verifier.verify_multiple(
        claim=claim,
        evidence=evidence,
    )

    print_result(result)

    assert result.label == VerificationLabel.SUPPORTS
    assert result.evidence_count == 2

    print(
        "[PASS] Direct evidence dominates merely related evidence"
    )

    # =========================================================
    # TEST 3 — MULTI-EVIDENCE CONTRADICTION
    # =========================================================

    print("\n" + "-" * 80)
    print("TEST 3 — MULTI-EVIDENCE CONTRADICTION")
    print("-" * 80)

    claim = (
        "AERIS uses BM25 for sparse retrieval."
    )

    evidence = [
        (
            "AERIS uses sparse retrieval."
        ),
        (
            "AERIS does not use BM25 for sparse retrieval. "
            "Its sparse retrieval component uses another "
            "ranking method."
        ),
    ]

    result = verifier.verify_multiple(
        claim=claim,
        evidence=evidence,
    )

    print_result(result)

    assert result.label == VerificationLabel.CONTRADICTS
    assert result.evidence_count == 2

    print(
        "[PASS] Explicit contradiction detected in evidence set"
    )

    # =========================================================
    # TEST 4 — MULTI-EVIDENCE RELATED ONLY
    # =========================================================

    print("\n" + "-" * 80)
    print("TEST 4 — RELATED EVIDENCE SET")
    print("-" * 80)

    claim = (
        "AERIS uses BM25 for sparse retrieval."
    )

    evidence = [
        (
            "The sky is blue."
        ),
        (
            "Grass is green."
        ),
    ]

    result = verifier.verify_multiple(
        claim=claim,
        evidence=evidence,
    )

    print_result(result)

    assert result.label == VerificationLabel.RELATED
    assert result.evidence_count == 2

    print(
        "[PASS] Related evidence does not become factual support"
    )

    # =========================================================
    # TEST 5 — EMPTY EVIDENCE
    # =========================================================

    print("\n" + "-" * 80)
    print("TEST 5 — EMPTY EVIDENCE")
    print("-" * 80)

    try:

        verifier.verify_multiple(
            claim="AERIS uses BM25.",
            evidence=[],
        )

        raise AssertionError(
            "Expected ValueError for empty evidence."
        )

    except ValueError:

        print(
            "[PASS] Empty evidence set rejected"
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    print("\n" + "=" * 80)
    print("STEP 14B TEST COMPLETE")
    print("=" * 80)

    print("[PASS] Complementary multi-evidence verification")
    print("[PASS] Related + supporting evidence handling")
    print("[PASS] Multi-evidence contradiction detection")
    print("[PASS] Related-only evidence handling")
    print("[PASS] Empty evidence validation")
    print("[PASS] Evidence count preservation")
    print("[PASS] Confidence remains bounded")
    print("=" * 80)


if __name__ == "__main__":
    main()
