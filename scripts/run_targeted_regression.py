import sys
import os
import json
import statistics

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_ablation import build_real_controller
from app.ablation.runner import AblationRunner

def evaluate_regression():
    results_path = "data/results/ablation_robustness_regression.json"
    diag_path = "data/results/generation_diagnostics.jsonl"
    
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    diags = []
    if os.path.exists(diag_path):
        with open(diag_path, "r", encoding="utf-8") as f:
            for line in f:
                diags.append(json.loads(line))
                
    total_runs = len(results)
    successful = [r for r in results if r.get("final_status") == "COMPLETED"]
    failed = [r for r in results if r.get("final_status") == "FAILED"]
    
    repair_count = sum(1 for d in diags if d.get("repair_invoked"))
    retry_count = sum(1 for d in diags if d.get("retry_invoked"))
    
    success_rate = (len(successful) / total_runs) * 100 if total_runs else 0
    
    latencies = [r.get("latency_seconds", 0) for r in successful]
    mean_lat = statistics.mean(latencies) if latencies else 0
    med_lat = statistics.median(latencies) if latencies else 0
    p95_lat = sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0
    
    md = []
    md.append("# Targeted Robustness Regression (Step 22C Fix)")
    md.append(f"- **Attempted Runs:** {total_runs}")
    md.append(f"- **Successful Runs:** {len(successful)}")
    md.append(f"- **Failed Runs:** {len(failed)}")
    md.append(f"- **Final Success Rate:** {success_rate:.1f}%")
    md.append(f"- **JSON Repair Count:** {repair_count}")
    md.append(f"- **Retry Count:** {retry_count}")
    md.append(f"- **Mean Latency:** {mean_lat:.2f}s")
    md.append(f"- **Median Latency:** {med_lat:.2f}s")
    md.append(f"- **P95 Latency:** {p95_lat:.2f}s\n")
    
    md.append("## Per-Question Success")
    q_counts = {}
    q_succ = {}
    for r in results:
        q = r["question_id"]
        q_counts[q] = q_counts.get(q, 0) + 1
        if r.get("final_status") == "COMPLETED":
            q_succ[q] = q_succ.get(q, 0) + 1
    for q in q_counts:
        md.append(f"- {q}: {q_succ.get(q,0)}/{q_counts[q]}")
        
    md.append("\n## Per-Variant Success")
    v_counts = {}
    v_succ = {}
    for r in results:
        v = r["variant"]
        v_counts[v] = v_counts.get(v, 0) + 1
        if r.get("final_status") == "COMPLETED":
            v_succ[v] = v_succ.get(v, 0) + 1
    for v in v_counts:
        md.append(f"- {v}: {v_succ.get(v,0)}/{v_counts[v]}")
        
    if failed:
        md.append("\n## Failures")
        for r in failed:
            md.append(f"- **{r['variant']} / {r['question_id']}**: {r.get('error')}")
            
    with open("data/results/ablation_robustness_regression.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
        
    print(f"\nRegression Success Rate: {success_rate:.1f}%")
    if success_rate >= 95.0:
        print("ACCEPTANCE CRITERION MET.")
    else:
        print("ACCEPTANCE CRITERION FAILED.")


def main():
    print("==================================================")
    print("AERIS-RAG TARGETED ROBUSTNESS REGRESSION")
    print("==================================================")
    
    target_questions = {
        "q_df_06",
        "q_mh_02",
        "q_mh_04",
        "q_meth_01",
        "q_comp_01",
        "q_comp_02",
        "q_contra_02",
        "q_quant_02"
    }
    
    output_path = "data/results/ablation_robustness_regression.json"
    diag_path = "data/results/generation_diagnostics.jsonl"
    
    if os.path.exists(output_path):
        os.remove(output_path)
    if os.path.exists(diag_path):
        os.remove(diag_path)
    
    import glob
    for cache_file in glob.glob("data/aeris_cache_*.json"):
        try:
            os.remove(cache_file)
        except:
            pass
            
    import app.benchmark.dataset as bdataset
    
    class FilteredBenchmarkDataset(bdataset.BenchmarkDataset):
        def __init__(self, path):
            super().__init__(path)
            self.records = [r for r in self.records if r.question_id in target_questions]
            
    bdataset.BenchmarkDataset = FilteredBenchmarkDataset
    
    controller = build_real_controller()
    runner = AblationRunner(controller)
    benchmark_path = "data/benchmark/aeris_benchmark.json"
    
    runner.run_experiment(benchmark_path, output_path)
    
    evaluate_regression()

if __name__ == "__main__":
    main()
