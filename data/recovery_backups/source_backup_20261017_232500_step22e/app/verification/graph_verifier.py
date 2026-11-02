from pydantic import BaseModel, Field

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import (
    ClaimEvidenceEdge,
    EdgeType,
)
from app.verification.claim_verifier import (
    ClaimVerifier,
    MultiEvidenceVerificationResult,
)


class GraphVerificationResult(BaseModel):
    claim_id: str
    claim: str
    evidence_count: int = Field(ge=1)
    evidence_chunk_ids: list[str]
    label: EdgeType
    verification_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    rationale: str


class GraphClaimVerifier:
    """
    Integrates the claim-evidence graph with multi-evidence verification.

    Graph semantic similarity and factual verification are kept separate.

    Semantic similarity:
        edge.confidence

    Factual verification:
        edge.verification_confidence
    """

    def __init__(self, verifier: ClaimVerifier):
        self.verifier = verifier

    def verify_claim(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claim_id: str,
    ) -> GraphVerificationResult:

        if claim_id not in graph.claims:
            raise ValueError(
                f"Unknown claim_id: {claim_id}"
            )

        claim = graph.claims[claim_id]

        edges = graph.get_claim_evidence(claim_id)

        if not edges:
            raise ValueError(
                f"No evidence connected to claim: {claim_id}"
            )

        evidence = []

        for edge in edges:
            if edge.chunk_id not in graph.evidence:
                raise ValueError(
                    f"Missing evidence node: {edge.chunk_id}"
                )

            evidence.append(
                graph.evidence[edge.chunk_id].text
            )

        result: MultiEvidenceVerificationResult = (
            self.verifier.verify_multiple(
                claim=claim.text,
                evidence=evidence,
            )
        )

        # Map verification label to graph edge type.
        edge_type = EdgeType(result.label.value)

        # Update every evidence relationship belonging
        # to this claim.
        for edge in edges:
            edge.edge_type = edge_type
            edge.verification_confidence = result.confidence

        return GraphVerificationResult(
            claim_id=claim_id,
            claim=claim.text,
            evidence_count=result.evidence_count,
            evidence_chunk_ids=[
                edge.chunk_id for edge in edges
            ],
            label=edge_type,
            verification_confidence=result.confidence,
            rationale=result.rationale,
        )
