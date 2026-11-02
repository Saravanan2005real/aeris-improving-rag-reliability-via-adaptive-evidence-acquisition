from typing import Dict, List, Optional

from app.retrieval_memory.schemas import (
    QueryMemory,
    EvidenceMemory,
    RetrievalMemoryState,
)


class RetrievalMemory:
    """
    In-memory retrieval history for AERIS-RAG with support for explicit
    per-document and per-session scoping, compatibility matching, and telemetry.
    """

    def __init__(
        self,
        document_id: str,
        question: str = "",
        session_id: Optional[str] = None,
    ):
        self.state = RetrievalMemoryState(
            document_id=document_id,
            question=question,
        )
        self.session_id = session_id
        self.lookup_count = 0
        self.hit_count = 0
        self.skip_count = 0

    @property
    def miss_count(self) -> int:
        return max(0, self.lookup_count - self.hit_count)

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
    # LOOKUPS & COMPATIBILITY
    # ------------------------------------------------------------------

    def has_query_attempt(
        self,
        query: str,
        requirement_id: Optional[str] = None,
        candidate_k: int = 0,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        match_requirement: bool = True,
    ) -> bool:
        """
        Determines whether a compatible query attempt exists in memory.
        Enforces strict dimension compatibility:
        - document_id must match (no cross-document reuse/leakage).
        - session_id must match (no cross-session/user leakage).
        - query must match (case-insensitive normalized).
        - cached candidate_k must be >= requested candidate_k.
        - requirement_id must match when match_requirement is True and requirement_id is provided.
        """
        self.lookup_count += 1

        # Check document isolation
        if document_id is not None and document_id != self.state.document_id:
            return False

        # Check session isolation
        if session_id is not None and session_id != self.session_id:
            return False

        normalized_query = query.strip().lower()

        for item in self.state.query_history:
            if item.query.strip().lower() != normalized_query:
                continue

            # Requirement dimension compatibility
            if match_requirement and requirement_id is not None:
                if item.requirement_id != requirement_id:
                    continue

            # Candidate depth compatibility: cached depth must be sufficient
            # e.g., an entry cached at k=10 cannot satisfy a request for k=25 or k=50
            if item.candidate_k < candidate_k:
                continue

            self.hit_count += 1
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
    # SUMMARY & LIFECYCLE
    # ------------------------------------------------------------------

    def query_count(self) -> int:
        return len(self.state.query_history)

    def evidence_count(self) -> int:
        return len(self.state.evidence_history)

    def record_skip(self, reason: Optional[str] = None) -> None:
        self.skip_count += 1

    def invalidate_for_document(self, document_id: str) -> None:
        if self.state.document_id == document_id:
            self.clear()

    def clear(self) -> None:
        self.state.query_history.clear()
        self.state.evidence_history.clear()
        self.lookup_count = 0
        self.hit_count = 0
        self.skip_count = 0

    def get_state(self) -> RetrievalMemoryState:
        return self.state


class RetrievalMemoryRegistry:
    """
    Registry for explicitly scoped retrieval memory instances.
    Provides session-level and document-level isolation across requests.
    """
    _instances: Dict[str, RetrievalMemory] = {}

    @classmethod
    def get_scoped_memory(
        cls,
        document_id: str,
        session_id: Optional[str] = None,
        question: Optional[str] = None,
    ) -> RetrievalMemory:
        key = f"{document_id}::{session_id or 'default'}"
        if key not in cls._instances:
            cls._instances[key] = RetrievalMemory(
                document_id=document_id,
                question=question or "",
                session_id=session_id,
            )
        return cls._instances[key]

    @classmethod
    def invalidate(
        cls,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Invalidates memory entries matching the specified document and/or session scope.
        If both are None, all cached memory is invalidated.
        """
        if document_id is None and session_id is None:
            cls._instances.clear()
        else:
            keys_to_del = [
                k for k in cls._instances
                if (document_id is None or k.startswith(f"{document_id}::"))
                and (session_id is None or k.endswith(f"::{session_id}"))
            ]
            for k in keys_to_del:
                del cls._instances[k]

    @classmethod
    def clear(cls) -> None:
        cls.invalidate()

    @classmethod
    def invalidate_for_document(cls, document_id: str) -> None:
        cls.invalidate(document_id=document_id)
