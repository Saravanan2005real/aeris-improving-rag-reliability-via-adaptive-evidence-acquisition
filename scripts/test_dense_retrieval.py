import sys
import os
import argparse
import io

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval.dense_retriever import DenseRetriever

def main():
    parser = argparse.ArgumentParser(description="Test Dense Retrieval")
    parser.add_argument("pdf_path", help="Path to the PDF file (used to derive document_id)")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found at {args.pdf_path}")
        sys.exit(1)
        
    filename = os.path.basename(args.pdf_path)
    document_id = os.path.splitext(filename)[0]

    retriever = DenseRetriever()
    
    test_queries = [
        "What datasets were used in the experiments?",
        "What is the RAG model?",
        "How does the retriever work?",
        "What are the main experimental results?",
        "What is the difference between RAG-Sequence and RAG-Token?"
    ]
    
    successful = 0
    failures = 0
    top_k = 5
    
    for query in test_queries:
        print("=" * 50)
        print("QUERY")
        print("=" * 50)
        print()
        print(f"Query: {query}")
        print()
        print("-" * 50)
        print(f"TOP {top_k} RESULTS")
        print("-" * 50)
        print()
        
        try:
            results = retriever.retrieve(document_id=document_id, query=query, top_k=top_k)
            for res in results:
                print(f"Rank {res.rank}")
                print(f"Chunk ID      : {res.chunk_id}")
                print(f"Similarity    : {res.similarity_score:.4f}")
                print(f"Pages         : {res.pages}")
                print(f"Language      : {res.language}")
                
                snippet = res.text[:400].replace('\n', ' ')
                print("Text          : ", end="")
                try:
                    print(snippet)
                except UnicodeEncodeError:
                    print(snippet.encode('ascii', 'replace').decode('ascii'))
                print("\n")
            successful += 1
        except Exception as e:
            print(f"Retrieval failed for query: {e}")
            failures += 1
            
    print("=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"- Queries tested         : {len(test_queries)}")
    print(f"- Successful queries     : {successful}")
    print(f"- Retrieval failures     : {failures}")
    print(f"- Top-k used             : {top_k}")
    print(f"- Index document ID      : {document_id}")
    
    # Try to count chunks
    try:
        from app.indexing.vector_store import VectorStore
        vs = VectorStore()
        meta, _ = vs.load(document_id)
        print(f"- Number of indexed chunks : {len(meta)}")
    except:
        print("- Number of indexed chunks : Unknown")

if __name__ == "__main__":
    main()
