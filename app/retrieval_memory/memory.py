from collections import OrderedDict
import threading
from typing import Any, Dict, List, Optional

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
        self.cached_evidence_count = 0
        self.fallback_count = 0
        self.incompatibility_count = 0

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
        cached_evidence: Optional[List[Any]] = None,
        coverage_status: Optional[str] = None,
        coverage_score: Optional[float] = None,
        successful: bool = False,
    ) -> QueryMemory:

        serialized_evidence: List[Dict[str, Any]] = []
        if cached_evidence:
            for item in cached_evidence:
                if hasattr(item, "model_dump"):
                    serialized_evidence.append(item.model_dump())
                elif hasattr(item, "dict"):
                    serialized_evidence.append(item.dict())
                elif isinstance(item, dict):
                    serialized_evidence.append(item)
                elif hasattr(item, "__dict__"):
                    serialized_evidence.append(dict(item.__dict__))

        memory = QueryMemory(
            query=query,
            query_type=query_type,
            requirement_id=requirement_id,
            candidate_k=candidate_k,
            rerank_top_k=rerank_top_k,
            retrieved_chunk_ids=retrieved_chunk_ids or [],
            cached_evidence=serialized_evidence,
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
        payload: Optional[Dict[str, Any]] = None,
    ) -> EvidenceMemory:

        existing = self.get_evidence(chunk_id)

        if existing is None:
            existing = EvidenceMemory(
                chunk_id=chunk_id,
                document_id=document_id,
                payload=payload,
            )
            self.state.evidence_history.append(existing)
        elif payload is not None and existing.payload is None:
            existing.payload = payload

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

    def get_compatible_query_attempt(
        self,
        query: str,
        candidate_k: int = 0,
        requirement_id: Optional[str] = None,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        match_requirement: bool = True,
        require_evidence: bool = True,
    ) -> Optional[QueryMemory]:
        """
        Retrieves a compatible query attempt from memory, verifying:
        - document_id isolation (must match self.state.document_id).
        - session_id isolation (must match self.session_id).
        - query text (normalized case-insensitive match).
        - requirement_id match (when match_requirement is True and requirement_id is provided).
        - candidate_k depth compatibility (cached depth must be >= requested candidate_k).
        - valid reconstructible cached_evidence (when require_evidence is True).

        Telemetry tracking:
        - Increments lookup_count.
        - Increments hit_count on compatible match.
        - Increments fallback_count if entry matches query/depth but lacks valid evidence.
        - Increments incompatibility_count and skip_count on scope/depth mismatch.
        """
        self.lookup_count += 1

        # Check document isolation
        if document_id is not None and document_id != self.state.document_id:
            self.incompatibility_count += 1
            self.skip_count += 1
            return None

        # Check session isolation
        if session_id is not None and session_id != self.session_id:
            self.incompatibility_count += 1
            self.skip_count += 1
            return None

        normalized_query = query.strip().lower()

        for item in self.state.query_history:
            if item.query.strip().lower() != normalized_query:
                continue

            # Requirement dimension compatibility
            if match_requirement and requirement_id is not None:
                if item.requirement_id is not None and item.requirement_id != requirement_id:
                    self.incompatibility_count += 1
                    continue

            # Candidate depth compatibility: cached depth must be sufficient
            # e.g., an entry cached at k=10 cannot satisfy a request for k=25 or k=50
            if item.candidate_k < candidate_k:
                self.incompatibility_count += 1
                continue

            # If require_evidence is True, verify entry contains valid reconstructible evidence
            if require_evidence:
                if (
                    not item.cached_evidence
                    or not isinstance(item.cached_evidence, list)
                    or len(item.cached_evidence) == 0
                ):
                    # Candidate matched query & depth, but contains no reconstructible evidence!
                    # Treat as cache miss and record fallback
                    self.fallback_count += 1
                    return None

            self.hit_count += 1
            return item

        return None

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
        Enforces strict dimension compatibility without requiring cached_evidence payload,
        preserving backward compatibility with unit tests.
        """
        return (
            self.get_compatible_query_attempt(
                query=query,
                candidate_k=candidate_k,
                requirement_id=requirement_id,
                document_id=document_id,
                session_id=session_id,
                match_requirement=match_requirement,
                require_evidence=False,
            )
            is not None
        )

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

    def record_cache_hit_delivery(self, count: int = 1) -> None:
        """Records delivered cached evidence count."""
        self.cached_evidence_count += max(0, count)

    def record_fallback(self, reason: Optional[str] = None) -> None:
        """Records a retrieval fallback due to invalid or unparseable cached entry."""
        self.fallback_count += 1

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
        self.cached_evidence_count = 0
        self.fallback_count = 0
        self.incompatibility_count = 0

    def get_state(self) -> RetrievalMemoryState:
        return self.state


class RetrievalMemoryRegistry:
    """
    Registry for explicitly scoped retrieval memory instances.
    Provides thread-safe access, session-level and document-level isolation,
    and a bounded LRU capacity to prevent unbounded memory growth.
    """
    _instances: OrderedDict[str, RetrievalMemory] = OrderedDict()
    _lock = threading.RLock()
    _max_capacity: int = 1000

    @classmethod
    def set_capacity(cls, capacity: int) -> None:
        """Sets the maximum capacity for bounded LRU cache."""
        with cls._lock:
            cls._max_capacity = max(1, capacity)
            while len(cls._instances) > cls._max_capacity:
                cls._instances.popitem(last=False)

    @classmethod
    def get_capacity(cls) -> int:
        with cls._lock:
            return cls._max_capacity

    @classmethod
    def get_scoped_memory(
        cls,
        document_id: str,
        session_id: Optional[str] = None,
        question: Optional[str] = None,
    ) -> RetrievalMemory:
        key = f"{document_id}::{session_id or 'default'}"
        with cls._lock:
            if key in cls._instances:
                cls._instances.move_to_end(key)
                return cls._instances[key]

            if len(cls._instances) >= cls._max_capacity:
                cls._instances.popitem(last=False)

            instance = RetrievalMemory(
                document_id=document_id,
                question=question or "",
                session_id=session_id,
            )
            cls._instances[key] = instance
            return instance

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
        with cls._lock:
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
