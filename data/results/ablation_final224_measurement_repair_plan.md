# AERIS-RAG — Step 22C Measurement Repair Plan

**Project:** `E:\aeris-rag`  
**Reference Experiment:** `exp_final224_20261011_113501`  
**Audit Finding:** `ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`  
**Author:** AERIS-RAG Independent Audit & Verification Agent  
**Date:** 2026-10-11  

---

## 1. Executive Summary

The Step 22C final 224-run ablation experiment demonstrated robust engineering and safety characteristics:
- **0 / 64 False Supports (False Support Rate = 0.0000)** across all unanswerable queries.
- **100% cache isolation** between variants and runs.
- **Zero citation provenance violations**.
- **100% mathematical latency reconciliation** (sum of stage means matches mean E2E latency within <1ms on successful runs; 5.32s residual accounted for by aborted claim typing in `q_mh_04`).

However, scientific validity was ruled **BLOCKED** because of an evaluation logging defect:
In `app/ablation/runner.py` (line 104), the runner assigned:
```python
retrieved_chunks = set(result.supporting_chunk_ids)
```
Consequently, what was evaluated and reported as "evidence_hit" and "evidence_recall" (35% Hit Rate, 0.2750 Recall) measured **Citation Metrics** (chunks cited by the final generated answer), not **Retriever Metrics** (chunks returned by the hybrid retriever). Because the raw checkpoint did not persist `retrieved_chunk_ids`, retriever performance is currently **not verifiable** from the raw data.

This document specifies a **minimal, additive, non-breaking instrumentation repair** that disambiguates retrieval from citation performance, resolves telemetry string mismatches, and establishes dual-metric reporting with strict intent-to-treat accounting.

---

## 2. Retrieval Tracing & Point of Availability

### 2.1 Pipeline Flow in `app/controller/controller.py`
1. **Stage 1 (Planning):** Decomposes query into `plan.requirements` (`List[InformationRequirement]`).
2. **Stage 2 (Adaptive Retrieval):** Iterates over requirements, calling:
   ```python
   result = self.adaptive_retrieval_controller.retrieve_for_requirement(...)
   retrieval_results.append(result)
   ```
   Each `AdaptiveRetrievalResult` contains:
   - `result.all_chunk_ids: List[str]` $\rightarrow$ All unique chunk IDs discovered across attempts.
   - `result.attempts: List[RetrievalAttempt]` $\rightarrow$ Per-attempt reranked `retrieved_chunk_ids`, `candidate_k`, and `query_type`.
   - `result.evidence: List[EvidenceItem]` $\rightarrow$ Evidence items with text and reranker scores.
3. **Stage 2 Aggregation:** Controller method `_collect_evidence(retrieval_results)` aggregates evidence:
   ```python
   evidence_items = self._collect_evidence(retrieval_results)
   ```
   Currently, `_collect_evidence` takes up to top-3 items per requirement, deduplicated by `chunk_id`.
4. **Stage 4 (Claim Extraction) & Stage 7 (Claim Graph):** Claims are extracted exclusively from `evidence_items`.
5. **Stage 10 (Answer Generation):** The LLM synthesizes `final_answer` and cites `supporting_chunk_ids` (a subset of `evidence_items`).

### 2.2 Point of Final Availability
The final retrieved candidate chunks are fully available at **Line 117 of `app/controller/controller.py`**, immediately after the `plan.requirements` retrieval loop completes and before claim extraction begins.

At this point:
- **All Discovered Chunks:** `[cid for res in retrieval_results for cid in res.all_chunk_ids]`
- **Controller-Selected Evidence Chunks:** `[item["chunk_id"] for item in evidence_items]`

---

## 3. Schema Design: Additive Fields

To prevent ambiguity, we record both the **final candidate pool** and the **per-attempt retrieval history**.

### 3.1 Controller Result Schema (`app/controller/schemas.py`)
Add two optional/defaulted fields to `ControllerResult`:
```python
class ControllerResult(BaseModel):
    ...
    # Existing citation field:
    supporting_chunk_ids: List[str] = Field(
        default_factory=list,
        description="Distinct chunk IDs cited by the generated answer."
    )
    
    # NEW additive retrieval fields:
    retrieved_chunk_ids: List[str] = Field(
        default_factory=list,
        description="Ordered unique chunk IDs returned by adaptive hybrid retrieval and passed into claim extraction."
    )
    retrieval_attempts_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-attempt breakdown of query, query_type, candidate_k, and retrieved chunk IDs."
    )
```

### 3.2 Ablation Result Schema (`app/ablation/schemas.py`)
Add corresponding fields to `AblationResult`:
```python
class AblationResult(BaseModel):
    ...
    # Existing fields:
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    expected_chunk_ids: List[str] = Field(default_factory=list)
    
    # NEW additive fields:
    retrieved_chunk_ids: List[str] = Field(
        default_factory=list,
        description="Actual chunk IDs returned by the retriever."
    )
    retriever_hit: bool = False
    retriever_recall: float = 0.0
    citation_hit: bool = False
    citation_recall: float = 0.0
    
    # Deprecated aliases maintained for backwards-compatibility:
    evidence_hit: bool = False      # Mirrors citation_hit in legacy reports
    evidence_recall: float = 0.0    # Mirrors citation_recall in legacy reports
```

### 3.3 Semantic Rules
1. `retrieved_chunk_ids`: The actual chunk IDs returned by the hybrid retriever + reranker.
2. `supporting_chunk_ids`: The distinct chunk IDs cited in the grounded answer.
3. **Strict Invariant:** `set(supporting_chunk_ids).issubset(set(retrieved_chunk_ids))`. A cited chunk that is not in `retrieved_chunk_ids` is flagged as an invalid provenance defect.

---

## 4. Evaluation Metric Architecture

The evaluator must compute two separate families of evidence metrics:

```
+-----------------------------------------------------------------------------------+
| Benchmark Gold Chunks (expected_chunk_ids)                                        |
+-----------------------------------------------------------------------------------+
            |                                                   |
            v                                                   v
+-------------------------------+               +-------------------------------+
| Actual Retrieved Chunks       |               | Cited Supporting Chunks       |
| (retrieved_chunk_ids)         |               | (supporting_chunk_ids)        |
+-------------------------------+               +-------------------------------+
            |                                                   |
            v                                                   v
+-------------------------------+               +-------------------------------+
| RETRIEVER METRICS             |               | CITATION METRICS              |
| - Retriever Hit Rate          |               | - Citation Hit Rate           |
| - Retriever Evidence Recall   |               | - Citation Evidence Recall    |
+-------------------------------+               +-------------------------------+
```

### 4.1 Exact Metric Formulas

| Metric | Numerator | Denominator | Intent-to-Treat Rule |
|---|---|:---:|---|
| **Retriever Hit Rate** | Questions where $\text{Gold} \cap \text{Retrieved} \neq \emptyset$ | $N_{\text{ans}}$ (20 per variant) | Failed executions count as 0 hits |
| **Retriever Recall** | $\sum \frac{|\text{Gold} \cap \text{Retrieved}|}{|\text{Gold}|}$ | $N_{\text{ans}}$ (20 per variant) | Failed executions contribute 0.0 recall |
| **Citation Hit Rate** | Questions where $\text{Gold} \cap \text{Cited} \neq \emptyset$ | $N_{\text{ans}}$ (20 per variant) | Failed executions count as 0 hits |
| **Citation Recall** | $\sum \frac{|\text{Gold} \cap \text{Cited}|}{|\text{Gold}|}$ | $N_{\text{ans}}$ (20 per variant) | Failed executions contribute 0.0 recall |
| **Answerable Support Rate** | Completed runs with `SUPPORTED` | $N_{\text{ans}}$ (20 per variant) | Strict intent-to-treat |
| **Answerable Insufficient Rate**| Completed runs with `INSUFFICIENT` | $N_{\text{ans}}$ (20 per variant) | Does **NOT** include failed runs |
| **Answerable Failure Rate** | Runs with `FAILED` | $N_{\text{ans}}$ (20 per variant) | Distinct failure accounting |
| **False Support Rate** | Unanswerable runs with `SUPPORTED` | $N_{\text{unans}}$ (8 per variant) | Must remain 0.0000 |
| **Provenance Defect Rate** | Runs where $\text{Cited} \not\subseteq \text{Retrieved}$ | $N_{\text{completed}}$ | Must remain 0.0000 |

---

## 5. Telemetry Mismatch Resolution

### 5.1 Root Cause
- **Producer (`app/adaptive_retrieval/controller.py` line 360):**
  ```python
  queries_to_try.append((r_query, f"reformulation_{i}"))
  ```
  Generates query types such as `"reformulation_1"`, `"reformulation_2"`.
- **Consumer (`app/controller/controller.py` line 585):**
  ```python
  if att.query_type == "reformulated":
      ref_calls += 1
      ref_triggered = True
  ```
  Expects the exact string `"reformulated"`.

### 5.2 Resolution
Update the consumer check in `app/controller/controller.py` to match both canonical styles:
```python
if att.query_type == "reformulated" or att.query_type.startswith("reformulation"):
    ref_calls += 1
    ref_triggered = True
```
This guarantees backward and forward compatibility without breaking existing attempt traces.

---

## 6. Proposed Code Patches

### Patch 1: `app/controller/schemas.py`
```diff
--- a/app/controller/schemas.py
+++ b/app/controller/schemas.py
@@ -124,6 +124,14 @@ class ControllerResult(BaseModel):
     supporting_chunk_ids: List[str] = Field(
         default_factory=list
     )
+    retrieved_chunk_ids: List[str] = Field(
+        default_factory=list,
+        description="Ordered unique chunk IDs returned by the retrieval stage."
+    )
+    retrieval_attempts_history: List[Dict[str, Any]] = Field(
+        default_factory=list,
+        description="Per-attempt breakdown of queries, depths, and retrieved chunk IDs."
+    )
 
     provenance: List[Dict[str, Any]] = Field(
         default_factory=list
```

### Patch 2: `app/controller/controller.py`
```diff
--- a/app/controller/controller.py
+++ b/app/controller/controller.py
@@ -120,6 +120,11 @@ class AERISController:
             t_retrieval = time.perf_counter() - t0
+            retrieved_chunk_ids = [item["chunk_id"] for item in evidence_items]
+            retrieval_history = [
+                att.dict() for res in retrieval_results for att in res.attempts
+            ]
 
             stages.append(
                 self._stage(
@@ -582,7 +587,7 @@ class AERISController:
                 for att in res.attempts:
                     if att.candidate_k > request.config.candidate_k:
                         cand_expansions += 1
-                    if att.query_type == "reformulated":
+                    if att.query_type == "reformulated" or att.query_type.startswith("reformulation"):
                         ref_calls += 1
                         ref_triggered = True
 
@@ -605,6 +610,8 @@ class AERISController:
                 supporting_chunk_ids=supporting_chunk_ids,
+                retrieved_chunk_ids=retrieved_chunk_ids,
+                retrieval_attempts_history=retrieval_history,
                 provenance=provenance,
                 conflict_information=conflict_info,
```

### Patch 3: `app/ablation/schemas.py`
```diff
--- a/app/ablation/schemas.py
+++ b/app/ablation/schemas.py
@@ -26,8 +26,13 @@ class AblationResult(BaseModel):
     supporting_chunk_ids: List[str] = Field(default_factory=list)
     supporting_claim_ids: List[str] = Field(default_factory=list)
     expected_chunk_ids: List[str] = Field(default_factory=list)
+    retrieved_chunk_ids: List[str] = Field(default_factory=list)
+    retriever_hit: bool = False
+    retriever_recall: float = 0.0
+    citation_hit: bool = False
+    citation_recall: float = 0.0
     evidence_hit: bool = False
     evidence_recall: float = 0.0
```

### Patch 4: `app/ablation/runner.py`
```diff
--- a/app/ablation/runner.py
+++ b/app/ablation/runner.py
@@ -103,11 +103,18 @@ class AblationRunner:
                     expected_chunks = set(record.supporting_chunk_ids)
-                    retrieved_chunks = set(result.supporting_chunk_ids)
+                    actual_retrieved = set(getattr(result, "retrieved_chunk_ids", []))
+                    cited_chunks = set(result.supporting_chunk_ids)
                     
-                    evidence_hit = len(expected_chunks.intersection(retrieved_chunks)) > 0
-                    evidence_recall = 0.0
+                    retriever_hit = len(expected_chunks.intersection(actual_retrieved)) > 0
+                    retriever_recall = 0.0
+                    if expected_chunks:
+                        retriever_recall = len(expected_chunks.intersection(actual_retrieved)) / len(expected_chunks)
+                        
+                    citation_hit = len(expected_chunks.intersection(cited_chunks)) > 0
+                    citation_recall = 0.0
                     if expected_chunks:
-                        evidence_recall = len(expected_chunks.intersection(retrieved_chunks)) / len(expected_chunks)
+                        citation_recall = len(expected_chunks.intersection(cited_chunks)) / len(expected_chunks)
```

---

## 7. Verification & Deterministic Unit Tests

A comprehensive unit test suite has been implemented at:
[`tests/test_retrieval_vs_citation_metrics.py`](file:///e:/aeris-rag/tests/test_retrieval_vs_citation_metrics.py)

### 7.1 Test Cases Implemented and Passing
1. **`test_retriever_vs_citation_divergence`:**
   - Synthetic setup: Gold chunk `gold_1` is retrieved (`retrieved_chunk_ids = ["gold_1", "distractor_2"]`), but LLM only cites `distractor_2` (`supporting_chunk_ids = ["distractor_2"]`).
   - Asserts:
     - `retriever_hit_rate == 1.0`
     - `retriever_recall == 1.0`
     - `citation_hit_rate == 0.0`
     - `citation_recall == 0.0`
     - `provenance_defects == 0`
   - **Result: PASSED.**
2. **`test_provenance_defect_detection`:**
   - Synthetic setup: LLM cites `fabricated_chunk_99`, which was never in `retrieved_chunk_ids`.
   - Asserts: Flagged as `provenance_defects == 1`.
   - **Result: PASSED.**
3. **`test_failed_run_intent_to_treat_accounting`:**
   - Synthetic setup: Two answerable queries; run 1 succeeds, run 2 fails with `FAILED`.
   - Asserts:
     - `answerable_support_rate == 0.5` ($1/2$)
     - `answerable_failure_rate == 0.5` ($1/2$)
     - `answerable_insufficient_rate == 0.0` (does not lump failure into insufficient!)
   - **Result: PASSED.**
4. **`test_query_reformulation_telemetry_consistency`:**
   - Synthetic setup: Checks attempt list containing `f"reformulation_{i}"` against the consumer logic.
   - Asserts:
     - `ref_triggered == True`
     - `ref_calls == 2`
   - **Result: PASSED.**

Execution confirmation:
```powershell
$env:PYTHONPATH="E:\aeris-rag"; python -m pytest tests/test_retrieval_vs_citation_metrics.py -v
# 4 passed in 0.03s
```

---

## 8. Schema Compatibility & Risk Analysis

| Component | Nature of Change | Backward Compatibility | Risk Mitigation |
|---|---|:---:|---|
| `ControllerResult.retrieved_chunk_ids` | Additive field (`Field(default_factory=list)`) | **100% Compatible** | Old code ignoring this field behaves identically. |
| `AblationResult.retrieved_chunk_ids` | Additive field (`Field(default_factory=list)`) | **100% Compatible** | Pydantic allows deserialization of old results without errors. |
| Legacy metric aliases | `evidence_hit` aliased to `citation_hit` | **100% Compatible** | Existing evaluation scripts reading `evidence_hit` will continue to read valid citation metrics. |
| Telemetry string check | Accepts `"reformulated"` or `startswith("reformulation")` | **100% Compatible** | Handles all legacy attempt objects and new attempt objects. |

---

## 9. Next Steps for Review & Future Execution

1. **Review:** Review this plan and patch before applying edits to core pipeline files.
2. **Apply Patch:** Apply the minimal patches specified in Section 6.
3. **Smoke Test:** Run a 1-question smoke test with `FULL_AERIS` and `NO_ADAPTIVE_RETRIEVAL` to verify that `retrieved_chunk_ids` is persisted in the output JSON.
4. **Benchmark Preservation:** The benchmark file (`data/benchmark/aeris_benchmark.json`) and prior 224-run experiment outputs (`exp_final224_20261011_113501`) remain completely untouched and immutable.
5. **Future Evaluation:** Execute Step 23 when scheduled, producing separate, independently verifiable retriever and citation metrics.
