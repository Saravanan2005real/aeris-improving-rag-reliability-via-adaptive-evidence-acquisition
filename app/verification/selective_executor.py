from typing import List

from pydantic import BaseModel, Field

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.graph_verifier import (
    GraphClaimVerifier,
    GraphVerificationResult,
)
from app.verification.selective_verification import (
    SelectiveVerificationSelector,
    VerificationCandidate,
)


class SelectiveVerificationReport(BaseModel):
    candidate_count: int = Field(ge=0)
    selected_count: int = Field(ge=0)
    verified_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    budget: int = Field(ge=0)

    candidates: List[VerificationCandidate] = Field(
        default_factory=list
    )

    selected_claim_ids: List[str] = Field(
        default_factory=list
    )

    verification_results: List[GraphVerificationResult] = Field(
        default_factory=list
    )


class SelectiveVerificationExecutor:
    """
    Executes deeper verification only for claims selected
    by the selective verification policy.

    The executor itself does not decide priority.
    Priority is delegated to SelectiveVerificationSelector.
    """

    def __init__(
        self,
        verifier: GraphClaimVerifier,
        selector: SelectiveVerificationSelector | None = None,
    ):
        self.verifier = verifier
        self.selector = selector or SelectiveVerificationSelector()

    def execute(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claims: list[dict],
        budget: int,
    ) -> SelectiveVerificationReport:

        if budget < 0:
            raise ValueError("budget must be non-negative")

        candidates = self.selector.evaluate(
            graph=graph,
            claims=claims,
        )

        selected = self.selector.select(
            candidates=candidates,
            budget=budget,
        )

        verification_results = []

        for candidate in selected:
            result = self.verifier.verify_claim(
                graph=graph,
                claim_id=candidate.claim_id,
            )

            verification_results.append(result)

        selected_ids = [
            candidate.claim_id
            for candidate in selected
        ]

        skipped_count = sum(
            1
            for candidate in candidates
            if candidate.claim_id not in selected_ids
        )

        return SelectiveVerificationReport(
            candidate_count=len(candidates),
            selected_count=len(selected),
            verified_count=len(verification_results),
            skipped_count=skipped_count,
            budget=budget,
            candidates=candidates,
            selected_claim_ids=selected_ids,
            verification_results=verification_results,
        )
