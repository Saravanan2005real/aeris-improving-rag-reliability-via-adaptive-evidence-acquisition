from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.bm25_retriever import BM25Retriever


@dataclass
class HybridResult:
    rank: int
    chunk_id: str
    document_id: str
    text: str
    language: str
    pages: List[int]
    start_page: int
    end_page: int
    dense_score: float
    bm25_score: float
    hybrid_score: float


class HybridRetriever:
    def __init__(
        self,
        index_root: str = "data/indexes",
        rrf_k: int = 60,
    ):
        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than zero.")

        self.rrf_k = rrf_k

        from app.indexing.vector_store import VectorStore
        vs = VectorStore(base_dir=index_root)
        self.dense_retriever = DenseRetriever(vector_store=vs)
        self.bm25_retriever = BM25Retriever(index_root=index_root)

    def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int = 5,
        candidate_k: int = 10,
    ) -> List[HybridResult]:

        if not document_id.strip():
            raise ValueError("document_id cannot be empty.")

        if not query.strip():
            raise ValueError("query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if candidate_k <= 0:
            raise ValueError("candidate_k must be greater than zero.")

        candidate_k = max(candidate_k, top_k)

        dense_results = self.dense_retriever.retrieve(
            document_id=document_id,
            query=query,
            top_k=candidate_k,
        )

        bm25_results = self.bm25_retriever.retrieve(
            document_id=document_id,
            query=query,
            top_k=candidate_k,
        )

        dense_scores = {}
        dense_ranks = {}
        metadata_by_chunk = {}
        for res in dense_results:
            dense_scores[res.chunk_id] = res.similarity_score
            dense_ranks[res.chunk_id] = res.rank
            metadata_by_chunk[res.chunk_id] = res

        bm25_scores = {}
        bm25_ranks = {}
        for res in bm25_results:
            bm25_scores[res.chunk_id] = res.bm25_score
            bm25_ranks[res.chunk_id] = res.rank
            if res.chunk_id not in metadata_by_chunk:
                metadata_by_chunk[res.chunk_id] = res

        all_chunk_ids = set(dense_scores) | set(bm25_scores)

        combined = []

        for chunk_id in all_chunk_ids:
            dense_score = dense_scores.get(chunk_id, 0.0)
            bm25_score = bm25_scores.get(chunk_id, 0.0)

            hybrid_score = 0.0
            if chunk_id in dense_ranks:
                hybrid_score += 1.0 / (self.rrf_k + dense_ranks[chunk_id])
            if chunk_id in bm25_ranks:
                hybrid_score += 1.0 / (self.rrf_k + bm25_ranks[chunk_id])

            base = metadata_by_chunk[chunk_id]

            combined.append(
                HybridResult(
                    rank=0,
                    chunk_id=chunk_id,
                    document_id=base.document_id,
                    text=base.text,
                    language=base.language,
                    pages=base.pages,
                    start_page=base.start_page,
                    end_page=base.end_page,
                    dense_score=float(dense_score),
                    bm25_score=float(bm25_score),
                    hybrid_score=float(hybrid_score),
                )
            )

        combined.sort(
            key=lambda result: result.hybrid_score,
            reverse=True,
        )

        final_results = combined[:top_k]

        for rank, result in enumerate(final_results, start=1):
            result.rank = rank

        return final_results
