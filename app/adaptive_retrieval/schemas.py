from typing import List, Optional
from pydantic import BaseModel, Field
from app.coverage.evidence_coverage import EvidenceItem


class RetrievalAttempt(BaseModel):
    """
    Records one adaptive retrieval attempt for a single information requirement.
    """

    attempt_number: int = Field(ge=1)

    requirement_id: str

    query: str

    query_type: str = "original"

    candidate_k: int = Field(gt=0)

    rerank_top_k: int = Field(gt=0)

    retrieved_chunk_ids: List[str] = Field(default_factory=list)

    new_chunk_ids: List[str] = Field(default_factory=list)

    coverage_status: Optional[str] = None

    coverage_score: Optional[float] = None

    stopped: bool = False

    stop_reason: Optional[str] = None


class AdaptiveRetrievalResult(BaseModel):
    """
    Final result of adaptive evidence acquisition for one requirement.
    """

    requirement_id: str

    original_query: str

    final_query: str

    attempts: List[RetrievalAttempt] = Field(default_factory=list)

    evidence: List[EvidenceItem] = Field(default_factory=list)

    all_chunk_ids: List[str] = Field(default_factory=list)

    final_candidate_k: int = 0

    total_unique_chunks: int = 0

    final_coverage_status: Optional[str] = None

    final_coverage_score: Optional[float] = None

    success: bool = False

    stop_reason: Optional[str] = None
