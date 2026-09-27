from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import EvidenceRelationType
from app.verification.cross_claim_contradiction import (
    CrossClaimContradictionReport,
)


class ContradictionGraphIntegrator:
    """
    Persists Step 15C contradiction-analysis results
    inside the claim-evidence graph.
    """

    def integrate(
        self,
        graph: ClaimEvidenceGraphBuilder,
        report: CrossClaimContradictionReport,
    ):
        if report.document_id != graph.document_id:
            raise ValueError(
                "Report document_id does not match graph document_id"
            )

        relations = []

        for result in report.conflicts:

            relation_type = EvidenceRelationType(
                result.label.value
            )

            relation = graph.add_evidence_relation(
                evidence_a_chunk_id=result.evidence_a_chunk_id,
                evidence_b_chunk_id=result.evidence_b_chunk_id,
                relation_type=relation_type,
                confidence=result.confidence,
                rationale=result.rationale,
                source_claim_a_id=result.claim_a_id,
                source_claim_b_id=result.claim_b_id,
            )

            relations.append(relation)

        return relations
