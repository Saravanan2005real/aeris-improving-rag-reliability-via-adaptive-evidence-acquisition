from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.claim_extraction.schemas import ClaimType


class ClaimVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTED = "CONFLICTED"


class ClaimNode(BaseModel):
    claim_id: str
    text: str
    claim_type: ClaimType
    document_id: str
    source_chunk_id: str


class EvidenceNode(BaseModel):
    chunk_id: str
    document_id: str
    text: str


class EdgeType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    RELATED = "RELATED"


class ClaimEvidenceEdge(BaseModel):
    edge_id: str
    claim_id: str
    chunk_id: str
    edge_type: EdgeType = EdgeType.RELATED
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verification_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class EvidenceRelationType(str, Enum):
    AGREEMENT = "AGREEMENT"
    NO_CONTRADICTION = "NO_CONTRADICTION"
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"
    CONTRADICTION = "CONTRADICTION"
    UNCERTAIN = "UNCERTAIN"


class EvidenceRelationEdge(BaseModel):
    relation_id: str
    document_id: str

    evidence_a_chunk_id: str
    evidence_b_chunk_id: str

    relation_type: EvidenceRelationType
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str

    source_claim_a_id: str
    source_claim_b_id: str


class ClaimEvidenceGraph(BaseModel):
    document_id: str

    claims: List[ClaimNode] = Field(default_factory=list)
    evidence: List[EvidenceNode] = Field(default_factory=list)
    edges: List[ClaimEvidenceEdge] = Field(default_factory=list)

    evidence_relations: List[EvidenceRelationEdge] = Field(
        default_factory=list
    )
