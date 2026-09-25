import ollama
from typing import List
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_host)
        self.model = settings.embedding_model
        
    def embed_text(self, text: str) -> List[float]:
        response = self.client.embeddings(
            model=self.model,
            prompt=text
        )
        return response["embedding"]
        
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Generating embeddings one by one for reliability
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_text(text))
        return embeddings
