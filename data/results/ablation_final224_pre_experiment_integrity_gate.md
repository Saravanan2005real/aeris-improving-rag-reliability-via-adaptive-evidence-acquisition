# AERIS-RAG — Final Pre-Experiment Integrity Gate Report

**Project:** `E:\aeris-rag`  
**Reference Experiment:** `exp_final224_20261011_113501`  
**Integrity Gate Verdict:** **PASS** (Ready for Review)  
**Date:** 2026-10-11  

---

## 1. Executive Summary & Gate Verdict

This audit independently inspects the code diffs, schema changes, failure paths, provenance guardrails, and telemetry across all changed Python files following the Step 22C measurement repair.

| Integrity Gate Focus | Requirement | Verification Result | Gate Verdict |
|---|---|---|:---:|
| **1. Python File Diffs** | Review diffs across all seven changed Python files | Clean, additive, backward-compatible diffs verified | **PASS** |
| **2. Ground-Truth Answerability** | Preserve `is_answerable` as benchmark ground truth on failure; never classify failed runs as abstentions | Exception handler and normal path preserve `record.answerability`; failure is isolated as `FAILED` with 0 ITT credit | **PASS** |
| **3. Final Evidence Pool vs. Union** | `retrieved_chunk_ids` must record final deduplicated pool passed downstream; attempts history must be separate | `retrieved_chunk_ids` captures exact `evidence_items` pool passed to claim graph; attempts history captured in `retrieval_attempts_history` | **PASS** |
| **4. Metric Decoupling & Legacy Aliases** | Retriever metrics use `retrieved_chunk_ids`; citation metrics use `supporting_chunk_ids`; aliases tested | Strict decoupling verified; `evidence_hit/recall` preserved as tested citation aliases | **PASS** |
| **5. Provenance Defect Visibility** | Invalid citations must remain visible in defects and cannot silently disappear upon downgrade | Provenance defects recorded in dedicated field and metadata; citations retained | **PASS** |
| **6. Denominator & Serialization Audit** | No overwritten benchmark labels or denominator drift across failure paths | Intent-to-treat denominators ($N=160, N=20$) preserved; failures explicitly tracked | **PASS** |
| **7. Test Suite Execution** | All deterministic unit and integration tests pass | **24 / 24 PASSED** (0 failures, 0.93s) | **PASS** |

### Overall Verdict: `PASS`

---

## 2. Detailed Inspection of Seven Changed Python Files

### File 1: `app/controller/schemas.py`
- **Additive Fields in `ControllerResult`:**
  - `retrieved_chunk_ids: List[str] = Field(default_factory=list)` $\rightarrow$ Final deduplicated evidence pool.
  - `retrieval_attempts_history: List[Dict[str, Any]] = Field(default_factory=list)` $\rightarrow$ Per-attempt attempt logs.
  - `provenance_defects: List[str] = Field(default_factory=list)` $\rightarrow$ Invalid citation tracker.
- **Verification:** Completely non-breaking; default factories guarantee existing callers do not fail.

### File 2: `app/controller/controller.py`
- **Line 117–135 (Evidence Pool Capture):**
  ```python
  evidence_items = self._collect_evidence(retrieval_results)
  retrieved_chunk_ids = []
  for item in evidence_items:
      cid = item.get("chunk_id")
      if cid and cid not in retrieved_chunk_ids:
          retrieved_chunk_ids.append(cid)
  ```
  *Finding:* Confirmed. This captures the exact deduplicated evidence items passed to Stage 4 (`CLAIM_EXTRACTION`) and Stage 7 (`CLAIM_GRAPH`), rather than the uncurated candidate union.
- **Line 550–565 (Provenance Guardrail):**
  ```python
  provenance_defects = [
      cid for cid in supporting_chunk_ids if cid not in retrieved_chunk_ids
  ]
  if provenance_defects:
      defect_msg = f"Provenance defect: cited chunk(s) {provenance_defects} not in retrieved evidence pool."
      insufficiency_info = f"{insufficiency_info} | {defect_msg}" if insufficiency_info else defect_msg
      if answer_status in ["SUPPORTED", "COMPLETED", "PARTIALLY_SUPPORTED"]:
          answer_status = "INSUFFICIENT_EVIDENCE"
  ```
  *Finding:* When an unretrieved chunk is cited, the answer status is downgraded, but the citation IDs and `provenance_defects` list are preserved. The defect is permanently logged in `ControllerResult.provenance_defects` and `metadata["provenance_defects"]`.
- **Line 600 (Query-Reformulation Telemetry):**
  ```python
  if att.query_type == "reformulated" or str(att.query_type).startswith("reformulation"):
      ref_calls += 1
      ref_triggered = True
  ```
  *Finding:* Resolves the producer-consumer string mismatch between `"reformulation_1"` and `"reformulated"`.
- **Line 670–690 (Exception Handler):**
  Returns `ControllerResult` with `status=StageStatus.FAILED`, `retrieved_chunk_ids=[]`, `provenance_defects=[]`.

### File 3: `app/ablation/schemas.py`
- **Fields in `AblationResult`:**
  - `retrieved_chunk_ids: List[str]`
  - `retriever_hit: bool`, `retriever_recall: float`
  - `citation_hit: bool`, `citation_recall: float`
  - `provenance_defects: List[str]`
  - `evidence_hit: bool`, `evidence_recall: float` (documented citation aliases).

### File 4: `app/ablation/runner.py`
- **Metric Evaluation Decoupling:**
  - `retriever_hit` & `retriever_recall`: Evaluated by intersecting `record.supporting_chunk_ids` (gold evidence) with `actual_retrieved` (`result.retrieved_chunk_ids`).
  - `citation_hit` & `citation_recall`: Evaluated by intersecting gold evidence with `cited_chunks` (`result.supporting_chunk_ids`).
- **Ground-Truth Preservation:**
  - Normal path: `is_answerable=record.answerability`, `expected_answerability=record.answerability`.
  - Exception path: `is_answerable=record.answerability`, `expected_answerability=record.answerability`, `final_status="FAILED"`, `success=False`.
  *Finding:* A failed run on an answerable question remains ground-truth answerable (`is_answerable=True`). It is never overwritten to `False` or counted as an abstention (`INSUFFICIENT_EVIDENCE`).

### File 5: `app/adaptive_retrieval/schemas.py`
- Added canonical helper `is_reformulated_query_type(query_type)` supporting both canonical `"reformulated"` and indexed `"reformulation_<n>"`.

### Files 6 & 7: Test Suites
- [`tests/test_retrieval_vs_citation_metrics.py`](file:///e:/aeris-rag/tests/test_retrieval_vs_citation_metrics.py): 4 unit tests covering metric divergence, provenance defect detection, intent-to-treat failure accounting, and telemetry consistency.
- [`tests/test_integration_measurement_repair.py`](file:///e:/aeris-rag/tests/test_integration_measurement_repair.py): 5 integration tests covering schema propagation, controller provenance defect flagging, runner metric divergence, ground-truth preservation on failure, and query reformulation matching.

---

## 3. Critical Verification: Ground-Truth Answerability Preservation

### 3.1 Trace of `is_answerable`
- **Benchmark Source:** `BenchmarkRecord.answerability: bool` from [aeris_benchmark.json](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json).
- **Prior Flaw:** The runner previously set `is_answerable=(result.answer_status in ["SUPPORTED", ...])` on successful runs and `is_answerable=False` in the exception handler. This conflated the model's decision with the benchmark ground truth and caused failed runs to appear unanswerable.
- **Repair:**
  - `expected_answerability` is set to `record.answerability`.
  - `is_answerable` is set to `record.answerability` across **both** normal completion and failure paths.
  - The model's decision is represented independently by `final_status` (`"SUPPORTED"`, `"INSUFFICIENT_EVIDENCE"`, or `"FAILED"`) and `success` (`True` or `False`).

### 3.2 Intent-to-Treat Failure Accounting
- When an execution fails on an answerable query (e.g. `q_mh_04`):
  - `expected_answerability == True`
  - `is_answerable == True`
  - `final_status == "FAILED"`
  - `success == False`
  - `retriever_hit == False` (0 hits)
  - `citation_hit == False` (0 hits)
  - `retriever_recall == 0.0`
  - `citation_recall == 0.0`
- It is counted in the failure rate ($1 / 160 = 0.62\%$), NOT the insufficient rate ($136 / 160 = 85.00\%$), preserving exact intent-to-treat denominators without distorting abstention metrics.

---

## 4. Evidence Pool vs. Adaptive Candidate Union Verification

- **Candidate Union:** In adaptive retrieval, query attempts across $k \in [10, 25, 50]$ may retrieve 50+ raw candidates.
- **Final Evidence Pool:** The controller executes `evidence_items = self._collect_evidence(retrieval_results)` to select and deduplicate the top reranked chunks per requirement (e.g. up to 3 chunks per requirement).
- **Exact Recording:**
  - `retrieved_chunk_ids` contains strictly `[item["chunk_id"] for item in evidence_items]`. This is the exact set passed to downstream claim extraction and the claim graph.
  - The per-attempt candidate traces are preserved separately in `retrieval_attempts_history`.

---

## 5. Provenance Defect Visibility Verification

- If an answer generator hallucinates a citation `chunk_xyz` that was not in `retrieved_chunk_ids`:
  1. `provenance_defects` is populated with `["chunk_xyz"]`.
  2. `supporting_chunk_ids` retains `["chunk_xyz"]` so the defect remains auditable.
  3. `answer_status` is downgraded to `INSUFFICIENT_EVIDENCE`.
  4. `insufficiency_information` explicitly states: `"Provenance defect: cited chunk(s) ['chunk_xyz'] not in retrieved evidence pool."`
  5. In serialized results, `provenance_defects` is written to `AblationResult.provenance_defects` and `metadata["provenance_defects"]`.
  - The invalid citation **cannot silently disappear**.

---

## 6. Complete Deterministic Test Suite Results

Command executed:
```powershell
$env:PYTHONPATH="E:\aeris-rag"; python -m pytest tests/test_retrieval_vs_citation_metrics.py tests/test_integration_measurement_repair.py tests/test_cache_isolation.py tests/test_profiler_accounting.py tests/test_json_parsing.py tests/test_requirement_support.py -v
```

```
tests/test_retrieval_vs_citation_metrics.py::test_retriever_vs_citation_divergence PASSED [  4%]
tests/test_retrieval_vs_citation_metrics.py::test_provenance_defect_detection PASSED [  8%]
tests/test_retrieval_vs_citation_metrics.py::test_failed_run_intent_to_treat_accounting PASSED [ 12%]
tests/test_retrieval_vs_citation_metrics.py::test_query_reformulation_telemetry_consistency PASSED [ 16%]
tests/test_integration_measurement_repair.py::test_controller_schema_fields PASSED [ 20%]
tests/test_integration_measurement_repair.py::test_provenance_defect_flagging_in_controller PASSED [ 25%]
tests/test_integration_measurement_repair.py::test_runner_metric_divergence_and_provenance PASSED [ 29%]
tests/test_integration_measurement_repair.py::test_failed_execution_runner_handling PASSED [ 33%]
tests/test_integration_measurement_repair.py::test_query_reformulation_telemetry_matching PASSED [ 37%]
tests/test_cache_isolation.py::test_1_existing_cache_loads_correctly PASSED [ 41%]
tests/test_cache_isolation.py::test_2_missing_cache_starts_empty PASSED  [ 45%]
tests/test_cache_isolation.py::test_3_sequential_cache_switching PASSED  [ 50%]
tests/test_cache_isolation.py::test_4_existing_b_after_a PASSED          [ 54%]
tests/test_cache_isolation.py::test_5_corrupt_cache_isolation PASSED     [ 58%]
tests/test_cache_isolation.py::test_6_variant_style_isolation PASSED     [ 62%]
tests/test_cache_isolation.py::test_7_regression_original_failure PASSED [ 66%]
tests/test_profiler_accounting.py::test_successful_pipeline PASSED       [ 70%]
tests/test_profiler_accounting.py::test_failed_claim_extraction PASSED   [ 75%]
tests/test_json_parsing.py::test_plain_valid_json PASSED                 [ 79%]
tests/test_json_parsing.py::test_markdown_wrapped_json PASSED            [ 83%]
tests/test_json_parsing.py::test_json_with_explanatory_text PASSED       [ 87%]
tests/test_json_parsing.py::test_duplicated_model_output_fragments PASSED [ 91%]
tests/test_json_parsing.py::test_truncated_incomplete_json PASSED        [ 95%]
tests/test_requirement_support.py::test_requirement_support_guardrail PASSED [100%]

============================= 24 passed in 0.93s ==============================
```

All 24 tests passed deterministically with zero failures.

---

## 7. Artifact Immutability & Operational Safety

- Benchmark dataset [data/benchmark/aeris_benchmark.json](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json) remains **100% untouched and unchanged**.
- Historical 224-run experiment outputs [ablation_results_final224.json](file:///e:/aeris-rag/data/results/ablation_results_final224.json), manifest, and diagnostics remain **100% immutable**.
- All previous audit reports remain **100% immutable**.
- **No full experiment was executed.**
- **Step 23 has not been started.**
- **Scientific validity is not prematurely claimed.**

The codebase has successfully passed the Pre-Experiment Integrity Gate and is ready for your review.
