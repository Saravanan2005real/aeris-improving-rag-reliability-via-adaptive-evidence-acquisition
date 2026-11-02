# AERIS-RAG — Benchmark Completion Review & Scientific Audit

**Experiment ID:** `exp_final224_remediation_20261017_142200`  
**Evaluation Mode:** Read-Only Completion & Independent Scientific Verification  
**Date / Timestamp:** `2026-10-17T20:28:00+05:30`  
**Execution Host / Model:** Ollama `llama3.2:latest` (temperature: 0.0, connect timeout: 10s, read timeout: 180s)  
**Total Benchmark Duration:** 21,364.1 seconds (356.1 minutes = 5.93 hours)  
**Overall Automated Audit Status:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`  
**Final Independent Review Verdict:** **`COMPLETED — INDEPENDENT REVIEW REQUIRED`**  

---

## 1. Executive Summary & Acceptance Gate Results

All 224 planned question-variant evaluations for experiment `exp_final224_remediation_20261017_142200` have completed successfully with **zero execution aborts, zero HTTP timeouts, zero dropped stages, and zero provenance defects**.

The engineering remediations implemented in Step 22D and Step 22D.1 functioned exactly as designed:
1. **Retrieval Memory Evidence Delivery:** Repaired cache-hit path delivered valid, non-empty `EvidenceItem` structures, accumulating 10,336 memory hits across ablation variants without dropping evidence or corrupting graph construction.
2. **Ablation Component Isolation:** Disabling `NO_ADAPTIVE_RETRIEVAL` strictly prevented candidate expansions (0 expansions across all 28 questions), while isolating query reformulations.
3. **Decoupled Evaluation:** Candidate retrieval metrics (evaluated on `retrieved_chunk_ids`) and citation metrics (evaluated on `supporting_chunk_ids`) were strictly decoupled across all 224 runs.
4. **Zero Provenance Defects:** Supported answers strictly cite chunks present in the retrieved candidate pool.
5. **Answerable Coverage Recovery:** Answerable supported answers increased from 17 runs (10.6%) in the defective Step 22C benchmark to 77 runs (48.1%) in this run.

However, the automated scientific audit Gate 3 flagged a new scientific trade-off: **False Support Rate on unanswerable questions reached 48.44% (31/64)**, causing Gate 3 to report `BLOCKED`. Consequently, the overall experiment is certified as **ENGINEERING VALID**, but **SCIENTIFICALLY BLOCKED** pending independent review of the answer-support validator threshold.

### Acceptance Gates Summary

| Gate # | Gate Name | Automated Status | Findings & Justification |
|:---:|:---|:---:|:---|
| **1** | **Structural Integrity** | **PASS** | Exactly 224 records, 28 questions $\times$ 8 variants, 0 duplicates, 0 missing records. |
| **2** | **Cache Isolation** | **PASS** | Isolated per-experiment and per-variant cache namespaces verified (`data/cache_exp_final224_remediation_20261017_142200_<variant>.json`). |
| **3** | **Answerability & False Support Safety** | **BLOCKED** | False Support Rate = 48.44% (31 of 64 unanswerable questions were marked `SUPPORTED`). Gate requires $\le 5\%$. |
| **4** | **Provenance Integrity** | **PASS** | 0 supported answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects. |
| **5** | **Evidence Metric Denominators** | **PASS** | Candidate hit rate and recall evaluated strictly on answerable denominator ($N = 20$ per variant, $N = 160$ globally). |
| **6** | **Ablation Activation** | **PASS** | Telemetry proves all 7 disabled components were 100% bypassed under their respective ablation variants. |
| **7** | **Latency Instrumentation** | **PASS** | Valid monotonic timing across all 224 runs; 0 sleep/suspension anomalies ($> 300\text{s}$) detected. |
| **8** | **Overall Status** | **ENG. VALID / SCI. BLOCKED** | Engineering pipeline fully sound; scientific certification withheld due to False Support Rate. |

---

## 2. Record Accounting & Execution Summary

- **Total Expected Records:** 224 ($28 \text{ questions} \times 8 \text{ variants}$)
- **Completed Records:** **224 / 224 (100.0%)**
- **Failed Records:** **0 (0.0%)**
- **Skipped Records:** **0 (0.0%)**
- **Pending Records:** **0**
- **Unified Experiment ID:** `exp_final224_remediation_20261017_142200`
- **Total Execution Time:** 21,364.1 seconds (5h 56m)
- **Mean Latency per Record:** 95.38 seconds

### Answerability Outcomes Breakdown

| Category | Total Evaluated | Answered (SUPPORTED) | Rejected (INSUFFICIENT) | Success / Accuracy |
|:---|:---:|:---:|:---:|:---:|
| **Answerable Questions** ($N_{\text{ans}} = 20 \times 8$) | **160** | **77** (48.1%) | **83** (51.9%) | **48.1% Supported Rate** |
| **Unanswerable Questions** ($N_{\text{unans}} = 8 \times 8$) | **64** | **31** (48.4%) | **33** (51.6%) | **51.6% Rejection Rate** |
| **Total Benchmark** | **224** | **108** (48.2%) | **116** (51.8%) | **49.11% Overall Accuracy** |

- **False Support Rate:** $\frac{31}{64} = \mathbf{48.44\%}$
- **Provenance Defects:** **0 / 224** (100% compliant)

---

## 3. Variant Performance & Ablation Telemetry

All metrics were independently recomputed from raw outputs in [`data/results/ablation_results_exp_final224_remediation_20261017_142200.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261017_142200.json).

| Ablation Variant | Retriever Hit | Retriever Recall | Citation Hit | Citation Recall | Supported Runs ($N_{\text{ans}}=20$) | Mean Latency | Depth Expansions | Reform. Calls | Mem Hits | Claims Verified |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 90.0% | 0.7917 | 35.0% | 0.2750 | 10 / 20 (50.0%) | 99.30s | 25 | 27 | 0 | 66 |
| `NO_ADAPTIVE_RETRIEVAL` | 90.0% | 0.7917 | 35.0% | 0.2750 | 10 / 20 (50.0%) | 96.09s | **0** | 10 | 718 | 70 |
| `NO_CLAIM_VERIFICATION` | 90.0% | 0.7917 | 40.0% | 0.3000 | 10 / 20 (50.0%) | 92.32s | 25 | 27 | 3,868 | **0** |
| `NO_CONTRADICTION_ANALYSIS` | 90.0% | 0.7917 | 30.0% | 0.2500 | 9 / 20 (45.0%) | 93.26s | 25 | 27 | 6,024 | 70 |
| `NO_CROSSLINGUAL_AGREEMENT` | 90.0% | 0.7917 | 35.0% | 0.2750 | 10 / 20 (50.0%) | 94.30s | 25 | 27 | 8,180 | 70 |
| `NO_QUERY_REFORMULATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 9 / 20 (45.0%) | 94.13s | 7 | **0** | 2,162 | 70 |
| `NO_RETRIEVAL_MEMORY` | 90.0% | 0.7917 | 35.0% | 0.2750 | 10 / 20 (50.0%) | 100.87s | 25 | 27 | **0** | 70 |
| `NO_SELECTIVE_VERIFICATION` | 90.0% | 0.7917 | 35.0% | 0.2750 | 9 / 20 (45.0%) | 92.44s | 25 | 27 | 10,336 | 70 |

---

## 4. Question Category Breakdown

Performance across the 8 benchmark question categories ($N = 224$ total):

| Category | Total Runs | Answerable Runs | Unanswerable Runs | Supported Runs | Insufficient Runs | Supported Rate on Answerable | False Support on Unanswerable |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `DIRECT_FACT` | 48 | 48 | 0 | 8 | 40 | 16.7% | N/A |
| `MULTI_HOP` | 40 | 40 | 0 | 9 | 31 | 22.5% | N/A |
| `METHOD` | 32 | 24 | 8 | 30 | 2 | 91.7% | 8 / 8 (100.0%) |
| `COMPARATIVE` | 24 | 16 | 8 | 14 | 10 | 37.5% | 8 / 8 (100.0%) |
| `QUANTITATIVE` | 24 | 16 | 8 | 16 | 8 | **100.0%** | **0 / 8 (0.0%)** |
| `CONTRADICTION` | 16 | 16 | 0 | 16 | 0 | **100.0%** | N/A |
| `MULTILINGUAL` | 8 | 0 | 8 | 7 | 1 | N/A | 7 / 8 (87.5%) |
| `UNANSWERABLE` | 32 | 0 | 32 | 8 | 24 | N/A | **8 / 32 (25.0%)** |

### Category Analysis
1. **Dramatic Improvements in Grounded Categories:**
   - In the defective Step 22C run, `QUANTITATIVE`, `METHOD`, and `CONTRADICTION` had a 0% supported answer rate.
   - In this run, `QUANTITATIVE` and `CONTRADICTION` reached **100.0% supported answer rate** with zero provenance defects, and `METHOD` reached **91.7%**.
2. **Root Cause of False Support:**
   - For `QUANTITATIVE` unanswerables, the validator was **100% effective (0/8 false support)** because quantitative values could not be hallucinated against the chunks.
   - For `UNANSWERABLE` explicit distractors, false support was **25.0% (8/32)**.
   - For `METHOD` and `COMPARATIVE` unanswerable questions, the semantic relaxation allowed conceptual overlap with the paper's broad methodological terms to qualify as support, resulting in 8/8 false support.
   - For `MULTILINGUAL` unanswerable questions (which asked in English for non-existent multilingual findings), 7/8 were falsely supported.

---

## 5. Comparison: New Experiment vs. Historical Step 22C

> [!WARNING]
> Historical experiment `exp_final224_repaired_20261011_222000` is **SCIENTIFICALLY INVALID — REJECTED**. This comparison is provided solely for diagnostic forensics and defect resolution verification.

| Dimension | Historical Step 22C (`exp_final224_repaired`) | Fresh Remediation Run (`exp_final224_remediation`) | Diagnostic Analysis |
|:---|:---:|:---:|:---|
| **Answerable Supported Runs** | 17 / 160 (10.6%) | **77 / 160 (48.1%)** | **+352% increase**. Resolves the catastrophic over-rejection bug where 82 valid answers were downgraded. |
| **Quantitative Category Support** | 0 / 16 (0.0%) | **16 / 16 (100.0%)** | Fully recovered. |
| **Contradiction Category Support** | 0 / 16 (0.0%) | **16 / 16 (100.0%)** | Fully recovered. |
| **False Support Rate** | 0.00% (0 / 64) | **48.44% (31 / 64)** | **Degradation**. Step 22C had 0% false support only because it rejected virtually all answers. The relaxed validator allows false support on conceptual unanswerables. |
| **Adaptive Retrieval Bypass** | FAILED (55 attempts under `NO_AR`) | **PASS (0 depth expansions under `NO_AR`)** | Fully isolated. Candidate schedule pinned strictly to base depth `[10]`. |
| **Retrieval Memory Hits** | 0 across all variants | **10,336 hits accumulated across variants** | Fully functional. Cache-hit evidence delivery repaired; zero empty-evidence drops. |
| **Outlier Latency (Max)** | **67,295.9s (18.69 hrs)** | **297.1s (4.95 mins)** | Latency contamination eliminated. Monotonic timing and active timeouts enforced. |
| **Provenance Defects** | 0 | **0** | Clean provenance preserved. |
| **Total Failures / Aborts** | 0 | **0** | 100% execution completion. |

---

## 6. Artifact Integrity Verification

Original Step 22C benchmark files were checked against their recorded SHA-256 hashes:

| File Path | Recorded Hash | Verified Hash | Integrity Status |
|:---|:---|:---|:---:|
| `data/benchmark/aeris_benchmark.json` | `CE9A86B6...` | `CE9A86B6B4EA354217C54DB4B23A5251E97065DE53773CF154BB95DACCC8E974` | **UNTOUCHED** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000.json` | `A043DADD...` | `A043DADD00685E59310564FFABA14A697EB3EBCD6C3879F2A619F829F9039BF3` | **UNTOUCHED** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_manifest.json` | `043C1E14...` | `043C1E14F663656C0B4BDCCC6C34DF6D8E7050D7BA6E96B77723F50CE0A32714` | **UNTOUCHED** |
| `data/results/ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl` | `BDB0D362...` | `BDB0D362BFB4066741449FE4C74631ED065F6DD7B8EC55ACF534D86A69A69643` | **UNTOUCHED** |

---

## 7. Deliverables & Generated Artifacts

The following experiment artifacts have been generated in `data/results/`:
- **Raw Results (JSON):** [`data/results/ablation_results_exp_final224_remediation_20261017_142200.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261017_142200.json)
- **Manifest (JSON):** [`data/results/ablation_results_exp_final224_remediation_20261017_142200_manifest.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261017_142200_manifest.json)
- **Diagnostics (JSONL):** [`data/results/ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl)
- **Automated Structural Audit:** [`data/results/ablation_exp_final224_remediation_20261017_142200_structural_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261017_142200_structural_audit.json)
- **Automated Scientific Validity Audit:** [`data/results/ablation_exp_final224_remediation_20261017_142200_scientific_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261017_142200_scientific_audit.json)
- **Automated Activation Audit:** [`data/results/ablation_exp_final224_remediation_20261017_142200_activation_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261017_142200_activation_audit.json)
- **Automated Metrics & Deltas:** [`data/results/ablation_exp_final224_remediation_20261017_142200_metrics.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261017_142200_metrics.json)
- **Automated Markdown Summary:** [`data/results/ablation_results_exp_final224_remediation_20261017_142200.md`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261017_142200.md)

---

## 8. Final Status Verdict

In accordance with the required deliverables protocol:

### Verdict: **`COMPLETED — INDEPENDENT REVIEW REQUIRED`**

### Summary Rationale
1. **Engineering Verification:** 100% complete and valid. All 224 runs finished with zero crashes, zero timeouts, decoupled candidate/citation metrics, complete memory reuse without empty evidence drops, and zero provenance defects.
2. **Scientific Review Requirement:** While answerable coverage recovered by +352% (from 17 to 77 supported runs), false support on unanswerable questions rose to 48.44% (31/64). An independent review is required to calibrate the answer-support validator threshold to balance answerable support recovery against unanswerable hallucination rejection before proceeding to Step 23.
