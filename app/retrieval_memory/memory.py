from typing import List, Optional

from app.retrieval_memory.schemas import (
    QueryMemory,
    EvidenceMemory,
    RetrievalMemoryState,
)


class RetrievalMemory:
    """
    In-memory retrieval history for AERIS-RAG.

    Step 11A intentionally keeps memory in RAM.
    Persistence and controller integration will be added later.
    """

    def __init__(
        self,
        document_id: str,
        question: str,
    ):
        self.state = RetrievalMemoryState(
            document_id=document_id,
            question=question,
        )

    # ------------------------------------------------------------------
    # QUERY MEMORY
    # ------------------------------------------------------------------

    def record_query(
        self,
        query: str,
        query_type: str = "original",
        requirement_id: Optional[str] = None,
        candidate_k: int = 0,
        rerank_top_k: int = 0,
        retrieved_chunk_ids: Optional[List[str]] = None,
        coverage_status: Optional[str] = None,
        coverage_score: Optional[float] = None,
        successful: bool = False,
    ) -> QueryMemory:

        memory = QueryMemory(
            query=query,
            query_type=query_type,
            requirement_id=requirement_id,
            candidate_k=candidate_k,
            rerank_top_k=rerank_top_k,
            retrieved_chunk_ids=retrieved_chunk_ids or [],
            coverage_status=coverage_status,
            coverage_score=coverage_score,
            successful=successful,
        )

        self.state.query_history.append(memory)

        return memory

    # ------------------------------------------------------------------
    # EVIDENCE MEMORY
    # ------------------------------------------------------------------

    def record_evidence(
        self,
        chunk_id: str,
        document_id: str,
        requirement_id: Optional[str] = None,
        source_query: Optional[str] = None,
        retrieval_depth: Optional[int] = None,
        coverage_score: Optional[float] = None,
        coverage_status: Optional[str] = None,
    ) -> EvidenceMemory:

        existing = self.get_evidence(chunk_id)

        if existing is None:
            existing = EvidenceMemory(
                chunk_id=chunk_id,
                document_id=document_id,
            )

            self.state.evidence_history.append(existing)

        if requirement_id and requirement_id not in existing.requirement_ids:
            existing.requirement_ids.append(requirement_id)

        if source_query and source_query not in existing.source_queries:
            existing.source_queries.append(source_query)

        if (
            retrieval_depth is not None
            and retrieval_depth not in existing.retrieval_depths
        ):
            existing.retrieval_depths.append(retrieval_depth)

        if coverage_score is not None:
            if (
                existing.best_coverage_score is None
                or coverage_score > existing.best_coverage_score
            ):
                existing.best_coverage_score = coverage_score

        if coverage_status is not None:
            status_rank = {
                "UNSUPPORTED": 0,
                "PARTIAL": 1,
                "SUPPORTED": 2,
            }

            current_rank = status_rank.get(
                existing.coverage_status,
                -1,
            )

            new_rank = status_rank.get(
                coverage_status,
                -1,
            )

            if new_rank > current_rank:
                existing.coverage_status = coverage_status

        return existing

    # ------------------------------------------------------------------
    # LOOKUPS
    # ------------------------------------------------------------------

    def has_query_attempt(
        self,
        query: str,
        requirement_id: Optional[str],
        candidate_k: int,
    ) -> bool:
        normalized_query = query.strip().lower()

        for item in self.state.query_history:
            if item.query.strip().lower() != normalized_query:
                continue

            if item.requirement_id != requirement_id:
                continue

            if item.candidate_k != candidate_k:
                continue

            return True

        return False

    def has_query(
        self,
        query: str,
        requirement_id: Optional[str] = None,
    ) -> bool:

        normalized_query = query.strip().lower()

        for item in self.state.query_history:
            if item.query.strip().lower() != normalized_query:
                continue

            if requirement_id is None:
                return True

            if item.requirement_id == requirement_id:
                return True

        return False

    def get_queries(
        self,
        requirement_id: Optional[str] = None,
    ) -> List[QueryMemory]:

        if requirement_id is None:
            return list(self.state.query_history)

        return [
            item
            for item in self.state.query_history
            if item.requirement_id == requirement_id
        ]

    def get_evidence(
        self,
        chunk_id: str,
    ) -> Optional[EvidenceMemory]:

        for item in self.state.evidence_history:
            if item.chunk_id == chunk_id:
                return item

        return None

    def has_evidence(
        self,
        chunk_id: str,
    ) -> bool:

        return self.get_evidence(chunk_id) is not None

    def get_all_chunk_ids(self) -> List[str]:

        return [
            item.chunk_id
            for item in self.state.evidence_history
        ]

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------

    def query_count(self) -> int:
        return len(self.state.query_history)

    def evidence_count(self) -> int:
        return len(self.state.evidence_history)

    def clear(self) -> None:
        self.state.query_history.clear()
        self.state.evidence_history.clear()

    def get_state(self) -> RetrievalMemoryState:
        return self.state
