import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.benchmark.dataset import BenchmarkDataset
from app.baselines.dense_baseline import DenseBaseline
from app.baselines.bm25_baseline import BM25Baseline
from app.baselines.hybrid_baseline import HybridBaseline
from app.baselines.hybrid_rerank_baseline import HybridRerankBaseline

def main():
    print("==================================================")
    print("AERIS-RAG BASELINE RETRIEVAL RUNNER")
    print("==================================================")
    
    dataset_path = "data/benchmark/aeris_benchmark.json"
    results_path = "data/results/baseline_retrieval_results.json"
    
    if not os.path.exists(dataset_path):
        print("Dataset not found!")
        sys.exit(1)
        
    dataset = BenchmarkDataset(dataset_path)
    
    print("Initializing base retrievers...")
    from app.retrieval.hybrid_retriever import HybridRetriever
    from app.retrieval.reranker import Reranker
    
    shared_hybrid = HybridRetriever()
    shared_dense = shared_hybrid.dense_retriever
    shared_bm25 = shared_hybrid.bm25_retriever
    shared_reranker = Reranker()
    
    print("Initializing baselines...")
    dense_bl = DenseBaseline(retriever=shared_dense)
    bm25_bl = BM25Baseline(retriever=shared_bm25)
    hybrid_bl = HybridBaseline(retriever=shared_hybrid)
    hybrid_rerank_bl = HybridRerankBaseline(hybrid=shared_hybrid, reranker=shared_reranker)
    
    baselines = [
        ("DENSE_TOP_K", dense_bl),
        ("BM25_TOP_K", bm25_bl),
        ("HYBRID_TOP_K", hybrid_bl),
        ("HYBRID_RERANKED", hybrid_rerank_bl)
    ]
    
    results = []
    
    top_k = 5
    
    for i, record in enumerate(dataset.records):
        print(f"\nProcessing {i+1}/{len(dataset.records)}: {record.question_id}")
        
        for name, bl in baselines:
            print(f"  -> Running {name}")
            try:
                res = bl.run(
                    question_id=record.question_id,
                    question=record.question,
                    document_id=record.document_id,
                    top_k=top_k
                )
                results.append(res.model_dump())
            except Exception as e:
                print(f"     [ERROR] Failed on {name}: {e}")
                
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("\n==================================================")
    print(f"DONE! Saved {len(results)} results to {results_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
