from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from rank_bm25 import BM25Okapi


@dataclass
class BM25Result:
    rank: int
    chunk_id: str
    document_id: str
    text: str
    language: str
    pages: List[int]
    start_page: int
    end_page: int
    bm25_score: float


class BM25Retriever:
    def __init__(self, index_root: str = "data/indexes"):
        self.index_root = Path(index_root)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _load_metadata(self, document_id: str):
        metadata_path = self.index_root / document_id / "metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata not found for document: {document_id}"
            )

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        if not isinstance(metadata, list) or not metadata:
            raise ValueError("Metadata is empty or malformed.")

        return metadata

    def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[BM25Result]:

        if not document_id.strip():
            raise ValueError("document_id cannot be empty.")

        if not query.strip():
            raise ValueError("query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        metadata = self._load_metadata(document_id)

        documents = [item["text"] for item in metadata]
        tokenized_documents = [
            self._tokenize(text)
            for text in documents
        ]

        bm25 = BM25Okapi(tokenized_documents)

        query_tokens = self._tokenize(query)

        if not query_tokens:
            raise ValueError("Query contains no valid tokens.")

        scores = bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        results = []

        for rank, index in enumerate(
            ranked_indices[:min(top_k, len(ranked_indices))],
            start=1,
        ):
            item = metadata[index]

            results.append(
                BM25Result(
                    rank=rank,
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    language=item["language"],
                    pages=item["pages"],
                    start_page=item["start_page"],
                    end_page=item["end_page"],
                    bm25_score=float(scores[index]),
                )
            )

        return results
