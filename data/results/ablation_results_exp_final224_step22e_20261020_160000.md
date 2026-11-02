# AERIS-RAG — Repaired 224-Run Scientific Ablation Report

**Experiment ID:** `exp_final224_step22e_20261020_160000`  
**Date:** 2026-10-20 20:33:37  
**Final Scientific Status:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`

## 1. Executive Summary & Acceptance Gates

| Gate # | Evaluation Gate | Status | Detail / Justification |
|:---:|:---|:---:|:---|
| 1 | Structural Integrity | **PASS** | Exactly 224 records, 28 questions × 8 variants, 0 duplicates, 0 missing. |
| 2 | Cache Isolation | **PASS** | Isolated per-experiment and per-variant cache namespaces verified. |
| 3 | Answerability & False-Support Safety | **BLOCKED** | False Support Rate = 0.1094 (7/64 unanswerables answered). |
| 4 | Provenance Integrity | **PASS** | 0 answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects. |
| 5 | Correct Evidence Metric Denominators | **PASS** | Hit rate & recall evaluated on answerable questions denominator (N=20 per variant). |
| 6 | Ablation Activation | **PASS** | Telemetry proves disabled components were 100% bypassed. |
| 7 | Latency Instrumentation | **PASS** | Valid end-to-end and stage-level timing without dropped stages. |
| 8 | Overall Scientific Validity | **ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED** | All critical safety and scientific gates passed. |

## 2. Structural & Execution Integrity

- **Total Executions:** 224 / 224
- **Distinct Questions:** 28 (Expected: 28)
- **Distinct Variants:** 8 (Expected: 8)
- **Duplicate Pairs:** 0
- **Missing Pairs:** 0
- **Total Execution Failures:** 151 (Answerable: 119, Unanswerable: 32)
- **Unified Experiment ID:** `exp_final224_step22e_20261020_160000` throughout all records.

## 3. Answerability, Provenance & Evidence Metrics

- **Answerable Questions Correctly Answered (SUPPORTED):** 14 / 160 (8.8%)
- **Answerable Questions Conservatively Rejected (INSUFFICIENT):** 27 / 160 (16.9%)
- **UNANSWERABLE Questions Correctly Rejected (INSUFFICIENT):** 25 / 64 (39.1%)
- **UNANSWERABLE Questions Incorrectly Answered (False Support):** 7 / 64 (**False Support Rate: 0.1094**)
- **Overall Answerability Accuracy:** 17.41%
- **Supported Answers with Zero Claims:** 0
- **High-Confidence Answers without Evidence:** 0
- **Duplicate Claim / Chunk Provenance IDs:** 0 claims, 0 chunks
- **Provenance Defects Detected:** 0 defects across 0 records

## 4. Variant Performance & Ablation Activation Telemetry

| Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Mean Latency | Verified Claims | Selected Claims | Adaptive Retr. Calls | Reform. Calls | Mem Hits |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 25.0% | 0.2250 | 10.0% | 0.0750 | 73.14s | 15 | 13 | 20 | 9 | 0 |
| `NO_ADAPTIVE_RETRIEVAL` | 25.0% | 0.2250 | 10.0% | 0.0750 | 68.35s | 16 | 14 | 12 | 3 | 333 |
| `NO_CLAIM_VERIFICATION` | 25.0% | 0.2250 | 10.0% | 0.0750 | 70.60s | 0 | 14 | 20 | 9 | 212 |
| `NO_CONTRADICTION_ANALYSIS` | 25.0% | 0.2250 | 15.0% | 0.1250 | 69.51s | 16 | 14 | 20 | 9 | 315 |
| `NO_CROSSLINGUAL_AGREEMENT` | 25.0% | 0.2250 | 10.0% | 0.0750 | 71.41s | 16 | 14 | 20 | 9 | 116 |
| `NO_QUERY_REFORMULATION` | 25.0% | 0.2250 | 10.0% | 0.0750 | 67.48s | 16 | 14 | 11 | 0 | 790 |
| `NO_RETRIEVAL_MEMORY` | 25.0% | 0.2250 | 10.0% | 0.0750 | 73.17s | 16 | 14 | 20 | 9 | 0 |
| `NO_SELECTIVE_VERIFICATION` | 30.0% | 0.2500 | 15.0% | 0.1000 | 70.87s | 19 | 0 | 22 | 9 | 287 |

## 5. Ablation Deltas vs FULL_AERIS

| Variant | Retr. Hit Delta | Retr. Rec Delta | Cite. Hit Delta | Cite. Rec Delta | Latency Delta (s) | Latency Delta (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NO_ADAPTIVE_RETRIEVAL` | +0.0% | +0.0000 | +0.0% | +0.0000 | -4.78s | -6.5% |
| `NO_CLAIM_VERIFICATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -2.54s | -3.5% |
| `NO_CONTRADICTION_ANALYSIS` | +0.0% | +0.0000 | +5.0% | +0.0500 | -3.63s | -5.0% |
| `NO_CROSSLINGUAL_AGREEMENT` | +0.0% | +0.0000 | +0.0% | +0.0000 | -1.73s | -2.4% |
| `NO_QUERY_REFORMULATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -5.66s | -7.7% |
| `NO_RETRIEVAL_MEMORY` | +0.0% | +0.0000 | +0.0% | +0.0000 | +0.03s | +0.0% |
| `NO_SELECTIVE_VERIFICATION` | +5.0% | +0.0250 | +5.0% | +0.0250 | -2.26s | -3.1% |

## 6. Component Bypass Verification

- **`NO_ADAPTIVE_RETRIEVAL` Bypass:** PASS (0 activations detected)
- **`NO_QUERY_REFORMULATION` Bypass:** PASS (0 activations detected)
- **`NO_RETRIEVAL_MEMORY` Bypass:** PASS (0 activations detected)
- **`NO_CLAIM_VERIFICATION` Bypass:** PASS (0 activations detected)
- **`NO_CONTRADICTION_ANALYSIS` Bypass:** PASS (0 activations detected)
- **`NO_CROSSLINGUAL_AGREEMENT` Bypass:** PASS (0 activations detected)
- **`NO_SELECTIVE_VERIFICATION` Bypass:** PASS (0 activations detected)

## 7. Deliverables & Artifact Paths

- **Raw Results:** `data/results/ablation_results_exp_final224_step22e_20261020_160000.json`
- **Manifest:** `data/results/ablation_results_exp_final224_step22e_20261020_160000_manifest.json`
- **Diagnostics:** `data/results/ablation_results_exp_final224_step22e_20261020_160000_diagnostics.jsonl`
- **Structural Audit:** `data/results\ablation_exp_final224_step22e_20261020_160000_structural_audit.json`
- **Scientific Validity Audit:** `data/results\ablation_exp_final224_step22e_20261020_160000_scientific_audit.json`
- **Ablation Activation Audit:** `data/results\ablation_exp_final224_step22e_20261020_160000_activation_audit.json`
- **Metrics & Deltas:** `data/results\ablation_exp_final224_step22e_20261020_160000_metrics.json`
- **Markdown Report:** `data/results\ablation_results_exp_final224_step22e_20261020_160000.md`
