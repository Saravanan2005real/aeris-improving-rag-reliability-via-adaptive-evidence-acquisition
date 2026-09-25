from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sentence_transformers import CrossEncoder

from app.retrieval.hybrid_retriever import HybridResult


@dataclass
class RerankResult:
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
    retrieval_score: float
    rerank_score: float


class Reranker:
    """
    Cross-encoder reranker.

    Takes candidates produced by hybrid retrieval and
    reorders them according to query-passage relevance.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: List[HybridResult],
        top_k: int = 5,
    ) -> List[RerankResult]:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if not candidates:
            return []

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        pairs = [
            (query, candidate.text)
            for candidate in candidates
        ]

        scores = self.model.predict(pairs)

        results = []

        for candidate, score in zip(candidates, scores):

            results.append(
                RerankResult(
                    rank=0,
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    text=candidate.text,
                    language=candidate.language,
                    pages=candidate.pages,
                    start_page=candidate.start_page,
                    end_page=candidate.end_page,
                    dense_score=candidate.dense_score,
                    bm25_score=candidate.bm25_score,
                    retrieval_score=candidate.hybrid_score,
                    rerank_score=float(score),
                )
            )

        results.sort(
            key=lambda result: result.rerank_score,
            reverse=True,
        )

        results = results[:top_k]

        for rank, result in enumerate(results, start=1):
            result.rank = rank

        return results
