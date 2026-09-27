from pydantic import BaseModel, Field


class VerificationEfficiencyReport(BaseModel):
    candidate_count: int = Field(ge=0)
    selected_count: int = Field(ge=0)
    verified_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)

    budget: int = Field(ge=0)

    verification_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    skip_rate: float = Field(
        ge=0.0,
        le=1.0,
    )

    budget_utilization: float = Field(
        ge=0.0,
        le=1.0,
    )

    estimated_verification_calls_saved: int = Field(
        ge=0
    )


class VerificationEfficiencyCalculator:
    """
    Calculates the efficiency of selective verification.

    The baseline assumes that every candidate claim would
    otherwise receive one verification call.
    """

    def calculate(
        self,
        candidate_count: int,
        selected_count: int,
        verified_count: int,
        budget: int,
    ) -> VerificationEfficiencyReport:

        if candidate_count < 0:
            raise ValueError(
                "candidate_count must be non-negative"
            )

        if selected_count < 0:
            raise ValueError(
                "selected_count must be non-negative"
            )

        if verified_count < 0:
            raise ValueError(
                "verified_count must be non-negative"
            )

        if budget < 0:
            raise ValueError(
                "budget must be non-negative"
            )

        if selected_count > candidate_count:
            raise ValueError(
                "selected_count cannot exceed candidate_count"
            )

        if verified_count > selected_count:
            raise ValueError(
                "verified_count cannot exceed selected_count"
            )

        if candidate_count == 0:
            return VerificationEfficiencyReport(
                candidate_count=0,
                selected_count=0,
                verified_count=0,
                skipped_count=0,
                budget=budget,
                verification_rate=0.0,
                skip_rate=0.0,
                budget_utilization=0.0,
                estimated_verification_calls_saved=0,
            )

        skipped_count = candidate_count - selected_count

        verification_rate = (
            verified_count / candidate_count
        )

        skip_rate = (
            skipped_count / candidate_count
        )

        budget_utilization = (
            verified_count / budget
            if budget > 0
            else 0.0
        )

        estimated_calls_saved = (
            candidate_count - verified_count
        )

        return VerificationEfficiencyReport(
            candidate_count=candidate_count,
            selected_count=selected_count,
            verified_count=verified_count,
            skipped_count=skipped_count,
            budget=budget,
            verification_rate=verification_rate,
            skip_rate=skip_rate,
            budget_utilization=min(
                budget_utilization,
                1.0,
            ),
            estimated_verification_calls_saved=(
                estimated_calls_saved
            ),
        )
