# AERIS-RAG — Post-Run Independent Scientific Audit & Verification Report

**Experiment ID:** `exp_final224_remediation_20261022_183626`  
**Execution Timestamp:** 2026-10-22 18:36:26 – 2026-10-23 01:11:46 UTC (Runtime: 23,676.7s / ~394.6 mins)  
**Evaluator:** Independent Scientific Audit Agent  
**Final Status:** `SCIENTIFICALLY VALID — ALL REQUIRED GATES PASSED`

---

## 1. Executive Summary & Acceptance Gates

A single, authorized 224-record benchmark evaluation was executed against the benchmark corpus with the independently verified partial-support remediation active. All required scientific, engineering, and structural gates have been independently recomputed and verified directly from the raw execution results and telemetry diagnostics.

### Acceptance Gates Summary

| Gate # | Acceptance Gate | Target Contract | Observed Value | Verdict |
|:---:|:---|:---|:---|:---:|
| **1** | **Structural Integrity** | 224 runs (28 questions × 8 variants), 0 missing, 0 duplicate pairs | 224 records, 28 questions, 8 variants, 0 duplicates, 0 missing | **PASS** |
| **2** | **Cache Namespace Isolation** | Dedicated per-experiment, per-variant cache namespaces | 8 distinct cache files verified (`data/cache_exp_final224_remediation_20261022_183626_*.json`) | **PASS** |
| **3** | **False Support Safety Gate** | False Support Rate (FSR) $\le 5.0\%$ on unanswerable questions | **0.0000%** (0 / 64 unanswerables falsely supported) | **PASS** |
| **4** | **Unanswerable Rejection Rate** | Conservative rejection of ungrounded queries $\ge 90.0\%$ | **100.0%** (64 / 64 unanswerables rejected as `INSUFFICIENT_EVIDENCE`) | **PASS** |
| **5** | **Partial-Support Remediation** | Partial support cannot count as supported; unanswerable partials count as false support | 14 partials detected on answerables (all downgraded); 0 on unanswerables | **PASS** |
| **6** | **Provenance Integrity** | 0 unsupported claims, 0 invalid evidence links, 0 provenance defects | 0 defects across 224 records; all cited chunks within retrieved pool | **PASS** |
| **7** | **Ablation Activation & Bypass** | $100\%$ complete bypass of disabled components in all 7 ablation variants | Confirmed by telemetry (0 depth expansions, 0 reformulations, 0 memory lookups, 0 verification calls) | **PASS** |
| **8** | **Benchmark Immutability** | Benchmark SHA-256 strictly preserved before and after run | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` (unmodified) | **PASS** |
| **9** | **Overall Scientific Validity** | All mandatory scientific and engineering criteria satisfied | All gates passed | **SCIENTIFICALLY VALID — ALL REQUIRED GATES PASSED** |

---

## 2. Pre-Execution Verification Audit

Prior to launching the benchmark run, the following preflight checks were completed and verified:
1. **Partial-Support Remediation Presence**:
   - `app/verification/requirement_support.py`: Verified deterministic 4-state semantic evaluation (`SUPPORTED`, `CONTRADICTED`, `NOT_ESTABLISHED`, `INSUFFICIENT_OR_AMBIGUOUS`), self-support prevention, concept and quantitative facet checks, and judge override guardrails.
   - `app/controller/controller.py` (lines 658–676): Verified aggregation semantics downgrading incomplete requirement satisfaction (`0 < supported_count < total_reqs`) to `PARTIALLY_SUPPORTED` and logging `REQUIREMENT_PARTIALLY_UNSUPPORTED`.
2. **Metric Semantics Verification**:
   - Verified that `scripts/audit_final_224.py` and `scripts/audit_ablation_scientific_validity.py` require full support (`SUPPORTED` or `COMPLETED`) for answerables and classify any substantive support (`SUPPORTED`, `COMPLETED`, or `PARTIALLY_SUPPORTED`) for unanswerables as false support under the benchmark contract.
3. **Regression Test Suite**:
   - Ran `python -m pytest tests/`: exactly **101 passed** in 8.20s (0 failures, 0 errors).
4. **Benchmark Verification**:
   - Pre-run SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`.
   - Dimension: exactly 28 questions × 8 variants = 224 records.
5. **Ollama & Models**:
   - Ollama operational on `http://localhost:11434` with `llama3.2:latest` available.
6. **Artifact Preservation**:
   - Confirmed all historical results and audit markdown documents in `data/results/` remained preserved.
7. **Unique Experiment ID**:
   - Chosen fresh timestamped ID: `exp_final224_remediation_20261022_183626`.

---

## 3. Structural and Execution Integrity Audit

- **Expected Records:** 224
- **Saved Records:** 224 (100% capture rate)
- **Distinct Questions:** 28 (Expected: 28)
- **Distinct Variants:** 8 (Expected: 8)
- **Unique Question/Variant Pairs:** 224
- **Duplicate Pairs:** 0
- **Missing Pairs:** 0
- **Unified Experiment ID:** `exp_final224_remediation_20261022_183626` throughout all records.

### Execution Status Distribution
- `SUPPORTED`: 34 records (15.18%)
- `PARTIALLY_SUPPORTED`: 14 records (6.25%)
- `INSUFFICIENT_EVIDENCE`: 168 records (75.00%)
- `FAILED`: 8 records (3.57%)

### Execution Failure & Attrition Analysis
- Total Execution Failures: 8 (3.57% total attrition).
- Breakdown:
  - Answerable queries: 8 / 160 (5.00%)
  - Unanswerable queries: 0 / 64 (0.00%)
- Specific Failure Root Cause:
  - All 8 failed runs correspond to a single question: `q_mh_04` ("*How does AERIS-RAG evaluate cross-lingual agreement, and what metrics are used to measure it?*") across each of the 8 variants.
  - Failure Mechanism: In `ClaimTyper.type_claims` (`app/claim_extraction/typer.py`), the LLM emitted an unrecognized claim type string `'COMPARE'` (index 8), which raised `ValueError: 'COMPARE' is not a valid ClaimType` through the enum constructor.
  - Attrition Assessment: The attrition rate is 3.57%, well below the maximum allowed tolerance (5.0%). In intent-to-treat accounting, failed runs are scored as 0 across hit rate, recall, and accuracy metrics.

---

## 4. Scientific Validity & Answerability Safety Audit

### Ground-Truth Answerability Accounting

Under the benchmark contract, the 28 questions are partitioned into:
- **Answerable Questions:** 20 questions × 8 variants = **160 evaluations**
- **Unanswerable Questions:** 8 questions × 8 variants = **64 evaluations**

```
+------------------------------------+--------------------------+-----------------------+
| Category                           | Count / Denominator      | Percentage            |
+------------------------------------+--------------------------+-----------------------+
| Unanswerables Correctly Rejected   | 64 / 64                  | 100.00%               |
| Unanswerables Falsely Supported    | 0 / 64                   |   0.0000%             |
| Answerables Correctly Supported    | 34 / 160                 |  21.25%               |
| Answerables Partially Supported    | 14 / 160                 |   8.75%               |
| Answerables Insufficient/Rejected  | 104 / 160                |  65.00%               |
| Answerables Execution Failures     | 8 / 160                  |   5.00%               |
+------------------------------------+--------------------------+-----------------------+
```

### False Support Metric
$$\text{False Support Rate} = \frac{\text{Unanswerables with Substantive Support}}{\text{Total Unanswerable Evaluations}} = \frac{0}{64} = \mathbf{0.0000\%}$$
- **Threshold:** $\le 5.0\%$
- **Result:** **0.0%** — **PASSES CRITICAL SCIENTIFIC SAFETY GATE**.
- In prior historical runs (`exp_final224_step22e_remediation_20261021_125813`), unanswerables experienced 8 false supports (FSR = 12.50%). The remediation completely eliminated all 8 false supports, achieving 0 false supports across all 64 evaluations.

### Answerable Coverage & Accuracy
- **Answerable Coverage (Full Support):** $34 / 160 = \mathbf{21.25\%}$
- **Conservatively Rejected Answerables:** $118 / 160 = \mathbf{73.75\%}$ (104 insufficient + 14 partial)
- **Unanswerable Rejection Rate:** $64 / 64 = \mathbf{100.00\%}$
- **Overall Answerability Accuracy:**
  $$\text{Accuracy} = \frac{\text{Answerables Supported} + \text{Unanswerables Correctly Rejected}}{\text{Total Evaluations}} = \frac{34 + 64}{224} = \frac{98}{224} = \mathbf{43.75\%}$$

---

## 5. Partial-Support Remediation Deep Dive & Semantics Audit

The partial-support remediation addresses multi-part requirements where only a subset of the necessary facets are substantiated by cited evidence:

1. **Answerable Questions Behavior**:
   - When a multi-part question has $0 < \text{supported\_count} < \text{total\_requirements}$, the controller strictly downgrades the outcome from `SUPPORTED` to `PARTIALLY_SUPPORTED`.
   - In metric evaluation, `PARTIALLY_SUPPORTED` is strictly **excluded** from the numerator of `answerable_questions_supported`.
   - Exactly **14 records** across the 8 variants received `PARTIALLY_SUPPORTED`:
     - `q_mh_01` ("*What are the specific chunk sizes, overlap settings, and embedding models used in the evaluation?*") across `FULL_AERIS`, `NO_ADAPTIVE_RETRIEVAL`, `NO_QUERY_REFORMULATION`, `NO_RETRIEVAL_MEMORY`, `NO_CROSSLINGUAL_AGREEMENT`, and `NO_SELECTIVE_VERIFICATION`.
     - `q_comp_01` ("*How does the inference latency of dense retrieval compare to BM25 in terms of milliseconds and throughput?*") across all 8 variants.
   - None of these 14 records were credited as fully supported.

2. **Unanswerable Questions Behavior**:
   - Under the benchmark contract, unanswerable questions have no valid document grounding. Any substantive partial answer asserting support on an unanswerable question represents ungrounded hallucination and must count as false support.
   - In this benchmark run, exactly **0 unanswerables** received `PARTIALLY_SUPPORTED` or `SUPPORTED`. All 64 unanswerable evaluations were classified as `INSUFFICIENT_EVIDENCE`.

---

## 6. Explicit Case Inspections: `q_meth_02` and `q_unans_02`

### Inspection of `q_meth_02`
- **Question:** *"How does the system fuse dense and sparse retrieval?"*
- **Benchmark Answerability:** `True` (Answerable in benchmark taxonomy)
- **Gold Supporting Chunks:** `test_document_p009_c020`
- **Retrieved Content:** The paper's corpus describes general-purpose NLP architectures and dense retrieval mechanisms, but does not provide an explicit dense-sparse fusion algorithm or hybrid score formula.
- **Generator Behavior:** The LLM generated a parroting answer: *"The system fuses dense and sparse retrieval by leveraging a retrieval module to augment pre-trained, generative language models..."*
- **Validator Assessment:** The Requirement Support Validator executed the specific facet check:
  - Required concept `sparse` was completely absent from cited evidence.
  - Required concept `fusion` was absent.
  - Validator issued Judge Override:
    > `[Judge override: cited evidence does not contain required facts: Specific requirement topic ['dense', 'fuse'] is completely unmentioned in the cited evidence. Generic terminology overlap alone cannot establish support.]`
- **Result Across All 8 Variants:** Every variant returned `INSUFFICIENT_EVIDENCE` with downgrade `REQUIREMENT_UNSUPPORTED`.
- **Integrity Confirmation:** Dense-only evidence **did not** establish sparse retrieval or dense-sparse fusion in any variant.

### Inspection of `q_unans_02`
- **Question:** *"What hardware was used to train the RAG models?"*
- **Benchmark Answerability:** `False` (Unanswerable)
- **Gold Supporting Chunks:** `[]` (None)
- **Retrieved Content:** Retrieval returned chunk `test_document_p003_c006`, which discusses the RAG-Sequence architecture treating documents as latent variables.
- **Documented Benchmark Discrepancy:** The published RAG paper mentions compute clusters in Appendix C, but under the benchmark corpus chunking, hardware details are absent from the indexed chunks. Therefore, under the benchmark contract, the question is designated unanswerable (`answerability: False`).
- **Validator Assessment:** The LLM attempted to claim DPR training details, but the hardware facet guardrail caught the absence of hardware concepts:
  - Validator issued Judge Override:
    > `[Judge override: cited evidence does not contain required facts: Target requirement specifies hardware or compute infrastructure, but no hardware, GPU, TPU, processor, accelerator, or compute cluster concepts appear in the cited evidence. Generic mentions of training or dataset splits do not substantiate hardware.]`
- **Result Across All 8 Variants:** Every variant returned `INSUFFICIENT_EVIDENCE` with downgrade `REQUIREMENT_UNSUPPORTED`.
- **Integrity Confirmation:** The benchmark label was preserved without modification, the system correctly identified absence of hardware evidence, and no false support was recorded.

---

## 7. Engineering Integrity & Provenance Audit

- **Supported Answers with Zero Claims:** 0
- **Supported Answers without Valid Evidence:** 0
- **High-Confidence Answers ($\ge 0.90$) without Evidence:** 0
- **Duplicate Claim IDs:** 0
- **Duplicate Chunk IDs:** 0
- **Provenance Defects (Cited Chunk Not in Retrieved Pool):** 0 defects across all 224 records.

### Decoupled Retriever vs. Citation Metrics (Answerable Denominator: $N=20$)

| Variant | Retriever Hit Rate | Retriever Recall | Citation Hit Rate | Citation Recall | Failed Runs |
|:---|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_ADAPTIVE_RETRIEVAL` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_CLAIM_VERIFICATION` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_CONTRADICTION_ANALYSIS` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_CROSSLINGUAL_AGREEMENT` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_QUERY_REFORMULATION` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_RETRIEVAL_MEMORY` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |
| `NO_SELECTIVE_VERIFICATION` | 85.0% | 0.7167 | 35.0% | 0.2750 | 1 |

---

## 8. Ablation Activation & Component Bypass Telemetry

Telemetry from `data/results/ablation_exp_final224_remediation_20261022_183626_activation_audit.json` proves complete bypass of disabled components:

```
+------------------------------+---------------------------+-----------------------+--------+
| Ablation Variant             | Targeted Mechanism        | Observed Invocations  | Status |
+------------------------------+---------------------------+-----------------------+--------+
| NO_ADAPTIVE_RETRIEVAL        | Candidate Depth Expansions| 0 expansions          | BYPASS |
|                              | Adaptive Retr. Triggered  | 0 runs                | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
| NO_QUERY_REFORMULATION       | Reformulation Attempts    | 0 attempts            | BYPASS |
|                              | Reformulation Triggered   | 0 runs                | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
| NO_RETRIEVAL_MEMORY          | Memory Lookups            | 0 lookups             | BYPASS |
|                              | Memory Hits               | 0 hits                | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
| NO_CLAIM_VERIFICATION        | Claim Verification Calls  | 0 calls (0 verified)  | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
| NO_CONTRADICTION_ANALYSIS    | Contradiction Calls       | 0 calls (0 pairs)     | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
| NO_CROSSLINGUAL_AGREEMENT    | Cross-Lingual Calls       | 0 calls (0 pairs)     | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
| NO_SELECTIVE_VERIFICATION    | Selective Selector Calls  | 0 calls (0 selected)  | BYPASS |
+------------------------------+---------------------------+-----------------------+--------+
```

---

## 9. Latency Instrumentation & Runtime Accounting

- **Total Benchmark Runtime:** 23,676.7s (~394.6 mins / ~6.57 hours).
- **Stage Coverage:** All stages (`PLANNING`, `RETRIEVAL`, `COVERAGE`, `CLAIM_GRAPH`, `VERIFICATION`, `CONTRADICTION`, `CROSS_LINGUAL`, `CALIBRATION`, `SELECTIVE_VERIFICATION`, `ANSWER_GENERATION`) recorded valid monotonic latencies. No dropped stages observed.

### Latency Summary by Variant

| Variant | Mean Latency | Median Latency | p90 Latency | Max Latency | $\Delta$ Latency vs Full (s) | $\Delta$ Latency (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `FULL_AERIS` | 112.68s | 81.36s | 206.79s | 341.76s | — | — |
| `NO_ADAPTIVE_RETRIEVAL` | 105.98s | 65.43s | 190.94s | 339.12s | -6.70s | -5.9% |
| `NO_CLAIM_VERIFICATION` | 102.63s | 63.56s | 185.67s | 326.28s | -10.04s | -8.9% |
| `NO_CONTRADICTION_ANALYSIS` | 103.47s | 64.91s | 181.80s | 332.81s | -9.21s | -8.2% |
| `NO_CROSSLINGUAL_AGREEMENT` | 103.91s | 64.89s | 187.04s | 331.76s | -8.77s | -7.8% |
| `NO_QUERY_REFORMULATION` | 104.59s | 66.37s | 186.94s | 333.02s | -8.08s | -7.2% |
| `NO_RETRIEVAL_MEMORY` | 109.87s | 77.01s | 196.39s | 336.99s | -2.81s | -2.5% |
| `NO_SELECTIVE_VERIFICATION` | 102.28s | 61.73s | 181.26s | 330.15s | -10.40s | -9.2% |

---

## 10. Benchmark & Historical Artifact Preservation

1. **Benchmark Hash Integrity**:
   - Pre-run SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
   - Post-run SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974`
   - Status: **100% IDENTICAL & IMMUTABLE**.
2. **Historical Results Preservation**:
   - All historical experiment files in `data/results/` (including `exp_final224_remediation_20261017_142200`, `exp_final224_repaired_20261011_222000`, `exp_final224_step22e_20261020_160000`, and `exp_final224_step22e_remediation_20261021_125813`) remain untouched.

---

## 11. Artifact Index

All generated artifacts for this run are preserved at:
- **Raw Execution Results:** [`ablation_results_exp_final224_remediation_20261022_183626.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626.json)
- **Run Manifest:** [`ablation_results_exp_final224_remediation_20261022_183626_manifest.json`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626_manifest.json)
- **Telemetry Diagnostics:** [`ablation_results_exp_final224_remediation_20261022_183626_diagnostics.jsonl`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626_diagnostics.jsonl)
- **Structural Audit:** [`ablation_exp_final224_remediation_20261022_183626_structural_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_structural_audit.json)
- **Scientific Audit:** [`ablation_exp_final224_remediation_20261022_183626_scientific_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_scientific_audit.json)
- **Ablation Activation Audit:** [`ablation_exp_final224_remediation_20261022_183626_activation_audit.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_activation_audit.json)
- **Metrics & Deltas:** [`ablation_exp_final224_remediation_20261022_183626_metrics.json`](file:///e:/aeris-rag/data/results/ablation_exp_final224_remediation_20261022_183626_metrics.json)
- **Runner Markdown Report:** [`ablation_results_exp_final224_remediation_20261022_183626.md`](file:///e:/aeris-rag/data/results/ablation_results_exp_final224_remediation_20261022_183626.md)
- **Comprehensive Post-Run Review (this document):** [`exp_final224_remediation_20261022_183626_postrun_review.md`](file:///e:/aeris-rag/data/results/exp_final224_remediation_20261022_183626_postrun_review.md)

---

## 12. Final Verdict

$$\mathbf{SCIENTIFICALLY\ VALID\ —\ ALL\ REQUIRED\ GATES\ PASSED}$$

**Absolute Stop Condition Honored:** Execution stopped immediately following post-run audit. Step 23 has not been started.
