
import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ablation.schemas import AblationVariant
from app.benchmark.dataset import BenchmarkDataset
from scripts.run_ablation import build_real_controller
from app.ablation.runner import AblationRunner
import app.utils.diagnostics as diag


def run_smoke_test():
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_id = f"exp_measurement_smoke_{timestamp_str}"
    
    print("=" * 70)
    print(f"AERIS-RAG — End-to-End Measurement Repair Smoke Test")
    print(f"Experiment ID: {experiment_id}")
    print("=" * 70)
    
    benchmark_path = "data/benchmark/aeris_benchmark.json"
    output_path = f"data/results/ablation_results_{experiment_id}.json"
    diag_path = f"data/results/ablation_results_{experiment_id}_diagnostics.jsonl"
    manifest_path = f"data/results/ablation_results_{experiment_id}_manifest.json"
    
    diag.DIAGNOSTICS_FILE = diag_path
    
    # 4 representative benchmark questions:
    # 1. Answerable Direct-Fact: q_df_01
    # 2. Answerable Multi-Hop: q_mh_03
    # 3. Unanswerable: q_unans_01 (exercises depth expansions & reformulations)
    # 4. Multi-Hop with multiple requirements: q_mh_01
    selected_qids = ["q_df_01", "q_mh_03", "q_unans_01", "q_mh_01"]
    selected_variants = [AblationVariant.FULL_AERIS]
    
    dataset = BenchmarkDataset(benchmark_path)
    selected_records = [r for r in dataset.records if r.question_id in selected_qids]
    
    print(f"Benchmark: {benchmark_path}")
    print(f"Selected questions ({len(selected_records)}):")
    for r in selected_records:
        print(f"  - {r.question_id}: {r.category} (Answerable: {r.answerability}, Gold: {r.supporting_chunk_ids})")
    print(f"Selected variants: {[v.value for v in selected_variants]}")
    print(f"Expected runs: {len(selected_records) * len(selected_variants)}")
    print(f"Output path: {output_path}")
    print(f"Manifest path: {manifest_path}")
    print(f"Diagnostics path: {diag_path}")
    
    controller = build_real_controller()
    runner = AblationRunner(controller)
    
    t0 = time.time()
    runner.run_experiment(
        benchmark_path=benchmark_path,
        output_path=output_path,
        experiment_id=experiment_id,
        variants_to_run=selected_variants,
        question_ids_to_run=selected_qids,
    )
    total_duration = time.time() - t0
    print(f"\nSmoke test execution completed in {total_duration:.2f}s ({total_duration/60:.2f} mins).")
    
    # Return output paths and experiment_id for validation
    return {
        "experiment_id": experiment_id,
        "total_duration": total_duration,
        "output_path": output_path,
        "manifest_path": manifest_path,
        "diag_path": diag_path,
        "benchmark_path": benchmark_path,
        "selected_qids": selected_qids
    }

if __name__ == "__main__":
    run_smoke_test()
