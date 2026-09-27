from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AnswerStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTED = "CONFLICTED"

class ProvenanceItem(BaseModel):
    document_id: str
    chunk_id: str
    pages: List[int] = Field(default_factory=list)
    relevant_claim_ids: List[str] = Field(default_factory=list)

class GroundedAnswer(BaseModel):
    question: str
    answer: str
    status: AnswerStatus
    confidence: Optional[float] = Field(
        default=None,
        description="Engineering score representing generation confidence, NOT a calibrated probability unless explicitly stated."
    )
    supporting_claim_ids: List[str] = Field(default_factory=list)
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    provenance: List[ProvenanceItem] = Field(default_factory=list)
    conflict_information: Optional[str] = None
    insufficiency_reason: Optional[str] = None
