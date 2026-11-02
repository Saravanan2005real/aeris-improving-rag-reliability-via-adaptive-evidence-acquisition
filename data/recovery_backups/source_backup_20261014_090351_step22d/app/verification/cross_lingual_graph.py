from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.claim_graph.schemas import EvidenceRelationType
from app.verification.cross_lingual_claim import (
    ClaimCrossLingualResult,
)


class CrossLingualGraphIntegrator:
    """
    Persists Step 16B cross-lingual claim analysis
    into the claim-evidence graph.

    Only actual cross-lingual evidence pairs are persisted.
    """

    def integrate(
        self,
        graph: ClaimEvidenceGraphBuilder,
        result: ClaimCrossLingualResult,
        evidence_pairs: list[dict],
    ):
        if result.claim_id not in graph.claims:
            raise ValueError(
                f"Unknown claim_id: {result.claim_id}"
            )

        relations = []

        for pair in evidence_pairs:

            evidence_a_chunk_id = pair["evidence_a_chunk_id"]
            evidence_b_chunk_id = pair["evidence_b_chunk_id"]

            if evidence_a_chunk_id not in graph.evidence:
                raise ValueError(
                    f"Unknown evidence chunk: "
                    f"{evidence_a_chunk_id}"
                )

            if evidence_b_chunk_id not in graph.evidence:
                raise ValueError(
                    f"Unknown evidence chunk: "
                    f"{evidence_b_chunk_id}"
                )

            claim_a_id = pair.get(
                "source_claim_a_id",
                result.claim_id,
            )

            claim_b_id = pair.get(
                "source_claim_b_id",
                result.claim_id,
            )

            relation_type = EvidenceRelationType(
                pair["label"]
            )

            relation = graph.add_evidence_relation(
                evidence_a_chunk_id=evidence_a_chunk_id,
                evidence_b_chunk_id=evidence_b_chunk_id,
                relation_type=relation_type,
                confidence=float(pair["confidence"]),
                rationale=pair["rationale"],
                source_claim_a_id=claim_a_id,
                source_claim_b_id=claim_b_id,
            )

            relations.append(relation)

        return relations
