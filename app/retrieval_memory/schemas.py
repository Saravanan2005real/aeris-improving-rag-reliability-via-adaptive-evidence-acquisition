from typing import List, Optional
from pydantic import BaseModel, Field


class QueryMemory(BaseModel):
    """
    Records one retrieval query attempted by AERIS.
    """

    query: str
    query_type: str = "original"

    requirement_id: Optional[str] = None

    candidate_k: int = Field(default=0, ge=0)
    rerank_top_k: int = Field(default=0, ge=0)

    retrieved_chunk_ids: List[str] = Field(default_factory=list)

    coverage_status: Optional[str] = None
    coverage_score: Optional[float] = None

    successful: bool = False


class EvidenceMemory(BaseModel):
    """
    Records evidence acquired during retrieval.
    """

    chunk_id: str
    document_id: str

    requirement_ids: List[str] = Field(default_factory=list)

    source_queries: List[str] = Field(default_factory=list)

    retrieval_depths: List[int] = Field(default_factory=list)

    best_coverage_score: Optional[float] = None

    coverage_status: Optional[str] = None


class RetrievalMemoryState(BaseModel):
    """
    Complete memory state for one document/question retrieval process.
    """

    document_id: str
    question: str

    query_history: List[QueryMemory] = Field(default_factory=list)

    evidence_history: List[EvidenceMemory] = Field(default_factory=list)
