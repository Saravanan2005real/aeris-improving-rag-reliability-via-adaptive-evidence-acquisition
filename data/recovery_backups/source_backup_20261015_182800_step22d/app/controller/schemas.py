from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ControllerStage(str, Enum):
    PLANNING = "PLANNING"
    RETRIEVAL = "RETRIEVAL"
    COVERAGE = "COVERAGE"
    CLAIM_GRAPH = "CLAIM_GRAPH"
    VERIFICATION = "VERIFICATION"
    CONTRADICTION = "CONTRADICTION"
    CROSS_LINGUAL = "CROSS_LINGUAL"
    CALIBRATION = "CALIBRATION"
    SELECTIVE_VERIFICATION = "SELECTIVE_VERIFICATION"
    ANSWER_GENERATION = "ANSWER_GENERATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StageStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class ControllerStageResult(BaseModel):
    stage: ControllerStage
    status: StageStatus

    message: Optional[str] = None

    output_count: int = Field(
        default=0,
        ge=0,
    )
    
    latency_seconds: float = Field(
        default=0.0,
        ge=0.0
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


class ControllerConfig(BaseModel):
    """
    Configuration for one AERIS controller execution.

    These values are deliberately explicit so experiments can
    later record the exact controller configuration.
    """

    retrieval_top_k: int = Field(
        default=5,
        ge=1,
    )

    candidate_k: int = Field(
        default=25,
        ge=1,
    )

    verification_budget: int = Field(
        default=3,
        ge=0,
    )

    enable_adaptive_retrieval: bool = True
    enable_query_reformulation: bool = True
    enable_retrieval_memory: bool = True
    enable_claim_verification: bool = True

    enable_contradiction_analysis: bool = True

    enable_cross_lingual_analysis: bool = True

    enable_calibration: bool = True

    enable_selective_verification: bool = True

    answer_generation_enabled: bool = True


class ControllerRequest(BaseModel):
    document_id: str = Field(
        min_length=1
    )

    question: str = Field(
        min_length=1
    )

    config: ControllerConfig = Field(
        default_factory=ControllerConfig
    )


class ControllerResult(BaseModel):
    document_id: str

    question: str

    status: StageStatus

    stages: List[ControllerStageResult] = Field(
        default_factory=list
    )

    final_answer: Optional[str] = None

    answer_status: Optional[str] = None

    answer_confidence: Optional[float] = None

    supporting_claim_ids: List[str] = Field(
        default_factory=list
    )

    supporting_chunk_ids: List[str] = Field(
        default_factory=list,
        description="Distinct chunk IDs cited by the generated answer."
    )

    retrieved_chunk_ids: List[str] = Field(
        default_factory=list,
        description="Ordered unique chunk IDs returned by adaptive hybrid retrieval and passed into claim extraction."
    )

    retrieval_attempts_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-attempt breakdown of query, query_type, candidate_k, and retrieved chunk IDs."
    )

    provenance_defects: List[str] = Field(
        default_factory=list,
        description="Any cited chunk IDs that were not present in retrieved_chunk_ids."
    )

    provenance: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    conflict_information: Optional[str] = None

    insufficiency_information: Optional[str] = None

    claim_count: int = Field(
        default=0,
        ge=0,
    )

    evidence_count: int = Field(
        default=0,
        ge=0,
    )

    verified_claim_count: int = Field(
        default=0,
        ge=0,
    )

    selected_verification_count: int = Field(
        default=0,
        ge=0,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )
