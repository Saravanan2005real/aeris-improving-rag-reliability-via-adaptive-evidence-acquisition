from typing import List, Optional
from pydantic import BaseModel, Field

class ContradictionInfo(BaseModel):
    chunk_a_id: str
    chunk_b_id: str
    nature_of_disagreement: str
    expected_relation: str

class BenchmarkRecord(BaseModel):
    question_id: str
    document_id: str
    question: str
    category: str
    difficulty: str
    language: str = "English"
    information_requirements: List[str] = Field(default_factory=list)
    expected_answer: Optional[str] = None
    expected_claims: List[str] = Field(default_factory=list)
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    supporting_pages: List[int] = Field(default_factory=list)
    answerability: bool
    expected_status: str
    contradiction_information: Optional[ContradictionInfo] = None
    notes: Optional[str] = None
