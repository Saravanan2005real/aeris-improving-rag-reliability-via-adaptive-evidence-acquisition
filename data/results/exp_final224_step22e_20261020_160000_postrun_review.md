# AERIS-RAG Benchmark Post-Run Inspection & Scientific Audit Review

**Experiment ID:** `exp_final224_step22e_20261020_160000`  
**Date / Timestamp:** 2026-10-20T21:30:00+05:30  
**Inspection Type:** Strictly Read-Only Post-Benchmark Audit Review  
**Primary Report Audited:** `data/results/ablation_results_exp_final224_step22e_20261020_160000.md`  
**Overall Scientific Status:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`  

---

## 1. Acceptance Criteria Evaluation Matrix

| Acceptance Criterion | Status | Detailed Quantitative Evidence |
| :--- | :---: | :--- |
| **Record Completeness** | **PASS** | Expected: 224, Saved: 224 (28 questions × 8 variants). |
| **Record Deduplication** | **PASS** | 0 duplicate `(variant, question_id)` pairs, 0 missing pairs. |
| **Cache Isolation (Gate 2)** | **PASS** | Isolated per-experiment and per-variant namespaces verified across all 8 variants. |
| **Provenance Integrity (Gate 4)** | **PASS** | 0 supported answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects. |
| **Metric Denominators (Gate 5)** | **PASS** | Decoupled retrieval and citation metrics evaluated on answerable denominator ($N=20$). |
| **Ablation Activation (Gate 6)** | **PASS** | Telemetry proves disabled components were 100% bypassed (0 unwanted activations). |
| **Latency Instrumentation (Gate 7)** | **PASS** | End-to-end and stage-level latency tracking intact without dropped stages. |
| **Execution Reliability** | **FAIL** | **151 of 224 runs (67.4%) failed** due to `ModelTimeoutError` during Claim Extraction. |
| **False-Support Safety Gate (Gate 3)** | **FAIL** | **False Support Rate = 10.94% (7 / 64)**, exceeding the mandatory $\le 5.0\%$ threshold. |
| **Historical Artifact Preservation** | **PASS** | All historical experiment files and benchmark dataset match SHA-256 hashes 100%. |
| **Promotion to Production / Step 23** | **BLOCKED** | Promotion blocked; scientific criteria not satisfied. |

---

## 2. Record Counts & Failure Breakdown

- **Expected Records:** 224
- **Saved Records:** 224
- **Successful Evaluations:** 73 (32.6%)
  - Marked `INSUFFICIENT_EVIDENCE`: 52
  - Marked `SUPPORTED`: 21
- **Failed Evaluations (Timeouts):** 151 (67.4%)
  - Answerable Question Failures: 119 / 160
  - Unanswerable Question Failures: 32 / 64
- **Duplicate Pairs:** 0
- **Missing Pairs:** 0

### Root Cause of Execution Failures:
All 151 failed evaluations encountered the identical error:
```text
app.utils.model_client.ModelTimeoutError: Claim Extraction timed out after 60.00s / 62.00s: timed out
```
In `app/config.py`, `ollama_timeout` is configured to `60.0s`. When Claim Extraction processed dense multi-chunk contexts (typically 3,000–6,000 characters) on complex multi-hop or unanswerable questions, local inference on `llama3.2:latest` marginally exceeded 60 seconds (typically finishing in ~62–72 seconds), causing `timed_model_chat` to abort the execution and record `final_status: "FAILED"`.

---

## 3. False-Support Safety Analysis (Gate 3)

### 3.1 Numerical Evaluation:
- **False-Support Numerator:** **7**
- **Evaluation Denominator:** **64** (Total unanswerable question runs: 8 unanswerable questions × 8 variants)
- **False-Support Rate (Audit Formula):** $\frac{7}{64} = \mathbf{10.9375\%}$ (**0.1094**)
- **Alternative Denominator (Completed Unanswerable Runs Only):** $\frac{7}{7 + 25} = \frac{7}{32} = \mathbf{21.875\%}$ (**0.2188**)
- **Criterion Verdict:** **FAIL / BLOCKED** (Both $10.94\%$ and $21.88\%$ exceed the mandatory $\le 5.0\%$ gate).

### 3.2 Treatment of Failed / Timed-Out Records:
Under the established benchmark evaluation formula (`scripts/audit_final_224.py:164`):
$$\text{Total Unanswerable Runs} = \text{unans\_incorrect\_supported} + \text{unans\_correct\_insufficient} + \text{unans\_execution\_failures} = 7 + 25 + 32 = 64$$
Failed records on unanswerable questions are classified as `unans_execution_failures` and are included in the denominator (64). They are **not** counted in the numerator as false support, but they depress overall answerability accuracy ($17.41\%$) and prevent full empirical validation of the unanswerable suite.

### 3.3 Breakdown of the 7 False-Support Cases:
All 7 false-support cases originate from the **exact same unanswerable question** across 7 variants:
- **Question:** `q_unans_02` — *"What hardware was used to train the RAG models?"*
- **Variants affected (7 of 8):**
  1. `FULL_AERIS` (`SUPPORTED`)
  2. `NO_ADAPTIVE_RETRIEVAL` (`SUPPORTED`)
  3. `NO_QUERY_REFORMULATION` (`SUPPORTED`)
  4. `NO_RETRIEVAL_MEMORY` (`SUPPORTED`)
  5. `NO_CONTRADICTION_ANALYSIS` (`SUPPORTED`)
  6. `NO_CROSSLINGUAL_AGREEMENT` (`SUPPORTED`)
  7. `NO_SELECTIVE_VERIFICATION` (`SUPPORTED`)
  *(Note: In `NO_CLAIM_VERIFICATION`, `q_unans_02` timed out and was recorded as `FAILED`).*

### 3.4 Significant Remediation Progress on Step 22E Defects:
The four defects audited and remediated in Step 22E were **completely eliminated**:
- `q_meth_02` (*Dense-sparse fusion*): **0 false supports** (down from 8 in prior run).
- `q_quant_03` (*FEVER dataset instances*): **0 false supports** (down from 8 in prior run).
- `q_multi_01` (*Multilingual tasks*): **0 false supports** (down from 7 in prior run).
- `q_unans_01` (*Capital of Japan / world knowledge*): **0 false supports** (down from 8 in prior run).

Total false-support instances dropped from **31 / 224** ($13.84\%$) to **7 / 224** ($3.125\%$ across all runs, or $10.94\%$ of unanswerable runs), localized entirely to `q_unans_02`.

---

## 4. Audit Gates Review: Engineering vs. Scientific Validity

### 4.1 Engineering Validity: **100% PASS**
- **Gate 1 (Structural Integrity):** **PASS** — Exactly 224 records, 28 questions × 8 variants, 0 duplicates, 0 missing.
- **Gate 2 (Cache Isolation):** **PASS** — Verified isolated cache namespaces per experiment and variant.
- **Gate 4 (Provenance Integrity):** **PASS** — 0 answers without claims, 0 duplicate chunk/claim IDs, 0 provenance defects.
- **Gate 5 (Metric Denominators):** **PASS** — Retriever/citation hit and recall evaluated strictly on answerable denominator ($N=20$).
- **Gate 6 (Ablation Activation):** **PASS** — Telemetry confirms disabled components were 100% bypassed with 0 activations.
- **Gate 7 (Latency Instrumentation):** **PASS** — Valid end-to-end and stage-level timing without dropped stages.

### 4.2 Scientific Validity: **BLOCKED / FAIL**
- **Gate 3 (Answerability & False-Support Safety):** **BLOCKED**
  - **Reason 1:** False Support Rate = $10.94\% > 5.0\%$ due to `q_unans_02`.
  - **Reason 2:** Pervasive execution timeouts in Claim Extraction (151 of 224 records failed, collapsing answerable support rate to $8.75\%$).
- **Gate 8 (Overall Scientific Validity):** **ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED**
  - **Reason:** The experiment meets all software, architectural, and data integrity specifications, but cannot be scientifically promoted because the false-support rate exceeds the safety gate and two-thirds of runs failed due to the 60-second client timeout.

---

## 5. Benchmark & Historical Artifact Preservation

All historical files and benchmark definitions were checked via SHA-256 and confirmed **100% unchanged**:

| Artifact | Expected SHA-256 Checksum | Verified Status |
| :--- | :--- | :---: |
| `data/benchmark/aeris_benchmark.json` | `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` | **UNCHANGED** |
| `ablation_results_exp_final224_remediation_20261017_142200.json` | `df9850207668edaa59d3ce4f5acc7074c119f72b12ce0a4c86638c24197dd6cf` | **UNCHANGED** |
| `ablation_results_exp_final224_remediation_20261017_142200_manifest.json` | `e1f6bb0ae7cd35e4612e4f0adb9af9164032b974b37fd11612c9f5f0a4978a78` | **UNCHANGED** |
| `ablation_results_exp_final224_remediation_20261017_142200_diagnostics.jsonl` | `185273950894ef93ef89d4a0b46c24d5f3f4b3a3bbaae7e53976630af9bae975` | **UNCHANGED** |
| `ablation_exp_final224_remediation_20261017_142200_scientific_audit.json` | `354bb4488226a5ec31bc441c0d1e297e0ad08a86b97aab1887b704f9921cf294` | **UNCHANGED** |
| `ablation_results_exp_final224_repaired_20261011_222000.json` (Step 22C) | `a043dadd00685e59310564ffaba14a697eb3ebcd6c3879f2a619f829f9039bf3` | **UNCHANGED** |
| `ablation_results_exp_final224_repaired_20261011_222000_manifest.json` | `043c1e14f663656c0b4bdccc6c34df6d8e7050d7ba6e96b77723f50ce0a32714` | **UNCHANGED** |
| `ablation_results_exp_final224_repaired_20261011_222000_diagnostics.jsonl` | `bdb0d362bfb4066741449fe4c74631ed065f6dd7b8ec55acf534d86a69a69643` | **UNCHANGED** |
| `ablation_exp_final224_repaired_20261011_222000_scientific_audit.json` | `4b6c14352b208d9375f3fc218ecd0ed9850468f206a97d937df3c07dc3aa16be` | **UNCHANGED** |

---

## 6. Conclusion & Recommendation

1. **Step 22E Progress Confirmed:** The Step 22E fixes successfully eliminated false supports on `q_meth_02`, `q_quant_03`, `q_multi_01`, and `q_unans_01`.
2. **Two Remaining Blockers:**
   - **Timeout Configuration:** The 60-second Ollama timeout in `app/config.py` is too aggressive for local claim extraction on large multi-chunk contexts, causing 151 timeouts.
   - **Hardware Question Entailment:** `q_unans_02` requires explicit topic grounding (e.g. checking for hardware/GPU/TPU terms) in `RequirementSupportValidator`.
3. **Status:** Execution is stopped. No files were modified, no benchmark rerun was triggered, and Step 23 was not initiated.

**Awaiting human review and further instructions.**
