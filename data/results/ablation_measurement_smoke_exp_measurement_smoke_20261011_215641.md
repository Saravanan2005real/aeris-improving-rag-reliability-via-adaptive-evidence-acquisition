# AERIS-RAG — End-to-End Measurement Repair Smoke Test Report

**Experiment ID:** `exp_measurement_smoke_20261011_215641`  
**Date:** 2026-10-11 22:10:30  
**Final Verdict:** `PASS — READY FOR FULL RERUN`

## 1. Summary of Smoke Test Runs

| Question ID | Category | Ground Truth Answerable | Final Status | Success | Retrieved Chunks | Cited Chunks | Retriever Hit / Rec | Citation Hit / Rec | Verdict |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `q_df_01` | DIRECT_FACT | True | `INSUFFICIENT_EVIDENCE` | True | 3 | 1 | 0 / 0.00 | 0 / 0.00 | **PASS** |
| `q_mh_01` | MULTI_HOP | True | `INSUFFICIENT_EVIDENCE` | True | 5 | 0 | 1 / 0.50 | 0 / 0.00 | **PASS** |
| `q_mh_03` | MULTI_HOP | True | `INSUFFICIENT_EVIDENCE` | True | 5 | 1 | 1 / 0.50 | 1 / 0.50 | **PASS** |
| `q_unans_01` | UNANSWERABLE | False | `INSUFFICIENT_EVIDENCE` | True | 3 | 1 | 0 / 0.00 | 0 / 0.00 | **PASS** |

## 2. Independent vs. Runner Metric Verification

| Question ID | Runner Retriever Hit/Rec | Independent Retriever Hit/Rec | Runner Citation Hit/Rec | Independent Citation Hit/Rec | Exact Match? |
|---|:---:|:---:|:---:|:---:|:---:|
| `q_df_01` | 0 / 0.0000 | 0 / 0.0000 | 0 / 0.0000 | 0 / 0.0000 | PASS |
| `q_mh_01` | 1 / 0.5000 | 1 / 0.5000 | 0 / 0.0000 | 0 / 0.0000 | PASS |
| `q_mh_03` | 1 / 0.5000 | 1 / 0.5000 | 1 / 0.5000 | 1 / 0.5000 | PASS |
| `q_unans_01` | 0 / 0.0000 | 0 / 0.0000 | 0 / 0.0000 | 0 / 0.0000 | PASS |

## 3. Provenance Guardrail Verification

- **Per-record check:** In every completed smoke-test run, all cited chunks strictly belonged to the retrieved evidence pool (`supporting_chunk_ids.issubset(retrieved_chunk_ids)`). Zero provenance violations occurred in valid runs.
- **Isolated Defect Test Fixture:** Simulated citation outside allowed pool (`hallucinated_chunk_z`) was deterministically flagged as a defect: **True**.

## 4. Telemetry and Query Reformulation Verification

- **`q_df_01`:** Attempts=1, Adaptive Depth Expansions=0, Reformulation Triggered=False, Verifications=2.
- **`q_mh_01`:** Attempts=3, Adaptive Depth Expansions=0, Reformulation Triggered=False, Verifications=2.
- **`q_mh_03`:** Attempts=2, Adaptive Depth Expansions=0, Reformulation Triggered=False, Verifications=3.
- **`q_unans_01`:** Attempts=12, Adaptive Depth Expansions=4, Reformulation Triggered=True, Verifications=2.

## 5. Artifact Paths Generated

- Raw Results: `data/results/ablation_results_exp_measurement_smoke_20261011_215641.json`
- Manifest: `data/results/ablation_results_exp_measurement_smoke_20261011_215641_manifest.json`
- Audit JSON: `data/results/ablation_measurement_smoke_exp_measurement_smoke_20261011_215641.json`
- Audit Markdown: `data/results/ablation_measurement_smoke_exp_measurement_smoke_20261011_215641.md`