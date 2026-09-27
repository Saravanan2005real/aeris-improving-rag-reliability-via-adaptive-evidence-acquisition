from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class ClaimType(str, Enum):
    FACT = "FACT"
    METHOD = "METHOD"
    COMPONENT = "COMPONENT"
    RELATIONSHIP = "RELATIONSHIP"
    QUANTITATIVE = "QUANTITATIVE"
    COMPARATIVE = "COMPARATIVE"
    CAUSAL = "CAUSAL"
    DEFINITION = "DEFINITION"
    OTHER = "OTHER"

class ExtractedClaim(BaseModel):
    """Represents a single atomic claim extracted from an evidence chunk."""
    claim_id: str
    text: str = Field(description="The atomic claim extracted from the text.")
    source_chunk_id: str = Field(description="The ID of the chunk this claim was extracted from.")
    document_id: str = Field(description="The document ID this claim originates from.")

class TypedClaim(ExtractedClaim):
    """A claim with an assigned semantic/factual type."""
    claim_type: ClaimType = Field(description="The semantic category of the claim.")

class ClaimExtractionResult(BaseModel):
    """The full result of a claim extraction pass on a chunk."""
    chunk_id: str
    document_id: str
    claims: List[ExtractedClaim] = Field(default_factory=list)
