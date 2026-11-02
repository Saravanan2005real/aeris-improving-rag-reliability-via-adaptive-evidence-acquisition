import json
import time
from typing import List, Dict

from app.controller.schemas import ControllerRequest, ControllerConfig
from scripts.run_ablation import build_real_controller
from app.benchmark.dataset import BenchmarkDataset

def main():
    print("==================================================")
    print("AERIS-RAG PERFORMANCE PROFILING (BEFORE)")
    print("==================================================")
    
    questions = [
        "q_df_02",
        "q_mh_01",
        "q_method_01",
        "q_contradiction_01",
        "q_unanswerable_01"
    ]
    
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    records = [r for r in dataset.records if r.question_id in questions]
    
    if len(records) != 5:
        print(f"Warning: Found {len(records)} records instead of 5")
    
    controller = build_real_controller()
    
    from app.controller.controller import AERISController
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
    
    for record in records:
        print(f"Profiling: {record.question_id}")
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
        
        # We need to un-accumulate the last "COMPLETED" or "FAILED" stage which 
        # is just the final wrap-up, and instead give its time to the previous stage.
        # But this basic tracking gives latency of each block accurately enough.
        
        stages = []
        for stage in result.stages:
            stages.append({
                "stage": stage.stage.value,
                "status": stage.status.value,
                "latency_seconds": getattr(stage, "latency_seconds", 0.0), # Fallback if not populated
                "output_count": stage.output_count
            })
            
        results.append({
            "question_id": record.question_id,
            "total_latency": total_time,
            "stages": stages
        })
        
    out_path = "data/results/aeris_profile_before.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nStage | Avg latency | Total calls")
    print("-" * 50)
    
    # Calculate averages
    stage_totals = {}
    stage_counts = {}
    
    for r in results:
        for s in r["stages"]:
            name = s["stage"]
            stage_totals[name] = stage_totals.get(name, 0.0) + s["latency_seconds"]
            stage_counts[name] = stage_counts.get(name, 0) + 1
            
    for name in stage_totals.keys():
        avg = stage_totals[name] / stage_counts[name]
        print(f"{name:25} | {avg:11.2f} | {stage_counts[name]}")

if __name__ == "__main__":
    main()
