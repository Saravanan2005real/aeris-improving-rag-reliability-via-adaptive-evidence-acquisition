import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.verification.verification_efficiency import (
    VerificationEfficiencyCalculator,
)


def test_full_verification():

    calculator = VerificationEfficiencyCalculator()

    result = calculator.calculate(
        candidate_count=10,
        selected_count=10,
        verified_count=10,
        budget=10,
    )

    assert result.verification_rate == 1.0
    assert result.skip_rate == 0.0
    assert result.budget_utilization == 1.0
    assert result.estimated_verification_calls_saved == 0

    print(
        "TEST 1 — Full verification baseline: PASS"
    )


def test_selective_verification():

    calculator = VerificationEfficiencyCalculator()

    result = calculator.calculate(
        candidate_count=10,
        selected_count=4,
        verified_count=4,
        budget=4,
    )

    assert result.skipped_count == 6
    assert result.verification_rate == 0.4
    assert result.skip_rate == 0.6
    assert result.budget_utilization == 1.0
    assert result.estimated_verification_calls_saved == 6

    print(
        "TEST 2 — Selective verification savings: PASS"
    )


def test_partial_budget_usage():

    calculator = VerificationEfficiencyCalculator()

    result = calculator.calculate(
        candidate_count=10,
        selected_count=3,
        verified_count=3,
        budget=5,
    )

    assert result.verification_rate == 0.3
    assert result.skip_rate == 0.7
    assert result.budget_utilization == 0.6
    assert result.estimated_verification_calls_saved == 7

    print(
        "TEST 3 — Partial budget utilization: PASS"
    )


def test_zero_budget():

    calculator = VerificationEfficiencyCalculator()

    result = calculator.calculate(
        candidate_count=10,
        selected_count=0,
        verified_count=0,
        budget=0,
    )

    assert result.verification_rate == 0.0
    assert result.skip_rate == 1.0
    assert result.budget_utilization == 0.0
    assert result.estimated_verification_calls_saved == 10

    print(
        "TEST 4 — Zero-budget accounting: PASS"
    )


def test_empty_candidates():

    calculator = VerificationEfficiencyCalculator()

    result = calculator.calculate(
        candidate_count=0,
        selected_count=0,
        verified_count=0,
        budget=5,
    )

    assert result.candidate_count == 0
    assert result.skipped_count == 0
    assert result.verification_rate == 0.0
    assert result.skip_rate == 0.0
    assert result.estimated_verification_calls_saved == 0

    print(
        "TEST 5 — Empty candidate set: PASS"
    )


def test_invalid_selected_count():

    calculator = VerificationEfficiencyCalculator()

    try:
        calculator.calculate(
            candidate_count=3,
            selected_count=4,
            verified_count=4,
            budget=4,
        )
    except ValueError:
        print(
            "TEST 6 — Invalid selected count rejection: PASS"
        )
        return

    raise AssertionError(
        "Invalid selected count was not rejected"
    )


def test_invalid_verified_count():

    calculator = VerificationEfficiencyCalculator()

    try:
        calculator.calculate(
            candidate_count=3,
            selected_count=2,
            verified_count=3,
            budget=3,
        )
    except ValueError:
        print(
            "TEST 7 — Invalid verified count rejection: PASS"
        )
        return

    raise AssertionError(
        "Invalid verified count was not rejected"
    )


if __name__ == "__main__":

    print("\n=== STEP 18C TEST ===")

    test_full_verification()
    test_selective_verification()
    test_partial_budget_usage()
    test_zero_budget()
    test_empty_candidates()
    test_invalid_selected_count()
    test_invalid_verified_count()

    print("\nSTEP 18C TEST COMPLETE")
