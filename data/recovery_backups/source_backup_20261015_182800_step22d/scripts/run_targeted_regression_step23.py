import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ablation.config import get_config_for_variant
from app.ablation.schemas import AblationVariant
from app.controller.schemas import ControllerRequest
from app.benchmark.dataset import BenchmarkDataset
from app.performance_cache import aeris_cache
from scripts.run_full_ablation_robust import build_real_controller

def main():
    variants = list(AblationVariant)
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    
    targeted_qids = [
        "q_unans_01", "q_unans_02", "q_unans_03", "q_unans_04",
        "q_comp_02", "q_comp_03", "q_mh_01", "q_meth_01", 
        "q_quant_01", "q_contra_01", "q_multi_01"
    ]
    
    records = [r for r in dataset.records if r.question_id in targeted_qids]
    
    controller = build_real_controller()
    output_path = "data/results/targeted_regression_final_fix.json"
    
    results = []
    completed_pairs = set()
    
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                results = json.load(f)
                for res in results:
                    completed_pairs.add((res["variant"], res["question_id"]))
            except json.JSONDecodeError:
                pass
                
    experiment_id = "exp_targeted_20261006_234631"
    
    print(f"Starting Targeted Regression for Step 23")
    print(f"Experiment ID: {experiment_id}")
    
    for variant in variants:
        aeris_cache.cache_file = f"data/cache_{experiment_id}_{variant.value}.json"
        aeris_cache._load()
        
        config = get_config_for_variant(variant)
        
        for record in records:
            if (variant.value, record.question_id) in completed_pairs:
                continue
                
            print(f"Running {variant.value} / {record.question_id} ...")
            
            req = ControllerRequest(
                document_id=record.document_id,
                question=record.question,
                config=config
            )
            
            t0 = time.perf_counter()
            try:
                result = controller.run(req)
                latency = time.perf_counter() - t0
                
                final_status = str(result.answer_status) if result.answer_status else str(result.status.value)
                
                # We expect the fix in answer_generator to handle INSUFFICIENT_EVIDENCE when chunks or claims are missing,
                # but if the model hallucinated unsupported chunks we might also enforce it here just in case.
                # Since we already updated answer_generator to enforce it, we don't need redundant logic, 
                # but we will just pass whatever is returned.
                
                res_dict = {
                    "question_id": record.question_id,
                    "question_type": record.category,
                    "variant": variant.value,
                    "experiment_id": experiment_id,
                    "success": result.status.value == "COMPLETED" or result.status.value == "SUPPORTED",
                    "error": None,
                    "final_status": final_status,
                    "final_confidence": result.answer_confidence,
                    "answer": result.final_answer,
                    "supporting_chunk_ids": result.supporting_chunk_ids,
                    "supporting_claim_ids": getattr(result, "supporting_claim_ids", []),
                    "evidence_count": result.evidence_count,
                    "claim_count": result.claim_count,
                    "verified_claim_count": result.verified_claim_count,
                    "selected_verification_count": result.selected_verification_count,
                    "metadata": result.metadata,
                    "total_latency": latency
                }
                
            except Exception as e:
                latency = time.perf_counter() - t0
                res_dict = {
                    "question_id": record.question_id,
                    "question_type": record.category,
                    "variant": variant.value,
                    "experiment_id": experiment_id,
                    "success": False,
                    "error": str(type(e).__name__) + ": " + str(e),
                    "final_status": "FAILED",
                    "final_confidence": None,
                    "answer": None,
                    "supporting_chunk_ids": [],
                    "supporting_claim_ids": [],
                    "evidence_count": 0,
                    "claim_count": 0,
                    "verified_claim_count": 0,
                    "selected_verification_count": 0,
                    "metadata": {},
                    "total_latency": latency
                }
                
            results.append(res_dict)
            completed_pairs.add((variant.value, record.question_id))
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

    print("Targeted regression completed.")
    
if __name__ == "__main__":
    main()
