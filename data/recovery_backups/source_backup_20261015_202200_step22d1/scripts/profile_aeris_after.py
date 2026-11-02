import json
import time
import os
from typing import List, Dict

from app.controller.schemas import ControllerRequest, ControllerConfig, StageStatus, ControllerStage
from scripts.run_ablation import build_real_controller
from app.benchmark.dataset import BenchmarkDataset
from app.controller.controller import AERISController

def main():
    print("==================================================")
    print("AERIS-RAG PERFORMANCE PROFILING (AFTER)")
    print("==================================================")
    
    questions = [
        "q_df_02",
        "q_mh_01",
        "q_meth_01",
        "q_contra_01",
        "q_unans_01"
    ]
    
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    records = [r for r in dataset.records if r.question_id in questions]
    
    if len(records) != 5:
        print(f"Warning: Found {len(records)} records instead of 5")
    
    controller = build_real_controller()
    
    # Monkeypatch to measure latency
    original_stage = AERISController._stage
    
    class Tracker:
        last_time = time.time()
        
    def instrumented_stage(stage, status, message, output_count=0, metadata=None):
        now = time.time()
        latency = now - Tracker.last_time
        Tracker.last_time = now
        
        result = original_stage(stage, status, message, output_count, metadata)
        result.latency_seconds = latency
        return result
        
    AERISController._stage = staticmethod(instrumented_stage)
    
    results = []
    
    parsing_failures = 0
    pipeline_exceptions = 0
    stage_failures = 0
    completed_questions = 0
    
    for record in records:
        print(f"\nProfiling: {record.question_id}")
        config = ControllerConfig()
        request = ControllerRequest(
            document_id=record.document_id,
            question=record.question,
            config=config
        )
        
        Tracker.last_time = time.time()
        start_time = time.time()
        result = controller.run(request)
        total_time = time.time() - start_time
        
        stages = []
        q_failed = False
        
        if result.status == StageStatus.FAILED:
            q_failed = True
            stage_failures += 1
            error_type = result.metadata.get("error_type", "")
            if "JSONParsingError" in error_type:
                parsing_failures += 1
            else:
                pipeline_exceptions += 1
        else:
            completed_questions += 1
            
        for stage in result.stages:
            status_val = stage.status.value
            stages.append({
                "stage": stage.stage.value,
                "status": status_val,
                "latency_seconds": getattr(stage, "latency_seconds", 0.0),
                "output_count": stage.output_count,
                "message": stage.message
            })
            print(f"  [{stage.stage.value}] Status: {status_val} | Latency: {getattr(stage, 'latency_seconds', 0.0):.2f}s | Msg: {stage.message}")
            
        results.append({
            "question_id": record.question_id,
            "total_latency": total_time,
            "stages": stages,
            "status": result.status.value,
            "error_type": result.metadata.get("error_type")
        })
        
    out_path = "data/results/aeris_profile_after.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
        
    # Validation checks
    profile_valid = (stage_failures == 0 and len(records) == 5)
    
    print("\n==================================================")
    print("PROFILING VALIDITY")
    print("==================================================")
    print(f"PROFILE VALID = {'YES' if profile_valid else 'NO'}")
    print(f"Questions completed: {completed_questions}/5")
    print(f"Questions with stage failures: {stage_failures}/5")
    print(f"JSON parsing failures: {parsing_failures}")
    print(f"Pipeline exceptions: {pipeline_exceptions}")
    
    # Read Before profile
    try:
        with open("data/results/aeris_profile_before.json", "r") as f:
            before_results = json.load(f)
    except FileNotFoundError:
        print("\nCould not find aeris_profile_before.json. Skipping comparison.")
        return
        
    print("\nStage | Historical Ref Avg (s) | Measured Avg (s) | Status Counts (C/F/S)")
    print("-" * 80)
    
    def get_stage_stats(res):
        totals = {}
        counts = {}
        status_counts = {}
        for r in res:
            for s in r["stages"]:
                name = s["stage"]
                if name not in totals:
                    totals[name] = 0.0
                    counts[name] = 0
                    status_counts[name] = {"COMPLETED": 0, "FAILED": 0, "SKIPPED": 0}
                totals[name] += s.get("latency_seconds", 0.0)
                counts[name] += 1
                
                status_val = s.get("status")
                if status_val in status_counts[name]:
                    status_counts[name][status_val] += 1
                    
        # A failed stage time might be captured as FAILED
        return {k: (totals[k] / counts[k], status_counts[k]) for k in totals.keys()}
        
    before_stats = get_stage_stats(before_results)
    after_stats = get_stage_stats(results)
    
    for name in sorted(before_stats.keys()):
        before_val, _ = before_stats[name]
        after_val, after_sc = after_stats.get(name, (0.0, {"COMPLETED": 0, "FAILED": 0, "SKIPPED": 0}))
        
        status_str = f"{after_sc['COMPLETED']}/{after_sc['FAILED']}/{after_sc['SKIPPED']}"
        print(f"{name:25} | {before_val:14.2f} | {after_val:13.2f} | {status_str:20}")
        
    # Also print any new stages in 'after' like FAILED
    for name in sorted(after_stats.keys()):
        if name not in before_stats:
            after_val, after_sc = after_stats[name]
            status_str = f"{after_sc['COMPLETED']}/{after_sc['FAILED']}/{after_sc['SKIPPED']}"
            print(f"{name:25} | {'N/A':14} | {after_val:13.2f} | {status_str:20}")
        
    print("\nTotal Pipeline Latency (Wall-clock Average):")
    before_total = sum(r.get("total_latency", 0.0) for r in before_results) / len(before_results) if before_results else 0.0
    after_total = sum(r.get("total_latency", 0.0) for r in results) / len(results) if results else 0.0
    
    print(f"{'TOTAL (Avg per query)':25} | {before_total:14.2f} | {after_total:13.2f}")
    
    if profile_valid:
        speedup_total = before_total / after_total if after_total > 0 else float('inf')
        print(f"\nMeasured Speedup vs Historical Baseline: {speedup_total:.1f}x")
    else:
        print("\nNote: Speedup not calculated due to invalid profile (failures occurred).")
    
    print("\nStep 22B Optimization Profiling Complete!")

if __name__ == "__main__":
    main()
