# AERIS-RAG — Step 22C Measurement Repair Implementation Report

**Project:** `E:\aeris-rag`  
**Reference Experiment:** `exp_final224_20261011_113501`  
**Repair Status:** **IMPLEMENTED & VERIFIED VIA INTEGRATION TESTS** (Pending Review)  
**Date:** 2026-10-11  

---

## 1. Executive Summary

In response to the final gate audit finding (`ENGINEERING_VALID_BUT_SCIENTIFICALLY_BLOCKED`), the approved measurement repair specified in [ablation_final224_measurement_repair_plan.md](file:///e:/aeris-rag/data/results/ablation_final224_measurement_repair_plan.md) has been implemented and validated in the codebase.

The repair cleanly separates:
1. **Retriever Performance:** Evaluated strictly from `retrieved_chunk_ids` (the candidate chunks returned by the hybrid retriever and reranker).
2. **Citation Performance:** Evaluated strictly from `supporting_chunk_ids` (the subset of chunks cited in the generated answer).
3. **Provenance Validation:** Guarantees that citations outside `retrieved_chunk_ids` trigger an explicit provenance defect without silent removal.
4. **Query Reformulation Telemetry:** Standardizes query event types across producers and consumers.

**All existing experiment results, manifests, benchmark files, and previous audit reports remain 100% immutable and untouched.**

---

## 2. Code Changes Implemented

### 2.1 Retrieval Instrumentation (`app/controller/schemas.py` & `app/controller/controller.py`)
- **`app/controller/schemas.py`:** Added additive fields to `ControllerResult`:
  - `retrieved_chunk_ids: List[str]` $\rightarrow$ Deterministically ordered unique chunk IDs from the retrieval stage.
  - `retrieval_attempts_history: List[Dict[str, Any]]` $\rightarrow$ Detailed per-attempt record (query, candidate depth, returned chunks).
  - `provenance_defects: List[str]` $\rightarrow$ List of cited chunk IDs not present in `retrieved_chunk_ids`.
- **`app/controller/controller.py`:**
  - At line 117 (immediately after adaptive retrieval completes and before claim extraction begins), populated `retrieved_chunk_ids` and `retrieval_attempts_history`.
  - Added strict provenance validation comparing `supporting_chunk_ids` against `retrieved_chunk_ids`. If invalid chunk citations are detected, they are flagged in `provenance_defects` and the answer support status is invalidated to `INSUFFICIENT_EVIDENCE` with an explicit diagnostic reason.
  - Passed `retrieved_chunk_ids`, `retrieval_attempts_history`, and `provenance_defects` through `ControllerResult`.

### 2.2 Metric Calculation Decoupling (`app/ablation/schemas.py` & `app/ablation/runner.py`)
- **`app/ablation/schemas.py`:** Added additive metric fields to `AblationResult`:
  - `retrieved_chunk_ids: List[str]`
  - `retriever_hit: bool`
  - `retriever_recall: float`
  - `citation_hit: bool`
  - `citation_recall: float`
  - `provenance_defects: List[str]`
  - Maintained `evidence_hit` and `evidence_recall` as backward-compatible aliases mirroring citation metrics.
- **`app/ablation/runner.py`:**
  - Evaluates `retriever_hit` and `retriever_recall` by intersecting `record.supporting_chunk_ids` (gold evidence) with `result.retrieved_chunk_ids`.
  - Evaluates `citation_hit` and `citation_recall` by intersecting gold evidence with `result.supporting_chunk_ids`.
  - In execution failures (`except Exception` block), strictly populates `final_status="FAILED"`, `retriever_hit=False`, `retriever_recall=0.0`, `citation_hit=False`, `citation_recall=0.0`, `is_answerable=False`, and `success=False` (never lumping into insufficient or supported).

### 2.3 Query-Reformulation Telemetry Fix (`app/adaptive_retrieval/schemas.py` & `app/controller/controller.py`)
- **`app/adaptive_retrieval/schemas.py`:** Added canonical helper `is_reformulated_query_type(query_type)` that recognizes both `"reformulated"` and `"reformulation_<n>"`.
- **`app/controller/controller.py`:** Updated telemetry aggregation at line 600 to check `att.query_type == "reformulated" or str(att.query_type).startswith("reformulation")`.
- Guarantees that query reformulations are accurately tracked in `reformulation_triggered` and `reformulation_attempt_count`.

---

## 3. Test Suite & Integration Verification

Two test suites covering the measurement repair were executed:

### 3.1 Unit Test Suite (`tests/test_retrieval_vs_citation_metrics.py`)
- `test_retriever_vs_citation_divergence`: **PASSED** (Gold retrieved but not cited $\rightarrow$ Retriever Hit = 1.0, Citation Hit = 0.0).
- `test_provenance_defect_detection`: **PASSED** (Cited chunk not in retrieved pool $\rightarrow$ Flags provenance defect).
- `test_failed_run_intent_to_treat_accounting`: **PASSED** (Failed executions isolated from insufficient/supported; strict ITT denominators).
- `test_query_reformulation_telemetry_consistency`: **PASSED** (Consistent event counting).

### 3.2 Integration Test Suite (`tests/test_integration_measurement_repair.py`)
- `test_controller_schema_fields`: **PASSED** (Schema serialization and deserialization).
- `test_provenance_defect_flagging_in_controller`: **PASSED** (Controller detection and recording of invalid citations).
- `test_runner_metric_divergence_and_provenance`: **PASSED** (Runner consumes `retrieved_chunk_ids` for retrieval metrics and `supporting_chunk_ids` for citation metrics).
- `test_failed_execution_runner_handling`: **PASSED** (Failure serialization matches schema and intent-to-treat rules).
- `test_query_reformulation_telemetry_matching`: **PASSED** (Depth expansion and query reformulation matching).

### 3.3 Full Deterministic Test Execution
```powershell
$env:PYTHONPATH="E:\aeris-rag"; python -m pytest tests/test_retrieval_vs_citation_metrics.py tests/test_integration_measurement_repair.py tests/test_cache_isolation.py tests/test_profiler_accounting.py tests/test_json_parsing.py tests/test_scientific_validity.py tests/test_requirement_support.py -v
```
**Results:** **28 passed in 18.25s (100% PASS, 0 failures)**

---

## 4. Exact Modified Files Summary

| File Path | Description of Changes |
|---|---|
| [`app/controller/schemas.py`](file:///e:/aeris-rag/app/controller/schemas.py) | Added `retrieved_chunk_ids`, `retrieval_attempts_history`, and `provenance_defects` to `ControllerResult`. |
| [`app/controller/controller.py`](file:///e:/aeris-rag/app/controller/controller.py) | Populated retrieved chunk pool at line 117; enforced provenance validation; resolved query reformulation telemetry mismatch. |
| [`app/ablation/schemas.py`](file:///e:/aeris-rag/app/ablation/schemas.py) | Added `retrieved_chunk_ids`, `retriever_hit/recall`, `citation_hit/recall`, and `provenance_defects` to `AblationResult`. |
| [`app/ablation/runner.py`](file:///e:/aeris-rag/app/ablation/runner.py) | Decoupled retrieval metric calculation from citation metrics; added explicit failure handling. |
| [`app/adaptive_retrieval/schemas.py`](file:///e:/aeris-rag/app/adaptive_retrieval/schemas.py) | Added canonical `is_reformulated_query_type` helper. |
| [`tests/test_retrieval_vs_citation_metrics.py`](file:///e:/aeris-rag/tests/test_retrieval_vs_citation_metrics.py) | Unit tests for dual metrics, ITT denominators, provenance defects, and telemetry. |
| [`tests/test_integration_measurement_repair.py`](file:///e:/aeris-rag/tests/test_integration_measurement_repair.py) | Integration tests for controller evidence pool passing and runner consumption. |

---

## 5. Artifact Immutability Confirmation

The following reference artifacts remain **100% unchanged**:
- Benchmark dataset: [`data/benchmark/aeris_benchmark.json`](file:///e:/aeris-rag/data/benchmark/aeris_benchmark.json)
- Raw 224-run results: [`data/results/ablation_results_final224.json`](file:///e:/aeris-rag/data/results/ablation_results_final224.json)
- 224-run manifest: [`data/results/ablation_results_final224_manifest.json`](file:///e:/aeris-rag/data/results/ablation_results_final224_manifest.json)
- Independent audit report: [`data/results/ablation_final224_independent_audit.md`](file:///e:/aeris-rag/data/results/ablation_final224_independent_audit.md)
- Final gate audit report: [`data/results/ablation_final224_final_gate_audit.md`](file:///e:/aeris-rag/data/results/ablation_final224_final_gate_audit.md)
- Measurement repair plan: [`data/results/ablation_final224_measurement_repair_plan.md`](file:///e:/aeris-rag/data/results/ablation_final224_measurement_repair_plan.md)

---

## 6. Current Status & Next Steps

- **Repair Status:** Complete, verified via unit and integration tests.
- **Scientific Claim Status:** Scientific validity is **NOT** claimed at this stage. Step 23 has **NOT** been started.
- **Awaiting Review:** The instrumentation repair is ready for user review. Future ablation re-evaluations will now independently measure and report both Retriever Hit/Recall and Citation Hit/Recall.
