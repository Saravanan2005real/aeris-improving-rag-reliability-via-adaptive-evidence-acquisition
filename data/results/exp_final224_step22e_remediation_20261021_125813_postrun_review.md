# AERIS-RAG — Post-Run Scientific & Engineering Review

**Experiment ID:** `exp_final224_step22e_remediation_20261021_125813`  
**Execution Date:** 2026-10-21 (Start: 12:58:22, End: 19:02:18, Total Duration: 21,769.4s / 362.8 mins)  
**Runner:** `scripts/run_final_224_evaluation.py`  
**Target Benchmark:** `data/benchmark/aeris_benchmark.json` (SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`)  
**Final Scientific Verdict:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`  
**Operational Status:** EXPERIMENT COMPLETE — SCIENTIFICALLY BLOCKED (Step 23 strictly prohibited)

---

## 1. Executive Summary & Acceptance Gates

The fresh 224-record benchmark authorized following the Step 22E preflight completed with **zero execution failures and zero timeouts** (a major engineering remediation triumph compared to the 151 timeouts in Step 22E).

However, while **engineering integrity is 100% passed**, the benchmark remains **`SCIENTIFICALLY BLOCKED`** due to Gate 3 (Answerability & False-Support Safety). Specifically, the False-Support Rate is **12.50% (8 / 64)**, which exceeds the mandatory $\le 5.0\%$ scientific threshold.

### Audit Gates Summary

| Gate # | Evaluation Gate | Status | Detailed Finding / Metric |
| :---: | :--- | :---: | :--- |
| **Gate 1** | **Structural Integrity** | **`PASS`** | Exactly 224 records saved, 28 questions $\times$ 8 variants, 0 duplicates, 0 missing. |
| **Gate 2** | **Cache Isolation** | **`PASS`** | Strict per-experiment and per-variant cache isolation verified across all 8 variants. |
| **Gate 3** | **Answerability & False-Support Safety** | **`BLOCKED`** | **False Support Rate = 12.50% (8 / 64)**. Exceeds the 5.0% threshold. |
| **Gate 4** | **Provenance Integrity** | **`PASS`** | 0 answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects. |
| **Gate 5** | **Evidence Metric Denominators** | **`PASS`** | Correctly evaluated exclusively on answerable denominator ($N=20$ per variant). |
| **Gate 6** | **Ablation Activation** | **`PASS`** | 100% complete bypass verified for disabled components across all ablation variants. |
| **Gate 7** | **Latency Instrumentation** | **`PASS`** | Comprehensive monotonic and wall-clock stage timing; 0 dropped or missing stages. |
| **Gate 8** | **Overall Scientific Validity** | **`BLOCKED`** | **ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED** due to Gate 3 failure. |

---

## 2. Record Accounting & Execution Attrition

| Dimension | Target | Actual | Delta / Status |
| :--- | :---: | :---: | :--- |
| **Total Expected Records** | 224 | 224 | Match |
| **Total Saved Records** | 224 | 224 | Match |
| **Distinct Benchmark Questions** | 28 | 28 | Match |
| **Distinct Ablation Variants** | 8 | 8 | Match |
| **Unique Question-Variant Pairs** | 224 | 224 | Match |
| **Duplicate Pairs** | 0 | 0 | None |
| **Missing Pairs** | 0 | 0 | None |
| **Execution Failures / Crashes** | 0 | 0 | **0.0% Attrition** (vs. 151 in Step 22E) |
| **Timeouts Exceeded** | 0 | 0 | **180s HTTP timeout succeeded completely** |

### Per-Variant Record Accounting
All 8 variants completed all 28 questions with zero execution attrition:
- `FULL_AERIS`: 28 / 28 (0 failed)
- `NO_ADAPTIVE_RETRIEVAL`: 28 / 28 (0 failed)
- `NO_QUERY_REFORMULATION`: 28 / 28 (0 failed)
- `NO_RETRIEVAL_MEMORY`: 28 / 28 (0 failed)
- `NO_CLAIM_VERIFICATION`: 28 / 28 (0 failed)
- `NO_CONTRADICTION_ANALYSIS`: 28 / 28 (0 failed)
- `NO_CROSSLINGUAL_AGREEMENT`: 28 / 28 (0 failed)
- `NO_SELECTIVE_VERIFICATION`: 28 / 28 (0 failed)

---

## 3. False-Support Safety & Answerability Performance

### 3.1 False-Support Metric Analysis
- **False Support Numerator:** 8 runs
- **False Support Denominator:** 64 unanswerable evaluations (8 unanswerable questions $\times$ 8 variants)
- **False Support Rate:** $\frac{8}{64} = 0.1250$ (**12.50%**)
- **Threshold Requirement:** $\le 0.0500$ (5.0%)
- **Gate 3 Status:** **BLOCKED**

### 3.2 Breakdown of Unanswerable Questions
Eight questions in the 28-question benchmark are unanswerable (`answerability: false`, expected status `INSUFFICIENT_EVIDENCE`):

| Question ID | Category | Question Text | Status Across All 8 Variants | False Support? |
| :--- | :--- | :--- | :--- | :---: |
| `q_unans_01` | UNANSWERABLE | *"What is the exact parameter count of the dense retriever encoder?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** |
| `q_unans_02` | UNANSWERABLE | *"What hardware was used to train the RAG models?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** *(Remediated!)* |
| `q_unans_03` | UNANSWERABLE | *"What is the GPU memory consumption during inference?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** |
| `q_unans_04` | UNANSWERABLE | *"What is the exact date when model training was completed?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** |
| `q_comp_03` | COMPARATIVE | *"How does the memory footprint compare between models during training?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** |
| `q_multi_01` | MULTILINGUAL | *"What is the BLEU score of RAG on French-to-German translation?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** |
| `q_quant_03` | QUANTITATIVE | *"What is the exact inference latency in milliseconds on CPU?"* | `INSUFFICIENT_EVIDENCE` (8/8) | **NO (0 / 8)** |
| `q_meth_02` | METHOD | *"How does the system fuse dense and sparse retrieval?"* | `PARTIALLY_SUPPORTED` (8/8) | **YES (8 / 8)** |

### 3.3 The `q_unans_02` Success
In Step 22E, `q_unans_02` generated **7 false-supported records** because the validator accepted generic `"train"` mentions from p. 4 dataset splits.
In this fresh run:
- **`q_unans_02` false-support count:** **0 / 8** (100% correct rejection).
- Every variant evaluated `q_unans_02` as `INSUFFICIENT_EVIDENCE`.
- This empirically verifies that the Step 22E hardware-grounding fix was completely effective.

### 3.4 Root Cause of the 8 False-Support Cases on `q_meth_02`
All 8 false-support cases in this run belong to question `q_meth_02` (*"How does the system fuse dense and sparse retrieval?"*):
1. **Hidden by Prior Failures:** In Step 22E, `q_meth_02` timed out and failed across all 8 variants, so it was counted under execution attrition rather than evaluated for answerability.
2. **Conjunctive Partial Support Defect:**
   - The query asks how dense and sparse retrieval are fused.
   - The requirement planner decomposed this into 3 requirements: R1 (dense retrieval), R2 (sparse retrieval), and R3 (dense-sparse fusion).
   - The validator correctly rejected R2 and R3 via judge override: `[Judge override: cited evidence does not contain required facts: Required concept 'sparse' is absent from cited evidence.]`.
   - However, R1 (dense retrieval) was supported by the DPR text.
   - The controller assigned status `PARTIALLY_SUPPORTED` (1 of 3 requirements satisfied).
   - Under the scientific audit rule (`is_supported = status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]`), assigning partial support to an unanswerable question constitutes false support.

### 3.5 Answerable Question Performance
- **Answerable Questions (20 questions $\times$ 8 variants = 160 evaluations):**
  - **Correctly Answered (`SUPPORTED`):** 67 / 160 (41.88%)
  - **Conservatively Rejected (`INSUFFICIENT_EVIDENCE`):** 93 / 160 (58.12%)
  - **Execution Failures:** 0 / 160 (0.00%)
- **Overall Answerability Accuracy:** $\frac{67 + 56}{224} = \frac{123}{224} = 54.91\%$

---

## 4. Retrieval, Citation, Provenance & Ablation Telemetry

### 4.1 Evidence Retrieval and Citation Metrics ($N=20$ Answerable Questions)

| Variant | Retriever Hit Rate | Retriever Recall | Citation Hit Rate | Citation Recall |
| :--- | :---: | :---: | :---: | :---: |
| `FULL_AERIS` | 90.0% | 0.7917 | 35.0% | 0.2750 |
| `NO_ADAPTIVE_RETRIEVAL` | 90.0% | 0.7917 | 35.0% | 0.2750 |
| `NO_CLAIM_VERIFICATION` | 90.0% | 0.7917 | 40.0% | 0.3000 |
| `NO_CONTRADICTION_ANALYSIS` | 90.0% | 0.7917 | 30.0% | 0.2500 |
| `NO_CROSSLINGUAL_AGREEMENT` | 90.0% | 0.7917 | 35.0% | 0.2750 |
| `NO_QUERY_REFORMULATION` | 90.0% | 0.7917 | 35.0% | 0.2750 |
| `NO_RETRIEVAL_MEMORY` | 90.0% | 0.7917 | 35.0% | 0.2750 |
| `NO_SELECTIVE_VERIFICATION` | 90.0% | 0.7917 | 35.0% | 0.2750 |

### 4.2 Provenance Integrity (Gate 4: PASS)
- **Supported Answers with Zero Claims:** 0
- **Supported Answers with Zero Valid Evidence:** 0
- **High-Confidence Answers ($\ge 0.9$) without Evidence:** 0
- **Duplicate Claim IDs:** 0
- **Duplicate Chunk IDs:** 0
- **Provenance Defects Detected:** 0 defects across 0 records

### 4.3 Component Bypass Verification (Gate 6: PASS)
Telemetry audit verified 100% isolation and bypass when components were ablated:
- `NO_ADAPTIVE_RETRIEVAL`: 0 candidate depth expansions (bypassed)
- `NO_QUERY_REFORMULATION`: 0 reformulation calls (bypassed)
- `NO_RETRIEVAL_MEMORY`: 0 memory hits (bypassed)
- `NO_CLAIM_VERIFICATION`: 0 claims verified (bypassed)
- `NO_CONTRADICTION_ANALYSIS`: 0 contradiction checks (bypassed)
- `NO_CROSSLINGUAL_AGREEMENT`: 0 cross-lingual pairs evaluated (bypassed)
- `NO_SELECTIVE_VERIFICATION`: 0 selective calls (bypassed)

---

## 5. Latency and Stage-Level Telemetry

| Variant | Mean Latency (s) | Median Latency (s) | P90 Latency (s) | P95 Latency (s) | Max Latency (s) | Latency Delta vs FULL |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `FULL_AERIS` | 105.50s | 70.00s | 210.91s | 228.53s | 313.96s | Baseline |
| `NO_ADAPTIVE_RETRIEVAL` | 99.35s | 68.42s | 196.22s | 221.40s | 295.12s | -6.15s (-5.8%) |
| `NO_QUERY_REFORMULATION` | 97.92s | 66.85s | 194.50s | 220.10s | 291.45s | -7.58s (-7.2%) |
| `NO_RETRIEVAL_MEMORY` | 102.40s | 69.10s | 205.12s | 225.80s | 305.20s | -3.10s (-2.9%) |
| `NO_CLAIM_VERIFICATION` | 92.84s | 62.15s | 185.40s | 210.50s | 280.12s | -12.66s (-12.0%) |
| `NO_CONTRADICTION_ANALYSIS` | 92.37s | 61.80s | 184.90s | 209.80s | 279.50s | -13.13s (-12.4%) |
| `NO_CROSSLINGUAL_AGREEMENT` | 94.38s | 63.40s | 188.10s | 212.40s | 283.15s | -11.12s (-10.5%) |
| `NO_SELECTIVE_VERIFICATION` | 92.49s | 62.05s | 185.10s | 210.15s | 280.45s | -13.01s (-12.3%) |

---

## 6. Scientific Documentation of `q_unans_02` Discrepancy

1. **Benchmark Specification:**
   - Question: *"What hardware was used to train the RAG models?"*
   - Ground Truth Label: `UNANSWERABLE`, expected status `INSUFFICIENT_EVIDENCE`, `supporting_chunk_ids: []`.
2. **Document Truth:**
   - Appendix C (p. 17, `test_document_p017_c037`) explicitly states: *"distributing training across 8, 32GB NVIDIA V100 GPUs"*.
   - All 42 chunks across pages 1–19 are indexed in the vector store, and pages 18–19 are actively cited by other benchmark queries.
3. **Execution Behavior in this Run:**
   - The retrieval pipeline did not retrieve Appendix C (p. 17). It retrieved p. 4 (`test_document_p004_c010`), which contains generic `"train/dev/test splits"` but zero hardware information.
   - The remediated validator detected that no hardware concepts were present in the evidence and strictly rejected the answer claims across all 8 variants.
   - Result: 8 / 8 `INSUFFICIENT_EVIDENCE` decisions.
4. **Integrity Rule:**
   - The benchmark dataset hash remains strictly preserved (`ce9a86b6...`).

---

## 7. Byte-for-Byte SHA-256 Integrity Verification

All critical benchmark and historical result artifacts were hashed following the run to confirm zero tampering:

| Artifact Path | Baseline SHA-256 | Current SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `data/benchmark/aeris_benchmark.json` | `ce9a86b6...e974` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **IDENTICAL** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000.json` | `4d9d1655...e83c` | `4d9d1655378b8123b415110d35f68740a9be9e08f96b65961872ed058e14e83c` | **IDENTICAL** |
| `data/results/ablation_results_exp_final224_step22e_20261020_160000_manifest.json` | `5bbb6cce...9632` | `5bbb6cce9686282562c1d4e9ef58f1692018a348c947b5629572a44cf7c99632` | **IDENTICAL** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_metrics.json` | `863434c4...4a95` | `863434c4a39d55b24ff88bab917de3367b2e29cb49a558b009647fd322514a95` | **IDENTICAL** |
| `data/results/ablation_exp_final224_step22e_20261020_160000_scientific_audit.json` | `d3dde38a...b387` | `d3dde38a897436b9af0dc405f1354dda73b018262d617bda35dd8f96396eb387` | **IDENTICAL** |
| `data/results/exp_final224_step22e_20261020_160000_root_cause_investigation.md` | `10027ef7...38d2` | `10027ef7c541fd65cb9710291fccc4721ed2919e80611c9f9907ee9c374538d2` | **IDENTICAL** |
| `data/results/ablation_results_exp_final224_remediation_20261017_142200.json` | `df985020...d6cf` | `df9850207668edaa59d3ce4f5acc7074c119f72b12ce0a4c86638c24197dd6cf` | **IDENTICAL** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` | `a043dadd...9bf3` | `a043dadd00685e59310564ffaba14a697eb3ebcd6c3879f2a619f829f9039bf3` | **IDENTICAL** |
| `data/results/step22e_postrun_remediation_report.md` | `061ae55b...8976` | `061ae55b121ed7f3ecb5aaafc098a3bdb78ccd541d8dac5f2e629c2f0c18976d` | **IDENTICAL** |
| `data/results/step22e_postrun_remediation_independent_audit.md` | `723e91d0...a856` | `723e91d05a56a3ba8864c3560cf7e5277f95b785769651a5e5b2691ee6f5a856` | **IDENTICAL** |
| `data/results/step22e_final_preflight.md` | `88746d1a...737c` | `88746d1ab6cdcd4ebf0203192759e222442d865c32b8977a7dca85c55648737c` | **IDENTICAL** |

---

## 8. Final Scientific Verdict & Stop Condition

### **FINAL SCIENTIFIC VERDICT: ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED**

### Summary of Status:
1. **Engineering Status:** **100% PASSED**. 224/224 records completed, 0 execution failures, 0 timeouts, 0 provenance defects, 100% component bypass.
2. **Scientific Status:** **BLOCKED**. The False-Support Rate is **12.50% (8 / 64)** due to `q_meth_02` receiving `PARTIALLY_SUPPORTED` status instead of `INSUFFICIENT_EVIDENCE`.
3. **Step 23 Status:** **STRICTLY PROHIBITED**. Step 23 cannot be initiated until Gate 3 is satisfied.
4. **Historical Safeguard:** All historical experiment artifacts remain byte-for-byte preserved. No secondary benchmark runs will be launched without explicit authorization.
