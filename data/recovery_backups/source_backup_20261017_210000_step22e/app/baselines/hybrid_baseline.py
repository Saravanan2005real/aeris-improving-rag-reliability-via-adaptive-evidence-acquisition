import time
from app.retrieval.hybrid_retriever import HybridRetriever
from app.baselines.schemas import BaselineResult

class HybridBaseline:
    def __init__(self, retriever=None):
        self.retriever = retriever or HybridRetriever()
        
    def run(self, question_id: str, question: str, document_id: str, top_k: int) -> BaselineResult:
        start_time = time.time()
        
        # for strict top_k baseline with no expansion, we set candidate_k = top_k 
        # or we just use default candidate_k for hybrid inner mechanics and trim to top_k.
        # usually hybrid needs a larger candidate_k for RRF to work well. Let's use 25.
        results = self.retriever.retrieve(
            document_id=document_id,
            query=question,
            top_k=top_k,
            candidate_k=25
        )
        
        latency = time.time() - start_time
        
        pages = []
        for r in results:
            if getattr(r, "start_page", 0) > 0:
                pages.append(r.start_page)
                
        return BaselineResult(
            baseline_name="HYBRID_TOP_K",
            question_id=question_id,
            question=question,
            document_id=document_id,
            retrieved_chunk_ids=[r.chunk_id for r in results],
            retrieved_pages=list(set(pages)),
            retrieval_scores=[r.hybrid_score for r in results],
            retrieval_count=len(results),
            latency_seconds=latency
        )
