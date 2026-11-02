import json
import statistics
from collections import defaultdict
import os

def calculate_metrics(runs):
    total = len(runs)
    if total == 0:
        return {}
    
    success_runs = [r for r in runs if r["final_status"] != "FAILED"]
    failures = [r for r in runs if r["final_status"] == "FAILED"]
    
    # JSON parsing failures: this is a proxy. Usually ValueError or JSONDecodeError is in the error message.
    json_failures = [f for f in failures if f.get("error") and "JSON" in f["error"]]
    
    evidence_hits = sum(1 for r in success_runs if r.get("evidence_hit", False))
    evidence_recalls = [r.get("evidence_recall", 0.0) for r in success_runs]
    
    statuses = defaultdict(int)
    for r in success_runs:
        statuses[r.get("final_status", "UNKNOWN")] += 1
        
    supported = statuses.get("ANSWERED", 0)
    insufficient = statuses.get("INSUFFICIENT_EVIDENCE", 0)
    conflicted = statuses.get("CONFLICTING_EVIDENCE", 0)
    
    latencies = [r.get("latency_seconds", 0.0) for r in success_runs]
    avg_latency = statistics.mean(latencies) if latencies else 0.0
    median_latency = statistics.median(latencies) if latencies else 0.0
    
    latencies_sorted = sorted(latencies)
    p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0.0
    
    ev_counts = [r.get("evidence_count", 0) for r in success_runs]
    claim_counts = [r.get("claim_count", 0) for r in success_runs]
    verified_counts = [r.get("verified_claim_count", 0) for r in success_runs]
    selected_counts = [r.get("selected_verification_count", 0) for r in success_runs]
    
    return {
        "runs": total,
        "failures": len(failures),
        "json_failures": len(json_failures),
        "evidence_hit_rate": (evidence_hits / len(success_runs)) if success_runs else 0.0,
        "evidence_recall": statistics.mean(evidence_recalls) if evidence_recalls else 0.0,
        "supported_rate": (supported / len(success_runs)) if success_runs else 0.0,
        "insufficient_rate": (insufficient / len(success_runs)) if success_runs else 0.0,
        "conflicted_rate": (conflicted / len(success_runs)) if success_runs else 0.0,
        "avg_latency": avg_latency,
        "median_latency": median_latency,
        "p95_latency": p95_latency,
        "avg_evidence": statistics.mean(ev_counts) if ev_counts else 0.0,
        "avg_claims": statistics.mean(claim_counts) if claim_counts else 0.0,
        "avg_verified": statistics.mean(verified_counts) if verified_counts else 0.0,
        "avg_selected": statistics.mean(selected_counts) if selected_counts else 0.0,
        "status_distribution": dict(statuses)
    }

def print_metrics(name, m, base_m=None):
    print(f"\\n--- {name} ---")
    
    def format_val(key, val, base_val, is_pct=False):
        if is_pct:
            s = f"{val*100:.1f}%"
            if base_val is not None:
                diff = (val - base_val) * 100
                s += f" (diff {diff:+.1f}%)"
            return s
        else:
            s = f"{val:.2f}"
            if base_val is not None:
                diff = val - base_val
                s += f" (diff {diff:+.2f})"
            return s

    print(f"Evidence Hit Rate: {format_val('evidence_hit_rate', m['evidence_hit_rate'], base_m['evidence_hit_rate'] if base_m else None, True)}")
    print(f"Evidence Recall: {format_val('evidence_recall', m['evidence_recall'], base_m['evidence_recall'] if base_m else None, True)}")
    print(f"Supported Answer Rate: {format_val('supported_rate', m['supported_rate'], base_m['supported_rate'] if base_m else None, True)}")
    print(f"Insufficient Evidence Rate: {format_val('insufficient_rate', m['insufficient_rate'], base_m['insufficient_rate'] if base_m else None, True)}")
    print(f"Conflicted Rate: {format_val('conflicted_rate', m['conflicted_rate'], base_m['conflicted_rate'] if base_m else None, True)}")
    print(f"Avg Latency (s): {format_val('avg_latency', m['avg_latency'], base_m['avg_latency'] if base_m else None)}")
    print(f"Median Latency (s): {format_val('median_latency', m['median_latency'], base_m['median_latency'] if base_m else None)}")
    print(f"P95 Latency (s): {format_val('p95_latency', m['p95_latency'], base_m['p95_latency'] if base_m else None)}")
    print(f"Avg Evidence Count: {format_val('avg_evidence', m['avg_evidence'], base_m['avg_evidence'] if base_m else None)}")
    print(f"Avg Claim Count: {format_val('avg_claims', m['avg_claims'], base_m['avg_claims'] if base_m else None)}")
    print(f"Avg Verified Claims: {format_val('avg_verified', m['avg_verified'], base_m['avg_verified'] if base_m else None)}")
    print(f"Avg Selected Claims: {format_val('avg_selected', m['avg_selected'], base_m['avg_selected'] if base_m else None)}")
    print(f"Failures: {m['failures']}")
    print(f"JSON Parse Failures: {m['json_failures']}")
    print(f"Status Distribution: {m['status_distribution']}")

def main():
    path = "data/results/ablation_results_full.json"
    if not os.path.exists(path):
        print("No results file found.")
        return
        
    with open(path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    variants = defaultdict(list)
    categories = defaultdict(lambda: defaultdict(list))
    
    unique_pairs = set()
    for r in results:
        variants[r["variant"]].append(r)
        categories[r["question_type"]][r["variant"]].append(r)
        unique_pairs.add((r["variant"], r["question_id"]))
        
    print("==================================================")
    print("STEP 22C COMPLETE")
    print("=================")
    print(f"Runs expected: 224")
    print(f"Runs completed: {len(results)}")
    
    failed_runs = len([r for r in results if r["final_status"] == "FAILED"])
    print(f"Runs failed: {failed_runs}")
    print(f"Unique pairs: {len(unique_pairs)}")
    print(f"Duplicates: {len(results) - len(unique_pairs)}")
    print(f"Variants complete: {len(variants)}/8")
    for v, v_runs in variants.items():
        print(f"  {v}: {len(v_runs)} questions")
        
    is_valid = (len(results) == 224 and len(unique_pairs) == 224 and len(variants) == 8)
    print(f"Experiment valid: {'YES' if is_valid else 'NO'}")
    
    print("\\n==================================================")
    print("OVERALL METRICS (DELTAS RELATIVE TO FULL_AERIS)")
    
    full_metrics = calculate_metrics(variants.get("FULL_AERIS", []))
    print_metrics("FULL_AERIS", full_metrics)
    
    for variant, v_runs in variants.items():
        if variant == "FULL_AERIS":
            continue
        v_metrics = calculate_metrics(v_runs)
        print_metrics(variant, v_metrics, base_m=full_metrics)
        
    print("\\n==================================================")
    print("CATEGORY BREAKDOWN METRICS")
    
    for cat, cat_variants in categories.items():
        print(f"\\n[{cat}]")
        cat_full_metrics = calculate_metrics(cat_variants.get("FULL_AERIS", []))
        
        for variant, v_runs in cat_variants.items():
            if variant == "FULL_AERIS":
                print(f"  {variant}: hit={cat_full_metrics.get('evidence_hit_rate', 0):.1%} recall={cat_full_metrics.get('evidence_recall', 0):.1%} ans={cat_full_metrics.get('supported_rate', 0):.1%} lat={cat_full_metrics.get('avg_latency', 0):.1f}s")
            else:
                v_metrics = calculate_metrics(v_runs)
                lat_diff = v_metrics.get('avg_latency', 0) - cat_full_metrics.get('avg_latency', 0)
                rec_diff = v_metrics.get('evidence_recall', 0) - cat_full_metrics.get('evidence_recall', 0)
                ans_diff = v_metrics.get('supported_rate', 0) - cat_full_metrics.get('supported_rate', 0)
                
                print(f"  {variant}: hit={v_metrics.get('evidence_hit_rate', 0):.1%} recall={v_metrics.get('evidence_recall', 0):.1%} (diff {rec_diff*100:+.1f}%) ans={v_metrics.get('supported_rate', 0):.1%} (diff {ans_diff*100:+.1f}%) lat={v_metrics.get('avg_latency', 0):.1f}s (diff {lat_diff:+.1f}s)")

if __name__ == "__main__":
    main()
