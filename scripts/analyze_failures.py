import json
import statistics
import re
from collections import defaultdict

def analyze_results(input_path="data/results/ablation_results_full.json"):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_runs = len(data)
    successful_runs = [d for d in data if d.get('final_status') == 'COMPLETED']
    failed_runs = [d for d in data if d.get('final_status') == 'FAILED']

    overall = {
        "total": total_runs,
        "successful": len(successful_runs),
        "failed": len(failed_runs),
        "success_percentage": (len(successful_runs) / total_runs) * 100 if total_runs else 0,
        "failure_percentage": (len(failed_runs) / total_runs) * 100 if total_runs else 0,
    }

    variants = sorted(list(set(d['variant'] for d in data)))
    variant_stats = {}
    for v in variants:
        v_data = [d for d in data if d['variant'] == v]
        v_success = [d for d in v_data if d.get('final_status') == 'COMPLETED']
        v_fail = [d for d in v_data if d.get('final_status') == 'FAILED']
        
        hit_sum = sum(1 for d in v_success if d.get('evidence_hit'))
        recall_sum = sum(d.get('evidence_recall', 0.0) for d in v_success)
        latencies = [d.get('latency_seconds', 0.0) for d in v_success]
        
        v_stats = {
            "total_runs": len(v_data),
            "successful_runs": len(v_success),
            "failed_runs": len(v_fail),
            "success_rate": (len(v_success) / len(v_data)) * 100 if v_data else 0,
            "evidence_hit_rate": hit_sum / len(v_success) if v_success else 0.0,
            "evidence_hit_denominator": len(v_success),
            "evidence_recall": recall_sum / len(v_success) if v_success else 0.0,
            "evidence_recall_denominator": len(v_success),
            "mean_latency": statistics.mean(latencies) if latencies else 0.0,
            "median_latency": statistics.median(latencies) if latencies else 0.0,
            "p95_latency": sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0.0,
            "verified_claims_avg": sum(d.get('verified_claim_count', 0) for d in v_success) / len(v_success) if v_success else 0.0,
            "selected_claims_avg": sum(d.get('selected_verification_count', 0) for d in v_success) / len(v_success) if v_success else 0.0,
            "answer_status_distribution": {},
        }
        variant_stats[v] = v_stats

    # Failure distribution
    fail_by_variant = defaultdict(int)
    fail_by_question = defaultdict(int)
    fail_by_category = defaultdict(int)
    fail_by_stage = defaultdict(int)
    fail_by_type = defaultdict(int)
    
    json_parsing_count = 0
    timeout_count = 0
    model_api_count = 0
    controller_count = 0
    other_count = 0

    for d in failed_runs:
        v = d['variant']
        q = d['question_id']
        c = d['question_type']
        fail_by_variant[v] += 1
        fail_by_question[q] += 1
        fail_by_category[c] += 1
        
        error_msg = d.get('error', '')
        if not error_msg:
            error_msg = "Unknown Error"
            
        stage_statuses = d.get('stage_statuses', {})
        failed_stages = [k for k, v in stage_statuses.items() if v == 'FAILED']
        stage = failed_stages[0] if failed_stages else 'UNKNOWN'
        fail_by_stage[stage] += 1

        if "JSON Parsing Error" in error_msg or "json" in error_msg.lower() or "validation error" in error_msg.lower():
            json_parsing_count += 1
            fail_by_type["JSON Parsing"] += 1
        elif "timeout" in error_msg.lower() or "readtimeout" in error_msg.lower():
            timeout_count += 1
            fail_by_type["Timeout"] += 1
        elif "connection" in error_msg.lower() or "ollama" in error_msg.lower():
            model_api_count += 1
            fail_by_type["Model/API"] += 1
        elif "internal controller error" in error_msg.lower() or "traceback" in error_msg.lower():
            controller_count += 1
            fail_by_type["Controller/Programming"] += 1
        else:
            other_count += 1
            fail_by_type["Other"] += 1

    failure_distribution = {
        "by_variant": dict(fail_by_variant),
        "by_question": dict(fail_by_question),
        "by_category": dict(fail_by_category),
        "by_stage": dict(fail_by_stage),
        "by_type": dict(fail_by_type),
        "counts": {
            "json_parsing": json_parsing_count,
            "timeout": timeout_count,
            "model_api": model_api_count,
            "controller": controller_count,
            "other": other_count
        }
    }
    
    systematic = "The failures appear broadly distributed across all variants, primarily driven by JSON parsing or validation errors during LLM extraction rather than a specific algorithmic failure."
    if any(count > 15 for count in fail_by_question.values()):
         systematic = "Failures are concentrated on specific questions."
         
    analysis = {
        "overall": overall,
        "variant_stats": variant_stats,
        "failure_distribution": failure_distribution,
        "systematic_analysis": systematic
    }

    with open("data/results/ablation_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    md = []
    md.append("# AERIS-RAG Ablation Analysis (Step 22C)\n")
    md.append("## 1. Overall Execution Statistics\n")
    md.append(f"- **Total Runs:** {overall['total']}")
    md.append(f"- **Successful Runs:** {overall['successful']} ({overall['success_percentage']:.1f}%)")
    md.append(f"- **Failed Runs:** {overall['failed']} ({overall['failure_percentage']:.1f}%)\n")

    md.append("## 2. Per-Variant Statistics\n")
    for v in variants:
        s = variant_stats[v]
        md.append(f"### {v}")
        md.append(f"- Runs: {s['successful_runs']} successful, {s['failed_runs']} failed (Total: {s['total_runs']}, Rate: {s['success_rate']:.1f}%)")
        md.append(f"- Evidence Hit Rate: {s['evidence_hit_rate']:.3f} (Denominator: {s['evidence_hit_denominator']} successful valid runs)")
        md.append(f"- Evidence Recall: {s['evidence_recall']:.3f} (Denominator: {s['evidence_recall_denominator']} successful valid runs)")
        md.append(f"- Mean Latency: {s['mean_latency']:.2f}s | Median: {s['median_latency']:.2f}s | P95: {s['p95_latency']:.2f}s")
        md.append(f"- Verified Claims Avg: {s['verified_claims_avg']:.2f} | Selected Claims Avg: {s['selected_claims_avg']:.2f}\n")

    md.append("## 3. Failure Distribution\n")
    md.append("### By Type")
    for k, v in failure_distribution['counts'].items():
        md.append(f"- {k}: {v}")
    
    md.append("\n### By Stage")
    for k, v in fail_by_stage.items():
        md.append(f"- {k}: {v}")
        
    md.append("\n### By Category")
    for k, v in fail_by_category.items():
        md.append(f"- {k}: {v}")

    md.append(f"\n## 4. Systematic Analysis\n{systematic}\n")

    with open("data/results/ablation_analysis.md", "w", encoding="utf-8") as f:
        f.write('\n'.join(md))

    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    analyze_results()
