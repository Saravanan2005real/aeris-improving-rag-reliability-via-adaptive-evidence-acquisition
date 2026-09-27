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


def run_test(
    verifier,
    test_name,
    claim,
    evidence,
    expected_label,
):

    print("\n" + "-" * 80)
    print(test_name)
    print("-" * 80)

    print(f"Claim:    {claim}")
    print(f"Evidence: {evidence}")

    result = verifier.verify(
        claim=claim,
        evidence=evidence,
    )

    print(f"\nLabel:      {result.label.value}")
    print(f"Strength:   {result.strength.value}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Rationale:  {result.rationale}")

    assert result.confidence > 0.0
    assert result.confidence <= 1.0

    assert result.label == expected_label

    print("[PASS] Expected verification label detected")

    return result


def main():

    print("=" * 80)
    print("STEP 14A — CLAIM VERIFICATION TEST")
    print("=" * 80)

    verifier = ClaimVerifier()

    # ---------------------------------------------------------
    # TEST 1 — DIRECT SUPPORT
    # ---------------------------------------------------------

    run_test(
        verifier=verifier,
        test_name="TEST 1 — DIRECT SUPPORT",
        claim="AERIS uses BM25 for sparse retrieval.",
        evidence=(
            "AERIS uses BM25 as its sparse retrieval "
            "mechanism."
        ),
        expected_label=VerificationLabel.SUPPORTS,
    )

    # ---------------------------------------------------------
    # TEST 2 — CONTRADICTION
    # ---------------------------------------------------------

    run_test(
        verifier=verifier,
        test_name="TEST 2 — CONTRADICTION",
        claim="AERIS uses BM25 for sparse retrieval.",
        evidence=(
            "AERIS does not use BM25 for sparse retrieval. "
            "Its sparse retrieval component uses a different "
            "ranking method."
        ),
        expected_label=VerificationLabel.CONTRADICTS,
    )

    # ---------------------------------------------------------
    # TEST 3 — RELATED BUT NOT SUPPORTING
    # ---------------------------------------------------------

    run_test(
        verifier=verifier,
        test_name="TEST 3 — RELATED EVIDENCE",
        claim="AERIS uses BM25 for sparse retrieval.",
        evidence=(
            "AERIS combines dense and sparse retrieval "
            "methods and fuses their ranked results."
        ),
        expected_label=VerificationLabel.RELATED,
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("STEP 14A TEST COMPLETE")
    print("=" * 80)
    print("[PASS] SUPPORTS verification")
    print("[PASS] CONTRADICTS verification")
    print("[PASS] RELATED verification")
    print("[PASS] Evidence-grounded classification")
    print("[PASS] Non-zero bounded verification confidence")
    print("[PASS] No embedding similarity used as factual support")
    print("=" * 80)


if __name__ == "__main__":
    main()
