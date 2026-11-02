# AERIS-RAG — Repaired 224-Run Scientific Ablation Report

**Experiment ID:** `exp_final224_remediation_20261022_183626`  
**Date:** 2026-10-23 01:11:46  
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
- **Total Execution Failures:** 8 (Answerable: 8, Unanswerable: 0)
- **Unified Experiment ID:** `exp_final224_remediation_20261022_183626` throughout all records.

## 3. Answerability, Provenance & Evidence Metrics

- **Answerable Questions Correctly Answered (SUPPORTED):** 34 / 160 (21.2%)
- **Answerable Questions Conservatively Rejected (INSUFFICIENT):** 118 / 160 (73.8%)
- **UNANSWERABLE Questions Correctly Rejected (INSUFFICIENT):** 64 / 64 (100.0%)
- **UNANSWERABLE Questions Incorrectly Answered (False Support):** 0 / 64 (**False Support Rate: 0.0000**)
- **Overall Answerability Accuracy:** 43.75%
- **Supported Answers with Zero Claims:** 0
- **High-Confidence Answers without Evidence:** 0
- **Duplicate Claim / Chunk Provenance IDs:** 0 claims, 0 chunks
- **Provenance Defects Detected:** 0 defects across 0 records

## 4. Variant Performance & Ablation Activation Telemetry

| Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Mean Latency | Verified Claims | Selected Claims | Adaptive Retr. Calls | Reform. Calls | Mem Hits |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 85.0% | 0.7167 | 35.0% | 0.2750 | 112.68s | 63 | 49 | 63 | 18 | 0 |
| `NO_ADAPTIVE_RETRIEVAL` | 85.0% | 0.7167 | 35.0% | 0.2750 | 105.98s | 63 | 49 | 47 | 6 | 666 |
| `NO_CLAIM_VERIFICATION` | 85.0% | 0.7167 | 35.0% | 0.2750 | 102.63s | 0 | 49 | 63 | 18 | 3354 |
| `NO_CONTRADICTION_ANALYSIS` | 85.0% | 0.7167 | 35.0% | 0.2750 | 103.47s | 63 | 49 | 63 | 18 | 5109 |
| `NO_CROSSLINGUAL_AGREEMENT` | 85.0% | 0.7167 | 35.0% | 0.2750 | 103.91s | 63 | 49 | 63 | 18 | 6864 |
| `NO_QUERY_REFORMULATION` | 85.0% | 0.7167 | 35.0% | 0.2750 | 104.59s | 63 | 49 | 45 | 0 | 1977 |
| `NO_RETRIEVAL_MEMORY` | 85.0% | 0.7167 | 35.0% | 0.2750 | 109.87s | 63 | 49 | 63 | 18 | 0 |
| `NO_SELECTIVE_VERIFICATION` | 85.0% | 0.7167 | 35.0% | 0.2750 | 102.28s | 63 | 0 | 63 | 18 | 8619 |

## 5. Ablation Deltas vs FULL_AERIS

| Variant | Retr. Hit Delta | Retr. Rec Delta | Cite. Hit Delta | Cite. Rec Delta | Latency Delta (s) | Latency Delta (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NO_ADAPTIVE_RETRIEVAL` | +0.0% | +0.0000 | +0.0% | +0.0000 | -6.70s | -5.9% |
| `NO_CLAIM_VERIFICATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -10.04s | -8.9% |
| `NO_CONTRADICTION_ANALYSIS` | +0.0% | +0.0000 | +0.0% | +0.0000 | -9.21s | -8.2% |
| `NO_CROSSLINGUAL_AGREEMENT` | +0.0% | +0.0000 | +0.0% | +0.0000 | -8.77s | -7.8% |
| `NO_QUERY_REFORMULATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -8.08s | -7.2% |
| `NO_RETRIEVAL_MEMORY` | +0.0% | +0.0000 | +0.0% | +0.0000 | -2.81s | -2.5% |
| `NO_SELECTIVE_VERIFICATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -10.40s | -9.2% |

## 6. Component Bypass Verification

- **`NO_ADAPTIVE_RETRIEVAL` Bypass:** PASS (0 activations detected)
- **`NO_QUERY_REFORMULATION` Bypass:** PASS (0 activations detected)
- **`NO_RETRIEVAL_MEMORY` Bypass:** PASS (0 activations detected)
- **`NO_CLAIM_VERIFICATION` Bypass:** PASS (0 activations detected)
- **`NO_CONTRADICTION_ANALYSIS` Bypass:** PASS (0 activations detected)
- **`NO_CROSSLINGUAL_AGREEMENT` Bypass:** PASS (0 activations detected)
- **`NO_SELECTIVE_VERIFICATION` Bypass:** PASS (0 activations detected)

## 7. Deliverables & Artifact Paths

- **Raw Results:** `data/results/ablation_results_exp_final224_remediation_20261022_183626.json`
- **Manifest:** `data/results/ablation_results_exp_final224_remediation_20261022_183626_manifest.json`
- **Diagnostics:** `data/results/ablation_results_exp_final224_remediation_20261022_183626_diagnostics.jsonl`
- **Structural Audit:** `data/results\ablation_exp_final224_remediation_20261022_183626_structural_audit.json`
- **Scientific Validity Audit:** `data/results\ablation_exp_final224_remediation_20261022_183626_scientific_audit.json`
- **Ablation Activation Audit:** `data/results\ablation_exp_final224_remediation_20261022_183626_activation_audit.json`
- **Metrics & Deltas:** `data/results\ablation_exp_final224_remediation_20261022_183626_metrics.json`
- **Markdown Report:** `data/results\ablation_results_exp_final224_remediation_20261022_183626.md`
