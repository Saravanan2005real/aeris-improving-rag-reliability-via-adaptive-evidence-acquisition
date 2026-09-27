from itertools import combinations

from pydantic import BaseModel, Field

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.contradiction_classifier import (
    ContextualContradictionClassifier,
    ContradictionLabel,
)


class CrossClaimContradictionResult(BaseModel):
    claim_a_id: str
    claim_a: str
    evidence_a_chunk_id: str

    claim_b_id: str
    claim_b: str
    evidence_b_chunk_id: str

    label: ContradictionLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class CrossClaimContradictionReport(BaseModel):
    document_id: str
    claim_count: int = Field(ge=0)
    evidence_pair_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    contextual_difference_count: int = Field(ge=0)
    no_contradiction_count: int = Field(ge=0)
    uncertain_count: int = Field(ge=0)

    conflicts: list[CrossClaimContradictionResult] = Field(
        default_factory=list
    )


class CrossClaimContradictionAnalyzer:
    """
    Maps contextual contradictions between evidence belonging
    to different claims.

    Evidence contradictions are kept separate from claim-level
    verification status. A detected evidence conflict is reported
    as a potential cross-claim conflict rather than automatically
    declaring the claims contradictory.
    """

    def __init__(
        self,
        classifier: ContextualContradictionClassifier | None = None,
    ):
        self.classifier = (
            classifier
            or ContextualContradictionClassifier()
        )

    def analyze(
        self,
        graph: ClaimEvidenceGraphBuilder,
    ) -> CrossClaimContradictionReport:

        claim_ids = list(graph.claims.keys())

        results = []

        # Compare every pair of distinct claims.
        for claim_a_id, claim_b_id in combinations(
            claim_ids,
            2,
        ):
            claim_a = graph.claims[claim_a_id]
            claim_b = graph.claims[claim_b_id]

            edges_a = graph.get_claim_evidence(claim_a_id)
            edges_b = graph.get_claim_evidence(claim_b_id)

            evidence_a_ids = []
            evidence_b_ids = []

            for edge in edges_a:
                if edge.chunk_id not in graph.evidence:
                    raise ValueError(
                        f"Missing evidence node: {edge.chunk_id}"
                    )

                if edge.chunk_id not in evidence_a_ids:
                    evidence_a_ids.append(edge.chunk_id)

            for edge in edges_b:
                if edge.chunk_id not in graph.evidence:
                    raise ValueError(
                        f"Missing evidence node: {edge.chunk_id}"
                    )

                if edge.chunk_id not in evidence_b_ids:
                    evidence_b_ids.append(edge.chunk_id)

            for chunk_a_id in evidence_a_ids:
                for chunk_b_id in evidence_b_ids:

                    # The same evidence chunk does not form a
                    # cross-claim comparison.
                    if chunk_a_id == chunk_b_id:
                        continue

                    evidence_a = graph.evidence[chunk_a_id]
                    evidence_b = graph.evidence[chunk_b_id]

                    result = self.classifier.classify(
                        evidence_a=evidence_a.text,
                        evidence_b=evidence_b.text,
                    )

                    results.append(
                        CrossClaimContradictionResult(
                            claim_a_id=claim_a_id,
                            claim_a=claim_a.text,
                            evidence_a_chunk_id=chunk_a_id,
                            claim_b_id=claim_b_id,
                            claim_b=claim_b.text,
                            evidence_b_chunk_id=chunk_b_id,
                            label=result.label,
                            confidence=result.confidence,
                            rationale=result.rationale,
                        )
                    )

        contradiction_count = sum(
            result.label
            == ContradictionLabel.CONTRADICTION
            for result in results
        )

        contextual_difference_count = sum(
            result.label
            == ContradictionLabel.CONTEXTUAL_DIFFERENCE
            for result in results
        )

        no_contradiction_count = sum(
            result.label
            == ContradictionLabel.NO_CONTRADICTION
            for result in results
        )

        uncertain_count = sum(
            result.label
            == ContradictionLabel.UNCERTAIN
            for result in results
        )

        return CrossClaimContradictionReport(
            document_id=graph.document_id,
            claim_count=len(claim_ids),
            evidence_pair_count=len(results),
            contradiction_count=contradiction_count,
            contextual_difference_count=(
                contextual_difference_count
            ),
            no_contradiction_count=no_contradiction_count,
            uncertain_count=uncertain_count,
            conflicts=results,
        )
