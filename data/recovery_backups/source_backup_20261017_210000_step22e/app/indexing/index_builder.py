from app.ingestion.pdf_loader import load_pdf
from app.chunking.semantic_chunker import chunk_document
from app.indexing.embedding_service import EmbeddingService
from app.indexing.vector_store import VectorStore
from app.config import settings

def build_index(pdf_path: str):
    # 1. Load PDF
    document = load_pdf(pdf_path)
    
    # 2. Chunk Document
    chunks = chunk_document(document)
    
    if not chunks:
        raise ValueError("No chunks generated from the document.")
        
    # 3. Generate Embeddings
    embedding_service = EmbeddingService()
    
    metadata = []
    embeddings = []
    
    failed_chunks = 0
    
    for chunk in chunks:
        try:
            vector = embedding_service.embed_text(chunk.text)
            embeddings.append(vector)
            
            # Prepare metadata
            meta = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "language": chunk.language,
                "pages": chunk.pages,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page,
                "character_count": chunk.character_count,
                "embedding_model": settings.embedding_model,
                "text": chunk.text
            }
            metadata.append(meta)
            
        except Exception as e:
            failed_chunks += 1
            print(f"Failed to embed chunk {chunk.chunk_id}: {e}")
            
    # 4. Store
    vector_store = VectorStore()
    vector_store.save(document.document_id, metadata, embeddings)
    
    return {
        "document_id": document.document_id,
        "total_chunks": len(chunks),
        "embedded_chunks": len(embeddings),
        "failed_chunks": failed_chunks,
        "embedding_dim": len(embeddings[0]) if embeddings else 0,
        "metadata": metadata
    }
