import sys
import io
import os

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker


QUERIES = [
    "What datasets were used in the experiments?",
    "What is the RAG model?",
    "How does the retriever work?",
    "What are the main experimental results?",
    "What is the difference between RAG-Sequence and RAG-Token?",
]


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/test_reranker.py "
            "<pdf_path>"
        )
        sys.exit(1)

    pdf_path = sys.argv[1]
    
    document_id = (
        pdf_path
        .replace("\\", "/")
        .split("/")[-1]
        .replace(".pdf", "")
    )

    hybrid = HybridRetriever(
        index_root="data/indexes",
        rrf_k=60,
    )

    reranker = Reranker()

    successful = 0
    failed = 0

    for query in QUERIES:

        print("\n" + "=" * 60)
        print("QUERY")
        print("=" * 60)
        print(f"\nQuery: {query}")

        try:
            candidates = hybrid.retrieve(
                document_id=document_id,
                query=query,
                top_k=10,
                candidate_k=10,
            )

            results = reranker.rerank(
                query=query,
                candidates=candidates,
                top_k=5,
            )

            print("\n" + "-" * 60)
            print("TOP 5 RERANKED RESULTS")
            print("-" * 60)

            for result in results:

                print(f"\nRank {result.rank}")
                print(f"Chunk ID       : {result.chunk_id}")
                print(f"Dense Score    : {result.dense_score:.4f}")
                print(f"BM25 Score     : {result.bm25_score:.4f}")
                print(
                    f"RRF Score      : "
                    f"{result.retrieval_score:.4f}"
                )
                print(
                    f"Rerank Score   : "
                    f"{result.rerank_score:.4f}"
                )
                print(f"Pages          : {result.pages}")
                print(f"Language       : {result.language}")
                
                snippet = result.text[:700].replace('\n', ' ')
                try:
                    print(f"Text           : {snippet}")
                except UnicodeEncodeError:
                    print(f"Text           : {snippet.encode('ascii', 'replace').decode('ascii')}")

            successful += 1

        except Exception as exc:
            failed += 1

            print("\nERROR")
            print(str(exc))

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Queries tested     : {len(QUERIES)}")
    print(f"Successful queries : {successful}")
    print(f"Failed queries     : {failed}")
    print(f"Candidate-k        : 10")
    print(f"Final top-k        : 5")
    print(f"Index document ID  : {document_id}")
    print(
        "Reranker           : "
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )


if __name__ == "__main__":
    main()
