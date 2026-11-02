import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.calibration.calibrator import (
    ConfidenceCalibrator,
)
from app.calibration.schemas import (
    CalibrationLabel,
    CalibrationRecord,
)


def make_record(
    record_id: str,
    confidence: float,
    predicted: CalibrationLabel,
    actual: CalibrationLabel,
) -> CalibrationRecord:

    return CalibrationRecord(
        record_id=record_id,
        claim_id=f"claim_{record_id}",
        claim="Test claim",
        evidence_chunk_ids=["chunk1"],
        predicted_label=predicted,
        raw_confidence=confidence,
        ground_truth_label=actual,
    )


def main():

    print("\n=== STEP 17C TEST ===\n")

    # =====================================================
    # Calibration dataset
    # =====================================================

    records = [
        make_record(
            "r1",
            0.10,
            CalibrationLabel.INSUFFICIENT,
            CalibrationLabel.INSUFFICIENT,
        ),
        make_record(
            "r2",
            0.20,
            CalibrationLabel.INSUFFICIENT,
            CalibrationLabel.CONTRADICTED,
        ),
        make_record(
            "r3",
            0.35,
            CalibrationLabel.INSUFFICIENT,
            CalibrationLabel.INSUFFICIENT,
        ),
        make_record(
            "r4",
            0.50,
            CalibrationLabel.SUPPORTED,
            CalibrationLabel.CONTRADICTED,
        ),
        make_record(
            "r5",
            0.65,
            CalibrationLabel.SUPPORTED,
            CalibrationLabel.SUPPORTED,
        ),
        make_record(
            "r6",
            0.75,
            CalibrationLabel.SUPPORTED,
            CalibrationLabel.SUPPORTED,
        ),
        make_record(
            "r7",
            0.85,
            CalibrationLabel.SUPPORTED,
            CalibrationLabel.SUPPORTED,
        ),
        make_record(
            "r8",
            0.95,
            CalibrationLabel.SUPPORTED,
            CalibrationLabel.SUPPORTED,
        ),
    ]

    # =====================================================
    # TEST 1 — Fit
    # =====================================================

    calibrator = ConfidenceCalibrator()

    calibrator.fit(records)

    assert calibrator.fitted is True

    print(
        "TEST 1 — Model fitting: PASS"
    )


    # =====================================================
    # TEST 2 — Calibration output bounds
    # =====================================================

    calibrated = calibrator.calibrate(
        0.90
    )

    assert 0.0 <= calibrated <= 1.0

    print(
        "TEST 2 — Calibrated confidence bounds: PASS"
    )

    print(
        f"Raw confidence: 0.900"
    )

    print(
        f"Calibrated confidence: "
        f"{calibrated:.4f}"
    )


    # =====================================================
    # TEST 3 — Monotonicity
    # =====================================================

    test_confidences = [
        0.10,
        0.30,
        0.50,
        0.70,
        0.90,
    ]

    calibrated_values = [
        calibrator.calibrate(value)
        for value in test_confidences
    ]

    for previous, current in zip(
        calibrated_values,
        calibrated_values[1:],
    ):
        assert current >= previous

    print(
        "TEST 3 — Monotonic calibration: PASS"
    )


    # =====================================================
    # TEST 4 — Record calibration
    # =====================================================

    record = make_record(
        "test",
        0.90,
        CalibrationLabel.SUPPORTED,
        CalibrationLabel.SUPPORTED,
    )

    assert record.calibrated_confidence is None

    calibrator.calibrate_record(record)

    assert (
        record.calibrated_confidence is not None
    )

    assert (
        0.0
        <= record.calibrated_confidence
        <= 1.0
    )

    print(
        "TEST 4 — Record calibration: PASS"
    )


    # =====================================================
    # TEST 5 — Batch calibration
    # =====================================================

    calibrated_records = (
        calibrator.calibrate_records(records)
    )

    assert len(calibrated_records) == len(records)

    assert all(
        record.calibrated_confidence is not None
        for record in calibrated_records
    )

    print(
        "TEST 5 — Batch calibration: PASS"
    )


    # =====================================================
    # TEST 6 — Reject calibration before fitting
    # =====================================================

    unfitted = ConfidenceCalibrator()

    rejected = False

    try:
        unfitted.calibrate(0.90)
    except RuntimeError:
        rejected = True

    assert rejected

    print(
        "TEST 6 — Unfitted model rejection: PASS"
    )


    # =====================================================
    # TEST 7 — Invalid confidence
    # =====================================================

    rejected = False

    try:
        calibrator.calibrate(1.5)
    except ValueError:
        rejected = True

    assert rejected

    print(
        "TEST 7 — Confidence validation: PASS"
    )


    print(
        "\nSTEP 17C TEST COMPLETE"
    )


if __name__ == "__main__":
    main()
