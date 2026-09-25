from typing import List, Literal

from pydantic import BaseModel, Field


RequirementType = Literal[
    "definition",
    "fact",
    "factual",
    "list",
    "comparison",
    "quantitative",
    "causal",
    "procedural",
    "multi_hop",
    "summary",
    "other",
]


class InformationRequirement(BaseModel):
    requirement_id: str = Field(
        description="Unique requirement identifier such as R1, R2, R3."
    )

    description: str = Field(
        description="Specific information that must be obtained to answer the question."
    )

    requirement_type: RequirementType = Field(
        description="Type of information required."
    )

    priority: int = Field(
        ge=1,
        le=5,
        description="Importance of this requirement. 1 is highest priority."
    )

    expected_evidence_type: str = Field(
        description="Type of evidence expected, such as definition, table, result, comparison, or explanation."
    )

    entities: List[str] = Field(
        default_factory=list,
        description="Important entities, concepts, datasets, methods, or terms."
    )

    retrieval_queries: List[str] = Field(
        default_factory=list,
        description="Alternative search queries that can retrieve evidence for this requirement."
    )


class RequirementPlan(BaseModel):
    question: str

    question_type: str = Field(
        description="High-level question type."
    )

    complexity: Literal[
        "simple",
        "moderate",
        "complex"
    ]

    requirements: List[InformationRequirement]

    reasoning_summary: str = Field(
        description="Short explanation of why these requirements are needed."
    )
