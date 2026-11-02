import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ablation.schemas import AblationVariant
from app.benchmark.dataset import BenchmarkDataset
from app.performance_cache import aeris_cache
from scripts.run_ablation import build_real_controller
from app.ablation.runner import AblationRunner
import app.utils.diagnostics as diag

def main():
    parser = argparse.ArgumentParser(description="Run AERIS-RAG Repaired 224-Run Scientific Ablation Evaluation")
    parser.add_argument("--experiment-id", type=str, default=None, help="Explicit experiment ID (default: generates fresh exp_repaired224_<timestamp>)")
    parser.add_argument("--resume", type=str, default=None, help="Path to existing result file to resume")
    args = parser.parse_args()

    print("=" * 70)
    print("AERIS-RAG — Repaired 224-Run Scientific Ablation Evaluation")
    print("=" * 70)
    
    benchmark_path = "data/benchmark/aeris_benchmark.json"
    dataset = BenchmarkDataset(benchmark_path)
    
    expected_variants = len(list(AblationVariant))
    expected_questions = len(dataset.records)
    expected_total_runs = expected_variants * expected_questions
    
    print(f"Benchmark questions: {expected_questions}")
    print(f"Variants: {expected_variants}")
    print(f"Total expected runs: {expected_total_runs}")
    
    if expected_total_runs != 224:
        raise ValueError(f"Expected exactly 224 runs, got {expected_total_runs}")

    # Compute SHA256 of the benchmark
    with open(benchmark_path, "rb") as bf:
        benchmark_sha256 = hashlib.sha256(bf.read()).hexdigest()
    print(f"Benchmark SHA256: {benchmark_sha256}")
        
    # Experiment ID: format exp_repaired224_YYYYMMDD_HHMMSS
    if args.resume and os.path.exists(args.resume):
        output_path = args.resume
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
            experiment_id = existing[0]["experiment_id"] if existing else args.experiment_id
            print(f"Resuming experiment: {experiment_id} ({len(existing)} pairs completed)")
        diag_path = output_path.replace(".json", "_diagnostics.jsonl")
        manifest_path = output_path.replace(".json", "_manifest.json")
    else:
        if args.experiment_id:
            experiment_id = args.experiment_id
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_id = f"exp_repaired224_{timestamp_str}"
            
        print(f"New Experiment ID: {experiment_id}")
        output_path = f"data/results/ablation_results_{experiment_id}.json"
        diag_path = f"data/results/ablation_results_{experiment_id}_diagnostics.jsonl"
        manifest_path = f"data/results/ablation_results_{experiment_id}_manifest.json"
    
    diag.DIAGNOSTICS_FILE = diag_path
    
    manifest = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now().isoformat(),
        "model_name": "llama3.2:latest",
        "benchmark_path": benchmark_path,
        "benchmark_sha256": benchmark_sha256,
        "benchmark_question_count": expected_questions,
        "variant_list": [v.value for v in AblationVariant],
        "expected_run_count": expected_total_runs,
        "experiment_configuration": {
            "temperature": 0.0,
            "total_variants": expected_variants,
            "total_questions": expected_questions,
            "provenance_guardrails": "enabled",
            "decoupled_metrics": "enabled"
        },
        "output_path": output_path,
        "diagnostics_path": diag_path
    }
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    controller = build_real_controller()
    runner = AblationRunner(controller)
    
    t_start_total = time.time()
    runner.run_experiment(
        benchmark_path=benchmark_path,
        output_path=output_path,
        experiment_id=experiment_id
    )
    t_total = time.time() - t_start_total
    print(f"\nAll runs finished in {t_total:.1f}s ({t_total/60:.1f} mins).")
    
    # Load and post-process diagnostics into the result records
    with open(output_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    diag_entries = []
    if os.path.exists(diag_path):
        with open(diag_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        diag_entries.append(json.loads(line))
                    except Exception:
                        pass
                        
    for r in results:
        q_id = r["question_id"]
        v_name = r["variant"]
        rep_count = 0
        ret_count = 0
        for d in diag_entries:
            if d.get("question_id") == q_id and d.get("variant") == v_name:
                if d.get("repair_invoked"):
                    rep_count += 1
                if d.get("retry_invoked"):
                    ret_count += 1
        r["repair_count"] = rep_count
        r["retry_count"] = ret_count

    # Save enriched results atomically
    temp_path = f"{output_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    os.replace(temp_path, output_path)
    print("Enriched results with repair/retry counts.")

    # Now generate the comprehensive audit reports
    from scripts.audit_final_224 import run_full_audits
    run_full_audits(output_path, benchmark_path, manifest_path, diag_path)

if __name__ == "__main__":
    main()
