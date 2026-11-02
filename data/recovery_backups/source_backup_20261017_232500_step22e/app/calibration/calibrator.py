from typing import Optional

from sklearn.isotonic import IsotonicRegression

from app.calibration.schemas import CalibrationRecord


class ConfidenceCalibrator:
    """
    Learns a monotonic mapping from raw verification
    confidence to empirical correctness probability.

    Raw confidence is treated as a score, not as a
    calibrated probability.
    """

    def __init__(self):

        self.model = IsotonicRegression(
            y_min=0.0,
            y_max=1.0,
            increasing=True,
            out_of_bounds="clip",
        )

        self._fitted = False

    @property
    def fitted(self) -> bool:
        return self._fitted

    def fit(
        self,
        records: list[CalibrationRecord],
    ) -> None:

        if not records:
            raise ValueError(
                "Calibration records cannot be empty"
            )

        confidences = []
        targets = []

        for record in records:

            if record.correct is None:
                record.compute_correctness()

            confidences.append(
                record.raw_confidence
            )

            targets.append(
                1.0 if record.correct else 0.0
            )

        if len(set(confidences)) < 2:
            raise ValueError(
                "Calibration requires at least "
                "two distinct confidence values"
            )

        if len(set(targets)) < 2:
            raise ValueError(
                "Calibration requires both "
                "correct and incorrect examples"
            )

        self.model.fit(
            confidences,
            targets,
        )

        self._fitted = True

    def calibrate(
        self,
        raw_confidence: float,
    ) -> float:

        if not self._fitted:
            raise RuntimeError(
                "Calibrator must be fitted before "
                "calibration"
            )

        if not 0.0 <= raw_confidence <= 1.0:
            raise ValueError(
                "raw_confidence must be between 0 and 1"
            )

        calibrated = self.model.predict(
            [raw_confidence]
        )[0]

        return float(calibrated)

    def calibrate_record(
        self,
        record: CalibrationRecord,
    ) -> CalibrationRecord:

        calibrated = self.calibrate(
            record.raw_confidence
        )

        record.calibrated_confidence = calibrated

        return record

    def calibrate_records(
        self,
        records: list[CalibrationRecord],
    ) -> list[CalibrationRecord]:

        if not records:
            raise ValueError(
                "Calibration records cannot be empty"
            )

        return [
            self.calibrate_record(record)
            for record in records
        ]
