# AERIS-RAG — Independent Scientific Audit of Final 224-Run Results

**Experiment ID:** `exp_final224_20261011_113501`  
**Audit Date:** 2026-10-11  
**Final Audit Status:** `SCIENTIFICALLY_VALID` (with Metric Reporting Corrections)

## Executive Summary of Audit Findings

| Issue / Gate | Audit Finding | Status |
|---|---|:---:|
| **1. Failed-Run Denominator** | Failed run `FULL_AERIS / q_mh_04` was grouped into 'insufficient' in earlier script. Fully separated and reconciled below. | **PASS** (Resolved) |
| **2. Identical Retrieval Metrics** | Retrieval metrics (35% hit, 0.275 recall) are genuinely identical across variants. Cited chunks differ across ablations, but 7 gold hits are identical. | **PASS** |
| **3. Cross-Lingual Latency** | Timing is accurate (~82.8 microseconds). Formatted as 0.00s due to 2-decimal rounding on unilingual English benchmark. | **PASS** |
| **4. Latency Reconciliation** | 5.32s difference between stage sums and E2E is 100% accounted for by 149.06s aborted claim typing in `q_mh_04` ($149.06 / 28 = 5.32s$). | **PASS** |
| **5. Overall Scientific Validity** | 0/64 False Supports (FSR = 0.0000), 100% cache isolation, 0 provenance defects. | **SCIENTIFICALLY_VALID** |

## Issue 1: Failed-Run Denominator & Metric Breakdown

In the raw 224-run dataset, exactly **1 execution failed**:
- **Record:** `FULL_AERIS / q_mh_04`
- **Root Cause:** Local LLM returned non-standard claim type `'COMPARE'` (instead of `'COMPARISON'`), raising `ClaimTypingError` after 3 retries.
- **Audit Finding:** The previous reporting script used a binary check (`if is_supported: ... else: insufficient += 1`), which incremented the 'insufficient' counter for `q_mh_04`. It should be distinctly categorized as `FAILED`.

### Corrected Metric Enumeration:

| Metric | Formula | Exact Value | Prior Reported Value |
|---|:---:|:---:|:---:|
| Answerable Supported Rate (All 160) | $23 / 160$ | **14.38%** | 14.38% |
| Answerable Supported Rate (Completed 159) | $23 / 159$ | **14.47%** | — |
| Answerable Insufficient Rate | $136 / 160$ | **85.00%** | 85.62% (contained failed run) |
| Answerable Failed Rate | $1 / 160$ | **0.62%** | 0.00% |
| False Support Rate | $0 / 64$ | **0.0000 (0.0%)** | 0.0000 |
| Answerability Accuracy (All 224) | $(23 + 64) / 224$ | **38.84%** | 38.84% |
| Answerability Accuracy (Completed 223) | $(23 + 64) / 223$ | **39.01%** | — |
| `FULL_AERIS` Hit Rate (N=20, Intent-to-treat) | $7 / 20$ | **35.00%** | 35.00% |
| `FULL_AERIS` Hit Rate (N=19, Completed only) | $7 / 19$ | **36.84%** | — |
| `FULL_AERIS` Evidence Recall (N=20) | $5.5 / 20$ | **0.2750** | 0.2750 |
| `FULL_AERIS` Evidence Recall (N=19) | $5.5 / 19$ | **0.2895** | — |

## Issue 2: Why Retrieval Metrics Are Genuinely Identical

All eight variants report **Evidence Hit Rate = 35.0%** and **Evidence Recall = 0.2750**. Independent audit confirms this is **genuinely invariant**, not a software bug or shared cache:

1. **Cited Chunk Sets Differ:** Cross-variant chunk set comparison confirms differences on `q_df_01`, `q_mh_03`, `q_mh_04`, `q_mh_05`, `q_comp_03`, and `q_unans_03`, proving distinct execution pathways.
2. **Identical Gold Hits:** On exactly 7 answerable questions (`q_mh_03`, `q_mh_05`, `q_meth_01`, `q_comp_02`, `q_quant_02`, `q_contra_01`, `q_contra_02`), the initial hybrid retrieval ($k=10/25$) already captured the gold chunk. All variants cited these chunks, yielding $7 \times 1 = 7$ hits and $\sum \text{Recall} = 5.5$.
3. **Identical Misses:** On the remaining 13 answerable questions, neither baseline hybrid retrieval nor adaptive depth expansion ($k=50$) found the gold chunks.
4. **Component Boundary Isolation:** Downstream components (`NO_CLAIM_VERIFICATION`, `NO_CONTRADICTION_ANALYSIS`, `NO_CROSSLINGUAL_AGREEMENT`, `NO_SELECTIVE_VERIFICATION`) execute after retrieval and claim extraction; they affect claim calibration and filtering, but do not alter document chunk retrieval.

### Per-Question Evidence Hit & Recall Breakdown (All 20 Answerable Questions):

| Question ID | Gold Chunks | Hit? | Recall | Result Across All 8 Variants |
|---|---|:---:|:---:|---|
| `q_df_01` | `['test_document_p001_c001']` | **0** | 0.00 | Identical across all 8 variants |
| `q_df_02` | `['test_document_p003_c007']` | **0** | 0.00 | Identical across all 8 variants |
| `q_df_03` | `['test_document_p002_c005', 'test_document_p018_c040', 'test_document_p019_c041']` | **0** | 0.00 | Identical across all 8 variants |
| `q_df_04` | `['test_document_p007_c018']` | **0** | 0.00 | Identical across all 8 variants |
| `q_df_05` | `['test_document_p018_c039']` | **0** | 0.00 | Identical across all 8 variants |
| `q_df_06` | `['test_document_p005_c011']` | **0** | 0.00 | Identical across all 8 variants |
| `q_mh_01` | `['test_document_p006_c014', 'test_document_p018_c039']` | **0** | 0.00 | Identical across all 8 variants |
| `q_mh_02` | `['test_document_p002_c004', 'test_document_p003_c007']` | **0** | 0.00 | Identical across all 8 variants |
| `q_mh_03` | `['test_document_p018_c040', 'test_document_p019_c041']` | **1** | 0.50 | Identical across all 8 variants |
| `q_mh_04` | `['test_document_p006_c015', 'test_document_p009_c022']` | **0** | 0.00 | Identical across all 8 variants |
| `q_mh_05` | `['test_document_p007_c018', 'test_document_p008_c019']` | **1** | 0.50 | Identical across all 8 variants |
| `q_meth_01` | `['test_document_p004_c010']` | **1** | 1.00 | Identical across all 8 variants |
| `q_meth_03` | `['test_document_p004_c008', 'test_document_p004_c009']` | **0** | 0.00 | Identical across all 8 variants |
| `q_meth_04` | `['test_document_p009_c021']` | **0** | 0.00 | Identical across all 8 variants |
| `q_comp_01` | `['test_document_p009_c022']` | **0** | 0.00 | Identical across all 8 variants |
| `q_comp_02` | `['test_document_p006_c014']` | **1** | 1.00 | Identical across all 8 variants |
| `q_quant_01` | `['test_document_p007_c017']` | **0** | 0.00 | Identical across all 8 variants |
| `q_quant_02` | `['test_document_p008_c019']` | **1** | 1.00 | Identical across all 8 variants |
| `q_contra_01` | `['test_document_p006_c014']` | **1** | 1.00 | Identical across all 8 variants |
| `q_contra_02` | `['test_document_p018_c039', 'test_document_p008_c019']` | **1** | 0.50 | Identical across all 8 variants |

## Issue 3: Cross-Lingual Latency Audit

- **Reported Value:** 0.00s
- **Actual Raw Latency:** Mean = **0.00008277 seconds** (82.77 microseconds)
- **Call Count:** 27 calls in `FULL_AERIS`, 28 in others (0 in `NO_CROSSLINGUAL_AGREEMENT`).
- **Explanation:** The benchmark document is 100% English. The `ClaimCrossLingualAnalyzer` inspected chunk language metadata, found 0 multilingual pairs, and exited in sub-millisecond time. Standard `:.2f` formatting rounded $0.00008277\text{s}$ to `0.00s`. The component was actively invoked and timed on every run.

## Issue 4: Latency Reconciliation (FULL_AERIS)

The 5.32s discrepancy between the sum of stage means (96.61s) and mean end-to-end latency (101.93s) is **100% mathematically accounted for** by the single failed run:

| Component | Duration / Metric | Note |
|---|:---:|---|
| 27 Successful Runs Mean E2E | **99.8477s** | Measured by controller |
| 27 Successful Runs Sum of Stage Means | **99.8471s** | Sum of Planning through Answer Gen |
| **Residual on Successful Runs** | **0.0006s** | **Near-zero (<1ms timer precision)** |
| `q_mh_04` (Failed Run) Total Latency | **158.2165s** | Total execution timer |
| `q_mh_04` Recorded Stage Latencies | **9.1574s** | Planning (5.98s) + Retrieval (3.18s) |
| `q_mh_04` Unrecorded Aborted Claim Typing | **149.0591s** | 3 LLM retries before throwing exception |
| Amortized Unrecorded Time ($149.06 / 28$) | **5.3235s** | Added to 28-run average |
| All 28 Runs Sum of Stage Means + Amortized Overhead | 96.6082s + 5.3235s = **101.9317s** | Exactly equals reported E2E mean (**101.93s**) |

## Audit Deliverables

- JSON Audit: `data/results/ablation_final224_independent_audit.json`
- Markdown Audit: `data/results/ablation_final224_independent_audit.md`
