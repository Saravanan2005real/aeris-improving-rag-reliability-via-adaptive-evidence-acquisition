import sys
import os
import argparse
import io

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.indexing.index_builder import build_index
from app.indexing.vector_store import VectorStore
from app.config import settings

def main():
    parser = argparse.ArgumentParser(description="Test PDF Indexing")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found at {args.pdf_path}")
        sys.exit(1)

    print("Building index... (this may take a minute as it calls Ollama)")
    
    try:
        result = build_index(args.pdf_path)
    except Exception as e:
        print(f"Error building index: {e}")
        sys.exit(1)

    print("=" * 50)
    print("AERIS-RAG INDEXING TEST")
    print("=" * 50)
    print()
    print(f"Document ID      : {result['document_id']}")
    print(f"Total chunks     : {result['total_chunks']}")
    print(f"Embedding model  : {settings.embedding_model}")
    print(f"Embedded chunks  : {result['embedded_chunks']}")
    print(f"Failed chunks    : {result['failed_chunks']}")
    print(f"Embedding dim    : {result['embedding_dim']}")
    print()

    # Validation
    metadata = result['metadata']
    valid_chunk_ids = all("chunk_id" in m and isinstance(m["chunk_id"], str) for m in metadata)
    valid_doc_ids = all(m.get("document_id") == result['document_id'] for m in metadata)
    valid_pages = all("pages" in m and isinstance(m["pages"], list) for m in metadata)

    print("Provenance validation")
    print("-" * 21)
    print(f"Valid chunk IDs        : {valid_chunk_ids}")
    print(f"Valid document IDs     : {valid_doc_ids}")
    print(f"Valid page references  : {valid_pages}")
    print()

    # Test loading
    try:
        store = VectorStore()
        loaded_meta, loaded_vecs = store.load(result['document_id'])
        
        # Verify vector and metadata length match
        if len(loaded_meta) == result['embedded_chunks'] and loaded_vecs.shape == (result['embedded_chunks'], result['embedding_dim']):
            print("Index status           : SUCCESS")
            
            # Validation for requirement 5
            if loaded_meta:
                sample = loaded_meta[0]
                expected_keys = ["document_id", "text", "language", "pages", "start_page", "end_page"]
                has_all_keys = all(k in sample for k in expected_keys)
                
                print("Mapping status         : " + ("SUCCESS" if has_all_keys else "FAILED"))
                print(f"Sample chunk_id        : {sample['chunk_id']}")
                if has_all_keys:
                    print("Sample metadata mapping:")
                    for k in expected_keys:
                        val = str(sample[k])
                        if len(val) > 60:
                            val = val[:60] + "..."
                        print(f"  - {k:<13}: {val}")
                else:
                    print(f"Missing keys in sample chunk: {[k for k in expected_keys if k not in sample]}")
        else:
            print("Index status           : FAILED (load mismatch)")
    except Exception as e:
        print(f"Index status           : FAILED ({e})")

if __name__ == "__main__":
    main()
