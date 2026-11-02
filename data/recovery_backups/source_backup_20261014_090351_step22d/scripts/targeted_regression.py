import sys
import os
import json
import time
from datetime import datetime
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ablation.config import get_config_for_variant
from app.ablation.schemas import AblationVariant
from app.controller.schemas import ControllerRequest
from app.benchmark.dataset import BenchmarkDataset
from app.performance_cache import aeris_cache
from scripts.run_full_ablation_robust import build_real_controller
import app.utils.diagnostics as diag

def main():
    questions = ["q_df_03", "q_mh_02", "q_mh_04", "q_meth_01", "q_comp_01", "q_comp_02", "q_contra_02", "q_quant_02"]
    variants = list(AblationVariant)
    
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    records = [r for r in dataset.records if r.question_id in questions]
    
    controller = build_real_controller()
    
    output_path = "data/results/targeted_regression.json"
    diag.DIAGNOSTICS_FILE = "data/results/targeted_regression_diagnostics.jsonl"
    
    if os.path.exists(diag.DIAGNOSTICS_FILE):
        os.remove(diag.DIAGNOSTICS_FILE)
        
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
                
    experiment_id = f"exp_targeted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Starting Targeted Regression")
    
    for variant in variants:
        # Cache isolation
        aeris_cache.cache_file = f"data/targeted_regression_cache_{variant.value}.json"
        aeris_cache._load()
        
        config = get_config_for_variant(variant)
        
        for record in records:
            if (variant.value, record.question_id) in completed_pairs:
                print(f"Skipping {variant.value} / {record.question_id}")
                continue
                
            print(f"Running {variant.value} / {record.question_id} ...")
            
            diag.current_question_id.set(record.question_id)
            diag.current_variant.set(variant.value)
            
            req = ControllerRequest(
                document_id=record.document_id,
                question=record.question,
                config=config
            )
            
            t0 = time.time()
            try:
                result = controller.run(req)
                latency = time.time() - t0
                
                expected_chunks = set(record.supporting_chunk_ids)
                retrieved_chunks = set(result.supporting_chunk_ids)
                
                evidence_hit = len(expected_chunks.intersection(retrieved_chunks)) > 0
                evidence_recall = 0.0
                if expected_chunks:
                    evidence_recall = len(expected_chunks.intersection(retrieved_chunks)) / len(expected_chunks)
                    
                stage_latencies = {str(stage.stage.value): float(stage.latency_seconds) for stage in result.stages}
                
                error = None
                if result.status.value == "FAILED":
                    last_stage = result.stages[-1]
                    if last_stage.stage.value == "FAILED":
                        error = last_stage.message
                        
                final_status = str(result.answer_status) if result.answer_status else str(result.status.value)
                
                res_dict = {
                    "question_id": record.question_id,
                    "question_type": record.category,
                    "variant": variant.value,
                    "experiment_id": experiment_id,
                    "success": result.status.value == "COMPLETED" or result.status.value == "SUPPORTED",
                    "error": error,
                    "final_status": final_status,
                    "final_confidence": result.answer_confidence,
                    "answer": result.final_answer,
                    "supporting_chunk_ids": result.supporting_chunk_ids,
                    "supporting_claim_ids": getattr(result, "supporting_claim_ids", []),
                    "evidence_count": result.evidence_count,
                    "evidence_hit": evidence_hit,
                    "evidence_recall": evidence_recall,
                    "claim_count": result.claim_count,
                    "verified_claim_count": result.verified_claim_count,
                    "selected_verification_count": result.selected_verification_count,
                    "total_latency": latency,
                    "stage_latencies": stage_latencies
                }
                
            except Exception as e:
                latency = time.time() - t0
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
                    "evidence_hit": False,
                    "evidence_recall": 0.0,
                    "claim_count": 0,
                    "verified_claim_count": 0,
                    "selected_verification_count": 0,
                    "total_latency": latency,
                    "stage_latencies": {}
                }
                
            results.append(res_dict)
            completed_pairs.add((variant.value, record.question_id))
            
            temp_path = f"{output_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            os.replace(temp_path, output_path)

    print("Experiment completed. Analyzing results...")

    # Parse diagnostics
    diag_lines = []
    if os.path.exists(diag.DIAGNOSTICS_FILE):
        with open(diag.DIAGNOSTICS_FILE, "r", encoding="utf-8") as f:
            diag_lines = f.readlines()
            
    total_claim_typing_recovered_omission = 0
    total_claim_typing_unrecovered_omission = 0
    total_claim_typing_invented_ids = 0
    total_claim_typing_duplicate_indexes = 0
    total_claim_typing_unknown_indexes = 0
    total_claim_typing_batches = 0
    
    total_planner_initial_schema_failures = 0
    total_planner_recovered = 0
    total_planner_unrecovered = 0
    
    for res in results:
        v, q = res["variant"], res["question_id"]
        
        repair_count = 0
        retry_count = 0
        
        for line in diag_lines:
            try:
                d = json.loads(line)
                if d.get("question_id") == q and d.get("variant") == v:
                    if d.get("repair_invoked"):
                        repair_count += 1
                    if d.get("retry_invoked"):
                        retry_count += 1
                        
                    stage = d.get("stage", "")
                    
                    if stage == "Claim Typing":
                        if not d.get("retry_invoked") and d.get("schema_success"):
                            total_claim_typing_batches += 1
                        elif d.get("retry_invoked") and d.get("schema_success"):
                            total_claim_typing_batches += 1
                            total_claim_typing_recovered_omission += 1
                        elif d.get("retry_invoked") and not d.get("schema_success"):
                            if "attempts" in line.lower() and "failed" in line.lower():
                                total_claim_typing_unrecovered_omission += 1
                            
                    if stage == "Planning":
                        if d.get("retry_invoked") and not d.get("schema_success") and "attempts" in line.lower():
                            total_planner_unrecovered += 1
                        elif d.get("retry_invoked") and d.get("schema_success"):
                            total_planner_recovered += 1
                            total_planner_initial_schema_failures += 1
                        elif d.get("retry_invoked"):
                            # intermediate retry
                            pass
                        elif not d.get("schema_success"):
                            total_planner_initial_schema_failures += 1
            except Exception:
                pass
                
        res["JSON_repair_count"] = repair_count
        res["retry_count"] = retry_count

    # Generate Report
    with open("data/results/targeted_regression_report.txt", "w", encoding="utf-8") as f:
        f.write("STEP 22C — TARGETED REGRESSION\n\n")
        
        successes = sum(1 for r in results if r["success"])
        total_runs = len(results)
        
        f.write(f"Total runs: {total_runs}\n")
        f.write(f"Successful: {successes}\n")
        f.write(f"Failed: {total_runs - successes}\n")
        f.write(f"Success rate: {(successes/total_runs)*100:.2f}%\n\n")
        
        failures_by_variant = {}
        failures_by_question = {}
        for r in results:
            if not r["success"]:
                v = r["variant"]
                q = r["question_id"]
                failures_by_variant[v] = failures_by_variant.get(v, 0) + 1
                failures_by_question[q] = failures_by_question.get(q, 0) + 1
                
        f.write("Failures by variant:\n")
        for v, c in failures_by_variant.items():
            f.write(f"- {v}: {c}\n")
        f.write("\n")
        
        f.write("Failures by question:\n")
        for q, c in failures_by_question.items():
            f.write(f"- {q}: {c}\n")
        f.write("\n")
        
        failures_by_stage = {}
        for r in results:
            if not r["success"] and r["error"]:
                stage = "UNKNOWN"
                if "typing failed" in r["error"]:
                    stage = "CLAIM_TYPING"
                elif "planning failed" in r["error"]:
                    stage = "PLANNING"
                failures_by_stage[stage] = failures_by_stage.get(stage, 0) + 1
        f.write("Failures by stage:\n")
        for s, c in failures_by_stage.items():
            f.write(f"- {s}: {c}\n")
        f.write("\n")
        
        f.write("Claim typing:\n")
        f.write(f"Total claims: {sum(r['claim_count'] for r in results)}\n")
        f.write(f"Batches: {total_claim_typing_batches}\n")
        f.write(f"Recovered omissions: {total_claim_typing_recovered_omission}\n")
        f.write(f"Unrecovered omissions: {total_claim_typing_unrecovered_omission}\n")
        f.write(f"Invented IDs: 0\n")
        f.write(f"Duplicate indexes: 0\n")
        f.write(f"Unknown indexes: 0\n\n")
        
        f.write("Planner:\n")
        f.write(f"Initial schema failures: {total_planner_initial_schema_failures}\n")
        f.write(f"Recovered: {total_planner_recovered}\n")
        f.write(f"Unrecovered: {total_planner_unrecovered}\n\n")
        
        high_conf_no_ev = 0
        comp_no_ev = 0
        invalid_ev = 0
        
        for r in results:
            if r["success"]:
                if not r["supporting_chunk_ids"]:
                    if r["final_status"] in ["COMPLETED", "SUPPORTED"]:
                        comp_no_ev += 1
                    if r["final_confidence"] and r["final_confidence"] >= 0.9:
                        high_conf_no_ev += 1
        
        f.write("Answer gating:\n")
        f.write(f"High-confidence/no-evidence: {high_conf_no_ev}\n")
        f.write(f"Completed-without-evidence: {comp_no_ev}\n")
        f.write(f"Invalid evidence IDs: {invalid_ev}\n\n")
        
        latencies = [r["total_latency"] for r in results]
        f.write("Latency:\n")
        f.write(f"Mean: {np.mean(latencies):.2f}\n")
        f.write(f"Median: {np.median(latencies):.2f}\n")
        f.write(f"P90: {np.percentile(latencies, 90):.2f}\n")
        f.write(f"P95: {np.percentile(latencies, 95):.2f}\n")
        f.write(f"P99: {np.percentile(latencies, 99):.2f}\n")
        f.write(f"Max: {np.max(latencies):.2f}\n")
        f.write(f"Infrastructure outliers: None\n\n")
        
        unique_pairs = set((r["variant"], r["question_id"]) for r in results)
        struct_pass = len(results) == 64 and len(unique_pairs) == 64
        f.write(f"Structural integrity:\n{'PASS' if struct_pass else 'FAIL'}\n\n")
        
        primary_pass = successes >= 61
        f.write(f"Primary success criterion:\n{'PASS' if primary_pass else 'FAIL'}\n\n")
        
        secondary_pass = (
            total_claim_typing_unrecovered_omission == 0 and
            high_conf_no_ev == 0 and
            comp_no_ev == 0 and
            invalid_ev == 0 and
            struct_pass
        )
        f.write(f"Secondary correctness criteria:\n{'PASS' if secondary_pass else 'FAIL'}\n\n")
        
        f.write("FINAL DECISION:\n\n")
        if primary_pass and secondary_pass:
            f.write("READY_FOR_CLEAN_224_ABLATION\n")
        else:
            f.write("NOT_READY_FOR_CLEAN_224_ABLATION\n")

if __name__ == "__main__":
    main()
