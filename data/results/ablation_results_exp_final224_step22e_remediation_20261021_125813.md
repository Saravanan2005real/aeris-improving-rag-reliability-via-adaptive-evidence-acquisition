# AERIS-RAG — Repaired 224-Run Scientific Ablation Report

**Experiment ID:** `exp_final224_step22e_remediation_20261021_125813`  
**Date:** 2026-10-21 19:02:18  
**Final Scientific Status:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`

## 1. Executive Summary & Acceptance Gates

| Gate # | Evaluation Gate | Status | Detail / Justification |
|:---:|:---|:---:|:---|
| 1 | Structural Integrity | **PASS** | Exactly 224 records, 28 questions × 8 variants, 0 duplicates, 0 missing. |
| 2 | Cache Isolation | **PASS** | Isolated per-experiment and per-variant cache namespaces verified. |
| 3 | Answerability & False-Support Safety | **BLOCKED** | False Support Rate = 0.1250 (8/64 unanswerables answered). |
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
- **Unified Experiment ID:** `exp_final224_step22e_remediation_20261021_125813` throughout all records.

## 3. Answerability, Provenance & Evidence Metrics

- **Answerable Questions Correctly Answered (SUPPORTED):** 67 / 160 (41.9%)
- **Answerable Questions Conservatively Rejected (INSUFFICIENT):** 93 / 160 (58.1%)
- **UNANSWERABLE Questions Correctly Rejected (INSUFFICIENT):** 56 / 64 (87.5%)
- **UNANSWERABLE Questions Incorrectly Answered (False Support):** 8 / 64 (**False Support Rate: 0.1250**)
- **Overall Answerability Accuracy:** 54.91%
- **Supported Answers with Zero Claims:** 0
- **High-Confidence Answers without Evidence:** 0
- **Duplicate Claim / Chunk Provenance IDs:** 0 claims, 0 chunks
- **Provenance Defects Detected:** 0 defects across 0 records

## 4. Variant Performance & Ablation Activation Telemetry

| Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Mean Latency | Verified Claims | Selected Claims | Adaptive Retr. Calls | Reform. Calls | Mem Hits |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 90.0% | 0.7917 | 35.0% | 0.2750 | 105.50s | 67 | 50 | 77 | 27 | 0 |
| `NO_ADAPTIVE_RETRIEVAL` | 90.0% | 0.7917 | 35.0% | 0.2750 | 99.35s | 71 | 52 | 55 | 12 | 718 |
| `NO_CLAIM_VERIFICATION` | 90.0% | 0.7917 | 40.0% | 0.3000 | 92.84s | 0 | 52 | 77 | 27 | 3868 |
| `NO_CONTRADICTION_ANALYSIS` | 90.0% | 0.7917 | 30.0% | 0.2500 | 92.37s | 71 | 52 | 77 | 27 | 6024 |
| `NO_CROSSLINGUAL_AGREEMENT` | 90.0% | 0.7917 | 35.0% | 0.2750 | 94.38s | 71 | 52 | 77 | 27 | 8180 |
| `NO_QUERY_REFORMULATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 97.92s | 71 | 52 | 50 | 0 | 2162 |
| `NO_RETRIEVAL_MEMORY` | 90.0% | 0.7917 | 35.0% | 0.2750 | 102.40s | 71 | 52 | 77 | 27 | 0 |
| `NO_SELECTIVE_VERIFICATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 92.49s | 71 | 0 | 77 | 27 | 10336 |

## 5. Ablation Deltas vs FULL_AERIS

| Variant | Retr. Hit Delta | Retr. Rec Delta | Cite. Hit Delta | Cite. Rec Delta | Latency Delta (s) | Latency Delta (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NO_ADAPTIVE_RETRIEVAL` | +0.0% | +0.0000 | +0.0% | +0.0000 | -6.15s | -5.8% |
| `NO_CLAIM_VERIFICATION` | +0.0% | +0.0000 | +5.0% | +0.0250 | -12.66s | -12.0% |
| `NO_CONTRADICTION_ANALYSIS` | +0.0% | +0.0000 | -5.0% | -0.0250 | -13.13s | -12.4% |
| `NO_CROSSLINGUAL_AGREEMENT` | +0.0% | +0.0000 | +0.0% | +0.0000 | -11.12s | -10.5% |
| `NO_QUERY_REFORMULATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -7.59s | -7.2% |
| `NO_RETRIEVAL_MEMORY` | +0.0% | +0.0000 | +0.0% | +0.0000 | -3.10s | -2.9% |
| `NO_SELECTIVE_VERIFICATION` | +0.0% | +0.0000 | +0.0% | +0.0000 | -13.01s | -12.3% |

## 6. Component Bypass Verification

- **`NO_ADAPTIVE_RETRIEVAL` Bypass:** PASS (0 activations detected)
- **`NO_QUERY_REFORMULATION` Bypass:** PASS (0 activations detected)
- **`NO_RETRIEVAL_MEMORY` Bypass:** PASS (0 activations detected)
- **`NO_CLAIM_VERIFICATION` Bypass:** PASS (0 activations detected)
- **`NO_CONTRADICTION_ANALYSIS` Bypass:** PASS (0 activations detected)
- **`NO_CROSSLINGUAL_AGREEMENT` Bypass:** PASS (0 activations detected)
- **`NO_SELECTIVE_VERIFICATION` Bypass:** PASS (0 activations detected)

## 7. Deliverables & Artifact Paths

- **Raw Results:** `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813.json`
- **Manifest:** `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813_manifest.json`
- **Diagnostics:** `data/results/ablation_results_exp_final224_step22e_remediation_20261021_125813_diagnostics.jsonl`
- **Structural Audit:** `data/results\ablation_exp_final224_step22e_remediation_20261021_125813_structural_audit.json`
- **Scientific Validity Audit:** `data/results\ablation_exp_final224_step22e_remediation_20261021_125813_scientific_audit.json`
- **Ablation Activation Audit:** `data/results\ablation_exp_final224_step22e_remediation_20261021_125813_activation_audit.json`
- **Metrics & Deltas:** `data/results\ablation_exp_final224_step22e_remediation_20261021_125813_metrics.json`
- **Markdown Report:** `data/results\ablation_results_exp_final224_step22e_remediation_20261021_125813.md`
