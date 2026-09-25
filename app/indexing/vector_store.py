import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple

class VectorStore:
    def __init__(self, base_dir: str = "data/indexes"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
    def save(self, document_id: str, metadata: List[Dict[str, Any]], embeddings: List[List[float]]):
        doc_dir = os.path.join(self.base_dir, document_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        # Save metadata
        metadata_path = os.path.join(doc_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        # Save embeddings
        embeddings_path = os.path.join(doc_dir, "embeddings.npy")
        np.save(embeddings_path, np.array(embeddings, dtype=np.float32))
        
    def load(self, document_id: str) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        doc_dir = os.path.join(self.base_dir, document_id)
        metadata_path = os.path.join(doc_dir, "metadata.json")
        embeddings_path = os.path.join(doc_dir, "embeddings.npy")
        
        if not os.path.exists(metadata_path) or not os.path.exists(embeddings_path):
            raise FileNotFoundError(f"Index for {document_id} not found.")
            
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        embeddings = np.load(embeddings_path)
        
        return metadata, embeddings
