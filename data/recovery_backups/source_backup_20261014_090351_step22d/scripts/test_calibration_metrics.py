import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.calibration.metrics import (
    CalibrationMetricsCalculator,
)


def main():

    print("\n=== STEP 17B TEST ===\n")

    calculator = CalibrationMetricsCalculator(
        bin_count=10
    )

    # =====================================================
    # TEST 1 — Perfect confidence
    # =====================================================

    confidences = [
        1.0,
        1.0,
        0.0,
        0.0,
    ]

    correctness = [
        True,
        True,
        False,
        False,
    ]

    brier = calculator.brier_score(
        confidences,
        correctness,
    )

    ece = calculator.expected_calibration_error(
        confidences,
        correctness,
    )

    assert brier == 0.0
    assert ece == 0.0

    print(
        "TEST 1 — Perfect calibration: PASS"
    )


    # =====================================================
    # TEST 2 — Known Brier score
    # =====================================================

    confidences = [
        0.9,
        0.8,
        0.2,
        0.1,
    ]

    correctness = [
        True,
        False,
        True,
        False,
    ]

    brier = calculator.brier_score(
        confidences,
        correctness,
    )

    expected = (
        (0.9 - 1.0) ** 2
        + (0.8 - 0.0) ** 2
        + (0.2 - 1.0) ** 2
        + (0.1 - 0.0) ** 2
    ) / 4

    assert abs(
        brier - expected
    ) < 1e-9

    print(
        "TEST 2 — Brier calculation: PASS"
    )


    # =====================================================
    # TEST 3 — ECE detects miscalibration
    # =====================================================

    confidences = [
        0.9,
        0.9,
        0.9,
        0.9,
    ]

    correctness = [
        True,
        False,
        False,
        False,
    ]

    ece = calculator.expected_calibration_error(
        confidences,
        correctness,
    )

    expected_ece = abs(
        0.9 - 0.25
    )

    assert abs(
        ece - expected_ece
    ) < 1e-9

    print(
        "TEST 3 — ECE calculation: PASS"
    )


    # =====================================================
    # TEST 4 — Complete metrics
    # =====================================================

    result = calculator.calculate(
        confidences=[
            0.9,
            0.8,
            0.7,
            0.2,
        ],
        correctness=[
            True,
            True,
            False,
            False,
        ],
    )

    assert result.sample_count == 4

    assert (
        0.0
        <= result.brier_score
        <= 1.0
    )

    assert (
        0.0
        <= result.expected_calibration_error
        <= 1.0
    )

    print(
        "TEST 4 — Complete metrics: PASS"
    )


    # =====================================================
    # TEST 5 — Invalid lengths
    # =====================================================

    rejected = False

    try:

        calculator.calculate(
            confidences=[0.9, 0.8],
            correctness=[True],
        )

    except ValueError:

        rejected = True

    assert rejected

    print(
        "TEST 5 — Length validation: PASS"
    )


    # =====================================================
    # TEST 6 — Invalid confidence
    # =====================================================

    rejected = False

    try:

        calculator.brier_score(
            confidences=[1.2],
            correctness=[True],
        )

    except ValueError:

        rejected = True

    assert rejected

    print(
        "TEST 6 — Confidence validation: PASS"
    )


    print(
        "\nSTEP 17B TEST COMPLETE"
    )


if __name__ == "__main__":
    main()
