import sys
import io
import os

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval.hybrid_retriever import HybridRetriever


def print_results(query, results):
    print("\n" + "=" * 60)
    print("QUERY")
    print("=" * 60)

    print(f"\nQuery: {query}")

    print("\n" + "-" * 60)
    print("TOP 5 HYBRID RESULTS (RRF)")
    print("-" * 60)

    for result in results:
        print(f"\nRank {result.rank}")
        print(f"Chunk ID       : {result.chunk_id}")
        print(f"Dense Score    : {result.dense_score:.4f}")
        print(f"BM25 Score     : {result.bm25_score:.4f}")
        print(f"Hybrid Score   : {result.hybrid_score:.4f} (RRF)")
        print(f"Pages          : {result.pages}")
        print(f"Language       : {result.language}")
        
        snippet = result.text[:500].replace('\n', ' ')
        try:
            print(f"Text           : {snippet}")
        except UnicodeEncodeError:
            print(f"Text           : {snippet.encode('ascii', 'replace').decode('ascii')}")


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/test_hybrid_retrieval.py "
            "data/raw/test_document.pdf"
        )
        sys.exit(1)

    pdf_path = sys.argv[1]

    document_id = (
        pdf_path
        .replace("\\", "/")
        .split("/")[-1]
        .replace(".pdf", "")
    )

    retriever = HybridRetriever(
        index_root="data/indexes",
        rrf_k=60,
    )

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
                candidate_k=10,
            )

            print_results(query, results)
            successful += 1

        except Exception as exc:
            print(f"\nERROR for query '{query}': {exc}")

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Queries tested     : {len(queries)}")
    print(f"Successful queries : {successful}")
    print(f"Failed queries     : {len(queries) - successful}")
    print(f"Top-k used         : 5")
    print(f"Candidate-k        : 10")
    print(f"RRF k-factor       : 60")
    print(f"Index document ID  : {document_id}")


if __name__ == "__main__":
    main()
