from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class AblationVariant(str, Enum):
    FULL_AERIS = "FULL_AERIS"
    NO_ADAPTIVE_RETRIEVAL = "NO_ADAPTIVE_RETRIEVAL"
    NO_QUERY_REFORMULATION = "NO_QUERY_REFORMULATION"
    NO_RETRIEVAL_MEMORY = "NO_RETRIEVAL_MEMORY"
    NO_CLAIM_VERIFICATION = "NO_CLAIM_VERIFICATION"
    NO_CONTRADICTION_ANALYSIS = "NO_CONTRADICTION_ANALYSIS"
    NO_CROSSLINGUAL_AGREEMENT = "NO_CROSSLINGUAL_AGREEMENT"
    NO_SELECTIVE_VERIFICATION = "NO_SELECTIVE_VERIFICATION"

class AblationResult(BaseModel):
    experiment_id: str
    variant: AblationVariant
    question_id: str
    question: str
    document_id: str
    question_type: str
    expected_answerability: bool
    final_status: str
    final_confidence: Optional[float] = None
    answer: Optional[str] = None
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    supporting_claim_ids: List[str] = Field(default_factory=list)
    expected_chunk_ids: List[str] = Field(default_factory=list)
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    retriever_hit: bool = False
    retriever_recall: float = 0.0
    citation_hit: bool = False
    citation_recall: float = 0.0
    provenance_defects: List[str] = Field(default_factory=list)
    evidence_hit: bool = False
    evidence_recall: float = 0.0
    evidence_count: int = 0
    claim_count: int = 0
    verified_claim_count: int = 0
    selected_verification_count: int = 0
    contradiction_count: int = 0
    cross_lingual_count: int = 0
    latency_seconds: float = 0.0
    stage_latencies: Dict[str, float] = Field(default_factory=dict)
    stage_statuses: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    repair_count: int = 0
    retry_count: int = 0
    is_answerable: Optional[bool] = None
    success: bool = True

