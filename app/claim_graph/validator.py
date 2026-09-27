from typing import List

from app.claim_graph.schemas import ClaimEvidenceGraph


class GraphValidationError:
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def __str__(self):
        return f"[{self.code}] {self.message}"


class ClaimEvidenceGraphValidator:
    """
    Validates structural integrity of a Claim-Evidence Graph.

    This validator does NOT determine whether evidence supports
    or contradicts a claim.
    """

    def validate(
        self,
        graph: ClaimEvidenceGraph,
    ) -> List[GraphValidationError]:

        errors = []

        claim_ids = {
            claim.claim_id
            for claim in graph.claims
        }

        evidence_ids = {
            evidence.chunk_id
            for evidence in graph.evidence
        }

        # -----------------------------------------------------
        # Duplicate claim IDs
        # -----------------------------------------------------

        if len(claim_ids) != len(graph.claims):
            errors.append(
                GraphValidationError(
                    "DUPLICATE_CLAIM_ID",
                    "Duplicate claim IDs detected.",
                )
            )

        # -----------------------------------------------------
        # Duplicate evidence IDs
        # -----------------------------------------------------

        if len(evidence_ids) != len(graph.evidence):
            errors.append(
                GraphValidationError(
                    "DUPLICATE_EVIDENCE_ID",
                    "Duplicate evidence chunk IDs detected.",
                )
            )

        # -----------------------------------------------------
        # Claim provenance
        # -----------------------------------------------------

        for claim in graph.claims:

            if not claim.claim_id.strip():
                errors.append(
                    GraphValidationError(
                        "MISSING_CLAIM_ID",
                        "A claim has an empty claim_id.",
                    )
                )

            if not claim.text.strip():
                errors.append(
                    GraphValidationError(
                        "EMPTY_CLAIM_TEXT",
                        f"Claim {claim.claim_id} has empty text.",
                    )
                )

            if not claim.source_chunk_id.strip():
                errors.append(
                    GraphValidationError(
                        "MISSING_CLAIM_SOURCE",
                        f"Claim {claim.claim_id} has no source chunk.",
                    )
                )

            if claim.document_id != graph.document_id:
                errors.append(
                    GraphValidationError(
                        "DOCUMENT_MISMATCH",
                        f"Claim {claim.claim_id} belongs to "
                        f"document {claim.document_id}, not "
                        f"{graph.document_id}.",
                    )
                )

        # -----------------------------------------------------
        # Evidence provenance
        # -----------------------------------------------------

        for evidence in graph.evidence:

            if not evidence.chunk_id.strip():
                errors.append(
                    GraphValidationError(
                        "MISSING_EVIDENCE_ID",
                        "An evidence node has an empty chunk_id.",
                    )
                )

            if not evidence.text.strip():
                errors.append(
                    GraphValidationError(
                        "EMPTY_EVIDENCE_TEXT",
                        f"Evidence {evidence.chunk_id} has empty text.",
                    )
                )

            if evidence.document_id != graph.document_id:
                errors.append(
                    GraphValidationError(
                        "DOCUMENT_MISMATCH",
                        f"Evidence {evidence.chunk_id} belongs to "
                        f"document {evidence.document_id}, not "
                        f"{graph.document_id}.",
                    )
                )

        # -----------------------------------------------------
        # Edge validation
        # -----------------------------------------------------

        edge_ids = set()

        for edge in graph.edges:

            if edge.edge_id in edge_ids:
                errors.append(
                    GraphValidationError(
                        "DUPLICATE_EDGE_ID",
                        f"Duplicate edge ID: {edge.edge_id}",
                    )
                )

            edge_ids.add(edge.edge_id)

            if edge.claim_id not in claim_ids:
                errors.append(
                    GraphValidationError(
                        "INVALID_CLAIM_REFERENCE",
                        f"Edge {edge.edge_id} references "
                        f"unknown claim {edge.claim_id}.",
                    )
                )

            if edge.chunk_id not in evidence_ids:
                errors.append(
                    GraphValidationError(
                        "INVALID_EVIDENCE_REFERENCE",
                        f"Edge {edge.edge_id} references "
                        f"unknown evidence {edge.chunk_id}.",
                    )
                )

            if edge.confidence is not None:

                if not 0.0 <= edge.confidence <= 1.0:
                    errors.append(
                        GraphValidationError(
                            "INVALID_CONFIDENCE",
                            f"Edge {edge.edge_id} has confidence "
                            f"outside [0, 1].",
                        )
                    )

        # -----------------------------------------------------
        # Orphan claims
        # -----------------------------------------------------

        connected_claim_ids = {
            edge.claim_id
            for edge in graph.edges
        }

        for claim in graph.claims:

            if claim.claim_id not in connected_claim_ids:
                errors.append(
                    GraphValidationError(
                        "ORPHAN_CLAIM",
                        f"Claim {claim.claim_id} has no evidence "
                        f"relationship.",
                    )
                )

        # -----------------------------------------------------
        # Orphan evidence
        # -----------------------------------------------------

        connected_evidence_ids = {
            edge.chunk_id
            for edge in graph.edges
        }

        for evidence in graph.evidence:

            if evidence.chunk_id not in connected_evidence_ids:
                errors.append(
                    GraphValidationError(
                        "ORPHAN_EVIDENCE",
                        f"Evidence {evidence.chunk_id} has no "
                        f"claim relationship.",
                    )
                )

        # -----------------------------------------------------
        # Duplicate claim-evidence relationships
        # -----------------------------------------------------

        relationships = set()

        for edge in graph.edges:

            relationship = (
                edge.claim_id,
                edge.chunk_id,
            )

            if relationship in relationships:
                errors.append(
                    GraphValidationError(
                        "DUPLICATE_RELATIONSHIP",
                        f"Duplicate claim-evidence relationship: "
                        f"{edge.claim_id} <-> {edge.chunk_id}",
                    )
                )

            relationships.add(relationship)

        return errors

    def is_valid(
        self,
        graph: ClaimEvidenceGraph,
    ) -> bool:

        return len(self.validate(graph)) == 0
