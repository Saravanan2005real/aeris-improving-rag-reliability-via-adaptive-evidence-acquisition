import sys
import io

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')
    
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval.bm25_retriever import BM25Retriever


def print_results(query, results):
    print("\n" + "=" * 50)
    print("QUERY")
    print("=" * 50)

    print(f"\nQuery: {query}")

    print("\n" + "-" * 50)
    print("TOP 5 BM25 RESULTS")
    print("-" * 50)

    for result in results:
        print(f"\nRank {result.rank}")
        print(f"Chunk ID      : {result.chunk_id}")
        print(f"BM25 Score    : {result.bm25_score:.4f}")
        print(f"Pages         : {result.pages}")
        print(f"Language      : {result.language}")
        
        snippet = result.text[:500].replace('\n', ' ')
        try:
            print(f"Text          : {snippet}")
        except UnicodeEncodeError:
            print(f"Text          : {snippet.encode('ascii', 'replace').decode('ascii')}")


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/test_bm25_retrieval.py "
            "data/raw/test_document.pdf"
        )
        sys.exit(1)

    pdf_path = sys.argv[1]

    document_id = pdf_path.split("\\")[-1].split("/")[-1].replace(".pdf", "")

    retriever = BM25Retriever()

    queries = [
        "What datasets were used in the experiments?",
        "What is the RAG model?",
        "How does the retriever work?",
        "What are the main experimental results?",
        "What is the difference between RAG-Sequence and RAG-Token?",
    ]

    successful = 0

    for query in queries:
        try:
            results = retriever.retrieve(
                document_id=document_id,
                query=query,
                top_k=5,
            )

            print_results(query, results)
            successful += 1

        except Exception as exc:
            print(f"\nERROR for query '{query}': {exc}")

    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Queries tested     : {len(queries)}")
    print(f"Successful queries : {successful}")
    print(f"Failed queries     : {len(queries) - successful}")
    print(f"Top-k used         : 5")
    print(f"Index document ID  : {document_id}")


if __name__ == "__main__":
    main()
