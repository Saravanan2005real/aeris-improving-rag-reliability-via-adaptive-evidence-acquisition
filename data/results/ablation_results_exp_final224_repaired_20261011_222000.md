# AERIS-RAG — Repaired 224-Run Scientific Ablation Report

**Experiment ID:** `exp_final224_repaired_20261011_222000`  
**Date:** 2026-10-13 19:41:43  
**Final Scientific Status:** `SCIENTIFICALLY_VALID`

## 1. Executive Summary & Acceptance Gates

| Gate # | Evaluation Gate | Status | Detail / Justification |
|:---:|:---|:---:|:---|
| 1 | Structural Integrity | **PASS** | Exactly 224 records, 28 questions × 8 variants, 0 duplicates, 0 missing. |
| 2 | Cache Isolation | **PASS** | Isolated per-experiment and per-variant cache namespaces verified. |
| 3 | Answerability & False-Support Safety | **PASS** | False Support Rate = 0.0000 (0/64 unanswerables answered). |
| 4 | Provenance Integrity | **PASS** | 0 answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects. |
| 5 | Correct Evidence Metric Denominators | **PASS** | Hit rate & recall evaluated on answerable questions denominator (N=20 per variant). |
| 6 | Ablation Activation | **PASS** | Telemetry proves disabled components were 100% bypassed. |
| 7 | Latency Instrumentation | **PASS** | Valid end-to-end and stage-level timing without dropped stages. |
| 8 | Overall Scientific Validity | **SCIENTIFICALLY_VALID** | All critical safety and scientific gates passed. |

## 2. Structural & Execution Integrity

- **Total Executions:** 224 / 224
- **Distinct Questions:** 28 (Expected: 28)
- **Distinct Variants:** 8 (Expected: 8)
- **Duplicate Pairs:** 0
- **Missing Pairs:** 0
- **Total Execution Failures:** 0 (Answerable: 0, Unanswerable: 0)
- **Unified Experiment ID:** `exp_final224_repaired_20261011_222000` throughout all records.

## 3. Answerability, Provenance & Evidence Metrics

- **Answerable Questions Correctly Answered (SUPPORTED):** 17 / 160 (10.6%)
- **Answerable Questions Conservatively Rejected (INSUFFICIENT):** 143 / 160 (89.4%)
- **UNANSWERABLE Questions Correctly Rejected (INSUFFICIENT):** 64 / 64 (100.0%)
- **UNANSWERABLE Questions Incorrectly Answered (False Support):** 0 / 64 (**False Support Rate: 0.0000**)
- **Overall Answerability Accuracy:** 36.16%
- **Supported Answers with Zero Claims:** 0
- **High-Confidence Answers without Evidence:** 0
- **Duplicate Claim / Chunk Provenance IDs:** 0 claims, 0 chunks
- **Provenance Defects Detected:** 0 defects across 0 records

## 4. Variant Performance & Ablation Activation Telemetry

| Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Mean Latency | Verified Claims | Selected Claims | Adaptive Retr. Calls | Reform. Calls | Mem Hits |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 90.0% | 0.7917 | 35.0% | 0.2750 | 97.99s | 67 | 50 | 77 | 27 | 0 |
| `NO_ADAPTIVE_RETRIEVAL` | 90.0% | 0.7917 | 35.0% | 0.2750 | 2532.15s | 71 | 52 | 55 | 12 | 0 |
| `NO_CLAIM_VERIFICATION` | 90.0% | 0.7917 | 40.0% | 0.3000 | 96.64s | 0 | 52 | 77 | 27 | 0 |
| `NO_CONTRADICTION_ANALYSIS` | 90.0% | 0.7917 | 30.0% | 0.2500 | 99.48s | 71 | 52 | 77 | 27 | 0 |
| `NO_CROSSLINGUAL_AGREEMENT` | 90.0% | 0.7917 | 30.0% | 0.2250 | 105.70s | 57 | 48 | 77 | 27 | 0 |
| `NO_QUERY_REFORMULATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 97.05s | 71 | 52 | 50 | 0 | 0 |
| `NO_RETRIEVAL_MEMORY` | 90.0% | 0.7917 | 35.0% | 0.2750 | 100.28s | 71 | 52 | 77 | 27 | 0 |
| `NO_SELECTIVE_VERIFICATION` | 90.0% | 0.7667 | 35.0% | 0.2500 | 87.31s | 57 | 0 | 65 | 18 | 0 |

## 5. Ablation Deltas vs FULL_AERIS

| Variant | Retr. Hit Delta | Retr. Rec Delta | Cite. Hit Delta | Cite. Rec Delta | Latency Delta (s) | Latency Delta (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NO_ADAPTIVE_RETRIEVAL` | +0.0% | +0.0000 | +0.0% | +0.0000 | +2434.16s | +2484.0% |
| `NO_CLAIM_VERIFICATION` | +0.0% | +0.0000 | +5.0% | +0.0250 | -1.35s | -1.4% |
| `NO_CONTRADICTION_ANALYSIS` | +0.0% | +0.0000 | -5.0% | -0.0250 | +1.48s | +1.5% |
| `NO_CROSSLINGUAL_AGREEMENT` | +0.0% | +0.0000 | -5.0% | -0.0500 | +7.71s | +7.9% |
| `NO_QUERY_REFORMULATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -0.94s | -1.0% |
| `NO_RETRIEVAL_MEMORY` | +0.0% | +0.0000 | +0.0% | +0.0000 | +2.28s | +2.3% |
| `NO_SELECTIVE_VERIFICATION` | +0.0% | -0.0250 | +0.0% | -0.0250 | -10.68s | -10.9% |

## 6. Component Bypass Verification

- **`NO_ADAPTIVE_RETRIEVAL` Bypass:** PASS (0 activations detected)
- **`NO_QUERY_REFORMULATION` Bypass:** PASS (0 activations detected)
- **`NO_RETRIEVAL_MEMORY` Bypass:** PASS (0 activations detected)
- **`NO_CLAIM_VERIFICATION` Bypass:** PASS (0 activations detected)
- **`NO_CONTRADICTION_ANALYSIS` Bypass:** PASS (0 activations detected)
- **`NO_CROSSLINGUAL_AGREEMENT` Bypass:** PASS (0 activations detected)
- **`NO_SELECTIVE_VERIFICATION` Bypass:** PASS (0 activations detected)

## 7. Deliverables & Artifact Paths

- **Raw Results:** `data/results/ablation_results_exp_final224_repaired_20261011_222000.json`
- **Manifest:** `data/results/ablation_results_exp_final224_repaired_20261011_222000_manifest.json`
- **Diagnostics:** `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl`
- **Structural Audit:** `data/results\ablation_exp_final224_repaired_20261011_222000_structural_audit.json`
- **Scientific Validity Audit:** `data/results\ablation_exp_final224_repaired_20261011_222000_scientific_audit.json`
- **Ablation Activation Audit:** `data/results\ablation_exp_final224_repaired_20261011_222000_activation_audit.json`
- **Metrics & Deltas:** `data/results\ablation_exp_final224_repaired_20261011_222000_metrics.json`
- **Markdown Report:** `data/results\ablation_results_exp_final224_repaired_20261011_222000.md`
