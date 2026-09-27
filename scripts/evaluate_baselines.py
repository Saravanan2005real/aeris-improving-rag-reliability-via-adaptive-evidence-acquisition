import json
import os
import sys

def main():
    print("==================================================")
    print("AERIS-RAG BASELINE EVALUATION")
    print("==================================================")
    
    dataset_path = "data/benchmark/aeris_benchmark.json"
    results_path = "data/results/baseline_retrieval_results.json"
    
    if not os.path.exists(dataset_path) or not os.path.exists(results_path):
        print("Required files not found!")
        sys.exit(1)
        
    with open(dataset_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
        
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    benchmark_map = {r["question_id"]: r for r in benchmark}
    
    stats = {}
    
    for res in results:
        b_name = res["baseline_name"]
        q_id = res["question_id"]
        
        if b_name not in stats:
            stats[b_name] = {
                "total_questions": 0,
                "answerable_questions": 0,
                "hit_count": 0,
                "recall_sum": 0.0,
                "latency_sum": 0.0,
                "latencies": [],
                "retrieved_chunks_sum": 0,
                "category_hits": {}
            }
            
        b_record = benchmark_map.get(q_id)
        if not b_record:
            continue
            
        category = b_record["category"]
        if category not in stats[b_name]["category_hits"]:
            stats[b_name]["category_hits"][category] = {"hits": 0, "total": 0}
            
        stats[b_name]["total_questions"] += 1
        stats[b_name]["latency_sum"] += res["latency_seconds"]
        stats[b_name]["latencies"].append(res["latency_seconds"])
        stats[b_name]["retrieved_chunks_sum"] += res["retrieval_count"]
        
        if b_record["answerability"]:
            stats[b_name]["answerable_questions"] += 1
            stats[b_name]["category_hits"][category]["total"] += 1
            
            expected = set(b_record["supporting_chunk_ids"])
            retrieved = set(res["retrieved_chunk_ids"])
            
            intersection = expected.intersection(retrieved)
            if len(intersection) > 0:
                stats[b_name]["hit_count"] += 1
                stats[b_name]["category_hits"][category]["hits"] += 1
                
            if len(expected) > 0:
                recall = len(intersection) / len(expected)
                stats[b_name]["recall_sum"] += recall
                
    for b_name, data in stats.items():
        print(f"\n--- BASELINE: {b_name} ---")
        total = data["total_questions"]
        answerable = data["answerable_questions"]
        
        if answerable > 0:
            hit_rate = data["hit_count"] / answerable
            recall = data["recall_sum"] / answerable
        else:
            hit_rate = 0.0
            recall = 0.0
            
        avg_latency = data["latency_sum"] / total if total > 0 else 0.0
        sorted_l = sorted(data["latencies"])
        median_latency = sorted_l[len(sorted_l)//2] if sorted_l else 0.0
        avg_chunks = data["retrieved_chunks_sum"] / total if total > 0 else 0.0
        
        print(f"Total Questions Evaluated : {total}")
        print(f"Answerable Questions      : {answerable}")
        print(f"Evidence Hit Rate         : {hit_rate:.4f} ({data['hit_count']}/{answerable})")
        print(f"Evidence Recall           : {recall:.4f}")
        print(f"Average Latency           : {avg_latency:.4f}s")
        print(f"Median Latency            : {median_latency:.4f}s")
        print(f"Average Retrieved Chunks  : {avg_chunks:.2f}")
        
        print("Hits by Category (Answerable Only):")
        for cat, cdata in data["category_hits"].items():
            if cdata["total"] > 0:
                print(f"  {cat}: {cdata['hits']}/{cdata['total']} ({cdata['hits']/cdata['total']:.2f})")
                
if __name__ == "__main__":
    main()
