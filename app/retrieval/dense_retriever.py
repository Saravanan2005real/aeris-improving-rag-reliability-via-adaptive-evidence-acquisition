import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from app.indexing.embedding_service import EmbeddingService
from app.indexing.vector_store import VectorStore

class RetrievalResult(BaseModel):
    rank: int
    chunk_id: str
    document_id: str
    text: str
    language: str
    pages: List[int]
    start_page: int
    end_page: int
    similarity_score: float

class DenseRetriever:
    def __init__(self, vector_store: Optional[VectorStore] = None, embedding_service: Optional[EmbeddingService] = None):
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService()
        
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        v1_norm = np.linalg.norm(v1)
        v2_norm = np.linalg.norm(v2, axis=1)
        
        if v1_norm == 0:
            return np.zeros(v2.shape[0])
            
        # Avoid division by zero
        v2_norm = np.where(v2_norm == 0, 1.0, v2_norm)
        
        return np.dot(v2, v1) / (v1_norm * v2_norm)

    def retrieve(self, document_id: str, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
            
        if top_k <= 0:
            raise ValueError(f"Invalid top_k: {top_k}. Must be greater than 0.")
            
        try:
            metadata, embeddings = self.vector_store.load(document_id)
        except Exception as e:
            raise ValueError(f"Failed to load index for document {document_id}: {e}")
            
        if not metadata or len(embeddings) == 0:
            raise ValueError("Index is empty.")
            
        if len(metadata) != embeddings.shape[0]:
            raise ValueError("Index is malformed: metadata length doesn't match embeddings.")
            
        query_vector = np.array(self.embedding_service.embed_text(query), dtype=np.float32)
        
        if query_vector.shape[0] != embeddings.shape[1]:
            raise ValueError(f"Embedding dimension mismatch. Query: {query_vector.shape[0]}, Index: {embeddings.shape[1]}")
            
        similarities = self._cosine_similarity(query_vector, embeddings)
        
        # Get top_k indices
        k = min(top_k, len(similarities))
        
        # np.argsort sorts ascending, so we reverse it
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            meta = metadata[idx]
            results.append(RetrievalResult(
                rank=rank,
                chunk_id=meta["chunk_id"],
                document_id=meta["document_id"],
                text=meta["text"],
                language=meta["language"],
                pages=meta["pages"],
                start_page=meta["start_page"],
                end_page=meta["end_page"],
                similarity_score=float(similarities[idx])
            ))
            
        return results
