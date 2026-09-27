import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.calibration.calibrator import ConfidenceCalibrator
from app.calibration.metrics import CalibrationMetricsCalculator
from app.calibration.schemas import (
    CalibrationLabel,
    CalibrationRecord,
)


def make_record(
    record_id: str,
    confidence: float,
    correct: bool,
) -> CalibrationRecord:

    label = (
        CalibrationLabel.SUPPORTED
        if correct
        else CalibrationLabel.CONTRADICTED
    )

    return CalibrationRecord(
        record_id=record_id,
        claim_id=f"claim_{record_id}",
        claim=f"Calibration validation claim {record_id}",
        evidence_chunk_ids=["chunk1"],
        predicted_label=label,
        raw_confidence=confidence,
        ground_truth_label=label
        if correct
        else (
            CalibrationLabel.CONTRADICTED
            if label == CalibrationLabel.SUPPORTED
            else CalibrationLabel.SUPPORTED
        ),
    )


def main():

    print("\n=== STEP 17D TEST ===\n")

    # =====================================================
    # Calibration dataset
    # =====================================================

    records = [
        make_record("r1", 0.10, False),
        make_record("r2", 0.20, False),
        make_record("r3", 0.30, True),
        make_record("r4", 0.40, False),
        make_record("r5", 0.50, True),
        make_record("r6", 0.60, True),
        make_record("r7", 0.70, True),
        make_record("r8", 0.80, True),
        make_record("r9", 0.90, True),
        make_record("r10", 0.95, True),
    ]

    for record in records:
        record.compute_correctness()

    correctness = [
        record.correct
        for record in records
    ]

    raw_confidences = [
        record.raw_confidence
        for record in records
    ]

    # =====================================================
    # TEST 1 — Raw metrics
    # =====================================================

    metrics = CalibrationMetricsCalculator(
        bin_count=10
    )

    raw_metrics = metrics.calculate(
        confidences=raw_confidences,
        correctness=correctness,
    )

    print("TEST 1 — Raw calibration metrics: PASS")

    print(
        f"Raw Brier Score: "
        f"{raw_metrics.brier_score:.4f}"
    )

    print(
        f"Raw ECE: "
        f"{raw_metrics.expected_calibration_error:.4f}"
    )


    # =====================================================
    # TEST 2 — Fit calibrator
    # =====================================================

    calibrator = ConfidenceCalibrator()

    calibrator.fit(records)

    assert calibrator.fitted

    print(
        "TEST 2 — Calibration model fitting: PASS"
    )


    # =====================================================
    # TEST 3 — Apply calibration
    # =====================================================

    calibrated_records = (
        calibrator.calibrate_records(
            records
        )
    )

    calibrated_confidences = [
        record.calibrated_confidence
        for record in calibrated_records
    ]

    assert all(
        confidence is not None
        for confidence
        in calibrated_confidences
    )

    print(
        "TEST 3 — Calibration application: PASS"
    )


    # =====================================================
    # TEST 4 — Calibrated metrics
    # =====================================================

    calibrated_metrics = metrics.calculate(
        confidences=calibrated_confidences,
        correctness=correctness,
    )

    print(
        "TEST 4 — Calibrated metrics: PASS"
    )

    print(
        f"Calibrated Brier Score: "
        f"{calibrated_metrics.brier_score:.4f}"
    )

    print(
        f"Calibrated ECE: "
        f"{calibrated_metrics.expected_calibration_error:.4f}"
    )


    # =====================================================
    # TEST 5 — Bounds
    # =====================================================

    assert all(
        0.0 <= confidence <= 1.0
        for confidence
        in calibrated_confidences
    )

    print(
        "TEST 5 — Calibrated confidence bounds: PASS"
    )


    # =====================================================
    # TEST 6 — Calibration is monotonic
    # =====================================================

    ordered = sorted(
        zip(
            raw_confidences,
            calibrated_confidences,
        )
    )

    for (_, previous), (_, current) in zip(
        ordered,
        ordered[1:],
    ):

        assert current >= previous

    print(
        "TEST 6 — Monotonicity: PASS"
    )


    # =====================================================
    # TEST 7 — Improvement calculation
    # =====================================================

    brier_change = (
        raw_metrics.brier_score
        - calibrated_metrics.brier_score
    )

    ece_change = (
        raw_metrics.expected_calibration_error
        - calibrated_metrics.expected_calibration_error
    )

    print(
        "\nCalibration effect:"
    )

    print(
        f"Brier change: "
        f"{brier_change:+.4f}"
    )

    print(
        f"ECE change: "
        f"{ece_change:+.4f}"
    )

    print(
        "\nTEST 7 — Improvement measurement: PASS"
    )


    # =====================================================
    # TEST 8 — Print confidence mapping
    # =====================================================

    print(
        "\nConfidence mapping:"
    )

    for raw, calibrated in ordered:

        print(
            f"{raw:.2f} -> "
            f"{calibrated:.4f}"
        )

    print(
        "\nTEST 8 — Mapping inspection: PASS"
    )


    print(
        "\nSTEP 17D TEST COMPLETE"
    )


if __name__ == "__main__":
    main()
