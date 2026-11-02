import time
from app.retrieval.bm25_retriever import BM25Retriever
from app.baselines.schemas import BaselineResult

class BM25Baseline:
    def __init__(self, retriever=None):
        self.retriever = retriever or BM25Retriever()
        
    def run(self, question_id: str, question: str, document_id: str, top_k: int) -> BaselineResult:
        start_time = time.time()
        
        results = self.retriever.retrieve(
            document_id=document_id,
            query=question,
            top_k=top_k
        )
        
        latency = time.time() - start_time
        
        pages = []
        for r in results:
            if getattr(r, "start_page", 0) > 0:
                pages.append(r.start_page)
                
        return BaselineResult(
            baseline_name="BM25_TOP_K",
            question_id=question_id,
            question=question,
            document_id=document_id,
            retrieved_chunk_ids=[r.chunk_id for r in results],
            retrieved_pages=list(set(pages)),
            retrieval_scores=[r.bm25_score for r in results],
            retrieval_count=len(results),
            latency_seconds=latency
        )
