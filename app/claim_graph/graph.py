from typing import Optional

from sentence_transformers import SentenceTransformer

from app.claim_graph.schemas import (
    ClaimEvidenceEdge,
    ClaimEvidenceGraph,
    ClaimNode,
    EdgeType,
    EvidenceNode,
    EvidenceRelationEdge,
)


class ClaimEvidenceGraphBuilder:
    """
    Builds a claim-evidence graph.

    Supports:
    - many-to-many claim/evidence relationships
    - semantic relationship discovery
    - factual verification metadata
    - evidence-to-evidence contradiction relations

    Semantic similarity is used only for relationship discovery.
    It is NOT treated as factual support or contradiction.
    """

    def __init__(
        self,
        document_id: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.70,
    ):
        self.document_id = document_id
        self.similarity_threshold = similarity_threshold

        self.claims = {}
        self.evidence = {}
        self.edges = {}

        # Step 15D
        self.evidence_relations = {}

        self.embedding_model = SentenceTransformer(embedding_model)

    def add_claim(
        self,
        claim_id,
        text,
        claim_type,
        source_chunk_id,
    ):
        claim = ClaimNode(
            claim_id=claim_id,
            text=text,
            claim_type=claim_type,
            document_id=self.document_id,
            source_chunk_id=source_chunk_id,
        )

        self.claims[claim_id] = claim
        return claim

    def add_evidence(
        self,
        chunk_id,
        text,
    ):
        evidence = EvidenceNode(
            chunk_id=chunk_id,
            document_id=self.document_id,
            text=text,
        )

        self.evidence[chunk_id] = evidence
        return evidence

    def add_edge(
        self,
        claim_id,
        chunk_id,
        edge_type=EdgeType.RELATED,
        confidence=None,
        verification_confidence=None,
    ):
        if claim_id not in self.claims:
            raise ValueError(
                f"Unknown claim_id: {claim_id}"
            )

        if chunk_id not in self.evidence:
            raise ValueError(
                f"Unknown chunk_id: {chunk_id}"
            )

        edge_id = f"{chunk_id}__{claim_id}"

        edge = ClaimEvidenceEdge(
            edge_id=edge_id,
            claim_id=claim_id,
            chunk_id=chunk_id,
            edge_type=edge_type,
            confidence=confidence,
            verification_confidence=verification_confidence,
        )

        self.edges[edge_id] = edge

        return edge

    def add_evidence_relation(
        self,
        evidence_a_chunk_id: str,
        evidence_b_chunk_id: str,
        relation_type,
        confidence: float,
        rationale: str,
        source_claim_a_id: str,
        source_claim_b_id: str,
    ):
        """
        Adds an evidence-to-evidence relation.

        This is intentionally separate from ClaimEvidenceEdge.
        """

        if evidence_a_chunk_id not in self.evidence:
            raise ValueError(
                f"Unknown evidence chunk: {evidence_a_chunk_id}"
            )

        if evidence_b_chunk_id not in self.evidence:
            raise ValueError(
                f"Unknown evidence chunk: {evidence_b_chunk_id}"
            )

        if evidence_a_chunk_id == evidence_b_chunk_id:
            raise ValueError(
                "Evidence relation cannot connect a chunk to itself"
            )

        if source_claim_a_id not in self.claims:
            raise ValueError(
                f"Unknown source claim: {source_claim_a_id}"
            )

        if source_claim_b_id not in self.claims:
            raise ValueError(
                f"Unknown source claim: {source_claim_b_id}"
            )

        relation_id = (
            f"{evidence_a_chunk_id}"
            f"__{evidence_b_chunk_id}"
            f"__{source_claim_a_id}"
            f"__{source_claim_b_id}"
        )

        relation = EvidenceRelationEdge(
            relation_id=relation_id,
            document_id=self.document_id,
            evidence_a_chunk_id=evidence_a_chunk_id,
            evidence_b_chunk_id=evidence_b_chunk_id,
            relation_type=relation_type,
            confidence=confidence,
            rationale=rationale,
            source_claim_a_id=source_claim_a_id,
            source_claim_b_id=source_claim_b_id,
        )

        self.evidence_relations[relation_id] = relation

        return relation

    def get_evidence_relations(
        self,
        chunk_id: Optional[str] = None,
    ):
        if chunk_id is None:
            return list(self.evidence_relations.values())

        return [
            relation
            for relation in self.evidence_relations.values()
            if (
                relation.evidence_a_chunk_id == chunk_id
                or relation.evidence_b_chunk_id == chunk_id
            )
        ]

    def auto_link_claims_to_evidence(self):
        if not self.claims or not self.evidence:
            return []

        claim_ids = list(self.claims.keys())
        evidence_ids = list(self.evidence.keys())

        claim_texts = [
            self.claims[x].text
            for x in claim_ids
        ]

        evidence_texts = [
            self.evidence[x].text
            for x in evidence_ids
        ]

        claim_embeddings = self.embedding_model.encode(
            claim_texts,
            normalize_embeddings=True,
        )

        evidence_embeddings = self.embedding_model.encode(
            evidence_texts,
            normalize_embeddings=True,
        )

        new_edges = []

        for claim_index, claim_id in enumerate(claim_ids):

            claim_vector = claim_embeddings[claim_index]

            for evidence_index, chunk_id in enumerate(
                evidence_ids
            ):
                evidence_vector = evidence_embeddings[
                    evidence_index
                ]

                similarity = float(
                    claim_vector @ evidence_vector
                )

                if similarity >= self.similarity_threshold:
                    edge = self.add_edge(
                        claim_id=claim_id,
                        chunk_id=chunk_id,
                        edge_type=EdgeType.RELATED,
                        confidence=similarity,
                    )

                    new_edges.append(edge)

        return new_edges

    def get_claim_evidence(
        self,
        claim_id: str,
    ):
        return [
            edge
            for edge in self.edges.values()
            if edge.claim_id == claim_id
        ]

    def get_evidence_claims(
        self,
        chunk_id: str,
    ):
        return [
            edge
            for edge in self.edges.values()
            if edge.chunk_id == chunk_id
        ]

    def build(self):
        return ClaimEvidenceGraph(
            document_id=self.document_id,
            claims=list(self.claims.values()),
            evidence=list(self.evidence.values()),
            edges=list(self.edges.values()),
            evidence_relations=list(
                self.evidence_relations.values()
            ),
        )

    def claim_count(self):
        return len(self.claims)

    def evidence_count(self):
        return len(self.evidence)

    def edge_count(self):
        return len(self.edges)

    def evidence_relation_count(self):
        return len(self.evidence_relations)
