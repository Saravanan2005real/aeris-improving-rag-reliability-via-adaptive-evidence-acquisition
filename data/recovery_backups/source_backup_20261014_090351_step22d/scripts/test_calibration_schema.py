import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ),
)

from app.calibration.schemas import (
    CalibrationLabel,
    CalibrationRecord,
)


def main():

    print("\n=== STEP 17A TEST ===\n")

    # =====================================================
    # TEST 1 — Correct supported prediction
    # =====================================================

    record = CalibrationRecord(
        record_id="r1",
        claim_id="c1",
        claim="AERIS uses BM25.",
        evidence_chunk_ids=["chunk1", "chunk2"],
        predicted_label=CalibrationLabel.SUPPORTED,
        raw_confidence=0.90,
        ground_truth_label=CalibrationLabel.SUPPORTED,
    )

    result = record.compute_correctness()

    assert result is True
    assert record.correct is True
    assert record.raw_confidence == 0.90
    assert record.calibrated_confidence is None

    print(
        "TEST 1 — Correct prediction: PASS"
    )


    # =====================================================
    # TEST 2 — Incorrect prediction
    # =====================================================

    record2 = CalibrationRecord(
        record_id="r2",
        claim_id="c2",
        claim="AERIS uses BM25.",
        evidence_chunk_ids=["chunk3"],
        predicted_label=CalibrationLabel.SUPPORTED,
        raw_confidence=0.90,
        ground_truth_label=CalibrationLabel.CONTRADICTED,
    )

    result2 = record2.compute_correctness()

    assert result2 is False
    assert record2.correct is False

    print(
        "TEST 2 — Incorrect prediction: PASS"
    )


    # =====================================================
    # TEST 3 — Confidence bounds
    # =====================================================

    invalid = False

    try:
        CalibrationRecord(
            record_id="r3",
            claim_id="c3",
            claim="Invalid confidence.",
            evidence_chunk_ids=["chunk1"],
            predicted_label=CalibrationLabel.SUPPORTED,
            raw_confidence=1.5,
            ground_truth_label=CalibrationLabel.SUPPORTED,
        )
    except ValueError:
        invalid = True

    assert invalid

    print(
        "TEST 3 — Confidence bounds: PASS"
    )


    # =====================================================
    # TEST 4 — Evidence required
    # =====================================================

    invalid_evidence = False

    try:
        CalibrationRecord(
            record_id="r4",
            claim_id="c4",
            claim="No evidence.",
            evidence_chunk_ids=[],
            predicted_label=CalibrationLabel.INSUFFICIENT,
            raw_confidence=0.35,
            ground_truth_label=CalibrationLabel.INSUFFICIENT,
        )
    except ValueError:
        invalid_evidence = True

    assert invalid_evidence

    print(
        "TEST 4 — Evidence requirement: PASS"
    )


    # =====================================================
    # TEST 5 — Calibrated confidence can be added later
    # =====================================================

    record3 = CalibrationRecord(
        record_id="r5",
        claim_id="c5",
        claim="AERIS uses hybrid retrieval.",
        evidence_chunk_ids=["chunk1"],
        predicted_label=CalibrationLabel.SUPPORTED,
        raw_confidence=0.90,
        ground_truth_label=CalibrationLabel.SUPPORTED,
        calibrated_confidence=0.84,
    )

    assert record3.calibrated_confidence == 0.84

    print(
        "TEST 5 — Calibrated confidence field: PASS"
    )


    print(
        "\nSTEP 17A TEST COMPLETE"
    )


if __name__ == "__main__":
    main()
