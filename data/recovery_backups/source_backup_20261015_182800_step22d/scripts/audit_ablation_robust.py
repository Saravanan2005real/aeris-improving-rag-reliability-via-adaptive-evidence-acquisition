import json
import os
import sys
import numpy as np
from collections import defaultdict

def main():
    results_path = "data/results/ablation_results_full_robust.json"
    diag_path = "data/results/generation_diagnostics_full_robust.jsonl"
    
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    print("### 1. Verify record integrity")
    print(f"Total records: {len(results)}")
    
    variants = set()
    questions = set()
    pairs = set()
    missing_fields = []
    
    for r in results:
        v = r.get("variant")
        q = r.get("question_id")
        variants.add(v)
        questions.add(q)
        pairs.add((v, q))
        
        if "experiment_id" not in r: missing_fields.append("experiment_id")
        if "timestamp" not in r: missing_fields.append("timestamp")
        if "latency_seconds" not in r: missing_fields.append("latency_seconds")
        if "final_status" not in r: missing_fields.append("final_status")
        if r.get("final_status") == "FAILED" and "error" not in r:
            missing_fields.append("error (on failed)")
            
    print(f"Total variants: {len(variants)} (Expected: 8)")
    print(f"Total questions: {len(questions)} (Expected: 28)")
    print(f"Unique pairs: {len(pairs)}")
    print(f"Missing pairs: {224 - len(pairs)}")
    print(f"Duplicate pairs: {len(results) - len(pairs)}")
    
    # Check experiment_id uniqueness to ensure no old records
    exp_ids = set(r.get("experiment_id") for r in results)
    print(f"Experiment IDs found: {exp_ids}")
    if missing_fields:
        print(f"Anomalies found! Missing fields: {set(missing_fields)}")
    else:
        print("No missing core fields found.")
        
    print("\n### 2. Analyze the 39 failures")
    failures = [r for r in results if r.get("final_status") == "FAILED"]
    print(f"Total failures: {len(failures)}")
    
    fail_by_var = defaultdict(int)
    fail_by_q = defaultdict(int)
    fail_by_stage = defaultdict(int)
    fail_by_err = defaultdict(int)
    
    for f in failures:
        fail_by_var[f.get("variant")] += 1
        fail_by_q[f.get("question_id")] += 1
        
        err = str(f.get("error", ""))
        
        if "Missing claim_id" in err:
            err_type = "Missing claim_id"
            stage = "CLAIM_TYPING"
        elif "validation error" in err or "ValidationError" in err:
            err_type = "ValidationError"
            stage = "PLANNING" if "RequirementPlan" in err else "UNKNOWN"
        elif "JSON" in err:
            err_type = "JSONParsingError"
            stage = "UNKNOWN"
        else:
            err_type = err.split(":")[0] if ":" in err else "Other"
            stage = "UNKNOWN"
            
        fail_by_stage[stage] += 1
        fail_by_err[err_type] += 1
        
    print("\nFAILURES BY VARIANT:")
    for k, v in fail_by_var.items(): print(f"{k}: {v}")
    
    print("\nFAILURES BY QUESTION:")
    for k, v in sorted(fail_by_q.items(), key=lambda x: x[1], reverse=True): print(f"{k}: {v}/8")
    
    print("\nFAILURES BY STAGE:")
    for k, v in fail_by_stage.items(): print(f"{k}: {v}")
    
    print("\nFAILURES BY ERROR TYPE:")
    for k, v in fail_by_err.items(): print(f"{k}: {v}")
    
    print("\n### 3. Determine whether failures are systematic")
    print("Questions failed in multiple variants:")
    for q, c in sorted(fail_by_q.items(), key=lambda x: x[1], reverse=True):
        if c > 1:
            vars_failed = [f.get("variant") for f in failures if f.get("question_id") == q]
            print(f"- {q}: {c}/8 failures in variants {vars_failed}")
            
    print("\nVariant Success Rates:")
    for v in variants:
        v_runs = [r for r in results if r.get("variant") == v]
        v_succ = [r for r in v_runs if r.get("final_status") != "FAILED"]
        print(f"{v}: {len(v_succ)}/{len(v_runs)} ({(len(v_succ)/len(v_runs))*100:.1f}%)")

    print("\n### 4. Audit JSON repair and retry behavior")
    diag_lines = []
    if os.path.exists(diag_path):
        with open(diag_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    diag_lines.append(json.loads(line))
                except:
                    pass
                    
    total_attempts = len(diag_lines)
    parse_fails = sum(1 for d in diag_lines if not d.get("parse_success"))
    repair_invokes = sum(1 for d in diag_lines if d.get("repair_invoked"))
    schema_fails = sum(1 for d in diag_lines if not d.get("schema_success"))
    retry_invokes = sum(1 for d in diag_lines if d.get("retry_invoked"))
    
    print(f"Total generation attempts: {total_attempts}")
    print(f"Total JSON parse failures: {parse_fails}")
    print(f"Total repair invocations: {repair_invokes}")
    print(f"Schema validation failures: {schema_fails}")
    print(f"Retry triggers: {retry_invokes}")
    
    # Analyze by component
    comp_fails = defaultdict(int)
    for d in diag_lines:
        if not d.get("schema_success") or not d.get("parse_success"):
            comp_fails[d.get("stage", "UNKNOWN")] += 1
    print(f"Malformed outputs by component: {dict(comp_fails)}")
    
    print("\n### 5. Audit SchemaError failures")
    print("Exact validation failures:")
    for f in failures:
        err = str(f.get("error", ""))
        if "Missing claim_id" in err:
            print(f"[{f.get('variant')} / {f.get('question_id')}] Missing claim_id: {err.strip().splitlines()[-1]}")
        elif "ValidationError" in err:
            print(f"[{f.get('variant')} / {f.get('question_id')}] ValidationError: missing required field / wrong type")
        else:
            print(f"[{f.get('variant')} / {f.get('question_id')}] Other Error: {err.strip().splitlines()[-1]}")
            
    print("\n### 6. Audit latency contamination")
    lats = [r.get("latency_seconds", 0) for r in results]
    outliers = [r for r in results if r.get("latency_seconds", 0) > 1000]
    for o in outliers:
        print(f"OUTLIER FOUND: {o.get('variant')} / {o.get('question_id')} -> {o.get('latency_seconds')}s")
        print(f"  Stage latencies: {o.get('stage_latencies')}")
        
    print(f"\nRaw Stats (All):")
    print(f"Mean: {np.mean(lats):.2f}, Median: {np.median(lats):.2f}, P95: {np.percentile(lats, 95):.2f}, Max: {np.max(lats):.2f}")
    
    lats_clean = [l for l in lats if l < 1000]
    print(f"\nClean Stats (No outliers):")
    print(f"Mean: {np.mean(lats_clean):.2f}, Median: {np.median(lats_clean):.2f}, P95: {np.percentile(lats_clean, 95):.2f}, Max: {np.max(lats_clean):.2f}")
    
    print("\n### 7. Audit stage latency instrumentation")
    stages = ["PLANNING", "RETRIEVAL", "COVERAGE", "CLAIM_GRAPH", "VERIFICATION", "CONTRADICTION", "CROSS_LINGUAL", "CALIBRATION", "SELECTIVE_VERIFICATION", "ANSWER_GENERATION"]
    
    for s in stages:
        ran_count = 0
        lat_gt_0 = 0
        lat_eq_0 = 0
        lat_sum = 0
        for r in results:
            sl = r.get("stage_latencies", {})
            if s in sl:
                ran_count += 1
                lat = float(sl[s])
                if lat > 0: lat_gt_0 += 1
                else: lat_eq_0 += 1
                lat_sum += lat
        avg = lat_sum / ran_count if ran_count > 0 else 0
        print(f"{s}: Ran={ran_count}, >0={lat_gt_0}, =0={lat_eq_0}, Avg={avg:.2f}s")
        
    print("\n### 8. Audit answer-status validity")
    status_counts = defaultdict(int)
    for r in results:
        # Check actual field final_status
        status_counts[r.get("final_status")] += 1
    print(f"final_status distribution: {dict(status_counts)}")
    
    # Check fields for successful runs
    for r in results:
        if r.get("final_status") != "FAILED":
            if "answer" not in r or "final_confidence" not in r or "supporting_chunk_ids" not in r or "supporting_claim_ids" not in r:
                print(f"Anomaly: Successful run missing fields! {r.get('variant')} / {r.get('question_id')}")
            
            # Identify suspicious success with empty chunks
            stat = r.get("final_status")
            if stat in ["SUPPORTED", "COMPLETED"] and not r.get("supporting_chunk_ids"):
                print(f"Anomaly: final_status is {stat} but supporting_chunk_ids is empty! {r.get('variant')} / {r.get('question_id')}")

    print("\n### 9. Audit benchmark/evidence consistency")
    for r in results:
        if r.get("final_status") != "FAILED":
            ans = r.get("expected_answerability")
            stat = r.get("final_status")
            conf = r.get("final_confidence", 0)
            hit = r.get("evidence_hit")
            
            if not ans and stat in ["SUPPORTED", "COMPLETED"]:
                print(f"Consistency Warning: Expected unanswerable but got {stat} ({r.get('variant')} / {r.get('question_id')})")
            if ans and stat == "INSUFFICIENT_EVIDENCE":
                pass
            if conf > 0.8 and not hit:
                print(f"Consistency Warning: High confidence ({conf}) but evidence_hit=False ({r.get('variant')} / {r.get('question_id')})")

    print("\n### 10. Critical output")
    
if __name__ == "__main__":
    import builtins
    with open("audit_output.txt", "w", encoding="utf-8") as f:
        def my_print(*args, **kwargs):
            kwargs["file"] = f
            builtins.print(*args, **kwargs)
        globals()["print"] = my_print
        main()
