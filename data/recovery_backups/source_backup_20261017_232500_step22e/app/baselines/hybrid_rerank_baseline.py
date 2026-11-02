import time
from typing import List
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.baselines.schemas import BaselineResult
from pydantic import BaseModel

# Mocking reranker schemas since reranker requires EvidenceItem
class DummyEvidenceItem(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    language: str
    pages: List[int]
    start_page: int
    end_page: int
    retrieval_score: float

class HybridRerankBaseline:
    def __init__(self, hybrid=None, reranker=None):
        self.hybrid = hybrid or HybridRetriever()
        self.reranker = reranker or Reranker()
        
    def run(self, question_id: str, question: str, document_id: str, top_k: int, candidate_k: int = 25) -> BaselineResult:
        start_time = time.time()
        
        # 1. Hybrid Retrieval
        hybrid_results = self.hybrid.retrieve(
            document_id=document_id,
            query=question,
            top_k=candidate_k,
            candidate_k=candidate_k
        )
        
        if not hybrid_results:
            return BaselineResult(
                baseline_name="HYBRID_RERANKED",
                question_id=question_id,
                question=question,
                document_id=document_id,
                retrieved_chunk_ids=[],
                retrieved_pages=[],
                retrieval_scores=[],
                retrieval_count=0,
                latency_seconds=time.time() - start_time
            )
            
        # 2. Reranking
        reranked_results = self.reranker.rerank(
            query=question,
            candidates=hybrid_results,
            top_k=top_k
        )
        
        latency = time.time() - start_time
        
        pages = []
        for r in reranked_results:
            if getattr(r, "start_page", 0) > 0:
                pages.append(r.start_page)
                
        return BaselineResult(
            baseline_name="HYBRID_RERANKED",
            question_id=question_id,
            question=question,
            document_id=document_id,
            retrieved_chunk_ids=[r.chunk_id for r in reranked_results],
            retrieved_pages=list(set(pages)),
            retrieval_scores=[r.rerank_score or 0.0 for r in reranked_results],
            retrieval_count=len(reranked_results),
            latency_seconds=latency
        )
