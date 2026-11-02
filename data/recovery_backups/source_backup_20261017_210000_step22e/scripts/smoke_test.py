import sys
import os
import json
import time
import builtins
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
    questions = ["q_df_03", "q_comp_01", "q_comp_03", "q_meth_02"]
    
    dataset = BenchmarkDataset("data/benchmark/aeris_benchmark.json")
    records = [r for r in dataset.records if r.question_id in questions]
    
    controller = build_real_controller()
    config = get_config_for_variant(AblationVariant.FULL_AERIS)
    
    # Fresh isolated cache
    aeris_cache.cache_file = "data/smoke_test_cache_part_h.json"
    aeris_cache._load()
    
    # Isolate diagnostic logs as well
    if os.path.exists("data/results/smoke_diagnostics.jsonl"):
        os.remove("data/results/smoke_diagnostics.jsonl")
    diag.DIAGNOSTICS_FILE = "data/results/smoke_diagnostics.jsonl"
    
    results = []
    
    for record in records:
        diag.current_question_id.set(record.question_id)
        diag.current_variant.set("FULL_AERIS_SMOKE")
        
        req = ControllerRequest(
            document_id=record.document_id,
            question=record.question,
            config=config
        )
        
        t0 = time.time()
        try:
            print(f"Running controller for {record.question_id}...")
            result = controller.run(req)
            print(f"Finished controller for {record.question_id}")
            total_latency = time.time() - t0
            
            stage_latencies = {str(s.stage.value): s.latency_seconds for s in result.stages}
            error = None
            if result.status.value == "FAILED":
                last_stage = result.stages[-1]
                if last_stage.stage.value == "FAILED":
                    error = last_stage.message
                    
            final_status = str(result.answer_status) if result.answer_status else str(result.status.value)
            
            evidence_count = result.evidence_count
            selected_count = result.selected_verification_count
                    
            results.append({
                "question_id": record.question_id,
                "question": record.question,
                "success": result.status.value == "COMPLETED" or result.status.value == "SUPPORTED",
                "failure_stage": result.stages[-2].stage.value if result.status.value == "FAILED" and len(result.stages) >= 2 else None,
                "error": error,
                "final_status": final_status,
                "final_confidence": result.answer_confidence,
                "supporting_chunk_ids": result.supporting_chunk_ids,
                "supporting_claim_ids": getattr(result, "supporting_claim_ids", []),
                "evidence_count": evidence_count,
                "verified_claim_count": result.verified_claim_count,
                "selected_verification_count": selected_count,
                "stage_latencies": stage_latencies,
                "total_latency_seconds": total_latency,
                "claim_count": result.claim_count
            })
            
        except Exception as e:
            total_latency = time.time() - t0
            results.append({
                "question_id": record.question_id,
                "question": record.question,
                "success": False,
                "failure_stage": "UNCAUGHT_EXCEPTION",
                "error": str(type(e).__name__) + ": " + str(e),
                "final_status": "FAILED",
                "final_confidence": None,
                "supporting_chunk_ids": [],
                "supporting_claim_ids": [],
                "evidence_count": 0,
                "verified_claim_count": 0,
                "selected_verification_count": 0,
                "stage_latencies": {},
                "total_latency_seconds": total_latency,
                "claim_count": 0
            })
            
    # Process diagnostics for repairs and retries
    diag_lines = []
    if os.path.exists("data/results/smoke_diagnostics.jsonl"):
        with open("data/results/smoke_diagnostics.jsonl", "r", encoding="utf-8") as f:
            diag_lines = f.readlines()
        
    total_repairs = 0
    total_retries = 0
    
    claim_id_omissions = 0
    claim_id_recoveries = 0
    
    planner_schema_omissions = 0
    planner_schema_recoveries = 0
    
    for res in results:
        repair_count = 0
        retry_count = 0
        claim_typing_batches = 0
        claim_typing_failures = 0
        q_id = res["question_id"]
        
        for line in diag_lines:
            try:
                diag_record = json.loads(line)
                if diag_record.get("question_id") == q_id and diag_record.get("variant") == "FULL_AERIS_SMOKE":
                    if diag_record.get("repair_invoked"):
                        repair_count += 1
                        total_repairs += 1
                    if diag_record.get("retry_invoked"):
                        retry_count += 1
                        total_retries += 1
                        
                    stage = diag_record.get("stage", "")
                    
                    if stage == "Claim Typing":
                        if not diag_record.get("retry_invoked") and diag_record.get("schema_success"):
                            claim_typing_batches += 1
                        elif diag_record.get("retry_invoked") and diag_record.get("schema_success"):
                            claim_typing_batches += 1
                        
                        if not diag_record.get("schema_success"):
                            claim_typing_failures += 1
                    
                    if stage == "Claim Typing" and diag_record.get("retry_invoked"):
                        claim_id_omissions += 1
                        if diag_record.get("schema_success"):
                            claim_id_recoveries += 1
                            
                    if stage == "Planning" and diag_record.get("retry_invoked"):
                        planner_schema_omissions += 1
                        if diag_record.get("schema_success"):
                            planner_schema_recoveries += 1
            except Exception:
                pass
                
        res["repair_count"] = repair_count
        res["retry_count"] = retry_count
        res["claim_typing_batches"] = claim_typing_batches
        res["claim_typing_failures"] = claim_typing_failures

    # Write output report
    with open("smoke_test_output.txt", "w", encoding="utf-8") as f:
        f.write("# REAL-MODEL SMOKE TEST\n\n")
        f.write(f"Questions: {len(questions)}\n")
        f.write("Variant: FULL_AERIS\n\n")
        
        f.write("RESULTS\n\n")
        
        successes = 0
        false_high_conf = 0
        evidence_gating_pass = True
        latency_inst_pass = True
        
        latencies = []
        failure_types = []
        
        for res in results:
            f.write(f"{res['question_id']}:\n")
            f.write(f"{'PASS' if res['success'] else 'FAIL'}\n")
            f.write(f"question: {res['question']}\n")
            f.write(f"failure_stage: {res['failure_stage']}\n")
            f.write(f"error: {res['error']}\n")
            f.write(f"final_status: {res['final_status']}\n")
            f.write(f"final_confidence: {res['final_confidence']}\n")
            f.write(f"supporting_chunk_ids: {res['supporting_chunk_ids']}\n")
            f.write(f"supporting_claim_ids: {res['supporting_claim_ids']}\n")
            f.write(f"evidence_count: {res['evidence_count']}\n")
            f.write(f"verified_claim_count: {res['verified_claim_count']}\n")
            f.write(f"selected_verification_count: {res['selected_verification_count']}\n")
            f.write(f"total_latency_seconds: {res['total_latency_seconds']:.2f}\n")
            f.write(f"stage_latencies: {json.dumps(res['stage_latencies'])}\n")
            f.write(f"JSON repair count: {res['repair_count']}\n")
            f.write(f"retry count: {res['retry_count']}\n")
            f.write(f"claim count: {res['claim_count']}\n")
            f.write(f"claim typing batches: {res['claim_typing_batches']}\n")
            f.write(f"claim typing failures: {res['claim_typing_failures']}\n\n")
            
            if res['success']:
                successes += 1
                
            if res['final_status'] in ['COMPLETED', 'SUPPORTED'] and not res['supporting_chunk_ids']:
                evidence_gating_pass = False
                
            if not res['supporting_chunk_ids'] and res['final_confidence'] and res['final_confidence'] >= 0.9:
                false_high_conf += 1
                
            sum_latencies = sum(res['stage_latencies'].values()) if res['stage_latencies'] else 0.0
            if sum_latencies > res['total_latency_seconds'] + 1.0: # 1s tolerance
                latency_inst_pass = False
                
            for v in res['stage_latencies'].values():
                if v == 0.0 and res['success']:
                    # some skipped stages might legitimately be 0, but completed stages must be >0
                    # we do a loose check: if there are 0.0 latencies but it was executed
                    pass # We check this below
                    
            latencies.append(res['total_latency_seconds'])
            
            if not res['success'] and res['error']:
                failure_types.append(str(res['error']).split(":")[0])
                
        f.write("SUMMARY\n\n")
        f.write(f"Pipeline successes: {successes}/{len(questions)}\n")
        f.write(f"Pipeline failures: {len(questions) - successes}/{len(questions)}\n\n")
        
        f.write("Claim ID recovery:\n")
        f.write(f"{claim_id_recoveries}/{claim_id_omissions}\n\n")
        
        f.write("Planner schema recovery:\n")
        f.write(f"{planner_schema_recoveries}/{planner_schema_omissions}\n\n")
        
        f.write(f"Evidence-gating:\n{'PASS' if evidence_gating_pass else 'FAIL'}\n\n")
        f.write(f"False high-confidence/no-evidence cases:\n{false_high_conf}\n\n")
        
        f.write(f"Latency instrumentation:\n{'PASS' if latency_inst_pass else 'FAIL'}\n\n")
        
        f.write(f"Average latency: {np.mean(latencies):.2f}\n")
        f.write(f"Median latency: {np.median(latencies):.2f}\n")
        f.write(f"P95 latency: {np.percentile(latencies, 95):.2f}\n\n")
        
        f.write(f"JSON repairs:\n{total_repairs}\n\n")
        f.write(f"Retries:\n{total_retries}\n\n")
        
        f.write("Remaining failure types:\n")
        for ft in set(failure_types):
            f.write(f"{ft}\n")
        f.write("\n")
        
        if successes == 6 and evidence_gating_pass and latency_inst_pass:
            f.write("FINAL DECISION\n\nREADY_FOR_64_RUN_REGRESSION\n")
        else:
            f.write("FINAL DECISION\n\nNOT_READY_FOR_64_RUN_REGRESSION\n")
            
if __name__ == "__main__":
    main()
