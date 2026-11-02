import time
from app.retrieval.dense_retriever import DenseRetriever
from app.baselines.schemas import BaselineResult

class DenseBaseline:
    def __init__(self, retriever=None):
        self.retriever = retriever or DenseRetriever()
        
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
            baseline_name="DENSE_TOP_K",
            question_id=question_id,
            question=question,
            document_id=document_id,
            retrieved_chunk_ids=[r.chunk_id for r in results],
            retrieved_pages=list(set(pages)),
            retrieval_scores=[r.similarity_score for r in results],
            retrieval_count=len(results),
            latency_seconds=latency
        )
