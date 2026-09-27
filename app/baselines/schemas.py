import time
from typing import List, Optional
from pydantic import BaseModel

class BaselineResult(BaseModel):
    baseline_name: str
    question_id: str
    question: str
    document_id: str
    retrieved_chunk_ids: List[str]
    retrieved_pages: List[int]
    retrieval_scores: List[float]
    retrieval_count: int
    latency_seconds: float
