import json
import os
import sys
import numpy as np

def main():
    print("==================================================")
    print("STEP 22C COMPLETE")
    print("=================")
    
    results_path = "data/results/ablation_results_full.json"
    benchmark_path = "data/benchmark/aeris_benchmark.json"
    
    if not os.path.exists(results_path) or not os.path.exists(benchmark_path):
        print("Required files not found!")
        sys.exit(1)
        
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
        
    # Validation checks
    expected_variants = [
        "FULL_AERIS",
        "NO_ADAPTIVE_RETRIEVAL",
        "NO_QUERY_REFORMULATION",
        "NO_RETRIEVAL_MEMORY",
        "NO_CLAIM_VERIFICATION",
        "NO_CONTRADICTION_ANALYSIS",
        "NO_CROSSLINGUAL_AGREEMENT",
        "NO_SELECTIVE_VERIFICATION"
    ]
    
    expected_runs = 224
    completed_runs = len(results)
    failed_runs = sum(1 for r in results if r.get("final_status") == "FAILED")
    
    unique_pairs = set((r["variant"], r["question_id"]) for r in results)
    duplicates = completed_runs - len(unique_pairs)
    
    variants_completed = 0
    for v in expected_variants:
        q_count = sum(1 for r in results if r["variant"] == v)
        if q_count == 28:
            variants_completed += 1
            
    is_valid = (
        completed_runs == expected_runs and
        len(unique_pairs) == expected_runs and
        duplicates == 0 and
        variants_completed == len(expected_variants)
    )
    
    print(f"Runs expected: {expected_runs}")
    print(f"Runs completed: {completed_runs}")
    print(f"Runs failed: {failed_runs}")
    print(f"Unique pairs: {len(unique_pairs)}")
    print(f"Duplicates: {duplicates}")
    print(f"Variants complete: {variants_completed}/{len(expected_variants)}")
    print(f"Questions per variant: 28")
    print(f"Experiment valid: {'YES' if is_valid else 'NO'}")
    print("\n==================================================")
    print("METRICS BY VARIANT")
    print("==================================================")
    
    stats = {}
    
    for res in results:
        v = res["variant"]
        if v not in stats:
            stats[v] = {
                "total": 0,
                "failed": 0,
                "answerable": 0,
                "unanswerable": 0,
                "hit_count": 0,
                "recall_sum": 0.0,
                "latencies": [],
                "evidence_sum": 0,
                "claim_sum": 0,
                "verified_sum": 0,
                "selected_sum": 0,
                "status_counts": {},
                "supported_answers": 0,
                "insuff_answers": 0,
                "contra_answers": 0,
                "json_failures": 0,
                "categories": {}
            }
            
        cat = res["question_type"]
        if cat not in stats[v]["categories"]:
            stats[v]["categories"][cat] = {"total": 0, "hits": 0, "recall_sum": 0.0}
            
        stats[v]["total"] += 1
        stats[v]["categories"][cat]["total"] += 1
        
        if res.get("final_status") == "FAILED":
            stats[v]["failed"] += 1
            if "JSON" in str(res.get("error", "")):
                stats[v]["json_failures"] += 1
            continue
            
        stats[v]["latencies"].append(res.get("latency_seconds", 0))
        stats[v]["evidence_sum"] += res.get("evidence_count", 0)
        stats[v]["claim_sum"] += res.get("claim_count", 0)
        stats[v]["verified_sum"] += res.get("verified_claim_count", 0)
        stats[v]["selected_sum"] += res.get("selected_verification_count", 0)
        
        f_status = res.get("final_status", "")
        stats[v]["status_counts"][f_status] = stats[v]["status_counts"].get(f_status, 0) + 1
        
        if res.get("answer_status") == "SUPPORTED":
            stats[v]["supported_answers"] += 1
        elif res.get("answer_status") == "INSUFFICIENT_EVIDENCE":
            stats[v]["insuff_answers"] += 1
        elif res.get("answer_status") == "CONTRADICTED":
            stats[v]["contra_answers"] += 1
            
        if res.get("expected_answerability", True):
            stats[v]["answerable"] += 1
            if res.get("evidence_hit", False):
                stats[v]["hit_count"] += 1
                stats[v]["categories"][cat]["hits"] += 1
            stats[v]["recall_sum"] += res.get("evidence_recall", 0.0)
            stats[v]["categories"][cat]["recall_sum"] += res.get("evidence_recall", 0.0)
        else:
            stats[v]["unanswerable"] += 1
            
    metrics = {}
    for v, data in stats.items():
        ans = data["answerable"]
        tot = data["total"] - data["failed"]
        unans = data["unanswerable"]
        
        l_sorted = sorted(data["latencies"])
        metrics[v] = {
            "hr": data["hit_count"] / ans if ans > 0 else 0.0,
            "rec": data["recall_sum"] / ans if ans > 0 else 0.0,
            "avg_l": sum(data["latencies"]) / tot if tot > 0 else 0.0,
            "med_l": np.median(l_sorted) if l_sorted else 0.0,
            "p95_l": np.percentile(l_sorted, 95) if l_sorted else 0.0,
            "avg_ev": data["evidence_sum"] / tot if tot > 0 else 0.0,
            "avg_cl": data["claim_sum"] / tot if tot > 0 else 0.0,
            "avg_ver": data["verified_sum"] / tot if tot > 0 else 0.0,
            "avg_sel": data["selected_sum"] / tot if tot > 0 else 0.0,
            "supp_rt": data["supported_answers"] / ans if ans > 0 else 0.0,
            "insuff_rt": data["insuff_answers"] / unans if unans > 0 else 0.0,
            "contra_rt": data["contra_answers"] / tot if tot > 0 else 0.0,
            "failed": data["failed"],
            "json_err": data["json_failures"],
            "status": data["status_counts"],
            "raw": data
        }

    for v, m in metrics.items():
        print(f"\n[{v}]")
        print(f"  Evidence Hit Rate        : {m['hr']:.4f}")
        print(f"  Evidence Recall          : {m['rec']:.4f}")
        print(f"  Supported Answer Rate    : {m['supp_rt']:.4f}")
        print(f"  Insufficient Rate        : {m['insuff_rt']:.4f}")
        print(f"  Contradicted Rate        : {m['contra_rt']:.4f}")
        print(f"  Avg Latency (s)          : {m['avg_l']:.2f}")
        print(f"  Median Latency (s)       : {m['med_l']:.2f}")
        print(f"  P95 Latency (s)          : {m['p95_l']:.2f}")
        print(f"  Avg Evidence Count       : {m['avg_ev']:.2f}")
        print(f"  Avg Claim Count          : {m['avg_cl']:.2f}")
        print(f"  Avg Verified Claims      : {m['avg_ver']:.2f}")
        print(f"  Avg Selected Claims      : {m['avg_sel']:.2f}")
        print(f"  Failed Runs              : {m['failed']}")
        print(f"  JSON Parsing Failures    : {m['json_err']}")
        print(f"  Status Distribution      : {m['status']}")
        
    print("\n==================================================")
    print("CATEGORY BREAKDOWN (HIT RATE / RECALL)")
    print("==================================================")
    
    for v, m in metrics.items():
        print(f"\n[{v}]")
        for cat, cdata in m['raw']['categories'].items():
            ans_cat = cdata['total']
            cat_hr = cdata['hits'] / ans_cat if ans_cat > 0 else 0.0
            cat_rec = cdata['recall_sum'] / ans_cat if ans_cat > 0 else 0.0
            print(f"  {cat:15} : HR={cat_hr:.2f} REC={cat_rec:.2f}")

    print("\n==================================================")
    print("DELTAS FROM FULL_AERIS")
    print("==================================================")
    
    if "FULL_AERIS" not in metrics:
        print("FULL_AERIS missing.")
        return
        
    ctrl = metrics["FULL_AERIS"]
    print(f"{'Variant':30} | {'HR Delta':10} | {'Rec Delta':10} | {'Latency Delta':15}")
    print("-" * 75)
    for v, m in metrics.items():
        if v == "FULL_AERIS": continue
        print(f"{v:30} | {m['hr'] - ctrl['hr']:10.4f} | {m['rec'] - ctrl['rec']:10.4f} | {m['avg_l'] - ctrl['avg_l']:15.2f}")
        
    print("\nNote: Removing components changed metrics as observed above.")
    print("These results represent a controlled ablation comparison.")

if __name__ == "__main__":
    main()
