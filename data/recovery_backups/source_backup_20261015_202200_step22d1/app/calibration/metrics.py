from pydantic import BaseModel, Field


class CalibrationMetrics(BaseModel):
    sample_count: int = Field(ge=1)

    brier_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    expected_calibration_error: float = Field(
        ge=0.0,
        le=1.0,
    )


class CalibrationMetricsCalculator:

    def __init__(self, bin_count: int = 10):

        if bin_count < 1:
            raise ValueError(
                "bin_count must be >= 1"
            )

        self.bin_count = bin_count

    def brier_score(
        self,
        confidences: list[float],
        correctness: list[bool],
    ) -> float:

        if not confidences:
            raise ValueError(
                "confidences cannot be empty"
            )

        if len(confidences) != len(correctness):
            raise ValueError(
                "confidences and correctness "
                "must have the same length"
            )

        for confidence in confidences:

            if not 0.0 <= confidence <= 1.0:
                raise ValueError(
                    "confidence must be between 0 and 1"
                )

        total = 0.0

        for confidence, correct in zip(
            confidences,
            correctness,
        ):

            target = 1.0 if correct else 0.0

            total += (
                confidence - target
            ) ** 2

        return total / len(confidences)

    def expected_calibration_error(
        self,
        confidences: list[float],
        correctness: list[bool],
    ) -> float:

        if not confidences:
            raise ValueError(
                "confidences cannot be empty"
            )

        if len(confidences) != len(correctness):
            raise ValueError(
                "confidences and correctness "
                "must have the same length"
            )

        bins = [
            []
            for _ in range(self.bin_count)
        ]

        for confidence, correct in zip(
            confidences,
            correctness,
        ):

            if not 0.0 <= confidence <= 1.0:
                raise ValueError(
                    "confidence must be between 0 and 1"
                )

            index = min(
                int(
                    confidence
                    * self.bin_count
                ),
                self.bin_count - 1,
            )

            bins[index].append(
                (confidence, correct)
            )

        ece = 0.0
        total = len(confidences)

        for bucket in bins:

            if not bucket:
                continue

            average_confidence = (
                sum(
                    confidence
                    for confidence, _
                    in bucket
                )
                / len(bucket)
            )

            accuracy = (
                sum(
                    1.0
                    if correct
                    else 0.0
                    for _, correct
                    in bucket
                )
                / len(bucket)
            )

            ece += (
                len(bucket) / total
            ) * abs(
                average_confidence
                - accuracy
            )

        return ece

    def calculate(
        self,
        confidences: list[float],
        correctness: list[bool],
    ) -> CalibrationMetrics:

        if not confidences:
            raise ValueError(
                "calibration data cannot be empty"
            )

        return CalibrationMetrics(
            sample_count=len(confidences),
            brier_score=self.brier_score(
                confidences,
                correctness,
            ),
            expected_calibration_error=(
                self.expected_calibration_error(
                    confidences,
                    correctness,
                )
            ),
        )
