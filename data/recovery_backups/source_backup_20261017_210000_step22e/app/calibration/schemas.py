from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CalibrationLabel(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"


class CalibrationRecord(BaseModel):
    record_id: str

    claim_id: str
    claim: str

    evidence_chunk_ids: list[str] = Field(
        min_length=1
    )

    predicted_label: CalibrationLabel

    raw_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    ground_truth_label: CalibrationLabel

    correct: Optional[bool] = None

    calibrated_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    def compute_correctness(self) -> bool:
        self.correct = (
            self.predicted_label
            == self.ground_truth_label
        )

        return self.correct
