from itertools import combinations

from pydantic import BaseModel, Field

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.contradiction_classifier import (
    ContextualContradictionClassifier,
    ContradictionLabel,
)


class ContradictionPairResult(BaseModel):
    claim_id: str
    claim: str
    evidence_a_chunk_id: str
    evidence_b_chunk_id: str
    label: ContradictionLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class ClaimContradictionReport(BaseModel):
    claim_id: str
    claim: str
    evidence_count: int = Field(ge=0)
    pair_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    contextual_difference_count: int = Field(ge=0)
    no_contradiction_count: int = Field(ge=0)
    uncertain_count: int = Field(ge=0)
    pairs: list[ContradictionPairResult] = Field(
        default_factory=list
    )


class ClaimContradictionAnalyzer:
    """
    Performs pairwise contextual contradiction analysis
    over all evidence connected to a claim.

    This layer does NOT modify the existing claim-evidence
    EdgeType values. It creates a separate contradiction report.
    """

    def __init__(
        self,
        classifier: ContextualContradictionClassifier | None = None,
    ):
        self.classifier = (
            classifier
            or ContextualContradictionClassifier()
        )

    def analyze_claim(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claim_id: str,
    ) -> ClaimContradictionReport:

        if claim_id not in graph.claims:
            raise ValueError(
                f"Unknown claim_id: {claim_id}"
            )

        claim = graph.claims[claim_id]

        edges = graph.get_claim_evidence(claim_id)

        evidence_ids = []

        for edge in edges:
            if edge.chunk_id not in graph.evidence:
                raise ValueError(
                    f"Missing evidence node: {edge.chunk_id}"
                )

            if edge.chunk_id not in evidence_ids:
                evidence_ids.append(edge.chunk_id)

        pairs = []

        for chunk_a_id, chunk_b_id in combinations(
            evidence_ids,
            2,
        ):
            evidence_a = graph.evidence[chunk_a_id]
            evidence_b = graph.evidence[chunk_b_id]

            result = self.classifier.classify(
                evidence_a=evidence_a.text,
                evidence_b=evidence_b.text,
            )

            pairs.append(
                ContradictionPairResult(
                    claim_id=claim_id,
                    claim=claim.text,
                    evidence_a_chunk_id=chunk_a_id,
                    evidence_b_chunk_id=chunk_b_id,
                    label=result.label,
                    confidence=result.confidence,
                    rationale=result.rationale,
                )
            )

        contradiction_count = sum(
            pair.label == ContradictionLabel.CONTRADICTION
            for pair in pairs
        )

        contextual_difference_count = sum(
            pair.label
            == ContradictionLabel.CONTEXTUAL_DIFFERENCE
            for pair in pairs
        )

        no_contradiction_count = sum(
            pair.label
            == ContradictionLabel.NO_CONTRADICTION
            for pair in pairs
        )

        uncertain_count = sum(
            pair.label == ContradictionLabel.UNCERTAIN
            for pair in pairs
        )

        return ClaimContradictionReport(
            claim_id=claim_id,
            claim=claim.text,
            evidence_count=len(evidence_ids),
            pair_count=len(pairs),
            contradiction_count=contradiction_count,
            contextual_difference_count=(
                contextual_difference_count
            ),
            no_contradiction_count=no_contradiction_count,
            uncertain_count=uncertain_count,
            pairs=pairs,
        )
