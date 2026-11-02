import json

with open("data/results/ablation_results_final224.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

fa = [r for r in raw if r["variant"] == "FULL_AERIS"]
stage_names = [
    "PLANNING", "RETRIEVAL", "COVERAGE", "CLAIM_GRAPH",
    "VERIFICATION", "CONTRADICTION", "CROSS_LINGUAL",
    "CALIBRATION", "SELECTIVE_VERIFICATION", "ANSWER_GENERATION"
]

print("=== Discrepancy by question in FULL_AERIS ===")
for r in fa:
    e2e = r.get("latency_seconds", 0.0)
    st_lats = r.get("stage_latencies", {})
    sum_st = sum(st_lats.get(st, 0.0) for st in stage_names)
    diff = e2e - sum_st
    if abs(diff) > 0.01:
        print(f"Q: {r['question_id']}, status: {r.get('final_status')}, E2E: {e2e:.4f}s, sum_stages: {sum_st:.4f}s, diff: {diff:.4f}s")

fa_succ = [r for r in fa if r.get("final_status") != "FAILED"]
n27 = len(fa_succ)
mean_e2e_27 = sum(r["latency_seconds"] for r in fa_succ) / n27
stage_means_27 = {st: sum(r["stage_latencies"].get(st, 0.0) for r in fa_succ) / n27 for st in stage_names}
sum_stages_27 = sum(stage_means_27.values())
print(f"\n27 Successful runs only:")
print(f"  Mean E2E: {mean_e2e_27:.4f}s")
print(f"  Sum of stage means: {sum_stages_27:.4f}s")
print(f"  Discrepancy on 27 runs: {mean_e2e_27 - sum_stages_27:.6f}s")

n28 = len(fa)
mean_e2e_28 = sum(r["latency_seconds"] for r in fa) / n28
stage_means_28 = {st: sum(r["stage_latencies"].get(st, 0.0) for r in fa) / n28 for st in stage_names}
sum_stages_28 = sum(stage_means_28.values())
failed_time_unaccounted = 158.2165 - 9.1574
print(f"\nAll 28 runs:")
print(f"  Mean E2E: {mean_e2e_28:.4f}s")
print(f"  Sum of stage means: {sum_stages_28:.4f}s")
print(f"  Total discrepancy: {mean_e2e_28 - sum_stages_28:.4f}s")
print(f"  Unaccounted failed-run time: {failed_time_unaccounted:.4f}s")
print(f"  Unaccounted failed-run time divided by 28: {failed_time_unaccounted / 28:.4f}s")
print(f"  Mathematical reconciliation residual: {(mean_e2e_28 - sum_stages_28) - (failed_time_unaccounted / 28):.6f}s")
