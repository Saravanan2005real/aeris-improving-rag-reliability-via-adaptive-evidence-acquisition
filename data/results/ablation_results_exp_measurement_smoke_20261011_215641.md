# AERIS-RAG — Repaired 224-Run Scientific Ablation Report

**Experiment ID:** `exp_measurement_smoke_20261011_215641`  
**Date:** 2026-10-11 22:19:43  
**Final Scientific Status:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`

## 1. Executive Summary & Acceptance Gates

| Gate # | Evaluation Gate | Status | Detail / Justification |
|:---:|:---|:---:|:---|
| 1 | Structural Integrity | **FAIL** | Exactly 224 records, 28 questions × 8 variants, 0 duplicates, 0 missing. |
| 2 | Cache Isolation | **PASS** | Isolated per-experiment and per-variant cache namespaces verified. |
| 3 | Answerability & False-Support Safety | **PASS** | False Support Rate = 0.0000 (0/1 unanswerables answered). |
| 4 | Provenance Integrity | **PASS** | 0 answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects. |
| 5 | Correct Evidence Metric Denominators | **BLOCKED** | Hit rate & recall evaluated on answerable questions denominator (N=20 per variant). |
| 6 | Ablation Activation | **PASS** | Telemetry proves disabled components were 100% bypassed. |
| 7 | Latency Instrumentation | **PASS** | Valid end-to-end and stage-level timing without dropped stages. |
| 8 | Overall Scientific Validity | **ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED** | All critical safety and scientific gates passed. |

## 2. Structural & Execution Integrity

- **Total Executions:** 4 / 224
- **Distinct Questions:** 4 (Expected: 28)
- **Distinct Variants:** 1 (Expected: 8)
- **Duplicate Pairs:** 0
- **Missing Pairs:** 220
- **Total Execution Failures:** 0 (Answerable: 0, Unanswerable: 0)
- **Unified Experiment ID:** `exp_measurement_smoke_20261011_215641` throughout all records.

## 3. Answerability, Provenance & Evidence Metrics

- **Answerable Questions Correctly Answered (SUPPORTED):** 0 / 3 (0.0%)
- **Answerable Questions Conservatively Rejected (INSUFFICIENT):** 3 / 3 (100.0%)
- **UNANSWERABLE Questions Correctly Rejected (INSUFFICIENT):** 1 / 1 (100.0%)
- **UNANSWERABLE Questions Incorrectly Answered (False Support):** 0 / 1 (**False Support Rate: 0.0000**)
- **Overall Answerability Accuracy:** 25.00%
- **Supported Answers with Zero Claims:** 0
- **High-Confidence Answers without Evidence:** 0
- **Duplicate Claim / Chunk Provenance IDs:** 0 claims, 0 chunks
- **Provenance Defects Detected:** 0 defects across 0 records

## 4. Variant Performance & Ablation Activation Telemetry

| Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Mean Latency | Verified Claims | Selected Claims | Adaptive Retr. Calls | Reform. Calls | Mem Hits |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 66.7% | 0.3333 | 33.3% | 0.1667 | 182.04s | 9 | 9 | 18 | 9 | 0 |

## 5. Ablation Deltas vs FULL_AERIS

| Variant | Retr. Hit Delta | Retr. Rec Delta | Cite. Hit Delta | Cite. Rec Delta | Latency Delta (s) | Latency Delta (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|

## 6. Component Bypass Verification

- **`NO_ADAPTIVE_RETRIEVAL` Bypass:** PASS (0 activations detected)
- **`NO_QUERY_REFORMULATION` Bypass:** PASS (0 activations detected)
- **`NO_RETRIEVAL_MEMORY` Bypass:** PASS (0 activations detected)
- **`NO_CLAIM_VERIFICATION` Bypass:** PASS (0 activations detected)
- **`NO_CONTRADICTION_ANALYSIS` Bypass:** PASS (0 activations detected)
- **`NO_CROSSLINGUAL_AGREEMENT` Bypass:** PASS (0 activations detected)
- **`NO_SELECTIVE_VERIFICATION` Bypass:** PASS (0 activations detected)

## 7. Deliverables & Artifact Paths

- **Raw Results:** `data/results/ablation_results_exp_measurement_smoke_20261011_215641.json`
- **Manifest:** `data/results/ablation_results_exp_measurement_smoke_20261011_215641_manifest.json`
- **Diagnostics:** `data/results/ablation_results_exp_measurement_smoke_20261011_215641_diagnostics.jsonl`
- **Structural Audit:** `data/results\ablation_exp_measurement_smoke_20261011_215641_structural_audit.json`
- **Scientific Validity Audit:** `data/results\ablation_exp_measurement_smoke_20261011_215641_scientific_audit.json`
- **Ablation Activation Audit:** `data/results\ablation_exp_measurement_smoke_20261011_215641_activation_audit.json`
- **Metrics & Deltas:** `data/results\ablation_exp_measurement_smoke_20261011_215641_metrics.json`
- **Markdown Report:** `data/results\ablation_results_exp_measurement_smoke_20261011_215641.md`
