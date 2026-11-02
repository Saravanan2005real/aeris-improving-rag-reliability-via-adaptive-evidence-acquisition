from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import (
    ClaimVerificationStatus,
    EdgeType,
)


class ClaimStatusResolver:
    """
    Resolves the claim-level verification status from
    verified claim-evidence relationships.

    This operates only on verification labels already
    assigned to graph edges.
    """

    def resolve(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claim_id: str,
    ) -> ClaimVerificationStatus:

        if claim_id not in graph.claims:
            raise ValueError(
                f"Unknown claim_id: {claim_id}"
            )

        edges = graph.get_claim_evidence(claim_id)

        if not edges:
            return ClaimVerificationStatus.UNVERIFIED

        labels = {
            edge.edge_type
            for edge in edges
        }

        # If any edge has not undergone factual verification,
        # the claim cannot be considered fully verified.
        if EdgeType.RELATED in labels:
            return ClaimVerificationStatus.INSUFFICIENT

        has_support = EdgeType.SUPPORTS in labels
        has_contradiction = EdgeType.CONTRADICTS in labels

        if has_support and has_contradiction:
            return ClaimVerificationStatus.CONFLICTED

        if has_support:
            return ClaimVerificationStatus.SUPPORTED

        if has_contradiction:
            return ClaimVerificationStatus.CONTRADICTED

        return ClaimVerificationStatus.INSUFFICIENT
