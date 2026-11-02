import os
import sys
import json
import time
import numpy as np
from collections import defaultdict
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ablation.schemas import AblationVariant, AblationResult
from app.ablation.config import get_config_for_variant
from app.controller.schemas import ControllerRequest
from app.benchmark.dataset import BenchmarkDataset
from app.performance_cache import aeris_cache
from scripts.run_ablation import build_real_controller

def run_regression():
    questions_to_run = [
        "q_df_06", "q_mh_02", "q_mh_04", "q_meth_01",
        "q_comp_01", "q_comp_02", "q_contra_02", "q_quant_02"
    ]
    
    # Isolate cache
    aeris_cache.cache_file = "data/aeris_cache_robustness_test.json"
    aeris_cache._load()
    
    # Diagnostics file
    diag_file = "data/results/generation_diagnostics_robustness.jsonl"
    import app.utils.diagnostics as diag
    diag.DIAGNOSTICS_FILE = diag_file
    if os.path.exists(diag_file):
        os.remove(diag_file)
        
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    records = [r for r in dataset.records if r.question_id in questions_to_run]
    
    controller = build_real_controller()
    
    results = []
    success_count = 0
    fail_count = 0
    failures_by_stage = defaultdict(int)
    failures_by_error = defaultdict(int)
    
    for variant in AblationVariant:
        config = get_config_for_variant(variant)
        
        for record in records:
            # Set contextvars
            diag.current_question_id.set(record.question_id)
            diag.current_variant.set(variant.value)
            
            print(f"Running {record.question_id} - {variant.value}")
            try:
                req = ControllerRequest(
                    document_id=record.document_id,
                    question=record.question,
                    config=config
                )
                start = time.time()
                res = controller.run(req)
                lat = time.time() - start
                
                if res.status.value == "ERROR":
                    raise Exception(res.error)
                    
                results.append({"question_id": record.question_id, "variant": variant.value, "success": True})
                success_count += 1
            except Exception as e:
                import traceback
                traceback.print_exc()
                
                stage = "Unknown"
                error_type = type(e).__name__
                if "JSONParsingError" in error_type:
                    stage = "Parsing"
                elif "ValidationError" in error_type or "ValueError" in error_type:
                    stage = "Schema"
                    
                failures_by_stage[stage] += 1
                failures_by_error[error_type] += 1
                results.append({"question_id": record.question_id, "variant": variant.value, "success": False, "error": str(e)})
                fail_count += 1
                
    repair_count = 0
    retry_count = 0
    latencies = []
    per_q_success = defaultdict(int)
    per_v_success = defaultdict(int)
    
    for r in results:
        if r["success"]:
            per_q_success[r["question_id"]] += 1
            per_v_success[r["variant"]] += 1
            
    if os.path.exists(diag_file):
        with open(diag_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                if data.get("repair_invoked"):
                    repair_count += 1
                if data.get("retry_invoked"):
                    retry_count += 1
                latencies.append(data.get("latency", 0.0))
                
    mean_lat = np.mean(latencies) if latencies else 0.0
    med_lat = np.median(latencies) if latencies else 0.0
    p95_lat = np.percentile(latencies, 95) if latencies else 0.0
    
    total_runs = len(questions_to_run) * len(AblationVariant)
    success_rate = success_count / total_runs * 100
    
    report_json = {
        "total_runs": total_runs,
        "successful_runs": success_count,
        "failed_runs": fail_count,
        "final_success_rate": success_rate,
        "failures_by_stage": dict(failures_by_stage),
        "failures_by_error": dict(failures_by_error),
        "json_repair_count": repair_count,
        "retry_count": retry_count,
        "mean_latency": mean_lat,
        "median_latency": med_lat,
        "p95_latency": p95_lat,
        "per_question_success_count": dict(per_q_success),
        "per_variant_success_count": dict(per_v_success)
    }
    
    os.makedirs("data/results", exist_ok=True)
    with open("data/results/ablation_robustness_regression.json", "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
        
    md = f"""# Ablation Robustness Regression Report

- *(Total Runs**: {total_runs}
- **Successful**: {success_count}
- **Failed**: {fail_count}
- **Success Rate**: {success_rate:.2f}%

		## Latency
- Mean: {mean_lat:.2f}s
- Median: {med_lat:.2f}s
- P95: {p95_lat:.2f}s

## Recovery Mechanisms
- JSON Repairs Invoked: {repair_count}
- Retries Invoked: {retry_count}

## Failures
### By Stage
"""
    
    for s, c in failures_by_stage.items():
        md += f"- {s}: {c}\n"
        
    md += "\n### By Error Type\n"
    for e, c in failures_by_error.items():
        md += f"- {e}: {c}\n"
        
    md += "\n## Success Counts\n### By Question\n"
    for q, c in sorted(per_q_success.items()):
        md += f"- {q}: {c}/8\n"
        
    md += "\n### By Variant\n"
    for v, c in sorted(per_v_success.items()):
        md += f"- {v}: {c}/8\n"
        
    with open("data/results/ablation_robustness_regression.md", "w", encoding="utf-8") as f:
        f.write(md)
        
    print("\n" + md)
    
if __name__ == "__main__":
    run_regression()
