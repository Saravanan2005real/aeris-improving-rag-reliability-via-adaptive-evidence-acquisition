import json
import os
import sys
import numpy as np
from collections import defaultdict

def main():
    results_path = "data/results/ablation_results_full_robust.json"
    diag_path = "data/results/generation_diagnostics_full_robust.jsonl"
    
    if not os.path.exists(results_path):
        print(f"File not found: {results_path}")
        sys.exit(1)
        
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    repair_count = 0
    retry_count = 0
    
    if os.path.exists(diag_path):
        with open(diag_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("repair_invoked"):
                        repair_count += 1
                    if data.get("retry_invoked"):
                        retry_count += 1
                except:
                    pass

    total_runs = len(results)
    successful_runs = sum(1 for r in results if r.get("final_status") != "FAILED")
    failed_runs = total_runs - successful_runs
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    q_counts = defaultdict(int)
    v_counts = defaultdict(int)
    failures_by_stage = defaultdict(int)
    failures_by_error = defaultdict(int)
    question_failures = defaultdict(int)
    variant_failures = defaultdict(int)
    
    latencies = []
    
    evidence_hit_count = 0
    evidence_recall_sum = 0.0
    ans_count = 0
    verified_sum = 0
    selected_sum = 0
    status_dist = defaultdict(int)

    for res in results:
        v, q = res.get("variant", "UNKNOWN"), res.get("question_id", "UNKNOWN")
        q_counts[q] += 1
        v_counts[v] += 1
        
        lat = res.get("latency_seconds", 0)
        latencies.append(lat)
        
        if res.get("final_status") == "FAILED":
            question_failures[q] += 1
            variant_failures[v] += 1
            
            error_str = str(res.get("error", ""))
            error_type = "Unknown"
            if "JSON" in error_str:
                error_type = "ParsingError"
            elif "Valid" in error_str or "Value" in error_str:
                error_type = "SchemaError"
            else:
                error_type = error_str.split(":")[0] if ":" in error_str else error_str[:30]
                
            failures_by_error[error_type] += 1
            
            stage = "Unknown"
            if "stage_statuses" in res:
                # Need to deduce stage based on what failed
                pass
            # Just approximation, can't perfectly know stage if runner didn't log it nicely
            failures_by_stage[stage] += 1
        else:
            if res.get("expected_answerability", True):
                ans_count += 1
                if res.get("evidence_hit", False):
                    evidence_hit_count += 1
                evidence_recall_sum += res.get("evidence_recall", 0.0)
                
            verified_sum += res.get("verified_claim_count", 0)
            selected_sum += res.get("selected_verification_count", 0)
            status_dist[res.get("answer_status", res.get("final_status", "UNKNOWN"))] += 1

    mean_lat = np.mean(latencies) if latencies else 0.0
    med_lat = np.median(latencies) if latencies else 0.0
    p95_lat = np.percentile(latencies, 95) if latencies else 0.0
    min_lat = np.min(latencies) if latencies else 0.0
    max_lat = np.max(latencies) if latencies else 0.0

    print("==================================================")
    print("STEP 22C - FULL ROBUST ABLATION REPORT")
    print("==================================================")
    print(f"Total runs: {total_runs}")
    print(f"Successful runs: {successful_runs}")
    print(f"Failed runs: {failed_runs}")
    print(f"Success rate: {success_rate:.2f}%")
    print("")
    print(f"JSON repairs: {repair_count}")
    print(f"Retries: {retry_count}")
    print("")
    print("--- Latencies ---")
    print(f"Mean: {mean_lat:.2f}s")
    print(f"Median: {med_lat:.2f}s")
    print(f"P95: {p95_lat:.2f}s")
    print(f"Min: {min_lat:.2f}s")
    print(f"Max: {max_lat:.2f}s")
    print("")
    print("--- Metrics ---")
    print(f"Evidence hit rate: {evidence_hit_count/ans_count if ans_count > 0 else 0:.4f}")
    print(f"Evidence recall: {evidence_recall_sum/ans_count if ans_count > 0 else 0:.4f}")
    print(f"Verified claims (total): {verified_sum}")
    print(f"Selected verification (total): {selected_sum}")
    print("")
    print("--- Answer Status Distribution ---")
    for k, v in status_dist.items():
        print(f"{k}: {v}")
    
    print("")
    print("--- Failures by Error Type ---")
    for k, v in failures_by_error.items():
        print(f"{k}: {v}")
        
    print("")
    print("--- Dataset Balance ---")
    is_balanced = True
    for v, c in v_counts.items():
        if c != 28:
            print(f"Variant {v} has {c} runs (Expected: 28)")
            is_balanced = False
    for q, c in q_counts.items():
        if c != 8:
            print(f"Question {q} has {c} runs (Expected: 8)")
            is_balanced = False
            
    if is_balanced:
        print("Dataset is fully balanced: 28 runs per variant, 8 runs per question.")
    else:
        print("WARNING: Dataset is NOT fully balanced!")
        
    print("==================================================")

if __name__ == "__main__":
    main()
