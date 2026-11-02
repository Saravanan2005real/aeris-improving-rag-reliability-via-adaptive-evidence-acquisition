# AERIS-RAG — Repaired 224-Run Scientific Ablation Report

**Experiment ID:** `exp_final224_remediation_20261017_142200`  
**Date:** 2026-10-17 20:26:42  
**Final Scientific Status:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`

## 1. Executive Summary & Acceptance Gates

| Gate # | Evaluation Gate | Status | Detail / Justification |
|:---:|:---|:---:|:---|
| 1 | Structural Integrity | **PASS** | Exactly 224 records, 28 questions × 8 variants, 0 duplicates, 0 missing. |
| 2 | Cache Isolation | **PASS** | Isolated per-experiment and per-variant cache namespaces verified. |
| 3 | Answerability & False-Support Safety | **BLOCKED** | False Support Rate = 0.4844 (31/64 unanswerables answered). |
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
- **Total Execution Failures:** 0 (Answerable: 0, Unanswerable: 0)
- **Unified Experiment ID:** `exp_final224_remediation_20261017_142200` throughout all records.

## 3. Answerability, Provenance & Evidence Metrics

- **Answerable Questions Correctly Answered (SUPPORTED):** 77 / 160 (48.1%)
- **Answerable Questions Conservatively Rejected (INSUFFICIENT):** 83 / 160 (51.9%)
- **UNANSWERABLE Questions Correctly Rejected (INSUFFICIENT):** 33 / 64 (51.6%)
- **UNANSWERABLE Questions Incorrectly Answered (False Support):** 31 / 64 (**False Support Rate: 0.4844**)
- **Overall Answerability Accuracy:** 49.11%
- **Supported Answers with Zero Claims:** 0
- **High-Confidence Answers without Evidence:** 0
- **Duplicate Claim / Chunk Provenance IDs:** 0 claims, 0 chunks
- **Provenance Defects Detected:** 0 defects across 0 records

## 4. Variant Performance & Ablation Activation Telemetry

| Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Mean Latency | Verified Claims | Selected Claims | Adaptive Retr. Calls | Reform. Calls | Mem Hits |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 90.0% | 0.7917 | 35.0% | 0.2750 | 99.30s | 66 | 49 | 77 | 27 | 0 |
| `NO_ADAPTIVE_RETRIEVAL` | 90.0% | 0.7917 | 35.0% | 0.2750 | 96.09s | 70 | 51 | 53 | 10 | 718 |
| `NO_CLAIM_VERIFICATION` | 90.0% | 0.7917 | 40.0% | 0.3000 | 92.32s | 0 | 51 | 77 | 27 | 3868 |
| `NO_CONTRADICTION_ANALYSIS` | 90.0% | 0.7917 | 30.0% | 0.2500 | 93.26s | 70 | 51 | 77 | 27 | 6024 |
| `NO_CROSSLINGUAL_AGREEMENT` | 90.0% | 0.7917 | 35.0% | 0.2750 | 94.30s | 70 | 51 | 77 | 27 | 8180 |
| `NO_QUERY_REFORMULATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 94.13s | 70 | 51 | 50 | 0 | 2162 |
| `NO_RETRIEVAL_MEMORY` | 90.0% | 0.7917 | 35.0% | 0.2750 | 100.87s | 70 | 51 | 77 | 27 | 0 |
| `NO_SELECTIVE_VERIFICATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 92.44s | 70 | 0 | 77 | 27 | 10336 |

## 5. Ablation Deltas vs FULL_AERIS

| Variant | Retr. Hit Delta | Retr. Rec Delta | Cite. Hit Delta | Cite. Rec Delta | Latency Delta (s) | Latency Delta (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NO_ADAPTIVE_RETRIEVAL` | +0.0% | +0.0000 | +0.0% | +0.0000 | -3.21s | -3.2% |
| `NO_CLAIM_VERIFICATION` | +0.0% | +0.0000 | +5.0% | +0.0250 | -6.97s | -7.0% |
| `NO_CONTRADICTION_ANALYSIS` | +0.0% | +0.0000 | -5.0% | -0.0250 | -6.03s | -6.1% |
| `NO_CROSSLINGUAL_AGREEMENT` | +0.0% | +0.0000 | +0.0% | +0.0000 | -5.00s | -5.0% |
| `NO_QUERY_REFORMULATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -5.17s | -5.2% |
| `NO_RETRIEVAL_MEMORY` | +0.0% | +0.0000 | +0.0% | +0.0000 | +1.57s | +1.6% |
| `NO_SELECTIVE_VERIFICATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -6.85s | -6.9% |

## 6. Component Bypass Verification

- **`NO_ADAPTIVE_RETRIEVAL` Bypass:** PASS (0 activations detected)
- **`NO_QUERY_REFORMULATION` Bypass:** PASS (0 activations detected)
- **`NO_RETRIEVAL_MEMORY` Bypass:** PASS (0 activations detected)
- **`NO_CLAIM_VERIFICATION` Bypass:** PASS (0 activations detected)
- **`NO_CONTRADICTION_ANALYSIS` Bypass:** PASS (0 activations detected)
- **`NO_CROSSLINGUAL_AGREEMENT` Bypass:** PASS (0 activations detected)
- **`NO_SELECTIVE_VERIFICATION` Bypass:** PASS (0 activations detected)

## 7. Deliverables & Artifact Paths

- **Raw Results:** `data/results/ablation_results_exp_final224_remediation_20261017_142200.json`
- **Manifest:** `data/results/ablation_results_exp_final224_remediation_20261017_142200_manifest.json`
- **Diagnostics:** `data/results/ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl`
- **Structural Audit:** `data/results\ablation_exp_final224_remediation_20261017_142200_structural_audit.json`
- **Scientific Validity Audit:** `data/results\ablation_exp_final224_remediation_20261017_142200_scientific_audit.json`
- **Ablation Activation Audit:** `data/results\ablation_exp_final224_remediation_20261017_142200_activation_audit.json`
- **Metrics & Deltas:** `data/results\ablation_exp_final224_remediation_20261017_142200_metrics.json`
- **Markdown Report:** `data/results\ablation_results_exp_final224_remediation_20261017_142200.md`
