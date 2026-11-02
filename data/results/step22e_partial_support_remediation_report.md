# AERIS-RAG — Post-Benchmark Remediation Report: Partial-Support False Positives

**Document ID:** `step22e_partial_support_remediation_report`  
**Date:** 2026-10-21  
**Experiment Under Review:** `exp_final224_step22e_remediation_20261021_125813`  
**Status:** IMPLEMENTED AND VERIFIED VIA TEST SUITE (BENCHMARK RERUN NOT EXECUTED)

---

## 1. Executive Summary

Following the execution of benchmark experiment `exp_final224_step22e_remediation_20261021_125813`, the previous defect on `q_unans_02` (training hardware hallucination) was completely eliminated (0/8 false support, 100% rejected as `INSUFFICIENT_EVIDENCE`). However, Gate 3 (False-Support Rate $\le 5.0\%$) failed with an observed rate of 12.50% (8/64 unanswerable evaluations). 

Detailed audit revealed that **all 8 false-support instances stemmed from a single question: `q_meth_02`**, evaluated across all 8 ablation variants.

`q_meth_02` asks: *"How does the system fuse dense and sparse retrieval representations?"*  
The source paper (Lewis et al., 2020) evaluates Dense Passage Retrieval (DPR) with BART, but does not implement or evaluate sparse retrieval (BM25/TF-IDF) or dense-sparse fusion. The benchmark ground truth marks `q_meth_02` as `answerability = False` with `supporting_chunk_ids = []`.

This remediation resolves the mechanism by which `q_meth_02` became a positive support label, enforces strict multi-aspect requirement satisfaction, prevents ungrounded claim self-support, and separates partial support from full support across the controller and scientific audit metrics.

---

## 2. Root Cause Analysis of `q_meth_02`

The root cause was traced through three interacting layers:

### 2.1 Coarse Synonym Clustering in `RequirementSupportValidator`
In `app/verification/requirement_support.py`, the semantic synonym group was previously:
```python
{"retrieval", "retriever", "dense", "sparse", "dpr", "bm25", "search"}
```
Because `dense` and `sparse` were grouped together into a single synonym bag with generic `retrieval`, any retrieved passage containing the word "retrieval" or "retriever" was treated as satisfying requirements for "sparse" and "dense". Dense and sparse are fundamentally distinct retrieval paradigms; conflating them caused the validator to treat sparse retrieval as established when only dense retrieval was present.

### 2.2 Ungrounded Claim Self-Support
In the validator's deterministic evaluator:
```python
source_evidence_text = " ".join(claims) + " " + evidence_str
source_tokens = get_semantic_tokens(source_evidence_text)
```
If the LLM generated an ungrounded claim asserting "The system uses sparse retrieval," the token `sparse` entered `source_tokens` directly from the claim. The requirement validator then matched `sparse` against itself, creating self-support where an ungrounded claim substantiated its own requirement.

### 2.3 Partial Support Treated as Fully Supported in Scientific Auditing
When the controller evaluated the 3 sub-requirements planned for `q_meth_02` (R1: Dense retrieval, R2: Sparse retrieval, R3: Fusion), only R1 was grounded. The controller downgraded the answer from `SUPPORTED` to `PARTIALLY_SUPPORTED`.

However, in `scripts/audit_final_224.py` and `scripts/audit_ablation_scientific_validity.py`, the audit logic evaluated:
```python
is_supported = status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]
```
For answerable questions, this conflated partial support with full support. For unanswerables, the benchmark contract correctly treats any substantive claim of support as false support, but the controller had allowed an answer that failed essential requirements (sparse retrieval and fusion) to retain substantive support rather than being fully rejected as insufficient evidence.

---

## 3. Remediation Implementation

### 3.1 Decoupling Retrieval Modalities and Distinctive Facet Checks
In `app/verification/requirement_support.py`:
1. **Decoupled Synonym Bags:**
   ```python
   {"retrieval", "retriever", "search", "lookup"},
   {"dense", "dpr", "embedding", "vector", "bi-encoder", "biencoder"},
   {"sparse", "bm25", "tfidf", "tf-idf", "lexical", "keyword"},
   {"fuse", "fused", "fusion", "combines", "combination", "hybrid", "joint"},
   ```
2. **Facet Verification for Sparse, Dense, and Fusion:**
   Explicit checks ensure that if a requirement asks for `sparse`, `dense`, or `fusion`, the cited evidence must contain corresponding concepts. Generic retrieval overlap cannot establish support.
3. **Elimination of Self-Support:**
   `source_tokens` now strictly combines `evidence_tokens` with `claim_grounded_tokens`. Ungrounded tokens from claims can never enter `source_tokens`.
4. **General Non-Numeric Contradiction Detection:**
   Contradiction scanning was extended beyond numerical claims to specific non-generic entities and phrases qualified by explicit negations (`not used`, `not supported`, `unsupported`, `never`).

### 3.2 Essential Requirement Validation in the Controller
In `app/controller/controller.py`:
1. Identifies essential requirements (`priority == 1`). If no requirements are explicitly marked priority 1, all planned requirements are treated as essential.
2. Tracks `essential_unsupported` and `essential_contradicted`.
3. Ensures that missing or contradicted essential requirements strictly prevent classification as fully `SUPPORTED`.
4. Logs detailed downgrade diagnostics including `essential_unsupported` and `essential_contradicted`.

### 3.3 Metric Semantics Separation
In `scripts/audit_final_224.py` and `scripts/audit_ablation_scientific_validity.py`:
- **Answerable Questions:** Only `SUPPORTED` and `COMPLETED` count towards `ans_correct_supported`. `PARTIALLY_SUPPORTED` is tracked separately and does not count as full support.
- **Unanswerable Questions:** Under the benchmark contract, any substantive answer claiming support (`SUPPORTED`, `COMPLETED`, `PARTIALLY_SUPPORTED`) to an unanswerable question is counted as false support (`unans_incorrect_supported`).

---

## 4. Regression Test Suite

A dedicated regression test suite was implemented in `tests/test_step22e_partial_support_remediation.py` covering all six required conditions:

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_dense_supported_sparse_unsupported_fusion_unsupported` | Validates R1 (dense) supported, R2 (sparse) unsupported, R3 (fusion) unsupported when evidence only contains dense DPR text. | **PASSED** |
| `test_all_essential_requirements_supported` | Verifies full `SUPPORTED` validation when all essential requirements are grounded. | **PASSED** |
| `test_one_essential_requirement_contradicted` | Verifies that explicit evidence negation ("sparse retrieval is not supported") triggers `CONTRADICTED`. | **PASSED** |
| `test_genuinely_partial_answer_downgraded_and_metrics_separated` | Verifies controller downgrades answer to `PARTIALLY_SUPPORTED` and safety metrics exclude it from full support. | **PASSED** |
| `test_unanswerable_question_partial_support_counts_as_false_support` | Verifies benchmark contract: substantive partial support on an unanswerable question counts as false support. | **PASSED** |
| `test_ablation_variants_retain_intended_behavior` | Verifies all 8 ablation variants instantiate cleanly with correct component-disable flags. | **PASSED** |

---

## 5. Test Suite Execution Results

The entire AERIS-RAG test suite was executed:
- **Command:** `python -m pytest tests/`
- **Total Test Files:** 18
- **Total Tests Collected:** 101
- **Exact Results:** **101 passed, 0 failed, 0 skipped** (execution time: 7.92s)

---

## 6. Strict Boundaries and Audit Compliance

1. **Zero Benchmark Runs:** No benchmark runs, reruns, or evaluation scripts were launched.
2. **Benchmark Integrity:** `data/benchmark/aeris_benchmark.json` was verified:
   - SHA-256: `ce9a86b6b4ea354217c54db4b23a5251e97065de53773cf154bb95daccc8e974` (unmodified).
3. **Historical Preservation:** Completed benchmark artifacts for `exp_final224_step22e_remediation_20261021_125813` remain byte-for-byte identical.
4. **Step 23:** Step 23 was not started.
5. **Gate Status:** Gate 3 is documented as pending future authorized evaluation; no unauthorized gate pass is claimed.

---

## 7. Modified Files List

1. `app/verification/requirement_support.py`
2. `app/controller/controller.py`
3. `scripts/audit_final_224.py`
4. `scripts/audit_ablation_scientific_validity.py`
5. `tests/test_step22e_partial_support_remediation.py`
